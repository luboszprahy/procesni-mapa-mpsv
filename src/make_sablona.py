# -*- coding: utf-8 -*-
"""Generátor šablony pro hromadný import aktivit.

Ze `src/schema.json` vyrobí `runs/build/sablona_import_aktivit.xlsx` — sešit, který
správce procesního rámce vyplní a nahraje do knihovny `Import`. Čte ho konektor
Excel Online (Business) akcí `List rows present in a table`, a ta umí jen
**formátovanou Tabulku**, ne volnou mřížku; proto se hlavička zakládá jako
`Table`, ne jen jako tučný první řádek.

Generuje se, aby se nemohla rozejít se schématem listu Aktivity. Sloupce, které
si systém drží sám, v šabloně NEJSOU:

    Title             identifikační kód — přiděluje ho appka, ne správce
    nazev_kratky      odvozený ze sloupce nazev
    datum_aktualizace razítko importu
    puvodni_kod       stopa po přesunu pod jiného rodiče

Vedlejší zařazení aktivity (M:N) šablona nenese — import zakládá aktivitu
s primárním dílčím procesem a další zařazení se přidávají v appce.

Spouštět z kořene projektu:
    python src/make_sablona.py
"""

import argparse
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

SCHEMA = Path("src/schema.json")
VYSTUP = Path("runs/build/sablona_import_aktivit.xlsx")

LIST = "Aktivity"          # list schématu, ze kterého se šablona staví
TABULKA = "Aktivity"       # jméno Tabulky — na něj se odkazuje ImportFlow
LIST_POKYNY = "Pokyny"
LIST_CISELNIKY = "Ciselniky"

MODEL = Path("runs/normalize/model.json")
UTVARY = Path("runs/normalize/utvary.csv")

# Pomocný sloupec: slouží JEN k zúžení nabídky dílčích procesů, do rejstříku
# se neimportuje. Flow čte sloupce podle schématu listu Aktivity, takže o něm
# neví a přeskočí ho — proto tu smí být, aniž by se sahalo do schématu.
POMOCNY_PROCES = {
    "name": "_proces",
    "display": "Proces",
    "type": "Text",
    "pomocny": True,
}

# Vlastníci nadřazených úrovní. Do listu Aktivity nepatří (ten je o aktivitě),
# ale importovat je potřeba — sekce je vyplňuje spolu s aktivitami a nemá jinou
# cestu než appku. Import je zapíše k příslušné agendě, procesu a dílčímu
# procesu, které si odvodí z kódu dílčího procesu na témž řádku.
#
# Cena té volby (rozhodl uživatel 06.09.2026): hodnota se opakuje na každém
# řádku téže agendy, takže si dva řádky mohou odporovat. Import to musí
# OHLÁSIT, ne tiše přepsat — viz `Rozpory_vlastniku` v build_import_flow.py.
VLASTNICI_NADRAZENYCH = [
    {"name": "_vlastnik_agendy", "display": "Vlastník agendy",
     "type": "Text", "pomocny": True, "uroven": "agenda", "delka_kodu": 2},
    {"name": "_vlastnik_procesu", "display": "Vlastník procesu",
     "type": "Text", "pomocny": True, "uroven": "proces", "delka_kodu": 5},
    {"name": "_vlastnik_dilciho", "display": "Vlastník dílčího procesu",
     "type": "Text", "pomocny": True, "uroven": "dilci_proces", "delka_kodu": 9},
]

# Kolik řádků číselníkových tabulek se založí. Rozsah validace musí být stálý,
# proto se nepočítá z dat, ale drží se na stropu — dokud se do něj číselník
# vejde, může ho refresh přepisovat bez zásahu do šablony.
STROP_CISELNIKU = {"procesy": 200, "dilci_procesy": 600, "utvary": 200}

# Sloupce, které plní systém. Klíčem je interní název ve schématu.
SYSTEMOVE = {
    "Title": "identifikační kód přiděluje appka",
    "nazev_kratky": "odvozuje se z názvu",
    "datum_aktualizace": "razítko importu",
    "puvodni_kod": "stopa po přesunu pod jiného rodiče",
}

