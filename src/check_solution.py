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

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402
import check_app  # noqa: E402  — návrhová plocha, proti které se počítají překryvy

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

# Hostitelé, kteří v definici flow být smí a s webem appky nesouvisí:
# schéma Logic Apps a jmenný prostor HTML v šabloně exportovaného dokumentu.
POVOLENI_HOSTI = {"schema.management.azure.com", "www.w3.org"}


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
            klic, obsah = next(iter(datasety.items()))
            # Klíč nese s napojením přes proměnné suffix se schemaname webu;
            # čistá adresa je v datasetOverride.name.
            return (obsah.get("datasetOverride") or {}).get("name") or klic
    return None


def _flow_soubory(vystupni):
    for jmeno in vystupni.namelist():
        cesta = jmeno.replace("\\", "/")
        if cesta.startswith("Workflows/") and cesta.endswith(".json"):
            yield jmeno, cesta.split("/")[-1]


def _sharepointove_akce(definice):
    """Projde trigger i všechny akce a vrátí ty, které jedou přes SharePoint konektor."""
    fronta = [definice.get("triggers") or {}, definice.get("actions") or {}]
    while fronta:
        skupina = fronta.pop()
        for jmeno, uzel in skupina.items():
            if not isinstance(uzel, dict):
                continue
            vstupy = uzel.get("inputs")
            if isinstance(vstupy, dict):
                host = vstupy.get("host") or {}
                if "shared_sharepointonline" in str(host.get("apiId", "")):
                    yield jmeno, host.get("operationId"), vstupy.get("parameters") or {}
            for klic in ("actions",):
                if isinstance(uzel.get(klic), dict):
                    fronta.append(uzel[klic])
            if isinstance(uzel.get("else"), dict):
                fronta.append(uzel["else"].get("actions") or {})
            for vetev in (uzel.get("cases") or {}).values():
                if isinstance(vetev, dict):
                    fronta.append(vetev.get("actions") or {})


def adresy_ve_flow(vystupni, customizations):
    """V definicích flow nesmí být adresa webu ani GUID listu — jen proměnné.

    Do 1.0.0.61 tam adresa byla, a to na 16 místech: parametr `dataset`
    u každé SharePoint akce, `table` u čtení i zápisu a složená návratová
    adresa. Tehdejší brána to připouštěla, jen hlídala, že všechna míří na týž
    web jako canvas app — a přesně na tom padl import na tenant MPSV
    28.08.2026: web PPF tam neexistuje, akce jsou neplatné, flow nejde zapnout
    a designer list ani nenabídne k přepnutí.

    Od 1.0.0.62 se web i listy berou z proměnných prostředí, takže se v definici
    nesmí objevit vůbec. Kontrola je proto absolutní, ne relativní k appce.
    """
    web = adresa_webu(customizations)
    overit(web is not None, "v balíku není adresa webu canvas appky")
    host_appky = re.match(r"https://([^/]+)", web).group(1).lower() if web else ""

    for jmeno, soubor in _flow_soubory(vystupni):
        text = vystupni.read(jmeno).decode("utf-8-sig")

        adresy = sorted(set(re.findall(r"[A-Za-z0-9-]+\.sharepoint\.com[^\"']*", text)))
        overit(not adresy,
               f"{soubor}: adresa SharePointu v definici flow — na cizím tenantu "
               f"tam takové místo nejde opravit ani v designeru: {adresy[:2]}")

        # Cizí hostitel i mimo sharepoint.com; předchozí kontrola ho nechytí.
        hosti = {h.lower() for h in re.findall(r"https?://([A-Za-z0-9.-]+)", text)}
        neznami = sorted(hosti - {host_appky} - POVOLENI_HOSTI)
        overit(not neznami, f"{soubor} obsahuje adresu na cizího hostitele: {neznami}")


GUID_LISTU = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"


