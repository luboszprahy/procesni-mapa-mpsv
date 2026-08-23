# AUDIT — Procesní mapa MPSV

Poslední audit: 23.08.2026 · kolo: 3 (canvas app — mazání, editace, vazby, flow)
Předchozí: 19.08.2026 · powerplatform-auditor · kolo 2 (datová vrstva)
Verdikt kolo 3: NÁLEZY (0 blokujících / 3 vážné / 3 střední / 2 drobné) — neopraveno,
nejzávažnější je referenční integrita vazební tabulky (A-01) a strop 500 řádků (A-03)
Verdikt kolo 2: NÁLEZY (0/1/0) — žádný otevřený BLOKUJÍCÍ, F1 připravená na ostrý běh
Rozsah kola 2: re-audit oprav P-01/P-02/P-03 z kola 1 (`src/make_import.py`,
`src/anonymize.py`, `PLAN.md`), spuštění `check_schema.py`/`make_setup.py`/
`make_import.py`/`check_setup.js`/`check_import.js`, nově `deploy/app_navrh.md`
(technická tvrzení o delegaci a přidělení kódu — appka sama neexistuje).

V tomto projektu **neplatí** kritéria vázaná na publisher `ppf`/prefix `ppf_`/
tenant `ppfbanka.sharepoint.com` — viz zdůvodnění v kole 1 níže (beze změny).

## Nálezy — kolo 3 (23.08.2026, appka 1.0.0.37)

Rozsah: všechna mutační místa ve zdrojích appky, referenční integrita vazební
tabulky, soulad kolekcí se zdrojem, tři flow a šablona mapy.

**Stav k 23.08.2026 večer (balík 1.0.0.42): opraveno A-01 až A-07.**

| nález | stav |
|---|---|
| A-01 vazby po smazaném dílčím procesu + recyklace kódu | **opraveno** |
| A-02 duplicitní vazba při změně primárního zařazení | **opraveno** |
| A-03 strop 500 řádků proti slibovaným 2 000 | **opraveno** |
| A-04 `RemoveIf` nad velkým listem se nedeleguje | **opraveno** |
| A-05 publikace osiřelé záznamy tiše zahodí | **opraveno** |
| A-06 flow přepisuje pole, která nepočítá | **opraveno**; rozdvojené pravidlo zkrácení zůstává jako vědomý kompromis |
| A-07 `varCiselnikKod` přežije smazání z přehledu | **opraveno** |
| A-08 zbytky a natvrdo zapsané hodnoty | duchové v `.msapp` opraveni, zbytek otevřený |

Tři nálezy jsem po auditorovi ověřil sám (A-01, A-03 a tvrzení o `check_solution`);
jeden se nepotvrdil, viz „Zamítnuté nálezy — kolo 3" na konci sekce.

### A-01 · VÁŽNÝ · vazby přežijí smazání dílčího procesu a přilepí se k cizí položce

`RemoveIf('Vazba aktivita–dílčí proces', dilci_proces_kod = …)` **v appce
neexistuje**; všechny čtyři úklidy vazeb jdou přes `aktivita_kod`
(`scr_Detail` 712 a 759, `scr_Ciselnik` 1673, `scr_Dashboard` 1418). Ověřeno
greppem.

Scénář:
1. Dílčí proces `01-02-005` má tři aktivity, tedy tři vazby.
2. Smaže se (číselník nebo přehled) → vazby zůstanou a nedá se na ně dostat:
   žádná obrazovka je podle dílčího procesu nefiltruje a chip osiřelých je
   nezná, protože `colCiselnik` úroveň „vazba" nemá.
3. Kód se přiděluje jako *poslední existující + 1*, takže se `005`
   po smazání **uvolní a znovu přidělí** jinému dílčímu procesu.
4. Publikace: `mapa_template.html` seskupuje vazby podle `dilci_proces_kod`,
   takže staré aktivity vyskočí pod novým, obsahově nesouvisejícím dílčím
   procesem.

