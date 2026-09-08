<!-- GENEROVÁNO src/make_deploy_ppf.py — needituj ručně.
     Zdroj textu: src/sablona_instalace_ppf.md, čísla z balíku procesnimapa_1_0_0_107.zip. -->

# Instalace balíku `procesnimapa_1_0_0_107.zip`

Postup nasazení na **PPF DEV**. Sedm kroků, každý má vlastní ověření —
dělej je v pořadí a další krok začni, až předchozí ověření projde.

Cílový web:

```
https://ppfbanka.sharepoint.com/sites/DigiData_D/testovaci_subsajta/procesnimapa
```

> **Pro MPSV platí `deploy/mpsv/README.md`**, ne tenhle soubor. Ta složka se
> generuje (`src/make_deploy_mpsv.py`) a je aktuální pro týž balík 1.0.0.107;
> liší se tím, že veze **neanonymizovaná** data a osmý krok navíc.

> **Číselník útvarů je i v téhle sadě skutečný** (`O11`, `Sekce 3`, čísla
> odborů) — od 08.09.2026 anonymizací neprochází. Do té doby měl anonymní kódy
> (`91`, `911`), jenže importní šablona nabízela skutečné, takže kdo ji vyplnil
> podle nabídky, zadal útvary, které v listu `Útvary` nebyly. Anonymní zůstává
> název úřadu, osoby a vnitřní předpisy.

## Pořadí kroků 1 a 2 je závazné

Balík 80 přidal proměnné `mpsv_listHistorieKodu` a `mpsv_listZalohy`. Průvodce
importem se na ně zeptá a nabídne rozbalovátko listů cílového webu. **Když
list `HistorieKodu` nebo knihovna `Zalohy` na webu ještě neexistují, není co
vybrat** — proměnná zůstane prázdná a to shodí napojení **celé** SharePoint
connection, tedy i listů, které s ní nesouvisejí (canvas váže všechny datasety
jedné connection v jednom bloku).

Projeví se to jako `We didn't find any datasets` při spuštění appky a vypadá to
jako vada balíku. Krok 1 obojí zakládá, proto musí být první.

## Co balík obsahuje

| složka | co |
|---|---|
| `CanvasApps/` | canvas app *procesní mapa*, šest obrazovek |
| `Workflows/` | devět flow (viz krok 3) |
| `environmentvariabledefinitions/` | devět proměnných, **bez hodnot** |
| `solution.xml`, `customizations.xml` | manifest a napojení |

Dokumentace v zipu **není** — solution zip nese jen artefakty Power Platform.
Referenční popisy jsou vedle: `sharepoint_schema.md` (listy a knihovny),
`flow_Zaloha.md`, `flow_Restore.md`, `flow_Import.md`, `flow_MapaPublish.md`,
`flow_Export.md`, `flow_Presun.md`,
`flow_AktualizaceKratkehoNazvu.md` (kontrakty flow), `navod_sprava.md`
(jak appku používat), `navod_publikace_mapy.md` (HTML mapa).

---

## 1. Založit listy, sloupce a knihovny

Otevři cílový web, dej **F12 → Console**, vlož celý obsah
`src/setup_sharepoint.js` a spusť.

Skript si web odvodí z adresy stránky, na které běží — žádnou URL v sobě nemá.
Je **idempotentní**: co existuje, nezakládá znovu; co chybí, doplní; sloupce
mimo výchozí zobrazení do něj přidá.

Založí sedm listů, knihovny **`Zalohy`**, **`Exporty`** a **`Import`**
a doplní sloupec
`puvodni_kod` do `Procesy`, `DilciProcesy` a `Aktivity`. Knihovny vznikají
jako BaseTemplate 101, tedy v kořenu webu (`/Zalohy`, `/Exporty`,
`/Import`), ne pod `/Lists/`.

> **Balíky 85, 87 a 99 tenhle krok vyžadují znovu i tam, kde už skript běžel.**
> 85/87: knihovna `Import`, bez které `ImportFlow` spadne na neexistující složce.
> 99: list **`Útvary`** (číselník organizačních útvarů, 44 položek) — appka z něj
> plní nabídku vlastníků a bez něj se formulář číselníku neotevře.
> Skript je idempotentní, takže se nic dalšího nezaloží dvakrát.

