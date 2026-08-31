# Instalace balíku `procesnimapa_1_0_0_76.zip`

Postup nasazení na **PPF DEV**. Sedm kroků, každý má vlastní ověření —
dělej je v pořadí a další krok začni, až předchozí ověření projde.

Cílový web:

```
https://ppfbanka.sharepoint.com/sites/DigiData_D/testovaci_subsajta/procesnimapa
```

> **Pro MPSV platí `deploy/mpsv/README.md`**, ne tenhle soubor. MPSV běží na
> 1.0.0.65 a jeho složka je snímek k té verzi; přegeneruje se, až bude přístup
> do tenantu.

## Pořadí kroků 1 a 2 je závazné

Balík 76 přidal osmou proměnnou prostředí `mpsv_listHistorieKodu`. Průvodce
importem se na ni zeptá a nabídne rozbalovátko listů cílového webu. **Když
list `HistorieKodu` na webu ještě neexistuje, není co vybrat** — proměnná
zůstane prázdná a to shodí napojení **celé** SharePoint connection, tedy
i listů, které s ní nesouvisejí (canvas váže všechny datasety jedné connection
v jednom bloku).

Projeví se to jako `We didn't find any datasets` při spuštění appky a vypadá to
jako vada balíku. Krok 1 ten list zakládá, proto musí být první.

## Co balík obsahuje

| složka | co |
|---|---|
| `CanvasApps/` | canvas app *procesní mapa*, čtyři obrazovky |
| `Workflows/` | šest flow (viz krok 4) |
| `environmentvariabledefinitions/` | osm proměnných, **bez hodnot** |
| `solution.xml`, `customizations.xml` | manifest a napojení |

Dokumentace v zipu **není** — solution zip nese jen artefakty Power Platform.
Referenční popisy jsou vedle: `sharepoint_schema.md` (listy a knihovna),
`flow_Zaloha.md`, `flow_MapaPublish.md`, `flow_Export.md`,
`flow_AktualizaceKratkehoNazvu.md` (kontrakty flow), `navod_sprava.md`
(jak appku používat), `navod_publikace_mapy.md` (HTML mapa).

---

## 1. Založit listy, sloupce a knihovnu

Otevři cílový web, dej **F12 → Console**, vlož celý obsah
`src/setup_sharepoint.js` a spusť.

Skript si web odvodí z adresy stránky, na které běží — žádnou URL v sobě nemá.
Je **idempotentní**: co existuje, nezakládá znovu; co chybí, doplní; sloupce
mimo výchozí zobrazení do něj přidá.

Založí sedm listů, **knihovnu `Zalohy`** a doplní sloupec `puvodni_kod`
do `Procesy`, `DilciProcesy` a `Aktivity`. Knihovna vzniká jako BaseTemplate
101, tedy v kořenu webu (`/Zalohy`), ne pod `/Lists/`.

**Ověření:** poslední řádek výpisu musí říct, že chybných sloupců je **0**.
V knihovně Site contents musí být vidět `Zálohy` a list `Historie kódů`.
Struktura je popsaná v `sharepoint_schema.md`.

## 2. Naimportovat solution a VYPLNIT VŠECH OSM PROMĚNNÝCH

Power Apps → **Solutions → Import solution** → `procesnimapa_1_0_0_76.zip`
(unmanaged, jako upgrade).

Průvodce se zeptá na:

1. **připojení** — connection reference na SharePoint,
2. **osm proměnných**. U `mpsv_procesnimapaSite` zadej adresu webu; zbylých
   sedm se pak vybírá **z rozbalovátka listů toho webu**.

| proměnná | zobrazí se jako | vybírá se |
|---|---|---|
| `mpsv_procesnimapaSite` | Procesni mapa - web | web |
| `mpsv_listAgendy` | Procesni mapa - Agendy | list `Agendy` |
| `mpsv_listProcesy` | Procesni mapa - Procesy | list `Procesy` |
| `mpsv_listDilciProcesy` | Procesni mapa - Dilci procesy | list `Dílčí procesy` |
| `mpsv_listAktivity` | Procesni mapa - Aktivity | list `Aktivity` |
| `mpsv_listVazby` | Procesni mapa - Vazby | list `Vazba aktivita–dílčí proces` |
| `mpsv_listUtvary` | Procesni mapa - Utvary | list `Útvary` |
| `mpsv_listHistorieKodu` | Procesni mapa - Historie kodu | list `Historie kódů` |

> **Průvodce neproklikávej.** Definice **nemají výchozí hodnotu** schválně:
> s ní by průvodce předvyplnil adresu vývojového webu a import by tiše prošel
> se špatným napojením. Nevyplněná proměnná se neprojeví při importu, ale až
> tím, že flow nejde zapnout — a vypadá to jako chyba balíku.
>
> Prostředí si hodnoty po prvním vyplnění drží, další import už se neptá.
> **Zkontroluj je i tak** (Solutions → Environment variables): balík je nemá
> čím přepsat, ale taky nemá čím doplnit.