# Nápověda pro správce. Schéma nese vývojářské popisy bez diakritiky, tohle je
# text pro člověka, který sešit vyplňuje. Brána hlídá, že slovník pokrývá
# přesně sloupce šablony — po přidání sloupce do schématu build spadne, dokud
# se nápověda nedopíše.
NAPOVEDA = {
    "nazev": "Úplné znění činnosti tak, jak má stát v organizačním řádu.",
    "_proces": "Pomocný sloupec — vyberte proces a nabídka dílčích procesů "
               "vedle se zúží jen na ty jeho. Do rejstříku se neimportuje.",
    "dilci_proces_kod": "Vyberte z nabídky (zúží ji sloupec Proces vlevo). "
                        "Můžete nechat PRÁZDNÉ — aktivita se pak založí jako "
                        "nezařazená a přiřadíte ji až v aplikaci. "
                        "Neexistující kód import odmítne.",
    "vykonava": "Oddělení, které činnost vykonává. Více útvarů oddělte '; '.",
    "spolupracuje": "Útvary, které se na činnosti podílejí. Více útvarů oddělte '; '.",
    "vnitrni_predpis": "Předpis, ze kterého činnost plyne. Více předpisů oddělte '; '.",
    "text_pro_or": "Nepovinné. Znění pro organizační řád, pokud se liší od názvu; "
                   "jinak nechte prázdné a doplňte později v aplikaci.",
    "sekce": "Číslo sekce, pod kterou činnost spadá.",
    "stav": "Nevyplněno = pracovní. 'schváleno' použijte jen u činností, "
            "které už prošly schválením.",
    "_vlastnik_agendy": "Vlastník AGENDY, ne aktivity — kód sekce. Více "
                        "oddělte '; '. Prázdné = vlastník se nemění. Vyplňujete "
                        "ho u každého řádku téže agendy, takže musí být všude "
                        "stejný; jinak import ohlásí rozpor a nic nezapíše.",
    "_vlastnik_procesu": "Vlastník PROCESU — kód odboru. Více oddělte '; '. "
                         "Prázdné = nemění se. Platí totéž o shodě napříč řádky "
                         "téhož procesu.",
    "_vlastnik_dilciho": "Vlastník DÍLČÍHO PROCESU — kód odboru. Více oddělte "
                         "'; '. Prázdné = nemění se. Platí totéž o shodě napříč "
                         "řádky téhož dílčího procesu.",
}

# Kolik prazdnych radku ma Tabulka mit hned pri zalozeni.
#
# Duvod je nalez z provozu (02.09.2026): sesit s jednim datovym radkem svadi
# k tomu, napsat aktivity nekam nize - a radky MIMO Tabulku konektor Excelu
# vubec nevidi. Import pak hlasi prazdny sesit a vypada to jako vada flow.
# Excel rozsiruje Tabulku sam jen tehdy, kdyz se pise do radku tesne pod ni.
#
# 200 je zaroven bezpecne pod limitem akce `List rows present in a table`,
# ktera bez strankovani vraci nejvyse 256 radku.
DATOVYCH_RADKU = 200

SIRKA_PODLE_TYPU = {"Note": 42, "Choice": 14}
HLAVICKA_VYSKA = 30
POSLEDNI_RADEK_KONTROLY = 1000


def nacti_schema(cesta=SCHEMA):
    return json.loads(Path(cesta).read_text(encoding="utf-8"))


def sloupce_sablony(schema):
    """Sloupce listu Aktivity minus systémové, v pořadí ze schématu."""
    listy = [l for l in schema["lists"] if l["name"] == LIST]
    if len(listy) != 1:
        raise SystemExit(f"CHYBA: ve schématu není právě jeden list {LIST}")
    return [c for c in listy[0]["columns"] if c["name"] not in SYSTEMOVE]


def sloupce_sesitu(schema):
    """Sloupce tak, jak stojí v sešitě — se vloženým pomocným sloupcem.

    Pomocný `Proces` stojí těsně před dílčím procesem: vybere se nejdřív
    proces a nabídka dílčích procesů se tím zúží z dvou set padesáti na
    jednotky. Bez toho je rozbalovátko k nepoužití — Excel v něm neumí hledat,
    jen rolovat.
    """
    vysledek = []
    for sloupec in sloupce_sablony(schema):
        if sloupec["name"] == "dilci_proces_kod":
            vysledek.append(POMOCNY_PROCES)
        vysledek.append(sloupec)
    # Vlastníci nadřazených úrovní až na konci: patří k jiné úrovni než zbytek
    # řádku a uprostřed by mátli. Kdo je nevyplní, nechá je prázdné a import
    # se jich nedotkne.
    return vysledek + VLASTNICI_NADRAZENYCH


def jmeno_rozsahu(kod_procesu):
    """Kód procesu na jméno pojmenovaného rozsahu (Excel nesnese pomlčky)."""
    return "P_" + kod_procesu.replace("-", "_")