def promenne_ve_flow(vystupni, promenne_appky=frozenset()):
    """Každá SharePoint akce bere web i list z deklarované proměnné prostředí.

    Samotná nepřítomnost adresy nestačí: GUID listu adresu neobsahuje, takže
    by prošel nepovšimnut, a odkaz na proměnnou, kterou balík nedeklaruje, se
    projeví až tím, že flow po importu nejde zapnout.
    """
    ocekavany_web = ep.web()
    listove = {ep.param(schema) for schema in ep.LIST_PROMENNA.values()}
    pouzite = set()

    for jmeno, soubor in _flow_soubory(vystupni):
        definice = json.loads(vystupni.read(jmeno).decode("utf-8-sig"))["properties"]["definition"]
        # AktualizaceKratkehoNazvu je výjimka a musí jí zůstat: PatchItem si
        # schéma těla odvozuje z konkrétního listu, takže s `table` z proměnné
        # se rozložené klíče `item/<sloupec>` nerozbalí a flow nejde zapnout
        # ("missing required property 'item'", MPSV 28.08.2026). Celé flow proto
        # drží jeden GUID — trigger, čtení i zápis, ať nemíří každý jinam.
        # `dataset` (web) proměnnou snese i tady; pro tělo nemá význam.
        list_natvrdo = "AktualizaceKratkehoNazvu" in soubor
        guidy = set()
        for akce, operace, parametry in _sharepointove_akce(definice):
            if "dataset" in parametry:
                overit(parametry["dataset"] == ocekavany_web,
                       f"{soubor}/{akce} ({operace}): dataset není proměnná "
                       f"{ep.WEB}, ale {parametry['dataset']!r}")
                pouzite.add(parametry["dataset"])
            if "table" in parametry:
                if list_natvrdo:
                    overit(re.fullmatch(GUID_LISTU, str(parametry["table"])) is not None,
                           f"{soubor}/{akce} ({operace}): table musí být GUID "
                           f"(PatchItem runtime výraz nesnese), ale je "
                           f"{parametry['table']!r}")
                    guidy.add(parametry["table"])
                else:
                    overit(parametry["table"] in listove,
                           f"{soubor}/{akce} ({operace}): table není žádná z proměnných "
                           f"listů, ale {parametry['table']!r}")
                    pouzite.add(parametry["table"])
        overit(len(guidy) <= 1,
               f"{soubor}: trigger, čtení a zápis míří na různé listy: {sorted(guidy)}")

    slozky = {c.split("/")[1] for c in
              (n.replace("\\", "/") for n in vystupni.namelist())
              if c.startswith(ep.SLOZKA + "/") and c.endswith("environmentvariabledefinition.xml")}
    overit(slozky == {d[0] for d in ep.DEFINICE},
           f"definice proměnných v balíku nesedí na env_promenne.py: "
           f"{sorted(slozky ^ {d[0] for d in ep.DEFINICE})}")

    hodnoty = [n for n in vystupni.namelist() if "environmentvariablevalues" in n]
    overit(not hodnoty,
           f"balík nese uložené hodnoty proměnných {hodnoty} — každý import by jimi "
           f"přepsal nastavení cílového prostředí")

    # Proměnnou nemusí používat flow — od F9 si přes ni bere napojení i appka
    # (`Útvary` jsou jen v appce). Nepoužitá je teprve ta, kterou nezná ani jedno.
    pouzite |= {ep.param(schema) for schema in promenne_appky}
    nepouzite = sorted({ep.param(d[0]) for d in ep.DEFINICE} - pouzite)
    overit(not nepouzite,
           f"deklarovaná, ale nepoužitá proměnná: {nepouzite} — průvodce importem "
           f"se na ni zeptá a nikdo nebude vědět proč")


