# -*- coding: utf-8 -*-
"""Mutační test brány check_import_flow.py.

Import zapisuje do dat podle souboru, který někdo vyplnil ručně. Jeho vady
jsou tiché: přeskočený prázdný řádek, který přeskočený nebyl, dvě aktivity
s týmž kódem, duplicita založená znovu, zápis proběhlý v režimu náhledu.
Tenhle skript zavede do hotového balíku po jedné takové chybě a ověří, že ji
brána shodí.

Spouštět z kořene projektu:
    python src/mutace_import.py --vystup deploy/procesnimapa_1_0_0_85.zip
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
from build_import_flow import FLOW  # noqa: E402


def smycka(definice):
    return definice["actions"]["Zapis"]["actions"]["Zaloz"]


# ---------- co se zapisuje ----------

def soubezna_smycka(definice):
    """Souběžné průchody přidělí dvěma aktivitám pod týmž dílčím procesem
    stejný kód — proměnná se čte dřív, než ji předchozí průchod doplní."""
    smycka(definice)["runtimeConfiguration"]["concurrency"]["repetitions"] = 20


def zaklada_vsechno(definice):
    """Smyčka jede přes všechny řádky, ne jen přes ověřené: založí i duplicity
    a řádky s neexistujícím dílčím procesem."""
    smycka(definice)["foreach"] = "@body('Ocistene')"


def kod_bez_pojistky(definice):
    """max() nad prázdným polem spadne — první aktivita pod dílčím procesem
    bez sourozenců by import shodila."""
    uzel = smycka(definice)["actions"]["Novy_kod"]
    uzel["inputs"] = uzel["inputs"].replace(
        "if(empty(body('Cisla')), 0, max(body('Cisla')))", "max(body('Cisla'))")


def kod_bez_doplneni_nul(definice):
    """Bez doplnění na čtyři místa vznikne 01-02-003-1 místo 01-02-003-0001."""
    uzel = smycka(definice)["actions"]["Novy_kod"]
    uzel["inputs"] = ("@concat(items('Zaloz')?['dilci_proces_kod'], '-',"
                      " string(add(if(empty(body('Cisla')), 0, max(body('Cisla'))), 1)))")


def zapamatuj_predcasne(definice):
    """Kód se zapamatuje dřív, než je řádek zapsaný; při chybě zápisu se
    přeskočí číslo a v rejstříku vznikne díra."""
    smycka(definice)["actions"]["Zapamatuj_kod"]["runAfter"] = {}


def sourozenci_z_listu(definice):
    """Sourozenci se hledají v listu, ne v proměnné — kód přidělený o řádek
    dřív se nezapočítá a druhá aktivita dostane týž."""
    uzel = smycka(definice)["actions"]["Sourozenci"]
    uzel["inputs"]["from"] = "@body('Kody_aktivit')"


def pise_kratky_nazev(definice):
    """Import a AktualizaceKratkehoNazvu by si sloupec přepisovaly navzájem."""
    telo = (smycka(definice)["actions"]["Vloz_aktivitu"]["inputs"]["parameters"]
            ["parameters/body"])
    telo["nazev_kratky"] = "@items('Zaloz')?['nazev']"


def vazba_jinou_spojkou(definice):
    """Jiný tvar klíče vazby než ten, který zakládá appka — vzniknou vazby,
    které appka nenajde, a založí je podruhé."""
    telo = (smycka(definice)["actions"]["Vloz_vazbu"]["inputs"]["parameters"]
            ["parameters/body"])
    telo["Title"] = "@concat(outputs('Novy_kod'), '-', items('Zaloz')?['dilci_proces_kod'])"


def bez_data_aktualizace(definice):
    """Bez razítka nejde poznat, co přišlo importem a kdy."""
    telo = (smycka(definice)["actions"]["Vloz_aktivitu"]["inputs"]["parameters"]
            ["parameters/body"])
    del telo["datum_aktualizace"]


# ---------- kdy se zapisuje ----------

def zapis_mimo_podminku(definice):
    """Zápis vytažený z podmínky proběhne i v náhledu."""
    vytazena = definice["actions"]["Zapis"]["actions"].pop("Zaloz")
    vytazena["runAfter"] = {}
    definice["actions"]["Zaloz"] = vytazena


# ---------- co se čte ----------

def prazdnost_bez_sloupce(definice):
    """Řádek vyplněný jen v jednom sloupci by se považoval za prázdný
    a zmizel by z rozkladu úplně."""
    uzel = definice["actions"]["Prazdne"]
    uzel["inputs"]["where"] = uzel["inputs"]["where"].replace(
        ", empty(item()?['sekce'])", "")


def sloupec_podle_jineho_nadpisu(definice):
    """Klíč se rozejde s hlavičkou šablony — sloupec se tiše načte prázdný."""
    vyber = definice["actions"]["Ocistene"]["inputs"]["select"]
    vyber["vykonava"] = vyber["vykonava"].replace("Vykonává útvar", "Vykonava utvar")


def bez_orezani(definice):
    """Bez trim() udělá mezera navíc z duplicity nový záznam."""
    vyber = definice["actions"]["Ocistene"]["inputs"]["select"]
    vyber["nazev"] = vyber["nazev"].replace("@trim(", "@(")


def cislo_radku_od_jednicky(definice):
    """Čísla řádků v hlášení by ukazovala o jeden výš, než kde chyba je."""
    vyber = definice["actions"]["Ocistene"]["inputs"]["select"]
    vyber["radek"] = "@add(item(), 1)"


def bez_strankovani(definice):
    """Nad 100 aktivitami by import neviděl existující a zakládal duplicity."""
    definice["actions"]["Nacti_Aktivity"].pop("runtimeConfiguration", None)


def duplicity_se_zakladaji(definice):
    """K_zalozeni přestane být doplňkem duplicit."""
    uzel = definice["actions"]["K_zalozeni"]
    uzel["inputs"]["where"] = uzel["inputs"]["where"].replace("@not(", "@(")


def rozklad_z_jineho_zdroje(definice):
    """Duplicity se hledají mezi všemi řádky včetně chybných — skupiny se
    překryjí a čísla v náhledu přestanou sedět."""
    definice["actions"]["Duplicitni"]["inputs"]["from"] = "@body('Ocistene')"


# ---------- přenositelnost ----------

def drive_natvrdo(definice):
    """Graph drive id vázané na jednu knihovnu jednoho tenantu."""
    definice["actions"]["Radky"]["inputs"]["parameters"]["drive"] = (
        "b!gFPziHO__EC50jP6WCcDM5yOFPI4DDRCuUWfWYTq2Rw2lJuZkVGpT5pY475NIjmO")


def source_natvrdo(definice):
    definice["actions"]["Radky"]["inputs"]["parameters"]["source"] = (
        "sites/ppfbanka.sharepoint.com,88f35380-bf73-40fc-b9d2-33fa58270333,"
        "f2148e9c-0c38-4234-b945-9f5984ead91c")


def tabulka_jinak(definice):
    """Jméno tabulky se rozejde se šablonou — konektor ji nenajde."""
    definice["actions"]["Radky"]["inputs"]["parameters"]["table"] = "Activity"


def disk_podle_nazvu(definice):
    """Hledání disku podle zobrazovaného názvu místo URL segmentu."""
    uzel = definice["actions"]["Disk_kandidati"]
    uzel["inputs"]["where"] = "@equals(string(item()?['name']), 'Import')"


def rodic_pred_prazdnymi(definice):
    """Dosazení rodiče nad `Ocistene` místo nad `S_obsahem`.

    Nejdražší chyba celého kroku: prázdné řádky by přestaly být prázdné
    (`00-00-000` je hodnota) a šablona s dvěma sty prázdnými řádky by při
    každém importu založila dvě stě sirotků.
    """
    uzel = definice["actions"]["Doplneny_rodic"]
    uzel["inputs"]["from"] = "@body('Ocistene')"
    uzel["runAfter"] = {"Ocistene": ["Succeeded"]}


def rodic_se_nedosazuje(definice):
    """Prázdný dílčí proces projde beze změny — aktivita bez zařazení pak
    spadne mezi chybné řádky a nahrát holé činnosti nejde."""
    uzel = definice["actions"]["Doplneny_rodic"]
    uzel["inputs"]["select"]["dilci_proces_kod"] = "@item()?['dilci_proces_kod']"


def rodic_zahodi_sloupec(definice):
    """Select vynechá jeden sloupec — do zápisu se pak nedostane."""
    uzel = definice["actions"]["Doplneny_rodic"]
    uzel["inputs"]["select"].pop("vykonava", None)


def nezarazene_podle_jineho_kodu(definice):
    """Počet nezařazených se počítá podle cizího kódu, takže by ukazoval nulu
    i tehdy, když sirotci vznikli."""
    uzel = definice["actions"]["Nezarazene"]
    uzel["inputs"]["where"] = ("@equals(item()?['dilci_proces_kod'], '01-01-001')")


def _zapisova_smycka(definice, klic):
    """Smyčka zápisu vlastníků leží uvnitř větve `Zapis`."""
    return definice["actions"]["Zapis"]["actions"][f"Zapis_vlastniku_{klic}"]


def vlastnik_bez_merge(definice):
    """Zápis vlastníka bez MERGE. POST na /items(ID) by k agendě nezměnil
    vlastníka, ale pokusil se založit další řádek."""
    uloz = _zapisova_smycka(definice, "agendy")["actions"][
        "Pokud_existuje_agendy"]["actions"]["Uloz_vlastnika_agendy"]
    uloz["inputs"]["parameters"]["parameters/headers"].pop("X-HTTP-Method", None)


def vlastnik_zapisuje_rozporne(definice):
    """Zápis jde přes všechny unikátní dvojice, ne jen přes ty bez rozporu —
    vlastník by pak závisel na pořadí řádků v sešitu."""
    _zapisova_smycka(definice, "procesu")["foreach"] = "@outputs('Unikatni_procesu')"


def rozpor_se_nehlasi(definice):
    """Rozpory se odfiltrují, ale nedostanou se mezi chyby. Import doběhne
    zeleně a správce se nedozví, že se vlastník nezapsal."""
    definice["actions"]["Chybne_radky"]["inputs"] = (
        "@join(union(body('Popis_chybne'), body('Popis_neznamy')), '|#|')")


def vlastnik_i_nezarazenym(definice):
    """Filtr přestane vylučovat nezařazené aktivity, takže se vlastník zapíše
    technické agendě 00."""
    uzel = definice["actions"]["S_vlastnikem_agendy"]
    uzel["inputs"]["where"] = "@not(empty(item()?['_vlastnik_agendy']))"


def klic_ze_spatne_delky(definice):
    """Kód agendy se odvodí z pěti znaků místo dvou — vlastník agendy by se
    zapisoval k procesu, který pod tím kódem neexistuje."""
    uzel = definice["actions"]["Klice_agendy"]
    uzel["inputs"]["select"] = uzel["inputs"]["select"].replace(", 0, 2)", ", 0, 5)")


def vlastnik_bez_union(definice):
    """Duplicity se nezahazují, takže shodně vyplněná agenda na deseti řádcích
    vypadá jako deset různých vlastníků a hlásí se rozpor."""
    definice["actions"]["Unikatni_dilcich"]["inputs"] = "@body('Klice_dilcich')"


def vlastnik_meni_i_nazev(definice):
    """Tělo MERGE nese víc než sloupec vlastnik — přepsalo by název agendy."""
    uloz = _zapisova_smycka(definice, "dilcich")["actions"][
        "Pokud_existuje_dilcich"]["actions"]["Uloz_vlastnika_dilcich"]
    uloz["inputs"]["parameters"]["parameters/body"]["nazev"] = "@items('Zapis_vlastniku_dilcich')"


MUTACE = [
    ("vlastník se zapisuje bez MERGE", vlastnik_bez_merge),
    ("zapisují se i rozporné dvojice", vlastnik_zapisuje_rozporne),
    ("rozpor se odfiltruje, ale nehlásí", rozpor_se_nehlasi),
    ("vlastník se zapisuje i nezařazeným", vlastnik_i_nezarazenym),
    ("kód rodiče se bere ze špatné délky", klic_ze_spatne_delky),
    ("duplicity se nezahazují přes union", vlastnik_bez_union),
    ("MERGE mění i název, nejen vlastníka", vlastnik_meni_i_nazev),
    ("souběžná smyčka přidělování kódů", soubezna_smycka),
    ("zakládají se všechny řádky, ne jen ověřené", zaklada_vsechno),
    ("max() bez pojistky na prázdné pole", kod_bez_pojistky),
    ("kód se nedoplňuje nulami na čtyři místa", kod_bez_doplneni_nul),
    ("kód se zapamatuje před zápisem", zapamatuj_predcasne),
    ("sourozenci se hledají v listu, ne v proměnné", sourozenci_z_listu),
    ("import zapisuje nazev_kratky", pise_kratky_nazev),
    ("klíč vazby jinou spojkou než appka", vazba_jinou_spojkou),
    ("chybí razítko data aktualizace", bez_data_aktualizace),
    ("zápis vytažený z podmínky režimu", zapis_mimo_podminku),
    ("prázdnost řádku se neptá na všechny sloupce", prazdnost_bez_sloupce),
    ("sloupec se čte podle jiné hlavičky", sloupec_podle_jineho_nadpisu),
    ("hodnoty se neořezávají", bez_orezani),
    ("číslo řádku je o jedna nižší", cislo_radku_od_jednicky),
    ("vypnuté stránkování u aktivit", bez_strankovani),
    ("duplicity se zakládají znovu", duplicity_se_zakladaji),
    ("rozklad se počítá z překrývajícího zdroje", rozklad_z_jineho_zdroje),
    ("drive natvrdo v definici", drive_natvrdo),
    ("source natvrdo v definici", source_natvrdo),
    ("jméno tabulky se rozešlo se šablonou", tabulka_jinak),
    ("disk se hledá podle zobrazovaného názvu", disk_podle_nazvu),
    ("rodič se dosazuje před oddělením prázdných", rodic_pred_prazdnymi),
    ("prázdný dílčí proces se nedoplňuje", rodic_se_nedosazuje),
    ("dosazení rodiče zahodí sloupec", rodic_zahodi_sloupec),
    ("nezařazené se počítají podle cizího kódu", nezarazene_podle_jineho_kodu),
]


def uprav(zip_cesta, zmena):
    with zipfile.ZipFile(zip_cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klic = next(n for n in polozky
                if n.replace("\\", "/").startswith(f"Workflows/{FLOW}"))
    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    pred = json.dumps(flow, ensure_ascii=False, sort_keys=True)
    zmena(flow["properties"]["definition"])
    if json.dumps(flow, ensure_ascii=False, sort_keys=True) == pred:
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
                [sys.executable, "src/check_import_flow.py", "--solution", str(kopie)],
                capture_output=True, text=True, encoding="utf-8", errors="replace")

        if beh.returncode == 0:
            print(f"NEODHALENO: {popis} — brána mutaci propustila")
        else:
            hlidane += 1
            prvni = next((r for r in beh.stdout.splitlines()
                          if r.startswith("CHYBA:")), beh.stderr.strip()[:150])
            print(f"chycena: {popis}")
            print(f"          -> {prvni[:150]}")

    print(f"\nchycených mutací: {hlidane}/{len(MUTACE)}")
    return 0 if hlidane == len(MUTACE) else 1


if __name__ == "__main__":
    sys.exit(main())
