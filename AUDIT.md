# AUDIT — Procesní mapa MPSV

Poslední audit: 25.08.2026 · kolo: 4 (ExportFlow, druhé flow, zrušení stav_mapovani, balík 1.0.0.59)
Předchozí: 23.08.2026 · powerplatform-auditor · kolo 3 (canvas app — mazání, editace, vazby, flow)
Verdikt kolo 4: NÁLEZY (0 blokujících / 1 vážný / 1 střední / 0 drobných / 1 eskalace)
  — **vše vyřízeno v 1.0.0.60**: B-01 a B-02 opraveny, B-03 zmírněn a ověřen provozem
Verdikt kolo 3: NÁLEZY (0 blokujících / 3 vážné / 3 střední / 2 drobné) — nejzávažnější
byla referenční integrita vazební tabulky (A-01, opraveno) a strop 500 řádků (A-03, opraveno)
Verdikt kolo 2: NÁLEZY (0/1/0) — žádný otevřený BLOKUJÍCÍ, F1 připravená na ostrý běh

V tomto projektu **neplatí** kritéria vázaná na publisher `ppf`/prefix `ppf_`/
tenant `ppfbanka.sharepoint.com` — viz zdůvodnění v kole 1 níže (beze změny).
Testovací tenant je skutečně `ppfbanka.sharepoint.com` a jeho výskyt v balíku
proto sám o sobě není nález — nález je až to, že jeho **rozsah** (kolik míst
je potřeba přepojit při přenosu na MPSV) je jinde v projektu podhodnocený,
viz B-01.

## Nálezy — kolo 4 (25.08.2026, balík `deploy/procesnimapa_1_0_0_59.zip`)

Rozsah: `ExportFlow` (`src/build_export_flow.py`, `src/check_export_flow.py`,
`deploy/flow_Export.md`), tlačítko Export v `scr_Dashboard.pa.yaml`, druhé
flow `MapaPublishScheduled` (`src/add_mapa_schedule.py`), zrušení sloupce
`stav_mapovani`, oprava `Concurrent()` v `App.OnStart`. Ověřeno nad skutečně
rozbaleným `deploy/procesnimapa_1_0_0_59.zip` (`unzip -t` bez chyby na
solution zipu i vnořeném `.msapp`) a nad `input/procesnimapa_1_0_0_57.zip`
jako referenčním „před". Všechny brány spuštěny přímo, ne odečteny ze
`STATUS.md`: `check_export_flow.py` 109/109, `check_solution.py --vstup
input/procesnimapa_1_0_0_57.zip --vystup deploy/procesnimapa_1_0_0_59.zip`
229/0, `check_mapa_flow.py` 139/139, `check_flow.py` 17/17, `check_app.py`
OK (199 prvků, 2241 vzorců). Solution verze `1.0.0.59` > `1.0.0.57`,
`<Managed>0</Managed>` — A2/A4 v pořádku.

Dvě věci jsem ověřil vlastní mutací balíku (ne převzetím tvrzení ze
`STATUS.md`), viz B-02 níže — jedna mutace bránu chytila (HTML escapování),
druhá ji obešla.

### B-01 · VÁŽNÝ · testovací tenant v flow je mimo dosah kontroly hardcoded URL

`check_solution.py` prohledává na `http://`/`https://` **jen soubory
`*.pa.yaml`** canvas appky (řádek 236-249: `for polozka in polozky: if not
polozka.endswith(".pa.yaml"): continue`). `Workflows/*.json` se vůbec
neprochází.

Repro nad rozbaleným `deploy/procesnimapa_1_0_0_59.zip`:
```
grep -o "ppfbanka.sharepoint.com[^\"]*" Workflows/*.json | wc -l
→ AktualizaceKratkehoNazvu: 2, ExportFlow: 2, MapaPublishFlow: 7,
  MapaPublishScheduled: 7   (celkem 18 výskytů ve všech čtyřech flow)
grep -o "ppfbanka.sharepoint.com[^&\"<]*" customizations.xml
→ 1 další výskyt v ConnectionReferences canvas appky
```
Přitom jediné varování, které balík k migraci vydává (`check_solution.py`
řádek 244-247, a stejně tak `HANDOVER.md` řádek 181-183), zní: „adresa mapy
`varMapaUrl` je natvrdo, **je to jediné místo**". To neodpovídá skutečnosti —
`dataset` je natvrdo zapečený v `parameters` akce `Uloz`/`CreateFile`
**každého** ze čtyř flow (`ExportFlow`, `MapaPublishFlow`,
`MapaPublishScheduled`, `AktualizaceKratkehoNazvu`) a v samostatné
`Adresa`-Compose akci `ExportFlow` (`concat('https://…/testovaci_subsajta/procesnimapa/SiteAssets/', …)`).

