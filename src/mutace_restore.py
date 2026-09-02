# -*- coding: utf-8 -*-
"""Mutační test brány check_restore_flow.py.

Obnova je jediná operace projektu, která přepisuje existující data. Zelená
brána nad ní sama nedokazuje nic — tenhle skript zavede do hotového balíku
po jedné chybě a ověří, že ji brána shodí. Vybrané jsou ty, které by
v provozu prošly bez jediného červeného běhu a poznaly by se až na datech:
zápis podle ID ze snímku, oříznuté čtení, rozešlé otisky, zápis v režimu
náhledu.

Spouštět z kořene projektu:
    python src/mutace_restore.py --vystup deploy/procesnimapa_1_0_0_84.zip
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
from build_restore_flow import FLOW  # noqa: E402


def zapis_akce(definice, jmeno):
    return definice["actions"]["Zapis"]["actions"][jmeno]


# ---------- mutace, které mění cíl zápisu ----------

def podle_id_ze_snimku(definice):
    """Nejdražší chyba, jaká v obnově může být: zápis podle ID ze snímku.

    To ID je stav k okamžiku zálohy. Když se záznam mezitím smazal a jiný
    vznikl, patří dnes někomu jinému — MERGE by tiše přepsal cizí řádek
    a běh by přitom skončil zeleně.
    """
    akce = zapis_akce(definice, "Uprav_Aktivity")["actions"]["Zmen_Aktivity"]
    parametry = akce["inputs"]["parameters"]
    parametry["parameters/uri"] = parametry["parameters/uri"].replace(
        "string(first(body('Najdi_Aktivity'))?['ID'])",
        "string(items('Uprav_Aktivity')?['ID'])")


def bez_dohledani(definice):
    """Dohledání podle kódu úplně vypadlo."""
    smycka = zapis_akce(definice, "Uprav_Aktivity")
    del smycka["actions"]["Najdi_Aktivity"]
    smycka["actions"]["Zmen_Aktivity"]["runAfter"] = {}


def dohledani_podle_nazvu(definice):
    """Dohledání se přestalo ptát na kód a hledá podle názvu — dva různé
    záznamy se stejným názvem pak dostanou zápis do toho prvního."""
    najdi = zapis_akce(definice, "Uprav_Aktivity")["actions"]["Najdi_Aktivity"]
    najdi["inputs"]["where"] = najdi["inputs"]["where"].replace("Title", "nazev")


# ---------- mutace, které mění, CO se porovnává ----------

def bez_strankovani(definice):
    """Nad 100 řádky se porovnává proti oříznutému stavu a obnova pak
    „vrací" i to, co se nezměnilo."""
    definice["actions"]["Nacti_DilciProcesy"].pop("runtimeConfiguration", None)


def otisk_bez_value(definice):
    """Choice se z listu čte jako objekt; bez ?['Value'] se otisky nikdy
    neshodnou a obnova ohlásí změnu u každého řádku."""
    akce = definice["actions"]["Otisky_Agendy"]
    akce["inputs"]["select"] = akce["inputs"]["select"].replace("?['Value']", "")


def otisk_snimku_s_value(definice):
    """Totéž z druhé strany: ve snímku je Choice už rozbalený."""
    akce = definice["actions"]["Ke_zmene_Agendy"]
    akce["inputs"]["where"] = akce["inputs"]["where"].replace(
        "coalesce(item()?['zdroj'], '')", "coalesce(item()?['zdroj']?['Value'], '')")


def otisk_bez_sloupce(definice):
    """Sloupec vypadl z porovnání — jeho změnu obnova neuvidí a nevrátí ji."""
    akce = definice["actions"]["Otisky_Agendy"]
    akce["inputs"]["select"] = akce["inputs"]["select"].replace(
        ", '|~|', string(coalesce(item()?['vlastnik'], ''))", "")


# ---------- mutace, které mění, KDY se zapisuje ----------

def zapis_mimo_podminku(definice):
    """Zápis vytažený z podmínky proběhne i v režimu náhledu."""
    smycka = definice["actions"]["Zapis"]["actions"].pop("Zaloz_Agendy")
    smycka["runAfter"] = {}
    definice["actions"]["Zaloz_Agendy"] = smycka


def podminka_na_neco_jineho(definice):
    """Podmínka se přestala ptát na režim."""
    definice["actions"]["Zapis"]["expression"] = {
        "equals": ["@outputs('Vstup')?['soubor'], ''", ""]}


def bez_ukonceni_pri_neshode(definice):
    """Snímek proti jiné verzi schématu by se obnovil napůl."""
    vetev = definice["actions"]["Kontrola_verze"]["else"]["actions"]
    del vetev["Konec"]


# ---------- mutace, které mění, CO se zapíše ----------

def merge_bez_hlavicky(definice):
    """Bez X-HTTP-Method je z úpravy druhý POST — místo opravy vznikne
    duplicitní řádek se stejným kódem."""
    parametry = (zapis_akce(definice, "Uprav_Aktivity")["actions"]["Zmen_Aktivity"]
                 ["inputs"]["parameters"])
    parametry["parameters/headers"].pop("X-HTTP-Method")


def datum_prazdnym_retezcem(definice):
    """Prázdné datum jako "" SharePoint odmítne a řádek se nezapíše."""
    telo = (zapis_akce(definice, "Uprav_Aktivity")["actions"]["Zmen_Aktivity"]
            ["inputs"]["parameters"]["parameters/body"])
    telo["datum_aktualizace"] = "@coalesce(items('Uprav_Aktivity')?['datum_aktualizace'], '')"


