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

# Vědomé ústupky z delegace: (control, vlastnost, funkce) -> proč se to smí.
# Hlásí se jako varování, ne chyba — ale nesmí zmizet z výstupu, aby se na ně
# při růstu dat přišlo dřív, než začnou tiše ořezávat.
VYJIMKY_DELEGACE = {
    ("gal_Aktivity", "Items", "Search"): (
        "fulltext přes celý název i kód; SharePoint konektor deleguje jen "
        "StartsWith, takže hledání kdekoli uvnitř řetězce delegovat nelze. "
        "Search je proto navlečený AŽ NA VÝSLEDEK delegovaného Filter — sekce, "
        "útvar a stav zúží dotaz na serveru nad celým rejstříkem a fulltext "
        "běží nad tím, co přijde. Do 2 000 aktivit je výsledek úplný, nad tím "
        "prohledá jen první okno a lbl_ChipFiltr na to oranžově upozorní. "
        "Až rejstřík povyroste, je náhradou fulltext v publikované HTML mapě "
        "nebo pomocný indexovaný sloupec s normalizovaným názvem"
    ),
}

# Appka běží s příznakem supportcolumnnamesasidentifiers = True (Properties.json
# v .msapp), takže názvy sloupců se těmto funkcím předávají jako identifikátory.
# Řetězec na místě sloupce = chyba "Name isn't valid" / "invalid arguments".
# Hodnota = kolik prvních argumentů sloupec nenese.
SLOUPCOVE_FUNKCE = {
    "ShowColumns": 1,
    "DropColumns": 1,
    "RenameColumns": 1,
    "AddColumns": 1,
    # SortByColumns tady schválně NENÍ: příznak supportcolumnnamesasidentifiers
    # na ni nedopadá a identifikátor odmítne ("name isn't valid", ověřeno
    # importem 1.0.0.13). Bere řetězec. Appka ji proto vůbec nepoužívá —
    # řadí se přes Sort(), který dostává výraz a je jednoznačný v obou režimech.
    "GroupBy": 1,
    "Ungroup": 1,
    "Distinct": 1,
    "Search": 2,
}

chyby = []
varovani = []


class BezDuplicit(yaml.SafeLoader):
    """SafeLoader, který duplicitní klíč nahlásí místo tichého přepsání.

    PyYAML poslední výskyt tiše vyhraje, ale packer canvas appky skončí
    PA1001 „Duplicate name ... used" a appka se neotevře. Kontrola tedy
    musí být přísnější než parser, jinou past neuvidí.
    """


def _mapovani(nacitac, uzel, deep=False):
    klice = set()
    for klic_uzel, _ in uzel.value:
        klic = nacitac.construct_object(klic_uzel, deep=deep)
        if klic in klice:
            raise yaml.constructor.ConstructorError(
                None, None,
                f"duplicitní klíč '{klic}' (řádek {klic_uzel.start_mark.line + 1})",
                uzel.start_mark)
        klice.add(klic)
    return yaml.SafeLoader.construct_mapping(nacitac, uzel, deep)


BezDuplicit.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    lambda nacitac, uzel: _mapovani(nacitac, uzel))


def nacti_yaml(cesta):
    """Načte pa.yaml; chybu zapíše jako nález, ať výstup zůstane čitelný."""
    try:
        return yaml.load(io.open(cesta, encoding="utf-8"), Loader=BezDuplicit)
    except yaml.YAMLError as chyba:
        popis = " ".join(str(chyba).split())
        if not any(popis in x for x in chyby):
            chyby.append(f"{Path(cesta).name}: {popis}")
        return {}





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
            dokument = nacti_yaml(cesta)
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
        dokument = nacti_yaml(cesta)
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


def bez_retezcu_presne(text):
    """Vyhodí obsah řetězců; vrátí (zbytek, chyba). \"\" uvnitř je escapovaná uvozovka."""
    zbytek, index, v_retezci = [], 0, False
    while index < len(text):
        znak = text[index]
        if znak == '"':
            if v_retezci and index + 1 < len(text) and text[index + 1] == '"':
                index += 2
                continue
            v_retezci = not v_retezci
            index += 1
            continue
        if not v_retezci:
            zbytek.append(znak)
        index += 1
    if v_retezci:
        return "".join(zbytek), "neuzavřený řetězec"
    hloubka = 0
    for znak in zbytek:
        if znak == "(":
            hloubka += 1
        elif znak == ")":
            hloubka -= 1
            if hloubka < 0:
                return "".join(zbytek), "závorka navíc"
    if hloubka:
        return "".join(zbytek), f"chybí {hloubka}× zavírací závorka"
    return "".join(zbytek), None


