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
  v excelové tabulce vlastním sloupcem.
- `format` je `word` nebo `excel`. Cokoli jiného spadne do `word`.
- Chybějící `vlastnik` nebo `stav` (null) je v pořádku — vznikne prázdná buňka.

Odpověď: `{"adresa": "https://…/SiteAssets/procesni_mapa_20260825_143012.doc"}`.

## Formáty

| volba | soubor | proč tak |
|---|---|---|
| Word | `.doc` — HTML dokument | Word ho otevře a umí uložit jako `.docx`. Skutečné OOXML by znamenalo premium konektor (Encodian, Word Online) a ten v tomhle tenantu neprojde DLP. Vědomý ústupek. |
| Excel | `.xls` — HTML tabulka s excelovými styly | Kódování i typ buňky se dají určit napevno. |

### Proč Excel nedostává `.csv`

Do 1.0.0.58 to CSV bylo a v provozu selhalo **dvakrát naráz** (snímek
25.08.2026):

- **diakritika se rozsypala** — `Úroveň` přišlo jako `Ãšroveň`. Soubor měl na
  začátku BOM, jenže řádek `sep=;` přepne Excel na starý textový parser, který
  BOM ignoruje a čte podle národního nastavení;
- **kódy se změnily na data** — `01-01` skončilo jako `01.I`, `01` jako číslo
  `1`. Uvozovky kolem pole proti tomu nepomáhají, typ si Excel hádá z obsahu.

HTML tabulka obojí určuje napevno: kódování hlavičkou `charset=utf-8` (přesně
jako u Wordu, který funguje) a typ buňky stylem `mso-number-format:"\@"`, což
je vynucený text. Úroveň je jediný sloupec s číselným formátem, aby se dala
filtrovat.

**Cena:** Excel při otevření jednou upozorní, že přípona neodpovídá obsahu —
potvrdit Ano. Je to jediný způsob, jak z cloud flow bez placeného konektoru
dostat sešit se správným kódováním a typy; `.xlsx` je zip a ten Logic Apps
sestavit neumí.

## Akce (8)

```
Vstup       Compose   json(triggerBody()['text'])
Html_radky  Select    řádek tabulky pro .doc (escapuje & < >)
Xls_radky   Select    řádek excelové tabulky (buňky s vynuceným textem)
Jmeno       Compose   procesni_mapa_<yyyyMMdd_HHmmss>.doc | .xls
Dokument    Compose   if(format = excel, tabulka pro Excel, dokument pro Word)
Uloz        SharePoint CreateFile do /SiteAssets
Adresa      Compose   <web>/SiteAssets/<jmeno>
Odpoved     Response  { "adresa": … }
```

Obě podoby dokumentu se počítají vždy — jsou to jen řetězce a větvení přes
If/Scope by přidalo akce, které by brána musela obcházet; jedna z podob by
pak nikdy nebyla otestovaná.

Adresa se skládá z webu a názvu, ne z odpovědi konektoru: pole odpovědi
`CreateFile` nejsou v dokumentaci závazná a mlčky se mění.

## Registrace flow v appce (hotovo od 1.0.0.57)

Aby appka mohla zavolat `ExportFlow.Run()`, musí mít flow zaregistrované jako
**datový zdroj**. To jde udělat **jen ve Studiu** (Add data → ExportFlow),
protože `FlowNameId` přiděluje až prostředí při importu — lokálně se
dogenerovat nedá. V tomhle prostředí je to hotové
(`FlowNameId 4b36e7da-c006-4859-af44-e22c8a790738`) a zápis se přenáší
v každém dalším balíku.

**Při přenosu na tenant MPSV se to bude muset udělat znovu**, protože nové
prostředí přidělí vlastní `FlowNameId`. Pořadí: import → zapnout flow →
Studio → Add data → mikro-změna → Save → Publish.

Po **každém** importu je potřeba ve Studiu mikro-změna → Save → Publish,
jinak se publikovaná verze pro ostatní účty neaktualizuje.

## Ruční zkouška flow bez appky

V designeru **Test → Manually** a do vstupu vložit:

```json
{"nadpis":"zkouška","format":"excel","radky":[{"uroven":2,"kod":"01-01","nazev":"Test; s středníkem","vlastnik":"30","stav":""}]}
```

Běh musí skončit zeleně a v Site Assets vzniknout `procesni_mapa_*.xls`.
Excel ho otevře do pěti sloupců, kód zůstane `01-01` (ne datum) a diakritika
bude v pořádku.

## Meze

- `Response` v PowerAppV2 flow má strop běhu **120 s**. U dnešního rejstříku
  (7 agend, 46 procesů, 251 dílčích procesů, ~50 aktivit — tedy nejvýš ~350
  řádků) je to daleko. Nad ~2 000 řádky se nafoukne vstup flow a export je
  potřeba zúžit filtrem.
- Exporty se v Site Assets **hromadí** — každý běh je nový soubor s razítkem
  v názvu, aby si dva souběžné exporty nepřepsaly výsledek. Staré je potřeba
  občas smazat ručně.
