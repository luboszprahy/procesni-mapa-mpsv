# Procesní mapa MPSV — projektový CLAUDE.md

## Účel projektu

Digitální podpora projektu **„Úprava Organizačního řádu MPSV s využitím metod
procesního řízení“** (realizace do 06/2028). Cílem je nahradit současnou evidenci
v excelových evidenčních kartách **centrálním rejstříkem agend a procesů**
v prostředí Microsoft 365 (SharePoint Online + Power Platform) a nad ním
**automaticky generovanou procesní mapou**, která se aktualizuje spolu s daty.

Zadavatelka řešení pracuje se SharePoint seznamem (agenda → proces → dílčí proces
→ aktivita) a chce mapu, kterou nemusí ručně přegenerovávat a která je trvale
viditelná (webová část na SharePoint stránce).

## Doménový model (dle Metodiky v1.0)

Čtyřúrovňová hierarchie, jeden řádek evidence = jedna **aktivita**:

```
Agenda  →  Proces  →  Dílčí proces  →  Aktivita
  AA        BB          CCC             DDDD      identifikační kód AA-BB-CCC-DDDD
```

- **Agenda** — oblast činnosti daná zákonem/vnitřním předpisem; vlastník = sekce.
- **Proces** — tok činností s definovaným vstupem/výstupem; vlastník = odbor.
- **Dílčí proces** — vymezený úsek procesu; vlastník = odbor.
- **Aktivita** — nejnižší úroveň, odpovídá znění činností v organizačním řádu;
  vykonává oddělení. Aktivita může patřit do více dílčích procesů (M:N).
- Vlastník **není** součástí kódu — eviduje se samostatně kvůli organizačním změnám.

Role: Správce procesního rámce (celé MPSV), Sekční správce procesního rámce (sekce),
vlastníci agend/procesů/dílčích procesů, vykonávající útvary.

Pole evidenční karty / rejstříku: Agenda, Vlastník agendy, Proces, Vlastník procesu,
Dílčí proces, Vlastník dílčího procesu, Aktivita, Vykonává útvar, Spolupracuje,
Vnitřní předpis, Text pro OŘ, Datum aktualizace, Stav (pracovní/schváleno).

## Podklady (`input/`)

| Soubor | Obsah |
|---|---|
| `Metodika_pro_praci_s_procesy_verze1.0.docx` | závazná metodika — definice pojmů, hierarchie, kódování, pravidla evidence |
| `Navrh_SharePoint_reseni.docx` | zadání řešení: proč SharePoint (ne Dataverse), struktura seznamu, požadované funkce, budoucí rozvoj |
| `Analyza_vyuzit_PowerBI_PowerApps.docx` | rešerše variant vizualizace (Power BI strom rozkladu / Visio / Power Apps) |
| `VZOR_Evidenční karta _ S 3_varianta 17.7.2026.xlsx` | reálná evidenční karta sekce 3 (~45 aktivit) — vzor vstupních dat |
| `REJSTRIK_MAPA_A-P-DP_aktualizace 17.7.2026.xlsx` | centrální rejstřík / mapa agend–procesů–dílčích procesů, barevně odlišené stavy využití |
| `VZOR_OŘ - nově sekce 3_17.7.2026.docx` | cílový tvar textu organizačního řádu generovaného z aktivit |

`input/extracted/` = textové výtahy z těchto souborů (generované, viz níže) —
slouží k rychlému čtení obsahu bez rozbalování Office formátů.

## Struktura repozitáře

```
input/            zadání a podklady (Office soubory + extracted/ textové výtahy)
input/extracted/  generované .txt výtahy podkladů
src/              skripty a zdrojáky (pa.yaml, build skripty, extraktory)
deploy/           finální výstupy k nasazení (solution zipy, návody, HTML)
runs/             jednotlivé testovací běhy, každý ve vlastním podadresáři
viz/              grafické výstupy (HTML mapy, obrázky)
(root)            .md dokumenty, konfigurace
```

## Příkazy

Windows. Python **jen z venv** — `openpyxl` je nainstalovaný tam, ne v systémovém.
Skripty se spouštějí **z kořene projektu**, cesty k `input/`, `runs/`, `viz/`
jsou relativní. Cesty piš s lomítky dopředu, zpětná lomítka se v markdownu lámou.

