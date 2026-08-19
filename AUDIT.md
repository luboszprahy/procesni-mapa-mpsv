# AUDIT — Procesní mapa MPSV

Poslední audit: 19.08.2026 12:40 · auditor: powerplatform-auditor · kolo: 1
Verdikt: NÁLEZY (1/2/0)
Rozsah: fáze F1 (SharePoint rejstřík) před prvním ostrým během na
`/sites/DigiData_D/testovaci_subsajta/procesnimapa` — `src/schema.json`,
`src/check_schema.py`, `src/make_setup.py`→`src/setup_sharepoint.js`,
`src/make_import.py`→`src/import_data.js`, `src/check_setup.js`,
`src/check_import.js`, `src/fake_sharepoint.js`, `src/normalize.py` + `kody.json`,
soulad s `PRD.md`/`PLAN.md`/`STATUS.md`/projektovým `CLAUDE.md`. Kanvas app, flow
a solution balíček v této fázi neexistují — checklist body A–D, F, G se
nepoužijí (nejsou předmětem F1); použity jen relevantní body E a H.

V tomto projektu **neplatí** kritéria vázaná na publisher `ppf`/prefix `ppf_`/
tenant `ppfbanka.sharepoint.com` (A1, A3, B kap.) — cílová organizace je MPSV,
publisher/prefix v `schema.json` jsou `mpsv`/`mpsv_` v souladu se
STATUS.md rozhodnutím 19.08.2026. Vývojová site v PPF je jen dočasný hostitel;
hardcoded URL v `src/` ani `deploy/` nejsou (ověřeno greppem, viz P-02).

## Nálezy

### P-01 · BLOKUJÍCÍ · src/make_import.py
Pojistka „do vývojového tenantu smí jen anonymizovaná data" (NFR-4) kontroluje
**jen název poslední složky cesty** (`datadir.name != "anonym"`), ne obsah dat.
Neanonymizovaná data zkopírovaná/přejmenovaná do libovolné složky, jejíž
poslední segment se jmenuje `anonym`, projdou bez `--povolit-realna-data`
a vygenerují plnohodnotný `import_data.js` s reálnými identifikujícími údaji.

Repro (provedeno ve scratchpadu, mimo projekt):
```
mkdir pojistka_test/anonym
cp runs/normalize/*.csv pojistka_test/anonym/      # NEanonymizovaná data
python src/make_import.py --data pojistka_test/anonym --out import_TEST.js
# exit 0, bez --povolit-realna-data
grep -c "MPSV" import_TEST.js   -> 3 výskyty (v runs/anonym verzi je to 0)
grep -c "ÚP ČR" import_TEST.js  -> 3 výskyty
```
Skutečný `src/import_data.js` (z `runs/anonym`) tokeny neobsahuje — aktuální
běh je čistý. Riziko je v tom, že bezpečnostní mechanismus je čistě nominální
(kontrola názvu adresáře) a dá se obejít nedopatřením (přejmenování složky,
kopie dat do jinak pojmenovaného „anonym" adresáře, oprava dat přímo v
`runs/anonym/*.csv` bez opětovného spuštění `anonymize.py`) — přesně scénář,
kterému má pojistka podle `PLAN.md` krok 3 a `PRD.md` NFR-4 zabránit.
Checklist: mimo číslované body (analogie B1 — žádná neanonymizovaná data do
cizího tenantu); zadání PRD NFR-4.
Stav: otevřeno

