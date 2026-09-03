# PLAN — Procesní mapa MPSV

Verze: 1.0 (19.08.2026) | Navazuje na `PRD.md` | Stav postupu drží `STATUS.md`

## Fáze

| # | Fáze | Stav |
|---|---|---|
| F0 | Normalizace podkladů + prototyp mapy | **hotovo** |
| F1 | SharePoint rejstřík — schéma, provisioning, import dat | **hotovo** |
| F2 | Canvas app pro pořizování aktivit | **hotovo** (1.0.0.23 ověřeno v provozu 21.08.) |
| F3 | Publikační flow: data → HTML mapa v Site Assets | **hotovo** (ověřeno v provozu 21.08.) |
| F4 | Přenos na tenant MPSV | **blokováno** — bez přístupu k tenantu MPSV (21.08.) |
| F6 | Připomínky z provozu: mapa, drobnosti v appce, dashboard, zadávací obrazovky, úklid číselníků, sjednocení editace | A–G **hotovo** (1.0.0.37, čeká na import) |
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

### 9. Flow `MapaPublish` — HOTOVO v 1.0.0.20 (20.08.2026)

Trigger **ruční** (PowerApps V2, tak ho založil uživatel v designeru); plánovaný
běh 1× denně přijde až po ověření kroku 10, a protože trigger může být jen jeden,
znamená to druhé flow se stejnými akcemi, ne úpravu tohoto.

14 akcí: `Sablona` (Get file content ze Site Assets) → 5× `Nacti_*` (Get items,
`$top` 5 000 + pagination) → 5× `Map_*` (Select na datový kontrakt) → `Model`
(Compose) → `Stranka` (dvojí `replace` kotev nad `base64ToString`) → `Uloz_mapu`
(Create file). Generuje `src/build_mapa_flow.py` do exportované kostry — úprava
exportu, ne stavba zipu od nuly.

**verify (hotovo):** `src/check_mapa_flow.py` — 126 kontrol; výraz kroku `Stranka`
se vytáhne z balíku, vyhodnotí nad skutečnou šablonou a projde stejným sítem jako
`build_mapa.py`. **12 mutací, všechny chycené.**
**verify (na uživateli, `deploy/navod_publikace_mapy.md`):** ruční spuštění →
`Nacti_DilciProcesy` vrátí **250 položek, ne 100**; ve staženém HTML nezbyly kotvy
a jsou v něm všechny klíče modelu; změna názvu v listu se po dalším běhu propíše.
**edge cases:** `Get items` default 100 → pagination zapnutá a hlídaná bránou;
Choice sloupce potřebují `?['Value']`; servisní účet potřebuje **Contribute
na Site Assets**; `Create file` nad existujícím souborem musí přepsat, ne založit
`procesni_mapa1.html`.
**risk:** kostra ze Studia nenesla **žádnou connection reference** — doplňuje se
ta, kterou už v balíku používá druhé flow. Import stav zapnutí nemění, flow je
proto po importu nutné **ručně zapnout**. `contentVersion` musí být `"1.0.0.0"`;
s `"undefined"` z kostry import projde, ale flow nejde otevřít v designeru.

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

### 10. Ověření zobrazení mapy na SP stránce — HOTOVO 20.08.2026, dopadlo dobře

**Mapa se v tenantu zobrazí.** Klik na `procesni_mapa.html` v knihovně
Site Assets ji otevře; `securitypolicyviolation` v konzoli nepadá, protože
data jsou zapečená a stránka nic nefetchuje. Tím padlo riziko, které se od
začátku neslo jako jediné, co mohlo celý přístup k mapě otočit — publikační
flow (krok 9) zůstává a zobrazení se do canvas appky stěhovat nemusí.

