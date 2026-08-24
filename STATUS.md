# STATUS — Procesní mapa MPSV

Aktualizováno: 2026-08-23 (konec dne, balík 1.0.0.50)

## Připomínky po vyzkoušení 1.0.0.50 (24.08.2026) — balík 1.0.0.51

Zadáno dokumentem `claude 1.docx` s pěti snímky. Rozhodnutí padla hned:
**export do Wordu jen v appce** (v sandboxu SharePointu je stahování z JS
nejisté stejně jako `fetch`) a **paleta jako světlé plochy + plné barvy na
pruzích** (přes sytý tyrkys ani zelenou by nešly číst dlouhé názvy).

**Hotovo v 1.0.0.51:**

| co | jak |
|---|---|
| tři stupně písma o dva body dolů | `varFs` -2 / 0 / 2, střední je tím, co bývalo nejmenší |
| `POLOŽEK` → `POLOŽKY`, sloupec doleva od „+" | mezera k ikoně 10 → 30 px, čísla vycentrovaná pod nadpisy |
| přepínač kódu zpátky na Přehled | regrese z 1.0.0.37, výchozí stav zobrazeno |
| ovládací prvky číselníku a detailu na 32 px | Přehled je měřítko; víceřádková pole si výšku nechala |
| nová paleta v appce i v mapě | `#110B7A` `#149EBB` `#A9C7EC` `#171F09` `#3CA050` |
| jméno správce z hlavičky mapy pryč | část auditního A-08 |
| filtr mapy: vše / schváleno / pracovní | místo zmapované/nezmapované, stejně jako Přehled |
| chip „jen osiřelé" v mapě | při nulovém počtu neaktivní a řekne proč |

**Barvy jsou spočítané, ne odhadnuté.** Tyrkys má na bílé 3,16:1 a zelená
3,31:1 — obojí pod WCAG AA, takže jako barva textu neprošly. Pro text se
používají ztmavené varianty (`#107E96`, `#308040`), plné barvy zůstaly na
svislých pruzích, kde o kontrast nejde. Nejtěsnější dvojice v celé appce je
teď 4,62:1 (slabý text na nejsytější ploše agendy).

**Dvě nové brány, obě mutačně ověřené.** `kontrola_prepinacu` hlídá, že
proměnná řídící vzhled má v appce něco, co ji přepne — přesně tak zmizel
přepínač kódu a tři balíky si toho nikdo nevšiml. `kontrola_velikosti` drží
jednu výšku ovládacích prvků napříč obrazovkami; hned při zavedení našla dvě
tlačítka dialogu na Přehledu, která jsem sám minul.

**Zděděný rozpor mezi bránou a opravou auditu.** `check_flow.py` spadl —
a spadl i na 1.0.0.50, takže to není regrese z dneška. Oprava A-07 (flow smí
přepsat jen to, co samo spočítalo) odebrala ze zápisu `item/nazev`
a `item/dilci_proces_kod`, ale brána dál vyžadovala původní čtveřici. Nikdo ji
po opravě nepřespustil. Sladěno na `Title` + `nazev_kratky`.

**Osm bran zeleně:** `check_app`, `check_solution` 225/0, `check_schema`,
`check_mapa_html` 31, `check_mapa_beh` 25 (na datech se sirotky 27),
`check_mapa_flow` 142, `check_flow` 17, `check_setup.js`, `check_import.js`.

**Zbývá:** export do Wordu z Přehledu (F7/D) — potřebuje nové flow, jeho import
a **registraci jako datový zdroj ve Studiu**, což jde udělat jen tam. Do té doby
se `.Run()` nemá na co navázat.

## Shrnutí dne 23.08.2026

Den měl tři části: **dokončení editace**, **audit s opravami** a **design**.
Mezi tím tři importy, které neběžely — a stály za to, protože každý odhalil
jinou past.

**Co se postavilo:** obrazovka číselníku pro agendy, procesy a dílčí procesy
(F6/D), úklid osiřelých položek (F6/E), sjednocení editace do jedné obrazovky
včetně aktivit a zrušení `scr_Seznam` (F6/F), akce nad HTML mapou v rolovacích
nabídkách (F6/G), zakládání ikonou + přímo z řádku stromu.

**Co se opravilo z auditu:** A-01 až A-07 — referenční integrita vazeb,
duplicitní vazby, strop řádků 500 → 2 000, nedelegovatelné mazání, osiřelé
záznamy v publikované mapě, flow přepisující cizí pole.

**Tři poruchy z jednoho kořene.** Zrušení `scr_Seznam` vyrobilo ducha
v `.msapp` (626 kB starých Controls), dvojité rovnítko z generujícího skriptu
a osiřelou proměnnou bez typu. Každá shodila import zvlášť a žádnou brány
neviděly, protože kontrolovaly YAML jako datovou strukturu — ne to, co z něj
nakonec vznikne v balíku. Na každou je teď brána a `check_solution.py` kouká
dovnitř `.msapp`.

**Nejužitečnější diagnostický okamžik** nebyl seznam chyb, ale nesrovnalost
na kartách: agend 0, procesů 0, dílčích procesů 0 — ale aktivit 47. První tři
kolekce plní `App.OnStart`, aktivity se načítají až v `OnVisible` obrazovky.
Z toho bylo jasné, že OnStart neproběhl, ještě než přišel App checker.

**Brány ke konci dne (osm, všechny zelené):** `check_app` (4 obrazovky,
194 prvků, 2 148 vzorců), `check_solution` 224/0, `check_schema`,
`check_mapa_flow` 142, `check_mapa_html` 31, `check_mapa_beh` 18,
`check_setup.js`, `check_import.js`.

Přibylo přitom devět nových kontrol, všechny mutačně ověřené: sloupce kolekcí,
režim číselníku, nedelegovatelné predikáty, dvojité rovnítko, proměnné bez
typu, pořadí prvků v rolovacích nabídkách, duchové v `.msapp`, strop řádků
a adresa natvrdo v `Launch()`.

## Barvy podruhé: škála z výchozí modré (23.08.2026) — balík 1.0.0.49

## Barvy podruhé: škála z výchozí modré (23.08.2026) — balík 1.0.0.49

Paleta z coolors (šalvějová + krémová) se neujala: k tmavě modrému navbaru
neseděla a na obrazovce vznikly dvě nesouvisející barevné rodiny. Zadavatel
to shrnul výstižně — „z toho se mi dělá špatně".

Nová škála vychází z barvy, která na obrazovce už je: `stylPrimarni`
**#00126B**. Odstíny jsou její světlé varianty, takže strom a navbar mluví
touž řečí. Hierarchii dělá sytost, ne odstín:

| úroveň | plocha | pruh |
|---|---|---|
| agenda | `#D6DFF2` | `#00126B` (výchozí modrá) |
| proces | `#E6ECF8` | `#005AB5` |
| dílčí proces | `#F0F4FB` | `#4A7FC1` |
| aktivita | `#FAFBFE` | `#93AFD6` |

Aktivita je skoro bílá, ale ne bílá — bílá by splynula s podkladem karty.

Kód řádku je `#47546B`, tmavá modrošedá z téže rodiny: **5,71:1** na
nejsytějším podkladu, tedy nad hranicí WCAG AA. Neutrální šedá by dala jen
3,83:1, takže by neprošla.

Poučení je zapsané do skillu `harmonicke-barvy` jako pravidlo nulté: **vyjdi
z barvy, kterou aplikace už má**, a když zadaná paleta k ní nesedí, řekni to
— ale nabídni konkrétní náhradu, ne jen námitku.

## Barvy podle zadané palety a dlouhé názvy (23.08.2026) — balík 1.0.0.48

## Barvy podle zadané palety a dlouhé názvy (23.08.2026) — balík 1.0.0.48

**Paleta z coolors.co**: `#EFECCA` krémová · `#A9CBB7` šalvějová ·
`#F7FF58` žlutá · `#FF934F` oranžová · `#5E565A` tmavá šedofialová.

Přímo jako podklad řádku se hodí jen dvě z nich — žlutá a oranžová mají
takovou sytost, že by přes ně nešlo číst dlouhé názvy. Rozdělily se proto
podle role: krémová a šalvějová (a jejich světlejší varianty, spočítané
průměrem s bílou) nesou plochu, oranžová a tmavá dělají akcenty na svislých
pruzích, žlutá zůstala jako rezerva pro zvýraznění.

Hierarchie čte shora dolů: šalvějová pro organizační úrovně (agenda sytější,
proces světlejší), krémová pro výkonné (dílčí proces, aktivita nejsvětlejší).
Pruhy karet s počty nahoře berou tytéž barvy jako vrstvy, na které ukazují —
jinak by obrazovka měla dvě nesouvisející barevné soustavy.