### P-02 · OPRAVIT · src/make_import.py
`check_schema.py` (referenční integrita, unikátnost klíčů, délky, Choice
hodnoty) se **nevolá automaticky** před generováním `import_data.js` —
`make_import.py` importuje z `check_schema` jen `read_csv` a `zkratit`, ne
funkci `check()`. Pokud někdo upraví CSV v `runs/anonym` (nebo `runs/normalize`
pro ostrý běh) přímo a zapomene spustit `check_schema.py`, poškozená data
(např. referenční kód mimo číselník) se tiše zapečou do `import_data.js`
a odešlou do SharePointu — platforma referenční integritu textových klíčů
nekontroluje (viz `deploy/sharepoint_schema.md` „Zásady").

Repro:
```
# procesy.csv: agenda_kod řádku 01-01 přepsán na neexistující "99"
python src/check_schema.py --data runs/anonym   # BY to odhalilo (CHYBA, exit 1)
python src/make_import.py --data runs/anonym --out import_TEST.js
# exit 0 — make_import.py chybu nekontroluje
grep '"agenda_kod": "99"' import_TEST.js  -> nalezeno, zapečeno beze varování
```
Pro aktuální commitnutá data (`runs/anonym`, `runs/normalize`) `check_schema.py`
prochází bez chyby (ověřeno), takže dnešní `src/import_data.js` je v pořádku.
Nález je o chybějící vazbě mezi oběma skripty pro *budoucí* běhy, ne o vadě
aktuálního balíčku.
Checklist: E2 (kontrola výsledku, ne jen že „proběhlo"); zadání `deploy/sharepoint_schema.md`
„referenční integritu … hlídá check_schema.py a pořizovací aplikace" — v praxi
ji hlídá jen tehdy, když ji operátor spustí ručně před importem.
Stav: otevřeno

### P-03 · OPRAVIT · PLAN.md řádek 63 vs src/schema.json řádek 183-192
`PLAN.md` dokumentuje `stav_rejstrik = Choice (` využitý` / `nevyužitý`)`, ale
skutečné schéma má **tři** hodnoty: `využitý`, `využitý-S4`, `nevyužitý`
(`src/normalize.py` řádek 210, barva `ARGB_S4`). Funkčně v pořádku — `check_schema.py`
prochází bez chyby a `deploy/sharepoint_schema.md` je generovaný správně ze
skutečného schématu — ale `PLAN.md` jako plánovací dokument zastaral proti
implementaci.
Checklist: H1 (PLAN.md vs skutečnost).
Stav: otevřeno

## Co bylo ověřeno spuštěním (v pořádku)

- `check_schema.py` proti `runs/normalize` i `runs/anonym`: OK, 7/46/250/46/46,
  žádná chyba referenční integrity, generuje `deploy/sharepoint_schema.md`.
  Mutační test (agenda_kod na neexistující „99") skript spolehlivě odhalí
  (`CHYBA: … nema protejsek …`, exit 1) — kontrola je reálná, ne jen tvrzená.
- `check_setup.js` (32 kontrol/3 scénáře) a `check_import.js` (26 kontrol/3
  scénáře): oba `exit 0`. Mutační testy nad kopiemi ve scratchpadu potvrdily,
  že testy umí SELHAT: `Options 13→9` shodí `check_setup.js`
  (`SELHALO: Options = 13 u vsech zakladanych sloupcu`); vypnutí kontroly
  existujících klíčů v `import_data.js` i zúžení `$top=5000→100` shodí
  `check_import.js` (`SELHALO: druhy beh nezalozil ani jednu polozku`,
  `SELHALO: dotaz na existujici klice pouziva $top=5000`).
- `node --check` na `setup_sharepoint.js` i `import_data.js`: syntakticky OK.
- **Generované skripty sedí na schéma/data**: `make_setup.py` a `make_import.py`
  spuštěné znovu nad stejným `schema.json`/`runs/anonym` vyprodukují bajtově
  identický `setup_sharepoint.js` a `import_data.js` (jediný rozdíl je časové
  razítko `datum_aktualizace`, které se plní časem běhu záměrně). Riziko
  „rozejde se generátor od schématu" se nepotvrdilo.
- **Idempotence je reálná, ne jen tvrzená**: 2. běh `check_setup.js` nezaloží
  nic navíc (0 nových `createfieldasxml`/`AddViewField`), 2. běh `check_import.js`
  nezaloží žádnou položku — obojí ověřeno i negativně (mutace idempotenci
  vypne → test spadne, viz výše).
- **Žádné hardcoded URL/GUID** v `src/` ani `deploy/`: grep na `sharepoint.com`,
  `ppfbanka`, `DigiData` našel jen mock URL `https://tenant.sharepoint.com/...`
  v testovacích souborech (`check_setup.js`, `check_import.js`,
  `fake_sharepoint.js`) — ne v generátorech ani generovaných skriptech.
  `urciWeb()` v obou runtime skriptech odvozuje web z `_spPageContextInfo`
  nebo z `location.href`, žádná URL napevno.
- **Stabilita `kody.json`**: opakovaný běh `normalize.py` nezměnil ani jeden
  kód (diff prázdný). Ruční přepis kódu v `kody.json` (agenda „eu a mezinarodni
  vztahy" 06→99) přebil pořadí, ostatní kódy se nepohnuly a „06" se nikde
  znovu neobjevilo — reprodukováno ve scratchpadu, tvrzení ze `STATUS.md`
  potvrzeno.
- E1/E3 (Options=13, past LinkTitle), E2 (závěrečná kontrolní tabulka za
  každý sloupec) — implementováno a pokryto testem `check_setup.js`.
- NFR-7 (interní názvy bez diakritiky): všechny sloupce v `schema.json` mají
  ASCII interní název; zobrazovaný název s diakritikou se nastavuje až přes
  MERGE po založení (ověřeno testem „zobrazovany nazev s diakritikou nastaven
  pres MERGE").
- Publisher/prefix `mpsv`/`mpsv_` v `schema.json` — v souladu s projektovým
  `CLAUDE.md` a rozhodnutím ve `STATUS.md` (PPF prefix se pro tento projekt
  správně nepoužívá).
- Počty v `deploy/sharepoint_schema.md`, `check_schema.py`, `check_import.js`
  a `STATUS.md` si vzájemně odpovídají: 7/46/250/46/46.

## Neověřeno

### N-01 · reálný běh na SharePointu
Vše výše je ověřeno proti mock/fake SharePointu (`fake_sharepoint.js`) a proti
CSV datům. Skutečné REST chování cílové PPF site (`getbytitle` vs.
`GetList`, tvar odpovědi `DefaultView/ViewFields`, chování `createfieldasxml`
s `Options=13`) nebylo v tomto kole ověřeno naživo — STATUS.md to eviduje
jako čekající krok („F1 krok 4, pak první ostrý běh") a `setup_sharepoint.js`
/`check_setup.js` sám o sobě obsahuje závěrečnou kontrolní tabulku pro tento
účel. Potřeba: spuštění na skutečné site (mimo rozsah tohoto auditu — provádí
se čtení lokálních artefaktů, ne zásah do prostředí).

### N-02 · stabilita kódu při změně textu položky (přejmenování, ne jen oprava)
Ověřil jsem stabilitu při beze změny textu (opakovaný běh) a při ručním
přepsání v `kody.json`. Neověřil jsem scénář „text položky se v `input/`
skutečně přejmenuje" (např. oprava překlepu v rejstříku) — podle kódu
(`Registry._kod`, klíč = `key(nazev)`) by taková položka dostala **nový** kód
a starý zůstal osiřelý v `kody.json` (neškodné, ale tichá duplicita
identity). Toto je STATUS.md už evidované jako otevřené riziko
(„Co stále chybí: potvrzení zadavatelky … pro vývoj v PPF to nevadí"), proto
to nezvyšuji na nový nález — jen potvrzuji, že riziko je reálné a nemá
zatím žádnou technickou pojistku (jen proces „nesmazat kody.json bez
domluvy"). Potřeba k doověření: konkrétní editace `input/` a nový běh
`normalize.py` s diffem `kody.json`.

## Zamítnuté nálezy

*(žádné — první kolo auditu tohoto projektu)*
