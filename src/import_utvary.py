# -*- coding: utf-8 -*-
"""Číselník útvarů ze skutečného MPSV listu *Organizační útvary*.

Nahrazuje `make_utvary.py`, který číselník vyráběl z čísel v aktivitách,
názvy vymýšlel a **hierarchii hádal z délky čísla** (111 -> 11 -> 1). Dodaný
export to vyvrátil: `O11` patří pod `Sekce 3`, ne pod „sekcí 1", a `O32`,
`O34`, `O35` jsou pod `Sekce 6`, i když jejich číslo začíná trojkou.

Kód zůstává holé číslo (`11`, `331`, `3`), protože ho tak nesou aktivity
i rejstřík; označení z MPSV (`O11`, `Sekce 3`) jde do názvu. Rozhodl uživatel
06.09.2026 — data se tím nepřepisují.

Nesrovnalosti ve zdroji skript **neopravuje**, jen vypíše: cyklus (`O33` je
nadřízený sám sobě), odbor pod odborem, oddělení bez odboru. První je chyba,
zbylé dvě jsou legitimní organizační výjimky — rozhodnout to musí člověk.

Spouštět z kořene projektu:
    python src/import_utvary.py
    python src/import_utvary.py --zdroj input/organizacni_utvary.xlsx --cil runs/normalize
"""

import argparse
import csv
import io
import re
import sys
from pathlib import Path

from openpyxl import load_workbook

ZDROJ = Path("input/organizacni_utvary.xlsx")
CIL = Path("runs/normalize")

# Úroveň ve zdroji -> úroveň v číselníku. Co tu není, do číselníku útvarů
# nepatří: `neobsazeno`, `věcně příslušné útvary MPSV` a `podřízené služební
# úřady` jsou hodnoty pro sloupec `spolupracuje`, ne útvary.
UROVNE = {
    "ministr": "ministr",
    "sekce": "sekce",
    "odbor": "odbor",
    "oddělení": "oddělení",
}

# Kód ministra. V datech se nevyskytuje (nic pod něj přímo nespadá), ale
# hierarchie ho potřebuje jako kořen, aby sekce neměly prázdného rodiče.
KOD_MINISTRA = "0"

RE_ODBOR = re.compile(r"^O(\d{1,3})$")
RE_SEKCE = re.compile(r"^Sekce\s+(\d{1,2})$", re.IGNORECASE)


def kod_z_oznaceni(oznaceni):
    """`O331` -> `331`, `Sekce 3` -> `3`, `Ministr` -> `0`. Jinak None."""
    text = (oznaceni or "").strip()
    if text.lower() == "ministr":
        return KOD_MINISTRA
    shoda = RE_ODBOR.match(text)
    if shoda:
        return shoda.group(1)
    shoda = RE_SEKCE.match(text)
    if shoda:
        return shoda.group(1)
    return None


def cti_zdroj(cesta):
    """Řádky exportu jako slovníky podle hlavičky prvního řádku."""
    sesit = load_workbook(cesta, data_only=True)
    list_dat = sesit[sesit.sheetnames[0]]
    radky = list(list_dat.iter_rows(values_only=True))
    if not radky:
        raise SystemExit(f"CHYBA: {cesta} je prázdný")
    hlavicka = [str(h or "").strip() for h in radky[0]]
    for povinny in ("Útvar", "Úroveň", "Nadřízený útvar"):
        if povinny not in hlavicka:
            raise SystemExit(
                f"CHYBA: {cesta} nemá sloupec '{povinny}' — sloupce: {hlavicka}")
    return [dict(zip(hlavicka, radek)) for radek in radky[1:]
            if any(b is not None and str(b).strip() for b in radek)]


def poradi(radek):
    """Sloupec Pořadí; nečíselné hodnoty jdou na konec."""
    try:
        return (0, int(str(radek.get("Pořadí") or "").strip()))
    except ValueError:
        return (1, 0)