def nacti_ciselniky(cesta_modelu=MODEL, cesta_utvaru=UTVARY):
    """Číselníky pro rozbalovátka: procesy, dílčí procesy, útvary.

    Snímek, ne živá data — sešit je statický soubor. Aktuální ho drží
    plánované flow, které do těchto tabulek zapisuje (F13/B3).
    """
    model = json.loads(Path(cesta_modelu).read_text(encoding="utf-8"))
    procesy = [(p["kod"], p["nazev"]) for p in model["procesy"]]
    dilci = [(d["kod"], d["proces_kod"], d["nazev"])
             for d in model["dilci_procesy"]]

    utvary = []
    radky = Path(cesta_utvaru).read_text(encoding="utf-8-sig").splitlines()
    for radek in radky[1:]:
        if not radek.strip():
            continue
        casti = radek.split(";")
        utvary.append((casti[0], casti[1]))

    # Dílčí procesy musí být seskupené podle procesu: pojmenovaný rozsah je
    # souvislý blok řádků, takže rozházené pořadí by kaskádu rozbilo.
    dilci.sort(key=lambda r: (r[1], r[0]))
    procesy.sort()
    return {"procesy": procesy, "dilci_procesy": dilci, "utvary": utvary}


def sirka(sloupec):
    if sloupec["type"] in SIRKA_PODLE_TYPU:
        return SIRKA_PODLE_TYPU[sloupec["type"]]
    return 20 if (sloupec.get("maxlen") or 255) <= 20 else 26


def omezeni(sloupec):
    """Strojově odvoditelná omezení sloupce — text do listu Pokyny."""
    if sloupec.get("uroven"):
        return "kód útvaru, víc oddělených středníkem; prázdné = nemění se"
    if sloupec.get("pomocny"):
        return "výběr z nabídky, neimportuje se"
    if sloupec["type"] == "Choice":
        return " / ".join(sloupec["choices"])
    if sloupec.get("maxlen"):
        return f"nejvýše {sloupec['maxlen']} znaků"
    return "delší text"


def zaloz_tabulku(sesit, sloupce):
    list_dat = sesit.active
    list_dat.title = LIST

    for index, sloupec in enumerate(sloupce, start=1):
        bunka = list_dat.cell(row=1, column=index, value=sloupec["display"])
        bunka.font = Font(bold=True)
        bunka.alignment = Alignment(wrap_text=True, vertical="center")
        list_dat.column_dimensions[get_column_letter(index)].width = sirka(sloupec)
    list_dat.row_dimensions[1].height = HLAVICKA_VYSKA

    # Prázdné řádky musí import přeskočit — dělá to krok `Prazdne` ve flow.
    # Tabulka bez jediného datového řádku by se navíc Excelu jevila jako vadná
    # a při otevření by ji „opravoval".
    posledni = get_column_letter(len(sloupce))
    tabulka = Table(displayName=TABULKA,
                    ref=f"A1:{posledni}{1 + DATOVYCH_RADKU}")
    tabulka.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2", showRowStripes=True)
    list_dat.add_table(tabulka)

    # Sloupec pomocného procesu potřebuje znát ten, kdo staví kaskádu níž.
    pozice = {c["name"]: get_column_letter(i)
              for i, c in enumerate(sloupce, start=1)}

    for index, sloupec in enumerate(sloupce, start=1):
        vzorec = None
        if sloupec["type"] == "Choice":
            # Krátký výčet jde přímo do validace jako seznam v uvozovkách.
            vzorec = '"' + ",".join(sloupec["choices"]) + '"'
        elif sloupec["name"] == POMOCNY_PROCES["name"]:
            vzorec = "=Cis_Procesy"
        elif sloupec["name"] == "dilci_proces_kod":
            # Kaskáda: nabídka se zúží na dílčí procesy vybraného procesu.
            # Kód procesu je prvních pět znaků hodnoty ve vedlejším sloupci
            # (`01-01`), zbytek je název — ten je tam kvůli čitelnosti výběru.
            sloupec_procesu = pozice[POMOCNY_PROCES["name"]]
            vzorec = (f'=INDIRECT("P_"&SUBSTITUTE(LEFT(${sloupec_procesu}2,5),'
                      f'"-","_"))')
        elif sloupec["name"] == "vykonava":
            vzorec = "=Cis_Utvary"
        if vzorec is None:
            continue

        # Rozsah sahá pod tabulku, aby platil i na řádky, které správce dopíše.
        pismeno = get_column_letter(index)
        # showErrorMessage: bez něj je rozbalovátko jen ozdoba a překlep projde
        # až k importu, kde ho správce uvidí jako odmítnutý řádek.
        #
        # allow_blank platí i pro dílčí proces: aktivita nahraná BEZ zařazení
        # je legitimní vstup, import jí dosadí technický kód 00-00-000
        # a správce ji zařadí až v aplikaci.
        kontrola = DataValidation(
            type="list", allow_blank=True, formula1=vzorec,
            showErrorMessage=True, errorTitle="Neplatná hodnota",
            error="Vyberte jednu z nabízených hodnot, nebo nechte prázdné.")
        list_dat.add_data_validation(kontrola)
        kontrola.add(f"{pismeno}2:{pismeno}{POSLEDNI_RADEK_KONTROLY}")

    list_dat.freeze_panes = "A2"
    return list_dat


