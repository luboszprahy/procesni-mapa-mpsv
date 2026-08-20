# HANDOVER — stav k restartu konverzace (20.08.2026 14:15)

Tenhle soubor je vstupní bod pro novou session. Nejdřív si přečti `STATUS.md`
(chronologie a odůvodnění rozhodnutí), pak tohle (co se má udělat teď).
Postup a fáze drží `PLAN.md`, zadání `PRD.md`.

## 1. CO JE NA TOBĚ (uživateli) — v tomto pořadí

1. **Importovat `deploy/procesnimapa_1_0_0_20.zip`** jako upgrade a appku
   jednou otevřít ve Studiu (z YAML zabalená appka se validuje až tam).
2. **Nahrát `deploy/mapa_template.html` a `deploy/procesni_mapa.html`
   do Site Assets** a kliknutím ověřit, jestli tenant HTML **zobrazí, nebo
   stáhne**. To je jediná neověřená věc celého řešení — postup a co dělat
   v obou případech má `deploy/navod_publikace_mapy.md`.
3. **Zapnout a ručně spustit `MapaPublishFlow`** (import stav zapnutí nemění).
   Kontrolní body po běhu jsou v témže návodu; nejdůležitější: krok
   `Nacti_DilciProcesy` musí vrátit **250 položek, ne 100**.
4. **Připojit `MapaPublishFlow` k appce** ve Studiu (Power Automate → Add flow)
   a exportovat solution — teprve pak jde do appky dát tlačítko „Obnovit mapu".
   Vzorec tlačítka je připravený v `deploy/navod_publikace_mapy.md`.
5. **Úklid v prostředí (odloženo vědomě):** odpojit z appky datové zdroje
   `Documents` a `CustomGallerySample` a odebrat ze solution connection
   reference `ppf_sharedsharepointonline_12718` („SharePoint Pruvodnilist-12718",
   zbytek z jiného projektu). **Až po tom, co 1.0.0.20 běží** — obě flow na ní
   dnes visí, takže odebrání je nutné udělat pro obě naráz, a míchat to
   s velkou funkční změnou by znamenalo, že při selhání importu nepoznáš,
   co ho shodilo.

## 2. CO DĚLÁM JÁ (asistent) — hotovo v 1.0.0.20

**Grafika seznamu přestavěná podle vzoru Správy notifikací**
(`input/snimky/vzor-notifikace-2.png`):

- **navbar** 64 px: vlevo název aplikace, vedle záložka „Seznam aktivit"
  s bílým podtržením, vpravo jméno a e-mail přihlášeného,
- **souhrnná karta**: nadpis, tři čísla (zobrazeno / schváleno / pracovní)
  a vpravo dvě tlačítka — druhotné „Zobrazit v HTML" a primární „+ Nová aktivita",
- **řádek hledání a filtrů** s popisky, vpravo dva informační chipy
  (počet zobrazených aktivit, „Bez filtru — celý rejstřík" / „Filtrováno"),
- **tabulková galerie** s pěti sloupci (KÓD / AKTIVITA / VYKONÁVÁ / SEKCE /
  STAV); hlavička prvních tří je **klikací a řadí**, u aktivního sloupce je
  šipka směru. `drp_Razeni` tím zanikl.
- Vzhled je plochý: bílé řádky, oddělení linkou 1 px, žádné barevné pruhy
  ani chipy uvnitř řádku. Barva zůstala jen u stavu a u čísel v souhrnu.

**Ostatní zadané body:**

- **celý řádek je klikací** — `OnSelect` s `Navigate` má podklad i všech pět
  labelů a ikona (ne `Select(Parent)`, ten jen vybíral řádek),
- **info panel „i" zrušen** na obou obrazovkách i s proměnnou `varNapovedaKod`;
  text o stavbě kódu `AA-BB-CCC-DDDD` je v tooltipech „+ Nová aktivita"
  a „Uložit",
- **globus nahradilo tlačítko „Zobrazit v HTML"** (druhotný styl, `Launch`).

**`MapaPublishFlow` dokončené** — 14 akcí: šablona ze Site Assets, pět dotazů
do listů se zapnutým stránkováním, pět `Select` na datový kontrakt, `Model`,
zapečení do HTML a `Create file`. Generuje `src/build_mapa_flow.py`
(GUID listů i adresu webu čte z balíku, ne natvrdo), kontroluje
`src/check_mapa_flow.py`.

