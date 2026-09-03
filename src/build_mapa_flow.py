# -*- coding: utf-8 -*-
"""Doplní do exportovaného MapaPublishFlow akce publikace procesní mapy.

Uživatel dodá z designeru kostru (trigger PowerApps V2 + jedna Compose),
tenhle skript doplní čtení šablony, pět dotazů do listů, přemapování na datový
kontrakt, zapečení do HTML a uložení do Site Assets. Trigger ani GUID flow se
nemění — jinak by import nebyl upgrade.

Kontrakt dat drží deploy/flow_MapaPublish.md; kotvy v šabloně src/mapa_template.html.

Spouštět z kořene projektu:
    python src/build_mapa_flow.py --solution deploy/procesnimapa_1_0_0_20.zip
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402

FLOW_PREFIX = "Workflows/MapaPublishFlow"
SABLONA_CESTA = "/SiteAssets/mapa_template.html"
CILOVA_SLOZKA = "/SiteAssets"
CILOVY_SOUBOR = "procesni_mapa.html"

# Kolik položek se z listu načte. 5 000 je view threshold SharePointu — až se
# k němu rejstřík přiblíží, potřebuje jiné řešení, ne vyšší číslo.
STRANKOVANI = 5000

# Jméno správce se do mapy nepíše (auditní nález A-08): je to údaj o osobě
# v dokumentu pro celý úřad a natvrdo zapsané jméno by po první organizační
# změně lhalo. Sekce zůstává, dokud rejstřík pokrývá jen ji.
META = {"sekce": "3"}

# Zobrazovaný název listu v canvas appce -> název kroku ve flow a mapování
# sloupců na datový kontrakt. 'kod' je v SharePointu vždy ve sloupci Title.
# Technická větev „Nezařazeno" (00 / 00-00 / 00-00-000) a aktivity, které pod
# ní čekají na přiřazení, do publikované mapy nepatří — je to provizorium pro
# import holých aktivit, ne kus rejstříku. Filtruje se u zdroje, ne až v mapě:
# co se nenačte, nemůže se do stránky omylem dostat jinou cestou (F13/C3).
FILTR_NEZARAZENO = {
    "Agendy": "Title ne '00'",
    "Procesy": "Title ne '00-00'",
    "DilciProcesy": "Title ne '00-00-000'",
    "Aktivity": "dilci_proces_kod ne '00-00-000'",
    "Vazby": "dilci_proces_kod ne '00-00-000'",
}

LISTY = [
    ("Agendy", "Agendy", {
        "kod": "Title", "nazev": "nazev", "vlastnik": "vlastnik",
    }),
    ("Procesy", "Procesy", {
        "kod": "Title", "nazev": "nazev", "agenda_kod": "agenda_kod",
        "vlastnik": "vlastnik",
    }),
    ("Dílčí procesy", "DilciProcesy", {
        "kod": "Title", "nazev": "nazev", "proces_kod": "proces_kod",
        "vlastnik": "vlastnik",
    }),
    ("Aktivity", "Aktivity", {
        "kod": "Title", "nazev": "nazev", "dilci_proces_kod": "dilci_proces_kod",
        "vykonava": "vykonava", "spolupracuje": "spolupracuje",
        "vnitrni_predpis": "vnitrni_predpis", "sekce": "sekce",
    }),
    ("Vazba aktivita–dílčí proces", "Vazby", {
        "aktivita_kod": "aktivita_kod", "dilci_proces_kod": "dilci_proces_kod",
    }),
]

HOST_SP = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"


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


def nacti_metadata(customizations):
    """Vytáhne z canvas appky adresu webu a GUID listů.

    Číst je z balíku je bezpečnější než mít je natvrdo: kdyby uživatel appku
    přepojil na jiný web, natvrdo zapsané GUID by ukazovaly do prázdna a flow
    by publikovalo mapu ze špatných dat, aniž by cokoli spadlo.
    """
    shoda = re.search(r"<ConnectionReferences>(.*?)</ConnectionReferences>",
                      customizations, re.S)
    if not shoda:
        raise SystemExit("CHYBA: v customizations.xml není blok ConnectionReferences canvas appky")
    text = shoda.group(1).replace("&quot;", '"').replace("&amp;", "&")
    data = json.loads(text)
    # Ne první connection reference, ale ta SharePointová: pořadí klíčů není
    # dané a v exportu ze Studia stojí první logicflows (dataSets prázdné).
    spojeni = next((s for s in data.values()
                    if "shared_sharepointonline" in s.get("id", "")), None)
    if spojeni is None:
        raise SystemExit("CHYBA: v appce není SharePoint connection reference")
    datasety = spojeni["dataSets"]
    if len(datasety) != 1:
        raise SystemExit(f"CHYBA: čekám právě jeden web, appka jich má {len(datasety)}")
    web, obsah = next(iter(datasety.items()))
    # S napojením přes proměnné nese klíč suffix se schemaname (viz build_app.py);
    # čistá adresa webu je v datasetOverride.name.
    web = (obsah.get("datasetOverride") or {}).get("name") or web
    tabulky = {n: v["tableName"] for n, v in obsah["dataSources"].items()}
    return web, tabulky


def akce(web, tabulky):
    kroky = {}
    kroky["Sablona"] = sp_akce(
        "GetFileContentByPath",
        {"dataset": ep.web(), "path": SABLONA_CESTA, "inferContentType": True},
        None)

    predchozi = "Sablona"
    for zobrazovany, krok, _ in LISTY:
        # Do flow jde proměnná, ne GUID. Napojení appky se přesto ověřuje:
        # kdyby v ní list chyběl, byla by chyba i tak, jen o krok dál.
        if zobrazovany not in tabulky:
            raise SystemExit(
                f"CHYBA: appka nemá připojený list '{zobrazovany}'")
        jmeno = f"Nacti_{krok}"
        kroky[jmeno] = sp_akce(
            "GetItems",
            {"dataset": ep.web(), "table": ep.list_param(zobrazovany),
             "$filter": FILTR_NEZARAZENO[krok], "$top": STRANKOVANI},
            predchozi)
        # Bez pagination načte konektor jen prvních 100 položek a mapa vypadá,
        # že v rejstříku chybí data. Tichá chyba, nic nespadne.
        kroky[jmeno]["runtimeConfiguration"] = {
            "paginationPolicy": {"minimumItemCount": STRANKOVANI}
        }
        predchozi = jmeno

    for zobrazovany, krok, mapovani in LISTY:
        vyber = {}
        for klic, zdroj in mapovani.items():
            if isinstance(zdroj, tuple):
                # Choice sloupec vrací objekt; bez ?['Value'] by se do JSON
                # dostalo {"Value":"…"} a filtr stavu v mapě přestane fungovat.
                vyber[klic] = f"@item()?['{zdroj[0]}']?['Value']"
            else:
                vyber[klic] = f"@item()?['{zdroj}']"
        kroky[f"Map_{krok}"] = {
            "type": "Select",
            "inputs": {"from": f"@outputs('Nacti_{krok}')?['body/value']", "select": vyber},
            "runAfter": {predchozi: ["Succeeded"]},
        }
        predchozi = f"Map_{krok}"

    kroky["Model"] = {
        "type": "Compose",
        "inputs": {
            "meta": META,
            "agendy": "@body('Map_Agendy')",
            "procesy": "@body('Map_Procesy')",
            "dilci_procesy": "@body('Map_DilciProcesy')",
            "aktivity": "@body('Map_Aktivity')",
            "vazby": "@body('Map_Vazby')",
        },
        "runAfter": {predchozi: ["Succeeded"]},
    }

    # body('Sablona') je rovnou řetězec, ne objekt s $content: s
    # inferContentType=true konektor odvodí u .html textový typ a obsah
    # dekóduje sám. Původní base64ToString(body('Sablona')?['$content'])
    # shodilo běh 20.08.2026 hláškou „Property selection is not supported
    # on values of type 'String'". Bez string() naschvál — kdyby konektor
    # jednou vrátil objekt, replace() spadne hlasitě místo toho, aby do
    # stránky tiše zapsal JSON obalu.
    # Kolem __GEN__ musí být uvozovky, je to řetězcový literál v JavaScriptu.
    kroky["Stranka"] = {
        "type": "Compose",
        "inputs": (
            "@replace("
            "replace("
            "body('Sablona'),"
            " '__DATA_JSON__', string(outputs('Model'))"
            "),"
            " '__GEN__',"
            " concat('\"vygenerováno ', formatDateTime(utcNow(), 'dd.MM.yyyy HH:mm'), '\"')"
            ")"
        ),
        "runAfter": {"Model": ["Succeeded"]},
    }

    kroky["Uloz_mapu"] = sp_akce(
        "CreateFile",
        {"dataset": ep.web(), "folderPath": CILOVA_SLOZKA, "name": CILOVY_SOUBOR,
         "body": "@outputs('Stranka')"},
        "Stranka")
    return kroky


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True, help="solution zip s exportovaným flow")
    argumenty = parser.parse_args()

    cesta = Path(argumenty.solution)
    with zipfile.ZipFile(cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    workflow = [n for n in polozky if n.replace("\\", "/").startswith(FLOW_PREFIX)]
    if len(workflow) != 1:
        raise SystemExit(
            f"CHYBA: čekám právě jedno flow MapaPublishFlow, našel jsem {len(workflow)}")
    klic = workflow[0]

    web, tabulky = nacti_metadata(polozky["customizations.xml"].decode("utf-8-sig"))

    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    definice = flow["properties"]["definition"]

    triggery = definice.get("triggers", {})
    if len(triggery) != 1:
        raise SystemExit("CHYBA: flow musí mít právě jeden trigger")
    trigger = next(iter(triggery.values()))
    if trigger.get("kind") != "PowerAppV2":
        raise SystemExit(f"CHYBA: trigger je '{trigger.get('kind')}', čekal jsem PowerAppV2")

    # Kostra ze Studia žádnou connection reference nenese — SharePoint akce by
    # bez ní neměly čím běžet. Bereme tu, kterou už v tomto balíku používá
    # hotové flow, takže se neváže nic nového.
    druhe = [n for n in polozky
             if n.replace("\\", "/").startswith("Workflows/AktualizaceKratkehoNazvu")]
    if len(druhe) != 1:
        raise SystemExit("CHYBA: v balíku není flow AktualizaceKratkehoNazvu, odkud vzít spojení")
    vzor = json.loads(polozky[druhe[0]].decode("utf-8-sig"))
    flow["properties"]["connectionReferences"] = vzor["properties"]["connectionReferences"]

    definice["actions"] = akce(web, tabulky)
    # "undefined" z kostry je past: import projde, ale flow pak nejde otevřít
    # v designeru („Flow not found").
    definice["contentVersion"] = "1.0.0.0"
    polozky[klic] = json.dumps(flow, ensure_ascii=False, indent=1).encode("utf-8")

    with zipfile.ZipFile(cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)

    spojeni = next(iter(flow["properties"]["connectionReferences"].values()))
    print(f"flow doplněno: {klic.split('/')[-1]}")
    print(f"  akcí: {len(definice['actions'])}")
    print(f"  web z proměnné: {ep.web()}")
    print(f"  web napojený v appce (jen kontrola): {web}")
    print(f"  spojení: {spojeni['connection']['connectionReferenceLogicalName']}")
    print(f"  ukládá: {CILOVA_SLOZKA}/{CILOVY_SOUBOR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