`PLAN.md` (F6/F) pokrývá výslovně jen vazby osiřelé po **aktivitě**; vazby
osiřelé po dílčím procesu nejsou popsané nikde. Není to tedy přijatý kompromis.

**OPRAVENO (1.0.0.42).** Mazání dílčího procesu v číselníku i na přehledu
uklidí `RemoveIf('Vazba aktivita–dílčí proces', dilci_proces_kod = …)`.
Recyklaci kódu řeší kontrola při zakládání: leží-li pod navrženým kódem
osiřelé položky, uložení se odmítne s vysvětlením, že je potřeba je nejdřív
uklidit. Odmítnout je tu lepší než tiše přeskočit na další volný kód — v datech
leží neuklizený zbytek a kdo zakládá, se to má dozvědět.

### A-02 · VÁŽNÝ · změna primárního dílčího procesu umí vyrobit duplicitní vazbu

`scr_Detail.pa.yaml` 712-724: `RemoveIf(… primarni.Value = "ano")` a hned
`Patch` nové primární vazby. Nekontroluje se, jestli dvojice aktivita–dílčí
proces už neexistuje jako **neprimární** — `scr_Vazby` tu kontrolu má
(`ico_Pridat`), cesta přes detail ne.

Scénář: aktivita primární v `A`, přes „Spravovat" přidaná i do `B`; v detailu
se přepne dílčí proces na `B` → vznikne druhý záznam `AKT__B`. V mapě je
aktivita pod `B` dvakrát a počty nadřazených uzlů jsou o jedna vyšší, zatímco
přehled v appce počítá z `Aktivity.dilci_proces_kod` a ukazuje správně —
čísla v appce a v mapě se rozejdou.

**OPRAVENO (1.0.0.42).** Stará vazba se odebírá podle **starého dílčího
procesu**, ne podle příznaku `primarni`, a před zápisem se odebere i případná
neprimární vazba na cílový dílčí proces. Tím zmizela duplicita i nedelegovatelný
predikát z A-04 naráz.

### A-03 · VÁŽNÝ · appka má strop 500 řádků, ale všude tvrdí 2 000

`Properties.json` v `.msapp`: `DefaultConnectedDataSourceMaxGetRowsCount = 500`.
Ověřeno přímo v balíku 1.0.0.37.

Proti tomu tooltipy na přehledu, komentáře ve zdrojích, výjimka delegace
v `check_app.py` a řada míst v `STATUS.md` i `PLAN.md` tvrdí, že do 2 000
aktivit je výsledek úplný. Práh se přitom láme už u **501. aktivity**:
`colAkt`, počty ve stromu, chip osiřelých i fulltext pracují s prvním oknem.

**OPRAVENO (1.0.0.42).** `build_app.py` hodnotu srovnává na 2 000
(`nastav_limit_radku`), `check_solution.py` to hlídá. Ověřeno v balíku.

### A-04 · STŘEDNÍ · `RemoveIf` nad velkým listem se nedeleguje a brána mlčí

`NEDELEGOVATELNE` v `check_app.py` neobsahuje `Remove`/`RemoveIf`, přestože
vazební tabulka je ve `VELKE_LISTY`. Nad ~500 vazbami se `RemoveIf` provede
jen nad prvním oknem: stará primární vazba se nemusí odstranit a `Patch`
přidá druhou → aktivita se **dvěma primárními** vazbami. Predikát
`primarni.Value = "ano"` (choice) delegaci zabíjí sám o sobě.

**OPRAVENO (1.0.0.42).** Choice predikát z mazání zmizel spolu s opravou A-02
— vybírá se podle textových sloupců `aktivita_kod` a `dilci_proces_kod`, které
SharePoint deleguje. `kontrola_predikatu` nově hlídá i `RemoveIf`: jak volání
nedelegovatelné funkce v podmínce, tak rozhodování podle choice sloupce.
Mutačně ověřeno vrácením původního tvaru.