```powershell
$env:PYTHONIOENCODING = "utf-8"
$py = ".venv/Scripts/python.exe"

# --- datová vrstva ---
& $py src/normalize.py        # podklady -> runs/normalize/ (*.csv, model.json, report.md)
                              #   kódy bere z kody.json a nikdy je nepřečísluje
& $py src/anonymize.py        # runs/normalize -> runs/anonym/ (data pro cizí tenant)
& $py src/build_mapa.py       # model -> viz/mapa_prototyp.html
& $py src/build_mapa.py --model runs/anonym/model.json --out viz/mapa_dev_anonym.html

# --- SharePoint vrstva (vše se generuje ze src/schema.json) ---
& $py src/check_schema.py     # validace schéma<->data + deploy/sharepoint_schema.md
& $py src/make_setup.py       # -> src/setup_sharepoint.js  (založení listů a sloupců)
& $py src/make_import.py      # -> src/import_data.js       (import dat, jen anonymizovaná)

# --- testy (Node) ---
node src/check_setup.js       # 32 kontrol provisioningu proti falešnému SharePointu
node src/check_import.js      # 26 kontrol importu

# --- pomocné: výpis obsahu podkladů ---
& $py src/dump_docx.py "input/Metodika_pro_praci_s_procesy_verze1.0.docx"
& $py src/dump_xlsx.py "input/VZOR_Evidenční karta _ S 3_varianta 17.7.2026.xlsx" 200
```

`setup_sharepoint.js` a `import_data.js` se **nespouštějí z konzole Windows** —
vkládají se do konzole prohlížeče (F12) na stránce cílového SharePoint webu.
Oba jsou idempotentní a web si odvodí z adresy stránky.

Prohlédnutí HTML v prohlížeči: `file://` bývá blokované, spusť
`& $py -m http.server 8765 --bind 127.0.0.1` a otevři
`http://127.0.0.1:8765/viz/mapa_prototyp.html`.

## Klíčové soubory

| Soubor | Role |
|---|---|
| `src/schema.json` | **jediný zdroj pravdy** o struktuře SharePoint listů; čte ho validátor i oba generátory |
| `kody.json` | zmrazený rejstřík identifikačních kódů — jednou přidělený kód se nemění |
| `PRD.md` / `PLAN.md` / `STATUS.md` | zadání / postup / stav; `STATUS.md` má nahoře „CO JE NA TOBĚ" a „CO DĚLÁM JÁ" |
| `AUDIT.md` | nálezy nezávislého auditu a jejich vyřízení |
| `deploy/` | výstupy k nasazení: schéma listů, návrh appky, návod na publikační flow |

## Datový model (implementovaný)

| Tabulka | Klíč | Obsah |
|---|---|---|
| `agendy` | `AA` | 7 agend z rejstříku |
| `procesy` | `AA-BB` | 46 procesů, vazba na agendu |
| `dilci_procesy` | `AA-BB-CCC` | 250 dílčích procesů, stav využitý/nevyužitý z barvy v rejstříku |
| `aktivity` | `AA-BB-CCC-DDDD` | aktivity z evidenčních karet, vykonává útvar, spolupracuje, předpis |
| `aktivita_dilciproces` | — | **vazební tabulka M:N** (aktivita může patřit do více dílčích procesů) |

Číselník agend/procesů/dílčích procesů pochází z **rejstříku**, aktivity z **evidenčních
karet**. Karta sekce 3 se s rejstříkem shodla na 45 ze 46 dílčích procesů — parsování
obou zdrojů se tím navzájem ověřuje.

Skripty se spouštějí **z kořene projektu**, cesty k `input/`, `runs/`, `viz/`
jsou relativní. Závislosti: Python 3.14, `openpyxl` (docx se parsuje přes
`zipfile` + `ElementTree`, `python-docx` není nainstalováno).

## Konvence

- **Cílová platforma:** SharePoint Online + Power Apps / Power Automate / Power BI.
  Bez dodatečných licencí, bez Dataverse — s tím, že migrace do Dataverse musí
  zůstat možná bez ztráty dat (viz `Navrh_SharePoint_reseni.docx`).
- **Interní názvy sloupců SharePoint listů zakládat bez diakritiky** (přejmenování
  zobrazovaného názvu interní název nemění; REST `$select` pracuje s interními).
- URL webů a listů nikdy nehardcodovat — environment variables v solution.
- Žádné externí CDN ve výstupech; vše self-contained.
- Skill `power-Apps-skill` popisuje prostředí **PPF Banky** — technické vzory
  (formát solution, .msapp/pa.yaml, úskalí importu flow, CSP v Site Assets) platí
  obecně, ale **publisher `ppf`, prefix `ppf_` a tenant ppfbanka.sharepoint.com
  pro tento projekt neplatí** — MPSV má vlastní tenant a naming.
- Komunikace a dokumentace česky.
