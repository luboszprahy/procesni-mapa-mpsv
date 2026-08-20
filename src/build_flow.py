# -*- coding: utf-8 -*-
"""Dopíše do exportovaného flow AktualizaceKratkehoNazvu chybějící akce.

Uživatel dodá z designeru kostru (trigger nad listem Aktivity + jedna Compose),
tenhle skript doplní řetěz výpočtu, podmínku a zápis. Trigger, connection
reference ani GUID flow se nemění — jinak by import nebyl upgrade.

Spouštět z kořene projektu:
    python src/build_flow.py --solution deploy/procesnimapa_1_0_0_9.zip
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

# GUID listu Aktivity na vývojové site (z F1). Zápisová akce ho musí mít
# natvrdo — s runtime výrazem se flow naimportuje, ale nejde zapnout.
LIST_AKTIVITY = "9dfbb5a1-65a6-4fd4-b9f9-fdd35fa246cd"

MAXLEN = 150
VYPUSTKA = "decodeUriComponent('%E2%80%A6')"


def compose(vyraz, po):
    return {"type": "Compose", "inputs": vyraz, "runAfter": {po: ["Succeeded"]} if po else {}}


def orez(zdroj):
    """Odmaže jeden koncový znak z ' ,;.'; pro prázdný vstup nedělá nic.

    min/max drží všechny podvýrazy platné i pro prázdný řetězec — `if()`
    v Logic Apps vyhodnocuje obě větve, takže neplatný podvýraz by akci shodil
    i ve větvi, která se nepoužije.
    """
    x = f"outputs('{zdroj}')"
    posledni = f"substring({x}, max(0, sub(length({x}), 1)), min(1, length({x})))"
    bez_posledniho = f"substring({x}, 0, max(0, sub(length({x}), 1)))"
    return f"@if(contains(' ,;.', {posledni}), {bez_posledniho}, {x})"


def akce():
    b = "outputs('Bez_bilych_znaku')"
    rez = "outputs('Rez')"
    mezera = f"lastIndexOf({rez}, ' ')"

    kroky = {
        "Nazev_syrovy": compose("@coalesce(triggerBody()?['nazev'], '')", None),
        "Bez_bilych_znaku": compose(
            "@trim(replace(replace(replace(replace(replace(replace("
            "outputs('Nazev_syrovy'), decodeUriComponent('%0D'), ' '), "
            "decodeUriComponent('%0A'), ' '), decodeUriComponent('%09'), ' '), "
            "'  ', ' '), '  ', ' '), '  ', ' '))",
            "Nazev_syrovy"),
        "Rez": compose(f"@substring({b}, 0, min({MAXLEN - 1}, length({b})))", "Bez_bilych_znaku"),
        "Rez_na_slovo": compose(
            f"@if(greater({mezera}, {MAXLEN // 2}), substring({rez}, 0, max(0, {mezera})), {rez})",
            "Rez"),
        "Orez_1": compose(orez("Rez_na_slovo"), "Rez_na_slovo"),
        "Orez_2": compose(orez("Orez_1"), "Orez_1"),
        "Orez_3": compose(orez("Orez_2"), "Orez_2"),
        "Cil": compose(
            f"@if(lessOrEquals(length({b}), {MAXLEN}), {b}, "
            f"concat(outputs('Orez_3'), {VYPUSTKA}))",
            "Orez_3"),
    }

    kroky["Lisi_se"] = {
        "type": "If",
        "expression": {"and": [{"not": {"equals": [
            "@coalesce(triggerBody()?['nazev_kratky'], '')",
            "@outputs('Cil')",
        ]}}]},
        "actions": {
            "Zapsat_kratky_nazev": {
                "type": "OpenApiConnection",
                "inputs": {
                    "parameters": {
                        "dataset": DATASET,
                        "table": LIST_AKTIVITY,
                        "id": "@triggerBody()?['ID']",
                        "item/nazev_kratky": "@outputs('Cil')",
                    },
                    "host": {
                        "apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                        "operationId": "PatchItem",
                        "connectionName": "shared_sharepointonline",
                    },
                },
                "runAfter": {},
            }
        },
        "else": {"actions": {}},
        "runAfter": {"Cil": ["Succeeded"]},
    }
    return kroky


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True, help="solution zip s exportovaným flow")
    argumenty = parser.parse_args()

    cesta = Path(argumenty.solution)
    with zipfile.ZipFile(cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    workflow = [n for n in polozky if n.replace("\\", "/").startswith("Workflows/")]
    if len(workflow) != 1:
        raise SystemExit(f"CHYBA: čekám právě jedno flow, našel jsem {len(workflow)}")
    klic = workflow[0]

    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    definice = flow["properties"]["definition"]

    triggery = definice.get("triggers", {})
    if len(triggery) != 1:
        raise SystemExit("CHYBA: flow musí mít právě jeden trigger")
    trigger = next(iter(triggery.values()))
    operace = trigger.get("inputs", {}).get("host", {}).get("operationId")
    if operace != "GetOnUpdatedItems":
        raise SystemExit(f"CHYBA: trigger je '{operace}', čekal jsem GetOnUpdatedItems")
    tabulka = trigger["inputs"]["parameters"].get("table")
    if tabulka != LIST_AKTIVITY:
        raise SystemExit(f"CHYBA: trigger míří na list {tabulka}, ne na Aktivity ({LIST_AKTIVITY})")

    global DATASET
    DATASET = trigger["inputs"]["parameters"]["dataset"]

    definice["actions"] = akce()
    definice["contentVersion"] = "1.0.0.0"
    polozky[klic] = json.dumps(flow, ensure_ascii=False, indent=1).encode("utf-8")

    with zipfile.ZipFile(cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)

    print(f"flow doplněno: {klic.split('/')[-1]}")
    print(f"  akcí: {len(definice['actions'])}, zápis do listu {LIST_AKTIVITY}")
    print(f"  web z triggeru: {DATASET}")
    return 0


DATASET = None

if __name__ == "__main__":
    sys.exit(main())
