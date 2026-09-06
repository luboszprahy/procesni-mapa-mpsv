# Flow `AktualizaceKratkehoNazvu` — pojistka nad sloupcem `nazev_kratky`

Hlídá, aby `nazev_kratky` v listu `Aktivity` vždy odpovídal sloupci `nazev`.
Řeší zápisy, které neprošly pořizovací appkou — ruční editaci přímo v listu,
hromadný import z Excelu, opravu přes datové zobrazení.

**Stav: flow je hotové a je součástí `deploy/procesnimapa_1_0_0_98.zip`.**
Kostru (trigger + jedna akce Compose) vyrobil uživatel v designeru, zbytek
doplnil skript `src/build_flow.py` do exportovaného balíku. Tenhle dokument
proto popisuje, **co v tom flow je a proč** — ne postup na naklikání.
Pro ruční stavbu na tenantu MPSV slouží tytéž kroky, jen se naklikají.

## Proč to nemůže dělat počítaný sloupec

Dvě nezávislé překážky, obě ověřené:

- vzorec počítaného sloupce **neumí číst sloupec typu „více řádků textu"**,
  a `nazev` jím být musí (naměřeno 220 znaků, hranice Text je 255),
- počítaný sloupec **nejde indexovat**, takže by nad 5 000 položkami neuneslo
  řazení výchozího zobrazení, které na `nazev_kratky` stojí.

## Kanonické zkrácení (co přesně se počítá)

Závazná je funkce `zkratit()` v `src/check_schema.py`; touž používá import:

1. srovnat bílé znaky — víc mezer za sebou na jednu, konce oříznout,
2. je-li výsledek **150 znaků nebo kratší**, je hotovo a **nic se nemění**
   (tečka na konci krátkého názvu tedy zůstane),
3. jinak useknout na **149** znaků,
4. najít v uříznutém textu **poslední mezeru**; leží-li za 75. znakem, seknout
   tam (aby se neřezalo uprostřed slova),
5. odmazat z konce znaky `,`, `;`, `.` a mezery,
6. připojit výpustku `…` (jeden znak U+2026, ne tři tečky).

## Akce ve flow

Trigger: **`When an item is created or modified`** nad listem `Aktivity`
z proměnné `mpsv_listAktivity`, pak jedenáct akcí.

| akce | výraz |
|---|---|
| `Nacti_aktivitu` | `Get item` — `id` = `@triggerBody()?['ID']`, list z `mpsv_listAktivity` |
| `Cesta_webu` | `@concat('/', join(skip(split(parameters('Procesni mapa - web (mpsv_procesnimapaSite)'), '/'), 3), '/'))` |
| `Nazev_syrovy` | `@coalesce(body('Nacti_aktivitu')?['nazev'], '')` |
| `Bez_bilych_znaku` | `@trim(replace(replace(replace(replace(replace(replace(outputs('Nazev_syrovy'), decodeUriComponent('%0D'), ' '), decodeUriComponent('%0A'), ' '), decodeUriComponent('%09'), ' '), '  ', ' '), '  ', ' '), '  ', ' '))` |
| `Rez` | `@substring(outputs('Bez_bilych_znaku'), 0, min(149, length(outputs('Bez_bilych_znaku'))))` |
| `Rez_na_slovo` | `@if(greater(lastIndexOf(outputs('Rez'), ' '), 75), substring(outputs('Rez'), 0, max(0, lastIndexOf(outputs('Rez'), ' '))), outputs('Rez'))` |
| `Orez_1` … `Orez_3` | `@if(contains(' ,;.', substring(X, max(0, sub(length(X), 1)), min(1, length(X)))), substring(X, 0, max(0, sub(length(X), 1))), X)`, kde `X` = výstup předchozí akce |
| `Cil` | `@if(lessOrEquals(length(outputs('Bez_bilych_znaku')), 150), outputs('Bez_bilych_znaku'), concat(outputs('Orez_3'), decodeUriComponent('%E2%80%A6')))` |
| `Lisi_se` (If) | `not(equals(coalesce(body('Nacti_aktivitu')?['nazev_kratky'], ''), outputs('Cil')))` |
| `Zapsat_kratky_nazev` (v *If yes*) | `Send an HTTP request to SharePoint` — POST na `_api/web/GetList('<Cesta_webu>/Lists/Aktivity')/items(<ID>)`, hlavičky `X-HTTP-Method: MERGE`, `IF-MATCH: *`, `Accept`/`Content-Type` `application/json;odata=nometadata`, tělo `{"nazev_kratky": "@outputs('Cil')"}` |

### Proč všude `min` a `max`

**`if()` v Logic Apps vyhodnocuje obě větve**, ne jen tu platnou. Kdyby
`substring` dostal ve „falešné" větvi zápornou délku nebo šel za konec
řetězce, akce spadne — i když se ta větev nepoužije. `min`/`max` proto drží
každý podvýraz platný pro **libovolný** vstup, včetně prázdného názvu.
Ověřeno mutací: bez `min` v akci `Rez` spadne výpočet na 87 vzorcích ze 104.

Tři průchody `'  '` → `' '` složí až osm mezer za sebou na jednu. Delší shluk
v datech není a nic nerozbije — jen by zůstal.