### A-05 · STŘEDNÍ · publikace osiřelé záznamy tiše zahodí

`mapa_template.html`, `buildTree()`: strom se skládá shora, takže co nemá
živého rodiče, se do mapy vůbec nedostane. Flow nemá žádnou kontrolu.

Dialog při mazání agendy slibuje „nezmizí, najdeš je přepínačem osiřelé" —
v rejstříku ano, ale z publikované mapy zmizí celá větev včetně desítek
aktivit a mapa to nijak nepřizná. Texty dialogů o dopadu na mapu mlčí.

**OPRAVENO (1.0.0.42).** `buildTree()` přidá na konec stromu uzel
**„Nezařazené — chybí nadřazená položka rejstříku"** se všemi třemi druhy
sirotků (proces bez agendy, dílčí proces bez procesu, aktivita bez dílčího
procesu). Ověřeno spuštěním `buildTree` nad daty se sirotky: uzel se objeví
se všemi třemi a živá větev zůstane nedotčená; bez sirotků uzel nevznikne.

### A-06 · STŘEDNÍ · appka a flow `AktualizaceKratkehoNazvu` počítají zkratku jinak

Appka ukládá `Left(text, 150)`, flow počítá kanonické zkrácení (kolaps mezer,
řez na hranici slova, oříznutí interpunkce, `…`). U názvu delšího než 150
znaků tedy appka uloží useknuté slovo a flow ho do minuty přepíše.

Flow navíc patchuje `Title`, `nazev` i `dilci_proces_kod` ze snapshotu
triggeru, takže může přepsat opravu uloženou do minuty po prvním uložení.
`STATUS.md` přitom tvrdil „jen `item/nazev_kratky`" — dokumentace se
rozcházela s tím, co flow dělá.

**Zápis navíc OPRAVEN (1.0.0.42).** `build_app.py` při každém buildu odebere
`item/nazev` a `item/dilci_proces_kod`; `item/Title` zůstává, protože je to
kód a ten se z principu nikdy nemění. `check_solution.py` to hlídá.

**Rozdvojené pravidlo zkrácení zůstává jako vědomý kompromis.** Appka zapíše
`Left(text, 150)` jako provizorium, aby seznam neukazoval prázdno, a flow ho
do minuty dorovná na kanonický tvar. Liší se to jen u názvů delších než 150
znaků a jen do doběhnutí flow. Sjednotit by šlo tak, že by appka
`nazev_kratky` nezapisovala vůbec — za cenu prázdného sloupce v seznamu
po dobu, než flow doběhne.

### A-07 · DROBNÝ · `varCiselnikKod` přežije smazání položky z přehledu

`scr_Ciselnik.OnVisible` resetuje `varChybaC` a `varSmazatC`, ale ne
`varCiselnikKod`. Když se položka načtená ve formuláři smaže z **přehledu**,
formulář po návratu dál hlásí „Úprava …" nad neexistujícím záznamem. Skončí
to hláškou z `IfError`, data se nerozbijí. `PLAN.md` (F6/E) tenhle edge case
vyžaduje ošetřit — ošetřený byl jen pro mazání z téže obrazovky.

**OPRAVENO (1.0.0.42).** `scr_Ciselnik.OnVisible` se po naplnění `colCiselnik`
zeptá, jestli vybraná položka ještě existuje, a když ne, vrátí formulář na
zakládání. Kontrola musí být až za naplněním kolekce — před ním by se ptala
do prázdna a formulář by se resetoval pokaždé.

### A-08 · DROBNÝ · zbytky a natvrdo zapsané hodnoty

