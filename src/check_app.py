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

sys.path.insert(0, "src")
from build_restore_flow import ODD_POPISKU  # noqa: E402

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

# Návrhová plocha appky. Odpovídá DocumentLayoutWidth/Height v .msapp a appka
# má ScaleToFit, takže Parent.Width je za běhu vždycky 1366 bez ohledu na okno
# prohlížeče — souřadnice z výrazů `Parent.Width - N` jdou tedy dopočítat
# přesně, ne odhadem. Shodu s .msapp hlídá check_solution.py.
SIRKA_PLOCHY = 1366
VYSKA_PLOCHY = 768


def souradnice_v_px(vyraz, rozmer):
    """Pixelová hodnota souřadnice, nebo None, když ji spočítat nejde.

    Vzniklo z btn_Zaloha (01.09.2026): popisek `lbl_RozpadPocet` má
    `X = Parent.Width - 240`, tedy 1126, a ležel tak přes pravých 94 px
    tlačítka Záloha. Protože byl v souboru později, kreslil se NAD ním a
    klikání do většiny tlačítka spolkl — tlačítko „nic nedělalo" a ukazovalo
    cizí tooltip. Brána to přeskakovala právě proto, že souřadnice byla výraz.
    """
    text = str(vyraz).lstrip("=").strip()
    if text.isdigit():
        return int(text)
    plocha = {"Width": SIRKA_PLOCHY, "Height": VYSKA_PLOCHY}
    shoda = re.fullmatch(r"Parent\.(Width|Height)(?:\s*([-+])\s*(\d+))?", text)
    if not shoda:
        return None
    zaklad = plocha[shoda.group(1)]
    if shoda.group(2) is None:
        return zaklad
    return zaklad - int(shoda.group(3)) if shoda.group(2) == "-" else zaklad + int(shoda.group(3))


