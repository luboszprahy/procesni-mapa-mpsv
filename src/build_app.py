"""Vloží zdroje z src/app_src/ do exportované solution a vyrobí zip k importu.

Postup: rozbalí vstupní solution -> pac canvas unpack (layout SourceCode) ->
vymění Src/*.pa.yaml za naše -> pac canvas pack -> složí solution zpět.

Spouštět z kořene projektu:
    python src/build_app.py
    python src/build_app.py --verze 1.0.0.3

Cesta k pac.exe: přepínač --pac nebo proměnná PAC_EXE. Bez ní se hledá
v rozšíření Power Platform Tools ve VS Code.
"""

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne  # noqa: E402

APP_SRC = Path("src/app_src")
VYCHOZI_SOLUTION = Path("input/procesnimapa_1_0_0_1.zip")
VYSTUP = Path("deploy")
PRACOVNI = Path("runs/app_build")
SABLONY = Path("src/control_templates.json")

# pořadí rozhoduje: první je úvodní obrazovka appky
OBRAZOVKY = ["scr_Dashboard", "scr_Detail", "scr_Vazby", "scr_Ciselnik",
             "scr_Nahled"]




def najdi_pac(zadana):
    if zadana:
        return Path(zadana)
    if os.environ.get("PAC_EXE"):
        return Path(os.environ["PAC_EXE"])

    # rozšíření VS Code dodává pac jako nupkg; rozbalený bývá vedle něj
    koren = Path.home() / ".vscode" / "extensions"
    for kandidat in sorted(koren.glob("microsoft-isvexptools.powerplatform-vscode-*/dist/pac/tools/pac.exe")):
        return kandidat
    for kandidat in sorted(koren.glob("microsoft-isvexptools.powerplatform-vscode-*/dist/pac/*.nupkg")):
        cil = PRACOVNI / "pac"
        if not (cil / "tools" / "pac.exe").exists():
            cil.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(kandidat) as balik:
                balik.extractall(cil)
        return cil / "tools" / "pac.exe"
    return None


def odstran_duchy(cesta_msapp):
    """Vyhodí z .msapp Controls/*.json obrazovek, které už v OBRAZOVKY nejsou.

    `pac canvas unpack --layout SourceCode` rozbalí jen Src/*.pa.yaml; zbytek
    balíku (Controls, References, Assets) drží v .msapr a pack ho vrátí zpátky
    beze změny. Zrušená obrazovka tak v balíku přežije jako duch: Studio ho
    načte, každý odkaz na prvek, který už neexistuje, nahlásí jako chybu,
    a kvůli těm chybám NEPROVEDE App.OnStart. Appka pak naběhne černá (barvy
    jsou proměnné z OnStart) a s prázdnými kolekcemi — jen aktivity, které se
    načítají až v OnVisible obrazovky, v ní jsou.

    Zjištěno 23.08.2026 na 1.0.0.37: zrušená scr_Seznam nechala v .msapp
    Controls/4.json o 626 kB s 65 prvky, z toho 30 už neexistujících, a appka
    se po importu neotevřela. Obrazovky, které naopak v Controls nejsou
    (scr_Dashboard, scr_Ciselnik), Studio bez potíží načte z YAML — Controls
    tedy nutné nejsou a smazat je je bezpečné.
    """
    with zipfile.ZipFile(cesta_msapp) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    smazane = []
    for jmeno in list(polozky):
        cesta = jmeno.replace("\\", "/")
        if "Controls/" not in cesta or not cesta.endswith(".json"):
            continue
        data = json.loads(polozky[jmeno].decode("utf-8-sig"))
        nazev = (data.get("TopParent") or {}).get("Name") or data.get("Name")
        if nazev and nazev != "App" and nazev not in OBRAZOVKY:
            del polozky[jmeno]
            smazane.append(f"{nazev} ({cesta.split('/')[-1]})")
        elif not nazev:
            raise SystemExit(f"CHYBA: v {cesta} nenacházím jméno obrazovky — "
                             f"kontrola duchů by mlčky přestala fungovat")

    # výsledek App checkeru z minulého buildu drží odkazy na zrušené prvky
    for jmeno in list(polozky):
        if jmeno.replace("\\", "/").endswith("AppCheckerResult.sarif"):
            del polozky[jmeno]
            smazane.append("AppCheckerResult.sarif")

    if smazane:
        with zipfile.ZipFile(cesta_msapp, "w", zipfile.ZIP_DEFLATED) as balik:
            for jmeno, data in polozky.items():
                balik.writestr(jmeno, data)
    return smazane


