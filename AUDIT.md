# AUDIT — Procesní mapa MPSV

Poslední audit: 19.08.2026 · auditor: powerplatform-auditor · kolo: 2
Verdikt: NÁLEZY (0/1/0) — žádný otevřený BLOKUJÍCÍ, F1 je připravená na první ostrý běh
Rozsah kola 2: re-audit oprav P-01/P-02/P-03 z kola 1 (`src/make_import.py`,
`src/anonymize.py`, `PLAN.md`), spuštění `check_schema.py`/`make_setup.py`/
`make_import.py`/`check_setup.js`/`check_import.js`, nově `deploy/app_navrh.md`
(technická tvrzení o delegaci a přidělení kódu — appka sama neexistuje).

V tomto projektu **neplatí** kritéria vázaná na publisher `ppf`/prefix `ppf_`/
tenant `ppfbanka.sharepoint.com` — viz zdůvodnění v kole 1 níže (beze změny).

## Nálezy — kolo 1 (stav po kole 2)

### P-01 · BLOKUJÍCÍ (kolo 1) · src/make_import.py
Původní nález: pojistka „do vývojového tenantu smí jen anonymizovaná data"
kontrolovala jen název poslední složky cesty, ne obsah dat.

**Oprava přijata.** `neanonymizovane_tokeny()` (src/make_import.py:26-35) skenuje
`json.dumps(data)` proti `TOKENY` importovanému z `src/anonymize.py` — stejný
seznam, kterým si anonymizace ověřuje vlastní výsledek. Původní repro scénář
teď spolehlivě selže:
```
cp runs/normalize/*.csv <scratch>/pojistka_test/anonym/
python src/make_import.py --data <scratch>/pojistka_test/anonym --out import_TEST.js
→ ODMITNUTO: … jsou identifikujici udaje (\bMPSV\b, \bÚP ČR\b, …). EXIT 1
```
Funguje, protože „MPSV" je jako literální řetězec prakticky ve všech `nazev`
polích všech čtyř tabulek (ověřeno greppem přes `runs/normalize/*.csv`) —
náhodná/nedbalá kopie neanonymizovaných dat tedy tuto pojistku nepodejde.

**Ale: cílená/dílčí obchazka funguje** — viz nový nález **P-04** níže. Kontrola
je jen tak dobrá, jako seznam `TOKENY`, a ten nepokrývá útvarová čísla
(`UTVARY` v `anonymize.py`) ani formát čísel předpisů (`RE_PREDPIS`), přestože
`anonymize.py` sám tyto dvě kategorie aktivně anonymizuje. Aktuální komitnutá
data v `runs/anonym` tímto problémem netrpí (prošla `anon()` normálně) — jde o
riziko pro budoucí ruční zásahy do dat, ne o vadu dnešního balíčku.
Checklist: mimo číslované body; zadání PRD NFR-4.
Stav: **oprava přijata pro nahlášený scénář; navazující gap zaveden jako P-04 (OPRAVIT)**

### P-02 · OPRAVIT (kolo 1) · src/make_import.py
Původní nález: `check_schema.py` se nevolal automaticky před generováním
importu, poškozená data (referenční kód mimo číselník) se tiše zapekla.