**Kontrast ověřen výpočtem, ne okem.** Hlavní text projde s rezervou
(7,9 až 13,0:1), ale kód řádku na nejsytějším podkladu měl **4,03:1**, tedy
pod hranicí WCAG AA. Ztmavil se z `#5E565A` na `#4A4347` → 5,45:1. Text je
nově jednotně tmavý místo tří různých barev: podklad a pruh odlišují úroveň
dost a barevný text na barevné ploše ubírá čitelnost.

**Dlouhé názvy začínají od horního okraje.** Vertikálně vystředěný text se
ořízne z obou stran, takže byl vidět prostředek věty a začátek chyběl.
U dílčích procesů a aktivit je proto zarovnání nahoru, u agend a procesů
zůstává vystředění — tam jsou názvy krátké a působí to klidněji.

**Tooltip ukazuje název celý.** Strom dosud nesl jen zkrácenou verzi
(150 znaků, sloupec `nazev_kratky`), takže i tooltip končil uprostřed věty.
`colAkt` proto načítá i plný název a kolekce ho vedle zobrazovaného nesou
jako `nazevPlny`.

Postup hledání a použití palet je zapsaný jako uživatelský skill
`harmonicke-barvy` — mimo jiné to, že hex hodnoty z coolors.co jsou přímo
v URL a stránku není potřeba otevírat.

## Designové připomínky ze snímků (23.08.2026) — balík 1.0.0.46

## Designové připomínky ze snímků (23.08.2026) — balík 1.0.0.46

**Aktivity už nejsou bílé.** Čtvrtá úroveň splývala s podkladem karty
a vypadala jako „žádná úroveň". Škála je laděná jako analogická s jedním
teplým protipólem: agenda a proces modré (sytost klesá s hloubkou), dílčí
proces zelený jako předěl k výkonu, aktivita teple pískoví. Sytost je všude
nízká, protože přes to jde číst dlouhé názvy.

**Hlavičky sloupců se lámaly na dva řádky.** „VLASTNÍK / VYKONÁVÁ" a
„POLOŽEK UVNITŘ" se do 160 a 110 px nevešly. Sloupec rozšířit nešlo — musel
by ustoupit název — takže se zkrátily texty na „VLASTNÍK" a „POLOŽEK";
co se ztratilo, doplňuje tooltip, který hlavičky mají od 1.0.0.31.

**Číselník na úrovni aktivit hlásil cizí texty.** `Switch` bez větve pro
`aktivita` spadl do else, takže hlavička ukazovala „Číselník — dílčí procesy"
a formulář „Nový dílčí proces", i když uživatel stál na aktivitách. Chybějící
větev doplněna na třech místech.

**Tlačítko „Otevřít detail" zrušeno.** Dělalo totéž co klik do řádku, jen
o krok víc: nejdřív vyber řádek, pak zamiř dolů a klikni znovu. Zůstává
„Nová aktivita", protože tu klik do seznamu nabídnout nemůže — a u aktivit
se posune na uvolněné místo.