def spust(prikaz):
    vysledek = subprocess.run(prikaz, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if vysledek.returncode != 0:
        print(vysledek.stdout)
        print(vysledek.stderr, file=sys.stderr)
        raise SystemExit(f"CHYBA: selhalo {prikaz[0]} {prikaz[1] if len(prikaz) > 1 else ''}")
    return vysledek.stdout


def rozbal(zdroj, cil):
    """Rozbalí zip; msapp/solution používají zpětná lomítka, unzip by je nezvládl."""
    cil.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zdroj) as balik:
        for polozka in balik.namelist():
            cesta = cil / polozka.replace("\\", "/")
            cesta.parent.mkdir(parents=True, exist_ok=True)
            if not polozka.endswith("/"):
                cesta.write_bytes(balik.read(polozka))


def zabal(adresar, cil):
    with zipfile.ZipFile(cil, "w", zipfile.ZIP_DEFLATED) as balik:
        for cesta in sorted(adresar.rglob("*")):
            if cesta.is_file():
                balik.write(cesta, cesta.relative_to(adresar).as_posix())


def vloz_verzi(cesta_app_yaml, verze):
    """Dosadí do App.OnStart číslo balíku, aby ho appka uměla ukázat.

    Bez razítka se z běžící appky nedá poznat, jestli po importu proběhla ve
    Studiu mikro-změna + Save + Publish. Publikovaný dokument vzniká až tam,
    takže ostatním účtům může dál běžet stará verze — a jediný rozdíl je
    v obsahu obrazovek, který nikdo nezná zpaměti (nález B-03, kolo 4).
    """
    text = cesta_app_yaml.read_text(encoding="utf-8")
    novy, pocet = re.subn(r'Set\(varVerze, "[^"]*"\)', f'Set(varVerze, "{verze}")', text)
    if pocet != 1:
        raise SystemExit(f"CHYBA: razítko verze nahrazeno {pocet}x, čekal jsem 1x")
    cesta_app_yaml.write_text(novy, encoding="utf-8")


MAX_RADKU = 2000


def nastav_limit_radku(cesta_msapp):
    """Srovná strop načítaných řádků s tím, co appka o sobě tvrdí.

    Prázdná appka ze Studia má DefaultConnectedDataSourceMaxGetRowsCount = 500,
    takže Search i počty nad aktivitami pracují s prvním pěti stovkami — a
    popisky u toho slibují úplný výsledek do 2 000. Rozpor je tichý: nic
    nespadne, jen odpověď přestane být úplná dřív, než kdokoli čeká.
    """
    with zipfile.ZipFile(cesta_msapp) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klic = next(n for n in polozky if n.replace("\\", "/").endswith("Properties.json"))
    vlastnosti = json.loads(polozky[klic].decode("utf-8-sig"))
    puvodni = vlastnosti.get("DefaultConnectedDataSourceMaxGetRowsCount")
    if puvodni == MAX_RADKU:
        return None

    vlastnosti["DefaultConnectedDataSourceMaxGetRowsCount"] = MAX_RADKU
    polozky[klic] = json.dumps(vlastnosti, ensure_ascii=False).encode("utf-8")
    with zipfile.ZipFile(cesta_msapp, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)
    return puvodni