def sloupec_se_nezapisuje(definice):
    """Sloupec vypadl z těla — obnova ho nevrátí a nikdo si nevšimne."""
    telo = (zapis_akce(definice, "Zaloz_Aktivity")["actions"]["Vloz_Aktivity"]
            ["inputs"]["parameters"]["parameters/body"])
    del telo["text_pro_or"]


def mazani_ve_smycce(definice):
    """Obnova, která maže, je z opravy druhá destruktivní operace."""
    zapis_akce(definice, "Zaloz_Agendy")["actions"]["Smaz_Agendy"] = {
        "type": "OpenApiConnection",
        "inputs": {
            "parameters": {"dataset": "@parameters('Procesni mapa - web "
                                      "(mpsv_procesnimapaSite)')",
                           "table": "@parameters('Procesni mapa - Agendy "
                                    "(mpsv_listAgendy)')",
                           "id": 1},
            "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                     "operationId": "DeleteItem",
                     "connectionName": "shared_sharepointonline"},
        },
        "runAfter": {"Vloz_Agendy": ["Succeeded"]},
    }


def adresa_pres_guid(definice):
    """GUID listu v adrese je vázaný na jeden tenant — na MPSV by mířil nikam."""
    parametry = (zapis_akce(definice, "Zaloz_Agendy")["actions"]["Vloz_Agendy"]
                 ["inputs"]["parameters"])
    parametry["parameters/uri"] = (
        "@concat('_api/web/lists(guid''3f2b6d41-8c55-4a37-9d21-5b8e0c47a9f2'')/items')")


def seznam_bez_created(definice):
    """Bez Created v $select nemá appka u snímků co ukázat vedle jména."""
    akce = definice["actions"]["Rezim_seznam"]["actions"]["Soubory"]
    parametry = akce["inputs"]["parameters"]
    parametry["parameters/uri"] = parametry["parameters/uri"].replace(
        "FileLeafRef,Created", "FileLeafRef")


def seznam_bez_prevodu_pasma(definice):
    """Created je UTC. Bez převodu by noční záloha hlásila čas o dvě hodiny
    dřív, než v kolik opravdu vznikla — a vypadala by jako cizí soubor."""
    akce = definice["actions"]["Rezim_seznam"]["actions"]["Jmena"]
    vyber = akce["inputs"]["select"]
    akce["inputs"]["select"] = re.sub(
        r"convertFromUtc\(([^,]+), '[^']*'\)", r"", vyber)


MUTACE = [
    ("zápis podle ID ze snímku", podle_id_ze_snimku),
    ("dohledání podle kódu vypadlo", bez_dohledani),
    ("dohledává se podle názvu, ne kódu", dohledani_podle_nazvu),
    ("vypnuté stránkování u jednoho listu", bez_strankovani),
    ("otisk listu bez ?['Value'] u Choice", otisk_bez_value),
    ("otisk snímku s ?['Value'] u Choice", otisk_snimku_s_value),
    ("sloupec vypadl z otisku", otisk_bez_sloupce),
    ("zápis vytažený z podmínky", zapis_mimo_podminku),
    ("podmínka se neptá na režim", podminka_na_neco_jineho),
    ("neshoda verze schématu běh neukončí", bez_ukonceni_pri_neshode),
    ("MERGE bez X-HTTP-Method", merge_bez_hlavicky),
    ("prázdné datum jako prázdný řetězec", datum_prazdnym_retezcem),
    ("sloupec se nezapisuje", sloupec_se_nezapisuje),
    ("mazání ve smyčce", mazani_ve_smycce),
    ("adresa listu přes GUID", adresa_pres_guid),
    ("seznam snímků bez data pořízení", seznam_bez_created),
    ("datum snímku se nepřevádí z UTC", seznam_bez_prevodu_pasma),
]


def uprav(zip_cesta, zmena):
    with zipfile.ZipFile(zip_cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klic = next(n for n in polozky
                if n.replace("\\", "/").startswith(f"Workflows/{FLOW}"))
    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    pred = json.dumps(flow, ensure_ascii=False, sort_keys=True)
    zmena(flow["properties"]["definition"])
    po = json.dumps(flow, ensure_ascii=False, sort_keys=True)
    if pred == po:
        raise SystemExit(f"CHYBA: mutace {zmena.__name__} se do definice netrefila")
    polozky[klic] = json.dumps(flow, ensure_ascii=False, indent=1).encode("utf-8")

    with zipfile.ZipFile(zip_cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, obsah in polozky.items():
            balik.writestr(jmeno, obsah)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vystup", required=True)
    argumenty = parser.parse_args()

    hlidane = 0
    for popis, zmena in MUTACE:
        with tempfile.TemporaryDirectory() as docasny:
            kopie = Path(docasny) / "mutace.zip"
            shutil.copy(argumenty.vystup, kopie)
            uprav(kopie, zmena)
            beh = subprocess.run(
                [sys.executable, "src/check_restore_flow.py", "--solution", str(kopie)],
                capture_output=True, text=True, encoding="utf-8", errors="replace")

        if beh.returncode == 0:
            print(f"NEODHALENO: {popis} — brána mutaci propustila")
        else:
            hlidane += 1
            # Vypisuje se PRVNÍ hláška: mutace chycená nesouvisející kontrolou
            # vypadá stejně zeleně a přitom nedokazuje nic.
            prvni = next((r for r in beh.stdout.splitlines()
                          if r.startswith("CHYBA:")), beh.stderr.strip()[:150])
            print(f"chycena: {popis}")
            print(f"          -> {prvni[:150]}")

    print(f"\nchycených mutací: {hlidane}/{len(MUTACE)}")
    return 0 if hlidane == len(MUTACE) else 1


if __name__ == "__main__":
    sys.exit(main())
