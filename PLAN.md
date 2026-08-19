# PLAN — Procesní mapa MPSV

Verze: 1.0 (19.08.2026) | Navazuje na `PRD.md` | Stav postupu drží `STATUS.md`

## Fáze

| # | Fáze | Stav |
|---|---|---|
| F0 | Normalizace podkladů + prototyp mapy | **hotovo** |
| F1 | SharePoint rejstřík — schéma, provisioning, import dat | další |
| F2 | Canvas app pro pořizování aktivit | čeká na F1 |
| F3 | Publikační flow: data → HTML mapa v Site Assets | čeká na F1 |
| F4 | Přenos na tenant MPSV | čeká na F2+F3 |
| F5 | Generování textu organizačního řádu | fáze 2 (po 06/2028) |

Brány s `/audit` (agent `powerplatform-auditor`): před importem do DEV (konec F1),
před transportem na MPSV (konec F3), před předáním (konec F4).

---

## F0 — Normalizace a prototyp (HOTOVO)

Doloženo v `STATUS.md`: `src/normalize.py` (7 agend, 46 procesů, 250 dílčích procesů,
46 aktivit, 46 vazeb), `src/build_mapa.py` → `viz/mapa_prototyp.html`,
`src/anonymize.py` → `runs/anonym/`. Ověřeno v prohlížeči.

**Otevřená závislost:** zpětná vazba zadavatelky k prototypu (viz `PRD.md` §9).
Blokuje zmrazení datového modelu, neblokuje F1 kroky 1–3.

---

## F1 — SharePoint rejstřík

### 0. Zmrazení identifikačních kódů — co: `kody.json` + `src/normalize.py` (HOTOVO)

Kódy `AA-BB-CCC-DDDD` v podkladech neexistují (karta i rejstřík mají čísla prázdná),
přiděluje je náš skript. Bez zmrazení by vložení položky doprostřed přečíslovalo
vše pod ní. `kody.json` drží už přidělené kódy; nové položky dostávají první volné
číslo na své úrovni.

**verify (proběhlo):** opakovaný běh nezmění ani jeden kód; položka odebraná
z `kody.json` dostane volné číslo a ostatní se nepohnou; kód ručně přepsaný
v `kody.json` přebije pořadí.
**edge cases:** smazání `kody.json` = úmyslné přečíslování načisto (jen se
souhlasem zadavatelky).
**risk:** výchozí číslování zatím nepotvrdila zadavatelka — pro vývoj v PPF
na anonymizovaných datech nevadí, před nasazením na MPSV se musí potvrdit.

### 1. Návrh schématu listů — co: `src/schema.json` + `deploy/sharepoint_schema.md` (HOTOVO)

Pět listů, interní názvy sloupců bez diakritiky (NFR-7), vztahy přes **textové
kódy**, ne lookup ID (NFR-2 migrovatelnost do Dataverse).

| List | Klíč (Title) | Sloupce |
|---|---|---|
| `Agendy` | `kod` (AA) | nazev, vlastnik, stav_mapovani |
| `Procesy` | `kod` (AA-BB) | nazev, agenda_kod, vlastnik, stav_mapovani |
| `DilciProcesy` | `kod` (AA-BB-CCC) | nazev, proces_kod, vlastnik, stav_rejstrik, stav_mapovani |
| `Aktivity` | `kod` (AA-BB-CCC-DDDD) | nazev, vykonava, spolupracuje, vnitrni_predpis, text_pro_or, sekce, stav, datum_aktualizace |
| `AktivitaDilciProces` | `kod` (`<akt>__<dp>`) | aktivita_kod, dilci_proces_kod, primarni |

- `stav_mapovani` = Choice (`zmapováno` / `zmapováno jiným útvarem` / `nezmapováno`).
- `stav` na aktivitě = Choice (`pracovní` / `schváleno`).
- `stav_rejstrik` = Choice (`využitý` / `využitý-S4` / `nevyužitý`). Třetí hodnota
  odpovídá barevně odlišeným dílčím procesům, které už využila sekce 4
  (3 položky) — v rejstříku mají vlastní barvu, takže je nelze slít s `využitý`.
  Závazný je vždy `src/schema.json`, tady jde jen o přehled.
- `primarni` = Choice (`ano` / `ne`) — určuje, kde se aktivita v mapě zobrazí primárně.
- Indexovat: `agenda_kod`, `proces_kod`, `aktivita_kod`, `dilci_proces_kod`,
  `vykonava`, `sekce` (NFR-6, delegace a view threshold).
- Verzování zapnout na všech pěti listech (FR-1.3).

