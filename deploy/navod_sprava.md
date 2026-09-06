# Rejstřík agend a procesů — návod pro správce

Návod pro **správce procesního rámce** a **sekční správce**: jak v aplikaci
pořizovat agendy, procesy, dílčí procesy a aktivity, jak se publikuje procesní
mapa a co dělat, když něco nefunguje.

Návod popisuje aplikaci **Procesní mapa MPSV** ve verzi 1.0.0.98. Doménové
pojmy (agenda, proces, dílčí proces, aktivita, vlastník) drží *Metodika pro
práci s procesy v1.0* — tenhle text je nevykládá, jen říká, kam se co v aplikaci
zapisuje.

---

## 1. Než začneš

**Aplikaci otevřeš** z Power Apps (`make.powerapps.com` → Apps → *procesni
mapa*) nebo z odkazu, který ti pošle správce. Poprvé si vyžádá souhlas
s připojením k SharePointu — potvrdit.

**Data leží v SharePointu**, ne v aplikaci. Sedm listů: `Agendy`, `Procesy`,
`DilciProcesy`, `Aktivity`, `AktivitaDilciProces` (zařazení aktivit), `Utvary`
(číselník útvarů) a `HistorieKodu` (uzavřené kódy po přesunech, §8). Vedle nich
tři knihovny: `Zalohy`, `Exporty` a `Import`. Aplikace je jen pohodlnější
způsob, jak do nich psát — v nouzi jde všechno vidět i přímo v SharePointu.

**Všechny listy mají zapnuté verzování.** Když se něco přepíše omylem,
předchozí verze položky se dá v SharePointu obnovit (položka → Podrobnosti →
Historie verzí). Smazané položky jsou v koši webu 93 dní.

---

## 2. Rozvržení aplikace

Aplikace má čtyři obrazovky. Do dvou se dostaneš záložkami v tmavém pruhu
nahoře, zbylé dvě se otevírají z nich.

| obrazovka | k čemu je |
|---|---|
| **Přehled** | úvodní; karty s počty a strom celého rejstříku |
| **Editace** | číselník — zakládání a úprava všech čtyř úrovní |
| detail aktivity | otevře se tužkou u aktivity nebo tlačítkem „Nová aktivita" |
| zařazení do dílčích procesů | otevře se z detailu tlačítkem „Spravovat…" |

Vpravo v tmavém pruhu jsou **tři tlačítka „A"** — malé, střední, velké písmo.
Mění velikost textu ve stromu i v seznamech a výšku řádků; výchozí je střední.
Nastavení platí do zavření aplikace.

### Přehled

Nahoře **čtyři karty s počty**: AGENDY, PROCESY, DÍLČÍ PROCESY, AKTIVITY.
Pod nimi **strom** celého rejstříku — čtyři úrovně nad sebou, barevně odlišené
(agenda nejsytější, aktivita skoro bílá). Sloupce: ÚROVEŇ A NÁZEV, VLASTNÍK,
POLOŽKY (kolik položek leží uvnitř), KÓD.

Ovládání nad stromem:

- **hledání „Hledat v celém rejstříku"** — hledá ve všech čtyřech úrovních
  naráz, v názvu i v kódu, a najde i položky uvnitř zabalených větví;
- **nabídka „Rozbalit ▾"** — jen agendy / + procesy / + dílčí procesy /
  + aktivity;
- **nabídka „Stav: … ▾"** — všechno, co mění pohled na strom. Popisek tlačítka
  nese, co je právě zapnuté, takže filtr nejde přehlédnout:

  | volba | co udělá |
  |---|---|
  | **vše** | bez filtru stavu |
  | **schváleno** / **pracovní** | nechá jen aktivity v daném stavu a nad nimi jen větve, ve kterých po odfiltrování něco zbylo |
  | **osiřelé** | položky, jejichž nadřazená úroveň v číselníku chybí (viz §6) |
  | **nezařazené (N)** | aktivity nahrané importem bez zařazení; číslo říká, kolik jich čeká (viz §6) |
  | **zobrazit kód** | schová nebo vrátí sloupec KÓD; hledání podle kódu funguje dál |

  *Osiřelé* a *nezařazené* se vzájemně vylučují — obojí přepne strom na plochý
  seznam, protože takové položky ve stromu nemají pod čím viset;
- **nabídka „HTML mapa ▾"** — „Zobrazit v HTML" a „Obnovit HTML" (viz §9);
- **nabídka „Data ▾"** — export, hromadný import, záloha a obnova (viz §7).