### Proč se zapisuje přes REST, a ne akcí `Update item`

`PatchItem` (`Update item`) posílá tělo rozložené na klíče `item/<sloupec>`
a schéma si k tomu stahuje z **konkrétního** listu. S `table` z proměnné
prostředí se schéma nerozbalí, klíče přestanou platit a flow **nejde zapnout**
(*„The API operation 'PatchItem' is missing required property 'item'"*,
MPSV 28.08.2026). List proto musel být GUID natvrdo a balík platil jen pro
jeden tenant — třikrát kvůli tomu odešel do MPSV balík s GUIDem PPF DEV,
naposledy 1.0.0.96, kde zapnutí spadlo na `GetTable … List not found`.

Od 1.0.0.98 zapisuje `Send an HTTP request to SharePoint` (je součástí
standardního SharePoint konektoru, ne premium HTTP). V REST adrese je list
obyčejný text, takže snese proměnnou; skládá se z **interního** názvu listu,
který je na všech tenantech stejný, kdežto GUID ne. `X-HTTP-Method: MERGE`
mění jen uvedený sloupec — povinná pole listu se v těle posílat nemusí a zápis
tím nemá čím přepsat novější editaci.

`Nacti_aktivitu` zůstává: trigger dává snímek starý až o minutu, takže
porovnávat s uloženou hodnotou se musí čerstvý stav řádku.

### Proč to necyklí

`Update item` spustí trigger znovu, ale při druhém průchodu se `nazev_kratky`
už rovná `Cil`, podmínka je nepravdivá a nezapisuje se. Cyklus by vznikl jen
tehdy, kdyby výpočet nebyl stabilní — proto se počítá **vždy z `nazev`**,
nikdy z `nazev_kratky`. Stabilitu ověřuje test (druhý průchod nad vlastním
výstupem musí dát tutéž hodnotu).

Cena je **jeden běh navíc po každé skutečné změně**. U hromadného importu se
flow spustí na každý řádek, ale import plní `nazev_kratky` sám, takže všechny
ty běhy skončí větví If no.

## Ověření

```powershell
& .venv/Scripts/python.exe src/check_flow.py --solution deploy/procesnimapa_1_0_0_10.zip
```

Skript nečte tenhle dokument ani kopii logiky — **vytáhne výrazy z balíku,
vyhodnotí je** mini-interpretem (hladově, jako Logic Apps) nad 104 vzorky
(reálná i anonymizovaná data + 12 hraničních) a porovná s `zkratit()`.
Kontroluje i strukturu: trigger a čtení berou list z proměnné, v definici
není žádný GUID, zápis je REST POST s `MERGE` a `IF-MATCH`, tělo nese právě
`nazev_kratky`, řetěz `runAfter` drží a podmínka porovnává uloženou hodnotu
s vypočtenou. **REST adresu přitom vyhodnotí**, ne jen porovná textem — chytí
tím i špatně zdvojený apostrof.

Mutačně ověřeno dvěma testy: `src/mutace_kratky_nazev.py` (14 mutací —
chybějící `MERGE` nebo `IF-MATCH`, GUID zpátky v adrese či v triggeru, adresa
bez `/items(ID)`, návrat k `PatchItem`, zapsaný `nazev` místo `nazev_kratky`,
metoda GET, čtení z triggeru, zápis bez porovnání) a mutacemi nad výrazy
zkracování (vypuštěné `min`, posunutá hranice slova, podmínka bez `not`,
rozbitý `runAfter`).

### Ruční zkouška po importu

1. **Krátký název beze změny** — u aktivity s názvem do 150 znaků změň
   vykonávající útvar. `nazev_kratky` se **nesmí** změnit a nesmí k němu
   přibýt výpustka.
2. **Dlouhý název** — aktivitě `07-04-006-0001` (nejdelší v datech, 220 znaků;
   ve vývojové anonymizované sadě 218) smaž ručně obsah `nazev_kratky`.
   Po doběhu musí být pole vyplněné, končit `…` a neuseknuté uprostřed slova.
   Kanonická délka je 149 znaků (147 v anonymizované sadě).
3. **Necyklí** — po zápisu z bodu 2 se smí objevit **právě jeden** další běh
   a ten musí skončit větví If no.

## Na co si dát pozor

- **Po importu flow zapnout**, pokud import hlásil „one or more flows may not
  have turned on" — import stav zapnutí nemění.
- **V definici flow není žádný GUID** — web i list přicházejí z proměnných
  prostředí, takže týž balík platí pro každý tenant. Podmínkou je vyplněná
  *Current Value* u `mpsv_procesnimapaSite` a `mpsv_listAktivity`; balík
  hodnoty záměrně nevozí, aby import nepřepsal cílové prostředí.
- **Výpustka je jeden znak** `…`; tři tečky by hodnotu rozešly s importem
  a flow by ji přepisovalo pořád dokola.
- Změna pravidel zkracování se dělá **na jednom místě** (`zkratit()`
  v `src/check_schema.py`) a promítá se do tří stran: import, appka, flow.
  `src/check_flow.py` hlídá, že se strany nerozejdou.
