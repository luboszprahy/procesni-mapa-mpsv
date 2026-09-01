# -*- coding: utf-8 -*-
"""Brána nad flow ZalohaFlow a ZalohaScheduled v hotovém solution zipu.

Záloha je jediná věc v projektu, jejíž vada se pozná až ve chvíli, kdy je
pozdě — při obnově. Proto se kontroluje offline, nad tím, co se opravdu
nasazuje:

1. úplnost — snímek čte KAŽDÝ list ze schématu a z každého VŠECHNY sloupce;
2. stránkování — u každého `Get items`; bez něj se snímek nad 100 řádky tiše
   ořízne a běh přitom skončí zeleně;
3. tvar snímku — verze schématu, jedno razítko pro obsah i jméno souboru,
   Choice sloupce s ?['Value'], zápis do knihovny Zalohy;
4. dvojčata — plánované flow dělá totéž co ruční, liší se jen triggerem.

Spouštět z kořene projektu:
    python src/check_zaloha_flow.py --solution deploy/procesnimapa_1_0_0_76.zip
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402
from build_zaloha_flow import (CASOVE_PASMO, DELKA_JMENA, JMENO_SNIMKU,  # noqa: E402
                               KNIHOVNA, PLANOVANE, POCET_ZALOH, POLE_JMENA,
                               RUCNI, STRANKOVANI, nacti_schema)

chyby = []
kontrol = 0


def overit(podminka, popis):
    global kontrol
    kontrol += 1
    if not podminka:
        chyby.append(popis)


def jedine_flow(polozky, prefix):
    klice = [n for n in polozky if n.replace("\\", "/").startswith(f"Workflows/{prefix}")]
    overit(len(klice) == 1, f"čekám právě jedno {prefix}, je jich {len(klice)}")
    return klice[0] if len(klice) == 1 else None


def viditelne(akce, jmeno):
    """Množina akcí, na které smí akce odkazovat: vše v jejím řetězu runAfter
    směrem nahoru. Odkaz mimo ni se naimportuje, ale flow nejde zapnout."""
    videt, fronta = set(), list(akce[jmeno].get("runAfter", {}))
    while fronta:
        krok = fronta.pop()
        if krok in videt or krok not in akce:
            continue
        videt.add(krok)
        fronta.extend(akce[krok].get("runAfter", {}))
    return videt


def zkontroluj_cteni(akce, schema):
    """Každý list schématu se čte, se stránkováním a z proměnné prostředí."""
    ocekavane = {f"Nacti_{l['name']}" for l in schema["lists"]}
    ctene = {j for j in akce if j.startswith("Nacti_")}
    overit(ctene == ocekavane,
           f"snímek nečte tytéž listy jako schéma — chybí {sorted(ocekavane - ctene)}, "
           f"navíc {sorted(ctene - ocekavane)}")

    for lst in schema["lists"]:
        jmeno = f"Nacti_{lst['name']}"
        krok = akce.get(jmeno)
        if krok is None:
            continue
        parametry = (krok.get("inputs") or {}).get("parameters") or {}
        host = (krok.get("inputs") or {}).get("host") or {}
        overit(host.get("operationId") == "GetItems",
               f"{jmeno}: operace je {host.get('operationId')!r}, čekám GetItems")
        overit(parametry.get("dataset") == ep.web(),
               f"{jmeno}: dataset není proměnná {ep.WEB}, ale {parametry.get('dataset')!r}")
        overit(parametry.get("table") == ep.list_param(lst.get("display") or lst["name"]),
               f"{jmeno}: table není proměnná listu, ale {parametry.get('table')!r}")

        strankovani = (((krok.get("runtimeConfiguration") or {})
                        .get("paginationPolicy") or {}).get("minimumItemCount"))
        overit(strankovani == STRANKOVANI,
               f"{jmeno}: stránkování je {strankovani!r} místo {STRANKOVANI} — bez něj "
               f"konektor vrátí jen prvních 100 položek a snímek se TIŠE ořízne")
        overit(parametry.get("$top") == STRANKOVANI,
               f"{jmeno}: $top je {parametry.get('$top')!r} místo {STRANKOVANI}")


def zkontroluj_mapovani(akce, schema):
    """Z každého listu se ukládají všechny sloupce schématu, Choice s ?['Value']."""
    for lst in schema["lists"]:
        jmeno = f"Map_{lst['name']}"
        krok = akce.get(jmeno)
        overit(krok is not None and krok.get("type") == "Select",
               f"{jmeno}: chybí nebo není Select")
        if krok is None:
            continue
        vyber = (krok.get("inputs") or {}).get("select") or {}
        ocekavane = {c["name"] for c in lst["columns"]} | {"ID"}
        overit(set(vyber) == ocekavane,
               f"{jmeno}: snímek neukládá tytéž sloupce jako schéma — chybí "
               f"{sorted(ocekavane - set(vyber))}, navíc {sorted(set(vyber) - ocekavane)}")
        overit((krok.get("inputs") or {}).get("from")
               == f"@outputs('Nacti_{lst['name']}')?['body/value']",
               f"{jmeno}: čte z jiného kroku než z Nacti_{lst['name']}")

        for sloupec in lst["columns"]:
            hodnota = vyber.get(sloupec["name"])
            if hodnota is None:
                continue
            if sloupec["type"] == "Choice":
                overit(hodnota == f"@item()?['{sloupec['name']}']?['Value']",
                       f"{jmeno}.{sloupec['name']}: Choice bez ?['Value'] — do snímku by "
                       f"se uložilo {{\"Value\":\"…\"}} a restore by zapsal nesmysl")
            else:
                overit(hodnota == f"@item()?['{sloupec['name']}']",
                       f"{jmeno}.{sloupec['name']}: neočekávaný výraz {hodnota!r}")


def zkontroluj_snimek(akce, schema):
    """Tvar snímku a zápis do knihovny."""
    snimek = akce.get("Snimek")
    overit(snimek is not None and snimek.get("type") == "Compose",
           "chybí Compose 'Snimek'")
    if snimek is not None:
        vstup = snimek.get("inputs") or {}
        overit(vstup.get("schema_verze") == schema["verze"],
               f"snímek nenese verzi schématu {schema['verze']!r}, ale "
               f"{vstup.get('schema_verze')!r} — restore pak nemá podle čeho poznat, "
               f"že soubor vznikl nad jinou strukturou listů")
        overit(vstup.get("porizeno") == "@outputs('Razitko')",
               "razítko ve snímku není z kroku Razitko")
        listy = vstup.get("listy") or {}
        overit(set(listy) == {l["name"] for l in schema["lists"]},
               f"snímek nenese tytéž listy jako schéma: {sorted(listy)}")
        for jmeno in listy:
            overit(listy[jmeno] == f"@body('Map_{jmeno}')",
                   f"snímek/{jmeno} nebere data z Map_{jmeno}, ale {listy[jmeno]!r}")

    razitko = akce.get("Razitko")
    overit(razitko is not None
           and razitko.get("inputs") == "@formatDateTime(utcNow(), 'yyyy-MM-dd_HHmm')",
           "chybí Compose 'Razitko' s formátem yyyy-MM-dd_HHmm")

    uloz = akce.get("Uloz_zalohu")
    overit(uloz is not None, "chybí akce 'Uloz_zalohu'")
    if uloz is not None:
        parametry = (uloz.get("inputs") or {}).get("parameters") or {}
        host = (uloz.get("inputs") or {}).get("host") or {}
        overit(host.get("operationId") == "CreateFile",
               f"Uloz_zalohu: operace je {host.get('operationId')!r}, čekám CreateFile")
        overit(parametry.get("dataset") == ep.web(),
               f"Uloz_zalohu: dataset není proměnná {ep.WEB}")
        overit(parametry.get("folderPath") == KNIHOVNA,
               f"Uloz_zalohu: ukládá do {parametry.get('folderPath')!r} místo {KNIHOVNA}")
        overit(parametry.get("name") == "@concat('rejstrik_', outputs('Razitko'), '.json')",
               f"Uloz_zalohu: jméno souboru je {parametry.get('name')!r} — musí být "
               f"z téhož razítka jako obsah, jinak snímek tvrdí jiný čas, než má v názvu")
        overit(parametry.get("body") == "@string(outputs('Snimek'))",
               f"Uloz_zalohu: tělo je {parametry.get('body')!r} místo string(outputs('Snimek'))")


def zkontroluj_retez(akce):
    """Řetěz runAfter: právě jeden začátek a žádný odkaz dopředu."""
    zacatky = [j for j, k in akce.items() if not k.get("runAfter")]
    overit(zacatky == ["Razitko"],
           f"první akcí musí být Razitko, je {zacatky}")
    for jmeno, krok in akce.items():
        vidi = viditelne(akce, jmeno)
        for odkaz in set(re.findall(r"(?:outputs|body)\('([^']+)'\)",
                                    json.dumps(krok, ensure_ascii=False))):
            if odkaz not in akce:
                continue
            overit(odkaz in vidi,
                   f"{jmeno} se odkazuje na {odkaz}, který v jeho řetězu runAfter není — "
                   f"flow se naimportuje, ale nejde zapnout")


def zkontroluj_dvojce(polozky, rucni_klic, rucni, hodina):
    """Plánované flow musí dělat totéž a lišit se jen triggerem."""
    klic = jedine_flow(polozky, PLANOVANE)
    if klic is None:
        return
    overit(klic != rucni_klic, "dvojče má stejný soubor jako ruční flow")

    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    definice = flow["properties"]["definition"]
    rucni_def = rucni["properties"]["definition"]

    overit(definice.get("contentVersion") == "1.0.0.0",
           f"dvojče má contentVersion {definice.get('contentVersion')!r}; s 'undefined' "
           "import projde, ale flow nejde otevřít v designeru")
    overit(definice.get("actions") == rucni_def.get("actions"),
           "akce dvojčete se liší od ručního flow — plán by zálohoval něco jiného než "
           "tlačítko a poznalo by se to až při obnově")
    overit(flow["properties"].get("connectionReferences")
           == rucni["properties"].get("connectionReferences"),
           "dvojče nemá stejné connection reference, akce by neměly čím běžet")

    triggery = definice.get("triggers") or {}
    overit(list(triggery) == ["Recurrence"],
           f"dvojče musí mít jediný trigger Recurrence, má {list(triggery)}")
    spousteni = (triggery.get("Recurrence") or {}).get("recurrence") or {}
    overit(spousteni.get("frequency") == "Day" and spousteni.get("interval") == 1,
           f"dvojče se nespouští denně: {spousteni.get('frequency')} / {spousteni.get('interval')}")
    overit(spousteni.get("timeZone") == CASOVE_PASMO,
           f"dvojče má časové pásmo {spousteni.get('timeZone')!r}; bez něj by UTC posunulo "
           "běh podle letního času")
    hodiny = (spousteni.get("schedule") or {}).get("hours")
    overit(hodiny == [str(hodina)], f"dvojče se nespouští v {hodina}:00, ale v {hodiny}")

    overit((rucni_def.get("triggers") or {}).get("manual", {}).get("kind") == "PowerAppV2",
           "ruční flow nemá trigger PowerAppV2, appka by ho nespustila")

    # Bez zápisu v obou XML se flow do prostředí vůbec nedostane.
    customizations = polozky["customizations.xml"].decode("utf-8-sig")
    solution = polozky["solution.xml"].decode("utf-8-sig")
    for jmeno, cesta in ((RUCNI, rucni_klic), (PLANOVANE, klic)):
        guid = re.search(r"-([0-9A-Fa-f-]{36})\.json$", cesta).group(1).lower()
        overit(f'<Workflow WorkflowId="{{{guid}}}" Name="{jmeno}">' in customizations,
               f"{jmeno} chybí v customizations.xml")
        overit(cesta.replace("\\", "/") in customizations.replace("/Workflows", "Workflows"),
               f"customizations.xml neodkazuje na soubor {jmeno}")
        overit(f'<RootComponent type="29" id="{{{guid}}}"' in solution,
               f"{jmeno} není v RootComponents solution.xml, do balíku se nezahrne")


def zkontroluj_knihovnu(schema):
    """Knihovna, do které se ukládá, musí být ve schématu — jinak ji nikdo nezaloží."""
    knihovny = {k["name"] for k in (schema.get("libraries") or [])}
    overit(KNIHOVNA.lstrip("/") in knihovny,
           f"knihovna {KNIHOVNA} není v schema.json/libraries ({sorted(knihovny)}) — "
           f"setup_sharepoint.js ji nezaloží a flow spadne na neexistující složce")


def zkontroluj_uklid(akce):
    """Úklid starých snímků. Maže data, takže se hlídá přísněji než zbytek.

    Čtyři věci, jejichž záměna se pozná až tím, že záloha, kterou někdo
    potřeboval, v knihovně není:

    1. úklid běží AŽ PO uložení nového snímku — jinak by se mazalo o jeden
       víc a při chybě zápisu by zůstal úklid bez zálohy;
    2. maže se jen to, co flow samo vyrobilo (jméno i jeho DÉLKA) — snímek,
       který někdo přejmenoval, aby ho udržel, musí přežít;
    3. `skip`, ne `take` — zahazuje se ocas, ne hlava;
    4. `recycle()`, ne DELETE — soubor jde do koše, takže chyba v úklidu
       není nevratná.
    """
    for jmeno in ("Kolik_nechat", "Cesta_webu", "Snimky", "Nase_snimky",
                  "Ke_smazani", "Smaz_stare"):
        overit(jmeno in akce, f"chybí akce úklidu {jmeno}")
    if "Smaz_stare" not in akce:
        return

    kolik = (akce.get("Kolik_nechat") or {}).get("inputs")
    overit(isinstance(kolik, int) and kolik > 0,
           f"počet ponechaných záloh není kladné číslo, ale {kolik!r}")
    overit(kolik == POCET_ZALOH,
           f"počet ponechaných záloh je {kolik}, generátor má {POCET_ZALOH}")

    overit("Uloz_zalohu" in json.dumps((akce.get("Kolik_nechat") or {}).get("runAfter"), ensure_ascii=False),
           "úklid nezačíná až po uložení nového snímku — mazalo by se o jeden víc, "
           "než je potřeba, a při chybě zápisu by zůstal úklid bez zálohy")

    snimky = ((akce.get("Snimky") or {}).get("inputs") or {}).get("parameters") or {}
    overit(str(snimky.get("$orderby", "")).endswith("desc"),
           f"snímky se nečtou od nejnovějšího ({snimky.get('$orderby')!r}) — "
           f"skip by pak zahodil ty nejnovější")
    strankovani = (((akce.get("Snimky") or {}).get("runtimeConfiguration") or {})
                   .get("paginationPolicy") or {}).get("minimumItemCount")
    overit(strankovani == STRANKOVANI,
           f"čtení snímků nemá stránkování {STRANKOVANI}")

    kde = str(((akce.get("Nase_snimky") or {}).get("inputs") or {}).get("where", ""))
    overit(POLE_JMENA in kde,
           f"úklid nefiltruje podle názvu souboru ({POLE_JMENA})")
    overit(f"'{JMENO_SNIMKU}'" in kde,
           f"úklid se neomezuje na soubory {JMENO_SNIMKU}… — smazal by i cizí "
           f"soubory, které do knihovny někdo nahrál")
    overit(f"length" in kde and str(DELKA_JMENA) in kde,
           "úklid nekontroluje délku názvu — přejmenovaný snímek, který si někdo "
           "schválně nechal, by se smazal taky")

    ke_smazani = str((akce.get("Ke_smazani") or {}).get("inputs", ""))
    overit(ke_smazani.startswith("@skip("),
           f"ke smazání se nebere skip(), ale {ke_smazani[:40]!r} — s take() by "
           f"se mazaly právě ty nejnovější snímky")
    overit("body('Nase_snimky')" in ke_smazani,
           "skip nejede přes filtrované snímky, ale přes všechny soubory")
    overit("outputs('Kolik_nechat')" in ke_smazani,
           "počet ponechaných záloh se nebere z akce Kolik_nechat, takže by ho "
           "nešlo změnit na jednom místě")

    smycka = akce.get("Smaz_stare") or {}
    overit(smycka.get("foreach") == "@outputs('Ke_smazani')",
           f"smyčka úklidu nejede přes Ke_smazani, ale {smycka.get('foreach')!r}")
    recykluj = (smycka.get("actions") or {}).get("Recykluj") or {}
    parametry = ((recykluj.get("inputs") or {}).get("parameters") or {})
    uri = str(parametry.get("parameters/uri", ""))
    overit("recycle()" in uri,
           f"úklid nemaže přes recycle() — soubor by nešel vrátit z koše: {uri[:60]}")
    overit(str(parametry.get("parameters/method", "")).upper() != "DELETE",
           "úklid maže metodou DELETE, tedy natrvalo")
    overit(KNIHOVNA in uri,
           f"úklid neadresuje knihovnu {KNIHOVNA}: {uri[:60]}")
    overit(not re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-", uri),
           "úklid má v adrese GUID vázaný na jeden tenant")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True)
    parser.add_argument("--hodina", type=int, default=5, help="čekaná hodina denního běhu")
    argumenty = parser.parse_args()

    cesta = Path(argumenty.solution)
    if not cesta.exists():
        raise SystemExit(f"CHYBA: solution {cesta} neexistuje")
    with zipfile.ZipFile(cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    schema = nacti_schema()
    zkontroluj_knihovnu(schema)

    klic = jedine_flow(polozky, RUCNI)
    if klic is None:
        vypis()
        return 1

    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    definice = flow["properties"]["definition"]
    akce = definice.get("actions") or {}

    overit(definice.get("contentVersion") == "1.0.0.0",
           f"{RUCNI} má contentVersion {definice.get('contentVersion')!r}")
    overit(bool(flow["properties"].get("connectionReferences")),
           f"{RUCNI} nemá connection reference, SharePoint akce by neměly čím běžet")

    zkontroluj_cteni(akce, schema)
    zkontroluj_mapovani(akce, schema)
    zkontroluj_snimek(akce, schema)
    zkontroluj_uklid(akce)
    zkontroluj_retez(akce)
    zkontroluj_dvojce(polozky, klic, flow, argumenty.hodina)

    vypis()
    return 1 if chyby else 0


def vypis():
    print(f"kontrol: {kontrol}")
    for chyba in chyby:
        print(f"CHYBA: {chyba}")
    print("NEPROŠLO" if chyby else "OK — snímek rejstříku odpovídá schématu")


if __name__ == "__main__":
    sys.exit(main())
