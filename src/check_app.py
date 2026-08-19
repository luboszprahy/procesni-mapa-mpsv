"""Kontrola zdrojů canvas appky (src/app_src/*.pa.yaml) proti schématu listů a delegaci.

Spouštět z kořene projektu:  python src/check_app.py
Návratový kód 0 = vše v pořádku, 1 = nalezena chyba.
"""

import io
import json
import re
import sys
from pathlib import Path

import yaml

APP_SRC = Path("src/app_src")
SCHEMA = Path("src/schema.json")

# Zobrazované názvy datových zdrojů tak, jak je appka vidí v connection reference.
# Klíč = název ve vzorcích, hodnota = název listu v schema.json.
DATASOURCE_TO_LIST = {
    "Agendy": "Agendy",
    "Procesy": "Procesy",
    "Dílčí procesy": "DilciProcesy",
    "Aktivity": "Aktivity",
    "Vazba aktivita–dílčí proces": "AktivitaDilciProces",
}

# Sloupce, které SharePoint dodává sám a ve schématu nejsou.
VESTAVENE_SLOUPCE = {"ID", "Created", "Modified", "Author", "Editor"}

# Funkce, které SharePoint konektor nedelegoval by — nad velkými listy tiše ořežou na 2000.
NEDELEGOVATELNE = ["Search", "Distinct", "CountRows", "CountIf", "Sum", "Max", "Min", "AddColumns"]

# Listy, u kterých na delegaci opravdu záleží (rostou do tisíců).
VELKE_LISTY = ["Aktivity", "Vazba aktivita–dílčí proces"]

chyby = []
varovani = []


def nacti_schema():
    data = json.loads(SCHEMA.read_text(encoding="utf-8-sig"))
    return {
        spec["name"]: {c["name"] for c in spec.get("columns", [])}
        for spec in data["lists"]
    }


def projdi_stromy(soubory):
    """Vrátí (controly, vzorce) — jméno každého controlu a všechny textové hodnoty vlastností."""
    controly = set()
    obrazovky = set()
    vzorce = []

    def zanoreni(uzel, cesta):
        if isinstance(uzel, dict):
            for klic, hodnota in uzel.items():
                if klic == "Properties" and isinstance(hodnota, dict):
                    for prop, text in hodnota.items():
                        if isinstance(text, str):
                            vzorce.append((cesta, prop, text))
                elif klic == "Children" and isinstance(hodnota, list):
                    for polozka in hodnota:
                        if isinstance(polozka, dict):
                            for jmeno, telo in polozka.items():
                                controly.add(jmeno)
                                zanoreni(telo, jmeno)
                elif klic == "Control":
                    continue
                else:
                    zanoreni(hodnota, cesta)
        elif isinstance(uzel, list):
            for polozka in uzel:
                zanoreni(polozka, cesta)

    for cesta in soubory:
        try:
            dokument = yaml.safe_load(io.open(cesta, encoding="utf-8"))
        except yaml.YAMLError as chyba:
            chyby.append(f"{cesta.name}: YAML nelze načíst — {chyba}")
            continue
        if not isinstance(dokument, dict):
            chyby.append(f"{cesta.name}: kořen není mapování")
            continue
        for koren, obsah in dokument.items():
            if koren == "Screens":
                for jmeno, telo in obsah.items():
                    obrazovky.add(jmeno)
                    controly.add(jmeno)
                    zanoreni(telo, jmeno)
            elif koren == "App":
                controly.add("App")
                zanoreni(obsah, "App")
    return controly, obrazovky, vzorce


def bez_retezcu(text):
    """Vyhodí obsah řetězcových literálů, aby se slova z hlášek nepletla s identifikátory."""
    return re.sub(r'"[^"]*"', '""', text)


def argumenty_volani(text, pozice):
    """Vrátí text argumentů volání, jehož levá závorka je na `pozice`."""
    hloubka = 0
    for index in range(pozice, len(text)):
        if text[index] == "(":
            hloubka += 1
        elif text[index] == ")":
            hloubka -= 1
            if hloubka == 0:
                return text[pozice + 1:index]
    return text[pozice + 1:]


