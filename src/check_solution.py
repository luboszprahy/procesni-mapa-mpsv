"""Kontrola přebalené solution před importem do Power Platform.

Porovnává výstup z src/build_app.py proti vstupní solution: co se změnit mělo
(obrazovky, verze) i co se změnit nesmělo (publisher, připojení na listy).

Spouštět z kořene projektu:  python src/check_solution.py
Návratový kód 0 = v pořádku, 1 = nalezena chyba.
"""

import json
import re
import sys
import zipfile
from pathlib import Path

import argparse

_p = argparse.ArgumentParser()
_p.add_argument("--vstup", default="input/procesnimapa_1_0_0_2 (2).zip")
_p.add_argument("--vystup", default="deploy/procesnimapa_1_0_0_3.zip")
_a = _p.parse_args()
VSTUP = Path(_a.vstup)
VYSTUP = Path(_a.vystup)

OCEKAVANE_OBRAZOVKY = {"scr_Dashboard", "scr_Detail", "scr_Vazby", "scr_Ciselnik"}
UVODNI_OBRAZOVKA = "scr_Dashboard"
OCEKAVANE_LISTY = {"Agendy", "Procesy", "Dílčí procesy", "Aktivity", "Vazba aktivita–dílčí proces",
                   "Útvary"}

chyby = []
varovani = []
kontrol = 0

# Jediná povolená adresa v appce: odkaz na publikovanou mapu. Canvas app umí
# číst jen datasetové proměnné prostředí, textové ne — dokud nevznikne list
# Nastaveni (F3), nemá kam jinam. Hlásí se jako varování, aby se na přenos
# na MPSV nezapomnělo; kdekoli jinde je URL dál chyba.
VYJIMKA_URL = "varMapaUrl"


def adresa_webu(customizations):
    """Adresa webu, na který je připojená canvas app — proti ní se měří flow."""
    shoda = re.search(r"<ConnectionReferences>(.*?)</ConnectionReferences>",
                      customizations, re.S)
    if not shoda:
        return None
    data = json.loads(shoda.group(1).replace("&quot;", '"').replace("&amp;", "&"))
    for spojeni in data.values():
        datasety = spojeni.get("dataSets") or {}
        if datasety:
            return next(iter(datasety))
    return None


def adresy_ve_flow(vystupni, customizations):
    """Adresy v definicích flow musí mířit na týž web jako canvas app.

    Do 1.0.0.59 se prohledávaly jen `*.pa.yaml` canvas appky, takže brána
    i HANDOVER.md tvrdily, že jediné natvrdo zapsané místo je `varMapaUrl`.
    Ve skutečnosti je adresa webu ve **všech** flow (parametr `dataset`
    a složená návratová adresa) — nález B-01 z kola 4.

    Není to samo o sobě chyba: build skripty adresu berou z připojení appky,
    ne z ruky. Chyba je, když některé flow míří jinam než appka — to se jinak
    pozná až za běhu, na cizím webu nebo prázdnou odpovědí.
    """
    web = adresa_webu(customizations)
    overit(web is not None, "v balíku není adresa webu canvas appky")
    if web is None:
        return

    celkem = 0
    for jmeno in vystupni.namelist():
        cesta = jmeno.replace("\\", "/")
        if not cesta.startswith("Workflows/") or not cesta.endswith(".json"):
            continue
        text = vystupni.read(jmeno).decode("utf-8-sig")
        adresy = set(re.findall(r"https://[A-Za-z0-9.-]+\.sharepoint\.com[^\"']*", text))
        cizi = [a for a in adresy if not a.startswith(web)]
        overit(not cizi,
               f"{cesta.split('/')[-1]} míří na jiný web než canvas app: {sorted(cizi)[:2]}")
        celkem += sum(text.count(a) for a in adresy)

    if celkem:
        varovani.append(
            f"adresa webu je v definicích flow na {celkem} místech — při přenosu na MPSV "
            f"se NEopravuje ručně: appku připojit na cílový web ve Studiu, exportovat "
            f"a znovu spustit build_mapa_flow.py / build_export_flow.py / "
            f"add_mapa_schedule.py"
        )


