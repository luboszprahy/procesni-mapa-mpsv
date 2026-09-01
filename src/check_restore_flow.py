# -*- coding: utf-8 -*-
"""Brána nad flow RestoreFlow v hotovém solution zipu.

Obnova je jediná operace projektu, která přepisuje existující data, a její
vada se pozná až ve chvíli, kdy je pozdě. Kontroluje se proto offline, nad
tím, co se opravdu nasazuje:

1. **Cíl zápisu se dohledává podle kódu, ne podle ID ze snímku.** To ID je
   stav k okamžiku zálohy; po smazání a znovuzaložení patří jinému záznamu
   a zápis podle něj by tiše přepsal cizí řádek. MERGE proto musí adresovat
   `first(body('Najdi_<list>'))?['ID']` a nikde nesmí sáhnout na `ID`
   z položky smyčky.
2. **Restore nemaže.** Žádná mazací operace ani metoda DELETE.
3. **V náhledu se nezapisuje.** Všechny zápisy leží uvnitř podmínky `Zapis`
   a ta se ptá na režim.
4. **Otisky se počítají symetricky.** Ze seznamu s `?['Value']` u Choice,
   ze snímku bez něj — a v témže pořadí sloupců. Kdyby se rozešly, hlásila
   by obnova změnu u každého řádku a přepsala by celý rejstřík sama sebou.
5. **Úplnost.** Každý list schématu má svou pětici porovnávacích akcí a
   každý sloupec schématu se opravdu zapisuje.
6. **Stránkování** u každého čtení; bez něj se porovnává proti oříznutému
   stavu a obnova by „vracela" i to, co se nezměnilo.

Spouštět z kořene projektu:
    python src/check_restore_flow.py --solution deploy/procesnimapa_1_0_0_84.zip
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402
from build_restore_flow import (FLOW, FLOW_GUID, KNIHOVNA, ODDELOVAC,  # noqa: E402
                                REZIM_ZAPIS, STRANKOVANI, nacti_schema)

chyby = []
kontrol = 0

# Operace a metody, které by z obnovy udělaly mazání. Restore smí zakládat
# a přepisovat, nic víc — řádek, který dnes je a ve snímku není, se jen hlásí.
MAZACI = ("DeleteItem", "DeleteFile", "RecycleItem", "RecycleFile")


def overit(podminka, popis):
    global kontrol
    kontrol += 1
    if not podminka:
        chyby.append(popis)


def text_vseho(uzel):
    return json.dumps(uzel, ensure_ascii=False)


def sp_parametry(akce):
    """Parametry SharePoint akce, nebo None."""
    vstupy = akce.get("inputs")
    if not isinstance(vstupy, dict):
        return None
    host = vstupy.get("host") or {}
    if "shared_sharepointonline" not in str(host.get("apiId", "")):
        return None
    return host.get("operationId"), (vstupy.get("parameters") or {})


def vsechny_akce(kroky, cesta=""):
    """Projde i akce vnořené v If a Foreach — mazání schované ve smyčce
    vypadá v plochém výpisu jako by tam nebylo."""
    for jmeno, uzel in (kroky or {}).items():
        yield (cesta + jmeno), uzel
        for klic in ("actions",):
            yield from vsechny_akce(uzel.get(klic) or {}, cesta + jmeno + "/")
        if isinstance(uzel.get("else"), dict):
            yield from vsechny_akce(uzel["else"].get("actions") or {},
                                    cesta + jmeno + "/else/")


def zkontroluj_kostru(definice, schema):
    akce = definice.get("actions") or {}
    for jmeno in ("Vstup", "Soubor", "Snimek", "Cesta_webu", "Kontrola_verze",
                  "Zapis", "Prehled", "Odpoved"):
        overit(jmeno in akce, f"chybí akce {jmeno}")

    overit(definice.get("contentVersion") == "1.0.0.0",
           f"contentVersion je {definice.get('contentVersion')!r}, "
           f"s jinou hodnotou flow nejde otevřít v designeru")

    trigger = definice.get("triggers") or {}
    overit(len(trigger) == 1, f"čekám právě jeden trigger, je jich {len(trigger)}")
    prvni = next(iter(trigger.values()), {})
    overit(prvni.get("kind") == "PowerAppV2",
           f"trigger není PowerAppV2, ale {prvni.get('kind')!r} — "
           f"obnova se spouští z appky, nikdy plánovaně")
    vlastnosti = ((prvni.get("inputs") or {}).get("schema") or {}).get("properties") or {}
    overit(list(vlastnosti) == ["text"],
           f"trigger má vstupy {list(vlastnosti)}, čekám jediný 'text'")

    soubor = akce.get("Soubor") or {}
    operace, parametry = sp_parametry(soubor) or (None, {})
    overit(operace == "GetFileContentByPath",
           f"snímek se nečte přes GetFileContentByPath, ale {operace!r}")
    overit(parametry.get("inferContentType") is False,
           "čtení snímku nemá inferContentType=false — s výchozím true vrací "
           "konektor obsah rovnou a base64ToString v další akci spadne za běhu")
    overit(KNIHOVNA in str(parametry.get("path", "")),
           f"snímek se nečte z knihovny {KNIHOVNA}: {parametry.get('path')!r}")
    overit("$content" in text_vseho(akce.get("Snimek")),
           "rozbalení snímku nečte $content, ačkoli se stahuje bez inferContentType")

    podminka = text_vseho((akce.get("Kontrola_verze") or {}).get("expression"))
    overit(schema["verze"] in podminka,
           f"kontrola verze schématu neporovnává proti {schema['verze']!r}: {podminka}")
    vetev = ((akce.get("Kontrola_verze") or {}).get("else") or {}).get("actions") or {}
    overit(any(u.get("type") == "Terminate" for u in vetev.values()),
           "při neshodě verze schématu se běh neukončuje — obnova by pokračovala "
           "nad daty, kterým snímek neodpovídá")
    overit(any(u.get("type") == "Response" for u in vetev.values()),
           "při neshodě verze schématu se appce nic nevrací, takže by čekala na "
           "odpověď, která nepřijde")


def zkontroluj_cteni(akce, schema):
    for lst in schema["lists"]:
        jmeno = f"Nacti_{lst['name']}"
        uzel = akce.get(jmeno)
        overit(uzel is not None, f"chybí čtení listu {lst['name']}")
        if not uzel:
            continue
        operace, parametry = sp_parametry(uzel) or (None, {})
        overit(operace == "GetItems", f"{jmeno} není GetItems, ale {operace!r}")
        overit(parametry.get("dataset") == ep.web(),
               f"{jmeno} nebere web z proměnné {ep.WEB}")
        overit(parametry.get("table") == ep.list_param(lst.get("display") or lst["name"]),
               f"{jmeno} nebere list z proměnné prostředí: {parametry.get('table')!r}")
        strankovani = ((uzel.get("runtimeConfiguration") or {})
                       .get("paginationPolicy") or {}).get("minimumItemCount")
        overit(strankovani == STRANKOVANI,
               f"{jmeno} nemá stránkování {STRANKOVANI} — nad 100 řádky by se "
               f"porovnávalo proti oříznutému stavu a obnova by přepsala i to, "
               f"co se nezměnilo")


def sloupce_z_otisku(vyraz):
    """Z výrazu otisku vytáhne dvojice (sloupec, má ?['Value'])."""
    return [(m.group(1), bool(m.group(2)))
            for m in re.finditer(r"item\(\)\?\['([^']+)'\](\?\['Value'\])?", vyraz)]


def zkontroluj_porovnani(akce, schema):
    for lst in schema["lists"]:
        jmeno = lst["name"]
        sloupce = lst["columns"]
        for prefix in ("Kody", "Otisky", "KodySnimku", "K_zalozeni", "Ke_zmene", "Navic"):
            overit(f"{prefix}_{jmeno}" in akce,
                   f"chybí akce {prefix}_{jmeno} — list {jmeno} se neporovnává celý")

        otisk_listu = ((akce.get(f"Otisky_{jmeno}") or {}).get("inputs") or {}).get("select", "")
        ze_seznamu = sloupce_z_otisku(str(otisk_listu))
        overit([s for s, _ in ze_seznamu] == [c["name"] for c in sloupce],
               f"otisk listu {jmeno} nepokrývá sloupce schématu ve stejném pořadí: "
               f"{[s for s, _ in ze_seznamu]}")
        for (nazev, ma_value), sloupec in zip(ze_seznamu, sloupce):
            overit(ma_value == (sloupec["type"] == "Choice"),
                   f"otisk listu {jmeno}, sloupec {nazev}: "
                   f"{'chybí' if sloupec['type'] == 'Choice' else 'přebývá'} ?['Value'] "
                   f"— otisky ze snímku a z listu by se rozešly a obnova by "
                   f"hlásila změnu u každého řádku")
        overit(ODDELOVAC in str(otisk_listu),
               f"otisk listu {jmeno} nepoužívá oddělovač {ODDELOVAC!r}")

        zmena = str(((akce.get(f"Ke_zmene_{jmeno}") or {}).get("inputs") or {}).get("where", ""))
        ze_snimku = sloupce_z_otisku(zmena)
        # Ve where je nejdřív Title z podmínky contains, pak celý otisk.
        overit([s for s, _ in ze_snimku[1:]] == [c["name"] for c in sloupce],
               f"otisk snímku u {jmeno} nepokrývá tytéž sloupce jako otisk listu: "
               f"{[s for s, _ in ze_snimku[1:]]}")
        overit(not any(ma_value for _, ma_value in ze_snimku),
               f"otisk snímku u {jmeno} sahá na ?['Value'] — ve snímku je Choice "
               f"už rozbalený, takže by se otisky nikdy neshodly")
        overit(f"body('Kody_{jmeno}')" in zmena,
               f"Ke_zmene_{jmeno} nekontroluje, že kód v listu vůbec je")

        navic = str(((akce.get(f"Navic_{jmeno}") or {}).get("inputs") or {}).get("where", ""))
        overit(f"body('KodySnimku_{jmeno}')" in navic,
               f"Navic_{jmeno} se neporovnává proti kódům ze snímku")


def zkontroluj_zapis(akce, schema):
    zapis = akce.get("Zapis") or {}
    overit(zapis.get("type") == "If",
           "zápisy nejsou v podmínce — v režimu náhledu by se rejstřík přepsal")
    podminka = text_vseho(zapis.get("expression"))
    overit(REZIM_ZAPIS in podminka,
           f"podmínka zápisu se neptá na režim {REZIM_ZAPIS!r}: {podminka}")
    vnitrek = zapis.get("actions") or {}

    # Žádný zápis nesmí ležet mimo tu podmínku.
    for cesta, uzel in vsechny_akce(akce):
        dvojice = sp_parametry(uzel)
        if not dvojice:
            continue
        operace, parametry = dvojice
        overit(operace not in MAZACI,
               f"{cesta}: mazací operace {operace} — obnova nikdy nemaže, "
               f"řádek navíc se jen hlásí")
        if operace != "HttpRequest":
            continue
        metoda = str(parametry.get("parameters/method", "")).upper()
        overit(metoda != "DELETE", f"{cesta}: REST metoda DELETE — obnova nemaže")
        if metoda in ("POST", "PATCH", "PUT", "MERGE"):
            overit(cesta.startswith("Zapis/"),
                   f"{cesta}: zápis leží mimo podmínku Zapis, takže by proběhl "
                   f"i v režimu náhledu")

    for lst in schema["lists"]:
        jmeno = lst["name"]
        zaloz = vnitrek.get(f"Zaloz_{jmeno}") or {}
        uprav = vnitrek.get(f"Uprav_{jmeno}") or {}
        overit(zaloz.get("type") == "Foreach", f"chybí smyčka Zaloz_{jmeno}")
        overit(uprav.get("type") == "Foreach", f"chybí smyčka Uprav_{jmeno}")
        overit(zaloz.get("foreach") == f"@body('K_zalozeni_{jmeno}')",
               f"Zaloz_{jmeno} nejede přes K_zalozeni_{jmeno}")
        overit(uprav.get("foreach") == f"@body('Ke_zmene_{jmeno}')",
               f"Uprav_{jmeno} nejede přes Ke_zmene_{jmeno}")

        zkontroluj_rest(zaloz.get("actions") or {}, f"Vloz_{jmeno}", lst,
                        f"Zaloz_{jmeno}", merge=False)
        zkontroluj_rest(uprav.get("actions") or {}, f"Zmen_{jmeno}", lst,
                        f"Uprav_{jmeno}", merge=True)

        if merge_akce := (uprav.get("actions") or {}).get(f"Zmen_{jmeno}"):
            zkontroluj_dohledani(uprav.get("actions") or {}, merge_akce, jmeno)


def zkontroluj_rest(vnorene, jmeno_akce, lst, smycka, merge):
    uzel = vnorene.get(jmeno_akce)
    overit(uzel is not None, f"chybí akce {jmeno_akce}")
    if not uzel:
        return
    operace, parametry = sp_parametry(uzel) or (None, {})
    overit(operace == "HttpRequest",
           f"{jmeno_akce} nezapisuje přes SendHTTPRequest, ale {operace!r} — "
           f"konektorová zápisová akce s rozloženým tělem chce table jako GUID "
           f"natvrdo a balík by se nepřenesl na jiný tenant")
    overit(parametry.get("dataset") == ep.web(),
           f"{jmeno_akce} nebere web z proměnné {ep.WEB}")

    uri = str(parametry.get("parameters/uri", ""))
    overit(f"/Lists/{lst['name']}" in uri,
           f"{jmeno_akce} neadresuje list interním názvem {lst['name']}: {uri}")
    overit("outputs('Cesta_webu')" in uri,
           f"{jmeno_akce} neskládá adresu ze server-relative cesty webu")
    overit(not re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-", uri),
           f"{jmeno_akce} má v adrese GUID — ten je vázaný na jeden tenant: {uri}")

    hlavicky = parametry.get("parameters/headers") or {}
    overit("nometadata" in str(hlavicky.get("Content-Type", "")),
           f"{jmeno_akce} neposílá Content-Type s odata=nometadata, ale tělo "
           f"nenese __metadata.type — SharePoint by zápis odmítl")
    if merge:
        overit(str(hlavicky.get("X-HTTP-Method", "")).upper() == "MERGE",
               f"{jmeno_akce} není MERGE — bez něj by POST zakládal další řádek")
        overit(hlavicky.get("IF-MATCH") == "*",
               f"{jmeno_akce} nemá IF-MATCH, SharePoint MERGE bez něj odmítne")
    else:
        overit("X-HTTP-Method" not in hlavicky,
               f"{jmeno_akce} zakládá, ale posílá X-HTTP-Method")

    telo = parametry.get("parameters/body") or {}
    overit(set(telo) == {c["name"] for c in lst["columns"]},
           f"{jmeno_akce} nezapisuje právě sloupce schématu: "
           f"navíc {sorted(set(telo) - {c['name'] for c in lst['columns']})}, "
           f"chybí {sorted({c['name'] for c in lst['columns']} - set(telo))}")
    for sloupec in lst["columns"]:
        hodnota = str(telo.get(sloupec["name"], ""))
        overit(f"items('{smycka}')" in hodnota,
               f"{jmeno_akce}/{sloupec['name']} nebere hodnotu z řádku snímku")
        if sloupec["type"] == "DateTime":
            overit("json('null')" in hodnota,
                   f"{jmeno_akce}/{sloupec['name']} je datum a posílá prázdný "
                   f"řetězec místo null — SharePoint takový řádek odmítne")


def zkontroluj_dohledani(vnorene, merge_akce, jmeno):
    """Tohle je ta kontrola, kvůli které brána existuje."""
    najdi = vnorene.get(f"Najdi_{jmeno}")
    overit(najdi is not None,
           f"chybí Najdi_{jmeno} — cílové ID se pak nemá odkud vzít podle kódu")
    if najdi:
        kde = str((najdi.get("inputs") or {}).get("where", ""))
        overit("item()?['Title']" in kde and f"items('Uprav_{jmeno}')?['Title']" in kde,
               f"Najdi_{jmeno} nedohledává řádek podle kódu: {kde}")

    uri = str(((merge_akce.get("inputs") or {}).get("parameters") or {})
              .get("parameters/uri", ""))
    overit(f"body('Najdi_{jmeno}')" in uri and "['ID']" in uri,
           f"Zmen_{jmeno} nebere cílové ID z dohledaného řádku: {uri}")
    overit(f"items('Uprav_{jmeno}')?['ID']" not in uri,
           f"Zmen_{jmeno} zapisuje podle ID ZE SNÍMKU. To ID je stav k okamžiku "
           f"zálohy — po smazání a znovuzaložení patří jinému záznamu a zápis "
           f"podle něj přepíše cizí řádek.")


def zkontroluj_odpoved(akce, schema):
    odpoved = akce.get("Odpoved") or {}
    overit(odpoved.get("kind") == "PowerApp",
           "odpověď není typu PowerApp, appka by ji nepřečetla")
    schema_odpovedi = ((odpoved.get("inputs") or {}).get("schema") or {}).get("properties") or {}
    overit(set(schema_odpovedi) == {"stav", "hlaseni", "porizeno", "prehled"},
           f"schéma odpovědi je {sorted(schema_odpovedi)} — mění-li se, přestane "
           f"appce sedět a musí se znovu registrovat ve Studiu")
    for jmeno, typ in schema_odpovedi.items():
        overit(typ.get("type") == "string",
               f"pole odpovědi {jmeno} není string; přehled jde schválně jako "
               f"řetězec, aby se schéma neměnilo s počtem listů")

    prehled = text_vseho((akce.get("Prehled") or {}).get("inputs"))
    for lst in schema["lists"]:
        overit(f"K_zalozeni_{lst['name']}" in prehled and f"Navic_{lst['name']}" in prehled,
               f"přehled nezmiňuje list {lst['name']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True)
    argumenty = parser.parse_args()

    cesta = Path(argumenty.solution)
    if not cesta.exists():
        raise SystemExit(f"CHYBA: solution {cesta} neexistuje")
    with zipfile.ZipFile(cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klice = [n for n in polozky if n.replace("\\", "/").startswith(f"Workflows/{FLOW}")]
    overit(len(klice) == 1, f"čekám právě jedno {FLOW}, je jich {len(klice)}")
    if len(klice) != 1:
        return vypis()
    overit(FLOW_GUID.upper() in klice[0],
           f"soubor flow nenese očekávané GUID: {klice[0]}")

    flow = json.loads(polozky[klice[0]].decode("utf-8-sig"))
    overit(bool(flow["properties"].get("connectionReferences")),
           f"{FLOW} nemá connection reference, SharePoint akce by neměly čím běžet")
    definice = flow["properties"]["definition"]
    akce = definice.get("actions") or {}
    schema = nacti_schema()

    zkontroluj_kostru(definice, schema)
    zkontroluj_cteni(akce, schema)
    zkontroluj_porovnani(akce, schema)
    zkontroluj_zapis(akce, schema)
    zkontroluj_odpoved(akce, schema)

    return vypis()


def vypis():
    print(f"kontrol: {kontrol}")
    for chyba in chyby:
        print(f"CHYBA: {chyba}")
    print("NEPROŠLO" if chyby else f"OK — {FLOW} obnovuje podle kódu a nikdy nemaže")
    return 1 if chyby else 0


if __name__ == "__main__":
    sys.exit(main())