**Oprava přijata a ověřena.** `make_import.py` teď importuje a volá `check()`
(řádky 220-228) před generováním. Mutační test — `procesy.csv` řádek
`01-01;…;01;` přepsán na `01-01;…;99;` (neexistující agenda):
```
python src/make_import.py --data <scratch>/p02_test --out import_p02.js
→ CHYBA: Procesy.agenda_kod: 1 odkazu nema protejsek v Agendy, napr. ['99']
→ ODMITNUTO: … nesedi na schema (1 chyb). EXIT 1
```
Běžný běh nad `runs/anonym` (bez mutace) proběhl bez problémů — `check()`
poškozená data odmítá, nepoškozená propouští (viz „Ověřeno spuštěním" níže).
Checklist: E2. Stav: **opraveno, ověřeno**

### P-03 · OPRAVIT (kolo 1) · PLAN.md
Původní nález: `PLAN.md` dokumentoval u `stav_rejstrik` 2 hodnoty místo 3.

**Oprava přijata.** `PLAN.md` řádek 64 nyní uvádí `využitý` / `využitý-S4` /
`nevyužitý` se zdůvodněním (3 položky, kde už dílčí proces využila sekce 4) a
větou „Závazný je vždy `src/schema.json`". Sedí na skutečné schéma.
Stav: **opraveno**

## Nový nález — kolo 2

### P-04 · OPRAVIT · src/make_import.py + src/anonymize.py
Pojistka `neanonymizovane_tokeny()` kontroluje obsah dat, ale **jen proti
pevnému seznamu `TOKENY`** (13 institucionálních zkratek + 2 vlastní jména).
Nekontroluje:
- **útvarová čísla** — `UTVARY` (`{"3":"7","33":"71","331":"711","11":"72",
  "111":"721","113":"723","12":"73","6":"74","4":"75"}` v `anonymize.py`),
  přestože `anon()` je aktivně přepisuje jako identifikující údaj,
- **čísla vnitřních předpisů** — `RE_PREDPIS` (`SP/MP/PM ##/####`), přestože
  `Predpisy` třída v `anonymize.py` existuje přesně proto, aby je nahradila.

Repro (nad kopií `runs/anonym`, tedy řádně anonymizovaná data, do nichž se
ručně vrátí jen dvě reálné hodnoty — util kód a číslo předpisu — beze změny
čehokoli jiného, „MPSV" nikde nepřidáno):
```
cp runs/anonym/*.csv <scratch>/pojistka_test3/
# v aktivity.csv nahrazeno (jen tento jeden řádek):
#   "07-08-009;711;věcně příslušné útvary XÚ;VP 01/2015, VP 02/2016;7;8"
#   -> "07-08-009;331;věcně příslušné útvary XÚ;SP 10/2021, SP 13/2025;7;8"
python src/make_import.py --data <scratch>/pojistka_test3 --out import_TEST3.js
→ EXIT 0, žádné varování
grep '"vykonava": "331"' import_TEST3.js   → nalezeno (reálný útvarový kód MPSV)
grep "SP 10/2021" import_TEST3.js          → nalezeno (reálné číslo interního předpisu)
```
Import se zapeče beze zádrhelu do `import_data.js` a odešel by do PPF tenantu.
Reálný útvarový kód a reálné číslo interního předpisu jsou přesně ta
kategorie údajů, kterou `anonymize.py` sám považuje za nutné anonymizovat
(viz `UTVARY`, `Predpisy`) — pojistka v `make_import.py` na ně ale nedosáhne,
protože kontroluje jen `TOKENY`.

Proč jde o **OPRAVIT**, ne BLOKUJÍCÍ: netýká se aktuálních komitnutých dat
(`runs/anonym` prošla `anon()` běžnou cestou a je čistá — ověřeno i greppem v
kole 1). Scénář vyžaduje ruční zásah do už anonymizovaných CSV (typicky oprava
jednoho pole „z ruky" bez opětovného běhu `anonymize.py`), ne prostou
nedbalost jako u P-01. Riziko roste s tím, jak přibudou karty dalších sekcí a
někdo bude opravovat data přímo v `runs/anonym`.

Doporučená oprava (neprovádět, jen návrh pro hlavního asistenta): rozšířit
`neanonymizovane_tokeny()` o kontrolu `RE_PREDPIS` (jakýkoli match = reálné
číslo předpisu, protože po anonymizaci by měly být jen `VP ##/20##`) a o
kontrolu, že žádná hodnota polí `vykonava`/`vlastnik` neodpovídá klíči v
`UTVARY` (reálné originální kódy `3/33/331/11/111/113/12/6/4`).
Checklist: mimo číslované body; zadání PRD NFR-4.
Stav: otevřeno

## Ověřeno spuštěním — kolo 2

Všech pět požadovaných příkazů proběhlo bez chyby a testy prokazatelně umí
selhat (ne jen „proběhlo bez erroru"):

- `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe src/check_schema.py`
  → `schema OK proti runs/normalize: Agendy=7, Procesy=46, DilciProcesy=250,
  Aktivity=46, AktivitaDilciProces=46`, exit 0.
- `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe src/make_setup.py`
  → `src\setup_sharepoint.js (21.2 kB) - 5 listu, 33 sloupcu`, exit 0.
- `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe src/make_import.py`
  → `src\import_data.js (113.8 kB) - Agendy=7, Procesy=46, DilciProcesy=250,
  Aktivity=46, AktivitaDilciProces=46`, exit 0. Regenerovaný soubor se lišil
  od komitnutého jen v `datum_aktualizace` (46 řádků diffu, jen časové
  razítko, ověřeno `git diff` a vráceno `git checkout -- src/import_data.js`,
  auditor v repu nic nezanechal).
- `node src/check_setup.js` → 32/32 kontrol OK ve 3 scénářích, exit 0.
- `node src/check_import.js` → 26/26 kontrol OK ve 3 scénářích, exit 0.
- P-01 fix ověřen mutací (viz výše, exit 1 pro reálná data).
- P-02 fix ověřen mutací (viz výše, exit 1 pro poškozený `agenda_kod`).
- P-04 gap ověřen mutací (viz výše, exit 0 pro útvarový kód + číslo předpisu
  — to je nález, ne potvrzení funkčnosti).

Oprava tedy nic nerozbila — běžný běh nad `runs/anonym` prochází stejně jako
před opravou, jen navíc odmítá scénáře, které dřív procházely tiše.

## deploy/app_navrh.md — kontrola technických tvrzení

Dokument, appka zatím neexistuje (v souladu se zadáním — to není nález).
Ověřil jsem tvrzení o delegaci a přidělení kódu proti `src/schema.json`
(skutečné indexování sloupců) a proti `reference/canvas-architecture-patterns.md`
+ `reference/datovy-zdroj-nenacita.md` (checklist C2):

- **`Filter(Aktivity, StartsWith(Title, varPrefix))`** — `Title` (pole `kod`)
  je v `src/schema.json` `indexed: true` (ověřeno vypsáním schématu). `StartsWith`
  nad indexovaným textovým sloupcem je pro SharePoint delegovatelný a `varPrefix`
  je globální proměnná (`Set`), ne hodnota počítaná uvnitř `ForAll` — přesně
  vzor, který `canvas-architecture-patterns.md` označuje za bezpečný („v
  delegovaném Filter smí být jen literál nebo globální proměnná"). Tvrzení sedí.
- **Filtry `scr_Seznam`** (`sekce`, `vykonava`, `stav`, `nazev_kratky`) — všechny
  čtyři sloupce jsou v schématu `indexed: true` (ověřeno). Vzor
  `IsBlank(ctrl.Selected.Value) || sloupec = ctrl.Selected.Value` je standardní
  delegace-bezpečný idiom pro volitelné filtry nad SharePointem (kombinace
  `Or`/`And` nad delegovatelnými porovnáními `=`/`StartsWith`) — konzistentní
  s tím, co `canvas-architecture-patterns.md` a `datovy-zdroj-nenacita.md`
  o delegaci nad SharePointem dokumentují. Nenašel jsem rozpor.
- **„Search() a in delegovatelné nejsou"** — v lokálních skillech není explicitně
  zmíněno (dostupné artefakty mluví hlavně o `ID >`, `Sort`, `StartsWith`),
  takže tvrzení nejde ověřit `[SPUSŤ]` nad rozbaleným balíčkem (appka
  neexistuje). Odpovídá to obecně známému a stabilnímu faktu o SharePoint
  konektoru, ale bez appky/prostředí ho nejde potvrdit místní reprodukcí →
  **NEOVĚŘENO** (viz N-03).
- **Vazba M:N** (`AktivitaDilciProces`, dotaz podle `aktivita_kod`) — sloupec
  `aktivita_kod` je `indexed: true` (ověřeno), matches.
- **Přidělení kódu** (`Right("000" & (Value(Right(varPosledni,4))+1), 4)`) —
  prázdný dílčí proces: `Right(Blank(),4)` → `Blank()`, `Value(Blank())+1` = 1
  (Power Fx počítá s `Blank()` jako 0 v aritmetice) → `0001`, sedí na tvrzení
  v dokumentu. Přetečení nad 9999 aktivit v jednom dílčím procesu vzorec
  neřeší (`Right("000"&10000,4)` by dalo `"0000"`), ale to je při dnešním
  rozsahu (max řádově desítky aktivit na dílčí proces) čistě teoretické —
  POZNÁMKA, ne nález.
- **`vlastnik` jen ke čtení, mimo `Aktivity`** — schéma `Aktivity` v
  `src/schema.json` skutečně nemá sloupec `vlastnik` (ověřeno výpisem), sedí
  na tvrzení „vlastníci patří číselníku, ne aktivitě".

Žádné faktické chybné tvrzení v `deploy/app_navrh.md` jsem nenašel; jedno
tvrzení (Search/in) zůstává NEOVĚŘENO z důvodu chybějícího prostředí/appky,
ne proto, že by bylo zpochybněno.

## Neověřeno

### N-01 · reálný běh na SharePointu (z kola 1, stále platí)
Vše je ověřeno proti mock/fake SharePointu a CSV datům. Skutečné REST chování
cílové PPF site nebylo ověřeno naživo — mimo rozsah auditu (čtení lokálních
artefaktů, ne zásah do prostředí).

### N-02 · stabilita kódu při přejmenování položky (z kola 1, stále platí)
Neověřeno, jen potvrzeno jako známé riziko bez technické pojistky (viz
STATUS.md).

### N-03 · Search()/in nedelegovatelnost nad SharePointem (nové)
`deploy/app_navrh.md` tvrdí, že `Search()` a `in` nejsou pro SharePoint
delegovatelné. Odpovídá obecně známému chování SharePoint konektoru, ale
lokální skill materiály to explicitně nedokládají a appka/prostředí neexistuje,
takže to nejde ověřit `[SPUSŤ]`. Potřeba k doověření: appka nad reálným
SharePoint listem + Power Apps Studio delegation warning, nebo oficiální
dokumentace Microsoftu (offline nedostupná).

## Zamítnuté nálezy

*(žádné)*
