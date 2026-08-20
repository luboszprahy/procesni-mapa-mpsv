# STATUS — Procesní mapa MPSV

Aktualizováno: 2026-08-20 14:15

## Grafika podle vzoru + publikační flow — 1.0.0.20 (20.08.2026 14:15)

**Seznam přestavěn podle Správy notifikací.** Tmavý pruh s tlačítkem uvnitř
nahradil navbar (název aplikace, záložka s podtržením, identita uživatele),
pod ním bílá souhrnná karta s třemi čísly a dvěma tlačítky, pak řádek filtrů
s chipy a plochá tabulková galerie. Z řádku zmizel barevný pruh i chip kolem
kódu — zbyla bílá karta oddělená linkou 1 px, jak vzor chce.

**Řazení je v hlavičce, ne v nabídce.** Klik na KÓD / AKTIVITA / VYKONÁVÁ
přepne sloupec, další klik obrátí směr; u aktivního je šipka. Drží to
`varRazeni` a `varRazeniAsc`, `drp_Razeni` zanikl. `Sort` zůstal uvnitř
každé větve `Switch` zvlášť — vypočítaný výraz v `Sort` by delegaci shodil.

**Čísla v souhrnu se počítají z galerie, ne z listu.** `CountRows` nad
SharePointem se nedeleguje a nad 2 000 aktivitami by tiše lhal, takže popisek
říká „Zobrazeno", ne „Celkem". Je to vědomý ústupek, ne opomenutí.

**Celý řádek otevírá detail** (dřív jen šipka) — `Navigate` má podklad
i všech pět labelů. `Select(Parent)` řádek jen vybíral, nenavigoval.

**Info panel „i" zrušen** na obou obrazovkách i s `varNapovedaKod`; výklad
kódu `AA-BB-CCC-DDDD` je v tooltipech „+ Nová aktivita" a „Uložit".
**Globus nahradilo tlačítko „Zobrazit v HTML".**

**`MapaPublishFlow` dokončené — 14 akcí.** Generuje `src/build_mapa_flow.py`
do kostry z designeru: šablona ze Site Assets → pět `Get items` se zapnutým
stránkováním → pět `Select` na kontrakt → `Model` → zapečení kotev →
`Create file`. Kostra neměla žádnou connection reference (Studio ji u prázdného
flow nezaloží), takže se bere ta, kterou už v balíku používá druhé flow.
GUID listů a adresa webu se čtou z `customizations.xml`, ne natvrdo — kdyby
uživatel appku přepojil jinam, natvrdo zapsané GUID by ukazovaly do prázdna
a mapa by se publikovala ze špatných dat, aniž by cokoli spadlo.

**Nová brána `check_mapa_flow.py`** — 126 kontrol ve třech vrstvách: struktura
(trigger beze změny, spojení, viditelnost odkazů v runAfter cestě), kontrakt
(klíče každého `Select`, `?['Value']` u Choice, pagination, GUID místo runtime
výrazu) a význam (výraz kroku `Stranka` se vytáhne z balíku, vyhodnotí nad
skutečnou šablonou a výsledek projde stejným sítem jako `build_mapa.py`).
**12 mutací, všechny chycené** — mj. vypnuté stránkování, `kod` z jiného
sloupce, Choice bez `?['Value']`, `contentVersion: undefined` a `__GEN__`
bez uvozovek.

**Tlačítko „Obnovit mapu" v appce v balíku není** a je to zjištění, ne
opomenutí: `MapaPublishFlow` není v `.msapp` mezi datovými zdroji, takže
`MapaPublishFlow.Run()` by Studio odmítlo. Musí ho ve Studiu připojit uživatel
(Power Automate → Add flow); vzorec je připravený v návodu.

**Úklid connection reference `…_12718` vědomě odložen.** Obě flow na ní visí,
takže odebrání je změna pro obě naráz — mísit ji s velkou funkční změnou by
znamenalo, že při selhání importu nepůjde poznat, co ho shodilo.

### Další krok
Ověřit, jestli tenant HTML ze Site Assets **zobrazí, nebo stáhne**
(`deploy/navod_publikace_mapy.md`, krok 2). Na tom stojí, jestli publikační
flow má smysl, nebo se zobrazení musí přesunout do canvas appky.

## Grafika sjednocena + úklid — 1.0.0.19 (20.08.2026 odpoledne)

**Styl je nově na jednom místě.** `App.OnStart` drží 16 proměnných
(`stylPrimarni`, `stylAkce`, `stylRadekHover`, `stylUspech`, …) a obrazovky
už žádnou barvu nemají natvrdo — 63 zapsaných hodnot nahrazeno proměnnými.
Změna palety je tím na jeden řádek.

**Reakce na myš** (`HoverFill` / `HoverColor` / `PressedFill` /
`FocusedBorderColor`) doplněny na 68 míst: tlačítka ve třech úrovních
(primární / druhotné / nebezpečné), ikony, nabídky, textová pole i **řádky
všech tří galerií** — u vazeb přes podkladový obdélník, protože klasická
galerie hover na řádku sama neumí. Fokus má modrý dvoubodový okraj kvůli
ovládání klávesnicí.

**Seznam**: filtry sedí v bílé kartě s linkou, pod ní hlavička sloupců
a řádky s podbarvením při najetí i výběru.

**Skripty**: `build_flow.py` i `check_flow.py` vybírají flow **podle jména** —
od základu 1.0.0.18 jsou v solution dvě (naše hotové + nové `MapaPublishFlow`
s ručním triggerem a jednou akcí, čeká na doplnění).

**Úklid složky:** `runs/` ze 179 MB na 344 kB (rozbalené `pac` a staré buildy
pryč), `deploy/` drží jen poslední balík, starší solution zipy v `input/archiv/`,
snímky obrazovky v `input/snimky/`.

**Skill doplněn** — `power-Apps-skill/reference/pa-yaml-uskali.md`: pět tříd
chyb, které dnes shodily import nebo otevření appky, a poznámka, že
`pac canvas pack` nevaliduje vůbec nic.

### Další krok
`MapaPublishFlow` doplnit (načíst 6 listů → zapéct do `mapa_template.html` →
uložit do Site Assets) a přidat do appky tlačítko, které ho spustí.

## Galerie ve stylu notifikací — 1.0.0.17 (20.08.2026)

Seznam aktivit přestavěn podle vzoru z MessageCenterDashboard: hlavička
sloupců (KÓD / AKTIVITA / STAV), řádek s podbarvením při výběru, barevný pruh
podle stavu, kód v „chipu", název na dvou řádcích, stav jako barevný štítek
a šipka do detailu. Klasická `Gallery@2.15.0` neumí `TemplateFill` ani
zaoblení rohů, takže je to poskládané z vrstev uvnitř šablony řádku.

**Nová kontrola `kontrola_barev`** — `RGBA()` musí dostat čtyři čísla.
Vzniklo to z vlastního překlepu (`RGBA(223, haha, 0, 0)`), který by jinak
propadl až do Studia.

**Past, která mě stála čtvrt hodiny:** vkládání kódu přes bash heredoc mi do
`check_app.py` zapsalo neviditelný znak `` místo `` v regulárním výrazu.
Kontrola pak nikdy nesedla a `inspect.getsource` vypadal správně, protože
backspace v terminálu smaže předchozí znak. Odhaleno až disassemblem.
Zdroje jsou od řídicích znaků vyčištěné.

