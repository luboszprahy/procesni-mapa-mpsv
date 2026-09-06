# Schéma SharePoint listů — rejstřík agend a procesů MPSV

Generováno z `src/schema.json` skriptem `src/check_schema.py`. **Needituj ručně** —
uprav schéma a skript spusť znovu.

Publisher solution `mpsv`, prefix `mpsv_`.

## Zásady

- Interní názvy sloupců **bez diakritiky** — přejmenování zobrazovaného názvu
  interní název nemění a REST `$select` pracuje s interními.
- Vztahy nesou **textový kód**, ne SharePoint lookup ID. Důvod: přenositelnost
  mezi tenanty a migrovatelnost do Dataverse bez ztráty vazeb. Cenou je, že
  referenční integritu nehlídá platforma — hlídá ji `src/check_schema.py`
  a pořizovací aplikace.
- `Title` v SharePointu nelze vypnout, proto nese identifikační kód.
- Odvozené údaje (počet aktivit ve větvi) se **neukládají** — počítají se
  až v mapě ze zapečených dat, jinak by v listech zastarávaly.

## Listy

### `Agendy`

Ciselnik agend (uroven AA). Zdroj: centralni rejstrik.

Zdroj dat: `agendy.csv` (7 řádků). Verzování: zapnuto.

| Interní název | Zobrazovaný název | Typ | Povinný | Indexovaný | Zdroj v CSV |
|---|---|---|---|---|---|
| `Title` | Kód | Jeden řádek textu | ano | ano | kod |
| `nazev` | Název | Jeden řádek textu | ano | ne | nazev |
| `vlastnik` | Vlastník agendy | Jeden řádek textu | ne | ne | vlastnik |
| `zdroj` | Zdroj | Volba | ne | ne | zdroj |

- `zdroj` — hodnoty: `rejstrik`, `karta`
- `Title` — Identifikacni kod AA. Prirozeny klic.
- `vlastnik` — Sekce. Vice vlastniku je pripustny stav - oddelovac '; '.
- `zdroj` — Odkud polozka prisla - rejstrik nebo evidencni karta utvaru.

Sloupce CSV, které se **záměrně neukládají**:
- `pocet_aktivit` — odvozeny udaj - pocita se az v mape z vazebni tabulky, neuklada se

### `Procesy`

Ciselnik procesu (uroven AA-BB).

Zdroj dat: `procesy.csv` (46 řádků). Verzování: zapnuto.

| Interní název | Zobrazovaný název | Typ | Povinný | Indexovaný | Zdroj v CSV |
|---|---|---|---|---|---|
| `Title` | Kód | Jeden řádek textu | ano | ano | kod |
| `nazev` | Název | Jeden řádek textu | ano | ne | nazev |
| `agenda_kod` | Agenda (kód) | Jeden řádek textu | ano | ano | agenda_kod |
| `vlastnik` | Vlastník procesu | Jeden řádek textu | ne | ne | vlastnik |
| `zdroj` | Zdroj | Volba | ne | ne | zdroj |
| `puvodni_kod` | Vzniklo z kódu | Jeden řádek textu | ne | ne | — (zakládá se prázdné) |

- `zdroj` — hodnoty: `rejstrik`, `karta`
- `Title` — Identifikacni kod AA-BB.
- `agenda_kod` — Textovy odkaz na Agendy.Title - ne lookup ID (prenositelnost mezi tenanty).
- `vlastnik` — Odbor. Vice vlastniku pripustne - oddelovac '; '.
- `puvodni_kod` — Kod predchudce, ktery se pri presunu pod jineho rodice uzavrel. Prazdne u polozek, ktere vznikly rovnou. Protejsek: HistorieKodu.nastupce_kod.

Sloupce CSV, které se **záměrně neukládají**:
- `pocet_aktivit` — odvozeny udaj - pocita se az v mape

### `DilciProcesy`

Ciselnik dilcich procesu (uroven AA-BB-CCC).

Zdroj dat: `dilci_procesy.csv` (250 řádků). Verzování: zapnuto.

| Interní název | Zobrazovaný název | Typ | Povinný | Indexovaný | Zdroj v CSV |
|---|---|---|---|---|---|
| `Title` | Kód | Jeden řádek textu | ano | ano | kod |
| `nazev` | Název | Jeden řádek textu | ano | ne | nazev |
| `proces_kod` | Proces (kód) | Jeden řádek textu | ano | ano | proces_kod |
| `vlastnik` | Vlastník dílčího procesu | Jeden řádek textu | ne | ne | vlastnik |
| `stav_rejstrik` | Stav v rejstříku | Volba | ne | ne | stav_rejstrik |
| `zdroj` | Zdroj | Volba | ne | ne | zdroj |
| `puvodni_kod` | Vzniklo z kódu | Jeden řádek textu | ne | ne | — (zakládá se prázdné) |

