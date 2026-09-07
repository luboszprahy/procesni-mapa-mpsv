# Nasazení na tenant MPSV — postup

Tahle složka se **generuje** skriptem `src/make_deploy_mpsv.py`. Neupravuj
soubory v ní ručně — po příští změně schématu nebo appky se přepíšou.

Balík appky: **`procesnimapa_1_0_0_101.zip`** · 9 flow · 6 obrazovek ·
9 proměnných prostředí

Postup má osm kroků a **pořadí je závazné**. Každý krok má vlastní ověření;
další začni, až předchozí projde.

## Co se bude importovat

Ostrá data z `runs/normalize/` (ne anonymizovaná):

| tabulka | položek |
|---|---|
| `agendy` | 7 |
| `procesy` | 46 |
| `dilci_procesy` | 250 |
| `aktivity` | 46 |
| `vazby` | 46 |

> **`02_import_dat.js` nese neanonymizovaná data** — jména útvarů, vnitřní
> předpisy a znění činností. Do cizího vývojového tenantu nepatří.

## Jak se balík napojuje na SharePoint

Flow **nemají adresu webu ani GUIDy listů natvrdo** — berou je z proměnných
prostředí, které vyplníš v průvodci importem. Do 1.0.0.61 tam byly natvrdo
a nasazení na MPSV právě na tom padlo: web PPF v cílovém tenantu neexistuje,
akce jsou neplatné a flow nejde zapnout.

| proměnná | zobrazí se jako | vybírá se |
|---|---|---|
| `mpsv_procesnimapaSite` | Procesni mapa - web | adresa webu |
| `mpsv_listAgendy` | Procesni mapa - Agendy | list z rozbalovátka |
| `mpsv_listProcesy` | Procesni mapa - Procesy | list z rozbalovátka |
| `mpsv_listDilciProcesy` | Procesni mapa - Dilci procesy | list z rozbalovátka |
| `mpsv_listAktivity` | Procesni mapa - Aktivity | list z rozbalovátka |
| `mpsv_listVazby` | Procesni mapa - Vazby | list z rozbalovátka |
| `mpsv_listUtvary` | Procesni mapa - Utvary | list z rozbalovátka |
| `mpsv_listHistorieKodu` | Procesni mapa - Historie kodu | list z rozbalovátka |
| `mpsv_listZalohy` | Procesni mapa - Zalohy | list z rozbalovátka |

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

## 3. Naimportovat solution a VYPLNIT VŠECH 9 PROMĚNNÝCH

Power Apps → **Solutions → Import solution** → `procesnimapa_1_0_0_101.zip`
(unmanaged). Průvodce se zeptá na:

1. **připojení** (connection reference na SharePoint) — vyber nebo založ
   připojení v tenantu MPSV,
2. **9 proměnných** z tabulky výše. U `mpsv_procesnimapaSite` zadej adresu webu MPSV,
   ostatní se pak vybírají z rozbalovátka listů toho webu.

> **Průvodce neproklikávej.** Prázdná proměnná se při importu neprojeví —
> projeví se až tím, že flow nejde zapnout, a vypadá to jako vada balíku.

## 4. Zapnout všechna flow

**Import stav zapnutí nemění.** Flow, které se jednou nepodařilo zapnout,
zůstane vypnuté i po importu opravené verze.

| flow | co dělá | trigger |
|---|---|---|
| `AktualizaceKratkehoNazvu` | zkrácený název aktivity | změna v listu |
| `ExportFlow` | export přehledu do Wordu a Excelu, adresy souborů | z appky |
| `ImportFlow` | hromadné pořízení aktivit z Excelu | z appky |
| `MapaPublishFlow` | publikace HTML mapy se zapečenými daty | z appky |
| `MapaPublishScheduled` | táž publikace | denně 7:00 |
| `PresunFlow` | kaskádový přesun procesu a dílčího procesu | z appky |
| `RestoreFlow` | obnova rejstříku ze snímku | z appky |
| `ZalohaFlow` | snímek rejstříku do knihovny Zalohy | z appky |
| `ZalohaScheduled` | týž snímek | denně 5:00 |

Vypnuté flow se projeví jako chyba **appky**, ne flow: canvas app vidí jen
`502 BadGateway / NoResponse` a příčinu z toho poznat nejde — ta je v run
history.

**Ověření:** všech 9 má stav *On*.

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
2. **Add data** → `MapaPublishFlow`, `ExportFlow`, `ZalohaFlow`, `ImportFlow`, `RestoreFlow`, `PresunFlow`,
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
& $py src/check_solution.py --vstup <zip_z_kroku_6> --vystup runs/build/procesnimapa_<verze>.zip
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
