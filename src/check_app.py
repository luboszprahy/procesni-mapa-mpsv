"""Kontrola zdrojů canvas appky (src/app_src/*.pa.yaml) proti schématu listů a delegaci.

Spouštět z kořene projektu:  python src/check_app.py
Návratový kód 0 = vše v pořádku, 1 = nalezena chyba.
"""

import io
import json
import re
import sys
from xml.etree import ElementTree
from pathlib import Path

import yaml

APP_SRC = Path("src/app_src")
SCHEMA = Path("src/schema.json")
SABLONY = Path("src/control_templates.json")

def nacti_typy():
    """Povolené hodnoty Control: -> název šablony. Ověřeno proti pa.yaml funkčních appek."""
    return json.loads(SABLONY.read_text(encoding="utf-8"))["typy"]

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

# Appka běží s příznakem supportcolumnnamesasidentifiers = True (Properties.json
# v .msapp), takže názvy sloupců se těmto funkcím předávají jako identifikátory.
# Řetězec na místě sloupce = chyba "Name isn't valid" / "invalid arguments".
# Hodnota = kolik prvních argumentů sloupec nenese.
SLOUPCOVE_FUNKCE = {
    "ShowColumns": 1,
    "DropColumns": 1,
    "RenameColumns": 1,
    "AddColumns": 1,
    "SortByColumns": 1,
    "GroupBy": 1,
    "Ungroup": 1,
    "Distinct": 1,
    "Search": 2,
}

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


def rozdel_argumenty(text):
    """Rozdělí seznam argumentů na nejvyšší úrovni — závorky a řetězce se přeskakují."""
    casti, hloubka, start, v_retezci = [], 0, 0, False
    for index, znak in enumerate(text):
        if znak == '"':
            v_retezci = not v_retezci
        elif v_retezci:
            continue
        elif znak in "([{":
            hloubka += 1
        elif znak in ")]}":
            hloubka -= 1
        elif znak == "," and hloubka == 0:
            casti.append(text[start:index])
            start = index + 1
    casti.append(text[start:])
    return [c.strip() for c in casti]


def kontrola_identifikatoru(vzorce):
    """Sloupec se v režimu identifikátorů nesmí předávat jako řetězec."""
    for cesta, prop, text in vzorce:
        for funkce, preskoc in SLOUPCOVE_FUNKCE.items():
            for shoda in re.finditer(rf"\b{funkce}\s*\(", text):
                zavorka = text.index("(", shoda.start())
                argumenty = rozdel_argumenty(argumenty_volani(text, zavorka))
                for argument in argumenty[preskoc:]:
                    if argument.startswith('"') and argument.endswith('"'):
                        chyby.append(
                            f"{cesta}.{prop}: {funkce}() dostává sloupec jako řetězec "
                            f"{argument} — appka běží s supportcolumnnamesasidentifiers, "
                            f"takže musí být identifikátor {argument.strip(chr(34))}"
                        )


def kontrola_vzorovych_dat(soubory, typy, vzorova):
    """Vlastnost, jejíž výchozí hodnota míří na vzorová data, musí být nastavená.

    Nenastavená vlastnost si vezme výchozí hodnotu ze šablony controlu — a ta
    u ComboBoxu odkazuje na ukázkový zdroj ComboBoxSample, který v appce
    neexistuje. Studio to hlásí až po importu jako "Name isn't valid".
    """
    for cesta in soubory:
        dokument = yaml.safe_load(io.open(cesta, encoding="utf-8"))
        for koren, obsah in (dokument or {}).items():
            if koren != "Screens":
                continue
            for _obrazovka, telo in obsah.items():
                for jmeno, definice, typ in prvky_se_typem(telo):
                    sablona = typy.get(typ)
                    nastavene = set(definice.get("Properties") or {})
                    for vlastnost, (vychozi, skryta) in vzorova.get(sablona, {}).items():
                        if vlastnost in nastavene:
                            continue
                        if skryta:
                            chyby.append(
                                f"{jmeno}: typ '{typ}' nelze authorovat z YAML — vlastnost "
                                f"'{vlastnost}' má výchozí hodnotu '{vychozi}' na vzorová data "
                                f"a přepsat ji nejde (hidden, Studio ji dopočítává při vazbě "
                                f"v návrháři). Použij jiný typ controlu."
                            )
                        else:
                            chyby.append(
                                f"{jmeno}.{vlastnost}: nenastaveno, takže se použije "
                                f"výchozí hodnota šablony '{vychozi}' odkazující na "
                                f"vzorová data, která v appce nejsou"
                            )


def nacti_vzorova_data():
    """Pro každou šablonu vrátí vlastnosti, jejichž výchozí hodnota míří na vzorová data."""
    data = json.loads(SABLONY.read_text(encoding="utf-8"))
    nalezene = {}
    for sablona in data["sablony"]:
        vlastnosti = {}
        for shoda in re.finditer(r'<property name="([^"]+)"([^>]*)>', sablona["Template"]):
            atributy = shoda.group(2)
            vychozi = re.search(r'defaultValue="([^"]*)"', atributy)
            if vychozi and "Sample" in vychozi.group(1):
                vlastnosti[shoda.group(1)] = (vychozi.group(1), 'hidden="true"' in atributy)
        if vlastnosti:
            nalezene[sablona["Name"]] = vlastnosti
    return nalezene


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
        for odkaz in re.findall(r"\b(gal_[A-Za-z0-9_]+|cmb_[A-Za-z0-9_]+|txt_[A-Za-z0-9_]+|drp_[A-Za-z0-9_]+|btn_[A-Za-z0-9_]+|lbl_[A-Za-z0-9_]+|ico_[A-Za-z0-9_]+|rec_[A-Za-z0-9_]+|sep_[A-Za-z0-9_]+|scr_[A-Za-z0-9_]+)\b", text):
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