**Ověření:** poslední řádek výpisu musí říct, že chybných sloupců je **0**.
V Site contents musí být vidět `Zálohy`, `Exporty`, `Import` a list `Historie kódů`.
Struktura je popsaná v `sharepoint_schema.md`.

## 2. Naimportovat solution a VYPLNIT VŠECH DEVĚT PROMĚNNÝCH

Power Apps → **Solutions → Import solution** → `procesnimapa_1_0_0_107.zip`
(unmanaged, jako upgrade).

Průvodce se zeptá na:

1. **připojení** — connection reference na SharePoint,
2. **devět proměnných**. U `mpsv_procesnimapaSite` zadej adresu webu; zbylých
   osm se pak vybírá **z rozbalovátka listů toho webu** — knihovna `Zálohy`
   je v něm taky, knihovna je pro SharePoint taky list.

| proměnná | zobrazí se jako | vybírá se |
|---|---|---|
| `mpsv_procesnimapaSite` | Procesni mapa - web | web |
| `mpsv_listAgendy` | Procesni mapa - Agendy | list `Agendy` |
| `mpsv_listProcesy` | Procesni mapa - Procesy | list `Procesy` |
| `mpsv_listDilciProcesy` | Procesni mapa - Dilci procesy | list `Dílčí procesy` |
| `mpsv_listAktivity` | Procesni mapa - Aktivity | list `Aktivity` |
| `mpsv_listVazby` | Procesni mapa - Vazby | list `Vazby` |
| `mpsv_listUtvary` | Procesni mapa - Utvary | list `Útvary` |
| `mpsv_listHistorieKodu` | Procesni mapa - Historie kodu | list `Historie kódů` |
| `mpsv_listZalohy` | Procesni mapa - Zalohy | **knihovna** `Zálohy` |

> **Průvodce neproklikávej.** Definice **nemají výchozí hodnotu** schválně:
> s ní by průvodce předvyplnil adresu vývojového webu a import by tiše prošel
> se špatným napojením. Nevyplněná proměnná se neprojeví při importu, ale až
> tím, že flow nejde zapnout — a vypadá to jako chyba balíku.
>
> Prostředí si hodnoty po prvním vyplnění drží, další import už se neptá.
> **Zkontroluj je i tak** (Solutions → Environment variables): balík je nemá
> čím přepsat, ale taky nemá čím doplnit.

**Ověření:** import doběhne bez chyby a v Environment variables má všech devět
proměnných vyplněnou *Current Value*.

## 3. Zapnout flow

**Import stav zapnutí nemění.** Flow, které se jednou nepodařilo zapnout,
zůstane vypnuté i po importu opravené verze. Po importu, který skončil hláškou
„one or more flows may not have turned on", je zapni ručně.

| flow | co dělá | trigger |
|---|---|---|
| `AktualizaceKratkehoNazvu` | zkrácený název aktivity | změna v listu |
| `ExportFlow` | export přehledu do Wordu a Excelu, adresy souborů | z appky |
| `ImportFlow` | hromadné pořízení aktivit z Excelu | z appky |
| `MapaPublishFlow` | publikace HTML mapy se zapečenými daty | z appky |
| `MapaPublishScheduled` | táž publikace | denně 7:00 |
| `PresunFlow` | kaskádový přesun procesu a dílčího procesu | z appky |
| `RestoreFlow` | obnova rejstříku ze snímku | z appky |
| `ZalohaFlow` | snímek rejstříku do knihovny Zalohy | z appky |
| `ZalohaScheduled` | týž snímek | denně 5:00 |

Vypnuté flow se projeví jako chyba **appky**, ne flow: volající canvas app
vidí jen `502 BadGateway / NoResponse` a příčinu z ní poznat nejde.

**Ověření:** všech **devět** má stav *On*.

