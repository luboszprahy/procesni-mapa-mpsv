# -*- coding: utf-8 -*-
"""Přidá do solution flow ExportFlow — export momentálního zobrazení do Wordu a Excelu.

Appka pošle jedním textovým vstupem JSON momentálního zobrazení stromu
(už seřazeného a odfiltrovaného) a název formátu; flow z něj složí dokument,
uloží ho do Site Assets a vrátí adresu, na kterou appka zavolá Download().

Formáty:
- `word` -> `.doc`, HTML dokument, který Word otevře a umí uložit jako .docx.
  Skutečné OOXML by znamenalo premium konektor (Encodian, Word Online) a ten
  v tomhle tenantu neprojde DLP. Vědomý ústupek, ne opomenutí.
- `excel` -> `.csv` v UTF-8 s BOM a řádkem `sep=;`. Excel takový soubor otevře
  rovnou do sloupců a bez varování; `.xls` s HTML tabulkou by sice nesl
  formátování, ale Excel u něj hlásí nesoulad přípony a obsahu.

Obě podoby dokumentu se počítají vždy (jsou to jen řetězce) a `Dokument` z nich
vybírá výrazem `if`. Větvení přes If/Scope by přidalo akce, které by brána
musela obcházet, a jedna z podob by nikdy nebyla otestovaná.

Proč plochý seznam řádků a ne strom: Logic Apps neumí rekurzi ani vnořený
Foreach, takže stromovat musí appka. Flow z řádků dělá tabulku, úroveň se
v dokumentu projeví odsazením buňky a v CSV vlastním sloupcem.

Obálka (spojení, uzel <Workflow>, RootComponent) se KLONUJE z MapaPublishFlow
— je to nejbezpečnější lokální úprava exportu, jakou skill připouští. GUID je
pevné, aby opakovaný build nezakládal v prostředí sirotky.

Skript je idempotentní — když už flow v balíku je, přepíše ho.

Spouštět z kořene projektu:
    python src/build_export_flow.py --solution deploy/procesnimapa_1_0_0_56.zip
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

ZDROJ = "MapaPublishFlow"
CIL = "ExportFlow"
# Pevné GUID: opakované spuštění musí dát TOTÉŽ flow, jinak by každý build
# zakládal v prostředí nové a hromadili by se sirotci.
CIL_GUID = "3f2b6d41-8c55-4a37-9d21-5b8e0c47a9f2"

CILOVA_SLOZKA = "/SiteAssets"
HOST_SP = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"

# Klíče datového kontraktu. Drží je deploy/flow_Export.md a kontroluje
# check_export_flow.py — appka musí posílat přesně tyhle.
KLICE_RADKU = ("uroven", "kod", "nazev", "vlastnik", "stav")

ODSAZENI_PT = 18   # bodů na úroveň zanoření ve wordovém dokumentu
SLOUPCE = ("Úroveň", "Kód", "Název", "Vlastník / vykonává", "Stav")

HLAVICKA_HTML = (
    '<html xmlns:o="urn:schemas-microsoft-com:office:office"'
    ' xmlns:w="urn:schemas-microsoft-com:office:word"'
    ' xmlns="http://www.w3.org/TR/REC-html40"><head>'
    '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
    '<title>Procesní mapa MPSV</title><style>'
    "@page WordSection1 {size:842.0pt 595.0pt; mso-page-orientation:landscape;"
    " margin:40.0pt 40.0pt 40.0pt 40.0pt;}"
    "div.WordSection1 {page:WordSection1;}"
    "body {font-family:Arial,sans-serif; font-size:9.0pt; color:#1B2233;}"
    "h1 {font-family:Arial,sans-serif; font-size:14.0pt; color:#110B7A;}"
    "table {border-collapse:collapse; width:100%;}"
    "th {background:#110B7A; color:#FFFFFF; font-size:9.0pt; text-align:left;"
    " padding:4.0pt; border:0.5pt solid #A9C7EC;}"
    "td {padding:3.0pt; border:0.5pt solid #A9C7EC; vertical-align:top;}"
    "td.k {white-space:nowrap; font-size:8.0pt; color:#4A5568;}"
    "p.m {font-size:8.0pt; color:#4A5568;}"
    "</style></head><body><div class=WordSection1>"
)

# BOM a konec řádku se v Logic Apps jinak než procentní sekvencí napsat nedají.
BOM = "decodeUriComponent('%EF%BB%BF')"
KONEC_RADKU = "decodeUriComponent('%0D%0A')"


def lit(text):
    """Řetězcový literál výrazu Logic Apps; apostrof se zdvojuje."""
    return "'" + text.replace("'", "''") + "'"


def esc_html(vyraz):
    """HTML escapování hodnoty. & musí být první, jinak by rozbil vlastní entity.

    coalesce kolem: chybějící vlastník nebo stav přijde jako null a replace()
    by na něm spadl — celý export by selhal kvůli jedné prázdné buňce.
    """
    hodnota = f"coalesce({vyraz}, '')"
    for znak, entita in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;")):
        hodnota = f"replace({hodnota}, {lit(znak)}, {lit(entita)})"
    return hodnota


def esc_csv(vyraz):
    """Pole CSV v uvozovkách; vnitřní uvozovka se zdvojuje.

    V uvozovkách přežije středník i konec řádku uvnitř textu — obojí je
    v názvech aktivit reálně k vidění a bez uvozovek by rozhodilo sloupce.
    """
    return f"concat('\"', replace(coalesce({vyraz}, ''), '\"', '\"\"'), '\"')"


def pole(nazev):
    return f"item()?[{lit(nazev)}]"


def format_je(hodnota):
    return f"equals(outputs('Vstup')?['format'], {lit(hodnota)})"


def vyraz_radku_html():
    uroven = f"int(coalesce({pole('uroven')}, 1))"
    casti = [
        lit('<tr><td class="k">'),
        esc_html(pole("kod")),
        lit('</td><td style="padding-left:'),
        f"string(mul(sub({uroven}, 1), {ODSAZENI_PT}))",
        lit("pt;font-weight:"),
        f"if(equals({uroven}, 1), 'bold', 'normal')",
        lit('">'),
        esc_html(pole("nazev")),
        lit("</td><td>"),
        esc_html(pole("vlastnik")),
        lit("</td><td>"),
        esc_html(pole("stav")),
        lit("</td></tr>"),
    ]
    return "@concat(" + ", ".join(casti) + ")"


def vyraz_radku_csv():
    casti = [f"string(int(coalesce({pole('uroven')}, 1)))"]
    for nazev in ("kod", "nazev", "vlastnik", "stav"):
        casti.append(lit(";"))
        casti.append(esc_csv(pole(nazev)))
    return "@concat(" + ", ".join(casti) + ")"


def vyraz_wordu():
    casti = [
        # Word bez BOM u .doc hádá kódování podle národního nastavení
        # a diakritika se rozsype.
        BOM,
        lit(HLAVICKA_HTML),
        lit('<h1>Procesní mapa MPSV</h1><p class="m">Zobrazení: '),
        esc_html("outputs('Vstup')?['nadpis']"),
        lit("</p><table><tr>"
            + "".join(f"<th>{s}</th>" for s in SLOUPCE[1:])
            + "</tr>"),
        "join(body('Html_radky'), '')",
        lit('</table><p class="m">Vygenerováno '),
        "formatDateTime(utcNow(), 'dd.MM.yyyy HH:mm')",
        lit("</p></div></body></html>"),
    ]
    return "concat(" + ", ".join(casti) + ")"


def vyraz_csv():
    casti = [
        BOM,
        # sep=; říká Excelu oddělovač bez ohledu na národní nastavení stroje.
        # Bez toho by se soubor na anglickém Windows otevřel v jednom sloupci.
        lit("sep=;"),
        KONEC_RADKU,
        lit(";".join(SLOUPCE)),
        KONEC_RADKU,
        "join(body('Csv_radky'), " + KONEC_RADKU + ")",
        KONEC_RADKU,
    ]
    return "concat(" + ", ".join(casti) + ")"


def trigger():
    """PowerAppV2 s jedním textovým vstupem — tvar, jaký generuje designer."""
    return {
        "manual": {
            "type": "Request",
            "kind": "PowerAppV2",
            "inputs": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "title": "zobrazeni",
                            "type": "string",
                            "x-ms-dynamically-added": True,
                            "x-ms-content-hint": "TEXT",
                            "description": "JSON: nadpis, format (word/excel), radky",
                        }
                    },
                    "required": ["text"],
                }
            },
        }
    }


def akce(web):
    kroky = {}
    kroky["Vstup"] = {
        "type": "Compose",
        "inputs": "@json(triggerBody()['text'])",
        "runAfter": {},
    }
    kroky["Html_radky"] = {
        "type": "Select",
        "inputs": {"from": "@outputs('Vstup')?['radky']", "select": vyraz_radku_html()},
        "runAfter": {"Vstup": ["Succeeded"]},
    }
    kroky["Csv_radky"] = {
        "type": "Select",
        "inputs": {"from": "@outputs('Vstup')?['radky']", "select": vyraz_radku_csv()},
        "runAfter": {"Html_radky": ["Succeeded"]},
    }
    # Razítko v názvu: dva exporty spuštěné vedle sebe si nesmí přepsat soubor.
    kroky["Jmeno"] = {
        "type": "Compose",
        "inputs": ("@concat('procesni_mapa_',"
                   " formatDateTime(utcNow(), 'yyyyMMdd_HHmmss'),"
                   f" if({format_je('excel')}, '.csv', '.doc'))"),
        "runAfter": {"Csv_radky": ["Succeeded"]},
    }
    kroky["Dokument"] = {
        "type": "Compose",
        "inputs": f"@if({format_je('excel')}, {vyraz_csv()}, {vyraz_wordu()})",
        "runAfter": {"Jmeno": ["Succeeded"]},
    }
    kroky["Uloz"] = {
        "type": "OpenApiConnection",
        "inputs": {
            "parameters": {
                "dataset": web,
                "folderPath": CILOVA_SLOZKA,
                "name": "@outputs('Jmeno')",
                "body": "@outputs('Dokument')",
            },
            "host": {"apiId": HOST_SP, "operationId": "CreateFile",
                     "connectionName": "shared_sharepointonline"},
        },
        "runAfter": {"Dokument": ["Succeeded"]},
    }
    # Adresu skládáme sami z webu a názvu, ne z odpovědi CreateFile: pole
    # odpovědi konektoru nejsou v dokumentaci závazná a mlčky se mění.
    kroky["Adresa"] = {
        "type": "Compose",
        "inputs": f"@concat({lit(web + CILOVA_SLOZKA + '/')}, outputs('Jmeno'))",
        "runAfter": {"Uloz": ["Succeeded"]},
    }
    kroky["Odpoved"] = {
        "type": "Response",
        "kind": "PowerApp",
        "inputs": {
            "statusCode": 200,
            "body": {"adresa": "@outputs('Adresa')"},
            "schema": {"type": "object",
                       "properties": {"adresa": {"type": "string"}}},
        },
        "runAfter": {"Adresa": ["Succeeded"]},
    }
    return kroky


def nacti_web(customizations):
    """Adresu webu bere z canvas appky, ne natvrdo.

    Kdyby uživatel appku přepojil na jiný web, natvrdo zapsaná adresa by
    vracela odkaz do prázdna a nikdo by nepoznal proč.
    """
    shoda = re.search(r"<ConnectionReferences>(.*?)</ConnectionReferences>",
                      customizations, re.S)
    if not shoda:
        raise SystemExit("CHYBA: v customizations.xml není blok ConnectionReferences canvas appky")
    data = json.loads(shoda.group(1).replace("&quot;", '"').replace("&amp;", "&"))
    for spojeni in data.values():
        datasety = spojeni.get("dataSets") or {}
        if datasety:
            if len(datasety) != 1:
                raise SystemExit(f"CHYBA: čekám právě jeden web, appka jich má {len(datasety)}")
            return next(iter(datasety))
    raise SystemExit("CHYBA: v ConnectionReferences není žádný web")


def uzel_workflow(customizations, guid):
    zacatek = customizations.lower().index(f'<workflow workflowid="{{{guid.lower()}}}"')
    konec = customizations.index("</Workflow>", zacatek) + len("</Workflow>")
    return customizations[zacatek:konec]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True, help="solution zip, do kterého se flow přidá")
    argumenty = parser.parse_args()

    cesta = Path(argumenty.solution)
    if not cesta.exists():
        raise SystemExit(f"CHYBA: solution {cesta} neexistuje")
    with zipfile.ZipFile(cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    zdrojove = [n for n in polozky if n.replace("\\", "/").startswith(f"Workflows/{ZDROJ}")]
    if len(zdrojove) != 1:
        raise SystemExit(f"CHYBA: čekám právě jedno {ZDROJ}, našel jsem {len(zdrojove)}")
    zdroj_klic = zdrojove[0]
    zdroj_guid = re.search(r"-([0-9A-Fa-f-]{36})\.json$", zdroj_klic).group(1).lower()

    customizations = polozky["customizations.xml"].decode("utf-8-sig")
    web = nacti_web(customizations)

    # --- 1. definice flow ---
    vzor = json.loads(polozky[zdroj_klic].decode("utf-8-sig"))
    flow = {
        "properties": {
            # spojení se klonuje: SharePoint akce by bez něj neměly čím běžet
            "connectionReferences": vzor["properties"]["connectionReferences"],
            "definition": {
                "$schema": vzor["properties"]["definition"].get(
                    "$schema",
                    "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#"),
                # "undefined" je past: import projde, ale flow pak nejde
                # otevřít v designeru („Flow not found").
                "contentVersion": "1.0.0.0",
                "parameters": vzor["properties"]["definition"].get("parameters", {}),
                "triggers": trigger(),
                "actions": akce(web),
                "outputs": {},
            },
        },
        "schemaVersion": vzor.get("schemaVersion", "1.0.0.0"),
    }

    cil_klic = f"Workflows/{CIL}-{CIL_GUID.upper()}.json"
    for stary in [n for n in polozky if n.replace("\\", "/").startswith(f"Workflows/{CIL}")]:
        del polozky[stary]
    polozky[cil_klic] = json.dumps(flow, ensure_ascii=False, indent=1).encode("utf-8")

    # --- 2. customizations.xml: klon uzlu <Workflow> ---
    if f'Name="{CIL}"' in customizations:
        stary = uzel_workflow(customizations, CIL_GUID)
        customizations = customizations.replace("\n    " + stary, "").replace(stary, "")
    uzel = uzel_workflow(customizations, zdroj_guid)
    novy = (uzel.replace(zdroj_guid, CIL_GUID)
                .replace(zdroj_guid.upper(), CIL_GUID.upper())
                .replace(ZDROJ, CIL))
    if novy == uzel:
        raise SystemExit("CHYBA: klon uzlu Workflow se od předlohy neliší")
    customizations = customizations.replace(uzel, uzel + "\n    " + novy, 1)
    polozky["customizations.xml"] = customizations.encode("utf-8")

    # --- 3. solution.xml: RootComponent, jinak se flow do balíku nezahrne ---
    solution = polozky["solution.xml"].decode("utf-8-sig")
    solution = re.sub(r'\s*<RootComponent type="29" id="\{' + CIL_GUID + r'\}"[^>]*/>', "", solution)
    zdrojovy_rc = f'<RootComponent type="29" id="{{{zdroj_guid}}}" behavior="0" />'
    if zdrojovy_rc not in solution:
        raise SystemExit("CHYBA: RootComponent zdrojového flow nenalezen")
    solution = solution.replace(
        zdrojovy_rc,
        zdrojovy_rc + f'\n      <RootComponent type="29" id="{{{CIL_GUID}}}" behavior="0" />', 1)
    polozky["solution.xml"] = solution.encode("utf-8")

    with zipfile.ZipFile(cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)

    print(f"přidáno flow: {CIL}")
    print(f"  GUID: {CIL_GUID}")
    print(f"  akcí: {len(flow['properties']['definition']['actions'])}")
    print(f"  web: {web}")
    print(f"  ukládá do: {CILOVA_SLOZKA}/procesni_mapa_<razitko>.doc | .csv")
    print("  vstup: jeden text (JSON s klíči nadpis, format, radky)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