- **OPRAVENO (1.0.0.38)** — a ukázalo se, že to neškodné nebylo: Studio
  ducha načetlo, mrtvé odkazy nahlásilo jako chyby a kvůli nim neprovedlo
  App.OnStart, takže appka po importu naběhla černá. `build_app.py` teď
  Controls zrušených obrazovek maže, `check_solution.py` to hlídá.
  Původní text nálezu: `.msapp` nese `Controls/4.json` se zrušenou obrazovkou `scr_Seznam`
  a `AppCheckerResult.sarif` s odkazy na ni. Neškodné (`LoadFromYaml = true`,
  Studio čte `Src/*.pa.yaml`), ale je to smetí v balíku.
- `Model` v publikačním flow má natvrdo `"sekce": "3"` a jméno správce —
  po rozšíření mimo sekci 3 bude hlavička mapy lhát.
- `$top: 5000` bez `paginationPolicy` je strop pro aktivity v mapě.
- Testovací tenant je při přenosu na MPSV na čtyřech místech (`varMapaUrl`
  a `dataset` ve třech flow), ne na jednom.

### Zamítnuté nálezy — kolo 3

- **„`check_solution.py` při chybějícím vstupu skončí s exit 0, takže v CI
  mlčky projde."** Neplatí. Ověřeno spuštěním: bez vstupu vypíše
  `CHYBA: chybí …` a vrátí **exit 1**. Pravdivá je jen ta část, že výchozí
  cesta `input/procesnimapa_1_0_0_2 (2).zip` po úklidu repa neexistuje, takže
  se skript musí spouštět s `--vstup`/`--vystup` (což příkazy v `HANDOVER.md`
  dělají).

### Ověřeno spuštěním — kolo 3

| brána | výsledek |
|---|---|
| `check_app.py` | OK — 4 obrazovky, 193 prvků, 2 129 vzorců |
| `check_solution.py --vstup … --vystup …` | 219 kontrol / 0 chyb |
| `check_mapa_flow.py --solution …` | 142 kontrol OK; akce obou mapových flow bajtově shodné, liší se jen trigger |
| `check_schema.py` | OK — 7 / 46 / 250 / 46 / 46 / 8 |
| `check_mapa_html.py` | 31 kontrol OK |
| `check_mapa_beh.py` | 18 kontrol OK |

---

## Nálezy — kolo 1 (stav po kole 2)

### P-01 · BLOKUJÍCÍ (kolo 1) · src/make_import.py
Původní nález: pojistka „do vývojového tenantu smí jen anonymizovaná data"
kontrolovala jen název poslední složky cesty, ne obsah dat.

**Oprava přijata.** `neanonymizovane_tokeny()` (src/make_import.py:26-35) skenuje
`json.dumps(data)` proti `TOKENY` importovanému z `src/anonymize.py` — stejný
seznam, kterým si anonymizace ověřuje vlastní výsledek. Původní repro scénář
teď spolehlivě selže:
```
cp runs/normalize/*.csv <scratch>/pojistka_test/anonym/
python src/make_import.py --data <scratch>/pojistka_test/anonym --out import_TEST.js
→ ODMITNUTO: … jsou identifikujici udaje (\bMPSV\b, \bÚP ČR\b, …). EXIT 1
```
Funguje, protože „MPSV" je jako literální řetězec prakticky ve všech `nazev`
polích všech čtyř tabulek (ověřeno greppem přes `runs/normalize/*.csv`) —
náhodná/nedbalá kopie neanonymizovaných dat tedy tuto pojistku nepodejde.

**Ale: cílená/dílčí obchazka funguje** — viz nový nález **P-04** níže. Kontrola
je jen tak dobrá, jako seznam `TOKENY`, a ten nepokrývá útvarová čísla
(`UTVARY` v `anonymize.py`) ani formát čísel předpisů (`RE_PREDPIS`), přestože
`anonymize.py` sám tyto dvě kategorie aktivně anonymizuje. Aktuální komitnutá
data v `runs/anonym` tímto problémem netrpí (prošla `anon()` normálně) — jde o
riziko pro budoucí ruční zásahy do dat, ne o vadu dnešního balíčku.
Checklist: mimo číslované body; zadání PRD NFR-4.
Stav: **oprava přijata pro nahlášený scénář; navazující gap zaveden jako P-04 (OPRAVIT)**