def kontrola_barev(vzorce):
    """RGBA() musí dostat čtyři čísla — překlep v barvě jinak projde až do Studia."""
    for cesta, prop, text in vzorce:
        for shoda in re.finditer(r"RGBA\s*\(", text):
            zavorka = text.index("(", shoda.start())
            argumenty = rozdel_argumenty(argumenty_volani(text, zavorka))
            spatne = [a for a in argumenty if not re.fullmatch(r"-?\d+(\.\d+)?%?", a)]
            if len(argumenty) != 4 or spatne:
                chyby.append(
                    f"{cesta}.{prop}: RGBA{tuple(argumenty)} — čekám čtyři čísla"
                )


def kontrola_syntaxe(vzorce):
    """Uvozovky a závorky musí vyjít.

    Typická past: text má typografickou uvozovku otevírací („) a ASCII zavírací
    ("). Ta řetězec ukončí dřív, Power Fx pak hlásí „Expected operator" a lavinu
    navazujících „Name isn't valid" — chyb je pak desítky a žádná neukazuje
    na skutečné místo.
    """
    for cesta, prop, text in vzorce:
        if not isinstance(text, str) or not text.lstrip().startswith("="):
            continue
        _, chyba = bez_retezcu_presne(text)
        if chyba:
            ukazka = " ".join(text.split())[:110]
            chyby.append(f"{cesta}.{prop}: {chyba} — {ukazka}")


def kontrola_razeni(vzorce):
    """Pořadí řazení musí být kvalifikované — holé Descending Studio nezná."""
    for cesta, prop, text in vzorce:
        for funkce in ("Sort", "SortByColumns"):
            for shoda in re.finditer(rf"\b{funkce}\s*\(", text):
                zavorka = text.index("(", shoda.start())
                for argument in rozdel_argumenty(argumenty_volani(text, zavorka)):
                    if argument in ("Ascending", "Descending"):
                        chyby.append(
                            f"{cesta}.{prop}: {funkce}() dostává '{argument}' bez kvalifikace — "
                            f"musí být SortOrder.{argument}, jinak Studio hlásí "
                            f"„Name isn't valid\""
                        )


def kontrola_obsahovych_vychozich(soubory, typy, lokalizovane):
    """Obsahová vlastnost s lokalizovanou výchozí hodnotou musí být nastavená.

    Nenastavený `Default` u textového pole se vyplní překladem
    ##Text_DefaultValue_Default## = „Text input". Vypadá to jako placeholder,
    ale je to skutečná hodnota: filtr nad takovým polem pak nic nenajde
    a appka tvrdí, že data nejsou.
    """
    for cesta in soubory:
        dokument = nacti_yaml(cesta)
        for koren, obsah in (dokument or {}).items():
            if koren != "Screens":
                continue
            for _obrazovka, telo in obsah.items():
                for jmeno, definice, typ in prvky_se_typem(telo):
                    sablona = typy.get(typ)
                    nastavene = set(definice.get("Properties") or {})
                    for vlastnost in lokalizovane.get(sablona, ()):
                        if vlastnost not in nastavene:
                            chyby.append(
                                f"{jmeno}.{vlastnost}: nenastaveno — doplní se překlad "
                                f"(u textového pole „Text input“), který se chová jako "
                                f"zadaná hodnota a tiše rozbije filtry"
                            )


def nacti_lokalizovane_vychozi():
    """Obsahové vlastnosti, jejichž výchozí hodnota je lokalizační token ##…##."""
    data = json.loads(SABLONY.read_text(encoding="utf-8"))
    nalezene = {}
    for sablona in data["sablony"]:
        jmena = set()
        for shoda in re.finditer(r'<property name="(Default|Text|Items)"([^>]*)>', sablona["Template"]):
            vychozi = re.search(r'defaultValue="(##[^"]*##)"', shoda.group(2))
            if vychozi:
                jmena.add(shoda.group(1))
        if jmena:
            nalezene[sablona["Name"]] = jmena
    return nalezene


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