**Vnitřní předpis v detailu byl 300×64 px**, přestože se do něj píše ručně
a bývá delší („SP 10/2021; VP 02/2016; …"). Místo se vzalo tam, kde ho bylo
nejvíc nazbyt: tři vlastníci pod sebou zabírali 216 px svisle, ačkoli jsou
jen ke čtení z číselníku a vejdou se vedle sebe. Předpis tím dostal celou
šířku sloupce a dvojnásobnou výšku — z 19 200 px² na 74 400 px², tedy skoro
čtyřnásobek plochy.

## Zakládání přímo z řádku přehledu (23.08.2026) — balík 1.0.0.44

## Zakládání přímo z řádku přehledu (23.08.2026) — balík 1.0.0.44

V řádku stromu přibyla vedle tužky a koše **ikona +**: založí položku
**o úroveň níž** pod tou, na jejímž řádku stojí. U agendy tedy proces,
u procesu dílčí proces, u dílčího procesu aktivitu. **U aktivity ikona
schválně chybí** — je to nejnižší úroveň a pod ní se nic zakládat nedá.

Nadřazený řetěz se předvyplní: co je v kódu nad novým záznamem, uživatel
znovu nevybírá. Nese to `varRodicC` (kód nadřazené položky pro číselník)
a `varNovyDpKod` (předvolený dílčí proces pro novou aktivitu). U aktivity
se otevře rovnou detail, protože formulář v číselníku aktivity needituje.

Kaskáda v detailu se přitom nemusela zdvojovat: plnila se z `varDpKod`,
takže stačilo ho naplnit i pro novou aktivitu a pole se odvodí sama.
Podmínky `If(varNova, "", …)` v `Default` se změnily na `If(IsBlank(varDpKod), …)`
— pro obojí platí totéž pravidlo.

**Kontext se musí zahazovat.** Kdyby po „+" zůstal `varRodicC` viset, další
ručně založená položka by zdědila rodiče z minula. Zahazují ho segmentová
tlačítka, „Nová položka", klik na řádek číselníku i všechny návraty z detailu.
Aby se na některý vstup nezapomnělo, přibyl `varRodicC` mezi povinné
v bráně `kontrola_rezimu_ciselniku` — mutačně ověřeno.

Ikona je `Icon.Add`, ne `Icon.AddDocument`: první je v appce ověřená od
začátku (`scr_Vazby`), druhou by Studio vidělo poprvé. Po dnešku, kdy tři
importy padly na nevyzkoušených konstrukcích, to nestojí za risk.

## Opravy auditu a poučení ze zrušené obrazovky (23.08.2026) — balík 1.0.0.43

**Zrušení jedné obrazovky vyrobilo tři různé poruchy** a stálo tři importy.
Stojí za to je mít pohromadě, protože každá byla jinde a žádnou brány
neviděly:

1. **Duch v balíku.** `pac canvas unpack --layout SourceCode` rozbalí jen
   `Src/*.pa.yaml`; `Controls`, `References` a `Assets` drží v `.msapr`
   a pack je vrátí beze změny. Zrušená `scr_Seznam` tak v `.msapp` přežila
   jako `Controls/4.json` o 626 kB s 65 prvky, z toho 30 už neexistujících.
   Studio ducha načetlo, mrtvé odkazy nahlásilo jako chyby a kvůli nim
   neprovedlo `App.OnStart` — appka naběhla černá.
2. **Dvojité rovnítko.** Devět vlastností mělo `Y: ==If(…)`. Vzniklo při
   generování skriptem: hodnota už rovnítko obsahovala a další se přidalo
   při skládání řádku. YAML se rozparsuje, packer nenamítne nic, Studio
   hlásí „Unexpected characters" až po importu.
3. **Proměnná bez typu.** `Set(varSmazat, Blank())` zůstal v `OnStart` po
   zrušené obrazovce. `Blank()` typ neurčuje, a když je to jediné přiřazení
   v celé appce, Studio hlásí „No type found" — zase chyba v OnStart, zase
   černá appka.

Diagnózu nakonec neurčil seznam chyb, ale **nesrovnalost na kartách**:
agend 0, procesů 0, dílčích procesů 0, ale aktivit 47. První tři kolekce plní
`OnStart`, aktivity se načítají až v `OnVisible` obrazovky — to ukázalo, že
OnStart neproběhl, ještě než přišel App checker.

Na každou z těch tří poruch je teď brána: kontrola duchů v `.msapp`
(`check_solution.py`), `kontrola_dvojiteho_rovnitka` a `kontrola_promennych`
(`check_app.py`), všechny mutačně ověřené.

**Opravy auditních nálezů A-01 až A-07** (podrobně v `AUDIT.md`):

| nález | co se změnilo |
|---|---|
| A-01 | mazání dílčího procesu uklidí i vazby na něj; zakládání odmítne kód, pod kterým leží osiřelé položky po dřívější položce téhož kódu |
| A-02 | stará vazba se odebírá podle starého dílčího procesu, ne podle příznaku `primarni`, a napřed se odklidí i neprimární vazba na cíl |
| A-03 | strop načítaných řádků 500 → 2 000, aby seděl s tím, co appka o sobě tvrdí |
| A-04 | choice predikát z mazání zmizel; `kontrola_predikatu` hlídá i `RemoveIf` |
| A-05 | mapa má uzel „Nezařazené" — osiřelé záznamy z ní přestaly mizet beze stopy |
| A-06 | flow nad krátkým názvem posílá jen to, co samo počítá |
| A-07 | formulář číselníku se vrátí na zakládání, když vybraná položka zmizela |

**Nefunkční nabídka rozbalení** (hlášeno z provozu): položky zůstaly v souboru
před stínem nabídky, takže ležely pod ním a stín spolkl klik. V Power Apps
kreslí pořadí definice — co je dřív, leží níž. Nová brána
`kontrola_poradi_nabidek` to hlídá.

**Pás s počty na přehledu je poloviční** (84 → 44 px): popisek, číslo
i vysvětlivka se vejdou na jeden řádek vedle sebe. Uvolněných 40 px dostal
strom.



## Akce nad HTML mapou zpátky na přehledu (23.08.2026) — balík 1.0.0.37

**Nejdřív přiznání k regresi.** Tlačítka „Zobrazit v HTML" a „Obnovit mapu"
žila v `scr_Seznam`. Když ta obrazovka v F6/F zanikla, zmizela s ní i ona —
publikaci mapy nešlo z appky spustit vůbec. Při rušení obrazovky jsem
kontroloval odkazy NA ni, ne obsah, který nesla. Odhalilo se to až tím, že
si uživatel obě tlačítka vyžádal na přehledu.

Obojí je zpátky, na přehledu, pod nabídkou **„HTML mapa ▾"**. „Obnovit mapu"
se přejmenovalo na **„Obnovit HTML"** — v appce se nemění mapa, mění se ta
publikovaná HTML stránka.

**Pruh nad stromem měl devět ovládacích prvků** a další dva by se do něj
nevešly. Čtyři stupně rozbalení jsou proto pod nabídkou **„Rozbalit: … ▾"**,
která rovnou ukazuje, který stupeň zrovna platí; uvolněné místo zabrala
nabídka nad mapou. Pod oběma panely leží stín, který chytá kliknutí mimo —
bez něj by nabídka zůstala otevřená, dokud by na ni uživatel neklikl znovu.

**Brána musela pochopit, že nabídka leží nad obsahem záměrně.**
`kontrola_prekryvu` pozná prvek nabídky podle proměnné `varMenu…` a nehlásí
ho proti tomu, co je pod ním. Dva prvky **uvnitř téže** nabídky ale
porovnává dál — ty na sebe lézt nemají o nic víc než tlačítka v pruhu.
Mutačně ověřeno: posunutá položka nabídky přes sousední položku padá.

Druhá mutace odhalila mezeru, která tam byla už dřív: `kontrola_adresy_mapy`
hlídala jen `Set(varMapaUrl, "…")`, takže adresa zapsaná rovnou do `Launch()`
by prošla. V cizím tenantu by pak appka otevírala cizí web a nikdo by nevěděl
kde to změnit. Nově je zakázaná.

Ověřeno navíc přímo v balíku, že `MapaPublishFlow` zůstal v
`References/DataSources.json` — kdyby ho pac při přebalení vyhodil jako
nepoužitý, tlačítko by po importu hlásilo neznámý zdroj.

Brány: `check_app` OK (4 obrazovky, 193 prvků, 2 129 vzorců),
`check_solution` 219 kontrol / 0 chyb.



## Jedna editační obrazovka a úklid přímo z přehledu (23.08.2026) — balík 1.0.0.36

Pět připomínek k 1.0.0.35, které spolu souvisejí: editace se stáhla do jedné
obrazovky a přehled se z prohlížečky stal místem, odkud jde i uklízet.

**Aktivity jsou čtvrtou úrovní číselníku a `scr_Seznam` zanikla.** Dvě
obrazovky pro totéž (vybrat záznam, upravit, smazat) znamenaly dvojí zvyk
i dvojí údržbu. Zrušení obrazovky je nevratné rozhodnutí, proto se přeneslo
všechno, co uměla navíc: **filtry sekce / útvar / stav** jako druhý filtrační
řádek viditelný jen u aktivit, **řazení klikem na hlavičku** sloupce
a **mazání s potvrzením** včetně úklidu vazeb.

Formulář vpravo aktivitu **needituje** — má deset polí a zařazení M:N, což se
do panelu nevejde. Klik na řádek proto otevře `scr_Detail`, formulářová pole
se skryjí a obě tlačítka dole změní text i chování na „Otevřít detail"
a „Nová aktivita". Nové prvky pro to nevznikly, takže ani nový překryv.

**Navbar má nově záložky Přehled a Editace.** Tlačítko „+ Nová položka
rejstříku" zmizelo — se záložkou dělalo totéž dvakrát. Návrat z detailu vede
zpátky do číselníku a nastaví ho na úroveň aktivit s vybraným řádkem; hlídá
to brána, která právě tuhle mezeru našla.

**Fulltext na přehledu jde přes všechny čtyři úrovně naráz**, protože
`colStrom` je celá v paměti — nedeleguje se a ani nemusí. Strop je 2 000
aktivit (`colAkt` je první okno dat, dnes 49) a popisek to říká. Při zadaném
hledání se strom přepne na **plochý seznam výsledků**: rozbalování by
u hledání překáželo, nalezená aktivita se má ukázat rovnou, ne až po
rozkliknutí tří úrovní nad ní. `colOtevrene` se přitom nesahá, takže vymazání
pole vrátí strom do původního rozbalení.

**Chip „osiřelé" na přehledu má vlastní důvod existovat.** Osiřelá položka se
ve stromu **vůbec nezobrazí** — strom ukazuje jen uzly, jejichž předci jsou
otevření, a sirotek žádného předka nemá. Bez chipu je z přehledu neviditelná,
i když v datech je. Chip proto přepne strom na plochý seznam sirotků napříč
úrovněmi; `colStrom` k tomu dostal sloupec `osirely`.

**Koš vedle tužky v řádku stromu.** Nemaže hned, jen naplní `varSmazatD`;
maže až tlačítko v dialogu, který říká, kolik podřízených položek tím osiří.
Sloupce ve stromu o jeho šířku ustoupily doleva. Po smazání se přehled
přenaviguje sám na sebe, aby `OnVisible` přestavěl `colStrom` — příznak
osiřelosti se totiž mění i řádkům, kterých se mazání přímo netýkalo,
a přepisovat je po jednom by bylo křehčí.

**Dvě nové brány, obě mutačně ověřené:**

| brána | co hlídá | mutace |
|---|---|---|
| protiklady ve `vylucuji_se` | `kontrola_prekryvu` už nehlásí dvojici prvků, z nichž je vidět vždy jen jeden (`X = "a"` proti `X <> "a"`) — a u stejného `Visible` dál padá | posunutý popisek přes pole se stejným `Visible` |
| shoda definic kolekce | táž kolekce plněná na dvou obrazovkách musí mít stejné sloupce | `colAkt` bez sloupce `sekce` v jedné z definic |

Druhá vznikla z konkrétní příčiny: `colAkt` se plní na přehledu i v číselníku.
Kdyby se definice rozešly, chovala by se appka podle toho, odkud uživatel
přišel — a nikdo by netušil proč.

Brány: `check_app` OK (5 souborů, 4 obrazovky, 186 prvků, 2 019 vzorců),
`check_solution` 212 kontrol / 0 chyb.



## Číselník, karta zařazení a úklid sirotků (23.08.2026) — balík 1.0.0.35

**F6/D — obrazovka číselníku (`scr_Ciselnik`).** Do 1.0.0.34 se agendy, procesy
a dílčí procesy daly zakládat jedině ručně v SharePointu, což byl pro správce
rámce slepé místo: nový proces musí vzniknout dřív, než pod něj půjde zařadit
aktivita. Jedna obrazovka pro všechny tři úrovně, ne tři samostatné — formulář
se liší jen počtem nadřazených polí a tři skoro shodné obrazovky by znamenaly
trojí údržbu téhož vzorce pro přidělení kódu.

Kód se přiděluje stejným způsobem jako u aktivit: poslední existující v prefixu
+ 1, zleva doplněné nulami. **Náhled** se počítá nad kolekcemi (dotaz na
SharePoint při každém překreslení by obrazovku brzdil), **uložení** si ho
přepočítá nad zdrojem — kolekce může být stará o celou session. Popisek pod
tlačítkem to říká, aby náhled nikdo nečetl jako slib.

Formulář má **dva režimy** (`varCiselnikNova`): zakládání a úprava. Úprava
vznikla proto, aby tužka ve stromu měla kam vést i na úrovni agendy, procesu
a dílčího procesu — do 1.0.0.34 tam jen hlásila, že se ta úroveň mění přímo
v SharePointu. Při úpravě je zamčená úroveň i nadřazený prvek: obojí je
zapečené v kódu a kód se nikdy nemění, takže přesun pod jiného rodiče není
přejmenování, ale nová položka.

**Vlastník se při úpravě nepřepíše naprázdno.** V datech je přípustné mít
vlastníků víc oddělených středníkem („72; 71"), a takový řetězec se v nabídce
jednoho útvaru nenajde — pole by zůstalo prázdné a uložení by je smazalo.
Prázdný výběr proto při úpravě znamená „ponechat stávajícího" a popisek pole
to říká.

**F6/E — tři připomínky z provozu k 1.0.0.34.**

1. **Karta zařazení v detailu aktivity.** Galerie zařazení byla 300×60 px
   (dva řádky písmem 10) zaražená vedle pole Stav — z obrazovky nešlo poznat,
   že jde o zařazení do víc větví mapy. Nově karta přes celou šířku pravého
   sloupce: nadpis s počtem, tři čitelné řádky se štítkem „primární"
   a tlačítko „Spravovat…" v hlavičce karty. Místo se uvolnilo zkrácením
   vnitřního předpisu na polovinu a přesunem stavu vedle něj. U nové aktivity
   nese vysvětlení sám nadpis — samostatný popisek „zatím prázdno" přes
   galerii by neprošel branou `kontrola_prekryvu`, ta počítá geometrii,
   ne `Visible` za běhu.
2. **Dialog mazání byl malý a text se do něj nevešel** — karta 520×236,
   textové pole 456×84 při písmu 12. Nově 640×360 a 576×200. Text doplněný
   o to, že mazání nikdy nesahá na podřízené záznamy: ty zůstanou bez
   nadřazené položky a uklízejí se ve své vlastní entitě.
3. **Úklid osiřelých položek.** Sirotek = záznam, jehož nadřazená položka
   v číselníku není. Vzniká smazáním nadřazené položky a dosud ho nikdo
   neuklidil, protože číselník se z appky mazat nedal. Filtr je v každé
   entitě, kde se ta entita spravuje: agendy, procesy a dílčí procesy
   v číselníku, aktivity v jejich seznamu.

**Význam „úklidu" se liší podle úrovně a je to schválně.** U procesu a dílčího
procesu je to SIROTEK (chybí nadřazená položka), u agendy PRÁZDNÁ VĚTEV
(agenda nemá nadřazenou úroveň, takže osiřet nemůže — ale může být bez
procesů). Kdyby se ty dva významy prohodily, uklízecí tlačítko by nabízelo
mazání živých větví; proto to říká popisek chipu, štítek na řádku i text
dialogu.

`colCiselnik` je plochá kolekce všech tří úrovní v jedné tabulce, stejný vzor
jako `colStrom` na přehledu. Bez ní by galerie musela být trojí: `Switch` nad
`colAgendy` / `colProcesy` / `colDilci` neprojde typovou kontrolou, protože
každá z nich má jiné sloupce. Kolekce se přepočítá při vstupu na obrazovku
a mutace ji dál udržují na místě — **smazání nadřazené položky rovnou přepíše
příznak jejím potomkům**, jinak by se sirotci objevili až po opuštění
a novém otevření obrazovky.

Filtr osiřelých **aktivit** se nedeleguje (`LookUp` do kolekce), takže je
navlečený až na výsledek delegovaného dotazu — stejný kompromis jako fulltext.
Chip vpravo nad seznamem na to oranžově upozorňuje.

**Tři nové brány v `check_app.py`, všechny mutačně ověřené:**

| brána | co hlídá | mutace |
|---|---|---|
| `kontrola_sloupcu_kolekci` | zápis do kolekce se musí trefit do jejích sloupců — všech, ani o jeden víc | sloupec navíc i chybějící sloupec v `Collect` |
| `kontrola_rezimu_ciselniku` | kdo dělá `Navigate(scr_Ciselnik)`, musí nastavit úroveň i režim formuláře | vynechané `Set(varCiselnikNova, …)` |
| `kontrola_predikatu` | v podmínce `Filter` nad velkým listem nesmí být `LookUp` a spol. | `LookUp` vražený do delegovaného filtru aktivit |

Druhá z nich má důvod: `scr_Ciselnik` v režimu úpravy sahá na záznam podle
`varCiselnikKod`. Vstupní bod, který režim nenastaví, otevře formulář v tom,
co zbylo po minulé návštěvě — v horším případě uloží změnu do cizí položky.

Brány: `check_app` OK (6 souborů, 5 obrazovek, 238 prvků, 2 544 vzorců),
`check_solution` 265 kontrol / 0 chyb.



## Připomínky z provozu ke stromu a detailu (21.08.2026 16:10) — balík 1.0.0.34

- **Aaa přesunuto vpravo k identitě uživatele**, popisek „Písmo" zrušený —
  symboly mluví samy. Volba nově platí i na **detailu aktivity** a na
  **obrazovce vazeb**, tedy napříč appkou; **výchozí je střední stupeň**
  (`varFs = 2`), ne nejmenší.
- Na detailu se výšky polí měnit nemusely: popisek 20 px unese 14 pt (~19 px)
  a pole 40 px unese 17 pt (~23 px). Na obrazovce vazeb ano — kód a název jsou
  v řádku pod sebou s pevným Y, takže kód dostal `Height = 20 + varFs` a název
  `Y = 28 + varFs`, jinak by se kód na největším stupni ořízl.
- **Šipka zpět je celý čtvereček** (56 px, `Fill` průhledný, `HoverFill`
  bílá 18 %) — samotná šipka byl malý cíl. Classic/Icon `Fill`/`HoverFill` má,
  takže na to nebylo potřeba nic obcházet.
- **Návrat z detailu jde tam, odkud se přišlo.** `varDetailZpet` nastavuje
  seznam („seznam") i tužka ve stromu („dashboard"); šipka i návrat po uložení
  se podle toho rozhodnou. Do té doby proklik z přehledu končil v seznamu
  aktivit. `Navigate(If(...))` se schválně nepoužilo — brána `kontrola_navigace`
  čte jméno obrazovky hned za `Navigate(`, takže se větví If a uvnitř jsou dva
  samostatné `Navigate`.
- **Klik do řádku stromu detail neotevírá**, jen rozbaluje; detail je jedině
  přes tužku. Dokud dělalo obojí totéž, nebylo poznat, co která akce udělá.
  Tužka je větší (36 px) a odsazená od kraje (`TemplateWidth - 84`), sloupce
  útvaru i počtu se o to posunuly doleva včetně hlaviček.

## Ikona editace, velikost písma, denní publikace mapy (21.08.2026 15:45) — balík 1.0.0.33

**Ikona editace v každém řádku stromu.** Otevře detail dané položky. Detail
dnes existuje jen pro aktivitu, takže na vyšších úrovních je ikona tlumená
a po kliknutí řekne, že se agenda/proces/dílčí proces zatím mění přímo
v SharePoint seznamu — vlastní obrazovka je F6/D. Ikona musí být v šabloně
řádku **až za** překryvnou vrstvou, jinak by ji překryv zakryl a klik spolkl
(stejné pořadí jako `ico_Smazat` za `lbl_RadekPrekryv` v seznamu).

**Velikost písma galerií (tři stupně).** V tmavé liště obou obrazovek jsou
tlačítka **A / A / A** (`varFs` = 0 / 2 / 4). Mění velikost textu a výšku řádků
**jen v galeriích** — seznam aktivit a strom na přehledu — a jejich hlavičky;
zbytek appky zůstává. Rozhodnuto vědomě: Power Apps nemá obdobu CSS proměnné,
takže globální přepínač by znamenal výraz u `Size` všech ~179 prvků, a hlavně
by se nezvětšily pevné rozměry a delší texty by se ořezávaly.

Svisle to vychází samo: prvky uvnitř řádku mají `Height = TemplateHeight - 1`
a `Y = 0`, takže rostou s `TemplateSize` (strom 40 + varFs*4, seznam
56 + varFs*5). Vodorovně se muselo dopomoct — **sloupec kódu se rozšiřuje
spolu s písmem** (`140 + varFs * 12`, resp. `130 + varFs * 12`) a název se
o tolik posouvá, jinak by se při XL oříznulo `AA-BB-CCC-DDDD`.

Cena, kterou to má: `kontrola_prekryvu` v `check_app.py` počítá jen s číselnými
souřadnicemi, takže u prvků převedených na výraz překryv nehlídá. Uvnitř
galerií se tím ale nic neztratilo — řádkové prvky měly výšku jako výraz už
předtím, a proto je kontrola přeskakovala tak jako tak.

**Denní publikace mapy v 7:00.** Power Automate flow má právě **jeden**
trigger, takže „PowerApps + Recurrence" v jednom flow neexistuje. Ruční
spuštění z appky (`MapaPublishFlow.Run()`) muselo zůstat, proto vzniklo druhé
flow **`MapaPublishScheduled`** s triggerem Recurrence (denně 7:00,
Central Europe Standard Time).

Logika se ale nezdvojuje ve zdroji: `src/add_mapa_schedule.py` **klonuje akce**
z hotového `MapaPublishFlow` a mění jen trigger, GUID a název — ostatní zůstává
bajt v bajt. Skript je idempotentní a GUID dvojčete je pevné, aby opakovaný běh
nezakládal v prostředí sirotky. Ověřeno, že akce se na trigger nikde
neodkazují (`triggerBody` 0×, žádná Response akce), jinak by klon s Recurrence
nefungoval.

`check_mapa_flow.py` porovnává **celé** akce obou flow — kdyby se rozešly, mapa
by se v noci publikovala jinak než po stisku tlačítka a nikdo by si toho
nevšiml. Dál hlídá Recurrence denně v 7:00 včetně časového pásma (bez něj by
UTC posunulo běh podle letního času), zápis dvojčete v `customizations.xml`
i v `RootComponents`, a že ruční flow má pořád `PowerAppV2`. 129 -> 142 kontrol,
mutačně ověřeno na třech vadách (chybějící dvojče, hodina 8, rozejité akce).

**Po importu je nutné `MapaPublishScheduled` ručně zapnout** — import stav
zapnutí nemění a nové flow může přijít vypnuté; denní publikace by pak tiše
neběžela. Je to v `HANDOVER.md` §1 vedle mikro-změny před Save.

## Připomínky z provozu k dashboardu a seznamu (21.08.2026 15:00) — balík 1.0.0.31

Uživatel poslal dva snímky dashboardu: ve 12:14 ještě **čtyřsloupcovou**
verzi z 1.0.0.26, ve 14:35 už **strom** z naimportovaného 1.0.0.28 — a právě
ten druhý patří k připomínkám. Žlutě v něm označil sloupec vlastníka.

1. **„Klikání na řádky nefunguje"** — platilo i pro strom a byla to skutečná
   vada. Popisky (kód, název, útvar, počet) ležely nad podkladovým obdélníkem,
   který nesl `OnSelect`, a klik i hover spolkly. Řádek tak reagoval jen na
   mezerách mezi popisky. Opraveno průhlednou vrstvou `lbl_StromPrekryv` přes
   celý řádek jako **posledním** prvkem šablony — stejný vzor, jaký seznam
   aktivit používá od začátku (`lbl_RadekPrekryv`). Nese klik i podbarvení
   při najetí (`RGBA(0, 90, 181, 0.14)`), řádky se nikam neposouvají.
   `check_app.py` má nově obojí v `PREKRYV_POVOLEN`.
2. **„Netuším, co znamenají ta čísla"** — sloupec vlastníka hlavičku vůbec
   neměl a číslo vpravo mělo jen „OBSAHUJE". Doplněny hlavičky
   `VLASTNÍK / VYKONÁVÁ` a `POLOŽEK UVNITŘ`, obě s tooltipem po úrovních;
   tooltip celého řádku číslo vysvětluje taky.
3. **Seznam aktivit: tlačítko „Zobrazit vše"** — vynuluje hledání, sekci,
   útvar i stav naráz. Bez zapnutého filtru je neaktivní, takže je z něj vidět
   i to, jestli vůbec nějaký filtr běží. `Reset()` vrací ovládacím prvkům
   výchozí hodnotu, ale `varSekceKod` / `varUtvarKod` se plní až v `OnChange`,
   který se při Resetu nespustí — proto se mažou zvlášť. Filtrační řádek se
   kvůli místu zúžil (hledání 240→196, sekce 140→124, útvar 180→160,
   stav 130→112, kód 130→116).

Dodatečně zadaný **filtr stavu na dashboardu** (chipy vše / schváleno /
pracovní): filtruje celý strom, ne jen řádky aktivit — zůstanou aktivity
daného stavu a nad nimi jen ty větve, které aspoň jednu takovou obsahují.
Číslo ve sloupci se přepne na počet aktivit toho stavu ve větvi a hlavička
to říká (`AKTIVIT SCHVÁLENO`). Aby přepnutí filtru nesahalo na data ani
nepočítalo nic per řádek, nese si každý uzel `colStrom` už při stavbě
`aktC` (aktivit v podstromu) a `aktS` (z toho schválených); pracovních je
rozdíl, druhý počet se neukládá.

Na přání doplněno: **tooltip řádku rozepisuje kódy útvarů na „kód · název"**
z číselníku Útvary, i pro víc vlastníků oddělených středníkem. Do sloupce se
to nevejde (160 px, u dvou vlastníků teprve ne), proto tooltip.

Při tom **skill zachytil past, kterou by brána nechytila**: `Split()` vrací
sloupec **`Value`**, ne `Result` — `Result` je starý název a Správa notifikací
na něm spálila tři buildy. Napsaná je proto nová kontrola
`kontrola_stareho_result` v `check_app.py` (mutačně ověřená), protože packer
ani import to nechytí a chyba se projeví až neotevřením appky ve Studiu.
Ve vzorci je navíc pojmenovaný rozsah `Split(...) As u`, aby holé `Value`
nebylo dvojznačné vůči `ThisItem` galerie.

Brány: `check_app` 170 prvků / 1690 vzorců, `check_solution` 196 kontrol,
`check_mapa_flow` 129, `check_flow` 19 — vše bez chyb, beze změny výjimek.

## Publish se neprojevoval — chybela mikro-zmena pred Save (21.08.2026 13:07)

Po importu videly ostatni ucty **starou verzi**, prestoze ve Versions byla
nejnovejsi verze Live a pri spusteni naskocil zluty pruh „A new version of
this app is coming". **Vyreseno:** publikovany dokument vznika pri Save +
Publish ze Studia, ne importem solution — a po importu Studio appku nepovazuje
za rozpracovanou, takze **neni co ulozit**. Publish pak zverejni stary
dokument. Pomohla umela mikro-zmena (posun prvku o pixel a zpet), ktera Save
odemkne.

Postup po kazdem importu je v `HANDOVER.md` §1b a v skillu `power-Apps-skill`
(sekce u delby prace u canvas apps) — je to obecna past workflow „build zipu
mimo Studio", ne specifikum tohoto projektu.

Pri hledani opravena i souvisejici vada: **`AppVersion` v `customizations.xml`**
zustavala z puvodniho exportu, takze se appka netvarila jako zmenena. Build ji
ted prepisuje aktualnim UTC razitkem a bez nalezeni tagu skonci chybou
(`dokonci()` v `src/build_app.py`) — od baliku **1.0.0.28**. Samo o sobe to
publish neopravilo, ale spravne to tak byt ma.

## PŘECHOD NA JINÝ STROJ — 21.08.2026 12:45

Návod k rozjezdu, rozdělení práce a otevřené věci drží **`HANDOVER.md`**,
tenhle soubor chronologii a odůvodnění rozhodnutí.

Krátce: appka i publikační flow **běží v provozu** (poslední ověřená verze
v prostředí **1.0.0.26**), hotový a offline ověřený balík k importu je
**`deploy/procesnimapa_1_0_0_27.zip`** s přestavěným dashboardem. Další krok
asistenta je **F6/D — zadávací obrazovky pro agendu, proces a dílčí proces**.

**Úklid:** `runs/app_build` (179 MB rozbalený `pac`) i `runs/mapa_beh`
(generovaný výstup headless brány, nově v `.gitignore`) smazané, `__pycache__`
pryč, náhledový http server na portu 8765 zastavený, z `deploy/` odstraněné
nahrazené balíky 1.0.0.23 a 1.0.0.25 — zůstává poslední ověřený (26)
a aktuální (27). Projekt z 259 MB na ~81 MB, z toho 59 MB `.git`
a 18 MB `.venv` (ani jedno se nepřenáší jinak než klonem).

## F3 OVĚŘENA V PROVOZU — 1.0.0.23 běží (21.08.2026 10:47)

Uživatel naimportoval 1.0.0.23, appka je **bez chyb ve Formulas** a čtyři
kontroly z `deploy/navod_publikace_mapy.md` dopadly dobře:

| co | výsledek |
|---|---|
| soubory v Site Assets, mapa jde spustit z appky | ano |
| `Nacti_DilciProcesy` v běhu MapaPublishFlow | **250 položek** (pagination drží) |
| tlačítko „Zobrazit v HTML" | **zobrazí stránku**, nestahuje |
| fulltext hledání (1.0.0.23) | funguje |

Tím padla i poslední známá vada z 1.0.0.22 — adresa přes náhled knihovny
(`AllItems.aspx?id=…`) je správná a `kontrola_adresy_mapy` ji hlídá proti regresi.
**F3 je hotová.**

**F4 se odkládá:** uživatel nemá přístup k tenantu MPSV (stav 21.08.2026).
Pracuje se dál v PPF DEV.

**Návod pro správce (`deploy/navod_sprava.md`, krok 13) se zatím nepíše** —
rozhodnuto 21.08.2026, až podle finální podoby appky.

## Dashboard prestaven na strom, deploy kopie mapy opravena (21.08.2026 12:40)

Uzivatel naimportoval 1.0.0.26 a poslal dve pripominky.

### 1. Deploy kopie mapy se rozesla se zdrojem — MOJE CHYBA
Upravy sly do `src/mapa_template.html`, ale do Site Assets se nahrava
`deploy/mapa_template.html` a ta zustala z 20.08. Kopie se delala rucne.
Publikovana mapa proto vypadala nezmenene a uzivatel se spravne ptal, jestli
se uprava vubec nahrala.

Naprava, aby se to nemohlo opakovat:
- `src/build_mapa.py` zapisuje **i deploy kopie** (`mapa_template.html`
  i `procesni_mapa.html`) — clovek uz je nekopiruje,
- `src/check_mapa_html.py` porovnava deploy sablonu se zdrojem a hlida, ze
  `deploy/procesni_mapa.html` obsahuje nove ovladaci prvky (31 kontrol).

**Do Site Assets nahrat `deploy/mapa_template.html` A `deploy/procesni_mapa.html`
znovu** — obe jsou nove.

### 2. Dashboard mel byt strom, ne ctyri sloupce
Sloupcovy rozpad (Miller columns) uzivateli nevyhovoval. Prestaveno na
**strom v radcich** s postupnym rozpadem, jak to ma mapa:

- jedna galerie nad plochou kolekci `colStrom` (agendy + procesy + dilci
  procesy + aktivity v jedne tabulce, sloupce kod/nazev/utvar/uroven/rodic/pocet),
- **razeni resi kod**: `AA-BB-CCC-DDDD` se lexikograficky radi presne stromove,
  takze jediny `Sort(kod)` da spravne poradi bez rekurze,
- rozbalene uzly drzi kolekce `colOtevrene`; radek je videt, kdyz jsou otevreni
  vsichni jeho predci,
- **ctyri tlacitka rozpadu** (jen agendy / + procesy / + dilci procesy / vse)
  rozbali celou uroven naraz, klik na sipku u radku rozbali jednu vetev;
  po rucnim rozbaleni se zvyraznene tlacitko zhasne a popisek rekne
  „vlastni rozbaleni",
- odsazeni, barevny pruh a barva pisma odlisuji urovne, klik na aktivitu
  otevira detail, prepinac „Kod" ze seznamu plati i tady.

Vychozi stav pri prvnim otevreni: rozbalene agendy (uroven 2).

### Dve opravene brany (obe mutacne overene)
`check_app.py` hlasil dva falesne poplachy nad novou obrazovkou:
- `ThisItem.<sloupec>` se overoval jen proti listum, takze kazdy sloupec
  vlastni kolekce vypadal jako preklep → kontrola nove zna i sloupce, ktere
  si appka vyrabi sama v `Collect`/`ClearCollect`,
- `RemoveIf(colOtevrene, …)` v galerii se hlasil jako „mazani bez potvrzeni",
  prestoze jde o stav rozbaleni v pameti → kontrola ted rozlisuje datovy zdroj
  od lokalni kolekce.

Mutace `ThisItem.kodX` i `RemoveIf(Aktivity, …)` dal padaji, vyjimka ve
`scr_Vazby` se dal hlasi.

**`deploy/procesnimapa_1_0_0_27.zip`** — `check_app` OK (163 prvku, 1584
vzorcu), `check_solution` **189 kontrol, 0 chyb**, oba flow OK.

### Overeni po importu 1.0.0.27 (na uzivateli)
1. Prehled ukaze strom, ve vychozim stavu rozbalene agendy s procesy.
2. Tlacitka rozpadu: „+ dilci procesy" rozbali celou treti uroven, „vse"
   i aktivity, „jen agendy" sbali.
3. Klik na sipku u jedne vetve rozbali jen ji; popisek vpravo prepne na
   „vlastni rozbaleni".
4. Klik na radek aktivity otevre detail.
5. **Nahrat obe HTML z `deploy/` do Site Assets** a dat „Obnovit mapu" —
   teprve pak bude publikovana mapa mit nove ovladaci prvky.
6. Save & Publish.

## F6 skupiny A–C — prvni podoba (21.08.2026 12:05)

1.0.0.25 uživatel naimportoval a **všechno v prostředí funguje**: appka bez chyb,
tlačítko „Obnovit mapu" spustí flow, mapa se přegeneruje, `Nacti_DilciProcesy`
vrací 250 položek, „Zobrazit v HTML" mapu zobrazí (nestahuje), fulltext hledá.
Tím jsou **F2 i F3 ověřené v provozu**.

Zadání F6 z 21.08.2026 (detail v `PLAN.md`), stav:

### A — HTML mapa: hotovo
Přepínač **stupně rozbalení** (agendy / +procesy / +dílčí / vše) místo tlačítek
Rozbalit–Sbalit; **zatržítko „Zobrazit kód"** (výchozí zapnuto, skrývá CSS —
hledání podle kódu funguje dál); **čtyři stupně velikosti písma** přes jedinou
proměnnou `--fs` (všechny velikosti přepsané na `rem`, žádná druhá varianta
stránky se nikam nezapéká); **nápověda na řádku** s typem prvku, kódem, názvem
a počtem aktivit; **vrstvy odlišené** podkladem řádku, proužkem vlevo a barvou
linky odsazení. Volby se pamatují v `localStorage` v `try/catch`.

Dvě nové brány, obě mutačně ověřené:
`src/check_mapa_html.py` (26 statických kontrol, 6/6 mutací) a
`src/check_mapa_beh.py` (18 kontrol **v headless Edge** — proklikne ovládací
prvky a čte výsledný DOM, 4/4 mutace). Chrome extension nebyla dostupná;
headless Edge přes `--dump-dom` je navíc spustitelný opakovaně jako brána.

### B — drobnosti v appce: hotovo
Šipka `ico_Detail` z řádku pryč (řádek otevírá detail celý od 1.0.0.20);
**přepínač „Kód: zobrazen / skrytý"** v řádku filtrů (výchozí zobrazen, název
aktivity se při skrytí posune doleva, řazení podle kódu zůstává); v detailu
**galerie zařazení** o výšce dvou řádků se svislým posuvníkem, primární
zařazení tučně, nadpis nese počet.

