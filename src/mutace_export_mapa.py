"""Mutační test kontroly `vyznam_mapa` v check_export_flow.py.

Brána nad režimem `__mapa__` je nová a kontroluje tvar adresy, kterou nikdo
zatím neviděl v provozu. Tenhle skript do hotového balíku zavede po jedné
chybě a ověří, že ji brána shodí.

Spouštět z kořene projektu:
    python src/mutace_export_mapa.py --solution <balik.zip>
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
    with zipfile.ZipFile(zip_cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klic = next(n for n in polozky
                if n.replace("\\", "/").startswith(f"Workflows/{FLOW}"))
    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    puvodni = json.dumps(flow, ensure_ascii=False, sort_keys=True)
    zmena(flow["properties"]["definition"]["actions"])
    novy = json.dumps(flow, ensure_ascii=False, sort_keys=True)
    # Mutace, která se do definice netrefí (změní se tvar výrazu a `str.replace`
    # přestane nacházet), by se tvářila jako platný test. Zelená brána nad
    # nezměněným balíkem nedokazuje nic.
    if puvodni == novy:
        raise SystemExit("CHYBA: mutace nic nezměnila — test by nic nedokazoval")
    polozky[klic] = json.dumps(flow, ensure_ascii=False).encode("utf-8")

    with zipfile.ZipFile(zip_cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, obsah in polozky.items():
            balik.writestr(jmeno, obsah)


def primy_odkaz(akce):
    """Adresa mapy vede rovnou na .html — soubor se stáhne místo zobrazení."""
    akce["Adresa"]["inputs"] = (
        "@if(equals(triggerBody()['text'], '__mapa__'), "
        "concat(outputs('Cesta_webu'), '/SiteAssets/procesni_mapa.html'), "
        "concat(outputs('Cesta_webu'), '/SiteAssets/', outputs('Jmeno')))")


def neenkodovana_cesta(akce):
    """Parametr id se pošle bez URL-enkódování."""
    akce["Adresa"]["inputs"] = akce["Adresa"]["inputs"].replace(
        "encodeUriComponent(concat(outputs('Cesta_webu'), '/SiteAssets/procesni_mapa.html'))",
        "concat(outputs('Cesta_webu'), '/SiteAssets/procesni_mapa.html')")


def spatny_parent(akce):
    """parent ukazuje na web, ne na složku se souborem."""
    akce["Adresa"]["inputs"] = akce["Adresa"]["inputs"].replace(
        "encodeUriComponent(concat(outputs('Cesta_webu'), '/SiteAssets'))",
        "encodeUriComponent(outputs('Cesta_webu'))")


def zapis_mimo_podminku(akce):
    """Zápis souboru vyskočí z podmínky — v režimu mapy by přepsal mapu."""
    akce["Uloz"] = akce["Ulozeni"]["actions"]["Uloz"]
    akce["Uloz"]["runAfter"] = {"Dokument": ["Succeeded"]}
    akce["Ulozeni"] = {"type": "Compose", "inputs": "nic",
                       "runAfter": {"Dokument": ["Succeeded"]}}


def podminka_bez_rezimu(akce):
    """Podmínka zápisu přestane režim mapy vylučovat."""
    akce["Ulozeni"]["expression"] = {"equals": ["@outputs('Jmeno')", "x"]}


def rezim_v_exportu(akce):
    """Běžný export dostane adresu mapy — záměna větví."""
    akce["Adresa"]["inputs"] = akce["Adresa"]["inputs"].replace(
        "@if(equals(triggerBody()['text'], '__mapa__')", "@if(true")


def bez_nahrad_enkodovani(akce):
    """Cesta se enkóduje jen přes encodeUriComponent, bez %2D/%5F/%2E."""
    vyraz = akce["Adresa"]["inputs"]
    for kod in ("%2D", "%5F", "%2E"):
        znak = chr(int(kod[1:], 16))
        vyraz = vyraz.replace(f"replace(", "", 1).replace(
            f", '{znak}', '{kod}')", "", 1)
    akce["Adresa"]["inputs"] = vyraz


MUTACE = [
    ("adresa mapy jako přímý odkaz na .html", primy_odkaz),
    ("enkódování bez náhrad %2D/%5F/%2E", bez_nahrad_enkodovani),
    ("cesta v parametru id není enkódovaná", neenkodovana_cesta),
    ("parent ukazuje jinam než na složku souboru", spatny_parent),
    ("zápis souboru mimo podmínku", zapis_mimo_podminku),
    ("podmínka zápisu nevylučuje režim mapy", podminka_bez_rezimu),
    ("běžný export vrací adresu mapy", rezim_v_exportu),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True)
    argumenty = parser.parse_args()

    hlidane = 0
    for popis, zmena in MUTACE:
        with tempfile.TemporaryDirectory() as docasny:
            kopie = Path(docasny) / "mutace.zip"
            shutil.copy(argumenty.solution, kopie)
            uprav_flow(kopie, zmena)
            beh = subprocess.run(
                [sys.executable, "src/check_export_flow.py", "--solution", str(kopie)],
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