def overit(podminka, popis):
    global kontrol
    kontrol += 1
    if not podminka:
        chyby.append(popis)


def cti(balik, jmeno):
    for polozka in balik.namelist():
        if polozka.replace("\\", "/").endswith(jmeno):
            return balik.read(polozka).decode("utf-8-sig")
    return None


def nacti_msapp(solution_zip):
    with zipfile.ZipFile(solution_zip) as balik:
        msappy = [n for n in balik.namelist() if n.replace("\\", "/").endswith(".msapp")]
        if len(msappy) != 1:
            return None, len(msappy)
        data = balik.read(msappy[0])
    docasny = Path("runs/app_build/_kontrola.msapp")
    docasny.parent.mkdir(parents=True, exist_ok=True)
    docasny.write_bytes(data)
    return zipfile.ZipFile(docasny), 1


def guidy_listu(text_customizations):
    """Vytáhne z ConnectionReferences dvojice název listu -> GUID."""
    shoda = re.search(r"<ConnectionReferences>(.*?)</ConnectionReferences>", text_customizations, re.S)
    if not shoda:
        return {}
    surovy = shoda.group(1).replace("&quot;", '"').replace("&amp;", "&")
    nalezene = {}
    for jmeno, guid in re.findall(r'"([^"]+)"\s*:\s*\{\s*"tableName"\s*:\s*"([0-9a-f-]{36})"', surovy):
        nalezene[jmeno] = guid
    return nalezene


