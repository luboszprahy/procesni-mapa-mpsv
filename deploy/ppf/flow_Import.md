# Flow `ImportFlow` — hromadné pořízení aktivit z Excelu

Vyrábí ho `src/build_import_flow.py`, hlídá `src/check_import_flow.py`
(159 kontrol) a mutačně `src/mutace_import.py` (21/21).
Poprvé v balíku **1.0.0.85**, obrazovka náhledu od **1.0.0.87**.

## K čemu je

Správce vyplní sešit podle šablony (`Data ▾ → Vzorová tabulka pro import`),
nahraje ho do knihovny **`Import`** a spustí import. Flow sešit přečte,
porovná s rejstříkem a **nejdřív ukáže náhled**: co vznikne, co je duplicita,
co je chyba a na kterém řádku. Teprve po potvrzení zapisuje.

Nahrazuje `deploy/mpsv/02_import_dat.js`, což byl nástroj pro vývojáře, ne
pro správce.

## Datový kontrakt

```json
{"soubor": "karta_s3.xlsx", "rezim": "nahled"}
```

- `soubor` — název souboru v knihovně `Import`, bez cesty.
- `rezim` — `nahled` (nic se nezapíše) nebo `zapis`.

Odpověď:

```
stav    = "nahled"
soubor  = "karta_s3.xlsx"
prehled = "46|~|1|~|43|~|1|~|0|~|1"
chyby   = "17|~|Vede evidenci…|~|dílčí proces 01-02-999 v rejstříku není"
```

`prehled` je **šest čísel v pevném pořadí**: řádků celkem, prázdné, založí se,
duplicitní, chybné, neexistující dílčí proces. `chyby` je nula až N řádků
`číslo řádku |~| název |~| důvod`, oddělených `|#|`.

Proč ne JSON: viz poslední kapitola. Pořadí je součástí kontraktu, protože
oddělovaný text jméno pole nenese — hlídá ho brána.

## Co se o konektoru ověřilo měřením

Parametry akce `List rows present in a table` jsou čtyři a tři z nich vypadají
jako neprůhledná ID vázaná na tenant. Změřeno 01.09.2026 na PPF DEV:

| parametr | co snese | doklad |
|---|---|---|
| `file` | **výraz** | akce se dostala až k hledání tabulky, když `File` přišel z `Get file metadata using path` |
| `table` | **jméno** (`Aktivity`) | chyba zněla `No table was found with the name 'Activity'` — vyhledává tedy podle názvu |
| `drive` | **jen Graph ID `b!…`** | `Sdilene dokumenty` skončilo na `The provided drive id appears to be malformed` |
| `source` | Graph site id | `sites/<host>,<siteId>,<webId>` |

**Balík proto nenese ani jedno z těch ID.** `source` se skládá z proměnné webu
a dvou REST dotazů (`/_api/site/id`, `/_api/web/id`), `drive` se hledá
v `/_api/v2.0/drives` **podle URL segmentu knihovny** — ne podle zobrazovaného
názvu, ten nese diakritiku a přejmenováním se mění. Ověřeno, že endpoint na
webu odpovídá (`src/zjisti_excel_ids.js`).

Flow běží pod servisním účtem z connection reference (`embedded`, ne
`invoker`), takže appka po uživatelích nechce vlastní excelové spojení.

## Jak se řádky rozdělují

Rozklad je **úplný a nepřekrývá se** — každý řádek sešitu padne právě do jedné
skupiny. Kdyby se skupiny překrývaly, sedělo by v náhledu jiné číslo než ve
skutečnosti a správce by opravoval podle něj.

```
Ocistene ─┬─ Prazdne        všechny buňky prázdné → ignoruje se
          └─ S_obsahem ─┬─ Chybne          chybí název nebo kód dílčího procesu
                        └─ Uplne ─┬─ Neznamy_dilci   dílčí proces v rejstříku není
                                  └─ Zarazene ─┬─ Duplicitni  dvojice dílčí+název už existuje
                                               └─ K_zalozeni  zakládá se
```

**Prázdný řádek se musí přeskočit**, protože šablona se vydává s jedním —
Tabulku bez datového řádku Excel „opravuje". Bez toho by první použití šablony
založilo prázdnou aktivitu.

Duplicita se pozná podle dvojice **dílčí proces + název**, ne podle názvu
samotného: táž činnost pod dvěma dílčími procesy je legitimní stav.

Hodnoty se ořezávají (`trim`) — mezera navíc by z duplicity udělala nový
záznam.

## Přidělování kódů

Nová aktivita pod dílčím procesem `01-02-003` dostane `01-02-003-0001`,
`-0002` a tak dál. Číslo se odvozuje z **nejvyššího dosud použitého** kódu pod
tímtéž rodičem, ne z počtu aktivit — smazaný kód se tím nerecykluje.

Kódy přidělené v témže běhu se drží v proměnné `pouziteKody`, aby je viděl
i další řádek. Smyčka proto běží se **souběžností 1**: paralelní průchody by
dvěma aktivitám pod týmž dílčím procesem přidělily stejný kód.

Ke každé aktivitě vzniká i **primární vazba** v `AktivitaDilciProces` s klíčem
`<kod aktivity>__<kod dílčího procesu>` — týž tvar, jaký zakládá appka na
obrazovce vazeb. Jiný tvar by vyrobil duplicity, které by appka nenašla.

