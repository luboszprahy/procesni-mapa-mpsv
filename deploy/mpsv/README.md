# Nasazení na tenant MPSV — postup

Tahle složka se **generuje** skriptem `src/make_deploy_mpsv.py`. Neupravuj
soubory v ní ručně — po příští změně schématu nebo appky se přepíšou.

Balík appky: **`procesnimapa_1_0_0_64.zip`**

## Co se bude importovat

Ostrá data z `runs/normalize/` (ne anonymizovaná):

| tabulka | položek |
|---|---|
| `agendy` | 7 |
| `procesy` | 46 |
| `dilci_procesy` | 250 |
| `aktivity` | 46 |
| `vazby` | 46 |

## Jak se balík napojuje na SharePoint

Od verze 1.0.0.62 **nemají flow adresu webu ani GUIDy listů natvrdo** — berou
je z proměnných prostředí, které vyplníš v průvodci importem. Do 1.0.0.61 tam
byly natvrdo a import na MPSV právě na tom padl: web PPF tam neexistuje, akce
jsou neplatné, flow nejde zapnout a designer list ani nenabídne k přepnutí.

| proměnná | zobrazí se jako | vybírá se |
|---|---|---|
| `mpsv_procesnimapaSite` | Procesni mapa - web | web |
| `mpsv_listAgendy` | Procesni mapa - Agendy | list |
| `mpsv_listProcesy` | Procesni mapa - Procesy | list |
| `mpsv_listDilciProcesy` | Procesni mapa - Dilci procesy | list |
| `mpsv_listAktivity` | Procesni mapa - Aktivity | list |
| `mpsv_listVazby` | Procesni mapa - Vazby | list |

Definice **nemají výchozí hodnotu** schválně. Kdyby ji měly, průvodce by je
předvyplnil adresou vývojového webu a import by tiše prošel se špatným
napojením. Takhle se musí vyplnit vědomě. Prostředí si hodnoty po prvním
vyplnění drží — další import už se neptá.

## Postup

Kroky **1–2** se dělají v prohlížeči na cílovém webu MPSV, zbytek v Power Apps
a lokálně.

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

`03_vypis_guidy.js` je nepovinný — vypíše GUID každého listu. Od 1.0.0.62 ho
build nepotřebuje (listy se vybírají v průvodci), hodí se jen ke kontrole,
že listy vznikly.

### 3. Naimportovat solution a VYPLNIT PROMĚNNÉ

Power Apps → **Solutions → Import solution** → `procesnimapa_1_0_0_64.zip`
(unmanaged, jako upgrade).

Průvodce se postupně zeptá na:

1. **připojení** (connection reference na SharePoint) — vyber nebo založ
   připojení v tenantu MPSV,
2. **šest proměnných** z tabulky výše. U `mpsv_procesnimapaSite` zadej adresu webu MPSV;
   ostatních pět se pak vybírá **z rozbalovátka listů toho webu**.

> **Průvodce neproklikávej.** Proměnná bez hodnoty se neprojeví při importu,
> ale až tím, že flow nejde zapnout — a vypadá to jako chyba balíku.

### 4. Zapnout všechna čtyři flow

Import **stav zapnutí nemění**, takže po každém importu:

- `MapaPublishFlow` — publikace HTML mapy z tlačítka,
- `MapaPublishScheduled` — táž publikace denně v 7:00,
- `ExportFlow` — export přehledu do Wordu a Excelu,
- `AktualizaceKratkehoNazvu` — zkrácený název aktivity.

Vypnuté flow se projeví jako chyba appky, ne flow.

### 5. Přepojit appku a zaregistrovat flow

Flow už jsou hotová, ale **canvas app se na proměnné zatím nepřevedla** — drží
web a GUIDy listů ve svém napojení. Otevři ji v **Power Apps Studiu**:

1. datové zdroje přepni na listy na webu MPSV,
2. **Add data → ExportFlow** — bez toho se `ExportFlow.Run()` nemá na co
   navázat; `FlowNameId` přiděluje až cílové prostředí a lokálně se
   dogenerovat nedá,
3. **mikro-změna** (posunout prvek o pixel a vrátit) → **Save** → **Publish**,
4. **Export solution** (unmanaged) a ulož si zip.

### 6. Adresa mapy, sestavení a kontrola

`varMapaUrl` je jediné ručně psané místo s adresou — canvas app umí číst jen
datasetové proměnné prostředí, textové ne.

1. v `src/app_src/App.pa.yaml` přepiš `varMapaUrl` na adresu publikované mapy
   na webu MPSV,
2. sestav a zkontroluj:

```powershell
$py = ".venv/Scripts/python.exe"
& $py src/build_app.py --solution <exportovany_zip> --verze <nova_verze>
& $py src/check_solution.py --vstup <exportovany_zip> --vystup deploy/procesnimapa_<verze>.zip
& $py src/check_env.py
& $py src/check_app.py
& $py src/check_export_flow.py --solution deploy/procesnimapa_<verze>.zip
& $py src/check_mapa_flow.py   --solution deploy/procesnimapa_<verze>.zip
& $py src/check_flow.py        --solution deploy/procesnimapa_<verze>.zip
```

Flow se **znovu negenerují** — jsou přenositelná. Build skripty se pouští jen
tehdy, když se mění jejich logika.

`check_solution.py` **selže**, jakmile se do některého flow vrátí adresa webu
nebo GUID listu — je to hlavní pojistka proti opakování dnešní chyby.

3. výsledný balík naimportuj, flow zapni a ve Studiu znovu **mikro-změna →
   Save → Publish**.

### 7. Ověření, že to běží

- najeď myší na název **Procesní mapa MPSV** v modrém pruhu — nápověda musí
  ukázat verzi, kterou jsi právě naimportoval. Když se neukáže vůbec nebo
  číslo nesedí, neproběhl krok Save + Publish,
- na Přehledu musí karty ukazovat počty z tabulky výše,
- **Export → Do Wordu** a **Do Excelu** musí vyrobit soubor v Site Assets,
- **HTML mapa → Obnovit HTML** musí doběhnout a **Zobrazit v HTML** otevřít
  mapu s reálnými daty,
- uprav název aktivity a zkontroluj, že se zkrácený název srovnal — tím je
  ověřené i čtvrté flow.

## Co v téhle složce záměrně není

- **Anonymizovaná data** — ta jsou v `runs/anonym/` a patří do vývojového
  tenantu, ne sem.
- **Šablona mapy** `mapa_template.html` — nahrává se do knihovny Site Assets
  webu MPSV; postup je v `deploy/navod_publikace_mapy.md`.