def doplnit_sablony(cesta_msapp):
    """Doplní do balíku definice controlů, které původní appka neobsahovala.

    Prázdná appka ze Studia nese v References/Templates.json jen šablony, které
    sama používala. Studio pak odmítne otevřít appku s controlem, jehož definici
    nezná, a ohlásí to jako chybu YAML. Definice jsou nezávislé na tenantu
    (ověřeno shodou sdílených šablon), takže je stačí přiložit.
    """
    data = json.loads(Path(SABLONY).read_text(encoding="utf-8"))
    zasoba = {s["Name"]: s for s in data["sablony"]}
    typy = data["typy"]

    with zipfile.ZipFile(cesta_msapp) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klic = next(n for n in polozky if n.replace("\\", "/").endswith("References/Templates.json"))
    templates = json.loads(polozky[klic].decode("utf-8-sig"))
    pritomne = {s["Name"] for s in templates["UsedTemplates"]}

    potreba = set()
    for jmeno, obsah in polozky.items():
        if jmeno.replace("\\", "/").endswith(".pa.yaml"):
            for control in re.findall(r"Control:\s*(\S+)", obsah.decode("utf-8-sig")):
                if control not in typy:
                    raise SystemExit(f"CHYBA: neznámý typ controlu '{control}' — doplň ho do {SABLONY}")
                potreba.add(typy[control])

    chybi = sorted(potreba - pritomne)
    nemam = [s for s in chybi if s not in zasoba]
    if nemam:
        raise SystemExit(f"CHYBA: pro šablony {nemam} nemám definici v {SABLONY}")

    doplnene = []
    for sablona in chybi:
        templates["UsedTemplates"].append(zasoba[sablona])
        doplnene.append(f"{sablona}@{zasoba[sablona]['Version']}")

    if not doplnene:
        return []

    polozky[klic] = json.dumps(templates, ensure_ascii=False).encode("utf-8")
    with zipfile.ZipFile(cesta_msapp, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)
    return doplnene


def vymen_zdroje_bez_pac(cesta_msapp, verze):
    """Vymění Src/*.pa.yaml přímo v .msapp, bez pac.

    Balík zabalený z YAML má v packed.json LoadFromYaml=true, takže Studio čte
    Src/*.pa.yaml a Controls/*.json si dogeneruje samo — výměna zdrojů je pak
    obyčejná úprava zipu. Na stroji bez pac je to jediná cesta, jak vydat opravu.
    Nefunguje na balíku exportovaném ze Studia (ten YAML nenese).
    """
    with zipfile.ZipFile(cesta_msapp) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    def klic_koncici(pripona):
        nalezene = [n for n in polozky if n.replace("\\", "/").endswith(pripona)]
        if len(nalezene) != 1:
            raise SystemExit(f"CHYBA: v .msapp není právě jeden {pripona} (nalezeno {len(nalezene)})")
        return nalezene[0]

    packed = json.loads(polozky[klic_koncici("packed.json")].decode("utf-8-sig"))
    if packed.get("LoadConfiguration", {}).get("LoadFromYaml") is not True:
        raise SystemExit(
            "CHYBA: balík nemá LoadFromYaml=true — Studio by četlo Controls/*.json,\n"
            "       ne vyměněné YAML. Bez pac se dá upravit jen balík už zabalený z YAML."
        )

    for nazev in ["App"] + OBRAZOVKY:
        polozky[klic_koncici(f"Src/{nazev}.pa.yaml")] = (APP_SRC / f"{nazev}.pa.yaml").read_bytes()

    klic_app = klic_koncici("Src/App.pa.yaml")
    zdroj = polozky[klic_app].decode("utf-8-sig")
    novy, pocet = re.subn(r'Set\(varVerze, "[^"]*"\)', f'Set(varVerze, "{verze}")', zdroj)
    if pocet != 1:
        raise SystemExit(f"CHYBA: razítko verze nahrazeno {pocet}x, čekal jsem 1x")
    polozky[klic_app] = novy.encode("utf-8")

    stav = polozky[klic_koncici("Src/_EditorState.pa.yaml")].decode("utf-8-sig")
    for obrazovka in OBRAZOVKY:
        if obrazovka not in stav:
            raise SystemExit(f"CHYBA: _EditorState neuvádí obrazovku {obrazovka}")

    with zipfile.ZipFile(cesta_msapp, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)
    return len(OBRAZOVKY) + 1