def zaloz_ciselniky(sesit, ciselniky):
    """List s číselníky a pojmenované rozsahy pro kaskádu.

    List zůstává VIDITELNÝ schválně: správce v něm dohledá název podle kódu.
    Skrytý by byl čistší na pohled, ale kód `01-02-003` sám o sobě nic neříká
    a jinde v sešitě názvy nejsou (vzorce se do šablony dávat nesmí — chyba
    ve vzorci by ze všech dvou set prázdných řádků udělala neprázdné).
    """
    list_c = sesit.create_sheet(LIST_CISELNIKY)
    sedy = PatternFill("solid", fgColor="DDDDDD")

    bloky = [
        # Třetí sloupec je to, co se ukáže v nabídce. Proces se neimportuje,
        # takže jeho hodnota smí být čitelná („01-01 — Název"); dílčí proces
        # a útvar se importují, a tam musí být přesný kód.
        ("A", ["Proces (kód)", "Název procesu", "Nabídka"],
         [(k, n, f"{k} — {n}") for k, n in ciselniky["procesy"]],
         STROP_CISELNIKU["procesy"]),
        ("D", ["Dílčí proces (kód)", "Patří k procesu", "Název dílčího procesu"],
         ciselniky["dilci_procesy"], STROP_CISELNIKU["dilci_procesy"]),
        ("H", ["Útvar (kód)", "Název útvaru"],
         ciselniky["utvary"], STROP_CISELNIKU["utvary"]),
    ]
    for prvni_sloupec, hlavicka, data, strop in bloky:
        if len(data) > strop:
            raise SystemExit(
                f"CHYBA: číselník od sloupce {prvni_sloupec} má {len(data)} "
                f"položek, ale rozsah validace pokrývá jen {strop} — nabídka "
                f"by tiše vynechala konec")
        posun = ord(prvni_sloupec) - ord("A")
        for index, nadpis in enumerate(hlavicka):
            bunka = list_c.cell(row=1, column=posun + index + 1, value=nadpis)
            bunka.font = Font(bold=True)
            bunka.fill = sedy
            list_c.column_dimensions[
                get_column_letter(posun + index + 1)].width = 34 if index else 20
        for radek_index, radek in enumerate(data, start=2):
            for index, hodnota in enumerate(radek):
                list_c.cell(row=radek_index, column=posun + index + 1,
                            value=hodnota)

    # Pojmenované rozsahy pro kaskádu: jeden na každý proces, souvislý blok
    # jeho dílčích procesů. INDIRECT nad nimi je klasický kaskádový vzor —
    # OFFSET/MATCH by šlo taky, ale je volatile a v Excelu Online vrtkavý.
    dilci = ciselniky["dilci_procesy"]
    zacatky = {}
    for index, (_, proces_kod, _) in enumerate(dilci, start=2):
        zacatky.setdefault(proces_kod, [index, index])[1] = index
    for proces_kod, (od, do) in zacatky.items():
        sesit.defined_names.add(DefinedName(
            jmeno_rozsahu(proces_kod),
            attr_text=f"{LIST_CISELNIKY}!$D${od}:$D${do}"))

    # Rozsahy pro první stupeň kaskády a pro útvary — PŘESNĚ podle počtu
    # položek, ne na strop.
    #
    # Rozsah natažený do zásoby by do nabídky přidal tolik prázdných řádků,
    # kolik zbývá do stropu (u osmi útvarů dvě stě mínus osm), a rozbalovátko
    # by bylo k nepoužití. Cena je, že rozsah neroste sám: až přibude proces,
    # musí se šablona přegenerovat. Refresh přes Excel konektor to nedokáže —
    # umí přepsat buňky, ne definici pojmenovaného rozsahu (viz F13/B3).
    sesit.defined_names.add(DefinedName(
        "Cis_Procesy",
        attr_text=f"{LIST_CISELNIKY}!$C$2:$C${1 + len(ciselniky['procesy'])}"))
    sesit.defined_names.add(DefinedName(
        "Cis_Utvary",
        attr_text=f"{LIST_CISELNIKY}!$H$2:$H${1 + len(ciselniky['utvary'])}"))
    list_c.freeze_panes = "A2"
    return list_c


