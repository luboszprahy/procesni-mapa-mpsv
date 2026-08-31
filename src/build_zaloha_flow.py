# -*- coding: utf-8 -*-
"""Přidá do solution flow ZalohaFlow a jeho plánované dvojče ZalohaScheduled.

Snímek rejstříku: přečte všechny listy ze `src/schema.json` a uloží je jako
jeden JSON do knihovny `Zalohy` pod jménem `rejstrik_<RRRR-MM-DD_HHMM>.json`.

Proč dvě flow: Logic Apps má na flow právě jeden trigger, takže „na tlačítko
z appky" a „každý den ráno" nejde spojit. Obě definice se ale staví z TÉŽE
funkce `akce()` — ne klonováním hotového flow ze zipu. Rozejít se tedy nemají
jak; kdyby se stavěly zvlášť, zálohoval by plán časem něco jiného než tlačítko
a nikdo by si toho nevšiml, dokud by zálohu nepotřeboval.

Obálka (spojení, uzel <Workflow>, RootComponent) se klonuje z MapaPublishFlow
— je to nejbezpečnější lokální úprava exportu, jakou skill připouští. GUID jsou
pevné, aby opakovaný build nezakládal v prostředí nová flow.

Spouštět z kořene projektu, na balíku už složeném build_app.py:
    python src/build_zaloha_flow.py --solution deploy/procesnimapa_1_0_0_76.zip
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
RUCNI = "ZalohaFlow"
PLANOVANE = "ZalohaScheduled"

# Pevná GUID: opakované spuštění musí dát TÁŽ flow, jinak by každý build
# zakládal v prostředí nová a hromadili by se sirotci.
RUCNI_GUID = "9a4c7e13-2d68-4f05-b7c1-8e3a5d901f24"
PLANOVANE_GUID = "2f81b6ca-5e47-4d39-a0b2-c73f18e64d5b"

SCHEMA = Path("src/schema.json")
KNIHOVNA = "/Zalohy"
CASOVE_PASMO = "Central Europe Standard Time"

# Kolik položek se z listu načte. Stejná hodnota jako v build_mapa_flow.py:
# 5 000 je view threshold SharePointu. Bez pagination načte konektor jen
# prvních 100 a snímek se TIŠE ořízne — u zálohy nejhorší možná vada, protože
# se pozná až ve chvíli, kdy se z ní obnovuje.
STRANKOVANI = 5000

HOST_SP = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"


def nacti_schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


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


def vyber(sloupce):
    """Mapování řádku na snímek. Klíče jsou interní názvy sloupců, aby se
    ze snímku dalo zapisovat zpátky bez překladové tabulky."""
    v = {"ID": "@item()?['ID']"}
    for c in sloupce:
        if c["type"] == "Choice":
            # Choice vrací objekt; bez ?['Value'] by se do snímku uložilo
            # {"Value":"…"} a restore by zapsal nesmysl.
            v[c["name"]] = f"@item()?['{c['name']}']?['Value']"
        else:
            v[c["name"]] = f"@item()?['{c['name']}']"
    return v


def akce(schema):
    """Akce snímku. Sdílí je ruční i plánované flow — proto jedna funkce."""
    kroky = {}

    # Razítko se počítá JEDNOU. Kdyby se utcNow() volalo zvlášť pro jméno
    # souboru a zvlášť pro obsah, mohly by se o vteřinu rozejít a snímek by
    # tvrdil něco jiného, než má v názvu.
    kroky["Razitko"] = {
        "type": "Compose",
        "inputs": "@formatDateTime(utcNow(), 'yyyy-MM-dd_HHmm')",
        "runAfter": {},
    }

    predchozi = "Razitko"
    for lst in schema["lists"]:
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

    for lst in schema["lists"]:
        kroky[f"Map_{lst['name']}"] = {
            "type": "Select",
            "inputs": {"from": f"@outputs('Nacti_{lst['name']}')?['body/value']",
                       "select": vyber(lst["columns"])},
            "runAfter": {predchozi: ["Succeeded"]},
        }
        predchozi = f"Map_{lst['name']}"

    kroky["Snimek"] = {
        "type": "Compose",
        "inputs": {
            # Verze schématu je v souboru schválně: restore ze snímku, který
            # vznikl nad jinou strukturou listů, musí umět odmítnout.
            "schema_verze": schema["verze"],
            "porizeno": "@outputs('Razitko')",
            "listy": {lst["name"]: f"@body('Map_{lst['name']}')"
                      for lst in schema["lists"]},
        },
        "runAfter": {predchozi: ["Succeeded"]},
    }

    kroky["Uloz_zalohu"] = sp_akce(
        "CreateFile",
        {"dataset": ep.web(),
         "folderPath": KNIHOVNA,
         "name": "@concat('rejstrik_', outputs('Razitko'), '.json')",
         "body": "@string(outputs('Snimek'))"},
        "Snimek")
    return kroky


def trigger_rucni():
    """PowerAppV2 bez vstupů — tvar, jaký generuje designer."""
    return {"manual": {"type": "Request", "kind": "PowerAppV2",
                       "inputs": {"schema": {"type": "object", "properties": {},
                                             "required": []}}}}


def trigger_planovany(hodina):
    """Denní Recurrence. startTime bez pásma — timeZone si ho určuje sám."""
    return {"Recurrence": {
        "type": "Recurrence",
        "recurrence": {
            "frequency": "Day", "interval": 1, "timeZone": CASOVE_PASMO,
            "startTime": f"2026-01-01T{hodina:02d}:00:00",
            "schedule": {"hours": [str(hodina)], "minutes": [0]},
        },
    }}


def definice_flow(vzor, trigger, kroky):
    return {
        "properties": {
            # spojení se klonuje: SharePoint akce by bez něj neměly čím běžet
            "connectionReferences": vzor["properties"]["connectionReferences"],
            "definition": {
                "$schema": vzor["properties"]["definition"].get(
                    "$schema",
                    "https://schema.management.azure.com/providers/Microsoft.Logic/"
                    "schemas/2016-06-01/workflowdefinition.json#"),
                # "undefined" je past: import projde, ale flow pak nejde
                # otevřít v designeru („Flow not found").
                "contentVersion": "1.0.0.0",
                # Deklarace použitých parametrů doplní build_app.py
                # (dorovnej_deklarace_parametru) — jedno místo pro všechna flow.
                "parameters": vzor["properties"]["definition"].get("parameters", {}),
                "triggers": trigger,
                "actions": kroky,
                "outputs": {},
            },
        },
        "schemaVersion": vzor.get("schemaVersion", "1.0.0.0"),
    }


def uzel_workflow(customizations, guid):
    """Vystřihne <Workflow> daného flow — klon se z něj vyrobí náhradami."""
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
    parser.add_argument("--solution", required=True, help="solution zip, do kterého se flow přidají")
    parser.add_argument("--hodina", type=int, default=5, help="hodina denního běhu (0-23)")
    argumenty = parser.parse_args()
    if not 0 <= argumenty.hodina <= 23:
        raise SystemExit("CHYBA: --hodina musí být 0 až 23")

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
    kroky = akce(schema)

    customizations = polozky["customizations.xml"].decode("utf-8-sig")
    solution = polozky["solution.xml"].decode("utf-8-sig")

    for nazev, guid, trigger in (
            (RUCNI, RUCNI_GUID, trigger_rucni()),
            (PLANOVANE, PLANOVANE_GUID, trigger_planovany(argumenty.hodina))):
        flow = definice_flow(vzor, trigger, kroky)
        for stary in [n for n in polozky
                      if n.replace("\\", "/").startswith(f"Workflows/{nazev}")]:
            del polozky[stary]
        polozky[f"Workflows/{nazev}-{guid.upper()}.json"] = json.dumps(
            flow, ensure_ascii=False, indent=1).encode("utf-8")
        customizations = pridej_uzel(customizations, zdroj_guid, guid, nazev)
        solution = pridej_rootcomponent(solution, zdroj_guid, guid)

    polozky["customizations.xml"] = customizations.encode("utf-8")
    polozky["solution.xml"] = solution.encode("utf-8")

    with zipfile.ZipFile(cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)

    print(f"přidána flow: {RUCNI} ({RUCNI_GUID}), {PLANOVANE} ({PLANOVANE_GUID})")
    print(f"  akcí v každém: {len(kroky)} (týchž, z jedné funkce)")
    print(f"  zálohovaných listů: {len(schema['lists'])} "
          f"({', '.join(l['name'] for l in schema['lists'])})")
    print(f"  ukládá do: {KNIHOVNA}/rejstrik_<RRRR-MM-DD_HHMM>.json")
    print(f"  plán: denně v {argumenty.hodina}:00, {CASOVE_PASMO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
