"""Kontrola přebalené solution před importem do Power Platform.

Porovnává výstup z src/build_app.py proti vstupní solution: co se změnit mělo
(obrazovky, verze) i co se změnit nesmělo (publisher, připojení na listy).

Spouštět z kořene projektu:  python src/check_solution.py
Návratový kód 0 = v pořádku, 1 = nalezena chyba.
"""

import json
import re
import sys
import zipfile
from pathlib import Path

import argparse

_p = argparse.ArgumentParser()
_p.add_argument("--vstup", default="input/procesnimapa_1_0_0_2 (2).zip")
_p.add_argument("--vystup", default="deploy/procesnimapa_1_0_0_3.zip")
_a = _p.parse_args()
VSTUP = Path(_a.vstup)
VYSTUP = Path(_a.vystup)

OCEKAVANE_OBRAZOVKY = {"scr_Seznam", "scr_Detail", "scr_Vazby"}
OCEKAVANE_LISTY = {"Agendy", "Procesy", "Dílčí procesy", "Aktivity", "Vazba aktivita–dílčí proces"}

chyby = []
kontrol = 0


def overit(podminka, popis):
    global kontrol
    kontrol += 1
    if not podminka:
        chyby.append(popis)


def cti(balik, jmeno):
    for polozka in balik.namelist():
        if polozka.replace("\\", "/").endswith(jmeno):
            return balik.read(polozka).decode("utf-8-sig")
    return None


def nacti_msapp(solution_zip):
    with zipfile.ZipFile(solution_zip) as balik:
        msappy = [n for n in balik.namelist() if n.replace("\\", "/").endswith(".msapp")]
        if len(msappy) != 1:
            return None, len(msappy)
        data = balik.read(msappy[0])
    docasny = Path("runs/app_build/_kontrola.msapp")
    docasny.parent.mkdir(parents=True, exist_ok=True)
    docasny.write_bytes(data)
    return zipfile.ZipFile(docasny), 1


def guidy_listu(text_customizations):
    """Vytáhne z ConnectionReferences dvojice název listu -> GUID."""
    shoda = re.search(r"<ConnectionReferences>(.*?)</ConnectionReferences>", text_customizations, re.S)
    if not shoda:
        return {}
    surovy = shoda.group(1).replace("&quot;", '"').replace("&amp;", "&")
    nalezene = {}
    for jmeno, guid in re.findall(r'"([^"]+)"\s*:\s*\{\s*"tableName"\s*:\s*"([0-9a-f-]{36})"', surovy):
        nalezene[jmeno] = guid
    return nalezene


