# -*- coding: utf-8 -*-
"""Mutační test brány `check_flow.py` (flow AktualizaceKratkehoNazvu).

Brána se u F14 přepsala z `PatchItem` na REST MERGE. Přepsaná brána běží
zeleně už proto, že se dívá jinam — dokazuje to teprve seznam chyb, které
chytí. Mutace míří na to, co by se v REST zápisu pokazilo nejtišeji: špatná
hlavička nebo adresa flow nezastaví, jen zapíše jinam nebo něco jiného.

    python src/mutace_kratky_nazev.py --vystup deploy/procesnimapa_1_0_0_98.zip
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

FLOW = "AktualizaceKratkehoNazvu"
GUID_PPF = "9dfbb5a1-1111-2222-3333-444455556666"


def uprav_flow(zip_cesta, zmena):
    with zipfile.ZipFile(zip_cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klic = next(n for n in polozky
                if n.replace("\\", "/").startswith(f"Workflows/{FLOW}"))
    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    puvodni = json.dumps(flow, ensure_ascii=False, sort_keys=True)
    zmena(flow["properties"]["definition"])
    if json.dumps(flow, ensure_ascii=False, sort_keys=True) == puvodni:
        raise SystemExit("CHYBA: mutace nic nezměnila — test by nic nedokazoval")
    polozky[klic] = json.dumps(flow, ensure_ascii=False).encode("utf-8")

    with zipfile.ZipFile(zip_cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)


def _zapis(definice):
    return definice["actions"]["Lisi_se"]["actions"]["Zapsat_kratky_nazev"]["inputs"]


def bez_merge(definice):
    """Bez `X-HTTP-Method: MERGE` je to prostý POST na /items(ID) — SharePoint
    ho nevezme jako změnu řádku a flow zapisuje do prázdna."""
    del _zapis(definice)["parameters"]["parameters/headers"]["X-HTTP-Method"]


def merge_jako_patch(definice):
    """PATCH místo MERGE. Vypadá stejně správně, ale SharePoint REST rozumí
    jen MERGE přes X-HTTP-Method."""
    _zapis(definice)["parameters"]["parameters/headers"]["X-HTTP-Method"] = "PATCH"


def bez_if_match(definice):
    """Bez `IF-MATCH` odmítne SharePoint zápis na 412 Precondition Failed."""
    del _zapis(definice)["parameters"]["parameters/headers"]["IF-MATCH"]


def guid_v_adrese(definice):
    """Návrat k listu natvrdo — přesně to, co F14 ruší. Na cizím tenantu
    ten GUID neexistuje a flow spadne na 404."""
    _zapis(definice)["parameters"]["parameters/uri"] = (
        f"@concat('_api/web/lists(guid''{GUID_PPF}'')/items(',"
        " string(triggerBody()?['ID']), ')')")


def guid_v_triggeru(definice):
    """GUID zpátky v triggeru. Zápis by fungoval, ale flow by hlídalo list
    na jiném tenantu a nikdy se nespustilo."""
    trigger = next(iter(definice["triggers"].values()))
    trigger["inputs"]["parameters"]["table"] = GUID_PPF


def adresa_bez_items(definice):
    """Adresa míří na list, ne na položku — MERGE by šel proti kolekci."""
    _zapis(definice)["parameters"]["parameters/uri"] = (
        "@concat('_api/web/GetList(''', outputs('Cesta_webu'),"
        " '/Lists/Aktivity', ''')')")


def cesta_webu_bez_skip(definice):
    """`Cesta_webu` se skládá z celé adresy včetně https://tenant — REST
    adresa pak není server-relativní a SharePoint list nenajde."""
    definice["actions"]["Cesta_webu"]["inputs"] = (
        "@concat('/', join(split(parameters('Procesni mapa - web "
        "(mpsv_procesnimapaSite)'), '/'), '/'))")


def zapis_pres_patchitem(definice):
    """Návrat k PatchItem. Ten runtime výraz v `table` nesnese, takže by se
    musel vrátit i GUID natvrdo — a s ním dvoubalíkový režim."""
    vstupy = _zapis(definice)
    vstupy["host"]["operationId"] = "PatchItem"
    vstupy["parameters"] = {
        "dataset": "@parameters('Procesni mapa - web (mpsv_procesnimapaSite)')",
        "table": GUID_PPF,
        "id": "@triggerBody()?['ID']",
        "item/nazev_kratky": "@outputs('Cil')",
    }


def telo_prohozene(definice):
    """Zapisuje se `nazev` místo `nazev_kratky` — flow by přepsalo plný
    název jeho vlastní zkratkou a data by se nevratně zkrátila."""
    telo = _zapis(definice)["parameters"]["parameters/body"]
    telo.pop("nazev_kratky")
    telo["nazev"] = "@outputs('Cil')"


def telo_s_povinnymi_poli(definice):
    """Povinná pole listu zpátky v těle. PatchItem je vyžadoval, MERGE ne —
    tady by jen vracely hodnoty čtené před výpočtem přes novější editaci."""
    telo = _zapis(definice)["parameters"]["parameters/body"]
    telo["Title"] = "@body('Nacti_aktivitu')?['Title']"
    telo["nazev"] = "@body('Nacti_aktivitu')?['nazev']"


def telo_z_triggeru(definice):
    """Hodnota ze snímku triggeru, starého až o minutu — flow by vrátilo
    novější editaci na starou hodnotu."""
    _zapis(definice)["parameters"]["parameters/body"]["nazev_kratky"] = (
        "@triggerBody()?['nazev']")


def metoda_get(definice):
    """Metoda GET místo POST — nic se nezapíše a běh je přitom zelený."""
    _zapis(definice)["parameters"]["parameters/method"] = "GET"


def cteni_z_triggeru(definice):
    """`Nacti_aktivitu` zmizí a porovnává se snímek triggeru. Editace
    uložená krátce po sobě se pak zpracuje nad zastaralým stavem."""
    akce = definice["actions"]
    del akce["Nacti_aktivitu"]
    akce["Cesta_webu"]["runAfter"] = {}
    akce["Nazev_syrovy"]["inputs"] = "@coalesce(triggerBody()?['nazev'], '')"
    akce["Lisi_se"]["expression"]["and"][0]["not"]["equals"][0] = (
        "@coalesce(triggerBody()?['nazev_kratky'], '')")


def bez_podminky(definice):
    """Zápis bez porovnání s uloženou hodnotou — každý zápis spustí trigger
    znovu a flow cyklí."""
    akce = definice["actions"]
    akce["Zapsat_kratky_nazev"] = dict(
        akce["Lisi_se"]["actions"]["Zapsat_kratky_nazev"],
        runAfter={"Cil": ["Succeeded"]})
    del akce["Lisi_se"]


MUTACE = [
    ("chybí hlavička X-HTTP-Method: MERGE", bez_merge),
    ("MERGE nahrazený za PATCH", merge_jako_patch),
    ("chybí hlavička IF-MATCH", bez_if_match),
    ("GUID listu natvrdo v REST adrese", guid_v_adrese),
    ("GUID listu natvrdo v triggeru", guid_v_triggeru),
    ("adresa míří na list, ne na položku", adresa_bez_items),
    ("Cesta_webu není server-relativní", cesta_webu_bez_skip),
    ("zápis zpátky přes PatchItem", zapis_pres_patchitem),
    ("zapisuje se nazev místo nazev_kratky", telo_prohozene),
    ("v těle jsou i povinná pole listu", telo_s_povinnymi_poli),
    ("hodnota se bere ze snímku triggeru", telo_z_triggeru),
    ("metoda GET místo POST", metoda_get),
    ("čte se z triggeru, ne z Nacti_aktivitu", cteni_z_triggeru),
    ("zapisuje se bez porovnání s uloženou hodnotou", bez_podminky),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vystup", required=True)
    argumenty = parser.parse_args()

    zdroj = Path(argumenty.vystup)
    if not zdroj.exists():
        raise SystemExit(f"CHYBA: balík {zdroj} neexistuje")

    hlidane = 0
    for popis, zmena in MUTACE:
        with tempfile.TemporaryDirectory() as docasny:
            kopie = Path(docasny) / zdroj.name
            shutil.copy(zdroj, kopie)
            uprav_flow(kopie, zmena)
            beh = subprocess.run(
                [sys.executable, "src/check_flow.py", "--solution", str(kopie)],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
        chycena = beh.returncode != 0
        hlidane += chycena
        print(f"{'chycena ' if chycena else 'PROŠLA  '} {popis}")
        if not chycena:
            print("    ^ brána tuhle chybu nechytá")

    print(f"\nchycených mutací: {hlidane}/{len(MUTACE)}")
    return 0 if hlidane == len(MUTACE) else 1


if __name__ == "__main__":
    sys.exit(main())