### P-02 · OPRAVIT (kolo 1) · src/make_import.py
Původní nález: `check_schema.py` se nevolal automaticky před generováním
importu, poškozená data (referenční kód mimo číselník) se tiše zapekla.

**Oprava přijata a ověřena.** `make_import.py` teď importuje a volá `check()`
(řádky 220-228) před generováním. Mutační test — `procesy.csv` řádek
`01-01;…;01;` přepsán na `01-01;…;99;` (neexistující agenda):
```
python src/make_import.py --data <scratch>/p02_test --out import_p02.js
→ CHYBA: Procesy.agenda_kod: 1 odkazu nema protejsek v Agendy, napr. ['99']
→ ODMITNUTO: … nesedi na schema (1 chyb). EXIT 1
```
Běžný běh nad `runs/anonym` (bez mutace) proběhl bez problémů — `check()`
poškozená data odmítá, nepoškozená propouští (viz „Ověřeno spuštěním" níže).
Checklist: E2. Stav: **opraveno, ověřeno**

### P-03 · OPRAVIT (kolo 1) · PLAN.md
Původní nález: `PLAN.md` dokumentoval u `stav_rejstrik` 2 hodnoty místo 3.

**Oprava přijata.** `PLAN.md` řádek 64 nyní uvádí `využitý` / `využitý-S4` /
`nevyužitý` se zdůvodněním (3 položky, kde už dílčí proces využila sekce 4) a
větou „Závazný je vždy `src/schema.json`". Sedí na skutečné schéma.
Stav: **opraveno**

## Nový nález — kolo 2

### P-04 · OPRAVIT · src/make_import.py + src/anonymize.py
Pojistka `neanonymizovane_tokeny()` kontroluje obsah dat, ale **jen proti
pevnému seznamu `TOKENY`** (13 institucionálních zkratek + 2 vlastní jména).
Nekontroluje:
- **útvarová čísla** — `UTVARY` (`{"3":"7","33":"71","331":"711","11":"72",
  "111":"721","113":"723","12":"73","6":"74","4":"75"}` v `anonymize.py`),
  přestože `anon()` je aktivně přepisuje jako identifikující údaj,
- **čísla vnitřních předpisů** — `RE_PREDPIS` (`SP/MP/PM ##/####`), přestože
  `Predpisy` třída v `anonymize.py` existuje přesně proto, aby je nahradila.

Repro (nad kopií `runs/anonym`, tedy řádně anonymizovaná data, do nichž se
ručně vrátí jen dvě reálné hodnoty — util kód a číslo předpisu — beze změny
čehokoli jiného, „MPSV" nikde nepřidáno):
```
cp runs/anonym/*.csv <scratch>/pojistka_test3/
# v aktivity.csv nahrazeno (jen tento jeden řádek):
#   "07-08-009;711;věcně příslušné útvary XÚ;VP 01/2015, VP 02/2016;7;8"
#   -> "07-08-009;331;věcně příslušné útvary XÚ;SP 10/2021, SP 13/2025;7;8"
python src/make_import.py --data <scratch>/pojistka_test3 --out import_TEST3.js
→ EXIT 0, žádné varování
grep '"vykonava": "331"' import_TEST3.js   → nalezeno (reálný útvarový kód MPSV)
grep "SP 10/2021" import_TEST3.js          → nalezeno (reálné číslo interního předpisu)
```
Import se zapeče beze zádrhelu do `import_data.js` a odešel by do PPF tenantu.
Reálný útvarový kód a reálné číslo interního předpisu jsou přesně ta
kategorie údajů, kterou `anonymize.py` sám považuje za nutné anonymizovat
(viz `UTVARY`, `Predpisy`) — pojistka v `make_import.py` na ně ale nedosáhne,
protože kontroluje jen `TOKENY`.

Proč jde o **OPRAVIT**, ne BLOKUJÍCÍ: netýká se aktuálních komitnutých dat
(`runs/anonym` prošla `anon()` běžnou cestou a je čistá — ověřeno i greppem v
kole 1). Scénář vyžaduje ruční zásah do už anonymizovaných CSV (typicky oprava
jednoho pole „z ruky" bez opětovného běhu `anonymize.py`), ne prostou
nedbalost jako u P-01. Riziko roste s tím, jak přibudou karty dalších sekcí a
někdo bude opravovat data přímo v `runs/anonym`.

Doporučená oprava (neprovádět, jen návrh pro hlavního asistenta): rozšířit
`neanonymizovane_tokeny()` o kontrolu `RE_PREDPIS` (jakýkoli match = reálné
číslo předpisu, protože po anonymizaci by měly být jen `VP ##/20##`) a o
kontrolu, že žádná hodnota polí `vykonava`/`vlastnik` neodpovídá klíči v
`UTVARY` (reálné originální kódy `3/33/331/11/111/113/12/6/4`).
Checklist: mimo číslované body; zadání PRD NFR-4.
Stav: otevřeno

## Ověřeno spuštěním — kolo 2

Všech pět požadovaných příkazů proběhlo bez chyby a testy prokazatelně umí
selhat (ne jen „proběhlo bez erroru"):

- `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe src/check_schema.py`
  → `schema OK proti runs/normalize: Agendy=7, Procesy=46, DilciProcesy=250,
  Aktivity=46, AktivitaDilciProces=46`, exit 0.
- `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe src/make_setup.py`
  → `src\setup_sharepoint.js (21.2 kB) - 5 listu, 33 sloupcu`, exit 0.
- `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe src/make_import.py`
  → `src\import_data.js (113.8 kB) - Agendy=7, Procesy=46, DilciProcesy=250,
  Aktivity=46, AktivitaDilciProces=46`, exit 0. Regenerovaný soubor se lišil
  od komitnutého jen v `datum_aktualizace` (46 řádků diffu, jen časové
  razítko, ověřeno `git diff` a vráceno `git checkout -- src/import_data.js`,
  auditor v repu nic nezanechal).
- `node src/check_setup.js` → 32/32 kontrol OK ve 3 scénářích, exit 0.
- `node src/check_import.js` → 26/26 kontrol OK ve 3 scénářích, exit 0.
- P-01 fix ověřen mutací (viz výše, exit 1 pro reálná data).
- P-02 fix ověřen mutací (viz výše, exit 1 pro poškozený `agenda_kod`).
- P-04 gap ověřen mutací (viz výše, exit 0 pro útvarový kód + číslo předpisu
  — to je nález, ne potvrzení funkčnosti).

Oprava tedy nic nerozbila — běžný běh nad `runs/anonym` prochází stejně jako
před opravou, jen navíc odmítá scénáře, které dřív procházely tiše.

## deploy/app_navrh.md — kontrola technických tvrzení

Dokument, appka zatím neexistuje (v souladu se zadáním — to není nález).
Ověřil jsem tvrzení o delegaci a přidělení kódu proti `src/schema.json`
(skutečné indexování sloupců) a proti `reference/canvas-architecture-patterns.md`
+ `reference/datovy-zdroj-nenacita.md` (checklist C2):

- **`Filter(Aktivity, StartsWith(Title, varPrefix))`** — `Title` (pole `kod`)
  je v `src/schema.json` `indexed: true` (ověřeno vypsáním schématu). `StartsWith`
  nad indexovaným textovým sloupcem je pro SharePoint delegovatelný a `varPrefix`
  je globální proměnná (`Set`), ne hodnota počítaná uvnitř `ForAll` — přesně
  vzor, který `canvas-architecture-patterns.md` označuje za bezpečný („v
  delegovaném Filter smí být jen literál nebo globální proměnná"). Tvrzení sedí.
- **Filtry `scr_Seznam`** (`sekce`, `vykonava`, `stav`, `nazev_kratky`) — všechny
  čtyři sloupce jsou v schématu `indexed: true` (ověřeno). Vzor
  `IsBlank(ctrl.Selected.Value) || sloupec = ctrl.Selected.Value` je standardní
  delegace-bezpečný idiom pro volitelné filtry nad SharePointem (kombinace
  `Or`/`And` nad delegovatelnými porovnáními `=`/`StartsWith`) — konzistentní
  s tím, co `canvas-architecture-patterns.md` a `datovy-zdroj-nenacita.md`
  o delegaci nad SharePointem dokumentují. Nenašel jsem rozpor.
- **„Search() a in delegovatelné nejsou"** — v lokálních skillech není explicitně
  zmíněno (dostupné artefakty mluví hlavně o `ID >`, `Sort`, `StartsWith`),
  takže tvrzení nejde ověřit `[SPUSŤ]` nad rozbaleným balíčkem (appka
  neexistuje). Odpovídá to obecně známému a stabilnímu faktu o SharePoint
  konektoru, ale bez appky/prostředí ho nejde potvrdit místní reprodukcí →
  **NEOVĚŘENO** (viz N-03).
- **Vazba M:N** (`AktivitaDilciProces`, dotaz podle `aktivita_kod`) — sloupec
  `aktivita_kod` je `indexed: true` (ověřeno), matches.
- **Přidělení kódu** (`Right("000" & (Value(Right(varPosledni,4))+1), 4)`) —
  prázdný dílčí proces: `Right(Blank(),4)` → `Blank()`, `Value(Blank())+1` = 1
  (Power Fx počítá s `Blank()` jako 0 v aritmetice) → `0001`, sedí na tvrzení
  v dokumentu. Přetečení nad 9999 aktivit v jednom dílčím procesu vzorec
  neřeší (`Right("000"&10000,4)` by dalo `"0000"`), ale to je při dnešním
  rozsahu (max řádově desítky aktivit na dílčí proces) čistě teoretické —
  POZNÁMKA, ne nález.
- **`vlastnik` jen ke čtení, mimo `Aktivity`** — schéma `Aktivity` v
  `src/schema.json` skutečně nemá sloupec `vlastnik` (ověřeno výpisem), sedí
  na tvrzení „vlastníci patří číselníku, ne aktivitě".

Žádné faktické chybné tvrzení v `deploy/app_navrh.md` jsem nenašel; jedno
tvrzení (Search/in) zůstává NEOVĚŘENO z důvodu chybějícího prostředí/appky,
ne proto, že by bylo zpochybněno.

## Neověřeno

### N-01 · reálný běh na SharePointu (z kola 1, stále platí)
Vše je ověřeno proti mock/fake SharePointu a CSV datům. Skutečné REST chování
cílové PPF site nebylo ověřeno naživo — mimo rozsah auditu (čtení lokálních
artefaktů, ne zásah do prostředí).

### N-02 · stabilita kódu při přejmenování položky (z kola 1, stále platí)
Neověřeno, jen potvrzeno jako známé riziko bez technické pojistky (viz
STATUS.md).

### N-03 · Search()/in nedelegovatelnost nad SharePointem (nové)
`deploy/app_navrh.md` tvrdí, že `Search()` a `in` nejsou pro SharePoint
delegovatelné. Odpovídá obecně známému chování SharePoint konektoru, ale
lokální skill materiály to explicitně nedokládají a appka/prostředí neexistuje,
takže to nejde ověřit `[SPUSŤ]`. Potřeba k doověření: appka nad reálným
SharePoint listem + Power Apps Studio delegation warning, nebo oficiální
dokumentace Microsoftu (offline nedostupná).

## Zamítnuté nálezy

*(žádné)*