> **Testovací flow `import new data`** (to, kterým se ověřoval DLP pro
> Excel Online) v balíku 84 **není** — vezlo v sobě natvrdo adresu webu
> PPF. Odebrání z balíku ho ale z prostředí nesmaže: unmanaged solution
> komponenty nemaže. **Smaž ho v Power Automate ručně** (Turn off →
> Delete), ať nezůstane jako sirotek. Spojení na Excel Online zůstává
> a `ImportFlow` ho bude potřebovat.

## 4. Ověřit zálohu — první snímek ručně

`ZalohaScheduled` poběží sám až v 5:00, ale čekat na to nemá smysl. Od balíku
81 na to stačí appka: **Data ▾ → Záloha rejstříku** v horní liště Přehledu
(do balíku 80 to bylo samostatné tlačítko „Záloha"; leželo pod popiskem
s počtem řádků, takže se do něj nedalo pořádně kliknout). Kdo chce appku
obejít, spustí `ZalohaScheduled` v Power Automate přes
**Test → Manually → Run**.

**Ověření — a je důležitější, než vypadá:** běh musí být zelený **a** v knihovně
`Zalohy` musí přibýt soubor `rejstrik_<RRRR-MM-DD_HHMM>.json`. Otevři ho
a zkontroluj, že `listy.DilciProcesy` má **250 položek**, ne 100.

Sto položek by znamenalo, že se nepropsalo stránkování — běh je v tom případě
zelený a snímek je přesto oříznutý. Je to jediná vada zálohy, která se jinak
pozná až ve chvíli, kdy se z ní obnovuje. Kontrakt snímku popisuje
`flow_Zaloha.md`.

## 5. Nahrát soubory do Site Assets

Jen při **prvním** nasazení na daný web, nebo když se některý ze souborů
změnil. Podrobně `navod_publikace_mapy.md`; ve zkratce do knihovny
**Site Assets** přetáhni z `deploy/`:

Do Site Assets patří jen **statické** soubory webu; vyexportované dokumenty
od balíku 82 padají do vlastní knihovny `Exporty` (do 81 se hromadily tady).
Staré `procesni_mapa_<razitko>.doc/.xls/.csv` v Site Assets jde smazat —
appka na ně neodkazuje, adresu dostává vždy z čerstvého běhu flow.

| soubor | k čemu |
|---|---|
| `mapa_template.html` | šablona s kotvami, ze které flow skládá stránku |
| `procesni_mapa.html` | hotová mapa, aby bylo co otevřít, než flow poprvé proběhne |
| `sablona_import_aktivit.xlsx` | prázdný sešit, který appka nabízí ke stažení pod **Data ▾ → Vzorová tabulka pro import** |

Sešit se **musí jmenovat přesně takhle** — `ExportFlow` skládá jeho adresu
z názvu, ne z vyhledání souboru. Sestavit ho ve flow nejde: `.xlsx` je zip
a Logic Apps zip nevyrobí. Generuje ho `python src/make_sablona.py`.

Účet, pod kterým flow běží, potřebuje **Contribute na Site Assets** a na
knihovně `Zalohy`.

**Ověření:** `MapaPublishFlow` doběhne zeleně a `procesni_mapa.html` se
přepíše aktuálním časem. Ke vzorové tabulce stačí, že v knihovně je —
ověří se v kroku 7.

## 6. Otevřít appku ve Studiu a publikovat

Otevři appku v **Power Apps Studiu** → **mikro-změna** (posunout prvek
o pixel a vrátit) → **Save** → **Publish**.

**Není to formalita:** bez toho ostatní vidí pořád předchozí verzi appky,
i když import proběhl. Navíc appka zabalená z YAML se validuje až tady.

Registrace datových zdrojů (`ZalohaFlow`, `HistorieKodu`, knihovna `Zálohy`)
je na **PPF DEV už hotová** a balík 80 ji veze s sebou. **Na jiném prostředí
se dělá znovu** — `FlowNameId` i GUID listů přiděluje až cílové prostředí
a lokálně se dogenerovat nedají. Tam tedy platí: `Add data` → ty tři zdroje →
mikro-změna → Save → Publish → **Export solution** a poslat zip.

**Ověření:** ve Versions je nová verze označená jako *Live*.

## 7. Projít appku

