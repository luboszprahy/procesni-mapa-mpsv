# Flow `AktualizaceKratkehoNazvu` — pojistka nad sloupcem `nazev_kratky`

Hlídá, aby `nazev_kratky` v listu `Aktivity` vždy odpovídal sloupci `nazev`.
Řeší zápisy, které neprošly pořizovací appkou — ruční editaci přímo v listu,
hromadný import z Excelu, opravu přes datové zobrazení.

Návod je **klikací, pro designer** (stejný důvod jako u `flow_MapaPublish.md`).

## Proč to nemůže dělat počítaný sloupec

Dvě nezávislé překážky, obě ověřené:

- vzorec počítaného sloupce **neumí číst sloupec typu „více řádků textu"**,
  a `nazev` jím být musí (naměřeno 220 znaků, hranice Text je 255),
- počítaný sloupec **nejde indexovat**, takže by nad 5 000 položkami neuneslo
  řazení výchozího zobrazení, které na `nazev_kratky` stojí.

Proto hodnotu plní import i appka a tohle flow je pojistka pro zbytek.

## Kanonické zkrácení (co přesně se má spočítat)

Závazná je funkce `zkratit()` v `src/check_schema.py`; touž používá import:

1. srovnat bílé znaky — víc mezer za sebou na jednu, konce oříznout,
2. je-li výsledek **150 znaků nebo kratší**, je hotovo a **nic se nemění**
   (tečka na konci krátkého názvu tedy zůstane),
3. jinak useknout na **149** znaků,
4. najít v uříznutém textu **poslední mezeru**; leží-li za 75. znakem, seknout
   tam (aby se neřezalo uprostřed slova),
5. odmazat z konce znaky `,`, `;`, `.` a mezery,
6. připojit výpustku `…` (jeden znak U+2026, ne tři tečky).

Flow nemá regulární výrazy, takže se to skládá z `replace`, `substring`
a `lastIndexOf`. Že řetěz akcí níže dává **týž výsledek** jako `zkratit()`,
ověřuje `src/check_zkraceni_flow.py` na 106 vzorcích (reálná i anonymizovaná
data + 14 hraničních případů). Když se návod změní, změň i skript — a naopak.

```powershell
& .venv/Scripts/python.exe src/check_zkraceni_flow.py
```

## Trigger

**`When an item is created or modified`** nad listem `Aktivity`.

Site Address a List Name se vybírají z nabídky. **Nesmí to být proměnná
prostředí** — zápisové akce SharePoint konektoru (`Update item`) si tělo
požadavku odvozují z konkrétního listu; s runtime výrazem se import sice
povede, ale flow pak nejde zapnout (`PatchItem … is missing required property
'item'`). Na tenant MPSV se proto flow **staví znovu podle tohoto návodu**,
nepřenáší se výměnou hodnoty proměnné.

## Kroky v designeru

### 1. `Compose` → `Nazev_syrovy`

```
@{coalesce(triggerOutputs()?['body/nazev'], '')}
```

### 2. `Compose` → `Bez_bilych_znaku`

```
@{trim(
    replace(replace(replace(
      replace(replace(replace(outputs('Nazev_syrovy'),
        decodeUriComponent('%0D'), ' '),
        decodeUriComponent('%0A'), ' '),
        decodeUriComponent('%09'), ' '),
      '  ', ' '), '  ', ' '), '  ', ' ')
  )}
```