### C — dashboard: postavený, čeká na import
Nová obrazovka `scr_Dashboard` je **úvodní** (rozhodnuto 21.08.2026). Navbar má
záložky Přehled / Seznam aktivit, pod ním čtyři karty s čísly (agendy, procesy,
dílčí procesy s počtem zmapovaných, aktivity se schválenými) a **rozpad ve
čtyřech sloupcích** agenda → proces → dílčí proces → aktivita. Klik zúží sloupec
napravo, sloupce čekající na volbu ukazují výzvu, klik na aktivitu otevře detail.

Vědomá rozhodnutí:
- **Sloupec aktivit ukazuje primární zařazení** (`Aktivity.dilci_proces_kod`).
  Aktivita zařazená i jinam se v mapě objeví ve všech větvích, tady je pod tou
  hlavní — přes vazební tabulku by se ke každému řádku dohledával název zvlášť.
  Kde všude aktivita je, ukazuje její detail (a nově i s posuvníkem).
- **Počty se počítají z kolekcí, ne z listu** — `CountRows` nad SharePointem se
  nedeleguje. Aktivity se načítají do `colAkt` v `OnVisible`, a jen když je
  potřeba (`varAktStale` se zvedne po každém uložení i smazání aktivity).
  Nad 2 000 aktivitami je `colAkt` první okno dat, což říká tooltip karty.