**`deploy/procesnimapa_1_0_0_17.zip`** — brány čisté, 1.0.0.16 smazán.

### Zbývá k tomuto zadání
- **HTML mapa**: vygenerovat z anonymizovaných dat a nahrát do Site Assets
  (konzolový skript), aby ikona v appce vedla na existující soubor.
- **Tlačítko „obnovit data v mapě"**: potřebuje flow `MapaPublish`. Postup:
  uživatel založí v designeru flow s triggerem **PowerApps V2** + jednou akcí,
  přidá ho ve Studiu do appky (Power Automate → Add flow) a exportuje;
  asistent pak doplní akce flow i tlačítko volající `MapaPublish.Run()`.

## Číselník útvarů zapojen — 1.0.0.16 (20.08.2026)

Uživatel dodal `input/procesnimapa_1_0_0_15.zip` **bez chyb ve Studiu**
a s připojeným listem `Útvary` (GUID `774d8b0a`). Appka ho teď používá:

- `App.OnStart` načítá `colUtvary` z číselníku a z něj staví nabídky filtrů
  (`kód · název`, zvlášť sekce a zvlášť odbory/oddělení),
- v seznamu filtrují **kódy držené v proměnných** (`varUtvarKod`, `varSekceKod`),
  které se plní v `OnChange` — dotaz nad `Aktivity` tak zůstává delegovatelný,
- v detailu jsou **„Vykonává útvar" a „Sekce" nabídky z číselníku**, ne volný
  text; ukládá se jen kód (`Left(x, Find(" ·", x & " ·") - 1)` — spojka na konci
  zaručí, že `Find` neselže ani u prázdného výběru).

**Výjimka z delegace padla.** `Distinct` nad `Aktivity` už v appce není,
`VYJIMKY_DELEGACE` v `check_app.py` je prázdná a kontrola nehlásí varování.
`check_solution.py` navíc hlídá, že připojení listu `Útvary` z balíku nezmizí.

**`deploy/procesnimapa_1_0_0_16.zip`** — postaveno ze základu 1.0.0.15,
brány čisté. Zbývá jediné varování (`Sort` v `Items` se přepočítá při
překreslení), vědomé.

**Pozn.:** ve Studiu se do appky připojily i `Documents` a `CustomGallerySample`
— nevadí, ale při úklidu před předáním je odpojit.

## SortByColumns neumí identifikátory — 1.0.0.14 (20.08.2026)