**verify:** dokument obsahuje pro každý list tabulku sloupec / interní název / typ /
povinný / indexovaný; křížová kontrola proti hlavičkám `runs/normalize/*.csv` —
každý CSV sloupec má cíl v schématu, žádný sloupec schématu nezůstane bez zdroje.
Kontrolu napsat jako skript `src/check_schema.py`, který porovná hlavičky CSV
se schématem a při neshodě skončí nenulovým kódem.
**edge cases:** `Title` u SharePointu nelze vypnout → použije se jako `kod`;
délka `nazev` u aktivit přesahuje 255 znaků → typ „více řádků textu, prostý text";
`spolupracuje` a `vnitrni_predpis` obsahují seznamy oddělené mezerou po normalizaci.
**risk:** volba textového klíče znamená, že referenční integritu nehlídá platforma —
musí ji hlídat pořizovací appka a kontrolní skript.

### 2. Provisioning skript — co: `src/make_setup.py` → `src/setup_sharepoint.js` (HOTOVO)

REST z F12 konzole na cílovém SP webu (ověřený vzor: `POST /_api/web/lists`
`BaseTemplate: 100`; sloupce přes `fields/createfieldasxml` s
`Content-Type: application/json;odata=verbose` a
`__metadata.type = "SP.XmlSchemaFieldCreationInformation"`, **`Options = 13`**).
Skript je idempotentní: co existuje, přeskočí; co chybí v `DefaultView/ViewFields`,
dorovná přes `AddViewField`.

> **Poznámka k volbě nástroje:** `STATUS.md` uvažoval PnP PowerShell. Konzolový JS
> volím proto, že běží pod přihlášenou session bez registrace aplikace a bez
> souhlasu správce tenantu — v cizím vývojovém tenantu je to jediná spolehlivě
> dostupná cesta. PnP zůstává jako varianta pro MPSV, pokud tam bude povolen.

**verify (proběhlo):** `node src/check_setup.js` — smoke test proti falešnému
SharePointu (mock `fetch`), 32 kontrol ve třech scénářích: prázdný web,
opakovaný běh (idempotence), list se sloupci mimo výchozí zobrazení (oprava).
Ověřuje i to, co v konzoli není vidět: `Options = 13`, hlavičku `odata=verbose`,
`__metadata.type`, ASCII interní názvy, zapnuté verzování, indexy, řazení
a past s `LinkTitle`. Test sám ověřen mutacemi (`Options` 13→9 a vypuštěný
`LinkTitle` ho shodí).
**verify (zbývá při nasazení):** spustit na skutečném webu; skript na konci vypíše
tabulku „list / sloupec / stav / typ / ve zobrazení / skrytý" za **každý** sloupec
schématu plus sloupce navíc. Druhé spuštění nesmí nic změnit.
**edge cases:** `Title` je ve `ViewFields` veden jako `LinkTitle` — nehledat doslova
`Title`, jinak se přidá podruhé; `getbytitle` bere zobrazovaný název (s diakritikou),
adresovat přes `GetList('<server-relative-url>')`; sloupce založené dřív bez bitu 4
se neopraví samy → dorovnání přes `AddViewField`.
**risk:** `createfieldasxml` s hlavičkou `nometadata` tiše neudělá nic a nevrátí chybu
→ závěrečná kontrola přes `/fields` je povinná, ne volitelná.

### 3. Import anonymizovaných dat — co: `src/make_import.py` → `src/import_data.js` (HOTOVO)

Vezme `runs/anonym/*.csv` a založí položky ve všech pěti listech.
Digest z `POST /_api/contextinfo`; `__metadata.type` z `ListItemEntityTypeFullName`
listu; idempotence filtrem na `Title` (kód) před insertem.

**Odchylka od původního plánu:** místo `$batch` po 100 se používají **sekvenční
POSTy**. Každá operace stejně musela být ve vlastním changesetu (atomicita `$batch`
je tu nežádoucí), takže by dávkování ušetřilo jen round-tripy za cenu ruční stavby
multipart MIME — a sekvenční varianta umí navíc to podstatné: chyba jedné položky
nezastaví zbytek a na konci se vypíše, která přesně selhala. Cena ~395 requestů,
řádově minuta; jednorázová operace na prostředí.