`check_app.py` měl u dashboardu **falešný poplach na delegaci**: hlásil
`CountRows` nad `Aktivity`, přestože šlo o `CountRows(Filter(colAkt, …))`
v témže vzorci, kde se kolekce plní. Kontrola teď rozhoduje podle argumentů
konkrétního volání, ne podle výskytu názvu listu kdekoli ve vzorci —
mutace `CountRows(Aktivity)` dál padá.

**`deploy/procesnimapa_1_0_0_26.zip`** — brány: `check_app` OK (182 prvků,
1709 vzorců), `check_solution` **208 kontrol, 0 chyb** (nově hlídá i to, že
úvodní obrazovka je `scr_Dashboard`; mutace prohozeného pořadí chycena).

Úklid connection reference `…_12718` **znovu odložen** — mísit ho s takhle
velkou změnou by při selhání importu zamlžilo příčinu.

### Ověření po importu 1.0.0.26 (na uživateli)
1. Appka startuje **Přehledem**, čísla karet sedí (dnes 7 / 46 / 250 / 46).
2. Rozpad: klik na agendu naplní procesy, pak dílčí procesy, pak aktivity;
   „Zrušit výběr" vrátí do výchozího stavu; klik na aktivitu otevře detail.
3. Záložky Přehled ↔ Seznam aktivit přepínají.
4. Seznam: řádek už nemá šipku, otevírá se klikem kamkoli; „Kód: zobrazen"
   sloupec skryje a název se posune doleva.
