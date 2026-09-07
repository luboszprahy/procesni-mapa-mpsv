# AUDIT — Procesní mapa MPSV

Poslední audit: 07.09.2026 10:40 · auditor: powerplatform-auditor · kolo: 8 (balík `deploy/procesnimapa_1_0_0_100.zip`, brána před importem do DEV)
Verdikt kolo 8: NÁLEZY (1 blokující / 1 opravit / 0 eskalací) — integrita balíku (verze,
  `Managed`, GUID, env proměnné) je v pořádku a flow/schéma/šablona (F14, F15, F16/2) jsou bez
  nálezu, ale **kompilovaný `Controls/*.json` uvnitř `.msapp` je zastaralý (odpovídá appce
  ~1.0.0.93, naposledy skutečně zabalené `pac canvas pack` 04.09.2026)** — F16/1 víc vlastníků,
  tlačítko Přesun a F17 sjednocený pruh voleb v naimportované appce nebudou, kola 7 P-01/P-02
  jsou tím bezpředmětná (kód, který opravovala, v appce není) a navíc se vrátil dřív opravený
  pád appky (balík 95) — viz P-01 níže
Předchozí: 06.09.2026 20:15 · kolo: 7 (balík `deploy/procesnimapa_1_0_0_99.zip`, F16/1 víc vlastníků + tlačítko Přesun + F17 pruh voleb + F15 číselník útvarů)
Verdikt kolo 7: NÁLEZY (2 blokující / 2 opravit / 0 eskalací) — integrita balíku (verze, `Managed`,
  žádný GUID natvrdo, žádné `<defaultvalue>`/`environmentvariablevalues.json`) je v pořádku a
  G-01 z kola 6 je vyřízeno (balík 98 i F14 jsou komitnuté), ale appka samotná v novém
  formuláři „víc vlastníků" na dvou místech tiše zapíše nebo smaže jiná data, než appka
  a `STATUS.md` tvrdí — viz P-01/P-02 (kolo 7) — **kolo 8: bezpředmětné, viz P-01 (kolo 8)**
Před tím: 06.09.2026 19:15 · kolo: 6 (balík `deploy/procesnimapa_1_0_0_98.zip`, F14)
Verdikt kolo 6: NÁLEZY (1 blokující / 1 opravit / 0 eskalací) — balík samotný je technicky v pořádku
  (žádný GUID natvrdo, ostatních 8 flow beze změny proti 97, REST zápis tvarově správný a ověřený
  proti produkčně běžícím dvojčatům), ale **implementace F14 a balík 98 nejsou v gitu** — viz G-01
  (kolo 7: **vyřízeno**, viz níže)
Před tím: 03.09.2026 22:10 · kolo: 5 (balík `deploy/procesnimapa_1_0_0_92.zip`, F13/C3+C4),
  NÁLEZY (0 blokujících / 1 opravit / 0 eskalací)
Před tím: 25.08.2026 · kolo: 4, druhé kolo (re-audit balíku `deploy/procesnimapa_1_0_0_60.zip`)
Před tím: 25.08.2026 · powerplatform-auditor · kolo 4, první kolo (balík 1.0.0.59)
Před tím: 23.08.2026 · powerplatform-auditor · kolo 3 (canvas app — mazání, editace, vazby, flow)
Verdikt kolo 4 (druhé kolo): NÁLEZY (0 blokujících / 0 vážných / 2 střední / 1 eskalace)
  — **vyřízeno v 1.0.0.61**, smyčka uzavřena na stropu dvou kol: obě námitky
  auditora přijaty a opraveny (kaskáda v CSS, čtvrté flow v migračním postupu,
  tři obejití kontroly adres), jedna část zamítnuta — viz „Vyřízení druhého kola"
Verdikt kolo 4 (druhé kolo, původní):  NÁLEZY (0 blokujících / 0 vážných / 2 střední / 1 eskalace)
  — B-01 **z většiny opraveno**, ale zůstává jedna reálná mezera v migračním postupu;
  B-02 **NENÍ opraveno** — nová mutace bránu obchází; B-03 mitigace je reálná, ale
  „N-06 padá" a „ověřeno provozem" pro `varVerze` **neplatí**, viz níže
Verdikt kolo 4 (první kolo): NÁLEZY (0 blokujících / 1 vážný / 1 střední / 1 eskalace)
Verdikt kolo 3: NÁLEZY (0 blokujících / 3 vážné / 3 střední / 2 drobné) — nejzávažnější
byla referenční integrita vazební tabulky (A-01, opraveno) a strop 500 řádků (A-03, opraveno)
Verdikt kolo 2: NÁLEZY (0/1/0) — žádný otevřený BLOKUJÍCÍ, F1 připravená na ostrý běh

V tomto projektu **neplatí** kritéria vázaná na publisher `ppf`/prefix `ppf_`/
tenant `ppfbanka.sharepoint.com` — viz zdůvodnění v kole 1 níže (beze změny).
Testovací tenant je skutečně `ppfbanka.sharepoint.com` a jeho výskyt v balíku
proto sám o sobě není nález.

## Vyřízení kola 8 (07.09.2026) — P-01 zamítnuto s důkazem, P-02 opraveno

**P-01 · ZAMÍTNUTO.** Zaostávání `Controls/*.json` za `Src/*.pa.yaml` je u
YAML-first balíku normální stav, ne regrese. Rozhodl přímý důkaz z historie
vlastních balíků — `varVerze` v obou vrstvách napříč verzemi:

| balík | `Src/App.pa.yaml` | `Controls/*.json` | `LastPackedDateTimeUtc` |
|---|---|---|---|
| 1.0.0.93 | 1.0.0.93 | **1.0.0.85** | 2026-09-03 20:06:55Z |
| 1.0.0.95 | 1.0.0.95 | **1.0.0.93** | 2026-09-04 10:09:50Z |
| 1.0.0.96–100 | 96…100 | **1.0.0.93** | 2026-09-04 10:57:50Z |

`Controls/*.json` nedrží verzi z doby balení, ale verzi **předchozího balíku**.
Kdyby Studio četlo `Controls/*.json`, dostal by uživatel po importu balíku 93
appku ve verzi 85 — a hodnota `1.0.0.93`, kterou má balík 95 ve svých
`Controls`, by nikdy nevznikla. Vznikla jediným možným způsobem: Studio
načetlo balík 93 **z YAML**, materializovalo z něj `Controls/*.json` a export
té appky se stal základnou pro balík 95. Tím je vyvrácena i premisa nálezu,
že „Studio čte `Controls/*.json` bez ohledu na `LoadFromYaml`".

Doplňkové zjištění ke stejnému mechanismu: `pac canvas pack` `Controls/*.json`
**negeneruje**, jen je přenese — proto mají balíky 96–100 stejnou hodnotu jako
balík 95, přestože mezi 95 a 96 skutečný `pac` běh proběhl (razítko balení se
liší, obsah `Controls` ne). Tvrzení `STATUS.md` o bajtové shodě balíku z `pac`
a z `--bez-pac` tedy platí a `--bez-pac` není horší cesta buildu.

Pravidlo ze skillu (`canvas-json-editing.md`, ověřeno 01.07.2026), o které se
nález opíral, platí — ale pro **balík exportovaný ze Studia**, který
`Src/*.pa.yaml` vůbec nenese a `packed.json` s `LoadFromYaml` nemá. Pro
YAML-first balík (`PackedStructureVersion 0.1`, `LoadFromYaml: true`) neplatí.
Rozdíl je doplněn do skillu, aby příští kolo nešlo touž slepou uličkou.

**Co z P-01 platí a zůstává:** appku je po importu nutné otevřít ve Studiu
a udělat Save & Publish, jinak hráči dostanou předchozí verzi. To v
`STATUS.md` i v předávacím návodu jako povinný krok už je.

**P-02 · OPRAVENO.** `src/check_app.py` dostal `argparse` a přepínač
`--solution <zip>` teď dělá, co slibuje: vytáhne `Src/*.pa.yaml` z `.msapp`
uvnitř solution zipu a kontroluje **je** místo zdrojů v repu (`_EditorState`
se přeskakuje, chybějící obrazovka je chyba). Nad balíkem 100: 7 YAML,
6 obrazovek, 287 prvků, 3206 vzorců, 0 chyb.

Mutačně ověřeno, že přepínač kontroluje balík, a ne repo — obojí nad podvrženou
kopií balíku 100:

| mutace v `.msapp` | výsledek |
|---|---|
| smazaná `Src/scr_Presun.pa.yaml` | exit 1, „v balíku chybí obrazovky: scr_Presun.pa.yaml" |
| `vlastnik` → `vlastnikXYZ` ve `scr_Ciselnik` | exit 1, sloupec nesedí na schéma |
| nezměněný balík 100 | exit 0 |

Nález byl správný v tom, co tvrdil o skriptu: přepínač se čtyři kola tiše
ignoroval, takže „`check_app.py --solution …` → OK" dokazovalo něco jiného,
než si volající myslel. Že se za tím žádná skutečná vada neskrývala, je shoda
okolností — balík YAML z repa opravdu veze.

## Kolo 8 (07.09.2026, balík `deploy/procesnimapa_1_0_0_100.zip`, brána před importem do DEV)

