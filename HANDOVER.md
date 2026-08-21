# HANDOVER — přechod na jiný stroj (21.08.2026 12:45)

Vstupní bod pro novou session. Pořadí čtení: **tenhle soubor** (co se má dělat
teď) → `STATUS.md` (chronologie a odůvodnění rozhodnutí) → `PLAN.md` (fáze).
Zadání drží `PRD.md`.

> **Stav:** appka i publikační flow **běží v provozu**. Aktuální balík
> k importu je **`deploy/procesnimapa_1_0_0_34.zip`** (strom na dashboardu,
> klikací řádky, filtr stavu, „Zobrazit vše" v seznamu) — hotový a ověřený
> offline branami, ale **ještě nenaimportovaný**. Poslední ověřeně běžící
> verze v prostředí je **1.0.0.28** (strom na dashboardu, snímek 14:35).
> Nahrazené balíky 27–33 jsou z `deploy/` smazané.
>
> Pracovní strom je čistý a vše je pushnuté. `runs/app_build` (179 MB
> rozbalený `pac`) i `runs/mapa_beh` smazané, náhledový http server zastavený,
> projekt z 259 MB na ~81 MB (z toho 59 MB `.git`, 18 MB `.venv`).

## Rozjezd na novém stroji

```powershell
git pull
# venv se nepřenáší — pokud v projektu není, založit a doinstalovat:
python -m venv .venv
.venv\Scripts\python.exe -m pip install openpyxl pyyaml
```

`pac` CLI se při prvním buildu appky rozbalí samo z rozšíření Power Platform
Tools ve VS Code (pár sekund navíc, nic se nenastavuje). Node je potřeba jen
pro `check_setup.js` / `check_import.js` a pro syntaktickou část brány mapy.
Headless test mapy hledá Edge nebo Chrome ve standardních cestách.

## 1. CO JE NA TOBĚ (uživateli)

1. **Naimportovat `deploy/procesnimapa_1_0_0_34.zip`** jako upgrade a appku
   jednou otevřít ve Studiu (z YAML zabalená appka se validuje až tam).
   Na co se dívat na obrazovce **Přehled**:
   - strom se ve výchozím stavu ukáže s rozbalenými agendami (úroveň 2),
   - tlačítka **„jen agendy / + procesy / + dílčí procesy / + aktivity"**
     rozbalí celou úroveň naráz,
   - **klik kamkoli do řádku** rozbalí větev, u aktivity otevře detail —
     tohle byla hlášená vada, klikat musí jít i na text, ne jen mezi popisky,
   - najetí myší řádek **podbarví** (modrý nádech), řádek se neposouvá,
   - chipy **vše / schváleno / pracovní** zúží strom na aktivity daného stavu
     a na větve, které aspoň jednu takovou obsahují; číslo vpravo se přepne
     na počet takových aktivit a hlavička sloupce to říká,
   - hlavičky **VLASTNÍK / VYKONÁVÁ** a **POLOŽEK UVNITŘ** mají tooltip
     s vysvětlením po úrovních; tooltip řádku navíc rozepíše kódy útvarů
     na „kód · název" z číselníku, i když jich je víc („72; 71"),
   - názvy nesmí podlézat sloupec „vykonává" (v 1.0.0.26 to dělaly, opraveno).
   - **ikona tužky** v řádku otevře detail; u aktivity rovnou, u vyšších
     úrovní je tlumená a řekne, že vlastní obrazovka se teprve chystá.
     Klik do **řádku** detail neotevírá, jen rozbaluje — detail je jedině
     přes tužku,
   Na obrazovce **Seznam aktivit**: tlačítko **„Zobrazit vše"** vedle přepínače
   kódu vynuluje všechny čtyři filtry a bez zapnutého filtru je neaktivní.
   V tmavé liště **všech** obrazovek jsou vpravo u jména uživatele **tři
   tlačítka A**. Volba platí napříč appkou (`varFs`), výchozí je **střední**
   stupeň. Na největším stupni zkontrolovat, že se kódy neořezávají a nejdelší
   názvy zůstávají čitelné.
   Na **detailu aktivity**: šipka zpět je celý čtvereček, při najetí zesvětlá,
   a vrací se **tam, odkud se přišlo** — z přehledu na přehled, ze seznamu do
   seznamu. Ověřit obě cesty, včetně návratu po uložení.
2. **Nahrát do Site Assets OBĚ HTML z `deploy/`** — `mapa_template.html`
   (z ní flow skládá stránku) i `procesni_mapa.html` (hotová mapa). Do
   21.08. se kopie dělala ručně a rozešla se se zdrojem, takže publikovaná
   mapa neměla nové ovládací prvky. Teď je generuje `build_mapa.py`.
