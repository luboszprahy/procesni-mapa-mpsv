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
                               KOD_NEZARAZENO, KOD_RODICE_SLOUPEC,
                               ODD_POLE, ODD_RADKU, POCTY,
                               REZIM_SEZNAM, REZIM_ZAPIS, SPOJKA_VAZBY,
                               STRANKOVANI, TABULKA,
                               VYCHOZI_STAV, UROVNE_VLASTNIKU,
                               NEZARAZENY_PREFIX,
                               nacti_schema, sloupce_sablony,
                               sloupce_vlastniku)

chyby = []
kontrol = 0

MAZACI = ("DeleteItem", "DeleteFile", "RecycleItem", "RecycleFile")
# Sloupec, jehož PŘESNOU podobu (řez na hranici slova s výpustkou) počítá
# AktualizaceKratkehoNazvu. Import ho od 08.09.2026 zapisuje taky, ale jen
# hrubě useknutý — jinak by mezi importem a během toho flow (polling po
# minutě) měly čerstvé aktivity krátký název prázdný, a Přehled zobrazuje
# právě jeho. Nález z provozu: naimportované řádky vypadaly bez názvu.
#
# Obava, že se ta dvě místa budou přepisovat, neplatí: `Cil` se ve flow
# počítá výhradně z `nazev`, ne z `nazev_kratky`, takže výsledek je
# deterministický a podmínka `Lisi_se` po jednom přepisu utichne. U názvů
# do MAXLEN znaků vyjde hrubý ořez rovnou stejně a flow nezapíše vůbec nic.
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
                  "Rezim_seznam", "Prazdne", "S_obsahem", "Doplneny_rodic",
                  "Chybne", "Uplne", "Nezarazene",
                  "Neznamy_dilci", "Kody_utvaru",
                  "Chybne_povinne", "Chybne_utvar", "Popis_utvar",
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

    # Sloupce vlastníků nadřazených úrovní nejsou ve schématu listu Aktivity,
    # ale ze sešitu se číst MUSÍ — jinak by import mlčky nezapsal nic.
    ocekavane = ({"radek"} | {c["name"] for c in sloupce}
                 | {c["name"] for c in sloupce_vlastniku()})
    overit(set(vyber) == ocekavane,
           f"mapování sešitu nesedí na sloupce šablony: "
           f"navíc {sorted(set(vyber) - ocekavane)}, "
           f"chybí {sorted(ocekavane - set(vyber))}")
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

    dvojice = (("S_obsahem", "Ocistene"), ("Doplneny_rodic", "S_obsahem"),
               ("Chybne", "Doplneny_rodic"), ("Uplne", "Doplneny_rodic"),
               ("Neznamy_dilci", "Uplne"), ("Zarazene", "Uplne"),
               ("Duplicitni", "Zarazene"), ("K_zalozeni", "Zarazene"),
               ("Nezarazene", "K_zalozeni"))
    for skupina, zdroj in dvojice:
        odkud = str(((akce.get(skupina) or {}).get("inputs") or {}).get("from", ""))
        overit(odkud == f"@body('{zdroj}')",
               f"{skupina} se nepočítá z {zdroj}, ale z {odkud!r} — rozklad by "
               f"se překrýval a čísla v náhledu by nesouhlasila")

    chybne = str(((akce.get("Chybne") or {}).get("inputs") or {}).get("where", ""))
    uplne = str(((akce.get("Uplne") or {}).get("inputs") or {}).get("where", ""))

    # Útvar mimo číselník nesmí projít. Šablona ho nezachytí: sloupce
    # připouštějí víc útvarů oddělených „; " a seznamová validace Excelu by
    # takovou hodnotu odmítla, takže rozbalovátko tam je jen nabídka.
    # Kontrola je proto tady jediná — kdyby vypadla, překlep by se dostal
    # do dat a poznal by se až v appce jako prázdný vlastník.
    #
    # `spolupracuje` se schválně nekontroluje: v evidenčních kartách je to
    # volný text („věcně příslušné útvary MPSV"). Kdyby ho někdo do seznamu
    # přidal, import by odmítl řádky, které jsou v pořádku.
    for nazev in ("vykonava", "_vlastnik_agendy", "_vlastnik_procesu",
                  "_vlastnik_dilciho"):
        overit(f"item()?['{nazev}']" in chybne and "Kody_utvaru" in chybne,
               f"vadné řádky se neptají, jestli je útvar ve sloupci {nazev} "
               f"v číselníku — překlep by prošel až do dat")
        overit(f"item()?['{nazev}']" in uplne and "Kody_utvaru" in uplne,
               f"úplné řádky se neptají na útvar ve sloupci {nazev}")
    overit("item()?['spolupracuje']" not in chybne,
           "import kontroluje útvary ve 'spolupracuje', kde je ale legitimně "
           "volný text — odmítal by řádky, které jsou v pořádku")

    # Prázdný útvar je legitimní (vlastník se nemění) a split('') vrátí [''],
    # takže bez prázdného řetězce v číselníku by propadl každý takový řádek.
    kody = str(((akce.get("Kody_utvaru") or {}).get("inputs") or {}).get("from", ""))
    overit('"Title": ""' in kody or "'Title': ''" in kody,
           "mezi platné kódy útvarů se nepřidává prázdno — řádek s nevyplněným "
           "vlastníkem by import odmítl jako vadný")

    # Dvě příčiny vadného řádku se musí dát rozlišit v hlášce, jinak správce
    # hledá chybějící název tam, kde je překlep v útvaru.
    for skupina, zdroj in (("Chybne_povinne", "Chybne"), ("Chybne_utvar", "Chybne")):
        odkud = str(((akce.get(skupina) or {}).get("inputs") or {}).get("from", ""))
        overit(odkud == f"@body('{zdroj}')",
               f"{skupina} se nepočítá z {zdroj}, ale z {odkud!r}")
    radky = str(((akce.get("Chybne_radky") or {}).get("inputs") or ""))
    overit("body('Popis_utvar')" in radky,
           "hlášení chyb nezahrnuje řádky s neznámým útvarem — import je "
           "odmítne, ale správce se to nedozví")
    for nazev in povinne:
        overit(f"empty(item()?['{nazev}'])" in chybne,
               f"chybné řádky se neptají na povinný sloupec {nazev}")
        overit(f"empty(item()?['{nazev}'])" in uplne,
               f"úplné řádky se neptají na povinný sloupec {nazev}")
    overit(chybne.startswith("@not(") and not uplne.startswith("@not("),
           "Chybne a Uplne nejsou vzájemným doplňkem, takže rozklad není úplný")

    # Dosazení technického rodiče u aktivit nahraných bez zařazení.
    #
    # Nejdůležitější kontrola celého kroku je POŘADÍ: náhrada smí přijít až za
    # `S_obsahem`. Kdyby běžela nad `Ocistene`, přestaly by být prázdné řádky
    # prázdné a šablona by při každém importu založila dvě stě sirotků
    # z prázdných řádků pod Tabulkou.
    doplneny = (akce.get("Doplneny_rodic") or {}).get("inputs") or {}
    overit(str(doplneny.get("from")) == "@body('S_obsahem')",
           "technický rodič se dosazuje z jiného kroku než S_obsahem — nad "
           "Ocistene by se prázdné řádky změnily na sirotky")
    po_cem = list(((akce.get("Doplneny_rodic") or {}).get("runAfter") or {}))
    overit(po_cem == ["S_obsahem"],
           f"Doplneny_rodic běží po {po_cem}, musí po S_obsahem")

    # Vlastníci PATŘÍ do výčtu. Do 08.09.2026 tu stálo jen `sloupce`, tedy
    # přesně to, co generátor dělal — a brána tím vadu potvrzovala jako
    # správný stav: `_vlastnik_*` z proudu vypadli a import od F16 nikdy
    # žádného vlastníka nezapsal. Brána psaná podle chování kódu, ne podle
    # zadání, chybu neodhalí; ověřuje leda to, že se kód nezměnil.
    vyber = (doplneny.get("select") or {})
    overit(isinstance(vyber, dict) and set(vyber) ==
           {"radek"} | {c["name"] for c in sloupce + sloupce_vlastniku()},
           "dosazení rodiče nezachovává všechny sloupce řádku — co v Select "
           "chybí, to se ztratí i pro zápis")
    kod = str(vyber.get(KOD_RODICE_SLOUPEC, ""))
    overit(f"empty(item()?['{KOD_RODICE_SLOUPEC}'])" in kod
           and f"'{KOD_NEZARAZENO}'" in kod,
           f"prázdný {KOD_RODICE_SLOUPEC} se nenahrazuje kódem "
           f"{KOD_NEZARAZENO}: {kod[:80]}")
    for sloupec in sloupce:
        if sloupec["name"] == KOD_RODICE_SLOUPEC:
            continue
        overit(str(vyber.get(sloupec["name"], "")) ==
               f"@item()?['{sloupec['name']}']",
               f"sloupec {sloupec['name']} se při dosazení rodiče mění, "
               f"ačkoli má projít beze změny")

    nezarazene = str(((akce.get("Nezarazene") or {}).get("inputs") or {}).get("where", ""))
    overit(f"'{KOD_NEZARAZENO}'" in nezarazene,
           "počet nezařazených se nepočítá podle kódu technického rodiče")

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
    ocekavane = ({"Title", "datum_aktualizace", DOPOCITAVANE}
                 | {c["name"] for c in sloupce})
    overit(set(telo) == ocekavane,
           f"tělo zakládané aktivity nesedí: navíc {sorted(set(telo) - ocekavane)}, "
           f"chybí {sorted(ocekavane - set(telo))}")
    # Hrubý ořez se musí odvozovat z `nazev` a smí ho jen zkrátit. Kdyby
    # vznikal z něčeho jiného, přestal by být deterministický a `Lisi_se`
    # v druhém flow by ho přepisovalo pořád dokola.
    vyraz = str(telo.get(DOPOCITAVANE, ""))
    overit("['nazev']" in vyraz,
           f"{DOPOCITAVANE} se v importu neodvozuje z 'nazev' — jiný zdroj by "
           f"AktualizaceKratkehoNazvu přepisovalo při každé změně dokola")
    overit("substring" in vyraz and "length" in vyraz,
           f"{DOPOCITAVANE} se v importu nezkracuje — dlouhý název by zápis "
           f"shodil na délce sloupce")
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