def kontrola_sloupcu(vzorce, schema):
    """Sloupce v Patch záznamech a ve filtrech musí existovat ve schématu cílového listu."""
    vsechny_sloupce = set().union(*schema.values()) | VESTAVENE_SLOUPCE

    for cesta, prop, syrovy in vzorce:
        text = bez_retezcu(syrovy)

        for ds_nazev, list_nazev in DATASOURCE_TO_LIST.items():
            znama = schema[list_nazev] | VESTAVENE_SLOUPCE
            citovany = re.escape(ds_nazev)
            vzor = rf"\b(Patch|Filter|LookUp|RemoveIf|Remove|Sort|SortByColumns|ShowColumns)\s*\(\s*'?{citovany}'?\s*[,)]"

            for shoda in re.finditer(vzor, text):
                zavorka = text.index("(", shoda.start())
                argumenty = argumenty_volani(text, zavorka)
                funkce = shoda.group(1)

                if funkce == "Patch":
                    # sloupce = klíče record literálů { sloupec: hodnota }
                    for sloupec in re.findall(r"[{,]\s*([A-Za-z][A-Za-z0-9_]*)\s*:", argumenty):
                        if sloupec == "Value":
                            continue
                        if sloupec not in znama:
                            chyby.append(
                                f"{cesta}.{prop}: Patch do '{ds_nazev}' zapisuje sloupec "
                                f"'{sloupec}', který v listu {list_nazev} není"
                            )
                else:
                    # sloupce = levé strany porovnání a hodnoty přístupu .Value
                    for sloupec in re.findall(r"\b([a-z][a-z0-9_]{2,})\s*(?:=|<>|\.Value)", argumenty):
                        if sloupec.startswith(("var", "col")):
                            continue
                        if sloupec not in znama:
                            chyby.append(
                                f"{cesta}.{prop}: {funkce} nad '{ds_nazev}' pracuje se sloupcem "
                                f"'{sloupec}', který v listu {list_nazev} není"
                            )

        # čtení přes ThisItem.<sloupec> — slabší kontrola proti překlepu
        for sloupec in re.findall(r"ThisItem\.([A-Za-z][A-Za-z0-9_]*)", text):
            if sloupec in ("IsSelected", "Value"):
                continue
            if sloupec not in vsechny_sloupce:
                chyby.append(f"{cesta}.{prop}: ThisItem.{sloupec} — takový sloupec nemá žádný list")


def kontrola_odkazu(vzorce, controly):
    """Odkaz tvaru neco_jineho.Vlastnost musí mířit na existující control."""
    povolene_predpony = {"ThisItem", "Parent", "Self", "Icon", "Color", "Font", "FontWeight",
                         "TextMode", "VerticalAlign", "Align", "ScreenTransition",
                         "NotificationType", "DisplayMode", "RGBA", "PowerAppsTheme",
                         "FirstError", "Defaults", "Blank"}
    for cesta, prop, text in vzorce:
        for odkaz in re.findall(r"\b(gal_[A-Za-z0-9_]+|txt_[A-Za-z0-9_]+|drp_[A-Za-z0-9_]+|btn_[A-Za-z0-9_]+|lbl_[A-Za-z0-9_]+|ico_[A-Za-z0-9_]+|rec_[A-Za-z0-9_]+|sep_[A-Za-z0-9_]+|scr_[A-Za-z0-9_]+)\b", text):
            if odkaz in povolene_predpony:
                continue
            if odkaz not in controly:
                chyby.append(f"{cesta}.{prop}: odkaz na neexistující prvek '{odkaz}'")


def kontrola_delegace(vzorce):
    """Nad velkými listy se nesmí objevit nedelegovatelná funkce ani Sort v Items galerie."""
    for cesta, prop, text in vzorce:
        for list_nazev in VELKE_LISTY:
            if list_nazev not in text:
                continue
            for funkce in NEDELEGOVATELNE:
                # Sort je delegovatelný, Search není; hlídáme jen skutečné volání funkce.
                if re.search(rf"\b{funkce}\s*\(", text):
                    # výjimka: CountRows nad gal_*.AllItems pracuje s už načtenou stránkou
                    if funkce == "CountRows" and "AllItems" in text:
                        continue
                    chyby.append(
                        f"{cesta}.{prop}: {funkce}() nad '{list_nazev}' není delegovatelné"
                    )
        if prop == "Items" and cesta.startswith("gal_") and re.search(r"\bSort\s*\(", text):
            varovani.append(f"{cesta}.Items: Sort v Items se přepočítá při každém překreslení")


def kontrola_navigace(vzorce, obrazovky):
    for cesta, prop, text in vzorce:
        for cil in re.findall(r"Navigate\(\s*([A-Za-z0-9_]+)", text):
            if cil not in obrazovky:
                chyby.append(f"{cesta}.{prop}: Navigate na neexistující obrazovku '{cil}'")


def main():
    soubory = sorted(APP_SRC.glob("*.pa.yaml"))
    if not soubory:
        print("CHYBA: v src/app_src nejsou žádné .pa.yaml soubory")
        return 1

    schema = nacti_schema()
    controly, obrazovky, vzorce = projdi_stromy(soubory)

    kontrola_sloupcu(vzorce, schema)
    kontrola_odkazu(vzorce, controly)
    kontrola_delegace(vzorce)
    kontrola_navigace(vzorce, obrazovky)

    print(f"souborů: {len(soubory)}   obrazovek: {len(obrazovky)}   prvků: {len(controly)}   vzorců: {len(vzorce)}")
    for obrazovka in sorted(obrazovky):
        print(f"  - {obrazovka}")

    for text in varovani:
        print(f"VAROVÁNÍ: {text}")
    for text in chyby:
        print(f"CHYBA: {text}")

    if chyby:
        print(f"\nNEPROŠLO — {len(chyby)} chyb")
        return 1
    print("\nOK — YAML se parsuje, sloupce sedí na schéma, odkazy i navigace platí, delegace čistá")
    return 0


if __name__ == "__main__":
    sys.exit(main())