V každém řádku stromu jsou vpravo tři ikony:

| ikona | co udělá |
|---|---|
| **+** | založí položku **o úroveň níž** s předvyplněným zařazením (u aktivity chybí — pod ní už nic není) |
| **tužka** | otevře položku k úpravě |
| **koš** | smaže položku (s potvrzením, které řekne, co tím osiří) |

Klik do zbytku řádku větev rozbalí nebo sbalí, u aktivity otevře její detail.

### Editace

Vlevo seznam, vpravo formulář. Nahoře **čtyři segmentová tlačítka** — Agendy,
Procesy, Dílčí procesy, Aktivity — přepínají obojí naráz.

Formulář má dva režimy: **zakládání** (nadpis „Nová agenda", „Nový proces", …)
a **úprava** (nadpis „Úprava agendy 01", …). Do úpravy se dostaneš kliknutím na
řádek v seznamu vlevo, zpátky na zakládání tlačítkem „Zrušit".

---

## 3. Zakládání

### 3.1 Agenda, proces, dílčí proces

1. **Editace** → segment podle úrovně (Agendy / Procesy / Dílčí procesy).
2. U procesu vyber **Nadřazenou agendu**, u dílčího procesu **agendu i proces**.
3. Vyplň **Název** — tak, jak má stát v rejstříku i v procesní mapě.
4. Vyplň **Vlastníka** (agenda = sekce, proces a dílčí proces = odbor).
   Je nepovinný, ale bez něj bude ve stromu prázdné místo.
5. Nad tlačítkem vidíš **„Kód, který se přidělí"** — zkontroluj ho a dej
   **„Založit"**.

Rychlejší cesta: na **Přehledu** klikni na **+** v řádku nadřazené položky.
Otevře se týž formulář, ale nadřazené úrovně jsou už vyplněné.

### 3.2 Aktivita

1. **Editace** → segment **Aktivity** → **„Nová aktivita"**, nebo na Přehledu
   **+** v řádku dílčího procesu.
2. Vyber kaskádu **Agenda → Proces → Dílčí proces**. Dílčí proces je *primární
   zařazení* — určuje kód aktivity a víc se nemění.
3. Vyplň **„Aktivita — znění pro organizační řád"**. Píše se tak, jak to má
   stát v OŘ; celý text se ukládá a ve stromu se zobrazuje zkrácený na 150 znaků
   (celý ukáže tooltip).
4. **Vykonává útvar** a **Sekce** jsou nabídky z číselníku útvarů, ne volný
   text — překlep by aktivitu schoval před filtrem. Chybí-li útvar v nabídce,
   viz §5.
5. **Spolupracuje** — útvary oddělené středníkem, např. `712; 721`.
6. **Vnitřní předpis** — víc předpisů středníkem, např. `SP 10/2021; VP 02/2016`.
7. **Stav** — `pracovní` nebo `schváleno`.
8. **Text pro OŘ** nech zatím prázdný; plní se až pro generování organizačního
   řádu (fáze 2).
9. **„Uložit"**. Kód se přidělí až teď a aplikace ho vypíše („Založeno jako
   03-11-001-0007").

**Zařazení do dalších dílčích procesů** jde nastavit až po uložení — dokud
aktivita nemá kód, není co s čím spojit. Karta zařazení to říká textem
„Zařazení do dílčích procesů — vznikne po uložení".

---

## 4. Úprava, zařazení, mazání

### 4.1 Úprava

Tužka v řádku stromu nebo klik na řádek v seznamu v Editaci. U agend, procesů
a dílčích procesů jde měnit **jen název a vlastník** — kód a zařazení pod
nadřazenou položku jsou zapečené v kódu a ten se nikdy nemění. Potřebuješ-li
položku přesunout jinam, je to **nová položka**, ne přejmenování.

U aktivity jde měnit všechno kromě kódu a primárního dílčího procesu.

### 4.2 Zařazení aktivity do víc dílčích procesů

Aktivita může patřit do několika dílčích procesů (M:N podle metodiky). V detailu
aktivity je karta **„Zařazení do dílčích procesů (n)"** se seznamem; tlačítko
**„Spravovat…"** otevře obrazovku, kde se vlevo odebírají existující zařazení
a vpravo přidávají nová z číselníku.

- **Primární zařazení odebrat nejde** — je v kódu aktivity.
- Totéž zařazení se nedá přidat dvakrát; aplikace řekne „Aktivita už v tomto
  dílčím procesu je."
- Odebrání se dělá bez potvrzovacího dialogu — je vratné jedním kliknutím na
  **+** vedle.

V procesní mapě se pak aktivita objeví ve **všech** dílčích procesech, do
kterých je zařazená. Ve stromu na Přehledu je jen pod tím primárním.

### 4.3 Mazání

Koš v řádku stromu nebo v seznamu v Editaci. Dialog vždy řekne, **co tím
osiří** („Pod tímto procesem je 12 dílčích procesů") — smazání nadřazené
položky potomky nemaže, jen jim vezme rodiče.

Co se uklidí samo: **smazání dílčího procesu odstraní i vazby aktivit na něj**
(řádky v `AktivitaDilciProces`), aby po něm nezůstalo neviditelné smetí.
Smazání aktivity odstraní všechna její zařazení.

Vrátit smazání v aplikaci nejde. Jde to z **koše SharePointu** (93 dní).

---

## 5. Číselník útvarů

Nabídky „Vykonává útvar" a „Sekce" se plní z listu **`Utvary`**, ne z hodnot
zapsaných v aktivitách — proto je nabídka úplná bez ohledu na to, kolik aktivit
v rejstříku je.

**Útvary se v aplikaci nezakládají.** Chybí-li útvar v nabídce, přidej řádek
přímo do listu `Utvary` v SharePointu:

| sloupec | co do něj |
|---|---|
| Kód útvaru | číslo útvaru — 1 číslice = sekce, 2 = odbor, 3 = oddělení |
| Název útvaru | název tak, jak má být vidět v nabídce |
| Úroveň | `sekce` / `odbor` / `oddělení` |
| Nadřízený útvar (kód) | kód nadřízeného útvaru; u sekce prázdné |

Aplikace načítá číselníky při **spuštění**, takže nový útvar se v nabídce objeví
až po jejím zavření a otevření (nebo po `Ctrl+F5` v prohlížeči).

---

## 6. Osiřelé položky

**Osiřelá položka** je taková, jejíž nadřazená úroveň v číselníku není — proces
bez agendy, dílčí proces bez procesu, aktivita bez dílčího procesu. Vzniká
smazáním nadřazené položky. Ve stromu ji neuvidíš, protože nemá pod čím viset;
proto na ni upozorňuje **chip „osiřelé"** na Přehledu a **přepínač úklidu**
v Editaci.

U **agend** má týž přepínač jiný význam — agenda nadřazenou úroveň nemá, takže
místo sirotků ukazuje **prázdné agendy**, tedy ty, pod kterými není žádný proces.
Dialog i popisek to říkají; nezaměňovat, protože prázdná agenda je platná
položka, kdežto sirotek je smetí.

**Úklid:** přepni chip, projdi seznam a buď položky smaž, nebo — chceš-li je
zachovat — založ chybějící nadřazenou položku se **stejným kódem**, jaký měla
smazaná. Sirotci se tím zase zařadí.

Zakládání položky pod kódem, na kterém sirotci visí, aplikace **odmítne** —
jinak by se pod nový název tiše přilepila cizí historie.

### Nezařazené aktivity — jiná věc než osiřelé

Hromadný import (§7) umí nahrát **holé aktivity** bez zařazení: znění činnosti
a útvar stačí, dílčí proces se doplní až v aplikaci. Takové aktivity dostanou
dočasný kód pod technickou větví `00-00-000` a **nejsou osiřelé** — rodiče mají,
jen je to provizorium. Volba *osiřelé* je proto neukáže; hledá se přes
**nezařazené (N)**.

**Zařazení:** otevři aktivitu, vyber *Dílčí proces* a ulož. Teprve tím dostane
platný kód `AA-BB-CCC-DDDD`. Původní technický kód se **nezapisuje do historie
kódů** — nikdy platným kódem nebyl; zůstane jen u záznamu jako `puvodni_kod`.

Technická větev `00 Nezařazeno` se ve stromu, v číselníku, v nabídkách ani
v publikované mapě neukazuje. To je schválně: není to kus rejstříku.

---

## 7. Data: export, import, záloha, obnova

Všechno je pod tlačítkem **Data ▾** na Přehledu.

| volba | co udělá |
|---|---|
| **Export do Wordu** / **do Excelu** | vysází to, co je právě vidět ve stromu — po filtru, hledání i chipech, ne celý rejstřík. Soubor přibude v knihovně `Exporty` |
| **Vzorová tabulka pro import** | stáhne prázdný sešit s rozbalovátky číselníků |
| **Import z tabulky** | hromadné pořízení aktivit ze sešitu nahraného do knihovny `Import` |
| **Záloha rejstříku** | snímek všech listů do knihovny `Zalohy` (`rejstrik_<datum>.json`); běží i sám denně v 5:00 |
| **Obnova ze zálohy** | vrátí rejstřík do stavu z vybraného snímku |

**Import i obnova jdou přes jednu obrazovku náhledu:** vyber soubor →
*Zkontrolovat* → podívej se, co z toho vyjde → teprve pak *Provést*. Dokud
kontrola pro vybraný soubor neproběhla, je *Provést* zhasnuté.

**Po *Zkontrolovat* se v rejstříku nesmí změnit ani jedna položka.** Náhled
říká, kolik řádků se založí, kolik je duplicitních, kolik chybných a kolik
přijde bez zařazení. Chybné řádky vypíše i s důvodem.

**Když import spadne na „nemáte oprávnění k otevření souboru":** sešit má
citlivostní štítek, který ho šifruje. Štítek *Interní* projde, přísnější ne —
přeštítkuj sešit a nahraj ho znovu. Není to chyba importu a soubor přitom
vlastníš.

**Obnova nikdy nemaže**: co ve snímku není a v rejstříku je, nechá být.
Vrací tedy stav položek, ne stav světa.

---

## 8. Přesun procesu nebo dílčího procesu

Přesun pod jiného rodiče **není přejmenování**. Starý kód se uzavře a zůstane
v evidenci jako doklad, pod novým rodičem vzniká nový kód a obě strany na sebe
ukazují. Kód tím navždy znamená jednu jedinou věc — vlastnost, kterou po
schválení organizačního řádu už nejde dodělat zpětně.

**Kudy:** *Editace* → úroveň *Procesy* nebo *Dílčí procesy* → v řádku **ikona
přesunu**. Agenda se přesunout nedá (nemá rodiče), aktivita se přesouvá ve svém
detailu změnou dílčího procesu.

Obrazovka má týž tvar jako import: **vyber cíl a napiš důvod → *Spočítat
náhled* → tabulka „uzavře se → vznikne" přes celý podstrom → *Provést
přesun***.

- **Důvod je povinný** — zapíše se ke každému uzavřenému kódu, takže z historie
  jde později dohledat, proč se celá větev přečíslovala.
- **Přečísluje se jen přesouvaná úroveň.** Potomci dědí nový prefix a nechají
  si své pořadové číslo: `07-08-001-0006` → `03-05-001-0006`.
- **Nové číslo se hledá i v historii**, ne jen mezi živými položkami — uzavřený
  kód se nikdy nerecykluje.
- Před zápisem si aplikace **sama udělá zálohu**.
- Změní-li se cíl, náhled zhasne a musí se spočítat znovu; jinak by se
  zapisovalo podle čísel, která platila pro jiného rodiče.

Přesun procesu s osmi dílčími procesy a čtyřiceti aktivitami uzavře 49 kódů
a založí 49 nových. Je to nejdražší operace v aplikaci — proto ten náhled.

---

## 9. Procesní mapa

Mapa je HTML stránka v knihovně **Site Assets** cílového webu. Je jen ke čtení,
zobrazí ji kdokoli s přístupem na web a nepotřebuje k tomu licenci Power Apps.

**Data v mapě nejsou živá — jsou v ní zapečená.** Aktualizují se dvěma způsoby:

1. **denně v 7:00** flow `MapaPublishScheduled` (Central Europe Standard Time),
2. **na vyžádání** volbou **„Obnovit HTML"** v nabídce *HTML mapa* na Přehledu.

Po „Obnovit HTML" aplikace řekne, že publikace běží. **Přegenerování chvíli
trvá** — mapu otevři až za pár desítek sekund volbou „Zobrazit v HTML".
Otevře se v novém panelu prohlížeče.

Co v mapě je: celý rejstřík ke čtení, rozbalování větví, fulltext („obsahuje",
ne jen „začíná na"), filtr útvaru, **filtr stavu** (vše / schváleno / pracovní —
stejný jako na Přehledu), volba **Zobrazit kód**, přepínač **Jen osiřelé**,
čtyři velikosti písma a uzel **„Nezařazené"** pro osiřelé záznamy — ty z mapy
dřív mizely, takže počty neseděly.

---

## 10. Po nasazení nové verze aplikace

Tuhle sekci potřebuje ten, kdo importuje solution — ne běžný správce rejstříku.
**Vynechaný krok se vždycky projeví jako „aplikace nefunguje", ne jako chyba
nasazení.**

1. **Import** `deploy/procesnimapa_<verze>.zip` jako upgrade (Power Apps →
   Solutions → Import solution).
2. **Zapnout všechna flow** (Power Automate → Solutions → daná solution).
   Balík jich veze devět: publikace mapy z appky i podle plánu, export,
   zkrácený název, záloha z appky i podle plánu, obnova, import a přesun.
   **Import stav zapnutí nemění**, takže flow přijde vypnuté a projeví se to
   jako chyba aplikace (`502 BadGateway`), ne jako chyba flow.
3. **Nahrát do Site Assets** obě HTML z `deploy/` — `mapa_template.html`
   i `procesni_mapa.html` — pokud se šablona měnila.
4. **Otevřít aplikaci ve Studiu, udělat mikro-změnu** (posunout prvek o pixel
   a vrátit zpět), **Save**, pak **Publish**. Bez mikro-změny není co uložit
   a Publish zveřejní pořád starou verzi — ostatní účty pak vidí staré UI,
   i když je nová verze označená jako *Live*.
5. **Uživatelům zavřít běžící session** aplikace; žlutý pruh „A new version of
   this app is coming" znamená „až při příštím spuštění".

---

## 11. Když něco nefunguje

| co se děje | proč | co s tím |
|---|---|---|
| po přihlášení jsou všechny karty na nule | nedoběhlo načtení číselníků při startu | zavřít a otevřít aplikaci; drží-li to, zkontrolovat přístup k SharePointu |
| ostatní vidí starou verzi aplikace | po importu neproběhlo Save + Publish s mikro-změnou | §10 krok 4 |
| mapa se místo zobrazení stáhne do Downloads | adresa vede přímo na `.html`, SharePoint na ni pošle „stáhni" | adresa musí být náhled knihovny (`AllItems.aspx?id=…`); mění se v `App.OnStart`, proměnná `varMapaUrl` |
| mapa je stará i po „Obnovit HTML" | publikace ještě běží, nebo je flow vypnuté | počkat, pak zkontrolovat běh v Power Automate; §10 krok 2 |
| mapa se v 7:00 neaktualizuje | `MapaPublishScheduled` je vypnuté nebo běží v UTC | zapnout; trigger má být Recurrence denně 7:00, Central Europe Standard Time |
| útvar chybí v nabídce | není v číselníku `Utvary`, nebo se aplikace od jeho přidání neotevřela znovu | §5 |
| založená položka se v seznamu neobjeví | seznam pracuje s načtenými daty | přepnout segment tam a zpět, nebo otevřít aplikaci znovu |
| „Kód … mezitím někdo zabral" | dva správci zakládali totéž ve stejnou chvíli | dát „Založit" znovu — kód se přepočítá |
| ve stromu chybí položka, která v SharePointu je | je osiřelá — chybí jí nadřazená úroveň | §6 |
| po návratu z detailu je strom odrolovaný nahoru | rozbalené větve se vrátí, pozici posuvníku si Power Apps řídí sám | nelze ovlivnit; známé omezení |

---

## 12. Meze dnešního řešení

Ať se nehledá chyba tam, kde je vědomé rozhodnutí:

- **2 000 aktivit.** Přehled i seznam v Editaci pracují s prvním oknem dat
  o 2 000 řádcích; dnes jich jsou desítky. Až se rejstřík bude blížit ~1 500
  aktivitám, je připravená přestavba (`PLAN.md`, „Připravený plán: rejstřík nad
  2 000 aktivitami"). Popisky karet na to upozorňují.
- **Souběh při zakládání.** Kód se rezervuje až při uložení, takže dva správci
  zakládající tutéž úroveň ve stejnou vteřinu můžou dostat týž kód. Aplikace to
  pozná a řekne „zkus uložit znovu"; při jednotkách změn měsíčně je to
  přijatelné.
- **Kód se nikdy nemění a nikdy nerecykluje.** Přesun pod jiného rodiče proto
  není přepis kódu, ale zánik a vznik (§8): starý kód se uzavře v historii,
  nový vznikne pod novým rodičem. Ruční přečíslování by rozbilo odkazy
  v evidenčních kartách i v OŘ.
- **Text pro OŘ se zatím nikde negeneruje.** Sloupec existuje a dá se plnit,
  ale generování organizačního řádu je fáze 2 (po 06/2028).
- **Historii změn nedrží aplikace, ale SharePoint.** Kdo a kdy záznam změnil,
  se dá dohledat v historii verzí položky; v aplikaci to vidět není.
