# STATUS — Procesní mapa MPSV

Aktualizováno: 2026-08-19 10:31

## CO JE NA TOBĚ

Zadavatelka není k dispozici (stav 19.08.2026), takže se pracuje podle best
practice. Otevřené otázky mají prozatímní rozhodnutí v `PRD.md` §9 — všechna
jsou volená tak, aby se dala revidovat bez ztráty dat.

1. **Teď hned nic.**
2. **Až bude zadavatelka k dispozici:** projít `PRD.md` §9 (5 otázek) a potvrdit
   nebo změnit prozatímní rozhodnutí. Ukázat jí `viz/mapa_prototyp.html`.
3. **Před nasazením na MPSV, ne dřív:** nechat potvrdit výchozí číslování kódů
   (viz sekce „Identifikační kódy" níže).
4. **Až řeknu, že je to připravené:** spustit v konzoli prohlížeče na
   `/sites/DigiData_D/testovaci_subsajta/procesnimapa` nejdřív
   `src/setup_sharepoint.js`, pak `src/import_data.js`. Zatím nespouštěj —
   čeká se na re-audit (kolo 2).

## CO DĚLÁM JÁ (další krok)

**Re-audit F1** (kolo 2) — první kolo našlo 1 blokující + 2 k opravě, všechny
tři jsou opravené a ověřené, ale re-audit ještě neproběhl. Až projde, je F1
připravená na první ostrý běh. Pak F2 (canvas app) / F3 (publikační flow).

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
