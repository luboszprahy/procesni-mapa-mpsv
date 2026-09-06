# -*- coding: utf-8 -*-
"""Kontrola: každý útvar použitý v datech je v číselníku.

Do 06.09.2026 tenhle skript číselník **vyráběl** — z čísel, která se objeví
v aktivitách, s vymyšlenými názvy a s hierarchií odvozenou z délky čísla
(111 -> 11 -> 1). Skutečný MPSV list to vyvrátil: `O11` je pod `Sekce 3`
a `O32` pod `Sekce 6`, i když jejich čísla začínají jinak. Číselník proto
staví `import_utvary.py` z dodaného exportu a tady zbyla jen kontrola.

Hlídá jediné: že se v datech neobjeví útvar, který v číselníku není. Takový
nález řeší zadavatelka (doplní útvar do MPSV listu, nebo opraví kartu) —
skript si ho nesmí domyslet, protože právě z domýšlení vznikla chybná
hierarchie.

Spouštět z kořene projektu:
    python src/make_utvary.py                       # runs/normalize + runs/anonym
    python src/make_utvary.py --dir runs/anonym
"""

import argparse
import csv
import io
import re
import sys
from pathlib import Path

# Kód útvaru je 1-3 číslice. Volný text ve `spolupracuje` („věcně příslušné
# útvary MPSV", „odbor 11") se za kód považovat nesmí — bere se jen buňka,
# která je celá číslo, případně čísla oddělená ; , /.
RE_KOD = re.compile(r"^\d{1,3}$")
SLOUPCE = {
    "aktivity.csv": ("vykonava", "spolupracuje"),
    "agendy.csv": ("vlastnik",),
    "procesy.csv": ("vlastnik",),
    "dilci_procesy.csv": ("vlastnik",),
}


def cti(cesta):
    with io.open(cesta, encoding="utf-8-sig", newline="") as soubor:
        return list(csv.DictReader(soubor, delimiter=";"))


def kody_v_datech(adresar):
    """Čísla útvarů z aktivit i z vlastníků všech tří úrovní."""
    nalezene = {}
    for soubor, sloupce in SLOUPCE.items():
        cesta = Path(adresar) / soubor
        if not cesta.exists():
            continue
        for radek in cti(cesta):
            for sloupec in sloupce:
                hodnota = radek.get(sloupec) or ""
                for cast in hodnota.replace(",", ";").replace("/", ";").split(";"):
                    cast = cast.strip()
                    if RE_KOD.match(cast):
                        nalezene.setdefault(cast, set()).add(f"{soubor}:{sloupec}")
    return nalezene


def ciselnik(adresar):
    cesta = Path(adresar) / "utvary.csv"
    if not cesta.exists():
        raise SystemExit(
            f"CHYBA: {cesta} neexistuje — číselník staví src/import_utvary.py")
    return {radek["kod"] for radek in cti(cesta)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", action="append", dest="adresare",
                        help="adresář s daty (lze uvést vícekrát)")
    argumenty = parser.parse_args()
    adresare = argumenty.adresare or ["runs/normalize", "runs/anonym"]

    chyby = 0
    for adresar in adresare:
        if not (Path(adresar) / "aktivity.csv").exists():
            print(f"PRESKOCENO: {adresar}/aktivity.csv neexistuje")
            continue
        znam = ciselnik(adresar)
        pouzite = kody_v_datech(adresar)
        chybejici = {k: v for k, v in pouzite.items() if k not in znam}
        nepouzite = sorted(znam - set(pouzite), key=lambda k: (len(k), k))

        print(f"{adresar}: {len(pouzite)} útvarů v datech, {len(znam)} v číselníku")
        if chybejici:
            chyby += len(chybejici)
            print(f"  CHYBA: v číselníku chybí {len(chybejici)} útvarů:")
            for kod in sorted(chybejici, key=lambda k: (len(k), k)):
                print(f"    - {kod}  (z {', '.join(sorted(chybejici[kod]))})")
        if nepouzite:
            print(f"  v datech se nevyskytuje {len(nepouzite)} útvarů "
                  f"z číselníku: {', '.join(nepouzite[:12])}"
                  + (" …" if len(nepouzite) > 12 else ""))

    if chyby:
        print("\nNEPROŠLO — doplň útvary do MPSV listu, nebo oprav data")
        return 1
    print("\nOK — každý útvar použitý v datech je v číselníku")
    return 0


if __name__ == "__main__":
    sys.exit(main())