def sloupce_kolekci(vzorce):
    """Sloupce, které si appka vyrábí sama — record literály v Collect nad col*.

    Galerie nad vlastní kolekcí (colStrom na přehledu) má sloupce, které v žádném
    SharePoint listu nejsou. Bez tohohle by kontrola ThisItem.* hlásila každý
    z nich jako překlep.
    """
    nalezene = set()
    for _cesta, _prop, syrovy in vzorce:
        text = bez_retezcu(syrovy)
        for shoda in re.finditer(r"\b(?:Clear)?Collect\s*\(\s*(col[A-Za-z0-9_]*)", text):
            zavorka = text.index("(", shoda.start())
            argumenty = argumenty_volani(text, zavorka)
            nalezene |= set(re.findall(r"[{,]\s*([A-Za-z][A-Za-z0-9_]*)\s*:", argumenty))
    return nalezene


def kontrola_sloupcu(vzorce, schema):
    """Sloupce v Patch záznamech a ve filtrech musí existovat ve schématu cílového listu."""
    vsechny_sloupce = set().union(*schema.values()) | VESTAVENE_SLOUPCE | sloupce_kolekci(vzorce)

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
                chyby.append(f"{cesta}.{prop}: ThisItem.{sloupec} — takový sloupec nemá "
                             f"žádný list ani kolekce")


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
                for shoda in re.finditer(rf"\b{funkce}\s*\(", text):
                    # Rozhoduje, co dostane TOHLE volání, ne co je jinde ve vzorci:
                    # CountRows(Filter(colAkt, …)) ve stejném OnVisible, kde se
                    # kolekce plní ze SharePointu, s delegací nemá nic společného.
                    zavorka = text.index("(", shoda.start())
                    uvnitr = argumenty_volani(text, zavorka)
                    if list_nazev not in uvnitr:
                        continue
                    # výjimka: CountRows nad gal_*.AllItems pracuje s už načtenou stránkou
                    if funkce == "CountRows" and "AllItems" in uvnitr:
                        continue
                    duvod = VYJIMKY_DELEGACE.get((cesta, prop, funkce))
                    if duvod:
                        varovani.append(
                            f"{cesta}.{prop}: {funkce}() nad '{list_nazev}' není "
                            f"delegovatelné — povolená výjimka: {duvod}"
                        )
                    else:
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
        dokument = nacti_yaml(cesta)
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
        dokument = nacti_yaml(cesta)
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


# Prvky, které se překrývat SMĚJÍ: podklady (rec_) leží pod popisky z definice
# a překryvná vrstva galerie leží nad celým řádkem záměrně.
PREKRYV_POVOLEN = {"lbl_RadekPrekryv", "lbl_StromPrekryv", "lbl_RadekPrekryvC"}


def kontrola_prekryvu(soubory):
    """Dva prvky s obsahem nesmějí ležet přes sebe.

    Vzniklo z lbl_l_Vazby (20.08.2026): popisek široký 740 px zasahoval do
    nabídky Stav a seděl na stejné pozici jako jiný popisek. Studio ani packer
    to nehlásí, appka se otevře — vidí to až člověk na snímku obrazovky.

    Počítá se jen tam, kde jsou všechny čtyři souřadnice obou prvků čísla;
    výrazy typu `Parent.Width - 80` se přeskakují, protože bez znalosti šířky
    plochy by kontrola jen hádala.
    """
    obsahove = ("lbl_", "txt_", "drp_", "btn_", "cmb_", "ico_")

    def sourozenci(uzel):
        """Skupiny prvků se společným rodičem. Souřadnice prvku uvnitř galerie
        jsou relativní k šabloně řádku, takže srovnávat je s prvky obrazovky
        nedává smysl."""
        skupina = []
        for polozka in uzel or []:
            for jmeno, definice in polozka.items():
                skupina.append((jmeno, definice))
                if definice.get("Children"):
                    yield from sourozenci(definice["Children"])
        if skupina:
            yield skupina

    for cesta in soubory:
        dokument = nacti_yaml(cesta)
        for koren, obsah in (dokument or {}).items():
            if koren != "Screens":
                continue
            for jmeno_obrazovky, telo in obsah.items():
                for skupina in sourozenci(telo.get("Children")):
                    obdelniky = []
                    for jmeno, definice in skupina:
                        if not jmeno.startswith(obsahove) or jmeno in PREKRYV_POVOLEN:
                            continue
                        vlastnosti = definice.get("Properties") or {}
                        souradnice = []
                        for klic in ("X", "Y", "Width", "Height"):
                            hodnota = str(vlastnosti.get(klic, "")).lstrip("=").strip()
                            souradnice.append(int(hodnota) if hodnota.isdigit() else None)
                        if any(s is None for s in souradnice):
                            continue
                        # Prvky skryté za stejné podmínky se nepřekrývají za běhu.
                        viditelnost = str(vlastnosti.get("Visible", "")).strip()
                        obdelniky.append((jmeno, souradnice, viditelnost))

                    porovnej(jmeno_obrazovky, obdelniky)


