# HANDOVER — stav k restartu konverzace (20.08.2026 13:48)

Tenhle soubor je vstupní bod pro novou session. Nejdřív si přečti `STATUS.md`
(chronologie a odůvodnění rozhodnutí), pak tohle (co se má udělat teď).
Postup a fáze drží `PLAN.md`, zadání `PRD.md`.

## 1. Zadané, ale NEUDĚLANÉ (priorita shora dolů)

1. **Grafika seznamu podle Správy notifikací.** Předloha:
   `input/snimky/vzor-notifikace-2.png` (jak to má vypadat) a
   `input/snimky/vzor-notifikace-1.png` (jak to vypadá teď u nás).
   Zdrojové vzory: `C:\projekty-Claude\powerApps-správaNotifikací\src\canvas_vzory\`
   (`gallery.json`, `templates_gallery.json`, `container.json`, `navbar.json`).
   Co z předlohy převzít:
   - **navbar** nahoře: tmavý pruh, vlevo název aplikace / sekce jako záložka
     s podtržením aktivní položky, vpravo identita uživatele,
   - **souhrnná karta** pod ním: vlevo nadpis, uprostřed pár čísel
     (celkem aktivit / zmapováno / nezmapováno), vpravo primární tlačítko,
   - **řádek hledání** a vpravo informační „chipy" (např. „47 ze 47 aktivit"),
   - **tabulková galerie**: hlavička sloupců s možností řadit (šipka u aktivně
     řazeného sloupce), řádky jako světlé karty s tenkým oddělením,
     akční ikony vpravo,
   - vzhled je plochý, hodně bílé, tenké linky, žádné výrazné bloky.
2. **Celý řádek první galerie musí být klikací** (dnes otevírá detail jen
   šipka vpravo). Řešení: `OnSelect` na podkladovém obdélníku i na labelech
   → `Set(varNova, false); Set(varAktivita, ThisItem); Navigate(scr_Detail, …)`,
   ne `Select(Parent)`.
3. **Zrušit informační panel „i"** na `scr_Seznam` i `scr_Detail`
   (`ico_Info*`, `rec_Napoveda*`, `lbl_Napoveda*`, `ico_ZavritNapovedu*`,
   proměnná `varNapovedaKod`). Text o stavbě kódu `AA-BB-CCC-DDDD` přesunout
   **do tooltipu tlačítka „+ Nová aktivita"** (a případně tlačítka Uložit).
4. **Místo ikony globusu tlačítko s popiskem „Zobrazit v HTML"** — styl
   druhotného tlačítka, `OnSelect: =Launch(varMapaUrl, {}, LaunchTarget.New)`.
5. **Dokončit `MapaPublishFlow`** (v základu je kostra: ruční trigger + jedna
   akce `Compose`) a přidat do appky tlačítko, které ho spustí:
   načíst 6 listů → složit JSON podle kontraktu v `deploy/flow_MapaPublish.md`
   → nahradit kotvy `__DATA_JSON__` a `__GEN__` v `mapa_template.html`
   → uložit `procesni_mapa.html` do Site Assets.
   Šablonu je předtím potřeba nahrát do Site Assets (konzolový skript).

## 2. Poznámka k solution od uživatele

Balík obsahuje **dvě SharePoint connection reference**:

- `ppf_sharedsharepointonline_12718` = **„SharePoint Pruvodnilist-12718"** —
  zbytek z jiného projektu, **uživatel ji chce příště pryč**,
- `ppf_sharedsharepointonline_bec33` = ta správná, kterou uživatel přidal.

Při dalším exportu ověřit, že zůstala jen ta druhá; do `check_solution.py`
se hodí kontrola, že v balíku není connection reference s cizím názvem.
Do appky se ve Studiu připojily i datové zdroje `Documents`
a `CustomGallerySample` — před předáním odpojit.

## 3. Kde co je

| věc | kde |
|---|---|
| základ pro build (nejnovější export ze Studia) | `input/procesnimapa_1_0_0_18.zip` |
| poslední vydaný balík | `deploy/procesnimapa_1_0_0_19.zip` |
| zdroje appky | `src/app_src/*.pa.yaml` (App + 3 obrazovky) |
| styl (16 proměnných) | `src/app_src/App.pa.yaml`, `App.OnStart` |
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
& $py src/build_app.py --solution "input/procesnimapa_1_0_0_18.zip" --verze 1.0.0.20
& $py src/build_flow.py --solution deploy/procesnimapa_1_0_0_20.zip
& $py src/check_flow.py --solution deploy/procesnimapa_1_0_0_20.zip
& $py src/check_solution.py --vstup "input/procesnimapa_1_0_0_18.zip" --vystup deploy/procesnimapa_1_0_0_20.zip
```

`build_flow.py` doplňuje **jen** flow `AktualizaceKratkehoNazvu`
(vybírá podle jména, v balíku jsou dvě). `MapaPublishFlow` zatím nikdo neplní.

## 5. Co je hotové a nemá se rozbít

- SharePoint: 6 listů založených a naplněných (7 / 46 / 250 / 46 / 46 / 7).
- Appka: 3 obrazovky, kaskáda agenda → proces → dílčí proces, přidělování
  kódů, vazby M:N, filtry z číselníku `Útvary`, řazení, tooltipy.
- Flow `AktualizaceKratkehoNazvu`: hotové, ověřené mini-interpretem
  (104 vzorků), zapisuje jen `nazev_kratky`.
- Brány: `check_app` (7 tříd kontrol), `check_flow` (19), `check_solution` (107),
  node testy provisioningu a importu. **Všechny kontroly jsou mutačně ověřené.**

## 6. Co se dnes stálo nejvíc času (ať se to neopakuje)

Podrobně v `power-Apps-skill/reference/pa-yaml-uskali.md`. Zkráceně:
**`pac canvas pack` nevaliduje nic** — hidden vlastnost, duplicitní klíč,
řetězec místo identifikátoru, neuzavřená uvozovka i překlep v `RGBA` projdou
až do Studia. Před každým vydáním pouštět `check_app.py`; když spadne import
nebo otevření, **nejdřív doplnit kontrolu**, teprve pak opravit výskyt.

Neznámý dopad má pořád **delegace nad 2 000 aktivitami** — test se odkládá
od začátku a je to jediný bod, kde se může ukázat, že seznam tiše ořezává.