- `stav_rejstrik` — hodnoty: `využitý`, `využitý-S4`, `nevyužitý`
- `zdroj` — hodnoty: `rejstrik`, `karta`
- `Title` — Identifikacni kod AA-BB-CCC.
- `nazev` — Nejdelsi namereny nazev 166 znaku - rezerva do 255 je mala, ale sloupec musi zustat Text kvuli razeni a indexaci.
- `vlastnik` — Odbor. Vice vlastniku pripustne - oddelovac '; '.
- `stav_rejstrik` — Barevne odliseni v puvodnim rejstriku.
- `puvodni_kod` — Kod predchudce, ktery se pri presunu pod jineho rodice uzavrel. Prazdne u polozek, ktere vznikly rovnou. Protejsek: HistorieKodu.nastupce_kod.

Sloupce CSV, které se **záměrně neukládají**:
- `pocet_aktivit` — odvozeny udaj - pocita se az v mape

### `Aktivity`

Aktivity (uroven AA-BB-CCC-DDDD). Jeden radek evidence = jedna aktivita.

Zdroj dat: `aktivity.csv` (46 řádků). Verzování: zapnuto. Výchozí řazení: `nazev_kratky`, pak `Title`.

| Interní název | Zobrazovaný název | Typ | Povinný | Indexovaný | Zdroj v CSV |
|---|---|---|---|---|---|
| `Title` | Kód | Jeden řádek textu | ano | ano | kod |
| `nazev` | Název aktivity (úplný) | Více řádků textu (prostý text) | ano | ne | nazev |
| `nazev_kratky` | Název | Jeden řádek textu | ne | ano | odvozeno z `nazev`, zkráceno na 150 znaků |
| `dilci_proces_kod` | Primární dílčí proces (kód) | Jeden řádek textu | ano | ano | dilci_proces_kod |
| `vykonava` | Vykonává útvar | Jeden řádek textu | ne | ano | vykonava |
| `spolupracuje` | Spolupracuje | Více řádků textu (prostý text) | ne | ne | spolupracuje |
| `vnitrni_predpis` | Vnitřní předpis | Více řádků textu (prostý text) | ne | ne | vnitrni_predpis |
| `text_pro_or` | Text pro OŘ | Více řádků textu (prostý text) | ne | ne | — (zakládá se prázdné) |
| `sekce` | Sekce | Jeden řádek textu | ne | ano | sekce |
| `stav` | Stav | Volba | ne | ano | — (zakládá se prázdné) |
| `datum_aktualizace` | Datum aktualizace | Datum a čas | ne | ne | — (zakládá se prázdné) |
| `puvodni_kod` | Vzniklo z kódu | Jeden řádek textu | ne | ne | — (zakládá se prázdné) |

- `stav` — hodnoty: `pracovní`, `schváleno`
- `Title` — Identifikacni kod AA-BB-CCC-DDDD.
- `nazev` — Uplny nazev. Note (vice radku, prosty text) - namereno 220 znaku, hranice 255 je blizko. Note nejde indexovat ani radit, proto vedle nej stoji nazev_kratky.
- `nazev_kratky` — Odvozeny ze sloupce nazev - useknuty na hranici slova na 150 znaku, s vypustkou. Slouzi k razeni a indexaci ve view, ktere Note neumi. Udrzuje ho import a porizovaci appka pri kazde zmene nazvu.
- `dilci_proces_kod` — Primarni zarazeni. Vsechna zarazeni vc. tohoto drzi list AktivitaDilciProces.
- `vykonava` — Oddeleni.
- `vnitrni_predpis` — Vice predpisu oddeleno '; '. Namereno 293 znaku - proto Note.
- `text_pro_or` — V evidencni karte neexistuje - zaklada se prazdny, plni se rucne pro budouci generovani organizacniho radu.
- `stav` — V evidencni karte neexistuje - pri importu se plni hodnotou 'pracovní'.
- `datum_aktualizace` — V evidencni karte neexistuje - pri importu se plni datem importu, dal ji udrzuje porizovaci appka.
- `puvodni_kod` — Kod predchudce, ktery se pri presunu pod jineho rodice uzavrel. Prazdne u polozek, ktere vznikly rovnou. Protejsek: HistorieKodu.nastupce_kod.

Sloupce CSV, které se **záměrně neukládají**:
- `zdroj_radek` — cislo radku ve zdrojove evidencni karte - artefakt importu, do rejstriku nepatri

### `AktivitaDilciProces`

Vazebni tabulka M:N - aktivita muze patrit do vice dilcich procesu.

Zdroj dat: `aktivita_dilciproces.csv` (46 řádků). Verzování: zapnuto.

