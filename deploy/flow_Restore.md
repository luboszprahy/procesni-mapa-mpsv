# Flow `RestoreFlow` — obnova rejstříku ze snímku zálohy

Vyrábí ho `src/build_restore_flow.py`, hlídá `src/check_restore_flow.py`
(568 kontrol) a mutačně `src/mutace_restore.py` (15/15).
Poprvé v balíku **1.0.0.84**, obrazovka náhledu od **1.0.0.87**.

## K čemu je

Vrátí rejstřík do stavu, ve kterém byl v okamžiku pořízení snímku
`Zalohy/rejstrik_<razitko>.json`. Nikdy neběží plánovaně — vždycky ručně
z appky, a vždycky se dá spustit nejdřív **nanečisto**.

Doplňuje to, co verzování listů nepokrývá: verze vrací jednotlivé položky,
ne stav celého rejstříku k danému okamžiku, a koš pomáhá jen se smazanými
řádky, ne se změněnými.

## Datový kontrakt

Trigger `PowerAppV2` má **jeden textový vstup** s tímto JSON:

```json
{"soubor": "rejstrik_2026-09-01_0300.json", "rezim": "nahled"}
```

- `soubor` — název souboru v knihovně `Zalohy`, bez cesty.
- `rezim` — `nahled` (nic se nezapíše) nebo `zapis`.

Odpověď:

```
stav     = "nahled"
hlaseni  = ""
porizeno = "2026-09-01_0300"
prehled  = "Agendy|~|0|~|1|~|0|~|6|#|Procesy|~|0|~|0|~|0|~|44|#|…"
```

`prehled` je jeden řádek na list, pole v pevném pořadí: **název, založit,
změnit, navíc, celkem ve snímku**. Řádky odděluje `|#|`, pole `|~|`.

Jde schválně jako **jeden řetězec**, ne jako pole objektů: schéma odpovědi se
tak nemění s počtem listů. Kdyby se změnilo, přestane appce sedět a flow se
musí znovu registrovat ve Studiu.

Když snímek vznikl nad jinou verzí schématu, vrátí flow
`stav: "neshoda_schematu"` s vysvětlením a **běh se ukončí** — obnova se
neprovede ani napůl.

## Čtyři pravidla, na kterých to stojí

### 1. Cíl zápisu se dohledává podle kódu, nikdy podle ID ze snímku

Snímek u každého řádku nese i `ID`. To je ale stav k okamžiku zálohy: když se
záznam mezitím smazal a jiný vznikl, patří dnes to ID někomu jinému a zápis
podle něj by **tiše přepsal cizí řádek** — a běh by skončil zeleně.

Proto každá úprava nejdřív dohledá cílový řádek v aktuálním listu podle
`Title` (kódu), akcí `Najdi_<list>`, a teprve na jeho ID pošle MERGE. `ID`
ze snímku slouží jen k tomu, aby náhled uměl říct „tenhle záznam mezitím
zanikl a vznikl znovu".

Tohle je ta kontrola, kterou shazuje první mutace v `mutace_restore.py`.

### 2. Obnova nikdy nemaže

Řádek, který dnes v listu je a ve snímku není, se jen spočítá do sloupce
`navic` a ohlásí. Kdyby restore mazal, byla by z opravy druhá destruktivní
operace a chybný výběr snímku by stál data. Brána proto odmítá jakoukoli
mazací operaci i metodu `DELETE`.

### 3. Zapisuje se přes `SendHTTPRequest`, ne přes konektorový `PatchItem`

Konektorová zápisová akce s rozloženým tělem `item/<sloupec>` vyžaduje
parametr `table` jako **GUID natvrdo** — s runtime výrazem se flow naimportuje,
ale nejde zapnout. U sedmi listů by to znamenalo sedm GUID vázaných na jeden
tenant, tedy balík, který se na MPSV nepřenese.

REST adresuje list **interním názvem ze schématu**
(`_api/web/GetList('<cesta webu>/Lists/DilciProcesy')/items`), a ten je na
všech tenantech stejný. Web se bere z proměnné `mpsv_procesnimapaSite`.

Zapisuje se po řádku, ne přes `$batch`: multipart changeset by se v Logic Apps
skládal ručně z hranic a hlaviček a chyba v něm se pozná až za běhu.

### 4. Porovnává se otiskem řádku

Logic Apps neumí uvnitř `Filter array` sáhnout do druhého pole, takže se
z každého řádku poskládá jeden řetězec ze všech sloupců schématu (oddělovač
`|~|`). „Beze změny" je pak `contains()` nad polem otisků.

Otisky se musí počítat **symetricky**: z listu se Choice čte jako objekt a
potřebuje `?['Value']`, ve snímku je už rozbalený a nesmí ho mít. Kdyby se
rozešly, hlásila by obnova změnu u každého řádku a přepsala by celý rejstřík
sama sebou. Brána to hlídá z obou stran.

## Akce (57 nejvyšší úrovně)

```
Vstup            Compose   json(triggerBody()['text'])
Soubor           SP        GetFileContentByPath /Zalohy/<soubor>, inferContentType=false
Snimek           Compose   json(base64ToString($content))
Cesta_webu       Compose   server-relative cesta webu pro REST adresy
Kontrola_verze   If        schema_verze sedí? else -> Odpoved_neshoda + Terminate
Nacti_<list>     SP        GetItems se stránkováním 5000                    ×7
Kody_<list>      Select    kódy v listu                                     ×7
Otisky_<list>    Select    otisky řádků z listu (Choice s ?['Value'])       ×7
KodySnimku_<l>   Select    kódy ve snímku                                   ×7
K_zalozeni_<l>   Filter    ve snímku, v listu ne                            ×7
Ke_zmene_<l>     Filter    v listu je, ale otisk se liší                    ×7
Navic_<list>     Filter    v listu je, ve snímku ne (JEN se hlásí)          ×7
Zapis            If        rezim = zapis -> Zaloz_<l> (POST) + Uprav_<l> (MERGE)
Prehled          Compose   počty za každý list
Odpoved          Response  { stav, hlaseni, porizeno, prehled }
```

Prázdné datum se v těle zápisu posílá jako `json('null')`, ne jako prázdný
řetězec — ten SharePoint u sloupce typu DateTime odmítne a řádek by se
nezapsal.

## Ruční zkouška bez appky

Power Automate → RestoreFlow → **Test → Manually**. Do vstupu vlož:

```json
{"soubor": "rejstrik_2026-09-01_0300.json", "rezim": "nahled"}
```

Běh musí být zelený a `Odpoved` musí vrátit přehled se sedmi listy.
V režimu náhledu **nesmí přibýt ani se změnit jediná položka** — ověř to
tím, že se počty v listech nezměnily.

Teprve pak zkus `"rezim": "zapis"` na datech, o která nejde: smaž pět řádků
z `Aktivity`, spusť obnovu a ověř, že se vrátily s týmiž kódy a vazbami.
**Nikdy poprvé na MPSV.**

## Meze

- Snímek se čte celý do paměti běhu; při dnešní velikosti rejstříku
  (stovky řádků) to není problém, u desetitisíců by se muselo stránkovat.
- Zápis po řádku: šest set řádků je otázka desítek sekund. Appka na dokončení
  nečeká — hlášení potvrzuje spuštění.
- Obnova nesahá na knihovny (`Zalohy`, `Exporty`, `Site Assets`), jen na
  sedm listů schématu.

## Třetí režim: `seznam`

```json
{"rezim": "seznam"}
```

Vrátí názvy snímků v knihovně `Zalohy` v poli `prehled`, oddělené `|#|`. Obrazovka náhledu jimi plní
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

