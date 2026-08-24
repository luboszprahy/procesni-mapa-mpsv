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

Rozdělení práce: appka pošle flow serializovaný strom (`JSON(colStrom…)`),
flow z něj složí dokument, uloží ho do Site Assets a vrátí adresu; appka
zavolá `Download()`.

> **Formát:** vznikne `.doc` — HTML dokument, který Word otevře a umí uložit
> jako `.docx`. Skutečné OOXML by ve flow znamenalo premium konektor
> (Encodian, Word Online), a ten v tomhle tenantu neprojde DLP. Je to vědomý
> ústupek, ne opomenutí.

**verify:** `check_export_flow.py` — definice flow má právě jeden trigger
`PowerAppV2` s textovým vstupem, zápis souboru necílí na runtime výraz
(pravidlo `PatchItem`), akce `Response` vrací adresu; smoke test složí
dokument z vzorového JSON mimo prostředí a ověří, že obsahuje všechny čtyři
úrovně a tolik aktivit, kolik bylo na vstupu. Ručně: export s filtrem
„schváleno" nesmí obsahovat pracovní aktivity.
**edge cases:** prázdný výběr (export se nespustí a řekne proč); velký strom —
u dnešních 47 aktivit je JSON malý, u tisíců narazí na limit vstupu flow
(popsat mez v návodu); souběžné exporty přepisující týž soubor → název nese
časové razítko.
**risk:** appka musí flow registrovat jako datový zdroj, což jde **jen ve
Studiu** — potřebuji od uživatele nový export solution poté, co flow přidá.
Bez toho se `.Run()` nedá zavolat a build by ho vyhodil.

### E. Brána a předání

**verify:** všech osm dnešních bran zeleně + tři nové (kontrast, přepínač
proměnné, minimální velikost prvku); `check_solution.py` na výsledném balíku;
teprve pak předat zip.
**risk:** nová paleta se dotkne obou výstupů naráz (appka i mapa) — kdyby se
zadavateli nelíbila, musí jít vrátit jednou změnou hodnot, ne přepisem
prvků. Proto barvy zůstávají v proměnných `styl*` a v CSS proměnných, nikde
natvrdo.

---

## Náměty na rozšíření (neschválené, k připomenutí)

Sepsáno 23.08.2026 na vyžádání. **Nic z toho není zadané ani rozpracované** —
je to seznam, ze kterého se vybírá, seřazený podle toho, jak moc to bude
v provozu chybět.

### N-1 · Hromadné pořízení z evidenční karty

Zadavatelka pracuje s excelovými kartami (~45 aktivit na sekci) a sekcí bude
víc. Appka umí zakládat po jedné; hromadný import existuje jen jako
`src/import_data.js`, který se vkládá do konzole prohlížeče — to je nástroj
pro vývojáře, ne pro správce rámce. Až přijde karta další sekce, znamená to
45× proklikat formulář.

Návrh: flow, které přečte kartu nahranou do knihovny a založí aktivity dávkou,
s náhledem „co vznikne / co je duplicita" před zápisem. Kódy přiděluje stejný
mechanismus jako appka.

**Proč je to podle mě nejdůležitější:** je to jediná věc ze seznamu, která
brání běžnému provozu — zbytek jsou vylepšení něčeho, co funguje.

### N-2 · Datum poslední publikace mapy

„Obnovit HTML" řekne „spuštěno" a tím to končí. Uživatel neví, jestli flow
doběhlo ani k jakému okamžiku jsou data v mapě. Stačilo by, aby flow zapsalo
datum do listu `Nastaveni` (PRD s ním počítá) a přehled ho ukázal vedle
tlačítka.

### N-3 · Pohled „co ještě není zmapováno"

V datech je 250 dílčích procesů a 46 aktivit — poměr zmapovanosti je hlavní
metrika projektu do 06/2028. Dashboard ukazuje součty, ale ne rozpad podle
sekcí a vlastníků, tedy „kdo má co dodělat". Pro řízení projektu je to podle
mě užitečnější než cokoli dalšího v appce.

### N-4 · Kdo a kdy záznam změnil

SharePoint drží `Modified` a `Editor`, appka je nezobrazuje. U evidence, ze
které se stane organizační řád, je dohledatelnost změny na místě — dva řádky
v detailu aktivity.

### N-5 · Schvalování s rolemi a notifikací

Stav „schváleno" dnes přepne kdokoli s přístupem. Metodika má role (vlastník
procesu, sekční správce), ale bez oprávnění a notifikace je to čestné
prohlášení. `PRD.md` to řadí do fáze 2, takže to není nedodělek — ale hotové
schvalování to není.

### N-6 · Drobnosti

- **Jedinečnost kódu** drží jen optimistický zámek v appce; „Enforce unique
  values" na `Title` by z tiché duplicity udělalo hlášku (viz A-01 v `AUDIT.md`).
- **Rozvržení je pevné** na 1366×768; na menším monitoru Power Apps appku
  zdrobní, ale nepřeskládá.
- **Aktivita zařazená do víc dílčích procesů** se v mapě objeví vícekrát
  a mapa nenaznačí, že jde o tutéž činnost.
- **Osiřelé vazby** v tabulce `Vazba aktivita–dílčí proces` nemají vlastní
  filtr, protože vazební tabulka nemá obrazovku.

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