def porovnej(jmeno_obrazovky, obdelniky):
    for i, (jmeno_a, (xa, ya, wa, ha), va) in enumerate(obdelniky):
        for jmeno_b, (xb, yb, wb, hb), vb in obdelniky[i + 1:]:
            prekryv_x = min(xa + wa, xb + wb) - max(xa, xb)
            prekryv_y = min(ya + ha, yb + hb) - max(ya, yb)
            if prekryv_x <= 0 or prekryv_y <= 0:
                continue
            chyby.append(
                f"{jmeno_obrazovky}: '{jmeno_a}' a '{jmeno_b}' se překrývají "
                f"o {prekryv_x}×{prekryv_y} px — Studio to nehlásí, "
                f"pozná se to až na snímku obrazovky"
                + ("" if va != vb or not va else
                   f" (obojí Visible: {va}, takže i za běhu naráz)")
            )


# Mazání v galerii, které se smí obejít bez potvrzení: (obrazovka, control) -> proč.
# Hlásí se jako varování, ne chyba — smysl je, aby každé takové místo bylo
# vidět a dalo se znovu posoudit, ne aby zmizelo.
VYJIMKY_MAZANI = {
    ("scr_Vazby", "ico_Odebrat"): (
        "odebírá jen zařazení aktivity do dalšího dílčího procesu, ne data — "
        "vrátí se jedním kliknutím na + v nabídce vedle, a primární vazbu "
        "vzorec odebrat nedovolí. Dialog by u vratné operace jen překážel"
    ),
}


def kontrola_potvrzeni_mazani(soubory):
    """Uvnitř galerie se nesmí mazat — jen otevřít potvrzovací dialog.

    Řádek galerie se dá trefit omylem (je celý klikací a ikony jsou malé),
    takže `Remove`/`RemoveIf` přímo v šabloně řádku znamená nevratnou ztrátu
    dat na jeden překlep. Mazat smí až tlačítko dialogu, které je jinde na
    obrazovce a vyžaduje druhé kliknutí.

    Vratné operace (odebrání vazby) patří do VYJIMKY_MAZANI a hlásí se jako
    varování.
    """
    def uvnitr_galerie(uzel):
        for polozka in uzel or []:
            for jmeno, definice in polozka.items():
                deti = definice.get("Children")
                if jmeno.startswith("gal_"):
                    yield from vsechny(deti)
                elif deti:
                    yield from uvnitr_galerie(deti)

    def vsechny(uzel):
        for polozka in uzel or []:
            for jmeno, definice in polozka.items():
                yield jmeno, definice
                yield from vsechny(definice.get("Children"))

    for cesta in soubory:
        dokument = nacti_yaml(cesta)
        for koren, obsah in (dokument or {}).items():
            if koren != "Screens":
                continue
            for jmeno_obrazovky, telo in obsah.items():
                for jmeno, definice in uvnitr_galerie(telo.get("Children")):
                    for prop, text in (definice.get("Properties") or {}).items():
                        # Maže se jen to, co míří na datový zdroj. RemoveIf nad
                        # lokální kolekcí (colOtevrene drží, co je ve stromu
                        # rozbalené) žádná data neztratí a dialog by u ní byl
                        # nesmysl.
                        if not re.search(r"\bRemove(If)?\s*\(\s*(?!col[A-Za-z0-9_]*\s*[,)])",
                                         str(text)):
                            continue
                        duvod = VYJIMKY_MAZANI.get((jmeno_obrazovky, jmeno))
                        if duvod:
                            varovani.append(
                                f"{jmeno_obrazovky}: '{jmeno}.{prop}' maže uvnitř galerie "
                                f"bez potvrzení — povolená výjimka: {duvod}"
                            )
                        else:
                            chyby.append(
                                f"{jmeno_obrazovky}: '{jmeno}.{prop}' maže přímo uvnitř "
                                "galerie — řádek se dá trefit omylem, takže mazat smí "
                                "až tlačítko potvrzovacího dialogu"
                            )


