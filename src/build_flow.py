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

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402

# Web i list bere flow z proměnných prostředí — včetně triggeru a zápisové
# akce. Do 1.0.0.61 tu byl GUID vývojového listu natvrdo, protože skill tvrdí,
# že zápisová akce runtime výraz nesnese. Rozbor produkčních balíků PPF
# (Clearstream, Průvodní list, Správa notifikací) to vyvrátil: PatchItem,
# PostItem i trigger nad listem s proměnnou běží. Podmínkou je typ proměnné —
# datasetová (100000004), ne textová. Viz src/env_promenne.py.
MAXLEN = 150
AKTUALNI = "body('Nacti_aktivitu')"

# GUID listu Aktivity v CÍLOVÉM prostředí. Jediné místo v celém balíku, kde je
# identifikátor listu natvrdo — a je to nutné zlo:
#
#   PatchItem si schéma těla odvozuje z konkrétního listu. Když je `table`
#   runtime výraz (proměnná prostředí), schéma se nerozbalí a rozložené klíče
#   `item/<sloupec>` přestanou být platné. Flow se naimportuje, ale zapnout
#   nejde — "The API operation 'PatchItem' is missing required property 'item'"
#   (MPSV, 28.08.2026, balík 1.0.0.64; totéž FloorPlan 1.0.0.21).
#
# `dataset` (web) proměnnou snese, ta je pro tělo bez významu — přesně tuhle
# kombinaci má i produkční FloorPlan. Ostatní tři flow zůstávají celá na
# proměnných; tohle jediné se při přenosu na další tenant musí přegenerovat
# s novým GUID (`--list-aktivity`).
LIST_AKTIVITY_MPSV = "b1daaa38-53df-4c7b-b9f8-03b36d46bc60"
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


def akce(list_aktivity):
    b = "outputs('Bez_bilych_znaku')"
    rez = "outputs('Rez')"
    mezera = f"lastIndexOf({rez}, ' ')"

    kroky = {
        # Čerstvý stav řádku. Trigger dává snímek starý až o minutu (polling
        # po 1 min), takže z něj smí přijít jen ID — jinak flow zapíše povinná
        # pole v podobě, v jaké byla PŘED editací, a novější hodnotu přepíše.
        "Nacti_aktivitu": {
            "type": "OpenApiConnection",
            "inputs": {
                "parameters": {
                    "dataset": ep.web(),
                    "table": list_aktivity,
                    "id": "@triggerBody()?['ID']",
                },
                "host": {
                    "apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                    "operationId": "GetItem",
                    "connectionName": "shared_sharepointonline",
                },
            },
            "runAfter": {},
        },
        "Nazev_syrovy": compose(
            f"@coalesce({AKTUALNI}?['nazev'], '')", "Nacti_aktivitu"),
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
            f"@coalesce({AKTUALNI}?['nazev_kratky'], '')",
            "@outputs('Cil')",
        ]}}]},
        "actions": {
            "Zapsat_kratky_nazev": {
                "type": "OpenApiConnection",
                "inputs": {
                    "parameters": {
                        "dataset": ep.web(),
                        "table": list_aktivity,
                        "id": "@triggerBody()?['ID']",
                        # Povinné sloupce listu musí v těle být, i když se nemění —
                        # bez nich se flow nedá aktivovat (OpenApiOperation-
                        # ParameterValidationFailed, "missing required property
                        # 'item/Title'"; ověřeno importem 1.0.0.9 na PPF a znovu
                        # 1.0.0.63 na MPSV). Berou se z Nacti_aktivitu, tedy ze stavu
                        # z okamžiku zápisu — z triggeru by to byl snímek starý až
                        # o minutu a novější editace by se tiše vrátila zpátky.
                        "item/Title": f"@{AKTUALNI}?['Title']",
                        "item/nazev": f"@{AKTUALNI}?['nazev']",
                        "item/dilci_proces_kod": f"@{AKTUALNI}?['dilci_proces_kod']",
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
    parser.add_argument("--list-aktivity", default=LIST_AKTIVITY_MPSV,
                        help="GUID listu Aktivity v cílovém prostředí (PatchItem "
                             "ho runtime výrazem nesnese, viz komentář u konstanty)")
    argumenty = parser.parse_args()

    cesta = Path(argumenty.solution)
    with zipfile.ZipFile(cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    # Solution obsahuje víc flow, vybíráme podle jména — pořadí ani počet
    # se spoléhat nedá (od 1.0.0.18 je v balíku i MapaPublishFlow).
    workflow = [n for n in polozky
                if n.replace("\\", "/").startswith("Workflows/AktualizaceKratkehoNazvu")]
    if len(workflow) != 1:
        raise SystemExit(
            f"CHYBA: čekám právě jedno flow AktualizaceKratkehoNazvu, našel jsem {len(workflow)}")
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

    # Web a list v triggeru přepisujeme taky, jinak by flow po importu na cizí
    # tenant hlídalo list, který tam neexistuje. Který list kostra ze Studia
    # ukazovala, je od téhle chvíle jedno — vybírá se v průvodci importem.
    puvodni = dict(trigger["inputs"]["parameters"])
    trigger["inputs"]["parameters"]["dataset"] = ep.web()
    trigger["inputs"]["parameters"]["table"] = argumenty.list_aktivity

    definice["actions"] = akce(argumenty.list_aktivity)
    definice["contentVersion"] = "1.0.0.0"
    polozky[klic] = json.dumps(flow, ensure_ascii=False, indent=1).encode("utf-8")

    with zipfile.ZipFile(cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)

    print(f"flow doplněno: {klic.split('/')[-1]}")
    print(f"  akcí: {len(definice['actions'])}")
    print(f"  web z proměnné: {ep.web()}")
    print(f"  list Aktivity natvrdo (PatchItem runtime výraz nesnese): "
          f"{argumenty.list_aktivity}")
    print(f"  kostra ukazovala na: {puvodni.get('dataset')} / {puvodni.get('table')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