def zaloz_pokyny(sesit, sloupce):
    chybi = [c["name"] for c in sloupce if c["name"] not in NAPOVEDA]
    if chybi:
        raise SystemExit(
            f"CHYBA: chybí nápověda ke sloupcům {chybi} — dopiš ji do NAPOVEDA")

    list_pokyny = sesit.create_sheet(LIST_POKYNY)
    sedy = PatternFill("solid", fgColor="DDDDDD")

    uvod = [
        "Šablona pro hromadný import aktivit do rejstříku procesní mapy.",
        "",
        "1. Vyplňujte POUZE list „Aktivity“, jeden řádek = jedna aktivita.",
        "2. Nepřejmenovávejte list ani sloupce a žádné nepřidávejte —"
        " import čte tabulku podle jejich názvů.",
        "3. Pište od prvního prázdného řádku dolů, bez mezer. Sešit má"
        f" připravených {DATOVYCH_RADKU} řádků; když potřebujete víc, pište"
        " těsně pod poslední řádek tabulky a Excel ji rozšíří sám.",
        "   POZOR: řádky napsané NÍŽE, oddělené od tabulky prázdným místem,"
        " import vůbec neuvidí — jsou mimo tabulku a hlásí se jako prázdný"
        " sešit.",
        "4. Identifikační kód nevyplňujte, přiděluje ho aplikace při importu.",
        "5. Soubor ukládejte jako .xlsx a nahrajte do knihovny „Import“.",
        "   POZOR na citlivostní štítek: nechte „Interní“. Přísnější štítek"
        " sešit zašifruje a import ho pak nedokáže otevřít — ohlásí"
        " „Nemáte oprávnění k otevření tohoto souboru“, přestože soubor"
        " vlastníte.",
        "6. Import nejdřív ukáže náhled (co vznikne / co je duplicita /"
        " co je chyba) a teprve po potvrzení zapisuje.",
        "",
    ]
    for text in uvod:
        list_pokyny.append([text])

    hlavicka = ["Sloupec", "Povinný", "Omezení", "K čemu slouží"]
    list_pokyny.append(hlavicka)
    for index in range(1, len(hlavicka) + 1):
        bunka = list_pokyny.cell(row=list_pokyny.max_row, column=index)
        bunka.font = Font(bold=True)
        bunka.fill = sedy

    for sloupec in sloupce:
        list_pokyny.append([
            sloupec["display"],
            "ano" if sloupec.get("required") else "ne",
            omezeni(sloupec),
            NAPOVEDA[sloupec["name"]],
        ])

    for pismeno, sirka_sloupce in zip("ABCD", (30, 10, 26, 74)):
        list_pokyny.column_dimensions[pismeno].width = sirka_sloupce
    for radek in list_pokyny.iter_rows(min_col=4, max_col=4):
        for bunka in radek:
            bunka.alignment = Alignment(wrap_text=True, vertical="top")
    return list_pokyny


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", default=str(SCHEMA))
    parser.add_argument("--vystup", default=str(VYSTUP))
    parser.add_argument("--model", default=str(MODEL))
    parser.add_argument("--utvary", default=str(UTVARY))
    argumenty = parser.parse_args()

    schema = nacti_schema(argumenty.schema)
    sloupce = sloupce_sesitu(schema)
    ciselniky = nacti_ciselniky(argumenty.model, argumenty.utvary)

    sesit = Workbook()
    zaloz_tabulku(sesit, sloupce)
    zaloz_pokyny(sesit, sloupce)
    zaloz_ciselniky(sesit, ciselniky)

    cesta = Path(argumenty.vystup)
    cesta.parent.mkdir(parents=True, exist_ok=True)
    sesit.save(cesta)

    print(f"zapsáno: {cesta}")
    print(f"tabulka {TABULKA}: {len(sloupce)} sloupců, "
          f"{DATOVYCH_RADKU} prázdných řádků "
          f"({', '.join(c['display'] for c in sloupce)})")
    print(f"číselníky: {len(ciselniky['procesy'])} procesů, "
          f"{len(ciselniky['dilci_procesy'])} dílčích procesů, "
          f"{len(ciselniky['utvary'])} útvarů")
    return 0


if __name__ == "__main__":
    sys.exit(main())
