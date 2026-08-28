# HANDOVER — vstupní bod pro další session (24.08.2026)

Vstupní bod pro novou session. Pořadí čtení: **tenhle soubor** (co se má dělat
teď) → `STATUS.md` (chronologie a odůvodnění rozhodnutí) → `PLAN.md` (fáze).
Zadání drží `PRD.md`.

> **Stav:** appka běží v provozu a je **ověřená v tenantu**. Aktuální balík
> je **`deploy/procesnimapa_1_0_0_55.zip`** — nese připomínky z vyzkoušení
> 1.0.0.50 (menší písmo, sloupec POLOŽKY, přepínač kódu, subtilnější ovládací
> prvky, nová paleta, mapa bez jména správce, filtr stavu a chip osiřelých).
> Poslední potvrzeně naběhlá verze je 1.0.0.50.
>
> **Jedenáct bran zeleně** (28.08.2026, balík 1.0.0.63): `check_app`,
> `check_env`, `check_solution` 270/0, `check_schema`, `check_mapa_html` 31,
> `check_mapa_beh` 25, `check_mapa_flow` 139, `check_flow` 18,
> `check_export_flow` 110, `check_setup.js`, `check_import.js`.
>
> `.venv` se přes git nepřenáší; na novém stroji viz Rozjezd.
>

## Rozjezd na novém stroji

```powershell
git pull
# venv se nepřenáší — pokud v projektu není, založit a doinstalovat:
python -m venv .venv
.venv\Scripts\python.exe -m pip install openpyxl pyyaml
```

`pac` CLI se při prvním buildu appky rozbalí samo z rozšíření Power Platform
Tools ve VS Code (pár sekund navíc, nic se nenastavuje). Node je potřeba jen
pro `check_setup.js` / `check_import.js` a pro syntaktickou část brány mapy.
Headless test mapy hledá Edge nebo Chrome ve standardních cestách.

## 1. CO JE NA TOBĚ (uživateli)

1. **Podívat se na barvy v `viz/mapa_prototyp.html`** — mapa i appka mají
   novou paletu a je to nejrychlejší způsob, jak posoudit, jestli sedí.
   Kdyby ne, vrací se to změnou hodnot (`styl*` v `App.OnStart`, CSS proměnné
   v šabloně), ne přepisem prvků.
2. **Naimportovat `deploy/procesnimapa_1_0_0_55.zip`** jako upgrade — nese
   **opravu prázdných počtů** (strom se stavěl z nedonačtených kolekcí,
   viz `STATUS.md`). Proti
   1.0.0.50 přibylo: menší tři stupně písma, sloupec **POLOŽKY** posunutý od
   ikony „+" s vycentrovanými čísly, **přepínač kódu** zpátky v pruhu nad
   stromem, ovládací prvky číselníku a detailu **na velikost z Přehledu**
   (32 px) a nová paleta.
3. **Nahrát do Site Assets OBĚ HTML z `deploy/`** — `mapa_template.html`
   i `procesni_mapa.html`. Šablona se dnes měnila (barvy, filtr stavu, chip
   osiřelých, hlavička bez jména), takže bez nahrání se nic z toho v publikované
   mapě neprojeví. Tím se zároveň objeví volba **Zobrazit kód**, která
   v mapě existuje od 1.0.0.31 — ve staré nahrané verzi prostě není.
4. **Mikro-změna → Save → Publish** ve Studiu (§1b), jinak ostatní vidí starou
   verzi.
5. **Zapnout flow** `MapaPublishFlow` i `MapaPublishScheduled`, pokud import
   hlásí, že se nezapnula. Import stav zapnutí nemění.
6. **Pro export do Wordu (F7/D):** až dodám flow a naimportuješ ho, přidej ho
   v Power Apps Studiu jako **datový zdroj** (Add data → flow) a pošli mi
   **nový export solution**. Registrace flow vzniká jen ve Studiu; bez ní se
   `.Run()` nemá na co navázat a build ji nedogeneruje.

## 1b. VYŘEŠENO: po importu je nutná mikro-změna, jinak Save neproběhne

**Ověřeno 21.08.2026 v provozu.** Po importu solution vidí ostatní účty dál
starou verzi, i když je ve Versions nejnovější verze **Live** a při spuštění
naskočí žlutý pruh *„A new version of this app is coming. We'll let you know
when it's available."*