Nejdřív CR, LF a tabulátor na mezeru, pak **tři průchody** `'  '` → `' '`.
Jeden průchod počet mezer jen půlí, takže tři pokryjí až osm mezer za sebou.
Delší shluk by zůstal — v datech se nevyskytuje a flow kvůli tomu necyklí
(viz „Proč to necyklí" níže).

### 3. `Compose` → `Rez`

```
@{if(lessOrEquals(length(outputs('Bez_bilych_znaku')), 150),
     outputs('Bez_bilych_znaku'),
     substring(outputs('Bez_bilych_znaku'), 0, 149))}
```

### 4. `Compose` → `Rez_na_slovo`

```
@{if(lessOrEquals(length(outputs('Bez_bilych_znaku')), 150),
     outputs('Bez_bilych_znaku'),
     if(greater(lastIndexOf(outputs('Rez'), ' '), 75),
        substring(outputs('Rez'), 0, lastIndexOf(outputs('Rez'), ' ')),
        outputs('Rez')))}
```

Hranice **75** = polovina ze 150. Bez ní by název bez mezer (jedno dlouhé
slovo) přišel skoro o celý obsah.

### 5. `Compose` → `Orez_1`, `Orez_2`, `Orez_3`

Tři akce se stejným tvarem; každá čte výstup té předchozí. Níže je znění pro
`Orez_1`; v `Orez_2` nahraď **každý** výskyt `outputs('Rez_na_slovo')` za
`outputs('Orez_1')` a v `Orez_3` za `outputs('Orez_2')` (v každé akci je jich pět).

```
@{if(equals(length(outputs('Rez_na_slovo')), 0),
     outputs('Rez_na_slovo'),
     if(contains(' ,;.', substring(outputs('Rez_na_slovo'),
                                   sub(length(outputs('Rez_na_slovo')), 1), 1)),
        substring(outputs('Rez_na_slovo'), 0,
                  sub(length(outputs('Rez_na_slovo')), 1)),
        outputs('Rez_na_slovo')))}
```

Test na nulovou délku **není zbytečný**: `substring` nad prázdným řetězcem
akci shodí a `and()` v Logic Apps vyhodnocuje oba argumenty, takže se
podmínky nedají spojit — musí být vnořené `if`.

### 6. `Compose` → `Cil`

```
@{if(lessOrEquals(length(outputs('Bez_bilych_znaku')), 150),
     outputs('Bez_bilych_znaku'),
     concat(outputs('Orez_3'), decodeUriComponent('%E2%80%A6')))}
```

Ořez koncových znaků se uplatní **jen u zkráceného názvu** — u krátkého se
vrací text tak, jak je. `decodeUriComponent('%E2%80%A6')` je výpustka `…`;
psát ji do výrazu přímo se nevyplácí, kopírováním se snadno zamění za tři tečky.

### 7. `Condition` → `Lisi_se`

```
@not(equals(coalesce(triggerOutputs()?['body/nazev_kratky'], ''), outputs('Cil')))
```

Ve větvi **If yes**: `Update item` nad listem `Aktivity`.

| pole | hodnota |
|---|---|
| Id | `@triggerOutputs()?['body/ID']` |
| Title (Kód) | `@triggerOutputs()?['body/Title']` |
| Název aktivity (`nazev`) | `@triggerOutputs()?['body/nazev']` |
| Primární dílčí proces (`dilci_proces_kod`) | `@triggerOutputs()?['body/dilci_proces_kod']` |
| Název (`nazev_kratky`) | `@outputs('Cil')` |

**Povinná pole se musí poslat zpátky, i když se nemění.** `Update item`
skládá tělo z formuláře listu; nevyplněné povinné pole akce odmítne.

Větev **If no** zůstane prázdná — to je normální stav při většině spuštění.

## Proč to necyklí

`Update item` spustí trigger znovu. Při druhém průchodu ale `nazev_kratky`
už je rovno `Cil`, podmínka je nepravdivá a nic se nezapisuje. Cyklus by
vznikl jen tehdy, kdyby výpočet nebyl stabilní (jiný výsledek při druhém
běhu nad vlastním výstupem) — proto se počítá **vždy z `nazev`**, nikdy
z `nazev_kratky`.

Cenou je **jeden běh navíc po každé skutečné změně**. To je přijatelné;
u hromadného importu se flow spustí na každý řádek, ale import plní
`nazev_kratky` sám, takže všechny ty běhy skončí větví If no.

## Jak se ověří, že to funguje

1. **Krátký název beze změny** — u aktivity s názvem do 150 znaků změň
   vykonávající útvar. Flow doběhne, `nazev_kratky` se **nesmí** změnit
   a nesmí k němu přibýt výpustka.
2. **Dlouhý název** — vezmi aktivitu `07-04-006-0001` (nejdelší v datech:
   220 znaků, ve vývojové anonymizované sadě 218), smaž jí ručně obsah
   `nazev_kratky`. Po doběhu musí být pole vyplněné, končit `…`
   a **neuseknuté uprostřed slova**. Kanonická délka je 149 znaků
   (147 v anonymizované sadě).
3. **Shoda s kanonickou funkcí** — co má v poli být, vypíše:
   ```powershell
   & .venv/Scripts/python.exe -c "import csv,io,sys; sys.path.insert(0,'src'); from check_schema import zkratit; print([zkratit(r['nazev'],150) for r in csv.DictReader(io.open('runs/anonym/aktivity.csv',encoding='utf-8-sig',newline=''),delimiter=';') if r['kod']=='07-04-006-0001'][0])"
   ```
   Musí sedět znak po znaku včetně výpustky. Další dvě aktivity nad hranicí
   jsou `01-01-003-0001` (181 znaků) a `01-01-003-0002` (199) — liší se až
   za 165. znakem, takže jsou zároveň kontrolou, že se `nazev_kratky`
   nepoužívá jako jediný klíč řazení.
4. **Necyklí** — po zápisu z bodu 2 se smí objevit **právě jeden** další běh
   a ten musí skončit větví If no. Když běhů přibývá, je chyba ve výpočtu,
   ne v podmínce.
5. **Nic se neztratilo** — po zásahu flow zkontroluj, že `nazev`,
   `dilci_proces_kod` i `Title` mají původní hodnoty (past s povinnými poli).

## Na co si dát pozor

- **Zápisová akce nesmí mít list jako runtime výraz** — jinak flow nejde zapnout.
- **Povinná pole posílat zpět** i beze změny, jinak je `Update item` vyprázdní
  nebo skončí chybou.
- **Výpustka je jeden znak** `…`, ne tři tečky — jinak se hodnota rozejde
  s importem a flow ji bude přepisovat pořád dokola.
- **Po importu solution flow ručně zapnout**, pokud import hlásil
  „one or more flows may not have turned on" — import stav zapnutí nemění.
- Změna pravidel zkracování se dělá **na jednom místě** (`zkratit()`
  v `src/check_schema.py`) a promítá se do tří stran: import, appka, tohle
  flow. Test `src/check_zkraceni_flow.py` hlídá, že se strany nerozejdou.