**verify (proběhlo):** `node src/check_import.js` — 26 kontrol ve třech scénářích:
prázdné listy (počty 7/46/250/46/46, odvozený klíč vazby, `stav` = `pracovní`,
ISO UTC datum, výpustka u dlouhých názvů, více vlastníků, `$top=5000`), opakovaný
běh (nezaloží se nic), selhání jednoho listu (běh pokračuje, chyby se nasbírají).
Test ověřen mutacemi — vypnutá idempotence i zúžené stránkování ho shodí.
**verify (zbývá při nasazení):** po doběhu porovnat souhrnnou tabulku skriptu
s očekávanými počty; namátkou 3 řádky `Aktivity` proti CSV.
**edge cases:** 250 dílčích procesů > výchozí stránka 100 → `$top=5000`
plus následování `odata.nextLink`; datum jako ISO UTC.
**risk (ošetřeno):** do vývojového tenantu smí jen anonymizovaná data (NFR-4) —
generátor odmítne jinou sadu než `runs/anonym`, dokud nedostane
`--povolit-realna-data`. Ověřeno (`exit 1`).

### 4. Brána: `/audit` před importem do DEV

Nezávislá kontrola schématu, skriptů a souladu se zadáním. Nálezy dojet do koncového
stavu (opraveno / zamítnuto se zdůvodněním / eskalováno), strop 2 kola.

---

## F2 — Canvas app pro pořizování

### 5. Návrh obrazovek — co: `deploy/app_navrh.md`

Seznam aktivit (galerie + fulltext + filtr útvaru/sekce) → detail/editace aktivity
→ výběr dílčích procesů (M:N). Kaskáda agenda → proces → dílčí proces
filtrováním číselníků přes `agenda_kod` / `proces_kod`.

**verify:** klikací průchod popsaný krok za krokem s očekávaným stavem obrazovky;
prochází kritérium A3 z PRD.
**edge cases:** dílčí proces bez procesu (sirotek v datech); aktivita bez vazby.
**risk:** kaskáda nad 250 dílčími procesy je pod limitem delegace, ale nad celým
MPSV už být nemusí — číselníky načítat do kolekcí v `App.OnStart`, ne filtrovat živě.

### 6. Přidělení kódu aktivity — co: vzorec v `App`/detail obrazovce

Další volné `DDDD` = `Max(Filter(colAktivity, dilci_proces_kod = vybraný), poradi) + 1`,
formátováno na 4 číslice.

**verify:** test v appce — pro dílčí proces s aktivitami 0001 a 0002 vrátí vzorec
`0003`; pro prázdný dílčí proces `0001`.
**edge cases:** souběžné pořizování dvěma správci → kolize kódu; ošetřit kontrolou
existence před `Patch` a `IfError` + `Notify`.
**risk:** `Max` nad kolekcí je nedelegovatelný — proto číselníky v kolekcích.

### 7. Sestavení a import solution

Publisher a prefix **MPSV, ne `ppf_`** (viz projektový `CLAUDE.md`). Env variables
na site URL, connection reference na SharePoint. Definice env proměnných
s `<defaultvalue>` a **bez** `environmentvariablevalues.json`; po importu vyplnit
current values v prostředí.

**verify:** `testzip` obou zipů před importem; po importu appka otevře seznam
aktivit a zobrazí 46 řádků.
**edge cases:** import hlásí „one or more flows may not have turned on" → flow ručně
zapnout (import stav zapnutí nemění).
**risk:** zaseknutý sirotek v Default Solution blokuje opakovaný import —
Turn off → Delete → Publish all customizations.

---

## F3 — Publikační flow (mapa se zapečenými daty)

### 8. Šablona a build — co: `src/mapa_template.html` (existuje) + kotva pro flow

Mapa **nefetchuje** data — dostane je zapečená. Kotva `__DATA_JSON__` už v šabloně je
a `src/build_mapa.py` ji hlídá (každá kotva právě 1×, jinak build selže).

**verify:** `python src/build_mapa.py` a smoke test: v HTML není řetězec `http://`
ani `https://` mimo komentáře (zákaz CDN), počty uzlů v zapečeném JSON = počty v CSV.
**edge cases:** JSON s diakritikou → `ensure_ascii=False`; uvozovky a sekvence
`</script>` v názvech aktivit musí být escapované, aby nerozbily `<script>` blok.
**risk:** žádný nový — postup je ověřený z F0.

### 9. Flow `MapaPublish` — co: `deploy/flow_MapaPublish.md` (klikací návod) + zip

Trigger plánovaný (1× denně) + ruční. Get file content šablony → Get items z pěti
listů → Compose JSON → nahradit kotvu → Create file do Site Assets.

**verify:** ruční spuštění flow, stažení výsledného HTML, kontrola že obsahuje
aktuální počet aktivit; změna jednoho názvu v listu → další běh → změna je v HTML.
**edge cases:** `Get items` vrací max 5 000, default 100 → nastavit pagination;
servisní účet potřebuje **Contribute na Site Assets**.
**risk:** generované flow zipy jsou nespolehlivé → primárně klikací návod v designeru,
zip jen jako doplněk. Definice flow musí mít `"contentVersion": "1.0.0.0"`.

