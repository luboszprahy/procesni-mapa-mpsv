# -*- coding: utf-8 -*-
"""Mutační test F23: shodí brána vadnou volbu kódu a dialog o sirotcích?

Spouštět z kořene projektu:
    python src/mutace_kod.py

Každá mutace je chyba, kterou by šlo udělat při běžné úpravě. Zelená brána
nad zeleným kódem nedokazuje nic — cenu má až to, že mutace **padne**, a to
z vlastního důvodu, ne náhodou na něčem jiném.
"""

import subprocess
import sys
from pathlib import Path

CIL = Path("src/app_src/scr_Ciselnik.pa.yaml")
BRANA = [sys.executable, "src/check_app.py"]

# (název, co se v souboru nahradí, čím, jaký kus hlášky se čeká)
MUTACE = [
    (
        "mazací dialog nezavírá dialog sirotků",
        """                  OnSelect: |-
                    =Set(varSirotciModalC, false);
                    Set(varSmazatC, ThisItem)""",
        """                  OnSelect: =Set(varSmazatC, ThisItem)""",
        "se otevírá, aniž by zavřel",
    ),
    (
        "dialog sirotků nezavírá dialog mazání",
        """                          Set(varSmazatC, Blank());
                          Set(varSirotciModalC, true),""",
        """                          Set(varSirotciModalC, true),""",
        "se otevírá, aniž by zavřel",
    ),
    (
        "pole kódu ztratí Default (dostane text „Text input“)",
        "            Default: |-\n              =If(\n"
        "                  !varCiselnikNova,\n                  varCiselnikKod,",
        "            Tooltip2: |-\n              =If(\n"
        "                  !varCiselnikNova,\n                  varCiselnikKod,",
        "Default",
    ),
    (
        "prvek dialogu vypadne z konvence Modal* a přestane být vrstvou",
        "      - lbl_ModalSirotciTextC:",
        "      - lbl_SirotciTextC:",
        "se překrývají",
    ),
]


def brana():
    hotovo = subprocess.run(BRANA, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    return hotovo.returncode, (hotovo.stdout or "") + (hotovo.stderr or "")


def main():
    puvodni = CIL.read_text(encoding="utf-8")

    kod, vypis = brana()
    if kod != 0:
        print("CHYBA: brána neprochází ani bez mutace — nejdřív ji srovnej")
        print(vypis[-2000:])
        return 1

    selhalo = []
    for nazev, stare, nove, cekana_hlaska in MUTACE:
        if puvodni.count(stare) != 1:
            selhalo.append(f"{nazev}: kotva nesedí ({puvodni.count(stare)}x) — "
                           f"mutace neproběhla, takže nic nedokazuje")
            continue
        CIL.write_text(puvodni.replace(stare, nove), encoding="utf-8")
        try:
            kod, vypis = brana()
        finally:
            CIL.write_text(puvodni, encoding="utf-8")
        if kod == 0:
            selhalo.append(f"{nazev}: brána mutaci PUSTILA")
        elif cekana_hlaska not in vypis:
            selhalo.append(f"{nazev}: spadlo, ale z jiného důvodu — "
                           f"čekal jsem '{cekana_hlaska}'")
        else:
            print(f"chyceno: {nazev}")

    if selhalo:
        for text in selhalo:
            print(f"NEPROŠLO: {text}")
        return 1
    print(f"OK — {len(MUTACE)} mutací, každou brána chytila z vlastního důvodu")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