**Zároveň to opravuje závěr z FloorPlanu** („`.html` i `.aspx` ze Site Assets
se v PPF stahují vždy, hosting dead-end"). Neplatí to — stahuje se **přímý
odkaz na soubor**, ne otevření z knihovny.

**Zbývá dílčí vada:** tlačítko „Zobrazit v HTML" v appce volá `Launch()` na
přímou cestu `…/SiteAssets/procesni_mapa.html` a na tu SharePoint kvůli
*Strict browser file handling* pošle `Content-Disposition: attachment`.

**verify:** `src/zjisti_url_mapy.js` v konzoli změří u šesti kandidátních
adres hlavičku odpovědi a vypíše `ZOBRAZÍ SE` / `STÁHNE SE`; funkční adresa
se dosadí do `varMapaUrl` v `App.OnStart` (jediné místo v appce).
**edge cases:** fetch musí běžet s `redirect: "manual"` — potichu následované
přesměrování by změřilo hlavičky jiné adresy.
**risk:** kdyby se stahovalo úplně všechno, zbývá **stránka s web partem
Vložit** (stránky se nestahují nikdy); mapa v iframu poběží i pod sandboxem
`about:srcdoc`, protože nic nefetchuje. Cena je užší zobrazovací plocha.

### 11. Brána: `/audit` před transportem

---

## F4 — Přenos na tenant MPSV

### 12. Provisioning + import reálných dat

Stejné skripty jako F1, jiný web, data z `runs/normalize/` (ne anonymizovaná).

**Pořadí kroků (adresa webu je v balíku na 20 místech, nález B-01):**

1. provisioning listů na webu MPSV (`setup_sharepoint.js`),
2. import solution do prostředí MPSV a **zapnutí všech čtyř flow**,
3. appku ve Studiu **přepojit na web MPSV** a zaregistrovat `ExportFlow`
   jako datový zdroj (`FlowNameId` přiděluje až cílové prostředí),
4. mikro-změna → Save → Publish → **export solution**,
5. lokálně znovu spustit `build_mapa_flow.py`, `build_export_flow.py`
   a `add_mapa_schedule.py` — adresu i GUIDy listů si vezmou z připojení appky,
5b. **`AktualizaceKratkehoNazvu` se tímhle nespraví** a je to jediné flow,
   které chce ruční zásah (nález B-01, kolo 4):
   - `src/build_flow.py` má na řádku 20 konstantu `LIST_AKTIVITY` — GUID listu
     Aktivity. **Přepsat na GUID téhož listu na MPSV** (vypíše ho
     `setup_sharepoint.js` nebo `export_sp_schema.js`). Runtime výraz tam
     nejde: flow se naimportuje, ale nepůjde zapnout (pravidlo `PatchItem`).
   - Trigger flow je nad listem Aktivity, takže se **nedá přepojit úpravou
     definice** — v Power Automate designeru nad webem MPSV se založí nová
     kostra (trigger „When an item is created or modified" nad listem Aktivity
     + jedna akce Compose), exportuje se a `build_flow.py` do ní dopíše zbytek.
   - Teprve pak dá `check_solution.py` zelenou; do té doby správně selže na
     tomhle flow.

6. ručně přepsat `varMapaUrl` v `src/app_src/App.pa.yaml` (jediné ručně psané
   místo — canvas app textové env proměnné číst neumí),
7. `build_app.py` + brány + import výsledku.

**verify:** počty položek = počty v `runs/normalize/*.csv`; kritérium A6 z PRD
— `check_solution.py` musí projít bez chyby (selže, když některé flow míří na
jiný web než canvas app) a jeho varování o počtu míst musí uvádět web MPSV.
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

## F6 — Připomínky z provozu (zadáno 21.08.2026)

Zadáno po ověření 1.0.0.25 v prostředí. Pořadí je dané závislostmi: skupina A
je nezávislá na Studiu a jde hned, B je drobná a jede v jednom balíku s C,
D až po C.

### A. HTML mapa — co: `src/mapa_template.html`, `src/build_mapa.py`

Všechny čtyři úpravy jsou v šabloně; data se nemění, kotvy `__DATA_JSON__`
a `__GEN__` zůstávají beze změny.

**A1. Zatržítko „Zobrazit kód" v ovládací liště, ve výchozím stavu zapnuté.**
Vypnuté skryje `span.kod` v celém stromu (CSS třída na `<body>`, ne přerenderování).

**A2. Volba velikosti písma, bez zapékání variant.** Čtyři stupně (S / M / L / XL)
přepínají jedinou CSS proměnnou `--fs` na `:root`; všechny velikosti v šabloně
se přepočítají z ní (`em`/`calc`), takže se nikde nezapéká druhá varianta stránky.
Volba se pamatuje přes `localStorage` v `try/catch` — v sandboxovaném náhledu
může přístup k úložišti vyhodit výjimku a stránka to nesmí odnést.

**A3. Nápověda při najetí myší.** `title` na řádku: typ prvku (agenda / proces /
dílčí proces / aktivita), kód a u aktivity vykonávající útvar. `title` je zvolený
schválně — vlastní tooltip by v náhledovém iframu musel řešit ořezání okrajem.

**A4. Volba stupně rozbalení + barevné odlišení vrstev.** Místo dvou tlačítek
„Rozbalit / Sbalit vše" přepínač úrovní **1 agendy · 2 procesy · 3 dílčí procesy ·
4 vše**; každá úroveň rozbalí strom právě po tu vrstvu. Vrstvy dostanou vlastní
podklad řádku a barvu svislé linky odsazení, ne jen barvu písma jako dnes.

**verify:** `python src/build_mapa.py`, otevřít `viz/mapa_prototyp.html` přes
`http://127.0.0.1:8765/` a projít: (a) odškrtnutí kódu skryje kódy na všech
čtyřech úrovních a hledání podle kódu se tím **nerozbije**, (b) čtyři stupně
písma mění velikost celé stránky včetně detailu, po reloadu drží, (c) najetí
na řádek každé úrovně ukáže správný typ, (d) stupeň 2 rozbalí procesy a nic
hlubšího, (e) smoke test `build_mapa.py` (kotvy 1×, žádné `http://` mimo
komentáře) prochází.
**edge cases:** filtr útvaru + stupeň rozbalení se nesmí přebíjet — vyhledávání
už dnes rozbaluje nalezené větve a to má přednost; `localStorage` nedostupný.
**risk:** `mapa_template.html` čte publikační flow **ze Site Assets**, ne z repa
— bez nahrání nové šablony do knihovny se úprava v publikované mapě neprojeví.
Do ověření proto patří i běh flow.

### B. Drobnosti v canvas appce — co: `src/app_src/scr_Seznam.pa.yaml`, `scr_Detail.pa.yaml`

**B1. Zrušit šipku pro otevření detailu** v řádku galerie. Celý řádek detail
otevírá od 1.0.0.20, šipka je zbytek dřívějšího chování.

**B2. Přepínač „Zobrazit kód" nad seznamem, výchozí zapnuto.** Skrývá sloupec
kódu v galerii i jeho hlavičku; řazení podle kódu zůstane dostupné.

**B3. Detail — pole dílčích procesů.** Dnes je vidět jedno zařazení. Nově galerie
o výšce dvou řádků se svislým posuvníkem a popiskem „zařazeno do N dílčích
procesů", aby bylo poznat, že jich je víc.

**verify:** `python src/check_app.py` (parsuje YAML, hlídá delegaci, překryvy);
po importu ve Studiu: řádek bez šipky se otevírá klikem, přepínač kódu schová
sloupec a nezmění počty, aktivita se třemi zařazeními ukáže dvě a posuvník.
**edge cases:** aktivita s jedním zařazením nesmí mít prázdný druhý řádek;
skrytí sloupce kódu nesmí posunout ostatní sloupce mimo kartu.
**risk:** `Visible` na sloupcích galerie mění šířky — hlídá `kontrola_prekryvu`.

### C. Dashboard — co: nová obrazovka `src/app_src/scr_Dashboard.pa.yaml`

Styl podle `powerApps-MessageCenterDashboard`: tmavý pruh s velkými čísly vpravo,
pod ním karty s podílem, chip filtry, plochý seznam.

Rozhodnuto 21.08.2026: **dashboard je úvodní obrazovka appky** (na seznam
aktivit se jde tlačítkem) a **rozpad jde po hierarchii A–P–DP–aktivita**;
pohledy podle útvarů a podle stavu zmapování se teď nestaví.

Obsah: **KPI** (agend, procesů, dílčích procesů, aktivit, z toho schváleno
a pracovní, podíl zmapovaných dílčích procesů) a hlavně **klikací rozpad** —
sloupec agend → klik rozbalí procesy dané agendy → dílčí procesy → aktivity,
s drobečkovou navigací a počty u každé úrovně. Z aktivity vede otevření detailu.

**verify:** `check_app.py` + `check_solution.py` nad novým balíkem; ve Studiu:
součty KPI sedí na počty v listech (7 / 46 / 250 / 46 dnes), klik na agendu
zúží druhý sloupec jen na její procesy, drobečková navigace se vrací o úroveň,
zpět na seznam funguje.
**edge cases:** delegace — počty nad 2 000 aktivitami; agenda bez procesů;
dílčí proces bez aktivit (běžný stav, 250 vs. 46).
**risk:** `CountRows` nad SharePointem se nedeleguje (známé z 1.0.0.20) —
čísla se musí počítat nad načtenými kolekcemi a popisek to musí říkat.

### D. Zadávací obrazovky pro agendu, proces a dílčí proces (po C)

Dnes jde založit jen aktivita (`scr_Detail`). Číselníky agend, procesů a dílčích
procesů se dají doplnit jedině ručně v SharePointu, což je pro správce rámce
slepé místo — nový proces musí vzniknout dřív, než pod něj půjde zařadit
aktivita.

**Rozhodnutí (21.08.2026):** jedna obrazovka `scr_Ciselnik` pro všechny tři
úrovně, ne tři samostatné. Formulář se liší jen počtem nadřazených polí
(agenda žádné, proces jedno, dílčí proces dvě); tři skoro shodné obrazovky by
znamenaly trojí údržbu téhož vzorce pro přidělení kódu. Úroveň drží
`varUrovenTyp` ∈ `agenda` / `proces` / `dilci` a přepíná se segmentovými
tlačítky nahoře — to je zároveň ten „průvodce": uživatel vidí všechny tři
možnosti a k nim nápovědu podle Metodiky (kdo je vlastník, co ta úroveň je).

**D1. Nová obrazovka — co: `src/app_src/scr_Ciselnik.pa.yaml`**

- Hlavička jako v `scr_Detail` (tmavý pruh 72 px, šipka zpět na `scr_Dashboard`),
  nadpis podle `varUrovenTyp`.
- Segmentová volba úrovně: `btn_UrovenAgenda` / `btn_UrovenProces` /
  `btn_UrovenDilci`; přepnutí vynuluje rozdělané pole (`Reset` nabídek).
- Nadřazená pole s `Visible` podle úrovně:
  `drp_AgendaC` (proces i dílčí proces), `drp_ProcesC` (jen dílčí proces,
  `Items` filtrované podle vybrané agendy, `OnChange` agendy ho resetuje).
  U agendy místo nich popisek „nejvyšší úroveň, nadřazený prvek nemá".
- `txt_NazevC` (povinné), `drp_VlastnikC` (nepovinné) — nabídka podle úrovně:
  agenda → útvary úrovně `sekce`, proces a dílčí proces → úroveň `odbor`
  (Metodika: vlastníkem agendy je sekce, procesu a dílčího procesu odbor).
  Ukládá se **kód útvaru**, ne „kód · název" — stejně jako `vykonava`
  v `scr_Detail`.
- Pravý panel `rec_NahledC`: co vznikne — úroveň, nadřazený řetěz a **náhled
  kódu**, který se přidělí. Kódy se počítají stejným způsobem jako u aktivit:
  poslední existující v daném prefixu + 1, zleva doplněné nulami
  (agenda 2 místa, proces 2 za pomlčkou, dílčí proces 3).
- Uložení `btn_UlozitC`: validace (nadřazená úroveň + název), přepočet kódu
  nad **zdrojem** (ne nad kolekcí — kvůli čerstvosti), kontrola, že kód mezitím
  nikdo nezabral, `Patch` do příslušného listu v `IfError`, doplnění nového
  záznamu do `colAgendy` / `colProcesy` / `colDilci` a `Set(varAktStale, true)`,
  aby dashboard přepočítal `colStrom`. Pak `Notify` + návrat na dashboard.
- Zapisované hodnoty: `stav_mapovani = "nezmapováno"` (nová položka aktivity
  zatím nemá), `zdroj = "karta"` (nevznikla z rejstříku), u dílčího procesu
  navíc `stav_rejstrik = "využitý"` — do rejstříku ji právě zakládá správce.

**D2. Vstupní bod — co: `src/app_src/scr_Dashboard.pa.yaml`**

Tlačítko `btn_NovaPolozka` v pruhu nad rozpadem: `Set(varUrovenTyp, "agenda")`
a `Navigate(scr_Ciselnik)`. Dashboard je úvodní obrazovka, takže zakládání
číselníku je odsud na jedno kliknutí; ze seznamu aktivit se tam chodit nemusí,
tam se pořizují aktivity.

**D3. Zařazení obrazovky — co: `src/build_app.py`**

`OBRAZOVKY` doplnit o `scr_Ciselnik` na konec — pořadí určuje úvodní obrazovku
a ta musí zůstat `scr_Dashboard`.

**verify:**
1. `python src/check_app.py` — projde beze změny počtu chyb; ve výpisu je
   pět obrazovek a nová obrazovka nepřidá varování o delegaci.
2. `python src/build_app.py --solution input/procesnimapa_1_0_0_24.zip --verze 1.0.0.29`
   a `python src/check_solution.py` — balík se postaví, úvodní obrazovka je
   pořád `scr_Dashboard`, `ScreensOrder` má pět položek.
3. Ve Studiu po importu: založit **proces** v agendě `01` → náhled kódu ukáže
   první volné `01-BB`, po uložení se stejný kód objeví v listu `Procesy`
   a v nabídce procesů na `scr_Detail` **bez restartu appky** (kolekce se
   doplňuje na místě).
4. Založit **dílčí proces** pod tím procesem → kód `01-BB-001`, dashboard ho
   po návratu ukáže ve třetím sloupci s počtem aktivit 0.
5. Založit **agendu** → kód je o jedno vyšší než dosud nejvyšší, `kody.json`
   se nemění (appka do něj nesahá, kódy drží SharePoint).
6. Po publikaci mapy („Obnovit mapu") jsou nové položky ve stromu.

**edge cases:** prázdný číselník v prefixu → první kód `01` / `AA-01` /
`AA-BB-001`; přepnutí úrovně s rozdělaným formulářem (musí vyčistit, ne
nechat viset agendu u nově zakládané agendy); vlastník nevyplněný (nepovinný);
název delší než 255 znaků — SharePoint by ho ořízl, proto `MaxLength` na poli.

**risk a jeho vyhodnocení — kolize kódů při souběžném zakládání:**
`LookUp` před `Patch` není atomický, takže dva správci zakládající tutéž úroveň
ve stejnou vteřinu můžou dostat týž kód. Vyhodnoceno jako **přijatelné bez
pojistného flow**: číselník se mění řádově jednotky případů za měsíc a upravuje
ho úzký okruh správců rámce, zatímco pojistné flow by přidalo asynchronní krok
do jinak okamžité operace a vlastní chybové stavy. Stejný optimistický zámek
má dnes i zakládání aktivit a v provozu se neprojevil.
**Doporučené zpevnění na později (ne teď):** zapnout na sloupci `Title`
u všech čtyř listů „Enforce unique values" — SharePoint pak duplicitu odmítne
a z tiché chyby v datech se stane hláška. Znamená to zásah do `src/schema.json`
a `make_setup.js` včetně dorovnání už založených listů, což je samostatná
úloha, ne součást D.

---

## F6/E — Zařazení v detailu, dialog mazání, úklid osiřelých položek

Zadáno 23.08.2026 po prohlídce 1.0.0.34. Tři nezávislé věci; E1 a E2 jsou
drobné, E3 mění tvar obrazovky číselníku z F6/D.

### E1. Detail aktivity — karta zařazení do dílčích procesů

**co:** `src/app_src/scr_Detail.pa.yaml`

Dnes je `gal_Zarazeni` galerie 300×60 px (dva řádky po 30 px, písmo 10)
zaražená vedle pole Stav a pod ní tlačítko „Další dílčí procesy…". Z obrazovky
není poznat, že jde o zařazení do víc větví mapy — vypadá to jako omylem
vložený prvek.

Nově **karta na celou šířku pravého sloupce (620 px)**:

- `rec_KartaVazby` X=700 Y=516 W=620 H=140, podklad `stylKarta`.
- Nadpis `lbl_l_Vazby` (724, 524): „Zařazení do dílčích procesů (N)". U nové
  aktivity místo počtu text, že zařazení vznikne až po uložení — nadpis je
  tedy vidět vždycky, galerie a tlačítko jen u uložené aktivity. Popisek
  „prázdno" jako samostatný prvek přes galerii nejde: `kontrola_prekryvu`
  hlásí překryv i u prvků s opačným `Visible`.
- `btn_Vazby` vpravo nahoře v kartě (1120, 520, 184×32), text „Spravovat…".
- `gal_Zarazeni` (724, 560, 572×84), `TemplateSize` 28 + varFs*3, písmo
  11 + varFs; kód, název a u primárního štítek „primární" jako na `scr_Vazby`.
- Uvolnění místa: `txt_Predpis` se zkrátí z 620 na 300 px a vedle něj (1020,
  448) se přesune `drp_StavDetail`; pás Y 516–656 tím zůstane celý kartě.

**verify:** `python src/check_app.py` projde bez nových chyb (hlídá i překryvy,
takže přesun stavu a předpisu se ověří sám); po importu ve Studiu má aktivita
se třemi zařazeními všechny tři čitelné, primární má štítek, tlačítko vede
na `scr_Vazby`; u nové aktivity je karta prázdná s vysvětlením.
**edge cases:** aktivita s jedním zařazením (žádný prázdný druhý řádek),
aktivita se šesti (posuvník), nová aktivita (galerie skrytá).
**risk:** přesun stavu a předpisu rozhodí pořadí tabulátoru; vizuálně ověřit
ve Studiu.

### E2. Dialog mazání — velikost a text

**co:** `src/app_src/scr_Seznam.pa.yaml`

Karta dialogu je 520×236 a text 456×84 při písmu 12 — dnešní text se do ní
nevejde a po doplnění o osiřelé položky by přetekl úplně.

- `rec_ModalKarta` a `rec_ModalPruh` 520×236 → **640×360**, souřadnice
  `Parent.Width / 2 - 320`, `Parent.Height / 2 - 180`.
- `lbl_ModalText` 456×84 → **576×200**, tlačítka o řádek níž.
- Text se doplní o odstavec: smazání nemaže, co je pod položkou — podřízené
  záznamy zůstanou bez nadřazené položky a uklidí se ve své vlastní entitě,
  kde je najde filtr osiřelých (E3). U aktivity je to poučení pro symetrii
  s číselníkem, kde sirotci vznikají doopravdy.

**verify:** `check_app.py`; ve Studiu se celý text vejde bez ořezu i při
nejdelším názvu aktivity (220 znaků v datech).
**edge cases:** nejdelší `nazev_kratky` (150 znaků) + kód na prvním řádku.
**risk:** karta na malé obrazovce (1024×640) přeteče — 360 px výšky se vejde.

### E3. Úklid osiřelých položek — filtr a mazání v každé entitě

**co:** `src/app_src/scr_Ciselnik.pa.yaml` (přestavba), `scr_Seznam.pa.yaml`

Sirotek = záznam, jehož nadřazená položka v číselníku neexistuje. Vzniká
smazáním nadřazené položky a dnes ho nikdo neuklidí, protože číselník se
z appky mazat nedá.

| entita | sirotek | kde se uklidí |
|---|---|---|
| Agendy | nemá nadřazenou úroveň — místo toho **bez procesů** | `scr_Ciselnik` |
| Procesy | `agenda_kod` prázdný nebo neodpovídá žádné agendě | `scr_Ciselnik` |
| Dílčí procesy | `proces_kod` prázdný nebo neodpovídá žádnému procesu | `scr_Ciselnik` |
| Aktivity | `dilci_proces_kod` neodpovídá žádnému dílčímu procesu | `scr_Seznam` |

Vazební tabulka vlastní obrazovku nemá; osiřelé vazby maže `RemoveIf` při
mazání aktivity, takže zůstávají mimo rozsah.

**E3a. `scr_Ciselnik` se přestaví na správce číselníku (dva panely):**

- **Vlevo (X 40, W 620)** seznam položek zvolené úrovně: hledání v kódu
  i názvu, chip **vše / osiřelé** (u agendy „bez procesů"), galerie
  `gal_Ciselnik` s kódem, názvem, vlastníkem, ikonou tužky (načte položku do
  formuláře) a ikonou koše. Pod galerií počet a věta, co se filtruje.
- **Vpravo (X 700, W 620)** dosavadní formulář zakládání/úpravy; z náhledového
  panelu zůstane jednořádkový náhled kódu nad tlačítkem, zbytek zabere seznam.
- **Mazání** neběží z řádku galerie: `kontrola_potvrzeni_mazani` to zakazuje
  a má pravdu — koš v řádku se dá trefit omylem. Ikona jen naplní
  `varSmazatC`, maže až tlačítko v modálním dialogu (stejný vzor jako
  `scr_Seznam`), a text dialogu říká, kolik podřízených položek osiří.
- Segmentová volba úrovně přepíná obojí naráz — seznam i formulář.

**E3b. `scr_Seznam`:** k dosavadním filtrům (hledání, sekce, útvar, stav)
přibude chip **jen osiřelé**. Osiřelost se nedeleguje (`LookUp` do kolekce
v `Filter` nad SharePointem), takže se stejně jako fulltext navlékne až na
výsledek delegovaného dotazu; popisek to musí říct a `check_app.py` na to
dostane pojmenovanou výjimku, ne mlčení.

**verify:**
1. `python src/check_app.py` — bez nových chyb; nová výjimka delegace je
   ve výpisu jako varování, ne jako mlčení.
2. Ve Studiu: založit proces v agendě `01`, pak agendu `01` smazat →
   v číselníku procesů ho chip „osiřelé" ukáže, koš + potvrzení ho smaže,
   po návratu na přehled zmizí ze stromu.
3. Chip „osiřelé" nad daty bez sirotků ukáže prázdný seznam s větou
   „žádné osiřelé položky", ne prázdnou plochu.
4. U agendy chip „bez procesů" vybere agendu, pod kterou nic není.
5. V seznamu aktivit chip „jen osiřelé" nad dnešními daty (49 aktivit, všechny
   zařazené) vrátí nula řádků; po smazání dílčího procesu se v něm objeví
   aktivity, které pod ním visely.

**edge cases:** prázdný číselník úrovně; položka s prázdným nadřazeným kódem
(je sirotek); smazání položky, která je právě načtená ve formuláři — formulář
se musí přepnout zpět na zakládání, jinak by uložení psalo do neexistujícího
záznamu; víc než 2 000 aktivit (chip filtruje první okno, popisek to říká).
**risk:** hlavní riziko je záměna „osiřelý" a „prázdný". Osiřelý = chybí
NADŘAZENÁ položka (smaže se bez následků). Prázdný = nemá pod sebou nic
(u agendy). Kdyby se to prohodilo, uklízecí tlačítko by mazalo živé větve —
proto to hlídá pojmenovaný filtr ve vzorci i text v dialogu, ne jen popisek.

---

## F6/F — Sjednocení editace a úklid přímo z přehledu

Zadáno 23.08.2026 po prohlídce 1.0.0.35. Pět bodů, které spolu souvisejí:
editace se stahuje do jedné obrazovky a přehled se z prohlížečky mění
na místo, odkud jde i uklízet.

### F1. Aktivity jako čtvrtá úroveň číselníku

**co:** `src/app_src/scr_Ciselnik.pa.yaml`, zrušení `scr_Seznam.pa.yaml`

Aktivity mají dnes vlastní obrazovku se záložkou v navbaru; agendy, procesy
a dílčí procesy druhou. Dvě obrazovky pro totéž (vybrat záznam, upravit,
smazat) znamenají dvojí zvyk a dvojí údržbu.

- Segmentová volba dostane **čtvrté tlačítko „Aktivity"** (čtyři po 148 px).
- `colCiselnik` dostane i aktivity: `rodic` = dílčí proces, `vlastnik`
  = vykonávající útvar, `uklid` = dílčí proces v číselníku neexistuje.
- **Formulář vpravo aktivity needituje** — aktivita má deset polí a zařazení
  M:N, což se do panelu nevejde. Klik na řádek proto otevře `scr_Detail`.
  Formulářová pole se skryjí a obě tlačítka dole změní text a chování:
  „Otevřít detail" a „Nová aktivita". Nové prvky pro to nevznikají, takže
  ani nový překryv.
- Co si `scr_Seznam` bere s sebou a musí se přenést: **filtry sekce, útvar,
  stav** (druhý filtrační řádek, viditelný jen u aktivit), **řazení klikem
  na hlavičku** sloupce a **mazání s potvrzením** (číselník ho už má, jen
  musí umět smazat i aktivitu včetně jejích vazeb).
- `varDetailZpet` se přepíše z `"seznam"` na `"ciselnik"`.

**verify:** `check_app.py` (5 obrazovek, ne 6, a žádný odkaz na `scr_Seznam`);
ve Studiu: čtvrtý segment ukáže aktivity, klik otevře detail, šipka zpět
se vrátí do číselníku, filtry zúží seznam, řazení podle útvaru funguje.
**edge cases:** aktivita s prázdným `vykonava`; návrat z detailu po uložení;
prázdný výsledek filtru.
**risk:** zrušení obrazovky je nevratné rozhodnutí a `scr_Seznam` uměl víc
než seznam v číselníku. Proto se filtry a řazení přenášejí, ne škrtají.

### F2. Přehled a Editace jako dvě záložky

**co:** `src/app_src/scr_Dashboard.pa.yaml`

Záložka „Seznam aktivit" se mění na **„Editace"** a míří na `scr_Ciselnik`.
Tlačítko „+ Nová položka rejstříku" z navbaru mizí — se záložkou by dělalo
totéž dvakrát.

**verify:** ve Studiu vede záložka na číselník ve stavu zakládání agendy;
zpět z číselníku se vrací na přehled.

### F3. Fulltext na přehledu

**co:** `src/app_src/scr_Dashboard.pa.yaml`

Pole nad stromem hledá **kdekoli uvnitř kódu i názvu na všech čtyřech
úrovních naráz**. Jde to, protože `colStrom` je celá v paměti — hledání se
nedeleguje a ani nemusí. Strop je 2 000 aktivit (`colAkt` je první okno dat,
dnes 49) a popisek to říká.

Při zadaném hledání se strom přepne do **plochého seznamu výsledků**:
zobrazí každý odpovídající uzel bez ohledu na to, co je rozbalené. Rozbalování
by u hledání spíš překáželo — nalezená aktivita se má ukázat rovnou, ne až po
rozkliknutí tří úrovní nad ní.

**verify:** hledání „nábor" najde aktivity i dílčí procesy s tím slovem;
vymazání pole vrátí strom do původního rozbalení (`colOtevrene` se nesahá).
**edge cases:** hledání bez výsledku (popisek, ne prázdná plocha);
hledání + filtr stavu naráz.

### F4. Mazání přímo z přehledu

**co:** `src/app_src/scr_Dashboard.pa.yaml`

Vedle tužky v řádku stromu **koš se stejnou logikou**: nemaže hned, jen
naplní `varSmazatD`, a maže až tlačítko v modálním dialogu. Dialog říká,
kolik podřízených položek tím osiří — u aktivity místo toho, že mizí i její
zařazení do dílčích procesů.

Sloupce ve stromu se o šířku koše posunou doleva (tužka na
`TemplateWidth - 128`, koš na `- 84`).

**verify:** `check_app.py` (`kontrola_potvrzeni_mazani` musí projít — koš
v galerii jen nastavuje proměnnou); ve Studiu smazat dílčí proces a ověřit,
že aktivity pod ním zůstaly a jsou vidět pod chipem osiřelých.
**risk:** koš vedle tužky v řádku se dá trefit omylem — proto dialog
a proto je koš až za překryvnou vrstvou, ne pod ní.

### F5. Osiřelé položky na přehledu

**co:** `src/app_src/scr_Dashboard.pa.yaml`

Chip **„osiřelé"** vedle filtru stavu. Má vlastní důvod existovat: osiřelá
položka se ve stromu **vůbec nezobrazí**, protože strom ukazuje jen uzly,
jejichž předci jsou otevření — a sirotek žádného předka nemá. Bez tohoto
chipu je z přehledu neviditelná, i když v datech je.

Chip proto přepne strom do plochého seznamu osiřelých napříč úrovněmi.
`colStrom` k tomu dostane sloupec `osirely`, počítaný při stavbě kolekce
stejně jako `uklid` v číselníku: proces bez agendy, dílčí proces bez procesu,
aktivita bez dílčího procesu, agenda bez procesů.

**verify:** smazat proces v číselníku, přepnout na přehled → chip ukáže jeho
dílčí procesy; vypnutí chipu vrátí strom.
**edge cases:** žádní sirotci (popisek „nic k úklidu", ne prázdná plocha).
**risk:** stejná past jako v F6/E — „osiřelý" u agendy znamená „prázdná".
Popisek chipu i štítek na řádku to musí říkat, ne mlčet.

### F6. Brána na vzájemně se vylučující prvky

**co:** `src/check_app.py`

`kontrola_prekryvu` dnes hlásí překryv i u dvojice prvků, z nichž je vždycky
vidět jen jeden (`Visible: =X = "a"` proti `=X <> "a"`). Kvůli tomu se
panelový layout musel obcházet. Kontrola se rozšíří o rozpoznání téhle
dvojice — porovná operandy a pozná, že jde o protiklady.

**verify:** mutačně — dva prvky přes sebe se **stejným** Visible musí dál
padat, s protikladným projít.
**risk:** kdyby se rozpoznávání spletlo, brána by přestala hlásit skutečné
překryvy. Proto porovnává celé normalizované operandy, ne podřetězce.

---

## F6/G — Akce nad HTML mapou na přehledu, rolovací nabídky

Zadáno 23.08.2026. **Vzniklo z regrese:** obě tlačítka nad publikovanou mapou
(„Zobrazit v HTML" a „Obnovit mapu") žila v `scr_Seznam` a zrušením té
obrazovky v F6/F zmizela z appky. Zadání je vrátit je na přehled — a protože
pruh nad stromem měl devět ovládacích prvků, schovat ovládání do nabídek.

**co:** `src/app_src/scr_Dashboard.pa.yaml`, `src/check_app.py`

- **Nabídka „HTML mapa ▾"** s volbami *Zobrazit v HTML* (`Launch(varMapaUrl)`)
  a *Obnovit HTML* (`MapaPublishFlow.Run()`). Tlačítko se přejmenovalo
  z „Obnovit mapu": v appce se nemění mapa, ale publikovaná HTML stránka.
- **Nabídka „Rozbalit: … ▾"** sbalí čtyři stupně rozbalení do jednoho
  tlačítka, které rovnou ukazuje, který stupeň platí. Tím se v pruhu uvolní
  místo pro nabídku nad mapou.
- **Stín pod panely** chytá kliknutí mimo nabídku; bez něj by zůstala
  otevřená, dokud by na ni uživatel neklikl znovu.
- `check_app.py`: `kontrola_prekryvu` pozná prvek rozbalovací nabídky podle
  proměnné `varMenu…` a nehlásí ho proti obsahu pod ním — dva prvky **uvnitř
  téže** nabídky ale porovnává dál. `kontrola_adresy_mapy` navíc zakáže
  adresu zapsanou natvrdo do `Launch()`, aby zůstalo jediné místo s adresou.

**verify:** `check_app.py` a `check_solution.py`; v balíku musí zůstat
`MapaPublishFlow` v `References/DataSources.json` — ověřeno, jinak by tlačítko
po importu hlásilo neznámý zdroj. Ve Studiu: obě nabídky se otevřou, klik
mimo je zavře, „Obnovit HTML" spustí flow a je po dobu běhu neaktivní.
**edge cases:** `varMapaUrl` prázdná (volba *Zobrazit v HTML* se skryje);
otevřená nabídka při kliknutí na druhou (první se zavře).
**risk:** obě nabídky leží nad stromem, takže špatné souřadnice by zakryly
řádky — proto je kontrola překryvu uvnitř nabídky zachovaná.

---

## F7 — Připomínky po vyzkoušení 1.0.0.50 (zadáno 24.08.2026)

Zadáno dokumentem `claude 1.docx` po vyzkoušení balíku 1.0.0.50 v tenantu.
Dvě rozhodnutí padla hned při zadání:

- **Export do Wordu bude jen v appce**, HTML mapa ho nedostane. V sandboxu
  SharePointu (origin `null`) je stahování souboru z JS nejisté stejně jako
  `fetch`, takže se do toho neinvestuje — kdo chce dokument, vezme si ho
  z Přehledu.
- **Nová paleta se mapuje jako světlé plochy + plné barvy na svislých
  pruzích**, ne čtyři barevné rodiny pod sebou. Sytá tyrkysová ani zelená
  nesmí nést dlouhý název — přes ně se nedá číst.

Paleta (Adobe Color, dodal zadavatel):
`#110B7A` · `#149EBB` · `#A9C7EC` · `#171F09` · `#3CA050`.

### A1. Menší tři stupně písma — co: `scr_Dashboard.pa.yaml`, `scr_Ciselnik.pa.yaml`

Dnešní `varFs ∈ {0, 2, 4}` se přičítá k základní velikosti, takže střední
stupeň je o 2 body větší než výchozí. Posune se celá trojice o dva body dolů
(`-2 / 0 / +2`), aby střední odpovídal výchozí velikosti Power Apps a velký
byl tím, co je dnes střední.

**verify:** `check_app.py` projde; ve třech snímcích ze Studia (malý, střední,
velký) se do stromu vejde víc řádků než dnes a nejdelší kód `AA-BB-CCC-DDDD`
se v žádném stupni neoříznul.
**edge cases:** výška řádku galerie je odvozená z `varFs` — musí klesnout
s písmem, jinak vznikne prázdné místo pod textem; sloupec kódu má šířku
`191 + varFs * 12`, přepočítat na nové hodnoty.
**risk:** záporná hodnota `varFs` v `Size: =13 + varFs` může u nejmenšího
popisku spadnout pod 8 bodů, což je hranice čitelnosti — projít všechna místa,
kde se `varFs` přičítá k něčemu menšímu než 12.

### A2. Sloupec POLOŽKY — co: `scr_Dashboard.pa.yaml`

Tři změny v hlavičce a řádku stromu:
- hlavička **POLOŽEK → POLOŽKY**,
- sloupec se posune doleva, aby mezi číslem a ikonou **+** vznikla mezera,
- čísla pod hlavičkami VLASTNÍK a POLOŽKY se **vycentrují pod nadpis**
  (dnes je hodnota zarovnaná jinak než nadpis, takže sloupec vypadá rozjetě).

**verify:** `kontrola_prekryvu` v `check_app.py` nesmí najít překryv s ikonami;
vizuálně ze snímku — svislá osa čísla a nadpisu je táž, mezera k „+" aspoň
16 px.
**edge cases:** trojmístné počty (dnes max 251) nesmí přetéct do ikon;
při největším písmu je číslo širší.
**risk:** ikony `+`, tužka a koš mají pevné `X` odvozené od `Parent.Width` —
posun sloupce musí respektovat všechny tři, jinak se sloupec s ikonami
překryje jen u některých šířek okna.

### A3. Přepínač kódu zpátky na Přehled — co: `scr_Dashboard.pa.yaml`

**Regrese z 1.0.0.37.** `varZobrazitKod` řídí viditelnost sloupce KÓD i odsazení
názvu, ale od přestavby pruhu na rolovací nabídky ji nikdo nepřepíná — nastaví
se v `App.OnStart` na `true` a tam zůstane. Vrátí se přepínač do pruhu nad
stromem; výchozí stav **zobrazeno**.

**verify:** nová kontrola v `check_app.py` — každá proměnná, na které visí
`Visible` nebo šířka, musí mít v appce aspoň jedno místo, které ji přepíná
(mutačně ověřit odebráním přepínače). Ručně: klik skryje sloupec a název se
posune doleva.
**edge cases:** pruh je plný, prvek se musí vejít vedle nabídek; při skrytém
kódu se mění odsazení všech čtyř úrovní.
**risk:** týž typ regrese může být i jinde — kontrola z verify ji odhalí
plošně, ne jen tady.

### A4. Ovládací prvky detailů srovnat na Přehled — co: `scr_Ciselnik`, `scr_Detail`, `scr_Vazby`

Zadáno snímkem s vyznačenými prvky a upřesněno v konverzaci: **měřítkem je
Přehled**, ne nová vymyšlená hodnota. Změřeno ve zdrojích:

| obrazovka | dnešní výšky ovládacích prvků | dnešní písmo |
|---|---|---|
| Přehled (**vzor**) | 28 a 32 px | `Size 10–11` |
| Číselník | 36, 40, 44 px | `12–14 + varFs` |
| Detail | 40 a 44 px | `13–14 + varFs` |
| Vazby | 40 px | `13 + varFs` |

Cíl: každý **ovládací** prvek (tlačítko, rozbalovací nabídka, jednořádkové
pole, chip, segment) má na všech obrazovkách výšku **32 px** a písmo
`11 + varFs`. Víceřádková pole pro obsah (znění aktivity, spolupracuje,
vnitřní předpis, text pro OŘ) si výšku nechávají — jsou to plochy pro text,
ne ovládací prvky — ale písmo dostanou stejné.

**verify:** nová kontrola v `check_app.py` — žádný ovládací prvek mimo Přehled
nemá `Height` větší než největší hodnota na Přehledu; mutačně ověřit vrácením
jedné výšky na 44. Ručně: snímky číselníku a detailu vedle Přehledu.
**edge cases:** texty tlačítek („Uložit změny", „Přidat další dílčí proces")
se při největším písmu nesmí oříznout — kontrola šířky proti délce textu;
ikony zpět v hlavičce (56 px) do pravidla nepatří, jsou to prvky navigace.
**risk:** zmenšení výšky bez zmenšení `Y` následujících prvků nechá v obou
formulářích mezery — souřadnice se musí přepočítat po sloupcích, ne po
prvcích. Uvolněné místo padne formulářovým polím, ne prázdnu.

### B. Nová paleta — co: `App.pa.yaml`, obě obrazovky se stromem, `src/mapa_template.html`

Mapování rozhodnuté při zadání:

| úroveň | plocha | pruh |
|---|---|---|
| agenda | `#D5D8EF` | `#110B7A` |
| proces | `#E2E9F6` | `#149EBB` |
| dílčí proces | `#EDF2FA` | `#3CA050` |
| aktivita | `#FAFBFE` | `#A9C7EC` |

Navbar `#110B7A`, akce `#149EBB`, text `#1B2233`, „schváleno" `#3CA050`.
Mapa dostane tytéž hodnoty přes CSS proměnné, aby appka a mapa mluvily touž
řečí.

**verify:** skript spočítá kontrast každé dvojice text/plocha podle WCAG
a selže pod 4,5:1 — pro hlavní text i pro kód řádku, na všech čtyřech
plochách. Ručně: snímek Přehledu a mapy vedle sebe.
**edge cases:** kód řádku je slabší šedomodrý, na `#D5D8EF` je nejtěsnější;
hover a vybraný řádek musí zůstat rozlišitelné od plochy pod sebou.
**risk:** paleta se už dvakrát vrátila jako nepovedená — proto se nejdřív
pošle snímek, teprve pak se staví zbytek.

### C1. Jméno správce z hlavičky mapy — co: `src/build_mapa_flow.py`, `src/mapa_template.html`

`META = {"sekce": "3", "spravce": "Ing. Tomáš Kroutil"}` — obojí je natvrdo
zapsané a je to část otevřeného auditního nálezu **A-08**. Jméno se z hlavičky
odstraní úplně; „Sekce 3" zůstává, dokud se rejstřík netýká víc sekcí.

**verify:** `check_mapa_flow.py` — nové tvrzení „hlavička neobsahuje jméno
osoby" (mutačně ověřit vrácením jména); `check_mapa_html.py` na výstupu.
**edge cases:** starší publikovaná mapa v Site Assets jméno pořád nese, dokud
neproběhne publikace.
**risk:** žádné — ubývá pole, nic na něm nevisí.

### C2. Filtr stavu podle Přehledu — co: `src/mapa_template.html`

Dnešní `#fStav` filtruje podle `stav_mapovani` (zmapované / zmapované jiným
útvarem / nezmapované). Nahradí se filtrem **stavu aktivit** (vše / schváleno /
pracovní), jak ho má Přehled — větev se schová, když v ní po odfiltrování
nezbude žádná aktivita. Legenda pod hlavičkou se přepíše podle toho.

**verify:** `check_mapa_beh.py` — nový průchod v headless prohlížeči: přepnutí
na „schváleno" musí snížit počet viditelných aktivit a schovat prázdné větve;
mutačně ověřit filtrem, který nedělá nic.
**edge cases:** aktivita bez vyplněného stavu (import ji plní hodnotou
`pracovní`, ale ručně založená ji mít nemusí) — patří do „pracovní";
dílčí proces bez aktivit zmizí v obou filtrech kromě „vše".
**risk:** `stav_mapovani` se používá i v odznaku vpravo („jiný útvar",
„nezmapováno") — ten zůstává, mění se jen filtr, jinak by se ztratila
informace, kterou nic jiného nenese.

### C3. Osiřelé položky v mapě — co: `src/mapa_template.html`

Mapa už osiřelé záznamy neztrácí — od 1.0.0.43 je věší pod uzel
„Nezařazené". Přibude **chip „jen osiřelé"**, který ostatní větve schová,
stejně jako to umí Přehled.

**verify:** `check_mapa_beh.py` — klik na chip nechá viditelné jen uzly pod
„Nezařazené"; při nulovém počtu osiřelých je chip neaktivní s vysvětlením.
**edge cases:** žádné osiřelé záznamy (dnes reálný stav); osiřelá aktivita,
jejíž dílčí proces je jen v jiné sekci.
**risk:** chip a hledání se musí kombinovat, ne přebíjet.

### D. Export do Wordu z Přehledu — co: nové flow + `scr_Dashboard.pa.yaml`

Exportuje se **momentální zobrazení**, tedy strom po filtru stavu, hledání
a chipu osiřelých — ne celý rejstřík.

Rozdělení práce: appka pošle flow serializované zobrazení (jeden textový
vstup s JSON), flow z něj složí dokument, uloží ho do Site Assets a vrátí
adresu; appka zavolá `Download()`.

> **Formát:** vznikne `.doc` — HTML dokument, který Word otevře a umí uložit
> jako `.docx`. Skutečné OOXML by ve flow znamenalo premium konektor
> (Encodian, Word Online), a ten v tomhle tenantu neprojde DLP. Je to vědomý
> ústupek, ne opomenutí.

**Datový kontrakt** (jediný vstup `text`, JSON):

```json
{"nadpis": "vše · bez hledání",
 "radky": [{"uroven": 1, "kod": "01", "nazev": "…", "vlastnik": "…", "stav": ""}]}
```

`radky` je **plochý, už seřazený a odfiltrovaný** seznam — flow nic
nestromuje, protože Logic Apps neumí rekurzi. Úroveň 1–4 se v dokumentu
projeví odsazením buňky a tučností.

#### D1. Flow `ExportWordFlow` — co: `src/build_export_flow.py`

Klon obálky z `MapaPublishFlow` (spojení, uzel `<Workflow>`, RootComponent),
**pevné vlastní GUID**, trigger `PowerAppV2` s jedním textovým vstupem a šest
akcí: `Vstup` (json z triggeru) → `Html_radky` (Select na řádky tabulky) →
`Jmeno` (časové razítko) → `Dokument` (Compose celého HTML) → `Uloz`
(CreateFile do `/SiteAssets`) → `Adresa` → `Odpoved` (Response).

**verify:** `check_export_flow.py` (D2).
**edge cases:** prázdné `radky` (dokument vznikne s hlavičkou a bez řádků);
znaky `& < >` v názvech; chybějící `vlastnik`/`stav` (null → prázdná buňka).
**risk:** `Response` v PowerAppV2 flow má strop 120 s běhu — u dnešních
~300 řádků je to daleko, u tisíců ne (popsat mez v návodu).

#### D2. Brána — co: `src/check_export_flow.py`

Tři vrstvy jako u `check_mapa_flow.py`:
1. **struktura** — právě jeden trigger `PowerAppV2` s jedním textovým
   vstupem; řetěz `runAfter` bez děr; každý odkaz `outputs('X')`/`body('X')`
   míří na akci, která je v řetězu před ním; `contentVersion` je `1.0.0.0`;
   zápis souboru necílí na runtime výraz (pravidlo `PatchItem`);
2. **kontrakt** — `Response` vrací `adresa`; jméno souboru končí `.doc`;
   Select čte právě klíče kontraktu;
3. **význam** — výrazy `Html_radky` a `Dokument` se **vytáhnou z balíku**
   a vyhodnotí mini-interpretem nad vzorovým zobrazením. Ověří se, že
   dokument obsahuje všechny čtyři úrovně, tolik řádků, kolik bylo na vstupu,
   že `<` v názvu je escapované a že hlavička nese text filtru.

**verify:** `python src/check_export_flow.py --solution deploy/…zip` →
`OK`; mutačně: odebrání escapování shodí bránu.
**edge cases:** interpret musí zvládnout `concat/replace/coalesce/if/equals/
string/int/sub/mul/join/json/item/outputs/body/triggerBody/decodeUriComponent/
formatDateTime/utcNow`; co nezná, musí **spadnout**, ne tiše vrátit prázdno.
**risk:** interpret se rozejde s Logic Apps — proto se testují jen funkce,
které flow opravdu používá, a builder nesmí použít jinou.

#### D3. Předání flow uživateli — co: `deploy/flow_ExportWord.md`, balík 1.0.0.56

Balík obsahuje flow, appka se nemění. Návod: import → **flow ručně zapnout**
→ otevřít appku ve Studiu → **Add data → ExportWordFlow** → mikro-změna →
Save → Publish → export solution zpět.

**verify:** ruční spuštění flow z designeru s testovacím JSON vyrobí soubor
v Site Assets, který Word otevře.
**risk:** appka musí flow registrovat jako datový zdroj, což jde **jen ve
Studiu** — `References/DataSources.json` nese `FlowNameId`, které přiděluje
až prostředí při importu, takže lokálně se dogenerovat nedá. Bez toho se
`.Run()` nemá na co navázat a build by ho vyhodil.

#### D4. Tlačítko na Přehledu — co: `src/app_src/scr_Dashboard.pa.yaml` (až po dodání zipu)

`colExport` = plochý seznam z `colStrom` po všech filtrech;
`ExportWordFlow.Run(JSON(colExport, JSONFormat.Compact))` → `Download(adresa)`.
Nad ~2 000 řádky se vstup flow nafoukne — tlačítko proto při větším počtu
řekne, ať se zobrazení zúží.

**verify:** `check_app.py` projde; ručně export s filtrem „schváleno" nesmí
obsahovat pracovní aktivity.
**edge cases:** prázdné zobrazení (export se nespustí a řekne proč);
souběžné exporty přepisující týž soubor → název nese časové razítko.
**risk:** `Download()` v mobilním klientu otevře prohlížeč — v návodu zmínit.

### E. Brána a předání

**verify:** všech osm dnešních bran zeleně + tři nové (kontrast, přepínač
proměnné, minimální velikost prvku); `check_solution.py` na výsledném balíku;
teprve pak předat zip.
**risk:** nová paleta se dotkne obou výstupů naráz (appka i mapa) — kdyby se
zadavateli nelíbila, musí jít vrátit jednou změnou hodnot, ne přepisem
prvků. Proto barvy zůstávají v proměnných `styl*` a v CSS proměnných, nikde
natvrdo.

---

## F8 — Kratší notifikace a přenositelnost přes env proměnné (zadáno 28.08.2026)

Dvě zadání z 28.08.2026:

1. **Notifikace v appce svítí moc dlouho** — zkrátit; příklad „po výmazu záznamu".
2. **Import na tenant MPSV selhal na flow** — nešlo napojit SharePoint tabulky.
   Appku se napojit podařilo. Zadání: převést řešení na proměnné, aby bylo
   napojení na nové tabulky snadné.

### Příčina bodu 2 (ověřeno v balíku 1.0.0.61)

Ve všech čtyřech flow je **adresa vývojového webu PPF a GUIDy vývojových listů
natvrdo** — u každé SharePoint akce parametr `dataset`, u čtení a zápisu do
listu `table`. Na MPSV ten web neexistuje, akce jsou neplatné a designer
nenabídne list k přepnutí. Appka je jinde: váže se přes connection reference,
kterou průvodce importem přepojí sám.

Rozsah: `MapaPublishFlow` 7 akcí, `MapaPublishScheduled` 7, `ExportFlow` 1,
`AktualizaceKratkehoNazvu` trigger + 1 akce. Celkem **16 míst** ve flow
a jedno v appce (`varMapaUrl`).

### Oprava dřívějšího tvrzení o zápisových akcích (28.08.2026)

Skill `power-Apps-skill` tvrdí, že **zápisová akce nesmí mít list jako runtime
výraz** (`PatchItem`/`PostItem` si schéma těla odvozují z konkrétního listu),
a na ten výklad jsem nejdřív napsal, že `AktualizaceKratkehoNazvu` převést nejde.
**Plošně to neplatí.** Rozbor šesti produkčních balíků PPF
(repo `luboszprahy/powerApps-vzory-aplikaci-pro-claude` + vzory ve skillu):

| parametr z proměnné | operace | v kolika balících |
|---|---|---|
| `table` | `PatchItem` | 4 |
| `table` | `PostItem` | 3 |
| `table` | `GetOnNewItems` (trigger) | 3 |
| `dataset` | `CreateFile` | 2 |
| `dataset` | `PatchItem` | 6 |

Rozhodující je, že `FloorPlan_1_0_0_19` — balík, ze kterého pochází varování ve
skillu — má `dataset` z proměnné, ale **`table` natvrdo**. Právě jeho přepnutím
ve verzi 1.0.0.21 to tehdy spadlo. Ostatní balíky (Clearstream, Průvodní list,
Správa notifikací, MiddleOffice, MessageCenter) to dělají a běží.

Nejpravděpodobnější skutečná příčina pádu FloorPlanu: proměnná bez vyplněné
hodnoty v cílovém prostředí (skill má tenhle režim selhání doložený jinde),
ne druh akce. Poznámku ve skillu opravit — viz krok 7.

### Tvar proměnné, který funguje

Rozhoduje **typ**. Textová proměnná (typ `100000000`) na dataset/table nestačí.
Funguje **datasetová (typ `100000004`)**, která nese `apiid` konektoru
a `parameterkey`, a u listu navíc `parentdefinitionid` s odkazem na proměnnou
webu. Průvodce importem pak ukáže výběr webu a rozbalovátko listů toho webu,
ne textové pole na GUID.

```xml
<environmentvariabledefinition schemaname="mpsv_listAktivity">
  <apiid>/providers/microsoft.powerapps/apis/shared_sharepointonline</apiid>
  <displayname default="Procesni mapa - Aktivity"> ... </displayname>
  <parameterkey>table</parameterkey>
  <parentdefinitionid><schemaname>mpsv_procesnimapaSite</schemaname></parentdefinitionid>
  <iscustomizable>1</iscustomizable><isrequired>0</isrequired>
  <secretstore>0</secretstore><type>100000004</type>
</environmentvariabledefinition>
```

Odkaz ve flow: `@parameters('Procesni mapa - Aktivity (mpsv_listAktivity)')`.

**Definice záměrně nenese `<defaultvalue>` a balík neobsahuje
`environmentvariablevalues.json`.** Kdyby default byl, import na MPSV by tiše
prošel s adresou PPF — přesně dnešní chyba, jen přesunutá o patro dál. Bez
defaultu se průvodce zeptat musí. Po prvním vyplnění si prostředí hodnotu drží,
další import se už neptá. V `RootComponents` se env proměnné neuvádějí (ověřeno
na všech vzorech), stačí složka `environmentvariabledefinitions/`.

### Rozhodnutí (28.08.2026)

- Notifikace: potvrzení/varování **1000 ms**, chyby **2000 ms**, laditelné
  z jednoho místa v `App.OnStart`.
- `AktualizaceKratkehoNazvu` **zůstává** a převede se stejně jako ostatní.
  (Původní záměr flow zrušit a zkracovat po slovech v Power Fx padl s opravou
  výše — převod je teď levnější než přepis do appky.)
- Napojení **canvas appky** přes `datasetOverride`/`tableNameOverride` se
  odkládá do F8/5 jako volitelné, až budou flow ověřená na DEV.

### Proměnné, které vzniknou

| schemaname | displayname | parameterkey | rodič |
|---|---|---|---|
| `mpsv_procesnimapaSite` | `Procesni mapa - web` | `dataset` | — |
| `mpsv_listAgendy` | `Procesni mapa - Agendy` | `table` | site |
| `mpsv_listProcesy` | `Procesni mapa - Procesy` | `table` | site |
| `mpsv_listDilciProcesy` | `Procesni mapa - Dilci procesy` | `table` | site |
| `mpsv_listAktivity` | `Procesni mapa - Aktivity` | `table` | site |
| `mpsv_listVazby` | `Procesni mapa - Vazby` | `table` | site |

Prefix `mpsv_` podle publishera balíku (canvas app `mpsv_procesnimapa_319bc`).
Zobrazované názvy bez diakritiky — jdou do `@parameters(...)` uvnitř JSON flow
i do XML definice.

### Kroky

```
0. [Prostředí] — co: .venv na tomto stroji (chybí; není ani pac)
   verify: .venv/Scripts/python.exe -c "import yaml, openpyxl" projde bez chyby;
           check_app.py doběhne a vypíše stejné počty jako HANDOVER (163 prvků,
           1584 vzorců)
   edge cases: stroj bez pac -> build_app.py --bez-pac; základem musí být
           deploy/procesnimapa_1_0_0_61.zip (nese LoadFromYaml=true), NE
           input/procesnimapa_1_0_0_57.zip (export ze Studia, YAML nenese)
   risk: runs/app_build/pac je gitignorovaný a na tomto stroji chybí -> build
           s pac by spadl; --bez-pac to obchází

1. [Notify] — co: src/app_src/App.pa.yaml (OnStart) + 27 volání Notify
      v scr_Ciselnik/scr_Dashboard/scr_Detail/scr_Vazby.pa.yaml
   Set(varNotifyMs, 1000); Set(varNotifyChybaMs, 2000) v OnStart;
   každé Notify dostane třetí argument podle typu.
   verify: nová brána kontrola_notify() v check_app.py — každé Notify má právě
           3 argumenty, NotificationType.Error používá varNotifyChybaMs,
           ostatní varNotifyMs, obě proměnné jsou v App.OnStart nastavené.
           Mutační test: (a) ubrat třetí argument u jednoho Notify,
           (b) prohodit varNotifyMs za varNotifyChybaMs u chyby,
           (c) smazat Set z OnStart — brána musí spadnout ve všech třech.
   edge cases: Notify(varChybaC, NotificationType.Warning) je varování, ne chyba
           -> 1000 ms; víceřádkové Notify přes YAML blok (scr_Ciselnik:1304)
   risk: parsování víceřádkových volání regulárem; brána musí počítat argumenty
           až po složení celého vzorce, ne po řádcích

2. [Modul proměnných] — co: nový src/env_promenne.py
   DEFINICE (6 položek), xml(schema) -> obsah definičního souboru,
   param(schema) -> odkaz @parameters, vloz_do_solution(polozky) -> doplní
   environmentvariabledefinitions/*.
   verify: nová brána src/check_env.py — XML je well-formed (ElementTree),
           má type 100000004, apiid konektoru, správný parameterkey,
           pět listových má parentdefinitionid na site, žádná nemá
           defaultvalue, tvar param() sedí na očekávaný regulár.
   edge cases: XML entity v displayname (žádná diakritika ani ampersand)
   risk: špatný parameterkey by import přijal a flow by pak nešlo zapnout

3. [Flow na proměnné] — co: build_mapa_flow.py, build_export_flow.py,
      build_flow.py, add_mapa_schedule.py + build_app.py (vložení definic)
   Místo konkrétní adresy/GUIDu emitovat param(...); build_app.dokonci()
   vloží definiční soubory do zipu.
   verify: rozšířený check_solution.py — (a) v žádném Workflows/*.json není
           řetězec sharepoint.com, (b) každý dataset/table SharePoint akce
           i triggeru je odkaz na deklarovanou proměnnou, (c) každá
           deklarovaná proměnná je aspoň jednou použitá, (d) v zipu je šest
           definičních souborů a žádný environmentvariablevalues.json.
           Mutační test: vrátit natvrdo URL do jedné akce -> brána spadne.
   edge cases: add_mapa_schedule klonuje MapaPublishFlow — klon musí vyjít
           bajtově shodný v akcích (hlídá check_mapa_flow);
           build_flow.py dnes tvrdě ověřuje, že trigger míří na GUID Aktivit —
           kontrola se přesouvá na "trigger je GetOnUpdatedItems", GUID
           nahradí proměnná
   risk: check_export_flow.py:316 dnes tvrdí opak ("dataset zápisové akce je
           runtime výraz — flow by nešlo zapnout"). Podle rozboru šesti
           produkčních balíků je to tvrzení nesprávné; kontrola se obrací
           a do komentáře patří doklad (Clearstream a Průvodní list mají
           CreateFile s datasetem z proměnné). Potvrdí to až zapnutí na DEV.

4. [Build 1.0.0.62] — co: build_app.py --bez-pac --solution
      deploy/procesnimapa_1_0_0_61.zip --verze 1.0.0.62, pak čtyři flow buildery
      nad výstupem
   verify: všechny brány zeleně (check_app, check_solution, check_schema,
           check_mapa_html, check_mapa_beh, check_mapa_flow, check_flow,
           check_setup.js, check_import.js) + nová check_env.py;
           zipfile.testzip() nad výsledkem; razítko verze v App.pa.yaml = 1.0.0.62
   edge cases: check_mapa_beh potřebuje headless Edge/Chrome — když na stroji
           není, vypsat to jako přeskočené, ne tiše minout
   risk: brány psané proti natvrdo zadané adrese začnou padat legitimně;
           každou takovou opravit vědomě, ne vypnout

5. [Nasazení] — co: make_deploy_mpsv.py, deploy/mpsv/README.md, HANDOVER.md
   README dostane krok "vyplnit šest proměnných v průvodci importem" a ztratí
   krok o ruční kostře AktualizaceKratkehoNazvu v designeru (odpadá).
   03_vypis_guidy.js zůstává jako kontrola, GUIDy se do buildu už neopisují.
   verify: README krok za krokem projít proti seznamu souborů ve složce;
           check_solution potvrdí, že zip ve složce je 1.0.0.62
   edge cases: na DEV se průvodce po upgradu zeptá taky (dosud hodnoty neměl)
   risk: uživatel průvodce proklikne bez vyplnění -> flow spadnou na prázdném
           datasetu; patří do README tučně

6. [Ověření na DEV] — co: uživatel importuje 1.0.0.62 na PPF DEV
   verify: (a) průvodce nabídne šest proměnných a u listů rozbalovátko,
           (b) všechna čtyři flow jdou zapnout — tím padne/potvrdí riziko
           z kroku 3, (c) Obnovit HTML doběhne a mapa se přegeneruje,
           (d) export do Wordu i Excelu stáhne soubor,
           (e) změna názvu aktivity srovná nazev_kratky,
           (f) notifikace zhasnou do vteřiny, chybová do dvou.
   risk: kdyby CreateFile s runtime datasetem přece jen nešlo zapnout, fallback
           je nechat to jediné pole natvrdo a generovat ho build skriptem

7. [Skill] — co: doplnit do power-Apps-skill opravu tvrzení o zápisových akcích
   verify: v skillu je uvedeno, které balíky to dokládají, a rozlišení
           typ 100000000 vs 100000004
   risk: bez toho se stejná chybná úvaha vrátí v dalším projektu
```

### F8/5 — Napojení canvas appky přes proměnné (volitelné, odloženo)

Appka dnes drží web a GUIDy listů v `<ConnectionReferences>` v
`customizations.xml`. Jde je převést stejným mechanismem — VendorManagement
i Průvodní list to v produkci dělají přes `datasetOverride` / `tableNameOverride`:

```json
"dataSets": {"<web>_mpsv_procesnimapaSite": {
  "datasetOverride": {"name": "<web>", "environmentVariableName": "mpsv_procesnimapaSite"},
  "dataSources": {"Agendy": {"tableName": "<guid>",
     "tableNameOverride": {"name": "<guid>", "environmentVariableName": "mpsv_listAgendy"}}}}}
```

**Proč se to odkládá:** appku se uživateli na MPSV napojit podařilo, takže to
neřeší dnešní blokaci; skill má doložené, že **jedna proměnná bez hodnoty
shodí napojení celé connection**, tedy i listů, které s ní nesouvisejí; a sahá
se tím do `.msapp` (`References/DataSources.json`), což offline neověřím.
Dělat až po zeleném kroku 6, jako samostatný balík.

---

## F9 — Přenositelnost mezi tenanty bez ručních kroků (zadáno 30.08.2026)

**Zadání:** testovat se bude dál i na PPF DEV, aniž by se střídavými importy
rozbíjelo to, co na druhém tenantu běží.

### Co dnes brání (ověřeno v balících 1.0.0.63 a 1.0.0.66)

Balík z MPSV základny naimportovaný na PPF DEV appku **rozbije**: v
`<ConnectionReferences>` v `customizations.xml` je adresa
`mpsvcr.sharepoint.com/...` a sedm GUIDů tamních listů (1.0.0.63, které na PPF
běželo, tam má `ppfbanka.sharepoint.com/sites/DigiData_D/testovaci_subsajta/procesnimapa`).
Po importu by appka ukazovala na listy, které na PPF nejsou, `App.OnStart`
spadne na prvním `ClearCollect(colAgendy, …)` a nenačte **nic** — týž režim
selhání jako 28.08. na MPSV, jen obráceně.

Tři místa se liší mezi tenanty:

| co | kde | dnes |
|---|---|---|
| napojení appky na 7 zdrojů | `<ConnectionReferences>` | ručně ve Studiu, 7× odebrat a přidat |
| `varMapaUrl` | `App.OnStart` natvrdo | ruční změna v YAML |
| GUID listu Aktivity | `PatchItem` ve flow | `build_flow.py --list-aktivity <GUID>` — hotovo |

### Klíčové zjištění průzkumu: do `.msapp` se nesahá

Vzory `MiddleOfficeParametrizace_1_2_0_3` a `VendorManagement_1_0_0_5` mají
overridy **jen v `customizations.xml`**. V `.msapp/References/DataSources.json`
zůstává `DatasetName` čistá URL a `TableName` holý GUID — žádný override tam
není. Tím padá hlavní důvod, proč se F8/5 odkládalo („sahá se do `.msapp`,
což offline neověřím").

Ověřený tvar (MiddleOffice, produkce) — klíč datasetu je **URL + `_` + schemaname**:

```json
"dataSets": {
  "https://…/testovaci_subsajta_ppf_sourceSiteParametrizace": {
    "datasetOverride": {
      "name": "https://…/testovaci_subsajta",
      "environmentVariableName": "ppf_sourceSiteParametrizace"},
    "dataSources": {
      "middleOfficeScenarioDefinitions": {
        "tableName": "60e610d7-…",
        "tableNameOverride": {
          "name": "60e610d7-…",
          "environmentVariableName": "ppf_middleOfficeScenarioDefinitions"}}}}}
```

### Adresa mapy: levněji než listem `Nastaveni`

Původní návrh byl list `Nastaveni` (F3 v námětech). Průzkum ukázal levnější
cestu, která **nepotřebuje nový list, nové napojení ani kolo přes Studio**:

`ExportFlow` už dnes bere vstup `text` (které zobrazení exportovat) a vrací
`{ adresa: string }` — appka tu adresu používá pro `Download()`. Schéma je
v appce zapečené jako WADL v `References/DataSources.json` a **měnit se nesmí**
(skill: „schéma odpovědi se měnit nesmí"). Měnit ho ale netřeba: stačí poslat
smluvenou hodnotu `text` a nechat flow vrátit adresu mapy místo exportu.
Adresu složí z proměnné `mpsv_procesnimapaSite`, takže je vždy z toho
prostředí, kde appka běží.

Volání patří **až do `OnSelect` tlačítka mapy**, ne do `App.OnStart` — start
appky se tím nezdrží a nedostupné flow neshodí načtení dat.

### Kroky

```
1. [Proměnná pro Útvary, mrtvý zdroj pryč] — co: src/env_promenne.py
   Appka má napojených 7 zdrojů, proměnné existují pro 5. Chybí `Útvary`
   (v schema.json je, proměnnou nemá) a `Dokumenty` (knihovna, kterou
   ŽÁDNÝ vzorec appky nepoužívá — grep přes src/app_src je prázdný).
   Útvary: doplnit `mpsv_listUtvary` do POLOZKY i do mapy zobrazovaný→schema.
   Dokumenty: odebrat z appky jako mrtvý zdroj (z `dataSets` v
   customizations.xml i z DataSources.json v .msapp).
   verify: `check_env` vypíše 7 definic (web + 6 listů) a seznam odpovídá
     listům v schema.json; `check_app` zůstane zelený — tím je doložené,
     že žádný vzorec `Dokumenty` nepoužívá.
   edge cases: název s diakritikou (`Útvary`) jako klíč v JSON i v XML;
     `Vazba aktivita–dílčí proces` má v názvu pomlčku U+2013.
   risk: kdyby `Dokumenty` přece jen někde figurovaly, appka po importu
     spadne na neznámém zdroji. Proto to ověřuje check_app, ne můj úsudek.

2. [Overridy do customizations.xml] — co: src/build_app.py, nová funkce
     `napoj_appku_na_promenne(solution_dir)` volaná z `dokonci()`
   Přepíše blok `dataSets` u SharePoint connection reference: klíč datasetu
   na `<url>_<schemaname webu>`, přidá `datasetOverride` a každému zdroji
   `tableNameOverride` podle mapy z env_promenne.py.
   verify: brána z kroku 3 + ruční diff proti vzoru MiddleOffice — stejné
     klíče, stejná vnořenost, `name` drží původní hodnotu.
   edge cases: obě connection reference na logicflows mají `dataSets: {}` —
     do těch se sahat nesmí; JSON je v XML HTML-escapovaný, takže se musí
     unescapovat, upravit a znovu escapovat týmž způsobem.
   risk: špatně poskládaný klíč = appka po importu napojení nenajde.
     Ověří se až importem, offline jen tvarem proti vzoru.

3. [Brána nad overridy] — co: src/check_solution.py, kontrola `napojeni_appky`
   Kontroly: (a) každý zdroj v `dataSources` má `tableNameOverride`,
   (b) jeho `environmentVariableName` je proměnná deklarovaná v balíku,
   (c) klíč datasetu = `datasetOverride.name` + "_" + schemaname webu,
   (d) v `dataSets` nezůstal zdroj bez overridu.
   verify: čtyři mutace — vynechaný `tableNameOverride`, odkaz na
     nedeklarovanou proměnnou, klíč bez suffixu, přidaný zdroj bez overridu.
     Každá MUSÍ bránu shodit; zelená brána bez mutací nedokazuje nic.
   edge cases: appka bez overridů (starší základna) — brána musí říct
     „nenapojeno přes proměnné", ne spadnout na chybějícím klíči.
   risk: brána kontroluje tvar, ne funkci. Funkci ověří jedině import.

4. [Adresa mapy z ExportFlow] — co: generátor ExportFlow,
     src/app_src/App.pa.yaml, src/app_src/scr_Dashboard.pa.yaml
   Flow: hned za triggerem větev na `triggerBody()?['text'] = '__mapa__'`
   → Response s adresou složenou z proměnné webu a cesty k souboru v tvaru
   `SiteAssets/Forms/AllItems.aspx?id=…` (náhled knihovny, NE přímý odkaz —
   jinak se mapa stáhne místo zobrazení, ověřeno 20.08.2026).
   Appka: `App.OnStart` nechá `varMapaUrl` prázdné; `OnSelect` tlačítka mapy
   adresu dotáhne přes `IfError(ExportFlow.Run("__mapa__").adresa, "")`
   a teprve pak `Launch()`.
   verify: `check_export_flow` — nový vzorek vstupu `__mapa__` projde
     mini-interpretem a vrátí adresu obsahující `AllItems.aspx?id=`;
     mutace: rozbít skládání adresy a ověřit, že brána spadne.
     `check_solution` kontrola `adresy_ve_flow` musí zůstat zelená — adresa
     se skládá z proměnné, v definici nesmí být natvrdo.
   edge cases: flow vypnuté nebo nedostupné → `IfError` vrátí prázdno
     a tlačítko nesmí spustit `Launch("")`; dvojí kliknutí během čekání.
   risk: schéma WADL se nesmí změnit ani o vlastnost. Kontrola: WADL blok
     v DataSources.json musí zůstat bajtově shodný se základnou.

4b. [Enkódování adresy na ověřený tvar] — co: build_export_flow.py,
     funkce `enkoduj_cestu()`  — HOTOVO 30.08.2026, balík 1.0.0.68
   `encodeUriComponent` nechává `-`, `_` a `.` být; SharePoint je v odkazu
   píše jako `%2D`, `%5F`, `%2E`. Náhrady až po enkódování.
   verify: `vyznam_mapa_vzorek` v check_export_flow složí adresu pro web
     PPF DEV a porovná ji znak po znaku s adresou z reálného kliknutí
     z 20.08.2026. Mutace „enkódování bez náhrad" bránu shodí.
   edge cases: `%` už vzniklá enkódováním se nesmí re-enkódovat — `-`, `_`
     ani `.` se v `%2F` nevyskytují, takže na pořadí náhrad nezáleží.
   risk: `viewid` ověřená adresa měla, skládaná ho nemá. Náhled si bez něj
     má vzít výchozí zobrazení; ověří se až importem.

5. [Build a import na PPF DEV] — HOTOVO 31.08.2026, balík 1.0.0.70.
     Cestou nalezena a opravena chybějící deklarace parametru v ExportFlow
     (viz STATUS „Nález: chybějící deklarace parametru"). Ověřeno v provozu:
     appka čte data přes proměnné, mapa se zobrazí. `viewid` chybět smí.
   Pořadí buildu drží HANDOVER.md §5: build_flow.py PŘED build_app.py.
   `--list-aktivity` = GUID listu Aktivity na PPF DEV (vypíše
   `deploy/mpsv/03_vypis_guidy.js` spuštěný na PPF webu).
   verify: import jako upgrade → v Solutions → Environment variables vyplnit
     web a šest listů PPF → appku otevřít ve Studiu (mikro-změna, Save,
     Publish) → spustit: strom se načte, číselník i vazby ukazují data,
     tlačítko mapy otevře mapu, export do Wordu i Excelu stáhne soubor.
     Flow po importu ručně zapnout.
   edge cases: proměnná, jejíž hodnota se při importu nepropíše (stalo se
     28.08. u `mpsv_listAgendy`) — zkontrolovat všech sedm PŘED zapínáním flow.
   risk: první import s overridy. Když appka nenačte data, je to buď
     nevyplněná proměnná, nebo špatný tvar overridu — rozliší se pohledem
     do panelu Data, na co je zdroj napojený.

6. [Zpět na MPSV] — ODLOŽENO 31.08.2026: uživatel nemá několik dní
     přístup do tenantu MPSV. Balík 1.0.0.71 smazán (postavený před opravou
     deklarací parametrů, na MPSV by shodil MapaPublishFlow). Až bude
     přístup, postaví se nový z tehdy aktuálního balíku — jméno souboru
     se odvozuje z verze, takže dva tenanty = dvě verze.
   Po zeleném PPF: `--list-aktivity` na GUID MPSV, build, import na MPSV,
   vyplnit proměnné, ověřit stejným seznamem jako v kroku 5.
   verify: obě prostředí běží ze stejného zdroje a liší se jen tím GUIDem.
   risk: jediný, ale reálný — MPSV je prostředí, kde už appku někdo používá.
     Import dělat po dohodě, ne mimochodem.
```

### Co zůstane ruční i po F9

- **GUID listu Aktivity** v `PatchItem` — z proměnné to nejde (ověřeno
  28.08. v provozu, `OpenApiOperationParameterValidationFailed`). Zůstává
  parametr `--list-aktivity`, tedy dva balíky z jednoho zdroje.
- **Vyplnění proměnných** při prvním importu do prostředí. Prostředí si je
  pak drží, další import se neptá.
- **Mikro-změna + Save + Publish** ve Studiu po každém importu a **ruční
  zapnutí flow** — to import neumí a nikdy neuměl.

---

## F10 — Životní cyklus kódu: přesun jako zánik + vznik (zadáno 30.08.2026)

**Rozhodnutí zadavatele (30.08.2026 18:08): varianta C — zánik a vznik.**
Přesun položky pod jiného rodiče neznamená přepis kódu. Starý kód se uzavře
a zůstane v evidenci jako doklad, nový kód vznikne pod novým rodičem a obě
strany na sebe ukazují.

Tím kód navždy znamená jednu jedinou věc — což je vlastnost, kterou po
schválení organizačního řádu už nejde dodělat zpětně. Volba je konzervativnější
než přečíslování a nikdy se nebude migrovat.

### Co to stojí — ať to není překvapení

Přesun **procesu** s 8 dílčími procesy a 40 aktivitami uzavře 49 kódů a založí
49 nových, protože každému potomkovi se mění prefix. To je podstata varianty C:
uzavírá se každý záznam, jehož kód se mění, ne jen ten, který se fyzicky
přesouvá. V mapovací fázi, kdy jsou opravy zařazení časté, tak evidence poroste
rychleji, než by rostla přečíslováním.

Proto **uzavřené kódy nejdou do živých listů**, ale do samostatného listu
`HistorieKodu` (viz krok 1). Živé listy tím zůstanou čisté a nepřiblíží se
delegačnímu stropu 2 000 rychleji, než musí (souvislost s K1–K4 níže).

### Pravidla, která z varianty C plynou

1. **Uzavřený kód se nikdy nerecykluje.** Přidělovací vzorec musí brát maximum
   přes živý list **i přes historii**.
2. **Uzavřený záznam se nemaže.** Je to doklad, ne odpad.
3. **Uzavřené kódy nejdou do mapy, do stromu ani do textu OŘ.** Dohledatelné
   jsou přes filtr „zobrazit historii" a přes odkaz z nástupce.
4. **Přesun je kaskáda.** Uzavírá se celý podstrom, protože prefix se mění všem.
5. **Kaskáda je jedna transakce s protokolem.** Metodika vyžaduje, aby změny
   byly verzované a schvalované — protokol je to, co se schvaluje.

### Nález, kvůli kterému to není hypotetické (30.08.2026)

Appka dnes přesun o úroveň níž **umí a řeší ho tiše variantou A** (kód zůstane,
rodič se změní, prefix začne lhát):

- `drp_Dilci` je editovatelný i u existující aktivity
  (`DisplayMode.Edit`, `scr_Detail.pa.yaml:235`),
- při uložení se přepíše `dilci_proces_kod` a přesype vazební tabulka
  (`scr_Detail.pa.yaml:712–741`),
- ale `varNovyKod` je u existujícího záznamu `varAktivita.Title`
  (`scr_Detail.pa.yaml:698`) — **kód zůstane starý.**

Tooltip u toho dropdownu přitom tvrdí „určuje kód aktivity a její primární
zařazení", což platí jen při zakládání. Zjištěno čtením YAML, ne během appky.

Proto je krok 2 první na řadě: je to nejmenší instance téže operace a ověří
celý návrh na reálných datech dřív, než se pustíme do kaskády nad procesem.

### Kroky

```
1. [List HistorieKodu a sloupce nástupnictví] — HOTOVO 31.08.2026
     (src/schema.json, src/check_schema.py, src/make_import.py,
      src/check_setup.js; make_setup.py se měnit nemusel, je schéma-řízený.
      Mutačně ověřeno 4/4. `deploy/mpsv/` se přegeneruje až s krokem 2.)
   Nový list `HistorieKodu` (jeden pro všechny úrovně):
     Title = uzavřený kód (přirozený klíč), uroven (Choice: agenda/proces/
     dilci_proces/aktivita), nazev, nastupce_kod (Text, prázdné = zrušeno bez
     náhrady), duvod (Note), datum (DateTime), kdo (Text).
   Živé listy Procesy / DilciProcesy / Aktivity dostanou `puvodni_kod` (Text)
     — odkaz na předchůdce; prázdné u položek, které vznikly rovnou.
   POZOR na názvosloví: list Aktivity už má sloupec `stav`
     (pracovní/schváleno) — to je schvalovací stav, ne životní cyklus kódu.
     Proto se sem žádný druhý `stav` nezavádí; uzavřenost je dána tím,
     že kód JE v HistorieKodu.
   verify: `check_schema.py` projde; `node src/check_setup.js` (32 kontrol)
     rozšířen o nový list — musí ohlásit chybu, když sloupec chybí.
     Mutace: odeber `nastupce_kod` ze schématu → check_setup musí spadnout.
   edge cases: interní názvy bez diakritiky (konvence projektu);
     `Options = 13` u zakládání sloupců, ať jsou vidět ve výchozím zobrazení.
   risk: nový list = sedmá proměnná prostředí navíc (celkem osm). Musí se
     doplnit do env_promenne.py, jinak appka po přenosu zdroj nenajde.

2. [Přesun aktivity = uzavření + vznik] — co: src/app_src/scr_Detail.pa.yaml
   Změna výběru dílčího procesu u EXISTUJÍCÍ aktivity už nesmí jen přepsat
   `dilci_proces_kod`. Nově: potvrzovací modál („kód 07-08-001-0006 se uzavře,
   vznikne nový pod 03-02-005"), pak Patch do HistorieKodu, založení nové
   aktivity s novým kódem a `puvodni_kod`, převod VŠECH vazeb (primární
   i vedlejší) na nový kód, smazání vazeb starého.
   verify: `check_app.py` — nová kontrola, že žádný vzorec nepatchuje
     `dilci_proces_kod` na existujícím záznamu bez zápisu do HistorieKodu.
     Mutace: vrať původní chování → kontrola musí spadnout.
     Ruční test na PPF DEV: přesuň aktivitu, ověř, že starý kód je v historii
     s vyplněným `nastupce_kod`, nový má `puvodni_kod`, vazby sedí a mapa
     ukazuje aktivitu jen jednou, pod novým dílčím procesem.
   edge cases: aktivita zařazená do víc dílčích procesů — přesouvá se
     PRIMÁRNÍ zařazení, vedlejší se musí přenést, ne zahodit;
     dvojí kliknutí během ukládání; přesun zpět tam, odkud přišla
     (musí vzniknout TŘETÍ kód, ne oživit první — pravidlo 1).
   risk: nejsložitější místo je vazební tabulka. Když se převod vazeb udělá
     půlkou, vzniknou osiřelé vazby na neexistující kód. Proto pořadí:
     nejdřív založ nové vazby, pak smaž staré — sirotek je pak nanejvýš
     duplicita, ne ztráta.

3. [Přidělování kódů respektuje historii] — co: scr_Ciselnik.pa.yaml
     (4 místa: agenda 1129/1244, proces, dílčí proces 1143/1165/1255/1273),
     scr_Detail.pa.yaml:686 (aktivita)
   Maximum se nově bere přes živý list I HistorieKodu pro týž prefix.
   verify: `check_app.py` — kontrola, že každý přidělovací vzorec sahá na obě
     množiny. Mutace: uber jednu z nich → spadne.
     Datový test: uzavři kód 05-03, založ nový proces pod agendou 05 →
     MUSÍ dostat 05-04, ne 05-03.
   edge cases: prázdná historie (`Right("",4)` → prázdno → +1 = 1, dnešní
     chování zachovat); prefix, který v historii je a v živém listu ne.
   risk: `StartsWith` je delegovatelný, `Sort` nad filtrovaným listem taky —
     ale dvojnásobek dotazů na každém založení. Měřit, ne odhadovat.

4. [Přesun dílčího procesu a procesu — kaskáda] — HOTOVO 03.09.2026 (1.0.0.93)
     jako `PresunFlow` — co: src/build_presun_flow.py, src/check_presun_flow.py,
     src/mutace_presun.py, src/app_src/scr_Presun.pa.yaml, deploy/flow_Presun.md

   DVĚ OTOČKY BĚHEM JEDNOHO VEČERA, obě zapsané, ať se nezapomene proč:

   (a) Nejdřív jsem to chtěl udělat CELÉ V APPCE. Argument: kaskáda není
       rekurzivní (hierarchie má pevné tři úrovně, stačí tři průchody)
       a nové flow by znamenalo dvoukolový postup se Studiem. Appka přitom
       má všechny listy připojené včetně `Historie kódů` — ověřeno
       v `References/DataSources.json` balíku 92, devět zdrojů. (Poznámka
       v `env_promenne.py`, že HistorieKodu appka připojenou nemá, je
       zastaralá; napojení dodělal `napoj_appku_na_promenne`.)

   (b) Uživatel nabídl, že kolo se Studiem udělá — a tím padl jediný důvod
       pro appku. Rozhodlo: kaskáda je ~240 zápisů, v appce běží v prohlížeči
       a zavření okna ji přeruší uprostřed, kdežto `Foreach` v Logic Apps
       doběhne na serveru a je vidět v run history.

   POZOR na argument, který NEPLATÍ: sliboval jsem `$batch` po stovkách.
   Projekt `$batch` vědomě nepoužívá (`RestoreFlow` má u toho poznámku, že
   multipart changeset se v Logic Apps skládá ručně a chyba se pozná až za
   běhu). PresunFlow zapisuje po jednom stejně jako obnova.

   PRAVIDLO PŘEČÍSLOVÁNÍ: nové číslo dostane JEN ta úroveň, která se stěhuje.
   Potomci dědí nový prefix a ponechají si své pořadové číslo:
     proces 07-08 → 03-05  (první volné BB v cílové agendě)
       dílčí proces 07-08-001 → 03-05-001   (CCC beze změny)
         aktivita  07-08-001-0006 → 03-05-001-0006  (DDDD beze změny)
   Hledat pod novým rodičem volná CCC/DDDD není potřeba: číslují se v rámci
   svého rodiče, a ten je nový, takže jsou volná všechna. Tím je jediné nové
   číslo v celé kaskádě to jedno na přesouvané úrovni; zbytek je náhrada
   prefixu. (Totéž o úroveň níž: dílčí proces dostane nové CCC pod cílovým
   procesem, jeho aktivity si nechají DDDD.)

```
4a. [Obrazovka scr_Presun] — co: src/app_src/scr_Presun.pa.yaml,
    src/build_app.py (seznam OBRAZOVKY), vstup z scr_Ciselnik
    Tvar shodný s scr_Nahled, protože je to táž úloha: vyber → spočítej
    nanečisto → podívej se, co z toho vyjde → teprve pak zapiš.
    Nahoře co se stěhuje (kód + název + počty pod ním), pak výběr cíle
    (agenda u procesu; agenda + proces u dílčího procesu), povinný důvod,
    tlačítko Spočítat náhled, galerie starý kód → nový kód přes celý
    podstrom, souhrn, a Provést přesun s potvrzovacím modálem.
    verify: `check_app.py` projde (nová obrazovka v seznamu, 6 obrazovek).
      Ruční: otevřít z číselníku u procesu, ověřit, že hlavička sedí.
    edge cases: vstup na obrazovku bez vybrané položky (varPresunKod prázdné)
      → všechno zhasnuté a výzva vrátit se do číselníku, ne prázdná obrazovka.
    risk: pruh nabídek na přehledu byl plný na pixel; tady ať se rovnou
      počítá s tím, že obrazovka je samostatná a nic se do ní nemá vejít.

4b. [Výpočet náhledu] — co: btn_SpocitatP.OnSelect
    Nový prefix = kód cíle & "-" & první volné číslo na přesouvané úrovni,
    braný jako maximum přes ŽIVÝ list i `HistorieKodu` (pravidlo 1) — tady
    se to dělá poprvé a je to zároveň referenční tvar pro krok 3.
    colPresun = jeden řádek na každý dotčený kód: { stary, novy, uroven,
    nazev }. Tři průchody: přesouvaná položka, její děti, jejich aktivity.
    Potomci: novy = novyPrefix & "-" & Right(stary, N), kde N je délka
    zbytku kódu za prefixem (3 u dílčího procesu, 8 u aktivity pod procesem,
    4 u aktivity pod dílčím procesem).
    verify: `check_app.py` — nová kontrola, že přidělení sahá na Procesy
      i 'Historie kódů' (u přesunu dílčího procesu na 'Dílčí procesy'
      i historii). Mutace: uber historii → spadne.
      Ruční test na datech: přesuň proces se 3 dílčími procesy a 7 aktivitami,
      porovnej náhled znak po znaku s ručně spočítaným seznamem.
    edge cases: cílová agenda je táž jako současná → tlačítko zhasnuté,
      přesun na místo nedává smysl; cílová agenda má 99 procesů → odmítnout
      s hláškou, ne přetéct na tříciferné BB; přesouvaná položka je technická
      větev 00 → do nabídky se nedostane (číselník ji nezobrazuje).
    risk: `Right(stary, 8)` mlčky vrátí nesmysl, kdyby kód neměl očekávanou
      délku. Náhled to ukáže člověku dřív, než se zapíše — proto je náhled
      povinný krok a ne volitelný.

4c. [Zápis kaskády] — co: btn_ModalProvestP.OnSelect
    POŘADÍ JE PODSTATNÉ a je zvolené tak, aby přerušení uprostřed nechalo
    duplicitu, ne ztrátu:
      1. záloha rejstříku (`ZalohaFlow.Run()`) — je to zároveň protokol,
         který metodika u kaskády vyžaduje, i cesta zpátky;
      2. VZNIK: nové záznamy s novým kódem a `puvodni_kod` (proces, dílčí
         procesy, aktivity);
      3. VAZBY: nové vazby na nové kódy — přepisuje se aktivita_kod
         i dilci_proces_kod, každý zvlášť podle toho, jestli je v colPresun.
         Vedlejší vazba MIMO přesouvaný podstrom se tím přenese taky;
      4. HISTORIE: starý kód do `HistorieKodu` s `nastupce_kod`, důvodem,
         datem a `kdo`;
      5. ZÁNIK: staré vazby a staré záznamy pryč.
    verify: `check_app.py` — kontrola, že zápis do živých listů předchází
      mazání a že každý řádek colPresun jde do HistorieKodu. Mutace:
      prohoď vznik a zánik → spadne; vynech historii → spadne.
      Ruční test na PPF DEV: přesuň proces, ověř všech pět listů, mapu
      a to, že se aktivita ve stromu objeví jednou a pod novým kódem.
    edge cases: aktivita zařazená vedlejší vazbou ven z podstromu (kód se
      mění, cizí dílčí proces ne) a naopak cizí aktivita zařazená dovnitř
      (kód se nemění, dílčí proces ano) — obě větve musí projít;
      dvojí kliknutí na Provést (tlačítko se hned zhasne);
      přesun zpět tam, odkud přišel, musí vyrobit TŘETÍ kód (pravidlo 1).
    risk: největší je počet operací — proces s 8 dílčími procesy a 40
      aktivitami znamená ~240 zápisů. Není to transakce (SharePoint ji
      neumí ani přes flow), proto ta záloha v kroku 1. Druhé riziko je
      delegace: všechno se počítá nad KOLEKCEMI, ne nad zdrojem; colVazby
      se proto plní v OnVisible téhle obrazovky, ne až na přehledu.
```

   verify: `check_presun_flow.py` — mini-interpret nad výrazy vytaženými
     ZE ZIPU (ne z kopie logiky v Pythonu), vzorová větev 1 proces /
     3 dílčí procesy / 7 aktivit → očekávaný seznam dvojic starý→nový kód
     znak po znaku. Mutace: rozbij skládání prefixu → spadne.
   edge cases: cílová agenda nemá volné BB (99 procesů) → flow musí
     odmítnout, ne přetéct; přesun do agendy, kde už proces téhož názvu je;
     souběžná editace aktivity uvnitř přesouvané větve.
   risk: Logic Apps neumí vnořený Foreach — kaskáda přes tři úrovně se musí
     složit jako sourozenecké kroky uvnitř Until, stejně jako vyprazdňování
     složek v servisníUtilitě. Počítat s tím při návrhu, ne až při ladění.

5. [Historie ve stromu a v mapě] — co: scr_Ciselnik, scr_Detail,
     src/mapa_template.html
   Uzavřené kódy se nikde nezobrazují, kromě: filtru „zobrazit historii"
   v číselníku a řádku „vzniklo z <kód>" v detailu.
   verify: `check_mapa_html.py` + `check_mapa_beh.py` — uzavřený kód se
     v HTML mapě nesmí objevit ani v datovém bloku. Mutace: zapeč ho tam
     → kontrola spadne.
   risk: publikační flow zapéká data do HTML — filtr musí být VE FLOW,
     ne až v JS, jinak uzavřené kódy odejdou do souboru a jsou vidět
     ve zdroji stránky.
```

### Co zůstane otevřené

- **Agenda se přesunout nedá** (nemá rodiče), ale zrušit ano. Kroky výše to
  pokrývají: záznam v HistorieKodu s prázdným `nastupce_kod`.
- **Sloučení dvou položek** (dva procesy → jeden) varianta C neřeší; potřebovalo
  by `nastupce_kod` jako víceznačný odkaz. Až se to objeví, ne dřív.

---

## F11 — Záloha a hromadný import (zadáno 30.08.2026)

**Stav: HOTOVO celé** (01.09.2026, balík 1.0.0.87). Krok 1 záloha vč. úklidu,
krok 2 DLP test prošel, krok 3a šablona, 3b import, krok 4 obnova — a nad
3b i 4 jedna společná obrazovka náhledu. Zbývá zkouška na datech v prostředí;
offline brány a mutace jsou zelené.

**Rozhodnutí zadavatele (30.08.2026 18:08): import a záloha oddělené.**
Sdílí tvar tabulky a validační/náhledový engine, ale ne formát a ne operaci.

Důvody, proč to nejde spojit do jednoho tlačítka:

- záloha musí být **úplná a věrná** (všechny sloupce včetně odvozených),
  import **minimální a validovaný** (kdo zakládá 30 aktivit, nesmí vyplňovat
  `nazev_kratky` ani si vymýšlet kódy),
- import **přidává**, restore **přepisuje a maže**.

### Formát: proč Excel jen na import

**Logic Apps neumí sestavit `.xlsx`** — je to zip. `ExportFlow` proto vyrábí
HTML s příponou `.xls`; to se v Excelu otevře, ale zpátky se z toho číst nedá
spolehlivě (Excel ho při uložení přepíše). **Jako záloha to neobstojí.**

CSV je vyloučené a je to změřené (viz `power-Apps-skill`): Excel udělá z kódu
`01-01` datum a z `01` číslo `1`. U evidence, kde je kód klíč, je to fatální.

| směr | formát | jak |
|---|---|---|
| import | pravý `.xlsx` se šablonou formátovanou jako **Tabulka** | Excel Online (Business), `List rows present in a table` |
| záloha | **JSON** snímek | plánované flow do knihovny `Zalohy` |

### Co už je zadarmo a nestaví se znovu

`make_setup.py:157` zapíná na listech **verzování s limitem 500 verzí**.
K tomu koš (93 dní) a obnova na úrovni tenantu. To pokrývá „někdo smazal řádek"
i „vrať mi předchozí znění položky".

Snímek přidává to, co tím pokryté není:
- jak rejstřík vypadal, když se schvalovala verze OŘ (dřívější námět R-5),
- **rollback rozjetého hromadného importu** — ten mění stovky řádků naráz
  a koš pomáhá jen se smazanými, ne se změněnými,
- přenos mezi tenanty, což tenhle projekt reálně dělá.

### Pořadí je záloha → import → restore

Stavět nástroj, který hromadně píše do dat, dřív než je čím to vrátit, je
pozpátku. Záloha je pojistka k importu, ne samostatné přání.

### Kroky

```
1. [Snímek rejstříku] — HOTOVO 31.08.2026 — co: flow `ZalohaFlow` + plánované dvojče
   Čte všech šest (po F10 sedm) listů a zapisuje
   `Zalohy/rejstrik_<RRRR-MM-DD_HHMM>.json`: verze schématu, razítko,
   všechny řádky se všemi sloupci.
   Flow má právě jeden trigger → ruční a plánovaná varianta jsou DVĚ flow,
   akce klonované skriptem z jednoho zdroje (vzor: MapaPublishFlow + jeho
   plánované dvojče, add_mapa_schedule.py).
   verify: `check_zaloha_flow.py` — počet čtených listů odpovídá schématu;
     pagination zapnutá u každého `Get items`; výstup se naparsuje jako JSON
     a počty řádků sedí na vzorová data. Mutace: vypni pagination u jednoho
     listu → kontrola spadne. Plus porovnání akcí obou flow (kdyby se
     rozešly, plán by zálohoval něco jiného než tlačítko a nikdo by si
     nevšiml).
   edge cases: >2 000 řádků na listu — bez pagination se snímek TIŠE ořízne
     a je to nejhorší možná vada zálohy; prázdný list; diakritika v datech
     (`ensure_ascii=False` ekvivalent — JSON z flow musí být UTF-8).
   risk: soubory se hromadí. Úklidové flow po N dnech je pár akcí, ale musí
     nechat naživu poslední snímek každého měsíce, ne mazat podle stáří slepě.
   ÚKLID DOPLNĚN 01.09.2026 (balík 1.0.0.85), a jinak, než plán čekal: místo
     „poslední snímek každého měsíce" se nechává **posledních 20** (zadáno
     uživatelem 13:52). Obava plánu se řeší jinak a lépe — maže se jen to, co
     flow samo vyrobilo, tedy `rejstrik_RRRR-MM-DD_HHMM.json` VČETNĚ délky
     jména. Snímek, který má přežít natrvalo, stačí přejmenovat. Úklid běží
     až po uložení nového snímku, bere `skip` (ne `take`) a maže přes
     `recycle()`, takže omyl není nevratný. Sedm nových mutací.
   PROVEDENO JINAK, NEŽ PLÁN ČEKAL: obě flow staví `src/build_zaloha_flow.py`
     z jedné funkce `akce()`, ne klonováním hotového flow ze zipu (klon zůstal
     jen pro obálku — uzel <Workflow>, RootComponent, spojení). Brána
     `src/check_zaloha_flow.py` má 157 kontrol, mutace `src/mutace_zaloha.py`
     9/9. K tomu bylo potřeba dvoje, co plán neuváděl: knihovnu `Zalohy`
     (`make_setup.py` uměl jen listy, teď i BaseTemplate 101) a osmou proměnnou
     prostředí `mpsv_listHistorieKodu`. Zbývá úklid starých snímků a tlačítko
     v appce — obojí čeká na registraci flow ve Studiu.

2. [Test DLP pro Excel Online (Business)] — co: jedno testovací flow, ručně
     v designeru, PŘED čímkoli dalším z kroku 3
   Jedna akce `List rows present in a table` nad testovacím .xlsx v knihovně.
   Tři kontrolní body: akce se objeví ve vyhledávání, flow jde uložit,
   běh doběhne zeleně a vrátí řádky.
   verify: běh flow, ne úvaha. Ověřit v OBOU tenantech (PPF DEV i MPSV) —
     DLP politiky se liší a projít musí obě.
   edge cases: soubor musí mít formátovanou Tabulku, ne volnou mřížku —
     konektor jinak neuvidí nic a vypadá to jako chyba oprávnění.
   risk: kdyby konektor neprošel, R-1 se musí postavit jinak — fallback je
     povýšit `deploy/mpsv/02_import_dat.js` z vývojářského skriptu na
     nástroj pro správce. To rozhodnutí padne TADY, ne po týdnu stavění.

3a. [Šablona] — HOTOVO 01.09.2026 — co: src/make_sablona.py + src/check_sablona.py
   Vydělený z kroku 3, protože platí v OBOU jeho větvích: ať konektor Excel
   Online projde, nebo se import postaví jako konzolový nástroj pro správce,
   správce vyplňuje týž soubor. Dá se tedy stavět, aniž by byl znám výsledek
   kroku 2.
   verify: `check_sablona.py` — sloupce šablony = sloupce schématu minus
     systémové; mutace: přidej do schématu sloupec a ověř, že kontrola spadne.
   edge cases: sešit musí být formátovaná Tabulka, ne volná mřížka (jinak ho
     konektor neuvidí); kód a odvozené sloupce v šabloně NEJSOU.
   risk: rozejití se schématem — proto se generuje, ne udržuje ručně.
   ROZHODNUTO 01.09.2026 (zadavatel): šablona nese **jen list Aktivity**,
     osm sloupců. Agendy/procesy/dílčí procesy (7/46/250) už z rejstříku
     existují a spravují se v appce; hromadně přibývají aktivity. **Vedlejší
     zařazení (M:N) šablona nenese** — import zakládá aktivitu s primárním
     dílčím procesem, další zařazení se přidávají v appce.
   PROVEDENO NAVÍC oproti plánu: druhý list `Pokyny` (povinnost, omezení
     a max. délka odvozené ze schématu + krátká nápověda ke každému sloupci,
     hlídaná bránou) a rozbalovátko s chybovou hláškou nad sloupcem Stav —
     bez `showErrorMessage` je rozbalovátko ozdoba a překlep projde až
     k importu. Brána `check_sablona.py` má **66 kontrol**, mutace
     `src/mutace_sablona.py` **15/15** (6 mutací schématu, 9 sešitu).
     Zákaz systémových sloupců brána vyslovuje **vlastním seznamem**, ne
     konstantou z generátoru: kdyby z ní sloupec vypadl, obě strany by se
     shodly a nikdo by nezakřičel.

3b. [Hromadný import] — HOTOVO 01.09.2026 (balík 1.0.0.85) — co: src/make_sablona.py (generuje .xlsx
     ze schématu), knihovna `Import`, flow `ImportFlow`, obrazovka náhledu
   Šablona se generuje ZE SCHÉMATU, aby se nemohla rozejít s listy.
   Sloupce, které si systém drží sám (kód, `nazev_kratky`,
   `datum_aktualizace`, `puvodni_kod`), v šabloně NEJSOU.
   Import je dvoufázový: nahrání → náhled („založí se X, změní se Y,
   tohle je duplicita, tohle je chyba na řádku N") → potvrzení → zápis.
   verify: `check_import_flow.py` nad výrazy ze zipu + `check_sablona.py`
     (sloupce šablony = sloupce schématu minus systémové; mutace: přidej
     do schématu sloupec a ověř, že kontrola šablony spadne).
     Datový test: vzorový soubor s 3 platnými řádky, 1 duplicitou,
     1 chybějícím povinným polem a 1 odkazem na neexistující dílčí proces
     → náhled musí vypsat přesně tohle rozdělení a NIC nezapsat.
   edge cases: kód v souboru vyplněný ručně (musí se odmítnout, ne
     respektovat); název delší než 255; středník uvnitř názvu útvaru;
     prázdné řádky na konci tabulky; soubor nahraný dvakrát.
   risk: největší je slepý zápis. Náhled není komfort, je to pojistka —
     bez potvrzovacího kroku se krok 3 nenasazuje.
   ZMĚŘENO, NE ODHADNUTO: konektor snese `file` jako výraz a `table` jménem,
     ale `drive` musí být Graph ID `b!…`. Balík proto nenese ani jedno
     tenantové ID — `source` se skládá z proměnné webu a dvou REST dotazů,
     `drive` se hledá v `/_api/v2.0/drives` podle URL segmentu knihovny.
     Bez toho by se flow na MPSV nepřeneslo.
   PROVEDENO: `src/build_import_flow.py` (31 akcí), brána
     `src/check_import_flow.py` 145 kontrol, mutace `src/mutace_import.py`
     21/21, kontrakt `deploy/flow_Import.md`, knihovna `Import` ve schématu.
     Zbývá obrazovka náhledu — čeká na registraci flow ve Studiu.

4. [Restore ze snímku] — co: flow `RestoreFlow` + tatáž obrazovka náhledu
   Nikdy plánovaně, vždy ručně, vždy s dry-runem a protokolem do knihovny.
   Tvrdé pravidlo: kód ze snímku se vrací TÉMUŽ záznamu; kdyby ten kód mezitím
   patřil něčemu jinému, restore skončí chybou a nezapíše nic.
   verify: `check_restore_flow.py` — mutace „vypusť kontrolu shody kódu"
     musí kontrolu shodit. Datový test na PPF DEV: smaž 5 řádků, obnov ze
     snímku, ověř, že se vrátily s týmiž kódy a vazbami.
   edge cases: snímek starší než změna schématu (verze schématu v souboru
     se musí kontrolovat a při neshodě odmítnout); záznam, který mezitím
     vznikl a ve snímku není (restore ho NESMÍ smazat, jen ohlásit).
   risk: jediná destruktivní operace v projektu. Nasazovat až po zeleném
     kroku 1 a 3, a otestovat na PPF DEV, nikdy poprvé na MPSV.

   NÁVRH ROZHODNUT 01.09.2026, proti tvaru snímku, který záloha opravdu
   vyrábí (`{schema_verze, porizeno, listy.<Nazev>[]}`, klíče řádků = interní
   názvy sloupců, Choice už rozbalený na hodnotu, u každého řádku i `ID`):

   a) **Co znamená „témuž záznamu".** Nikdy nezapisovat podle `ID` ze snímku.
      To ID je stav k okamžiku zálohy; když se mezitím záznam smazal a jiný
      vznikl, patří dnes někomu jinému a zápis podle něj by přepsal cizí řádek
      — tiše a nevratně. Cílové ID se proto VŽDY dohledává v aktuálním listu
      podle `Title` (kódu). `ID` ze snímku slouží jen k tomu, aby náhled uměl
      říct „tenhle záznam mezitím zanikl a vznikl znovu". Tohle je ta kontrola,
      kterou musí mutační test shodit.

   b) **Restore nikdy nemaže.** Řádek, který dnes je a ve snímku není, se jen
      ohlásí. Kombinace „obnov a smaž, co přibylo" by z opravy udělala druhou
      destruktivní operaci a chybný výběr snímku by stál data.

   c) **Zápis přes `SendHTTPRequest`, ne přes `PatchItem`.** Konektorová
      zápisová akce s rozloženým tělem `item/<sloupec>` vyžaduje `table` jako
      GUID natvrdo (jinak flow nejde zapnout) — u sedmi listů by to znamenalo
      sedm GUID vázaných na jeden tenant, tedy nepřenositelný balík. REST
      adresuje list interním názvem ze `schema.json` (`Lists/DilciProcesy`),
      který je na všech tenantech stejný, a web bere z `mpsv_procesnimapaSite`
      jako dosud. `SendHTTPRequest` je součást SharePoint konektoru, v PPF
      povolená (ověřeno u servisníUtility 07.08.2026).

   d) **Po řádku, ne `$batch`.** Multipart changeset by se v Logic Apps skládal
      ručně z hranic a hlaviček a chyba v něm se pozná až za běhu. Šest set
      řádků po jednom je s `Apply to each` a souběžností otázka desítek sekund
      a jde to číst. Kdyby to přestalo stačit, `$batch` je optimalizace, ne
      podmínka funkčnosti.

   e) **Dva režimy, jeden vstup.** `{"soubor": "rejstrik_…json", "rezim":
      "nahled" | "zapis"}`. V režimu náhledu se nesmí provést jediný zápis —
      stejný vzor jako podmínka `Ulozeni` v `ExportFlow`, a stejně se hlídá.
      Odpověď nese počty za každý list: vrátí se / vznikne / beze změny /
      mezitím přibylo / konflikt.

   f) **Pořadí nasazení je dvoukolové** (registrace flow ve Studiu):
      balík s `RestoreFlow` → import → zapnout → Studio Add data → export →
      teprve pak balík s tlačítkem a obrazovkou náhledu. V rozvržení nabídky
      Data ▾ je proto potřeba nechat místo na pátou položku dopředu.

   HOTOVO 01.09.2026 (balík 1.0.0.84): `src/build_restore_flow.py`,
   brána `src/check_restore_flow.py` **531 kontrol**, mutace
   `src/mutace_restore.py` **15/15**, kontrakt `deploy/flow_Restore.md`.
   Zbývá druhé kolo — registrace ve Studiu a obrazovka náhledu.

   Dvě věci, které plán nepředvídal a stály cyklus navíc:

   - **Pořadí buildu je závazné: generátor flow PŘED `build_app.py`.**
     Deklarace použitých parametrů doplňuje jedno místo v buildu
     (`dorovnej_deklarace_parametru`), takže flow přidané až do hotového
     balíku je nemá a spadne za běhu na `InvalidTemplate`. Brána
     `check_solution` to chytila hned; docstring u `build_zaloha_flow.py`
     přitom radí opak — neřídit se jím.
   - **Testovací flow uživatele se z balíku musí vyndat.** `importnewdata`
     veze natvrdo adresu webu PPF (parametry Excel konektoru jsou neprůhledná
     ID vázaná na tenant), takže balík neprošel bránou přenositelnosti.
     Odebírá ho `src/odeber_flow.py`; connection reference na Excel zůstává,
     kvůli ní to flow vzniklo.
```

### Vztah k dřívějším námětům

Tenhle plán nahrazuje námět **R-1** (hromadné pořízení aktivit) a naplňuje
**R-5** (snímek rejstříku k datu). Oba zůstávají v seznamu níže jen jako
historický kontext.

## F12 — sjednocená nabídka Data a vydání šablony (zadáno 01.09.2026)

**Stav:** hotovo, balík **1.0.0.81**. Zadáno z provozu po testu balíku 80.

Tři věci naráz, protože všechny sedí ve stejném pruhu tlačítek nad stromem:

```
1. [Tlačítko Záloha nereaguje] — HOTOVO — co: src/check_app.py, kontrola_prekryvu
   Příčina NENÍ ve flow ani v registraci: popisek `lbl_RozpadPocet`
   („47 řádků") má X = Parent.Width - 240, tedy 1126 na návrhové ploše 1366,
   a ležel tak přes pravých 94 px tlačítka Záloha (X 1120, šířka 100). Protože
   je v souboru později, kreslí se NAD ním — spolkl klik i tooltip. Odtud oba
   hlášené příznaky naráz: „nic nedělá" a „divný tooltip" (byl to tooltip toho
   popisku).
   verify: brána `kontrola_prekryvu` dopočítává souřadnice z výrazů
     `Parent.Width/Height ± N` proti návrhové ploše, místo aby je přeskakovala.
     Spuštěná na vadném zdroji vypsala přesně jeden nález:
     `'btn_Zaloha' a 'lbl_RozpadPocet' se překrývají o 94×28 px` — a nic
     jiného, takže nejde o plošné zpřísnění.
   edge cases: appka má ScaleToFit, takže Parent.Width je vždycky 1366 bez
     ohledu na okno prohlížeče — dopočet je přesný, ne odhad.
   risk: kdyby se návrhová plocha v appce změnila a konstanta v bráně ne,
     počítala by kontrola s cizími čísly. Hlídá to `check_solution.py` proti
     DocumentLayoutWidth/Height v .msapp.

2. [Jedna nabídka místo tří tlačítek] — HOTOVO — co: src/app_src/scr_Dashboard.pa.yaml
   Export ▾, Záloha a (budoucí) Import sjednoceny do rozbalovátka **Data ▾**
   na X = 1016. Položky: Export do Wordu · Export do Excelu · Vzorová tabulka
   pro import · Záloha rejstříku. `varMenuExport` přejmenována na `varMenuData`.
   HTML mapa ▾ zůstává samostatně — zadání mluvilo o exportu, importu a záloze.
   verify: `check_app.py` zeleně (žádný překryv, pořadí nabídek proti stínu,
     odkazy a proměnné) + `check_solution.py` 443 kontrol nad balíkem.
   edge cases: položky nabídky musí být v souboru ZA stínem `rec_MenuStin`,
     jinak stín spolkne klik (1.0.0.41) — hlídá `kontrola_poradi_nabidek`.
   risk: pruh se zkrátil, takže popisek s počtem řádků už na nic neleze;
     kdyby v budoucnu přibylo další tlačítko, brána z kroku 1 to ohlásí.

3. [Vydání vzorové tabulky uživateli] — HOTOVO — co: build_export_flow.py,
     položka btn_SablonaImport, INSTALACE.md krok 5
   Šablona z F11/3a se ke správci dostane stažením z appky. `.xlsx` sestavit
   ve flow nejde (je to zip), takže hotový soubor leží v **Site Assets** a
   `ExportFlow` v novém režimu `__sablona__` vrací jen jeho adresu — appka na
   ni zavolá `Download()`. Nová smluvená hodnota vstupu je totéž, co už dělá
   `__mapa__`, takže flow NEPOTŘEBUJE novou registraci ve Studiu.
   Rozdíl proti mapě: šablona dostane **přímou cestu** k souboru (má se
   stáhnout), mapa odkaz na náhled knihovny (má se zobrazit).
   verify: `check_export_flow.py` 128 kontrol — nová `vyznam_sablona()`
     vyhodnotí flow pro vstup `__sablona__` a ověří, že adresa je přímá cesta
     k `SiteAssets/sablona_import_aktivit.xlsx`, že to není odkaz na náhled
     a že běžný export tím nedostal adresu šablony. Podmínka zápisu se
     kontroluje pro OBA režimy.
   edge cases: soubor v Site Assets se musí jmenovat přesně
     `sablona_import_aktivit.xlsx` — flow adresu skládá z názvu, nevyhledává.
   risk: zapomenutý upload → stáhne se chybová stránka místo sešitu. Proto je
     to bod v INSTALACE.md kroku 5 i řádek v tabulce příznaků.

4. [Exporty do vlastní knihovny] — HOTOVO (balík 1.0.0.82) — co: schema.json
     libraries, build_export_flow.py, check_export_flow.py, INSTALACE.md
   Zadáno z provozu: v Site Assets se za měsíc nashromáždilo přes deset
   vyexportovaných dokumentů vedle publikované mapy a její šablony.
   Úplně bez ukládání to nejde — `Download()` potřebuje adresu souboru na
   webu, takže flow ho musí nejdřív vytvořit; změnilo se místo, ne princip.
   Konstanta `CILOVA_SLOZKA` rozdělena na `/Exporty` (generované dokumenty)
   a `SLOZKA_ASSETS` (mapa, šablona mapy, vzorová tabulka — statické).
   verify: `check_export_flow.py` tvrdí, že `folderPath` zápisové akce je
     právě `/Exporty` — kontrola vrácené adresy sama nestačí, prošla by
     i zápisu jinam. 129 kontrol. Adresa mapy se dál ověřuje proti reálnému
     odkazu z knihovny, takže rozdělení konstant se do ní nemohlo promítnout.
   edge cases: knihovna musí existovat dřív, než flow poprvé zapíše — proto
     se krok 1 instalace spouští znovu i na webu, kde už proběhl.
   risk: exporty porostou dál, jen jinde. Úklid nezadán; až bude vadit, je to
     pár akcí v `ExportFlow` za `Response`, na které volající nečeká.
```

---
## F13 — Číselníky v šabloně, sirotčí aktivity, čas u záloh (zadáno 02.09.2026)

Zadání ze dne: import má být natolik veden číselníky, aby se údaj nemohl
rozejít s rejstříkem; a aby šlo nahrát **holé aktivity** bez zařazení, které
se doplní až v aplikaci. Vedle toho drobnost: u seznamu záloh vidět, kdy
která vznikla.

**Rozhodnutí zadavatele (02.09.2026 18:52):** refresh číselníků nočním flow
jen při změně · dílčí proces dvoustupňově (Proces → Dílčí proces) · sirotci
celé, včetně přiřazení v appce.

### Rozhodnutí, které z toho plyne a je potřeba potvrdit

**Přiřazení sirotka NENÍ přesun podle F10.** Varianta C (zánik + vznik)
uzavírá kód, který něco znamenal. Kód `00-00-000-0001` nikdy platným kódem
nebyl — je to provizorium do chvíle, než správce řekne, kam aktivita patří.
Zapisovat každého sirotka do `HistorieKodu` by historii zaplnilo doklady
o ničem.

Proto: **sirotčí kód se při přiřazení přepíše a do historie nejde.** Rozlišení
je strojové — prefix `00-00-000` znamená „nezařazeno", jakýkoli jiný prefix
znamená platný kód a jeho změna spadá pod F10 krok 2. Obojí je táž obrazovka,
liší se jen tím, odkud se přesouvá.

### Proč šablona nemůže být čerstvá až při stažení

`.xlsx` je zip a flow zip vyrobit neumí — proto je šablona statický soubor
v Site Assets a `ExportFlow` na ni jen odkáže (`__sablona__`). Excel konektor
do **existujícího** sešitu zapisovat umí, ale po jednom řádku: přepis 250
dílčích procesů jsou stovky volání, jednotky minut. Při kliknutí na tlačítko
je to nepoužitelné, v noci nikoho nezajímá.

---

### A. Datum a čas u seznamu záloh

```
A1. [Created do odpovědi režimu seznam] — co: src/build_restore_flow.py,
    krok `Rezim_seznam` → `Soubory` ($select) a `Jmena` (Select)
    Do `$select` přidat `Created`; `Jmena` složí název, oddělovač a datum
    přes `formatDateTime(convertFromUtc(Created, 'Central Europe Standard
    Time'), 'd.M.yyyy H:mm')`.
    Schéma odpovědi se NEMĚNÍ (dál čtyři řetězce) — flow se proto nemusí
    znovu registrovat ve Studiu a appka nepotřebuje druhé kolo.
    verify: `check_restore_flow.py` rozšířit o kontrolu, že `$select` obsahuje
      `Created` a že `Jmena` používá `convertFromUtc` (jinak by se ukazoval
      UTC čas a lišil by se o hodinu/dvě od toho, co uživatel čeká).
      Mutace v `mutace_restore.py`: odeber `Created` ze `$select` → brána
      musí spadnout. Ruční: v appce rozbalit seznam — u každé položky datum.
    edge cases: knihovna prázdná (Select nad prázdným polem projde, `join`
      vrátí prázdný řetězec); soubor nahraný ručně mimo flow (má `Created`
      také, formát jména může být jiný — datum se ukáže, název se nerozbije).
    risk: časové pásmo natvrdo. Pro MPSV i PPF je to totéž pásmo, takže
      to nevadí; kdyby se to někdy měnilo, je to jeden literál.

A2. [Appka pošle flow holý název] — co: src/app_src/scr_Nahled.pa.yaml
    `drp_SouborN.Items` zůstane tím, co vrátí flow (včetně data), ale všude,
    kde se hodnota posílá do flow, se ořízne na část před oddělovačem.
    Týká se i pojistky `varNahledHotovo <> drp_SouborN.Selected.Value` —
    ta porovnává celé zobrazené hodnoty, takže tam se ořezávat NESMÍ,
    jinak by přestala rozlišovat dva snímky se stejným názvem.
    verify: `check_app.py` — nová kontrola, že žádné `Flow.Run` v appce
      nedostane `.Selected.Value` bez oříznutí. Mutace: vrať neoříznutou
      hodnotu → kontrola spadne.
      Ruční: vyber zálohu → Zkontrolovat → flow musí soubor najít
      (kdyby se posílal název i s datem, spadne na `Soubor`).
    edge cases: název souboru sám obsahuje oddělovač — vyloučeno, jména dává
      flow ve tvaru `rejstrik_RRRR-MM-DD_HHMM.json`.
    risk: oříznutí se zapomene na jednom ze dvou míst (náhled/provést) →
      jedno tlačítko funguje, druhé ne. Proto ta kontrola v bráně.
```

---

### B. Číselníky v šabloně a jejich noční refresh

```
B1. [Číselníkový list v šabloně] — co: src/make_sablona.py
    Nový list `Ciselniky` (skrytý, `sheet_state = "hidden"`) se třemi
    pojmenovanými tabulkami: `Cis_Procesy` (kód + název), `Cis_DilciProcesy`
    (kód, název, kód procesu), `Cis_Utvary` (kód + název). Fixní výška
    (600 řádků u dílčích procesů, 200 u zbytku) — rozsah validace musí být
    stálý, protože ho flow nepřepočítává.
    verify: `check_sablona.py` — sešit má list `Ciselniky`, je skrytý, tabulky
      mají očekávaná jména a šířku. Mutace v `mutace_sablona.py`: přejmenuj
      tabulku → brána spadne.
    edge cases: skrytý list jde v Excelu odkrýt — počítá se s tím, není to
      ochrana, jen aby nepřekážel.
    risk: 600 řádků je strop. Až rejstřík naroste, validace přestane pokrývat
      poslední položky — brána proto hlídá, že počet položek < výška tabulky,
      a build spadne dřív, než se to projeví tichým vynecháním.

B2. [Dvoustupňová validace] — co: src/make_sablona.py
    Nový sloupec `Proces (kód)` do tabulky `Aktivity`, hned před dílčí proces.
    Validace: `Proces (kód)` = seznam z `Cis_Procesy`; `Primární dílčí proces
    (kód)` = závislý rozsah přes pojmenovaný rozsah s `OFFSET`/`MATCH` podle
    hodnoty ve sloupci Proces. `Vykonává útvar` = seznam z `Cis_Utvary`.
    Všechny s `allow_blank=True` (prázdno je nově legitimní, viz blok C).
    `Spolupracuje` rozbalovátko NEDOSTANE — je vícehodnotové a Excel umí
    validovat jen jednu hodnotu na buňku; zůstává volným textem.
    verify: `check_sablona.py` — každý číselníkový sloupec má DataValidation
      se správným rozsahem a `allow_blank`. Mutace: odeber validaci u dílčího
      procesu → brána spadne.
      Ruční test (nenahraditelný): otevřít vygenerovaný sešit v Excelu,
      vybrat proces, ověřit, že nabídka dílčích procesů se zúžila jen na jeho
      potomky, a že po změně procesu zůstane v buňce nesmyslná hodnota
      (Excel starou hodnotu nemaže — proto kontrola v ImportFlow zůstává).
    edge cases: `Proces (kód)` je sloupec navíc, který import IGNORUJE —
      slouží jen k filtrování nabídky. Musí se doplnit mezi ignorované,
      jinak ho ImportFlow bude číst jako neznámé pole.
    risk: závislý rozsah přes OFFSET je v Excelu Online vrtkavý. Když se
      ukáže, že tam nefunguje, fallback je jeden dlouhý seznam ve tvaru
      `01-02-003 — Název` (varianta B z nabídky) — proto se před stavbou
      refreshe (B3) ověří ručně otevřením v Excelu Online, ne až v provozu.

B3. POZNÁMKA Z REALIZACE (02.09.2026): zadání tohoto kroku se změnilo.
    Pojmenované rozsahy číselníků jsou PŘESNĚ podle počtu položek, ne natažené
    na strop — strop by do nabídky přidal tolik prázdných řádků, kolik zbývá
    (u osmi útvarů 192). Jenže Excel konektor umí přepsat BUŇKY, ne definici
    pojmenovaného rozsahu; refresh proto sám o sobě NESTAČÍ, jakmile položek
    přibude nebo ubude.
    Zbývají dvě cesty a je potřeba mezi nimi rozhodnout:
      (a) refresh jen přepisuje hodnoty a šablona se přegeneruje ručně, když
          se počet položek změní (jednoduché, ale „automatické" jen zpola);
      (b) číselníky jako Excel Tabulky a pojmenovaný rozsah na jejich sloupec
          (`TabProcesy[Nabídka]`) — rozsah pak roste sám se zápisem řádků.
          Neověřeno; a kaskádové rozsahy P_<kód> jsou podmnožiny, ty takhle
          řešit nejdou tak jako tak.

B3. [Noční refresh číselníků] — co: src/build_ciselnik_flow.py (nové),
    src/check_ciselnik_flow.py (nové), deploy/flow_Ciselnik.md
    Naplánované flow 1x/24 h: přečte `Procesy`, `DilciProcesy`, `Utvary`
    (REST, stránkovaně), spočítá otisk (počet + spojené kódy) a porovná
    s otiskem uloženým v prvním řádku listu `Ciselniky`. Shoda → konec bez
    zápisu. Neshoda → přes Excel konektor přepíše řádky tabulek a uloží nový
    otisk.
    verify: `check_ciselnik_flow.py` (~120 kontrol) + `mutace_ciselnik.py` —
      mutace: odeber porovnání otisku → flow by přepisovalo denně naprázdno,
      brána musí spadnout. Ruční: spustit flow ručně dvakrát za sebou —
      druhý běh musí skončit větví „beze změny" a NESMÍ zapsat ani řádek.
    edge cases: sešit má někdo otevřený v Excelu Online (zámek) → zápis
      selže; flow to musí ohlásit, ne tiše přeskočit. Číselník se zkrátí →
      zbylé řádky se musí VYMAZAT, ne nechat ležet, jinak zůstanou v nabídce
      neexistující kódy.
    risk: zápis po řádcích trvá minuty a Excel konektor je pomalý. Proto
      noční plán a proto porovnání otisku — většinu dní neproběhne nic.
      Druhé riziko: zápis do souboru, který si zrovna někdo stahuje. Řeší
      se tím, že refresh běží ve 3:00, kdy stahování nikdo nedělá.
```

---

### C. Sirotčí aktivity

```
C1. [Pseudo-rodič „nezařazeno"] — co: src/schema.json (seed),
    src/make_import.py, src/setup_sharepoint.js
    Do rejstříku patří tři technické položky: agenda `00` / proces `00-00` /
    dílčí proces `00-00-000`, všechny s názvem „Nezařazeno". Zakládá je
    provisioning, ne import dat — musí existovat i na prázdném webu.
    verify: `node src/check_setup.js` rozšířit o kontrolu, že po provisioningu
      ty tři položky existují. Mutace: odeber seed → kontrola spadne.
    edge cases: mapa, strom a export OŘ nesmí větev `00` zobrazovat jako
      běžnou agendu — vyfiltrovat na jednom místě (`colStrom`), ne v každé
      obrazovce zvlášť.
    risk: kdyby někdo `00-00-000` smazal, import sirotků začne padat na
      neznámý dílčí proces. Proto je to seed provisioningu a ne ruční krok.

C2. [Import bez zařazení] — co: src/build_import_flow.py
    Mezi `S_obsahem` a `Chybne` přibude krok `Doplneny_rodic` (Select), který
    prázdnému `dilci_proces_kod` dosadí `00-00-000`.
    POŘADÍ JE PODSTATNÉ: náhrada MUSÍ být až za `S_obsahem`. Kdyby se dosadilo
    dřív, přestaly by být prázdné řádky prázdné (`vsechny_prazdne` by
    neplatilo) a šablona by při každém importu založila stovky sirotků
    z prázdných řádků pod tabulkou.
    `dilci_proces_kod` zůstává ve schématu `required` — SharePoint list se
    nemění, prázdno řeší import, ne list.
    verify: `check_import_flow.py` — kontrola, že `Doplneny_rodic` běží po
      `S_obsahem` a před `Chybne`. Mutace v `mutace_import.py`: přesuň krok
      před `Prazdne` → brána spadne (to je ta past výše).
      Ruční test na datech: sešit se třemi řádky — jeden úplný, jeden bez
      dílčího procesu, jeden úplně prázdný. Náhled musí ohlásit
      1 k založení + 1 sirotek + 0 chyb, prázdný řádek se nesmí objevit nikde.
    edge cases: řádek s vyplněným procesem, ale prázdným dílčím procesem —
      chová se stejně jako holá aktivita (sloupec Proces import ignoruje).
    risk: nejzávažnější v celé fázi je právě záměna pořadí kroků. Proto
      mutace, ne jen kontrola.

C3. [Sirotci v appce] — HOTOVO 03.09.2026 (1.0.0.92)
    Chip „nezařazené (N)" v pruhu filtrů vedle osiřelých; strom se přepne na
    plochý seznam aktivit s rodičem 00-00-000. Počítá se z colAkt, ne colStrom:
    colStrom nese i vedlejší vazby, takže by chip ukazoval počet ZAŘAZENÍ,
    ne počet aktivit, a nesouhlasil by s kartou AKTIVITY.
    Chip zůstává viditelný i s nulou, dokud je režim zapnutý — jinak by po
    přiřazení posledního sirotka zmizel a strom by zůstal prázdný bez cesty zpět.
    ZÁROVEŇ dotažen edge case z C1: technická větev 00 se skrývá ve stromu,
    v kartách nahoře, ve správě číselníku, v nabídce nadřazené položky
    a v publikované HTML mapě ($filter u všech pěti GetItems v MapaPublishFlow).
    Export z appky se vyřešil sám — bere to, co je vidět ve stromu.
    Pruh filtrů byl plný na pixel: popisek počtu řádků se proto přestěhoval
    do hlavičky stromu, kam patří, a tlačítka nabídek se posunula doprava.
    Tím na sebe vlezly panely obou nabídek — za běhu se vylučují, ale nic to
    nehlídalo, takže to hlídá nová kontrola `vylucne_nabidky` (ověřeno mutací:
    když jeden přepínač zapomene zavřít druhou nabídku, brána spadne).
    Brána `kontrola_nezarazenych` v check_app.py + `$filter` v check_mapa_flow.py.
    Mutačně 4/4 (chybí chip · větev míří jinam · strom nevylučuje 00 ·
    karta počítá technickou položku) a 1/1 na mapě.

C3. PŮVODNÍ ZADÁNÍ — co: src/app_src/scr_Dashboard.pa.yaml
    Filtr / dlaždice „Nezařazené aktivity (N)" na přehledu, která vypíše
    aktivity s prefixem `00-00-000`. Bez toho by sirotky nikdo nenašel.
    verify: `check_app.py` — dlaždice existuje a počítá z `colStrom`.
      Ruční: po importu sirotků musí číslo sedět s počtem z náhledu.
    edge cases: nula sirotků → dlaždice zhasne, ne „0" natvrdo svítící.
    risk: přehled má strop delegace; filtr na prefix `00-00-000` musí jít
      přes už načtenou kolekci, ne přes nový dotaz do SharePointu.

C4. [Přiřazení sirotka] — HOTOVO 03.09.2026 (1.0.0.92)
    Sirotek (`varSirotek`, poznaný v OnVisible podle rodiče 00-00-000) má
    kaskádu odemčenou a při uložení dostane nový kód pod vybraným dílčím
    procesem — týmž vzorcem jako nová aktivita, včetně kolizní pojistky.
    `puvodni_kod` = sirotčí kód, do HistorieKodu se nezapisuje.
    Vazby: nejdřív se VŠECHNY přepíšou na nový kód (i vedlejší), teprve pak
    běží stávající blok, který srovná primární zařazení. V opačném pořadí by
    se mazalo podle kódu, který v tabulce ještě není.
    Uložení sirotka BEZ změny dílčího procesu kód nepřečísluje (`varPresun`) —
    jinak by každé uložení rozdávalo nové 00-00-000-XXXX za nic.
    U aktivity s platným kódem je zamčená CELÁ kaskáda, ne jen dílčí proces:
    se zamčeným jen dílčím procesem by změna agendy vynulovala výběr níž
    a aktivita by pak nešla uložit vůbec.
    NEDODĚLEK, vědomý: přidělení bere maximum jen z živého listu `Aktivity`,
    ne z `HistorieKodu` — ta je zatím prázdná a appka ji nemá připojenou jako
    datový zdroj. Doplní se v F10/3 na všech pěti místech naráz.
    Brána `kontrola_prirazeni_sirotka` v check_app.py, mutačně 4/4
    (odemčená kaskáda · kód jen pro novou · chybí puvodni_kod · vazby se
    nepřepisují).

C4. PŮVODNÍ ZADÁNÍ — co: src/app_src/scr_Detail.pa.yaml
    U aktivity s prefixem `00-00-000` je výběr dílčího procesu editovatelný
    a uložení provede: nový kód pod vybraným rodičem (týmž vzorcem jako
    ImportFlow — maximum přes živý list i `HistorieKodu`, viz F10 pravidlo 1),
    Patch `Title` a `dilci_proces_kod`, přepis vazby v `AktivitaDilciProces`,
    `puvodni_kod` = sirotčí kód. Do `HistorieKodu` se NEZAPISUJE (viz
    rozhodnutí na začátku fáze).
    U aktivity s jakýmkoli JINÝM prefixem zůstává výběr zamčený až do F10/2 —
    dnes se tam totiž tiše děje varianta A (kód zůstane, prefix začne lhát),
    což je nález z F10, který se touto fází NEOPRAVUJE. Zamčení je menší zlo
    než tichá lež v kódu.
    verify: `check_app.py` — kontrola, že větev přiřazení běží jen pro prefix
      `00-00-000` a že u ostatních je `drp_Dilci` v `DisplayMode.View`.
      Mutace: povol editaci všem → kontrola spadne.
      Ruční test na PPF DEV: naimportuj holou aktivitu, přiřaď ji, ověř nový
      kód, vazbu, `puvodni_kod`, a že v `HistorieKodu` NEPŘIBYL řádek.
    edge cases: dva správci přiřadí sirotka současně → oba dostanou týž nový
      kód. Ošetří se tím, že se po Patchi ověří, že kód nebyl mezitím obsazen
      (stejná pojistka jako u zakládání aktivity).
    risk: Patch `Title` mění přirozený klíč. Vazby, které na starý kód
      ukazují, se musí přepsat ve stejném kroku — jinak vznikne osiřelá vazba,
      kterou přehled ukáže jako chybu. Test to musí ověřit explicitně.
```

### Pořadí a proč

`A` první — je hotové rychle a nedotýká se ničeho, co se dál mění.
Pak `C` (sirotci), protože to je vlastní zadání a `B2` na něm závisí
(prázdný dílčí proces musí být legitimní dřív, než šablona nabídne prázdno).
`B3` (noční refresh) jde poslední — je nejdražší a nejmíň naléhavý, číselníky
se dnes mění řádově jednou za týdny.

**Nezávislá brzda:** F11 (import dat) pořád nemá vysvětlené selhání z 01.09.
`C2` mění právě `ImportFlow`, takže se do něj sahá dřív, než se ví, proč
neběžel. Pořadí kroků je proto psané tak, aby se `C2` dala nasadit samostatně
a rozlišilo se, co je nová vada a co ta stará.

---
## Náměty na rozšíření (neschválené, k připomenutí)

Přepracováno 25.08.2026 (původní seznam z 23.08.2026 byl psaný před exportem
a před zrušením `stav_mapovani`). **Nic z toho není zadané ani rozpracované.**
Řazeno podle toho, co projektu chybí nejvíc, ne podle náročnosti.

Východisko, ze kterého to počítám: rejstřík má **7 agend, 46 procesů, 250
dílčích procesů — a 46 aktivit**. Popsaných je 26 dílčích procesů z 251, tedy
zhruba **desetina**. Do 06/2028 se má zmapovat zbytek a z výsledku vzniknout
text organizačního řádu. Tomu má odpovídat i pořadí námětů.

---

### A. Co brzdí běžný provoz

#### R-1 · Hromadné pořízení aktivit — **podle mě jednoznačně první**

Zadavatelka pracuje s excelovými kartami (~45 aktivit na sekci) a sekcí je
sedm. Appka umí zakládat po jedné; hromadný import existuje jen jako
`deploy/mpsv/02_import_dat.js` do konzole prohlížeče — nástroj pro vývojáře,
ne pro správce rámce. Každá další karta dnes znamená 45× proklikat formulář.

**Nově je to levnější, než bylo.** Export do Excelu už umí vyrobit tabulku
v přesném tvaru rejstříku, takže se nabízí **obousměrná cesta**: exportovat
prázdnou nebo rozpracovanou větev → vyplnit v Excelu, na který jsou útvary
zvyklé → nahrát zpět do knihovny → flow založí a aktualizuje.

Klíčové je, aby import **nebyl slepý zápis**: nejdřív náhled „co vznikne /
co se změní / co je duplicita" a teprve po potvrzení zápis. Kódy přiděluje
týž mechanismus jako appka.

**Odhad:** flow nad knihovnou + obrazovka náhledu v appce. Největší riziko je
parsování Excelu ve flow — konektor umí jen tabulky (`Get tables`), takže
šablona musí být formátovaná jako tabulka, ne volná mřížka.

#### R-2 · Pohled „kdo má co dodělat"

Přehled ukazuje součty, ne rozpad podle sekcí a vlastníků. Přitom poměr
zmapovanosti je hlavní metrika projektu a řízení potřebuje odpověď na „který
odbor má kolik dílčích procesů bez jediné aktivity".

Data na to jsou — `colStrom` už nese `aktC`/`aktS` na každé úrovni. Chybí
jen obrazovka: tabulka útvar × (dílčích procesů / z toho popsaných / aktivit
/ z toho schválených) s prokliky do stromu a exportem přes hotové flow.

---

### B. Co projekt dluží svému zadání

#### R-3 · Generování textu organizačního řádu — **nově laciné, dřív drahé**

`PRD.md` to má jako **FR-4, fáze 2, po 06/2028**. Ten odhad platil, dokud
nebylo z čeho dokument skládat. Dnes existuje `ExportFlow`, které z plochého
seznamu řádků staví `.doc` — a pole `text_pro_or` je v listu Aktivity od
začátku. Chybí tedy jen **třetí volba v nabídce Export**: místo tabulky
vysázet text v členění podle vykonávajícího útvaru, ve tvaru vzoru
`VZOR_OŘ - nově sekce 3`.

**Proč to navrhuji předsunout:** je to jediný výstup, kvůli kterému celý
projekt vznikl. Až bude vidět, jak vygenerovaný text vypadá vedle vzoru,
ukáže se, jestli je pole `text_pro_or` vyplňované užitečně — a to je lepší
zjistit u 46 aktivit než u 2 000.

**Riziko:** vzor OŘ má vlastní číslování a formulace („útvar zajišťuje…“),
které se z holého `text_pro_or` nemusí složit. Než se to postaví, patří se
projít vzor a doplnit do PRD, co přesně se generuje a co zůstává ruční.

#### R-4 · Schvalování s rolemi a notifikací

Stav „schváleno" dnes přepne kdokoli s přístupem. Metodika má role (vlastník
procesu, sekční správce, správce rámce), ale bez oprávnění a notifikace je
schválení čestné prohlášení. U evidence, ze které se stane vnitřní předpis,
to dřív nebo později někdo napadne.

Postavitelné bez Dataverse: skupiny SharePointu na role, `stav` přepínatelný
jen členem odpovídající skupiny (kontrola v appce + oprávnění na listu),
notifikace flow do Teams nebo mailem. Vzor na notifikace je ověřený.

#### R-5 · Snímek rejstříku k datu

Až se z rejstříku stane podklad předpisu, bude potřeba odpovědět „jak to
vypadalo, když se to schvalovalo". SharePoint verzuje jednotlivé položky, ale
ne rejstřík jako celek a přes appku se k tomu nikdo nedostane.

Levná varianta: publikační flow už umí vyrobit HTML mapu — ať vedle
`procesni_mapa.html` ukládá i datovanou kopii a v Site Assets vznikne řada
snímků. Dražší varianta: list `Snimky` s odkazem, datem a poznámkou, co se
tehdy schvalovalo.

---

### C. Provozní jistoty

#### R-6 · Datum poslední publikace mapy

„Obnovit HTML" řekne „spuštěno" a tím to končí — uživatel neví, jestli flow
doběhlo ani k jakému okamžiku jsou data v mapě. Flow by mělo zapsat datum do
listu `Nastaveni` (PRD s ním počítá) a přehled ho ukázat vedle tlačítka.

#### R-7 · Kdo a kdy záznam změnil

SharePoint drží `Modified` a `Editor`, appka je nezobrazuje. Dva řádky
v detailu aktivity; u podkladu pro organizační řád je dohledatelnost na místě.

#### R-8 · Oprávnění po sekcích

Dnes je v rejstříku jedna sekce a všichni na ni vidí stejně. Jakmile přibudou
další, sekční správce nemá důvod editovat cizí sekci. Řešitelné oprávněními
na úrovni položek nebo filtrem + skupinami; stojí za rozhodnutí **dřív**, než
se naimportuje druhá sekce, protože zpětně se to dělá hůř.

---

### D. Drobnosti

- **Jedinečnost kódu** drží jen optimistický zámek v appce; „Enforce unique
  values" na `Title` by z tiché duplicity udělalo hlášku (viz A-01 v `AUDIT.md`).
- **Rozvržení je pevné** na 1366×768; na menším monitoru Power Apps appku
  zdrobní, ale nepřeskládá.
- **Aktivita zařazená do víc dílčích procesů** se v mapě objeví vícekrát
  a mapa nenaznačí, že jde o tutéž činnost.
- **Osiřelé vazby** v tabulce `Vazba aktivita–dílčí proces` nemají vlastní
  filtr, protože vazební tabulka nemá obrazovku.
- **Exporty se hromadí** v Site Assets — každý běh je nový soubor s razítkem.
  Úklidové flow po N dnech je pár akcí.
- **Pozice posuvníku stromu** se při návratu z detailu neobnoví (rozbalené
  větve ano). Power Apps scroll galerie z `pa.yaml` neovlivníš.

---

### Co bych dělal v jakém pořadí

1. **R-1** — bez něj se rejstřík nenaplní a všechno ostatní pracuje s deseti
   procenty dat.
2. **R-3 jako pilot na sekci 3** — ukáže, jestli se sbírají správné údaje,
   dokud je levné to změnit.
3. **R-2** — jakmile začne dat přibývat, bude potřeba je řídit.
4. **R-8** — rozhodnout před druhou sekcí, ne po ní.

Zbytek podle toho, co se v provozu ozve. **K1** (předpočítané počty, viz níže)
se stane povinným kolem 1 500 aktivit — to je zhruba tehdy, až bude R-1
v provozu a rejstřík poroste.

---

## Připravený plán: rejstřík nad 2 000 aktivitami

Sepsáno 23.08.2026, **odloženo rozhodnutím zadavatele** — při 47 aktivitách
není co řešit. Tenhle plán tu leží hotový, aby se k němu dalo sáhnout bez
dalšího přemýšlení, až přijde čas.

### Kdy to vytáhnout

Spouštěč je **zhruba 1 500 aktivit**. Tou dobou je pořád rezerva a je čas
pracovat v klidu. Dobrý průběžný ukazatel: 250 dílčích procesů × průměrně
8 aktivit = 2 000, takže hranice přijde zhruba při zmapování poloviny
rejstříku.

### Proč zvednutí limitu nestačí

`DefaultConnectedDataSourceMaxGetRowsCount` je dnes 2 000 a **to je strop,
který Power Apps nedovolí překročit**. Řešení tedy není mít víc dat v paměti,
ale nepotřebovat je tam.

Rozhoduje delegace: `Filter(Aktivity, sekce = "3")` SharePoint vyřídí sám
a galerie si výsledek dotahuje po stránkách bez omezení. Cokoli, čemu
konektor nerozumí (`Search` uvnitř textu, `CountRows`, choice přes `.Value`,
`LookUp` do kolekce v podmínce), se počítá až v appce nad prvním oknem dat.

### K1. Předpočítané počty na dílčím procesu

**co:** `src/schema.json`, `src/make_setup.py`, `src/app_src/*`

Strom na přehledu ve skutečnosti aktivity nepotřebuje — potřebuje jejich
**počty**. Dílčí proces dostane sloupce `pocet_aktivit` a `pocet_schvalenych`
(Number; `make_setup.py` dnes typ Number neumí, musí se doplnit). Strom se pak
postaví ze 7 + 46 + 250 = 303 řádků, což se do limitu vejde s velkou rezervou
i při plném rejstříku.

Počty udržuje **appka inkrementálně** při každém svém zápisu (+1 / −1 při
založení, smazání, změně stavu a přesunu aktivity) — to je delegovatelné
a bez limitu. Pro nápravu po ruční editaci v SharePointu tlačítko
**„Přepočítat počty"** pro správce.

**verify:** založit aktivitu → číslo u dílčího procesu vzroste bez znovunačtení;
smazat → klesne; přesunout jinam → klesne u starého, vzroste u nového.
**edge cases:** selhání zápisu uprostřed (počet zůstane vedle — proto tlačítko
přepočtu); souběžný zápis dvou uživatelů.
**risk:** inkrementální údržba je na víc místech a každé opomenutí se projeví
tiše. Kontrola: brána, která ověří, že každý `Patch`/`Remove` nad `Aktivity`
sahá i na počty.

### K2. Aktivity ve stromu až po rozbalení

**co:** `src/app_src/scr_Dashboard.pa.yaml`

Řádky aktivit se do `colStrom` doplní až při rozbalení konkrétního dílčího
procesu — delegovaným `Filter(Aktivity, dilci_proces_kod = …)`, tedy vždy
úplně, bez ohledu na velikost rejstříku.

Tlačítko **„+ aktivity"** (rozbalit vše) je jediné místo, kde se limit udrží:
načte, co se vejde, a popisek to musí říct. Hromadné rozbalení 250 dílčích
procesů je stejně nepřehledné, takže to není velká ztráta.

**verify:** rozbalit dílčí proces s 20 aktivitami → všech 20; sbalit a rozbalit
znovu → nenačítá se dvakrát.
**risk:** filtr stavu a chip osiřelých dnes pracují nad `colStrom` jako celkem
— po změně musí počítat z předpočítaných čísel, ne z řádků.

### K3. Seznam aktivit zpátky na delegovaný dotaz

**co:** `src/app_src/scr_Ciselnik.pa.yaml`

Filtry sekce, útvar a stav jsou rovnosti a SharePoint je deleguje, pokud jsou
sloupce indexované. **Háček:** `stav` je Choice a choice se nedeleguje — musel
by přibýt pomocný textový sloupec, nebo se stav filtroval až nad výsledkem.

Hledání uvnitř textu delegovat nejde nikdy. Buď pomocný indexovaný sloupec
`nazev_norm` (bez diakritiky, malá písmena) a `StartsWith`, nebo fulltext
odkázat na publikovanou HTML mapu, která má data v prohlížeči a hledá bez
omezení.

### K4. Osiřelé aktivity příznakem

Podmínka `IsBlank(LookUp(colDilci, …))` se nedeleguje nikdy. Aktivita dostane
příznak `osirely`, který nastaví flow při změně číselníku nebo jednou denně —
může to být totéž flow, které publikuje mapu.

### Co se do plánu nevešlo a proč

- **Dataverse** by problém vyřešil elegantně (deleguje i `Contains`), ale
  `PRD.md` ho vylučuje kvůli licencím. Zůstává jako záložní cesta; datový
  model je na něj převeditelný bez ztráty, jak zadání vyžaduje.
- **Stránkované načítání do kolekce** je v Power Fx bez `Skip()` křehký trik.
- **List per sekce** by rozbil vazby a kódy.

---

## F5 — Generování textu OŘ (fáze 2)

Ze schválených aktivit (`stav = schváleno`) sestavit text organizačního řádu
v členění podle vykonávajících útvarů, ve tvaru vzoru
`input/VZOR_OŘ - nově sekce 3_17.7.2026.docx`.

**verify:** vygenerovaný text pro sekci 3 se porovná se vzorem — shoda struktury
a pokrytí všech aktivit.
**risk:** pole `Text pro OŘ` bude v datech dlouho prázdné; generování má smysl
až po jeho naplnění.