def deklarace_parametru(vystupni):
    """Každý parametr, na který se flow odkazuje, musí být deklarovaný.

    Bez deklarace flow spadne na
    `InvalidTemplate … The workflow parameter '…' is not found` a volající
    appka vidí jen `502 BadGateway / NoResponse` — z appky se příčina poznat
    nedá, proto brána.

    Platí to i pro odkaz, který je celou hodnotou parametru konektoru
    (`dataset`, `table`). Po prvním nálezu (ExportFlow/Cesta_webu, výraz)
    to vypadalo, že konektor je výjimka — balík 1.0.0.63 běžel úplně bez
    deklarací. Druhý nález (MapaPublishFlow/Sablona, `dataset` jako celá
    hodnota) to vyvrátil. Brána proto nerozlišuje, kde se odkaz objeví.
    """
    for jmeno, soubor in _flow_soubory(vystupni):
        definice = json.loads(vystupni.read(jmeno).decode("utf-8-sig"))["properties"]["definition"]
        vsechny = definice.get("parameters") or {}
        pouzite = {p for p in re.findall(r"parameters\('([^']+)'\)",
                                         json.dumps(definice, ensure_ascii=False))
                   if not p.startswith("$")}

        for p in sorted(pouzite):
            overit(p in vsechny,
                   f"{soubor}: parametr {p!r} je použitý, ale není "
                   f"v definition.parameters — flow spadne na InvalidTemplate")
            # Deklarace sama nestačí: bez `metadata.schemaName` je to parametr
            # bez vazby na proměnnou prostředí, takže by zůstal bez hodnoty.
            schema = ((vsechny.get(p) or {}).get("metadata") or {}).get("schemaName")
            overit(schema is not None and f"({schema})" in p,
                   f"{soubor}: deklarace {p!r} nemá metadata.schemaName navázané "
                   f"na proměnnou prostředí (je {schema!r}) — hodnota do parametru "
                   f"nedorazí")

        for nazev, popis in vsechny.items():
            if nazev.startswith("$") or not isinstance(popis, dict):
                continue
            overit(popis.get("defaultValue", None) != "",
                   f"{soubor}: parametr {nazev!r} má prázdný defaultValue — "
                   f"s ním selže import solution")


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


