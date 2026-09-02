# -*- coding: utf-8 -*-
"""Generátor šablony pro hromadný import aktivit.

Ze `src/schema.json` vyrobí `deploy/sablona_import_aktivit.xlsx` — sešit, který
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
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

SCHEMA = Path("src/schema.json")
VYSTUP = Path("deploy/sablona_import_aktivit.xlsx")

LIST = "Aktivity"          # list schématu, ze kterého se šablona staví
TABULKA = "Aktivity"       # jméno Tabulky — na něj se odkazuje ImportFlow
LIST_POKYNY = "Pokyny"

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
    "dilci_proces_kod": "Kód existujícího dílčího procesu ve tvaru AA-BB-CCC, "
                        "např. 01-02-003. Neexistující kód import odmítne.",
    "vykonava": "Oddělení, které činnost vykonává. Více útvarů oddělte '; '.",
    "spolupracuje": "Útvary, které se na činnosti podílejí. Více útvarů oddělte '; '.",
    "vnitrni_predpis": "Předpis, ze kterého činnost plyne. Více předpisů oddělte '; '.",
    "text_pro_or": "Nepovinné. Znění pro organizační řád, pokud se liší od názvu; "
                   "jinak nechte prázdné a doplňte později v aplikaci.",
    "sekce": "Číslo sekce, pod kterou činnost spadá.",
    "stav": "Nevyplněno = pracovní. 'schváleno' použijte jen u činností, "
            "které už prošly schválením.",
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


def sirka(sloupec):
    if sloupec["type"] in SIRKA_PODLE_TYPU:
        return SIRKA_PODLE_TYPU[sloupec["type"]]
    return 20 if (sloupec.get("maxlen") or 255) <= 20 else 26


def omezeni(sloupec):
    """Strojově odvoditelná omezení sloupce — text do listu Pokyny."""
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

    for index, sloupec in enumerate(sloupce, start=1):
        if sloupec["type"] != "Choice":
            continue
        # Rozsah sahá pod tabulku, aby platil i na řádky, které správce dopíše.
        pismeno = get_column_letter(index)
        # showErrorMessage: bez něj je rozbalovátko jen ozdoba a překlep projde
        # až k importu, kde ho správce uvidí jako odmítnutý řádek.
        kontrola = DataValidation(
            type="list", allow_blank=True,
            formula1='"' + ",".join(sloupec["choices"]) + '"',
            showErrorMessage=True, errorTitle="Neplatná hodnota",
            error="Vyberte jednu z nabízených hodnot, nebo nechte prázdné.")
        list_dat.add_data_validation(kontrola)
        kontrola.add(f"{pismeno}2:{pismeno}{POSLEDNI_RADEK_KONTROLY}")

    list_dat.freeze_panes = "A2"
    return list_dat


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
    argumenty = parser.parse_args()

    schema = nacti_schema(argumenty.schema)
    sloupce = sloupce_sablony(schema)

    sesit = Workbook()
    zaloz_tabulku(sesit, sloupce)
    zaloz_pokyny(sesit, sloupce)

    cesta = Path(argumenty.vystup)
    cesta.parent.mkdir(parents=True, exist_ok=True)
    sesit.save(cesta)

    print(f"zapsáno: {cesta}")
    print(f"tabulka {TABULKA}: {len(sloupce)} sloupců, "
          f"{DATOVYCH_RADKU} prázdných řádků "
          f"({', '.join(c['display'] for c in sloupce)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
