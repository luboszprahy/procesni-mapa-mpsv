# STATUS — Procesní mapa MPSV

Aktualizováno: **2026-09-06 19:55**. Balík **1.0.0.100** — F15 (číselník
útvarů), F16 (víc vlastníků v appce **i v importním Excelu**), F17 (pruh
voleb), tlačítko Přesun a čtyři opravy z auditu kola 7.
Hotová **F14**: krátký název se zapisuje přes REST MERGE, ne `PatchItem` —
z balíku zmizel poslední GUID listu natvrdo a **balík je pro každý tenant
stejný**. Dvoubalíkový režim končí.

## CO JE NA TOBĚ — v tomhle pořadí

1. **Otestuj balík 1.0.0.101 na PPF DEV.** Celá sada je v **`deploy/ppf/`**,
   postup krok za krokem v `deploy/ppf/README.md` (sedm kroků).

   - **`ImportFlow` po importu ručně zapni** — v balíku 100 nešlo zapnout
     (zacyklený `runAfter`, opraveno v 101) a import stav zapnutí nemění.
   - **Krok 1 spusť znovu i tam, kde už běžel** (`deploy/ppf/01_zaloz_listy.js`) —
     balík 99 přidal list `Útvary`, bez něj se formulář číselníku neotevře.
   - Číselník útvarů narostl ze 7 na 44 položek → přenes data znovu
     (`deploy/ppf/02_import_dat.js`, anonymizovaná).
   - Do Site Assets nahraj `deploy/ppf/site_assets/` — je tam i importní
     šablona s 12 sloupci.

   Co je nového proti tomu, cos viděl naposledy: tlačítko **Přesun** v řádku
   procesu (Editace → Procesy), sjednocený pruh voleb na úvodní obrazovce,
   **víc vlastníků** u agendy, procesu i dílčího procesu, a `O33` je zařazený
   pod `Sekce 3`.
2. Ještě neodzkoušená v provozu je oprava `substring` z balíku 96 — plný přesun
   z aplikace, blok **I** testovacího scénáře. To je jediné, co u přesunu chybí.
3. Až bude přístup na MPSV: import `deploy/mpsv/` a zapnout
   `AktualizaceKratkehoNazvu` (blok **K** testovacího scénáře).

## 07.09.2026 večer — F21/F22: úklid mapy a druhá varianta rozkladu

Zadal uživatel nad snímkem mapy. Dvě věci najednou: **úklid** toho, co
na stránce přebývalo, a **vodorovná varianta** rozkladu vedle sloupcové.

**Co zmizelo.** Podtitulek „Sekce 3 · vygenerováno …" — mapa nese celý
rejstřík (7 agend, 46 procesů), takže z ní ta hlavička dělala výsek, kterým
není; zůstalo jen datum. Barevná legenda se čtyřmi puntíky. Vysvětlivka
odznaku zůstala u stromu, ale **v obou rozkladech se schová** — mluví
o odznaku v řádku, a ten karty rozkladu nemají.

**Barvy jsou teď jedna monochromatická řada** odvozená z barvy navbaru:
`#110b7a → #2a3f9e → #4463bd → #5470c4`, podklady tytéž barvy naředěné bílou.
Předtím se v paletě mísil tyrkys se zelenou a vedle tmavě modré hlavičky to
byly tři nesouvisející rodiny. Hierarchii teď dělá **sytost**, ne odstín —
což je zároveň důvod, proč k ní není potřeba legenda. Kontrast je spočítaný,
ne odhadnutý: nejtěsnější dvojice je 4,62:1 (sekundární text na podkladu
agendy), bílý text na nejsvětlejší hlavičce 4,68:1 — obojí nad WCAG AA.

**Vodorovná varianta** je třetí volba přepínače (`Strom │ Rozklad │ Rozklad
vodorovně`); sloupcová zůstala beze změny. Úrovně leží jako pásy pod sebou,
hlavička vlevo, karty v pásu vedle sebe, pás roluje vodorovně — 250 dílčích
procesů se do řádky nevejde a zalomit ji nelze, jinak přestane být poznat,
co je jedna úroveň. Spojnice vedou dolů místo doprava.

**Podstatné je, že si obě zobrazení nemají čím lhát.** Vrstvy počítá jedna
`rzVrstvy()`, karty staví jedna `rzKarta()`, spojnice kreslí jedna
`rzKresliSpojnice()` s osou jako parametrem; renderery řeší výhradně
rozvržení. Kdyby si každé počítalo své, obě stránky by vypadaly věrohodně
a jen jedna by mluvila pravdu. Brána to hlídá stejně, jako od F20 hlídá
společnou `filtruj()`.

**Ověřeno:** brána `check_mapa_html.py` 46 kontrol / 0 chyb (dřív 37),
`test_rozklad.js` 38 kontrol (dřív 28) — mezi nimi přímé porovnání počtů
mezi zobrazeními: `7/46/250/46` bez výběru, `7/10/41/10` po výběru agendy 01,
`2/3/6/1` při hledání „rozpočt", v pásech i sloupcích totéž.

**Mutačně 5/5** — a stojí za zápis, proč první běh nic nedokazoval: hlásil
„chyceno" u všech pěti mutací, ale test byl u všech zelený a červenala jen
brána. Příčina nebyla v mutacích: mutační skript spouštěl build přes
`shell=True` s dopřednými lomítky v cestě, cmd.exe ho nespustil, brána
zčervenala na nesouhlasu `runs/build` se zdrojem a **test celou dobu běžel
nad starou, nezmutovanou stránkou**. Po opravě padá každá mutace z vlastního
důvodu (test 4×, brána 2×). Mutační skript teď na neúspěšný build zastaví,
místo aby ho přešel — bez toho měření tvrdí, co se mu zlíbí.

**Prohlédnuto v prohlížeči** (rozšíření Chrome se konečně připojilo — bylo
nainstalované celou dobu, jen nebyl vybraný prohlížeč: `list_connected_browsers`
ho ukázal a `select_browser` stačil). První podoba vodorovné varianty
neobstála, uživatel ji odmítl slovy „moc namačkaně, nepřehledně". Tři
příčiny a tři opravy:

| co vadilo | proč | oprava |
|---|---|---|
| svazek křivek z jednoho rodiče | deset dětí = deset oblouků sbíhajících se do chuchvalce a křižujících celou řádku | v pásech se kreslí **lomeně** — jedna svislá noha, vodorovná sběrnice, odbočky k dětem, jako v org. schématu |
| pás zabíral půl obrazovky | jediný dlouhý název natáhl řádku na čtyři řádky a všechny karty s ní | název se ořízne na tři řádky (celý zůstává v nápovědě), karty mají `align-items:stretch`, takže tvoří mřížku, ne schody |
| hlavička pásu přebíjela obsah | plný tmavý blok přes celou výšku byl nejsytější věc na obrazovce | štítek: barevný text a svislý pruh, žádná plocha |

Tím se na obrazovku vejdou všechny čtyři pásy najednou. Sloupcová varianta
zůstala beze změny — křivky se v ní kříží mnohem míň, protože sousední
vrstvy jsou vedle sebe, ne nad sebou.

### Druhé kolo připomínek (19:44) — a jedna oprava, která platí pro oba rozklady

Lomené čáry z předchozího kola **neobstály**: „nesjednocuj ty čáry, není poznat
jak karty patří pod sebe." Sdílená vodorovná sběrnice je hezká na pohled, ale
právě tím sdílením vzala informaci o tom, které dítě patří kterému rodiči.
Spojnice jsou proto zase **samostatné křivky** — s tím rozdílem, že ve
vodorovné variantě vycházejí z **různých bodů spodní hrany rodiče**,
rozprostřených podle pořadí dítěte. To byl skutečný důvod původního
chuchvalce: ne oblouky, ale jeden společný výchozí bod. Mezery mezi kartami
jsou vzaté ze sloupcové varianty (tam karta zabírá 48 % šířky sloupce a zbytek
je pruh pro čáru) — tady je to spodní odsazení řádky, 46 px.

**Volba „Rozbalit" teď rozbaluje opravdu vše, a to v obou rozkladech.**
Dosud ji zúžení výběrem přebíjelo: kdo měl vybranou agendu bez aktivit
a zvolil „vše až po aktivity", dostal hlášku, že rejstřík končí — přestože
aktivity v rejstříku jsou. Změna volby proto výběr zahodí; zužovat se dá zase
klikáním. Ověřeno v prohlížeči i testem: `7/46/250/46` v obou zobrazeních,
349 karet celkem. Brána 46 kontrol, `test_rozklad.js` 44 kontrol,
mutačně 5/5. (Zpráva commitu `fd0cdae` uvádí u testu 46 — správně je 44.)

Přepínač se jmenuje `Řádkové zobrazení │ Rozklad svisle │ Rozklad vodorovně`.

### Třetí kolo (19:52) — úprava stromu

Zadal uživatel: přejmenovat první tlačítko, posunout úrovně vlevo a dát mezeru
mezi řádky. Odsazení stupně bylo 26+14 px — na čtvrté úrovni odtékal text
doprava a řádky se zkracovaly; je teď 16+12. Zpět až na 17+9 px to jít nemůže,
ty 24.08.2026 splývaly, ale hierarchii navíc drží nová mezera 4 px za každým
řádkem (i mezi rodičem a prvním potomkem) — bez ní na sebe barevné pruhy
vrstev navazovaly a splývaly v jednu plochu.

Vedlejší efekt delšího popisku: lišta se zalomila a přepínač velikosti písma
spadl na druhý řádek. Vyhledávací pole má proto minimum 190 px místo 260.

### Čtvrté kolo (19:56) — čáry zpět do jednoho bodu, značka jako kolečko

Rozprostření začátků spojnic po spodní hraně rodiče (třetí kolo) uživatel
zamítl: **čáry mají vycházet z jednoho středového bodu**. Vějíř z jednoho
místa čte hierarchii líp — je vidět, že za všechny ty čáry může jedna karta.

Značka „jde rozpadnout níž" je teď **kolečko v barvě vrstvy** s bílou šipkou,
ne holá šipka. Sedí přesně v bodě, ze kterého spojnice vycházejí (v pásech
dole uprostřed, ve sloupcích vpravo uprostřed), takže značka a začátek čar
jsou totéž místo.

**Rozbalování uživatel potvrdil jako v pořádku** (20:05) — měření sedělo,
chyba tam žádná nebyla.

### Páté kolo (20:05) — místo pro obsah

Okraje byly široké a panel Detail zabíral 330 px, většinou prázdných. Zúženo:
`main` má 10 px po stranách místo 20, panel 248 px, štítek vrstvy v pásech
84 px místo 96. Do pásu se tím vejde šest karet místo pěti.

Zároveň se zvětšil **krok odsazení ve stromu** na 24+18 px. To jsou dvě věci,
které se snadno pletou a v tomhle projektu se popletly: kde strom **začíná**
(řeší okraj `main`) a jak velký je **krok mezi úrovněmi**. Ve třetím kole se
zmenšilo obojí naráz, ačkoli vadilo jen to první.

### Šesté kolo (20:11) — nová paleta, odstín místo sytosti

Monochromatická modrá řada z prvního kola **neobstála v provozu**: „je potřeba
použít odlišnější barvy, tohle moc splývá." Čtyři stupně sytosti téže modré
jsou na papíře elegantní, ale nad dlouhými názvy a přes čtyři úrovně se rozdíl
mezi sousedními stupni ztratí. Uživatel dodal paletu z Adobe Color:

```
#1C0F99  #17885A  #545715  #A17863  #22B7F4
```

Sedla bez úprav v jedné podstatné věci: `#1C0F99` je prakticky ta modrá, která
na stránce už byla (navbar), takže nevznikly dvě nesouvisející rodiny —
podmínka, kvůli které se 24.08.2026 musela vyhodit paleta šalvějová a krémová.

Rozdělení podle role a spočítané kontrasty:

| vrstva | linka a kolečko | text / hlavička | plocha |
|---|---|---|---|
| agenda | `#1C0F99` | `#1C0F99` (13,31:1) | `#d6d4ed` |
| proces | `#17885A` | `#13704a` (6,10:1) | `#d5eae1` |
| dílčí proces | `#545715` | `#545715` (7,63:1) | `#e0e1d5` |
| aktivita | `#A17863` | `#745647` (6,64:1) | `#eee7e3` |

Zelená má na bílé jen **4,46:1** a terakota **3,90:1**, takže pro bílý text na
nich musely vzniknout ztmavené varianty; plné barvy zůstaly tam, kde nic nenese
text (linky, kolečka). `#22B7F4` je na plochu i na text moc světlá (2,30:1) —
slouží jako akcent vybrané karty, jediné místo bez textu. Sekundární barva textu
se ztmavila na `#4a5266`. Nejtěsnější dvojice text/podklad je 4,84:1.

Krok odsazení ve stromu je 32+22 px.

**Poučení zapsané do skillu** `harmonicke-barvy` (commit `d331925`): pravidlo
„hierarchii dělá sytost, ne odstín" platí na dvě úrovně, ne na čtyři. Při
čtyřech se sousední stupně téže barvy přestanou lišit dřív, než dojde barva.
Druhý zápis tamtéž: sytá barva z palety zpravidla neunese bílý text.

### Sedmé kolo (20:20) — druhá paleta z Adobe Color

Uživatel dodal jinou paletu: `#5C75F2 #4AD1B2 #4F5BBD #EA9B0B #8A153E`.
Postup byl týž jako u předchozí, jen s jinými čísly:

| vrstva | linka | text / hlavička / kolečko | plocha | pruh |
|---|---|---|---|---|
| agenda | `#4F5BBD` | `#4F5BBD` (5,89:1) | `#dfe1f3` | `#f3f4fa` |
| proces | `#4AD1B2` | `#2b7967` (5,21:1) | `#def7f1` | `#f2fcfa` |
| dílčí proces | `#EA9B0B` | `#885a06` (5,98:1) | `#fbedd3` | `#fef8ee` |
| aktivita | `#8A153E` | `#8A153E` (9,30:1) | `#ead5dc` | `#f7eff1` |

`#4F5BBD` je základ (drží kontinuitu s dosavadní modrou hlavičkou),
`#5C75F2` je mu na sousední vrstvu příliš blízká, takže z ní je **akcent**
vybrané karty. Mátová a okrová jsou světlé — na bílý text potřebovaly ztmavit
o 42 %, což je dvakrát víc než u předchozí palety.

**Změna proti minulému kolu, která nebyla vidět dopředu:** spojnice teď berou
**ztmavené** varianty, ne plné barvy linek. Plná mátová má na bílé 1,90:1
a okrová 2,28:1 — jako tenká čára s poloviční průhledností by prostě zmizely.
Průhlednost šla z 0,5 na 0,6. U předchozí palety tenhle problém nebyl, protože
všechny její barvy byly tmavé.

Nejtěsnější dvojice text/podklad: 4,55:1.

### Osmé kolo (20:27) — třetí paleta, a poprvé v plné sytosti