**Ověření:** import doběhne bez chyby a v Environment variables má všech osm
proměnných vyplněnou *Current Value*.

## 3. Zapnout flow

**Import stav zapnutí nemění.** Flow, které se jednou nepodařilo zapnout,
zůstane vypnuté i po importu opravené verze. Po importu, který skončil hláškou
„one or more flows may not have turned on", je zapni ručně.

| flow | co dělá | trigger |
|---|---|---|
| `MapaPublishFlow` | publikace HTML mapy | z appky |
| `MapaPublishScheduled` | táž publikace | denně 7:00 |
| `ExportFlow` | export přehledu do Wordu a Excelu | z appky |
| `AktualizaceKratkehoNazvu` | zkrácený název aktivity | změna v listu |
| `ZalohaFlow` | **nové** — snímek rejstříku do `Zalohy` | z appky |
| `ZalohaScheduled` | **nové** — týž snímek | denně 5:00 |

Vypnuté flow se projeví jako chyba **appky**, ne flow: volající canvas app
vidí jen `502 BadGateway / NoResponse` a příčinu z ní poznat nejde.

**Ověření:** všech šest má stav *On*.

## 4. Ověřit zálohu — první snímek ručně

`ZalohaScheduled` poběží sám až v 5:00, ale čekat na to nemá smysl.

Power Automate → `ZalohaScheduled` → **Test → Manually → Run**.

**Ověření — a je důležitější, než vypadá:** běh musí být zelený **a** v knihovně
`Zalohy` musí přibýt soubor `rejstrik_<RRRR-MM-DD_HHMM>.json`. Otevři ho
a zkontroluj, že `listy.DilciProcesy` má **250 položek**, ne 100.

Sto položek by znamenalo, že se nepropsalo stránkování — běh je v tom případě
zelený a snímek je přesto oříznutý. Je to jediná vada zálohy, která se jinak
pozná až ve chvíli, kdy se z ní obnovuje. Kontrakt snímku popisuje
`flow_Zaloha.md`.

## 5. Nahrát soubory mapy do Site Assets

Jen při **prvním** nasazení na daný web, nebo když se změnila šablona.
Podrobně `navod_publikace_mapy.md`; ve zkratce do knihovny **Site Assets**
přetáhni z `deploy/`:

| soubor | k čemu |
|---|---|
| `mapa_template.html` | šablona s kotvami, ze které flow skládá stránku |
| `procesni_mapa.html` | hotová mapa, aby bylo co otevřít, než flow poprvé proběhne |

Účet, pod kterým flow běží, potřebuje **Contribute na Site Assets** a na
knihovně `Zalohy`.

**Ověření:** `MapaPublishFlow` doběhne zeleně a `procesni_mapa.html` se
přepíše aktuálním časem.

## 6. Zaregistrovat nové zdroje ve Studiu a publikovat

Tenhle krok **za tebe udělat nejde** — registrace datového zdroje vzniká jen
ve Studiu. `FlowNameId` i GUID listu přiděluje cílové prostředí a lokálně se
dogenerovat nedají.

Otevři appku v **Power Apps Studiu**:

1. **Add data → `ZalohaFlow`** — bez toho nejde do appky napsat tlačítko
   „Pořídit zálohu",
2. **Add data → `HistorieKodu`** — bez toho nejde zapisovat zánik kódu,
3. **mikro-změna** (posunout prvek o pixel a vrátit) → **Save** → **Publish**,
4. **Export solution** (unmanaged) a ten zip pošli — navazuje na něj další
   balík.

**Mikro-změna a Publish nejsou formalita:** bez nich ostatní vidí pořád
předchozí verzi appky, i když import proběhl.

**Ověření:** v Data appky jsou vidět oba nové zdroje a ve Versions je nová
verze označená jako *Live*.

## 7. Projít appku

| co zkusit | co má nastat |
|---|---|
| otevřít Přehled | strom se sedmi agendami, počty u větví |
| přidat a odebrat zařazení na obrazovce vazeb | Přehled se po návratu přepočítá |
| Export → Word / Excel | soubor se stáhne |
| Zobrazit v HTML | otevře se publikovaná mapa |

---

## Když se něco nepovede

| příznak | kde je příčina |
|---|---|
| `We didn't find any datasets` při startu appky | nevyplněná Current Value některé proměnné (krok 2) |
| `Flow.Run failed: 502 BadGateway / NoResponse` | vypnuté flow (krok 3) nebo nevyplněná proměnná; pravdu řekne run history, ne hláška v appce |
| flow nejde zapnout | prázdná proměnná, nebo sirotek po starší solution v Default Solution (Turn off → Delete → Publish all customizations) |
| `ZalohaFlow` spadne na neexistující složce | neproběhl krok 1, knihovna `Zalohy` chybí |
| snímek má u `DilciProcesy` přesně 100 položek | nepropsalo se stránkování — nahlas to, je to vada balíku |
| appka ukazuje starou verzi | chybí mikro-změna → Save → Publish (krok 6) |

Sestavení balíku, brány a historii rozhodnutí drží `STATUS.md`.
