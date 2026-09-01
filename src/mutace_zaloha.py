"""Mutační test brány check_zaloha_flow.py.

Vada zálohy se pozná až při obnově, takže zelená brána sama nedokazuje nic.
Tenhle skript zavede do hotového balíku po jedné chybě a ověří, že ji brána
shodí. Mutace jsou ty, které by v provozu prošly bez jediného červeného běhu:
oříznutý snímek, vynechaný list, Choice bez ?['Value'], rozešlá dvojčata.

Spouštět z kořene projektu:
    python src/mutace_zaloha.py --vystup deploy/procesnimapa_1_0_0_76.zip
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RUCNI = "ZalohaFlow"
PLANOVANE = "ZalohaScheduled"


def uprav(zip_cesta, prefix, zmena):
    """Přepíše definici daného flow funkcí `zmena`; nezměněná definice = chyba.

    Mutace, která se do definice netrefí, by se jinak tvářila jako platný test —
    brána by prošla a vypadalo by to, že mutaci nechytá nikdo.
    """
    with zipfile.ZipFile(zip_cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klic = next(n for n in polozky
                if n.replace("\\", "/").startswith(f"Workflows/{prefix}"))
    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    pred = json.dumps(flow, ensure_ascii=False, sort_keys=True)
    zmena(flow["properties"]["definition"])
    po = json.dumps(flow, ensure_ascii=False, sort_keys=True)
    if pred == po:
        raise SystemExit(f"CHYBA: mutace se do definice {prefix} netrefila")
    polozky[klic] = json.dumps(flow, ensure_ascii=False, indent=1).encode("utf-8")

    with zipfile.ZipFile(zip_cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, obsah in polozky.items():
            balik.writestr(jmeno, obsah)


def obe(zmena):
    """Mutace, která má postihnout obě flow — jinak by ji chytila jen kontrola
    dvojčat a nebylo by vidět, že ji chytá i kontrola věcná."""
    return [(RUCNI, zmena), (PLANOVANE, zmena)]


def bez_strankovani(definice):
    """Nejhorší možná vada zálohy: nad 100 řádky se snímek TIŠE ořízne
    a běh přitom skončí zeleně."""
    definice["actions"]["Nacti_DilciProcesy"].pop("runtimeConfiguration", None)


def vynechany_list(definice):
    """Jeden list ze snímku vypadne — soubor vznikne a vypadá v pořádku."""
    akce = definice["actions"]
    nasledujici = next(j for j, k in akce.items() if "Nacti_Utvary" in k.get("runAfter", {}))
    akce[nasledujici]["runAfter"] = akce["Nacti_Utvary"]["runAfter"]
    del akce["Nacti_Utvary"]
    del akce["Map_Utvary"]
    del definice["actions"]["Snimek"]["inputs"]["listy"]["Utvary"]


def vynechany_sloupec(definice):
    """Sloupec, který se do snímku neuloží, se z něj nedá obnovit."""
    del definice["actions"]["Map_Aktivity"]["inputs"]["select"]["text_pro_or"]


def choice_bez_value(definice):
    """Bez ?['Value'] se uloží {"Value":"…"} a restore zapíše nesmysl."""
    definice["actions"]["Map_Aktivity"]["inputs"]["select"]["stav"] = "@item()?['stav']"


def dve_razitka(definice):
    """Jméno souboru z vlastního utcNow() — obsah pak tvrdí jiný čas než název."""
    definice["actions"]["Uloz_zalohu"]["inputs"]["parameters"]["name"] = (
        "@concat('rejstrik_', formatDateTime(utcNow(), 'yyyy-MM-dd_HHmm'), '.json')")


def jina_slozka(definice):
    """Zápis mimo knihovnu Zalohy — snímky by se mísily s publikovanou mapou."""
    definice["actions"]["Uloz_zalohu"]["inputs"]["parameters"]["folderPath"] = "/SiteAssets"


def bez_verze_schematu(definice):
    """Bez verze schématu nemá restore podle čeho poznat starý snímek."""
    del definice["actions"]["Snimek"]["inputs"]["schema_verze"]


def uklid_pred_zapisem(definice):
    """Úklid před uložením nového snímku smaže o jeden víc, než má, a při
    chybě zápisu zůstane po sobě úklid bez zálohy."""
    definice["actions"]["Kolik_nechat"]["runAfter"] = {"Snimek": ["Succeeded"]}


def uklid_bere_hlavu(definice):
    """take() místo skip() smaže právě ty nejnovější snímky."""
    definice["actions"]["Ke_smazani"]["inputs"] = (
        "@take(body('Nase_snimky'), outputs('Kolik_nechat'))")


def uklid_bez_kontroly_jmena(definice):
    """Bez filtru na jméno smaže úklid i cizí soubory a přejmenované snímky,
    které si někdo schválně nechal."""
    definice["actions"]["Ke_smazani"]["inputs"] = (
        "@skip(outputs('Snimky')?['body/value'], outputs('Kolik_nechat'))")


def uklid_bez_delky(definice):
    """Kontrola prefixu bez kontroly délky: `rejstrik_schvaleni_OR.json`
    projde jako běžný snímek a smaže se."""
    uzel = definice["actions"]["Nase_snimky"]
    kde = uzel["inputs"]["where"]
    uzel["inputs"]["where"] = "@" + kde[kde.index("startsWith("):kde.rindex(",")]


def uklid_maze_natrvalo(definice):
    """DELETE místo recycle(): omyl v úklidu je nevratný."""
    parametry = (definice["actions"]["Smaz_stare"]["actions"]["Recykluj"]
                 ["inputs"]["parameters"])
    parametry["parameters/method"] = "DELETE"
    parametry["parameters/uri"] = parametry["parameters/uri"].replace("/recycle()", "")


def uklid_od_nejstarsiho(definice):
    """Bez `desc` čte flow snímky od nejstaršího a skip zahodí ty nejnovější."""
    definice["actions"]["Snimky"]["inputs"]["parameters"]["$orderby"] = "Created"


def uklid_nechava_nula(definice):
    """Nula ponechaných záloh smaže i právě pořízený snímek."""
    definice["actions"]["Kolik_nechat"]["inputs"] = 0


MUTACE = (
    [("vypnuté stránkování u jednoho listu", *obe(bez_strankovani))]
    + [("ze snímku vypadl celý list", *obe(vynechany_list))]
    + [("ze snímku vypadl sloupec", *obe(vynechany_sloupec))]
    + [("Choice sloupec bez ?['Value']", *obe(choice_bez_value))]
    + [("jméno souboru z druhého utcNow()", *obe(dve_razitka))]
    + [("zápis mimo knihovnu Zalohy", *obe(jina_slozka))]
    + [("snímek bez verze schématu", *obe(bez_verze_schematu))]
    # úklid starých snímků — maže data, takže se hlídá přísněji než zbytek
    + [("úklid běží před uložením snímku", *obe(uklid_pred_zapisem))]
    + [("úklid bere hlavu místo ocasu", *obe(uklid_bere_hlavu))]
    + [("úklid nekontroluje jméno souboru", *obe(uklid_bez_kontroly_jmena))]
    + [("úklid nekontroluje délku jména", *obe(uklid_bez_delky))]
    + [("úklid maže natrvalo, ne do koše", *obe(uklid_maze_natrvalo))]
    + [("snímky se čtou od nejstaršího", *obe(uklid_od_nejstarsiho))]
    + [("úklid nenechá ani jednu zálohu", *obe(uklid_nechava_nula))]
    # poslední dvě: zásah jen do plánovaného flow, tedy rozešlá dvojčata
    + [("dvojčata se rozešla (stránkování)", (PLANOVANE, bez_strankovani))]
    + [("dvojčata se rozešla (vynechaný list)", (PLANOVANE, vynechany_list))]
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vystup", required=True)
    argumenty = parser.parse_args()

    hlidane = 0
    for popis, *zasahy in MUTACE:
        with tempfile.TemporaryDirectory() as docasny:
            kopie = Path(docasny) / "mutace.zip"
            shutil.copy(argumenty.vystup, kopie)
            for prefix, zmena in zasahy:
                uprav(kopie, prefix, zmena)
            beh = subprocess.run(
                [sys.executable, "src/check_zaloha_flow.py", "--solution", str(kopie)],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
        if beh.returncode == 0:
            print(f"NEODHALENO: {popis} — brána mutaci propustila")
        else:
            hlidane += 1
            # Vypisuje se PRVNÍ hláška, ne jen návratový kód: mutace chycená
            # nesouvisející kontrolou vypadá stejně zeleně jako správně
            # chycená, a přitom nedokazuje nic o kontrole, kvůli které vznikla.
            prvni = next((r for r in beh.stdout.splitlines() if r.startswith("CHYBA:")), "")
            print(f"chycena: {popis}")
            print(f"          -> {prvni[:150]}")

    print(f"\nchycených mutací: {hlidane}/{len(MUTACE)}")
    return 0 if hlidane == len(MUTACE) else 1


if __name__ == "__main__":
    sys.exit(main())
