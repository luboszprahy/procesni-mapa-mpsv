# PRD — Centrální rejstřík agend a procesů MPSV + procesní mapa

Verze: 1.0 (19.08.2026) | Stav: návrh k odsouhlasení zadavatelkou

## 1. Kontext

Projekt „Úprava Organizačního řádu MPSV s využitím metod procesního řízení"
(realizace do 06/2028) mapuje agendy, procesy, dílčí procesy a aktivity napříč
ministerstvem. Dnes běží evidence na excelových evidenčních kartách útvarů
a jednom centrálním rejstříku, konsolidace je ruční.

Rozsah poroste z dnešních ~46 aktivit (sekce 3) na celé ministerstvo. Ruční
evidence tento růst neunese — aktualizace, hledání vazeb, řízení změn
a odhalování duplicit mezi útvary přestanou být zvládnutelné.

## 2. Cíl

1. **Centrální rejstřík** agend/procesů/dílčích procesů/aktivit v SharePoint Online,
   který nahradí ruční konsolidaci excelových karet.
2. **Procesní mapa**, která se generuje z dat a nemusí se ručně přegenerovávat;
   je trvale viditelná na SharePoint stránce.
3. Podklad pro **automatizované generování textu organizačního řádu** (fáze 2).

## 3. Uživatelé a role

| Role | Rozsah | Co dělá v řešení |
|---|---|---|
| Správce procesního rámce | celé MPSV | číselníky agend/procesů, schvalování, konzistence, publikace mapy |
| Sekční správce procesního rámce | sekce | pořizuje a udržuje aktivity své sekce, navrhuje nové dílčí procesy |
| Vlastník agendy / procesu / dílčího procesu | dle úrovně | připomínkuje, potvrzuje svou část |
| Vykonávající útvar (oddělení) | vlastní aktivity | čte, hlásí neshody |
| Ostatní zaměstnanci | celé MPSV | čtou procesní mapu |

## 4. Doménový model

Čtyřúrovňová hierarchie, jeden řádek evidence = jedna aktivita:

```
Agenda (AA) → Proces (AA-BB) → Dílčí proces (AA-BB-CCC) → Aktivita (AA-BB-CCC-DDDD)
```

- Vlastník **není** součástí kódu — eviduje se samostatně (organizační změny nesmí
  měnit kódy).
- Aktivita může patřit do **více dílčích procesů** → vazba M:N přes vazební tabulku.
- Číselník agend/procesů/dílčích procesů pochází z **rejstříku**; aktivity
  z **evidenčních karet** útvarů.

## 5. Funkční požadavky

### FR-1 Rejstřík (SharePoint)
- FR-1.1 Číselníky Agendy / Procesy / DilciProcesy, list Aktivity, vazební list
  AktivitaDilciProces.
- FR-1.2 Pole dle evidenční karty: Agenda, Vlastník agendy, Proces, Vlastník procesu,
  Dílčí proces, Vlastník dílčího procesu, Aktivita, Vykonává útvar, Spolupracuje,
  Vnitřní předpis, Text pro OŘ, Datum aktualizace, Stav (pracovní/schváleno).
- FR-1.3 Zapnuté verzování na všech listech.
- FR-1.4 Filtrování podle sekce, odboru, oddělení, agendy, procesu, dílčího procesu.
- FR-1.5 Export do Excelu (nativní SharePoint export vybraného zobrazení).
- FR-1.6 Fulltextové hledání nad všemi čtyřmi úrovněmi.
- FR-1.7 Příznak `stav_mapovani` na všech úrovních: `zmapováno` /
  `zmapováno jiným útvarem` / `nezmapováno`. Do rejstříku jdou **všechny** položky,
  i ty bez aktivit.

### FR-2 Pořizovací aplikace (Power Apps canvas)
- FR-2.1 Kaskádové číselníky agenda → proces → dílčí proces (SharePoint formulář to neumí).
- FR-2.2 Automatické přidělení kódu `AA-BB-CCC-DDDD` (další volné DDDD v rámci dílčího procesu).
- FR-2.3 Přiřazení aktivity k více dílčím procesům (zápis do vazebního listu).
- FR-2.4 Rozhraní blízké dnešní evidenční kartě — jeden formulář = jedna aktivita.
- FR-2.5 Přepínač stavu pracovní/schváleno; `Datum aktualizace` se plní automaticky.

### FR-3 Procesní mapa (read-only pro všechny)
- FR-3.1 Strom Agenda → Proces → Dílčí proces → Aktivita s počty aktivit ve větvích.
- FR-3.2 Fulltext, filtr vykonávajícího útvaru, filtr stavu zmapování
  (zmapované / celý rejstřík / nezmapované).
- FR-3.3 Detail aktivity: vykonává, spolupracuje, vnitřní předpis, kód.
- FR-3.4 Nezmapované větve vizuálně odlišené (ztlumené).
- FR-3.5 Publikace automatická — po změně dat se mapa přegeneruje bez ručního zásahu.

### FR-4 Generování textu OŘ (fáze 2, po 06/2028)
- FR-4.1 Z pole `Text pro OŘ` aktivit sestavit text organizačního řádu v členění
  podle vykonávajících útvarů, ve tvaru vzoru `VZOR_OŘ - nově sekce 3`.

## 6. Nefunkční požadavky a omezení

- **NFR-1 Bez dodatečných licencí** — SharePoint Online + Power Apps/Automate v rámci M365.
  Žádný Dataverse, žádné premium konektory.