def kontrola_adresy_mapy(vzorce):
    """varMapaUrl nesmí být přímý odkaz na soubor v knihovně.

    Ověřeno 20.08.2026: na přímou cestu `…/SiteAssets/procesni_mapa.html`
    pošle SharePoint kvůli Strict browser file handling
    `Content-Disposition: attachment` a mapa se místo zobrazení stáhne.
    Zobrazí ji až náhled knihovny (`AllItems.aspx?id=<cesta>`) nebo stránka
    s web partem Vložit. Chyba je tichá — appka běží, tlačítko funguje,
    jen výsledek skončí v Downloads.
    """
    for cesta, prop, text in vzorce:
        for adresa in re.findall(r'Set\(\s*varMapaUrl\s*,\s*"([^"]*)"', text):
            if not adresa:
                continue
            bez_dotazu = adresa.split("?", 1)[0]
            if bez_dotazu.lower().endswith((".html", ".htm")):
                chyby.append(
                    f"{cesta}.{prop}: varMapaUrl míří přímo na soubor "
                    f"({bez_dotazu.rsplit('/', 1)[-1]}) — SharePoint ho pošle jako "
                    "přílohu a mapa se stáhne místo zobrazení. Použij adresu "
                    "náhledu knihovny (AllItems.aspx?id=…) nebo stránky s web "
                    "partem Vložit."
                )
            if not adresa.lower().startswith("https://"):
                chyby.append(f"{cesta}.{prop}: varMapaUrl není https adresa")


def kontrola_stareho_result(vzorce):
    """`Split` i `Distinct` vracejí sloupec `Value`, ne `Result`.

    `Result` je starý název, který dnešní Power Fx neuzná — appka se pak
    neotevře a chyba se projeví až ve Studiu, protože packer ji nechytí.
    Správa notifikací na tom spálila tři buildy (1.0.0.30), proto to hlídá
    brána. Řetězce se vyhazují, aby popisek se slovem Result neplašil.
    """
    for cesta, prop, syrovy in vzorce:
        if re.search(r"\bResult\b", bez_retezcu(syrovy)):
            chyby.append(
                f"{cesta}.{prop}: identifikátor 'Result' — Split() i Distinct() "
                f"vracejí sloupec 'Value'. 'Result' je starý název, appka se "
                f"s ním ve Studiu neotevře"
            )


def schema_kolekci(vzorce):
    """col* založená jako ClearCollect(colX, ShowColumns(zdroj, a, b)) -> {a, b}.

    Takové kolekci Power Fx zapamatuje schéma z prvního plnění. Záznam, který
    do ní přiteče později s jiným kompletem sloupců, appku buď neotevře, nebo
    v galerii tiše ukáže prázdná pole tam, kde ostatní řádky mají hodnotu.
    """
    nalezene = {}
    for _cesta, _prop, syrovy in vzorce:
        text = bez_retezcu(syrovy)
        for shoda in re.finditer(
                r"\bClearCollect\s*\(\s*(col[A-Za-z0-9_]*)\s*,\s*ShowColumns\s*\(", text):
            argumenty = rozdel_argumenty(argumenty_volani(text, shoda.end() - 1))
            nalezene[shoda.group(1)] = set(argumenty[1:])
    return nalezene


def kontrola_sloupcu_kolekci(vzorce):
    """Zápis do kolekce se musí trefit do jejích sloupců — všech, ani o jeden víc."""
    schema = schema_kolekci(vzorce)
    for cesta, prop, syrovy in vzorce:
        text = bez_retezcu(syrovy)
        for funkce in ("Collect", "UpdateIf"):
            for shoda in re.finditer(rf"\b{funkce}\s*\(\s*(col[A-Za-z0-9_]*)\s*,", text):
                jmeno = shoda.group(1)
                if jmeno not in schema:
                    continue
                zavorka = text.index("(", shoda.start())
                klice = set(re.findall(r"[{,]\s*([A-Za-z][A-Za-z0-9_]*)\s*:",
                                       argumenty_volani(text, zavorka)))
                if not klice:
                    continue  # Collect(col, jináTabulka) — sloupce nejsou vypsané
                navic = klice - schema[jmeno]
                if navic:
                    chyby.append(
                        f"{cesta}.{prop}: {funkce} do '{jmeno}' zapisuje sloupec "
                        f"{sorted(navic)}, který kolekce nemá — má "
                        f"{sorted(schema[jmeno])}"
                    )
                chybi = schema[jmeno] - klice if funkce == "Collect" else set()
                if chybi:
                    chyby.append(
                        f"{cesta}.{prop}: Collect do '{jmeno}' nevyplňuje sloupec "
                        f"{sorted(chybi)} — řádek by v galerii měl prázdno tam, "
                        f"kde ostatní mají hodnotu"
                    )