def nacti_povolene_vlastnosti():
    """Pro každou šablonu controlu vrátí množinu vlastností, které lze nastavit.

    Nastavitelné jsou vlastní vlastnosti s direction="in" a zděděné includeProperty.
    Vlastnosti s direction="out" (a ty bez direction, např. dropdown.Value) Studio
    odmítne hláškou PA2108.
    """
    data = json.loads(SABLONY.read_text(encoding="utf-8"))
    povolene = {}
    for sablona in data["sablony"]:
        koren = ElementTree.fromstring(sablona["Template"])
        jmena = set(re.findall(r'<appMagic:includeProperty[^>]*name="([^"]+)"', sablona["Template"]))

        # Jen přímí potomci <properties> jsou vlastnosti controlu. Vnořené
        # <property> popisují sloupce dat (dropdown.Value uvnitř Items) a Studio
        # je jako vlastnost neuznává — právě na tom spadl import 1.0.0.3.
        for skupina in koren:
            if not skupina.tag.endswith("properties"):
                continue
            for vlastnost in skupina:
                if not vlastnost.tag.endswith("property"):
                    continue
                jmeno = vlastnost.get("name")
                # hidden="true" = vlastnost, kterou dopočítává Studio při vazbě
                # v návrháři (combobox.SearchItems, dropdown.Value). V YAML ji
                # nastavit nejde — packer skončí PA2108 a appka se neotevře.
                if vlastnost.get("hidden") == "true":
                    continue
                if jmeno and vlastnost.get("direction") != "out":
                    jmena.add(jmeno)
        povolene[sablona["Name"]] = jmena
    return povolene


def kontrola_vlastnosti(soubory, povolene, typy):
    """PA2108 — nastavovaná vlastnost musí u daného typu controlu existovat."""
    # vlastnosti, které nepatří controlu, ale zápisu v pa.yaml
    mimo = {"Control", "Variant", "Properties", "Children"}
    vzdy = {"Text", "Fill", "Color", "X", "Y", "Width", "Height", "Visible",
            "OnSelect", "Items", "Default", "Reset", "Tooltip", "DisplayMode"}

    for cesta in soubory:
        dokument = yaml.safe_load(io.open(cesta, encoding="utf-8"))
        for koren, obsah in (dokument or {}).items():
            if koren != "Screens":
                continue
            for jmeno_obrazovky, telo in obsah.items():
                for jmeno, definice, typ in prvky_se_typem(telo):
                    sablona = typy.get(typ)
                    if sablona is None:
                        chyby.append(
                            f"{jmeno}: neznámý typ controlu '{typ}'. Povolené tvary jsou "
                            f"{sorted(typy)} — bez prefixu Classic/ mapuje Studio control "
                            f"na modernější verzi a odmítne vlastnosti (PA2106/PA2108)"
                        )
                        continue
                    if sablona not in povolene:
                        continue
                    znama = povolene[sablona] | vzdy
                    for vlastnost in (definice.get("Properties") or {}):
                        if vlastnost in mimo:
                            continue
                        if vlastnost not in znama:
                            chyby.append(
                                f"{jmeno}.{vlastnost}: vlastnost '{vlastnost}' typ "
                                f"'{typ}' nemá (Studio hlásí PA2108)"
                            )


def prvky_se_typem(uzel):
    """Projde strom obrazovky a vrátí (jméno, definice, typ controlu)."""
    for polozka in (uzel.get("Children") or []):
        for jmeno, definice in polozka.items():
            typ = definice.get("Control")
            if typ:
                yield jmeno, definice, typ
            yield from prvky_se_typem(definice)


def kontrola_unikatnosti(soubory):
    """PA2110 — jména prvků musí být unikátní napříč celou appkou, ne jen obrazovkou."""
    kde = {}
    for cesta in soubory:
        dokument = yaml.safe_load(io.open(cesta, encoding="utf-8"))
        for koren, obsah in (dokument or {}).items():
            if koren != "Screens":
                continue
            for jmeno_obrazovky, telo in obsah.items():
                if jmeno_obrazovky in kde:
                    chyby.append(f"obrazovka '{jmeno_obrazovky}' je definovaná dvakrát")
                kde[jmeno_obrazovky] = cesta.name
                for jmeno, _definice, _typ in prvky_se_typem(telo):
                    if jmeno in kde:
                        chyby.append(
                            f"prvek '{jmeno}' už existuje v {kde[jmeno]} "
                            f"(znovu v {cesta.name}) — Studio hlásí PA2110"
                        )
                    else:
                        kde[jmeno] = cesta.name


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
    kontrola_unikatnosti(soubory)
    kontrola_identifikatoru(vzorce)
    kontrola_vlastnosti(soubory, nacti_povolene_vlastnosti(), nacti_typy())
    kontrola_vzorovych_dat(soubory, nacti_typy(), nacti_vzorova_data())

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