| Interní název | Zobrazovaný název | Typ | Povinný | Indexovaný | Zdroj v CSV |
|---|---|---|---|---|---|
| `Title` | Klíč | Jeden řádek textu | ano | ano | odvozeno: `{aktivita_kod}__{dilci_proces_kod}` |
| `aktivita_kod` | Aktivita (kód) | Jeden řádek textu | ano | ano | aktivita_kod |
| `dilci_proces_kod` | Dílčí proces (kód) | Jeden řádek textu | ano | ano | dilci_proces_kod |
| `primarni` | Primární | Volba | ne | ne | primarni |

- `primarni` — hodnoty: `ano`, `ne`
- `Title` — Odvozeny klic - zajistuje idempotenci importu a brani duplicitni vazbe.

### `Utvary`

Ciselnik utvaru (ministr/sekce/odbor/oddeleni). Zdrojem je MPSV list Organizacni utvary; kod je hole cislo utvaru, nazev je oznaceni z MPSV (O11, Sekce 3). Ministr ma kod 0.

Zdroj dat: `utvary.csv` (44 řádků). Verzování: zapnuto. Výchozí řazení: `Title`.

| Interní název | Zobrazovaný název | Typ | Povinný | Indexovaný | Zdroj v CSV |
|---|---|---|---|---|---|
| `Title` | Kód útvaru | Jeden řádek textu | ano | ano | kod |
| `nazev` | Název útvaru | Jeden řádek textu | ano | ne | nazev |
| `uroven` | Úroveň | Volba | ne | ano | uroven |
| `nadrizeny_kod` | Nadřízený útvar (kód) | Jeden řádek textu | ne | ano | nadrizeny_kod |

- `uroven` — hodnoty: `ministr`, `sekce`, `odbor`, `oddělení`
- `Title` — Cislo utvaru tak, jak ho nesou aktivity a rejstrik. Delka cisla NEURCUJE uroven ani nadrizeneho - O32 je odbor pod Sekci 6. Ministr ma 0.
- `nadrizeny_kod` — Kod nadrizeneho utvaru z MPSV listu; u ministra prazdne. Z cisla se odvodit neda.

### `HistorieKodu`

Uzavrene identifikacni kody vsech ctyr urovni. Zaznam vznika pri presunu polozky pod jineho rodice (zanik + vznik) nebo pri zruseni bez nahrady. Nemaze se a kod se nikdy nerecykluje - pridelovaci vzorec bere maximum pres zivy list I pres tuto historii.

Zdroj dat: `None` (0 řádků). Verzování: zapnuto.

| Interní název | Zobrazovaný název | Typ | Povinný | Indexovaný | Zdroj v CSV |
|---|---|---|---|---|---|
| `Title` | Uzavřený kód | Jeden řádek textu | ano | ano | — (zakládá se prázdné) |
| `uroven` | Úroveň | Volba | ne | ano | — (zakládá se prázdné) |
| `nazev` | Název | Jeden řádek textu | ano | ne | — (zakládá se prázdné) |
| `nastupce_kod` | Nástupce (kód) | Jeden řádek textu | ne | ne | — (zakládá se prázdné) |
| `duvod` | Důvod | Více řádků textu (prostý text) | ne | ne | — (zakládá se prázdné) |
| `datum` | Datum uzavření | Datum a čas | ne | ne | — (zakládá se prázdné) |
| `kdo` | Uzavřel | Jeden řádek textu | ne | ne | — (zakládá se prázdné) |

- `uroven` — hodnoty: `agenda`, `proces`, `dilci_proces`, `aktivita`
- `Title` — Uzavreny identifikacni kod. Prirozeny klic - kazdy kod se uzavira prave jednou.
- `uroven` — Uroven, na ktere kod stal. Odvoditelna z poctu segmentu, ale uklada se kvuli filtrovani ve view.
- `nazev` — Nazev polozky v okamziku uzavreni - doklad, ktery se uz nemeni.
- `nastupce_kod` — Novy kod, pod kterym polozka zije dal. Prazdne = zruseno bez nahrady.

## Knihovny

Zakládá je týž skript jako listy (`setup_sharepoint.js`), jen jako
BaseTemplate 101 — knihovna sedí v kořenu webu, ne pod `/Lists/`.

### `Zalohy`

Snimky rejstriku (JSON) z flow ZalohaFlow. Nazev souboru nese razitko, verzovani proto neni potreba.

Zobrazovaný název: Zálohy.

### `Exporty`

Vyexportovane dokumenty z prehledu (.doc/.xls) z flow ExportFlow. Do 1.0.0.81 padaly do Site Assets a misily se s publikovanou mapou.

Zobrazovaný název: Exporty.

### `Import`

Vyplnene sesity pro hromadny import aktivit. Spravce sem nahrava .xlsx podle sablony; cte je ImportFlow.

Zobrazovaný název: Import.