3. **Spustit „Obnovit mapu"** v appce a v mapě zkontrolovat: přepínač stupně
   rozbalení, zatržítko „Zobrazit kód", čtyři velikosti písma (tlačítka A),
   nápovědu při najetí na řádek.
4. **Zapnout nové flow `MapaPublishScheduled`** (Power Automate > Solutions >
   procesní mapa). Import stav zapnutí nemění, takže nové flow může přijít
   vypnuté a denní publikace by pak tiše neběžela. Ověřit v jeho detailu, že
   trigger je Recurrence **denně v 7:00, Central Europe Standard Time**.
5. **Save & Publish** ve Studiu, jinak uživatelé vidí starou verzi.

## 1b. VYŘEŠENO: po importu je nutná mikro-změna, jinak Save neproběhne

**Ověřeno 21.08.2026 v provozu.** Po importu solution vidí ostatní účty dál
starou verzi, i když je ve Versions nejnovější verze **Live** a při spuštění
naskočí žlutý pruh *„A new version of this app is coming. We'll let you know
when it's available."*

Příčina: **publikovaný dokument vzniká při Save + Publish ze Studia, ne
importem solution.** Po importu ale Studio appku nepovažuje za rozpracovanou,
takže **není co uložit** — Publish pak zveřejní pořád ten starý publikovaný
dokument. Žlutý pruh přitom tvrdí, že nová verze existuje, což svádí hledat
chybu v cache nebo v odkazu.

**Postup po KAŽDÉM importu (dát do předávacího návodu):**
1. Otevřít appku ve Studiu.
2. Udělat **umělou mikro-změnu** — posunout libovolný prvek o pixel a vrátit
   ho zpět. Tím se appka stane rozpracovanou a Save se odemkne.
