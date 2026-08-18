# STATUS — Procesní mapa MPSV

Aktualizováno: 2026-08-18

## Dohodnutá východiska

- Zadavatelka pracuje na **MPSV**, vývoj probíhá v **tenantu PPF** → řešení musí být
  přenositelné (listy zakládat skriptem, env variables, žádné hardcoded URL).
- Do PPF tenantu jdou **jen anonymizovaná data** (`runs/anonym/`).
- Pořizování dat = **Power Apps canvas app od začátku** (kaskádové číselníky
  agenda→proces→dílčí proces SharePoint formulář neumí).
- Vazba aktivita ↔ dílčí proces je **M:N přes vazební tabulku**.
- Prezentace: canvas app ve stylu MessageCenterDashboard + HTML se zapečenými daty
  (FloorPlan pattern).

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

## Nálezy k rozhodnutí (report `runs/normalize/report.md`)

1. **46 buněk karty** mělo přebytečné mezery / překlepy — normalizace je čistí automaticky.
2. **Konflikt vlastnictví**: proces „Strategie a koncepce MPSV" a „Řízení lidských zdrojů"
   a dílčí proces „Personální správa" mají v kartě dva vlastníky (11 a 33).
   Metodika předpokládá jednoho → nutné rozhodnutí zadavatelky.
3. **1 dílčí proces navíc** proti rejstříku: „Podezření ze spáchání protiprávního jednání".
4. **2 dvojice podobných aktivit** (podobnost 0,92 a 0,88) — kandidáti na sloučení
   nebo na vazbu M:N.

## Zbývá

- PRD.md a PLAN.md (čeká na zpětnou vazbu k prototypu).
- Návrh SharePoint listů + provisioning skript (PnP) — číselníky, aktivity, vazební tabulka.
- Canvas app pro pořizování (kaskádové číselníky, automatické kódy).
- Publikační flow: model → HTML do Site Assets.
- Generování textu OŘ z aktivit (fáze 2).

## Next step

Ukázat `viz/mapa_prototyp.html` zadavatelce, posbírat připomínky k obsahu i vzhledu,
teprve pak zmrazit datový model a psát PRD.