def zkontroluj_vlastniky(akce):
    """Vlastníci nadřazených úrovní: rozpor se hlásí, zápis je MERGE.

    Nejdražší past téhle funkce je tichost: kdyby se rozpor jen odfiltroval,
    import by doběhl zeleně a v rejstříku by nic nepřibylo. Proto se kontroluje
    obojí — že se rozporné kódy nezapisují A že se objeví mezi chybami.
    """
    popisy_v_chybach = text((akce.get("Chybne_radky") or {}).get("inputs"))
    # Zápisové smyčky leží uvnitř větve `Zapis`, na nejvyšší úrovni nejsou.
    ploche = {jmeno.split("/")[-1]: uzel for jmeno, uzel in vsechny_akce(akce)}

    for uroven in UROVNE_VLASTNIKU:
        k = uroven["klic"]

        vybrane = akce.get(f"S_vlastnikem_{k}")
        overit(vybrane is not None, f"chybí krok S_vlastnikem_{k}")
        if vybrane:
            kde = text(vybrane["inputs"].get("where"))
            overit(f"item()?['{uroven['sloupec']}']" in kde,
                   f"S_vlastnikem_{k} nefiltruje podle sloupce "
                   f"{uroven['sloupec']} (je tam {kde!r})")
            # Nezařazené aktivity visí pod technickým rodičem 00-00-000;
            # vlastník se k němu připsat nesmí, není to skutečná agenda.
            overit(NEZARAZENY_PREFIX in kde,
                   f"S_vlastnikem_{k} nevylučuje nezařazené aktivity — vlastník "
                   f"by se zapsal technické agendě {NEZARAZENY_PREFIX}")

        klice = akce.get(f"Klice_{k}")
        overit(klice is not None, f"chybí krok Klice_{k}")
        if klice:
            vyraz = text(klice["inputs"].get("select"))
            overit(f"0, {uroven['delka']})" in vyraz.replace("  ", " "),
                   f"Klice_{k} neodvozuje kód rodiče prvními {uroven['delka']} "
                   f"znaky kódu dílčího procesu: {vyraz!r}")

        unikatni = akce.get(f"Unikatni_{k}")
        overit(unikatni is not None and "union(" in text(unikatni.get("inputs")),
               f"Unikatni_{k} nezahazuje duplicity přes union — každý řádek "
               f"sešitu by se počítal jako další vlastník a rozpor by hlásil "
               f"i shodně vyplněná agenda")

        rozpor = akce.get(f"Rozpor_{k}")
        k_zapisu = akce.get(f"K_zapisu_{k}")
        overit(rozpor is not None, f"chybí krok Rozpor_{k}")
        overit(k_zapisu is not None, f"chybí krok K_zapisu_{k}")
        if rozpor and k_zapisu:
            overit("greater(" in text(rozpor["inputs"].get("where")),
                   f"Rozpor_{k} nehledá kódy s víc než jedním vlastníkem")
            overit("equals(" in text(k_zapisu["inputs"].get("where")),
                   f"K_zapisu_{k} nezapisuje jen kódy s právě jedním vlastníkem "
                   f"— rozporné by se zapsaly podle pořadí řádků")

        overit(f"Popis_rozpor_{k}" in popisy_v_chybach,
               f"rozpory úrovně '{uroven['popis']}' se nedostanou do seznamu "
               f"chyb — import by je mlčky přeskočil")

        popis = akce.get(f"Popis_rozpor_{k}")
        if popis:
            overit(uroven["popis"] in text(popis["inputs"].get("select")),
                   f"Popis_rozpor_{k} neříká, které úrovně se rozpor týká")

        # zápis
        smycka = ploche.get(f"Zapis_vlastniku_{k}")
        overit(smycka is not None, f"chybí zápisová smyčka Zapis_vlastniku_{k}")
        if smycka:
            overit(f"K_zapisu_{k}" in text(smycka.get("foreach")),
                   f"Zapis_vlastniku_{k} nejde přes K_zapisu_{k} — zapsaly by "
                   f"se i rozporné kódy")
            vnitrek = smycka.get("actions") or {}
            uloz = vnitrek.get(f"Pokud_existuje_{k}", {}).get(
                "actions", {}).get(f"Uloz_vlastnika_{k}")
            overit(uloz is not None,
                   f"chybí akce Uloz_vlastnika_{k} uvnitř podmínky na existenci")
            if uloz:
                parametry = uloz["inputs"]["parameters"]
                hlavicky = parametry.get("parameters/headers") or {}
                overit(uloz["inputs"]["host"]["operationId"] == "HttpRequest",
                       f"Uloz_vlastnika_{k} nezapisuje přes REST")
                overit(str(hlavicky.get("X-HTTP-Method", "")).upper() == "MERGE",
                       f"Uloz_vlastnika_{k} nemá MERGE — POST by k agendě "
                       f"založil další řádek místo změny vlastníka")
                telo = parametry.get("parameters/body")
                overit(isinstance(telo, dict) and set(telo) == {"vlastnik"},
                       f"Uloz_vlastnika_{k} mění víc než sloupec vlastnik: "
                       f"{sorted(telo) if isinstance(telo, dict) else telo!r}")
                overit(f"/Lists/{uroven['list']}" in text(
                           parametry.get("parameters/uri")),
                       f"Uloz_vlastnika_{k} nemíří na list {uroven['list']}")

        nacti = akce.get(f"Nacti_{uroven['list']}")
        overit(nacti is not None,
               f"chybí Nacti_{uroven['list']} — bez načteného listu se nedá "
               f"dohledat ID položky, ke které se vlastník zapisuje")


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

    # Obrazovka náhledu bere čísla podle POŘADÍ — oddělovaný text jméno pole
    # nenese. Kdyby se pořadí změnilo, appka by tiše ukázala čísla v jiných
    # sloupcích a nikdo by si toho nevšiml, protože jsou to malá celá čísla.
    prehled = str((akce.get("Prehled") or {}).get("inputs", ""))
    poradi = re.findall(r"body\('([^']+)'\)", prehled)
    overit(tuple(poradi) == tuple(POCTY),
           f"přehled má skupiny v pořadí {poradi}, kontrakt je {list(POCTY)}")
    overit(prehled.count(f"'{ODD_POLE}'") == len(POCTY) - 1,
           f"přehled neodděluje čísla oddělovačem {ODD_POLE!r}")

    chybne = str((akce.get("Chybne_radky") or {}).get("inputs", ""))
    overit(chybne.startswith("@join(") and f"'{ODD_RADKU}'" in chybne,
           f"chybné řádky nejsou spojené oddělovačem {ODD_RADKU!r}: {chybne[:60]}")
    for jmeno in ("Popis_chybne", "Popis_neznamy"):
        radek = str(((akce.get(jmeno) or {}).get("inputs") or {}).get("select", ""))
        overit(radek.count(f"'{ODD_POLE}'") == 2,
               f"{jmeno} nemá tři pole (řádek, název, důvod) oddělená {ODD_POLE!r}")
        overit("item()?['radek']" in radek,
               f"{jmeno} nenese číslo řádku v sešitě")


