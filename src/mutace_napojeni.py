"""Mutační test kontroly `napojeni_appky` v check_solution.py.

Zelená brána sama o sobě nedokazuje nic — může kontrolovat něco jiného, než
si myslím, nebo nekontrolovat vůbec. Tenhle skript zavede do hotového balíku
po jedné chybě a ověří, že brána každou z nich shodí.

Spouštět z kořene projektu:
    python src/mutace_napojeni.py --vstup <base.zip> --vystup <balik.zip>
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def uprav_napojeni(zip_cesta, zmena):
    """Přepíše dataSets v customizations.xml funkcí `zmena`."""
    with zipfile.ZipFile(zip_cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klic = next(n for n in polozky if n.replace("\\", "/").endswith("customizations.xml"))
    text = polozky[klic].decode("utf-8-sig")
    nalez = re.search(r"<ConnectionReferences>(.*?)</ConnectionReferences>", text, re.S)
    reference = json.loads(nalez.group(1))

    for odkaz in reference.values():
        if "shared_sharepointonline" in odkaz.get("id", ""):
            zmena(odkaz)

    novy = json.dumps(reference, separators=(",", ":"), ensure_ascii=False)
    polozky[klic] = (text[: nalez.start(1)] + novy + text[nalez.end(1):]).encode("utf-8")

    with zipfile.ZipFile(zip_cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, obsah in polozky.items():
            balik.writestr(jmeno, obsah)


def _prvni_dataset(odkaz):
    return next(iter(odkaz["dataSets"].values()))


def bez_override_listu(odkaz):
    zdroje = _prvni_dataset(odkaz)["dataSources"]
    zdroje[next(iter(zdroje))].pop("tableNameOverride")


def cizi_promenna(odkaz):
    zdroje = _prvni_dataset(odkaz)["dataSources"]
    zdroje[next(iter(zdroje))]["tableNameOverride"]["environmentVariableName"] = "mpsv_neexistuje"


def klic_bez_suffixu(odkaz):
    adresa, dataset = next(iter(odkaz["dataSets"].items()))
    odkaz["dataSets"] = {dataset["datasetOverride"]["name"]: dataset}


def zdroj_navic_bez_override(odkaz):
    _prvni_dataset(odkaz)["dataSources"]["Dokumenty"] = {
        "tableName": "46e0a505-bbb6-4bd4-a5eb-c201629b97b6"}
    odkaz["dataSources"].append("Dokumenty")


def rozejity_guid(odkaz):
    zdroje = _prvni_dataset(odkaz)["dataSources"]
    zdroje[next(iter(zdroje))]["tableNameOverride"]["name"] = "00000000-0000-0000-0000-000000000000"


MUTACE = [
    ("chybí tableNameOverride", bez_override_listu),
    ("odkaz na nedeklarovanou proměnnou", cizi_promenna),
    ("klíč datasetu bez suffixu proměnné", klic_bez_suffixu),
    ("zdroj bez overridu navíc", zdroj_navic_bez_override),
    ("tableNameOverride.name nesedí na tableName", rozejity_guid),
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
            uprav_napojeni(kopie, zmena)
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
