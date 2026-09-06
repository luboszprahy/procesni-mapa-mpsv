# -*- coding: utf-8 -*-
"""Sestaví deploy/mpsv/ — všechno, co je potřeba k nasazení na tenant MPSV.

Složka se **generuje**, neudržuje ručně: jinak by po první změně schématu
nebo appky obsahovala starou verzi a nikdo by to nepoznal, protože soubory
uvnitř vypadají pořád stejně.

Obsah:
  README.md                    postup krok za krokem
  01_zaloz_listy.js            provisioning listů, sloupců a knihoven
  02_import_dat.js             import OSTRÝCH dat z runs/normalize
  03_vypis_guidy.js            vypíše GUIDy listů (nepovinné, jen kontrola)
  procesnimapa_*.zip           poslední solution balík
  site_assets/                 soubory k nahrání do knihovny Site Assets
  sharepoint_schema.md         dokumentace schématu
  navod_sprava.md              jak appku používat (pro správce rejstříku)
  navod_publikace_mapy.md      HTML mapa a její publikace
  TESTOVACI_SCENAR.md          přejímka po nasazení, bod po bodu
  flow_*.md                    kontrakty jednotlivých flow

Spouštět z kořene projektu:
    python src/make_deploy_mpsv.py
"""

import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402

KOREN = Path(".")
CIL = Path("deploy/mpsv")
DATA = Path("runs/normalize")
PY = Path(".venv/Scripts/python.exe")

VYPIS_GUIDU = """// Vypíše GUIDy listů rejstříku — potřebné pro src/build_flow.py.
// Vložit do konzole prohlížeče (F12) na stránce cílového webu MPSV.
// Jen čte, nic nemění.
(async () => {
  const web = location.pathname.replace(/\\/(SitePages|Lists|_layouts)\\/.*$/i, "")
                              .replace(/\\/$/, "");
  const api = (cesta) =>
    fetch(web + "/_api/" + cesta, {
      headers: { Accept: "application/json;odata=nometadata" },
      credentials: "same-origin",
    }).then((r) => r.json());

  const data = await api("web/lists?$select=Title,Id,ItemCount&$filter=Hidden eq false");
  const radky = data.value
    .filter((l) => %s.includes(l.Title))
    .map((l) => ({ list: l.Title, GUID: l.Id, polozek: l.ItemCount }));
  console.log("web: " + web);
  console.table(radky);
  console.log(
    radky.length === %d
      ? "OK - nalezeny vsechny listy rejstriku"
      : "POZOR - ceka se " + %d + " listu, nalezeno " + radky.length
  );
})();
"""