Příčina: **publikovaný dokument vzniká při Save + Publish ze Studia, ne
importem solution.** Po importu ale Studio appku nepovažuje za rozpracovanou,
takže **není co uložit** — Publish pak zveřejní pořád ten starý publikovaný
dokument. Žlutý pruh přitom tvrdí, že nová verze existuje, což svádí hledat
chybu v cache nebo v odkazu.

**Postup po KAŽDÉM importu (dát do předávacího návodu):**
1. Otevřít appku ve Studiu.
2. Udělat **umělou mikro-změnu** — posunout libovolný prvek o pixel a vrátit
   ho zpět. Tím se appka stane rozpracovanou a Save se odemkne.
3. **Save**, počkat na dokončení.
4. **Publish**.
5. U ostatních účtů zavřít běžící session appky (žlutý pruh znamená „až při
   příštím spuštění").

Vedlejší nález, opravený při hledání: **`AppVersion` v `customizations.xml`**
zůstávala z původního exportu, takže se appka netvářila jako změněná. Build ji
teď přepisuje aktuálním UTC razítkem (`dokonci()` v `build_app.py`, bez nálezu
tagu skončí chybou) — od balíku **1.0.0.28**. Samo o sobě to problém
neodstranilo, ale správně to být má.

Vyloučeno: cache prohlížeče (stejné chování v jiném prohlížeči), špatný odkaz,
chybějící Live verze.

## 2b. HOTOVO: sloupec `stav_mapovani` zrušen (24.08.2026)

Byla to odvozenina uložená do sloupce, který od importu zamrzl a nedal se
nikde změnit. Odstraněn ze schématu, dat, flow, mapy i appky; odznak v mapě
má nově jen `N akt.` / `bez aktivit`, obojí počítané ze skutečnosti.
Podrobnosti v `STATUS.md`.

**Na tobě:** smazat sloupec `stav_mapovani` ze SharePoint listů `Agendy`,
`Procesy` a `DilciProcesy` (v appce ani mapě už ho nikdo nečte, takže to
nespěchá a nic se tím nerozbije).

## 2. CO DĚLÁM JÁ (další krok)

**F7/D — export do Wordu z Přehledu.** Exportuje se momentální zobrazení
(strom po filtru stavu, hledání a chipu osiřelých), ne celý rejstřík. Appka
pošle flow serializovaný strom, flow z něj složí dokument, uloží ho do Site
Assets a vrátí adresu; appka zavolá `Download()`.

Vznikne **`.doc`** — HTML, které Word otevře a umí uložit jako `.docx`.
Skutečné OOXML by chtělo premium konektor (Encodian, Word Online) a ten přes
DLP neprojde. Vědomý ústupek, ne opomenutí.

Rozpracovaného nic není. Plán drží `PLAN.md` §F7.

Připravené k vytažení, až přijde čas:

- **`deploy/navod_sprava.md`** (krok 13) — rozepsaný, přerušený zadáním F7.
- **Rejstřík nad 2 000 aktivitami** — hotový plán v `PLAN.md`, spouštěč je
  zhruba 1 500 aktivit, dnes 47.
- **A-08 z auditu** — zbývá `$top: 5000` bez stránkování a testovací tenant
  na čtyřech místech; jméno správce z mapy odešlo 24.08.2026.
- **Náměty N-1 až N-6** v `PLAN.md`.

## 3. Co je hotové (24.08.2026)

| oblast | stav |
|---|---|
| F1 SharePoint rejstřík | hotovo, provisioning i import dat |
| F2 canvas app | **ověřeno v provozu** (1.0.0.50) |
| F3 publikační flow + HTML mapa | **ověřeno v provozu** — mapa se v tenantu zobrazí, flow vrací 250 dílčích procesů |
| F3b denní publikace mapy | hotovo, čeká na import — druhé flow `MapaPublishScheduled`, Recurrence 7:00 |
| F6/A mapa: rozbalení, kód, písmo, nápovědy, barvy vrstev | hotovo |
| F6/B appka: šipka pryč, přepínač kódu, zařazení s posuvníkem | hotovo (1.0.0.50) |
| F6/C dashboard jako úvodní obrazovka | hotovo, čeká na import (1.0.0.50) |
| F6 připomínky z provozu: klikací řádky, hlavičky sloupců, filtr stavu, „Zobrazit vše" | hotovo, čeká na import (1.0.0.50) |
| F6/D zadávací obrazovky (`scr_Ciselnik`) | hotovo, čeká na import (1.0.0.50) |
| F6/E karta zařazení, větší dialog mazání, úklid osiřelých | hotovo, čeká na import (1.0.0.50) |
| F6/F sjednocená editace, hledání a úklid z přehledu | hotovo, čeká na import (1.0.0.50) |
| F6/G akce nad HTML mapou na přehledu, rolovací nabídky | hotovo, čeká na import (1.0.0.50) |
| F4 přenos na MPSV | **blokováno** — uživatel nemá přístup k tenantu MPSV |
| F5 generování textu OŘ | fáze 2 (po 06/2028) |

## 3b. Co se udělalo 21.08. odpoledne (balíky 29–34)

Všechno na základě připomínek z provozu, chronologie a odůvodnění v `STATUS.md`:

| co | proč |
|---|---|
| klik do celého řádku stromu + podbarvení při najetí | popisky nad podkladem spolkly klik i hover |
| hlavičky `VLASTNÍK / VYKONÁVÁ` a `POLOŽEK UVNITŘ` + tooltipy | z obrazovky nešlo poznat, co ta čísla znamenají |
| tooltip rozepisuje kódy útvarů na „kód · název" | sloupec ukazuje jen kódy, do 160 px se název nevejde |
| filtr stavu na přehledu (vše / schváleno / pracovní) | zadáno; filtruje celý strom, ne jen řádky aktivit |
| „Zobrazit vše" v seznamu aktivit | vynuluje všechny čtyři filtry naráz |
| ikona tužky v řádku stromu | detail na jeden klik; klik do řádku jen rozbaluje |
| tři velikosti písma napříč appkou (`varFs`, výchozí střední) | čitelnost; jen text a výšky řádků, ne celý layout |
| šipka zpět jako celý čtvereček, návrat podle původu | proklik z přehledu končil v seznamu aktivit |
| denní publikace mapy v 7:00 (`MapaPublishScheduled`) | flow má jediný trigger, plán proto řeší klon |

Nové brány: `kontrola_stareho_result` v `check_app.py` (Split vrací `Value`,
ne `Result`) a kontrola plánovaného dvojčete v `check_mapa_flow.py`
(129 → 142 kontrol). Obě mutačně ověřené.

Vzory z téhle session jsou zapsané do skillu `power-Apps-skill`
(`reference/canvas-architecture-patterns.md`, `reference/pa-yaml-uskali.md`,
`SKILL.md`) — řádková ikona za překryvem, klikací ikona v liště, návrat na
obrazovku původu, volitelná velikost písma, předpočítané agregace pro filtr
a „flow má jediný trigger".

## 4. Odložené a otevřené věci

- **Úklid connection reference `ppf_sharedsharepointonline_12718`**
  („SharePoint Pruvodnilist-12718" — cizí, z jiného projektu). Visí na ní obě
  flow, takže výměna za `ppf_sharedsharepointonline_bec33` znamená při importu
  přemapování připojení. Odloženo dvakrát, aby se při selhání importu dalo
  poznat, co ho shodilo. Půjde samostatně, bez jiných změn.
- **Brána `/audit`** (`powerplatform-auditor`) před transportem na MPSV —
  krok 11 v `PLAN.md`. Zatím neproběhla, protože transport je blokovaný.
- **`deploy/navod_sprava.md`** (krok 13) — rozhodnuto 21.08.2026 psát ho až
  podle finální podoby appky, tedy po F6/D.
- **Adresa testovacího webu je v balíku na 20 místech**, ne na jednom
  (nález B-01, kolo 4 — do té doby tu stálo, že je to jen `varMapaUrl`):
  - `varMapaUrl` v `App.pa.yaml` — **jediné ručně psané místo**; canvas app umí
    číst jen datasetové env proměnné, textové ne, takže nemá kam jinam;
  - napojení **canvas appky** na listy (`<ConnectionReferences>`) — přepojuje se
    ve Studiu, na proměnné zatím převedené není (viz `PLAN.md`, F8/5).

  **Flow už mezi ně nepatří.** Od 1.0.0.62 berou web i listy z proměnných
  prostředí (typ 100000004, `parameterkey` + `parentdefinitionid`), takže se
  vybírají v průvodci importem a v definici žádná adresa ani GUID nejsou. Do
  1.0.0.61 jich tam bylo 16 a přesně na tom padl import na MPSV 28.08.2026.

  `check_solution.py` to hlídá dvěma bránami: `adresy_ve_flow` nepřipustí ve
  `Workflows/*.json` **žádnou** adresu SharePointu, `promenne_ve_flow` navíc
  vyžaduje, aby každý `dataset`/`table` mířil na deklarovanou proměnnou, aby
  v balíku bylo všech šest definic a žádný `environmentvariablevalues.json`.
  Obě jsou ověřené šesti mutacemi.

  Postup přenosu je pak: naimportovat balík a **v průvodci vyplnit šest
  proměnných** → zapnout čtyři flow → ve Studiu přepojit datové zdroje appky
  a zaregistrovat `ExportFlow` → přepsat `varMapaUrl` a přestavět appku.
  Flow se znovu negenerují. Rozepsáno v `deploy/mpsv/README.md`.
- **Pozice posuvníku stromu se při návratu z detailu neobnoví.** Rozbalené
  větve drží `colOtevrene`, takže ty se vrátí, ale scroll galerie si Power Apps
  řídí sám a z `pa.yaml` ho neovlivníš. Zatím neřešeno — čeká se, jestli to
  v provozu vadí.
- **Delegace nad 2 000 aktivitami**: fulltext v seznamu a `colAkt` na přehledu
  pracují s prvním oknem dat. Dnes 49 aktivit, takže úplné; popisky to říkají.

## 5. Příkazy

```powershell
$env:PYTHONIOENCODING = "utf-8"
$py = ".venv/Scripts/python.exe"

# --- data a mapa ---
& $py src/normalize.py            # podklady -> runs/normalize/
& $py src/build_mapa.py           # šablona -> viz/mapa_prototyp.html + deploy kopie
& $py src/check_mapa_html.py      # 31 statických kontrol šablony a výstupu
& $py src/check_mapa_beh.py       # 25 kontrol v headless Edge/Chrome

# --- kontroly bez buildu ---
& $py src/check_app.py            # zdroje appky: YAML, sloupce, delegace, Notify
& $py src/check_env.py            # tvar definic proměnných prostředí
& $py src/check_schema.py
node src/check_setup.js
node src/check_import.js
```

### Flow AktualizaceKratkehoNazvu je vázané na konkrétní tenant

`PatchItem` si schéma těla odvozuje z konkrétního listu. S `table` z proměnné
se schéma nerozbalí, rozložené klíče `item/<sloupec>` přestanou platit a flow
**nejde zapnout** ("The API operation 'PatchItem' is missing required property
'item'", MPSV 28.08.2026). Celé flow proto drží GUID listu Aktivity — trigger,
čtení i zápis. `dataset` (web) proměnnou snese.

Při přenosu na další prostředí se musí přegenerovat s novým GUID:

```powershell
& $py src/build_flow.py --solution $zaklad --list-aktivity <GUID listu Aktivity>
```

GUID zjistí `deploy/mpsv/03_vypis_guidy.js` vložený do konzole na cílovém webu.
Ostatní tři flow jsou celá na proměnných a přegenerovat se nemusí.

### Sestavení balíku — POŘADÍ NENÍ LIBOVOLNÉ

`build_app.py` musí běžet **jako poslední** — vkládá definice proměnných
prostředí a jako poslední krok ověřuje flow `AktualizaceKratkehoNazvu`
(`zkontroluj_flow_kratky_nazev`).

Do 1.0.0.63 tahle funkce pole `item/nazev` a `item/dilci_proces_kod`
z `PatchItem` **odebírala**, protože se braly ze snímku triggeru starého až
o minutu a přepisovaly novější editaci. Tím se ale balík stal
neaktivovatelným na čistém prostředí (MPSV 28.08.2026): bez povinných polí
flow nejde zapnout. Od 1.0.0.64 se pole posílají, ale plní se z akce
`Nacti_aktivitu` (`GetItem` těsně před zápisem), takže platí obojí —
a `build_app.py` už jen kontroluje, že to tak zůstalo.

Flow buildery upravují zip **na místě**, takže se pracuje na kopii, ne na
vydaném balíku. Pracovní kopie nesmí ležet v `runs/app_build/` — `build_app.py`
tu složku na začátku maže.

```powershell
$zaklad = "$env:TEMP/base.zip"
Copy-Item deploy/procesnimapa_1_0_0_62.zip $zaklad

& $py src/build_mapa_flow.py   --solution $zaklad
& $py src/build_export_flow.py --solution $zaklad
& $py src/add_mapa_schedule.py --solution $zaklad --hodina 7
& $py src/build_flow.py        --solution $zaklad
& $py src/build_app.py --bez-pac --solution $zaklad --verze 1.0.0.63
```

`--bez-pac` vymění `Src/*.pa.yaml` přímo v už zabaleném balíku. Jde to jen
proti balíku **zabalenému z YAML** (má `LoadFromYaml=true`), tedy proti
dřívějšímu výstupu `build_app.py` — ne proti exportu ze Studia. Na stroji
s `pac` (rozšíření VS Code Power Platform Tools) se přepínač vynechá.

```powershell
# --- brány nad hotovým balíkem ---
$z = "deploy/procesnimapa_1_0_0_63.zip"
& $py src/check_solution.py --vstup deploy/procesnimapa_1_0_0_62.zip --vystup $z
& $py src/check_mapa_flow.py   --solution $z   # --base = předchozí balík
& $py src/check_export_flow.py --solution $z
& $py src/check_flow.py        --solution $z

# --- složka pro nasazení ---
& $py src/make_deploy_mpsv.py

# --- náhled mapy v prohlížeči (file:// bývá blokované) ---
& $py -m http.server 8765 --bind 127.0.0.1
# http://127.0.0.1:8765/viz/mapa_prototyp.html
```

**Poslední export ze Studia je `input/procesnimapa_1_0_0_57.zip`** — z něj se
staví na stroji s `pac`. Na stroji bez `pac` se staví z posledního vlastního
balíku (`deploy/procesnimapa_1_0_0_62.zip` a novější) přes `--bez-pac`; export
ze Studia tak upravit nejde, protože YAML zdroje nenese.

## 6. Dělba práce u canvas appky

Zavedený postup, ne výjimka: **uživatel** založí/upraví appku ve Studiu
(zejména připojení datových zdrojů a flow) a pošle **export unmanaged
solution**; **asistent** vymění `Src/*.pa.yaml`, přebalí přes `pac` a vrátí zip
k importu jako upgrade. `.msapp` nejde postavit od nuly.

Z toho plyne: cokoli, co vzniká **jen ve Studiu** (connection reference,
registrace flow jako datového zdroje), musí udělat uživatel — a pak dodat nový
export, jinak ho další build přepíše.

## 6b. Co přibylo 23.08. (balík 1.0.0.35)

| co | proč |
|---|---|
| obrazovka `scr_Ciselnik` — seznam + formulář pro tři úrovně | agendy, procesy a dílčí procesy se daly zakládat jedině ručně v SharePointu |
| režim úpravy v témž formuláři | tužka ve stromu neměla u vyšších úrovní kam vést |
| přepínač osiřelých v číselníku i v seznamu aktivit | smazání nadřazené položky nechává potomky viset a nikdo je neuklidil |
| mazání položky číselníku s potvrzením | dialog říká, kolik podřízených položek tím osiří |
| karta zařazení v detailu aktivity | galerie 300×60 px vedle pole Stav se nedala přečíst |
| dialog mazání 520×236 → 640×360 | text se do něj nevešel |

Nové brány: `kontrola_sloupcu_kolekci`, `kontrola_rezimu_ciselniku`
a `kontrola_predikatu` v `check_app.py` — všechny tři mutačně ověřené
(pět mutací, pět zachycení).

## 6c. Co přibylo 23.08. odpoledne (balík 1.0.0.36)

| co | proč |
|---|---|
| aktivity jako čtvrtá úroveň číselníku, `scr_Seznam` zrušena | dvě obrazovky pro totéž znamenaly dvojí zvyk i dvojí údržbu |
| filtry sekce/útvar/stav a řazení klikem přeneseny do číselníku | zrušená obrazovka je uměla a nesmělo se to ztratit |
| záložky Přehled / Editace místo Přehled / Seznam aktivit | jedna cesta k editaci, ne dvě |
| fulltext na přehledu přes všechny čtyři úrovně | hledat šlo jen v seznamu aktivit, tedy v jedné úrovni ze čtyř |
| chip osiřelých na přehledu | sirotek nemá pod čím viset, takže se ve stromu vůbec nezobrazí |
| koš vedle tužky v řádku stromu | uklidit šlo jen z editace, ne odtud, kde je problém vidět |

Nové brány: rozpoznání vzájemně se vylučujících prvků v `kontrola_prekryvu`
a kontrola shody definic téže kolekce na víc obrazovkách — obě mutačně
ověřené.

## 6d. Co přibylo 23.08. večer (balík 1.0.0.37)

| co | proč |
|---|---|
| „Zobrazit v HTML" a „Obnovit HTML" na přehledu | obě tlačítka byla v zrušeném seznamu aktivit a v 1.0.0.36 v appce chyběla — regrese |
| přejmenování „Obnovit mapu" → „Obnovit HTML" | v appce se nemění mapa, mění se publikovaná HTML stránka |
| rolovací nabídky „Rozbalit" a „HTML mapa" | pruh nad stromem měl devět prvků, další dva by se nevešly |

Brány: `kontrola_prekryvu` pozná prvek nabídky podle `varMenu…` a nehlásí ho
proti obsahu pod ním (uvnitř nabídky hlídá dál), `kontrola_adresy_mapy`
zakazuje adresu natvrdo v `Launch()`. Obě mutačně ověřené.

## 6e. Co přibylo 23.08. večer (balík 1.0.0.43)

Tři poruchy po zrušení `scr_Seznam` (duch v `.msapp`, dvojité rovnítko,
proměnná bez typu) — podrobně v `STATUS.md`. Na každou je brána.

Opravy auditních nálezů **A-01 až A-07** (stav u každého v `AUDIT.md`):
úklid vazeb po smazaném dílčím procesu, odmítnutí recyklovaného kódu
s osiřelými potomky, zrušení duplicitní vazby, strop řádků 500 → 2 000,
uzel „Nezařazené" v mapě, flow posílá jen to, co počítá, a formulář
číselníku se vrací na zakládání po smazání vybrané položky.

Z provozu: nefunkční nabídka rozbalení (položky ležely pod stínem) a užší
pás s počty na přehledu (84 → 44 px).

**Otevřené z auditu:** A-08 — natvrdo zapsaná `"sekce": "3"` a jméno správce
v publikačním flow (po rozšíření mimo sekci 3 bude hlavička mapy lhát),
`$top: 5000` bez stránkování, testovací tenant na čtyřech místech.

## 7. Brány (všechny mutačně ověřené)

| brána | rozsah | co hlídá |
|---|---|---|
| `check_app.py` | 163 prvků, 1584 vzorců | YAML bez duplicit, sloupce proti schématu **i proti vlastním kolekcím**, delegace podle argumentů volání, překryvy, mazání v galerii, adresa mapy |
| `check_solution.py` | 270 kontrol | publisher, verze, GUID listů, flow nezmizelo, `.Run()` má datový zdroj, **úvodní obrazovka**, žádné externí URL |
| `check_mapa_html.py` | 31 kontrol | id v JS vs. HTML, syntaxe skriptu šablony i výstupu, žádná velikost v px mimo přepínač, **shoda deploy kopií se zdrojem** |
| `check_mapa_beh.py` | 18 kontrol | proklik ovládacích prvků mapy v headless prohlížeči |
| `check_mapa_flow.py` | 139 kontrol | kontrakt publikačního flow, pagination, zapékání kotev |
| `check_flow.py` | 18 kontrol | flow nad `nazev_kratky` počítá totéž co `zkratit()`, web i list bere z proměnných |
| `check_env.py` | 6 proměnných | tvar definic env proměnných: typ 100000004, `parameterkey`, vazba listu na web, žádná výchozí hodnota |
| `check_setup.js` / `check_import.js` | 32 + 26 | provisioning a import proti falešnému SharePointu |

Když brána spadne na něčem, co je vědomý ústupek, patří to do jejího seznamu
výjimek s odůvodněním — ne do obcházení kontroly.
