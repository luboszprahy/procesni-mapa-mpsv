"""Mutační test kontroly `deklarace_parametru` v check_solution.py.

Brána vznikla po nálezu z PPF DEV 31.08.2026: `ExportFlow` používal
`parameters('Procesni mapa - web (…)')` ve výrazu akce `Cesta_webu`, ale
neměl ho v `definition.parameters`. Flow spadlo na
`InvalidTemplate … The workflow parameter '…' is not found` a volající appka
viděla jen `502 BadGateway / NoResponse`.

Zelená brána sama nedokazuje nic — tenhle skript zavede do hotového balíku
po jedné chybě a ověří, že ji brána shodí.

Spouštět z kořene projektu:
    python src/mutace_parametry.py --vstup <base.zip> --vystup <balik.zip>
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

FLOW = "ExportFlow"


def uprav_flow(zip_cesta, zmena):
    """Přepíše definici ExportFlow funkcí `zmena`; nezměněná definice = chyba.

    Mutace, která se do definice netrefí, by se jinak tvářila jako platný
    test — brána by prošla a vypadalo by to, že mutaci nechytá nikdo.
    """
    with zipfile.ZipFile(zip_cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klic = next(n for n in polozky
                if n.replace("\\", "/").startswith(f"Workflows/{FLOW}"))
    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    pred = json.dumps(flow, ensure_ascii=False, sort_keys=True)
    zmena(flow["properties"]["definition"])
    po = json.dumps(flow, ensure_ascii=False, sort_keys=True)
    if pred == po:
        raise SystemExit(f"CHYBA: mutace se do definice {FLOW} netrefila")
    polozky[klic] = json.dumps(flow, ensure_ascii=False, indent=1).encode("utf-8")

    with zipfile.ZipFile(zip_cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, obsah in polozky.items():
            balik.writestr(jmeno, obsah)


def bez_deklarace(definice):
    """Přesně stav balíku 1.0.0.69, který na PPF DEV spadl."""
    definice["parameters"] = {k: v for k, v in definice["parameters"].items()
                              if k.startswith("$")}


def bez_schema_name(definice):
    """Deklarace bez vazby na proměnnou — parametr by zůstal bez hodnoty."""
    for nazev, popis in definice["parameters"].items():
        if not nazev.startswith("$"):
            popis.pop("metadata", None)


def cizi_schema_name(definice):
    for nazev, popis in definice["parameters"].items():
        if not nazev.startswith("$"):
            popis["metadata"]["schemaName"] = "mpsv_neexistuje"


def prazdny_default(definice):
    """Prázdný defaultValue shodí import solution na 29 %."""
    for nazev, popis in definice["parameters"].items():
        if not nazev.startswith("$"):
            popis["defaultValue"] = ""


MUTACE = [
    ("parametr použitý ve výrazu není deklarovaný", bez_deklarace),
    ("deklarace bez metadata.schemaName", bez_schema_name),
    ("metadata.schemaName míří na jinou proměnnou", cizi_schema_name),
    ("prázdný defaultValue", prazdny_default),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vstup", required=True)
    parser.add_argument("--vystup", required=True)
    argumenty = parser.parse_args()

    hlidane = 0
    for popis, zmena in MUTACE:
        with tempfile.TemporaryDirectory() as docasny:
            kopie = Path(docasny) / "mutace.zip"
            shutil.copy(argumenty.vystup, kopie)
            uprav_flow(kopie, zmena)
            beh = subprocess.run(
                [sys.executable, "src/check_solution.py",
                 "--vstup", argumenty.vstup, "--vystup", str(kopie)],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
        if beh.returncode == 0:
            print(f"NEODHALENO: {popis} — brána mutaci propustila")
        else:
            hlidane += 1
            print(f"chycena: {popis}")

    print(f"\nchycených mutací: {hlidane}/{len(MUTACE)}")
    return 0 if hlidane == len(MUTACE) else 1


if __name__ == "__main__":
    sys.exit(main())