Paleta `#426AC9 #6E20A3 #23C3BB #4166AE #230818`, tentokrát se zadáním, které
mění princip: **plné syté barvy jako plocha a bílé písmo**, ne světlé
odvozeniny s tmavým textem. Dosavadní pravidlo skillu („syté barvy patří na
akcenty, ne na plochy, přes které se čte") tím padá — u tří ze čtyř barev to
vyjde, protože jsou dost tmavé.

| vrstva | plocha (plná sytost) | písmo | kontrast |
|---|---|---|---|
| agenda | `#4166AE` | bílé | 5,62:1 |
| proces | `#6E20A3` | bílé | 8,76:1 |
| dílčí proces | `#23C3BB` | **tmavé** | 7,25:1 (bílé by mělo 2,19:1) |
| aktivita | bez plochy, linka `#230818` | tmavé | — |

Výjimka u tyrkysu není vkus, ale měření — a **týž závěr má i Adobe**: na jeho
pruzích je popisek u `#23C3BB` tmavý, u ostatních čtyř bílý. Uživatel na to
sám upozornil („v té paletě máš naznačené jaké písmo použít"), když už byla
opravená; shoda výpočtu s tím, co nástroj sám ukazuje, je slušná kontrola.

Aktivita zůstala bez plochy: `#230818` je prakticky černá a nejnižší úroveň
nese nejdelší texty, takže by z ní plný černý pruh udělal nejtěžší prvek
stránky.

**Co plná sytost strhla s sebou** (nic z toho nebylo v zadání, všechno by bez
opravy zmizelo):
- sekundární text (kód, odznak) je na sytých plochách světlý `#e9eef8`, ne šedý;
- kolečko značky rozpadu je bílé s barevnou šipkou — tmavé by v ploše zaniklo;
- `mark` (zvýraznění hledání) dostal explicitní tmavou barvu, jinak by dědil
  bílou a byla by bílá na žluté;
- nezmapovaná položka se drží šedé `--muted`, která na sytých plochách nemá
  kontrast — na nich přebírá světlou/tmavou barvu své vrstvy.

### Deváté kolo (20:36) — čtvrtá paleta a přeuspořádaný přepínač

Paleta `#86A2E3 #52729E #332F74 #60ACEF #5B5290`, opět v plné sytosti. Tahle
se od předchozích liší tím, že **se sama odstupňuje**: seřazená podle relativní
luminance dá `0,040 → 0,103 → 0,163 → 0,365`, což je přesně čtyřstupňová řada
od agendy po aktivitu. Vrstvy tedy rozlišuje odstín i světlost zároveň.

| vrstva | plocha | písmo | kontrast |
|---|---|---|---|
| agenda | `#332F74` | bílé | 11,67:1 |
| proces | `#5B5290` | bílé | 6,88:1 |
| dílčí proces | `#52729E` | bílé | 4,93:1 |
| aktivita | `#86A2E3` | tmavé | 6,27:1 |

Rozdělení bílá/tmavá zase sedlo s tím, co Adobe ukazuje na svých pruzích.
U `#52729E` je bílá těsná (4,93), takže **i sekundární text je čistě bílý** —
odlišuje ho velikost, ne barva; na světlejší šedou tam kontrast nezbývá.
`--k` je ztmavená varianta `#86A2E3` pro hlavičku sloupce, kolečko a spojnice,
kde je potřeba bílý text a viditelná tenká čára.

**Aktivita dostala plochu poprvé** — u minulé palety to nešlo, protože
`#230818` je prakticky černá. Vyžádalo si to pravidlo, které dosud neexistovalo
(`.lvl-k>.row{background:…}`): dokud byla `--k-bg` průhledná, nebylo co nastavit,
takže samotná změna proměnné se v řádkovém zobrazení neprojevila.

Přepínač je přeuspořádaný podle zadání na `Rozklad vodorovně │ Rozklad svisle │
Řádkové zobrazení`. **Vodorovný rozklad je tím i výchozím zobrazením** — první
tlačítko nese `aria-pressed`, a nechat aktivní jiné než první by vypadalo jako
chyba.

### Desáté kolo (20:41) — rozklady zůstávají syté, řádkové zobrazení světlé

Uživatel oba rozklady schválil („ty rozklady jsou super") a zadal, že **řádkové
zobrazení má být světlé a všude s černým písmem**. Plná sytost, která na kartách
rozkladu funguje, dělá z řádku úzký barevný pruh přes celou šířku stránky —
a takových pruhů jsou ve stromu stovky pod sebou.

Zobrazení proto mají oddělené sady ploch: `--a-bg…--k-bg` drží plnou sytost pro
oba rozklady, nová `--a-row…--k-row` je táž řada naředěná bílou (76 %) jen pro
řádkové zobrazení:

```
agenda #cecdde   proces #d8d5e4   dílčí proces #d5dde8   aktivita #e2e9f8
```

Černý text má na nich 10,1 až 13,0:1. Odpadly tím všechny výjimky, které si
syté plochy ve stromu vynutily (světlé chipy, obrácený trojúhelník, přebarvená
nezmapovaná položka) — na světlém podkladu platí zase jedno pravidlo pro celý
strom.

**Co ověřené není:** chování spojnic při rolování pásů do velké vzdálenosti
(ořez je otestovaný jen strukturálně) a vzhled při největší velikosti písma.

## 07.09.2026 — F20/model: rozklad ukazuje všechny větve, ne jednu cestu

Rozhodl uživatel. Původní chování (Power BI decomposition tree: sloupec N+1 =
potomci **vybrané** položky) neodpovídalo tomu, co od tlačítka „Rozbalit"
čekal — zvolil „vše až po aktivity" a viděl pořád jen jednu cestu.

**Nový model:** sloupec ukazuje potomky **všech** položek vlevo. Bez výběru
tedy sloupec procesů nese všech 46 procesů a sloupec dílčích procesů všech
250. **Výběr slouží k zúžení**, ne k navigaci: klik na agendu `01` omezí
sloupec procesů na jejích 10 a dílčí procesy na 41 pod nimi. Klik na už
vybranou kartu výběr zruší a rozsah se zase rozšíří.

Spojnice vedou od **každé** karty k jejím dětem, ne jen od vybrané — teprve
tím vznikne stromový rozklad z předlohy.

**Aktivita může patřit do víc dílčích procesů (M:N), takže se ve sloupci
objeví víckrát** — jednou pod každým rodičem. Karty proto nejdou párovat podle
kódu a spojnice se drží indexu rodiče (`data-rodic`).

### Dvě chyby při přepisu a jedna poučná oprava testu

1. **`rzCesta.length = i` natáhlo pole podruhé**, tentokrát v obsluze kliku.
   Zkracování teď vede přes `rzZkrat()`, které navíc uklidí koncové díry,
   takže platí invariant „poslední index vždy existuje".
2. **Hláška „Tady rejstřík končí" u prázdného filtru** — prázdno kvůli filtru
   není totéž co konec větve; rozlišuje se podle toho, jestli něco prošlo.
3. **Test musel změnit kritérium.** Kontrola „cesta nemá díry" v novém modelu
   neplatí: vybrat proces bez vybrané agendy je platný stav, protože sloupec
   procesů ukazuje procesy všech agend. Řídké pole je tedy v pořádku — vadná
   je jen díra na **posledním** indexu, což je přesně otisk omylem nataženého
   pole.

Mutačně ověřeno 4/4: sloupec jen z vybraného, výběr bez zúžení, karta bez
rodiče, `rzZkrat` bez úklidu — každá mutace test shodí. Celkem 23 kontrol.

## 07.09.2026 — F20/oprava: rozklad byl po otevření prázdný

Uživatel poslal snímek se třemi prázdnými sloupci a hláškou „Tady rejstřík
končí — níž už nic není." Dvě chyby najednou, obě moje:

**1. `rzCesta.length = i` na kratším poli ho NATÁHNE.** Při prázdné cestě
a `i = 1` vznikne řídké pole délky 1, sloupec pak tvrdí, že výběr existuje,
a místo „Vyber položku vlevo" hlásí konec rejstříku. Podmínka je teď
`if (!vybrany && rzCesta.length > i)`.

**2. Prázdný diagram po otevření.** I s opravenou hláškou byly tři sloupce ze
čtyř prázdné. Při prvním zobrazení se proto předvybere první větev; jakmile
uživatel klikne, řídí výběr on.

Zároveň podle připomínek: spojnice měly barvu `--line` (světle šedá na bílém,
prakticky neviditelná) — berou teď **barvu cílové vrstvy**, tah 2,5 px; karty
mají mezeru 16 px místo 7; volba „Rozbalit" se v rozkladu vrátila a určuje,
**kolik sloupců je vidět** (skrývá se s nimi i hlavička).

### Nový test `src/test_rozklad.js` — a proč byl zprvu slepý

Brána `check_mapa_html.py` kontroluje strukturu, ne chování, takže tuhle chybu
chytit nemohla. Přibyl test, který spouští **skutečnou** `renderRozklad()`
z hotové stránky nad minimálním DOM stubem (12 kontrol).

Poučné je, že první verze testu původní chybu **nechytila**:
`rzCesta.length = 3` na prázdném poli vyrobí **řídké pole s dírami**
a `Array.every()` díry **přeskakuje** — nad `[ , , ]` vrátí `true`. Kontrola
tedy prošla nad polem, které JSON vypíše jako `[null,null,null]`. Léčba je
spread (`[...pole].every(...)`), který díry rozbalí na `undefined`.

Mutačně ověřeno 4/4: původní bug se zkracováním, odebraný předvýběr,
ignorovaná volba úrovně, sloupec bez filtru — každá mutace test shodí.

## 07.09.2026 — F20: mapa má druhé zobrazení, rozkladový diagram

Zadal uživatel s předlohami (Power BI decomposition tree, stromový diagram).
Rozhodl **přepínač v existující mapě** místo druhého souboru a **rozbalování
jedné cesty** místo celého stromu — při 250 dílčích procesech by stránka
vykreslená naráz měla přes 10 000 px.

Nahoře v liště je `Strom | Rozklad`. Rozklad má čtyři sloupce
(Agenda → Proces → Dílčí proces → Aktivita); sloupec N+1 ukazuje děti uzlu
vybraného ve sloupci N, spojnice jsou SVG křivky od vybraného uzlu k jeho
dětem. Klik na aktivitu otevře týž detail jako ve stromu.

**Filtry jsou společné, a to je na tom to podstatné.** Filtrování bylo dosud
zapletené do stavby DOM ve funkci `mk()`; vznikla z něj samostatná `filtruj()`,
kterou volají obě zobrazení. Kdyby každé filtrovalo po svém, ukázala by dvě
zobrazení téhož rejstříku jiná čísla — a to je přesně ten druh chyby, které si
nikdo nevšimne. Brána to hlídá: ověřuje, že `filtruj` existuje **jednou** a že
ji volá `render()` i `renderRozklad()`.

Volba hloubky (`Rozbalit:`) se v rozkladu schová — tam hloubku řídí klikání.

**Ověřeno bez prohlížeče** (rozšíření Chrome nebylo připojené):
- datová vrstva v Node nad hotovou stránkou — průchod první větví dá
  `7 → 10 → 4 → 2` uzlů a cestu `01 / 01-01 / 01-01-001 / 01-01-001-0001`,
  celkem 7/46/250/46 uzlů, filtr vrací podmnožinu (hledání „rozpočt" → 2/3/6/1);
- brána `check_mapa_html.py`: 37 kontrol (dřív 31), 0 chyb;
- mutačně 4/4: odebraný přepínač, odebraný kontejner sloupců, rozklad
  obcházející `filtruj`, chybějící hlavičky — každá mutace shodí bránu, a to
  z vlastního důvodu, ne na kontrole čerstvosti stránky.

**Co ověřené není:** jak to vypadá a jestli spojnice sedí při scrollu a změně
velikosti písma. To umí posoudit jen oko v prohlížeči.

## 07.09.2026 odpoledne — balík 1.0.0.101: ImportFlow šlo zase zapnout

**Příznak:** po importu balíku 100 nešlo `ImportFlow` zapnout:

```
Flow save failed with code 'InvalidTemplate' … The circular dependency
detected in template language expressions
```

Hláška nejmenuje flow ani akci. Poznávacím znamením byl **graf rozpadlý na dva
kusy** — pravá část v designeru nevisela na triggeru (všiml si uživatel).

**Příčina: kolize jmen akcí.** F16/2 generuje pro každou úroveň vlastníků
šestici akcí, mezi nimi `Kody_{úroveň}`. Pro úroveň `dilcich` z toho vyšlo
`Kody_dilcich` — jméno, které od F1 patří **validační** akci (seznam
existujících dílčích procesů z listu, čte `Nacti_DilciProcesy`). Python slovník
starou akci tiše přepsal:

| balík | `Kody_dilcich` čte | runAfter |
|---|---|---|
| 97 (šel zapnout) | `Nacti_DilciProcesy` | `Nacti_Aktivity` |
| 100 (nešel) | `Unikatni_dilcich` | `Unikatni_dilcich` |

Tím se `runAfter` uzavřel do kruhu přes 28 akcí: `Kody_dilcich` po
`Unikatni_dilcich` po … po `Nezarazene` po … po `Klice_aktivit` po
`Kody_dilcich`. Balík 97 cyklus neměl žádný.

Druhá, tišší část škody: `Zarazene` a `Neznamy_dilci` čtou `body('Kody_dilcich')`
v původním významu (existující kódy z listu), ale dostaly by kódy ze sešitu.
I kdyby cyklus nebyl, flow by třídilo řádky podle špatného seznamu.

**Oprava trojí:**
1. akce se jmenuje `Kody_vlastniku_{úroveň}` — `Kody_dilcich` je zase validační;
2. `build_import_flow.py` staví akce do slovníku `Kroky`, který **přepsání
   jména odmítne** místo aby ho tiše provedl;
3. `check_solution.py` má bránu `bez_cyklu_runafter` nad **všemi** flow v balíku
   — ta chytí zacyklení bez ohledu na to, čím vzniklo.

**Doloženo zpětně na skutečně vadném balíku**, ne jen zelenou bránou: nad
balíkem 100 brána nález vypíše i s celým řetězem, nad balíkem 97 mlčí.

Brány balíku 101: `check_solution` 688 kontrol / 0 chyb, `check_import_flow`
243 kontrol, `check_app --solution` čistý.

**Poznámka k radě z „Assist me"**, kterou vrátil designer: mluvila o chybějících
povinných údajích v řádcích (`Popis_chybne`, `Chybne`). Byla mimo — flow se
nespustilo, takže žádný řádek nikdo nečetl. Šlo o vadu definice, ne dat.

## 07.09.2026 — F19: `deploy/` obsahuje jen hotové sady

Zadal uživatel. Kořen `deploy/` míchal tři různé věci a všechny vypadaly jako
„výstup k nasazení": ručně psanou dokumentaci, generované mezistupně a pět
solution balíků. Přitom **dvě z nich byly vstupem** obou generátorů sad, takže
je nešlo jen smazat.

| co | kam | proč |
|---|---|---|
| 7× `flow_*.md`, `navod_*.md`, `TESTOVACI_SCENAR.md`, `app_navrh.md` | `docs/` | píše se ručně, je to zdroj |
| balík, `mapa_template.html`, `procesni_mapa.html`, `sharepoint_schema.md`, `sablona_import_aktivit.xlsx` | `runs/build/` | vyrábí je build skripty |
| balíky 96–99 | smazány | jsou v git historii, dají se odtud vytáhnout |

`deploy/` = `ppf/` + `mpsv/`, nic jiného.

**Přepsáno devět skriptů:** `build_app.py`, `build_mapa.py`, `check_mapa_html.py`,
`check_schema.py`, `check_solution.py`, `make_sablona.py`, `make_deploy_mpsv.py`,
`make_deploy_ppf.py` (+ docstringy). V generátorech vznikly konstanty
`DOKUMENTACE = docs/` a `BALIKY = runs/build/`, takže se cesty neopakují.

**Past, do které jsem sám spadl:** `sharepoint_schema.md` vypadá jako
dokumentace, ale generuje ho `check_schema.py` — patří do `runs/build/`, ne do
`docs/`. Nejdřív jsem ho kopíroval ze špatného místa; chytila to až kontrola
proti baseline.

**Jak je doloženo, že reorganizace nic nerozbila:** před prvním zásahem otisk
(`sha256`) všech 38 souborů obou sad, po dokončení přegenerování a porovnání.
**37 z 38 sedí bit po bitu.** Jediný rozdíl je `deploy/mpsv/README.md`, kde se
změnila jedna cesta v návodu na build (`deploy/procesnimapa_<verze>.zip` →
`runs/build/…`) — tedy přesně ta změna, která je smyslem F19, ne vedlejší účinek.

Brány po reorganizaci: `check_schema`, `check_mapa_html`, `check_app`,
`check_app --solution`, `check_setup.js`, `check_import.js` — všechny zelené.

`CLAUDE.md` má novou strukturu i příkazy na oba generátory. `HANDOVER.md` má
srovnané cesty a **nově nahoře upozornění, že jeho popis stavu je z 24.08. a
neplatí** (mluvil o balíku 55) — cesty by jinak seděly a stav lhal, což je
horší než zjevně starý dokument.

## 07.09.2026 — F18: nasazovací sada pro PPF se generuje (`deploy/ppf/`)

**`deploy/INSTALACE.md` zanikla.** Byla to jediná ručně udržovaná část nasazení
a zaostala o třináct verzí — v nadpisu balík 87, čtyři obrazovky místo šesti,
šest flow místo devíti, `PresunFlow` nikde. Nikdo si toho nevšiml, protože
návod vypadá pořád stejně; `deploy/mpsv/` tím netrpí, protože se generuje.

Nově tedy **dvě zrcadlové sady**, obě generované:

| sada | skript | data | čím se liší |
|---|---|---|---|
| `deploy/ppf/` | `src/make_deploy_ppf.py` | `runs/anonym` | 7 kroků, anonymizovaná data |
| `deploy/mpsv/` | `src/make_deploy_mpsv.py` | `runs/normalize` | 8 kroků, ostrá data |

Text návodu pro PPF drží šablona `src/sablona_instalace_ppf.md`; čísla (verze
balíku, počet flow, obrazovek, proměnných, listů) i obě tabulky se vyplňují
**z balíku a ze schématu**, ne z paměti. Sdílený kód (`posledni_balik`,
`overuj_bez_guidu`, `FLOW`, `VYPIS_GUIDU`) se importuje z generátoru pro MPSV,
takže popis flow existuje na jednom místě.

**Brána v generátoru** hlídá, že README sedí na balík, se kterým se předává:
nevyplněná kotva, chybějící flow v tabulce, flow bez popisu ve `FLOW` a
neshoda počtu flow shodí build. Počet se čte **z balíku**, ne ze slovníku
`FLOW` — jinak by brána ověřovala generátor sama sebou.

Mutačně doloženo (4/4): ubylo flow v balíku → „README nežádá zapnutí osm flow";
flow bez popisu → jmenuje ho; neznámá kotva v šabloně → jmenuje ji; README
z jiného balíku → „README neuvádí balík …". Nezměněný vstup projde.

Historické zmínky `INSTALACE.md` v `PLAN.md` a starších zápisech `STATUS.md`
zůstávají — popisují stav v dané době, přepisovat je by falšovalo záznam.

## 07.09.2026 ráno — O33 zařazen, audit kola 8 vyřízen

**`O33` patří pod `Sekce 3`.** V exportu z MPSV je nadřízený sám sobě, takže
odbor zůstával bez rodiče a mimo strom. `src/import_utvary.py` ho zařazuje
natvrdo jedním řádkem hned za načtením nadřízeného (uživatel 07.09.2026:
žádná mechanika výjimek); zdrojový sešit se needituje. **Chyba je ale
v produkčním listu *Organizační útvary* na MPSV** — dokud se neopraví tam,
bude každý další export vadný stejně.

Přegenerováno: `runs/normalize/utvary.csv` (44 útvarů, `33;O33;odbor;3`),
`runs/anonym`, `src/import_data.js`. V anonymizovaných datech se útvar posunul
z `95` (bez rodiče) na `922` pod `92` — přímý dopad zařazení, ne chyba
anonymizace. Brány: `check_schema` OK, `check_setup.js` a `check_import.js`
smoke OK.

### Audit kola 8 — P-01 zamítnuto, P-02 opraveno

Auditor označil za blokující, že `Controls/*.json` v balíku 100 odpovídají
appce 1.0.0.93. **Zamítnuto s důkazem:** u YAML-first balíku (`packed.json`
→ `LoadFromYaml: true`) zaostávají `Controls` o generaci vždycky a nesou verzi
*předchozího* balíku — balík 93 měl v `Controls` 1.0.0.85, balík 95 měl
1.0.0.93. Ta hodnota mohla vzniknout jedině tím, že Studio načetlo balík 93
**z YAML**. Kdyby četlo `Controls`, dostal by uživatel z balíku 93 appku 85.
`pac canvas pack` `Controls/*.json` negeneruje, jen přenáší. Rozlišení
YAML-first balíku od exportu ze Studia je doplněné do skillu `power-Apps-skill`,
protože právě vytržené pravidlo ten falešný nález vyrobilo.

**P-02 opraveno:** `src/check_app.py` neměl `argparse` a `--solution <zip>`
tiše ignoroval — čtyři kola auditu tak tím přepínačem „ověřovala balík"
a přitom četla repo. Teď skutečně vytáhne `Src/*.pa.yaml` z `.msapp` a
kontroluje je (balík 100: 7 YAML, 6 obrazovek, 287 prvků, 3206 vzorců, 0 chyb).
Mutačně doloženo: smazaná obrazovka i podvržený sloupec v balíku dají exit 1,
nezměněný balík exit 0.

**Balík 1.0.0.100 je tím bez otevřeného blokujícího nálezu a připravený
k testu na PPF DEV.** Číselník útvarů se ale změnil až teď, takže se přenáší
znovu (`src/import_data.js`).

## 06.09.2026 večer — číselník útvarů, pruh voleb, tlačítko Přesun

### F16/1 — víc vlastníků v aplikaci

`vlastnik` u agendy, procesu i dílčího procesu byl jeden útvar z rozbalovátka.
Data přitom víc vlastníků už nesla (`procesy.vlastnik` = `11; 33`) a nová
evidenční karta s tím počítá taky.

**Oddělovač `; ` je už v datech zavedený**, takže sloupec zůstal `Text`
a migrace dat odpadla — u schváleného rejstříku podstatné.

V formuláři je teď trojice na jednom řádku, bez přeskládání zbytku:

```
[ nabídka útvarů ▾ ][ + ][ 11; 33            ]
      260 px         40        260 px
```

Zdrojem pravdy je **textové pole**, rozbalovátko je jen pomůcka pro přidání.
Důvod: jinak by nešel zapsat útvar, který v číselníku ještě není — a to se
u rozpracované evidence stává. Tlačítko `+` odmítne přidat útvar, který
v seznamu už je. Před zápisem se seznam srovná (prázdné úseky pryč, jednotný
oddělovač `; `), takže jeden vlastník nikdy nedostane středník navíc.

Popisek pole už neslibuje „prázdné = ponechat stávajícího" — seznam je zdroj
pravdy, takže prázdný seznam znamená žádný vlastník. Tooltip řádku dohledává
název ke **každému** kódu zvlášť; `LookUp` na celý řetězec by u `11; 33`
nenašel nic.

**Mapa zásah nepotřebuje** — vlastníka jen přenáší z dat do JSON a nikde ho
nevykresluje.

### F16/2 — import z Excelu (hotovo, čeká na balík)

Rozhodnuto 06.09.2026 (uživatel): do listu Aktivity přibyly **tři sloupce** —
`Vlastník agendy`, `Vlastník procesu`, `Vlastník dílčího procesu`. Šablona má
tedy 12 sloupců místo 9; kód rodiče si import odvodí z kódu dílčího procesu
na témž řádku (`01-01-001` → agenda `01`, proces `01-01`).

**Rozpor se hlásí, netiší.** Hodnota se opakuje u každého řádku téže agendy,
takže si dva řádky mohou odporovat. Import takový kód **nezapíše** a vypíše ho
mezi chybami — tiché „poslední vyhrává" by znamenalo, že vlastník závisí na
pořadí řádků v sešitu. Ostatní úrovně a všechny aktivity projdou normálně.

Jak se rozpor pozná bez smyček: dvojice `kód|~|vlastník` projdou `union` samy
se sebou (zahodí duplicity), takže kód, který v seznamu zbude víc než jednou,
má víc různých vlastníků. Počet výskytů se měří přes `split` obaleného kódu.

Zápis je REST **MERGE** na `vlastnik` — mění jediný sloupec, takže se nedotkne
názvu ani zařazení. Běží až **za** založením aktivit: kdyby import spadl
uprostřed, je lepší mít aktivity bez vlastníka než vlastníka bez aktivit.
Nezařazené aktivity (technický rodič `00-00-000`) jsou z toho vyloučené —
není to skutečná agenda.

`check_import_flow` **243 kontrol** (bylo 175), `mutace_import` **32/32**
(sedm nových: zápis bez MERGE, zápis rozporných dvojic, odfiltrovaný ale
nehlášený rozpor, vlastník nezařazeným, špatná délka kódu rodiče, chybějící
`union`, MERGE měnící i název). `check_sablona` 206 (bylo 185).

### F15 — skutečný číselník útvarů (kroky 1–5 hotové)

Dodaný `query.iqy.xlsx` je export z MPSV listu *Organizační útvary*
(`sites/MPSV-App-Mapovani-Procesu-OR`), 47 řádků. Nahradil zástupný číselník,
který `make_utvary.py` vyráběl z čísel v aktivitách a jehož **hierarchie byla
odvozená z délky čísla** (111 → 11 → 1). To se ukázalo jako chybné: `O11` je
pod `Sekce 3`, ne pod „sekcí 1", a `O32`/`O34`/`O35` jsou pod `Sekce 6`.

**Kód zůstal holé číslo** (`11`, `331`, `3`), označení z MPSV (`O11`, `Sekce 3`)
šlo do názvu — rozhodl uživatel, data v aktivitách ani v rejstříku se
nepřepisují. Ministr dostal kód `0`.

| co | kde |
|---|---|
| nový extraktor | `src/import_utvary.py` — čte `input/organizacni_utvary.xlsx`, píše `runs/normalize/utvary.csv` |
| `make_utvary.py` | z generátoru na **kontrolu**: každý útvar použitý v datech musí být v číselníku |
| `schema.json` | `Utvary.uroven` má navíc volbu `ministr`; popisy už netvrdí, že délka čísla určuje úroveň |
| `anonymize.py` | mapování útvarů se **odvozuje z hierarchie**, ne z ruky (bylo tam deset čísel napsaných napevno) |

**Nálezy ve zdroji — neopravené, rozhodne zadavatelka:**

| útvar | co je tam | posouzení |
|---|---|---|
| `O33` | nadřízený sám sobě | chyba; útvar bez rodiče, čeká na potvrzení |
| `O12` | odbor přímo pod ministrem | vypadá legitimně (kabinet) |
| `O401`, `O601` | oddělení přímo pod sekcí | legitimní, bez mezistupně odboru |
| `O425` | odbor pod odborem `O42` | legitimní, ale ojedinělé |
| 3 speciální | `neobsazeno`, `věcně příslušné útvary MPSV`, `podřízené služební úřady` | do útvarů nepatří — jsou to hodnoty pro `spolupracuje` |

**Dvě vady anonymizace, které odhalily až brány — obojí stojí za zapamatování:**

1. Anonymní název `Sekce 7` by spustil vlastní kontrolu anonymity, která hlídá
   vzor „sekce ‹číslice›" jako identifikující údaj. Tvar je proto
   `Utvar 7 (sekce)` — přesně jak to měl zástupný číselník a proč.
2. **Anonymní čísla se trefila do skutečných.** Odbor `O12` dostal anonymní kód
   `11`, jenže `11` je zároveň skutečný kód MPSV (`O11`) — a od sebe se to
   nedá odlišit. Pojistka v `make_import.py` sadu správně odmítla jako
   neanonymizovanou. Anonymní prostor teď začíná devítkou (`9`, `91`, `911`,
   `9211`), kterou žádný skutečný kód nemá.

Druhá vada je poučnější: mapování vypadalo správně, sada se vygenerovala bez
chyby a teprve **nezávislá pojistka** ukázala, že anonymní není. Kdyby ta
kontrola nebyla, odešla by na PPF DEV organizační struktura MPSV.

### F17 — sjednocený pruh voleb na úvodní obrazovce

`Rozbalit` (190), `Stav` (240), `HTML mapa` (110) a `Data` (100) měly každá
jinou šířku. Teď mají **240 px a krok 248**; šířku určuje `Stav`, jehož popisek
nese celý stav filtru (`Stav: schváleno · nezařazené`). Přepínač písma `Aaa`
(34/38/42 px) zůstal — velikost tam nese význam, je to náhled stupně písma.

Rozbalené panely byly navázané natvrdo na staré `X`, takže šly s tlačítky;
panely `HTML mapa` a `Data` byly navíc užší (220) než tlačítko a srovnaly se
na 240. Poslední panel končí na 1246 px.

### Přesun: ikona → tlačítko

Přesun se spouští na obrazovce **Editace** (číselník), v řádku procesu nebo
dílčího procesu. Byla to ikona `Icon.Redo` bez popisku a **nešla najít** —
uživatel ji hledal na úvodní obrazovce. Teď je to tlačítko s textem
**„Přesun"** (`btn_PresunC`, 84 px). Vlastník a štítek úklidu se v řádku
posunuly o 88 px doleva, název dostal `Tooltip` s plným zněním, protože se
o tolik zkrátil.

U agendy a aktivity se tlačítko nezobrazuje: agenda nemá kam a aktivita se
přesouvá ve svém detailu.

### Brány

`check_schema`, `check_setup.js`, `check_import.js`, `check_sablona` 185,
`check_app` (6 obrazovek), `make_utvary` (obě sady) zeleně.

`check_import.js` měl počty listů **napsané natvrdo** (`Utvary: 7`) a po změně
číselníku hlásil selhání idempotence, ačkoli import byl v pořádku. Čte je teď
z `import_data.js`. Aby prázdný výsledek neprošel všemi `every` triviálně,
přibyla kontrola, že se počty načetly ze všech listů s daty.

---

## 06.09.2026 — F14: konec GUIDu natvrdo (balík 1.0.0.98)

Zápis krátkého názvu dělal `PatchItem` s rozloženým tělem `item/<sloupec>`.
Ten si schéma těla odvozuje z konkrétního listu, takže `table` musel být GUID
natvrdo — a pro každý tenant se stavěl vlastní balík. Třikrát kvůli tomu
odešel do MPSV balík s GUIDem PPF DEV (naposledy 1.0.0.96).

**Nově je zápis `Send an HTTP request to SharePoint`:**

```
POST  _api/web/GetList('<cesta webu>/Lists/Aktivity')/items(<ID>)
      X-HTTP-Method: MERGE, IF-MATCH: *
      {"nazev_kratky": "…"}
```

Adresa se skládá z proměnné `mpsv_procesnimapaSite` a z **interního** názvu
listu — ten je na všech tenantech stejný, kdežto GUID ne. Týž tvar používají
`ImportFlow`, `PresunFlow`, `RestoreFlow` a `ZalohaFlow`. Trigger
i `Nacti_aktivitu` teď berou list z `mpsv_listAktivity`.

**Krok 1 plánu (ruční ověření akce v designeru) odpadl a je to doložené, ne
odhadnuté.** `RestoreFlow` a `PresunFlow` mají v témž balíku přesně tuhle
akci včetně `MERGE` a `IF-MATCH: *`, a na MPSV jsou zapnuté — kdyby ji tam
DLP nepouštěla, nešly by zapnout. Ruční test by ověřil totéž.

**MERGE mění jen uvedený sloupec**, takže v těle nejsou povinná pole listu.
Tím padly obě tiché chyby, mezi kterými se předtím balancovalo: bez povinných
polí nešlo flow aktivovat, ze snímku triggeru přepisovalo novější editaci.

### Brány nad 98

`check_solution` **666** (bez výjimky pro tohle flow — GUID nesmí být v žádném)
· `check_restore_flow` 571 · `check_zaloha_flow` 184 · `check_import_flow` 175
· `check_mapa_flow` 144 · `check_export_flow` 129 · `check_presun_flow` 111
· **`check_flow` 30** · `check_env`, `check_app` zeleně.
Mutačně **`mutace_kratky_nazev` 14/14** (nový soubor).

Brána vyhodnocuje REST adresu mini-interpretem, ne porovnáním textu —
interpret umí `parameters`, `split`, `skip`, `join`, takže chytí i špatně
zdvojený apostrof. Zpětně nad balíkem 97 vypíše **12 nálezů**.

`make_deploy_mpsv.py`: `overuj_list_aktivity()` (porovnávala GUID proti MPSV)
je nahrazená `overuj_bez_guidu()` — GUID nesmí být ve `Workflows/` žádný.
V balíku 98 jich je **0**.

## 05.09.2026 — cizí GUID listu Aktivity v balíku pro MPSV

Zapnutí flow na MPSV skončilo na:

```
InvalidOpenApiFlow … DynamicOperationRequestClientFailure
The dynamic operation request to API 'sharepointonline' operation 'GetTable'
failed with status code 'NotFound' … "List not found"
```

**Jiná chyba než 28.08.** Tehdy `PatchItem` postrádal celé tělo `item`; teď
konektor nenašel list, protože ve vydaném `1.0.0.96` byl v tom jediném flow
GUID PPF DEV `9dfbb5a1-…` místo MPSV `b1daaa38-…`. Ostatních osm flow bere
list z proměnných prostředí, proto se zapnula.

Příčina není v buildu balíku, ale v **nasazovací sadě**:
`make_deploy_mpsv.py` bral přes `posledni_balik()` prostě nejvyšší verzi
z `deploy/` — a ta bývá ta pro PPF DEV, protože se na ní vyvíjí. Sada pro MPSV
tak dostala balík pro cizí tenant a README u něj tvrdilo, že flow žádné GUIDy
natvrdo nemají (u tohohle jednoho to od 1.0.0.65 neplatí).

**Oprava má dvě části:**

| část | co |
|---|---|
| `deploy/procesnimapa_1_0_0_97.zip` | 96 přegenerované `build_flow.py --list-aktivity b1daaa38-…`, pak `build_app.py --bez-pac --verze 1.0.0.97` |
| `overuj_list_aktivity()` v `make_deploy_mpsv.py` | sada se nepostaví, když balík nese v `AktualizaceKratkehoNazvu` jiný GUID než MPSV; hláška rovnou vypíše oba build příkazy |

Brána ověřená mutačně: nad 96 zastaví a vypíše cizí GUID, nad 97 projde.
Ostatní brány nad 97 zelené — `check_flow` 26, `check_solution` 664,
`check_export_flow` 129, `check_import_flow` 175, `check_mapa_flow` 144,
`check_presun_flow` 111, `check_restore_flow` 571, `check_zaloha_flow` 184,
`check_env`, `check_app`. V `Workflows/` je GUID MPSV 3× a PPF ani jednou.

**GUID do proměnné přímo nejde**, `PatchItem` s rozloženým tělem
`item/<sloupec>` si schéma stahuje z konkrétního listu a runtime výraz nesnese
(to je ta chyba z 28.08.). Obchvat je zápis přes akci `Send an HTTP request to
SharePoint` (MERGE na `_api/web/lists(guid'…')/items(<ID>)`) — v URL je list
obyčejný text, takže proměnnou snese a dvoubalíkový režim odpadne.

**Rozhodnuto 05.09.2026: uděláme to, v týdnu od 08.09.** Rozepsané jako
**F14** v `PLAN.md` — pět kroků, začíná ručním ověřením akce v designeru
(skill to u `SendHTTPRequest` požaduje, než se začne generovat).

## Nasazovací sada pro MPSV — hotová (04.09.2026 15:00)

`deploy/mpsv/` je přegenerovaná z balíku **1.0.0.96** a je to kompletní sada
k nasazení do tenantu MPSV. Generuje ji `python src/make_deploy_mpsv.py`.

| část | co v ní je |
|---|---|
| `README.md` | osm kroků, každý s ověřením; tabulka devíti flow, devíti proměnných, řešení potíží |
| `01_zaloz_listy.js` | provisioning listů, sloupců a knihoven (F12 konzole) |
| `02_import_dat.js` | **ostrá** data: 7 agend, 46 procesů, 250 dílčích, 46 aktivit, 46 vazeb |
| `03_vypis_guidy.js` | nepovinná kontrola GUIDů |
| `procesnimapa_1_0_0_96.zip` | solution balík |
| `site_assets/` | `mapa_template.html`, `procesni_mapa.html`, `sablona_import_aktivit.xlsx` |
| dokumentace | `sharepoint_schema.md`, `navod_sprava.md`, `navod_publikace_mapy.md`, `TESTOVACI_SCENAR.md`, sedm kontraktů `flow_*.md` |

**README se generuje z balíku, ne z paměti** — seznam flow i počet obrazovek
čte přímo ze zipu a z `src/app_src`, takže příště nemůže tvrdit něco jiného,
než balík obsahuje. Předtím mluvilo o čtyřech flow a šesti proměnných, zatímco
balík má devět a devět.

**`navod_sprava.md` byl přepsaný na 1.0.0.96.** Byl u verze 51: neznal
nezařazené aktivity, hromadný import, zálohu, obnovu ani přesun, popisoval
chipy místo nabídky filtrů — a v „Mezích" tvrdil, že přesun se dělá ručním
založením a smazáním, což od F10/4 neplatí. Přibyly sekce **§7 Data**
a **§8 Přesun**, zbytek se přečísloval.

**Co ještě není hotové a je na cizí straně:** přístup do tenantu MPSV.
Sada je připravená, ale nasazení proběhne, až bude přístup — kroky 6 a 7
README (registrace flow ve Studiu a adresa mapy) se dělají v cílovém
prostředí a vyžadují dvě kola.

---

## Co se udělalo 04.09.2026 odpoledne — balík 1.0.0.96

**Pád ostrého běhu: `substring` přes okraj.** Kaskáda skládá nový kód jako
`novyPrefix + zbytek za přesouvaným prefixem`. Zbytek se bral
`substring(kod, length(presouvanyKod))` — jenže u **samotné přesouvané
položky** je start index roven délce řetězce a Logic Apps vyžadují index
**menší** než délka. Běh spadl na akci `Mapa` hláškou *„'start index' must be
non-negative integer and should be less than the length of the string"*.
Táž past číhala ještě na dvou místech: `dilci_proces_kod` v `Zaloz_aktivity`
(při přesunu dílčího procesu) a vazba, jejíž `dilci_proces_kod` se rovná
přesouvanému kódu.

**První oprava byla špatně a je z ní poučení.** Podmínka
`if(greater(length(...)), substring(...), '')` vypadá jako správné ošetření,
ale **Logic Apps vyhodnocují všechny argumenty `if()`**, tedy i větev, která
se nepoužije — `substring` by spadl dál. Platný tvar počítá s délkou:
`substring(concat(kod, ' '), length(presouvany), sub(length(kod),
length(presouvany)))`; mezera navíc posune horní mez, výřez nulové délky dá
prázdný řetězec. Obě varianty jsou teď v `mutace_presun.py` jako mutace,
takže se ta mylná nemůže vrátit.

**Proč to brána nechytila, ačkoli výrazy opravdu POČÍTÁ.** `check_presun_flow`
pouští výrazy mini-interpretem nad vzorovým rejstříkem — ten ale `substring`
počítal pythonovsky, kde `text[len(text):]` tiše vrátí prázdno. Interpret
(v `check_export_flow.py`, sdílený) teď u dvouargumentové varianty modeluje
i **chybu** Logic Apps. Zpětně spuštěná brána nad balíkem 95 hlásí přesně to,
co spadlo v provozu: `substring('07-08', 5) je mimo rozsah`. Trojargumentová
varianta zůstala na původní kontrole — přísnější pravidlo tam není doložené
a shodilo by výrazy, které běží.

**Pruh filtrů na přehledu.** `Stav: vše | schváleno | pracovní`, chipy
`osiřelé` a `nezařazené (N)` a přepínač `kód` byly samostatná tlačítka —
devět prvků v jednom pruhu. Teď je to nabídka **Stav: … ▾**, jejíž popisek
nese celý stav filtru (`Stav: schváleno · nezařazené`), a v ní šest voleb
včetně **zobrazit kód**. Panel se krátí, když žádná nezařazená aktivita není.
Nabídky *HTML mapa* a *Data* se posunuly doleva, aby v pruhu nezůstala díra.

### Brány na 96

`check_solution` **664** · `check_restore_flow` 571 · `check_sablona` 185 ·
`check_zaloha_flow` 184 · `check_import_flow` 175 · `check_mapa_flow` 144 ·
`check_export_flow` 129 · `check_presun_flow` 111 · `check_flow` 26 ·
`check_env`, `check_schema` zeleně · `check_app`: 6 obrazovek, 285 prvků.
Mutačně: `mutace_import` 25/25, `mutace_sablona` 19/19, `mutace_restore`
17/17, `mutace_zaloha` 16/16, **`mutace_presun` 15/15 (+2 nové)**,
`mutace_export_mapa` 7/7, `mutace_napojeni` 5/5, `mutace_parametry` 4/4,
`mutace_app` 2/2.

Sestavení:

```
copy deploy\procesnimapa_1_0_0_95.zip runs\vstup_96.zip
python src/build_presun_flow.py --solution runs/vstup_96.zip
python src/build_app.py --solution runs/vstup_96.zip --verze 1.0.0.96
```

---

## Co se udělalo 04.09.2026 — balík 1.0.0.95

**Chyba z 94: `Patch` nad zdrojem, který prochází `ForAll`.** App checker ji
hlásil jako *„This function cannot operate on the same data source that is
used in ForAll"* u `btn_Ulozit.OnSelect` na `scr_Detail`. Přišla s balíkem
**92** (přiřazení sirotka, F13/C4), ne s 93 — 92 do té doby na prostředí
neběžel, takže se ukázala až teď. Vzorec filtroval vazby sirotka a v témž
průchodu je přepisoval; Power Fx to nedovolí. Léčba: řádky se odloží do
`colVazbySirotka` a `ForAll` běží nad kolekcí, zdroj se jen zapisuje.

**Brána to nechytila, protože takovou kontrolu neměla.** Přibyla
`kontrola_zapisu_v_forall` v `check_app.py` a mutační test
`src/mutace_app.py` (2/2: `Patch` a `RemoveIf` nad procházeným zdrojem).
Mutace je tu důležitější než kontrola sama — zelená brána bez ní nedokazuje,
že hlídá to, co si myslím.

**Napojení na flow.** `btn_SpocitatP` volá `PresunFlow` v režimu `nahled`,
`btn_ModalProvestP` udělá zálohu (`ZalohaFlow`) a pak `zapis`; přechodný
popisek `lbl_CekaNaTokP` je pryč, hlavička `scr_Presun.pa.yaml` už netvrdí,
že přesun dělá appka. `varPresunVysledek` a `varPresunZapis` se v
`App.OnStart` **neinicializují** — prázdný řetězec by jim dal typ textu
a záznam z `Flow.Run()` by se do nich nevešel (stejně to má `varNahledVysledek`).

**Dvě brány byly rozbité a nikdo o tom nevěděl:**
- `check_solution` neznala `scr_Presun` — obrazovka jí vycházela jako
  „duch po zrušené obrazovce". V 93 to neprasklo, protože Controls/*.json
  pro ni ještě neexistoval; vznikl až tím, že appku uložilo Studio.
- `check_mapa_flow` měla `--base` na `input/procesnimapa_1_0_0_66.zip`,
  který úklid přesunul do `input/archiv/`.

**Build na pracovním stroji (5CG5210MB2) jde taky.** VS Code s Power Platform
Tools tu není a .NET SDK taky ne, ale `pac` z nugetu (balíček
`Microsoft.PowerApps.CLI`) běží na .NET Frameworku 4.8. Rozbalený je
v `%LOCALAPPDATA%\PowerAppsCLI` a `build_app.py` se tam teď dívá sám.
Ověřeno: `.msapp` má `DocVersion 1.349` jako vstup a `FlowNameId` všech šesti
flow zůstalo zachované.

### Brány na 95

`check_solution` **663** · `check_restore_flow` 571 · `check_zaloha_flow` 184 ·
`check_import_flow` 175 · `check_sablona` 185 · `check_mapa_flow` 144 ·
`check_export_flow` 129 · `check_presun_flow` 111 · `check_flow` 26 ·
`check_env`, `check_schema` zeleně · `check_app`: 6 obrazovek, 284 prvků.
Node: `check_setup.js`, `check_import.js` OK.
Mutačně: **`mutace_app` 2/2 (nová)**, `mutace_import` 25/25,
`mutace_sablona` 19/19, `mutace_restore` 17/17, `mutace_zaloha` 16/16,
`mutace_presun` 13/13, `mutace_export_mapa` 7/7, `mutace_napojeni` 5/5,
`mutace_parametry` 4/4.

Sestavení:

```
python src/build_app.py --solution input/procesnimapa_1_0_0_94.zip --verze 1.0.0.95
```

---

## Co se udělalo 03.09.2026 večer — balík 1.0.0.93 (F10/4)

**Přesun dělá flow, ne appka.** Původní plán počítal s Power Fx kaskádou
v appce a byla už napsaná; po tvé nabídce udělat kolo se Studiem jsem ji
zahodil a přepsal na `PresunFlow`. Důvody, které rozhodly:

- kaskáda je ~240 zápisů; v appce běží v prohlížeči a zavření okna nebo
  výpadek sítě uprostřed nechá rejstřík rozpůlený, kdežto `Foreach`
  v Logic Apps doběhne na serveru,
- když to spadne, je vidět **na které akci** — appka řekne jen `FirstError`,
- protokol o přesunu, který metodika vyžaduje, umí flow uložit jako soubor.

**Jeden můj argument pro flow ale neplatil** a je fér to říct: sliboval jsem
`$batch` po stovkách místo jednotlivých volání. Projekt `$batch` **vědomě
nepoužívá** — `RestoreFlow` u toho má poznámku, že multipart changeset se
v Logic Apps skládá ručně a chyba se pozná až za běhu. `PresunFlow` proto
zapisuje po jednom stejně jako obnova; `Foreach` běží paralelně, takže je to
otázka sekund.

**Pravidlo přečíslování.** Přečísluje se jen přesouvaná úroveň; potomci dědí
nový prefix a nechají si pořadové číslo (`07-08-001-0006` → `03-05-001-0006`).
Volná čísla pro potomky se pod novým rodičem hledat nemusí — číslují se v jeho
rámci a ten je nový. Celá kaskáda je tím jediná náhrada prefixu a vejde se do
jednoho výrazu platného pro všechny tři úrovně.

**Nové číslo přes živý list I historii** — tady se poprvé uplatnilo pravidlo
F10/1 a je to hlavní věc, kterou brána hlídá: vzorový rejstřík má v agendě 03
živé procesy do `03-04` a v historii uzavřený `03-05`, takže správná odpověď
je `03-06`. Kdyby se historie nezapočítala, vyjde `03-05` — recyklovaný kód.

**Pořadí zápisu je závazné:** vznik → historie → zánik. V opačném pořadí by
výpadek uprostřed smazal větev, která ještě nikde jinde neexistuje. Takhle je
nejhorší možný výsledek duplicita, ne ztráta.

**Obrazovka `scr_Presun`** má tvar `scr_Nahled` (vyber → spočítej nanečisto →
podívej se → teprve pak zapiš): co se stěhuje, kam, povinný důvod, tabulka
starý → nový kód přes celý podstrom, souhrn, potvrzovací modál. Vstup je
ikona v řádku číselníku u procesu a dílčího procesu.

### Co brána chytila dřív, než to stihlo uškodit

- **`select()` a `filter()` jsou v Logic Apps AKCE, ne funkce výrazu.**
  Použil jsem je ve výrazu `Prehled` a ve `foreach` — za běhu by to spadlo.
  Nahrazeno samostatnými kroky `Prehled_radky` a `Mapa_dilci`.
- **Dvě mutace prošly a odhalily slabinu testu, ne kódu.** Uzavřený dílčí
  proces ve vzorku měl nízké poslední číslo, takže chybějící filtr na úroveň
  nebyl na výsledku vidět — vzorek dostal `03-05-099`. A mutace „děti přes
  prefix" byla neškodná (nad reálnými kódy dává `startsWith` totéž co
  `equals`), nahrazena mutací „děti se nefiltrují vůbec".
- **Brána `check_solution` brala zmínku o `.Run()` v komentáři jako volání.**
  Teď komentáře odstraňuje; ověřeno, že skutečné volání dál chytá.

### Auditní nález P-05 z balíku 92 — opraveno

Fulltextové hledání na přehledu technickou větev nefiltrovalo, a protože se ty
položky jmenují doslova „Nezařazeno", hledání toho slova je vracelo jako běžné
položky — a přes `gal_Strom.AllItems` i do exportu. Hledací větev dostala týž
filtr jako stromová. Brána `kontrola_nezarazenych` teď kontroluje **každou
větev `If` zvlášť**, ne text vlastnosti jako celek; ověřeno i opačně, že do
větve nezařazených ten filtr patřit nesmí (vyhodil by sirotky).

### Brány na 93

`check_solution` **663** (bylo 582) · `check_restore_flow` 571 ·
`check_zaloha_flow` 184 · `check_import_flow` 175 · `check_sablona` 185 ·
`check_mapa_flow` 144 · `check_export_flow` 129 · **`check_presun_flow` 111
(nová)** · `check_flow`, `check_env`, `check_schema` zeleně.
`check_app`: **6 obrazovek, 285 prvků**.
Mutačně: **`mutace_presun` 13/13 (nová)**, `mutace_import` 25/25,
`mutace_restore` 17/17, `mutace_zaloha` 16/16, `mutace_export_mapa` 7/7,
`mutace_parametry` 4/4, `mutace_napojeni` 5/5.

Sestavení:

```
copy deploy\procesnimapa_1_0_0_92.zip runs\vstup_93.zip
python src/build_presun_flow.py --solution runs/vstup_93.zip
python src/build_app.py --solution runs/vstup_93.zip --verze 1.0.0.93
```

Balík 93 **nemění MapaPublishFlow**, takže dvojče se přegenerovávat nemusí.

---

Předchozí stav (balík 1.0.0.92):
**F13 je celá hotová kromě B3** — sirotčí aktivity jdou po importu najít
(chip na přehledu) i přiřadit ke skutečnému dílčímu procesu (detail aktivity).
Technická větev „Nezařazeno" zmizela odevšad, kde se tvářila jako běžná
agenda. Stroj HP-LUBOS. Vše v gitu, poslední commit viz `git log -1`.

## KDE SE ZÍTRA ZAČÍNÁ

**Nic nevisí a nic není rozbité.** Balík 92 je postavený a všechny brány jsou
zelené; na prostředí zatím neběžel — to je první krok zítřka.

1. **Odzkoušet 92 na PPF DEV** (postup níž v „Zkušební seznam k balíku 92").
   Import → otevřít ve Studiu → mikro-změna, Save, Publish.
2. **F10 krok 2** — přesun aktivity mezi dílčími procesy jako zánik + vznik.
   Zámek kaskády, který přinesl balík 92, je do té doby jediná obrana proti
   tiché variantě A; F10/2 ho vymění za potvrzovací modál a zápis do historie.
3. **F10 krok 3** — přidělování kódů respektuje `HistorieKodu`. Souvisí:
   C4 dnes bere maximum jen z živého listu (viz nedodělek níž).
4. **F10 kaskáda — přesun procesu pod jinou agendu.** Největší kus: mění se
   prefix všem potomkům, takže přesun procesu s 8 dílčími procesy a 40
   aktivitami uzavře 49 kódů a založí 49 nových, plus protokol.
5. **F13/B3** — noční refresh číselníků v šabloně; čeká na rozhodnutí mezi
   dvěma cestami (viz `PLAN.md` u kroku B3).

**Proč tohle pořadí:** C4 se právě postavilo jako nejmenší instance přesunu
(nový kód pod novým rodičem, přepis vazeb, `puvodni_kod`). F10/2 z něj vychází
a přidává to, co u sirotka schválně chybí — uzavření starého kódu v historii.

## Ještě otevřené z dřívějška

1. **Nahraj do Site Assets novou šablonu** `deploy/sablona_import_aktivit.xlsx`.
   Ta v prostředí je ještě bez varování o citlivostním štítku a bez rozbalovátek.

2. **Zkušební seznam k balíku 92** (níž) — balík 93 ho obsahuje celý, takže
   se dá projít rovnou na něm.

## Co se udělalo 03.09.2026 — balík 1.0.0.92 (F13/C3 + C4)

**C3 — sirotci jsou vidět.** Pruh filtrů má nový chip „nezařazené (N)"; strom
se po něm přepne na plochý seznam aktivit s rodičem `00-00-000`. Číslo se
počítá z `colAkt`, ne z `colStrom` — ten nese i vedlejší vazby, takže by chip
ukazoval počet zařazení místo počtu aktivit a nesouhlasil by s kartou AKTIVITY.
Chip zůstane vidět i s nulou, dokud je režim zapnutý; jinak by po přiřazení
posledního sirotka zmizel a strom by zůstal prázdný bez cesty zpátky.

**Dotažen edge case z C1.** Technická větev `00 Nezařazeno` se do dneška
tvářila jako běžná agenda. Teď je skrytá ve stromu, v kartách nahoře, ve
správě číselníku, v nabídce nadřazené položky **a v publikované HTML mapě**
(`$filter` u všech pěti `GetItems` v `MapaPublishFlow`). Export z appky se
vyřešil sám — bere to, co je právě vidět ve stromu. Sirotčí aktivity ale
v číselníku vidět zůstávají, jinak by se nedaly otevřít a přiřadit.

**C4 — přiřazení sirotka.** Aktivita s rodičem `00-00-000` má kaskádu
odemčenou a při uložení dostane platný kód pod vybraným dílčím procesem,
`puvodni_kod` si nese ten sirotčí a do `HistorieKodu` se nezapisuje (kód
`00-00-000-XXXX` platným kódem nikdy nebyl). Vazby se nejdřív všechny
přepíšou na nový kód, teprve pak běží stávající blok srovnávající primární
zařazení — v opačném pořadí by se mazalo podle kódu, který v tabulce ještě
není. Uložení sirotka beze změny dílčího procesu kód nepřečísluje.

**Zámek kaskády u aktivit s platným kódem.** Zamčená je celá trojice
agenda → proces → dílčí proces, ne jen poslední pole: se zamčeným jen dílčím
procesem by změna agendy vynulovala výběr níž a aktivita by pak nešla uložit
vůbec. Do F10/2 je to jediná obrana proti tiché variantě A (kód zůstane,
prefix začne lhát).

**Vedlejší nález — panely nabídek.** Pruh filtrů byl plný na pixel, takže se
popisek počtu řádků přestěhoval do hlavičky stromu (kam patří) a tlačítka
nabídek se posunula doprava. Tím na sebe panely obou nabídek geometricky
vlezly. Za běhu se vylučují, protože každé tlačítko ostatní zavírá — jenže to
nic nehlídalo. Nová kontrola `vylucne_nabidky` tu invariantu ověřuje: stačí
v jednom `OnSelect` zapomenout `Set(varMenu…, false)` a brána spadne.

### Nedodělek, vědomý

Přidělení kódu při přiřazení sirotka bere maximum **jen z živého listu
`Aktivity`**, ne z `HistorieKodu` (pravidlo F10/1). Historie je zatím prázdná
a appka ji nemá připojenou jako datový zdroj, takže by to znamenalo druhé kolo
se Studiem za nic. Doplní se v **F10 kroku 3** na všech pěti přidělovacích
místech naráz.

### Zkušební seznam k balíku 92

| # | co udělat | očekávaný výsledek |
|---|---|---|
| 1 | import 92 jako upgrade, otevřít ve Studiu | otevře se bez „Error opening file" |
| 2 | mikro-změna, Save, Publish | tooltip názvu appky ukáže `1.0.0.92` |
| 3 | přehled — karty nahoře | AGENDY o jednu míň než dřív (technická `00` se nepočítá) |
| 4 | přehled — strom | větev `00 Nezařazeno` v něm není |
| 5 | naimportovat sešit s holou aktivitou | chip „nezařazené (1)" se rozsvítí |
| 6 | kliknout na chip | plochý seznam, v hlavičce stromu „1 nezařazených · plochý seznam" |
| 7 | otevřít sirotka, vybrat agendu → proces → dílčí proces | pole jsou odemčená |
| 8 | uložit | hláška „Uloženo jako AA-BB-CCC-DDDD" s **novým** kódem |
| 9 | zkontrolovat v listu Aktivity | `puvodni_kod` = původní `00-00-000-XXXX` |
| 10 | zkontrolovat list Vazba aktivita–dílčí proces | vazba je na nový kód a nový dílčí proces, na starý kód nic nezbylo |
| 11 | zkontrolovat list HistorieKodu | **nepřibyl** žádný řádek |
| 12 | chip nezařazených | ukazuje `(0)` a zůstává vidět, dokud je režim zapnutý |
| 13 | otevřít běžnou aktivitu s platným kódem | agenda, proces i dílčí proces jsou jen ke čtení |
| 14 | publikovat HTML mapu | `Nezařazeno` v ní není na žádné úrovni |

### Brány na 92

`check_solution` **582** · `check_restore_flow` 571 · `check_zaloha_flow` 184 ·
`check_import_flow` 175 · `check_sablona` 185 · `check_mapa_flow` **144**
(bylo 139) · `check_export_flow` 129 · `check_flow`, `check_env`,
`check_schema` zeleně. `check_app`: 5 obrazovek, **245 prvků**.
`node check_setup.js` i `node check_import.js` smoke OK.
Mutačně: `mutace_import` 25/25, `mutace_restore` 17/17, `mutace_zaloha` 16/16,
`mutace_export_mapa` 7/7, `mutace_parametry` 4/4, `mutace_napojeni` 5/5.
Nové kontroly ověřeny mutací zvlášť: C3 4/4, C4 4/4, výlučnost nabídek 1/1,
`$filter` v mapě 1/1.

Sestavení:

```
copy deploy\procesnimapa_1_0_0_91.zip runs\vstup_92.zip
python src/build_mapa_flow.py --solution runs/vstup_92.zip
python src/add_mapa_schedule.py --solution runs/vstup_92.zip
python src/build_app.py --solution runs/vstup_92.zip --verze 1.0.0.92
```

**Pozor na dvojče:** `build_mapa_flow.py` přepíše jen `MapaPublishFlow`.
Plánované `MapaPublishScheduled` je jeho klon a musí se přegenerovat hned
po něm, jinak `check_mapa_flow` hlásí „akce dvojčete se liší od ručního flow"
a v noci by se publikovalo podle staré definice.

**Pozor na `--base`:** `check_mapa_flow.py` má ve výchozím stavu
`input/procesnimapa_1_0_0_66.zip`, který se při úklidu 02.09. smazal.
Spouštět s `--base input/procesnimapa_1_0_0_86.zip`.

## MPSV — co bude potřeba, až bude přístup

**MPSV běží na 1.0.0.65, PPF DEV na 1.0.0.91.** Mezi nimi je 26 verzí a
`deploy/mpsv/` je snímek k té staré. Ověřeno 02.09.2026 porovnáním se
schématem — **snímku chybí**:

| co chybí ve snímku 65 | přibylo ve verzi |
|---|---|
| list `HistorieKodu` | F10/1 (31.08.) |
| knihovna `Zalohy` | F11 |
| knihovna `Exporty` | 1.0.0.81 |
| knihovna `Import` | 1.0.0.85 |
| technické položky `00` / `00-00` / `00-00-000` | F13/C1 (02.09.) |

**Z toho plyne: `deploy/mpsv/` se před přenosem MUSÍ přegenerovat.** Kdyby se
tam nasadil balík 91 se starým `01_zaloz_listy.js`, appka by nenašla listy ani
knihovny a flow by padaly na neexistujících složkách. Přegenerování je jeden
příkaz (`make_setup.py` + `make_import.py`), ale musí se na něj myslet —
snímek vypadá hotově a nic nehlásí, že je zastaralý.

Soubory potřebné pro přenos jsou zkontrolované a na místě (02.09.):
`deploy/mpsv/*` (4 skripty + README + balík 65 + schéma), `src/setup_sharepoint.js`,
`src/import_data.js`, `src/make_setup.py`, `src/make_import.py`, `src/schema.json`,
`kody.json`, `deploy/INSTALACE.md`, `deploy/sablona_import_aktivit.xlsx`,
`runs/normalize/` a `runs/anonym/` (data k importu).

**Přístup do tenantu MPSV chybí už několik dní** — do té doby se nedá nic z toho
ověřit.

## STAV ZKOUŠEK (vše ověřeno na datech 02.09.)

| co | stav |
|---|---|
| import balíku, otevření ve Studiu | **OK** |
| datum a čas u seznamu záloh | **OK** — `rejstrik_2026-09-02_1750.json · 2.9.2026 19:50` |
| náhled obnovy | **OK** |
| obnova na datech | **OK** |
| import — náhled | **OK** — 200 řádků, 198 prázdných, 2 založí, 1 bez zařazení |
| import — zápis | **OK** — nové položky vznikly |
| rozbalovátka v šabloně | **OK** — kaskáda proces → dílčí proces funguje |

## Co se dnes udělalo (02.09.2026)

**Balík 1.0.0.89 — datum u záloh (F13/A).** `RestoreFlow` v režimu `seznam`
přidal `Created` a skládá ho za název; schéma odpovědi zůstalo totožné, takže
flow nepotřebovalo novou registraci. Appka posílá zpět jen holý název, ořezává
na třech místech.

**F13/C1 — technické položky.** Provisioning zakládá `00` / `00-00` /
`00-00-000` „Nezařazeno". Bez nich by aktivita bez zařazení neměla pod čím
vzniknout — kód se odvozuje od rodiče a `Title` je povinný.

**Balík 1.0.0.90 — čitelný souhrn a šablona na 200 řádků.** Čtyři čísla obnovy
byla slepená do `0 · 0 · 0 · 6`; teď jsou to sloupce s hlavičkou a nula je
utlumená, aby nenulové číslo vyskočilo. Šablona měla jeden datový řádek, takže
cokoli napsaného níž bylo **mimo Tabulku** a konektor to nevidí.

**Balík 1.0.0.91 — holé aktivity (C2) a rozbalovátka (B1+B2).** Prázdný dílčí
proces se nahradí `00-00-000`; náhrada běží až za oddělením prázdných řádků,
jinak by šablona zakládala dvě stě sirotků z prázdných řádků. Šablona má list
`Ciselniky` a kaskádu proces → dílčí proces přes pojmenované rozsahy.

**Nález dne: citlivostní štítek.** Import padal na 403
`OpenWorkbookAccessDenied`. Štítek **„Interní" projde**, přísnější sešit
zašifruje a Excel Online ho přes Graph API neotevře ani vlastníkovi. Zapsáno
do `power-Apps-skill`, `deploy/flow_Import.md` a do pokynů v šabloně.

## Co zbývá z F13

| blok | stav |
|---|---|
| A — datum u záloh | **hotovo** (1.0.0.89) |
| B1 + B2 — rozbalovátka v šabloně | **hotovo** (1.0.0.91) |
| B3 — automatický refresh číselníků | **nezačato**, a zadání se změnilo — viz `PLAN.md` |
| C1 — technické položky | **hotovo** |
| C2 — import bez zařazení | **hotovo** (1.0.0.91) |
| C3 — dlaždice nezařazených | **hotovo** (1.0.0.92) |
| C4 — přiřazení sirotka v appce | **hotovo** (1.0.0.92) |

**C3 vyřešilo i to, co u něj stálo jako varování:** agenda `00` „Nezařazeno"
se skrývá teprve teď, kdy je náhradou chip na přehledu. Ve stromu, v kartách,
v číselníku ani v publikované mapě už není.

**Pozor u B3:** pojmenované rozsahy číselníků jsou přesně podle počtu položek
(jinak by nabídka měla prázdné řádky), ale Excel konektor umí přepsat buňky,
**ne definici rozsahu**. Refresh sám o sobě proto nestačí, jakmile položek
přibude nebo ubude. Dvě cesty k rozhodnutí jsou v `PLAN.md` u kroku B3.

## Balík 1.0.0.88 — oprava PA1011 (01.09.2026 14:55)

Appka z balíku 87 **nešla otevřít v editaci**: `Error opening file`, tři chyby
`PA1011: The keyword 'Variant' is required but is missing or empty` nad
`scr_Nahled.pa.yaml`. Import balíku přitom proběhl zeleně.

**Příčina:** galerie v `pa.yaml` musí mít hned pod `Control:` klíč `Variant`
(v téhle appce `BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0`). Moje tři
nové galerie ho neměly. Existující galerie v `scr_Vazby` a `scr_Ciselnik` ho
mají, takže to bylo vidět — jen jsem se na ně nepodíval.

**Co to nechytilo:** `pac canvas pack` zabalil bez námitek, import solution
prošel, `check_solution` i `check_app` byly zelené. Přesně ten případ, před
kterým varuje `power-Apps-skill`: *„pac canvas pack nechytí ani jednu z nich —
zabalí to a chyba přijde až ve Studiu."*

**Brána, která to od teď chytne:** `kontrola_varianty` v `check_app.py`.
Ověřeno mutací — po odebrání jednoho `Variant` vypíše
`'gal_SouhrnImportN' typu Gallery@2.15.0 nemá hned pod Control klíč Variant`
a spadne. Kontroluje i to, jestli varianta není v appce osamocená; osamocená
znamená šablonu navíc v `Templates.json`, a tu balík negeneruje.

Použitá varianta je táž, jakou už mají galerie v `scr_Vazby`, takže
`Templates.json` v `.msapp` zůstal beze změny (sedm šablon).

## Balík 1.0.0.87 — obrazovka náhledu (01.09.2026 15:05)

`src/app_src/scr_Nahled.pa.yaml` — **jedna obrazovka pro import i obnovu**.
Obě operace mají týž tvar (vyber soubor → zkontroluj nanečisto → podívej se,
co z toho vyjde → teprve pak zapiš), takže dvě obrazovky by znamenaly udržovat
dvakrát totéž. Rozlišuje je `varNahledRezim`.

Nabídka `Data ▾` má teď šest položek: dva exporty, vzorová tabulka, import,
záloha, obnova.

### Dvě rozhodnutí, která šetřila kolo se Studiem

**Odpovědi z flow chodí jako oddělovaný text, ne JSON.** Appka má
`dynamicschema = False`, takže na `ParseJSON` nemá co navázat; `Split()`
funguje vždycky. Pole se spojují `|~|`, řádky `|#|`. Appka je bere **podle
pořadí** — oddělovaný text jméno pole nenese —, takže pořadí je součástí
kontraktu a hlídají ho obě brány. Bez toho by se to poznalo až tím, že by
appka ve Studiu nešla otevřít.

**Obě flow dostala třetí režim `seznam`.** Vrátí názvy souborů v knihovně,
takže appka nemusí mít `Import` ani `Zálohy` připojené jako datový zdroj —
a připojit je jde jedině ve Studiu, tedy dalším kolem. Flow navíc vrací přesně
ta jména, která samo přijímá na vstupu, takže se nemají jak rozejít. Schéma
odpovědi zůstalo totožné (čtyři řetězce), takže registrace platí dál.

### Co brána chytila na obrazovce

Nic z toho by se jinak nepoznalo dřív než ve Studiu:

- tři tlačítka měla výšku 36 px, zbytek appky má 32 — „táž akce by na dvou
  obrazovkách vypadala jinak";
- `Classic/DropDown` **nemá vlastnost `Value`** (PA2108). Správný tvar je
  jednosloupcová tabulka v `Items` a čtení přes `Selected.Value` — a `Split()`
  takovou tabulku rovnou vrací, takže mezikolekce zmizela úplně.

### Pojistka proti zápisu podle cizích čísel

Tlačítko *Provést* je zhasnuté, dokud náhled neproběhl **právě nad vybraným
souborem** (`varNahledHotovo <> drp_SouborN.Selected.Value`). Změna souboru
v rozbalovátku náhled zneplatní. Bez toho by šlo zkontrolovat jeden soubor,
přepnout na druhý a odklepnout zápis podle čísel, která pro něj neplatí.

### Brány na 87

`check_solution` **571** · `check_restore_flow` **568** · `check_zaloha_flow`
184 · `check_import_flow` **159** · `check_export_flow` 129 ·
`check_mapa_flow` 139 · `check_flow` 26 · `check_app` (5 obrazovek, 234 prvků),
`check_env`, `check_sablona` zeleně. Mutačně: `mutace_import` 21/21,
`mutace_restore` 15/15, `mutace_zaloha` 16/16, `mutace_sablona` 15/15,
`mutace_export_mapa` 7/7, `mutace_parametry` 4/4, `mutace_napojeni` 5/5.

Sestavení:

```
copy input/procesnimapa_1_0_0_86.zip runs/vstup_87.zip
python src/odeber_flow.py --solution runs/vstup_87.zip --flow testtest
python src/build_import_flow.py --solution runs/vstup_87.zip
python src/build_restore_flow.py --solution runs/vstup_87.zip
python src/build_app.py --solution runs/vstup_87.zip --verze 1.0.0.87
```

## Balík 1.0.0.85 — ImportFlow a úklid záloh (01.09.2026 14:15)

### ImportFlow

`src/build_import_flow.py` → 31 akcí. Brána `src/check_import_flow.py`
**145 kontrol**, mutace `src/mutace_import.py` **21/21**, kontrakt
`deploy/flow_Import.md`.

Vstup `{"soubor": "karta_s3.xlsx", "rezim": "nahled" | "zapis"}`, odpověď
`{stav, soubor, prehled, chyby}` — `prehled` i `chyby` jako řetězec, aby se
schéma odpovědi neměnilo s obsahem a flow se nemuselo znovu registrovat.

**Balík nenese ani jedno tenantové ID.** Parametry excelového konektoru se
skládají za běhu: `source` z proměnné webu a dvou REST dotazů, `drive`
z `/_api/v2.0/drives` podle **URL segmentu** knihovny (ne podle zobrazovaného
názvu — ten nese diakritiku a mění se přejmenováním). Bez toho by se flow na
MPSV nepřeneslo.

**Rozklad řádků je úplný a nepřekrývá se:**

```
Ocistene ─┬─ Prazdne        všechny buňky prázdné → ignoruje se
          └─ S_obsahem ─┬─ Chybne          chybí název nebo kód dílčího procesu
                        └─ Uplne ─┬─ Neznamy_dilci   dílčí proces v rejstříku není
                                  └─ Zarazene ─┬─ Duplicitni  dvojice dílčí+název už je
                                               └─ K_zalozeni  zakládá se
```

Kdyby se skupiny překrývaly, sedělo by v náhledu jiné číslo než ve skutečnosti
a správce by opravoval podle něj. Čísla řádků v hlášení jsou skutečná čísla
v sešitě (index+2 kvůli hlavičce) — proto se řádky procházejí přes index.

**Kódy** se přidělují sekvenčně ze sdílené proměnné (souběžnost smyčky 1),
z nejvyššího dosud použitého pod týmž rodičem — smazaný kód se nerecykluje.
Ke každé aktivitě vzniká primární vazba s klíčem `<kod>__<dilci>`, tedy v témž
tvaru, jaký zakládá appka. `nazev_kratky` import nezapisuje, dopočítá ho
`AktualizaceKratkehoNazvu`.

### Úklid starých záloh

Zadáno v 13:52. Obě záložní flow po uložení nového snímku nechají v knihovně
**posledních 20** a starší pošlou **do koše**. Počet je akce `Kolik_nechat`;
mění se v `build_zaloha_flow.py` (`POCET_ZALOH`) a rebuildem.

Bylo to levné, protože flow už existovalo: šest akcí na konci, žádné nové
flow, žádná nová proměnná, žádné další oprávnění.

Čtyři věci, na kterých to stojí, každou shazuje vlastní mutace:

1. **běží až po uložení** nového snímku — jinak by mazal o jeden víc a při
   chybě zápisu by zůstal úklid bez zálohy;
2. **maže jen `rejstrik_RRRR-MM-DD_HHMM.json` včetně délky jména** — snímek,
   který chceš udržet natrvalo, stačí **přejmenovat**. To je schválně: bez
   toho by „posledních 20" znamenalo, že po třech týdnech není z čeho obnovit
   starší stav, což je přesně ten případ, kvůli kterému zálohy vznikly (R-5,
   stav při schvalování OŘ);
3. **`skip`, ne `take`** — zahazuje se ocas seznamu řazeného od nejnovějšího;
4. **`recycle()`, ne `DELETE`** — soubor jde do koše (93 dní).

Řadí SharePoint přes `$orderby: Created desc`; `sort()` nad polem objektů
Logic Apps nemá.

### Brány na 85

`check_solution` **536** · `check_restore_flow` 531 · `check_zaloha_flow`
**184** · `check_import_flow` **145** · `check_export_flow` 129 ·
`check_mapa_flow` 139 · `check_flow` 26 · `check_app`, `check_env` zeleně.
Mutačně: `mutace_import` **21/21**, `mutace_restore` 15/15, `mutace_zaloha`
**16/16**, `mutace_export_mapa` 7/7, `mutace_parametry` 4/4,
`mutace_napojeni` 5/5.

Sestavení (pořadí je součást postupu — generátory flow PŘED `build_app.py`):

```
copy deploy/procesnimapa_1_0_0_84.zip runs/vstup_85.zip
python src/build_zaloha_flow.py --solution runs/vstup_85.zip
python src/build_import_flow.py --solution runs/vstup_85.zip
python src/build_app.py --solution runs/vstup_85.zip --verze 1.0.0.85
```

## Zkouška dynamických parametrů Excelu — dvě ze tří odpovědí (01.09.2026 13:31)

Testovací flow (`Get file metadata using path` → `List rows present in a table`)
spadlo, ale na **překlepu v názvu tabulky**, ne na omezení konektoru:
`No table was found with the name 'Activity'` — v poli `Table` bylo anglicky
`Activity`, kdežto tabulka v šabloně se jmenuje **`Aktivity`**.

Právě proto je ta chyba cenná. Vyplývá z ní:

| otázka | odpověď | z čeho |
|---|---|---|
| smí být `file` dynamické? | **ano** | akce se k tabulce vůbec dostala; `File` se vyhodnotil na `%252fSdilene%2bdokumenty%252fsablona_import_aktivit.xlsx`, tedy `{Identifier}` ze SharePointu |
| dá se `table` adresovat jménem? | **ano** | konektor tabulky vyhledává podle názvu — jinak by nehlásil „no table was found with the **name**" |
| dá se `drive` zadat jménem knihovny? | **ne** | `Sdilene dokumenty` skončilo na `The provided drive id appears to be malformed, or does not represent a valid drive` |

Import tedy dokáže číst **libovolný nahraný sešit**, ne jen jedno pevné místo.

Vedlejší nález: knihovna `Dokumenty` má v URL segment **`Sdilene dokumenty`** —
zobrazovaný a interní název se u výchozí knihovny liší, s tím musí `ImportFlow`
počítat, pokud by se adresovalo cestou.

**Potvrzeno zeleným během v 13:38** (po opravě názvu tabulky na `Aktivity`):
akce vrátila jeden řádek se všemi osmi sloupci prázdnými, klíče jsou hlavičky
včetně diakritiky. `File` byl přitom dynamický z předchozí akce a `Table`
zadaná textem — obojí tedy konektor přijímá.

Běh jel pod **`sys_power_platform@pmb.cz`**, tedy pod servisním účtem
(connection reference, ne invoker) — appka nebude po uživatelích chtít vlastní
excelové spojení.

**`drive` musí být Graph ID `b!…`, jménem knihovny to nevezme** (ověřeno
13:43). Zbývá tedy jediná otázka: umí si ho flow dotáhnout za běhu?

- `source` **ano** — má tvar `sites/<host>,<siteId>,<webId>` a oba GUIDy
  vydává REST (`/_api/site/id`, `/_api/web/id`). Pro PPF DEV je to
  `sites/ppfbanka.sharepoint.com,88f35380-bf73-40fc-b9d2-33fa58270333,f2148e9c-0c38-4234-b945-9f5984ead91c`.
- `drive` — závisí na tom, jestli SharePoint vydá `/_api/v2.0/drives`.
  Odpoví to `src/zjisti_excel_ids.js` (konzole prohlížeče na cílovém webu).
  Když ano, `ImportFlow` si drive id najde podle jména knihovny za běhu
  a balík nepotřebuje ani novou proměnnou, ani ruční krok při instalaci.
  Když ne, přibude textová proměnná `mpsv_importDrive`, kterou správce
  jednou vyplní hodnotou z výpisu.

## Náhled obnovy proběhl — a odpověděl i na otevřenou otázku (01.09.2026 13:15)

První běh `RestoreFlow` v režimu `nahled` nad snímkem `rejstrik_2026-09-01_0300.json`
skončil zeleně a vrátil **samé nuly**:

| list | založit | změnit | navíc | celkem ve snímku |
|---|---|---|---|---|
| Agendy | 0 | 0 | 0 | 6 |
| Procesy | 0 | 0 | 0 | 44 |
| DilciProcesy | 0 | 0 | 0 | **249** |
| Aktivity | 0 | 0 | 0 | 48 |
| AktivitaDilciProces | 0 | 0 | 0 | 54 |
| Utvary | 0 | 0 | 0 | 7 |

**Tím padla i poslední otevřená otázka F11 kroku 1.** `celkem_ve_snimku` je
délka pole ve snímku, a u `DilciProcesy` je **249**, ne 100 — stránkování
v `ZalohaFlow` se tedy propsalo a snímek není oříznutý. Čísla navíc sedí na
Site contents řádek po řádku.

**Co to dokazuje o porovnání:** kdyby se otisky rozešly (Choice bez
`?['Value']`, jiné pořadí sloupců, jiný oddělovač), ukázalo by se 249
dílčích procesů ve sloupci „změnit". Nula u všech sedmi listů znamená, že
otisk ze snímku a otisk z listu vycházejí znak po znaku stejně.

**Co to NEdokazuje:** že obnova umí rozdíl najít a opravit. Zelený náhled nad
nezměněnými daty ukazuje jen to, že nevyrábí falešné rozdíly. Skutečná
zkouška je smazat pár řádků, spustit náhled (musí je vypsat ve sloupci
„založit") a pak režim `zapis`.

## Balík 1.0.0.84 — RestoreFlow (01.09.2026 13:10)

`src/build_restore_flow.py` → flow `RestoreFlow`, 57 akcí nejvyšší úrovně.
Brána `src/check_restore_flow.py` **531 kontrol**, mutace
`src/mutace_restore.py` **15/15**, kontrakt `deploy/flow_Restore.md`.

Vstup: `{"soubor": "rejstrik_….json", "rezim": "nahled" | "zapis"}`.
Odpověď: `{stav, hlaseni, porizeno, prehled}`, kde `prehled` je **řetězec** —
schéma odpovědi se tak nemění s počtem listů a appka ho rozebere `ParseJSON`.

### Čtyři pravidla, na kterých to stojí

1. **Cíl zápisu se dohledává podle kódu, nikdy podle `ID` ze snímku.** To ID
   je stav k okamžiku zálohy; po smazání a znovuzaložení patří jinému záznamu
   a MERGE podle něj by tiše přepsal cizí řádek — se zeleným během. Každá
   úprava proto nejdřív dohledá řádek podle `Title` akcí `Najdi_<list>`.
2. **Obnova nikdy nemaže.** Řádek, který dnes je a ve snímku není, se jen
   spočítá do `navic`. Brána odmítá jakoukoli mazací operaci i metodu DELETE.
3. **Zápis přes `SendHTTPRequest`, ne `PatchItem`.** Konektorová zápisová akce
   s rozloženým tělem chce `table` jako GUID natvrdo — u sedmi listů by to byl
   balík nepřenositelný na MPSV. REST adresuje list interním názvem ze
   schématu, který je všude stejný.
4. **Porovnává se otiskem řádku** ze všech sloupců schématu. Otisky musí být
   symetrické: z listu Choice s `?['Value']`, ze snímku bez něj. Kdyby se
   rozešly, hlásila by obnova změnu u každého řádku a přepsala by celý
   rejstřík sama sebou. Brána to hlídá z obou stran.

### Co mutační test opravdu dokázal

15 mutací, 15 chycených, a každou chytila ta kontrola, kvůli které vznikla —
ne nesouvisející. Mimo jiné: zápis podle ID ze snímku, dohledání podle názvu
místo kódu, vypnuté stránkování, otisk bez `?['Value']` z jedné i druhé
strany, zápis vytažený z podmínky režimu, MERGE bez `X-HTTP-Method`
(z úpravy by byl druhý POST a vznikl by duplicitní řádek), prázdné datum
jako `""` místo `null`.

### Dvě věci, které stály cyklus navíc

**Pořadí buildu je závazné: generátor flow PŘED `build_app.py`.** Deklarace
použitých parametrů doplňuje jedno místo v buildu, takže flow přidané až do
hotového balíku je nemá a spadlo by za běhu na `InvalidTemplate` — appka by
přitom viděla jen `502 BadGateway`. Chytila to `check_solution` hned.
Docstring u `build_zaloha_flow.py` přitom radí opak; neřídit se jím.

**Testovací flow uživatele se z balíku muselo vyndat.** `importnewdata` veze
natvrdo adresu webu PPF, protože parametry Excel konektoru jsou neprůhledná
ID vázaná na tenant. Odebírá ho nový `src/odeber_flow.py`; connection
reference `mpsv_sharedexcelonlinebusiness_035ba` zůstává, kvůli ní to flow
vzniklo.

### Brány na 84

`check_restore_flow` **531** · `check_solution` 499 · `check_export_flow` 129
· `check_zaloha_flow` 157 · `check_mapa_flow` 139 · `check_flow` 26 ·
`check_app`, `check_env` zeleně. Mutačně: `mutace_restore` 15/15,
`mutace_zaloha` 9/9, `mutace_export_mapa` 7/7, `mutace_parametry` 4/4,
`mutace_napojeni` 5/5.

Sestavení (pořadí je součást postupu):

```
copy input/procesnimapa_1_0_0_83.zip runs/vstup_84.zip
python src/odeber_flow.py --solution runs/vstup_84.zip --flow importnewdata
python src/build_restore_flow.py --solution runs/vstup_84.zip
python src/build_app.py --solution runs/vstup_84.zip --verze 1.0.0.84
```

`runs/vstup_84.zip` zůstává jako srovnávací základ pro `check_solution`
(`--vstup`) — proti původnímu exportu by brána správně hlásila, že v balíku
chybí flow, které jsme schválně vyndali.

## DLP test Excel Online — ZELENÝ (01.09.2026 12:34)

Běh doběhl `statusCode 200` a vrátil přesně čekaný tvar: **jeden řádek se
všemi osmi sloupci prázdnými** — ten prázdný datový řádek, se kterým se
šablona vydává.

Co se tím doložilo:

| co | doklad |
|---|---|
| Excel Online (Business) prochází DLP v PPF | akce je ve vyhledávání, flow jde uložit i spustit; hlavička `x-ms-dlp-re: GetItems\|False` |
| konektor vidí **formátovanou Tabulku** | rozbalovátko `Table` samo nabídlo `Aktivity` |
| klíče řádků = hlavičky včetně diakritiky | `"Název aktivity (úplný)"`, `"Primární dílčí proces (kód)"`, … |
| prázdný řádek se opravdu vrací | `value` má 1 položku se samými `""` — import ho MUSÍ přeskočit |

**Nález pro stavbu `ImportFlow`:** parametry akce jsou čtyři neprůhledná ID
vázaná na tenant a na konkrétní soubor —
`source: sites/ppfbanka.sharepoint.com,88f35380-…`,
`drive: b!gFPziHO__EC50jP6WCcDM5yOFPI4DDRCuU…`,
`file: 014MQA5N2GV4UBFLHC5NGITQROADGRAWQF`,
`table: {00000000-000C-0000-FFFF-FFFF00000000}`.
Natvrdo v balíku by to znamenalo flow, které se na MPSV nepřenese a navíc umí
číst jen jeden konkrétní soubor. Řeší se to při stavbě 3b; `file` musí být
dynamické tak jako tak, protože správce nahrává pokaždé jiný sešit.

## Balík 1.0.0.82 — exporty mají vlastní knihovnu (01.09.2026 11:45)

Zadáno z provozu: v Site Assets se za měsíc nashromáždilo přes deset
vyexportovaných dokumentů vedle publikované mapy a její šablony a knihovna
přestala být čitelná.

**Úplně bez ukládání to nejde** — `Download()` v Power Apps potřebuje adresu
souboru někde na webu, takže flow musí dokument nejdřív vytvořit. Změnilo se
tedy místo, ne princip:

| co | kam | proč |
|---|---|---|
| vyexportované `.doc` / `.xls` | knihovna **`Exporty`** | generuje se při každém kliknutí, roste |
| `procesni_mapa.html`, `mapa_template.html`, `sablona_import_aktivit.xlsx` | **Site Assets** | statické soubory webu, negenerují se |

Knihovnu zakládá `setup_sharepoint.js` ze `schema.json` (`libraries`), takže
**krok 1 instalace se musí spustit znovu** i tam, kde už proběhl. Novou
proměnnou prostředí to nepotřebuje: složka je literál relativní k webu,
adresu si flow bere z `mpsv_procesnimapaSite` jako dosud.

**Brána:** `check_export_flow` nově tvrdí, že `folderPath` zápisové akce je
právě `/Exporty` — samotná kontrola vrácené adresy nestačí, ta by prošla
i zápisu jinam. 129 kontrol. Adresa mapy i vzorové tabulky se dál skládá
proti Site Assets a je ověřená proti reálnému odkazu z knihovny, takže se
rozdělení konstant nemohlo tiše promítnout do nich.

**Úklid starých exportů zatím není.** Knihovna poroste dál, jen jinde. Až
bude vadit, je to pár akcí navíc v `ExportFlow` za `Response` (volající na ně
nečeká) — smazat soubory starší než N dní. Nabízeno, nezadáno.

## Kontrola nasazení na PPF DEV podle snímků (01.09.2026 10:42)

**Nic nechybí.** Site contents má všech sedm listů schématu plus knihovnu
`Zalohy`, kterou přidal balík 80:

| co | v prostředí | pozn. |
|---|---|---|
| Agendy · Procesy · Dílčí procesy · Aktivity | 6 · 44 · 249 · 48 | data, ne schéma — viz níže |
| Vazba aktivita–dílčí proces | 54 | M:N, víc řádků než aktivit je správně |
| Útvary | 7 | |
| Historie kódů | 0 | správně — plní se až při přesunu položky (F10/2) |
| Zálohy (knihovna) | 2 | oba snímky z plánovaného běhu |
| Site Assets | 14 | mapa, šablona mapy, exporty |
| Documents | 0 | výchozí knihovna webu, projekt ji nepoužívá |

**Počty se liší od čísel v dokumentaci a je to v pořádku.** Rejstřík se
importoval jako 7/46/250/46, dnes je 6/44/249/48. Rozdíl je testovacím
mazáním a zakládáním v appce, ne ztrátou dat — čísla v `CLAUDE.md` popisují
původní import, ne živý stav PPF DEV.

**Zálohy mají jen soubory z plánovaného běhu** (`_1748` z 31.08., `_0300`
z 01.09.), žádný ruční — což sedí na hlášenou vadu tlačítka, viz níže.

## Balík 1.0.0.81 — nabídka Data ▾ a vzorová tabulka (01.09.2026 11:05)

### Proč tlačítko Záloha nereagovalo

**Nebylo to flow ani registrace.** Popisek `lbl_RozpadPocet` („47 řádků") má
`X = Parent.Width - 240`, což je na návrhové ploše 1366 přesně **1126** —
a tlačítko Záloha sedělo na 1120 se šířkou 100. Popisek tedy ležel přes jeho
pravých **94 ze 100 px**, a protože je v souboru později, kreslí se NAD ním.
Spolkl klik i tooltip. Odtud oba hlášené příznaky naráz: „nic nedělá"
i „divný tooltip" — ten text o plochém seznamu a 2 000 záznamech patří tomu
popisku, ne tlačítku.

Klik na levých 6 px by fungoval, což vysvětluje, proč to nešlo poznat jako
chyba rozvržení.

### Brána, která to od teď chytne

`kontrola_prekryvu` v `check_app.py` souřadnice zadané výrazem dosud
**přeskakovala** — s odůvodněním, že bez znalosti šířky plochy by hádala.
Hádat ale nemusí: appka má `ScaleToFit`, takže `Parent.Width` je vždycky
1366 bez ohledu na okno prohlížeče. Nová `souradnice_v_px()` dopočítá tvary
`Parent.Width/Height ± N`.

Spuštěná na vadném zdroji vypsala **přesně jeden nález** —
`btn_Zaloha` a `lbl_RozpadPocet` se překrývají o 94×28 px — a nic jiného,
takže to není plošné zpřísnění, které by se muselo obcházet výjimkami.
Shodu konstanty s `DocumentLayoutWidth/Height` v `.msapp` hlídá
`check_solution.py`, aby brána nezačala počítat s cizími čísly.

### Nabídka Data ▾

Export ▾, Záloha a budoucí Import sjednoceny do jednoho rozbalovátka na
X = 1016. Položky: **Export do Wordu (.doc)** · **Export do Excelu (.xls)** ·
**Vzorová tabulka pro import** · **Záloha rejstříku**. `varMenuExport`
přejmenována na `varMenuData`. HTML mapa ▾ zůstává samostatně — zadání
mluvilo o exportu, importu a záloze.

Vedlejší účinek, který stojí za zmínku: pruh se tím zkrátil o dvě tlačítka,
takže popisek s počtem řádků už nemá na co lézt.

### Vzorová tabulka ke stažení

`ExportFlow` umí nový režim **`__sablona__`**: vrátí adresu souboru
`SiteAssets/sablona_import_aktivit.xlsx` a appka na ni zavolá `Download()`.
Je to táž smluvená hodnota vstupu jako `__mapa__`, takže **flow nepotřebuje
novou registraci ve Studiu** — schéma volání se nemění.

Rozdíl proti mapě je záměrný: šablona dostane **přímou cestu** k souboru
(Strict browser file handling ji pošle do Downloads, což je přesně to chtěné),
mapa odkaz na náhled knihovny (má se zobrazit, ne stáhnout).

Sešit flow **nesestavuje** — `.xlsx` je zip a Logic Apps zip nevyrobí.
Nahrává ho správce do Site Assets, nově krok 5 v `INSTALACE.md`, a soubor se
musí jmenovat přesně tak, protože flow adresu skládá z názvu.

### Brány na 81

`check_solution` **443** · `check_export_flow` **128** (nová `vyznam_sablona`)
· `check_zaloha_flow` 157 · `check_mapa_flow` 139 · `check_flow` 26 ·
`check_app`, `check_env` zeleně. Mutačně: `mutace_parametry` 4/4,
`mutace_napojeni` 5/5, `mutace_export_mapa` 7/7, `mutace_zaloha` 9/9.

### `pac` na 5CG5210MB2 nebyl

Build appky ho potřebuje (`.msapp` se z YAML balí přes `pac canvas pack`)
a rozšíření VS Code tu není — VS Code na stroji vůbec není. Stažen tedy
balíček `microsoft.powerapps.cli` **2.11.2** z nuget.org a rozbalen do
`runs/app_build/pac/`; `build_app.py` to místo sám prohledává, takže příště
se nic zadávat nemusí. Je novější než 2.0.15x na HP-LUBOS, proto ověřeno,
že se formát nezměnil: `DocVersion 1.349` a `MSAppStructureVersion 2.4.0`
vyšly stejné jako u vydaného balíku 80.

## F11 krok 3a — šablona pro hromadný import (01.09.2026 09:05)

`src/make_sablona.py` → **`deploy/sablona_import_aktivit.xlsx`**, brána
`src/check_sablona.py` (**66 kontrol**), mutace `src/mutace_sablona.py`
(**15/15** — 6 mutací schématu, 9 sešitu).

**Rozhodnutí zadavatele:** šablona nese **jen list Aktivity**, osm sloupců.
Agendy/procesy/dílčí procesy (7/46/250) už z rejstříku existují a spravují se
v appce; hromadně přibývají aktivity. **Vedlejší zařazení aktivity (M:N)
šablona nenese** — import zakládá aktivitu s primárním dílčím procesem, další
zařazení se přidávají v appce.

Sloupce (display názvy ze schématu, v jeho pořadí): Název aktivity (úplný) ·
Primární dílčí proces (kód) · Vykonává útvar · Spolupracuje · Vnitřní předpis ·
Text pro OŘ · Sekce · Stav. Systémové v šabloně NEJSOU: `Title` (kód),
`nazev_kratky`, `datum_aktualizace`, `puvodni_kod`.

**Co z toho platí pro 3b:**
- Tabulka se jmenuje **`Aktivity`** — na to jméno se `ImportFlow` odkazuje.
- Konektor nečte buňky hlavičky, ale **jména sloupců v definici Tabulky**;
  brána hlídá, že se ty dvě sady neliší. Klíče v `item()?['…']` jsou tedy
  display názvy včetně diakritiky a závorek.
- Sešit se vydává s **jedním prázdným datovým řádkem** (Tabulku bez datového
  řádku Excel „opravuje"). `List rows present in a table` ho vrátí jako řádek
  se samými prázdnými hodnotami — **import ho musí přeskočit**, jinak založí
  prázdnou aktivitu hned při prvním použití šablony.
- **Prázdný Stav = `pracovní`** (tak to slibují Pokyny v sešitě).

**Postaveno navíc oproti plánu:** druhý list `Pokyny` (povinnost, omezení
a max. délka odvozené ze schématu + krátká nápověda ke každému sloupci; brána
hlídá, že slovník `NAPOVEDA` pokrývá přesně sloupce šablony, takže přidání
sloupce do schématu shodí build, dokud se nápověda nedopíše) a rozbalovátko
s chybovou hláškou nad sloupcem Stav.

**Detail, na kterém stojí smysl brány:** zákaz systémových sloupců brána
vyslovuje **vlastním seznamem `ZAKAZANE`**, ne konstantou `SYSTEMOVE`
z generátoru. Kdyby ze `SYSTEMOVE` sloupec vypadl, generátor i brána by se
shodly na tom, že do šablony patří, a mutace by nic nechytila.

## Balík 1.0.0.80 — tlačítko „Záloha" (31.08.2026 20:35)

Postaveno z exportu `input/procesnimapa_1_0_0_79.zip`, který doložil
registraci všech tří nových zdrojů:

| zdroj | jak je v appce |
|---|---|
| `ZalohaFlow` | `ServiceInfo`, `FlowNameId 92767d85-1d09-4847-8d04-26141252cd19` |
| `Historie kódů` | `ConnectedDataSourceInfo` |
| `Zálohy` (knihovna) | `ConnectedDataSourceInfo` |

`ZalohaScheduled` registrované není a správně — plánované flow se z appky
nevolá.

**Tlačítko** `btn_Zaloha` v horní liště Přehledu (X=1120, vedle `Export ▾`).
Bez nabídky, protože má zatím jedinou volbu; až přibude obnova, stane se
z toho rozbalovátko jako u mapy a exportu. `DisplayMode` na `varZalohuji`,
aby dvojklik nevyrobil dva snímky. Vzorec je `IfError` + `Notify` podle
stejného vzoru jako `MapaPublishFlow` — hlášení potvrzuje **spuštění**,
ne dokončení.

**Brány na 80:** `check_solution` 435 · `check_zaloha_flow` 157 ·
`mutace_zaloha` 9/9 · `check_mapa_flow` 139 · `check_export_flow` 124 ·
`check_flow`, `check_env`, `check_app` zeleně.

Sestavení: `build_app.py --solution input/procesnimapa_1_0_0_79.zip
--verze 1.0.0.80` (přes `pac`, generátory flow se nepouštěly — flow jsou
na prostředí nezávislá a v exportu už jsou).

## Čeká se na export s listem `HistorieKodu` (31.08.2026 20:05)

Export **1.0.0.78** dorazil a doložil to hlavní: **`ZalohaFlow` je
zaregistrované** (`FlowNameId 92767d85-1d09-4847-8d04-26141252cd19`).
`ZalohaScheduled` registrované není a správně — plánované flow se z appky
nevolá. Uživatel do Studia dopojuje `HistorieKodu` a pošle další export;
z něj se staví 1.0.0.79.

**Knihovna `Zálohy` v appce zůstává.** Připojila se omylem místo
`HistorieKodu`, ale ukázalo se, že je pro F11 krok 4 potřeba: nabídku snímků
k obnově (podle data a času) umí canvas app přečíst z připojené knihovny sama,
kdežto obsah snímku přečíst neumí — to je práce `RestoreFlow`. Dostala proto
devátou proměnnou `mpsv_listZalohy`.

### Vada v `napoj_appku_na_promenne`, kterou ten export odhalil

Studio zakládá **ručně připojený zdroj do vlastního `dataSets` bloku**,
klíčovaného čistou URL, kdežto zdroje, které už buildem prošly, sedí v bloku
se suffixem `_mpsv_procesnimapaSite`. V 78 tak byly bloky dva: šest listů
v prvním, knihovna `Zálohy` ve druhém.

`napoj_appku_na_promenne` psala do slovníku klíč `f"{cista}_{WEB}"` po každém
bloku zvlášť. Oba bloky se po očištění klíče trefí na týž klíč, takže druhý
zápis první **přepsal** — v appce by zůstala napojená jen knihovna a šest
listů by po importu nemělo na co navázat. Nic by přitom nespadlo při buildu
ani na staré bráně: tvar přeživšího bloku je bezvadný, jen je v něm o šest
zdrojů méně.

Opraveno slučováním všech bloků do jednoho, s tvrdou chybou, kdyby zdroje
ležely na různých webech.

### Brána, která to od teď chytne

`check_solution` porovnává zdroje v napojení proti
`References/DataSources.json` v `.msapp` (typ `ConnectedDataSourceInfo`) —
pravdu o tom, na co se appka opravdu váže, má `.msapp`, ne XML. **431 kontrol.**
Mutačně ověřeno: z napojení ponechán jen poslední zdroj → brána vypíše
`v .msapp navíc ['Agendy', 'Aktivity', 'Dílčí procesy', 'Procesy',
'Vazba aktivita–dílčí proces', 'Útvary']`.

### Oprava zastaralého tvrzení o `pac`

STATUS na několika místech tvrdil, že **na HP-LUBOS `pac` není**. Je —
rozšíření VS Code `microsoft-isvexptools.powerplatform-vscode` (2.0.150
i 2.0.152) veze `microsoft.powerapps.cli.*.nupkg` a `build_app.py` si ho
rozbalí do `runs/app_build/pac/`. Ověřeno buildem z 78, který přes `pac`
proběhl. Na `--bez-pac` z téhle základny stavět stejně nejde: appka je
doauthorovaná Studiem, `LoadFromYaml` je pryč.


## F11 krok 1 hotový — snímek rejstříku (31.08.2026 19:10)

Balík **1.0.0.76**. Přibylo:

| co | kde |
|---|---|
| knihovna `Zalohy` | `src/schema.json` → `libraries`, zakládá `setup_sharepoint.js` (BaseTemplate 101) |
| 8. proměnná `mpsv_listHistorieKodu` | `src/env_promenne.py` |
| `ZalohaFlow` (PowerApps V2) + `ZalohaScheduled` (denně 5:00) | `src/build_zaloha_flow.py` |
| brána, 157 kontrol | `src/check_zaloha_flow.py` |
| mutace, 9/9 | `src/mutace_zaloha.py` |
| dokumentace a datový kontrakt | `deploy/flow_Zaloha.md` |

Snímek: `Zalohy/rejstrik_<RRRR-MM-DD_HHMM>.json`, všech sedm listů se všemi
sloupci schématu plus `ID`, klíče jsou interní názvy sloupců SharePointu
(ze snímku se dá zapisovat zpátky bez překladové tabulky).

### Dvojčata se staví z jedné funkce, ne klonováním

`add_mapa_schedule.py` vyrábí plánované dvojče klonem hotového flow ze zipu.
Tady jsem to udělal jinak: **obě definice staví jeden skript z téže funkce
`akce()`**. Klonování je pořád v pořádku pro obálku (uzel `<Workflow>`,
RootComponent, spojení), ale u logiky je zbytečné kolo, ve kterém se dá něco
ztratit. Brána dvojčata i tak porovnává celá — rozešlá dvojčata by se poznala
až ve chvíli, kdy je záloha potřeba.

### Rozhodnutí, které měl STATUS otevřené

Osmá proměnná se podle zápisu z 15:22 měla přidat až s exportem ze Studia,
protože by ji `check_solution` hlásil jako deklarovanou a nepoužitou. Ten
důvod padl: `ZalohaFlow` ji používá. Cena je pořadí úkolů výše — balík 76 se
nesmí importovat do prostředí, kde neběžel `setup_sharepoint.js`.

Rovnou se tím zavřela i druhá otevřená drobnost: `make_setup.py` uměl zakládat
jen listy (BaseTemplate 100). Teď umí i knihovny; `check_setup.js` má na to
čtyři kontroly (49 celkem) a obě mutace — knihovna založená jako list,
knihovna nezaložená vůbec — bránu shodí.

### Co je na tom mutačně ověřené

Devět mutací, každou chytí ta kontrola, kvůli které vznikla (skript vypisuje
první hlášku, ne jen návratový kód — mutace chycená nesouvisející kontrolou
vypadá stejně zeleně a přitom nedokazuje nic):

vypnuté stránkování u jednoho listu · ze snímku vypadl celý list · vypadl
sloupec · Choice bez `?['Value']` · jméno souboru z druhého `utcNow()` · zápis
mimo knihovnu `Zalohy` · snímek bez verze schématu · dvojčata rozešlá
stránkováním · dvojčata rozešlá vynechaným listem.

Nejdůležitější z nich je první: **bez `paginationPolicy` vrátí konektor jen
prvních 100 položek, běh skončí zeleně a snímek je oříznutý.** U
`DilciProcesy` (250 řádků) by se to stalo hned první noc a poznalo by se to
až při obnově.

### Brány po sestavení 76

`check_zaloha_flow` 157 · `check_solution` 427 · `check_mapa_flow` 139 ·
`check_export_flow` 124 · `check_setup.js` 49 · `check_env`, `check_app`,
`check_schema` zeleně.

## Stav balíků

V `deploy/` je jediný balík: **`procesnimapa_1_0_0_76.zip`** (PPF DEV).
Starší jsou smazané — měly vadu chybějících deklarací parametrů nebo byly
nahrazené. Je zabalený z YAML, takže z něj jde stavět dál přes `--bez-pac`
(na tomhle stroji `pac` není). Historie v gitu.

Sestavení 76: `runs/build_76/vstup.zip` je kopie 75, do ní
`build_zaloha_flow.py`, pak `build_app.py --bez-pac --verze 1.0.0.76`.
Pořadí je závazné — deklarace parametrů doplňuje `build_app.py`, takže
generátory flow musí běžet **před** ním.

## Vše z 31.08.2026 ověřeno v provozu (15:23)

Potvrzeno na PPF DEV z balíku 1.0.0.74: **publikace mapy** (oprava
`MapaPublishFlow`), **HTML mapa** ukazuje aktivitu pod všemi dílčími procesy,
**Přehled** taky, **mazání zařazení** se projeví správně. Spolu s dřívějším
potvrzením exportů, zkracování názvu a útvarů tím nezůstává nic otevřeného.

## Zneplatnění stromu po změně vazeb — vada, kterou přinesl balík 74 (15:23)

Uživatel při zkoušení mazal zařazení a vyšlo to. Kontrola kódu ale ukázala,
že to vyjít nemuselo: **`scr_Vazby` přidává i odebírá vazby bez
`Set(varAktStale, true)`**. Přehled si `colAkt`, `colVazby` a `colStrom`
staví jednou a přepočítá je až na ten příznak — bez něj by po návratu
z obrazovky vazeb visel starý strom.

Do 1.0.0.73 to nevadilo, protože Přehled vazby vůbec nečetl. **Závislost
přibyla s balíkem 74 a zneplatnění se k ní nedoplnilo** — klasická tichá
vada: projeví se jen podle toho, kudy uživatel prošel.

Opraveno v `scr_Vazby.pa.yaml` u přidání i odebrání.

### Brána `kontrola_zneplatneni_stromu`

Vzorec, který zapisuje do `Aktivity` nebo do vazebního listu a nenastaví
`varAktStale`, je od teď chyba. **Mutačně ověřeno 2/2** (odebrání, přidání) —
každá vrátí právě jednu chybu.

**Poznámka k té bráně:** napoprvé mutace nechytala a vypadala přitom zeleně.
Do regexu se při zápisu dostal skutečný znak backspace místo `` — v editoru
neviditelný, `sed` ho taky nezobrazí, našel ho až `od -c`. Kdybych se spokojil
se zelenou bránou, měl bych v repu kontrolu, která nekontroluje nic. Je to
přesně ten důvod, proč se mutace píšou.

## F10 krok 2 — co potřebuju od tebe (31.08.2026 15:22)

Appka bude zapisovat do nového listu `HistorieKodu`, a to je zásah, který
za mě lokálně udělat nejde — registrace datového zdroje vzniká jen ve Studiu
(`FlowNameId`/`DataSources.json` přiděluje prostředí, viz `power-Apps-skill`).
Pořadí je proto:

1. **Na PPF DEV spusť `src/setup_sharepoint.js`** (F12 → Console na webu
   `/sites/DigiData_D/testovaci_subsajta/procesnimapa`). Založí list
   `HistorieKodu` a doplní sloupec `puvodni_kod` do `Procesy`, `DilciProcesy`
   a `Aktivity`. Skript je idempotentní — co existuje, nechá být.
   Na konci musí říct, že chybných sloupců je 0.
2. **Power Apps Studio → Add data → `HistorieKodu`.**
3. **Mikro-změna → Save → Publish → export solution** a pošli mi zip.

Do té doby stavím vzorce a brány naslepo proti schématu — to jde, jen se
výsledek nedá zabalit do balíku, dokud zdroj v appce neexistuje.

**Osmá proměnná prostředí** (`mpsv_listHistorieKodu`) se přidá až s tím
exportem. Kdybych ji zavedl dřív, `check_solution` ji ohlásí jako
deklarovanou a nepoužitou — a měl by pravdu.

## Zobrazení M:N na Přehledu potvrzeno (31.08.2026 15:22)

Balík 1.0.0.74 ověřen v provozu — aktivita se ukazuje pod všemi svými
dílčími procesy, řazení sedí. Aktuální balík pro PPF DEV je **1.0.0.74**,
73 smazán.

## F9 krok 6 odložen — bez přístupu na MPSV (31.08.2026 14:50)

Uživatel nemá několik dní přístup do tenantu MPSV. Krok 6 (import na MPSV)
tedy **čeká na přístup**, ne na práci — je to jeden build a jeden import.

**Balík 1.0.0.71 smazán.** Byl postavený před opravou deklarací parametrů,
takže by na MPSV shodil `MapaPublishFlow` úplně stejně jako 70 na PPF.
Až bude přístup, postaví se nový z tehdy aktuálního balíku — příkaz je
`build_flow.py` s GUIDem MPSV (`b1daaa38-53df-4c7b-b9f8-03b36d46bc60`)
a pak `build_app.py --bez-pac`. Nechávat ležet vadný zip s lákavým jménem
je horší než ho postavit znovu za minutu.

Ze stejného důvodu jsou smazané i `1.0.0.67`, `68` a `70` — všechny mají
vadu deklarací. V `deploy/` zůstávají jen dva:

| balík | pro | role |
|---|---|---|
| `procesnimapa_1_0_0_73.zip` | PPF DEV | aktuální, k importu |
| `procesnimapa_1_0_0_72.zip` | PPF DEV | záloha bez zásahu do stromu, kdyby se appka z 73 neotevřela |

Oba jsou zabalené z YAML, takže z obou jde stavět dál přes `--bez-pac`.
Starší verze jsou v git historii, kdyby byly potřeba.

**MPSV běží dál na 1.0.0.65** a nic z dnešních nálezů se ho netýká — vada
deklarací přišla až s F9, tedy ve verzích, které tam nikdy nedoputovaly.

## Druhé kolo téhož nálezu — a oprava mého mylného závěru (31.08.2026 14:45)

`MapaPublishFlow` spadlo na PPF DEV toutéž chybou, jen v akci `Sablona`
(`GetFileContentByPath`). Tvrzení, které jsem zapsal o půl hodiny dřív —
že parametr konektoru deklaraci nepotřebuje a povinná je jen u template
výrazu — **neplatí**. `Sablona` používá parametr jako **celou hodnotu**
`dataset`, tedy přesně ten tvar, který měl být bezpečný.

Postavil jsem ten závěr na nepřítomnosti pádu: balík 1.0.0.63 běžel na PPF DEV
měsíc úplně bez deklarací (ověřeno v git historii, `git show e252e87^:…`).
To ale nedokazuje, že to je správně — jen že se to zatím neprojevilo.

**Nové jednotné pravidlo: deklaruje se každý použitý parametr, bez rozlišení.**

Nejlepší dostupné vysvětlení rozdílu: prostředí doplní parametry samo jen flow,
které nedeklaruje **žádný**; jakmile jeden přibude, bere se deklarace jako
úplný výčet. Nedoloženo do konce — a právě proto se deklarují všechny, ať na
tom nestojí nic.

### Kde to bylo špatně navržené

Deklaraci uměl doplnit jen `build_export_flow.py`. Ostatní generátory o ní
nevěděly — proto se to muselo objevit dvakrát. Nově to dělá **jedno místo**:
`dorovnej_deklarace_parametru()` v `build_app.py`, která běží nad **všemi**
flow v balíku, ať už je vyrobil kdokoli. Do balíku 72 doplnila 12 chybějících
deklarací v obou MapaPublish flow.

Funkce zároveň nahradila `zbav_flow_vychozich_hodnot()` — zahazování
`defaultValue` dělá dál (export ze Studia nese adresu vývojového webu), ale
je to teď vedlejší efekt jedné funkce místo dvou konkurenčních pravidel.

### Brána

`deklarace_parametru` už nerozlišuje výraz od parametru konektoru;
`_parametry_ve_vyrazech()` zrušena. **343 kontrol.** Zpětný důkaz: spuštěná
na vadném balíku 70 vypíše **24 nálezů**.

Skill `power-Apps-skill` opraven včetně toho mylného mezikroku — nechal jsem
ho tam jako varování, protože vypadal přesvědčivě.

## Nález: chybějící deklarace parametru shodila ExportFlow (31.08.2026 14:10)

Import 1.0.0.69 na PPF DEV **appku rozběhl** — strom ukázal 6 agend,
44 procesů, 249 dílčích a 47 aktivit, což přesně sedí na GUIDy z PPF DEV.
Napojení přes proměnné tedy funguje a hlavní cíl F9 platí.

Padalo ale volání flow. Appka hlásila jen
`ExportFlow.Run failed: 502 BadGateway … NoResponse`, run history řekla
pravdu:

```
InvalidTemplate. Unable to process template language expressions in action
'Cesta_webu' inputs at line '0' and column '0': The workflow parameter
'Procesni mapa - web (mpsv_procesnimapaSite)' is not found.
```

### Proč se to neprojevilo dřív

Rozhoduje, **kde** se `parameters('…')` použije:

| použití | deklarace v `definition.parameters` | doloženo |
|---|---|---|
| parametr konektoru (`inputs/parameters/dataset`) | není potřeba | MapaPublish běží týdny bez ní |
| ve výrazu (Compose, podmínka, Select) | **povinná** | pád výše |

`Cesta_webu` a `Adresa` jsou **první výrazové použití** v celém projektu
a přinesl je F9 krok 4 (adresa mapy z ExportFlow). Do té doby se parametr
objevoval jen jako `dataset` u SharePoint akcí, kde si ho runtime dosadí sám.
Proto stejný tvar roky procházel a spadl až teď.

Rozbor balíku ukázal, že deklaraci nemá `ExportFlow`, `MapaPublishFlow` ani
`MapaPublishScheduled` — u posledních dvou to ale **nevadí**, parametry mají
jen v konektorech. Vada je tedy přesně jedna, v jednom flow.

### Oprava

`build_export_flow.py` kopíroval `parameters` ze zdrojového `MapaPublishFlow`,
které je nemá. Nově doplní deklaraci proměnné webu vždy (`parametry()`).

Tvar se **neuhádl, opsal** — z deklarace, kterou do `AktualizaceKratkehoNazvu`
dopsal designer a která v provozu funguje. Skládá ji `ep.deklarace()`:

```json
{"type": "String",
 "metadata": {"schemaName": "mpsv_procesnimapaSite",
              "description": "Adresa SharePoint webu s rejstrikem."}}
```

`metadata.schemaName` je ta podstatná část — je to vazba na proměnnou
prostředí. Bez ní by parametr existoval, ale hodnota by do něj nedorazila;
byla by to druhá cesta k témuž selhání, jen o kolo později.

**`defaultValue` se ZÁMĚRNĚ nedoplňuje.** Hodnota patří do prostředí,
kde ji obsluha vyplní při importu — zapečená adresa je přesně to, co F9
rušil. (Prázdný řetězec je navíc zakázaný: s ním selže import na 29 %,
ověřeno v PPF na jiném projektu.)

### Brána: `deklarace_parametru` v check_solution.py

Žádná z jedenácti bran tohle nechytala — `check_export_flow` kontroluje
kontrakt akcí, ne deklarace. Nová kontrola projde **všechna** flow v balíku
a hlídá:

1. každý parametr použitý **ve výrazu** je v `definition.parameters`,
2. jeho deklarace má `metadata.schemaName` navázané na tu proměnnou,
3. žádná deklarace nemá `defaultValue: ""`.

Rozlišení „výraz vs. parametr konektoru" dělá `_parametry_ve_vyrazech()` —
kdyby bránu neuměla rozlišit, musely by se zbytečně deklarovat i parametry
v MapaPublish flow.

**Zpětný důkaz:** brána spuštěná na balíku 1.0.0.69 nález vypíše přesně tak,
jak ho ukázala run history.

**Mutačně ověřeno 4/4** (`src/mutace_parametry.py`): smazaná deklarace,
deklarace bez `metadata`, `schemaName` na jinou proměnnou, prázdný
`defaultValue`. Skript má i pojistku proti mutaci, která se do definice
netrefí.

### Co z toho platí obecně

Patří to do skillu `power-Apps-skill` jako doplněk pravidla o
`definition.parameters`: dosud tam stálo „nech je, jak přišly z exportu".
Nově je doložené i **proč** — a že rozhoduje způsob použití, ne to, jestli
flow zapisuje.

## Ověřeno na PPF DEV z balíku 1.0.0.70 (31.08.2026 14:33)

Prošlo: **export do Wordu i Excelu**, **zkracování dlouhého názvu** (a tím
i GUID listu Aktivity — je to jediné místo v balíku, kde je natvrdo),
**Vykonává útvar** se plní (sedmá proměnná z F9).

Neprošlo: **MapaPublishFlow** (viz nález výše) a **aktivita ve více dílčích
procesech** (viz níže).

## Aktivita ve více dílčích procesech na Přehledu (31.08.2026 14:45)

Nebyla to chyba kódu — Přehled ukazoval **jen primární zařazení** a bylo to
tak i okomentované v `scr_Dashboard.pa.yaml`. HTML mapa M:N ukazuje správně
odjakživa, takže test #4 z `app_navrh.md` („v obou větvích **mapy**")
formálně procházel. Očekávání uživatele ale míří na Přehled, kde se pracuje.

**Rozhodnutí zadavatele (31.08.2026 14:45): ukázat všude, počty jen primární.**

- Aktivita se objeví pod **každým** svým dílčím procesem.
- Vedlejší řádek je odlišený **značkou `↳`** ve volném slotu rozbalovací
  šipky (u aktivit je prázdný) a **ztlumenou barvou názvu**.
- `aktC`/`aktS` u vedlejších řádků jsou **0**, takže sloupec POLOŽKY a čísla
  u agend a procesů dál znamenají **počet aktivit, ne počet zařazení** —
  součet sedí na dlaždici AKTIVITY.
- **Ikona smazání je na vedlejším řádku schovaná.** Smazala by celou
  aktivitu, ne tu jednu vazbu; vazby se ruší v detailu.

Primární řádky se staví beze změny — přidaný `ForAll` jde jen přes vazby
s `primarni = "ne"`, kterých je z podstaty málo, takže to nepřidává
per-row scan nad celým seznamem.

**Značka je Label se znakem, ne `Classic/Icon`.** Ikonový výčet Power Apps
se z YAML lokálně neověří ničím a chybná hodnota se pozná až ve Studiu;
appka jich používá jen čtyři a žádná se sem nehodí. Rozbalovací šipky `▸ ▾`
o řádek výš jsou kreslené stejně.

**Číselník (záložka Editace) zůstává na primárním zařazení** — je to
editační seznam, kde se spravuje hlavní zařazení, a vedlejší se přidávají
v detailu. Kdyby to mělo být i tam, je to stejný zásah.

## Balíky 1.0.0.69 a 1.0.0.70 pro PPF DEV (31.08.2026 11:20)

GUID listu Aktivity na PPF DEV dodán v 11:08:
`9dfbb5a1-65a6-4fd4-b9f9-fdd35fa246cd`, web
`/sites/DigiData_D/testovaci_subsajta/procesnimapa`. Tím padla jediná
překážka F9 kroku 5.

**Dva balíky z jednoho zdroje se liší jen tímhle GUIDem** a jinak ničím:

| balík | list Aktivity | pro | stav |
|---|---|---|---|
| `deploy/procesnimapa_1_0_0_68.zip` | `b1daaa38-…` | MPSV | **nenasazovat** — vada ExportFlow; drží se jen jako základna pro build |
| ~~`1_0_0_69`~~ | `9dfbb5a1-…` | PPF DEV | smazaný — táž vada, nasazen a spadl |
| `deploy/procesnimapa_1_0_0_70.zip` | `9dfbb5a1-…` | PPF DEV | **nasazený a ověřený** (mapa se zobrazila) |
| `deploy/procesnimapa_1_0_0_71.zip` | `b1daaa38-…` | MPSV | čeká na import (F9 krok 6) |

Verze jsou dvě, ne jedna, protože `build_app.py` odvozuje jméno souboru
z verze — stejná verze by druhý balík přepsala. Pro obě prostředí jde
o upgrade (MPSV má 1.0.0.65, PPF DEV 1.0.0.63).

Postaveno z 68 přes `--bez-pac` (na tomhle stroji `pac` není a 68 je zabalený
z YAML): `build_flow.py --list-aktivity <GUID PPF>` a pak
`build_app.py --bez-pac --verze 1.0.0.69`. Ostatní tři flow se
nepřegenerovávaly — web berou z proměnné, takže jsou na prostředí nezávislé.
Ověřeno čtením obou zipů: v 69 je GUID PPF jen ve `Workflows/Aktualizace…`,
GUID MPSV zůstává v `customizations.xml` jako `name` u overridu, což je
záměrný tvar podle produkčních vzorů (`name` drží původní hodnotu,
`environmentVariableName` říká, co ji přebije).

### Co ověřit po importu

1. **Environment variables — všech sedm** (`mpsv_procesnimapaSite` +
   šest listů). Vyplnit PŘED zapnutím flow; 28.08. se stalo, že se hodnota
   `mpsv_listAgendy` nepropsala.
2. Appku otevřít ve Studiu → **mikro-změna → Save → Publish**.
3. **Flow ručně zapnout** — import stav zapnutí nemění.
4. Spustit appku: strom se načte, číselník i vazby ukazují data, tlačítko
   mapy mapu otevře (ne stáhne), export do Wordu i Excelu stáhne soubor.

**Neověřené, ukáže se až tady:** že náhled mapy funguje i bez `viewid`
v adrese. Kdyby SharePoint místo zobrazení soubor stáhl, je to ono — řeší se
dotažením GUID výchozího zobrazení knihovny, z proměnné, ne natvrdo.

Když appka data nenačte, rozliší se to pohledem do panelu Data: nevyplněná
proměnná vs. špatný tvar overridu.

**Krok 6 (zpět na MPSV)** čeká na zelený výsledek tady. Balík se postaví
stejně, jen s GUIDem MPSV a jako 1.0.0.70.

## F10 krok 1 hotový — HistorieKodu a sloupce nástupnictví (31.08.2026 11:20)

Datová vrstva pro variantu C stojí. Appka ji zatím nepoužívá, takže se to
**neprojevilo v balíku 69** a import na PPF DEV to nijak nezdrží.

- **Nový list `HistorieKodu`** ve `src/schema.json` — `Title` (uzavřený kód,
  indexovaný), `uroven` (Choice agenda/proces/dilci_proces/aktivita,
  indexovaný), `nazev`, `nastupce_kod` (prázdné = zrušeno bez náhrady),
  `duvod` (Note), `datum` (DateTime), `kdo`.
- **`puvodni_kod`** (Text 20) do `Procesy`, `DilciProcesy` a `Aktivity` —
  protějšek k `nastupce_kod`. `Agendy` ho nemají: agenda nemá rodiče, takže
  z předchůdce nevzniká.
- Žádný druhý `stav` se nezavádí. Uzavřenost je dána tím, že kód **je**
  v `HistorieKodu`; sloupec `stav` u aktivit zůstává schvalovací.

### Co bylo potřeba dotáhnout v generátorech

`HistorieKodu` je první list, který **nemá zdrojová data** — zakládá se
prázdný a plní ho až aplikace. Obojí to rozbíjelo:

- `check_schema.py` sahal na `datadir / lst["csv"]` bez ohledu na to, jestli
  zdroj existuje. Nově list s `csv: null` přeskočí datové kontroly, ale tvar
  se ověřuje dál (Title jako klíč, `default_sort`, a navíc chyba, kdyby
  takový list měl sloupec čerpající z CSV). Kontrola řazení se kvůli tomu
  vytáhla z těla smyčky do `zkontroluj_razeni()`.
- `make_import.py` list bez `csv` přeskakuje — do importního skriptu nepatří.

`make_setup.py` ani `check_import.js` se měnit nemusely, jsou schéma-řízené.

### Brána: kontroly jsou vyjmenované schválně

`check_setup.js` odvozuje očekávání ze `schema.json`, takže odebraný sloupec
by očekávání jen **snížil** a test by prošel. Kontroly pro `HistorieKodu`
a `puvodni_kod` proto sloupce **vyjmenovávají**. Číselník úrovní se čte
z odeslaného `SchemaXml` a hledá se podle obsahu, ne podle jména — sloupec
`uroven` má i list `Útvary`.

**Mutačně ověřeno, 4/4:** odebrání `nastupce_kod`, odebrání `uroven`,
odebrání `Aktivity.puvodni_kod` a odebrání celého listu — každá shodí bránu.

### Ještě není promítnuto do nasazovací složky

`deploy/mpsv/01_zaloz_listy.js` a `02_import_dat.js` jsou pořád ze schématu
bez `HistorieKodu` (generuje je `src/make_deploy_mpsv.py` a je navázaná na
balík 1.0.0.65). **Přegeneruje se až s F10 krokem 2**, kdy appka nový list
opravdu začne používat — dřív by se na tenanty zakládal list, do kterého
nikdo nepíše. `src/setup_sharepoint.js`, `src/import_data.js`
a `deploy/sharepoint_schema.md` už aktuální jsou.

### Brány po F10/1 a balíku 70

`check_solution` **304** · `check_mapa_flow` 139 · `check_export_flow` 124 ·
`check_flow` · `check_app` · `check_env` · `check_schema` (7 listů,
44 sloupců) · `check_mapa_html` 31 · `check_mapa_beh` 25 ·
`check_setup.js` (+13 nových) · `check_import.js` — vše zelené.
Mutačně: `mutace_parametry` 4/4, `mutace_napojeni` 5/5,
`mutace_export_mapa` 7/7, `check_setup.js` 4/4.

## F10 a F11 zadány — rozhodnutí z 30.08.2026 18:08

Podrobné kroky, testy a rizika jsou v `PLAN.md`. Sem jen to, co se rozhodlo:

- **Přesun položky pod jiného rodiče = zánik a vznik (varianta C).** Kód se
  nikdy nepřepisuje: starý se uzavře do listu `HistorieKodu`, nový vznikne pod
  novým rodičem a obě strany na sebe ukazují. Uzavřený kód se nerecykluje.
  Cena: přesun procesu uzavře celý podstrom, protože prefix se mění všem.
- **Záloha a import zůstávají oddělené.** Import = pravý `.xlsx` se šablonou
  formátovanou jako Tabulka, čtený konektorem Excel Online (Business).
  Záloha = JSON snímek plánovaným flow. Sdílí se tvar tabulky a náhledový
  engine, ne formát a ne operace. Pořadí: záloha → import → restore.

### Nález při rozboru: přesun aktivity dnes nechává starý kód

Appka přesun o úroveň níž už umí a řeší ho tiše variantou A. `drp_Dilci` je
editovatelný i u existující aktivity (`scr_Detail.pa.yaml:235`), při uložení se
přepíše `dilci_proces_kod` a přesype vazební tabulka (řádky 712–741), ale
`varNovyKod` je u existujícího záznamu `varAktivita.Title` (řádek 698) — **kód
zůstane starý a prefix od té chvíle ukazuje jinam než rodič.** Tooltip u toho
dropdownu přitom slibuje „určuje kód aktivity".

Zjištěno čtením YAML, ne během appky. Opraví to F10 krok 2 — je to zároveň
nejmenší instance téže operace, takže ověří návrh dřív než kaskáda nad procesem.

## F9 — přenositelnost mezi tenanty (30.08.2026)

**Zadání:** testovat se bude dál i na PPF DEV, aniž by se střídavými importy
rozbíjelo to, co běží na druhém tenantu. Plán je v `PLAN.md` sekce F9.

Do 1.0.0.66 by import balíku z jednoho tenantu na druhý appku rozbil: napojení
na sedm zdrojů je zapsané natvrdo v `<ConnectionReferences>`, takže by appka
ukazovala na listy, které tam nejsou, a `App.OnStart` by spadl na prvním
`ClearCollect`. Od 1.0.0.67 si napojení bere z proměnných prostředí.

### Co se změnilo

**Napojení appky přes proměnné** (`build_app.py`, funkce
`napoj_appku_na_promenne`). Klíč datasetu má tvar `<url>_<schemaname>`, uvnitř
`datasetOverride` a u každého listu `tableNameOverride` — tvar 1:1 podle
produkčních vzorů `MiddleOfficeParametrizace` a `VendorManagement`.

Klíčové zjištění, kvůli kterému to šlo udělat teď a ne až po dalším kole se
Studiem: **overidy žijí jen v `customizations.xml`**. V `.msapp` zůstává
`DataSources.json` na čisté URL a holém GUIDu i ve vzorech. Odpadl tím hlavní
důvod, proč se F8/5 od 28.08. odkládalo.

**Sedmá proměnná** `mpsv_listUtvary` — appka má napojených sedm zdrojů,
proměnné byly jen pro pět. `Útvary` používá jen appka, ne flow.

**Knihovna `Dokumenty` odebrána z appky.** Byla v napojení od založení appky
ve Studiu a žádný vzorec ji nepoužíval. Nechat ji tam by znamenalo dát jí
vlastní proměnnou — v jednom bloku `dataSets` nesmí zůstat zdroj bez overridu.

**Adresa mapy se už nepíše do kódu.** Appka si o ni řekne `ExportFlow`
smluvenou hodnotou vstupu `__mapa__`; flow ji složí z proměnné webu, takže je
vždy z toho prostředí, kde appka běží. Schéma volání (pošli text → dostaň
adresu) se tím nemění, takže flow nepotřebuje novou registraci ve Studiu.
Volá se až z `OnSelect` tlačítka mapy a výsledek se drží v `varMapaUrl`, takže
start appky se nezdrží a druhé kliknutí flow už nevolá.

Zápis souboru je kvůli tomu v podmínce `Ulozeni` — v režimu mapy se provést
nesmí, jinak by export přepsal samotnou mapu.

### Dvě opravy, na které se přišlo cestou

- `build_mapa_flow.py` bral **první** connection reference místo SharePointové.
  Fungovalo to jen díky pořadí klíčů; v exportu z MPSV stojí první `logicflows`
  s prázdným `dataSets`, takže build spadl na „čekám právě jeden web, appka
  jich má 0". Obě `nacti_*` funkce teď hledají podle `shared_sharepointonline`.
- Tytéž funkce umí i klíč se suffixem (berou `datasetOverride.name`), jinak by
  z balíku, který přes proměnné jednou prošel, nešlo stavět podruhé. Ověřeno
  druhým průchodem: suffix se nenabaluje.

### Brány

| brána | stav | co přibylo |
|---|---|---|
| `check_solution` | 300 kontrol | `napojeni_appky`: každý zdroj má override, proměnná je deklarovaná, klíč má suffix, nezůstal zdroj bez overridu |
| `check_export_flow` | 123 kontrol | `vyznam_mapa`: vstup `__mapa__` vrátí odkaz na náhled knihovny, ne na `.html`; export tím neutrpěl |
| `check_env` | zelená | `POCET` 7; LISTY flow smí být podmnožina `LIST_PROMENNA` (Útvary má jen appka) |
| `check_app`, `check_flow`, `check_mapa_flow` | zelené | beze změny |

**Mutačně ověřeno, 11 mutací:** `src/mutace_napojeni.py` 5/5 (chybějící
override, nedeklarovaná proměnná, klíč bez suffixu, zdroj navíc bez overridu,
rozejitý GUID) a `src/mutace_export_mapa.py` 6/6 (přímý odkaz na `.html`,
neenkódovaná cesta, špatný `parent`, zápis mimo podmínku, podmínka nevylučující
režim mapy, běžný export vracející adresu mapy).

### Co zůstane ruční i po F9

- **GUID listu Aktivity** — parametr `--list-aktivity`, tedy dva balíky
  z jednoho zdroje. Z proměnné to nejde.
- **Vyplnění proměnných** při prvním importu do prostředí (nově sedm místo
  šesti). Prostředí si je pak drží.
- **Mikro-změna + Save + Publish** ve Studiu po importu a **ruční zapnutí flow**.

### Enkódování adresy mapy dorovnáno na ověřený tvar — 1.0.0.68 (30.08.2026 17:50)

Riziko zapsané u balíku 67 („brána ověří tvar, ne chování SharePointu") šlo
zavřít offline, protože zlatý vzorek v repu je: adresa z **reálného kliknutí**
na mapu v knihovně PPF DEV z 20.08.2026, zapečená tehdy do `App.OnStart`.

`encodeUriComponent` nechává `-`, `_` a `.` být — jsou to unreserved znaky —
zatímco SharePoint je v odkazu píše jako `%2D`, `%5F` a `%2E`. Skládaná adresa
se tím od ověřené lišila. `enkoduj_cestu()` v `build_export_flow.py` teď
náhrady doplňuje; dělají se až po enkódování a žádná nevytvoří znak, který by
chytla další, takže na pořadí nezáleží.

**Nová kontrola `vyznam_mapa_vzorek`** složí adresu pro web PPF DEV a porovná
ji **znak po znaku** s tou ověřenou (bez `viewid` — je to GUID zobrazení,
v cizím prostředí neznámý; náhled si bez něj vezme výchozí). Kontroly tvaru
projdou i adrese, která se liší jen enkódováním — a právě tím se pozná, jestli
SharePoint mapu zobrazí, nebo pošle do Downloads.

### Nález: brána měřila adresu proti řetězci, který v provozu nevznikne

Při psaní vzorkového testu se ukázalo, že `nacti_web` v `check_export_flow.py`
vrací **suffixovaný klíč** datasetu (`…/procesnimapaApk_mpsv_procesnimapaSite`)
a dosazuje ho do mini-interpretu jako hodnotu proměnné webu. Adresa se pak
měřila proti sobě samé: `startswith(web)` prošlo, protože se suffix propsal do
obou stran. Táž chyba byla v `adresa_webu` v `check_solution.py` (tam bez
následku — bere se z ní jen hostname). Obě teď čtou `datasetOverride.name`,
stejně jako opravená `nacti_metadata` v `build_mapa_flow.py`.

Balík 67 tím nebyl vadný — vadný byl důkaz o něm.

**Mutační skript dostal pojistku:** mutace, která se do definice netrefí
(změní se tvar výrazu a `str.replace` přestane nacházet), se dřív tvářila jako
platný test. `uprav_flow` teď porovná definici před a po a na nezměněném
balíku skončí chybou. Dvě z existujících mutací adresu hledaly řetězcem, který
se doplněním náhrad změnil.

### Brány po 1.0.0.68

`check_export_flow` **124** (nová `vyznam_mapa_vzorek`) · `check_solution` 300 ·
`check_mapa_flow` 139 · `check_flow` 26 · `check_app` · `check_env` — vše zelené.
Mutačně: `mutace_export_mapa` **7/7** (přibyla „enkódování bez náhrad"),
`mutace_napojeni` 5/5.

**Oprava 30.08.2026 17:55:** `check_mapa_flow.py` měl `--base` natvrdo na
`deploy/procesnimapa_1_0_0_63.zip`, což je balík, který v `deploy/` už není —
brána spuštěná bez explicitního `--base` (tedy tak, jak ji uvádí HANDOVER)
padala na `FileNotFoundError`. Default nyní míří na aktuální základnu
`input/procesnimapa_1_0_0_66.zip`; proti ní i proti 67 dá týchž 139 kontrol.

### OVĚŘENO 31.08.2026 14:13 — `viewid` v adrese chybět smí

Mapa se na PPF DEV z balíku 1.0.0.70 **zobrazila správně**, ne stáhla. Náhled
si bez `viewid` vezme výchozí zobrazení knihovny, jak se předpokládalo. GUID
výchozího zobrazení tedy dotahovat nemusíme a riziko zapsané u balíků 67/68
padá.

Zároveň tím padlo druhé neověřené tvrzení: **deklarace parametru bez
`defaultValue` pro výrazové použití stačí** — hodnota přišla z Current Value.
Balík tedy nemusí vézt adresu žádného tenantu ani jako záložní hodnotu.
Zapsáno do skillu `power-Apps-skill`.
## Nová základna: 1.0.0.66, export z běžícího MPSV (30.08.2026)

Uživatel dodal `procesnimapa_1_0_0_66.zip` — export solution z MPSV, kde
appka běží. **Všechny další úpravy vycházejí z ní**, uloženo jako
`input/procesnimapa_1_0_0_66.zip` (dosavadní základ 1.0.0.57 je v `input/archiv/`).

```powershell
& $py src/build_app.py --solution input/procesnimapa_1_0_0_66.zip --verze 1.0.0.67
```

Co export dokládá:

- **`ExportFlow` je zaregistrovaný jako datový zdroj appky** —
  `FlowNameId 4b36e7da-c006-4859-af44-e22c8a790738`, tedy **stejné ID jako
  v mém balíku 1.0.0.65**. MPSV ID z importované solution převzalo, nepřidělilo
  vlastní; dvoukolový postup (balík s flow → Add data → druhý balík) tady
  vyšel na jedno kolo. Registrované jsou obě flow volané z appky
  (`MapaPublishFlow` i `ExportFlow`).
- Appka byla ve Studiu uložena 28.08. 22:46 (`LastSavedDateTimeUTC`), takže
  mikro-změna + Save + Publish po importu proběhly.
- `packed.json` je pryč a `Controls/*.json` jsou dogenerované Studiem —
  potvrzení, že z YAML zabalený balík se ve Studiu opravdu doauthoroval.
  **Důsledek: z téhle základny nejde stavět přes `--bez-pac`** (ta cesta
  vyžaduje `LoadFromYaml=true`); build hlásí jasnou chybu, `pac` si najde sám
  ve VS Code rozšíření.

### Jedna past, kterou export přinesl — a je opravená

Flow `AktualizaceKratkehoNazvu` mělo v definici
`parameters.<proměnná>.defaultValue` s adresou webu MPSV. Designer ji tam
dopíše aktuální hodnotou z prostředí, jakmile se flow jednou uloží — a právě
tohle flow se na MPSV 28.08. v designeru řešilo. Ostatní tři flow ji nemají.

Proč to vadí: na dalším tenantu by flow s nevyplněnou proměnnou tiše běželo
proti webu MPSV, místo aby selhalo. Je to tentýž režim selhání, kvůli kterému
se z balíku vynechává `<defaultvalue>` v definicích proměnných — jen o patro
níž, v definici flow.

Chytila to brána `check_solution` (kontrola `adresy_ve_flow`, 278 kontrol,
1 chyba). Oprava je v `build_app.py` — funkce `zbav_flow_vychozich_hodnot()`
volaná z `dokonci()` maže `defaultValue` u všech nesystémových parametrů
definic flow a vypisuje, které to byly. `$authentication` a `$connections`
se nechávají, jejich prázdný `defaultValue` je součást tvaru definice.

### Brány nad zkušebním buildem 1.0.0.67 z nové základny

`check_app` · `check_env` · `check_solution` 278 · `check_flow` 26 ·
`check_mapa_flow` 139 · `check_export_flow` 110 — vše zelené. Balík se
nikam nenasazoval a je smazaný; nasazená verze zůstává **1.0.0.65**.
Přegeneruje se jedním příkazem výše.

## Jak dopadl večer 28.08.2026 — tři nezávislé pasti

Nasazení na MPSV (první čisté prostředí) odhalilo tři věci, které na PPF DEV
nešlo najít. Balík je **1.0.0.65**.

### 1. PatchItem nesnese list z proměnné (1.0.0.65)

Zapnutí `AktualizaceKratkehoNazvu` končilo na `OpenApiOperationParameter-
ValidationFailed` — *„The API operation 'PatchItem' is missing required
property 'item'"*. Konektor si schéma těla odvozuje z konkrétního listu; při
runtime výrazu se nerozbalí a rozložené klíče `item/<sloupec>` přestanou platit.

Původní varování skillu tedy platilo a ranní „vyvrácení" bylo mylné: rozbor
produkčních balíků ukázal `table` z proměnné u `PatchItem`, ale nerozlišil,
jestli se tělo posílá **rozložené**, nebo jako celý objekt. Ověření na PPF DEV
bylo neplatné z druhého důvodu — flow tam bylo zapnuté z dřívějška a **import
stav zapnutí nemění**, takže se aktivace vůbec nespouštěla.

Oprava: celé flow drží **GUID listu Aktivity** (trigger, čtení i zápis),
`dataset` zůstává z proměnné. Zapsáno i do skillu.

### 2. Povinná pole vs. přepis novějších dat (1.0.0.64, platí dál)

`build_flow.py` povinné sloupce do `PatchItem` vkládal (bez nich nejde flow
aktivovat), `build_app.py` je zase odebíral (ze snímku triggeru by přepsaly
novější editaci) — a běží poslední, takže v balíku nebyly. Řeší to akce
`Nacti_aktivitu` (`GetItem` podle ID z triggeru): pole se posílají, ale ze
stavu čteného těsně před zápisem.

### 3. Přenos appky = přepojit VŠECHNY datové zdroje ručně

Po importu měla appka rozbitý jediný zdroj (`Agendy`, červený křížek v panelu
Data) a nenačetla **nic** — `App.OnStart` začíná `ClearCollect(colAgendy, …)`
a chyba v něm shodí i zbylých šest zdrojů. Vypadá to jako chyba appky, přitom
je to jedno nepřepojené napojení.

Řešením bylo **napojit znovu všechna data**, ne jen ten jeden zdroj. Tím je
doložené, proč má smysl `F8/5` z `PLAN.md` (napojení appky přes
`datasetOverride` / `tableNameOverride`) — odstranil by celý tenhle krok.

**Vedlejší zjištění:** hodnota proměnné prostředí se při importu nemusí uložit
(u `mpsv_listAgendy` se nepropsala). Definice je přitom bajtově stejná jako
u ostatních pěti. Doplnit ručně v Řešení → Proměnné prostředí — a udělat to
**před** zapínáním flow, protože proměnná bez hodnoty zapnutí shodí a hláška
o ní nemluví.

### Brány nad 1.0.0.65

`check_flow` 26 · `check_solution` 278 · `check_env` · `check_app` ·
`check_mapa_flow` 139 · `check_export_flow` 110 — vše zelené, mutačně ověřeno
šesti zásahy.

## Stav k 28.08.2026 — hotovo a ověřeno

**`deploy/procesnimapa_1_0_0_63.zip` běží na PPF DEV, potvrzeno uživatelem.**
Kopie balíku je i v `deploy/mpsv/`.

Dnes se udělaly dvě věci, obě uzavřené:

### 1. Notifikace se zkrátily

`Notify` bez třetího argumentu svítí výchozích deset vteřin a potvrzení tím
překážela. Všech 27 volání dostalo dobu zobrazení: potvrzení a varování
**3000 ms**, chyby **4000 ms**. Obě hodnoty drží `App.OnStart`
(`varNotifyMs`, `varNotifyChybaMs`), takže se ladí z jednoho místa.

Cesta k tomu byla 1 s → (chyby 2 s) → 3 s / 4 s podle toho, jak to vypadalo
v provozu. Kdyby se to mělo ladit dál, jsou to dvě čísla v `App.OnStart`,
nic víc.

### 2. Flow se převedly na proměnné prostředí

**Příčina pádu importu na MPSV:** ve všech čtyřech flow byla adresa
vývojového webu PPF a GUIDy vývojových listů natvrdo — 16 míst. Na cizím
tenantu jsou takové akce neplatné, flow nejde zapnout a designer list ani
nenabídne k přepnutí. Appka je jinde: váže se přes connection reference,
kterou průvodce importem přepojí sám, proto ta šla.

Balík deklaruje šest proměnných prostředí (`mpsv_procesnimapaSite` a pět
listových) a **v definicích flow není ani jedna adresa nebo GUID**.

### 3. Největší stupeň písma vyrostl o dva body

`varFs` má nově hodnoty **-4 / -2 / +2** (dřív -4 / -2 / 0), takže krok mezi
středním a největším stupněm je 4 body místo dvou. Měnila se tři místa na
obrazovku; všechny velikosti, výšky řádků galerií i šířka sloupce s kódem
jsou psané jako `N + varFs` nebo `N + varFs * k`, takže se přizpůsobily samy.

| při největším stupni | dřív | nově |
|---|---|---|
| řádek stromu na Přehledu | 40 px | 48 px |
| řádek číselníku | 44 px | 52 px |
| řádek vazeb | 64 px | 72 px |
| sloupec s kódem | 130 px | 154 px |

Glyfy `A` na samotných tlačítkách (9 / 11 / 13 b) zůstaly — ukazují poměr,
ne absolutní velikost.

## Oprava tvrzení ve skillu — nejcennější zjištění dne

Nejdřív jsem napsal, že převést na proměnné jdou jen tři flow ze čtyř: skill
`power-Apps-skill` tvrdí, že zápisová akce ani trigger nad listem runtime
výraz nesnesou. Na základě toho už padlo rozhodnutí čtvrté flow zrušit
a zkracování názvu přepsat do Power Fx.

Rozbor šesti produkčních balíků PPF (repo
`luboszprahy/powerApps-vzory-aplikaci-pro-claude`, dodal uživatel) to
vyvrátil:

| parametr z proměnné | operace | v kolika balících |
|---|---|---|
| `table` | `PatchItem` | 4 |
| `table` | `PostItem` | 3 |
| `table` | `GetOnNewItems` (trigger nad listem) | 3 |
| `dataset` | `CreateFile` | 2 |
| `dataset` | `PatchItem` | 6 |

Rozhodující je `FloorPlan_1_0_0_19` — balík, ze kterého to varování ve skillu
pochází. Má `dataset` z proměnné, ale **`table` natvrdo**; právě jeho
přepnutím ve verzi 1.0.0.21 to tehdy spadlo.

**Nerozhoduje druh akce, ale typ proměnné.** Textová (`100000000`) nestačí;
funguje datasetová (`100000004`) s `apiid` konektoru a `parameterkey`, u listu
navíc `parentdefinitionid` na proměnnou webu. Ta dvojice je zároveň důvod,
proč průvodce importem umí nabídnout výběr webu a pak rozbalovátko jeho listů
místo textového pole na GUID.

Po opravě se rozhodnutí obrátilo: čtvrté flow zůstalo a jen se převedlo jako
ostatní. Do appky se kvůli němu nesahalo.

**Ověřeno v provozu 28.08.2026** na PPF DEV: všechna čtyři flow šla zapnout
a proběhla, včetně triggeru `GetOnUpdatedItems` nad listem z proměnné,
`PatchItem` s rozloženými klíči `item/<sloupec>` a `CreateFile` s datasetem
z proměnné. Zapsáno do skillu jako doložené provozem, ne odvozené ze vzorů.

## Proč definice nemají výchozí hodnotu

Kdyby ji měly, průvodce by na MPSV předvyplnil adresu webu PPF a import by
tiše prošel se špatným napojením — tedy přesně původní chyba, jen přesunutá
o patro dál. Bez ní se musí vyplnit vědomě. Prostředí si hodnotu po prvním
vyplnění drží, další import se neptá. Z balíku se zároveň odstraňuje
`environmentvariablevalues.json`, aby import nepřepisoval nastavení cíle.

## Brány

Jedenáct zeleně nad 1.0.0.63.

| brána | stav | co přibylo |
|---|---|---|
| `check_app` | zelená | `kontrola_notify`, 3 mutace |
| `check_env` | **nová** | tvar definic proměnných proti vzoru Clearstream |
| `check_solution` | 270 kontrol | `adresy_ve_flow` nově absolutní (žádná adresa ve flow), `promenne_ve_flow` nová; **6 mutací** |
| `check_flow` | 18 | tři kontroly obrácené — web i list musí být proměnná |
| `check_mapa_flow` | 139 | `table` proti proměnné, ne proti GUID |
| `check_export_flow` | 110 | dataset proti proměnné; interpret umí `parameters()` |
| `check_mapa_html` / `check_mapa_beh` | 31 / 25 | beze změny |
| `check_setup.js` / `check_import.js` | zelené | beze změny |

Šest mutací nad `check_solution` je to podstatné: vrácená adresa, vrácený GUID
listu (adresu neobsahuje, první kontrola by ho minula), chybějící definice,
`environmentvariablevalues.json` v balíku, odkaz na nedeklarovanou proměnnou
a adresa na cizí doméně. Všechny chycené.

## Pořadí buildu — zapsáno, protože jsem na něm sám najel

`build_app.py` musí běžet **jako poslední**. Odebírá z `PatchItem` pole
`item/nazev` a `item/dilci_proces_kod`; kdyby běžel první, `build_flow.py` by
je vrátil a flow by přepisovalo novější data starým snímkem z triggeru —
tiše, bez chyby. Pracovní kopie navíc nesmí ležet v `runs/app_build/`, tu
`build_app.py` na začátku maže. Celé v `HANDOVER.md` §5.

Poznámka k prostředí: na stroji 5CG5210MB2 nebyl `.venv` ani `pac`. Venv se
založil (`pyyaml`, `openpyxl`), `pac` potřeba není — staví se přes
`build_app.py --bez-pac` z posledního vlastního balíku. Proti exportu ze
Studia to nejde, ten YAML zdroje nenese.

## Otevřené

- **N-04** z auditu: `Download()` v appce vložené jako webpart na SharePoint
  stránku. Ověří se až v provozu.
- **F8/5 v `PLAN.md`** (odloženo schválně): převést na proměnné i napojení
  canvas appky přes `datasetOverride` / `tableNameOverride` — dělá to
  VendorManagement i Průvodní list. Tím by z přenosu na další tenant zmizel
  i ruční krok ve Studiu. Odloženo bylo proto, že appku šlo napojit ručně,
  skill má doložené, že proměnná bez hodnoty shodí napojení celé connection,
  a sahá se tím do `.msapp`, což offline neověřím. Po dnešním testu ale víme,
  že mechanismus drží — je to reálná varianta, až bude chuť.

## Co dál, až bude MPSV nasazené

`PLAN.md` sekce „Náměty na rozšíření": osm námětů, doporučené pořadí
**R-1 → R-3 → R-2 → R-8**. Nic z toho není zadané.

## Konec dne 25.08.2026 — projekt uklizený, appka 1.0.0.61 v provozu

**Hotovo dnes:** export přehledu do Wordu a Excelu (flow + tlačítko), zúžené
rozvržení Přehledu, jednotný modrý pruh na všech obrazovkách, razítko verze,
audit kolo 4 se dvěma koly oprav, složka `deploy/mpsv/` a přepracované náměty
na rozvoj v `PLAN.md`.

**Next step:** nic rozpracovaného. Rozhodnutí je na zadavateli — v `PLAN.md`
sekci „Náměty na rozšíření" je osm námětů s doporučeným pořadím
**R-1 → R-3 → R-2 → R-8**. Jakmile padne volba, rozepíšu ji do kroků s testy.

**Otevřené z auditu:** jediné **N-04** — jestli `Download()` spustí stažení
i v appce vložené jako webpart na SharePoint stránku. Ověří se až v provozu.

### Úklid složky

- `deploy/` drží **poslední dva balíky** (1.0.0.61 aktuální, 1.0.0.60 jako
  základna pro `check_solution.py`); 55, 56, 58 a 59 smazané — v git historii
  zůstávají a dají se kdykoli vytáhnout.
- snímky obrazovek z kořene `input/` přesunuté do `input/snimky/`,
  starší základové balíky do `input/archiv/`. V kořeni `input/` zůstaly jen
  podklady a `procesnimapa_1_0_0_57.zip` (aktuální základ ze Studia).
- `runs/` vyčištěné od zbytků buildu a běhových testů. **`runs/app_build/pac`
  zůstává** — je to rozbalený `pac` CLI, který `build_app.py` jinak musí
  rozbalit znovu z nupkg. Zabírá 178 MB; když má jít taky pryč, stačí říct.
- kořen projektu je čistý: jen `.md`, `kody.json` a `.gitignore`.

Po úklidu přeběhly brány `check_app`, `check_solution` a `check_export_flow`
zeleně — nic z toho, co se smazalo, nebylo potřeba.

## Složka pro nasazení na MPSV — `deploy/mpsv/` (25.08.2026)

Zadáno: „složka, kde budou všechny soubory potřebné pro deploy (hlavně import
ostrých dat) a návod jak postupovat".

**Generuje ji `src/make_deploy_mpsv.py`, neudržuje se ručně** — jinak by po
první změně schématu nebo appky obsahovala starou verzi a nikdo by to nepoznal,
protože soubory uvnitř vypadají pořád stejně.

| soubor | co je |
|---|---|
| `README.md` | postup v devíti krocích, od založení listů po ověření běhu |
| `01_zaloz_listy.js` | provisioning listů a sloupců (do konzole prohlížeče) |
| `02_import_dat.js` | import **ostrých** dat z `runs/normalize` |
| `03_vypis_guidy.js` | vypíše GUIDy listů — potřebné pro `build_flow.py` |
| `sharepoint_schema.md` | dokumentace schématu |
| `procesnimapa_1_0_0_61.zip` | poslední balík appky |

Návod nese celé pořadí včetně věcí, které se dřív daly zjistit jen čtením
`PLAN.md` a `HANDOVER.md`: zapnout všechna čtyři flow, registrace `ExportFlow`
jako datového zdroje (jde jen ve Studiu), přegenerování tří flow build skripty,
ruční dorovnání `AktualizaceKratkehoNazvu` (GUID listu natvrdo + nová kostra
z designeru), přepis `varMapaUrl` a závěrečné ověření podle razítka verze.

`make_import.py` má pojistku proti nechtěnému úniku dat — neanonymizovaná sada
projde jen s `--povolit-realna-data`. Skript ji předává vědomě, protože přesně
tohle je ten jediný případ, kdy je to na místě. Repozitář je privátní a ostrá
data v něm už jsou (`input/`, `runs/normalize/`), takže se tím nic neodkrývá.

## Audit kolo 4 uzavřen — druhé kolo mělo pravdu dvakrát (25.08.2026) — balík 1.0.0.61

Re-audit rozporoval **všechny tři** stavy, které jsem po prvním kole zapsal
jako vyřízené. Dvakrát věcně správně.

### B-02 — moje oprava mezeru zúžila, nezavřela

`css_pravidlo()` vracelo **první** pravidlo se selektorem `td`. Druhé
pravidlo `td {}`, které formát zruší, tedy branou prošlo — a Excel by přitom
podle kaskády použil to poslední, poškozené. Funkčně týž dopad jako původní
nález, jen o patro dál.

Nahrazeno `css_hodnota()`, které projde všechna pravidla a vrátí **poslední**
hodnotu vlastnosti; selektory oddělené čárkou se rozebírají. Navíc kontrola,
že buňky nemají inline `style` — ten by kaskádu přebil a ve `<style>` bloku
by nebyl vidět. Kontrol 110 → 111.

### B-01 — migrační postup vynechával čtvrté flow

Napsal jsem, že se při přenosu na MPSV znovu spustí tři build skripty. Flow
jsou ale **čtyři** a `AktualizaceKratkehoNazvu` se rerunem nespraví:
`build_flow.py` má GUID listu Aktivity natvrdo v konstantě `LIST_AKTIVITY`
(runtime výraz by flow znemožnil zapnout) a jeho trigger je nad tím listem,
takže se musí založit nová kostra v designeru nad webem MPSV. Kdo by šel podle
starého postupu, narazil by až na spadlé bráně bez návodu, co dál.

Doplněno jako krok 12/5b v `PLAN.md` a výjimka v `HANDOVER.md`.

Zalátal jsem i tři obejití, která auditor sám řadil jen jako poznámku —
adresa bez schématu, cizí doména mimo `sharepoint.com`, cizí web. Kontrola
hlídá tři věci: celou adresu proti webu appky, hostitele proti allowlistu
a tenanty uvedené bez schématu. **Šest mutací, všechny chycené.**

### B-03 — přijato v podstatě, zamítnuto v důsledku

Auditor má pravdu, že `varVerze` je stejně nová YAML-only vlastnost jako kdysi
Export a Studiem zatím neprošla, takže tooltip sliboval špatný příznak selhání:
při nepublikované verzi se neukáže špatné číslo, ale **žádná nápověda**. Text
opraven.

**Zamítl jsem** požadavek znovu otevřít N-06. Ověřovaná otázka zní, jestli
Studio načte appku z YAML — a důkaz je tvrdý: tlačítko Export ve `Controls`
není a v provozu funguje. Že každá nová vlastnost jde toutéž cestou, je
vlastnost mechanismu, ne nová neznámá.

**Zamítl jsem** taky kontrolu cizích adres v `customizations.xml` mimo blok
`ConnectionReferences` — ten soubor je plný legitimních jmenných prostorů
`schemas.microsoft.com`, generuje ho Studio a build skripty do něj sahají jen
klonováním existujících uzlů. Allowlist by tam dělal hluk bez užitku.

### Uzavření

Smyčka končí na stropu dvou kol. **Žádný nález nebyl blokující**, takže se
dodává. Otevřená zůstává jediná věc, kterou bez Excelu uzavřít nejde — N-05
(injekce vzorců), viz „CO JE NA TOBĚ".

**Brány:** `check_export_flow` **111**, `check_solution` **240/0**,
`check_mapa_flow` 139, `check_flow` 17, `check_app`.

## Audit kolo 4 (25.08.2026) — verdikt NÁLEZY (0 blokujících), vše vyřízeno v 1.0.0.60

`powerplatform-auditor` nad balíkem 1.0.0.59: **0 blokujících / 1 vážný /
1 střední / 1 eskalace**. Všechny brány spustil sám a dvakrát je zkusil obejít
vlastní mutací balíku — jednou brána vadu chytila, jednou ne, a právě to je
nález B-02.

### B-01 · VÁŽNÝ — brána i dokumentace podhodnocovaly rozsah adres

`check_solution.py` hledal natvrdo zapsané URL jen v `*.pa.yaml` canvas appky,
takže `Workflows/*.json` nekontroloval vůbec. Adresa testovacího webu je
přitom v balíku na **20 místech**: jednou ručně psaná (`varMapaUrl`) a 19× ve
všech čtyřech flow. `HANDOVER.md` u toho tvrdil, že `varMapaUrl` je „jediné
místo" — což by při přenosu na MPSV znamenalo neúplný přenos.

**Opraveno:** brána prochází definice flow a **selže**, když některá adresa
nezačíná adresou webu, na který je připojená canvas app (mutačně ověřeno);
počet míst vypisuje jako varování. `HANDOVER.md` rozlišuje ručně psanou adresu
od generovaných a `PLAN.md` krok 12 dostal sedmikrokový postup přenosu.

Podstata: adresy ve flow samy o sobě chyba nejsou — build skripty je berou
z připojení appky, ne z ruky. Chyba byla v tom, co o nich projekt tvrdil.

### B-02 · STŘEDNÍ — brána kontrolovala textový formát Excelu na špatném místě

`check_export_flow.py` hledal `mso-number-format:"\@"` kdekoli v akci
`Dokument`. Mutace, která formát smaže jen z pravidla `td` (datové buňky)
a nechá ho v `th` (hlavičky), branou **prošla** — přitom by to byla přesně ta
vada, kterou 1.0.0.59 opravovala: Excel by z `01-01` zase udělal datum.

**Opraveno:** `<style>` blok se rozebere a formát se čte z těla pravidla `td`,
číselný formát z `td.n`. Původní mutace i druhá (`td.n` bez číselného formátu)
bránu nově shodí. Kontrol 109 → 110.

### B-03 · ESKALACE — uzavřena věcně, ne rozhodnutím

Auditor doložil, že `Controls/*.json` jsou bajtově shodné s 1.0.0.57 a celé
tlačítko Export i vizuální úpravy existují jen v `Src/*.pa.yaml`; nic v balíku
prý nedokáže potvrdit, že po importu proběhl povinný ruční krok ve Studiu.

Tenhle důkaz ale mechanismus **potvrzuje**, ne zpochybňuje: Export ve
`Controls` není, protože 1.0.0.57 je z doby před ním — a přesto s ním
25.08.2026 v provozu šlo exportovat. Studio tedy appku prokazatelně čte
z YAML. Tím padá i N-06.

Platná zůstávala jiná část: z běžící appky se nedalo poznat, **která verze**
je publikovaná. Doplněno razítko — `build_app.py` dosazuje do `App.OnStart`
`Set(varVerze, "<verze balíku>")` a nápověda u názvu appky ho ukazuje včetně
vysvětlení, co znamená, když nesedí. Build selže, když razítko v YAML nenajde.

### Neověřeno

- **N-04** `Download()` v appce vložené na SharePoint stránku — dnes se
  spouští samostatně, ověří se až při umístění na stránku.
- **N-05** injekce vzorců do buněk (`nazev` začínající `=`) — `mso-number-format`
  vynucuje zobrazení jako text, ale bez Excelu se nedá ověřit, jestli tím
  Excel potlačí i vyhodnocení. Viz „CO JE NA TOBĚ".

**Re-audit** oprav běží. Brány po opravách: `check_export_flow` **110**,
`check_solution` **234/0**, `check_mapa_flow` 139, `check_flow` 17, `check_app`.

## Excel dostal .xls místo .csv, tlačítka odpojena od písma (25.08.2026) — balík 1.0.0.59

### Export do Excelu selhal v provozu dvakrát naráz

Hlášeno jako „trochu hapruje font", ze snímku ale vyšly najevo **dvě** vady:

| příznak | příčina |
|---|---|
| `Úroveň` přišlo jako `Ãšroveň` | soubor **měl** BOM, jenže řádek `sep=;` přepne Excel na starý textový parser, který BOM ignoruje a čte podle národního nastavení |
| kód `01-01` skončil jako `01.I`, `01` jako číslo `1` | Excel si u CSV typ buňky hádá z obsahu; **uvozovky kolem pole proti tomu nepomáhají** |

Druhá vada byla vážnější — kódy jsou to jediné, co v rejstříku nesmí zmutovat.

**Excel proto dostává `.xls` — HTML tabulku s excelovými styly.** Obojí se
tím dá určit napevno: kódování hlavičkou `charset=utf-8` (přesně jako u Wordu,
který funguje bez výhrad) a typ buňky stylem `mso-number-format:"\@"`, což je
vynucený text. Úroveň je jediný sloupec s číselným formátem, aby se dala
v Excelu filtrovat.

**Cena:** Excel při otevření jednou upozorní, že přípona neodpovídá obsahu.
Je to jediná cesta, jak z cloud flow bez placeného konektoru dostat sešit se
správným kódováním a typy — `.xlsx` je zip a ten Logic Apps sestavit neumí.

**Brána přepsána, 109 kontrol.** Excelový výstup se nově rozebírá **parserem
HTML**, ne regulárem: ověřuje se počet buněk v každém řádku, obsah proti
vzorku, třída číselné buňky u úrovně a přítomnost textového formátu. Sedm
mutací (zrušený textový formát, jiný charset, buňka úrovně bez třídy, zrušené
escapování, přípona `.csv`, ubraná buňka, wordový dokument ve formátu excel)
**brána chytila všechny**.

Word export je podle snímku v pořádku — diakritika, odsazení úrovní, tučné
agendy, kódy jako text. Svislý pruh vpravo na snímku jsou jen značky konce
řádku Wordu, ne sloupec navíc.

### Tlačítka už nerostou s písmem

Zadáno: „při změně fontu k tomu dochází i u tlačítek na detailech — tlačítka
nech pořád stejná". Třináct tlačítek mělo `Size: =11 + varFs`; nově mají
pevných 11. Přepínač písma tak mění text v seznamech, stromu a formulářích,
ne rozvržení ovládacích prvků. Rozbalovací nabídky (`drp_*`) písmo dál mění —
je v nich obsah, ne ovládání; kdyby měly zůstat taky, je to stejná změna.

### Ověřeno, ne změněno

- **Modrý pruh na detailech** — potvrzeno v balíku i uživatelem: od 1.0.0.58
  má všech čtyři obrazovek 48 px.
- **Výchozí velikost písma je střední** — `App.OnStart` nastavuje `varFs = -2`,
  což je prostřední z trojice −4 / −2 / 0.

**Brány zeleně:** `check_app`, `check_solution` 229/0, `check_export_flow`
**109**, `check_mapa_flow` 139, `check_flow` 17.

## Tlačítko Export, sjednocené hlavičky, oprava karty (25.08.2026) — balík 1.0.0.58

Solution `1.0.0.57` s **registrovaným `ExportFlow`** dodána přes git
(`input/procesnimapa_1_0_0_57.zip`) — `FlowNameId 4b36e7da-…`. Tím padla
poslední překážka a export je hotový celý.

### Export z Přehledu

Tlačítko **Export ▾** vedle „HTML mapa" se dvěma volbami:
`Do Wordu (.doc)` a `Do Excelu (.csv)`.

Exportuje se **momentální pohled**, ne celý rejstřík: `btn_ExportMenu.OnSelect`
při otevření nabídky sebere `gal_Strom.AllItems` do `colExport` — tedy přesně
to, co je vidět po filtru stavu, hledání, chipu osiřelých i rozbalení úrovní.
Obě volby pak posílají **tutéž kolekci** a liší se jediným polem `format`,
takže se nemají jak rozejít.

Do dokumentu jde `nazevPlny`, ne `nazev` — v řádku stromu je u aktivity
zkrácený popisek, v dokumentu musí být celé znění činnosti.

`nadpis` nese slovní popis filtru („vše · jen osiřelé · hledáno: …"), aby
z dokumentu bylo poznat, jaký výřez to je. Prázdný strom export nespustí
a řekne proč.

### Grafická chyba z provozu: číslo na kartě se zalomilo

Na kartě DÍLČÍ PROCESY se **249 zalomilo na dva řádky** a druhý přetekl pod
kartu. Příčina: zúžení karet v 1.0.0.56 dalo číslu šířku 46 px, jenže Power
Apps k popisku připočítá vlastní odsazení 5 px z každé strany — trojmístné
číslo v 16 bodech potřebuje ~48 px. Karta je nově o 6 px vyšší a číslo má
70 px, což pobere i čtyřmístné, až rejstřík poroste.

### Modrý pruh 48 px na všech obrazovkách

Přehled měl po 1.0.0.56 pruh 48 px, Číselník, Detail a Vazby dál 72 px.
Sjednoceno na 48: menší šipka zpět (56 → 40 px), nadpis `16 + varFs` →
`14 + varFs`, přepínač písma jako na Přehledu. Obsah tří obrazovek se posunul
o 24 px nahoru (35 + 33 + 6 prvků), seznam v Číselníku o tolik vyrostl,
aby dole nezbyla díra.

### Výchozí velikost písma

**Už teď je střední** — `App.OnStart` nastavuje `varFs = -2`, což je
prostřední z trojice −4 / −2 / 0, a prostřední „A" je podle toho zvýrazněné.
Na snímku byla zvýrazněná nejmenší proto, že byla ručně vybraná; appka se
sama startuje na střední. Kdyby výchozí měla být největší z trojice, je to
jedno číslo v `App.OnStart`.

### Rozestoupení nabídek

Nabídka mapy je nově zarovnaná **zprava** ke svému tlačítku (X 792) a exportní
**zleva** (X 1016). Nikdy se sice nezobrazí naráz, ale kontrola překryvu to
nepozná — a překrývat se stejně nemají.

**Brány zeleně:** `check_app`, `check_solution` **229/0**, `check_export_flow`
100, `check_mapa_flow` 139, `check_flow` 17.

## Export do Wordu a Excelu + zúžení Přehledu (25.08.2026) — balík 1.0.0.56

**Zadáno:** tlačítko Export vedle „HTML mapa" se dvěma volbami (Word, Excel);
tlačítko „kód" přesunout mezi „Rozbalit" a „Stav"; tři stupně písma o další
stupeň dolů; užší a menší informační lišta s počty i horní modrý pruh.
Do exportu má jít **aktuální pohled** na Přehledu.

### Flow `ExportFlow` — hotové, čeká na registraci ve Studiu

Osm akcí, jeden textový vstup s JSON momentálního zobrazení
(`nadpis`, `format`, plochý seřazený seznam `radky`). Flow nestromuje —
Logic Apps neumí rekurzi ani vnořený Foreach, takže strom staví appka.

| formát | soubor | proč |
|---|---|---|
| Word | `.doc` (HTML) | Word otevře a uloží jako `.docx`; skutečné OOXML chce premium konektor, který neprojde DLP |
| Excel | `.csv` UTF-8 + BOM + `sep=;` | Excel otevře **bez varování**; `.xls` s HTML tabulkou hlásí nesoulad přípony a obsahu |

Obě podoby se počítají vždy a `Dokument` z nich vybírá výrazem `if` — větvení
přes If/Scope by přidalo akce, které by brána musela obcházet, a jedna z podob
by nikdy nebyla otestovaná.

**Brána `check_export_flow.py`: 100 kontrol, mini-interpret výrazů.** Výrazy
se **vytáhnou z balíku** a vyhodnotí nad vzorovým zobrazením pro oba formáty —
testuje se to, co se opravdu nasazuje, ne kopie logiky v Pythonu. CSV se čte
skutečnou čtečkou `csv`, takže název se středníkem a uvozovkami musí sedět
do sloupců. Devět mutací (odebrané escapování HTML, odebrané uvozovky v CSV,
zaseknutý přepínač formátu, chybějící BOM, chybějící `sep=;`, chybějící
`coalesce`, přehozený `runAfter`, název bez razítka, runtime výraz ve
`folderPath`) **brána chytila všechny**.

### Rozvržení Přehledu

| co | z | na |
|---|---|---|
| horní modrý pruh | 64 px, písmo 15/13 | 48 px, písmo 13/11 |
| karty s počty | 306×56 px, číslo 20 b | 260×40 px, číslo 16 b |
| tři stupně písma | −2 / 0 / +2 | **−4 / −2 / 0** |
| tlačítko „kód" | vpravo za „HTML mapa" | mezi „Rozbalit" a „Stav" |
| místo pro Export | — | 100 px vedle „HTML mapa" |

Uvolnilo se 40 px svislého místa — strom je o tolik vyšší.

**Nejmenší popisky tím padly na 6 bodů** (`10 + varFs` při `varFs = −4`).
Je to dolní mez a platí jen v nejmenším ze tří stupňů, kde je hustota celý
smysl; výchozí (střední) stupeň je dnes na 8 bodech. Kdyby to bylo moc,
je to změna tří čísel.

**Tlačítko Export v 1.0.0.56 ještě není** — potřebuje registraci flow jako
datového zdroje, což jde jen ve Studiu. Místo v pruhu je na něj nachystané,
aby se rozvržení podruhé nepřeskládávalo.

**Brány zeleně:** `check_app`, `check_solution` 225/0, `check_export_flow`
**100**, `check_mapa_flow` 139, `check_flow` 17, `check_schema`,
`check_mapa_html` 31, `check_setup.js`, `check_import.js`. Překryv v pruhu
mutačně ověřen — posun „kód" o 20 px doleva bránu shodí.

## Číslo, které neřeklo, co počítá (24.08.2026) — balík 1.0.0.55

**Hlášeno jako chyba:** „na html to píše bez aktivit, přitom aktivity tam
jsou". Nebyla to chyba — appka a mapa říkaly totéž, každá jinými slovy:

| | proces `01-06` | jeho dílčí procesy |
|---|---|---|
| appka, sloupec POLOŽKY | **4** (dílčí procesy) | **0** (aktivity) |
| mapa, odznak | **bez aktivit** | **bez aktivit** |

Proces má čtyři dílčí procesy, ale ani jeden z nich nemá popsanou činnost.
Obojí platí, jenže sloupec POLOŽKY ukazoval **holé číslo bez jednotky** —
u procesu tedy „4" vypadalo jako čtyři aktivity a vedle toho mapa psala „bez
aktivit". Vypadalo to jako spor dvou pohledů na tatáž data.

**Opraveno na obou stranách:**
- sloupec v appce říká, co počítá: `10 proc.` u agendy, `4 dílč.` u procesu,
  `0 akt.` u dílčího procesu. Se zapnutým filtrem stavu je jednotka vždy
  `akt.`, protože tam se počítají aktivity ve větvi;
- nápověda odznaku v mapě dovysvětlí obojí: „Uvnitř tohoto procesu jsou
  4 dílčí procesy, ale činnosti k ní zatím nikdo nepopsal."

**Odsazení úrovní v mapě** zvětšeno ze 17+9 px na 26+14 px — hlubší stupeň
splýval s tím nad sebou (zadáno tamtéž).

Potvrzeno ze snímků: oprava závodu s `Concurrent` (1.0.0.53) v provozu
zabrala — Přehled ukazuje reálné počty a karta „251 dílčích procesů,
26 s aktivitami".

## Sloupec `stav_mapovani` zrušen (24.08.2026) — balík 1.0.0.54

**Zadáno:** „je to celé matoucí a nechci tam pole které zastarává případně
vyžaduje ruční update. dej ho celé pryč."

Vyšlo to najevo z otázky, jak vzniká odznak „u jiného útvaru" v mapě. Řetěz
vedl přes `stav_mapovani`, což byla **čistá odvozenina**: má aktivitu →
`zmapováno`; nemá a `stav_rejstrik` začíná na „využitý" → `zmapováno jiným
útvarem`; jinak `nezmapováno`. Uložený sloupec se ale po importu nikdy
nepřepočítal — appka do něj při zakládání zapsala natvrdo `nezmapováno`
a v žádném formuláři se nedal změnit. Postupně tedy lhal, a nikdo neměl jak
to opravit.

**Odstraněno ze sedmi míst:** `schema.json` (3 listy), `normalize.py`
(funkce i sloupce v CSV), `anonymize.py`, `build_mapa_flow.py`,
`check_mapa_flow.py`, `mapa_template.html`, `scr_Ciselnik.pa.yaml`.
Přegenerované: `setup_sharepoint.js`, `import_data.js`,
`deploy/sharepoint_schema.md`, `deploy/flow_MapaPublish.md`.

**Odznak v mapě má nově jen dvě podoby:** `N akt.` a `bez aktivit` — obojí
spočítané ze skutečného počtu aktivit ve větvi, takže nemá jak zastarat.
Souhrn v `report.md` počítá totéž ze `pocet_aktivit` místo z uloženého stavu.

**Appka při zakládání nezapisuje ani `stav_rejstrik`.** Zapisovala natvrdo
„využitý", což u položky, která v původním rejstříku nikdy nebyla, není
pravda. `stav_rejstrik` v listu zůstává — na rozdíl od `stav_mapovani` to
není odvozenina, ale zdrojový údaj z barev v původním rejstříku.

**Sloupec v SharePoint listech smaže zadavatel ručně.** Do té doby tam
nevadí — nikdo ho nečte.

Brány po změně: `check_schema`, `check_app`, `check_solution` 225/0,
`check_mapa_html` 31, `check_mapa_beh` 25, `check_mapa_flow` **139**
(bylo 142 — ubyly kontroly zrušeného sloupce), `check_flow` 17,
`check_setup.js`, `check_import.js`.

## Strom se stavěl z nedonačtených kolekcí (24.08.2026) — balík 1.0.0.53

**Příznak z provozu:** na Přehledu měly všechny procesy ve sloupci POLOŽKY
**0** a karta hlásila „251 dílčích procesů, 0 s aktivitami"; v Číselníku bylo
zároveň **všech 251 dílčích procesů osiřelých**. Publikovaná mapa přitom tytéž
vazby z týchž listů zobrazovala správně.

**Sonda rozhodla spor.** `src/probe_dilci.js` (vložit do F12 konzole na webu
appky, jen čte) vypsala interní názvy sloupců, ukázku řádků a spárování:
**239 z 251 dílčích procesů má platný `proces_kod`**, 12 jich odkazuje na
proces `02-01`, který v listu není — ti jsou osiřelí právem. Data tedy byla
celou dobu v pořádku a chyba byla v appce.

**Příčina: `Concurrent()` v `App.OnStart` nečeká na dokončení.** Vrátí se hned
a načítání kolekcí dobíhá na pozadí. Úvodní obrazovka se mezitím zobrazí a její
`OnVisible` postaví `colStrom` z toho, co zrovna dorazilo. Vznikne snímek
prázdna, který se sám neopraví — `ClearCollect` proběhl jen jednou.

Proč to vypadalo jako vada dat: karty s počty čtou `CountRows()` **reaktivně**,
takže po dotažení ukazují 251 správně, kdežto strom postavený vedle nich
zůstane prázdný. A protože pořadí dokončení `Concurrent` nezaručuje nic,
dostala každá obrazovka jinou nedonačtenou kolekci — Přehled přišel o `colDilci`
(procesy bez dílčích procesů), Číselník o `colProcesy` (dílčí procesy bez
rodiče, tedy „osiřelé").

**Oprava:** `OnVisible` Přehledu i Číselníku má před stavbou odvozené kolekce
pojistku `IsEmpty()` — když číselník ještě nedorazil, načte se synchronně.
Test na prázdnotu stačí, protože `ClearCollect` je atomický: kolekce je buď
prázdná, nebo celá.

**Brána `kontrola_concurrent`** v `check_app.py`, mutačně ověřená: každá
kolekce plněná uvnitř `Concurrent()` musí mít v `OnVisible`, které z ní staví,
test `IsEmpty()`. Odebrání pojistky bránu shodí.

Zároveň v mapě: odznak **„nezmapováno" → „bez aktivit"** a **„jiný útvar" →
„u jiného útvaru"**, oba s nápovědou; legenda je vysvětluje ukázkou odznaku.
Obojí znělo jako hodnocení kvality místo údaje o evidenci.

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

**F9 je hotová.** Krok 5 ověřen v provozu na PPF DEV (appka čte data přes
proměnné, mapa se zobrazí). Krok 6 postavený: `deploy/procesnimapa_1_0_0_71.zip`
čeká na import na MPSV — viz „CO JE NA TOBĚ". Zbývá jen doověřit export
do Wordu/Excelu na PPF.

**F10 krok 1 hotový** (list `HistorieKodu`, `puvodni_kod`, brány mutačně
ověřené). Balíku se to netýká — appka nový list zatím nepoužívá.

Další v pořadí: **F11 krok 2** (test DLP pro Excel Online (Business) — je to
deset minut a rozhoduje o zbytku F11, čeká na uživateli) → **F10 krok 2**
(přesun aktivity = uzavření + vznik) → F10 kroky 3–5 → zbytek F11.

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