def spust(prikaz):
    vysledek = subprocess.run(prikaz, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    if vysledek.returncode != 0:
        print(vysledek.stdout)
        print(vysledek.stderr, file=sys.stderr)
        raise SystemExit(f"CHYBA: selhalo {' '.join(prikaz[1:3])}")
    return vysledek.stdout


def posledni_balik():
    baliky = sorted(Path("deploy").glob("procesnimapa_*.zip"),
                    key=lambda p: [int(c) for c in re.findall(r"\d+", p.stem)])
    if not baliky:
        raise SystemExit("CHYBA: v deploy/ není žádný solution balík")
    return baliky[-1]


def overuj_bez_guidu(balik):
    """Ve flow nesmí být GUID listu natvrdo — balík musí platit pro každý tenant.

    Do 1.0.0.97 měl `AktualizaceKratkehoNazvu` GUID listu Aktivity natvrdo
    (PatchItem runtime výraz nesnese) a `posledni_balik()` bere prostě nejvyšší
    verzi — ta bývá pro PPF DEV, na kterém se vyvíjí. Na MPSV pak flow nešlo
    zapnout: GetTable vrátil 404 "List not found" (05.09.2026, balík 1.0.0.96;
    totéž 28.08.). Od F14 se zapisuje REST MERGE a GUID v balíku nemá být žádný;
    tahle brána hlídá, že se tam nevrátí.
    """
    nalezy = []
    with zipfile.ZipFile(balik) as zip_balik:
        for jmeno in zip_balik.namelist():
            if not jmeno.replace("\\", "/").startswith("Workflows/"):
                continue
            definice = zip_balik.read(jmeno).decode("utf-8-sig")
            guidy = sorted(set(re.findall(
                r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", definice)))
            if guidy:
                nalezy.append(f"{jmeno.split('/')[-1]}: {', '.join(guidy[:2])}")
    if nalezy:
        raise SystemExit(
            f"CHYBA: {balik.name} nese ve flow GUID natvrdo, takže platí jen pro "
            f"jeden tenant:\n  " + "\n  ".join(nalezy))


# co flow dělá a čím se spouští — do tabulky v README
FLOW = {
    "MapaPublishFlow": ("publikace HTML mapy se zapečenými daty", "z appky"),
    "MapaPublishScheduled": ("táž publikace", "denně 7:00"),
    "ExportFlow": ("export přehledu do Wordu a Excelu, adresy souborů", "z appky"),
    "AktualizaceKratkehoNazvu": ("zkrácený název aktivity", "změna v listu"),
    "ZalohaFlow": ("snímek rejstříku do knihovny Zalohy", "z appky"),
    "ZalohaScheduled": ("týž snímek", "denně 5:00"),
    "RestoreFlow": ("obnova rejstříku ze snímku", "z appky"),
    "ImportFlow": ("hromadné pořízení aktivit z Excelu", "z appky"),
    "PresunFlow": ("kaskádový přesun procesu a dílčího procesu", "z appky"),
}

# flow, které appka volá přes Flow.Run() — musí se zaregistrovat ve Studiu
VOLANA_Z_APPKY = ["MapaPublishFlow", "ExportFlow", "ZalohaFlow", "ImportFlow",
                  "RestoreFlow", "PresunFlow"]


def readme(pocty, balik, listy, flow, obrazovky):
    prehled = "\n".join(f"| `{n}` | {p} |" for n, p in pocty)
    promenne = "\n".join(
        f"| `{schema}` | {nazev} | {'adresa webu' if klic == 'dataset' else 'list z rozbalovátka'} |"
        for schema, nazev, _, klic, _ in ep.DEFINICE)
    tabulka_flow = "\n".join(
        f"| `{f}` | {FLOW.get(f, ('—', '—'))[0]} | {FLOW.get(f, ('—', '—'))[1]} |"
        for f in flow)
    registrace = ", ".join(f"`{f}`" for f in VOLANA_Z_APPKY)
    return f"""# Nasazení na tenant MPSV — postup

Tahle složka se **generuje** skriptem `src/make_deploy_mpsv.py`. Neupravuj
soubory v ní ručně — po příští změně schématu nebo appky se přepíšou.

Balík appky: **`{balik.name}`** · {len(flow)} flow · {obrazovky} obrazovek ·
{len(ep.DEFINICE)} proměnných prostředí

Postup má osm kroků a **pořadí je závazné**. Každý krok má vlastní ověření;
další začni, až předchozí projde.

## Co se bude importovat

Ostrá data z `runs/normalize/` (ne anonymizovaná):

| tabulka | položek |
|---|---|
{prehled}

> **`02_import_dat.js` nese neanonymizovaná data** — jména útvarů, vnitřní
> předpisy a znění činností. Do cizího vývojového tenantu nepatří.

## Jak se balík napojuje na SharePoint

Flow **nemají adresu webu ani GUIDy listů natvrdo** — berou je z proměnných
prostředí, které vyplníš v průvodci importem. Do 1.0.0.61 tam byly natvrdo
a nasazení na MPSV právě na tom padlo: web PPF v cílovém tenantu neexistuje,
akce jsou neplatné a flow nejde zapnout.

| proměnná | zobrazí se jako | vybírá se |
|---|---|---|
{promenne}

Definice **nemají výchozí hodnotu** schválně. Kdyby ji měly, průvodce by je
předvyplnil adresou vývojového webu a import by tiše prošel se špatným
napojením — flow by pak celé týdny běhalo zeleně nad cizími daty.

---

## 1. Založit listy, sloupce a knihovny

Otevři cílový web MPSV, dej **F12 → Console**, vlož celý obsah
`01_zaloz_listy.js` a spusť. Skript si web odvodí z adresy stránky, na které
běží — žádnou URL v sobě nemá.

Založí listy rejstříku a knihovny **`Zalohy`**, **`Exporty`** a **`Import`**.
Je **idempotentní**: co existuje, nezakládá znovu; co chybí, doplní; sloupce
mimo výchozí zobrazení do něj přidá.

**Krok 1 musí být před importem solution.** Průvodce importem nabízí u každé
listové proměnné rozbalovátko listů cílového webu — když list ještě
neexistuje, není co vybrat, proměnná zůstane prázdná a to shodí napojení
**celé** SharePoint connection, tedy i listů, které s ní nesouvisejí. Projeví
se to jako `We didn't find any datasets` při startu appky a vypadá to jako
vada balíku.

**Ověření:** poslední řádek výpisu říká, že chybných sloupců je **0**;
v *Site contents* jsou vidět knihovny `Zálohy`, `Exporty`, `Import` a list
`Historie kódů`. Struktura je popsaná v `sharepoint_schema.md`.

## 2. Naimportovat ostrá data

Tamtéž vlož `02_import_dat.js`. Skript je idempotentní — položku pozná podle
identifikačního kódu (sloupec `Title`), takže opakované spuštění nezaloží
duplicity.

**Ověření:** počty na konci výpisu sedí s tabulkou výše.

`03_vypis_guidy.js` je nepovinný — vypíše GUID každého listu. Build ho
nepotřebuje (listy se vybírají v průvodci), hodí se jen ke kontrole.

## 3. Naimportovat solution a VYPLNIT VŠECH {len(ep.DEFINICE)} PROMĚNNÝCH

Power Apps → **Solutions → Import solution** → `{balik.name}`
(unmanaged). Průvodce se zeptá na:

1. **připojení** (connection reference na SharePoint) — vyber nebo založ
   připojení v tenantu MPSV,
2. **{len(ep.DEFINICE)} proměnných** z tabulky výše. U `{ep.WEB}` zadej adresu webu MPSV,
   ostatní se pak vybírají z rozbalovátka listů toho webu.

> **Průvodce neproklikávej.** Prázdná proměnná se při importu neprojeví —
> projeví se až tím, že flow nejde zapnout, a vypadá to jako vada balíku.

## 4. Zapnout všechna flow

**Import stav zapnutí nemění.** Flow, které se jednou nepodařilo zapnout,
zůstane vypnuté i po importu opravené verze.

| flow | co dělá | trigger |
|---|---|---|
{tabulka_flow}

Vypnuté flow se projeví jako chyba **appky**, ne flow: canvas app vidí jen
`502 BadGateway / NoResponse` a příčinu z toho poznat nejde — ta je v run
history.

**Ověření:** všech {len(flow)} má stav *On*.

## 5. Nahrát soubory do Site Assets

Ze složky `site_assets/` přetáhni do knihovny **Site Assets** cílového webu:

| soubor | k čemu |
|---|---|
| `mapa_template.html` | šablona s kotvami, ze které flow skládá stránku |
| `procesni_mapa.html` | hotová mapa, aby bylo co otevřít, než flow poprvé proběhne |
| `sablona_import_aktivit.xlsx` | prázdný sešit pro hromadný import |

Sešit se **musí jmenovat přesně takhle** — `ExportFlow` skládá jeho adresu
z názvu, ne vyhledáním souboru.

Účet, pod kterým flow běží, potřebuje **Contribute** na `Site Assets`,
`Zalohy`, `Exporty` a `Import`.

**Ověření:** `MapaPublishFlow` doběhne zeleně a `procesni_mapa.html` se
přepíše aktuálním časem.

## 6. Přepojit appku a zaregistrovat flow (kolo 1)

Flow jsou přenositelná, ale **canvas app se na proměnné nepřevádí** — drží
napojení na konkrétní listy a volání flow na jejich `FlowNameId`, které
přiděluje až cílové prostředí. Lokálně to dogenerovat nejde. Ve **Studiu**:

1. datové zdroje přepni na listy na webu MPSV,
2. **Add data** → {registrace},
3. **mikro-změna** (posunout prvek o pixel a vrátit) → **Save** → **Publish**,
4. **Export solution** (unmanaged) a ten zip si ulož.

Bez kroku 3 vidí ostatní pořád předchozí verzi appky, i když import proběhl;
navíc se appka zabalená z YAML validuje až tady (App checker musí být čistý).

## 7. Adresa mapy a přestavení balíku (kolo 2)

`varMapaUrl` je jediné ručně psané místo s adresou — canvas app umí číst jen
datasetové proměnné prostředí, textové ne.

1. v `src/app_src/App.pa.yaml` přepiš `varMapaUrl` na adresu publikované mapy
   na webu MPSV,
2. sestav a zkontroluj (z kořene projektu):

```powershell
$py = ".venv/Scripts/python.exe"
& $py src/build_app.py --solution <zip_z_kroku_6> --verze <nova_verze>
& $py src/check_solution.py --vstup <zip_z_kroku_6> --vystup deploy/procesnimapa_<verze>.zip
& $py src/check_app.py
& $py src/check_env.py
```

3. výsledný balík naimportuj, flow zapni a ve Studiu znovu **mikro-změna →
   Save → Publish**.

Flow se **znovu negenerují** — build skripty se pouštějí jen tehdy, když se
mění jejich logika. `check_solution.py` selže, jakmile by se do některého flow
vrátila adresa webu nebo GUID listu.

## 8. První záloha a přejímka

`ZalohaScheduled` poběží sám až v 5:00; první snímek si vynuť z appky:
**Data ▾ → Záloha rejstříku**.

**Ověření, na kterém záleží:** v knihovně `Zalohy` přibude
`rejstrik_<RRRR-MM-DD_HHMM>.json` a v něm má `listy.DilciProcesy`
**250 položek**, ne 100. Sto by znamenalo, že se nepropsalo stránkování —
běh je v tom případě zelený a snímek přesto oříznutý. Je to jediná vada
zálohy, která se jinak pozná až při obnově.

Pak projdi **`TESTOVACI_SCENAR.md`** — je to přejímka bod po bodu, včetně
toho, co se nesmí stát. Bloky, které mění data, jsou v něm označené.

---

## Když se něco nepovede

| příznak | kde je příčina |
|---|---|
| `We didn't find any datasets` při startu appky | nevyplněná Current Value některé proměnné (krok 3) |
| `Flow.Run failed: 502 BadGateway / NoResponse` | vypnuté flow (krok 4) nebo prázdná proměnná; pravdu řekne run history, ne hláška v appce |
| flow nejde zapnout | prázdná proměnná, nebo sirotek po starší solution v Default Solution (Turn off → Delete → Publish all customizations) |
| flow spadne na neexistující složce | neproběhl krok 1 — chybí knihovna `Zalohy`, `Exporty` nebo `Import` |
| import z Excelu: `403 OpenWorkbookAccessDenied` | sešit má citlivostní štítek, který ho šifruje. Štítek *Interní* projde, přísnější ne — přeštítkuj sešit. Není to chyba importu |
| Vzorová tabulka: stáhne se stránka s chybou místo sešitu | soubor není v Site Assets, nebo se jmenuje jinak (krok 5) |
| snímek má u `DilciProcesy` přesně 100 položek | nepropsalo se stránkování — nahlas to, je to vada balíku |
| appka ukazuje starou verzi | chybí mikro-změna → Save → Publish (krok 6) |
| v knihovně `Zálohy` ubývají staré snímky | tak to má být, nechává se posledních 20; snímek, který chceš udržet, přejmenuj |

## Co v téhle složce záměrně není

- **Anonymizovaná data** — jsou v `runs/anonym/` a patří do cizího vývojového
  tenantu, ne sem.
- **Zdrojové kódy a build skripty** — sada je pro nasazení, ne pro vývoj;
  ty jsou v repozitáři projektu.
"""


def main():
    if not (DATA / "model.json").exists():
        raise SystemExit(f"CHYBA: {DATA}/model.json neexistuje — spusť src/normalize.py")

    CIL.mkdir(parents=True, exist_ok=True)

    # 1) provisioning — týž skript jako pro vývojový tenant, web si odvodí z adresy
    spust([str(PY), "src/make_setup.py"])
    shutil.copy("src/setup_sharepoint.js", CIL / "01_zaloz_listy.js")

    # 2) import OSTRÝCH dat — jinam než na cílový tenant tenhle soubor nepatří
    spust([str(PY), "src/make_import.py", "--data", str(DATA),
           "--out", str(CIL / "02_import_dat.js"), "--povolit-realna-data"])

    # 3) výpis GUIDů listů pro build_flow.py
    schema = json.loads(Path("src/schema.json").read_text(encoding="utf-8"))
    # zobrazovaný název, ne interní — REST `lists` vrací Title
    nazvy = [l.get("display") or l["name"] for l in schema["lists"]]
    (CIL / "03_vypis_guidy.js").write_text(
        VYPIS_GUIDU % (json.dumps(nazvy, ensure_ascii=False), len(nazvy), len(nazvy)),
        encoding="utf-8")

    balik = posledni_balik()
    overuj_bez_guidu(balik)
    for stary in CIL.glob("procesnimapa_*.zip"):
        stary.unlink()
    shutil.copy(balik, CIL / balik.name)

    # dokumentace, kterou nasazující potřebuje u sebe, ne v repozitáři
    for jmeno in ("sharepoint_schema.md", "navod_sprava.md",
                  "navod_publikace_mapy.md", "TESTOVACI_SCENAR.md"):
        shutil.copy(f"deploy/{jmeno}", CIL / jmeno)
    for kontrakt in sorted(Path("deploy").glob("flow_*.md")):
        shutil.copy(kontrakt, CIL / kontrakt.name)

    # soubory do knihovny Site Assets — bez nich mapa ani import nefungují
    assets = CIL / "site_assets"
    shutil.rmtree(assets, ignore_errors=True)
    assets.mkdir()
    for jmeno in ("mapa_template.html", "procesni_mapa.html",
                  "sablona_import_aktivit.xlsx"):
        shutil.copy(f"deploy/{jmeno}", assets / jmeno)

    with zipfile.ZipFile(balik) as zip_balik:
        flow = sorted(n.split("/")[1].rsplit("-", 5)[0]
                      for n in zip_balik.namelist() if n.startswith("Workflows/"))
    obrazovky = len(list(Path("src/app_src").glob("scr_*.pa.yaml")))

    model = json.loads((DATA / "model.json").read_text(encoding="utf-8"))
    pocty = [(k, len(v)) for k, v in model.items() if isinstance(v, list)]
    (CIL / "README.md").write_text(
        readme(pocty, balik, nazvy, flow, obrazovky), encoding="utf-8")

    print(f"\nHOTOVO: {CIL}")
    for cesta in sorted(CIL.rglob("*")):
        if cesta.is_file():
            popis = str(cesta.relative_to(CIL)).replace("\\", "/")
            print(f"  {popis:34} {cesta.stat().st_size:>9} B")
    print(f"\nbalík appky: {balik.name}")
    print("POZOR: 02_import_dat.js nese NEANONYMIZOVANÁ data — jen na tenant MPSV")
    return 0


if __name__ == "__main__":
    sys.exit(main())