# Povinné sloupce listu, které zápisová akce flow MUSÍ posílat, jinak se flow
# nedá aktivovat (OpenApiOperationParameterValidationFailed). Do 1.0.0.63 je
# tenhle skript naopak odebíral, aby flow nepřepsalo novější název snímkem
# z triggeru — jenže tím se čistý import na cizí tenant stal neaktivovatelným
# (MPSV, 28.08.2026). Obojí řeší až `Nacti_aktivitu` v build_flow.py: pole se
# posílají, ale načtená těsně před zápisem. Tady se proto jen KONTROLUJE, že
# tam jsou a že nepocházejí z triggeru.
FLOW_POLE_POVINNA = ["item/Title", "item/nazev", "item/dilci_proces_kod"]


def zkontroluj_flow_kratky_nazev(solution_dir):
    """Zápis do listu musí nést povinná pole, a to ze stavu čteného před zápisem.

    Dvě selhání, každé tiché jiným způsobem:
    - pole chybí  -> flow se v cílovém prostředí nedá zapnout,
    - pole z triggerBody -> flow vrátí novější editaci na starou hodnotu.
    """
    nalezy = []
    for cesta in sorted((solution_dir / "Workflows").glob("*.json")):
        if "AktualizaceKratkehoNazvu" not in cesta.name:
            continue
        data = json.loads(cesta.read_text(encoding="utf-8-sig"))
        for akce in _projdi_akce(data["properties"]["definition"]["actions"]):
            vstupy = akce.get("inputs")
            if not isinstance(vstupy, dict):
                continue
            host = vstupy.get("host", {})
            if host.get("operationId") != "PatchItem":
                continue
            parametry = vstupy.get("parameters", {})
            chybi = [p for p in FLOW_POLE_POVINNA if p not in parametry]
            if chybi:
                nalezy.append(f"PatchItem nemá povinná pole: {', '.join(chybi)}")
            z_triggeru = [p for p in FLOW_POLE_POVINNA
                          if "triggerBody" in str(parametry.get(p, ""))]
            if z_triggeru:
                nalezy.append(
                    f"PatchItem bere ze snímku triggeru: {', '.join(z_triggeru)}")
    if nalezy:
        raise SystemExit("CHYBA: " + "; ".join(nalezy))
    return len(FLOW_POLE_POVINNA)


def _projdi_akce(akce):
    """Projde akce flow včetně větví If — zápis bývá vnořený."""
    for definice in (akce or {}).values():
        if not isinstance(definice, dict):
            continue
        yield definice
        for klic in ("actions", "else"):
            vnorene = definice.get(klic)
            if isinstance(vnorene, dict):
                vnorene = vnorene.get("actions", vnorene)
            if isinstance(vnorene, dict):
                yield from _projdi_akce(vnorene)


