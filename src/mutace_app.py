# -*- coding: utf-8 -*-
"""Mutační test kontroly `zapisu_v_forall` v check_app.py.

Zelená brána sama o sobě nedokazuje nic. Skript zavede do zdrojů appky po
jedné chybě a ověří, že ji brána shodí — a že to udělá právě tou kontrolou,
ne náhodou jinou. Zdroje se vždy vrátí do původního stavu.

Spouštět z kořene projektu:
    python src/mutace_app.py
"""

import subprocess
import sys
from pathlib import Path

DETAIL = Path("src/app_src/scr_Detail.pa.yaml")

# Vzor, který v appce je: řádky se odloží do kolekce a teprve nad ní běží ForAll.
SPRAVNE = """                              ClearCollect(
                                  colVazbySirotka,
                                  Filter('Vazba aktivita–dílčí proces', aktivita_kod = varStaryKod)
                              );
                              ForAll(
                                  colVazbySirotka As v,
                                  Patch(
                                      'Vazba aktivita–dílčí proces',
                                      v,
                                      {
                                          Title: varNovyKod & "__" & v.dilci_proces_kod,
                                          aktivita_kod: varNovyKod
                                      }
                                  )
                              )
"""

# 1.0.0.94: filtr a zápis v jednom průchodu — Studio appku odmítlo.
PATCH_V_FORALL = """                              ForAll(
                                  Filter('Vazba aktivita–dílčí proces', aktivita_kod = varStaryKod) As v,
                                  Patch(
                                      'Vazba aktivita–dílčí proces',
                                      v,
                                      {
                                          Title: varNovyKod & "__" & v.dilci_proces_kod,
                                          aktivita_kod: varNovyKod
                                      }
                                  )
                              )
"""

# Táž vada jinou funkcí — ověřuje, že kontrola nehlídá jen dvojici ForAll+Patch.
REMOVEIF_V_FORALL = """                              ForAll(
                                  Filter('Vazba aktivita–dílčí proces', aktivita_kod = varStaryKod) As v,
                                  RemoveIf(
                                      'Vazba aktivita–dílčí proces',
                                      ID = v.ID
                                  )
                              )
"""

MUTACE = [
    ("Patch nad zdrojem, který ForAll prochází", PATCH_V_FORALL),
    ("RemoveIf nad zdrojem, který ForAll prochází", REMOVEIF_V_FORALL),
]

ZNAK = "cannot operate on the same"


def spust_branu():
    beh = subprocess.run([sys.executable, "src/check_app.py"],
                         capture_output=True, text=True, encoding="utf-8")
    return beh.returncode, (beh.stdout or "") + (beh.stderr or "")


def main():
    puvodni = DETAIL.read_bytes()
    text = puvodni.decode("utf-8").replace("\r\n", "\n")
    if text.count(SPRAVNE) != 1:
        print("CHYBA: v scr_Detail.pa.yaml nesedí kotva se správným tvarem — "
              "mutace by měnila něco jiného, než si myslí")
        return 1

    kod, vystup = spust_branu()
    if kod != 0:
        print("CHYBA: brána neprošla už na nezmutovaných zdrojích:\n" + vystup)
        return 1

    chycene = 0
    try:
        for popis, vada in MUTACE:
            DETAIL.write_bytes(text.replace(SPRAVNE, vada).replace("\n", "\r\n").encode("utf-8"))
            kod, vystup = spust_branu()
            if kod != 0 and ZNAK in vystup:
                chycene += 1
                print(f"  chycena: {popis}")
            elif kod != 0:
                print(f"  NECHYCENA (spadlo na něčem jiném): {popis}")
            else:
                print(f"  NECHYCENA (brána prošla): {popis}")
    finally:
        DETAIL.write_bytes(puvodni)

    kod, _ = spust_branu()
    if kod != 0:
        print("CHYBA: zdroje se nevrátily do původního stavu")
        return 1

    print(f"\nchycených mutací: {chycene}/{len(MUTACE)}")
    return 0 if chycene == len(MUTACE) else 1


if __name__ == "__main__":
    sys.exit(main())