`nazev_kratky` import **nezapisuje**: dopočítá ho `AktualizaceKratkehoNazvu`,
které visí na „item is created or modified". Kdyby ho psaly obě, přepisovaly
by se navzájem.

`stav` nevyplněný v sešitě se doplní na `pracovní`, `datum_aktualizace`
razítkem importu.

## Akce (31 nejvyšší úrovně)

```
Vstup            Compose   json(triggerBody()['text'])
Cesta_webu       Compose   server-relative cesta webu
Site_id/Web_id   SP REST   /_api/site/id, /_api/web/id
Disky            SP REST   /_api/v2.0/drives
Zdroj            Compose   sites/<host>,<siteId>,<webId>
Disk_kandidati   Filter    disk, jehož webUrl končí /Import
Disk             Compose   jeho id
Soubor           SP        GetFileMetadataByPath /Import/<soubor>
Radky            Excel     List rows present in a table
Ocistene         Select    hlavičky → interní názvy + číslo řádku (index+2)
Nacti_*          SP        DilciProcesy a Aktivity se stránkováním
Kody_*/Klice_*   Select    kódy a klíče duplicit
Prazdne … K_zalozeni       rozklad řádků (viz výše)
Pouzite_kody     Variable  existující kódy aktivit
Zapis            If        rezim = zapis → Zaloz (Foreach, souběžnost 1)
Popis_*          Select    chybné řádky s důvodem a číslem řádku
Prehled/Odpoved            počty a odpověď
```

## Ruční zkouška bez appky

1. Nahraj vyplněný sešit do knihovny `Import`.
2. Power Automate → `ImportFlow` → **Test → Manually**, vstup:

```json
{"soubor": "karta_s3.xlsx", "rezim": "nahled"}
```

Běh musí být zelený a `Odpoved` vrátit rozpad. **V režimu náhledu nesmí
v listech přibýt jediná položka** — ověř to na počtech v Site contents.

Teprve pak `"rezim": "zapis"`. Po zápisu zkontroluj, že nové aktivity mají
kód ve tvaru `AA-BB-CCC-DDDD`, vyplněný `nazev_kratky` (dopočítá ho druhé flow,
chvíli to trvá) a v `Vazba aktivita–dílčí proces` primární vazbu.

## Meze

- Sešit se čte celý do paměti běhu. Karta o padesáti aktivitách je bez
  problému; u tisíců by se muselo stránkovat.
- Zápis po řádku se souběžností 1 — padesát aktivit je otázka desítek sekund.
- Import **nemaže a needituje**: existující aktivitu nepřepíše, jen ohlásí
  jako duplicitu. Opravy se dělají v appce.
- Kód v sešitě se nedá vyplnit — v šabloně ten sloupec není a import ho
  přiděluje sám.

## Třetí režim: `seznam`

```json
{"rezim": "seznam"}
```

Vrátí názvy sešitů v knihovně `Import` v poli `prehled`, oddělené `|#|`. Obrazovka náhledu jimi plní
rozbalovátko.

Existuje proto, že appka by jinak musela mít knihovnu připojenou jako datový
zdroj, a to jde jedině ve Studiu — tedy dalším kolem. Flow navíc vrací přesně
ta jména, která samo přijímá na vstupu, takže se nemají jak rozejít s tím, co
appka pošle zpátky.

**Schéma odpovědi zůstává totožné** (čtyři řetězce), takže flow kvůli tomuhle
režimu nepotřebuje novou registraci. Běh se po odpovědi ukončí — dál by se
pokračovalo nad souborem, jehož název v tomhle režimu nikdo nezadal.

## Odpovědi jdou jako oddělovaný text, ne JSON

Canvas app má `dynamicschema = False`, takže na `ParseJSON` nemá co navázat.
Pole se proto spojují oddělovači `|~|` (pole) a `|#|` (řádky) a appka je
rozebírá `Split()`. **Bere je podle POŘADÍ**, ne podle klíče — oddělovaný text
jméno pole nenese —, takže pořadí je součástí kontraktu a hlídá ho brána.

## Když import hlásí „Nemáte oprávnění k otevření tohoto souboru"

Ověřeno v provozu 02.09.2026 (PPF DEV). Akce `Radky` skončí na:

```
The request is forbidden by Graph API.
Error code is 'OpenWorkbookAccessDenied'.
Error message is 'Nemáte oprávnění k otevření tohoto souboru.'
statusCode: 403
```

**Příčina je citlivostní štítek sešitu, ne oprávnění k webu.** Štítek
**„Interní" projde**; přísnější stupeň soubor zašifruje a Excel Online
(Business) ho přes Graph API neotevře — ani člověku, který ho vlastní.
Náprava: přeštítkovat sešit na „Interní" a spustit náhled znovu.

**Proč to vypadá jako chyba flow.** Štítek si sešit vezme až při uložení
v desktop Excelu, takže vydaná šablona je čistá a vadný je až vyplněný sešit.
Všechny akce před `Radky` přitom projdou zeleně — `Soubor`
(`GetFileMetadataByPath`) čte metadata, a ta šifrovaná nejsou. Z appky je
navíc vidět jen `Flow.Run failed: 502 BadGateway / NoResponse`, jako u každé
jiné chyby flow.

**Rozlišovací test**, kdyby se to opakovalo: nahrát do knihovny `Import` sešit,
který nikdo neotevřel v desktop Excelu, a spustit náhled. Projde-li, je to
štítek. Padne-li stejně, je to účet u Excel Online connection.
