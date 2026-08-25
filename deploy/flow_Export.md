# Flow `ExportFlow` — export přehledu do Wordu a Excelu

Vyrábí ho `src/build_export_flow.py`, hlídá `src/check_export_flow.py`.
Poprvé v balíku **1.0.0.56**.

## K čemu je

Appka pošle **momentální zobrazení** stromu z Přehledu — tedy to, co je zrovna
vidět po filtru stavu, hledání, chipu osiřelých a rozbalení úrovní. Flow z toho
složí dokument, uloží ho do knihovny **Site Assets** cílového webu a vrátí
adresu; appka na ni zavolá `Download()`.

## Datový kontrakt

Trigger `PowerAppV2` má **jeden textový vstup** (`zobrazeni`) s tímto JSON:

```json
{
  "nadpis": "vše · bez hledání",
  "format": "word",
  "radky": [
    {"uroven": 1, "kod": "01", "nazev": "Řízení a správa", "vlastnik": "30", "stav": ""},
    {"uroven": 4, "kod": "01-01-001-0001", "nazev": "Vede evidenci",
     "vlastnik": "311", "stav": "schváleno"}
  ]
}
```

- `radky` je **plochý, už seřazený a odfiltrovaný** seznam. Flow nic nestromuje —
  Logic Apps neumí rekurzi ani vnořený Foreach, takže strom staví appka a flow
  z řádků dělá tabulku.
- `uroven` je 1–4 (agenda / proces / dílčí proces / aktivita). Ve Wordu se
  projeví odsazením buňky o 18 bodů na stupeň a tučností první úrovně,
  v CSV vlastním sloupcem.
- `format` je `word` nebo `excel`. Cokoli jiného spadne do `word`.
- Chybějící `vlastnik` nebo `stav` (null) je v pořádku — vznikne prázdná buňka.

Odpověď: `{"adresa": "https://…/SiteAssets/procesni_mapa_20260825_143012.doc"}`.

## Formáty

| volba | soubor | proč tak |
|---|---|---|
| Word | `.doc` — HTML dokument | Word ho otevře a umí uložit jako `.docx`. Skutečné OOXML by znamenalo premium konektor (Encodian, Word Online) a ten v tomhle tenantu neprojde DLP. Vědomý ústupek. |
| Excel | `.csv` — UTF-8 s BOM, `sep=;` | Excel takový soubor otevře rovnou do sloupců a **bez varování**. `.xls` s HTML tabulkou by nesl formátování, ale Excel u něj hlásí nesoulad přípony a obsahu, což u běžného uživatele vypadá jako poškozený soubor. |

Řádek `sep=;` na začátku CSV říká Excelu oddělovač bez ohledu na národní
nastavení stroje — bez něj by se soubor na anglických Windows otevřel
v jednom sloupci. Pole jsou v uvozovkách, takže středník ani uvozovka
uvnitř názvu nerozhodí sloupce.

## Akce (8)

```
Vstup       Compose   json(triggerBody()['text'])
Html_radky  Select    řádek tabulky pro .doc (escapuje & < >)
Csv_radky   Select    řádek CSV (pole v uvozovkách, vnitřní " se zdvojuje)
Jmeno       Compose   procesni_mapa_<yyyyMMdd_HHmmss>.doc | .csv
Dokument    Compose   if(format = excel, CSV, HTML)
Uloz        SharePoint CreateFile do /SiteAssets
Adresa      Compose   <web>/SiteAssets/<jmeno>
Odpoved     Response  { "adresa": … }
```

Obě podoby dokumentu se počítají vždy — jsou to jen řetězce a větvení přes
If/Scope by přidalo akce, které by brána musela obcházet; jedna z podob by
pak nikdy nebyla otestovaná.

Adresa se skládá z webu a názvu, ne z odpovědi konektoru: pole odpovědi
`CreateFile` nejsou v dokumentaci závazná a mlčky se mění.

## Co udělat po importu balíku 1.0.0.56

1. **Import** solution jako upgrade (Power Apps → Solutions → Import).
2. **Zapnout flow `ExportFlow`** — import stav zapnutí nemění, takže nové
   flow zůstane vypnuté a appka by hlásila `WorkflowTriggerIsNotEnabled`.
3. Otevřít appku **v Power Apps Studiu**.
4. **Add data → ExportFlow** (v seznamu Power Automate). Tímhle krokem se flow
   zaregistruje jako datový zdroj appky; **lokálně to udělat nejde**, protože
   `FlowNameId` přiděluje až prostředí při importu.
5. **Mikro-změna** (posunout prvek o pixel a vrátit) → **Save** → **Publish**.
   Bez ní se publikovaná verze pro ostatní účty neaktualizuje.
6. **Export solution** (unmanaged) a poslat zpět — do appky se pak doplní
   tlačítko **Export** s volbami Word / Excel. Do té doby se `.Run()` nemá
   na co navázat, takže tlačítko v 1.0.0.56 ještě není; v pruhu nad stromem
   je na něj vedle „HTML mapa" nachystané místo.

## Ruční zkouška flow bez appky

V designeru **Test → Manually** a do vstupu vložit:

```json
{"nadpis":"zkouška","format":"excel","radky":[{"uroven":1,"kod":"01","nazev":"Test; s středníkem","vlastnik":"30","stav":""}]}
```

Běh musí skončit zeleně a v Site Assets vzniknout `procesni_mapa_*.csv`,
který Excel otevře do pěti sloupců.

## Meze

- `Response` v PowerAppV2 flow má strop běhu **120 s**. U dnešního rejstříku
  (7 agend, 46 procesů, 251 dílčích procesů, ~50 aktivit — tedy nejvýš ~350
  řádků) je to daleko. Nad ~2 000 řádky se nafoukne vstup flow a export je
  potřeba zúžit filtrem.
- Exporty se v Site Assets **hromadí** — každý běh je nový soubor s razítkem
  v názvu, aby si dva souběžné exporty nepřepsaly výsledek. Staré je potřeba
  občas smazat ručně.