Po 1.0.0.13 zbylo 6 chyb, všechny v `gal_Aktivity.Items`: `SortByColumns`
odmítla názvy sloupců zapsané jako identifikátory. Příznak
`supportcolumnnamesasidentifiers` na ni tedy **nedopadá** — přesně jak říká
skill `power-Apps-skill` („ShowColumns chce identifikátory, SortByColumns
řetězce"). Tuhle poznámku jsem při zavádění kontroly identifikátorů přehlédl
a zařadil `SortByColumns` mezi ostatní.

**Řešení: řadí se přes `Sort()`**, který nedostává název sloupce, ale výraz —
je proto jednoznačný v obou režimech a zůstává delegovatelný. `SortByColumns`
je z tabulky `SLOUPCOVE_FUNKCE` v `check_app.py` odebraná i s vysvětlením,
aby na ni nikdo (ani já) znovu nepoužil identifikátory.

**`deploy/procesnimapa_1_0_0_14.zip`** — brány čisté, dvě varování (výjimka
z delegace u `Distinct`, `Sort` v `Items` se přepočítá při překreslení).
Balík 1.0.0.13 smazán.

## 40 chyb ve vzorcích — příčina dva popisky, opraveno v 1.0.0.13 (20.08.2026)

Po importu 1.0.0.12 hlásilo Studio ~40 chyb typu „Expected operator" a
„Name isn't valid". Příčinou byly **dva popisky**, ve kterých jsem napsal
typografickou uvozovku otevírací („) a **ASCII zavírací** (") — ta ukončí
řetězec dřív, zbytek textu se parsuje jako výrazy a jedna vada vyrobí desítky
hlášek, z nichž žádná neukazuje na skutečné místo:

- `lbl_l_Filtry.Text` (seznam) — „(vše)" ,
- `lbl_l_Vysvetleni.Text` (vazby) — „primární".

**Nová kontrola `kontrola_syntaxe`** projde každý vzorec a ověří, že uvozovky
a závorky vyjdou (escapované `""` se počítají správně). Najde to za sekundu
a ukáže konkrétní vlastnost. Mutačně ověřeno vrácením přesně té uvozovky.

Tím jsou v `check_app.py` pokryté všechny čtyři pasti, které dnes shodily
import nebo otevření: nesettovatelná `hidden` vlastnost (PA2108), duplicitní
klíč (PA1001), řetězec místo identifikátoru a teď nevyvážené uvozovky.
Připomínka: **žádnou z nich `pac canvas pack` nechytí.**

**`deploy/procesnimapa_1_0_0_13.zip`** — brány čisté. Starší balíky
1.0.0.11 a 1.0.0.12 smazány.

## 1.0.0.11 spadl na PA1001, opraveno v 1.0.0.12 (20.08.2026)

Appka se neotevřela: `PA1001 … Duplicate name 'Tooltip'` ve `scr_Vazby`.
Dvě chyby v jednom místě, obě moje:

1. **Duplicitní vlastnost** — dvě ikony už `Tooltip` měly a doplnění podrobných
   textů ho přidalo podruhé.
2. **Zbytek escapování** (`'=\"…"'`) ve třech tooltipech na téže obrazovce.

**Proč to kontrola nechytila:** PyYAML u duplicitního klíče **tiše vezme
poslední** a jede dál — parser je shovívavější než packer canvas appky.
`check_app.py` proto nově načítá YAML vlastním loaderem, který duplicitní klíč
ohlásí jako chybu (mutačně ověřeno reprodukcí přesně té hlášky z importu).
Připomínka: **`pac canvas pack` tuhle třídu chyb taky nechytí** — zabalí to.

**`deploy/procesnimapa_1_0_0_12.zip`** — brány čisté (`check_app`,
`check_flow` 19 kontrol / 104 vzorků, `check_solution` 107 kontrol).
Balík 1.0.0.11 smazán, ať se omylem neimportuje.

## Balík 1.0.0.11 — nápověda, ikona mapy, číselník útvarů (20.08.2026)

**Podrobné tooltipy u všech ovládacích prvků** (27 celkem) — každý vysvětluje
nejen co pole je, ale i proč a jaká má pravidla; cílem je, aby k appce nebyl
potřeba samostatný návod. Nejvíc prostoru dostaly dílčí procesy a vazby M:N,
kterým uživatel nerozuměl.

**Info panel „i" v hlavičce seznamu i detailu** vysvětluje stavbu kódu
`AA-BB-CCC-DDDD`, jak se přiděluje a proč se nikdy nemění.

**Ikona zeměkoule** v hlavičce seznamu otevře publikovanou HTML mapu.
Mapa zatím **neexistuje** — vznikne až publikačním flow (F3 krok 9), do té doby
odkaz vede na nenahraný soubor.

**Odchylka od pravidla „žádné hardcoded URL":** adresa mapy je v `App.OnStart`
(`varMapaUrl`). Canvas app umí číst jen datasetové proměnné prostředí, textové
ne, a list `Nastaveni` zatím není. Zapsáno jako **jediná povolená výjimka**
v `check_solution.py` (`VYJIMKA_URL`), která se při každém běhu vypíše jako
varování. Trvalé řešení: list `Nastaveni` (F3) nebo konfigurace přes flow.

## Číselník útvarů — nový list `Utvary`

Útvary v podkladech číselník nemají, jsou jen jako čísla v evidenčních kartách.
Hierarchie je ale v samotném čísle (1 číslice = sekce, 2 = odbor, 3 = oddělení),
takže ji `src/make_utvary.py` odvodí z dat a doplní i nadřízené úrovně, které se
samy v aktivitách nevyskytují. **Názvy jsou zástupné** („Útvar 711 (oddělení)")
— skutečné doplní zadavatelka.

- `runs/anonym/utvary.csv` — 7 útvarů (1 sekce, 2 odbory, 4 oddělení),
- `runs/normalize/utvary.csv` — 8 útvarů z reálných dat,
- schéma má **6 listů / 37 sloupců**, `check_schema` prošel,
- `setup_sharepoint.js` i `import_data.js` přegenerovány, node testy sedí
  (počty 7 / 46 / 250 / 46 / 46 / **7**), mutačně ověřeno.

**Past, kterou to odhalilo:** první verze zástupných názvů („Sekce 7") spustila
kontrolu anonymity — hlídá vzor „sekce <číslice>" jako identifikující údaj.
Kontrola má pravdu, proto se změnil formát názvu, ne kontrola.

**CO JE POTŘEBA UDĚLAT (uživatel):** aby appka číselník využila, musí
1. v konzoli prohlížeče na vývojové site spustit **znovu `setup_sharepoint.js`**
   (idempotentní — založí jen nový list `Utvary`) a pak `import_data.js`,
2. ve Studiu **připojit list `Utvary` jako datový zdroj** a solution znovu
   exportovat (connection reference lokálně vzniknout nemůže).
Teprve pak přepnu filtr útvaru a pole „Vykonává útvar" z volného textu
na číselník.

## Balík 1.0.0.10 — UI podle připomínek + oprava aktivace flow (20.08.2026)

**Import 1.0.0.9 prošel, ale aktivace flow selhala:**
`PatchItem is missing required property 'item/Title'`. Konektor trvá na tom,
aby **povinné sloupce listu byly v těle zápisu**, i když se nemění. Doplněny
`Title`, `nazev`, `dilci_proces_kod` — posílají se beze změny z triggeru.
`check_flow.py` nově hlídá obojí: že tam ty sloupce jsou a že se **nemění**
(mutačně ověřeno, 19 kontrol).

**Appka po importu funguje** — seznam ukazuje 47 aktivit, kaskáda vybírá,
vazby fungují (uživatel si založil testovací aktivitu `02-04-002-0001`).
Připomínky z provozu vyřešeny takto:

1. **Dlouhé názvy se v seznamu ořezávaly** — řádek zvýšen na 96 px, název
   má dva řádky, meta informace posunuty pod něj.
2. **Filtry sekce a útvar jsou teď rozbalovací nabídky** plněné v `App.OnStart`
   z `Distinct(Aktivity, …)` (kolekce `colSekce`, `colUtvary`, první položka
   `(vše)`). Přidána nabídka **Řadit podle** (kód / název / útvar) přes
   `SortByColumns` nad indexovanými sloupci — zůstává delegovatelné.
   Filtr je ve vzorci třikrát: název sloupce musí být identifikátor, takže
   ho nelze dosadit proměnnou.
3. **Nápovědy** (`HintText`) do všech textových polí detailu i seznamu,
   vysvětlující popisky nad filtry, u tlačítka „Další dílčí procesy" a nahoře
   na obrazovce vazeb.
4. **Vlastníci se nezobrazovali, protože v rejstříku nejsou** — vyplněné jsou
   jen u 2 ze 7 agend, 7 ze 46 procesů a 23 z 250 dílčích procesů. Pole teď
   místo prázdna píše „— v rejstříku nevyplněno —", aby to nevypadalo jako
   porucha.
5. **Vykonává útvar / sekce / vnitřní předpis zůstávají volným textem** —
   číselník pro ně neexistuje ani v podkladech. Mají aspoň nápovědu s příkladem.

**Vědomý ústupek z delegace:** `Distinct` nad `Aktivity` delegovatelný není,
nad 2 000 aktivitami přestane být nabídka filtru úplná. Zapsáno jako výjimka
v `check_app.py` (`VYJIMKY_DELEGACE`) — kontrola ji **vypisuje jako varování**,
takže nezapadne; jinde `Distinct` nad velkým listem dál shodí kontrolu
(ověřeno mutací). Až rejstřík naroste, bude potřeba číselník útvarů.

**`deploy/procesnimapa_1_0_0_10.zip`** — brány: `check_app` čistý,
`check_flow` 19 kontrol / 104 vzorků, `check_solution` 91 kontrol.
Po importu **flow zapnout** (po neúspěšné aktivaci zůstalo vypnuté).

## Balík 1.0.0.9 — appka bez chyb + hotové flow (20.08.2026)

**Appka se po importu 1.0.0.7 otevřela**, zbyly 2 chyby a dvě funkční vady:

1. `Sort(…, Descending)` — enum musí být `SortOrder.Descending`. Obě chyby
   ve Studiu byly z tohohle jediného místa v `btn_Ulozit`.
2. **„Zobrazeno 0 aktivit"** — filtrační pole neměla nastavený `Default`,
   takže se do nich doplnil překlad `##Text_DefaultValue_Default##` = **„Text
   input"**. To není placeholder, ale skutečná hodnota: `StartsWith(nazev_kratky,
   "Text input")` nenašel nic. Doplněno `Default: =""` u `txt_Hledat`,
   `txt_Sekce`, `txt_Utvar` a `txt_HledatDp`.
3. **Prázdné číselníky u procesu a dílčího procesu** nebyly rozbité — kaskáda
   je plní až po výběru nadřazené úrovně. Vypadalo to ale jako porucha, proto
   jsou teď **zašedlé** (`DisplayMode`), dokud nadřazený výběr nepadne.

**Dvě nové offline kontroly (mutačně ověřené):** holý `Ascending`/`Descending`
v `Sort()`; obsahová vlastnost s lokalizovanou výchozí hodnotou, která se
nenastaví (přesně past „Text input").

## Flow AktualizaceKratkehoNazvu — hotové

Uživatel dodal v `input/procesnimapa_1_0_0_8.zip` kostru (trigger nad
`Aktivity` + jedna Compose), `src/build_flow.py` doplnil zbytek: osm Compose
akcí, podmínku a `Update item` (`PatchItem`, jen `item/nazev_kratky`, GUID
listu natvrdo).

**Klíčové rozhodnutí:** `if()` v Logic Apps vyhodnocuje **obě** větve, takže
každý podvýraz musí být platný pro libovolný vstup — proto `min`/`max` kolem
každého `substring`. Ověřeno mutací: bez `min` v akci `Rez` spadne výpočet
na 87 vzorcích ze 104.

`src/check_flow.py` — **vytáhne výrazy z hotového balíku a vyhodnotí je**
mini-interpretem (hladově, jako Logic Apps), porovná s kanonickou `zkratit()`
a ověří i idempotenci (druhý průchod nad vlastním výstupem nesmí chtít zápis).
16 kontrol, 104 vzorků, 0 chyb. Mutačně ověřeno na šesti scénářích.
Nahrazuje `check_zkraceni_flow.py`, který modeloval logiku vedle balíku —
ten je smazaný.

`check_solution.py` nově hlídá, že **flow ze vstupní solution přebalením
nezmizí** (past „build ze staršího základu"); ověřeno mutací. 91 kontrol.

**`deploy/procesnimapa_1_0_0_9.zip`** — appka i flow, postaveno ze základu
`input/procesnimapa_1_0_0_8.zip`. Po importu **flow zapnout**, pokud import
hlásí „one or more flows may not have turned on".

## F2 — import 1.0.0.6 spadl na PA2108, opraveno v 1.0.0.7 (20.08.2026)

Appka se po importu 1.0.0.6 **neotevřela**:
`PA2108 : Unknown property 'SearchItems' for control type 'Classic/ComboBox@2.4.0'`
(3×). Moje oprava předchozí chyby byla tedy špatná — `SearchItems` má
v šabloně `hidden="true"`, což znamená **vlastnost, kterou Studio dopočítává
při vazbě v návrháři a z YAML se nastavit nedá**. Zároveň platí, že
nenastavená dědí `Search(ComboBoxSample, …)`. `Classic/ComboBox` je tedy
z YAML **nepoužitelný v obou směrech** — nastavit nejde a nenastavit taky ne.

**Řešení: kaskáda přepsána na `Classic/DropDown`** (`drp_Agenda`, `drp_Proces`,
`drp_Dilci`). Položky jsou `Distinct(…, Title & " · " & nazev)` — `Distinct`
vrací jednosloupcovou tabulku se sloupcem `Value`, což je přesně jméno, které
klasický dropdown pro zobrazovaný sloupec čeká (i tahle vlastnost je vnořená
a z YAML nenastavitelná). Kód se čte pevnou délkou (`Left(…,2/5/9)`), vlastníci
`LookUp` nad kolekcí. `AllowEmptySelection = true` u všech tří, jinak dropdown
vybere první položku sám a nová aktivita by tiše vznikla pod prvním dílčím
procesem.

**Potvrzeno vzorem z praxe:** VendorManagement (PPF produkce) používá moderní
`ComboBox@0.0.51`, který `SearchItems` vůbec nemá. Ta cesta je otevřená, kdyby
bylo hledání v kaskádě potřeba — chce ale doplnit šablonu `modernCombobox`
a nejspíš i příznak `fluentv9controlspreview` (vzor ho má, naše appka ne).
Dropdown volen proto, že nepřidává žádný nový příznak ani šablonu a kaskáda
stejně zúží nabídku na jednotky položek.

**Nová offline kontrola (mutačně ověřená):** `check_app.py` odmítá jak
nastavení `hidden` vlastnosti (PA2108), tak typ controlu, jehož `hidden`
vlastnost dědí vzorová data — s hláškou „použij jiný typ controlu".

**Důležité zjištění o `pac`:** `pac canvas pack` tuhle chybu **nechytí** —
zabalí to bez námitek (ověřeno mutací). Lokální bránou je tedy `check_app.py`,
ne pac. Úspěšný `pack` neříká nic o tom, jestli se appka ve Studiu otevře.

**`deploy/procesnimapa_1_0_0_7.zip`** — postaveno přes `pac`, brána
`check_solution.py` 90 kontrol / 0 chyb, v balíku žádný `ComboBox`
ani `SearchItems`, 3× dropdown s `Distinct` a `AllowEmptySelection`.

**`deploy/app_navrh.md` srovnán se skutečností** (verze 1.1): kaskáda,
identifikátory sloupců, filtr seznamu textovými poli, `primarni` jako Choice
a zakládání primární vazby při uložení.

## F2 — 67 chyb ve Studiu diagnostikováno, balík 1.0.0.6 k importu (20.08.2026)

Ze snímků v `input/` (Studio, panel Formulas): **67 chyb, z toho 38 na `scr_Detail`**.
Dvě příčiny, obě dohledané v balíku, ne odhadnuté:

1. **Appka běží s `supportcolumnnamesasidentifiers = True`** (`Properties.json`
   v `.msapp`) — názvy sloupců se předávají jako **identifikátory, ne řetězce**.
   `ShowColumns(Agendy, "Title", …)` v `App.OnStart` tedy neprošel, kolekce
   `colAgendy`/`colProcesy`/`colDilci` zůstaly bez schématu a od toho se odvíjí
   celá kaskáda „Name isn't valid. 'Title' isn't recognized" a „Incompatible
   types for comparison" v `DefaultSelectedItems`. Stejná past ve `scr_Vazby`
   (`Search(colDilci, …, "Title", "nazev")`).
2. **Nenastavená vlastnost si bere výchozí hodnotu ze šablony controlu.**
   `Classic/ComboBox` má `SearchItems` = `Search(ComboBoxSample, Self.SearchText, Value1)`,
   a protože ji YAML nenastavoval, zdědily ji všechny tři comboboxy — odtud
   trojice chyb „ComboBoxSample" / „Value1" / „function 'Search' has some
   invalid arguments" u každého z nich.

**Opraveno v `src/app_src/`:** identifikátory v `ShowColumns` i `Search`,
explicitní `SearchItems` u `cmb_Agenda` / `cmb_Proces` / `cmb_Dilci`
(hledá se podle `nazev` nad toutéž filtrovanou množinou jako `Items`).

**Aby se past nemohla vrátit — dvě nové offline kontroly v `src/check_app.py`,
obě ověřené mutací** (vrácení právě opravené chyby je shodí):
- řetězec na místě sloupce v `ShowColumns`/`Search`/`SortByColumns`/`AddColumns`/…,
- nenastavená vlastnost, jejíž výchozí hodnota v šabloně míří na vzorová data.
`src/check_solution.py` navíc hlídá, že balík příznak
`supportcolumnnamesasidentifiers` nese (90 kontrol, 0 chyb).

**`deploy/procesnimapa_1_0_0_6.zip` — připraveno k importu jako upgrade.**
Ověřeno v balíku: `testzip` obou zipů čistý, v YAML žádný `ComboBoxSample`,
`ShowColumns` a `Search` s identifikátory, 3× `SearchItems`, verze 1.0.0.6.

**Nová větev `build_app.py --bez-pac`** vymění `Src/*.pa.yaml` přímo v hotovém
`.msapp`; funguje jen u balíku už zabaleného z YAML (`packed.json` →
`LoadFromYaml: true`), na exportu ze Studia sama ohlásí chybu. Vznikla proto,
že na 5CG5210MB2 `pac` nebyl — mezitím **doinstalován** (rozšíření VS Code
`microsoft-IsvExpTools.powerplatform-vscode`, pac 2.9.3), takže na tomhle
stroji fungují obě cesty.

**Křížová kontrola obou cest:** týž balík postavený přes `pac` je proti
`--bez-pac` **bajtově shodný ve všech položkách kromě `packed.json`**, kde se
liší jediná hodnota `LastPackedDateTimeUtc` (časové razítko balení).
Větev bez pac tedy nevyrábí jiný artefakt, jen ho vyrábí bez nástroje.

**Nedořešeno:** že po importu bude chyb opravdu 0, se offline dokázat nedá —
kontroly pokrývají obě nalezené příčiny, ne zbytek seznamu, který na snímku
nebyl vidět. Po importu projít panel Formulas; pokud něco zůstane, poslat
seznam a doopravím.

**Publikace:** první snímek ukazuje přehrávanou appku ve staré verzi s hláškou
„A new version of this app is coming" — naimportovaná verze se hráčům ukáže
až po **Save & Publish** ve Studiu.

## F3 krok 9b HOTOV: pojistné flow nad `nazev_kratky` (20.08.2026)

`deploy/flow_AktualizaceKratkehoNazvu.md` — klikací návod do designeru.
Trigger nad `Aktivity`, řetěz Compose akcí místo regulárních výrazů, zápis
jen když se hodnota liší (tím i ochrana proti cyklení: počítá se vždy
z `nazev`, nikdy z `nazev_kratky`). Návod nese i pět ověřovacích kroků
s konkrétními aktivitami z dat (`07-04-006-0001` je nejdelší, 220 znaků)
a příkaz, který vypíše, co má v poli být.

**Pozor na přenos:** zápisová akce `Update item` nesmí mít list jako runtime
výraz (flow by po importu nešlo zapnout), takže se na tenantu MPSV staví
podle návodu znovu — proměnnou prostředí to nevyřeší.

`src/check_zkraceni_flow.py` — ověřuje, že řetěz Compose akcí, který flow
`AktualizaceKratkehoNazvu` použije (bez regulárních výrazů: kolaps mezer
opakovaným `replace`, řez na 149, hranice slova přes `lastIndexOf`, tři
průchody ořezu koncových `,;.`), dává **týž výsledek jako kanonická
`zkratit()`** z `check_schema.py`. 106 vzorků (reálná i anonymizovaná data
+ 14 hraničních), shoda ve všech; mutačně ověřeno (bez ořezu, jen dva
průchody, jiná hranice slova, řez na 150 → test padá).

**Zbývá:** postavit flow v designeru podle návodu (až bude appka bez chyb).

## F2 — APPKA SE OTEVŘELA (19.08.2026 večer)

`deploy/procesnimapa_1_0_0_5.zip` naimportován a **appka se ve Studiu otevřela.**
Tři obrazovky (`scr_Seznam`, `scr_Detail`, `scr_Vazby`) postavené z `pa.yaml`,
89 kontrol balíku bez chyby.

Cesta k tomu vedla přes tři kola importu; všechny tři příčiny jsou teď pokryté
offline kontrolou v `src/check_app.py` a zapsané do skillu `power-Apps-skill`
(nová sekce „Doauthorování canvas appky z pa.yaml"):

1. **Chybějící definice šablon** v `References/Templates.json` — prázdná appka nese
   jen 5 šablon, které sama používá. Doplňuje `build_app.py` z `src/control_templates.json`.
2. **PA2110** — jména prvků musí být unikátní napříč celou appkou.
3. **PA2108/PA2106** — přesný tvar `Control:` rozhoduje: `Classic/ComboBox@2.4.0`,
   ne `Combobox@2.4.0`. Bez prefixu Studio mapuje na moderní control jiné verze.

Nástroje, které z toho zůstaly (všechny kontroly **mutačně ověřené**):
`src/check_app.py` (typy, vlastnosti, unikátnost, sloupce, delegace),
`src/build_app.py` (unpack → výměna zdrojů → pack → doplnění šablon → solution),
`src/check_solution.py` (89 kontrol balíku před importem),
`src/control_templates.json` (9 šablon + povolené tvary `Control:`).

**Zbývá k uzavření F2:** projít 6 testů ze sekce „Jak se to ověří"
v `deploy/app_navrh.md` — kaskáda, přidělení kódu, **delegace nad >2 000 aktivitami**,
M:N vazba, kolize kódu, referenční integrita. Test delegace se nesmí odkládat.

**Neuzavřené proti návrhu:** `deploy/app_navrh.md` ještě nezná tři odchylky
(filtr útvaru/sekce textem místo `Distinct`, `primarni` jako Choice `ano`/`ne`,
zakládání primární vazby při uložení) ani přechod na `Classic/ComboBox`.

## F2 ROZPRACOVANÁ — appka doauthorovaná (19.08.2026 večer)

Solution zip dorazil (`input/procesnimapa_1_0_0_1.zip`, přišel přes git pull).
Ověřeno: unmanaged, publisher `mpsv`/prefix `mpsv_`, connection reference na všech
5 listů a **GUIDy listů se shodují s F1**.

**Hotovo:**
- `src/app_src/*.pa.yaml` — 3 obrazovky (`scr_Seznam`, `scr_Detail`, `scr_Vazby`)
  + `App.OnStart` podle `deploy/app_navrh.md`. 64 prvků, 543 vzorců.
- `src/check_app.py` — validace zdrojů proti `src/schema.json` (sloupce, odkazy
  mezi prvky, navigace, delegace). **Ověřeno mutací: 5 z 5 zavedených chyb chyceno.**
- `src/build_app.py` — reprodukovatelné přebalení: unpack (`--layout SourceCode`)
  → výměna `Src/*.pa.yaml` → pack → zpět do solution + zvýšení verze.
- `src/check_solution.py` — brána před importem, **24 kontrol, 0 chyb**.
- **`deploy/procesnimapa_1_0_0_2.zip` — připraveno k importu jako upgrade.**

**pac CLI je nově k dispozici** — nainstalováno rozšíření VS Code
`microsoft-IsvExpTools.powerplatform-vscode` (pac 2.9.3); `build_app.py` si pac
najde sám a nupkg si rozbalí do `runs/app_build/pac/`. Tím padá poznámka ve skillu,
že .msapp nelze stavět lokálně — **jde to**, jen appka po importu musí být jednou
otevřena ve Studiu (balík z YAML nese `packed.json` s `LoadFromYaml: true`
a Controls/*.json se dogeneruje až tam).

**Tři vědomé odchylky od `deploy/app_navrh.md`** (návrh zatím neaktualizován):
1. Filtr sekce a útvaru je **textové pole se `StartsWith`**, ne dropdown —
   `Distinct()` nad `Aktivity` není delegovatelný a nabídka by nad 2 000 aktivitami
   tiše ztratila hodnoty.
2. `primarni` ve vazebním listu je **Choice `ano`/`ne`**, ne Boolean (podle
   `schema.json`) — zapisuje se `{ Value: "ano" }`.
3. Uložení nové aktivity zakládá i **primární vazbu** do `AktivitaDilciProces`
   (a při změně dílčího procesu ji přepíše) — jinak by se rozešla s daty importu,
   kde má všech 46 aktivit vazbu `primarni = ano`.

**Next step:** naimportovat `deploy/procesnimapa_1_0_0_2.zip` do PPF prostředí
jako upgrade, otevřít appku ve Studiu (validace YAML) a projít 6 testů ze sekce
„Jak se to ověří" v `deploy/app_navrh.md`. Test delegace (bod 3, >2 000 aktivit)
se nesmí odkládat.

## F1 UZAVŘENA (19.08.2026 13:53)

Oba skripty doběhly na `/sites/DigiData_D/testovaci_subsajta/procesnimapa`.

**Provisioning:** 5 listů založeno, všech 33 sloupců schématu `zalozen`/`vestaveny`,
žádný `CHYBI`. GUIDy listů:
`Agendy 211209f7` · `Procesy 87116681` · `DilciProcesy cd8741a3` ·
`Aktivity 9dfbb5a1` · `AktivitaDilciProces d2067990`.

**Import:** 7 / 46 / 250 / 46 / 46, **0 chyb**, `ocekavano` = `v listech`.
Stránkování i idempotence odbaveny bez zásahu.

**Druhý běh provisioningu (idempotence na ostrém prostředí):** všech 33 sloupců
`existoval`/`vestaveny`, `ve_zobrazeni: ano` u všech, žádný řádek `NAVIC`,
`HOTOVO: vsech 33 radku v poradku`. Skript je tedy opravdu idempotentní
a lze ho pustit znovu kdykoli — i na tenantu MPSV.

Dvě zjištění z reality, která mock neukázal:

1. **`Options` bit 4 sloupce do výchozího zobrazení nedostal** — všech 33 mělo
   `ve_zobrazeni: doplneno`, tedy zařadila je až záchranná větev
   `AddViewField`. Výsledek je správný, ale potvrzuje, že na bit 4 se
   spoléhat nedá a dorovnání zobrazení musí zůstat.
2. **SharePoint zakládá u každého listu `_ColorTag` a `ComplianceAssetId`** —
   hlásilo se 10 sloupců „NAVIC". Nic nerozbíjejí, ale kazily smysl kontrolní
   tabulky (má v ní vyčnívat anomálie, ne šum). Doplněny do výjimek
   a **do falešného SharePointu v testech**, aby se past nemohla vrátit;
   ověřeno mutací.

## KONEC DNE 19.08.2026 — kde se pokračuje

**Blokující pro zítřek:** solution s canvas appkou **nedorazila**. V `input/`
ani v Downloads/na ploše nic nového nebylo. Zítra ji zkopírovat do `input/`
(zip z Power Apps → Solutions → Export, unmanaged).

Co má obsahovat, aby stačilo jedno kolo:
- publisher `mpsv`, prefix `mpsv_` (ne `ppf_`) — kvůli přenosu na tenant MPSV,
- **připojených všech 5 SharePoint listů** z vývojové site (connection reference
  se lokálně dogenerovat nedá, proto musí vzniknout ve Studiu),
- stačí jedna obrazovka, klidně prázdná,
- export **unmanaged**, ideálně už s finálním názvem appky (přejmenování
  později mění GUID a znamená nový import místo upgradu).

Napojení přes environment variables řeším já při přebalení — listy stačí
připojit normálně.

## Flow: dělba práce (dohodnuto 20.08.2026)

Stejná jako u canvas appky — **kostru udělá uživatel v designeru, dokončí ji
asistent v exportovaném zipu.** Generovat flow zip od nuly se v PPF opakovaně
nepovedlo; úprava exportu a import jako upgrade je ověřená cesta.

Co má uživatel v Power Automate vyrobit (flow `AktualizaceKratkehoNazvu`,
uvnitř solution `procesnimapa`, hned se správným názvem):

1. **Trigger** „When an item is created or modified" nad listem `Aktivity`
   — web i list vybrat z nabídky, **ne** jako proměnnou prostředí.
2. Jedna akce **Compose** (obsah nerozhoduje) — asistent si z ní naklonuje zbytek.
3. **Condition** a v jeho větvi *If yes* akce **Update item** nad `Aktivity`
   s vyplněnými poli `Id`, `Title`, `nazev`, `dilci_proces_kod`, `nazev_kratky`
   (hodnoty z výstupu triggeru). Tuhle akci musí založit designer — tělo
   požadavku si odvozuje ze schématu listu a ručně psané JSON je tu nejrizikovější.
4. Flow **uložit** (musí projít bez chyby) a solution **exportovat unmanaged**.

**Past, na kterou si dát pozor:** jakmile solution obsahuje i flow, musí být
základem každého dalšího přebalení **nejnovější export z prostředí**
(`build_app.py --solution <ten export>`). Kdyby se stavělo ze staršího balíku,
flow by v něm nebyl a upgrade by ho z prostředí odstranil.

Po importu upravené verze flow **ručně zapnout**, pokud import hlásí
„one or more flows may not have turned on" — import stav zapnutí nemění.

## CO JE NA TOBĚ

Zadavatelka není k dispozici (stav 19.08.2026), takže se pracuje podle best
practice. Otevřené otázky mají prozatímní rozhodnutí v `PRD.md` §9 — všechna
jsou volená tak, aby se dala revidovat bez ztráty dat.

1. **Naimportovat `deploy/procesnimapa_1_0_0_6.zip`** jako upgrade, otevřít appku
   ve Studiu a podívat se do panelu **Formulas**. Zbyde-li nějaká chyba, poslat
   její seznam (stačí snímek s rozbalenými skupinami) — doopravím.
2. **Až bude appka bez chyb:** projít 6 testů ze sekce „Jak se to ověří"
   v `deploy/app_navrh.md`. Test delegace (>2 000 aktivit) neodkládat.
3. **Save & Publish** ve Studiu, jinak hráči vidí pořád starou verzi.
4. **Až bude zadavatelka k dispozici:** projít `PRD.md` §9 (5 otázek) a potvrdit
   nebo změnit prozatímní rozhodnutí. Ukázat jí `viz/mapa_prototyp.html`.
5. **Před nasazením na MPSV, ne dřív:** nechat potvrdit výchozí číslování kódů
   (viz sekce „Identifikační kódy" níže).
6. **Hotovo** — provisioning, import i solution zip s appkou.

## CO DĚLÁM JÁ (další krok)

**F2 čeká na výsledek importu 1.0.0.6** (viz sekce nahoře). Mezitím F3 krok 9b —
klikací návod `deploy/flow_AktualizaceKratkehoNazvu.md`; ověřovací skript
`src/check_zkraceni_flow.py` už hotový a mutačně ověřený.

Dělba práce u canvas apps je zavedená a zapsaná ve skillu `power-Apps-skill`
i v paměti projektu: uživatel založí appku ve Studiu a pošle solution,
asistent doauthoruje obrazovky v `Controls/*.json` a vrátí přebalený zip
k importu jako upgrade. `.msapp` nejde postavit od nuly — `pac` CLI není
k dispozici.

## Audit F1 — kolo 2 (19.08.2026): 0 blokujících, F1 připravená

Opravy P-01, P-02 i P-03 přijaty. Auditor při hledání dalších obchazek našel
jeden nový nález, **P-04 — opraveno a ověřeno**:

Obsahová kontrola anonymity hlídala jen seznam názvů (`TOKENY`), ale
`anonymize.py` anonymizuje i **čísla útvarů** (3/33/331/11/111/113…)
a **čísla vnitřních předpisů** (`SP 10/2021`). Reálný útvarový kód vrácený
do jinak čistých dat tedy prošel — a přitom právě útvary prozradí
o organizační struktuře nejvíc. Kontrola teď pokrývá všechny tři kategorie
a vzory se importují z `anonymize.py`, aby se obě strany nemohly rozejít.

Dvě pasti, na které jsem při opravě narazil a které řeší kód:
- **Identifikační kódy nesmí do kontroly vstupovat.** `07-11`, `07-12-003`
  vypadají jako útvary a vyvolávaly falešné poplachy. Kódy jsou strukturální
  klíče, ne identifikující údaj.
- **Časové razítko `datum_aktualizace`** (`…T11:28:00Z`) obsahuje „11".
  Datumy se proto přeskakují **podle typu ve schématu**, ne podle jména
  sloupce — příští datumový sloupec tím pádem stejnou past nezaloží.

Ověřeno pěti scénáři: čistá data projdou; podvržený útvar `331`, předpis
`SP 10/2021`, název `MPSV` i sekce `3` skončí `exit 1`; plná reálná data
odmítnuta výčtem všech tří kategorií.

Auditor dále ověřil tvrzení v `deploy/app_navrh.md` o delegaci a o vzorci
pro přidělení kódu — bez faktických chyb. Nedelegovatelnost `Search()`/`in`
nešla lokálně ověřit (appka neexistuje) → zůstává jako **neověřené tvrzení**,
ne zpochybněné.

## Audit F1 — kolo 1 (19.08.2026), nálezy opraveny

Plné znění v `AUDIT.md`.

- **P-01 blokující, OPRAVENO** — pojistka proti neanonymizovaným datům byla jen
  naoko: kontrolovala **název složky** (`== "anonym"`), ne obsah. Reálná data
  zkopírovaná do složky pojmenované `anonym` prošla. Nahrazeno **obsahovou**
  kontrolou nad týmž seznamem tokenů (`TOKENY` v `anonymize.py`), kterým si
  anonymizace ověřuje vlastní výsledek — obě strany se tak nemůžou rozejít.
  Ověřeno reprodukcí scénáře z auditu: podvržená složka teď skončí `exit 1`.
- **P-02 opravit, OPRAVENO** — `make_import.py` nevolal validátor schématu,
  takže poškozená data (kód mimo číselník) se tiše zapekla do importu.
  Nyní se `check()` volá před generováním a při chybě se import odmítne.
  Ověřeno mutací `agenda_kod` na neexistující hodnotu.
- **P-03 drobný, OPRAVENO** — `PLAN.md` uváděl u `stav_rejstrik` 2 hodnoty,
  schéma má 3 (`využitý-S4`). Dokumentace srovnána, doplněno, že závazný
  je vždy `src/schema.json`.

Auditor potvrdil spuštěním: všechny tři testy procházejí a mutacemi doloženo,
že umí selhat; generátory reprodukovatelně sedí na schéma; žádné hardcoded URL;
stabilita `kody.json` potvrzena.

## Dohodnutá východiska

- Zadavatelka pracuje na **MPSV**, vývoj probíhá v **tenantu PPF** → řešení musí být
  přenositelné (listy zakládat skriptem, env variables, žádné hardcoded URL).
- Do PPF tenantu jdou **jen anonymizovaná data** (`runs/anonym/`).
- Pořizování dat = **Power Apps canvas app od začátku** (kaskádové číselníky
  agenda→proces→dílčí proces SharePoint formulář neumí).
- Vazba aktivita ↔ dílčí proces je **M:N přes vazební tabulku**.
- Do SharePointu jdou **všechna data rejstříku**; položky bez aktivit se označují
  příznakem `stav_mapovani`.
- Prezentace: canvas app ve stylu MessageCenterDashboard + HTML se zapečenými daty
  (FloorPlan pattern).
- **Vývojové prostředí = tenant PPF** (rozhodnuto 18.08.2026). Lokální SharePoint doma
  se zamítá: bezplatná edice neexistuje a Power Platform nemá lokální runtime, takže
  by appku ani flow stejně nešlo vyvíjet. Případná záloha do budoucna = vlastní
  M365 Business Basic (~150 Kč/uživatel/měsíc).

## Hotovo

- Projektová struktura, podklady v `input/`, git repo `luboszprahy/procesni-mapa-mpsv` (private).
- `src/normalize.py` — parsuje rejstřík (sloupcově, agendy přes sloučené buňky, procesy
  podle barvy motivu) i evidenční kartu (řádkově), přiděluje kódy `AA-BB-CCC-DDDD`,
  staví vazební tabulku a píše report kvality dat.
  Výsledek: 7 agend, 46 procesů, 250 dílčích procesů, 46 aktivit, 46 vazeb.
- `src/mapa_template.html` + `src/build_mapa.py` — interaktivní HTML mapa, data zapečená
  do šablony přes kotvu `__DATA_JSON__` (build kontroluje výskyt kotev, zákaz externích
  zdrojů). Výstup `viz/mapa_prototyp.html`.
- `src/anonymize.py` — vývojová data pro PPF (`runs/anonym/`), kontrola, že nezbyl
  žádný identifikující token. Mapování v `runs/anonym/mapovani.json`.
- Ověřeno v prohlížeči: strom, fulltext, filtr útvaru, detail aktivity, počty aktivit
  po větvích (10+36=46, filtr útvaru 331 → 11 aktivit = shoda s CSV).

## Stav zmapování (příznak `stav_mapovani` na všech úrovních)

| úroveň | zmapováno | zmapováno jiným útvarem | nezmapováno |
|---|---|---|---|
| agendy | 2 | — | 5 |
| procesy | 7 | — | 39 |
| dílčí procesy | 23 | 62 | 165 |

„Zmapováno jiným útvarem" = rejstřík položku barevně vede jako využitou, ale aktivity
k ní zatím nemáme, protože máme kartu jen ze sekce 3. Tento stav je nutné odlišit —
až přibudou karty dalších sekcí, překlopí se na „zmapováno". V mapě jsou nezmapované
větve ztlumené kurzívou a mají vlastní filtr (zmapované / celý rejstřík / nezmapované).

## Nálezy z dat (report `runs/normalize/report.md`)

Všechny mají rozhodnutí — plné znění i zdůvodnění je v `PRD.md` §9.

1. **46 buněk karty** mělo přebytečné mezery / překlepy — normalizace je čistí automaticky.
2. **Více vlastníků** u 3 položek (11 a 33) — rozhodnuto: přípustný stav, ne nález.
3. **1 dílčí proces navíc** proti rejstříku („Podezření ze spáchání protiprávního
   jednání") — prozatímně ponechán, provenienci nese sloupec `zdroj`.
4. **2 dvojice podobných aktivit** (0,92 a 0,88) — prozatímně ponechány odděleně;
   liší se vykonávajícím útvarem (111 vs 113), sloučením by se ztratilo,
   který útvar co dělá.

## Hotovo 19.08.2026 (F1 krok 2)

- `src/make_setup.py` → `src/setup_sharepoint.js` (21 kB) — provisioning pro konzoli
  prohlížeče, generovaný ze schématu. Zakládá 5 listů a 33 sloupců, zapíná
  verzování a indexy, dorovnává výchozí zobrazení, nastavuje řazení.
  Web si odvodí z adresy stránky — **žádná URL natvrdo**.
- Interní názvy se drží ASCII tak, že se pole zakládá pod ASCII `DisplayName`
  a český zobrazovaný název se nastaví až potom přes MERGE. Proto mají teď
  sloupce i listy pořádné české popisky (`Vlastník agendy`, `Dílčí procesy`).
- `src/check_setup.js` — smoke test proti falešnému SharePointu (mock `fetch`),
  **32 kontrol ve třech scénářích**: prázdný web, opakovaný běh (idempotence),
  list se sloupci mimo zobrazení (oprava přes `AddViewField`). Ověřuje i to, co
  v konzoli není vidět: `Options = 13`, `odata=verbose`, `__metadata.type`,
  ASCII interní názvy, verzování, indexy, řazení, past s `LinkTitle`.
  Test sám ověřen mutacemi — `Options` 13→9 i vypuštěný `LinkTitle` ho shodí.

## Rozhodnuto 19.08.2026: krátký název nelze držet vzorcem

Dotaz, jestli `nazev_kratky` nemůže udržovat počítaný sloupec SharePointu:
**ne**, ze dvou nezávislých důvodů — vzorec neumí číst sloupec typu „více řádků
textu" (a `nazev` jím být musí kvůli délce) a počítaný sloupec nejde indexovat,
takže by nad 5 000 položkami neuneslo řazení. Náhrada: hodnotu plní import
a pořizovací appka, plus pojistné flow `AktualizaceKratkehoNazvu`
(`PLAN.md` krok 9b) pro zápisy mimo appku.

## Zbývá (detail v `PLAN.md`)

- F1 krok 4: brána `/audit` a první ostrý běh na site v PPF.
- F2: canvas app pro pořizování (kaskádové číselníky, automatické kódy).
- F3: publikační flow model → HTML do Site Assets + pojistné flow nad `nazev_kratky`.
- F4: přenos na tenant MPSV.
- F5: generování textu OŘ z aktivit (fáze 2).

## Rozhodnutí 19.08.2026

- `PRD.md` a `PLAN.md` odsouhlaseny.
- **Ověření zobrazení HTML mapy na SharePoint stránce se odkládá** — řešení se
  nejprve zhotoví a otestuje se až po nasazení. Krok 10 v `PLAN.md` posunut za
  krok 12, riziko neseme vědomě.
- Do PPF tenantu jdou **jen anonymizovaná data** (`runs/anonym/`), v **celém rozsahu**.
- **Více vlastníků je přípustný stav** (default) — `vlastnik` je text, hodnoty
  oddělené `; `. Přestalo být nálezem, je to normální stav evidence.
- Publisher solution `mpsv`, prefix `mpsv_`.
- Pole `text_pro_or`, `stav`, `datum_aktualizace` se zakládají prázdná
  (`stav` = `pracovní`, `datum_aktualizace` = datum importu).
- **Vývojová site v PPF:** `https://ppfbanka.sharepoint.com/sites/DigiData_D/testovaci_subsajta/procesnimapa`
  (server-relative `/sites/DigiData_D/testovaci_subsajta/procesnimapa`). Zakládá
  uživatel. **Do skriptů se nehardcoduje** — konzolový skript si web odvodí
  z adresy stránky, na které běží.

## Identifikační kódy — vyřešeno mechanismem, potvrzení stále chybí

Nález: kódy `AA-BB-CCC-DDDD` **v podkladech neexistují**. Evidenční karta má
sloupce „Poř. číslo" u všech čtyř úrovní prázdné, rejstřík čísla nemá, metodika
(kap. 7) definuje jen tvar kódu. Kódy tedy přidělil náš skript podle pořadí
výskytu — a to je nestabilní: vložení položky doprostřed by přečíslovalo vše
pod ní a rozbilo vazby, na kterých stojí celý rejstřík.

**Řešení:** `kody.json` v kořeni = zmrazený rejstřík kódů. Jednou přidělený kód
se už nikdy nemění; nové položky dostávají první volné číslo na své úrovni.
Ověřeno třemi testy (opakovaný běh nic nezmění; odebraná položka dostane volné
číslo a ostatní se nepohnou; ručně přepsaný kód v `kody.json` přebije pořadí).

**Co stále chybí:** potvrzení zadavatelky, že *výchozí* číslování (pořadí agend
podle dnešního rejstříku) je to správné. Pro vývoj v PPF to nevadí — data jsou
anonymizovaná. Před nasazením na MPSV se musí potvrdit; případné oficiální
přečíslování = jednorázové smazání `kody.json` a nový běh.

## Hotovo navíc 19.08.2026 (F1 krok 1)

- `src/schema.json` — **jediný zdroj pravdy** o struktuře 5 SharePoint listů.
  Aktivity mají vedle Note sloupce `nazev` odvozený `nazev_kratky` (Text, useknuto
  na hranici slova na 150 znaků s výpustkou, indexovaný) — SharePoint podle Note
  neřadí ani neindexuje. Výchozí řazení listu: `nazev_kratky`, pak `Title`.
  Druhotný klíč je nutný: dvě aktivity `01-01-003-0001` a `01-01-003-0002` se liší
  až za 165. znakem, takže po zkrácení mají shodnou hodnotu.
- `src/check_schema.py` — validace schéma ↔ data: pokrytí sloupců oběma směry,
  délky, hodnoty Choice, unikátnost klíče, referenční integrita textových odkazů.
  Generuje `deploy/sharepoint_schema.md`, aby dokumentace nemohla zestárnout.
  Ověřeno negativním testem (podstrčené chyby → 3 nálezy, exit 1).
- `src/normalize.py` — opravy: víceřádkový `vnitrni_predpis` se už neslepuje
  (oddělovač `; `), více vlastníků se zachová, kódy se berou z `kody.json`.
- Přegenerováno: `runs/normalize/`, `runs/anonym/`, obě HTML mapy.
  Počty beze změny: 7 / 46 / 250 / 46 / 46.

## Zbývá (detail v `PLAN.md`)

- F1 krok 2: provisioning skript `src/setup_sharepoint.js` (konzole prohlížeče).
- F1 krok 3: import anonymizovaných dat `src/import_data.js`.
- F1 krok 4: brána `/audit`.
- F2 canvas app, F3 publikační flow, F4 přenos na MPSV, F5 generování OŘ.

## Hotovo 19.08.2026 (F1 krok 3)

- `src/make_import.py` → `src/import_data.js` (114 kB) — import do konzole
  prohlížeče. Hodnoty se dopočítávají v Pythonu, ne v prohlížeči: `nazev_kratky`
  používá **tutéž** funkci `zkratit()` jako validátor schématu, takže se obě
  strany nemůžou rozejít. JS už jen posílá hotové záznamy.
- **Pojistka proti neanonymizovaným datům:** výchozí sada je `runs/anonym`,
  běh nad `runs/normalize` skript odmítne (`exit 1`), dokud nedostane
  `--povolit-realna-data`. Ověřeno.
- `src/fake_sharepoint.js` — sdílená napodobenina SharePoint REST pro oba testy.
- `src/check_import.js` — **26 kontrol ve třech scénářích**: prázdné listy
  (počty 7/46/250/46/46, odvozený klíč vazby, `stav`, `datum_aktualizace`,
  výpustka, více vlastníků, `$top=5000`), opakovaný běh (nic se nezdvojí),
  selhání jednoho listu (běh pokračuje, chyby se nasbírají a vypíšou).
  Ověřeno mutacemi — vypnutá idempotence i zúžené stránkování test shodí.

## Odchylka od plánu (F1 krok 3)

Plán počítal s `$batch` po 100 položkách. Zvoleny **sekvenční POSTy**: každá
operace stejně musela být ve vlastním changesetu (atomicita `$batch` je tu
nežádoucí), takže by dávkování ušetřilo jen round-tripy za cenu ruční stavby
multipart MIME. Sekvenční varianta navíc umí to, co dávka ne — **chyba jedné
položky nezastaví zbytek** a na konci se vypíše, která přesně selhala.
Cena: ~395 requestů, řádově minuta běhu. Jde o jednorázovou operaci na prostředí.

## Stav

F1 kroky 1–3 hotové a otestované, zatím **jen proti mocku** — na skutečném
SharePointu ještě neběželo nic. Zbývá brána `/audit`, pak první ostrý běh.
Nic rozpracovaného.

Rozdělení práce je nahoře v sekcích „CO JE NA TOBĚ" a „CO DĚLÁM JÁ".