def main():
    for cesta in (VSTUP, VYSTUP):
        if not cesta.exists():
            print(f"CHYBA: chybí {cesta}")
            return 1

    vstupni = zipfile.ZipFile(VSTUP)
    vystupni = zipfile.ZipFile(VYSTUP)

    # --- manifest solution ---
    manifest = cti(vystupni, "solution.xml")
    overit(manifest is not None, "solution.xml ve výstupu chybí")
    if manifest:
        overit("<Managed>0</Managed>" in manifest, "solution není unmanaged (<Managed>0</Managed>)")
        overit("<UniqueName>mpsv</UniqueName>" in manifest, "publisher není 'mpsv'")
        overit("<CustomizationPrefix>mpsv</CustomizationPrefix>" in manifest, "prefix není 'mpsv'")
        verze = re.search(r"<Version>([^<]+)</Version>", manifest)
        overit(verze is not None and verze.group(1) != "1.0.0.1",
               "verze solution se proti vstupu nezvýšila — import by neproběhl jako upgrade")

    # --- připojení na listy se nesmělo změnit ---
    zdroj_custom = cti(vstupni, "customizations.xml")
    cil_custom = cti(vystupni, "customizations.xml")
    overit(cil_custom is not None, "customizations.xml ve výstupu chybí")
    if zdroj_custom and cil_custom:
        puvodni = guidy_listu(zdroj_custom)
        nove = guidy_listu(cil_custom)
        overit(set(nove) >= OCEKAVANE_LISTY,
               f"v connection reference chybí listy: {sorted(OCEKAVANE_LISTY - set(nove))}")
        overit(puvodni == nove,
               "GUIDy připojených listů se proti vstupní solution změnily")

    # --- obsah canvas appky ---
    msapp, pocet = nacti_msapp(VYSTUP)
    overit(msapp is not None, f"ve výstupu není právě jeden .msapp (nalezeno {pocet})")
    if msapp:
        polozky = [n.replace("\\", "/") for n in msapp.namelist()]

        packed = cti(msapp, "packed.json")
        overit(packed is not None, "v .msapp chybí packed.json (nebalil to pac?)")
        if packed:
            overit(json.loads(packed).get("LoadConfiguration", {}).get("LoadFromYaml") is True,
                   "packed.json nemá LoadFromYaml=true — Studio by načetlo zastaralé Controls/*.json")

        nalezene = {Path(p).name.replace(".pa.yaml", "") for p in polozky if p.endswith(".pa.yaml")}
        overit(OCEKAVANE_OBRAZOVKY <= nalezene,
               f"v .msapp chybí obrazovky: {sorted(OCEKAVANE_OBRAZOVKY - nalezene)}")
        overit("Screen1" not in nalezene, "v .msapp zůstala výchozí prázdná obrazovka Screen1")
        overit("App" in nalezene, "v .msapp chybí App.pa.yaml")

        stav = cti(msapp, "_EditorState.pa.yaml")
        overit(stav is not None and "Screen1" not in stav,
               "ScreensOrder stále odkazuje na Screen1")
        if stav:
            for obrazovka in OCEKAVANE_OBRAZOVKY:
                overit(obrazovka in stav, f"ScreensOrder neobsahuje {obrazovka}")

        # datové zdroje musí zůstat připojené i uvnitř appky
        datasources = cti(msapp, "References/DataSources.json")
        if datasources:
            jmena = {d.get("Name") for d in json.loads(datasources).get("DataSources", [])}
            overit(OCEKAVANE_LISTY <= jmena,
                   f"v appce chybí datové zdroje: {sorted(OCEKAVANE_LISTY - jmena)}")

        # každý použitý control musí mít definici šablony, jinak Studio appku
        # neotevře a ohlásí to jako chybu YAML (past z importu 1.0.0.2)
        NAZEV_SABLONY = {"Label": "label", "Gallery": "gallery", "Rectangle": "rectangle",
                         "Image": "image", "Icon": "icon", "Timer": "timer",
                         "Button": "button", "TextInput": "text", "DropDown": "dropdown"}
        sablony_json = cti(msapp, "Templates.json")
        if sablony_json:
            znamé = {x["Name"] for x in json.loads(sablony_json)["UsedTemplates"]}
            pouzite = set()
            for polozka in polozky:
                if polozka.endswith(".pa.yaml"):
                    for control in re.findall(r"Control:\s*(\S+)", cti(msapp, Path(polozka).name) or ""):
                        nazev = control.split("@")[0].split("/")[-1]
                        pouzite.add(NAZEV_SABLONY.get(nazev, nazev.lower()))
            overit(pouzite <= znamé,
                   f"chybí definice šablon pro controly: {sorted(pouzite - znamé)}")

        # politika projektu: žádné externí zdroje.
        # Komentáře se přeskakují — hlavičku s odkazem na dokumentaci píše do
        # každého souboru sám pac a za běhu se nikam nesahá.
        for polozka in polozky:
            if not polozka.endswith(".pa.yaml"):
                continue
            text = cti(msapp, Path(polozka).name)
            radky = [r for r in (text or "").splitlines() if not r.lstrip().startswith("#")]
            overit(not any("http://" in r or "https://" in r for r in radky),
                   f"{polozka} obsahuje externí URL")

    print(f"kontrol: {kontrol}, chyb: {len(chyby)}")
    for text in chyby:
        print(f"CHYBA: {text}")
    if chyby:
        print("\nNEPROŠLO — solution neimportovat")
        return 1
    print(f"\nOK — {VYSTUP} je připravená k importu jako upgrade")
    return 0


if __name__ == "__main__":
    sys.exit(main())
