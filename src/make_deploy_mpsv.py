# -*- coding: utf-8 -*-
"""Sestaví deploy/mpsv/ — všechno, co je potřeba k nasazení na tenant MPSV.

Složka se **generuje**, neudržuje ručně: jinak by po první změně schématu
nebo appky obsahovala starou verzi a nikdo by to nepoznal, protože soubory
uvnitř vypadají pořád stejně.

Obsah:
  README.md              postup krok za krokem
  01_zaloz_listy.js      provisioning listů a sloupců (do konzole prohlížeče)
  02_import_dat.js       import OSTRÝCH dat z runs/normalize
  03_vypis_guidy.js      vypíše GUIDy listů pro src/build_flow.py
  sharepoint_schema.md   dokumentace schématu
  procesnimapa_*.zip     poslední solution balík

Spouštět z kořene projektu:
    python src/make_deploy_mpsv.py
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

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


def readme(pocty, balik, listy):
    prehled = "\n".join(f"| `{n}` | {p} |" for n, p in pocty)
    return f"""# Nasazení na tenant MPSV — postup

Tahle složka se **generuje** skriptem `src/make_deploy_mpsv.py`. Neupravuj
soubory v ní ručně — po příští změně schématu nebo appky se přepíšou.

Balík appky: **`{balik.name}`**

## Co se bude importovat

Ostrá data z `runs/normalize/` (ne anonymizovaná):

| tabulka | položek |
|---|---|
{prehled}

## Postup

Kroky **1–3** se dělají v prohlížeči na cílovém webu MPSV, kroky **4–8**
v Power Apps a lokálně. Pořadí není libovolné: appka musí být připojená
na web MPSV dřív, než se přegenerují flow.

### 1. Založit listy a sloupce

Otevři cílový web MPSV, dej **F12 → Console**, vlož celý obsah
`01_zaloz_listy.js` a spusť.

Skript je **idempotentní** — co existuje, nezakládá znovu; co chybí, doplní;
sloupce, které nejsou ve výchozím zobrazení, do něj přidá. Na konci vypíše
tabulku se stavem každého sloupce.

**Ověření:** poslední řádek výpisu musí říct, že chybných sloupců je 0.
Struktura listů je popsaná v `sharepoint_schema.md`.

### 2. Naimportovat ostrá data

Tamtéž vlož `02_import_dat.js`.

Skript je také idempotentní — položku pozná podle identifikačního kódu
(sloupec `Title`), takže opakované spuštění nezaloží duplicity.

**Ověření:** počty na konci výpisu musí sedět s tabulkou výše.

> **Pozor:** tenhle soubor obsahuje **neanonymizovaná** data — jména útvarů,
> vnitřní předpisy a znění činností. Do cizího vývojového tenantu nepatří.

### 3. Vypsat GUIDy listů

Vlož `03_vypis_guidy.js`. Vypíše GUID každého listu rejstříku; zapiš si
GUID listu **Aktivity**, potřebuješ ho v kroku 7.

### 4. Naimportovat solution a zapnout flow

Power Apps → **Solutions → Import solution** → `{balik.name}`
(unmanaged, jako upgrade).

Po importu **ručně zapni všechna čtyři flow** — import stav zapnutí nemění
a vypnuté flow se projeví jako chyba appky, ne flow:

- `MapaPublishFlow` — publikace HTML mapy z tlačítka,
- `MapaPublishScheduled` — táž publikace denně v 7:00,
- `ExportFlow` — export přehledu do Wordu a Excelu,
- `AktualizaceKratkehoNazvu` — zkrácený název aktivity.

### 5. Přepojit appku na web MPSV a zaregistrovat flow

Otevři appku v **Power Apps Studiu**:

1. datové zdroje přepni na listy na webu MPSV,
2. **Add data → ExportFlow** — bez toho se `ExportFlow.Run()` nemá na co
   navázat; `FlowNameId` přiděluje až cílové prostředí a lokálně se
   dogenerovat nedá,
3. **mikro-změna** (posunout prvek o pixel a vrátit) → **Save** → **Publish**,
4. **Export solution** (unmanaged) a ulož si zip.

### 6. Přegenerovat flow lokálně

