# HANDOVER — vstupní bod pro další session (23.08.2026)

Vstupní bod pro novou session. Pořadí čtení: **tenhle soubor** (co se má dělat
teď) → `STATUS.md` (chronologie a odůvodnění rozhodnutí) → `PLAN.md` (fáze).
Zadání drží `PRD.md`.

> **Stav:** appka i publikační flow **běží v provozu**. Aktuální balík
> k importu je **`deploy/procesnimapa_1_0_0_44.zip`** (jedna editační
> obrazovka pro všechny čtyři úrovně, hledání a úklid přímo z přehledu) —
> hotový a ověřený offline branami, ale **ještě nenaimportovaný**. Poslední
> ověřeně běžící verze v prostředí je **1.0.0.28**. Balíky 34 a 35 jsou
> nahrazené a smazané; 44 obsahuje všechno z nich.
>
> **Obrazovka `scr_Seznam` zanikla.** Aktivity se editují jako čtvrtá úroveň
> číselníku; filtry, řazení i mazání se přenesly, nic se neztratilo.
>
> `.venv` se nepřenáší přes git — na tomhle stroji byl po úklidu pryč
> a musel se založit znovu (viz Rozjezd).

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

1. **Naimportovat `deploy/procesnimapa_1_0_0_44.zip`** jako upgrade a appku
   jednou otevřít ve Studiu (z YAML zabalená appka se validuje až tam).
   Balík nese všechno z nenaimportovaných 1.0.0.34 až 36.

   **Navbar má nově dvě záložky: Přehled a Editace.** Samostatný seznam
   aktivit zmizel — je to teď čtvrtá úroveň v číselníku.

   Na obrazovce **Editace** (dřív Číselník):
   - nahoře **Agendy / Procesy / Dílčí procesy / Aktivity**,
   - u aktivit se objeví druhý filtrační řádek **sekce / útvar / stav**
     a v pravém panelu místo formuláře vysvětlení a tlačítka
     **„Otevřít detail"** a **„Nová aktivita"**,
   - **klik na řádek aktivity otevře detail**, klik na řádek číselníku načte
     položku do formuláře vpravo — ověřit obojí,
   - **hlavičky sloupců řadí** (kód, název, vykonává/vlastník),
   - koš v řádku maže s potvrzením; u aktivity zmizí i její zařazení do
     dílčích procesů,
   - **šipka zpět z detailu** se vrací do editace na úroveň aktivit
     s vybraným řádkem — ověřit i návrat po uložení a po smazání.

   Na obrazovce **Přehled**:
   - vlevo nad stromem **pole pro hledání** — projde kód i název na všech
     čtyřech úrovních naráz; nalezené se vypíšou jako **plochý seznam**, ne
     ve stromu. Vymazání pole vrátí strom do původního rozbalení,
   - vpravo od chipů stavu **chip „osiřelé"** — vypíše položky bez nadřazené
     úrovně. Tohle je jediné místo, kde je z přehledu uvidíš: ve stromu se
     nezobrazují, protože nemají pod čím viset,
   - v řádku je vedle tužky **koš** se stejným potvrzením jako v editaci,
   - **zkusit celý cyklus**: smazat proces → jeho dílčí procesy se objeví
     pod chipem „osiřelé" → uklidit je košem,
   - **ikona +** v řádku: u agendy založí proces, u procesu dílčí proces,
     u dílčího procesu aktivitu — vždy s předvyplněnými nadřazenými úrovněmi.
     U aktivity ikona schválně není. Ověřit, že po „+" u procesu je v číselníku
     předvybraná agenda i proces a zbývá jen název,
   - **nabídka „Rozbalit: … ▾"** místo čtyř tlačítek — ukazuje, který stupeň
     platí; klik mimo ji zavře,
   - **nabídka „HTML mapa ▾"** s volbami **Zobrazit v HTML** a **Obnovit
     HTML** (dřív „Obnovit mapu"). Obojí bylo v zrušeném seznamu aktivit
     a ve verzi 1.0.0.36 v appce chybělo — ověřit, že publikace naskočí
     a že se hláška o spuštění objeví.
2. **Nahrát do Site Assets OBĚ HTML z `deploy/`** — `mapa_template.html`
   (z ní flow skládá stránku) i `procesni_mapa.html` (hotová mapa). Do
   21.08. se kopie dělala ručně a rozešla se se zdrojem, takže publikovaná
   mapa neměla nové ovládací prvky. Teď je generuje `build_mapa.py`.
3. **Spustit „Obnovit mapu"** v appce a v mapě zkontrolovat: přepínač stupně
   rozbalení, zatržítko „Zobrazit kód", čtyři velikosti písma (tlačítka A),
   nápovědu při najetí na řádek.
4. **Zapnout nové flow `MapaPublishScheduled`** (Power Automate > Solutions >
   procesní mapa). Import stav zapnutí nemění, takže nové flow může přijít
   vypnuté a denní publikace by pak tiše neběžela. Ověřit v jeho detailu, že
   trigger je Recurrence **denně v 7:00, Central Europe Standard Time**.
5. **Save & Publish** ve Studiu, jinak uživatelé vidí starou verzi.

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

## 2. CO DĚLÁM JÁ (další krok)

**Čeká se na zpětnou vazbu z importu 1.0.0.36.** Appka je po sjednocení
editace v jiném tvaru než ta, která běží v prostředí (1.0.0.44) — dvě
obrazovky se staly jednou a přibyla celá editace číselníku. Než přijde
zpětná vazba, nemá smysl stavět další.

Až přijde, na řadě je `deploy/navod_sprava.md` — rozhodnuto 21.08., že se
píše podle finální podoby appky, a tou je teď obrazovka Editace.

**Otevřené k rozmyšlení, ne k okamžité implementaci:**
- **Osiřelé vazby** v tabulce `Vazba aktivita–dílčí proces` (dílčí proces
  smazán, vazba zůstala) zatím filtr nemají — vazební tabulka vlastní
  obrazovku nemá. Mazání aktivity vazby uklízí, mazání dílčího procesu ne.
- **„Enforce unique values" na sloupci `Title`** u všech čtyř listů. Dnes
  drží jedinečnost kódu jen optimistický zámek v appce (`LookUp` před
  `Patch`), který není atomický. Znamená to zásah do `src/schema.json`
  a `make_setup.js` včetně dorovnání už založených listů.
- **Rejstřík nad 2 000 aktivitami.** Strop `DefaultConnectedDataSourceMaxGetRowsCount`
  je 2 000 a výš ho Power Apps nepustí; nad tím by strom, hledání, chip
  osiřelých i seznam aktivit pracovaly s prvním oknem dat, aniž by to řekly.
  **Hotový plán leží v `PLAN.md`** („Připravený plán: rejstřík nad 2 000
  aktivitami") — předpočítané počty na dílčím procesu, aktivity až po
  rozbalení, seznam zpátky na delegovaný dotaz, osiřelost příznakem.
  Odloženo rozhodnutím zadavatele 23.08.2026; spouštěč je zhruba
  **1 500 aktivit**, dnes jich je 47.

## 3. Co je hotové (23.08.2026)

| oblast | stav |
|---|---|
| F1 SharePoint rejstřík | hotovo, provisioning i import dat |
| F2 canvas app | **ověřeno v provozu** (1.0.0.44) |
| F3 publikační flow + HTML mapa | **ověřeno v provozu** — mapa se v tenantu zobrazí, flow vrací 250 dílčích procesů |
| F3b denní publikace mapy | hotovo, čeká na import — druhé flow `MapaPublishScheduled`, Recurrence 7:00 |
| F6/A mapa: rozbalení, kód, písmo, nápovědy, barvy vrstev | hotovo |
| F6/B appka: šipka pryč, přepínač kódu, zařazení s posuvníkem | hotovo (1.0.0.44) |
| F6/C dashboard jako úvodní obrazovka | hotovo, čeká na import (1.0.0.44) |
| F6 připomínky z provozu: klikací řádky, hlavičky sloupců, filtr stavu, „Zobrazit vše" | hotovo, čeká na import (1.0.0.44) |
| F6/D zadávací obrazovky (`scr_Ciselnik`) | hotovo, čeká na import (1.0.0.44) |
| F6/E karta zařazení, větší dialog mazání, úklid osiřelých | hotovo, čeká na import (1.0.0.44) |
| F6/F sjednocená editace, hledání a úklid z přehledu | hotovo, čeká na import (1.0.0.44) |
| F6/G akce nad HTML mapou na přehledu, rolovací nabídky | hotovo, čeká na import (1.0.0.44) |
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
- **Adresa mapy `varMapaUrl`** je v `App.pa.yaml` natvrdo (canvas app umí číst
  jen datasetové env proměnné, textové ne). Při přenosu na MPSV se mění tam —
  je to jediné místo a `check_solution.py` na to upozorňuje varováním.
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
& $py src/check_mapa_beh.py       # 18 kontrol v headless Edge/Chrome

# --- canvas app ---
& $py src/check_app.py            # zdroje appky: YAML, sloupce, delegace, překryvy
& $py src/build_app.py --solution "input/procesnimapa_1_0_0_44.zip" --verze 1.0.0.34
& $py src/check_solution.py --vstup "input/procesnimapa_1_0_0_44.zip" `
                            --vystup "deploy/procesnimapa_1_0_0_44.zip"

# --- flows ---
# dvojče s denním během; idempotentní, píše zpátky do vstupní solution
& $py src/add_mapa_schedule.py --solution "input/procesnimapa_1_0_0_44.zip" --hodina 7
& $py src/check_mapa_flow.py --solution "deploy/procesnimapa_1_0_0_44.zip"
& $py src/check_flow.py      --solution "deploy/procesnimapa_1_0_0_44.zip"

# --- náhled mapy v prohlížeči (file:// bývá blokované) ---
& $py -m http.server 8765 --bind 127.0.0.1
# http://127.0.0.1:8765/viz/mapa_prototyp.html
```

**Vstupní solution pro build je `input/procesnimapa_1_0_0_44.zip`** — je to
poslední export ze Studia a jako jediný nese `MapaPublishFlow` mezi datovými
zdroji appky (Add flow). Stavět z něj, dokud uživatel nedodá novější export.

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
| `check_solution.py` | 189 kontrol | publisher, verze, GUID listů, flow nezmizelo, `.Run()` má datový zdroj, **úvodní obrazovka**, žádné externí URL |
| `check_mapa_html.py` | 31 kontrol | id v JS vs. HTML, syntaxe skriptu šablony i výstupu, žádná velikost v px mimo přepínač, **shoda deploy kopií se zdrojem** |
| `check_mapa_beh.py` | 18 kontrol | proklik ovládacích prvků mapy v headless prohlížeči |
| `check_mapa_flow.py` | 129 kontrol | kontrakt publikačního flow, pagination, zapékání kotev |
| `check_flow.py` | 19 kontrol | flow nad `nazev_kratky` počítá totéž co `zkratit()` |
| `check_setup.js` / `check_import.js` | 32 + 26 | provisioning a import proti falešnému SharePointu |

Když brána spadne na něčem, co je vědomý ústupek, patří to do jejího seznamu
výjimek s odůvodněním — ne do obcházení kontroly.