def kontrola_prekryvu(soubory, vylucne):
    """Dva prvky s obsahem nesmějí ležet přes sebe.

    Vzniklo z lbl_l_Vazby (20.08.2026): popisek široký 740 px zasahoval do
    nabídky Stav a seděl na stejné pozici jako jiný popisek. Studio ani packer
    to nehlásí, appka se otevře — vidí to až člověk na snímku obrazovky.

    Počítá se tam, kde jdou všechny čtyři souřadnice obou prvků dopočítat —
    číslem, nebo výrazem `Parent.Width/Height ± N` proti návrhové ploše
    (viz `souradnice_v_px`). Zbytek se přeskakuje.
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
                        for klic, rozmer in (("X", "Width"), ("Y", "Height"),
                                             ("Width", "Width"), ("Height", "Height")):
                            souradnice.append(
                                souradnice_v_px(vlastnosti.get(klic, ""), rozmer))
                        if any(s is None for s in souradnice):
                            continue
                        # Prvky skryté za stejné podmínky se nepřekrývají za běhu.
                        viditelnost = str(vlastnosti.get("Visible", "")).strip()
                        obdelniky.append((jmeno, souradnice, viditelnost))

                    porovnej(jmeno_obrazovky, obdelniky, vylucne)


def vylucuji_se(va, vb):
    """Pozná dvojici Visible, z níž je vždycky vidět jen jeden prvek.

    Panelový layout přepíná dva obsahy na stejném místě: `X = "a"` proti
    `X <> "a"`. Bez tohohle by kontrola hlásila překryv, který za běhu
    nikdy nenastane, a layout by se musel obcházet.

    Porovnávají se CELÉ normalizované operandy, ne podřetězce — jinak by
    `varTyp = "aktivita"` a `varJinyTyp <> "aktivita"` prošly jako protiklady
    a brána by přestala hlásit skutečné překryvy.
    """
    def rozloz(vyraz):
        text = re.sub(r"\s+", "", str(vyraz).lstrip("=").strip())
        for operator in ("<>", "="):
            casti = text.split(operator)
            if len(casti) == 2 and all(casti):
                return operator, casti[0], casti[1]
        return None

    a, b = rozloz(va), rozloz(vb)
    if not a or not b:
        return False
    return a[0] != b[0] and a[1] == b[1] and a[2] == b[2]


def je_nabidka(visible):
    """Prvek rozbalovací nabídky — leží nad obsahem obrazovky záměrně.

    Poznává se podle toho, že jeho zobrazení řídí proměnná `varMenu…`.
    Dvojice, kde je nabídkou jen jeden z prvků, se proto nehlásí; dva prvky
    UVNITŘ téže nabídky se ale porovnávají dál, protože ty na sebe lézt
    nemají o nic víc než tlačítka v pruhu.
    """
    return "varMenu" in str(visible)


def nabidkova_promenna(visible):
    """Proměnná `varMenu…`, která řídí zobrazení prvku nabídky."""
    nalezene = re.findall(r"varMenu[A-Za-z0-9_]*", str(visible))
    return nalezene[0] if nalezene else ""


def _zavira(normalizovane, a, b):
    """Každý vzorec, který otevírá nabídku `a`, zavírá nabídku `b`."""
    otevirajici = [t for t in normalizovane
                   if f"Set({a},!{a})" in t or f"Set({a},true)" in t]
    return bool(otevirajici) and all(f"Set({b},false)" in t for t in otevirajici)


def vylucne_nabidky(vzorce):
    """Dvojice nabídkových proměnných, z nichž je otevřená vždy nanejvýš jedna.

    Panel jedné nabídky smí ležet přes panel druhé — ale jen tehdy, když se
    ty nabídky opravdu vylučují, tedy když KAŽDÉ tlačítko, které svou nabídku
    otevírá, ostatní zavírá. Vzniklo z 1.0.0.92: chip nezařazených si vyžádal
    místo v pruhu filtrů, tlačítka nabídek se posunula doprava a jejich panely
    na sebe geometricky vlezly. Bez téhle kontroly by stačilo v jednom
    OnSelect zapomenout `Set(varMenu…, false)` a dvě nabídky by se otevřely
    přes sebe, aniž by na to brána překryvu upozornila.
    """
    normalizovane = [re.sub(r"\s+", "", bez_retezcu(text)) for _, _, text in vzorce]
    promenne = sorted({jmeno for text in normalizovane
                       for jmeno in re.findall(r"varMenu[A-Za-z0-9_]*", text)})
    return {(a, b) for a in promenne for b in promenne
            if a < b and _zavira(normalizovane, a, b) and _zavira(normalizovane, b, a)}


def nacti_prefix_nezarazeno():
    """Kód technického dílčího procesu ze schématu — nikdy natvrdo v bráně."""
    data = json.loads(SCHEMA.read_text(encoding="utf-8-sig"))
    return data["seed"]["prefix_nezarazeno"]


def kontrola_nezarazenych(vzorce):
    """Nezařazené aktivity musí mít v přehledu vlastní cestu — a technická
    větev `00` v běžném stromu být nesmí.

    Aktivita nahraná bez zařazení dostane rodiče `00-00-000`, takže NENÍ
    osiřelá a chip osiřelých ji neukáže. Kdyby zmizel chip nezařazených nebo
    kdyby ze stromu nezmizela agenda „00 Nezařazeno", výsledek je pokaždé
    špatně: buď se sirotci nedají najít, nebo se technická větev tváří jako
    běžná agenda a lezou z ní čísla do karet nahoře. Obojí Studio ani packer
    nehlásí — pozná se to až na obrazovce (F13/C3, 03.09.2026).
    """
    prefix = nacti_prefix_nezarazeno()
    agenda = prefix.split("-")[0]
    text_chipu = ""
    items_stromu = ""
    for cesta, prop, text in vzorce:
        if (cesta, prop) == ("btn_NezarazeneD", "Text"):
            text_chipu = text
        if (cesta, prop) == ("gal_Strom", "Items"):
            items_stromu = text

    if not text_chipu:
        chyby.append(
            "scr_Dashboard: chybí chip 'btn_NezarazeneD' — bez něj se "
            "k nezařazeným aktivitám nedá dostat, ve stromu nejsou vidět "
            "a mezi osiřelé nespadnou (mají rodiče " + prefix + ")")
    elif f'dilci_proces_kod = "{prefix}"' not in text_chipu:
        chyby.append(
            f"btn_NezarazeneD.Text: nepočítá aktivity s rodičem {prefix} — "
            "číslo v chipu pak neodpovídá tomu, co je pod ním vidět")

    if not items_stromu:
        chyby.append("scr_Dashboard: nenašel jsem 'gal_Strom.Items'")
        return
    if "varDashNezarazene" not in items_stromu or f'rodic = "{prefix}"' not in items_stromu:
        chyby.append(
            f"gal_Strom.Items: chybí větev varDashNezarazene s filtrem "
            f"rodic = \"{prefix}\" — chip by se dal zapnout, ale strom by "
            "ukazoval dál totéž co předtím")
    if f'Left(kod, 2) <> "{agenda}"' not in items_stromu:
        chyby.append(
            f"gal_Strom.Items: stromový režim nevylučuje technickou větev "
            f"'{agenda}' — 'Nezařazeno' se v přehledu tváří jako běžná agenda")

    for kolekce, technicka in (("colAgendy", agenda),
                               ("colProcesy", "-".join(prefix.split("-")[:2])),
                               ("colDilci", prefix)):
        for cesta, prop, text in vzorce:
            if f"CountRows({kolekce})" in text:
                chyby.append(
                    f"{cesta}.{prop}: CountRows({kolekce}) počítá i technickou položku "
                    f"'{technicka}' — karta na přehledu pak ukazuje o jednu víc, "
                    "než kolik je v rejstříku doopravdy")


def kontrola_prirazeni_sirotka(vzorce):
    """Dílčí proces smí u uložené aktivity změnit jen sirotek — a musí přitom
    dostat nový kód.

    Dvě chyby, které se tudy dají udělat, vypadají obě jako drobnost:

    (a) kaskáda zůstane odemčená všem. Pak appka dělá u běžné aktivity
        variantu A: `dilci_proces_kod` se přepíše, `Title` zůstane a prefix
        kódu začne lhát o tom, kam aktivita patří. To je nález z F10 a opraví
        ho až F10/2 (zánik + vznik), do té doby je zámek jediná obrana.
    (b) sirotek se přiřadí, ale kód si nechá technický. Aktivita pak visí
        v dílčím procesu, do kterého podle kódu nepatří, a chip nezařazených
        ji dál počítá.

    Studio nic z toho nehlásí — projeví se to až v datech (F13/C4, 03.09.2026).
    """
    prefix = nacti_prefix_nezarazeno()
    for jmeno in ("drp_Agenda", "drp_Proces", "drp_Dilci"):
        rezim = next((t for c, p, t in vzorce
                      if (c, p) == (jmeno, "DisplayMode")), "")
        if "varSirotek" not in rezim or "DisplayMode.View" not in rezim:
            chyby.append(
                f"{jmeno}.DisplayMode: kaskáda není zamčená pro aktivitu "
                f"s platným kódem — appka by u ní přesunula zařazení a nechala "
                f"starý kód, takže by prefix lhal (varianta A, nález F10)")

    ulozeni = next((t for c, p, t in vzorce if (c, p) == ("btn_Ulozit", "OnSelect")), "")
    if not ulozeni:
        chyby.append("scr_Detail: nenašel jsem 'btn_Ulozit.OnSelect'")
        return
    cisty = bez_retezcu(ulozeni)
    prideleni = re.search(r"Set\(\s*varNovyKod\s*,", cisty)
    if not prideleni:
        chyby.append("btn_Ulozit.OnSelect: nenašel jsem přidělení 'varNovyKod'")
    elif "varPresun" not in argumenty_volani(cisty, cisty.index("(", prideleni.start())):
        chyby.append(
            "btn_Ulozit.OnSelect: nový kód se přiděluje jen nové aktivitě — "
            "přiřazený sirotek by si nechal technický kód pod " + prefix)
    if "puvodni_kod" not in ulozeni:
        chyby.append(
            "btn_Ulozit.OnSelect: přiřazený sirotek nemá zapsaný 'puvodni_kod' — "
            "po přepisu kódu by nešlo dohledat, pod čím byl naimportovaný")
    if "aktivita_kod = varStaryKod" not in ulozeni:
        chyby.append(
            "btn_Ulozit.OnSelect: vazby sirotka se nepřepisují na nový kód — "
            "zůstaly by viset na kódu, který už žádná aktivita nemá")


def porovnej(jmeno_obrazovky, obdelniky, vylucne):
    for i, (jmeno_a, (xa, ya, wa, ha), va) in enumerate(obdelniky):
        for jmeno_b, (xb, yb, wb, hb), vb in obdelniky[i + 1:]:
            prekryv_x = min(xa + wa, xb + wb) - max(xa, xb)
            prekryv_y = min(ya + ha, yb + hb) - max(ya, yb)
            if prekryv_x <= 0 or prekryv_y <= 0:
                continue
            if vylucuji_se(va, vb):
                continue
            if je_nabidka(va) != je_nabidka(vb):
                continue
            if je_nabidka(va):
                dvojice = tuple(sorted((nabidkova_promenna(va),
                                        nabidkova_promenna(vb))))
                if dvojice[0] != dvojice[1] and dvojice in vylucne:
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


def kontrola_zneplatneni_stromu(vzorce):
    """Zápis do listů, ze kterých stojí strom, musí strom zneplatnit.

    Přehled si `colAkt`, `colVazby` a `colStrom` staví jednou a přepočítá je
    až na `varAktStale`. Vzorec, který do `Aktivity` nebo do vazebního listu
    zapíše a příznak nenastaví, nechá na Přehledu viset starý obrázek.

    Vzniklo to v 1.0.0.74: strom začal záviset i na vazbách, ale obrazovka
    vazeb `varAktStale` nenastavovala — dokud strom četl jen primární
    zařazení, nemusela. Závislost přibyla a zneplatnění se nedoplnilo.
    """
    zdroje = ("'Vazba aktivita–dílčí proces'", "Aktivity")
    for cesta, prop, text in vzorce:
        zapisuje = any(
            re.search(r"\b(Patch|Remove|RemoveIf|Collect)\s*\(\s*" + re.escape(z), text)
            for z in zdroje)
        if zapisuje and "varAktStale" not in text:
            chyby.append(
                f"{Path(cesta).stem}: '{prop}' zapisuje do Aktivit nebo do vazebního "
                "listu, ale nenastavuje varAktStale — strom na Přehledu zůstane starý"
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

        # Adresa smí být v appce jen na jediném místě — v App.OnStart, kde ji
        # při přenosu na MPSV někdo najde. Zapsaná rovnou do Launch() by tam
        # zůstala schovaná a appka by v cizím tenantu otevírala cizí web.
        for shoda in re.finditer(r'Launch\(\s*"([^"]*)"', text):
            chyby.append(
                f"{cesta}.{prop}: Launch má adresu natvrdo ({shoda.group(1)[:60]}) — "
                f"musí jít přes varMapaUrl, jinak se při přenosu na jiný tenant "
                f"nenajde"
            )


def kontrola_notify(vzorce, soubory):
    """Notify bez třetího argumentu svítí výchozích deset vteřin.

    Potvrzení („Smazáno: …") tím překáží při další práci, proto má zhasnout
    do vteřiny. U chyby je to naopak — musí zbýt čas ji přečíst, takže má
    vlastní, delší dobu. Obě hodnoty drží App.OnStart, aby se ladily
    z jednoho místa; volání je 27 a přepisovat je po jednom nikdo nebude.
    """
    for cesta, prop, text in vzorce:
        for shoda in re.finditer(r"\bNotify\s*\(", text):
            zavorka = text.index("(", shoda.start())
            args = rozdel_argumenty(argumenty_volani(text, zavorka))
            if len(args) != 3:
                chyby.append(
                    f"{cesta}.{prop}: Notify má {len(args)} argumenty místo tří — "
                    f"bez doby zobrazení svítí hláška deset vteřin"
                )
                continue
            ceka = "varNotifyChybaMs" if "NotificationType.Error" in args[1] else "varNotifyMs"
            if args[2] != ceka:
                chyby.append(
                    f"{cesta}.{prop}: Notify s {args[1].strip()} má dobu "
                    f"'{args[2]}', čekám {ceka}"
                )

    app = next((c for c in soubory if Path(c).name == "App.pa.yaml"), None)
    text_app = io.open(app, encoding="utf-8").read() if app else ""
    for jmeno in ("varNotifyMs", "varNotifyChybaMs"):
        if not re.search(rf"Set\(\s*{jmeno}\s*,\s*\d+\s*\)", text_app):
            chyby.append(
                f"App.OnStart: chybí Set({jmeno}, <ms>) — Notify by dostal "
                f"prázdnou dobu a hláška by nezhasla vůbec"
            )


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
    nalezene, kde = {}, {}
    for cesta, prop, syrovy in vzorce:
        text = bez_retezcu(syrovy)
        for shoda in re.finditer(
                r"\bClearCollect\s*\(\s*(col[A-Za-z0-9_]*)\s*,\s*ShowColumns\s*\(", text):
            jmeno = shoda.group(1)
            sloupce = set(rozdel_argumenty(argumenty_volani(text, shoda.end() - 1))[1:])
            # Táž kolekce se plní na víc obrazovkách (colAkt na přehledu
            # i v číselníku). Kdyby se definice rozešly, chovala by se appka
            # podle toho, odkud uživatel přišel — a nikdo by netušil proč.
            if jmeno in nalezene and nalezene[jmeno] != sloupce:
                chyby.append(
                    f"{cesta}.{prop}: '{jmeno}' se plní jinými sloupci než "
                    f"v {kde[jmeno]} — {sorted(sloupce)} proti "
                    f"{sorted(nalezene[jmeno])}"
                )
            nalezene[jmeno] = sloupce
            kde[jmeno] = f"{cesta}.{prop}"
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
    povinne = ("varUrovenTyp", "varCiselnikNova", "varCiselnikKod", "varRodicC")
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


def bez_mezer(text):
    return re.sub(r"\s+", "", text)


def kontrola_orezani_popisku(vzorce):
    """Do flow smí jít jen holý název souboru, ne popisek i s datem.

    Rozbalovátko snímků ukazuje `nazev.json · 2.9.2026 5:00`, protože jinak
    nejde poznat, který snímek je který. Flow ale přijímá jméno souboru —
    kdyby dostalo popisek, spadne až za běhu na nenalezeném souboru a appka
    z toho ukáže jen 502 BadGateway.

    Kontroluje se každé čtení hodnoty rozbalovátka kromě testu na prázdno:
    buď je obalené oříznutím, nebo je to chyba. Oddělovač se bere z
    generátoru flow, takže se ta dvě místa nemají jak rozejít.
    """
    # Porovnává se bez bílých znaků: vzorec bývá zalomený přes dva řádky.
    # Mezery mizí i uvnitř řetězcového literálu oddělovače, proto se stejným
    # způsobem zhušťuje i vzor, se kterým se srovnává.
    hodnota = "drp_SouborN.Selected.Value"
    orezani = bez_mezer(f'Split({hodnota}, "{ODD_POPISKU}")')
    for cesta, prop, text in vzorce:
        zhusteny = bez_mezer(text)
        pouziti = zhusteny.count(hodnota)
        if not pouziti:
            continue
        povolene = (zhusteny.count(f"IsBlank({hodnota})")
                    + zhusteny.count(orezani))
        if povolene < pouziti:
            chyby.append(
                f"{cesta}.{prop}: hodnota rozbalovátka snímků se bere bez "
                f"oříznutí popisku — do flow by šel název i s datem "
                f"({pouziti}x použito, {povolene}x ošetřeno)"
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
            for shoda in re.finditer(rf"\b(Filter|RemoveIf)\s*\(\s*'?{re.escape(list_nazev)}'?\s*,", text):
                jmeno_funkce = shoda.group(1)
                zavorka = text.index("(", shoda.start())
                argumenty = argumenty_volani(text, zavorka)
                for funkce in NEDELEGOVATELNE_V_PREDIKATU:
                    if re.search(rf"\b{funkce}\s*\(", argumenty):
                        chyby.append(
                            f"{cesta}.{prop}: podmínka {jmeno_funkce} nad '{list_nazev}' volá "
                            f"{funkce}() — tím se celý dotaz přestane delegovat a vrátí "
                            f"jen první okno dat. Navlékni predikát až na výsledek."
                        )
                # Choice se porovnává přes .Value a to SharePoint nedeleguje.
                # U RemoveIf to není jen neúplná odpověď: nad velkým listem se
                # smaže jen část toho, co uživatel čeká, a zbytek zůstane
                # v datech bez hlášky. Přesně tak umí vzniknout aktivita se
                # dvěma primárními vazbami.
                if jmeno_funkce == "RemoveIf" and re.search(r"\w+\.Value\s*[=<>]", argumenty):
                    chyby.append(
                        f"{cesta}.{prop}: RemoveIf nad '{list_nazev}' se rozhoduje "
                        f"podle choice sloupce (.Value), což se nedeleguje — nad "
                        f"velkým listem by smazal jen část a zbytek nechal v datech. "
                        f"Vyber řádky podle textového sloupce."
                    )


def kontrola_operatoru_in(vzorce):
    """Operátor `in` se v této appce nepoužívá — hledá se přes `Search()`.

    `in` má v Power Fx dva významy (prvek v tabulce, podřetězec v textu)
    a nad sloupcem kolekce si Studio umí vybrat ten druhý. Když se to stane
    ve vlastnosti `Items` galerie, galerie ztratí typ a KAŽDÝ `ThisItem.*`
    v šabloně řádku se stane chybou — z jednoho vzorce je rázem padesát
    hlášek a prázdná galerie se vykreslí jako černá plocha.

    `Search(tabulka, text, sloupce…)` dělá totéž, prázdný text bere jako
    „neomezuj" a v této appce je ověřený od začátku (gal_Nabidka).
    """
    for cesta, prop, syrovy in vzorce:
        if re.search(r"[)\w\"]\s+in\s+", bez_retezcu(syrovy)):
            chyby.append(
                f"{cesta}.{prop}: operátor 'in' — použij Search(tabulka, text, "
                f"sloupce…). Nad sloupcem kolekce se 'in' umí vyhodnotit jinak, "
                f"než čekáš, a v Items galerie to shodí celou šablonu řádku"
            )


def kontrola_dvojiteho_rovnitka(soubory):
    """`Vlastnost: ==vzorec` je překlep, který projde YAML i packerem.

    V pa.yaml uvozuje vzorec jedno rovnítko. Když je tam omylem dvojité,
    YAML se rozparsuje, packer nic nenamítne a Studio až po importu hlásí
    „Unexpected characters" — u každého takového prvku zvlášť. Vzniká to
    při generování vlastností skriptem, kde už předpřipravená hodnota
    rovnítko obsahuje a další se přidá při skládání řádku.

    Kontroluje se nad SYROVÝM textem souboru, ne nad načteným YAML: parser
    druhé rovnítko schová do hodnoty a v načtené podobě není poznat.
    (Zjištěno 23.08.2026 na 1.0.0.38 — nesla devět takových vlastností.)
    """
    for cesta in soubory:
        for cislo, radek in enumerate(io.open(cesta, encoding="utf-8"), start=1):
            if re.match(r"\s+[A-Za-z][A-Za-z0-9]*: ==", radek):
                chyby.append(
                    f"{Path(cesta).name}:{cislo}: vlastnost má dvojité rovnítko "
                    f"({radek.strip()[:60]}) — Studio to hlásí jako "
                    f"jako „Unexpected characters“"
                )


def kontrola_promennych(soubory, vzorce):
    """Proměnná, která nikde nedostane typ, shodí celý App.OnStart.

    `Set(x, Blank())` typ neurčuje. Když je to JEDINÉ přiřazení v celé appce,
    Studio hlásí „No type found for variable 'x'" — a protože je ta chyba
    v OnStart, neprovede se ani zbytek: appka naběhne bez barev (černá,
    protože barvy jsou proměnné z OnStart) a s prázdnými kolekcemi.

    Typicky vznikne po zrušení obrazovky: proměnná, kterou používala, zůstane
    v OnStart viset. Přesně tohle shodilo 1.0.0.39 — `varSmazat` po zrušené
    scr_Seznam. Mrtvá proměnná, která typ má, appku neshodí, ale je to smetí
    ze stejného soudku, takže se hlásí jako varování.
    """
    app = next((c for c in soubory if Path(c).name == "App.pa.yaml"), None)
    if app is None:
        return
    text_app = io.open(app, encoding="utf-8").read()
    text_obrazovek = "".join(
        io.open(c, encoding="utf-8").read() for c in soubory if Path(c).name != "App.pa.yaml"
    )

    vse = text_app + text_obrazovek
    for jmeno in sorted(set(re.findall(r"Set\(\s*(var[A-Za-z0-9_]*)\s*,", text_app))):
        # Počítá se, ne parsuje: hodnota Blank() má vlastní závorky, takže
        # každý pokus vytáhnout ji regulárním výrazem skončí u té první.
        vsechna = len(re.findall(rf"Set\(\s*{jmeno}\s*,", vse))
        prazdna = len(re.findall(rf"Set\(\s*{jmeno}\s*,\s*Blank\(\)\s*\)", vse))
        if vsechna and vsechna == prazdna:
            chyby.append(
                f"App.OnStart: '{jmeno}' nikde nedostane typ — jediné přiřazení "
                f"je Blank(). Studio to hlásí jako 'No type found for variable' "
                f"a kvůli té chybě neprovede celý OnStart: appka naběhne černá "
                f"(barvy jsou proměnné z OnStart) a s prázdnými kolekcemi"
            )
        elif not re.search(rf"\b{jmeno}\b", text_obrazovek):
            varovani.append(
                f"App.OnStart: '{jmeno}' se v žádné obrazovce nepoužívá — "
                f"nejspíš zbytek po zrušené obrazovce"
            )


VYJIMKY_PREPINACU = {
    "varMapaUrl": "konfigurační hodnota, ne přepínač — adresu publikované mapy "
                  "nastavuje App.OnStart a mění se jen při přenosu na jiný tenant",
}


def je_slovo(jmeno, radek):
    """Jméno proměnné jako celé slovo, ne jako podřetězec delšího jména."""
    return re.search(r"\b" + re.escape(jmeno) + r"\b", radek)


def kontrola_prepinacu(soubory):
    """Proměnná, která řídí vzhled, musí mít v appce něco, co ji přepne.

    Vzniká to při přestavbě obrazovky: prvek, který proměnnou přepínal,
    zanikne, ale všechno, co na ní visí, zůstane. Proměnná pak drží hodnotu
    z App.OnStart a chová se jako konstanta — funkce z pohledu uživatele
    zmizela, ale ve zdrojích po ní zbyly viditelné stopy, takže při čtení
    kódu vypadá, že tam pořád je.

    Přesně tak zmizel přepínač sloupce s kódy na přehledu: v 1.0.0.37
    nahradily pruh nad stromem rolovací nabídky, tlačítko se do nich
    nevešlo a `varZobrazitKod` od té doby nikdo nepřepínal (hlášeno
    24.08.2026, tři balíky poté).

    Kontroluje se jen vzhled — behaviorální vlastnosti (OnSelect, OnVisible)
    proměnné nastavují, ne čtou.
    """
    app = next((c for c in soubory if Path(c).name == "App.pa.yaml"), None)
    if app is None:
        return
    text_app = io.open(app, encoding="utf-8").read()
    obrazovky = [c for c in soubory if Path(c).name != "App.pa.yaml"]
    text_obrazovek = "".join(io.open(c, encoding="utf-8").read() for c in obrazovky)

    VZHLED = ("Visible", "Width", "Height", "X", "Y", "Fill", "Color", "Size", "Text",
              "BorderColor", "DisplayMode", "PaddingTop")
    for jmeno in sorted(set(re.findall(r"Set\(\s*(var[A-Za-z0-9_]*)\s*,", text_app))):
        if jmeno in VYJIMKY_PREPINACU:
            continue
        if re.search(rf"Set\(\s*{jmeno}\s*,", text_obrazovek):
            continue  # něco ji za běhu přepíná
        kde = []
        for cesta in obrazovky:
            # Vlastnost si musí držet i přes pokračovací řádky bloku `|-`:
            # ve víceřádkovém vzorci je jméno proměnné o pár řádků níž než
            # `Text:` a jednořádkové hledání by ho minulo.
            vlastnost, odsazeni = None, 0
            for cislo, radek in enumerate(io.open(cesta, encoding="utf-8"), start=1):
                m = re.match(r"(\s+)([A-Za-z][A-Za-z0-9]*): ", radek)
                if m:
                    vlastnost, odsazeni = m.group(2), len(m.group(1))
                elif radek.strip() and len(radek) - len(radek.lstrip()) <= odsazeni:
                    vlastnost = None  # blok skončil
                if vlastnost in VZHLED and je_slovo(jmeno, radek):
                    kde.append(f"{Path(cesta).name}:{cislo} ({vlastnost})")
        if kde:
            chyby.append(
                f"'{jmeno}' řídí vzhled ({', '.join(kde[:3])}"
                f"{' a další' if len(kde) > 3 else ''}), ale žádná obrazovka ji "
                f"nepřepíná — drží hodnotu z App.OnStart, takže se ta funkce "
                f"z appky ztratila, i když ve zdrojích po ní zbyly stopy"
            )


VYJIMKY_VELIKOSTI = {
    "ico_Zpet": "šipka zpět v hlavičce je navigace, ne ovládací prvek formuláře",
    "ico_ZpetV": "totéž na obrazovce vazeb",
}

# Ovládací prvky mají napříč appkou jednu výšku. Vyšší TextInput je plocha
# pro psaní (znění aktivity, spolupracuje, předpis), ne ovládací prvek.
VYSKA_OVLADACIHO_PRVKU = 32
VICERADKOVE_POLE_OD = 48


def kontrola_velikosti(soubory):
    """Ovládací prvky musí mít napříč obrazovkami stejnou výšku.

    Přehled má tlačítka a pole na 28-32 px, kdežto číselník a detail vyrostly
    na 36-44 px, protože každá obrazovka vznikala zvlášť. Na husté obrazovce
    to působí hrubě a hlavně nesourodě — táž akce vypadá jinde jinak
    (hlášeno 24.08.2026 snímkem s vyznačenými prvky).

    Kontroluje se strop, ne přesná hodnota: menší prvek (28 px v pruhu nad
    stromem) je vědomé odlišení hustého ovládacího pásu, vyšší je regrese.
    """
    for cesta in soubory:
        if Path(cesta).name == "App.pa.yaml":
            continue
        t = io.open(cesta, encoding="utf-8").read()
        hranice = [m.start() for m in re.finditer(r"\n\s+- [A-Za-z0-9_]+:\n\s+Control: ", t)]
        hranice.append(len(t))
        for i, zac in enumerate(hranice[:-1]):
            blok = t[zac:hranice[i + 1]]
            m = re.match(r"\n\s+- ([A-Za-z0-9_]+):\n\s+Control: ([^\n]+)", blok)
            if not m:
                continue
            jmeno, ctrl = m.group(1), m.group(2).strip()
            if any(jmeno.startswith(v) for v in VYJIMKY_VELIKOSTI):
                continue
            if not any(k in ctrl for k in ("Button", "DropDown", "TextInput", "ComboBox")):
                continue
            mh = re.search(r"^\s+Height: =(\d+)$", blok, re.M)
            if not mh:
                continue
            vyska = int(mh.group(1))
            if "TextInput" in ctrl and vyska >= VICERADKOVE_POLE_OD:
                continue  # plocha pro psaní, ne ovládací prvek
            if vyska > VYSKA_OVLADACIHO_PRVKU:
                chyby.append(
                    f"{Path(cesta).name}: '{jmeno}' má výšku {vyska} px, "
                    f"ale ovládací prvky mají napříč appkou "
                    f"{VYSKA_OVLADACIHO_PRVKU} px — táž akce by na dvou "
                    f"obrazovkách vypadala jinak"
                )


def kontrola_concurrent(soubory):
    """Kolekce z `Concurrent()` nesmí být použitá bez pojistky na prázdnotu.

    `Concurrent()` v `App.OnStart` NEČEKÁ na dokončení — vrátí se hned a větve
    dobíhají na pozadí. Úvodní obrazovka se mezitím zobrazí a její `OnVisible`
    postaví odvozenou kolekci z něčeho, co ještě nedorazilo. Vznikne snímek
    prázdna, který se sám neopraví, protože `ClearCollect` proběhl jen jednou.

    Pozná se to špatně: karty s počty čtou `CountRows()` reaktivně, takže po
    dotažení ukazují správná čísla, kdežto strom postavený vedle nich zůstane
    prázdný. Vypadá to jako vada dat, ne jako závod.

    Přesně tak se 24.08.2026 projevil rejstřík v provozu: na Přehledu měly
    všechny procesy POLOŽKY = 0, v Číselníku bylo všech 251 dílčích procesů
    osiřelých — a sonda `probe_dilci.js` přitom v SharePointu našla 239 z 251
    vazeb v pořádku. Každá obrazovka dostala jinou nedonačtenou kolekci,
    protože pořadí dokončení `Concurrent` nezaručuje nic.

    Pojistkou je test `IsEmpty()` před stavbou odvozené kolekce. Stačí,
    protože `ClearCollect` je atomický — kolekce je buď prázdná, nebo celá.
    """
    app = next((c for c in soubory if Path(c).name == "App.pa.yaml"), None)
    if app is None:
        return
    text_app = io.open(app, encoding="utf-8").read()
    zacatek = re.search(r"Concurrent\(", text_app)
    if not zacatek:
        return
    uvnitr = argumenty_volani(text_app, zacatek.end() - 1)
    asynchronni = set(re.findall(r"ClearCollect\(\s*(col[A-Za-z0-9_]*)", uvnitr))
    if not asynchronni:
        return

    for cesta in soubory:
        if Path(cesta).name == "App.pa.yaml":
            continue
        dokument = nacti_yaml(cesta)
        for obrazovka, telo in (dokument.get("Screens") or {}).items():
            onvisible = ((telo or {}).get("Properties") or {}).get("OnVisible", "")
            if not isinstance(onvisible, str) or "ClearCollect" not in onvisible:
                continue
            pouzite = {k for k in asynchronni if je_slovo(k, onvisible)}
            hlidane = {k for k in pouzite
                       if re.search(r"IsEmpty\(\s*" + re.escape(k) + r"\s*\)", onvisible)}
            chybi = sorted(pouzite - hlidane)
            if chybi:
                chyby.append(
                    f"{Path(cesta).name}: {obrazovka}.OnVisible staví kolekci z "
                    f"{', '.join(chybi)} — ty plní Concurrent() v App.OnStart a ten "
                    f"na dokončení nečeká, takže se odvozená kolekce může postavit "
                    f"z prázdna. Před stavbou chybí test IsEmpty()"
                )


def kontrola_poradi_nabidek(soubory):
    """Položky rozbalovací nabídky musí ležet NAD jejím stínem.

    V Power Apps kreslí pořadí definice: co je v souboru dřív, leží níž.
    Stín, který zavírá nabídku kliknutím mimo ni, tedy musí být zapsaný
    PŘED položkami — jinak leží nad nimi, spolkne klik a nabídka se jen
    zavře, aniž by cokoli udělala.

    Přesně tak přestala fungovat nabídka rozbalení na přehledu (1.0.0.41):
    tlačítka úrovní zůstala na svém původním místě v souboru, zatímco stín
    přibyl až na konec. Studio nic nehlásí — vypadá to, že tlačítko nereaguje.
    """
    for cesta in soubory:
        radky = io.open(cesta, encoding="utf-8").read().splitlines()
        poradi, aktualni = {}, None
        for cislo, radek in enumerate(radky):
            jmeno = re.match(r"      - ([A-Za-z_][A-Za-z0-9_]*):\s*$", radek)
            if jmeno:
                aktualni = jmeno.group(1)
                poradi.setdefault(aktualni, {"radek": cislo, "visible": ""})
            elif aktualni and radek.strip().startswith("Visible:"):
                poradi[aktualni]["visible"] = radek.strip()

        stiny = [j for j, u in poradi.items() if "Stin" in j and "varMenu" in u["visible"]]
        if not stiny:
            continue
        prvni_stin = min(poradi[j]["radek"] for j in stiny)
        for jmeno, udaje in poradi.items():
            if "varMenu" not in udaje["visible"] or jmeno in stiny:
                continue
            if udaje["radek"] < prvni_stin:
                chyby.append(
                    f"{Path(cesta).name}: '{jmeno}' patří do rozbalovací nabídky, "
                    f"ale je zapsaný PŘED jejím stínem — leží pod ním, takže "
                    f"stín spolkne klik a položka nereaguje"
                )


def kontrola_navigace(vzorce, obrazovky):
    for cesta, prop, text in vzorce:
        for cil in re.findall(r"Navigate\(\s*([A-Za-z0-9_]+)", text):
            if cil not in obrazovky:
                chyby.append(f"{cesta}.{prop}: Navigate na neexistující obrazovku '{cil}'")


# Typy, které v pa.yaml vyžadují klíč `Variant`. Bez něj Studio appku vůbec
# neotevře (PA1011) — a `pac canvas pack` ani import balíku to nechytí, projeví
# se to až dialogem „Error opening file". Ověřeno 01.09.2026 na scr_Nahled.
VYZADUJI_VARIANTU = ("Gallery@",)


def kontrola_varianty(soubory):
    """Galerie musí mít `Variant`, a to takovou, jakou appka opravdu veze.

    Vzniklo z 1.0.0.87: tři nové galerie ho neměly, import balíku proběhl
    zeleně a appka pak nešla otevřít v editaci. Kontroluje se i hodnota —
    varianta, kterou nepoužívá žádná jiná galerie v appce, znamená šablonu
    navíc v Templates.json, a ta se do balíku negeneruje.
    """
    znama = set()
    zaznamy = []
    for cesta in soubory:
        radky = io.open(cesta, encoding="utf-8").read().splitlines()
        for cislo, radek in enumerate(radky):
            shoda = re.match(r"\s*Control:\s*(\S+)", radek)
            if shoda and any(shoda.group(1).startswith(t) for t in VYZADUJI_VARIANTU):
                dalsi = radky[cislo + 1] if cislo + 1 < len(radky) else ""
                varianta = re.match(r"\s*Variant:\s*(\S+)", dalsi)
                jmeno = "?"
                for zpet in range(cislo - 1, max(-1, cislo - 4), -1):
                    nalezeny = re.match(r"\s*-\s+([A-Za-z_][A-Za-z0-9_]*):", radky[zpet])
                    if nalezeny:
                        jmeno = nalezeny.group(1)
                        break
                zaznamy.append((Path(cesta).name, jmeno, shoda.group(1),
                                varianta.group(1) if varianta else None))
                if varianta:
                    znama.add(varianta.group(1))

    for soubor, jmeno, typ, varianta in zaznamy:
        if varianta is None:
            chyby.append(
                f"{soubor}: '{jmeno}' typu {typ} nemá hned pod Control klíč "
                f"Variant — Studio appku vůbec neotevře (PA1011) a import "
                f"balíku ani pac to nechytí")
        elif len(znama) > 1 and varianta not in znama - {varianta}:
            # jediný výskyt varianty napříč appkou = šablona, kterou balík
            # nemusí vézt; hlásí se jako varování, ne jako chyba
            if sum(1 for z in zaznamy if z[3] == varianta) == 1:
                varovani.append(
                    f"{soubor}: '{jmeno}' používá variantu {varianta}, kterou "
                    f"žádná jiná galerie v appce nemá — ověř, že je "
                    f"v Templates.json")


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
    kontrola_operatoru_in(vzorce)
    kontrola_dvojiteho_rovnitka(soubory)
    kontrola_promennych(soubory, vzorce)
    kontrola_poradi_nabidek(soubory)
    kontrola_prepinacu(soubory)
    kontrola_velikosti(soubory)
    kontrola_concurrent(soubory)
    kontrola_sloupcu_kolekci(vzorce)
    kontrola_predikatu(vzorce)
    kontrola_orezani_popisku(vzorce)
    kontrola_stareho_result(vzorce)
    kontrola_varianty(soubory)
    kontrola_prekryvu(soubory, vylucne_nabidky(vzorce))
    kontrola_nezarazenych(vzorce)
    kontrola_prirazeni_sirotka(vzorce)
    kontrola_adresy_mapy(vzorce)
    kontrola_notify(vzorce, soubory)
    kontrola_potvrzeni_mazani(soubory)
    kontrola_zneplatneni_stromu(vzorce)
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