| co zkusit | co má nastat |
|---|---|
| otevřít Přehled | strom se sedmi agendami, počty u větví |
| přidat a odebrat zařazení na obrazovce vazeb | Přehled se po návratu přepočítá |
| Data ▾ → Export do Wordu / do Excelu | soubor se stáhne a přibude v knihovně `Exporty`, ne v Site Assets |
| HTML mapa ▾ → Zobrazit v HTML | otevře se publikovaná mapa |
| **Data ▾ → Vzorová tabulka pro import** | stáhne se `sablona_import_aktivit.xlsx`; v Excelu má list Aktivity jako Tabulku a druhý list Pokyny |
| **Data ▾ → Záloha rejstříku** | hlášení „Záloha spuštěna" a za chvíli přibude soubor v knihovně `Zálohy` |

| **Data ▾ → Import z tabulky** | otevře obrazovku náhledu; v rozbalovátku jsou sešity z knihovny `Import` |
| **Data ▾ → Obnova ze zálohy** | totéž pro snímky z knihovny `Zálohy` |

Co přibylo v balících 95–100 a v předchozím návodu ještě nebylo:

| co zkusit | co má nastat |
|---|---|
| Editace → Procesy → **Přesun** v řádku | otevře obrazovku přesunu; *Spočítat* ukáže náhled dopadu a *Provést* teprve zapíše |
| číselník: pole **vlastníků** u agendy, procesu i dílčího procesu | trojice `nabídka útvarů ▾` + `+` + textové pole; `+` odmítne útvar, který v seznamu už je |
| nabídka útvarů v číselníku | **44 položek** (dřív 7); zdrojem je list `Útvary` |
| **Data ▾ → Vzorová tabulka pro import** | sešit má **12 sloupců** — tři z nich jsou vlastníci nadřazených úrovní |
| pruh voleb na úvodní obrazovce | jeden sjednocený pruh, ne roztroušená tlačítka |

Obojí vede na **jednu obrazovku** (od balíku 87): vyber soubor → Zkontrolovat
→ podívej se, co z toho vyjde → teprve pak Provést. Tlačítko *Provést* je
zhasnuté, dokud pro vybraný soubor neproběhla kontrola, a ještě se ptá.

**Ověření, na kterém záleží:** po *Zkontrolovat* **nesmí v listech přibýt ani
se změnit jediná položka**. Kontrakty obou flow jsou v `flow_Import.md`
a `flow_Restore.md`; spustit se dají i ručně bez appky.

---

## Když se něco nepovede

| příznak | kde je příčina |
|---|---|
| `We didn't find any datasets` při startu appky | nevyplněná Current Value některé proměnné (krok 2) |
| `Flow.Run failed: 502 BadGateway / NoResponse` | vypnuté flow (krok 3) nebo nevyplněná proměnná; pravdu řekne run history, ne hláška v appce |
| flow nejde zapnout | prázdná proměnná, nebo sirotek po starší solution v Default Solution (Turn off → Delete → Publish all customizations) |
| `ZalohaFlow` spadne na neexistující složce | neproběhl krok 1, knihovna `Zalohy` chybí |
| `ExportFlow` spadne na neexistující složce | neproběhl krok 1 po balíku 82, knihovna `Exporty` chybí |
| `ImportFlow` spadne na neexistující složce | neproběhl krok 1 po balíku 85, knihovna `Import` chybí |
| v knihovně `Zálohy` ubývají staré snímky | tak to má být: od balíku 85 se nechává posledních 20; snímek, který chceš udržet, přejmenuj |
| Záloha rejstříku hlásí `502 BadGateway` | `ZalohaFlow` je vypnuté (krok 3) nebo chybí Current Value; pravdu řekne run history |
| Vzorová tabulka: stáhne se stránka s chybou místo sešitu | soubor není v Site Assets, nebo se jmenuje jinak (krok 5) |
| snímek má u `DilciProcesy` přesně 100 položek | nepropsalo se stránkování — nahlas to, je to vada balíku |
| appka ukazuje starou verzi | chybí mikro-změna → Save → Publish (krok 6) |

Sestavení balíku, brány a historii rozhodnutí drží `STATUS.md`.
