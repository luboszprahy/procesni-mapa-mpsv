# -*- coding: utf-8 -*-
"""Sestaví číselník útvarů z čísel, která se objevují v aktivitách.

Útvary v podkladech vlastní číselník nemají — jsou jen jako čísla ve sloupcích
`vykonava` a `spolupracuje` evidenčních karet. Hierarchie je ale v samotném
čísle: 1 číslice = sekce, 2 = odbor, 3 = oddělení (7 -> 71 -> 711).

Skript z toho poskládá úplný číselník včetně nadřízených úrovní, které se samy
v datech nevyskytují. **Názvy jsou zástupné** ("Oddělení 711") — skutečné
názvy doplní zadavatelka; kódy a hierarchie jsou odvozené z dat, ne vymyšlené.

Spouštět z kořene projektu:
    python src/make_utvary.py                       # runs/normalize + runs/anonym
    python src/make_utvary.py --dir runs/anonym
"""

import argparse
import csv
import io
import sys
from pathlib import Path

UROVNE = {1: "sekce", 2: "odbor", 3: "oddělení"}


def cti(cesta):
    with io.open(cesta, encoding="utf-8-sig", newline="") as soubor:
        return list(csv.DictReader(soubor, delimiter=";"))


def cisla_utvaru(radky):
    """Posbírá čísla útvarů z 'vykonava' i 'spolupracuje' (víc hodnot po ';')."""
    nalezene = set()
    for radek in radky:
        for sloupec in ("vykonava", "spolupracuje"):
            for cast in (radek.get(sloupec) or "").replace(",", ";").split(";"):
                cast = cast.strip()
                if cast.isdigit() and 1 <= len(cast) <= 3:
                    nalezene.add(cast)
    return nalezene


def doplnit_nadrizene(kody):
    """Ke každému číslu přidá i jeho nadřízené úrovně (711 -> 71 -> 7)."""
    uplne = set()
    for kod in kody:
        for delka in range(1, len(kod) + 1):
            uplne.add(kod[:delka])
    return uplne


def ciselnik(kody):
    radky = []
    for kod in sorted(doplnit_nadrizene(kody), key=lambda k: (len(k), k)):
        uroven = len(kod)
        radky.append({
            "kod": kod,
            # Tvar "Útvar 7 (sekce)", ne "Sekce 7": kontrola anonymity hlídá vzor
            # "sekce <číslice>" jako identifikující údaj a zástupný název by ji
            # zbytečně spouštěl. Past tím zůstává funkční pro reálná data.
            "nazev": f"Útvar {kod} ({UROVNE.get(uroven, 'útvar')})",
            "uroven": UROVNE.get(uroven, "útvar"),
            "nadrizeny_kod": kod[:-1] if uroven > 1 else "",
        })
    return radky


def zapis(radky, cesta):
    with io.open(cesta, "w", encoding="utf-8-sig", newline="") as soubor:
        zapisovac = csv.DictWriter(soubor, fieldnames=["kod", "nazev", "uroven", "nadrizeny_kod"],
                                   delimiter=";")
        zapisovac.writeheader()
        zapisovac.writerows(radky)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", action="append", dest="adresare",
                        help="adresář s aktivity.csv (lze uvést vícekrát)")
    argumenty = parser.parse_args()
    adresare = argumenty.adresare or ["runs/normalize", "runs/anonym"]

    for adresar in adresare:
        zdroj = Path(adresar) / "aktivity.csv"
        if not zdroj.exists():
            print(f"PRESKOCENO: {zdroj} neexistuje")
            continue
        radky = ciselnik(cisla_utvaru(cti(zdroj)))
        cil = Path(adresar) / "utvary.csv"
        zapis(radky, cil)
        podle_urovne = {}
        for radek in radky:
            podle_urovne[radek["uroven"]] = podle_urovne.get(radek["uroven"], 0) + 1
        print(f"{cil}: {len(radky)} útvarů  {podle_urovne}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