### 9b. Flow `AktualizaceKratkehoNazvu` — pojistka nad `nazev_kratky`

Trigger „when an item is created or modified" nad listem `Aktivity`: pokud
`nazev_kratky` neodpovídá zkrácení `nazev`, přepíše ho. Řeší zápisy, které
neprošly pořizovací appkou — ruční editaci v listu, hromadný import, úpravu
z Excelu.

Počítaný sloupec SharePointu tuhle roli zastat **nemůže**: vzorec neumí číst
sloupec typu „více řádků textu" (a `nazev` jím být musí kvůli délce) a počítaný
sloupec navíc nejde indexovat, takže by nad 5 000 položkami neuneslo řazení.

**verify:** ruční změna `nazev` přímo v listu → po doběhu flow sedí
`nazev_kratky` na výstup `zkratit()` z `src/check_schema.py`; položka s názvem
kratším než 150 znaků zůstane beze změny výpustky.
**edge cases:** flow nesmí spustit sám sebe donekonečna — po zápisu se trigger
spustí znovu, proto podmínka „přepiš jen když se liší".
**risk:** při hromadném importu se flow spustí na každý řádek; u prvního nahrání
250+ položek to znamená dávku běhů. Import proto plní `nazev_kratky` rovnou
a flow je jen pojistka.

### 10. Ověření zobrazení mapy na SP stránce — ODLOŽENO (rozhodnutí 19.08.2026)

Ověření se **teď nedělá** — řešení se nejprve zhotoví a otestuje se až po nasazení.
Krok zůstává v plánu jako povinný, ale posouvá se za krok 12.

**verify (až se bude dělat):** otevřít HTML ze Site Assets v prohlížeči a v konzoli
zkontrolovat, že nepadá žádná `securitypolicyviolation`. Data jsou zapečená, takže
CSP sandbox (blokuje `connect-src` i `img-src`) nevadí — ověřit, ne předpokládat.
**edge cases:** tenant může HTML ze Site Assets **stahovat** místo zobrazovat
(Strict browser file handling) → pak zvolit zobrazení přes canvas app (vzor 1).
**risk:** **neseme ho vědomě.** Je to jediný bod, kde se může celý přístup k mapě
otočit, a odkladem se ověření dostává až za hotové F2 a F3. Pokud se ukáže, že
tenant HTML ze Site Assets nezobrazí, propadne práce na publikačním flow (krok 9)
a zobrazení se přesune do canvas appky. Mitigace: mapu stavět tak, aby zapečený
JSON šel použít i v canvas appce, a do flow neinvestovat víc, než je nutné.

### 11. Brána: `/audit` před transportem

---

## F4 — Přenos na tenant MPSV

### 12. Provisioning + import reálných dat

Stejné skripty jako F1, jiný web, data z `runs/normalize/` (ne anonymizovaná).

**verify:** počty položek = počty v `runs/normalize/*.csv`; kritérium A6 z PRD
(žádné hardcoded URL — grep přes `src/` a `deploy/` na `sharepoint.com`
nesmí najít nic mimo dokumentaci).
**edge cases:** jiné názvy útvarů, jiná oprávnění, jiný jazyk webu.
**risk:** DLP nebo politiky MPSV můžou zakázat custom script v Site Assets →
fallback na canvas app pro zobrazení mapy (viz krok 10).

### 13. Předání — co: `deploy/navod_sprava.md`

Návod pro správce procesního rámce: jak přidat sekci, jak pořídit aktivitu,
jak spustit publikaci mapy, co dělat při chybě.

**verify:** návod projde sekční správce bez asistence — kontrolní průchod
s uživatelkou.
**risk:** nezdokumentovaný krok „po importu zapnout flow" → typický zdroj
falešného hlášení „appka nefunguje". Musí být v návodu.

### 14. Brána: `/audit` před předáním

---

## F5 — Generování textu OŘ (fáze 2)

Ze schválených aktivit (`stav = schváleno`) sestavit text organizačního řádu
v členění podle vykonávajících útvarů, ve tvaru vzoru
`input/VZOR_OŘ - nově sekce 3_17.7.2026.docx`.

**verify:** vygenerovaný text pro sekci 3 se porovná se vzorem — shoda struktury
a pokrytí všech aktivit.
**risk:** pole `Text pro OŘ` bude v datech dlouho prázdné; generování má smysl
až po jeho naplnění.
