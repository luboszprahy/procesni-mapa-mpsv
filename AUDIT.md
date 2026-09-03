# AUDIT — Procesní mapa MPSV

Poslední audit: 03.09.2026 22:10 · auditor: powerplatform-auditor · kolo: 5 (balík `deploy/procesnimapa_1_0_0_92.zip`, F13/C3+C4)
Verdikt kolo 5: NÁLEZY (0 blokujících / 1 opravit / 0 eskalací) — balík je bezpečný k importu do PPF DEV,
  nic v něm neshodí prostředí ani nepřepíše hodnoty; jediný nález je funkční mezera bez dopadu na import
Předchozí: 25.08.2026 · kolo: 4, druhé kolo (re-audit balíku `deploy/procesnimapa_1_0_0_60.zip`)
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