def zkontroluj_seznam(akce):
    """Režim, kterým si appka řekne o seznam sešitů v knihovně.

    Existuje proto, že appka knihovnu `Import` připojenou nemá a připojit ji
    jde jedině ve Studiu, tedy dalším kolem. Dvě věci na tom musí sedět:
    běh se po odpovědi MUSÍ ukončit (jinak by se pokračovalo dohledáváním
    souboru, který nikdo nezadal), a schéma odpovědi musí zůstat totožné se
    schématem hlavní odpovědi — jinak by flow přestalo appce sedět a muselo
    by se znovu registrovat.
    """
    uzel = akce.get("Rezim_seznam") or {}
    overit(uzel.get("type") == "If", "režim seznamu není podmínka")
    overit(REZIM_SEZNAM in text(uzel.get("expression")),
           f"podmínka se neptá na režim {REZIM_SEZNAM!r}")
    vnitrek = uzel.get("actions") or {}
    for jmeno in ("Soubory", "Jmena", "Odpoved_seznam", "Konec"):
        overit(jmeno in vnitrek, f"v režimu seznamu chybí akce {jmeno}")

    overit((vnitrek.get("Konec") or {}).get("type") == "Terminate",
           "režim seznamu neukončuje běh — pokračovalo by se dohledáváním "
           "souboru, jehož název v tomhle režimu nikdo nezadal")

    uri = str((((vnitrek.get("Soubory") or {}).get("inputs") or {})
               .get("parameters") or {}).get("parameters/uri", ""))
    overit(f"/{KNIHOVNA}" in uri, f"seznam se nečte z knihovny {KNIHOVNA}: {uri[:70]}")
    overit("FileLeafRef" in uri, "seznam nevybírá název souboru (FileLeafRef)")

    hlavni = (((akce.get("Odpoved") or {}).get("inputs") or {})
              .get("schema") or {}).get("properties") or {}
    seznamova = (((vnitrek.get("Odpoved_seznam") or {}).get("inputs") or {})
                 .get("schema") or {}).get("properties") or {}
    overit(set(hlavni) == set(seznamova) and set(hlavni),
           f"schéma odpovědi seznamu ({sorted(seznamova)}) se liší od hlavní "
           f"odpovědi ({sorted(hlavni)}) — appka by jedno z nich nepřečetla")


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
    zkontroluj_vlastniky(akce)
    zkontroluj_rozklad(akce, sloupce)
    zkontroluj_zapis(akce, sloupce)
    zkontroluj_seznam(akce)
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
