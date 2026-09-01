# -*- coding: utf-8 -*-
"""Brána nad flow ImportFlow v hotovém solution zipu.

Import je slepý zápis do dat, pokud ho neuhlídá náhled — a jeho vady jsou
tiché: posunutý sloupec, přeskočený prázdný řádek, který přeskočený nebyl,
duplicitní kód přidělený dvěma aktivitám. Kontroluje se proto offline, nad
tím, co se opravdu nasazuje:

1. **V náhledu se nezapisuje.** Všechny zápisy leží uvnitř podmínky `Zapis`
   a ta se ptá na režim.
2. **Rozklad řádků je úplný a nepřekrývá se.** Každý řádek sešitu padne
   právě do jedné skupiny; jinak sedí v náhledu jiná čísla než ve
   skutečnosti a správce opravuje podle nich.
3. **Prázdný řádek se nezakládá.** Šablona se vydává s jedním prázdným
   datovým řádkem, protože Tabulku bez něj Excel „opravuje".
4. **Kód se přiděluje sekvenčně ze sdílené proměnné.** Souběžná smyčka by
   dvěma aktivitám pod týmž dílčím procesem dala týž kód.
5. **Nic v balíku není vázané na tenant.** Parametry excelového konektoru se
   skládají za běhu; adresa ani `b!…` v definici být nesmí.
6. **Sloupce sedí na šablonu.** Klíče se čtou podle hlaviček, které generuje
   `make_sablona.py` — kdyby se rozešly, import by tiše zapisoval prázdno.

Spouštět z kořene projektu:
    python src/check_import_flow.py --solution deploy/procesnimapa_1_0_0_85.zip
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402
from build_import_flow import (FLOW, FLOW_GUID, HOST_XLS, KNIHOVNA,  # noqa: E402
                               LIST_AKTIVITY, LIST_DILCI, LIST_VAZBY,
                               REZIM_ZAPIS, SPOJKA_VAZBY, STRANKOVANI, TABULKA,
                               VYCHOZI_STAV, nacti_schema, sloupce_sablony)

chyby = []
kontrol = 0

MAZACI = ("DeleteItem", "DeleteFile", "RecycleItem", "RecycleFile")
# Sloupec, který si dopočítá AktualizaceKratkehoNazvu. Kdyby ho import psal
# taky, přepisovali by se navzájem a v listu by chvíli stálo jedno, chvíli druhé.
DOPOCITAVANE = "nazev_kratky"


def overit(podminka, popis):
    global kontrol
    kontrol += 1
    if not podminka:
        chyby.append(popis)


def text(uzel):
    return json.dumps(uzel, ensure_ascii=False)


def parametry_akce(akce, host_fragment):
    vstupy = akce.get("inputs")
    if not isinstance(vstupy, dict):
        return None
    host = vstupy.get("host") or {}
    if host_fragment not in str(host.get("apiId", "")):
        return None
    return host.get("operationId"), (vstupy.get("parameters") or {})


def vsechny_akce(kroky, cesta=""):
    for jmeno, uzel in (kroky or {}).items():
        yield (cesta + jmeno), uzel
        yield from vsechny_akce(uzel.get("actions") or {}, cesta + jmeno + "/")
        if isinstance(uzel.get("else"), dict):
            yield from vsechny_akce(uzel["else"].get("actions") or {},
                                    cesta + jmeno + "/else/")


def zkontroluj_kostru(definice, spojeni):
    akce = definice.get("actions") or {}
    for jmeno in ("Vstup", "Cesta_webu", "Site_id", "Web_id", "Disky", "Zdroj",
                  "Disk_kandidati", "Disk", "Soubor", "Radky", "Ocistene",
                  "Prazdne", "S_obsahem", "Chybne", "Uplne", "Neznamy_dilci",
                  "Zarazene", "Duplicitni", "K_zalozeni", "Pouzite_kody",
                  "Zapis", "Chybne_radky", "Prehled", "Odpoved"):
        overit(jmeno in akce, f"chybí akce {jmeno}")

    overit(definice.get("contentVersion") == "1.0.0.0",
           f"contentVersion je {definice.get('contentVersion')!r}")

    trigger = definice.get("triggers") or {}
    prvni = next(iter(trigger.values()), {})
    overit(prvni.get("kind") == "PowerAppV2",
           f"trigger není PowerAppV2, ale {prvni.get('kind')!r}")
    vlastnosti = ((prvni.get("inputs") or {}).get("schema") or {}).get("properties") or {}
    overit(list(vlastnosti) == ["text"],
           f"trigger má vstupy {list(vlastnosti)}, čekám jediný 'text'")

    overit("shared_excelonlinebusiness" in spojeni,
           "flow nemá connection reference na Excel Online — excelová akce by "
           "neměla čím běžet; spojení vzniká v prostředí, ne v generátoru")
    overit("shared_sharepointonline" in spojeni,
           "flow nemá connection reference na SharePoint")
    excel = spojeni.get("shared_excelonlinebusiness") or {}
    overit(excel.get("runtimeSource") == "embedded",
           f"excelové spojení má runtimeSource {excel.get('runtimeSource')!r}; "
           f"s 'invoker' by appka po každém uživateli chtěla vlastní spojení")


def zkontroluj_excel(akce):
    radky = akce.get("Radky") or {}
    dvojice = parametry_akce(radky, "shared_excelonlinebusiness")
    overit(dvojice is not None, "akce Radky nejede přes konektor Excel Online")
    if not dvojice:
        return
    operace, parametry = dvojice
    overit(operace == "GetItems", f"Radky není GetItems, ale {operace!r}")

    overit(parametry.get("table") == TABULKA,
           f"tabulka je {parametry.get('table')!r}, šablona ji jmenuje {TABULKA!r} "
           f"— konektor tabulky vyhledává podle názvu, takže se to musí shodovat")
    for klic in ("source", "drive", "file"):
        hodnota = str(parametry.get(klic, ""))
        overit(hodnota.startswith("@"),
               f"parametr {klic} je natvrdo ({hodnota[:40]!r}) — vázalo by to balík "
               f"na jeden tenant" + (" a na jeden soubor" if klic == "file" else ""))

    # Skládání parametrů za běhu — tohle je to, co dělá balík přenositelným.
    zdroj = str((akce.get("Zdroj") or {}).get("inputs", ""))
    overit("body('Site_id')" in zdroj and "body('Web_id')" in zdroj,
           "source se neskládá ze site id a web id")
    overit(ep.vyraz(ep.WEB) in zdroj,
           f"source nebere hostitele z proměnné {ep.WEB}")

    kandidati = ((akce.get("Disk_kandidati") or {}).get("inputs") or {})
    overit("_api/v2.0/drives" in str((akce.get("Disky") or {}).get("inputs")),
           "drive id se nezjišťuje z /_api/v2.0/drives")
    overit(f"/{KNIHOVNA.lower()}" in str(kandidati.get("where", "")).lower(),
           f"disk se nehledá podle URL segmentu knihovny {KNIHOVNA}")
    overit("webUrl" in str(kandidati.get("where", "")),
           "disk se nehledá podle webUrl — zobrazovaný název nese diakritiku "
           "a mění se přejmenováním, kdežto URL segment je interní název")

    soubor = akce.get("Soubor") or {}
    operace_s, parametry_s = parametry_akce(soubor, "shared_sharepointonline") or (None, {})
    overit(operace_s == "GetFileMetadataByPath",
           f"soubor se nedohledává přes GetFileMetadataByPath, ale {operace_s!r}")
    overit(f"/{KNIHOVNA}/" in str(parametry_s.get("path", "")),
           f"soubor se nečte z knihovny {KNIHOVNA}: {parametry_s.get('path')!r}")


def zkontroluj_ctení_sesitu(akce, sloupce):
    ocistene = ((akce.get("Ocistene") or {}).get("inputs") or {})
    vyber = ocistene.get("select") or {}
    overit("range(0," in str(ocistene.get("from", "")).replace(" ", ""),
           "řádky se neprocházejí přes index — bez něj nejde do výsledku dostat "
           "číslo řádku v sešitě a správce by chybný řádek hledal očima")
    overit(str(vyber.get("radek", "")).startswith("@add(item(), 2"),
           f"číslo řádku není index+2 (hlavička je první řádek): {vyber.get('radek')!r}")

    overit(set(vyber) == {"radek"} | {c["name"] for c in sloupce},
           f"mapování sešitu nesedí na sloupce šablony: "
           f"navíc {sorted(set(vyber) - {'radek'} - {c['name'] for c in sloupce})}, "
           f"chybí {sorted({c['name'] for c in sloupce} - set(vyber))}")
    for sloupec in sloupce:
        hodnota = str(vyber.get(sloupec["name"], ""))
        overit(f"'{sloupec['display']}'" in hodnota,
               f"sloupec {sloupec['name']} se nečte podle hlavičky "
               f"{sloupec['display']!r}: {hodnota[:80]}")
        overit(hodnota.startswith("@trim("),
               f"hodnota sloupce {sloupec['name']} se neořezává — mezera navíc "
               f"by udělala z duplicity nový záznam")


def zkontroluj_rozklad(akce, sloupce):
    povinne = [c["name"] for c in sloupce if c.get("required")]
    overit(bool(povinne), "schéma nemá u aktivit žádný povinný sloupec, "
                          "což by znamenalo, že import nemá co validovat")

    prazdne = str(((akce.get("Prazdne") or {}).get("inputs") or {}).get("where", ""))
    for sloupec in sloupce:
        overit(f"empty(item()?['{sloupec['name']}'])" in prazdne,
               f"prázdnost řádku se neptá na sloupec {sloupec['name']} — řádek "
               f"vyplněný jen v něm by se považoval za prázdný")

    dvojice = (("S_obsahem", "Ocistene"), ("Chybne", "S_obsahem"),
               ("Uplne", "S_obsahem"), ("Neznamy_dilci", "Uplne"),
               ("Zarazene", "Uplne"), ("Duplicitni", "Zarazene"),
               ("K_zalozeni", "Zarazene"))
    for skupina, zdroj in dvojice:
        odkud = str(((akce.get(skupina) or {}).get("inputs") or {}).get("from", ""))
        overit(odkud == f"@body('{zdroj}')",
               f"{skupina} se nepočítá z {zdroj}, ale z {odkud!r} — rozklad by "
               f"se překrýval a čísla v náhledu by nesouhlasila")

    chybne = str(((akce.get("Chybne") or {}).get("inputs") or {}).get("where", ""))
    uplne = str(((akce.get("Uplne") or {}).get("inputs") or {}).get("where", ""))
    for nazev in povinne:
        overit(f"empty(item()?['{nazev}'])" in chybne,
               f"chybné řádky se neptají na povinný sloupec {nazev}")
        overit(f"empty(item()?['{nazev}'])" in uplne,
               f"úplné řádky se neptají na povinný sloupec {nazev}")
    overit(chybne.startswith("@not(") and not uplne.startswith("@not("),
           "Chybne a Uplne nejsou vzájemným doplňkem, takže rozklad není úplný")

    klic = f"'{SPOJKA_VAZBY}'"
    for skupina in ("Duplicitni", "K_zalozeni"):
        kde = str(((akce.get(skupina) or {}).get("inputs") or {}).get("where", ""))
        overit("body('Klice_aktivit')" in kde and klic in kde,
               f"{skupina} nepoznává duplicitu podle dvojice dílčí proces + název")
    overit(str(((akce.get("K_zalozeni") or {}).get("inputs") or {})
               .get("where", "")).startswith("@not("),
           "K_zalozeni není doplňkem duplicit — duplicity by se zakládaly znovu")

    for jmeno in (LIST_DILCI, LIST_AKTIVITY):
        uzel = akce.get(f"Nacti_{jmeno}") or {}
        strankovani = ((uzel.get("runtimeConfiguration") or {})
                       .get("paginationPolicy") or {}).get("minimumItemCount")
        overit(strankovani == STRANKOVANI,
               f"Nacti_{jmeno} nemá stránkování {STRANKOVANI} — nad 100 řádky by "
               f"import neviděl existující záznamy a zakládal duplicity")


def zkontroluj_zapis(akce, sloupce):
    zapis = akce.get("Zapis") or {}
    overit(zapis.get("type") == "If",
           "zápisy nejsou v podmínce — náhled by rovnou zakládal")
    overit(REZIM_ZAPIS in text(zapis.get("expression")),
           f"podmínka zápisu se neptá na režim {REZIM_ZAPIS!r}")

    for cesta, uzel in vsechny_akce(akce):
        dvojice = parametry_akce(uzel, "shared_sharepointonline")
        if not dvojice:
            continue
        operace, parametry = dvojice
        overit(operace not in MAZACI, f"{cesta}: mazací operace {operace} — import nemaže")
        if operace != "HttpRequest":
            continue
        metoda = str(parametry.get("parameters/method", "")).upper()
        if metoda in ("POST", "PATCH", "PUT", "MERGE"):
            overit(cesta.startswith("Zapis/"),
                   f"{cesta}: zápis leží mimo podmínku Zapis, proběhl by i v náhledu")

    smycka = (zapis.get("actions") or {}).get("Zaloz") or {}
    overit(smycka.get("type") == "Foreach", "chybí smyčka Zaloz")
    overit(smycka.get("foreach") == "@body('K_zalozeni')",
           f"smyčka nejede přes K_zalozeni, ale {smycka.get('foreach')!r} — "
           f"zakládaly by se i duplicitní nebo chybné řádky")
    soubeznost = ((smycka.get("runtimeConfiguration") or {})
                  .get("concurrency") or {}).get("repetitions")
    overit(soubeznost == 1,
           f"smyčka má souběžnost {soubeznost}, čekám 1 — kódy se přidělují ze "
           f"sdílené proměnné, takže paralelní průchody dají dvěma aktivitám týž kód")

    vnitrek = smycka.get("actions") or {}
    for jmeno in ("Sourozenci", "Cisla", "Novy_kod", "Vloz_aktivitu",
                  "Vloz_vazbu", "Zapamatuj_kod"):
        overit(jmeno in vnitrek, f"ve smyčce chybí akce {jmeno}")

    promenna = (akce.get("Pouzite_kody") or {}).get("inputs") or {}
    overit(promenna.get("variables", [{}])[0].get("value") == "@body('Kody_aktivit')",
           "proměnná použitých kódů se neplní existujícími kódy z listu")
    overit(str(((vnitrek.get("Sourozenci") or {}).get("inputs") or {})
               .get("from", "")) == "@variables('pouziteKody')",
           "sourozenci se hledají jinde než v proměnné použitých kódů, takže kód "
           "přidělený o řádek dřív by se nezapočítal")
    overit((vnitrek.get("Zapamatuj_kod") or {}).get("type") == "AppendToArrayVariable",
           "nově přidělený kód se nezapamatuje")
    overit("Vloz_vazbu" in text((vnitrek.get("Zapamatuj_kod") or {}).get("runAfter")),
           "kód se zapamatuje dřív, než je řádek opravdu zapsaný")

    novy_kod = str((vnitrek.get("Novy_kod") or {}).get("inputs", ""))
    overit("if(empty(body('Cisla')), 0" in novy_kod,
           "přidělení kódu nepočítá s tím, že dílčí proces zatím žádnou aktivitu "
           "nemá — max() nad prázdným polem spadne")
    overit("max(body('Cisla'))" in novy_kod,
           "nový kód se neodvozuje z nejvyššího dosud použitého čísla")
    overit("'000'" in novy_kod and ", 4)" in novy_kod,
           "pořadové číslo se nedoplňuje nulami na čtyři místa")

    zkontroluj_telo(vnitrek, sloupce)


def zkontroluj_telo(vnitrek, sloupce):
    telo = (((vnitrek.get("Vloz_aktivitu") or {}).get("inputs") or {})
            .get("parameters") or {}).get("parameters/body") or {}
    ocekavane = {"Title", "datum_aktualizace"} | {c["name"] for c in sloupce}
    overit(set(telo) == ocekavane,
           f"tělo zakládané aktivity nesedí: navíc {sorted(set(telo) - ocekavane)}, "
           f"chybí {sorted(ocekavane - set(telo))}")
    overit(DOPOCITAVANE not in telo,
           f"import zapisuje {DOPOCITAVANE}, který dopočítává "
           f"AktualizaceKratkehoNazvu — přepisovali by se navzájem")
    overit(telo.get("Title") == "@outputs('Novy_kod')",
           f"kód aktivity se nebere z přiděleného kódu: {telo.get('Title')!r}")
    overit("utcNow()" in str(telo.get("datum_aktualizace", "")),
           "datum aktualizace není razítko importu")
    overit(VYCHOZI_STAV in str(telo.get("stav", "")),
           f"nevyplněný stav se nedoplňuje na {VYCHOZI_STAV!r}")

    vazba = (((vnitrek.get("Vloz_vazbu") or {}).get("inputs") or {})
             .get("parameters") or {}).get("parameters/body") or {}
    overit(set(vazba) == {"Title", "aktivita_kod", "dilci_proces_kod", "primarni"},
           f"tělo vazby nesedí: {sorted(vazba)}")
    overit(f"'{SPOJKA_VAZBY}'" in str(vazba.get("Title", "")),
           f"klíč vazby se neskládá spojkou {SPOJKA_VAZBY!r} — appka zakládá vazby "
           f"v tomhle tvaru a jiný by vyrobil duplicity, které nenajde")
    overit(vazba.get("aktivita_kod") == "@outputs('Novy_kod')",
           "vazba neukazuje na právě založenou aktivitu")
    overit(vazba.get("primarni") == "ano",
           "vazba z importu není primární, ačkoli aktivita jiné zařazení nemá")

    for jmeno, uri in (("Vloz_aktivitu", LIST_AKTIVITY), ("Vloz_vazbu", LIST_VAZBY)):
        adresa = str((((vnitrek.get(jmeno) or {}).get("inputs") or {})
                      .get("parameters") or {}).get("parameters/uri", ""))
        overit(f"/Lists/{uri}" in adresa,
               f"{jmeno} neadresuje list interním názvem {uri}: {adresa[:80]}")
        overit(not re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-", adresa),
               f"{jmeno} má v adrese GUID vázaný na jeden tenant")


def zkontroluj_prenositelnost(flow):
    cely = text(flow)
    adresy = sorted(set(re.findall(r"[A-Za-z0-9-]+\.sharepoint\.com", cely)))
    overit(not adresy, f"v definici je adresa SharePointu: {adresy}")
    overit("b!" not in cely,
           "v definici je Graph drive id (b!…) — to je vázané na jednu knihovnu "
           "na jednom tenantu a musí se zjišťovat za běhu")
    # Hledá se hotové Graph site id (`sites/<host>,<guid>,<guid>`), ne holé
    # 'sites/' — to je legitimní kus výrazu, kterým se id skládá za běhu.
    hotove = re.findall(r"sites/[^'\",]+,[0-9a-fA-F-]{36},[0-9a-fA-F-]{36}", cely)
    overit(not hotove, f"v definici je natvrdo Graph site id: {hotove[:1]}")


def zkontroluj_odpoved(akce):
    odpoved = akce.get("Odpoved") or {}
    overit(odpoved.get("kind") == "PowerApp", "odpověď není typu PowerApp")
    vlastnosti = ((odpoved.get("inputs") or {}).get("schema") or {}).get("properties") or {}
    overit(set(vlastnosti) == {"stav", "soubor", "prehled", "chyby"},
           f"schéma odpovědi je {sorted(vlastnosti)} — mění-li se, přestane appce "
           f"sedět a flow se musí znovu registrovat ve Studiu")
    for jmeno, typ in vlastnosti.items():
        overit(typ.get("type") == "string", f"pole odpovědi {jmeno} není string")

    prehled = text((akce.get("Prehled") or {}).get("inputs"))
    for skupina in ("Prazdne", "K_zalozeni", "Duplicitni", "Chybne", "Neznamy_dilci"):
        overit(f"body('{skupina}')" in prehled,
               f"přehled nezmiňuje skupinu {skupina}")


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
    overit(FLOW_GUID.upper() in klice[0], f"soubor flow nenese očekávané GUID: {klice[0]}")

    flow = json.loads(polozky[klice[0]].decode("utf-8-sig"))
    definice = flow["properties"]["definition"]
    akce = definice.get("actions") or {}
    sloupce = sloupce_sablony(nacti_schema())

    zkontroluj_kostru(definice, flow["properties"].get("connectionReferences") or {})
    zkontroluj_excel(akce)
    zkontroluj_ctení_sesitu(akce, sloupce)
    zkontroluj_rozklad(akce, sloupce)
    zkontroluj_zapis(akce, sloupce)
    zkontroluj_odpoved(akce)
    zkontroluj_prenositelnost(flow)

    return vypis()


def vypis():
    print(f"kontrol: {kontrol}")
    for chyba in chyby:
        print(f"CHYBA: {chyba}")
    print("NEPROŠLO" if chyby else f"OK — {FLOW} zakládá jen ověřené řádky")
    return 1 if chyby else 0


if __name__ == "__main__":
    sys.exit(main())
