# Návrh pořizovací aplikace — Rejstřík agend a procesů MPSV

Canvas app nad SharePoint listy podle `deploy/sharepoint_schema.md`.
Pokrývá FR-2 z `PRD.md`. Verze návrhu 1.1 (20.08.2026) — kaskáda přepsána na dropdowny, viz níže.

## Proč canvas app a ne formulář SharePointu

SharePoint formulář neumí kaskádové číselníky agenda → proces → dílčí proces
ani přiřazení aktivity k více dílčím procesům (M:N přes vazební list).
Obojí je jádro pořizování, takže canvas app je nutná od začátku, ne až později.

## Datové zdroje a jejich objemy

| list | dnes | výhled 06/2028 | jak se s ním pracuje |
|---|---|---|---|
| `Agendy` | 7 | ~10 | kolekce v `App.OnStart` |
| `Procesy` | 46 | ~150 | kolekce v `App.OnStart` |
| `DilciProcesy` | 250 | ~800 | kolekce v `App.OnStart` |
| `Aktivity` | 46 | **tisíce** | **nikdy celé do kolekce** — delegovaný dotaz |
| `AktivitaDilciProces` | 46 | tisíce | delegovaný dotaz podle `aktivita_kod` |

Číselníky se vejdou pod limit delegace (2 000) i v roce 2028, takže se načtou
jednou do kolekcí a kaskáda nad nimi je okamžitá. **Aktivity ne** — u nich musí
zůstat každý dotaz delegovatelný, jinak appka tiše zobrazí jen prvních 2 000
záznamů a bude vypadat, že data chybí.

## Obrazovky

### 1. `scr_Seznam` — seznam aktivit

- Galerie `gal_Aktivity`, položka = jedna aktivita: kód, `nazev_kratky`,
  vykonávající útvar, stav.
- Filtry v hlavičce: sekce, vykonávající útvar, stav, dílčí proces.
- Vyhledávací pole nad názvem.
- Tlačítko „Nová aktivita" → `scr_Detail` v režimu nové položky.

**Delegace — klíčové omezení.** Nad SharePointem jsou delegovatelné `=`, `<>`,
`StartsWith`, `And`, `Or`, `Not` nad indexovanými sloupci. **`Search()` a `in`
delegovatelné nejsou** a nad tisíci aktivitami by tiše ořízly výsledek na 2 000.
Proto:

```
Filter(
    Aktivity,
    IsBlank(txt_Hledat.Text) || StartsWith(nazev_kratky, txt_Hledat.Text),
    IsBlank(txt_Sekce.Text)  || sekce = txt_Sekce.Text,
    IsBlank(txt_Utvar.Text)  || vykonava = txt_Utvar.Text,
    drp_Stav.Selected.Value = "(vše)" || stav.Value = drp_Stav.Selected.Value
)
```

Sekce, útvar i stav jsou **rozbalovací nabídky**, hledání podle názvu zůstává
textové pole (hledá se od začátku názvu, jinak by se ztratila delegace).
Nabídky sekce a útvaru plní `App.OnStart` z `Distinct(Aktivity, …)` do kolekcí
`colSekce` a `colUtvary`, první položka je `(vše)`.

**Vědomý ústupek:** `Distinct` nad `Aktivity` delegovatelný není — nad 2 000
aktivitami přestane být nabídka úplná. Jiný zdroj hodnot dnes neexistuje
(útvary ani sekce nemají číselník), takže je to nejlevnější řešení do doby,
než rejstřík naroste; pak je potřeba založit číselník útvarů. Výjimka je
zapsaná v `src/check_app.py` (`VYJIMKY_DELEGACE`) a kontrola ji při každém
běhu vypíše jako varování, aby se na ni nezapomnělo.

Řazení řeší nabídka „Řadit podle" (kód / název / útvar) přes `SortByColumns`
nad indexovanými sloupci — zůstává delegovatelné. Proto je filtr ve vzorci
třikrát: název sloupce musí být identifikátor, takže se nedá dosadit
proměnnou a každá varianta má vlastní větev `Switch`.