5. Detail aktivity s víc zařazeními ukáže dva řádky a posuvník.
6. **Nahrát nový `deploy/mapa_template.html` do Site Assets** a spustit
   „Obnovit mapu" — jinak publikovaná mapa zůstane v původní podobě. Šablonu
   čte flow z knihovny, ne z repa.
7. Save & Publish.

## Tlačítko „Obnovit mapu" hotové — 1.0.0.25 (21.08.2026 11:20, ověřeno v provozu)

Uživatel dodal přes git `input/procesnimapa_1_0_0_24.zip` s provedeným
**Add flow**: v `.msapp` → `References/DataSources.json` je nově
`MapaPublishFlow` jako `ServiceInfo` nad `shared_logicflows`. Tím šlo tlačítko
zabalit.

**`deploy/procesnimapa_1_0_0_25.zip`** — souhrnná karta má tři tlačítka:
„Obnovit mapu" | „Zobrazit v HTML" | „+ Nová aktivita".

Brány (offline; prostředí balík zatím nevidělo):

| brána | výsledek |
|---|---|
| `check_app.py` | 113 prvků, 1110 vzorců, 3 známé výjimky — OK |
| `check_solution.py` | **137 kontrol, 0 chyb** |
| `check_mapa_flow.py` | 129 kontrol — OK |
| `check_flow.py` | 19 kontrol, 104 vzorků — OK |