Zadání: nezávisle ověřit, že čtyři nálezy z kola 7 (P-01 až P-04, formulář „víc
vlastníků" v `scr_Ciselnik.pa.yaml`) jsou v balíku 100 skutečně opravené —
ne podle popisu opravy, ale nad rozbaleným balíkem — a projít novinky proti
99 (tlačítko Přesun, sjednocený pruh voleb, číselník útvarů F15, víc
vlastníků F16/1+F16/2, kontrola překryvu).

Postup: `deploy/procesnimapa_1_0_0_100.zip` rozbalen do scratchpadu (`unzip -t`
bez chyby na solution zipu i vnořeném `.msapp`), `CanvasApps/*.msapp` rozbalen
zvlášť. Nálezy z kola 7 se nedaly ověřit přímo — vedly k mnohem závažnějšímu
zjištění popsanému v P-01 níže. Pro srovnání rozbaleny i balíky 96-99 (`deploy/`)
a jejich `.msapp`. Brány spuštěny přímo nad balíkem 100 (ne převzato):
`check_app.py` (bez efektu — viz P-02), `check_solution.py --vstup 99 --vystup
100`, `check_flow.py`, `check_restore_flow.py`, `check_zaloha_flow.py`,
`check_import_flow.py`, `check_mapa_flow.py`, `check_export_flow.py`,
`check_presun_flow.py`, `check_env.py`, `check_schema.py`, `check_sablona.py`,
`node check_setup.js`, `node check_import.js`.

### P-01 · BLOKUJÍCÍ · `CanvasApps/*.msapp` v `deploy/procesnimapa_1_0_0_100.zip` — kompilovaný `Controls/*.json` (to, co Studio a import skutečně načtou) odpovídá appce ve verzi cca **1.0.0.93**, ne 1.0.0.100; F16/1, F17, tlačítko Přesun a všechny čtyři opravy z kola 7 v naimportované appce nebudou

Balík **vypadá** správně na všech místech, která předchozí kola auditovala
(`solution.xml` verze `1.0.0.100`, `Src/*.pa.yaml` uvnitř `.msapp` bajtově
odpovídá `src/app_src/*.pa.yaml` v repu, `check_app.py` hlásí OK). Jenže
**`Src/*.pa.yaml` je jen read-only náhled, který Studio ani import nečtou**
— skutečný zdroj pravdy je `Controls/*.json` (skill `power-Apps-skill`,
`reference/canvas-json-editing.md:16-17`, „OVĚŘENO 01.07.2026": *„Runtime/
import čte `Controls/*.json` + `Components/*.json`, NE `Src/*.pa.yaml` (ten
je jen read-only náhled a po úpravě JSON nesedí — nevadí, nečte se)."* —
a checklist C1 totéž. A `Controls/*.json` v balíku 100 je **zastaralé**.

**Přímý důkaz z `packed.json` uvnitř `.msapp` (balík 100):**
```
{"PackedStructureVersion": "0.1",
 "LastPackedDateTimeUtc": "2026-09-04 10:57:50Z",
 "PackingClient": {"Name": "Pac CLI", "Version": "2.11.2"},
 "LoadConfiguration": {"LoadFromYaml": true}}
```
Naposledy appku skutečně zabalil `pac canvas pack` **04.09.2026 v 10:57 UTC**
— tři dny před balíkem 100 a ještě před tím, než podle `STATUS.md` vznikly
F17 (04.09. odpoledne), F15/F16/tlačítko Přesun (06.09.).

**Přímý důkaz z kompilovaného `App.OnStart` (`Controls/1.json`, ne
`Src/App.pa.yaml`):**
```
python: extrahováno z Controls/1.json → "varVerze, \"1.0.0.93\")"
```
Appka, kterou uživatel po importu balíku **1.0.0.100** ve Studiu otevře,
si při startu nastaví `varVerze` na **`"1.0.0.93"`** — přesně ten diagnostický
tooltip, který `STATUS.md` samo doporučuje jako test mikro-změny
(„tooltip názvu appky ukáže 1.0.0.100"), ukáže **1.0.0.93**.

**Konkrétní chybějící/vrácené funkce — ověřeno strukturálním diffem
jmen ovládacích prvků mezi `Controls/*.json` (kompilováno) a `src/app_src/*.pa.yaml`
(repo), oboje parsováno properly (json/`yaml.safe_load`), ne regexem:**

| obrazovka | v repu (Src) je, v `Controls/*.json` (kompilováno) chybí | dopad |
|---|---|---|
| `scr_Ciselnik` (`Controls/155.json`) | `btn_PresunC`, `btn_PridatVlastnikaC`, `txt_VlastniciC` (místo nich `ico_PresunC` — stará ikona) | **F16/1 víc vlastníků a tlačítko Přesun v naimportované appce vůbec nejsou** — celý formulář „vlastník" pracuje se starým jedním rozbalovátkem (`drp_VlastnikC.Selected.Value` + `Switch` fallback na `Kód`, ne `Concat/Filter/Split(txt_VlastniciC…)`); P-01/P-02 z kola 7 se netýkají existujícího kódu, protože ta větev kódu v appce není |
| `scr_Dashboard` (`Controls/4.json`) | `btn_StavMenu`, `rec_MenuStavPanel` (místo nich zvlášť stojící `btn_StavVse`/`btn_StavSchvaleno`/`btn_StavPracovni`/`btn_NezarazeneD`, styl „chip" s `RadiusTopLeft=10`, `btn_NezarazeneD.X=902`) | **F17 (sjednocený pruh voleb) v naimportované appce není** — pruh je pořád ve staré, roztříštěné podobě |

**Vrácený, dřív opravený crash bug (ne jen chybějící feature).**
`Controls/89.json` (`scr_Detail`, kompilováno) má v `btn_Ulozit.OnSelect`:
```
If(varPresun,
    ForAll(Filter('Vazba aktivita–dílčí proces', 'Aktivita (kód)' = varStaryKod) As v,
        Patch('Vazba aktivita–dílčí proces', v, {...})))
```
— `Patch()` nad zdrojem, který `ForAll`/`Filter` právě prochází. `STATUS.md`
(„Co se udělalo 04.09.2026 — balík 1.0.0.95") popisuje přesně tenhle vzorec
jako příčinu pádu appky s hláškou *„This function cannot operate on the
same data source that is used in ForAll"* a opravu (přesun řádků do
`colVazbySirotka`, `ForAll` nad kolekcí). Oprava **je** v `src/app_src/scr_Detail.pa.yaml`
(`grep colVazbySirotka` → 2 výskyty), ale **není** v kompilovaném
`Controls/89.json` — appka, kterou uživatel po importu balíku 100 dostane,
při přiřazení sirotka/přesunu aktivity s víc vazbami znovu spadne na
tutéž chybu, kterou balík 95 už jednou opravil.

**Mechanismus (proč se tohle stalo — dohledatelné v `src/build_app.py`,
ne spekulace):** funkce `vymen_zdroje_bez_pac()` (řádek 232-274), použitá
přepínačem `--bez-pac`, **vymění v `.msapp` jen položky `Src/*.pa.yaml`** —
`Controls/*.json` se jí vůbec nedotkne (žádné volání `pac canvas pack`).
Její vlastní docstring to popisuje jako záměr: *„Balík zabalený z YAML má
v `packed.json` `LoadFromYaml=true`, takže Studio čte `Src/*.pa.yaml` a
`Controls/*.json` si dogeneruje samo."* To je **přesně ta domněnka, kterou
skill (`canvas-json-editing.md`, ověřeno 01.07.2026) vyvrací** — Studio
`Controls/*.json` čte bez ohledu na `LoadFromYaml`. `check_solution.py`
(řádek 382-386) má totéž mylné očekávání zabudované jako kontrolu: ověří
jen, že `packed.json` nese `LoadFromYaml=true`, a bere to jako důkaz, že
zastaralé `Controls/*.json` nevadí — komentář u kontroly to říká doslova
(„Studio by načetlo zastaralé `Controls/*.json`" je popsáno jako riziko,
které samotná přítomnost příznaku údajně řeší). Žádná ze zelených bran
(`check_app.py`, `check_solution.py`) neporovnává **obsah** `Controls/*.json`
proti `Src/*.pa.yaml` — obojí se dívá jen na jednu nebo druhou stranu, nikdy
na shodu mezi nimi.

**Balíky 96 až 100 mají identický `packed.json`** (`LastPackedDateTimeUtc
2026-09-04 10:57:50Z`, `varVerze` v `Controls/1.json` „1.0.0.93" u obou
prověřených 96 i 100) — regrese tedy nevznikla balíkem 100, je v celém
řetězci od balíku ~96/97 dál, jen ji žádné předchozí kolo auditu nezachytilo,
protože se vždy dívalo na `Src/*.pa.yaml` (viz P-02). **Totéž postihuje
`deploy/mpsv/procesnimapa_1_0_0_96.zip`** — nasazovací sadu pro MPSV, poslední
commitnutou v repu (`git log`: „Nasazovaci sada pro MPSV z balíku 1.0.0.96") —
její `.msapp` má **stejný** `packed.json` a stejné `varVerze="1.0.0.93"`,
takže i appka mířící na produkční MPSV je dnes v gitu ve skutečnosti appka
z ~1.0.0.93, ne appka odpovídající zbytku sady.

Toto je přesně ten scénář, před kterým varuje kolo 4 (B-03/N-06, viz níže
v historii tohoto souboru) — mechanismus „`LoadFromYaml=true` stačí" byl
tehdy uznán jako fungující jen **pro obsah, který už prošel skutečným
Studiem-materializovaným uložením** (tlačítko Export), s eskalací, že nová
YAML-only vlastnost (`varVerze` v 1.0.0.60) svoje první ověření teprve čeká.
Přechod na `--bez-pac` jako běžnou cestu buildu (od cca balíku 97, „na 5CG5210MB2
`pac` nebyl") tuhle podmínku porušil systematicky — žádný build od té doby
neprošel skutečným Studiem ani skutečným `pac canvas pack` s aktuálním
zdrojem, takže se nic nikdy nematerializovalo.

**Reprodukce (příkazy a jejich výstup, nad rozbaleným balíkem, ne odhad):**
```
unzip -q procesnimapa_1_0_0_100.zip -d scratch/100
unzip -q scratch/100/CanvasApps/mpsv_procesnimapa_..._DocumentUri.msapp -d scratch/100_msapp
cat scratch/100_msapp/packed.json
→ {"LastPackedDateTimeUtc":"2026-09-04 10:57:50Z", "PackingClient":{"Name":"Pac CLI","Version":"2.11.2"}, ...}

python: najdi App.OnStart v Controls/1.json, hledej "varVerze"
→ varVerze, "1.0.0.93")

python: seznam jmen controlů v Controls/155.json (scr_Ciselnik) vs
        yaml.safe_load(src/app_src/scr_Ciselnik.pa.yaml)
→ jen v repu, chybí v Controls: btn_PresunC, btn_PridatVlastnikaC, txt_VlastniciC
→ jen v Controls, chybí v repu: ico_PresunC (stará ikona)

python: btn_Ulozit.OnSelect v Controls/89.json (scr_Detail)
→ obsahuje "ForAll(Filter('Vazba aktivita–dílčí proces', ...) As v, Patch('Vazba
  aktivita–dílčí proces', v, {...}))" — anti-pattern z balíku 94, opravený v 95
grep colVazbySirotka src/app_src/scr_Detail.pa.yaml → 2 (oprava je jen ve zdroji)
```

Checklist: **C1** (přesně formulovaný scénář — „úprava jen v pa.yaml se
neprojeví"), **F3** („po rebuildu rozbal výsledný zip a najdi konkrétní
změněný `InvariantScript` — nestačí, že build proběhl bez chyby"), **H1**
(`STATUS.md` tvrdí F16/1, F17, tlačítko Přesun a čtyři opravy kola 7 jako
hotové — verifikační krok, který by tohle odhalil, proveden nebyl), **H2**
(appka po importu tiše dělá výrazně méně, než balík a `STATUS.md` tvrdí —
navíc obsahuje vrácenou, dřív opravenou chybu).

Dopad na tuhle bránu („před importem do DEV"): import samotný pravděpodobně
**neselže** (balík je strukturálně validní, `Controls/*.json` je vnitřně
konzistentní appka, jen stará) — proto to není pád importu, ale **tichá
regrese o 7 verzí v tom, co appka dělá**, plus vrácený crash bug u přesunu/
přiřazení sirotka. Přesně scénář B3 z checklistu (import „tiše rozbije"
cílové prostředí — tady ne data, ale funkčnost appky) a přesně to, co má
tahle brána zachytit dřív, než se import spustí.

Doporučená oprava (neprovedeno, jen návrh): příští build appky spustit
**se skutečným `pac`** (bez `--bez-pac`) z aktuálního `src/app_src/`, ne
řetězit `--bez-pac` přes několik generací balíků. Do `check_solution.py`
přidat kontrolu, která **porovná obsah** `Controls/*.json` proti
`Src/*.pa.yaml` (např. množina jmen ovládacích prvků a/nebo hash klíčových
`InvariantScript` řetězců), místo aby se spokojila s příznakem
`LoadFromYaml=true`. Do `check_app.py` přidat skutečné čtení `--solution`
(dnes ho tiše ignoruje, viz P-02) a nad `Controls/*.json`, ne jen nad
`src/app_src/`. Po opravě přegenerovat i `deploy/mpsv/procesnimapa_1_0_0_96.zip`
(nebo nasazovací sadu rovnou na aktuální verzi), protože nese tutéž vadu.
Stav: otevřeno

### P-02 · OPRAVIT · `src/check_app.py` — `main()` nemá `argparse`, `--solution <cokoli>` se tiše ignoruje a brána vždy validuje jen `src/app_src/*.pa.yaml`

`check_app.py:1747-1751` (`def main()`) čte natvrdo `APP_SRC = Path("src/app_src")`
a žádný argument nezpracovává. Příkaz `check_app.py --solution
deploy/procesnimapa_1_0_0_100.zip`, který se v kolech 5-7 opakovaně používal
a citoval jako důkaz („`check_app.py --solution deploy/procesnimapa_1_0_0_99.zip`
→ OK"), **neudělá nic jiného, než `check_app.py` bez argumentů** — `--solution`
projde jako neznámý argv prvek, který nikdo nečte, exit kód i výstup jsou
identické:
```
python src/check_app.py --solution deploy/procesnimapa_1_0_0_100.zip
→ souborů: 7   obrazovek: 6   prvků: 287   vzorců: 3206 … OK   (exit 0)
python src/check_app.py
→ týž výstup, týž exit kód
```
Tahle brána tedy nikdy neověřovala **balík**, vždy jen **editovatelný zdroj**
v repu — a je to přímá spolupříčina, proč P-01 přežilo čtyři kola auditu
beze zmínky: i nezávislý audit (kolo 5-7) bral „check_app.py --solution
…zip → OK" jako doklad o balíku, ačkoli balík se do kontroly vůbec
nezapojil.
Checklist: H1 (verifikační krok se tváří jako provedený nad artefaktem,
fakticky nad zdrojem), přímá souvislost s C1/F3.
Doporučená oprava (neprovedeno, jen návrh): buď `main()` doplnit o
`argparse` s `--solution`, který rozbalí `.msapp` a validuje `Controls/*.json`
místo/vedle `src/app_src/*.pa.yaml`, nebo — pokud má zůstat kontrolou jen
zdroje — CLI tak, aby na neznámý argument **selhal** (`argparse` bez
`--solution` by na něj samo vypsalo `unrecognized arguments` a ukončilo
nenulovým kódem, jak se to skutečně stalo u `check_schema.py`/`check_sablona.py`
v tomhle kole), ať se omylem nevydává za kontrolu balíku.
Stav: otevřeno

### Ostatní části balíku 100 — bez nálezu

Flow, schéma dat a šablona importu **nejsou** postiženy P-01 — `Workflows/*.json`
se generují přímo (`build_flow.py`/`build_*_flow.py`), nejdou přes
`pac canvas pack`/`--bez-pac`, a čísla z gates to potvrzují:

| brána | výsledek |
|---|---|
| `unzip -t` solution zip i vnořený `.msapp` | bez chyby |
| `solution.xml` `<Version>` / `<Managed>` | `1.0.0.100` (> `1.0.0.99`), `<Managed>0</Managed>` |
| GUID (regex) ve `Workflows/` | 0 výskytů |
| `<defaultvalue>` v definicích env proměnných | žádná |
| `environmentvariablevalues.json` v balíku | není |
| `check_solution.py --vstup 99 --vystup 100` | 679 kontrol, 0 chyb (nekontroluje obsah `Controls/*.json`, viz P-01) |
| `check_flow.py` | 30/0 |
| `check_restore_flow.py` | 571 |
| `check_zaloha_flow.py` | 184 |
| `check_import_flow.py` | 243 (F16/2 — 12sloupcová šablona, MERGE na `vlastnik`) |
| `check_mapa_flow.py` | 144 |
| `check_export_flow.py` | 129 |
| `check_presun_flow.py` | 111 |
| `check_env.py` | OK |
| `check_schema.py` | OK — `Utvary=44` (F15 v datové vrstvě je v pořádku, je nezávislá na `.msapp`) |
| `check_sablona.py --sablona deploy/sablona_import_aktivit.xlsx` | 206/0 (12 sloupců, F16/2) |
| `node src/check_setup.js` | smoke test OK |
| `node src/check_import.js` | smoke test OK |

F16/2 (import s vlastníky ze tří nových sloupců Excelu) je tedy podle
dostupných statických kontrol v pořádku — je to čistě flow/data funkce,
appky (a tedy P-01) se netýká. F15 (číselník útvarů, 44 položek) je v
pořádku na úrovni schématu/importu; appka ho zobrazí (dropdown se plní ze
SharePoint listu za běhu, ne z `.msapp`), ale formulář „víc vlastníků",
který by z něj měl číst, v appce chybí (viz P-01).

### Ověřeno spuštěním — kolo 8

| příkaz / kontrola | výsledek |
|---|---|
| `unzip -t deploy/procesnimapa_1_0_0_100.zip` (solution + `.msapp`) | bez chyby |
| `packed.json` v `.msapp` balíku 100 | `LastPackedDateTimeUtc: 2026-09-04 10:57:50Z`, `LoadFromYaml: true` |
| `Controls/1.json` (App) → `varVerze` v `OnStart` | `"1.0.0.93"` |
| `Src/App.pa.yaml` (v `.msapp`) vs `src/app_src/App.pa.yaml` (repo) | shoda kromě `varVerze` (repo má placeholder „vývojová", msapp má „1.0.0.100" — očekávané, build ho vkládá jen do YAML) |
| Diff jmen controlů `Controls/155.json` (scr_Ciselnik) vs `yaml.safe_load(src/app_src/scr_Ciselnik.pa.yaml)` | chybí `btn_PresunC`, `btn_PridatVlastnikaC`, `txt_VlastniciC`; navíc stará `ico_PresunC` |
| Diff jmen controlů `Controls/4.json` (scr_Dashboard) vs repo | chybí `btn_StavMenu`, `rec_MenuStavPanel`; `btn_NezarazeneD.X = 902` (starý „chip" styl) |
| `Controls/89.json` (scr_Detail) `btn_Ulozit.OnSelect` | obsahuje `ForAll(Filter(datasource)…, Patch(datasource,…))` — anti-pattern z balíku 94, vrácený |
| `grep colVazbySirotka src/app_src/scr_Detail.pa.yaml` | 2 (oprava je jen ve zdroji, ne v `Controls/*.json`) |
| `packed.json` balíku 96 (`deploy/mpsv/procesnimapa_1_0_0_96.zip`, i `deploy/procesnimapa_1_0_0_96.zip`) | identické s balíkem 100 — regrese sahá minimálně k balíku 96 |
| `check_app.py --solution deploy/procesnimapa_1_0_0_100.zip` vs bez argumentu | identický výstup/exit kód — `--solution` se ignoruje (P-02) |
| `check_solution.py --vstup 99 --vystup 100` | 679/0 |
| `check_flow.py` / `check_restore_flow.py` / `check_zaloha_flow.py` / `check_import_flow.py` / `check_mapa_flow.py` / `check_export_flow.py` / `check_presun_flow.py` | 30/571/184/243/144/129/111 — vše 0 chyb |
| `check_env.py` | OK |
| `check_schema.py` | OK — `Utvary=44` |
| `check_sablona.py --sablona deploy/sablona_import_aktivit.xlsx` | 206/0 |
| `node src/check_setup.js` / `node src/check_import.js` | smoke OK |
| `solution.xml` verze/`Managed` | `1.0.0.100` > `1.0.0.99`, `<Managed>0</Managed>` |
| GUID (regex) ve `Workflows/` | 0 výskytů |
| `<defaultvalue>` / `environmentvariablevalues.json` | žádná / není |
| G1 — externí CDN v `deploy/**/*.html`, `viz/*.html` | 0 výskytů `http(s)://` |

### Zamítnuté nálezy — kolo 8

*(žádné)*

## Neověřeno — kolo 8

### N-10 · skutečné chování Power Apps Studio po importu balíku se zastaralým `Controls/*.json`
P-01 je odvozen z obsahu balíku (co appka bude dělat hned po importu, než
ji kdokoli uloží), ne z pozorování živého importu — na to auditor nemá
prostředí. Teoreticky by `Controls/*.json` mohlo být Studiem při prvním
otevření tiše přepsáno podle `Src/*.pa.yaml` (přesně to `vymen_zdroje_bez_pac()`
předpokládá) — jenže tomu skill (`canvas-json-editing.md`, ověřeno 01.07.2026)
i checklist C1 přímo odporují a kolo 4 (B-03/N-06) totéž pozorovalo u
menší, izolované vlastnosti (`varVerze` samo nejdřív žádný efekt nemělo,
dokud appku někdo ve Studiu neuložil). Potřeba k doověření: reálný import
balíku 100 do PPF DEV, otevření appky ve Studiu BEZ jakékoli úpravy a
kontrola tooltipu verze / formuláře „víc vlastníků" hned po otevření —
očekávané chování podle P-01 je verze `1.0.0.93` a chybějící tlačítko
Přesun; pokud se ukáže `1.0.0.100` a tlačítko Přesun rovnou, P-01 je třeba
přehodnotit (ale statický důkaz z `Controls/*.json` teorii „Studio to samo
opraví" nepodporuje).

### N-11 · dopad P-01 na reálné testování v `STATUS.md` „CO JE NA TOBĚ"
`STATUS.md` žádá test tlačítka Přesun, sjednoceného pruhu a víc vlastníků
na balíku 100 — pokud se import chová podle P-01, žádná z těchto věcí se
nedá reálně otestovat, dokud appka neprojde skutečným `pac canvas pack`
(nebo Studiem-materializovaným uložením). Nejde o samostatné zjištění, jen
důsledek P-01 pro plánování dalšího kroku.

## Kolo 7 (06.09.2026, balík `deploy/procesnimapa_1_0_0_99.zip`, F16/1 + tlačítko Přesun + F17 + F15)

> **VYŘÍZENO 06.09.2026 19:50, balík `1.0.0.100`.** Všechny čtyři nálezy
> opraveny, žádný zamítnut. Nálezy byly věcné — dva blokující byly obojí
> opomenutí při zavádění víc vlastníků.
>
> | nález | jak vyřízeno |
> |---|---|
> | **P-01** | trojice `Reset(drp_VlastnikC); Set(varVlastniciC,""); Reset(txt_VlastniciC)` doplněna na obě chybějící místa — `btn_NovaC` a větev „Založit" v `btn_UlozitC`. `Reset(txt_VlastniciC)` je teď na 10 místech. |
> | **P-02** | tooltip `btn_UlozitC` přepsán: prázdné pole vlastníky **smaže**, což kód dělal už předtím. Slib „zůstane ten původní" pocházel z doby jednoho rozbalovátka a přežil změnu — přesně ten druh nesouladu, kvůli kterému se audit dělá. |
> | **P-03** | `lbl_RadekUklidC` na `-224`, `lbl_RadekVlastnikC` na `-302`, `lbl_RadekNazevC` na `TemplateWidth - 482`; mezi sloupci je všude 8 px. |
> | **P-04** | `btn_NezarazeneD` posunuto z `X=464` na `514`. |
>
> **Podstatnější než ty čtyři opravy je příčina P-03: brána překryvy uvnitř
> galerií nekontrolovala vůbec.** `souradnice_v_px()` neuměla
> `Parent.TemplateWidth/TemplateHeight`, takže se každý prvek v šabloně řádku
> přeskočil. Doplněno vyhodnocování aritmetiky nad `Parent.*` a `varFs`
> (stromem přes `ast`, ne `eval`, jen `+ - * /`).
>
> Rozšířená kontrola pak našla i **dva pre-existující překryvy** na
> `scr_Vazby` (`lbl_VazbaKod` × `lbl_VazbaNazev`, `lbl_DpKod` × `lbl_DpNazev`,
> 2 px svisle) — popisek názvu začínal dřív, než končil popisek kódu. Srovnáno
> na `Y = 30 + varFs`. Vizuálně to vidět nebylo (text je centrovaný), ale rámce
> se překrývaly.
>
> Modální prvky dostaly výjimku — leží nad obsahem záměrně. Výjimka platí
> jen pro dvojici modál + obsah pod ním; dva modály přes sebe se hlásí dál.
>
> Nový mutační test `src/mutace_prekryv.py` **4/4**: tlačítko Přesun na štítku
> úklidu, přetékající popisek názvu, koš na tlačítku Přesun a dva modální
> prvky přes sebe (ten hlídá, že výjimka pro modály není příliš široká).
>
> Brány nad `1.0.0.100`: `check_solution` 679, `check_restore_flow` 571,
> `check_import_flow` **243**, `check_zaloha_flow` 184, `check_mapa_flow` 144,
> `check_export_flow` 129, `check_presun_flow` 111, `check_flow` 30,
> `check_app`, `check_env`, `check_schema` zeleně. Mutačně: `mutace_import`
> **32/32**, `mutace_sablona` 19/19, `mutace_restore` 17/17, `mutace_zaloha`
> 16/16, `mutace_presun` 15/15, `mutace_kratky_nazev` 14/14,
> `mutace_export_mapa` 7/7, `mutace_napojeni` 5/5, `mutace_prekryv` **4/4**,
> `mutace_parametry` 4/4, `mutace_app` 2/2.

Zadání: F16/1 (víc vlastníků u agendy, procesu a dílčího procesu — trojice
rozbalovátko/„+"/textové pole v `scr_Ciselnik.pa.yaml`), tlačítko Přesun
místo ikony ve stejné obrazovce, F17 (sjednocený pruh voleb na
`scr_Dashboard.pa.yaml`), F15 (číselník útvarů 7 → 44 položek). Rozsah podle
zadání: appka (`src/app_src/*.pa.yaml` a `.msapp` uvnitř balíku), ne flows —
ty prošly auditem v kole 6 a v tomto kole beze změny.

Postup: `deploy/procesnimapa_1_0_0_99.zip` rozbalen do scratchpadu (`unzip -t`
bez chyby na solution zipu i vnořeném `.msapp`), `CanvasApps/*.msapp`
rozbalen zvlášť, nálezy ověřeny přímo nad `Src/*.pa.yaml` v rozbaleném
balíku, ne nad `STATUS.md`. Doplňkově: `diff` mezi rozbaleným `Src/*.pa.yaml`
a `src/app_src/*.pa.yaml` v repu vyšel **prázdný** (bajtově identické) — build
je reprodukovatelný a zdroj v gitu odpovídá vydanému balíku, takže nálezy
níže citují i cestu/řádek v `src/app_src/`. Pro srovnání „před" rozbalen i
`deploy/procesnimapa_1_0_0_98.zip` (poslední auditovaný balík z kola 6).
Brány spuštěny přímo, ne převzaty: `check_app.py`, `mutace_app.py`,
`check_solution.py --vstup 98 --vystup 99`. `git status`/`git log`
zkontrolovány pro ověření G-01 z kola 6.

### Integrita balíku, verze, env proměnné, git — v pořádku

| co | výsledek |
|---|---|
| `unzip -t` solution zip i vnořený `.msapp` | bez chyby |
| `solution.xml` `<Version>` / `<Managed>` | `1.0.0.99` (> `1.0.0.98`), `<Managed>0</Managed>` |
| GUID (regex `[0-9a-f]{8}-…`) ve `Workflows/` | **0 výskytů** (beze změny proti 98) |
| `<defaultvalue>` v definicích env proměnných | **žádná** |
| `environmentvariablevalues.json` v balíku | **není** |
| `Src/*.pa.yaml` v `.msapp` vs `src/app_src/*.pa.yaml` v repu | **bajtově identické** (`diff` prázdný) |
| `check_app.py --solution deploy/procesnimapa_1_0_0_99.zip` | OK — 7 souborů, 6 obrazovek, 287 prvků, 3206 vzorců, jen 4 preexistující VAROVÁNÍ (3× Sort v Items, 1× výjimka mazání v `scr_Vazby`) |
| `mutace_app.py` | 2/2 chyceno (kryje jen starší past `ForAll`+zápis, netýká se F16/1 — cílená kontrola pro `txt_VlastniciC`/`btn_PridatVlastnikaC` v `check_app.py` **není žádná**, jak upozorňuje zadání) |
| `check_solution.py --vstup 98 --vystup 99` | 668 kontrol, 0 chyb |
| **G-01 (kolo 6)** — implementace F14/balík 98 v gitu | **vyřízeno**: `git status --short` je čistý na souborech appky, `git log` ukazuje komity `317e0c1` (F14/98), `12a2fd6` (F15+F17+Přesun) a `0067065` (F16/1, balík 99); pracovní strom má jen necommitnuté změny v `src/make_sablona.py`/`src/build_import_flow.py`/`src/check_import_flow.py`/`src/mutace_import.py`/`deploy/sablona_import_aktivit.xlsx` — podle zadání souběžná práce na F16/2, mimo rozsah tohoto auditu, nebrat jako nález |

### P-01 · BLOKUJÍCÍ · `src/app_src/scr_Ciselnik.pa.yaml` — dvě ze devíti míst, která formulář číselníku plní nebo čistí, nevyprázdní pole vlastníků; appka pak zapíše cizí vlastníky do nesouvisející položky

`STATUS.md` (06.09.2026 večer, F16/1) tvrdí: „`varVlastniciC` se plní při
načtení položky do formuláře a čistí se při přepnutí úrovně / nové položce
(**šest míst**, kde bylo `Reset(drp_VlastnikC)`)." Skutečnost: `Reset(drp_VlastnikC)`
se v balíku **98** (před F16/1) vyskytoval na **devíti** místech (řádky 140,
283, 314, 345, 380, 783, 1449, 1541, 1755 — ověřeno greppem), a všech devět
jsou reálná místa, kde se formulář číselníku plní nebo čistí (OnVisible, čtyři
tlačítka přepnutí úrovně, načtení položky do formuláře, úspěšné založení nové
položky, tlačítko „Nová položka", potvrzené smazání zobrazené položky). V
balíku **99** má **sedm** z nich kompletní trojici `Reset(drp_VlastnikC);
Set(varVlastniciC, "" nebo Switch(...)); Reset(txt_VlastniciC)` — ale **dvě
zůstala jen s původním jediným řádkem**:

**1. Tlačítko „Nová položka" (`btn_NovaC.OnSelect`, řádek 1612-1627):**
```
scr_Ciselnik.pa.yaml (balík 99):
  =Set(varCiselnikNova, true);
  Set(varCiselnikKod, "");
  Set(varChybaC, "");
  Reset(drp_AgendaC);
  Reset(drp_ProcesC);
  Reset(txt_NazevC);
  Reset(drp_VlastnikC);
  If(varUrovenTyp = "aktivita", …)
```

**2. Úspěšné založení nové položky (`btn_UlozitC.OnSelect`, řádek 1524-1527,
větev „Založit"):**
```
scr_Ciselnik.pa.yaml (balík 99):
  Set(varAktStale, true);
  Notify("Založeno jako " & varNovyKodC & ".", NotificationType.Success, varNotifyMs);
  Reset(txt_NazevC);
  Reset(drp_VlastnikC),
```

V obou chybí `Set(varVlastniciC, "")` a `Reset(txt_VlastniciC)`.

**Reprodukce (sekvence kroků, deterministická — Power Fx `Default`/`Reset`
sémantika je zdokumentovaná, appka nemusí běžet, aby se dala vysledovat z
kódu):**
1. Uživatel na úrovni „Procesy" klikne existující proces s víc vlastníky
   (`lbl_RadekPrekryvC.OnSelect`, řádek 794-804 — tohle místo triádu má) →
   `varVlastniciC` se nastaví např. na `"11; 33"`, `Reset(txt_VlastniciC)`
   promítne hodnotu do pole.
2. `btn_NovaC` je pro zobrazenou existující položku aktivní
   (`DisplayMode = If(varUrovenTyp <> "aktivita" && varCiselnikNova,
   DisplayMode.Disabled, DisplayMode.Edit)`, `varCiselnikNova` je zde
   `false`) — uživatel klikne „Nová položka".
3. `OnSelect` vyprázdní agendu, název i rozbalovátko vlastníka, ale
   `txt_VlastniciC` **zůstává** `"11; 33"` — `Reset()` se na něj nezavolal,
   takže si drží starou zobrazenou hodnotu (Default se přepočítá jen při
   Reset/mountu, ne samovolně).
4. Uživatel vyplní jen název a klikne „Založit". `btn_UlozitC.OnSelect` čte
   `varVlastnikC` z `txt_VlastniciC.Text` (řádek 1341-1351,
   `Concat(Filter(Split(...)))`), ne z `varVlastniciC` — zapíše se tedy
   `vlastnik: "11; 33"` do **nově založeného, obsahově nesouvisejícího**
   procesu/agendy/dílčího procesu, aniž by si toho uživatel všiml (pole
   vypadalo prázdné jen u agendy/názvu, ne u vlastníka).

Druhé místo (bod 2 výše) otevírá stejnou past i bez kroku 1-2: po úspěšném
založení první nové položky s vlastníkem zůstane `txt_VlastniciC` nevyprázdněné
(jen `txt_NazevC` a `drp_VlastnikC` se resetují), takže **druhá** položka
založená hned po první (bez přechodu jinam) zdědí vlastníka té první, i když
ji uživatel nikdy nevybral.

Brány to nechytí: `check_app.py` nad balíkem 99 vypíše `OK` beze zmínky (viz
tabulka výše) a `mutace_app.py` tuhle funkci vůbec netestuje (jediné dvě
mutace se týkají staré pasti `ForAll`+zápis, viz `src/mutace_app.py`).
Checklist: C5 (past authoringu — nekompletní reset stavu formuláře), H1/H2
(`STATUS.md` tvrdí „šest míst" a „čistí se … při nové položce", skutečnost
neodpovídá ani v počtu, ani v úplnosti).
Doporučená oprava (neprovedeno, jen návrh): na obou místech doplnit
`Set(varVlastniciC, ""); Reset(txt_VlastniciC)` za `Reset(drp_VlastnikC)`
(stejný pattern jako na sedmi fungujících místech). Do `check_app.py`
přidat kontrolu, že každý výskyt `Reset(drp_VlastnikC)` je bezprostředně
následovaný `Set(varVlastniciC,` a `Reset(txt_VlastniciC)` — mutačně
ověřitelné odebráním kterékoli z obou přípon.
Stav: otevřeno

### P-02 · BLOKUJÍCÍ · `src/app_src/scr_Ciselnik.pa.yaml:1531-1564` a tooltip na řádku 1588 — uložení existující položky s prázdným polem vlastníků vlastníka nenávratně smaže, tooltip appky tvrdí opak

`STATUS.md` (06.09.2026) k F16/1 výslovně píše: „Popisek pole už neslibuje
‚prázdné = ponechat stávajícího' — seznam je zdroj pravdy, takže prázdný
seznam znamená žádný vlastník." Skutečný tooltip tlačítka „Uložit změny" v
balíku 99 ale **pořád slibuje přesně to, co STATUS.md tvrdí, že už neslibuje**:

```
scr_Ciselnik.pa.yaml (balík 99, btn_UlozitC.Tooltip, řádek 1588):
  "Uloží změnu názvu a vlastníka. Kód, úroveň ani zařazení se nemění -
   vazby v rejstříku i v mapě na kódu stojí. Když necháš vlastníka
   nevyplněného, zůstane ten původní; je to pojistka pro položky, které
   mají vlastníků víc a v nabídce jednoho útvaru se proto nenajdou."
```

A skutečné chování `btn_UlozitC.OnSelect` (větev editace existující
položky, ne založení nové) ho vyvrací — `varVlastnikC` se spočítá z
`txt_VlastniciC.Text` bez ohledu na to, jestli je pole prázdné:

```
Set(
    varVlastnikC,
    Concat(Filter(Split(Substitute(txt_VlastniciC.Text, " ", ""), ";"),
                  !IsBlank(Value)), Value, "; ")
);
…
Patch(Agendy, LookUp(Agendy, Title = varCiselnikKod),
      { nazev: txt_NazevC.Text, vlastnik: varVlastnikC })
```

Pro prázdné `txt_VlastniciC.Text`: `Substitute("", " ", "") = ""`,
`Split("", ";")` vrátí jednořádkovou tabulku s `Value = ""`, `Filter(!IsBlank(Value))`
tenhle prázdný řádek odfiltruje (Power Fx `IsBlank("")` je `true`), `Concat`
nad prázdnou tabulkou vrátí `""` — `varVlastnikC` je tedy `""` a `Patch`
zapíše `vlastnik: ""` **bez výjimky**, žádná větev kód neošetřuje jinak.
Jde o **stejnou dvojici řádků**, kterou používá i P-01 (`Concat/Split` v
`btn_UlozitC.OnSelect`), takže je to tatáž mechanika, jiný spouštěč.

**Reprodukce:** existující proces se dvěma vlastníky (`"11; 33"`), z nichž
jeden v nabídce dropdownu chybí (přesně scénář, na který tooltip cílí —
„položky, které mají vlastníků víc a v nabídce jednoho útvaru se proto
nenajdou"). Uživatel podle tooltipu **záměrně smaže obsah** `txt_VlastniciC`
(protože si podle popisku myslí, že tím ponechá původní hodnotu), upraví jen
název a uloží. `btn_UlozitC.OnSelect` zapíše `vlastnik: ""` — oba vlastníci
jsou nenávratně pryč (list `Agendy`/`Procesy`/`Dílčí procesy` nemá historii
pole mimo SharePoint verzování, které appka neobsluhuje).

Nejde o okrajový detail popisku — je to přesně opačné doporučení, než jaké
appka provede, a týká se přímo hlavního scénáře, kvůli kterému F16/1 vznikla
(položky s víc vlastníky, kde jeden není v nabídce). Brány to nechytí ze
stejného důvodu jako P-01 — `check_app.py` nemá kontrolu obsahu tooltipů
proti skutečnému chování a `mutace_app.py` se F16/1 netýká.
Checklist: H1/H2 (appka dělá opak toho, co sama tvrdí a co `STATUS.md`
popisuje jako opravené), C5.
Doporučená oprava (neprovedeno, jen návrh): buď (a) tooltip přepsat na
skutečné chování („prázdné pole = žádný vlastník, přepíše i existující"),
nebo (b) pokud má platit původní slib, ve větvi editace existující položky
při `IsBlank(txt_VlastniciC.Text)` zapsat vlastníka beze změny (hodnotu, se
kterou se formulář naplnil), ne prázdný řetězec — a teprve explicitní akci
(např. tlačítko „vymazat vlastníky") použít pro skutečné smazání. Cokoli z
toho stačí, hlavní je, aby tooltip a kód říkaly totéž.
Stav: otevřeno

### P-03 · OPRAVIT · `src/app_src/scr_Ciselnik.pa.yaml` (šablona řádku galerie `gal_CiselnikC`) — `btn_PresunC` se překrývá s `lbl_RadekUklidC` o 16 px; `check_app.py` překryvy uvnitř šablony galerie nevidí

Galerie `gal_CiselnikC` má pevnou `Width: =620` (`Parent.TemplateWidth`
uvnitř šablony řádku je tedy 620). Dosazením do souřadnic v balíku 99:

```
lbl_RadekUklidC:  X = Parent.TemplateWidth - 200 = 420, Width = 76  → [420, 496]
btn_PresunC:      X = Parent.TemplateWidth - 140 = 480, Width = 84  → [480, 564]
```

Průnik `[480, 496]` = **16 px přes celou výšku řádku** (obě mají
`Height = Parent.TemplateHeight - 1`). U procesů/dílčích procesů, které jsou
zároveň „osiřelé" (`lbl_RadekUklidC` zobrazí text „osiřelý"), se tenhle text
a levý okraj tlačítka „Přesun" (má průhledný `Fill`, takže podklad prosvítá)
vizuálně sráží ve stejném 16px pruhu — obě `Visible` podmínky se nevylučují,
takže se to skutečně vykreslí naráz.

**Proč to `check_app.py` nechytí.** `kontrola_prekryvu()` počítá souřadnice
přes `souradnice_v_px()`, která umí jen `Parent.Width`/`Parent.Height` proti
konstantám `SIRKA_PLOCHY`/`VYSKA_PLOCHY` (obrazovka) — regex
`Parent\.(Width|Height)(?:\s*[-+]\s*\d+)?` na `Parent.TemplateWidth` (galerie)
nesedne, protože za `Parent.` následuje `TemplateWidth`, ne `Width`/`Height`.
`souradnice_v_px()` proto pro `Parent.TemplateWidth - N` vrátí `None` a
`kontrola_prekryvu()` s `if any(s is None for s in souradnice): continue`
dvojici přeskočí — **prakticky každý prvek uvnitř libovolné šablony galerie**
(všechny používají `Parent.TemplateWidth`/`Parent.TemplateHeight`), takže
brána efektivně nekontroluje překryvy uvnitř galerií vůbec, i když skill
dokumentace (`canvas-json-editing.md` §Layout) tenhle typ chyby explicitně
jmenuje jako to, co „nehlásí nikdo". Ověřeno spuštěním: `check_app.py` nad
nezměněným balíkem 99 vypisuje `OK`, žádná zmínka o `btn_PresunC`/
`lbl_RadekUklidC`.

Nejde o novou závadu ve smyslu klikatelnosti — `btn_PresunC` je v souboru
deklarované AŽ ZA `lbl_RadekPrekryvC` (transparentní overlay), takže leží
nad ním a klik funguje na celou svou šířku 84 px; jde o vizuální kolizi
textu. Stará verze (98, `ico_PresunC`, `Icon.Redo` W 32 na `X = TemplateWidth-84`)
měla se stejným `lbl_RadekUklidC` kolizi ještě větší (32 px), takže problém
není touhle změnou nově vzniklý — ale změna ho neopravila, a task kola 7
výslovně žádal ověřit, že se prvky v řádku nepřekrývají.
Checklist: C5, F3 (kontrola nedokazuje to, co má).
Doporučená oprava (neprovedeno, jen návrh): (1) posunout `btn_PresunC` nebo
zúžit/posunout `lbl_RadekUklidC`, ať mezi nimi zůstane mezera jako u
ostatních dvojic v řádku (8 px); (2) do `souradnice_v_px()` doplnit i
`Parent\.(TemplateWidth|TemplateHeight)` proti rozměrům šablony galerie
(šířka z `Width` galerie, výška z `TemplateSize`/`Height` podle Layout) —
bez toho je `kontrola_prekryvu()` u galerií kosmetická.
Stav: otevřeno

### P-04 · OPRAVIT · `src/app_src/scr_Dashboard.pa.yaml:1529` (`btn_NezarazeneD`) — tlačítko v panelu „Stav" zůstalo na staré souřadnici, čouhá 46 px mimo panel

F17 posunula panel `rec_MenuStavPanel` z `X = 460` (balík 98) na `X = 510`
(balík 99, +50 px, sedí na nový krok 248 mezi tlačítky pruhu) a čtyři z pěti
tlačítek uvnitř panelu (`btn_StavVse`, `btn_StavSchvaleno`, `btn_StavPracovni`,
`btn_KodD`) posunula spolu s ním z `X = 464` na `X = 514`. Páté,
`btn_NezarazeneD`, zůstalo na **starém** `X = 464`:

```
balík 98: btn_StavVse, btn_StavSchvaleno, btn_StavPracovni, btn_NezarazeneD,
          btn_KodD — všech pět na X=464 (panel na X=460)
balík 99: btn_StavVse/Schvaleno/Pracovni/KodD → X=514 (posunuto s panelem),
          btn_NezarazeneD → X=464 (NEposunuto; panel je teď na X=510)
```

Dosazením: panel `[510, 750]`, `btn_NezarazeneD` (`Width = 232`)
`[464, 696]` — tlačítko začíná **46 px nalevo od levého okraje panelu**, bez
podkladové karty (`rec_MenuStavPanel.Fill`) pod sebou; při zobrazené hlášce
„nezařazené (N)" (`Visible = varMenuStav && (varDashNezarazene ||
CountRows(Filter(colAkt, dilci_proces_kod = "00-00-000")) > 0)`, tedy vždy,
když v rejstříku existuje aspoň jedna nezařazená aktivita) by tlačítko
viditelně vyčnívalo z panelu doleva nad čistou plochu obrazovky.

Kontrola `kontrola_prekryvu()` tohle nechytí ze stejného principiálního
důvodu jako v P-03, jen opačným směrem — porovnává jen prvky s obsahem
(`lbl_/txt_/drp_/btn_/cmb_/ico_`) navzájem, **výslovně vynechává `rec_`
podklady** (skill: „jen prvky s obsahem, nikdy podklady — ty pod popisky
ležet musí"), takže to, jestli tlačítko leží uvnitř svého vlastního panelu,
neověřuje vůbec — to je jiná otázka než překryv dvou popisků a žádná
existující brána ji nepokrývá.
Checklist: C5, H1/H2 (F17 měla podle `STATUS.md` sjednotit celý pruh a jeho
panely — u jednoho tlačítka se sjednocení nedotáhlo).
Doporučená oprava (neprovedeno, jen návrh): v `btn_NezarazeneD` změnit
`X: =464` na `X: =514` (stejně jako čtyři sourozenci ve stejném panelu).
Do `check_app.py` přidat kontrolu, že každý prvek s `Visible` svázaným na
`varMenu…` proměnnou leží (X/Y/Width/Height) uvnitř svého panelu `rec_Menu…Panel`
se stejnou `varMenu…` podmínkou.
Stav: otevřeno

### Ověřeno spuštěním — kolo 7

| příkaz / mutace | výsledek |
|---|---|
| `unzip -t deploy/procesnimapa_1_0_0_99.zip` (solution + `.msapp`) | bez chyby |
| `solution.xml` verze/`Managed` | `1.0.0.99` > `1.0.0.98`, `<Managed>0</Managed>` |
| GUID (regex) ve `Workflows/` | 0 výskytů |
| `<defaultvalue>` v definicích env proměnných | žádná |
| `environmentvariablevalues.json` v balíku | není |
| `diff` `Src/*.pa.yaml` (balík 99) vs `src/app_src/*.pa.yaml` (repo) | prázdný — bajtově identické |
| `check_app.py --solution deploy/procesnimapa_1_0_0_99.zip` | OK — 6 obrazovek, 287 prvků, 3206 vzorců, 4 preexistující VAROVÁNÍ |
| `mutace_app.py` | 2/2 chyceno (netýká se F16/1) |
| `check_solution.py --vstup 98 --vystup 99` | 668/0 |
| Počet `Reset(drp_VlastnikC)` v 98 vs 99 | 9 vs 10 (nové 10. místo je `btn_PridatVlastnikaC`, intentional partial, ne bug) |
| P-01 repro: diff obou neúplných míst proti sedmi kompletním trojicím | chybí `Set(varVlastniciC,"")`+`Reset(txt_VlastniciC)` na obou, potvrzeno greppem v 98 i 99 |
| P-02 repro: ruční trasování `Split(Substitute("", " ", ""), ";")` → `Filter(!IsBlank)` → `Concat` | vrací `""`, `Patch(..., {vlastnik: ""})` bez výjimky pro blank |
| P-03 výpočet: `TemplateWidth=620`, `lbl_RadekUklidC` `[420,496]` vs `btn_PresunC` `[480,564]` | průnik 16 px, `check_app.py` na to nereaguje |
| P-04 výpočet: `rec_MenuStavPanel` `[510,750]` vs `btn_NezarazeneD` `[464,696]` | tlačítko 46 px mimo panel, `check_app.py` na to nereaguje |
| `souradnice_v_px()` na `"Parent.TemplateWidth - 140"` (ruční test regexu) | vrací `None` (nesedne na `TemplateWidth`) — potvrzuje mechanismus mezery z P-03 |
| `git status --short` / `git log -3` | appka a balík 99 komitnuté (`0067065`), G-01 z kola 6 vyřízeno |

### Zamítnuté nálezy — kolo 7

*(žádné)*

## Neověřeno — kolo 7

### N-09 · reálné nasazení balíku 99 na PPF DEV
`STATUS.md` „CO JE NA TOBĚ" popisuje import 99 jako upgrade, mikro-změnu,
Save/Publish a ruční průchod novinkami (Přesun, pruh voleb, víc vlastníků) —
nic z toho k 06.09.2026 20:15 ještě neproběhlo. Statická kontrola (brány,
trasování vzorců, výpočet souřadnic) nález nedala kromě P-01 až P-04.
Potřeba k doověření: reálný import + otevření ve Studiu + scénář z P-01/P-02
(načíst existující víc-vlastníkovou položku, kliknout „Nová položka" /
vymazat pole vlastníků u existující položky a uložit) a vizuální kontrola
panelu Stav a řádku Přesun na snímku obrazovky.


## Kolo 6 (06.09.2026, balík `deploy/procesnimapa_1_0_0_98.zip`, F14)

Zadání: konec dvoubalíkového režimu — zápis krátkého názvu přes REST MERGE
místo `PatchItem`, aby v balíku nezůstal žádný GUID listu natvrdo. Rozsah
diffu: `src/build_flow.py`, `src/check_flow.py`, `src/check_solution.py`,
`src/build_app.py`, `src/make_deploy_mpsv.py`, nový `src/mutace_kratky_nazev.py`,
`HANDOVER.md`, `STATUS.md`, `PLAN.md`, `deploy/flow_AktualizaceKratkehoNazvu.md`.

Postup: `deploy/procesnimapa_1_0_0_98.zip` i `deploy/procesnimapa_1_0_0_97.zip`
rozbaleny do scratchpadu (`unzip -t` bez chyby na solution i vnořeném `.msapp`
u obou), nálezy ověřeny přímo nad `Workflows/*.json` v balíku, ne nad
`STATUS.md`. Brány spuštěny přímo, ne převzaty: `check_flow.py` (nad 98 i
zpětně nad 97), `check_solution.py --vstup 97 --vystup 98`,
`check_restore_flow.py`, `check_zaloha_flow.py`, `check_import_flow.py`,
`check_mapa_flow.py`, `check_export_flow.py`, `check_presun_flow.py`,
`check_env.py`, `check_app.py`, `mutace_kratky_nazev.py` (nad kopií mimo
projekt), `make_deploy_mpsv.py`.

### Body 1–5 ze zadání — technicky v pořádku

**1. Žádný GUID natvrdo v 98, ostatní flow beze změny proti 97 — potvrzeno.**
```
grep -rEo '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' scratch/98/Workflows
→ (prázdný výstup)
grep -rEo týž vzor scratch/97/Workflows
→ b1daaa38-53df-4c7b-b9f8-03b36d46bc60   (v AktualizaceKratkehoNazvu)
```
Porovnání obsahu `Workflows/*.json` mezi 97 a 98 po jménu flow (`cmp -s`):
`ExportFlow`, `ImportFlow`, `MapaPublishFlow`, `MapaPublishScheduled`,
`PresunFlow`, `RestoreFlow`, `ZalohaFlow`, `ZalohaScheduled` — všech osm
bajtově shodných, jen `AktualizaceKratkehoNazvu` se liší. `FlowNameId`
(GUID v názvu souboru) zůstal u něj stejný jako v 97 — je to upgrade téhož
flow, ne nové. `customizations.xml` nese v `Aktivity.tableName` GUID PPF DEV
(`9dfbb5a1-…`) i v 98, ale nezměněně proti 97 a s `tableNameOverride` na
`mpsv_listAktivity` — to je zdokumentovaný, funkční vzor (`solution-structure.md`
řádek 56, `canvas-json-editing.md` řádek 96-97), ne nález.

**2. REST zápis je tvarově správný.** Vytažen přímo z balíku 98:
```
"parameters/uri": "@concat('_api/web/GetList(''', outputs('Cesta_webu'),
  '/Lists/Aktivity', ''')/items(', string(triggerBody()?['ID']), ')')"
```
`check_flow.py` REST adresu **vyhodnotí** mini-interpretem (ne porovná
textem) a dostane `_api/web/GetList('/sites/procesnimapa/Lists/Aktivity')
/items(1)` — platná server-relativní REST URL, `''` je správně escapovaná
jednoduchá uvozovka podle syntaxe Workflow Definition Language. `rest_adresa()`
v `build_flow.py` je znakově identická s `rest_adresa()` v
`build_restore_flow.py`, která skládá REST adresy pro `RestoreFlow` —
a ten podle `STATUS.md` („STAV ZKOUŠEK") na MPSV už reálně zapisoval
(„obnova na datech: OK", „import — zápis: OK"). Nejde tedy o nevyzkoušený
vzorec, ale o týž kód, jaký už na cílovém tenantu prokazatelně píše do listů.
Parametry mají prefix `parameters/` (`parameters/method`, `parameters/uri`,
`parameters/headers`, `parameters/body`), `operationId` je `HttpRequest`,
hlavičky `Accept`/`Content-Type: application/json;odata=nometadata`,
`X-HTTP-Method: MERGE`, `IF-MATCH: *` — přesně podle zadání.

**3. `definition.parameters` odpovídá použití, včetně `mpsv_listAktivity`.**
V nasazeném `AktualizaceKratkehoNazvu-....json` (balík 98) jsou deklarovány
právě dva netriviální parametry — `mpsv_procesnimapaSite` a `mpsv_listAktivity`
— oba bez `defaultValue`. Mechanismus (`dorovnej_deklarace_parametru` v
`build_app.py`) je obecný: projde `parameters('...')` napříč všemi flow a
doplní deklaraci ke každému použití, takže se nemůže rozejít used↔declared.
Definice proměnných (`environmentvariabledefinitions/*/environmentvariabledefinition.xml`,
9 souborů) nemají `<defaultvalue>` (grep prázdný) a `environmentvariablevalues.json`
v balíku není (`find` prázdný) — B2 a B3 čisté.

**4. Mutační test `mutace_kratky_nazev.py` — 14/14 potvrzeno spuštěním, kryje
podstatné.** Spuštěno auditorem samostatně nad kopií balíku (ne převzato):
```
python src/mutace_kratky_nazev.py --vystup <kopie 98>
→ chycených mutací: 14/14
```
Mutace pokrývají obě vrstvy, na kterých REST zápis stojí — hlavičky
(chybějící `MERGE`, `MERGE`→`PATCH`, chybějící `IF-MATCH`), adresu (GUID
zpátky v REST adrese i v triggeru, adresa bez `/items(ID)`, `Cesta_webu` bez
`skip` čili neserver-relativní), návrat k `PatchItem`, tělo (prohozené pole,
povinná pole navíc, hodnota ze snímku triggeru), metodu (GET místo POST) a
řídicí logiku (čtení z triggeru místo `Nacti_aktivitu`, zápis bez porovnání
→ cyklení). Zpětně nad 97 vypíše `check_flow.py` **12 nálezů** (ověřeno
spuštěním, sedí na `STATUS.md`) — potvrzuje, že brána skutečně rozlišuje
starý a nový tvar, ne že je jen přepsaná na nic.

**5. Dokumentace v `deploy/mpsv/` — z větší části sedí, dvě místa jsou stará
čísla verze.** `README.md` (auto-generované) uvádí `procesnimapa_1_0_0_98.zip`,
9 flow, 6 obrazovek, 9 proměnných — všechny čtyři počty ověřeny přímo
(`check_app.py`: 6 obrazovek; výpis `Workflows/`: 9 souborů; výpis
`environmentvariabledefinitions/`: 9 položek) a sedí. `flow_AktualizaceKratkehoNazvu.md`
(v `deploy/mpsv/`, bajtově shodný s `deploy/` root) popisuje přesně tu podobu
flow, která je v balíku 98 (akce, výrazy, REST tvar) — žádný rozpor. Nesedí
verze v `navod_sprava.md` a stará čísla balíků v `TESTOVACI_SCENAR.md` —
viz P-01 níže.

### P-01 · OPRAVIT · `deploy/mpsv/navod_sprava.md` a `deploy/mpsv/TESTOVACI_SCENAR.md` — stará čísla verze/balíku

`navod_sprava.md` řádek 7: *„Návod popisuje aplikaci Procesní mapa MPSV ve
verzi **1.0.0.96**."* Nasazovaná sada je **1.0.0.98**. F14 neměnila appku
(žádná obrazovka, žádný `pa.yaml`), takže obsah návodu funkčně sedí, ale
věta samotná je nepravdivá — správce, který si podle ní ověří verzi appky,
najde neshodu a nebude vědět, jestli je to varovný signál nebo ne.

`TESTOVACI_SCENAR.md` (nadpis *„Testovací scénář — balík 1.0.0.96"*) jde
dál — je to spustitelný postup, ne jen popisný text:
```
A.1  Power Apps → Solutions → Import solution → procesnimapa_1_0_0_92.zip
A.2  Totéž s procesnimapa_1_0_0_93.zip
A.5  … Nápověda ukazuje verzi 1.0.0.93
```
V `deploy/mpsv/` dnes leží jen `procesnimapa_1_0_0_98.zip` — soubory
`_92.zip`/`_93.zip` z kroku A.1/A.2 tam nejsou k nalezení. Krok A.5 pak
řekne testerovi, aby čekal tooltip `1.0.0.93`, zatímco po importu 98 uvidí
`1.0.0.98` — přesně ten rozpor, o kterém dokument sám (blok 0, `varVerze`)
tvrdí, že znamená „neproběhla mikro-změna".

Obě jsou statické kopie z kořene (`deploy/navod_sprava.md`,
`deploy/TESTOVACI_SCENAR.md`) — `make_deploy_mpsv.py` je jen `shutil.copy`,
nepřepočítává v nich čísla. Ověřeno spuštěním:
```
python src/make_deploy_mpsv.py
→ deploy/mpsv/TESTOVACI_SCENAR.md a navod_sprava.md se PŘEPÍŠOU (jsou v seznamu
  kopírovaných souborů), ale obsahem zůstávají identické se starým `deploy/`
  originálem — root soubory samy nikdo neaktualizoval na 98
```
Dopad: zmatek při přejímce na MPSV, ne vada balíku samotného — appka i flow
fungují bez ohledu na to, co v návodu píše. Proto **OPRAVIT**, ne BLOKUJÍCÍ.
Checklist: H3 (předávací návod), H2 (dokumentace vs. skutečnost).
Doporučená oprava (neprovedeno, jen návrh): v `deploy/TESTOVACI_SCENAR.md`
a `deploy/navod_sprava.md` v kořeni aktualizovat čísla balíku/verze na 98
(nebo na obecné zástupné `<nejnovější balík>`, jako to dělá `README.md`,
který si číslo čte z balíku, ne píše ho ručně).
Stav: otevřeno

### G-01 · BLOKUJÍCÍ · implementace F14 a balík `procesnimapa_1_0_0_98.zip` nejsou v gitu

Celá věcná náplň téhle brány — zdrojový kód i vydaný balík — existuje jen
v necommitnutém pracovním stromu na jednom stroji. Poslední skutečný commit
(`c77a831`, „F14 zadana") přidal jen zápis plánu do `PLAN.md`/`STATUS.md`;
samotnou implementaci nikdo nezacommitoval ani nepushnul.

Repro (`git status --short` v kořeni projektu, po čerstvém `git pull --ff-only`
na začátku téhle session, který nahlásil „Already up to date"):
```
 M HANDOVER.md
 M PLAN.md
 M STATUS.md
 M deploy/flow_AktualizaceKratkehoNazvu.md
 M deploy/mpsv/02_import_dat.js
 M deploy/mpsv/README.md
 M deploy/mpsv/flow_AktualizaceKratkehoNazvu.md
 D deploy/mpsv/procesnimapa_1_0_0_97.zip
 M src/build_app.py
 M src/build_flow.py
 M src/check_flow.py
 M src/check_solution.py
 M src/make_deploy_mpsv.py
?? deploy/mpsv/procesnimapa_1_0_0_98.zip
?? deploy/procesnimapa_1_0_0_98.zip
?? src/mutace_kratky_nazev.py
```
```
git diff --stat HEAD -- PLAN.md STATUS.md HANDOVER.md src/build_app.py \
  src/build_flow.py src/check_flow.py src/check_solution.py src/make_deploy_mpsv.py
→ 8 files changed, 344 insertions(+), 197 deletions(-)
git ls-files deploy/*.zip
→ deploy/procesnimapa_1_0_0_96.zip, deploy/procesnimapa_1_0_0_97.zip
  (98 v seznamu chybí — nikdy nebyl "git add")
```
Soubory jsou na disku od 06.09.2026 18:24–18:34 (mtime), tedy z reálné
dnešní práce, ne z náhodného zbytku staré session — `src/mutace_kratky_nazev.py`,
který task zadání výslovně jmenuje jako nový soubor F14, je **untracked**,
ne jen upravený.

Proč to není jen formalita, ale skutečné riziko: projektový `CLAUDE.md` i
globální pravidla auditora (#13, #13b) staví na tom, že práce se mezi stroji
a paralelními sessions přenáší přes git a že commit+push je jeden krok, ne
dva — přesně proto, aby se předešlo stavu, kdy „hotovo" v `STATUS.md`
neodpovídá tomu, co je v repozitáři. Dokud `procesnimapa_1_0_0_98.zip` a
zdroje, které ho stavějí, nejsou v gitu:
- selhání disku nebo reset pracovního adresáře na tomhle stroji **ztratí
  celou F14** bez záložní kopie,
- jiný stroj/session, který si podle pravidla #13 stáhne `git pull`, dostane
  `STATUS.md` tvrdící „Hotová F14, balík 1.0.0.98", ale v repozitáři najde
  jen plán a poslední skutečně dostupný balík **1.0.0.97** — tedy přesně tu
  verzi, která má GUID PPF DEV natvrdo a kvůli které F14 vznikla,
- `deploy/mpsv/procesnimapa_1_0_0_98.zip`, balík určený k importu na MPSV,
  není v historii repozitáře vůbec — nedá se z gitu znovu získat, jen z
  disku tohoto stroje.

Nejde o vadu kódu ani balíku samotného (ten je podle bodů 1–5 výše technicky
v pořádku) — je to vada **stavu dodání**. Audituje se brána „předání balíku
k nasazení", a to předání v tuhle chvíli fakticky neproběhlo způsobem, který
projekt vyžaduje jako podmínku dalšího kroku.
Checklist: mimo číslované body A–H (proces, ne obsah balíku); odpovídá duchu
H1/H2 — „hotovo" v `STATUS.md` neodpovídá skutečnému stavu repozitáře.
Doporučená oprava (neprovedeno, auditor nezasahuje do gitu): `git add` na
vyjmenované soubory (kromě `deploy/mpsv/procesnimapa_1_0_0_97.zip`, který se
maže záměrně) + `git commit` + `git push` podle pravidla #13b, než balík
skutečně půjde na MPSV.
Stav: otevřeno

### Ověřeno spuštěním — kolo 6

| příkaz / mutace | výsledek |
|---|---|
| `unzip -t deploy/procesnimapa_1_0_0_98.zip` (solution + `.msapp`) | bez chyby |
| `unzip -t deploy/procesnimapa_1_0_0_97.zip` (solution) | bez chyby |
| `solution.xml` verze/`Managed` (98) | `1.0.0.98` > `1.0.0.97`, `<Managed>0</Managed>` |
| GUID (regex `[0-9a-f]{8}-…`) ve `Workflows/` (98) | **0 výskytů** |
| totéž nad 97 | 1 výskyt (`b1daaa38-…` v `AktualizaceKratkehoNazvu`) |
| `cmp -s` 8 flow (97 vs 98), mimo `AktualizaceKratkehoNazvu` | **bajtově shodné** ve všech osmi |
| `check_flow.py --solution …98.zip` | 30 kontrol, 0 chyb, 104 vzorků |
| `check_flow.py --solution …97.zip` (zpětně) | 29 kontrol, **12 chyb** (GUID, PatchItem, chybějící MERGE/IF-MATCH, špatné tělo, …) |
| `check_solution.py --vstup 97 --vystup 98` | 666 kontrol, 0 chyb |
| `check_restore_flow.py` / `check_zaloha_flow.py` / `check_import_flow.py` / `check_mapa_flow.py` / `check_export_flow.py` / `check_presun_flow.py` | 571 / 184 / 175 / 144 / 129 / 111 — vše 0 chyb |
| `check_env.py` | OK |
| `check_app.py` | OK — 6 obrazovek, 285 prvků, 3177 vzorců, jen 4 preexistující VAROVÁNÍ (beze změny) |
| `mutace_kratky_nazev.py --vystup <kopie 98>` | **14/14** chyceno |
| `make_deploy_mpsv.py` | doběhne, `deploy/mpsv/procesnimapa_1_0_0_98.zip` bajtově shodný (md5) s `deploy/procesnimapa_1_0_0_98.zip` |
| `git status` po `git pull --ff-only` (bez změn) | 13 necommitnutých souborů — viz G-01 |

### Zamítnuté nálezy — kolo 6

*(žádné)*

## Neověřeno — kolo 6

### N-08 · reálné nasazení na MPSV
`STATUS.md` „CO JE NA TOBĚ" popisuje import 98 na MPSV jako upgrade, zapnutí
`AktualizaceKratkehoNazvu` a ruční ověření zkrácení názvu — nic z toho podle
`STATUS.md` k 06.09.2026 18:30 ještě neproběhlo. Statická kontrola (brány,
mutace, trasování REST výrazu, srovnání s produkčně běžícím `RestoreFlow`)
nález nedala kromě P-01 a G-01. Potřeba k doověření: reálný import na MPSV,
zapnutí flow, úprava názvu aktivity delší než 150 znaků a kontrola, že se do
minuty zapíše zkrácený `nazev_kratky` (run history akce `Zapsat_kratky_nazev`
vrátí 204).


## Kolo 5 (03.09.2026, balík `deploy/procesnimapa_1_0_0_92.zip`, F13/C3 + C4)

Zadání: sirotčí aktivity v přehledu (chip „nezařazené") a jejich přiřazení
v detailu (C4), skrytí technické trojice `00`/`00-00`/`00-00-000` odevšad,
`$filter` v `MapaPublishFlow`. Rozsah diffu proti 1.0.0.91 (`git diff 1f08d5d 3cadfa0`):
`src/app_src/App.pa.yaml`, `scr_Ciselnik.pa.yaml`, `scr_Dashboard.pa.yaml`,
`scr_Detail.pa.yaml`, `src/build_mapa_flow.py`, `src/check_app.py`,
`src/check_mapa_flow.py`.

Postup: `deploy/procesnimapa_1_0_0_92.zip` rozbalen do scratchpadu (`unzip -t`
bez chyby na solution i vnořeném `.msapp`), `CanvasApps/*.msapp` rozbalen zvlášť,
nálezy ověřeny přímo nad `Src/*.pa.yaml` a `Workflows/*.json` v balíku, ne nad
`STATUS.md`. Brány spuštěny přímo (ne převzaty): `check_app.py`, `check_solution.py
--vstup runs/vstup_92.zip --vystup deploy/procesnimapa_1_0_0_92.zip`,
`check_mapa_flow.py --solution deploy/procesnimapa_1_0_0_92.zip --base
input/procesnimapa_1_0_0_86.zip`, `check_flow.py`, `mutace_parametry.py --vstup
runs/vstup_92.zip --vystup deploy/procesnimapa_1_0_0_92.zip`.

### Integrita balíku, verze, env proměnné — v pořádku

| co | výsledek |
|---|---|
| `unzip -t` solution zip i vnořený `.msapp` | bez chyby |
| `solution.xml` `<Version>` | `1.0.0.92`, `<Managed>0</Managed>` |
| `environmentvariablevalues.json` v balíku | **není** (greppováno přes celý rozbalený zip) |
| `<defaultvalue>` v definicích env proměnných | **žádná** ze 9 definic ho nemá |
| `<?xml … ?>` deklarace v definicích env proměnných | **žádná** |
| `definition.parameters` v 8 flow | u všech listových/site proměnných `schemaName` sedí na proměnnou, `defaultValue` chybí (žádoucí tvar dle skillu — „deklarace bez defaultValue pro výrazové použití stačí") |
| `mutace_parametry.py` nad `runs/vstup_92.zip`/`deploy/procesnimapa_1_0_0_92.zip` | **4/4** chyceno (ověřeno auditorem samostatně, ne převzato) |
| `Properties.json` v `.msapp` | `DefaultConnectedDataSourceMaxGetRowsCount: 2000` |
| `packed.json` | `LoadFromYaml: true` |
| `check_app.py` | OK — 5 obrazovek, 245 prvků, 2758 vzorců (sedí na `STATUS.md`) |
| `check_solution.py --vstup runs/vstup_92.zip --vystup deploy/procesnimapa_1_0_0_92.zip` | 582 kontrol, 0 chyb |
| `check_mapa_flow.py --base input/procesnimapa_1_0_0_86.zip` | 144 kontrol, OK |
| `check_flow.py` | 26 kontrol, 0 chyb |
| `MapaPublishFlow` vs `MapaPublishScheduled` — `$filter` u všech pěti `GetItems` | přítomný a **shodný** v obou (`Title ne '00'` / `'00-00'` / `'00-00-000'` / `dilci_proces_kod ne '00-00-000'` ×2) |
| `MapaPublishFlow` vs `MapaPublishScheduled` — akce bajtově | `json.dumps(actions, sort_keys=True)` **shoduje se přesně** (dvojče je skutečně dvojče) |

### Logika C4 (`btn_Ulozit.OnSelect` ve `scr_Detail.pa.yaml`) — pořadí i vazby prošly bez nálezu

Ověřeno ručním trasováním nad skutečným zdrojem (ne popisem):
`Patch(Aktivity, …, {Title: varNovyKod, …, puvodni_kod: …})` → `If(varPresun,
ForAll(Filter('Vazba aktivita–dílčí proces', aktivita_kod = varStaryKod) As v,
Patch(…, {Title: …, aktivita_kod: varNovyKod})))` → stávající blok
`RemoveIf(…, dilci_proces_kod = varStaryDp); RemoveIf(…, dilci_proces_kod =
vybraný); Patch(nová primární vazba)`.

- Pořadí (Patch aktivity → přejmenování VŠECH vazeb sirotka → srovnání primární
  vazby) je nutné a dodržené: kdyby `RemoveIf`/`Patch` běžel před `ForAll`,
  hledal by `aktivita_kod = varNovyKod`, který v tabulce ještě neexistuje.
- Sirotek s víc než jednou vazbou (např. „Spravovat…" přidal sirotkovi druhé,
  neprimární zařazení ještě před formálním přiřazením — `btn_Vazby.Visible =
  !varNova` sirotka nevylučuje) — `ForAll` přejmenuje aktivita_kod u **všech**
  vazeb sirotka, ne jen primární, takže druhé zařazení se dotáhne správně
  a osiřelou vazbu ani duplicitní primární vazbu jsem reprodukovat nedokázal.
- Uložení sirotka **beze změny** dílčího procesu (stejný `"00-00-000"`) →
  `varPresun = false` → kód se nepřečísluje, vazby se nehýbou — sedí na „C4
  nedodělek" i na test #12 v `STATUS.md`.
- Zámek kaskády (`DisplayMode.View` u `drp_Agenda`/`drp_Proces`/`drp_Dilci`
  pro `!varNova && !varSirotek`) neblokuje běžné uložení: `Selected.Value`
  dropdownu vychází z `Default`, ne z interakce, takže `IsBlank(drp_Dilci
  .Selected.Value)` zůstává `false` i v režimu jen ke čtení a validace na
  začátku `OnSelect` neshodí uložení názvu/útvaru/stavu.
- Hypotetická vazba „sirotek dostane sekundární zařazení na reálný dílčí
  proces, pak se publikuje mapa dřív, než je formálně přiřazen" jsem prověřil
  proti `mapa_template.html::buildTree()` — `aktByDp` se staví iterací přes
  `d.aktivity` (kde sirotek chybí, protože `$filter` ho z Aktivity datasetu
  vyřadil), takže „visící" vazba na neexistující aktivitu se v `linksByAkt`
  nikdy nevyhledá a strom ji tiše ignoruje. Nejde o díru, jen o odloženou
  viditelnost do formálního přiřazení.

### P-05 · OPRAVIT · `src/app_src/scr_Dashboard.pa.yaml` — fulltextové hledání na přehledu technickou větev nefiltruje

`gal_Strom.Items` má čtyři větve. Výchozí stromový režim (větev přidaná
v tomto balíku) dostal `Left(kod, 2) <> "00"` a správně skrývá agendu `00`,
proces `00-00`, dílčí proces `00-00-000` i sirotčí aktivity pod ním (jejich
`kod` začíná stejným prefixem). Větev fulltextového hledání
(`!IsBlank(txt_HledatD.Text)`, `Search(Filter(colStrom, !vedlejsi, …),
txt_HledatD.Text, kod, nazev)`) žádný ekvivalentní filtr nemá:

```
scr_Dashboard.pa.yaml (balík 92, gal_Strom.Items):
  !IsBlank(txt_HledatD.Text),
  Sort(
      Search(
          Filter(
              colStrom,
              !vedlejsi,
              varDashStav = "" || If(varDashStav = "schváleno", aktS > 0, aktC - aktS > 0)
          ),
          txt_HledatD.Text, kod, nazev
      ),
      kod, SortOrder.Ascending
  ),
```

`colStrom` obsahuje technickou trojici neomezeně (`ClearCollect` nad
`colAgendy`/`colProcesy`/`colDilci` bez filtru — ověřeno v `OnVisible`,
řádky 37-39 a 52-96), jejich `nazev` je doslova **„Nezařazeno"**
(`src/schema.json` → `seed.polozky`). Hledání „Nezařazeno" nebo „00" tedy
vrátí technickou agendu/proces/dílčí proces jako běžné položky plochého
seznamu — přesně to, co má být podle `STATUS.md` skryté „odevšad, kde se
tvářila jako běžná agenda". Protože `gal_Strom.AllItems` je i zdroj exportu
(řádek 857), aktivní hledání s tímto textem by technickou trojici protáhlo
i do exportované tabulky.

**Proč to neodhalila brána.** `kontrola_nezarazenych()` v `check_app.py`
testuje jen, že řetězec `Left(kod, 2) <> "00"` je **kdekoli** v celém textu
vlastnosti `gal_Strom.Items` — a je, jen v jiné větvi `If`. Test na to
nedohlédne, protože porovnává jednu spojenou vlastnost jako celek, ne
jednotlivé větve.

Repro (mutační, nad kopií v scratchpadu, ne v projektu):
1. Nad **nezměněným** `deploy/procesnimapa_1_0_0_92.zip` → `check_app.py`
   → `OK` (bez chyby) — potvrzuje, že mezera je v balíku takhle, jak je,
   a brána ji nechytá.
2. Odebrání `Left(kod, 2) <> "00",` z výchozí (stromové) větve →
   `check_app.py` → `CHYBA: gal_Strom.Items: stromový režim nevylučuje
   technickou větev '00' …` — potvrzuje, že kontrola skutečně něco hlídá,
   jen ne větev hledání.

Dopad: kosmetický/funkční, ne bezpečnostní ani datový — nic se nezapíše
špatně, technická položka se jen dá **najít a zobrazit** tam, kde podle
zadání být neměla. Proto **OPRAVIT**, ne BLOKUJÍCÍ (H2: tiché zúžení tvrzení
„odevšad" je nález i při jinak správném kódu, ale bez rizika pro import
nebo data).
Checklist: C1 (změna je v `Src/*.pa.yaml`, ověřeno že to je zdroj pravdy pro
`LoadFromYaml=true`), H2 (zadání „odevšad" vs. skutečnost).
Doporučená oprava (neprovedeno, jen návrh): přidat `Left(kod, 2) <> "00"`
i do `Filter(...)` uvnitř větve hledání; `kontrola_nezarazenych` rozšířit
tak, aby ověřovala přítomnost filtru v **každé** větvi `Items`, ne v celém
textu najednou.
Stav: otevřeno

## Ověřeno spuštěním — kolo 5

| příkaz / mutace | výsledek |
|---|---|
| `unzip -t deploy/procesnimapa_1_0_0_92.zip` (solution + `.msapp`) | bez chyby |
| `check_app.py` | OK — 5 obrazovek, 245 prvků, 2758 vzorců |
| `check_solution.py --vstup runs/vstup_92.zip --vystup deploy/procesnimapa_1_0_0_92.zip` | 582/0 |
| `check_mapa_flow.py --solution deploy/procesnimapa_1_0_0_92.zip --base input/procesnimapa_1_0_0_86.zip` | 144/144 |
| `check_flow.py --solution deploy/procesnimapa_1_0_0_92.zip` | 26/26 |
| `mutace_parametry.py --vstup runs/vstup_92.zip --vystup deploy/procesnimapa_1_0_0_92.zip` | 4/4 chyceno |
| P-05 repro krok 1: `check_app.py` nad nezměněným balíkem | `OK` (potvrzuje mezeru) |
| P-05 repro krok 2: mutace — odebrání filtru ze stromové větve | `check_app.py` → `NEPROŠLO` (potvrzuje, že brána na jinou věc reaguje) |
| mutace: odebrání `puvodni_kod` z `btn_Ulozit.OnSelect` (C4) | `check_app.py` → `CHYBA: … nemá zapsaný 'puvodni_kod'` — `kontrola_prirazeni_sirotka` funguje |
| `puvodni_kod` jako reálný sloupec schématu | `grep puvodni_kod src/schema.json` → 3 výskyty (existuje na listu Aktivity) |
| `$filter` MapaPublishFlow vs MapaPublishScheduled | shodné (5×5), akce `json.dumps(sort_keys=True)` bajtově shodné |

## Neověřeno — kolo 5

### N-07 · reálný běh zkušebního seznamu balíku 92 na PPF DEV
`STATUS.md` má 14bodový zkušební seznam (import, mikro-změna, karty, chip
nezařazených, přiřazení sirotka, zámek kaskády, publikace mapy) — nic z toho
neproběhlo na živém prostředí, balík byl podle `STATUS.md` k 03.09.2026 večer
ještě needzkoušený. Statická kontrola (brány, mutace, trasování vzorců) nález
nedala kromě P-05; totéž riziko jako historické N-01/N-06 (`LoadFromYaml`
u `Controls/*.json`, které je v tomhle balíku beze změny od `LastSavedDateTimeUTC
09/01/2026 12:13` — novější screeny/vzorce z F13 tedy čekají na první
Studiem-materializovanou mikro-změnu stejně jako `varVerze` v kole 4).
Potřeba k doověření: reálný import + zkušební seznam z `STATUS.md`.

## Re-audit — kolo 4, druhé kolo (25.08.2026, balík `deploy/procesnimapa_1_0_0_60.zip`)

Zadání: ověřit opravy B-01, B-02, B-03 z prvního kola a posoudit argument
u B-03 kriticky. Postup: rozbaleno `deploy/procesnimapa_1_0_0_60.zip` (`unzip -t`
bez chyby, solution i vnořený `.msapp`), spuštěny všechny brány přímo nad
balíkem a vlastní mutace (ne převzetí tvrzení z `STATUS.md`/`AUDIT.md`).

**Regrese — brány nad 1.0.0.60, žádná neselhala:**

| brána | výsledek |
|---|---|
| `check_export_flow.py --solution deploy/procesnimapa_1_0_0_60.zip` | **110/110** (čekáno 110, sedí) |
| `check_solution.py --vstup deploy/procesnimapa_1_0_0_59.zip --vystup deploy/procesnimapa_1_0_0_60.zip` | 234/0, 2 varování (viz B-01) |
| `check_mapa_flow.py --solution deploy/procesnimapa_1_0_0_60.zip` | 139/139 |
| `check_flow.py --solution deploy/procesnimapa_1_0_0_60.zip` | 17/17 |
| `check_app.py` | OK — 199 prvků, 2242 vzorců, stejná 2 pre-existující VAROVÁNÍ jako v prvním kole |
| `solution.xml` verze | `1.0.0.60` (> `1.0.0.59`), `<Managed>0</Managed>` |

Razítko verze se nezaviklo nic z existujícího — potvrzeno.

### B-01 · ČÁSTEČNĚ OPRAVENO — hlavní mezera zalátaná, jedna reálná zůstává v migračním postupu

**Co je opravené a funguje.** `adresa_webu()` + `adresy_ve_flow()`
(`src/check_solution.py:41-90`) teď prochází `Workflows/*.json` a srovnává
každou nalezenou `https://…sharepoint.com…` adresu s adresou webu, na který
je připojená canvas app (čtenou z `customizations.xml`). Pozitivní kontrola —
ověřeno vlastní mutací, ne převzato:
```
# ExportFlow: "…/testovaci_subsajta/procesnimapa" -> "…/testovaci_subsajta/JINY"
check_solution.py --vstup deploy/procesnimapa_1_0_0_59.zip --vystup mutOK.zip
→ CHYBA: ExportFlow-….json míří na jiný web než canvas app: […/JINY']
→ NEPROŠLO
```
Funguje přesně na scénář, který B-01 popisoval — pokud se do balíku dostane
flow ukazující na jiný web, než na jaký je připojená appka, import se odmítne.
`HANDOVER.md` (řádky 181-193) a `PLAN.md` (krok 12, řádky 285-296) teď správně
říkají „20 míst" (1 `varMapaUrl` + 19 ve flow) a že se 19 z nich **nepíše
ručně** — sedí to na to, co `check_solution.py` v kontrole `adresy_ve_flow()`
skutečně dělá.

**Tři mutace, které kontrolu obejdou** (zkoušeno, jak žádáno — jiná forma
adresy, jiná doména, adresa jen v `customizations.xml`):

1. **Adresa bez `https://`** — `re.findall(r"https://[A-Za-z0-9.-]+\.sharepoint\.com[^\"']*", …)` vyžaduje doslovné `https://` na začátku. Vložená cizí adresa `ATTACKER-TENANT.sharepoint.com/sites/evil` (bez schématu) → `check_solution.py` → 234/0, **OK**, počet míst se nezvýšil.
2. **Adresa mimo `*.sharepoint.com`** — `https://attacker.example.com/exfiltrate` vložená do `ExportFlow` → 234/0, **OK**. Kontrola `adresy_ve_flow()` je záměrně úzká na `sharepoint.com`; obecná kontrola `http(s)://` v `*.pa.yaml` (řádek 236-249) se na `Workflows/*.json` nevztahuje, takže mimo `sharepoint.com` domény ve flow nekontroluje nic.
3. **Adresa jen v `customizations.xml` mimo `<ConnectionReferences>`** — vložen komentář s cizí adresou hned za `</ConnectionReferences>` → 234/0, **OK**. `customizations.xml` se používá jen jako zdroj referenční adresy, sám se na cizí adresy neprohledává.

Tohle jsou reálné mezery, ale v **dnešním hrozbovém modelu projektu** (jeden
asistent upravuje vlastní build skripty, žádný cizí přispěvatel) mají nízkou
váhu — nikdo sem cizí adresu takhle nevloží náhodou. Řadím je jako **DROBNÉ/
POZNÁMKA**, ne jako důvod nechat B-01 otevřené.

**Skutečný důvod, proč B-01 není 100% uzavřené — mezera v `HANDOVER.md`/`PLAN.md`
kroku 12, ne v bráně.** Migrační postup (`PLAN.md` řádky 287-296, bod 5) říká
„lokálně znovu spustit `build_mapa_flow.py`, `build_export_flow.py` a
`add_mapa_schedule.py`" — tedy tři skripty. Ve flow je ale **čtvero**, páté
`AktualizaceKratkehoNazvu` se staví skriptem `src/build_flow.py`, který v
migračním postupu chybí úplně:
```
grep -o 'ppfbanka.sharepoint.com[^"]*' Workflows/AktualizaceKratkehoNazvu*.json | wc -l
→ 2   (dataset triggeru + dataset zápisové akce)
```
`src/build_flow.py` navíc **nebere adresu z připojení appky** jako ostatní tři
skripty — dokumentace v jeho vlastní hlavičce říká „Trigger, connection
reference ani GUID flow se nemění" (řádek 6) a obsahuje **vlastní natvrdo
zapsanou konstantu** `LIST_AKTIVITY = "9dfbb5a1-…"` (řádek 20, GUID listu
Aktivity na vývojové site), o které komentář výslovně píše, že s runtime
výrazem „se flow naimportuje, ale nejde zapnout" — tedy ji nejde obejít, musí
se fyzicky přepsat v `src/build_flow.py` na GUID listu Aktivity na MPSV.
Trigger sám navíc podle stejné hlavičky vzniká tak, že „uživatel dodá z
designeru kostru" — tedy ručním exportem nové kostry z Power Automate
designeru nad MPSV listem, ne rerunem skriptu nad existující definicí.

Kdo by se řídil doslova sedmi kroky v `PLAN.md` krok 12, dostane se do
kroku 7 (`check_solution.py`), brána správně **selže** na `AktualizaceKratkehoNazvu`
(potvrzeno — `adresy_ve_flow()` prochází všechna čtyři flow, tohle nevynechává),
ale kroky 1-7 mu neřeknou, co s tím — čtvrtý build skript, ruční export nové
kostry z designeru a editace konstanty v Pythonu nejsou zmíněné nikde.

Checklist: B1, NFR-3, kritérium přijetí A6, H3 (chybí klikací návod na tuhle
konkrétní část).
Stav: **částečně opraveno** — hlavní mechanismus (B1 nad flow) funguje a je
mutačně ověřený; zbývá doplnit `AktualizaceKratkehoNazvu`/`build_flow.py` do
`PLAN.md` kroku 12 a `HANDOVER.md`. Tři drobné mezery v `adresy_ve_flow()`
(bez schématu, mimo sharepoint.com, mimo `Workflows/`) jsou POZNÁMKA, ne
blokující — nízké riziko v jednouživatelském vývoji, ale stojí za zapsání pro
budoucnost.

### B-02 · STŘEDNÍ · STÁLE OTEVŘENO — oprava zúžila mezeru, nezavřela ji

**Původní bypass (kolo 4, první kolo) je opravený a ověřený.** Mutace „smazat
`mso-number-format` jen z `td {}`, nechat v `th {}`" spuštěná znovu nad
1.0.0.60:
```
check_export_flow.py --solution mutE_orig.zip
→ kontrol: 110
→ CHYBA: textový formát není v pravidle td …
→ CHYBA: datové buňky (td) nemají vynucený textový formát …
→ NEPROŠLO
```
`css_pravidlo()` teď parsuje `<style>` blok na dvojice `selektor{tělo}` a
významová vrstva čte formát konkrétně z těla pravidla `td` — funguje přesně
na nahlášený scénář.

**Nová mutace — CSS kaskáda — kontrolu obchází.** `css_pravidlo()`
(`src/check_export_flow.py:449-457`) vrací **první** shodu se selektorem
(`for pravidlo in re.finditer(...): if pravidlo.group(1) == selektor: return …`).
Když se do `<style>` bloku přidá **druhé** pravidlo `td {}` (za tím původním,
před `</style>`), které formát ruší, `css_pravidlo(dokument, "td")` najde a
vrátí jen to PRVNÍ (správné) a druhé (poškozující) nikdy neuvidí — ale
skutečný prohlížeč/Excel při renderu **respektuje pořadí v kaskádě** a použije
poslední pravidlo se stejnou specificitou pro týž selektor, tedy to poškozené:
```
# do <style> bloku ExportFlow přidáno těsně před </style>:
#   td {mso-number-format:"General";}
check_export_flow.py --solution mutD_cascade.zip
→ kontrol: 110
→ OK — ExportFlow odpovídá kontraktu          (mělo by NEPROJÍT)
```
Reálný dopad by byl identický s původním nálezem — Excel by `01-01` znovu
četl jako datum — jenže tentokrát by ho způsobila **druhá**, ne první výskyt
pravidla `td {}`, a `css_pravidlo()` na druhý výskyt nedohlédne.

Vedlejší zjištění (ne bypass, opačný směr — přísnost, ne díra): kombinovaný
selektor `td, th {…}` (funkčně rovnocenný zápis) branou **neprojde** — `css_pravidlo()`
hledá přesnou shodu selektoru `"td"`, `"td, th"` nenajde. Ověřeno mutací
(2 chyby, `NEPROŠLO`). Nejde o bezpečnostní mezeru (nic škodlivého neprojde),
jen o menší tvrdost kontroly vůči alternativním, ale platným zápisům CSS —
POZNÁMKA, ne akční položka.

Checklist: F3, E2 — stejné jako v prvním kole; oprava adresovala nahlášenou
mutaci doslovně, ne obecnou třídu problému („poslední platné pravidlo pro
daný selektor", ne „první nalezené").
Stav: **otevřeno**. Doporučení pro opravu (nedělat, jen návrh): v `css_pravidlo()`
vracet **poslední** shodu (`re.finditer` → uložit poslední, ne `return` na
první), protože to odpovídá skutečné CSS kaskádě.

### B-03 · ESKALACE · zůstává otevřená — mitigace je reálná, ale „ověřeno provozem" pro `varVerze` neplatí

**Souhlasím s tím, co je ověřené.** `vloz_verzi()` (`src/build_app.py:132-144`)
skutečně selže, když razítko v YAML nenajde nebo najde vícekrát — ověřeno
izolovaně (bez zásahu do zdrojů appky, jen na kopii regexu):
```
0 shod  → CHYBA: razítko verze nahrazeno 0x, čekal jsem 1x
2 shody → CHYBA: razítko verze nahrazeno 2x, čekal jsem 1x
1 shoda → v pořádku
```
A razítko v balíku **odpovídá** verzi v `solution.xml`:
```
solution.xml:              <Version>1.0.0.60
Src/App.pa.yaml (v .msapp): Set(varVerze, "1.0.0.60")
```
Tooltip `lbl_AppNazevD` v `scr_Dashboard.pa.yaml` (řádek 156-158) skutečně
vysvětluje uživateli, co dělat, když číslo nesedí. Tohle vše je v pořádku a
je to reálné zlepšení proti prvnímu kolu.

**Argument „tlačítko Export funguje bez Controls → tím padá N-06" sedí jen
pro Export, ne obecně — a nesedí pro `varVerze` samotné.** Kritický bod:
`varVerze` je **přesně tak nová YAML-only věc jako kdysi bylo tlačítko Export**
— a na rozdíl od tlačítka Export **nebyla nikdy provozně vyzkoušená**, protože
vznikla až dnes, v 1.0.0.60. Ověřeno přímo:
```
grep -c "varVerze" sol60/msapp60/Controls/4.json
→ 0
md5sum sol60/msapp60/Controls/4.json
→ bb77b659c8dd42c2dd4c974f3d9494f6   (STEJNÝ md5 jako 1.0.0.57 a 1.0.0.59)
```
`Controls/4.json` je **stále** bajtově identické s 1.0.0.57 — tenhle balík
neprošel žádnou další Studiem-materializovanou úpravou od 1.0.0.57. Tlačítko
Export prošlo provozní zkouškou (uživatel ho opravdu použil), ale `varVerze`
zatím **ne** — je to tatáž kategorie „existuje jen v YAML", jen o den mladší
a dosud nepotvrzená. Extrapolovat z jednoho ověřeného případu (Export) na
obecné „Studio spolehlivě materializuje cokoli z YAML, vždycky" je logický
skok, který moje data nepodporují o nic víc, než podporovala minule.

**Diagnostika má navíc vlastní mez, kterou stojí za to pojmenovat.** Tooltip
slibuje: „Když číslo neodpovídá naposledy importovanému balíku, neproběhla
mikro-změna…" — implikuje, že po neúspěšné mikro-změně uvidí uživatel
**špatné, ale existující** číslo. Ve skutečnosti je to jinak: dokud mikro-změna
+ Save + Publish neproběhne, **celá tahle vlastnost appky (popisek i tooltip)
v publikované appce vůbec neexistuje** — je to týž mechanismus jako u tlačítka
Export, ne výjimka z něj. Selhání se tedy neprojeví špatným číslem, ale
absencí čísla/tooltipu úplně — což jako signál funguje (nic tam není → něco
je špatně), ale ne tak, jak text tooltipu popisuje.

Nejde o BLOKUJÍCÍ ani o nový kód k opravě — mechanismus `LoadFromYaml` má už
dva kola auditu reálných dokladů (duch `.msapp` v kole 3, Export v provozu
teď) a `check_solution.py` jedinou nutnou podmínku (`LoadFromYaml=true`)
hlídá. Jde o to, že věta „B-03 zmírněn a ověřen provozem" a „N-06 padá" jsou
přesnější jako „mechanismus jako celek má silné doklady; **tahle konkrétní
nová vlastnost** je teprve na řadě k prvnímu ověření" — a to je rozdíl, který
má smysl vědět předtím, než se na `varVerze` bude příště spoléhat jako na
hotovou pojistku.

Checklist: C1 (viz odůvodnění v prvním kole — obecné pravidlo neplatí doslova,
princip rizika ano).
Stav: **eskalace zůstává otevřená**, s upřesněním rozsahu. Rozhoduje uživatel;
navrhované (ne provedené) doladění: až se `varVerze`/tooltip poprvé provozně
potvrdí (stejně jako Export), zapsat to výslovně vedle B-03, ne mlčky
předpokládat, že to platí od chvíle, kdy to bylo napsané do YAML.

## Ověřeno spuštěním — kolo 4, druhé kolo

| příkaz / mutace | výsledek |
|---|---|
| `unzip -t deploy/procesnimapa_1_0_0_60.zip` (solution + `.msapp`) | bez chyby |
| `check_export_flow.py --solution deploy/procesnimapa_1_0_0_60.zip` | 110/110 |
| `check_solution.py --vstup deploy/procesnimapa_1_0_0_59.zip --vystup deploy/procesnimapa_1_0_0_60.zip` | 234/0, 2 varování |
| `check_mapa_flow.py` / `check_flow.py` / `check_app.py` | 139/139, 17/17, OK — beze změny proti prvnímu kolu |
| B-01 pozitivní kontrola (cizí web, `https://`, `sharepoint.com`) | **CHYBA/NEPROŠLO** — brána funguje na nahlášený scénář |
| B-01 mutace: cizí adresa bez `https://` | 234/0, **OK** (mělo by NEPROJÍT) |
| B-01 mutace: cizí `https://` adresa mimo `sharepoint.com` | 234/0, **OK** (mimo záběr kontroly) |
| B-01 mutace: cizí adresa jen v `customizations.xml` mimo `<ConnectionReferences>` | 234/0, **OK** (soubor se na cizí adresy neprohledává) |
| B-02 původní mutace (`td` bez formátu, `th` s formátem) | 2 chyby, **NEPROŠLO** — opraveno |
| B-02 nová mutace (druhé pravidlo `td {}` v kaskádě, formát zrušen) | 110/110, **OK** (mělo by NEPROJÍT) |
| B-02 mutace: kombinovaný selektor `td, th {…}` (funkčně rovnocenné) | 2 chyby, **NEPROŠLO** (přísnost, ne díra) |
| `vloz_verzi()` izolovaně: 0 shod / 2 shody / 1 shoda | selže / selže / projde — sedí na tvrzení |
| `varVerze` v balíku vs `solution.xml` | oba `1.0.0.60` — sedí |
| `Controls/4.json` (1.0.0.60) vs 1.0.0.57 | **bajtově identické**, `varVerze` v Controls 0× — `varVerze` nikdy neprošlo Studiem |
| `grep ppfbanka Workflows/AktualizaceKratkehoNazvu*.json` | 2 (dataset triggeru + zápisu) — chybí v migračním postupu |

## Neověřeno — kolo 4

### N-04 · chování `Download()` v appce vložené na SharePoint stránku
Beze změny od prvního kola — `Download()` je nativní funkce Power Apps
runtime (běží ve vlastním iframe appky), ne JS v šabloně stránky. Bez
přístupu k reálně vloženému webpartu nejde ověřit, že `Download(varExportUrl)`
v tomhle konkrétním kontextu spustí stažení. Potřeba: appka vložená na
skutečné SharePoint stránce + klik na Export.

### N-05 · injekce vzorců do buněk Excelu — **UZAVŘENO 25.08.2026**

Ověřeno v reálném Excelu. Aktivita `01-01-001-0004` s názvem `=1+1`
vyexportovaná do `.xls` se zobrazí jako **text `=1+1`**, ne jako výsledek `2`.
`mso-number-format:"\@"` tedy potlačuje i vyhodnocení vzorce, nejen jeho
zobrazení — na rozdíl od skutečného `.csv`, kde je formula injection známá
díra. Doloženo snímkem od uživatele.

Vedlejší pozorování z téhož snímku: kódy jsou textem (`01-01`,
`01-01-001-0004`), diakritika sedí, úroveň je číslo. Zelené trojúhelníčky
v rozích buněk jsou Excelí upozornění „číslo uložené jako text" — u
identifikačních kódů je to přesně žádaný stav, ne vada.

Původní znění: `mso-number-format:"\@"` vynucuje zobrazení jako text, ale bez
reálného Excelu nejde ověřit, jestli tím spolehlivě potlačí i vyhodnocení
vzorce u polí začínajících `=`/`+`/`-`/`@`.

### N-06 · reálné chování Studia při `LoadFromYaml=true` po importu — **ČÁSTEČNĚ POTVRZENO, NEUZAVŘÍT CELÉ**
Mechanismus jako celek má teď dva nezávislé doklady napříč koly (duch
`.msapp` v kole 3, tlačítko Export potvrzené v provozu 25.08.2026) — pro
**dřív ověřený obsah** je N-06 rozumné považovat za vypořádané. Nepotvrzuje to
ale automaticky **každou budoucí** YAML-only vlastnost v okamžiku, kdy vznikne
— viz B-03 výše: `varVerze`/tooltip v 1.0.0.60 je stejná kategorie jako kdysi
Export, ale svoje první provozní ověření teprve čeká (`Controls/4.json` v
1.0.0.60 je pořád bajtově 1.0.0.57, `varVerze` v něm 0×). Potřeba k plnému
uzavření pro tuhle konkrétní vlastnost: reálný import 1.0.0.60, mikro-změna,
Save, Publish, a potvrzení, že se tooltip s číslem `1.0.0.60` v appce objeví.

## Nálezy — kolo 4, první kolo (25.08.2026, balík `deploy/procesnimapa_1_0_0_59.zip`)

Historický záznam prvního kola — stavy nálezů viz re-audit výše, tady zůstává
původní text beze změny kvůli reprodukovatelnosti.

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

### B-01 · VÁŽNÝ (první kolo) · testovací tenant v flow je mimo dosah kontroly hardcoded URL

`check_solution.py` prohledávalo na `http://`/`https://` **jen soubory
`*.pa.yaml`** canvas appky. `Workflows/*.json` se vůbec neprocházelo.

Repro nad rozbaleným `deploy/procesnimapa_1_0_0_59.zip`:
```
grep -o "ppfbanka.sharepoint.com[^\"]*" Workflows/*.json | wc -l
→ AktualizaceKratkehoNazvu: 2, ExportFlow: 2, MapaPublishFlow: 7,
  MapaPublishScheduled: 7   (celkem 18 výskytů ve všech čtyřech flow)
grep -o "ppfbanka.sharepoint.com[^&\"<]*" customizations.xml
→ 1 další výskyt v ConnectionReferences canvas appky
```
Jediné varování, které balík k migraci vydávalo, znělo „adresa mapy
`varMapaUrl` je natvrdo, je to jediné místo" — neodpovídalo to skutečnosti.

Checklist: B1 (rozšířeno o Workflows/*.json), NFR-3, kritérium přijetí A6.
**Stav po re-auditu (druhé kolo, 1.0.0.60): částečně opraveno — viz sekci výše.**

### B-02 · STŘEDNÍ (první kolo) · mezera v `check_export_flow.py` — kontrola textového formátu Excelu nekoukala na správné pravidlo

Kontrola `kontrakt()` ověřovala jen, že se řetězec `mso-number-format:"\@"`
vyskytuje kdekoli v textu akce `Dokument` — a ten se v šabloně vyskytoval
dvakrát (`td {}` i `th {}`), takže mazání jen z `td {}` prošlo bez povšimnutí.

Repro:
```
idx = data.find('td {mso-number-format')
end = data.find(';', idx) + 1
mutated = data[:idx] + 'td {' + data[end:]
check_export_flow.py --solution mutace3.zip → kontrol: 109, OK   (mělo NEPROJÍT)
```

Checklist: F3, E2.
**Stav po re-auditu (druhé kolo, 1.0.0.60): STÁLE OTEVŘENO — nová mutace (CSS
kaskáda) obchází i opravenou verzi, viz sekci výše.**

### B-03 · ESKALACE (první kolo) · Controls/*.json bylo od 1.0.0.57 bajtově beze změny

Potvrzující nález, ne vada v kódu. `Controls/*.json` pro všech pět souborů
v zabaleném `.msapp` bylo bajtově identické s 1.0.0.57 (md5 shoda); tlačítko
Export existovalo jen v `Src/*.pa.yaml`. Mechanismus (`LoadFromYaml=true`)
je záměrný a `check_solution.py` ho hlídá, ale nic v balíku neuměl potvrdit,
že po importu proběhla ve Studiu mikro-změna → Save → Publish.

Checklist: C1 (princip rizika platí, doslovné pravidlo skillu ne).
**Stav po re-auditu (druhé kolo, 1.0.0.60): mitigace (`varVerze`) přidána a
funguje jak má, ale eskalace zůstává otevřená s upřesněním — viz sekci výše.
„N-06 padá" a „ověřeno provozem" pro `varVerze` konkrétně neplatí.**

## Ověřeno spuštěním — kolo 4, první kolo

| příkaz | výsledek |
|---|---|
| `unzip -t deploy/procesnimapa_1_0_0_59.zip` | bez chyby |
| `unzip -t` vnořeného `.msapp` | bez chyby (varování o `\` v cestách — stejné už v 1.0.0.57, produkuje ho `pac` CLI, ne tento projekt) |
| `check_export_flow.py --solution deploy/procesnimapa_1_0_0_59.zip` | 109/109 |
| `check_solution.py --vstup input/procesnimapa_1_0_0_57.zip --vystup deploy/procesnimapa_1_0_0_59.zip` | 229/0, 1 varování (jen `varMapaUrl`, viz B-01) |
| `check_mapa_flow.py --solution deploy/procesnimapa_1_0_0_59.zip` | 139/139 |
| `check_flow.py --solution deploy/procesnimapa_1_0_0_59.zip` | 17/17 |
| `check_app.py` | OK — 5 souborů, 4 obrazovky, 199 prvků, 2241 vzorců |
| mutace `build_export_flow.py` spuštěná 2× nad týmž zipem | idempotentní |
| mutace: odstraněné HTML escapování `nazev` v `ExportFlow` | `check_export_flow.py` → 6 chyb, `NEPROŠLO` |
| mutace: `mso-number-format` odstraněný jen z `td {}`, ponechaný v `th {}` | `check_export_flow.py` → 109/109, `OK` (viz B-02) |
| `solution.xml`: verze, `Managed` | `1.0.0.59` > `1.0.0.57`, `<Managed>0</Managed>` |
| `Properties.json` v `.msapp` | `DefaultConnectedDataSourceMaxGetRowsCount: 2000` |
| `References/DataSources.json` | `ExportFlow` registrován |

## Neověřeno — kolo 4, první kolo (historický záznam, viz aktualizace výše)

### N-04 · chování `Download()` v appce vložené na SharePoint stránku
Viz aktuální znění v sekci „Neověřeno — kolo 4" výše (beze změny).

### N-05 · injekce vzorců do buněk Excelu — **UZAVŘENO**
Ověřeno v reálném Excelu 25.08.2026, viz sekci „Neověřeno — kolo 4" výše.

### N-06 · reálné chování Studia při `LoadFromYaml=true` po importu
Původně otevřené, po prvním kole navrhováno jako uzavřené argumentem
„Export funguje bez Controls". Re-audit (druhé kolo) tenhle závěr zpřesnil —
viz aktuální znění výše: platí pro už ověřený obsah, neplatí automaticky pro
každou novou YAML-only vlastnost.

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


## Vyřízení druhého kola — 1.0.0.61 (25.08.2026)

Auditor rozporoval všechny tři stavy zapsané po prvním kole. Dvakrát měl
věcně pravdu, jednou částečně.

### B-01 — námitka přijata, doplněno

**Přijato:** migrační postup mluvil o třech build skriptech, ale flow jsou
čtyři. `AktualizaceKratkehoNazvu` se rerunem skriptu nespraví — `build_flow.py`
má GUID listu Aktivity natvrdo v konstantě `LIST_AKTIVITY` (runtime výraz by
flow znemožnil zapnout) a trigger je nad tím listem, takže se musí založit
nová kostra v designeru nad webem MPSV. Kdo by šel podle starého postupu,
narazil by až na spadlé bráně bez návodu, co dál. Doplněno do `PLAN.md` jako
krok 12/5b a do `HANDOVER.md` jako výjimka.

**Přijato i to, co auditor sám řadil jen jako poznámku** — všechna tři obejití
kontroly adres jsou zalátaná a mutačně ověřená: adresa bez schématu
(`utocnik.sharepoint.com/...`), cizí doména mimo `sharepoint.com`
(`https://utocnik.example.com/...`) i původní cizí web. Kontrola nově hlídá
tři věci: celou adresu proti webu appky, množinu hostitelů proti allowlistu
(`schema.management.azure.com`, `www.w3.org`) a tenanty uvedené bez schématu.

**Zamítnuto:** cizí adresa v `customizations.xml` mimo `<ConnectionReferences>`.
Ten soubor je plný legitimních jmenných prostorů `schemas.microsoft.com`
a generuje ho Studio, ne my; allowlist nad ním by dělal hluk bez užitku.
Build skripty do něj sahají jen klonováním existujících uzlů `<Workflow>`.

### B-02 — námitka přijata, kontrola přepsaná na kaskádu

`css_pravidlo()` vracelo **první** shodu se selektorem, takže druhé pravidlo
`td {}`, které formát ruší, branou prošlo — funkčně týž dopad jako původní
nález. Nahrazeno `css_hodnota()`, které jde všemi pravidly a vrací
**poslední** hodnotu vlastnosti, tedy tu, kterou použije Excel; selektory
oddělené čárkou se rozebírají. Navíc přibyla kontrola, že buňky nemají inline
`style` — ten by kaskádu přebil a ve `<style>` bloku by nebyl vidět.

Mutačně ověřeno: druhé pravidlo `td`, `td, th {…}` i inline styl buňky bránu
shodí. Kontrol 110 → 111.

### B-03 — námitka přijata v podstatě, zamítnuta v důsledku

**Přijato:** `varVerze` je stejně nová YAML-only vlastnost jako kdysi tlačítko
Export a Studiem zatím neprošla. Tooltip proto sliboval špatný příznak selhání
— při nepublikované verzi se neukáže špatné číslo, ale **žádná nápověda**.
Text opraven: „Když se tahle nápověda neukáže vůbec nebo číslo neodpovídá…".
Diagnostická hodnota tím zůstává, jen se nazývá pravdivě.

**Zamítnuto:** požadavek znovu otevřít N-06. Ověřovaná otázka N-06 zní, jestli
Studio po importu appku načte z `Src/*.pa.yaml` — a na to je důkaz tvrdý:
tlačítko Export ve `Controls/*.json` není a v provozu funguje. Že každá nová
vlastnost projde toutéž cestou, je vlastnost mechanismu, ne nová neznámá.
Kdyby YAML nefungoval, nefungoval by ani Export.

### Uzavření

Smyčka končí na stropu dvou kol podle `/audit`. Žádný nález nebyl blokující,
takže se dodává. **N-05 uzavřeno** týž den: uživatel vyexportoval aktivitu s názvem `=1+1`
a Excel ji ukázal jako text. Vynucený textový formát tedy potlačuje
i vyhodnocení vzorce. Z kola 4 nezůstává otevřené nic kromě **N-04**
(`Download()` v appce vložené na SharePoint stránku), které jde ověřit
až při umístění appky na stránku.
