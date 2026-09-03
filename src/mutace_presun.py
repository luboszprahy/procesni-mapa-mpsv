# -*- coding: utf-8 -*-
"""Mutační test brány `check_presun_flow.py`.

Zavede do hotového balíku po jedné chybě a ověří, že ji brána shodí. Zelená
brána sama o sobě nedokazuje nic — dokazuje to až seznam chyb, které chytí.

Mutace jsou vybrané podle toho, co by se v kaskádě pokazilo nejtišeji:
většina z nich by nespadla za běhu, jen by přesunula něco jiného, než měla.

    python src/mutace_presun.py --vystup deploy/procesnimapa_1_0_0_93.zip
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

FLOW = "PresunFlow"


def uprav_flow(zip_cesta, zmena):
    with zipfile.ZipFile(zip_cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klic = next(n for n in polozky
                if n.replace("\\", "/").startswith(f"Workflows/{FLOW}"))
    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    puvodni = json.dumps(flow, ensure_ascii=False, sort_keys=True)
    zmena(flow["properties"]["definition"]["actions"])
    if json.dumps(flow, ensure_ascii=False, sort_keys=True) == puvodni:
        raise SystemExit("CHYBA: mutace nic nezměnila — test by nic nedokazoval")
    polozky[klic] = json.dumps(flow, ensure_ascii=False).encode("utf-8")

    with zipfile.ZipFile(zip_cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)


def bez_historie(akce):
    """Maximum se hledá jen v živém listu. Uzavřený 03-05 by se recykloval —
    přesně to, co varianta C zakazuje."""
    akce["Nove_cislo"]["inputs"] = (
        "@add(max(union(body('Cisla_ziva'), createArray(0))), 1)")


def historie_bez_urovne(akce):
    """Filtr historie přestane rozlišovat úroveň. Uzavřený dílčí proces
    03-05-002 se pak započítá mezi procesy."""
    akce["Uzavrene"]["inputs"]["where"] = (
        "@startsWith(coalesce(item()?['Title'], ''),"
        " concat(outputs('Vstup')?['cil'], '-'))")


def deti_bez_filtru(akce):
    """`Deti` přestanou filtrovat. Kaskáda by přečíslovala VŠECHNY dílčí
    procesy v rejstříku, ne jen ty pod přesouvaným procesem.

    Pozn.: první pokus o tuhle mutaci měnil rovnost na `startsWith`, jenže
    nad reálnými kódy dávají obě totéž (žádný `proces_kod` není vlastním
    prefixem jiného), takže mutace neškodila a brána ji po právu pustila.
    """
    akce["Deti"]["inputs"]["where"] = "@true"


def vnuci_jen_rovnost(akce):
    """`Vnuci` chytí jen aktivity, jejichž dílčí proces se kódu ROVNÁ.
    U přesunu procesu tím zmizí všechny aktivity a kaskáda přesune prázdno."""
    akce["Vnuci"]["inputs"]["where"] = (
        "@equals(coalesce(item()?['dilci_proces_kod'], ''),"
        " outputs('Vstup')?['kod'])")


def novy_kod_bez_zbytku(akce):
    """Nový kód se skládá bez zbytku po prefixu — všichni potomci by dostali
    týž kód jako přesouvaná položka."""
    akce["Mapa"]["inputs"]["select"]["novy"] = "@outputs('Novy_prefix')"


def vazby_jen_aktivita(akce):
    """Dotčené vazby se hledají jen podle aktivity. Cizí aktivita zařazená
    dovnitř přesouvané větve by zůstala viset na neexistujícím dílčím procesu."""
    akce["Vazby_dotcene"]["inputs"]["where"] = (
        "@startsWith(coalesce(item()?['aktivita_kod'], ''),"
        " concat(outputs('Vstup')?['kod'], '-'))")


def vazby_prilis_siroce(akce):
    """Opačná chyba: dotčené je všechno. Přesun by přepsal i vazby, kterých
    se netýká."""
    akce["Vazby_dotcene"]["inputs"]["where"] = "@true"


def zanik_pred_vznikem(akce):
    """Mazání se pustí dřív než zakládání. Výpadek uprostřed by smazal větev,
    která ještě nikde jinde neexistuje."""
    akce["Smaz_vazby"]["runAfter"] = {"Je_nahled": ["Succeeded"]}
    akce["Zaloz_proces"]["runAfter"] = {"Smaz_vlastni": ["Succeeded"]}


def nahled_bez_terminate(akce):
    """Náhled po odpovědi pokračuje dál — a přesune to, co měl jen ukázat."""
    del akce["Je_nahled"]["actions"]["Konec_nahledu"]


def mazani_podle_kodu(akce):
    """Maže se podle kódu, ne podle ID. Pod tím kódem už ale sedí nový záznam
    z tohoto samého běhu, takže by se smazal on."""
    akce["Smaz_aktivity"]["actions"]["Smaz_aktivitu"]["inputs"]["parameters"][
        "parameters/uri"] = (
        "@concat('_api/web/GetList(''', outputs('Cesta_webu'),"
        " '/Lists/Aktivity', ''')/items?$filter=Title eq ''',"
        " items('Smaz_aktivity')?['Title'], ''''')")


def bez_pagination(akce):
    """Bez stránkování vrátí konektor jen prvních 100 položek a kaskáda tiše
    mine většinu podstromu."""
    del akce["Nacti_Aktivity"]["runtimeConfiguration"]


def zapis_pres_konektor(akce):
    """Zápis přes konektorovou akci místo REST — flow by pak nešlo zapnout,
    protože PatchItem vyžaduje `table` jako GUID natvrdo."""
    akce["Zaloz_dilci"]["actions"]["Vloz_dilci"]["inputs"]["host"][
        "operationId"] = "PatchItem"


def odpoved_navic(akce):
    """Pátý údaj v odpovědi. Appka má dynamicschema false a rozebírá odpověď
    podle pořadí polí — změna schématu si vyžádá novou registraci ve Studiu."""
    akce["Odpoved"]["inputs"]["body"]["pocet"] = "@length(body('Mapa'))"


MUTACE = [
    ("maximum se hledá bez historie", bez_historie),
    ("filtr historie nerozlišuje úroveň", historie_bez_urovne),
    ("děti se nefiltrují vůbec", deti_bez_filtru),
    ("vnuci se hledají jen rovností", vnuci_jen_rovnost),
    ("nový kód se skládá bez zbytku po prefixu", novy_kod_bez_zbytku),
    ("dotčené vazby jen podle aktivity", vazby_jen_aktivita),
    ("dotčené vazby jsou všechny", vazby_prilis_siroce),
    ("zánik běží před vznikem", zanik_pred_vznikem),
    ("náhled nekončí Terminate", nahled_bez_terminate),
    ("maže se podle kódu, ne podle ID", mazani_podle_kodu),
    ("načítání bez pagination", bez_pagination),
    ("zápis přes konektor místo REST", zapis_pres_konektor),
    ("odpověď má pole navíc", odpoved_navic),
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
                [sys.executable, "src/check_presun_flow.py", "--solution", str(kopie)],
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