Nová kontrola „`.Run()` musí mít datový zdroj" **mutačně ověřena**: po záměně
`MapaPublishFlow` za neexistující jméno brána spadla s adresnou hláškou.

**Úklid connection reference `…_12718` zůstává odložený i teď.** Obě flow na ní
visí (`MapaPublishFlow` i `AktualizaceKratkehoNazvu`) a výměna za
`ppf_sharedsharepointonline_bec33` znamená při importu přemapování připojení.
Kdyby se to přibalilo k tlačítku a import selhal, nepůjde poznat, co za to může.
Půjde samostatně jako 1.0.0.26.

### Ověření po importu 1.0.0.25 (na uživateli)
1. Appka se otevře ve Studiu bez chyb ve Formulas.
2. Klik na **Obnovit mapu** → hlášení „Publikace mapy spuštěna…", tlačítko na
   okamžik zšedne.
3. V Power Automate má `MapaPublishFlow` nový běh, zeleně, `Nacti_DilciProcesy`
   = 250 položek.
4. `procesni_mapa.html` v Site Assets má **čerstvý čas úpravy** a razítko
   „vygenerováno" v hlavičce mapy odpovídá.
5. Save & Publish, jinak uživatelé uvidí starou verzi.

## Zadání kroku (splněno 21.08.2026 v 1.0.0.25)

`MapaPublishFlow` **je** v balíku jako `Workflows/MapaPublishFlow-60E67E42-….json`,
ale v `.msapp` → `References/DataSources.json` jsou jen SharePoint listy — flow
mezi datovými zdroji appky **není**. `MapaPublishFlow.Run()` by proto Studio
odmítlo („Name isn't valid"). Dělba práce:

1. **Uživatel ve Studiu:** Power Automate → **Add flow** → `MapaPublishFlow`
   → Uložit → Publikovat → export unmanaged solution → dodá zip.
2. **Asistent:** doauthoruje `btn_ObnovitMapu` do souhrnné karty na `scr_Seznam`
   (vzorec připravený v `deploy/navod_publikace_mapy.md`), přibalí odložený
   **úklid connection reference `…_12718`**, vrátí 1.0.0.24.

Bez kroku 1 nemá smysl stavět — z exportu bez Add flow vznikne totéž, co je dnes.

**Připraveno předem (21.08.2026 11:05), čeká jen na zip:**

- `btn_ObnovitMapu` v `src/app_src/scr_Seznam.pa.yaml` — třetí tlačítko souhrnné
  karty vlevo od „Zobrazit v HTML" (`X = btn_Mapa.X - Self.Width - 12`, žádná nová
  magická čísla). `DisplayMode` proti dvojímu kliku, `IfError` kolem `.Run()`.
  Notifikace záměrně říká „**spuštěna**", ne „hotovo": `MapaPublishFlow` nemá akci
  Respond to a PowerApp, takže se `.Run()` vrátí po odstartování, ne po doběhu —
  hlásit dokončení by lhalo.
- Nová kontrola v `src/check_solution.py`: každý identifikátor volaný jako `.Run()`
  ve vzorcích musí být v `.msapp` → `References/DataSources.json`. Regresní pojistka
  přesně na tenhle případ (flow je v solution, ale k appce není připojené).
- `src/check_app.py` nad upravenými zdroji prochází (113 prvků, 1110 vzorců,
  3 známé výjimky).

Pracovní strom čistý, `git pull` dotáhl commit z večera 20.08. (22:07):
**schematický obrázek datového modelu** `viz/db_schema.html`, generovaný
`src/build_schema_diagram.py` ze `src/schema.json` a počtů z `runs/normalize/`.
Kreslí 6 SharePoint listů včetně vazeb, typů a příznaků; self-contained,
bez CDN. Do dokumentace se hodí jako doprovod k `deploy/sharepoint_schema.md`.

**Blokující krok je na uživateli:** naimportovat `deploy/procesnimapa_1_0_0_23.zip`
jako upgrade a otevřít appku ve Studiu (panel Formulas). 1.0.0.23 je zatím
ověřený jen offline branami; poslední ověřeně běžící verze v prostředí je
1.0.0.22. Do výsledku importu se na zdrojích appky nepracuje.


## Konec dne 20.08.2026 — 1.0.0.23 nevyzkoušený, projekt uklizený

Uživatel ztratil přístup do virtuálu dřív, než stihl balík naimportovat.
**1.0.0.23 je proto ověřený jen offline branami, ne během ve Studiu**;
poslední ověřeně běžící verze v prostředí je 1.0.0.22. Zítra se začíná
importem, ne další prací na zdrojích — neověřené změny se opravují nejlevněji
dřív, než se na ně navrství další.

**Úklid:** `runs/app_build` (179 MB rozbalený `pac` a mezibuildy) smazaný,
`src/__pycache__` taky; projekt ze 183 MB na 4 MB. Kořen drží jen `.md`,
`kody.json` a adresáře podle konvence. Náhledový http server na portu 8765
zastavený. Pracovní strom čistý, vše pushnuté.

`pac` se při příštím buildu rozbalí sám z rozšíření VS Code — stojí to pár
sekund, nic se nastavovat nemusí.

## Fulltext, mazání s potvrzením, datum vytvoření — 1.0.0.23 (20.08.2026 18:40)

**Hledání najde řetězec kdekoli v názvu i v kódu.** `StartsWith` hledal jen od
začátku názvu; nahradil ho `Search(…, txt, nazev_kratky, Title)`.

Cena za to je delegace: **`Search` delegovatelný není** a SharePoint konektor
umí z textových operací delegovat jedině `StartsWith`. Aby to bolelo co nejmíň,
je `Search` navlečený **až na výsledek delegovaného `Filter`** — sekce, útvar
a stav zúží dotaz na serveru nad celým rejstříkem a fulltext běží nad tím, co
přijde. Do 2 000 aktivit (dnes 46) je výsledek úplný; nad tím prohledá jen
první okno. `lbl_ChipFiltr` na to **oranžově upozorní**, když se hledá bez
zúžení, a výjimka je pojmenovaná ve `VYJIMKY_DELEGACE`, takže z výstupu brány
nezmizí. Až rejstřík povyroste, je náhradou fulltext v publikované HTML mapě
nebo pomocný indexovaný sloupec s normalizovaným názvem.

**Mazání aktivity přímo ze seznamu, ale jen přes potvrzení.** Ikona koše
v řádku pouze nastaví `varSmazat`; smaže až tlačítko v dialogu, který má
červený pruh, vypíše kód i název a připomíná, že zmizí i zařazení do dílčích
procesů. Power Apps nemá nativní `confirm()`, takže je to vrstva nad
obrazovkou; stín zachytí kliknutí mimo kartu.

**Akční ikony musely nad překryvnou vrstvu.** `lbl_RadekPrekryv` pokrývá celý
řádek kvůli hoveru, takže ikony pod ním by nešly kliknout — v pořadí potomků
jsou proto až za ním. Alternativa (zkrátit vrstvu) by znamenala, že se pravý
okraj řádku při najetí nezvýrazní.

