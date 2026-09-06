# -*- coding: utf-8 -*-
"""Mutační test kontroly překryvů v check_app.py — hlavně UVNITŘ galerií.

Kontrola překryvů existovala od 20.08.2026, ale prvky uvnitř galerie
přeskakovala: jejich souřadnice jsou výrazy nad `Parent.TemplateWidth`
a `souradnice_v_px` je neuměla dopočítat. Prakticky tedy uvnitř žádné galerie
nekontrolovala nic — vyšlo to najevo až auditem (06.09.2026), když `btn_PresunC`
ležel 16 px přes štítek úklidu a brána mlčela.

Po opravě se dopočítávají i výrazy s `TemplateWidth`, `TemplateHeight` a se
stupněm písma `varFs`. Test ověřuje, že to skutečně hlídá — a zároveň že
výjimka pro modály (leží nad obsahem schválně) není tak široká, aby zakryla
překryv dvou modálních prvků mezi sebou.

Spouštět z kořene projektu:
    python src/mutace_prekryv.py
"""

import subprocess
import sys
from pathlib import Path

CISELNIK = Path("src/app_src/scr_Ciselnik.pa.yaml")
ZNAK = "se překrývají"


def spust_branu():
    beh = subprocess.run([sys.executable, "src/check_app.py"],
                         capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    return beh.returncode, (beh.stdout or "") + (beh.stderr or "")


# Každá mutace je (popis, hledaný úsek, náhrada). Úsek musí být v souboru
# právě jednou, jinak by se mutace tiše neprovedla a test by nic nedokazoval.
MUTACE = [
    ("tlačítko Přesun najede na štítek úklidu",
     "                  Width: =84\n                  X: =Parent.TemplateWidth - 140",
     "                  Width: =84\n                  X: =Parent.TemplateWidth - 200"),

    ("popisek názvu v řádku přeteče přes vlastníka",
     "                  Width: =Parent.TemplateWidth - 482",
     "                  Width: =Parent.TemplateWidth - 300"),

    ("koš v řádku galerie leží na tlačítku Přesun",
     "                  Width: =32\n                  X: =Parent.TemplateWidth - 48",
     "                  Width: =32\n                  X: =Parent.TemplateWidth - 130"),

    # Výjimka pro modály se vztahuje jen na dvojici modál + obsah pod ním.
    # Dva modální prvky přes sebe jsou pořád vada a brána je hlásit musí.
    ("dva modální prvky přes sebe",
     "            Y: =Parent.Height / 2 - 148",
     "            Y: =Parent.Height / 2 - 100"),
]


def main():
    puvodni = CISELNIK.read_bytes()
    text = puvodni.decode("utf-8").replace("\r\n", "\n")

    kod, vystup = spust_branu()
    if kod != 0:
        print("CHYBA: brána neprošla už na nezmutovaných zdrojích:\n" + vystup)
        return 1

    chycene = 0
    try:
        for popis, hledany, nahrada in MUTACE:
            if text.count(hledany) != 1:
                print(f"  PŘESKOČENA (úsek není právě jednou): {popis}")
                continue
            zmuteny = text.replace(hledany, nahrada, 1)
            CISELNIK.write_bytes(zmuteny.replace("\n", "\r\n").encode("utf-8"))
            kod, vystup = spust_branu()
            if kod != 0 and ZNAK in vystup:
                chycene += 1
                print(f"  chycena: {popis}")
            elif kod != 0:
                print(f"  NECHYCENA (spadlo na něčem jiném): {popis}")
            else:
                print(f"  NECHYCENA (brána prošla): {popis}")
    finally:
        CISELNIK.write_bytes(puvodni)

    kod, _ = spust_branu()
    if kod != 0:
        print("CHYBA: zdroje se nevrátily do původního stavu")
        return 1

    print(f"\nchycených mutací: {chycene}/{len(MUTACE)}")
    return 0 if chycene == len(MUTACE) else 1


if __name__ == "__main__":
    sys.exit(main())