- **NFR-2 Migrovatelnost do Dataverse** bez ztráty dat a logiky → vztahy nesou
  **textové přirozené klíče** (kódy), ne SharePoint lookup ID.
- **NFR-3 Přenositelnost mezi tenanty** — vývoj probíhá v cizím tenantu (PPF),
  nasazení na MPSV. Žádné hardcoded URL, listy zakládá skript, konfigurace
  přes environment variables.
- **NFR-4 Do vývojového tenantu jdou jen anonymizovaná data** (`runs/anonym/`).
- **NFR-5 Bez externích CDN** — mapa musí být self-contained.
- **NFR-6 Objemové stropy:** SharePoint list view threshold 5 000 položek,
  Power Apps delegace 2 000. Do 06/2028 se počet aktivit za celé MPSV k těmto
  hranicím může přiblížit → indexované sloupce, delegovatelné filtry, mapa
  se zapečenými daty (nefetchuje).
- **NFR-7 Interní názvy sloupců bez diakritiky** (přejmenování zobrazovaného názvu
  interní název nemění; REST `$select` pracuje s interními).

## 7. Rozsah — co NENÍ součástí

- Integrace na personální systémy (útvary se zadávají ručně jako text/číslo útvaru).
- Schvalovací workflow s notifikacemi (fáze 2 — zatím jen pole Stav).
- Power BI reporty (mapa je HTML; Power BI je alternativa, ne požadavek).
- Copilot nad rejstříkem.

## 8. Kritéria přijetí

| # | Kritérium | Ověření |
|---|---|---|
| A1 | Data ze všech evidenčních karet lze do rejstříku nahrát bez ztráty | import `runs/normalize/*.csv`, počty řádků v listech = počty v CSV |
| A2 | Aktivita může být ve více dílčích procesech | testovací aktivita se dvěma vazbami se zobrazí v obou větvích mapy |
| A3 | Sekční správce pořídí novou aktivitu bez znalosti kódů | průchod appkou: vybere agendu→proces→dílčí proces, kód se přidělí sám |
| A4 | Mapa se po změně dat aktualizuje sama | změna v listu → spuštění publikačního flow → nová hodnota v HTML |
| A5 | Rejstřík lze exportovat do Excelu | export zobrazení, kontrola sloupců |
| A6 | Řešení jde nasadit na tenant MPSV ze skriptů | provisioning skript proběhne na čistém webu, žádné hardcoded URL |

## 9. Otevřené otázky na zadavatelku

> **Stav 19.08.2026:** zadavatelka není k dispozici. Všechny otázky níže mají
> **prozatímní rozhodnutí podle best practice**, aby práce neuvázla. Rozhodnutí
> jsou zvolena tak, aby se dala revidovat bez ztráty dat — žádné z nich nic
> nezahazuje. Až bude zadavatelka k dispozici, projít znovu.

1. **Konflikt vlastnictví (3 položky)** — proces „Strategie a koncepce MPSV" (01-01),
   proces „Řízení lidských zdrojů" (07-08) a dílčí proces „Personální správa"
   (07-08-001) mají v kartě dva vlastníky (11 a 33). Metodika předpokládá jednoho.
   → **ROZHODNUTO 19.08.2026 (uživatel): více vlastníků je přípustný stav.**
   `vlastnik` je textové pole, hodnoty oddělené `; `. Přestalo být nálezem.

2. **Dílčí proces navíc proti rejstříku** — „Podezření ze spáchání protiprávního
   jednání" je v kartě, ne v rejstříku.
   → **Prozatímně: ponechat obojí, provenienci nese sloupec `zdroj`**
   (`rejstrik` / `karta`). Zahodit údaj, který útvar reálně eviduje, by byla
   ztráta dat; rejstřík je navíc živý dokument, který se doplňuje. Zadavatelka
   pak jen rozhodne, jestli položku do rejstříku převzít, nebo z karty odebrat —
   podklad pro obě varianty je v datech.

3. **Dvě dvojice podobných aktivit** (podobnost 0,92 a 0,88) — sloučit, nebo
   ponechat odděleně?
   → **Prozatímně: ponechat odděleně.** Ověřeno v datech:
   `01-01-003-0001` vykonává útvar **111** („v působnosti personálního oddělení"),
   `01-01-003-0002` útvar **113** („v působnosti oddělení personálního rozvoje
   a metodik") — sloučením by se ztratilo, který útvar co dělá, a to je hlavní
   výstup celého mapování. Druhá dvojice (`07-08-006-0001` hodnocení zaměstnanců
   vs `07-08-008-0001` vzdělávání a rozvoj) má sice týž útvar, ale jiný předmět
   i jiný dílčí proces — shoda je jen ve formulaci.

4. **Rozsah zobrazení mapy** — všem zaměstnancům, nebo jen správcům a vlastníkům?
   → **Prozatímně: čtení všem zaměstnancům, zápis jen správcům.** Odpovídá
   zadání „trvale viditelná na SharePoint stránce" a je to konzervativní
   v tom směru, který jde snadno zúžit; opačné pořadí (nejdřív zavřít, pak
   otevírat) by znamenalo znovu řešit oprávnění.

5. **Cílový web na MPSV** — existuje, nebo se má založit nový?
   → **Neblokuje.** Žádný skript nemá URL natvrdo — provisioning i import si web
   odvodí z adresy stránky, na které běží. Rozhodne se až při nasazení.