**Nová brána `kontrola_potvrzeni_mazani`.** Uvnitř galerie se nesmí objevit
`Remove`/`RemoveIf` — řádek je celý klikací a ikony jsou malé, takže mazání
přímo v šabloně řádku znamená nevratnou ztrátu dat na jeden překlep. Kontrola
rovnou našla `ico_Odebrat` na `scr_Vazby`; tam je to ale **vratná** operace
(vazba se vrátí kliknutím na + vedle a primární vazbu vzorec odebrat nedovolí),
takže dostala pojmenovanou výjimku ve `VYJIMKY_MAZANI` a hlásí se jako varování.

**Sloupec VYTVOŘENO a řazení podle něj.** Bere se vestavěný SharePointí
`Created`, ne `datum_aktualizace` — datum vzniku ručně změnit nejde. První klik
na hlavičku dá nejnovější nahoru.

**Šipka řazení je vidět.** Aktivní sloupec je nově **modrý** a nese `▲`/`▼`;
dřív byla šipka šedá v šedém textu velikosti 10. Výchozí řazení je podle kódu.

**Filtry zdrobněly** — výška 36 → 32, písmo 12 → 11, popisky 10 → 9, užší pole.

**Mutační testy:** 3 nad kontrolou mazání a datem (všechny chycené).

### Nedořešené, čeká na rozhodnutí
`btn_Smazat` v detailu aktivity maže **bez potvrzení** — je mimo galerii, takže
ho nová brána nehlídá. Nekonzistence proti seznamu; sjednotit by znamenalo
přidat týž dialog i na `scr_Detail`.

## Tlačítko „Zobrazit v HTML" míří na náhled knihovny — 1.0.0.22 (20.08.2026 15:25)

Uživatel dodal adresu z reálného kliknutí v knihovně. Je to **náhled knihovny**,
ne přímý odkaz na soubor:

```
…/SiteAssets/Forms/AllItems.aspx?viewid=<GUID zobrazení>&id=<cesta k souboru>&parent=<cesta ke složce>
```

Rozdíl, na kterém to celé stálo: na přímou cestu `…/SiteAssets/procesni_mapa.html`
pošle SharePoint kvůli *Strict browser file handling* `Content-Disposition:
attachment` a soubor skončí v Downloads. Přes `AllItems.aspx?id=…` ho servíruje
náhledem, který ho zobrazí. Adresa se přebírá **celá včetně `viewid`** — pochází
z ověřeného kliknutí a zkracovat ji bez ověření v prostředí by znamenalo hádat.

**Nová kontrola `kontrola_adresy_mapy`** hlídá, že `varMapaUrl` nekončí `.html`
(ani před dotazovacím řetězcem) a je `https`. Je to regresní pojistka přesně na
tuhle chybu: appka běží, tlačítko funguje, jen výsledek skončí v Downloads —
žádná jiná brána takové selhání nezachytí. Mutačně ověřeno 3 mutacemi.

Sonda `src/zjisti_url_mapy.js` v repu zůstává — bude potřeba znovu při přenosu
na tenant MPSV, kde bude adresa jiná.

### Další krok
Import 1.0.0.22 a vyzkoušet tlačítko. Pak zbývá připojit `MapaPublishFlow`
k appce ve Studiu (tlačítko „Obnovit mapu") a úklid cizí connection reference.

## Hlavní riziko projektu padlo — mapa se v tenantu ZOBRAZÍ (20.08.2026 15:15)

**Klik na `procesni_mapa.html` v knihovně Site Assets mapu otevře.** Odložené
ověření z `PLAN.md` kroku 10 tím proběhlo a dopadlo dobře: publikační flow
smysl má a zobrazení se nemusí stěhovat do canvas appky. Je to zároveň
oprava závěru z FloorPlanu, který tvrdil, že `.html` i `.aspx` ze Site Assets
se v PPF tenantu stahují **vždy** — neplatí to.

**Zbývá dílčí vada: tlačítko „Zobrazit v HTML" soubor stáhne do Downloads.**
Rozdíl není v souboru, ale v adrese. Knihovna otevírá soubor náhledovou
stránkou SharePointu; appka volá `Launch()` na přímou cestu
`…/SiteAssets/procesni_mapa.html` a na tu pošle SharePoint kvůli *Strict
browser file handling* `Content-Disposition: attachment`.

**Sonda `src/zjisti_url_mapy.js`** to rozhodne měřením, ne hádáním: u šesti
kandidátních adres (přímá, `?web=1`, `Doc.aspx` ve dvou režimech,
`embed.aspx`, `WopiFrame.aspx`, plus `LinkingUrl` ze SharePointu) přečte
hlavičku odpovědi a vypíše `ZOBRAZÍ SE` / `STÁHNE SE`. Volá se
s `redirect: "manual"` — kdyby fetch přesměrování potichu následoval, měřily
by se hlavičky úplně jiné adresy.

Záložní cesta, kdyby se stahovalo všechno: **stránka s web partem Vložit**
(stránky se nestahují nikdy). Mapa v iframu poběží i pod sandboxem
`about:srcdoc` s `connect-src 'none'`, protože data jsou zapečená přímo
ve stránce a nic nefetchuje. Obě cesty popisuje
`deploy/navod_publikace_mapy.md` krok 2.

**Grafika:** uživatel ji odsouhlasil jako lepší, další kolo úprav odloženo.

### Další krok
Dostat funkční adresu (sonda nebo prostě zkopírovat z adresního řádku)
a dosadit ji do `varMapaUrl` v `App.OnStart` — je to jediné místo v appce,
kde je adresa mapy zapsaná.

## Hover na řádku, překryvy a oprava flow — 1.0.0.21 (20.08.2026 15:00)

**Řádek na najetí myší nereagoval a byla to systémová chyba, ne kosmetika.**
Hover dostane jen control **přímo pod kurzorem**, a řádek galerie je ze čtyř
pětin pokrytý labely — podkladový obdélník s `HoverFill` se ho proto nikdy
nedočkal. Řeší to **průhledná vrstva přes celý řádek** (`lbl_RadekPrekryv`,
poslední potomek = nejvýš): `Fill` průhledná, `HoverFill` 10% modrá,
`HoverBorderColor` modrý rámeček. Je to **Label, ne Rectangle** — jen Label
umí `HoverBorderColor`. Vrstva zároveň dělá klikání celého řádku, takže
`OnSelect` na labelech je pojistka, ne jediná cesta.

**Pohyb řádku zapíná `Gallery.Transition`.** Bez `Transition.Push` galerie
na najetí nereaguje vůbec; žádná jiná vlastnost to nedělá.

**Nová brána `kontrola_prekryvu` v `check_app.py`.** Vznikla z vady, kterou
našel uživatel očima: `lbl_l_Vazby` (X 40, šířka 740) zasahoval do nabídky
`drp_StavDetail` (X 700) a navíc seděl na téže pozici jako `lbl_l_TextOR`.
Studio ani packer takový překryv nehlásí, appka se otevře — pozná se to až
na snímku obrazovky. Kontrola porovnává **jen sourozence**: souřadnice prvku
uvnitř galerie jsou relativní k šabloně řádku, takže srovnávat je s prvky
obrazovky nemá smysl (první verze na tom vyrobila 5 falešných nálezů).
Počítá se jen tam, kde jsou všechny čtyři souřadnice čísla.

**Kontrola rovnou našla tři další překryvy na `scr_Vazby`** — vysvětlující
odstavec (Y 84, výška 52) přetékal přes popisky obou sloupců i přes
vyhledávací pole. Zkrácen na 40 px, vše pod ním o 36 px níž.
`lbl_l_Vazby` v detailu je teď krátký popisek nad tlačítkem; plný výklad
zůstal v tooltipu tlačítka.

**Flow spadlo na typu obsahu šablony.** `body('Sablona')?['$content']` skončilo
hláškou *„Property selection is not supported on values of type 'String'"*:
`Get file content using path` s `inferContentType=true` u `.html` odvodí
textový typ a obsah **dekóduje sám**, takže `body()` vrací rovnou řetězec, ne
objekt s base64. Výraz je teď `replace(replace(body('Sablona'), …))` —
bez `string()` naschvál, aby při změně typu spadl hlasitě místo tichého zápisu
JSON obalu do stránky. Brána má na to tři kontroly (`?['$content']` se nesmí
objevit, `base64ToString` taky ne, `inferContentType` musí být `true`)
a mutační test **regresi na tuhle chybu**.

**Mutační testy:** 13 nad flow, 3 nad kontrolou překryvu — všechny chycené.

### Další krok
Nezměnil se: ověřit, jestli tenant HTML ze Site Assets **zobrazí, nebo stáhne**
(`deploy/navod_publikace_mapy.md`, krok 2).

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

1. **Naimportovat `deploy/procesnimapa_1_0_0_23.zip`** jako upgrade, otevřít appku
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