def napojeni_appky(text_customizations):
    """Vrátí blok dataSets SharePoint connection reference, nebo None."""
    shoda = re.search(r"<ConnectionReferences>(.*?)</ConnectionReferences>", text_customizations, re.S)
    if not shoda:
        return None
    try:
        reference = json.loads(shoda.group(1))
    except json.JSONDecodeError:
        return None
    for odkaz in reference.values():
        if "shared_sharepointonline" in odkaz.get("id", ""):
            return odkaz.get("dataSets") or {}
    return None


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
    napojene_zdroje = None
    if zdroj_custom and cil_custom:
        puvodni = guidy_listu(zdroj_custom)
        nove = guidy_listu(cil_custom)
        overit(set(nove) >= OCEKAVANE_LISTY,
               f"v connection reference chybí listy: {sorted(OCEKAVANE_LISTY - set(nove))}")
        # Zdroje, které build odebírá jako nepoužívané, ve výstupu chybět mají.
        zbyle = {k: v for k, v in puvodni.items() if k not in ep.NEPOUZIVANE_ZDROJE}
        overit(zbyle == nove,
               "GUIDy připojených listů se proti vstupní solution změnily")
        overit(not (set(nove) & set(ep.NEPOUZIVANE_ZDROJE)),
               f"ve výstupu zůstal nepoužívaný zdroj: "
               f"{sorted(set(nove) & set(ep.NEPOUZIVANE_ZDROJE))}")

        # --- appka musí být napojená přes proměnné prostředí, ne natvrdo ---
        # Bez toho ukazuje po importu na listy prostředí, ze kterého se
        # exportovala, a App.OnStart spadne na prvním ClearCollect.
        datasety = napojeni_appky(cil_custom)
        overit(datasety is not None,
               "v customizations.xml není SharePoint connection reference")
        deklarovane = {d[0] for d in ep.DEFINICE}
        for adresa, dataset in (datasety or {}).items():
            prepis = dataset.get("datasetOverride") or {}
            overit(prepis.get("environmentVariableName") == ep.WEB,
                   f"dataset {adresa} nemá datasetOverride na {ep.WEB}")
            overit(adresa == f"{prepis.get('name')}_{ep.WEB}",
                   f"klíč datasetu není '<url>_{ep.WEB}': {adresa}")
            for jmeno, popis in (dataset.get("dataSources") or {}).items():
                prepis_listu = popis.get("tableNameOverride") or {}
                promenna = prepis_listu.get("environmentVariableName")
                overit(promenna is not None,
                       f"zdroj {jmeno} nemá tableNameOverride — po importu jinam se nenapojí")
                overit(promenna in deklarovane,
                       f"zdroj {jmeno} odkazuje na nedeklarovanou proměnnou {promenna}")
                overit(prepis_listu.get("name") == popis.get("tableName"),
                       f"zdroj {jmeno}: tableNameOverride.name nesedí na tableName")

        napojene_zdroje = {jmeno for dataset in (datasety or {}).values()
                           for jmeno in (dataset.get("dataSources") or {})}

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
        # --- žádný zdroj se cestou neztratil ---
        # Tvar každého bloku v napojení může být bezvadný, a přesto tam chybí
        # polovina zdrojů: Studio zakládá ručně připojený zdroj do vlastního
        # `dataSets` bloku a build je slučuje do jednoho. Kdyby slučování
        # selhalo, jeden blok druhý přepíše — a v appce zůstane napojený jen
        # ten poslední. Pravdu o tom, na co se appka opravdu váže, má `.msapp`,
        # ne XML, proto se porovnávají proti sobě.
        zdroje_json = json.loads(msapp.read("References/DataSources.json").decode("utf-8-sig"))
        v_appce = {z.get("Name") for z in zdroje_json.get("DataSources", [])
                   if z.get("Type") == "ConnectedDataSourceInfo"} - set(ep.NEPOUZIVANE_ZDROJE)
        overit(napojene_zdroje is not None and napojene_zdroje == v_appce,
               f"napojení neodpovídá zdrojům appky — v .msapp navíc "
               f"{sorted(v_appce - napojene_zdroje)}, v napojení navíc "
               f"{sorted(napojene_zdroje - v_appce)}")

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
            # Podle návrhové plochy počítá check_app.py souřadnice z výrazů
            # `Parent.Width - N`, a tím hlídá překryvy prvků. Kdyby se plocha
            # v appce změnila a konstanta ne, kontrola překryvu by tiše
            # počítala s jinými čísly, než jaká appka doopravdy má.
            plocha = json.loads(vlastnosti)
            for klic, ocekavano, kde in (
                    ("DocumentLayoutWidth", check_app.SIRKA_PLOCHY, "šířka"),
                    ("DocumentLayoutHeight", check_app.VYSKA_PLOCHY, "výška")):
                overit(plocha.get(klic) == ocekavano,
                       f"{kde} návrhové plochy je {plocha.get(klic)}, ale "
                       f"check_app.py počítá s {ocekavano} — sjednoť to, jinak "
                       f"kontrola překryvu prvků počítá s cizími čísly")

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

            # Flow nad krátkým názvem musí povinné sloupce listu posílat
        # (jinak ho v cílovém prostředí nejde aktivovat), ale nikdy ze snímku
        # triggeru — ten je starý až o minutu a přepsal by novější editaci.
        # Obojí splní jen čtení přes `Nacti_aktivitu` těsně před zápisem.
        for jmeno in vystupni.namelist():
            if "AktualizaceKratkehoNazvu" not in jmeno.replace("\\", "/"):
                continue
            flow_json = json.loads(vystupni.read(jmeno).decode("utf-8-sig"))
            definice = flow_json["properties"]["definition"]
            zapis = (definice["actions"].get("Lisi_se", {})
                     .get("actions", {}).get("Zapsat_kratky_nazev", {}))
            parametry = zapis.get("inputs", {}).get("parameters", {})
            for pole in ("item/Title", "item/nazev", "item/dilci_proces_kod"):
                overit(parametry.get(pole) == "@body('Nacti_aktivitu')?['%s']"
                       % pole.split("/", 1)[1],
                       f"flow AktualizaceKratkehoNazvu neposílá do PatchItem '{pole}' "
                       f"ze stavu čteného těsně před zápisem (je tam "
                       f"'{parametry.get(pole)}') — bez povinných polí nejde flow "
                       f"aktivovat, ze snímku triggeru by přepsalo novější hodnotu")
            overit("Nacti_aktivitu" in definice["actions"],
                   "flow AktualizaceKratkehoNazvu nemá akci Nacti_aktivitu")

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

    # Proměnné, které si bere napojení appky (datasetOverride/tableNameOverride).
    promenne_appky = set()
    for dataset in (napojeni_appky(cil_custom) or {}).values():
        prepis = dataset.get("datasetOverride") or {}
        if prepis.get("environmentVariableName"):
            promenne_appky.add(prepis["environmentVariableName"])
        for popis in (dataset.get("dataSources") or {}).values():
            prepis_listu = popis.get("tableNameOverride") or {}
            if prepis_listu.get("environmentVariableName"):
                promenne_appky.add(prepis_listu["environmentVariableName"])
    promenne_ve_flow(vystupni, promenne_appky)
    deklarace_parametru(vystupni)

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