Adresa webu a GUIDy listů jsou v definicích flow na 19 místech. **Nepřepisují
se ručně** — build skripty si je vezmou z připojení appky v exportovaném zipu:

```powershell
$py = ".venv/Scripts/python.exe"
& $py src/build_mapa_flow.py   --solution <exportovany_zip>
& $py src/build_export_flow.py --solution <exportovany_zip>
& $py src/add_mapa_schedule.py --solution <exportovany_zip>
```

### 7. Ručně dorovnat `AktualizaceKratkehoNazvu`

Jediné flow, které se rerunem nespraví — jeho trigger je nad konkrétním
listem:

1. v `src/build_flow.py` přepiš konstantu `LIST_AKTIVITY` na GUID listu
   Aktivity z kroku 3 (runtime výraz tam nejde: flow by se naimportovalo,
   ale nešlo zapnout),
2. v Power Automate designeru nad webem MPSV založ novou kostru — trigger
   *When an item is created or modified* nad listem Aktivity + jedna akce
   *Compose* — a exportuj ji,
3. `& $py src/build_flow.py --solution <zip_s_kostrou>` doplní zbytek.

### 8. Adresa mapy, sestavení a kontrola

1. v `src/app_src/App.pa.yaml` přepiš `varMapaUrl` na adresu publikované
   mapy na webu MPSV (jediné ručně psané místo — canvas app umí číst jen
   datasetové proměnné prostředí, textové ne),
2. sestav a zkontroluj:

```powershell
& $py src/build_app.py --solution <exportovany_zip> --verze <nova_verze>
& $py src/build_export_flow.py --solution deploy/procesnimapa_<verze>.zip
& $py src/check_solution.py --vstup <exportovany_zip> --vystup deploy/procesnimapa_<verze>.zip
& $py src/check_export_flow.py --solution deploy/procesnimapa_<verze>.zip
& $py src/check_mapa_flow.py   --solution deploy/procesnimapa_<verze>.zip
& $py src/check_flow.py        --solution deploy/procesnimapa_<verze>.zip
& $py src/check_app.py
```

`check_solution.py` **selže**, dokud některé flow míří na jiný web než appka —
je to hlavní pojistka proti nedodělanému přenosu.

3. výsledný balík naimportuj, flow zapni a ve Studiu znovu **mikro-změna →
   Save → Publish**.

### 9. Ověření, že to běží

- najeď myší na název **Procesní mapa MPSV** v modrém pruhu — nápověda musí
  ukázat verzi, kterou jsi právě naimportoval. Když se neukáže vůbec nebo
  číslo nesedí, neproběhl krok Save + Publish,
- na Přehledu musí karty ukazovat počty z tabulky výše,
- **Export → Do Wordu** a **Do Excelu** musí vyrobit soubor v Site Assets,
- **HTML mapa → Obnovit HTML** musí doběhnout a **Zobrazit v HTML** otevřít
  mapu s reálnými daty.

## Co v téhle složce záměrně není

- **Anonymizovaná data** — ta jsou v `runs/anonym/` a patří do vývojového
  tenantu, ne sem.
- **Šablona mapy** `mapa_template.html` — nahrává se do knihovny Site Assets
  webu MPSV; postup je v `deploy/navod_publikace_mapy.md`.
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

    shutil.copy("deploy/sharepoint_schema.md", CIL / "sharepoint_schema.md")
    balik = posledni_balik()
    for stary in CIL.glob("procesnimapa_*.zip"):
        stary.unlink()
    shutil.copy(balik, CIL / balik.name)

    model = json.loads((DATA / "model.json").read_text(encoding="utf-8"))
    pocty = [(k, len(v)) for k, v in model.items() if isinstance(v, list)]
    (CIL / "README.md").write_text(readme(pocty, balik, nazvy), encoding="utf-8")

    print(f"\nHOTOVO: {CIL}")
    for cesta in sorted(CIL.iterdir()):
        print(f"  {cesta.name:28} {cesta.stat().st_size:>9} B")
    print(f"\nbalík appky: {balik.name}")
    print("POZOR: 02_import_dat.js nese NEANONYMIZOVANÁ data — jen na tenant MPSV")
    return 0


if __name__ == "__main__":
    sys.exit(main())