3. **Save**, počkat na dokončení.
4. **Publish**.
5. U ostatních účtů zavřít běžící session appky (žlutý pruh znamená „až při
   příštím spuštění").

Vedlejší nález, opravený při hledání: **`AppVersion` v `customizations.xml`**
zůstávala z původního exportu, takže se appka netvářila jako změněná. Build ji
teď přepisuje aktuálním UTC razítkem (`dokonci()` v `build_app.py`, bez nálezu
tagu skončí chybou) — od balíku **1.0.0.28**. Samo o sobě to problém
neodstranilo, ale správně to být má.

Vyloučeno: cache prohlížeče (stejné chování v jiném prohlížeči), špatný odkaz,
chybějící Live verze.

## 2. CO DĚLÁM JÁ (další krok)

Rozpracované: **F6 skupina D — zadávací obrazovky pro agendu, proces
a dílčí proces**
(`PLAN.md`, sekce F6/D). Dnes jde založit jen aktivita; nově má průvodce vést
uživatele i na vyšších úrovních a u zanořené úrovně vynutit údaje potřebné pro
vazbu (proces bez agendy nevznikne). Kódy přiděluje stejný mechanismus jako
u aktivit, `kody.json` se nesmí přečíslovat.

Otevřené riziko k rozmyšlení: kolize kódů při souběžném zakládání dvěma
uživateli — posoudit, zda stačí kontrola před zápisem, nebo je potřeba
pojistné flow.

## 3. Co je hotové (21.08.2026)

| oblast | stav |
|---|---|
| F1 SharePoint rejstřík | hotovo, provisioning i import dat |
| F2 canvas app | **ověřeno v provozu** (1.0.0.25) |
| F3 publikační flow + HTML mapa | **ověřeno v provozu** — mapa se v tenantu zobrazí, flow vrací 250 dílčích procesů |
| F3b denní publikace mapy | hotovo, čeká na import — druhé flow `MapaPublishScheduled`, Recurrence 7:00 |
| F6/A mapa: rozbalení, kód, písmo, nápovědy, barvy vrstev | hotovo |
| F6/B appka: šipka pryč, přepínač kódu, zařazení s posuvníkem | hotovo (1.0.0.26) |
| F6/C dashboard jako úvodní obrazovka | hotovo, čeká na import (1.0.0.34) |
| F6 připomínky z provozu: klikací řádky, hlavičky sloupců, filtr stavu, „Zobrazit vše" | hotovo, čeká na import (1.0.0.34) |
| F6/D zadávací obrazovky | **zbývá** |
| F4 přenos na MPSV | **blokováno** — uživatel nemá přístup k tenantu MPSV |
| F5 generování textu OŘ | fáze 2 (po 06/2028) |

## 4. Odložené a otevřené věci

- **Úklid connection reference `ppf_sharedsharepointonline_12718`**
  („SharePoint Pruvodnilist-12718" — cizí, z jiného projektu). Visí na ní obě
  flow, takže výměna za `ppf_sharedsharepointonline_bec33` znamená při importu
  přemapování připojení. Odloženo dvakrát, aby se při selhání importu dalo
  poznat, co ho shodilo. Půjde samostatně, bez jiných změn.
- **Brána `/audit`** (`powerplatform-auditor`) před transportem na MPSV —
  krok 11 v `PLAN.md`. Zatím neproběhla, protože transport je blokovaný.
- **`deploy/navod_sprava.md`** (krok 13) — rozhodnuto 21.08.2026 psát ho až
  podle finální podoby appky, tedy po F6/D.
- **Adresa mapy `varMapaUrl`** je v `App.pa.yaml` natvrdo (canvas app umí číst
  jen datasetové env proměnné, textové ne). Při přenosu na MPSV se mění tam —
  je to jediné místo a `check_solution.py` na to upozorňuje varováním.
- **Delegace nad 2 000 aktivitami**: fulltext v seznamu a `colAkt` na přehledu
  pracují s prvním oknem dat. Dnes 49 aktivit, takže úplné; popisky to říkají.

## 5. Příkazy

```powershell
$env:PYTHONIOENCODING = "utf-8"
$py = ".venv/Scripts/python.exe"

# --- data a mapa ---
& $py src/normalize.py            # podklady -> runs/normalize/
& $py src/build_mapa.py           # šablona -> viz/mapa_prototyp.html + deploy kopie
& $py src/check_mapa_html.py      # 31 statických kontrol šablony a výstupu
& $py src/check_mapa_beh.py       # 18 kontrol v headless Edge/Chrome

# --- canvas app ---
& $py src/check_app.py            # zdroje appky: YAML, sloupce, delegace, překryvy
& $py src/build_app.py --solution "input/procesnimapa_1_0_0_24.zip" --verze 1.0.0.34
& $py src/check_solution.py --vstup "input/procesnimapa_1_0_0_24.zip" `
                            --vystup "deploy/procesnimapa_1_0_0_34.zip"

# --- flows ---
# dvojče s denním během; idempotentní, píše zpátky do vstupní solution
& $py src/add_mapa_schedule.py --solution "input/procesnimapa_1_0_0_24.zip" --hodina 7
& $py src/check_mapa_flow.py --solution "deploy/procesnimapa_1_0_0_34.zip"
& $py src/check_flow.py      --solution "deploy/procesnimapa_1_0_0_34.zip"

# --- náhled mapy v prohlížeči (file:// bývá blokované) ---
& $py -m http.server 8765 --bind 127.0.0.1
# http://127.0.0.1:8765/viz/mapa_prototyp.html
```

**Vstupní solution pro build je `input/procesnimapa_1_0_0_24.zip`** — je to
poslední export ze Studia a jako jediný nese `MapaPublishFlow` mezi datovými
zdroji appky (Add flow). Stavět z něj, dokud uživatel nedodá novější export.

## 6. Dělba práce u canvas appky

Zavedený postup, ne výjimka: **uživatel** založí/upraví appku ve Studiu
(zejména připojení datových zdrojů a flow) a pošle **export unmanaged
solution**; **asistent** vymění `Src/*.pa.yaml`, přebalí přes `pac` a vrátí zip
k importu jako upgrade. `.msapp` nejde postavit od nuly.

Z toho plyne: cokoli, co vzniká **jen ve Studiu** (connection reference,
registrace flow jako datového zdroje), musí udělat uživatel — a pak dodat nový
export, jinak ho další build přepíše.

## 7. Brány (všechny mutačně ověřené)

| brána | rozsah | co hlídá |
|---|---|---|
| `check_app.py` | 163 prvků, 1584 vzorců | YAML bez duplicit, sloupce proti schématu **i proti vlastním kolekcím**, delegace podle argumentů volání, překryvy, mazání v galerii, adresa mapy |
| `check_solution.py` | 189 kontrol | publisher, verze, GUID listů, flow nezmizelo, `.Run()` má datový zdroj, **úvodní obrazovka**, žádné externí URL |
| `check_mapa_html.py` | 31 kontrol | id v JS vs. HTML, syntaxe skriptu šablony i výstupu, žádná velikost v px mimo přepínač, **shoda deploy kopií se zdrojem** |
| `check_mapa_beh.py` | 18 kontrol | proklik ovládacích prvků mapy v headless prohlížeči |
| `check_mapa_flow.py` | 129 kontrol | kontrakt publikačního flow, pagination, zapékání kotev |
| `check_flow.py` | 19 kontrol | flow nad `nazev_kratky` počítá totéž co `zkratit()` |
| `check_setup.js` / `check_import.js` | 32 + 26 | provisioning a import proti falešnému SharePointu |

Když brána spadne na něčem, co je vědomý ústupek, patří to do jejího seznamu
výjimek s odůvodněním — ne do obcházení kontroly.
