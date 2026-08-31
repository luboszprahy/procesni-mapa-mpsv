# Flow `ZalohaFlow` / `ZalohaScheduled` — snímek rejstříku

Přečte **všech sedm listů rejstříku** a uloží je jako jeden JSON do knihovny
`Zalohy` pod jménem `rejstrik_<RRRR-MM-DD_HHMM>.json`.

Flow jsou **generovaná, ne klikaná**: obě staví `src/build_zaloha_flow.py`
z jedné funkce `akce()`, kontroluje je `src/check_zaloha_flow.py`
(157 kontrol, 9 mutačně ověřených, `src/mutace_zaloha.py`).

## Proč dvě flow

Logic Apps má na flow právě jeden trigger, takže „na tlačítko z appky" a
„každý den ráno" nejde spojit:

| flow | trigger | k čemu |
|---|---|---|
| `ZalohaFlow` | PowerApps V2 | ruční snímek před hromadnou změnou |
| `ZalohaScheduled` | Recurrence, denně 5:00 SEČ | pojistka bez zásahu člověka |

Obě definice vznikají z **téže** funkce, ne klonováním hotového flow ze zipu.
Rozejít se tedy nemají jak — a brána to i tak porovnává, protože rozešlá
dvojčata by se poznala až ve chvíli, kdy by záloha byla potřeba.

## Proč snímek, když listy mají verzování

`make_setup.py` zapíná na listech verzování s limitem 500 verzí, k tomu koš
93 dní. To pokrývá „někdo smazal řádek" i „vrať mi předchozí znění položky".
Snímek přidává to, co tím pokryté není:

- jak rejstřík vypadal, když se schvalovala verze organizačního řádu,
- **rollback rozjetého hromadného importu** — ten mění stovky řádků naráz
  a koš pomáhá jen se smazanými, ne se změněnými,
- přenos mezi tenanty.

## Předpoklady

- Knihovna **`Zalohy`** na cílovém webu. Zakládá ji `src/setup_sharepoint.js`
  (F12 → Console na stránce webu). Bez ní flow spadne na neexistující složce.
- List **`HistorieKodu`** — zakládá týž skript. Flow ho zálohuje jako sedmý.
- Vyplněná **Current Value** u všech osmi proměnných prostředí, včetně
  `mpsv_listHistorieKodu`. Balík hodnoty záměrně nenese.
- Účet, pod kterým flow běží, má **Contribute na knihovně `Zalohy`**.

## Tvar snímku

```json
{
  "schema_verze": "1.0",
  "porizeno": "2026-08-31_1830",
  "listy": {
    "Agendy":  [ { "ID": 1, "Title": "01", "nazev": "…", "vlastnik": "…", "zdroj": "rejstrik" } ],
    "Procesy": [ … ], "DilciProcesy": [ … ], "Aktivity": [ … ],
    "AktivitaDilciProces": [ … ], "Utvary": [ … ], "HistorieKodu": [ … ]
  }
}
```

- Klíče jsou **interní názvy sloupců** SharePointu, aby se ze snímku dalo
  zapisovat zpátky bez překladové tabulky. `Title` nese identifikační kód.
- `Choice` sloupce se ukládají přes `?['Value']`, tedy jako řetězec — bez toho
  by ve snímku byl objekt `{"Value":"…"}` a restore by zapsal nesmysl.
- `schema_verze` je v souboru schválně: restore ze snímku, který vznikl nad
  jinou strukturou listů, musí umět odmítnout.
- `porizeno` a jméno souboru pocházejí z **jednoho** razítka (krok `Razitko`).
  Dvě volání `utcNow()` by se mohla o vteřinu rozejít a snímek by tvrdil jiný
  čas, než má v názvu.

## Stránkování — jediná věc, na které to může tiše selhat

Každý `Get items` má `runtimeConfiguration.paginationPolicy.minimumItemCount`
= 5 000. **Bez toho vrátí konektor jen prvních 100 položek, běh skončí zeleně
a snímek je oříznutý.** U `DilciProcesy` (250 řádků) by se to stalo hned.

5 000 je view threshold SharePointu; až se k němu rejstřík přiblíží, potřebuje
jiné řešení, ne vyšší číslo.

## Co zbývá

- **Tlačítko v appce** — `ZalohaFlow.Run()` jde napsat teprve tehdy, až je flow
  ve Studiu zaregistrované jako datový zdroj (`Add data`). Do té doby se ruční
  snímek spouští z Power Automate (`Test` → `Manually`).
- **Úklid starých snímků** — soubory se hromadí. Úklidové flow musí nechat
  naživu poslední snímek každého měsíce, ne mazat podle stáří slepě.
- **Restore** — F11 krok 4, staví se až po hromadném importu.
