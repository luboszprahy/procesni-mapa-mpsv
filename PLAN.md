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
| F6 | Připomínky z provozu: mapa, drobnosti v appce, dashboard, zadávací obrazovky | A–C **hotovo** (1.0.0.26), D zbývá |
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

Dnes jde založit jen aktivita. Nově průvodce i pro vyšší úrovně: uživatele vede,
co vyplnit, a u zanořené úrovně vynutí údaje potřebné pro vazbu (proces bez
agendy nevznikne). Kódy přiděluje stejný mechanismus jako u aktivit.

**verify:** založení procesu v agendě → kód `AA-BB` navazuje na poslední volný,
`kody.json` se nepřečísluje, nová položka se objeví v mapě po publikaci.
**risk:** kolize kódů při souběžném zakládání dvěma uživateli — vyhodnotit,
zda stačí kontrola před zápisem, nebo je potřeba pojistné flow.

---

## F5 — Generování textu OŘ (fáze 2)

Ze schválených aktivit (`stav = schváleno`) sestavit text organizačního řádu
v členění podle vykonávajících útvarů, ve tvaru vzoru
`input/VZOR_OŘ - nově sekce 3_17.7.2026.docx`.

**verify:** vygenerovaný text pro sekci 3 se porovná se vzorem — shoda struktury
a pokrytí všech aktivit.
**risk:** pole `Text pro OŘ` bude v datech dlouho prázdné; generování má smysl
až po jeho naplnění.
