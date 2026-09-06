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

# Web i list bere flow z proměnných prostředí — trigger, čtení i zápis.
# Do 1.0.0.97 tu byl GUID listu Aktivity natvrdo, protože zápis dělal
# `PatchItem` a ten si schéma rozloženého těla `item/<sloupec>` odvozuje
# z konkrétního listu; s runtime výrazem se flow naimportovalo, ale nešlo
# zapnout ("missing required property 'item'", MPSV 28.08.2026). Kvůli tomu
# se pro každý tenant stavěl vlastní balík a třikrát do MPSV odešel balík
# s GUIDem PPF DEV (naposledy 1.0.0.96).
#
# Od F14 se zapisuje přes `Send an HTTP request to SharePoint` (MERGE) —
# v URL je list obyčejný text, takže proměnnou snese. Týž tvar používají
# ImportFlow, PresunFlow, RestoreFlow a ZalohaFlow; na MPSV běží.
MAXLEN = 150
AKTUALNI = "body('Nacti_aktivitu')"

# Interní název listu. Je stejný na všech tenantech, kdežto GUID ani
# zobrazovaný název ne — proto se REST adresa skládá přes GetList z něj.
LIST_AKTIVITY = "Aktivity"

# `nometadata` znamená, že se do těla nemusí skládat `__metadata.type`.
HLAVICKY_ZAPIS = {
    "Accept": "application/json;odata=nometadata",
    "Content-Type": "application/json;odata=nometadata",
    "X-HTTP-Method": "MERGE",
    "IF-MATCH": "*",
}

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


def rest_adresa(vnitrek):
    """REST adresa listu Aktivity — server-relativní cesta webu z proměnné
    plus interní název listu. Týž tvar má RestoreFlow i PresunFlow."""
    return (f"@concat('_api/web/GetList(''', outputs('Cesta_webu'),"
            f" '/Lists/{LIST_AKTIVITY}', ''')/items{vnitrek}')")


def akce():
    b = "outputs('Bez_bilych_znaku')"
    rez = "outputs('Rez')"
    mezera = f"lastIndexOf({rez}, ' ')"
    list_aktivity = ep.list_param("Aktivity")

    kroky = {
        # Čerstvý stav řádku. Trigger dává snímek starý až o minutu (polling
        # po 1 min), takže z něj smí přijít jen ID — jinak flow porovná stav,
        # jaký byl PŘED editací, a zápis by se buď neprovedl, nebo přepsal
        # novější hodnotu.
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
        # Server-relativní cesta webu, ze které se skládá REST adresa zápisu.
        "Cesta_webu": compose(
            f"@concat('/', join(skip(split({ep.vyraz(ep.WEB)}, '/'), 3), '/'))",
            "Nacti_aktivitu"),
        "Nazev_syrovy": compose(
            f"@coalesce({AKTUALNI}?['nazev'], '')", "Cesta_webu"),
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
            # MERGE mění jen uvedený sloupec, takže povinná pole listu se
            # na rozdíl od PatchItem posílat nemusí — a tím padá i riziko,
            # že by zápis vrátil novější editaci na starou hodnotu.
            "Zapsat_kratky_nazev": {
                "type": "OpenApiConnection",
                "inputs": {
                    "parameters": {
                        "dataset": ep.web(),
                        "parameters/method": "POST",
                        "parameters/uri": rest_adresa(
                            "(', string(triggerBody()?['ID']), ')"),
                        "parameters/headers": HLAVICKY_ZAPIS,
                        "parameters/body": {"nazev_kratky": "@outputs('Cil')"},
                    },
                    "host": {
                        "apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                        "operationId": "HttpRequest",
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
    # Trigger je čtecí, rozložené tělo nemá, takže proměnnou snese.
    puvodni = dict(trigger["inputs"]["parameters"])
    trigger["inputs"]["parameters"]["dataset"] = ep.web()
    trigger["inputs"]["parameters"]["table"] = ep.list_param("Aktivity")

    definice["actions"] = akce()
    definice["contentVersion"] = "1.0.0.0"
    polozky[klic] = json.dumps(flow, ensure_ascii=False, indent=1).encode("utf-8")

    with zipfile.ZipFile(cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)

    print(f"flow doplněno: {klic.split('/')[-1]}")
    print(f"  akcí: {len(definice['actions'])}")
    print(f"  web z proměnné: {ep.web()}")
    print(f"  list z proměnné: {ep.list_param('Aktivity')}")
    print(f"  zápis: REST MERGE na GetList(.../Lists/{LIST_AKTIVITY})")
    print(f"  kostra ukazovala na: {puvodni.get('dataset')} / {puvodni.get('table')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