Hledání je tedy **od začátku názvu**, ne „obsahuje". Popisek pole to musí říct
(„Název začíná na…"), jinak uživatel nabude dojmu, že hledání nefunguje.
Fulltext „obsahuje" nad celým rejstříkem umí až publikovaná HTML mapa, která
pracuje se zapečenými daty — v appce by to znamenalo ztrátu delegace.

`Sort` **nepatří do `Gallery.Items`** (počítal by se při každém překreslení) —
řazení řeší výchozí zobrazení listu (`nazev_kratky`, pak `Title`).

### 2. `scr_Detail` — editace jedné aktivity

Rozvržení kopíruje evidenční kartu, aby přechod z Excelu nebolel:

```
Agenda        [kaskádový výběr]      Vlastník agendy        [z číselníku, jen ke čtení]
Proces        [kaskádový výběr]      Vlastník procesu       [z číselníku, jen ke čtení]
Dílčí proces  [kaskádový výběr]      Vlastník dílčího proc. [z číselníku, jen ke čtení]
Aktivita      [víceřádkový text]     Vykonává útvar         [text]
Spolupracuje  [víceřádkový text]     Vnitřní předpis        [víceřádkový text]
Text pro OŘ   [víceřádkový text]     Stav                   [pracovní / schváleno]
Kód           [jen ke čtení, přiděluje se sám]
Další dílčí procesy [seznam vazeb + přidat/odebrat]
```

Vlastníci jsou **jen ke čtení** — patří číselníku, ne aktivitě. Kdyby se dali
přepsat tady, rozešly by se hodnoty mezi listy.

### 3. `scr_Vazby` — přiřazení do dalších dílčích procesů

Modální výběr nad kolekcí dílčích procesů. Zápis do `AktivitaDilciProces`,
klíč `<aktivita_kod>__<dilci_proces_kod>`, `primarni` = `ne`
(primární vazba je ta z pole `dilci_proces_kod` na aktivitě).

## `App.OnStart`

```
Concurrent(
    ClearCollect(colAgendy,  ShowColumns(Agendy,           Title, nazev, vlastnik)),
    ClearCollect(colProcesy, ShowColumns(Procesy,          Title, nazev, agenda_kod, vlastnik)),
    ClearCollect(colDilci,   ShowColumns('Dílčí procesy',  Title, nazev, proces_kod, vlastnik))
)
```

Názvy sloupců jsou **identifikátory, ne řetězce** — appka běží s příznakem
`supportcolumnnamesasidentifiers` (`Properties.json` v `.msapp`). S řetězci
`ShowColumns` neprojde, kolekce zůstanou bez schématu a všechny vzorce, které
se na jejich sloupce odkazují, spadnou na „Name isn't valid". Totéž platí pro
`Search()`. Výběr sloupců není kosmetika: bez něj se tahají celé záznamy
včetně systémových polí a načtení se zbytečně prodlouží.

## Kaskáda číselníků

Tři `Classic/DropDown`, položky se skládají jako **`kód · název`**:

```
drp_Agenda.Items = Distinct(colAgendy, Title & " · " & nazev)
drp_Proces.Items = Distinct(Filter(colProcesy, agenda_kod = Left(drp_Agenda.Selected.Value, 2)),
                            Title & " · " & nazev)
drp_Dilci.Items  = Distinct(Filter(colDilci,   proces_kod = Left(drp_Proces.Selected.Value, 5)),
                            Title & " · " & nazev)
```

Filtruje se nad **kolekcemi**, ne nad zdrojem — proto tu delegace nehraje roli.
Při změně agendy se musí vyresetovat proces i dílčí proces (`Reset()`), jinak
zůstane viset nekonzistentní kombinace.

**Proč dropdown a ne combobox** (rozhodnuto 20.08.2026 po neúspěšném importu):
`Classic/ComboBox` má vlastnost `SearchItems` označenou v šabloně jako
`hidden="true"` — Studio si ji dopočítává, když zdroj navážeš v návrháři,
ale **z YAML ji nastavit nejde** (packer skončí `PA2108`). Nenastavená přitom
dědí výchozí hodnotu `Search(ComboBoxSample, Self.SearchText, Value1)`, která
míří na ukázková data, takže appka po importu hlásí „Name isn't valid".
Z YAML je tedy tenhle control nepoužitelný v obou variantách.

Ztráta je malá: kaskáda zúží nabídku na jednotky položek (procesy v agendě,
dílčí procesy v procesu), takže se hledání šeptem nechybí. Fulltext nad celým
rejstříkem obstarává seznam aktivit a obrazovka vazeb.

**Proč `Distinct` a proč `kód · název`:** klasický dropdown si zobrazovaný
sloupec drží ve vlastnosti `Value` **vnořené uvnitř `Items`**, a ta se z YAML
nastavit taky nedá. `Distinct()` vrací jednosloupcovou tabulku se sloupcem
pojmenovaným přesně `Value`, takže se vazba trefí sama. Kód v textu je pak
jediné, co spolehlivě vede zpátky na záznam — čte se pevnou délkou
(`Left(…, 2)` agenda, `5` proces, `9` dílčí proces), protože kódy
`AA-BB-CCC-DDDD` mají pevnou šířku. Vlastníci se dohledávají `LookUp`
nad kolekcí podle téhož kódu.

`AllowEmptySelection = true` je u všech tří povinné: bez něj dropdown vybere
první položku sám a nová aktivita by tiše vznikla pod prvním dílčím procesem
v seznamu.

## Přidělení kódu aktivity

Kód `AA-BB-CCC-DDDD` vzniká z vybraného dílčího procesu a prvního volného
čtyřčíslí. Musí se počítat **nad zdrojem, delegovaně**, ne nad kolekcí:

```
Set(varPrefix, Left(drp_Dilci.Selected.Value, 9) & "-");
Set(varPosledni,
    First(
        Sort(
            Filter(Aktivity, StartsWith(Title, varPrefix)),
            Title, Descending
        )
    ).Title
);
Set(varNovyKod,
    varPrefix & Right("000" & (Value(Right(varPosledni, 4)) + 1), 4)
)
```

`StartsWith` nad indexovaným `Title` je delegovatelný, takže to funguje i při
tisících aktivit. Prázdný dílčí proces dá `varPosledni` prázdné a kód `0001`.

**Souběh dvou správců** může přidělit stejný kód. Před zápisem proto kontrola
existence a při kolizi nové přečtení:

```
If(!IsBlank(LookUp(Aktivity, Title = varNovyKod)),
   Notify("Kód " & varNovyKod & " mezitím někdo použil, zkus uložit znovu.",
          NotificationType.Warning),
   /* jinak Patch */
)
```

## Zápis

```
IfError(
    Patch(Aktivity, dRec,
        {
            Title:            varNovyKod,
            nazev:            txt_Nazev.Text,
            nazev_kratky:     Left(txt_Nazev.Text, 150),
            dilci_proces_kod: Left(drp_Dilci.Selected.Value, 9),
            vykonava:         txt_Utvar.Text,
            spolupracuje:     txt_Spolupracuje.Text,
            vnitrni_predpis:  txt_Predpis.Text,
            text_pro_or:      txt_TextOR.Text,
            sekce:            txt_Sekce.Text,
            stav:             { Value: drp_StavDetail.Selected.Value },
            datum_aktualizace: Now()
        }
    ),
    Notify("Uložení selhalo: " & FirstError.Message, NotificationType.Error)
)
```

**`nazev_kratky` je zjednodušené** — `Left(...,150)` řeže i uprostřed slova,
zatímco import zkracuje na hranici slova a doplňuje výpustku. Srovnání zajistí
pojistné flow `AktualizaceKratkehoNazvu` (`PLAN.md` krok 9b), které hodnotu
po zápisu přepíše na kanonický tvar. Appka tedy nemusí logiku zkracování
duplikovat — jen nesmí pole nechat prázdné, protože se podle něj řadí.

## Vazba na dílčí procesy při uložení

Uložení aktivity zakládá i **primární vazbu** do `AktivitaDilciProces`
(`primarni` = Choice `ano`, zapisuje se `{ Value: "ano" }`), a při změně
dílčího procesu ji přepíše. Bez toho by se appka rozešla s daty importu,
kde má primární vazbu každá ze 46 aktivit — a mapa by aktivitu ve větvi
neukázala.

## Referenční integrita

Vazby nesou textové kódy, ne lookup ID (kvůli přenositelnosti mezi tenanty).
Platforma je proto **nehlídá** — hlídat je musí appka:

- dílčí proces jde vybrat jen z kaskády, takže `dilci_proces_kod` nemůže
  ukázat mimo číselník,
- před zápisem vazby kontrola, že aktivita i dílčí proces existují,
- smazání aktivity musí smazat i její vazby (jinak zůstanou sirotci ve
  vazebním listu a mapa je zobrazí jako prázdné větve).

## Co se v této fázi NEDĚLÁ

- Schvalovací workflow s notifikacemi — `stav` je zatím jen pole (PRD §7).
- Správa číselníků agend/procesů/dílčích procesů z appky. Zakládají se importem;
  nové položky přidává správce procesního rámce přímo v listu. Kdyby se
  zakládaly z appky, musela by řešit i přidělování kódů `AA` / `BB` / `CCC`
  a jejich zmrazení — to dnes drží `kody.json` na straně skriptů.

## Jak se to ověří

1. **Kaskáda** — vyber agendu 01, nabídka procesů musí mít právě ty s
   `agenda_kod = 01`; po změně agendy musí být proces i dílčí proces prázdný.
2. **Přidělení kódu** — pro dílčí proces s aktivitami `0001` a `0002` musí
   vzorec vrátit `0003`; pro dílčí proces bez aktivit `0001`.
3. **Delegace** — do listu nahrát >2 000 testovacích aktivit a ověřit, že
   filtr útvaru vrátí správný počet (ne přesně 2 000) a že Power Apps Studio
   nehlásí modrou vlnovku u vzorců galerie.
4. **M:N** — aktivitu přiřadit do druhého dílčího procesu; musí se objevit
   v obou větvích mapy a ve vazebním listu přibude právě jeden řádek.
5. **Kolize kódu** — ve dvou oknech appky založit aktivitu ve stejném dílčím
   procesu; druhé uložení musí skončit srozumitelným hlášením, ne přepsáním.
6. **Referenční integrita** — smazat aktivitu a ověřit, že ve vazebním listu
   nezůstal žádný řádek s jejím kódem.

## Rizika

- **Delegace u aktivit** je jediné místo, kde se objem projeví tvrdě a tiše.
  Bod 3 ověření se nesmí odkládat na dobu, kdy už bude v listu 5 000 řádků.
- **Souběžné pořizování** — kontrola před zápisem kolizi zmenší, ale
  neodstraní. Skutečné řešení (rezervace čísla) je nad rámec této fáze;
  při dvou až třech správcích na sekci je riziko přijatelné.
- **`nazev_kratky` prázdné** rozbije řazení výchozího zobrazení. Appka ho
  musí plnit vždy, i když ho flow později přepíše.