**HTML mapa vygenerovaná** — `deploy/procesni_mapa.html` (94 kB, 7 agend,
46 procesů, 250 dílčích procesů, 46 aktivit) z anonymizovaných dat, aby bylo
co otevřít dřív, než flow poprvé proběhne.

## 3. Kde co je

| věc | kde |
|---|---|
| základ pro build (nejnovější export ze Studia) | `input/procesnimapa_1_0_0_18.zip` |
| poslední vydaný balík | `deploy/procesnimapa_1_0_0_20.zip` |
| k nahrání do Site Assets | `deploy/mapa_template.html`, `deploy/procesni_mapa.html` |
| nasazovací návod | `deploy/navod_publikace_mapy.md` |
| datový kontrakt mapy + klikací fallback | `deploy/flow_MapaPublish.md` |
| zdroje appky | `src/app_src/*.pa.yaml` (App + 3 obrazovky) |
| styl (18 proměnných) | `src/app_src/App.pa.yaml`, `App.OnStart` |
| schéma listů (6 listů / 37 sloupců) | `src/schema.json` |
| data pro vývoj (anonymizovaná) | `runs/anonym/*.csv` |
| snímky obrazovek a předlohy | `input/snimky/` |
| starší solution zipy | `input/archiv/` |

**Základ pro `build_app.py` musí být vždy nejnovější export z prostředí** —
jinak by se z balíku ztratila flow nebo připojení listů.

## 4. Příkazy

```powershell
$env:PYTHONIOENCODING = "utf-8"
$py = ".venv/Scripts/python.exe"

& $py src/check_app.py                       # brána nad zdroji appky
& $py src/build_app.py --solution "input/procesnimapa_1_0_0_18.zip" --verze 1.0.0.21
& $py src/build_flow.py      --solution deploy/procesnimapa_1_0_0_21.zip
& $py src/build_mapa_flow.py --solution deploy/procesnimapa_1_0_0_21.zip
& $py src/check_flow.py      --solution deploy/procesnimapa_1_0_0_21.zip
& $py src/check_mapa_flow.py --solution deploy/procesnimapa_1_0_0_21.zip
& $py src/check_solution.py --vstup "input/procesnimapa_1_0_0_18.zip" --vystup deploy/procesnimapa_1_0_0_21.zip

# HTML mapa z dat
& $py src/build_mapa.py --model runs/anonym/model.json --out deploy/procesni_mapa.html
& $py -m http.server 8765 --bind 127.0.0.1   # náhled: http://127.0.0.1:8765/deploy/procesni_mapa.html
```

**Oba build skripty flow se pouštějí až po `build_app.py`** — ten balík
přepisuje od základu, takže by doplněné akce zahodil.

## 5. Co je hotové a nemá se rozbít

- SharePoint: 6 listů založených a naplněných (7 / 46 / 250 / 46 / 46 / 7).
- Appka: 3 obrazovky, kaskáda agenda → proces → dílčí proces, přidělování
  kódů, vazby M:N, filtry z číselníku `Útvary`, řazení klikem na hlavičku.
- Flow `AktualizaceKratkehoNazvu`: hotové, ověřené mini-interpretem (104 vzorků).
- Flow `MapaPublishFlow`: hotové, 126 kontrol, 12 mutací ověřených.
- Brány: `check_app` (7 tříd), `check_flow` (19), `check_mapa_flow` (126),
  `check_solution` (124), node testy provisioningu a importu.
  **Všechny kontroly jsou mutačně ověřené.**

## 6. Otevřená rizika

- **Zobrazí tenant HTML ze Site Assets?** Neověřeno. Když ne, publikační flow
  propadne a zobrazení se musí přesunout do canvas appky. Viz krok 2 výše.
- **Delegace nad 2 000 aktivitami.** Test se odkládá od začátku a je to
  jediný bod, kde se může ukázat, že seznam tiše ořezává. Čísla v souhrnné
  kartě jsou proto počítaná z galerie, ne z listu, a popisek říká „zobrazeno".
- **`pac canvas pack` nevaliduje nic** — hidden vlastnost, duplicitní klíč,
  řetězec místo identifikátoru, neuzavřená uvozovka i překlep v `RGBA` projdou
  až do Studia. Před každým vydáním pouštět `check_app.py`; když spadne import
  nebo otevření, **nejdřív doplnit kontrolu**, teprve pak opravit výskyt.
  Podrobně v `power-Apps-skill/reference/pa-yaml-uskali.md`.