Kolo 3 (A-08) tohle už jednou pojmenovalo jako „testovací tenant je na
čtyřech místech, ne na jednom" a nechalo to **otevřené**. Kolo 4 přidalo
dvě nová flow (`ExportFlow`, `MapaPublishScheduled`), obě klony s vlastním
`dataset`, takže rozsah **narostl**, a dokumentace (`HANDOVER.md`,
varování v bráně) se od kola 3 nezměnila — pořád mluví jen o jednom místě.

Dopad: dokud je F4 (přenos na MPSV) blokovaný nedostupností tenantu, dnešní
import do PPF testovacího tenantu tím netrpí (`dataset` ukazuje na správný
testovací web důsledně všude). Riziko je výhradně při budoucím přenosu —
kdo bude řešení stěhovat na MPSV a bude se řídit tím, co říká `check_solution.py`
a `HANDOVER.md`, přepojí `varMapaUrl` a bude si myslet, že je hotovo; čtyři
flow zůstanou tiše ukazovat/zapisovat do cizího PPF webu, dokud to někdo
neobjeví ručně v Power Automate designeru.

Checklist: B1 (rozšířeno o Workflows/*.json), NFR-3, kritérium přijetí A6.
Stav: **opraveno** (1.0.0.60) — nález přijat celý.

- `check_solution.py` nově prochází `Workflows/*.json`: každá adresa
  `*.sharepoint.com` musí začínat adresou webu, na který je připojená canvas
  app, jinak brána **selže**. Počet míst vypisuje jako varování (dnes 19).
  Mutačně ověřeno — přesměrování jednoho flow na cizí web bránu shodí.
- `HANDOVER.md` už netvrdí, že `varMapaUrl` je jediné místo; rozlišuje ručně
  psanou adresu mapy (jedna) od 19 míst ve flow, která se **nepíšou ručně**.
- `PLAN.md` krok 12 dostal sedmikrokový postup přenosu v pořadí, ve kterém se
  musí provést, aby build skripty adresu i GUIDy listů převzaly z připojení
  appky.

Podstata nálezu byla v tom, že brána i dokumentace **podhodnocovaly rozsah**;
samotné adresy ve flow chyba nejsou, protože je nikdo nepíše rukou.

### B-02 · STŘEDNÍ · mezera v `check_export_flow.py` — kontrola textového formátu Excelu nekouká na správné pravidlo

Kontrola `kontrakt()` (řádek 359-361) ověřuje jen:
```python
overit(TEXTOVY_FORMAT in akce["Dokument"]["inputs"], …)
```
— tedy že se řetězec `mso-number-format:"\@"` vyskytuje **kdekoli** v celém
textu akce `Dokument`. V šabloně `HLAVICKA_XLS` se ale vyskytuje **dvakrát**:
jednou v pravidle `td {…}` (datové buňky — kód, název, vlastník, stav) a
jednou v `th {…}` (hlavičky sloupců). Kontrola nerozlišuje, na kterém
pravidle formát je.

Repro — mutace, která smaže vynucený text jen z `td {}` a nechá ho v `th {}`
nedotčené (`overit` by v produkci znamenalo návrat přesně té vady, která se
opravovala 25.08.2026: Excel by `01-01` znovu četl jako datum):
```python
# scratchpad, nad kopií deploy/procesnimapa_1_0_0_59.zip
idx = data.find('td {mso-number-format')
end = data.find(';', idx) + 1
mutated = data[:idx] + 'td {' + data[end:]   # smazáno: mso-number-format:"\@";
# 'th {mso-number-format' v textu zůstává
```
```
python src/check_export_flow.py --solution mutace3.zip
→ kontrol: 109
→ OK — ExportFlow odpovídá kontraktu          (mělo by NEPROJÍT)
```
Pro srovnání — mutace odstranění HTML escapování `nazev` **stejným postupem
branou spolehlivě neprojde** (6 chyb, `NEPROŠLO`), takže kontrakt() obecně
funguje; jde o jednu konkrétní mezeru, ne o celkovou nefunkčnost brány.

Dnešní balík **není vadný** — `td {}` pravidlo s `mso-number-format:"\@"`
v `deploy/procesnimapa_1_0_0_59.zip` skutečně je (ověřeno přímo, viz výše).
Jde o mezeru v ověřovacím nástroji: brána, o které `STATUS.md` tvrdí „devět
mutací brána chytila všechny", má desátou mutaci, kterou nechytí — a je to
přesně ta vlastnost (vynucený textový formát datových buněk), kvůli které
Excel export vůbec dostal formát `.xls` místo `.csv`.

Checklist: F3 (ověření skutečného obsahu balíku, ne že build proběhl), E2
(kontrola výsledku, ne jen přítomnosti řetězce).
Stav: **opraveno** (1.0.0.60) — nález přijat.

Kontrola se navázala na konkrétní pravidlo: v kontraktu se hledá
`td {mso-number-format:"\@"`, ve významové vrstvě se `<style>` blok rozebere
a formát se čte z těla pravidla `td`, číselný formát z `td.n`. Mutace, kterou
auditor prošel — smazat formát jen z `td` a nechat ho v `th` — bránu nově
shodí; ověřeno spuštěním, stejně jako druhá mutace (`td.n` bez číselného
formátu). Kontrol 109 → 110.

### B-03 · ESKALACE · Controls/*.json je od 1.0.0.57 bajtově beze změny — vše visí na jednom ručním kroku ve Studiu

Potvrzující nález, ne nová vada v kódu — mechanismus je záměrný a
`check_solution.py` ho sám hlídá (řádek 128-132: `packed.json` musí mít
`LoadConfiguration.LoadFromYaml == true`, jinak „Studio by načetlo zastaralé
Controls/*.json"). Zapisuji ho, protože jsem si ověřil **rozsah**, na jakém
dnes tenhle mechanismus stojí, a je větší, než by se ze `STATUS.md` čekalo.

Repro — porovnání `.msapp` uvnitř `input/procesnimapa_1_0_0_57.zip` (poslední
verze prošlá reálným Studiem, „Add data → ExportFlow") a
`deploy/procesnimapa_1_0_0_59.zip` (dnešní balík, poskládaný lokálně skriptem
`build_app.py` přes `pac canvas unpack/pack`):
```
md5sum sol57/msapp57/Controls/{1,4,79,122,145}.json
md5sum sol59/msapp/Controls/{1,4,79,122,145}.json
→ všech pět souborů má STEJNÝ md5 v obou verzích
grep -c '"Name": "btn_ExportMenu"' sol59/msapp/Controls/4.json
→ 0   (tlačítko Export v pa.yaml existuje, v Controls/4.json ne)
```
`Src/scr_Dashboard.pa.yaml` uvnitř `.msapp` je přitom bajtově shodné
s `src/app_src/scr_Dashboard.pa.yaml` v repu — tedy obsahuje `btn_ExportMenu`,
`btn_ExportWord`, `btn_ExportExcel` i všechny rozvržení z 1.0.0.58/59.

Jinými slovy: v **zabaleném `.msapp`, který se importuje**, neexistuje ani
tlačítko Export, ani zúžené karty, ani odpojení tlačítek od velikosti
písma — nic z toho, co `STATUS.md` popisuje jako hotové v 1.0.0.58 a 1.0.0.59.
Existuje to jen v `Src/*.pa.yaml`. Materializuje se to teprve tehdy, když
Studio po importu appku otevře (LoadFromYaml=true řekne Studiu číst YAML)
a uživatel udělá **mikro-změnu → Save → Publish** — to Controls/*.json
skutečně přepočítá z YAML a teprve tenhle krok appku „dopeče" do stavu, který
`STATUS.md` popisuje.

`STATUS.md` tenhle krok už vyžaduje na prvním řádku („import jako upgrade,
pak ve Studiu mikro-změna → Save → Publish") a `deploy/flow_Export.md` ho
opakuje. Nejde tedy o objevenou mezeru v procesu — je to eskalace, protože:
- **nic v balíku ani v žádné bráně needá signál, že krok proběhl** — pokud
  se vynechá nebo se v Studiu neuloží (např. uživatel zavře kartu bez Save),
  appka v provozu tiše zůstane na úrovni 1.0.0.57 a nikdo to z importu
  samotného nepozná;
- rozsah, který na tomhle kroku dnes visí, je větší než u předchozích
  balíků — týká se **všech čtyř obrazovek** najednou (Controls/1.json,
  4.json, 79.json, 122.json, 145.json jsou identické se 1.0.0.57 do
  posledního bajtu), ne jen jedné dílčí úpravy.

Nejde o BLOKUJÍCÍ, protože mechanismus je stejný, jaký appka používá od
začátku (viz A-08/kolo 3, „duch v `.msapp`"), je ověřený v provozu (uživatel
opakovaně potvrdil funkčnost přes screenshoty) a `check_solution.py` jedinou
podmínku, která ho dělá bezpečným (`LoadFromYaml=true`), aktivně hlídá.
Rozhoduje uživatel, jestli mu tenhle rituál (ruční krok bez automatické
kontroly, že proběhl) po každém importu vyhovuje, nebo jestli má smysl
hledat jinou cestu (např. že hlavní asistent po každém buildu sám ověří
proti poslední Studiem uložené verzi, ne jen proti pa.yaml).

Checklist: C1 (Controls/*.json vs Src/*.pa.yaml — obecné pravidlo skillu
zde neplatí doslova, protože LoadFromYaml mechanismus je jiný a záměrný,
ale riziko, které C1 popisuje, je reálné, dokud se ruční krok nepotvrdí).
Stav: **zmírněno** (1.0.0.60) + **ověřeno provozem**; eskalace uzavřena.

Věcně: mechanismus `LoadFromYaml` **prokazatelně funguje**. Tlačítko Export
existuje jen v `Src/*.pa.yaml` — `Controls/*.json` jsou bajtově z 1.0.0.57,
tedy z doby, kdy Export ještě neexistoval — a uživatel s ním 25.08.2026
v provozu exportoval do Wordu i do Excelu. Kdyby Studio četlo Controls,
tlačítko by v appce nebylo. Tím padá i N-06.

Zůstávala platná část nálezu: z běžící appky se nedalo poznat, **která verze**
je publikovaná. Doplněno razítko — `build_app.py` dosazuje do `App.OnStart`
`Set(varVerze, "<verze balíku>")` a nápověda u názvu appky v pruhu ho ukazuje
i s vysvětlením, co znamená, když nesedí. Build selže, když razítko v YAML
nenajde, takže nemůže tiše vypadnout.

## Ověřeno spuštěním — kolo 4

| příkaz | výsledek |
|---|---|
| `unzip -t deploy/procesnimapa_1_0_0_59.zip` | bez chyby |
| `unzip -t` vnořeného `.msapp` | bez chyby (varování o `\` v cestách — stejné už v 1.0.0.57, produkuje ho `pac` CLI, ne tento projekt) |
| `check_export_flow.py --solution deploy/procesnimapa_1_0_0_59.zip` | 109/109 |
| `check_solution.py --vstup input/procesnimapa_1_0_0_57.zip --vystup deploy/procesnimapa_1_0_0_59.zip` | 229/0, 1 varování (jen `varMapaUrl`, viz B-01) |
| `check_mapa_flow.py --solution deploy/procesnimapa_1_0_0_59.zip` | 139/139 |
| `check_flow.py --solution deploy/procesnimapa_1_0_0_59.zip` | 17/17 |
| `check_app.py` | OK — 5 souborů, 4 obrazovky, 199 prvků, 2241 vzorců (2 nezávazná VAROVÁNÍ o `Sort` v `Items`, pre-existující, mimo rozsah kola 4) |
| mutace `build_export_flow.py` spuštěná 2× nad týmž zipem | GUID i obsah beze změny — idempotentní, ověřeno, ne převzato z docstringu |
| mutace: odstraněné HTML escapování `nazev` v `ExportFlow` | `check_export_flow.py` → 6 chyb, `NEPROŠLO` (brána funguje) |
| mutace: `mso-number-format` odstraněný jen z `td {}`, ponechaný v `th {}` | `check_export_flow.py` → 109/109, `OK` (viz B-02, brána tuhle mezeru nemá) |
| `solution.xml`: verze, `Managed` | `1.0.0.59` > `1.0.0.57` (referenční „před"), `<Managed>0</Managed>` |
| `Properties.json` v `.msapp` | `DefaultConnectedDataSourceMaxGetRowsCount: 2000` — shoda s 1.0.0.57, A-03 z kola 3 drží |
| `References/DataSources.json` | `ExportFlow` registrován, `FlowNameId` odpovídá `deploy/flow_Export.md` |

## Neověřeno — kolo 4

### N-04 · chování `Download()` v appce vložené na SharePoint stránku
`STATUS.md` řeší nejistotu `fetch`/stahování z JS pro HTML mapu v sandboxu
SharePointu, ale `Download()` je nativní funkce Power Apps runtime (běží ve
vlastním iframe), ne JS v šabloně stránky — technicky jiná situace. Bez
přístupu k reálně vloženému webpartu na SharePoint stránce nejde ověřit, že
`Download(varExportUrl)` v `scr_Dashboard.pa.yaml` v tomhle konkrétním
kontextu (embedded canvas app, ne samostatný player) skutečně spustí stažení
místo tichého selhání. Potřeba: appka vložená na skutečné SharePoint stránce
+ klik na Export.

### N-05 · injekce vzorců do buněk Excelu (CSV/HTML formula injection)
Textová pole (`nazev`, `vlastnik`) nejsou omezena na to, aby nezačínala
`=`, `+`, `-`, `@`. `mso-number-format:"\@"` vynucuje zobrazení jako text,
ale nemám jak bez reálného Excelu ověřit, jestli tím Excel spolehlivě
potlačí i vyhodnocení vzorce (na rozdíl od skutečného `.csv`, kde je to
známá díra) — HTML import do Excelu se může chovat jinak. Potřeba: otevřít
reálně vyexportovaný `.xls` v Excelu s řádkem, jehož `nazev` začíná `=1+1`.

### N-06 · reálné chování Studia při `LoadFromYaml=true` po importu — **UZAVŘENO**

Ověřeno provozem 25.08.2026, viz stav u B-03: tlačítko Export je jen v YAML,
a přesto v běžící appce funguje. Text níže je původní znění nálezu.
B-03 stojí na mechanismu, který `build_app.py` a `check_solution.py`
explicitně předpokládají a hlídají (`LoadFromYaml: true`), a `STATUS.md`
dokládá opakovanou funkčností v provozu (screenshoty). Nejde ale ověřit
lokálně/staticky, že Studio po **tomhle konkrétním** importu skutečně
Controls/*.json přepočítá při Save — jde o chování cizí platformy, ne o
obsah balíku. Potřeba: reálný import 1.0.0.59, otevření ve Studiu,
mikro-změna, Save, a až pak porovnání vyexportovaného `.msapp`.

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
| A-08 zbytky a natvrdo zapsané hodnoty | duchové v `.msapp` opraveni, zbytek otevřený — **rozsah narostl, viz B-01 v kole 4** |

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
(`nastav_limit_radku`), `check_solution.py` to hlídá. Ověřeno v balíku
— **znovu potvrzeno v kole 4** (Properties.json v 1.0.0.59 stále 2000).

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
- **Model v publikačním flow má natvrdo `"sekce": "3"` a jméno správce** —
  po rozšíření mimo sekci 3 bude hlavička mapy lhát.
- **`$top: 5000` bez `paginationPolicy`** je strop pro aktivity v mapě.
- **Testovací tenant je při přenosu na MPSV na čtyřech místech** (`varMapaUrl`
  a `dataset` ve třech flow), ne na jednom — **v kole 4 rozšířeno na B-01**:
  po přidání `ExportFlow` a `MapaPublishScheduled` je to `dataset` ve
  **čtyřech** flow + connection reference v appce, tedy pět míst, a
  dokumentace pořád mluví o jednom.

### A-09 · OTEVŘENÉ · sjednocení editace vzalo seznamu aktivit delegaci

Doplněno 23.08.2026 při vysvětlování limitu — není to nález auditora, ale
důsledek F6/F, který je fér pojmenovat.

Zrušený `scr_Seznam` měl filtry sekce, útvar a stav postavené jako
**delegovaný** dotaz nad listem `Aktivity`: běžely na serveru nad celým
rejstříkem a limit se dotýkal jen fulltextu. Po sjednocení editace stojí
seznam aktivit nad `colCiselnik`, tedy nad kolekcí odvozenou z `colAkt` —
a ta je omezená stropem 2 000 řádků vždycky.

Pro dnešní data (47 aktivit) to nic nemění a čitelnost obrazovky za to
stála. Je to ale skutečná ztráta, ne detail: nad 2 000 aktivitami by seznam
přestal být úplný, aniž by to řekl.

**Řešení je připravené** v `PLAN.md`, sekce „Připravený plán: rejstřík nad
2 000 aktivitami", bod K3. Odloženo rozhodnutím zadavatele.

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