def sestav(radky):
    """Vrátí (číselník, nálezy). Nálezy nezastavují — jen se vypíšou."""
    utvary, nalezy, mimo = [], [], []

    for radek in sorted(radky, key=poradi):
        oznaceni = str(radek.get("Útvar") or "").strip()
        uroven_zdroj = str(radek.get("Úroveň") or "").strip()
        uroven = UROVNE.get(uroven_zdroj.lower())
        if uroven is None:
            mimo.append(f"{oznaceni} (úroveň '{uroven_zdroj}')")
            continue

        kod = kod_z_oznaceni(oznaceni)
        if kod is None:
            nalezy.append(
                f"'{oznaceni}' — z označení nejde odvodit číslo útvaru, "
                f"řádek se do číselníku nedostal")
            continue

        nadrizeny_zdroj = str(radek.get("Nadřízený útvar") or "").strip()
        nadrizeny = ""
        if uroven == "ministr":
            pass  # kořen, rodiče nemá
        elif not nadrizeny_zdroj:
            nalezy.append(f"{oznaceni} ({kod}) nemá vyplněného nadřízeného")
        elif nadrizeny_zdroj == oznaceni:
            nalezy.append(
                f"{oznaceni} ({kod}) je nadřízený sám sobě — cyklus, "
                f"nadřízený se zahodil a útvar zůstal bez rodiče")
        else:
            nadrizeny = kod_z_oznaceni(nadrizeny_zdroj)
            if nadrizeny is None:
                nalezy.append(
                    f"{oznaceni} ({kod}) má nadřízeného '{nadrizeny_zdroj}', "
                    f"ze kterého nejde odvodit číslo")
                nadrizeny = ""

        utvary.append({"kod": kod, "nazev": oznaceni, "uroven": uroven,
                       "nadrizeny_kod": nadrizeny})

    if mimo:
        nalezy.append("do číselníku útvarů nepatří (hodnoty pro 'spolupracuje'): "
                      + ", ".join(mimo))

    podle_kodu = {}
    for utvar in utvary:
        podle_kodu.setdefault(utvar["kod"], []).append(utvar["nazev"])
    for kod, jmena in sorted(podle_kodu.items()):
        if len(jmena) > 1:
            nalezy.append(f"kód {kod} vyšel z víc označení: {', '.join(jmena)}")

    nalezy += nesrovnalosti_hierarchie(utvary, set(podle_kodu))
    return utvary, nalezy


def nesrovnalosti_hierarchie(utvary, kody):
    """Rodič mimo číselník a úrovně, které nejdou po sobě."""
    nalezy = []
    uroven_kodu = {u["kod"]: u["uroven"] for u in utvary}
    ocekavany_rodic = {"sekce": "ministr", "odbor": "sekce", "oddělení": "odbor"}

    for utvar in utvary:
        rodic = utvar["nadrizeny_kod"]
        if not rodic:
            continue
        if rodic not in kody:
            nalezy.append(
                f"{utvar['nazev']} ({utvar['kod']}) ukazuje na nadřízeného "
                f"{rodic}, který v číselníku není")
            continue
        cekano = ocekavany_rodic.get(utvar["uroven"])
        skutecny = uroven_kodu[rodic]
        if cekano and skutecny != cekano:
            nalezy.append(
                f"{utvar['nazev']} ({utvar['uroven']}) je pod útvarem "
                f"{rodic} ({skutecny}), čekal jsem {cekano}")

    bez_rodice = [u["nazev"] for u in utvary
                  if u["uroven"] != "ministr" and not u["nadrizeny_kod"]]
    if bez_rodice:
        nalezy.append("bez nadřízeného zůstaly: " + ", ".join(bez_rodice))
    return nalezy


def zapis(utvary, cesta):
    with io.open(cesta, "w", encoding="utf-8-sig", newline="") as soubor:
        zapisovac = csv.DictWriter(
            soubor, fieldnames=["kod", "nazev", "uroven", "nadrizeny_kod"],
            delimiter=";")
        zapisovac.writeheader()
        zapisovac.writerows(utvary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zdroj", default=str(ZDROJ))
    parser.add_argument("--cil", default=str(CIL))
    argumenty = parser.parse_args()

    zdroj = Path(argumenty.zdroj)
    if not zdroj.exists():
        raise SystemExit(f"CHYBA: {zdroj} neexistuje")

    utvary, nalezy = sestav(cti_zdroj(zdroj))
    if not utvary:
        raise SystemExit("CHYBA: ze zdroje nevyšel ani jeden útvar")

    cil = Path(argumenty.cil) / "utvary.csv"
    zapis(utvary, cil)

    podle_urovne = {}
    for utvar in utvary:
        podle_urovne[utvar["uroven"]] = podle_urovne.get(utvar["uroven"], 0) + 1
    print(f"{cil}: {len(utvary)} útvarů  {podle_urovne}")
    if nalezy:
        print(f"\nnálezy ({len(nalezy)}) — zdroj se NEOPRAVUJE, rozhoduje člověk:")
        for nalez in nalezy:
            print(f"  - {nalez}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
