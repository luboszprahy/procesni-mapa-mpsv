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

Extrakce textu z podkladů (Windows, PowerShell — nutné UTF-8 na stdout):

```powershell
$env:PYTHONIOENCODING = "utf-8"
python src\dump_docx.py "input\Metodika_pro_praci_s_procesy_verze1.0.docx"
python src\dump_xlsx.py "input\VZOR_Evidenční karta _ S 3_varianta 17.7.2026.xlsx" 200
```

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