def kontrola_rezimu_ciselniku(vzorce):
    """Kdo otevírá číselník, musí říct, co tam formulář dělá.

    scr_Ciselnik má dva režimy (varCiselnikNova) a v režimu úpravy sahá na
    záznam podle varCiselnikKod. Vstupní bod, který režim nenastaví, otevře
    formulář v tom, co zbylo po minulé návštěvě — v horším případě uloží
    změnu do cizí položky nebo založí duplicitu.
    """
    povinne = ("varUrovenTyp", "varCiselnikNova", "varCiselnikKod")
    for cesta, prop, text in vzorce:
        if not re.search(r"Navigate\(\s*scr_Ciselnik", text):
            continue
        # bílé znaky pryč: Set( a jméno proměnné bývají na dvou řádcích
        zhusteny = re.sub(r"\s+", "", text)
        chybi = [p for p in povinne if f"Set({p}," not in zhusteny]
        if chybi:
            chyby.append(
                f"{cesta}.{prop}: Navigate na scr_Ciselnik bez nastavení {chybi} — "
                f"formulář by se otevřel v režimu, který zbyl po minulé návštěvě"
            )


# Funkce, které uvnitř predikátu Filter zabijí delegaci celého dotazu.
NEDELEGOVATELNE_V_PREDIKATU = ("LookUp", "CountRows", "Search", "Concat", "Sum")


def kontrola_predikatu(vzorce):
    """V podmínce Filter nad velkým listem nesmí být nedelegovatelné volání.

    Filter nad SharePointem se posílá na server jen tehdy, když mu rozumí celý.
    Jediné LookUp do kolekce uvnitř podmínky shodí celý dotaz na první okno
    2 000 řádků — a bez hlášky: appka běží dál, jen odpovídá z části dat.
    Správně se takový predikát navléká AŽ NA VÝSLEDEK delegovaného dotazu
    (viz filtr osiřelých aktivit v gal_Aktivity.Items).
    """
    for cesta, prop, syrovy in vzorce:
        text = bez_retezcu(syrovy)
        for list_nazev in VELKE_LISTY:
            for shoda in re.finditer(rf"\bFilter\s*\(\s*'?{re.escape(list_nazev)}'?\s*,", text):
                zavorka = text.index("(", shoda.start())
                argumenty = argumenty_volani(text, zavorka)
                for funkce in NEDELEGOVATELNE_V_PREDIKATU:
                    if re.search(rf"\b{funkce}\s*\(", argumenty):
                        chyby.append(
                            f"{cesta}.{prop}: podmínka Filter nad '{list_nazev}' volá "
                            f"{funkce}() — tím se celý dotaz přestane delegovat a vrátí "
                            f"jen první okno dat. Navlékni predikát až na výsledek."
                        )


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
    kontrola_rezimu_ciselniku(vzorce)
    kontrola_sloupcu_kolekci(vzorce)
    kontrola_predikatu(vzorce)
    kontrola_stareho_result(vzorce)
    kontrola_prekryvu(soubory)
    kontrola_adresy_mapy(vzorce)
    kontrola_potvrzeni_mazani(soubory)
    kontrola_unikatnosti(soubory)
    kontrola_identifikatoru(vzorce)
    kontrola_syntaxe(vzorce)
    kontrola_barev(vzorce)
    kontrola_razeni(vzorce)
    kontrola_vlastnosti(soubory, nacti_povolene_vlastnosti(), nacti_typy())
    kontrola_vzorovych_dat(soubory, nacti_typy(), nacti_vzorova_data())
    kontrola_obsahovych_vychozich(soubory, nacti_typy(), nacti_lokalizovane_vychozi())

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