def main():
    for cesta in (VSTUP, VYSTUP):
        if not cesta.exists():
            print(f"CHYBA: chybí {cesta}")
            return 1

    vstupni = zipfile.ZipFile(VSTUP)
    vystupni = zipfile.ZipFile(VYSTUP)

    # --- manifest solution ---
    manifest = cti(vystupni, "solution.xml")
    overit(manifest is not None, "solution.xml ve výstupu chybí")
    if manifest:
        overit("<Managed>0</Managed>" in manifest, "solution není unmanaged (<Managed>0</Managed>)")
        overit("<UniqueName>mpsv</UniqueName>" in manifest, "publisher není 'mpsv'")
        overit("<CustomizationPrefix>mpsv</CustomizationPrefix>" in manifest, "prefix není 'mpsv'")
        verze = re.search(r"<Version>([^<]+)</Version>", manifest)
        overit(verze is not None and verze.group(1) != "1.0.0.1",
               "verze solution se proti vstupu nezvýšila — import by neproběhl jako upgrade")

    # --- připojení na listy se nesmělo změnit ---
    zdroj_custom = cti(vstupni, "customizations.xml")
    cil_custom = cti(vystupni, "customizations.xml")
    overit(cil_custom is not None, "customizations.xml ve výstupu chybí")
    if zdroj_custom and cil_custom:
        puvodni = guidy_listu(zdroj_custom)
        nove = guidy_listu(cil_custom)
        overit(set(nove) >= OCEKAVANE_LISTY,
               f"v connection reference chybí listy: {sorted(OCEKAVANE_LISTY - set(nove))}")
        overit(puvodni == nove,
               "GUIDy připojených listů se proti vstupní solution změnily")

    # --- flow ze vstupní solution nesmí přebalením zmizet ---
    # Kdyby se stavělo ze staršího balíku, flow by ve výstupu nebylo a upgrade
    # by ho z prostředí odstranil. Tichá ztráta, proto explicitní kontrola.
    def workflows(balik):
        return {Path(n.replace("\\", "/")).name for n in balik.namelist()
                if n.replace("\\", "/").startswith("Workflows/")}

    overit(workflows(vstupni) <= workflows(vystupni),
           f"ve výstupu chybí flow ze vstupní solution: "
           f"{sorted(workflows(vstupni) - workflows(vystupni))}")

    # --- obsah canvas appky ---
    msapp, pocet = nacti_msapp(VYSTUP)
    overit(msapp is not None, f"ve výstupu není právě jeden .msapp (nalezeno {pocet})")
    if msapp:
        polozky = [n.replace("\\", "/") for n in msapp.namelist()]

        packed = cti(msapp, "packed.json")
        overit(packed is not None, "v .msapp chybí packed.json (nebalil to pac?)")
        if packed:
            overit(json.loads(packed).get("LoadConfiguration", {}).get("LoadFromYaml") is True,
                   "packed.json nemá LoadFromYaml=true — Studio by načetlo zastaralé Controls/*.json")

        # vzorce předávají názvy sloupců jako identifikátory (ShowColumns, Search) —
        # to platí jen s tímhle příznakem; kdyby ho balík ztratil, Studio je odmítne
        vlastnosti = cti(msapp, "Properties.json")
        if vlastnosti:
            priznaky = json.loads(vlastnosti).get("AppPreviewFlagsMap", {})
            limit = json.loads(vlastnosti).get("DefaultConnectedDataSourceMaxGetRowsCount")
            overit(limit == 2000,
                   f"strop načítaných řádků je {limit}, ale popisky v appce "
                   f"i dokumentace slibují úplný výsledek do 2 000 — hledání "
                   f"a počty by přestaly být úplné dřív, než kdokoli čeká")
            overit(priznaky.get("supportcolumnnamesasidentifiers") is True,
                   "appka nemá supportcolumnnamesasidentifiers=True, ale vzorce "
                   "předávají sloupce jako identifikátory")

        nalezene = {Path(p).name.replace(".pa.yaml", "") for p in polozky if p.endswith(".pa.yaml")}
        overit(OCEKAVANE_OBRAZOVKY <= nalezene,
               f"v .msapp chybí obrazovky: {sorted(OCEKAVANE_OBRAZOVKY - nalezene)}")
        overit("Screen1" not in nalezene, "v .msapp zůstala výchozí prázdná obrazovka Screen1")

        # Zrušená obrazovka umí v balíku přežít jako Controls/*.json, i když
        # ve Src/*.pa.yaml dávno není. Studio ji načte, mrtvé odkazy nahlásí
        # jako chyby a kvůli nim neprovede App.OnStart — appka naběhne černá
        # a s prázdnými kolekcemi. (Zjištěno na 1.0.0.37, 23.08.2026.)
        duchove = []
        for jmeno in msapp.namelist():
            cesta = jmeno.replace("\\", "/")
            if "Controls/" not in cesta or not cesta.endswith(".json"):
                continue
            data = json.loads(msapp.read(jmeno).decode("utf-8-sig"))
            nazev = (data.get("TopParent") or {}).get("Name") or data.get("Name")
            if nazev and nazev != "App" and nazev not in OCEKAVANE_OBRAZOVKY:
                duchove.append(f"{nazev} v {cesta.split('/')[-1]}")
        overit(not duchove,
               f"v .msapp zůstaly zrušené obrazovky: {duchove} — Studio je načte, "
               f"mrtvé odkazy nahlásí jako chyby a kvůli nim neprovede "
               f"App.OnStart; appka pak naběhne černá")
        overit("App" in nalezene, "v .msapp chybí App.pa.yaml")

        stav = cti(msapp, "_EditorState.pa.yaml")
        overit(stav is not None and "Screen1" not in stav,
               "ScreensOrder stále odkazuje na Screen1")
        if stav:
            for obrazovka in OCEKAVANE_OBRAZOVKY:
                overit(obrazovka in stav, f"ScreensOrder neobsahuje {obrazovka}")
            # první obrazovka v ScreensOrder je ta, kterou appka po startu ukáže
            radky = stav.splitlines()
            index = next((i for i, r in enumerate(radky) if r.strip() == "ScreensOrder:"), None)
            prvni = radky[index + 1].strip().lstrip("- ") if index is not None else "?"
            overit(prvni == UVODNI_OBRAZOVKA,
                   f"úvodní obrazovka je '{prvni}', čekal jsem '{UVODNI_OBRAZOVKA}'")

            # Flow nad krátkým názvem smí přepsat jen to, co samo spočítalo.
        # Kdyby posílalo i nazev nebo dilci_proces_kod z triggerBody, vrátilo
        # by opravu uloženou krátce po sobě zpátky na starou hodnotu.
        for jmeno in vystupni.namelist():
            if "AktualizaceKratkehoNazvu" not in jmeno.replace("\\", "/"):
                continue
            text_flow = vystupni.read(jmeno).decode("utf-8-sig")
            for pole in ("item/nazev\"", "item/dilci_proces_kod"):
                overit(pole not in text_flow,
                       f"flow AktualizaceKratkehoNazvu posílá do PatchItem '{pole}' "
                       f"z triggerBody — přepsalo by novější hodnotu uloženou "
                       f"krátce po sobě")

    # datové zdroje musí zůstat připojené i uvnitř appky
        datasources = cti(msapp, "References/DataSources.json")
        if datasources:
            jmena = {d.get("Name") for d in json.loads(datasources).get("DataSources", [])}
            overit(OCEKAVANE_LISTY <= jmena,
                   f"v appce chybí datové zdroje: {sorted(OCEKAVANE_LISTY - jmena)}")

        # flow volané z appky musí být mezi jejími datovými zdroji. Samotné
        # Workflows/*.json v solution nestačí — dokud se flow ve Studiu nepřipojí
        # (Power Automate → Add flow), Studio vzorec odmítne „Name isn't valid".
        volana = set()
        for polozka in polozky:
            if polozka.endswith(".pa.yaml"):
                text = cti(msapp, Path(polozka).name) or ""
                volana |= set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\.Run\(", text))
        if datasources:
            overit(volana <= jmena,
                   f"appka volá .Run() na neexistující datový zdroj: {sorted(volana - jmena)} "
                   f"— chybí Add flow ve Studiu")

        # každý použitý control musí mít definici šablony, jinak Studio appku
        # neotevře a ohlásí to jako chybu YAML (past z importu 1.0.0.2)
        typy = json.loads(Path("src/control_templates.json").read_text(encoding="utf-8"))["typy"]
        sablony_json = cti(msapp, "Templates.json")
        if sablony_json:
            znamé = {x["Name"] for x in json.loads(sablony_json)["UsedTemplates"]}
            pouzite = set()
            for polozka in polozky:
                if polozka.endswith(".pa.yaml"):
                    for control in re.findall(r"Control:\s*(\S+)", cti(msapp, Path(polozka).name) or ""):
                        overit(control in typy, f"neznámý typ controlu '{control}'")
                        pouzite.add(typy.get(control, control))
            overit(pouzite <= znamé,
                   f"chybí definice šablon pro controly: {sorted(pouzite - znamé)}")

        # politika projektu: žádné externí zdroje.
        # Komentáře se přeskakují — hlavičku s odkazem na dokumentaci píše do
        # každého souboru sám pac a za běhu se nikam nesahá.
        for polozka in polozky:
            if not polozka.endswith(".pa.yaml"):
                continue
            text = cti(msapp, Path(polozka).name)
            radky = [r for r in (text or "").splitlines() if not r.lstrip().startswith("#")]
            s_url = [r for r in radky if "http://" in r or "https://" in r]
            povolene = [r for r in s_url if VYJIMKA_URL in r]
            for radek in povolene:
                varovani.append(
                    f"{Path(polozka).name}: povolená výjimka {VYJIMKA_URL} — adresa mapy "
                    f"je v appce natvrdo, při přenosu na MPSV ji je nutné změnit"
                )
            overit(not [r for r in s_url if VYJIMKA_URL not in r],
                   f"{polozka} obsahuje externí URL")

    adresy_ve_flow(vystupni, cil_custom)

    print(f"kontrol: {kontrol}, chyb: {len(chyby)}")
    for text_varovani in varovani:
        print(f"VAROVÁNÍ: {text_varovani}")
    for text in chyby:
        print(f"CHYBA: {text}")
    if chyby:
        print("\nNEPROŠLO — solution neimportovat")
        return 1
    print(f"\nOK — {VYSTUP} je připravená k importu jako upgrade")
    return 0


if __name__ == "__main__":
    sys.exit(main())
