# -*- coding: utf-8 -*-
"""Overi, ze retez vyrazu ve flow AktualizaceKratkehoNazvu dava tyz vysledek
jako kanonicka funkce zkratit() z check_schema.py.

Flow nema regularni vyrazy, takze normalizaci mezer i orez koncovych znaku
dela opakovanym replace/substring. Tady je tentyz postup krok za krokem
v Pythonu - kdyz se rozejde s kanonickou funkci, navod v
deploy/flow_AktualizaceKratkehoNazvu.md je spatne.
"""
import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_schema import zkratit  # noqa: E402

MAXLEN = 150
KOLAPS_PRUCHODU = 3      # replace('  ', ' ') - pokryje az 8 mezer za sebou
OREZ_PRUCHODU = 3        # orez koncovych znaku ' ,;.'
OREZAVANE = " ,;."


def zkratit_flow(text):
    """Presne to, co dela retez Compose akci ve flow."""
    # Compose 'Bez_bilych_znaku'
    t = (text or "").replace("\r", " ").replace("\n", " ").replace("\t", " ")
    for _ in range(KOLAPS_PRUCHODU):
        t = t.replace("  ", " ")
    t = t.strip()

    # Compose 'Rez'
    rez = t if len(t) <= MAXLEN else t[:MAXLEN - 1]

    # Compose 'Rez_na_slovo'
    if len(t) <= MAXLEN:
        rez_slovo = t
    else:
        mezera = rez.rfind(" ")
        rez_slovo = rez[:mezera] if mezera > MAXLEN // 2 else rez

    # Compose 'Orez_1'..'Orez_3'
    orez = rez_slovo
    for _ in range(OREZ_PRUCHODU):
        if orez and orez[-1] in OREZAVANE:
            orez = orez[:-1]

    # Compose 'Cil'
    return t if len(t) <= MAXLEN else orez + "…"


HRANICNI = [
    "",
    "   ",
    "Vede spisovou sluzbu.",                       # kratky text s teckou na konci
    "A" * MAXLEN,                                  # presne na hranici
    "A" * (MAXLEN + 1),                            # jedno slovo pres hranici, zadna mezera
    "A" * 200 + " konec",                          # mezera az za rezem
    ("slovo " * 40).strip(),                       # rez padne na hranici slova
    "x" * 100 + " zdroju, dalsi text " + "y" * 80,  # po rezu zbyde carka
    "Prvni  cast   se    tremi     mezerami " + "z" * 200,
    "Radek\nzalomeny\ta tabulatorem " + "q" * 200,
    "Text konci carkou, " + "w" * 200,
    # rez padne tesne za carku -> orez koncovych znaku musi zabrat
    "a" * 100 + " konec, " + "b" * 100,
    "a" * 100 + " konec., " + "b" * 100,       # dva znaky k orezu
    "a" * 100 + " konec.;, " + "b" * 100,      # tri znaky k orezu
]


def nazvy_z_csv(path):
    if not os.path.exists(path):
        return []
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        return [r["nazev"] for r in csv.DictReader(f, delimiter=";")]


def main():
    vzorky = list(HRANICNI)
    for p in ("runs/normalize/aktivity.csv", "runs/anonym/aktivity.csv"):
        vzorky += nazvy_z_csv(p)

    chyby = []
    for v in vzorky:
        ocekavano = zkratit(v, MAXLEN)
        dostal = zkratit_flow(v)
        if ocekavano != dostal:
            chyby.append((v, ocekavano, dostal))

    print("porovnano vzorku: %d (z toho hranicnich: %d)" % (len(vzorky), len(HRANICNI)))
    dlouhe = sum(1 for v in vzorky if len(" ".join((v or "").split())) > MAXLEN)
    print("z toho delsich nez %d znaku: %d" % (MAXLEN, dlouhe))

    if chyby:
        print("\nNESHODA v %d pripadech:" % len(chyby))
        for v, o, d in chyby[:10]:
            print("  vstup     : %r" % v[:80])
            print("  kanonicky : %r" % o[-60:])
            print("  flow      : %r" % d[-60:])
        return 1

    print("HOTOVO: retez vyrazu ve flow odpovida zkratit() ve vsech vzorcich")
    return 0


if __name__ == "__main__":
    sys.exit(main())
