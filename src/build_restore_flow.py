# -*- coding: utf-8 -*-
"""Přidá do solution flow RestoreFlow — obnovu rejstříku ze snímku zálohy.

Čte `Zalohy/rejstrik_<razitko>.json`, porovná ho s dnešním stavem listů
a v režimu zápisu vrátí data zpět. Vstup je jeden text:

    {"soubor": "rejstrik_2026-09-01_0300.json", "rezim": "nahled" | "zapis"}

Odpověď nese počty za každý list: co se založí, co se změní, co je beze
změny a co dnes je navíc proti snímku.

Čtyři rozhodnutí, která se špatně vracejí zpět (podrobně PLAN.md F11/4):

1. **Nikdy se nezapisuje podle `ID` ze snímku.** To ID je stav k okamžiku
   zálohy; když se záznam mezitím smazal a jiný vznikl, patří dnes někomu
   jinému a zápis podle něj by tiše přepsal cizí řádek. Cílové ID se proto
   VŽDY dohledá v aktuálním listu podle `Title` (kódu) — akce `Najdi_*`
   uvnitř smyčky. Tohle je ta „kontrola shody kódu" z plánu.

2. **Restore nikdy nemaže.** Řádek, který dnes je a ve snímku není, se jen
   spočítá a ohlásí. Jinak by chybný výběr snímku stál data.

3. **Zápis přes `SendHTTPRequest`, ne `PatchItem`.** Konektorová zápisová
   akce s rozloženým tělem `item/<sloupec>` vyžaduje `table` jako GUID
   natvrdo, jinak flow nejde zapnout. U sedmi listů by to znamenalo sedm
   GUID vázaných na jeden tenant. REST adresuje list interním názvem ze
   schématu, který je na všech tenantech stejný.

4. **Porovnává se otiskem.** Logic Apps neumí uvnitř `Filter array` sáhnout
   do druhého pole, takže se z každého řádku poskládá jeden řetězec ze všech
   sloupců schématu; „beze změny" je pak `contains()` nad polem otisků.

Pořadí je závazné: **nejdřív tenhle generátor, teprve pak `build_app.py`.**
Deklarace použitých parametrů doplňuje jedno místo v buildu
(`dorovnej_deklarace_parametru` v `build_app.py`), takže flow přidané až do
hotového balíku by je nemělo a spadlo by za běhu na `InvalidTemplate`.
Volající appka přitom vidí jen `502 BadGateway / NoResponse`.

    copy input/procesnimapa_1_0_0_83.zip runs/app_build/vstup_84.zip
    python src/build_restore_flow.py --solution runs/app_build/vstup_84.zip
    python src/build_app.py --solution runs/app_build/vstup_84.zip --verze 1.0.0.84
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402

ZDROJ = "MapaPublishFlow"
FLOW = "RestoreFlow"
# Pevné GUID: opakovaný build musí dát TOTÉŽ flow, jinak by v prostředí
# přibývali sirotci a každý z nich by blokoval import se stejným ID.
FLOW_GUID = "c4e18b76-3a52-4d09-8f61-2b7d05e9a318"

SCHEMA = Path("src/schema.json")
KNIHOVNA = "/Zalohy"
HOST_SP = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"

# Stejná hodnota jako u zálohy a mapy: 5 000 je view threshold SharePointu.
# Bez pagination načte konektor jen prvních 100 a obnova by porovnávala
# proti oříznutému stavu — tedy by „obnovovala" i to, co se nezměnilo.
STRANKOVANI = 5000

# Oddělovač v otisku řádku. Musí to být řetězec, který se v datech nevyskytne;
# holá svislítka by nestačila, názvy útvarů se oddělují středníkem a mezerou
# a nikdo neručí za to, že v názvu nebude '|'.
ODDELOVAC = "|~|"

# Odpovědi jdou appce jako ODDĚLOVANÝ TEXT, ne JSON. Canvas app má
# `dynamicschema = False`, takže by na `ParseJSON` neměla co navázat;
# `Split()` funguje vždycky. Oddělovače jsou zvolené tak, aby se nemohly
# potkat v názvu aktivity ani souboru.
ODD_POLE = "|~|"
ODD_RADKU = "|#|"

# Oddělovač jména snímku od jeho data v režimu `seznam`. Na rozdíl od
# ODD_POLE ho uživatel VIDÍ — je to popisek v rozbalovátku —, takže musí být
# čitelný. Appka podle něj hodnotu rozděluje zpátky; jsou to dvě místa v
# různých souborech, hlídá je brána `check_app.py`.
ODD_POPISKU = " · "
PASMO = "Central Europe Standard Time"
FORMAT_CASU = "d.M.yyyy H:mm"


REZIM_NAHLED = "nahled"
# Třetí režim: vrátí jen seznam snímků v knihovně, ve stejném tvaru jména,
# jaký sám přijímá na vstupu. Schéma odpovědi se nemění, takže flow
# nepotřebuje novou registraci ve Studiu.
REZIM_SEZNAM = "seznam"
REZIM_ZAPIS = "zapis"

# Hlavičky REST zápisu. `nometadata` znamená, že se do těla nemusí skládat
# `__metadata.type` — jeho tvar (`SP.Data.<list>ListItem`) by se musel buď
# hádat z interního názvu, nebo dotahovat sedmi dalšími voláními.
HLAVICKY_ZAPIS = {
    "Accept": "application/json;odata=nometadata",
    "Content-Type": "application/json;odata=nometadata",
}


def nacti_schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def lit(hodnota):
    """Řetězcový literál do výrazu Logic Apps."""
    return "'" + str(hodnota).replace("'", "''") + "'"


def sp_akce(operace, parametry, po):
    return {
        "type": "OpenApiConnection",
        "inputs": {
            "parameters": parametry,
            "host": {"apiId": HOST_SP, "operationId": operace,
                     "connectionName": "shared_sharepointonline"},
        },
        "runAfter": {po: ["Succeeded"]} if po else {},
    }


def hodnota_ze_snimku(sloupec):
    """Hodnota sloupce v řádku snímku. Choice je tam už rozbalený na text."""
    return f"coalesce(item()?['{sloupec['name']}'], '')"


def hodnota_z_listu(sloupec):
    """Hodnota téhož sloupce v řádku načteném z listu.

    Choice vrací konektor jako objekt — bez ?['Value'] by otisk vyšel jinak
    než ze snímku a obnova by hlásila změnu u každého řádku s číselníkem.
    """
    if sloupec["type"] == "Choice":
        return f"coalesce(item()?['{sloupec['name']}']?['Value'], '')"
    return f"coalesce(item()?['{sloupec['name']}'], '')"


def otisk(sloupce, hodnota):
    """Jeden řetězec ze všech sloupců schématu — porovnávací klíč řádku."""
    casti = []
    for sloupec in sloupce:
        if casti:
            casti.append(lit(ODDELOVAC))
        casti.append(f"string({hodnota(sloupec)})")
    return "@concat(" + ", ".join(casti) + ")"


def hodnota_do_tela(sloupec, smycka):
    """Hodnota jednoho sloupce v těle REST zápisu.

    Prázdné datum se musí poslat jako `null`, ne jako prázdný řetězec —
    ten SharePoint u sloupce typu DateTime odmítne a celý řádek se nezapíše.
    Textové sloupce naopak prázdný řetězec snesou a `null` by u nich jen
    zbytečně rozlišoval „prázdné" a „nevyplněné".
    """
    cti = f"items('{smycka}')?['{sloupec['name']}']"
    if sloupec["type"] == "DateTime":
        return f"@if(empty(coalesce({cti}, '')), json('null'), {cti})"
    return f"@coalesce({cti}, '')"


def telo_zapisu(sloupce, smycka):
    """Tělo REST zápisu z řádku snímku. Klíče jsou interní názvy sloupců —
    proto snímek ukládá právě je a ne zobrazované názvy."""
    return {c["name"]: hodnota_do_tela(c, smycka) for c in sloupce}


def akce(schema):
    kroky = {}
    listy = schema["lists"]

    kroky["Vstup"] = {
        "type": "Compose",
        "inputs": "@json(triggerBody()['text'])",
        "runAfter": {},
    }

    kroky["Cesta_seznamu"] = {
        "type": "Compose",
        "inputs": "@concat('/', join(skip(split(" + ep.vyraz(ep.WEB) + ", '/'), 3), '/'))",
        "runAfter": {"Vstup": ["Succeeded"]},
    }

    # Režim seznamu končí vlastní odpovědí a ukončením běhu — dál se nepokračuje,
    # protože bez názvu snímku by `Soubor` neměl co číst.
    kroky["Rezim_seznam"] = {
        "type": "If",
        "expression": {"equals": ["@outputs('Vstup')?['rezim']", REZIM_SEZNAM]},
        "actions": {
            "Soubory": sp_akce(
                "HttpRequest",
                {"dataset": ep.web(),
                 "parameters/method": "GET",
                 "parameters/uri": (
                     "@concat('_api/web/GetList(" + chr(39) * 3 + ", outputs('Cesta_seznamu'), "
                     + lit(KNIHOVNA) + ", " + chr(39) * 3
                     + ")/items?$select=FileLeafRef,Created&$top=500&$orderby=Created desc')"),
                 "parameters/headers": {"Accept": "application/json;odata=nometadata"}},
                None),
            # Za jméno se připojuje čas pořízení, aby šlo v appce poznat, který
            # snímek je který. `Created` ze SharePointu je UTC — bez převodu by
            # noční záloha hlásila 3:00 místo 5:00 a vypadala jako cizí soubor.
            # Appka si jméno před odesláním do flow ořízne po ODD_POPISKU.
            "Jmena": {
                "type": "Select",
                "inputs": {
                    "from": "@coalesce(body('Soubory')?['value'], createArray())",
                    "select": ("@concat(item()?['FileLeafRef'], " + lit(ODD_POPISKU)
                               + ", formatDateTime(convertFromUtc(item()?['Created'], "
                               + lit(PASMO) + "), " + lit(FORMAT_CASU) + "))"),
                },
                "runAfter": {"Soubory": ["Succeeded"]},
            },
            "Odpoved_seznam": {
                "type": "Response",
                "kind": "PowerApp",
                "inputs": {
                    "statusCode": 200,
                    "body": {
                        "stav": REZIM_SEZNAM,
                        "hlaseni": "",
                        "porizeno": "",
                        "prehled": "@join(body('Jmena'), " + lit(ODD_RADKU) + ")",
                    },
                    "schema": {"type": "object", "properties": {
                        "stav": {"type": "string"},
                        "hlaseni": {"type": "string"},
                        "porizeno": {"type": "string"},
                        "prehled": {"type": "string"},
                    }},
                },
                "runAfter": {"Jmena": ["Succeeded"]},
            },
            "Konec_seznamu": {
                "type": "Terminate",
                "inputs": {"runStatus": "Succeeded"},
                "runAfter": {"Odpoved_seznam": ["Succeeded"]},
            },
        },
        "runAfter": {"Cesta_seznamu": ["Succeeded"]},
    }

    # inferContentType false + $content: konektor obsah sám nedekóduje, takže
    # `base64ToString` platí. S výchozím true vrací body() rovnou řetězec
    # a $content neexistuje — míchat obojí se nedá (ověřeno u mapy).
    kroky["Soubor"] = sp_akce(
        "GetFileContentByPath",
        {"dataset": ep.web(),
         "path": f"@concat({lit(KNIHOVNA + '/')}, outputs('Vstup')?['soubor'])",
         "inferContentType": False},
        "Rezim_seznam")

    kroky["Snimek"] = {
        "type": "Compose",
        "inputs": "@json(base64ToString(body('Soubor')?['$content']))",
        "runAfter": {"Soubor": ["Succeeded"]},
    }

    # Server-relative cesta webu — z ní se skládají REST adresy listů.
    kroky["Cesta_webu"] = {
        "type": "Compose",
        "inputs": f"@concat('/', join(skip(split({ep.vyraz(ep.WEB)}, '/'), 3), '/'))",
        "runAfter": {"Snimek": ["Succeeded"]},
    }

    # Snímek pořízený nad jinou strukturou listů se musí odmítnout, ne obnovit
    # napůl. Odpověď odchází z větve `else` a běh se ukončí — další akce se
    # tedy neprovedou a nemá smysl je do podmínky vnořovat.
    kroky["Kontrola_verze"] = {
        "type": "If",
        "expression": {"equals": ["@outputs('Snimek')?['schema_verze']",
                                  schema["verze"]]},
        "actions": {},
        "else": {"actions": {
            "Odpoved_neshoda": {
                "type": "Response",
                "kind": "PowerApp",
                "inputs": {
                    "statusCode": 200,
                    "body": {
                        "stav": "neshoda_schematu",
                        "hlaseni": ("@concat('Snímek je proti jiné verzi schématu ('"
                                    ", string(outputs('Snimek')?['schema_verze']),"
                                    " '), rejstřík má " + schema["verze"] + "."
                                    " Obnovit ho nejde.')"),
                        "porizeno": "@outputs('Snimek')?['porizeno']",
                        "prehled": "",
                    },
                    "schema": {"type": "object", "properties": {
                        "stav": {"type": "string"},
                        "hlaseni": {"type": "string"},
                        "porizeno": {"type": "string"},
                        "prehled": {"type": "string"},
                    }},
                },
                "runAfter": {},
            },
            "Konec": {
                "type": "Terminate",
                "inputs": {"runStatus": "Succeeded"},
                "runAfter": {"Odpoved_neshoda": ["Succeeded"]},
            },
        }},
        "runAfter": {"Cesta_webu": ["Succeeded"]},
    }

    predchozi = "Kontrola_verze"
    for lst in listy:
        jmeno = f"Nacti_{lst['name']}"
        kroky[jmeno] = sp_akce(
            "GetItems",
            {"dataset": ep.web(),
             "table": ep.list_param(lst.get("display") or lst["name"]),
             "$top": STRANKOVANI},
            predchozi)
        kroky[jmeno]["runtimeConfiguration"] = {
            "paginationPolicy": {"minimumItemCount": STRANKOVANI}
        }
        predchozi = jmeno

    for lst in listy:
        jmeno = lst["name"]
        sloupce = lst["columns"]
        ze_snimku = f"@outputs('Snimek')?['listy']?['{jmeno}']"
        z_listu = f"@outputs('Nacti_{jmeno}')?['body/value']"

        kroky[f"Kody_{jmeno}"] = {
            "type": "Select",
            "inputs": {"from": z_listu, "select": "@item()?['Title']"},
            "runAfter": {predchozi: ["Succeeded"]},
        }
        kroky[f"Otisky_{jmeno}"] = {
            "type": "Select",
            "inputs": {"from": z_listu, "select": otisk(sloupce, hodnota_z_listu)},
            "runAfter": {f"Kody_{jmeno}": ["Succeeded"]},
        }
        kroky[f"KodySnimku_{jmeno}"] = {
            "type": "Select",
            "inputs": {"from": ze_snimku, "select": "@item()?['Title']"},
            "runAfter": {f"Otisky_{jmeno}": ["Succeeded"]},
        }
        kroky[f"K_zalozeni_{jmeno}"] = {
            "type": "Query",
            "inputs": {
                "from": ze_snimku,
                "where": (f"@not(contains(body('Kody_{jmeno}'),"
                          f" coalesce(item()?['Title'], '')))"),
            },
            "runAfter": {f"KodySnimku_{jmeno}": ["Succeeded"]},
        }
        # Změna = kód v listu je, ale otisk řádku se liší. Otisk se počítá
        # ze VŠECH sloupců schématu, takže „beze změny" znamená opravdu
        # shodu, ne jen shodu názvu.
        kroky[f"Ke_zmene_{jmeno}"] = {
            "type": "Query",
            "inputs": {
                "from": ze_snimku,
                "where": (f"@and(contains(body('Kody_{jmeno}'),"
                          f" coalesce(item()?['Title'], '')),"
                          f" not(contains(body('Otisky_{jmeno}'),"
                          f" {otisk(sloupce, hodnota_ze_snimku)[1:]})))"),
            },
            "runAfter": {f"K_zalozeni_{jmeno}": ["Succeeded"]},
        }
        # Řádky, které dnes jsou a ve snímku nejsou. Restore je NEMAŽE,
        # jen je spočítá do přehledu.
        kroky[f"Navic_{jmeno}"] = {
            "type": "Query",
            "inputs": {
                "from": z_listu,
                "where": (f"@not(contains(body('KodySnimku_{jmeno}'),"
                          f" coalesce(item()?['Title'], '')))"),
            },
            "runAfter": {f"Ke_zmene_{jmeno}": ["Succeeded"]},
        }
        predchozi = f"Navic_{jmeno}"

    kroky["Zapis"] = {
        "type": "If",
        "expression": {"equals": ["@outputs('Vstup')?['rezim']", REZIM_ZAPIS]},
        "actions": zapisove_akce(listy),
        "runAfter": {predchozi: ["Succeeded"]},
    }

    # Jeden řádek na list, pole v pevném pořadí: název, založit, změnit,
    # navíc, celkem ve snímku. Pořadí je součástí kontraktu s obrazovkou
    # náhledu — appka je bere podle indexu, ne podle klíče.
    radky = []
    for lst in listy:
        jmeno = lst["name"]
        radky.append("concat(" + ", ".join([
            lit(jmeno),
            lit(ODD_POLE),
            f"string(length(body('K_zalozeni_{jmeno}')))",
            lit(ODD_POLE),
            f"string(length(body('Ke_zmene_{jmeno}')))",
            lit(ODD_POLE),
            f"string(length(body('Navic_{jmeno}')))",
            lit(ODD_POLE),
            f"string(length(outputs('Snimek')?['listy']?['{jmeno}']))",
        ]) + ")")
    kroky["Prehled"] = {
        "type": "Compose",
        "inputs": "@concat(" + (", " + lit(ODD_RADKU) + ", ").join(radky) + ")",
        "runAfter": {"Zapis": ["Succeeded"]},
    }

    kroky["Odpoved"] = {
        "type": "Response",
        "kind": "PowerApp",
        "inputs": {
            "statusCode": 200,
            "body": {
                "stav": f"@if(equals(outputs('Vstup')?['rezim'], {lit(REZIM_ZAPIS)}),"
                        f" 'zapsano', 'nahled')",
                "hlaseni": "",
                "porizeno": "@outputs('Snimek')?['porizeno']",
                # Přehled jde jako řetězec: schéma odpovědi se pak nemění
                # s počtem listů a appka si ho rozebere ParseJSON.
                "prehled": "@outputs('Prehled')",
            },
            "schema": {"type": "object", "properties": {
                "stav": {"type": "string"},
                "hlaseni": {"type": "string"},
                "porizeno": {"type": "string"},
                "prehled": {"type": "string"},
            }},
        },
        "runAfter": {"Prehled": ["Succeeded"]},
    }
    return kroky


def rest_adresa(jmeno_listu, uvnitr=""):
    """REST adresa listu podle INTERNÍHO názvu — ten je na všech tenantech
    stejný, kdežto GUID ani zobrazovaný název ne."""
    return (f"@concat('_api/web/GetList(''', outputs('Cesta_webu'),"
            f" {lit('/Lists/' + jmeno_listu)}, ''')/items{uvnitr}')")


def zapisove_akce(listy):
    """Zápis po řádku. Založení je POST, změna MERGE na dohledané ID.

    `$batch` by byl rychlejší, ale multipart changeset se v Logic Apps skládá
    ručně z hranic a hlaviček a chyba v něm se pozná až za běhu. Šest set
    řádků po jednom je u ruční operace otázka desítek sekund.
    """
    kroky = {}
    predchozi = None
    for lst in listy:
        jmeno = lst["name"]
        sloupce = lst["columns"]

        smycka_z = f"Zaloz_{jmeno}"
        telo = telo_zapisu(sloupce, smycka_z)
        kroky[smycka_z] = {
            "type": "Foreach",
            "foreach": f"@body('K_zalozeni_{jmeno}')",
            "actions": {
                f"Vloz_{jmeno}": sp_akce(
                    "HttpRequest",
                    {"dataset": ep.web(),
                     "parameters/method": "POST",
                     "parameters/uri": rest_adresa(jmeno),
                     "parameters/headers": HLAVICKY_ZAPIS,
                     "parameters/body": telo},
                    None),
            },
            "runAfter": {predchozi: ["Succeeded"]} if predchozi else {},
        }

        smycka_u = f"Uprav_{jmeno}"
        telo_u = telo_zapisu(sloupce, smycka_u)
        kroky[smycka_u] = {
            "type": "Foreach",
            "foreach": f"@body('Ke_zmene_{jmeno}')",
            "actions": {
                # Cílové ID se dohledává podle KÓDU v aktuálním listu, nikdy
                # se nebere `ID` ze snímku: to je stav k okamžiku zálohy a po
                # smazání a znovuzaložení patří jinému záznamu.
                f"Najdi_{jmeno}": {
                    "type": "Query",
                    "inputs": {
                        "from": f"@outputs('Nacti_{jmeno}')?['body/value']",
                        "where": (f"@equals(coalesce(item()?['Title'], ''),"
                                  f" coalesce(items('{smycka_u}')?['Title'], ''))"),
                    },
                    "runAfter": {},
                },
                f"Zmen_{jmeno}": sp_akce(
                    "HttpRequest",
                    {"dataset": ep.web(),
                     "parameters/method": "POST",
                     "parameters/uri": rest_adresa(
                         jmeno,
                         f"(', string(first(body('Najdi_{jmeno}'))?['ID']), ')"),
                     "parameters/headers": dict(HLAVICKY_ZAPIS,
                                                **{"X-HTTP-Method": "MERGE",
                                                   "IF-MATCH": "*"}),
                     "parameters/body": telo_u},
                    f"Najdi_{jmeno}"),
            },
            "runAfter": {smycka_z: ["Succeeded"]},
        }
        predchozi = smycka_u
    return kroky


def trigger():
    """PowerAppV2 s jedním textovým vstupem — týž tvar, jaký má ExportFlow."""
    return {"manual": {
        "type": "Request",
        "kind": "PowerAppV2",
        "inputs": {"schema": {
            "type": "object",
            "properties": {"text": {
                "title": "pozadavek",
                "type": "string",
                "x-ms-dynamically-added": True,
                "description": ('JSON: {"soubor": "rejstrik_….json", '
                                '"rezim": "nahled" | "zapis"}'),
            }},
            "required": ["text"],
        }},
    }}


def definice_flow(vzor, kroky):
    return {
        "properties": {
            "connectionReferences": vzor["properties"]["connectionReferences"],
            "definition": {
                "$schema": vzor["properties"]["definition"].get(
                    "$schema",
                    "https://schema.management.azure.com/providers/Microsoft.Logic/"
                    "schemas/2016-06-01/workflowdefinition.json#"),
                "contentVersion": "1.0.0.0",
                "parameters": vzor["properties"]["definition"].get("parameters", {}),
                "triggers": trigger(),
                "actions": kroky,
                "outputs": {},
            },
        },
        "schemaVersion": vzor.get("schemaVersion", "1.0.0.0"),
    }


def uzel_workflow(customizations, guid):
    zacatek = customizations.index(f'<Workflow WorkflowId="{{{guid}}}"')
    konec = customizations.index("</Workflow>", zacatek) + len("</Workflow>")
    return customizations[zacatek:konec]


def pridej_uzel(customizations, zdroj_guid, cil_guid, cil_nazev):
    if f'Name="{cil_nazev}"' in customizations:
        stary = uzel_workflow(customizations, cil_guid)
        customizations = customizations.replace("\n    " + stary, "").replace(stary, "")
    uzel = uzel_workflow(customizations, zdroj_guid)
    novy = (uzel.replace(zdroj_guid, cil_guid)
                .replace(zdroj_guid.upper(), cil_guid.upper())
                .replace(ZDROJ, cil_nazev))
    if novy == uzel:
        raise SystemExit("CHYBA: klon uzlu Workflow se od předlohy neliší")
    return customizations.replace(uzel, uzel + "\n    " + novy, 1)


def pridej_rootcomponent(solution, zdroj_guid, cil_guid):
    solution = re.sub(r'\s*<RootComponent type="29" id="\{' + cil_guid + r'\}"[^>]*/>',
                      "", solution)
    zdrojovy = f'<RootComponent type="29" id="{{{zdroj_guid}}}" behavior="0" />'
    if zdrojovy not in solution:
        raise SystemExit("CHYBA: RootComponent zdrojového flow nenalezen")
    return solution.replace(
        zdrojovy,
        zdrojovy + f'\n      <RootComponent type="29" id="{{{cil_guid}}}" behavior="0" />', 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True)
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
    vzor = json.loads(polozky[zdroj_klic].decode("utf-8-sig"))

    schema = nacti_schema()
    flow = definice_flow(vzor, akce(schema))

    customizations = polozky["customizations.xml"].decode("utf-8-sig")
    solution = polozky["solution.xml"].decode("utf-8-sig")

    for stary in [n for n in polozky
                  if n.replace("\\", "/").startswith(f"Workflows/{FLOW}")]:
        del polozky[stary]
    polozky[f"Workflows/{FLOW}-{FLOW_GUID.upper()}.json"] = json.dumps(
        flow, ensure_ascii=False, indent=1).encode("utf-8")
    customizations = pridej_uzel(customizations, zdroj_guid, FLOW_GUID, FLOW)
    solution = pridej_rootcomponent(solution, zdroj_guid, FLOW_GUID)

    polozky["customizations.xml"] = customizations.encode("utf-8")
    polozky["solution.xml"] = solution.encode("utf-8")

    with zipfile.ZipFile(cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)

    pocet = len(flow["properties"]["definition"]["actions"])
    print(f"přidáno flow: {FLOW}")
    print(f"  GUID: {FLOW_GUID}")
    print(f"  akcí nejvyšší úrovně: {pocet}")
    print(f"  listů v obnově: {len(schema['lists'])}")
    print(f"  čte snímky z: {KNIHOVNA}")
    print(f"  režimy vstupu: {REZIM_NAHLED} | {REZIM_ZAPIS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