def odeber_nepouzivane_zdroje(cesta_msapp):
    """Vyhodí z appky datové zdroje, na které se neodkazuje žádný vzorec.

    Knihovna Dokumenty přibyla ze Studia při zakládání appky. Sama o sobě
    neškodí, ale při napojení přes proměnné by musela dostat vlastní
    proměnnou — v jednom `dataSets` bloku nesmí zůstat zdroj bez overridu.
    Že ji opravdu nikdo nepoužívá, hlídá check_app nad YAML zdroji.
    """
    with zipfile.ZipFile(cesta_msapp) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klic = next((n for n in polozky
                 if n.replace("\\", "/").endswith("References/DataSources.json")), None)
    if klic is None:
        raise SystemExit("CHYBA: v .msapp není References/DataSources.json")

    data = json.loads(polozky[klic].decode("utf-8-sig"))
    puvodni = len(data["DataSources"])
    odebrane = [d["Name"] for d in data["DataSources"]
                if d.get("Name") in env_promenne.NEPOUZIVANE_ZDROJE]
    data["DataSources"] = [d for d in data["DataSources"]
                           if d.get("Name") not in env_promenne.NEPOUZIVANE_ZDROJE]
    if len(data["DataSources"]) == puvodni:
        return []

    polozky[klic] = json.dumps(data, ensure_ascii=False).encode("utf-8")
    with zipfile.ZipFile(cesta_msapp, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, obsah in polozky.items():
            balik.writestr(jmeno, obsah)
    return odebrane


def napoj_appku_na_promenne(solution_dir):
    """Přepíše napojení canvas appky na proměnné prostředí.

    Bez toho drží appka v `<ConnectionReferences>` adresu webu a GUIDy listů
    toho prostředí, ze kterého se exportovala — po importu jinam ukazuje na
    listy, které tam nejsou, a `App.OnStart` spadne na prvním ClearCollect.
    S overridy si napojení vezme z proměnných, které se vyplňují při importu.

    Tvar podle produkčních vzorů MiddleOfficeParametrizace a VendorManagement:
    klíč datasetu je `<url>_<schemaname webu>`, uvnitř `datasetOverride`
    a u každého zdroje `tableNameOverride`. Do `.msapp` se přitom nesahá —
    `DataSources.json` zůstává na čisté URL a holém GUID i ve vzorech.
    """
    cesta = solution_dir / "customizations.xml"
    text = cesta.read_text(encoding="utf-8-sig")
    nalez = re.search(r"<ConnectionReferences>(.*?)</ConnectionReferences>", text, re.S)
    if nalez is None:
        raise SystemExit("CHYBA: customizations.xml nemá blok ConnectionReferences")

    reference = json.loads(nalez.group(1))
    napojene, odebrane = [], []
    for odkaz in reference.values():
        if "shared_sharepointonline" not in odkaz.get("id", ""):
            continue

        odkaz["dataSources"] = [z for z in odkaz.get("dataSources", [])
                                if z not in env_promenne.NEPOUZIVANE_ZDROJE]

        # Bloky se SLUČUJÍ do jednoho. Studio zakládá každý ručně připojený
        # zdroj do vlastního bloku klíčovaného čistou URL, kdežto zdroje, které
        # už jednou prošly tímhle buildem, sedí v bloku se suffixem. Obojí
        # ukazuje na týž web, takže po očištění klíče vyjde stejný klíč — a
        # zápis do slovníku po jednom bloku by ten předchozí PŘEPSAL. Projevilo
        # se to na exportu 1.0.0.78: šest listů v prvním bloku, knihovna Zálohy
        # ve druhém, a ve výsledku by v appce zůstala jen ta knihovna.
        cesty, zdroje = set(), {}
        for adresa, dataset in (odkaz.get("dataSets") or {}).items():
            # Klíč už suffix nese, když se staví z balíku, který přes proměnné
            # jednou prošel — jinak by se nabaloval podruhé.
            cista = adresa[: -len("_" + env_promenne.WEB)] if adresa.endswith("_" + env_promenne.WEB) else adresa
            cesty.add((dataset.get("datasetOverride") or {}).get("name") or cista)
            for jmeno, popis in (dataset.get("dataSources") or {}).items():
                if jmeno in env_promenne.NEPOUZIVANE_ZDROJE:
                    odebrane.append(jmeno)
                    continue
                promenna = env_promenne.LIST_PROMENNA.get(jmeno)
                if promenna is None:
                    raise SystemExit(
                        f"CHYBA: zdroj '{jmeno}' nemá proměnnou v LIST_PROMENNA — "
                        "doplň ji, nebo zdroj zařaď mezi nepoužívané")
                guid = popis.get("tableName")
                zdroje[jmeno] = {
                    "tableName": guid,
                    "tableNameOverride": {"name": guid, "environmentVariableName": promenna},
                }
                napojene.append(f"{jmeno}={promenna}")

        if len(cesty) > 1:
            raise SystemExit(
                f"CHYBA: appka má zdroje na více webech {sorted(cesty)} — sloučit je "
                f"pod jednu proměnnou {env_promenne.WEB} by je přepojilo jinam")
        if cesty:
            cista = next(iter(cesty))
            odkaz["dataSets"] = {
                f"{cista}_{env_promenne.WEB}": {
                    "datasetOverride": {"name": cista,
                                        "environmentVariableName": env_promenne.WEB},
                    "dataSources": zdroje,
                }
            }

    if not napojene:
        raise SystemExit("CHYBA: nenašel jsem SharePoint connection reference k napojení")

    novy = json.dumps(reference, separators=(",", ":"), ensure_ascii=False)
    cesta.write_text(text[: nalez.start(1)] + novy + text[nalez.end(1):], encoding="utf-8")
    return napojene, odebrane


def dorovnej_deklarace_parametru(solution_dir):
    """Každý parametr, na který se flow odkazuje, musí být v `definition.parameters`.

    Jinak flow spadne za běhu na
    `InvalidTemplate … The workflow parameter '<název>' is not found`
    a volající appka vidí jen `502 BadGateway / NoResponse`
    (PPF DEV 31.08.2026: ExportFlow/Cesta_webu v 1.0.0.69,
    MapaPublishFlow/Sablona v 1.0.0.70).

    Platí to i pro odkaz, který je celou hodnotou parametru konektoru
    (`dataset`, `table`) — tam to chvíli vypadalo, že deklarace potřeba není,
    protože balík 1.0.0.63 běžel úplně bez deklarací. Rozdíl je nejspíš v tom,
    že prostředí parametry samo doplní jen flow, které nedeklaruje ŽÁDNÝ;
    jakmile jeden přibude, platí deklarace jako úplný výčet. Na tom stavět
    nechceme, takže se deklarují všechny.

    `defaultValue` se ZÁMĚRNĚ nedoplňuje — hodnota patří do prostředí jako
    Current Value. Ověřeno 31.08.2026 v provozu: bez ní to funguje, a balík
    tím nemusí vézt adresu žádného tenantu. Zároveň se zahazuje hodnota,
    kterou do exportu dopsal designer (export z MPSV nesl adresu tamního webu).
    """
    doplnene = []
    for cesta in sorted((solution_dir / "Workflows").glob("*.json")):
        data = json.loads(cesta.read_text(encoding="utf-8-sig"))
        definice = data["properties"]["definition"]
        parametry = definice.setdefault("parameters", {})

        pouzite = set(re.findall(r"parameters\('([^']+)'\)",
                                 json.dumps(definice, ensure_ascii=False)))
        flow = cesta.name.split("-")[0]
        for klic in sorted(pouzite):
            if klic.startswith("$"):
                continue
            schema = env_promenne.schema_z_klice(klic)
            if schema is None:
                raise SystemExit(
                    f"CHYBA: {flow} se odkazuje na parametr {klic!r}, který "
                    f"neodpovídá žádné proměnné v env_promenne.py")
            if klic not in parametry:
                parametry[klic] = env_promenne.deklarace(schema)
                doplnene.append(f"{flow}/{schema}")

        for nazev, popis in parametry.items():
            if not nazev.startswith("$") and isinstance(popis, dict):
                popis.pop("defaultValue", None)

        cesta.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return doplnene


def dokonci(solution_dir, verze):
    """Přepíše verzi v manifestu a složí solution zip."""
    napojene, odebrane = napoj_appku_na_promenne(solution_dir)
    print(f"napojení appky přes proměnné: {len(napojene)} zdrojů ({', '.join(napojene)})")
    if odebrane:
        print(f"  odebrané nepoužívané zdroje: {', '.join(sorted(set(odebrane)))}")
    doplnene = dorovnej_deklarace_parametru(solution_dir)
    print(f"deklarace parametrů ve flow: doplněno {len(doplnene)}"
          + (f" ({', '.join(doplnene)})" if doplnene else ""))
    pocet = zkontroluj_flow_kratky_nazev(solution_dir)
    print(f"flow — povinná pole zápisu ověřena ({pocet}), žádné z triggeru")

    manifest = solution_dir / "solution.xml"
    text = manifest.read_text(encoding="utf-8-sig")
    novy, pocet = re.subn(r"<Version>[^<]+</Version>", f"<Version>{verze}</Version>", text, count=1)
    if pocet != 1:
        raise SystemExit("CHYBA: verzi v solution.xml se nepodařilo přepsat")
    manifest.write_text(novy, encoding="utf-8")

    # AppVersion canvas appky musí růst spolu s verzí solution. Když zůstane
    # z původního exportu, import projde, Studio ukáže nový obsah, ale
    # PUBLIKOVANÁ verze pro hráče se neaktualizuje — appka se tváří jako
    # nezměněná. Navenek to vypadá jako „publish nefunguje": ve Versions je
    # Live, odkaz i cache v pořádku, a přesto se hráčům servíruje stará verze.
    # (Zjištěno 21.08.2026 na 1.0.0.26.)
    customizations = solution_dir / "customizations.xml"
    if customizations.exists():
        text = customizations.read_text(encoding="utf-8-sig")
        razitko = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        novy, pocet = re.subn(r"<AppVersion>[^<]+</AppVersion>",
                              f"<AppVersion>{razitko}</AppVersion>", text, count=1)
        if pocet != 1:
            raise SystemExit("CHYBA: AppVersion canvas appky se nepodařilo přepsat")
        customizations.write_text(novy, encoding="utf-8")
        print(f"AppVersion canvas appky: {razitko}")

    # Proměnné prostředí, ze kterých flow berou web a listy. Vkládají se tady,
    # tedy do každého balíku — kdyby definice chyběla, odkaz @parameters ve flow
    # by se neměl na co navázat a flow by po importu nešlo zapnout.
    vlozene, smazane = env_promenne.vloz_do_slozky(solution_dir, verze)
    print(f"proměnné prostředí: {len(vlozene)} definic ({', '.join(vlozene)})")
    for soubor in smazane:
        print(f"  odstraněno z balíku: {soubor}")

    VYSTUP.mkdir(parents=True, exist_ok=True)
    vystupni_zip = VYSTUP / f"procesnimapa_{verze.replace('.', '_')}.zip"
    zabal(solution_dir, vystupni_zip)

    print(f"\nHOTOVO: {vystupni_zip}  ({vystupni_zip.stat().st_size} B), verze {verze}")
    print("Import: Power Apps > Solutions > Import solution (upgrade). Po importu appku")
    print("jednou otevřít v Power Apps Studiu — z YAML zabalená appka se validuje až tam.")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", default=str(VYCHOZI_SOLUTION), help="vstupní solution zip z Power Apps")
    parser.add_argument("--verze", default="1.0.0.2", help="verze výsledné solution")
    parser.add_argument("--pac", default=None, help="cesta k pac.exe")
    parser.add_argument("--bez-pac", action="store_true",
                        help="vyměnit YAML přímo v už zabaleném balíku (stroj bez pac)")
    argumenty = parser.parse_args()

    vstupni_zip = Path(argumenty.solution)
    if not vstupni_zip.exists():
        raise SystemExit(f"CHYBA: solution {vstupni_zip} neexistuje")

    pac = None
    if not argumenty.bez_pac:
        pac = najdi_pac(argumenty.pac)
        if pac is None or not pac.exists():
            raise SystemExit(
                "CHYBA: pac.exe nenalezen. Nainstaluj rozšíření Power Platform Tools do VS Code\n"
                "       (code --install-extension microsoft-IsvExpTools.powerplatform-vscode)\n"
                "       nebo předej cestu přes --pac / PAC_EXE.\n"
                "       Máš-li balík už zabalený z YAML, jde použít --bez-pac."
            )
        print(f"pac: {pac}")

    if PRACOVNI.exists():
        for polozka in PRACOVNI.iterdir():
            if polozka.name != "pac":
                shutil.rmtree(polozka) if polozka.is_dir() else polozka.unlink()
    PRACOVNI.mkdir(parents=True, exist_ok=True)

    solution_dir = PRACOVNI / "solution"
    rozbal(vstupni_zip, solution_dir)

    msappy = list((solution_dir / "CanvasApps").glob("*.msapp"))
    if len(msappy) != 1:
        raise SystemExit(f"CHYBA: čekal jsem právě jeden .msapp, našel {len(msappy)}")
    msapp = msappy[0]
    print(f"canvas app: {msapp.name}")

    if argumenty.bez_pac:
        vlozeno = vymen_zdroje_bez_pac(msapp, argumenty.verze)
        print(f"vloženo zdrojů (bez pac): {vlozeno}")
        puvodni_limit = nastav_limit_radku(msapp)
        if puvodni_limit is not None:
            print(f"strop načítaných řádků: {puvodni_limit} -> {MAX_RADKU}")
        odstraneno = odstran_duchy(msapp)
        if odstraneno:
            print(f"odstraněné zbytky zrušených obrazovek: {', '.join(odstraneno)}")
        doplneno = doplnit_sablony(msapp)
        if doplneno:
            print(f"doplněné šablony controlů: {', '.join(doplneno)}")
        odebrane_zdroje = odeber_nepouzivane_zdroje(msapp)
        if odebrane_zdroje:
            print(f"odebrané nepoužívané zdroje z appky: {', '.join(odebrane_zdroje)}")
        return dokonci(solution_dir, argumenty.verze)

    zdroje = PRACOVNI / "sources"
    spust([str(pac), "canvas", "unpack", "--msapp", str(msapp),
           "--sources", str(zdroje), "--layout", "SourceCode"])

    src_dir = zdroje / "Src"
    for stara in src_dir.glob("*.pa.yaml"):
        if stara.name != "_EditorState.pa.yaml":
            stara.unlink()

    for nazev in ["App"] + OBRAZOVKY:
        shutil.copy(APP_SRC / f"{nazev}.pa.yaml", src_dir / f"{nazev}.pa.yaml")
    vloz_verzi(src_dir / "App.pa.yaml", argumenty.verze)
    print(f"vloženo zdrojů: {len(OBRAZOVKY) + 1}, razítko verze {argumenty.verze}")

    stav = src_dir / "_EditorState.pa.yaml"
    text = stav.read_text(encoding="utf-8-sig")
    poradi = "  ScreensOrder:\n" + "".join(f"    - {o}\n" for o in OBRAZOVKY)
    novy, pocet = re.subn(r"  ScreensOrder:\n(?:    - .*\n)+", poradi, text)
    if pocet != 1:
        raise SystemExit(f"CHYBA: ScreensOrder nahrazen {pocet}x, čekal jsem 1x")
    stav.write_text(novy, encoding="utf-8")

    novy_msapp = PRACOVNI / "app.msapp"
    vystup_pac = spust([str(pac), "canvas", "pack", "--sources", str(zdroje), "--msapp", str(novy_msapp)])
    print(vystup_pac.strip().splitlines()[-1])

    puvodni_limit = nastav_limit_radku(novy_msapp)
    if puvodni_limit is not None:
        print(f"strop načítaných řádků: {puvodni_limit} -> {MAX_RADKU}")

    odstraneno = odstran_duchy(novy_msapp)
    if odstraneno:
        print(f"odstraněné zbytky zrušených obrazovek: {', '.join(odstraneno)}")

    doplneno = doplnit_sablony(novy_msapp)
    if doplneno:
        print(f"doplněné šablony controlů: {', '.join(doplneno)}")

    odebrane_zdroje = odeber_nepouzivane_zdroje(novy_msapp)
    if odebrane_zdroje:
        print(f"odebrané nepoužívané zdroje z appky: {', '.join(odebrane_zdroje)}")

    shutil.copy(novy_msapp, msapp)

    return dokonci(solution_dir, argumenty.verze)


if __name__ == "__main__":
    sys.exit(main())
