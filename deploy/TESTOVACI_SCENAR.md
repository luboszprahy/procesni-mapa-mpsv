# Testovací scénář — balík 1.0.0.96

Prochází se shora dolů. Bloky **A–E** testují sirotčí aktivity (přišly
s balíkem 92), **F–H** kaskádový přesun (93) a jeho napojení na aplikaci,
**I–J** plný přesun z aplikace.

**Zkouší se balík 96** — starší se přeskočí. V 94 měla appka chybný vzorec
(`Patch` nad zdrojem, který zrovna prochází `ForAll`) a Studio ji označilo
červeně; v 95 padal první ostrý běh `PresunFlow` na `substring` (viz blok F).
96 opravuje obojí: blok **D** je test prvního, blok **F** druhého.

**Pruh filtrů se změnil.** Stav, osiřelé, nezařazené i přepínač kódu jsou
v jedné rolovací nabídce **Stav: … ▾**; pruh má nově čtyři prvky místo devíti.

Každý krok má **co udělat** a **co musí nastat**. Kde je uvedeno „NESMÍ",
je to past, kvůli které ten krok existuje — projít bez povšimnutí se nedá.

---

## Než začneš

- [ ] **0.1** Pořiď zálohu rejstříku: appka → **Data ▾ → Záloha**.
      Bloky D, E a I data **mění** a záloha je jediná cesta zpět.
- [ ] **0.2** Zapiš si dnešní počty z přehledu (karty nahoře):
      AGENDY ___ · PROCESY ___ · DÍLČÍ PROCESY ___ · AKTIVITY ___.
      Budeš je porovnávat po každém zápisu.
- [ ] **0.3** Připrav si sešit pro blok C: stáhni **Data ▾ → Vzorová tabulka**,
      vyplň **jeden** řádek — jen sloupce *Název aktivity* a *Vykonává útvar*,
      **dílčí proces nech prázdný**. Ulož a nahraj do knihovny `Import`.

> **Citlivostní štítek.** Když sešit uložíš v desktop Excelu, může dostat
> štítek, který soubor šifruje, a import pak spadne na
> `403 OpenWorkbookAccessDenied` („Nemáte oprávnění k otevření tohoto
> souboru"). Štítek **„Interní" projde**, přísnější ne. Když na to narazíš,
> přeštítkuj sešit — není to chyba importu.

---

## A. Import balíků a otevření aplikace

- [ ] **A.1** Power Apps → Solutions → Import solution → `procesnimapa_1_0_0_92.zip`
      jako **upgrade**. → Import doběhne bez chyby.
- [ ] **A.2** Totéž s `procesnimapa_1_0_0_93.zip`. → Doběhne bez chyby.

> Pokud import skončí hláškou „one or more flows may not have turned on",
> **flow ručně zapni** (blok F.1). Import stav zapnutí nemění.

- [ ] **A.3** Otevři aplikaci **ve Studiu** (Edit). → Otevře se **bez** dialogu
      `Error opening file`.

> Tohle je kontrola, kterou nelze přeskočit: `.msapp` zabalený z YAML se
> validuje teprve tady. Import může projít zeleně i u appky, kterou Studio
> neotevře.

- [ ] **A.4** Udělej mikro-změnu (posuň libovolný prvek o pixel a zpět),
      **Save** a **Publish**.
- [ ] **A.5** Spusť appku a najeď myší na název „Procesní mapa MPSV" v pruhu
      nahoře. → Nápověda ukazuje **verzi 1.0.0.93**.

> Když ukazuje starší číslo nebo se neukáže vůbec, neproběhl krok A.4 a běží
> pořád stará publikovaná verze — všechno ostatní by se testovalo naslepo.

- [ ] **A.6** Přehled se načte, strom se zobrazí, karty nahoře ukazují čísla.

---

## B. Technická větev „Nezařazeno" je schovaná

Provisioning zakládá agendu `00`, proces `00-00` a dílčí proces `00-00-000`
s názvem „Nezařazeno". Jsou to technické položky, pod kterými čekají holé
aktivity — v rejstříku se ale tvářit jako běžná agenda nesmějí.

- [ ] **B.1** Přehled → karta **AGENDY**. → Číslo je **o jednu menší** než
      počet položek v listu `Agendy` na SharePointu.
- [ ] **B.2** Rozbal strom na první úroveň. → Agenda `00 Nezařazeno`
      ve stromu **NENÍ**.
- [ ] **B.3** Do pole *Hledat v celém rejstříku* napiš `Nezařazeno`.
      → Nenajde **žádnou** technickou položku (`00`, `00-00`, `00-00-000`).

> B.3 je nález z auditu balíku 92: hledání technickou větev nefiltrovalo,
> a protože se ty položky jmenují doslova „Nezařazeno", vracelo je jako
> běžné — a přes export šly dál do dokumentu.

- [ ] **B.4** Vymaž hledání. Přejdi na **Editace** (číselník) → přepni na
      úroveň **Agendy**. → `00 Nezařazeno` v seznamu **NENÍ**.
- [ ] **B.5** Tamtéž → úroveň **Procesy** → v seznamu není `00-00`;
      úroveň **Dílčí procesy** → není `00-00-000`.
- [ ] **B.6** V číselníku dej **Nová položka** na úrovni *Proces* a rozbal
      nabídku *Agenda*. → `00 Nezařazeno` se **nenabízí**.
- [ ] **B.7** Přehled → **Data ▾ → Export do Wordu**. → V dokumentu není
      žádná zmínka o „Nezařazeno".

---

## C. Chip nezařazených aktivit

- [ ] **C.1** Přehled → **Data ▾ → Import**. Vyber sešit z kroku 0.3
      a dej **Zkontrolovat**. → Náhled hlásí **1 k založení**, z toho
      **1 bez zařazení**, 0 chyb.
- [ ] **C.2** Dej **Provést import**. → Hlášení o úspěchu.
- [ ] **C.3** Vrať se na přehled a rozbal nabídku **Stav ▾**. → Je v ní
      volba **„nezařazené (1)"**.

> Ta volba je jediná cesta, jak se k nezařazeným aktivitám dostat: mají rodiče
> `00-00-000`, takže **nejsou osiřelé** a volba „osiřelé" je neukáže — a ve
> stromu nejsou, protože větev `00` je schovaná (blok B).

- [ ] **C.4** Vyber ji. → Nabídka se **zavře**, strom se přepne na **plochý
      seznam** a je v něm ta jedna aktivita s kódem `00-00-000-0001`.
- [ ] **C.5** Popisek tlačítka nabídky nese **„· nezařazené"**, takže je
      z pruhu poznat, že filtr běží. Vpravo v hlavičce tabulky stojí
      **„1 nezařazených · plochý seznam"**.
- [ ] **C.6** Nabídka → **„osiřelé"**. → Nezařazené se **vypnou**
      (režimy se vylučují) a seznam se změní na osiřelé položky.
- [ ] **C.7** Nabídka → **„nezařazené"** znovu, pak ještě jednou (vypnutí).
      → Strom se vrátí do normálu a popisek je zase jen **„Stav: vše"**.
- [ ] **C.8** Nabídka → **„zobrazit kód"**. → Sloupec s kódy zmizí a názvy
      se posunou doleva; hledání podle kódu funguje dál. Vrať ho zpátky.
- [ ] **C.9** Klikni vedle otevřené nabídky (kamkoli do plochy). → Nabídka
      se zavře, aniž by se cokoli přepnulo.

---

## D. Přiřazení sirotka  *(mění data)*

> Tohle je zároveň test opravy z balíku 95: uložení přepisuje vazby aktivity
> a v 94 na tom Studio hlásilo *„This function cannot operate on the same data
> source that is used in ForAll"*. Když uložení projde a vazby sedí, je oprava
> potvrzená.

- [ ] **D.1** Zapni chip nezařazených a klikni na aktivitu `00-00-000-0001`.
      → Otevře se detail.
- [ ] **D.2** Zapiš si její kód: `00-00-000-0001`.
- [ ] **D.3** Pole **Agenda**, **Proces** i **Dílčí proces** jsou
      **editovatelná** (ne šedá).
- [ ] **D.4** Vyber agendu → proces → dílčí proces (libovolné skutečné).
      Nabídka se po každém výběru zúží na potomky.
- [ ] **D.5** Dej **Uložit**. → Hláška **„Uloženo jako AA-BB-CCC-DDDD"**
      s **novým** kódem odpovídajícím vybranému dílčímu procesu.

> Kdyby hláška ukazovala pořád `00-00-000-0001`, přečíslování neproběhlo
> a aktivita by visela v dílčím procesu, do kterého podle kódu nepatří.

Kontrola v datech (SharePoint, list `Aktivity`):

- [ ] **D.6** Řádek s **novým** kódem existuje.
- [ ] **D.7** Má vyplněný sloupec **`puvodni_kod` = `00-00-000-0001`**.
- [ ] **D.8** Řádek se starým kódem `00-00-000-0001` už **neexistuje**.

Kontrola vazeb (list `Vazba aktivita–dílčí proces`):

- [ ] **D.9** Existuje vazba `<nový kód>__<nový dílčí proces>`,
      `primarni = ano`.
- [ ] **D.10** Na starý kód `00-00-000-0001` **neukazuje žádná** vazba.

Kontrola historie (list `HistorieKodu`):

- [ ] **D.11** **NEPŘIBYL** žádný řádek.

> Tohle je záměr, ne opomenutí: kód `00-00-000-XXXX` nikdy platným kódem
> nebyl — je to provizorium do chvíle, než správce řekne, kam aktivita patří.
> Zapisovat každého sirotka do historie by ji zaplnilo doklady o ničem.

- [ ] **D.12** Zpět na přehled. → Chip ukazuje **„nezařazené (0)"**
      a **zůstává vidět**, dokud je režim zapnutý.

> Kdyby zmizel hned, strom by zůstal prázdný a nebyla by cesta zpátky.

- [ ] **D.13** Vypni chip. → Chip zmizí úplně (žádní sirotci nezbyli).
- [ ] **D.14** Najdi aktivitu ve stromu pod novým dílčím procesem. → Je tam,
      **jednou**, s novým kódem.

---

## E. Zámek kaskády u aktivity s platným kódem

- [ ] **E.1** Otevři **jinou** aktivitu — takovou, která má normální kód
      (ne `00-00-000-…`).
- [ ] **E.2** Pole **Agenda**, **Proces** i **Dílčí proces** jsou
      **jen ke čtení** (nejdou rozbalit).

> Zamčená je celá trojice, ne jen dílčí proces. Se zamčeným posledním polem
> by změna agendy vynulovala výběr níž a aktivita by pak nešla uložit vůbec.
> Do doby, než bude hotový přesun aktivity (F10/2), je zámek jediná obrana
> proti tomu, aby se u ní tiše přepsalo zařazení a kód zůstal starý.

- [ ] **E.3** Změň **Znění aktivity**, **Vykonává útvar** a **Stav**,
      dej **Uložit**. → Uloží se bez potíží, kód se **nemění**.

> E.3 je kontrola, že zámek nezablokoval běžnou editaci.

---

## F. PresunFlow samostatně — bez aplikace

> Tady spadl první ostrý běh (04.09.2026): `substring` na položce, jejíž kód
> JE přesouvaný kód, protože Logic Apps chtějí start index **menší** než
> délka řetězce. Balík 96 to počítá bez `substring` přes okraj, takže krok
> F musí projít zeleně až do konce.

Tenhle blok se dá projít hned, ještě než je flow zaregistrované v appce.
Otestuje se tím výpočet kaskády na skutečných datech dřív, než k ní pustíš
uživatelské rozhraní.

- [ ] **F.1** Power Automate → prostředí DEV → **PresunFlow** → pokud je
      vypnuté, dej **Turn on**.
- [ ] **F.2** Vyber v rejstříku **skutečný proces**, který má aspoň dva dílčí
      procesy a několik aktivit. Zapiš si jeho kód: ______
      a kód **cílové agendy**, kam by šel: ______
- [ ] **F.3** PresunFlow → **Test → Manually → Test** → do pole `pozadavek`
      vlož (kód a cíl vyměň za své):

```json
{"kod":"07-08","uroven":"proces","cil":"03","duvod":"zkouška","rezim":"nahled"}
```

- [ ] **F.4** Běh doběhne **zeleně**.
- [ ] **F.5** Otevři krok **`Novy_prefix`** → OUTPUTS. → Je to kód tvaru
      `<cílová agenda>-NN`, kde `NN` je **první volné** číslo v té agendě.
- [ ] **F.6** Otevři krok **`Odpoved_nahled`** → v těle je `prehled`
      se seznamem dvojic oddělených `|~|` a `|#|`.
- [ ] **F.7** Spočítej řádky přehledu. → Musí jich být přesně
      **1 + (počet dílčích procesů) + (počet aktivit pod nimi)**.
- [ ] **F.8** Zkontroluj v přehledu **jeden konkrétní** dílčí proces
      a **jednu** aktivitu:
      `AA-BB-CCC` → `<nový prefix>-CCC` a
      `AA-BB-CCC-DDDD` → `<nový prefix>-CCC-DDDD`.
      → **CCC i DDDD se NEMĚNÍ**, mění se jen prefix.

> Tohle je jádro celého návrhu: přečísluje se jen ta úroveň, která se stěhuje.
> Kdyby se změnilo i `CCC` nebo `DDDD`, mapa i vazby by se rozpadly.

- [ ] **F.9** SharePoint → list `Procesy`, `DilciProcesy`, `Aktivity`,
      `AktivitaDilciProces`, `HistorieKodu`. → **Nic se nezměnilo.**

> Režim `nahled` nesmí zapsat ani řádek. Kdyby se cokoli změnilo, je vadná
> podmínka `Je_nahled` a **dál se nesmí pokračovat**.

Nepovinné, ale doporučené — zkouška úrovně níž:

- [ ] **F.10** Spusť znovu s `"uroven":"dilci_proces"`, `kod` = kód dílčího
      procesu a `cil` = kód **procesu**. → `Novy_prefix` má tvar `AA-BB-CCC`
      a v přehledu jsou jen ten dílčí proces a jeho aktivity — **žádné cizí
      dílčí procesy**.

---

## G. Obrazovka přesunu — vstup, nabídky, zámek náhledu

Nic nezapisuje: končí u zhasnutého tlačítka *Provést přesun*.

- [ ] **G.1** Editace (číselník) → úroveň **Procesy**. → V každém řádku je
      vedle koše **ikona přesunu**.
- [ ] **G.2** Úroveň **Agendy**. → Ikona přesunu tam **NENÍ** (agenda nemá
      kam) a u **Aktivit** taky ne (ty se přesouvají ve svém detailu).
- [ ] **G.3** Klikni na ikonu u nějakého procesu. → Otevře se obrazovka
      **„Přesun procesu pod jinou agendu"** a nahoře je kód a název toho
      procesu, vpravo počty dílčích procesů a aktivit pod ním.
- [ ] **G.4** Dole **NENÍ** žádné upozornění o registraci toku — v balíku 95
      obrazovka funguje naostro. (V 93 tam bylo, teď by lhalo.)
- [ ] **G.5** Rozbal nabídku **Cílová agenda**. → Jsou v ní agendy
      **kromě** `00 Nezařazeno`.
- [ ] **G.6** Tlačítko **Provést přesun** je **šedé** (náhled neproběhl).
- [ ] **G.7** Vyplň cíl, **důvod nech prázdný**. → *Spočítat náhled* zůstane
      šedé; důvod je povinný, protože se zapíše ke každému uzavřenému kódu.
- [ ] **G.8** Šipkou zpět se vrať. → Jsi v číselníku, nic se nezměnilo.

---

## H. Aplikace volá flow  *(nezapisuje)*

- [ ] **H.1** Znovu otevři přesun u procesu, vyplň **cíl i důvod**
      a dej **Spočítat náhled**.
- [ ] **H.2** → Během pár sekund se objeví tabulka **UZAVŘE SE / VZNIKNE**
      přes celý podstrom a vpravo nahoře **nový kód**. Žádná hláška
      o neregistrovaném toku.
- [ ] **H.3** Zkontroluj v Power Automate historii běhů `PresunFlow`. →
      Poslední běh je **zelený** a v jeho vstupu je `"rezim":"nahled"`.
- [ ] **H.4** Ověř, že se **nic nezapsalo**: karty na přehledu mají tytéž
      počty jako v kroku 0.2.
- [ ] **H.5** Změň **cílovou agendu** na jinou. → Tabulka náhledu zmizí
      a *Provést přesun* zešedne. To je ta pojistka proti zápisu podle
      čísel spočítaných pro jiného rodiče.

---

## I. Plný přesun z aplikace  *(mění data)*

- [ ] **I.1** Před začátkem si zapiš stav cílové agendy: kolik má procesů
      a jaký je nejvyšší kód: ______
- [ ] **I.2** Číselník → ikona přesunu u vybraného procesu.
- [ ] **I.3** Vyber cílovou agendu, vyplň **důvod**.
      → Bez důvodu je **Spočítat náhled** šedé.
- [ ] **I.4** **Spočítat náhled**. → Vpravo se objeví **„nový kód AA-BB"**
      a v tabulce seznam všech dvojic starý → nový.
- [ ] **I.5** Souhrn dole hlásí počet kódů a počet zařazení, která se přenesou.
- [ ] **I.6** **Změň cílovou agendu** na jinou. → Tabulka se vyprázdní
      a **Provést přesun** zšedne.

> Náhled platí jen pro ten cíl, nad kterým proběhl. Bez tohohle by šlo
> spočítat jeden cíl, přepnout na druhý a odklepnout zápis podle čísel,
> která pro něj neplatí.

- [ ] **I.7** Vrať původní cíl, znovu **Spočítat náhled**, pak
      **Provést přesun** → v modálu **Ano, přesunout**.
- [ ] **I.8** Během běhu svítí **„Přesouvám — nezavírej aplikaci…"**.
- [ ] **I.9** Skončí hláškou **„Přesun hotov: AA-BB je teď CC-DD."**

Kontrola v datech — projdi **všech pět** listů:

- [ ] **I.10** `Procesy`: nový proces existuje, má **`puvodni_kod`** = starý
      kód; starý proces už **neexistuje**.
- [ ] **I.11** `DilciProcesy`: každý dílčí proces má nový prefix a **stejné
      `CCC`** jako dřív; `puvodni_kod` ukazuje na starý kód; staré řádky pryč.
- [ ] **I.12** `Aktivity`: totéž, `DDDD` beze změny; sloupce **Spolupracuje**,
      **Vnitřní předpis** a **Text pro OŘ** jsou **vyplněné jako dřív**.

> I.12 je past: tyhle tři sloupce se nesou jen v plném záznamu. Kdyby se
> aktivity zakládaly ze zkráceného seznamu, tiše by se vyprázdnily.

- [ ] **I.13** `AktivitaDilciProces`: vazby ukazují na nové kódy;
      na žádný starý kód neukazuje nic.
- [ ] **I.14** `HistorieKodu`: **přibyl řádek pro každý** uzavřený kód —
      tedy 1 + dílčí procesy + aktivity. Každý má vyplněný
      **`nastupce_kod`**, **`duvod`** (tvůj text), **`datum`** a **`kdo`**.
- [ ] **I.15** V knihovně `Zalohy` **přibyl snímek** pořízený těsně před
      přesunem.

> Záloha je zároveň protokol, který metodika u změny kódu vyžaduje, i jediná
> cesta zpět — kaskáda není transakce, SharePoint ji neumí ani přes flow.

Kontrola v aplikaci:

- [ ] **I.16** Přehled → strom. Proces je pod **novou** agendou, se všemi
      dílčími procesy a aktivitami, a **žádná aktivita tam není dvakrát**.
- [ ] **I.17** Karty nahoře ukazují **stejné počty** jako v kroku 0.2.

> Přesun nic nepřidává ani neubírá — jen přečísluje. Jiné číslo znamená,
> že něco zůstalo viset nebo se založilo dvakrát.

- [ ] **I.18** Otevři aktivitu, která byla zařazená i do **jiného** dílčího
      procesu (vedlejší vazba). → Její další zařazení je **zachované**.
- [ ] **I.19** Přehled → **HTML mapa ▾ → Obnovit**, pak **Otevřít**.
      → Proces je v mapě pod novou agendou a starý kód v ní není.

---

## J. Zkouška pravidla „kód se nerecykluje"

Nepovinné, ale je to jediné místo, kde se dá ověřit smysl celé varianty C.

- [ ] **J.1** Přesuň tentýž proces **zpátky** do původní agendy.
- [ ] **J.2** → Dostane **TŘETÍ** kód, ne ten původní.

> Původní kód je v historii uzavřený a nikdy se neoživí. Kdyby se vrátil,
> znamenal by v evidenci dvě různé věci — a přesně tomu má varianta C
> zabránit.

- [ ] **J.3** `HistorieKodu` obsahuje **oba** předchozí kódy, každý se svým
      nástupcem, takže se dá projít celý řetěz.

---

## Když něco selže

| co se stalo | kde hledat |
|---|---|
| appka se neotevře ve Studiu (`Error opening file`) | chyba v `pa.yaml`; pošli mi znění hlášky, `pac` ani import to nechytí |
| appka hlásí `Flow.Run failed: 502 BadGateway / NoResponse` | není to chyba appky — otevři **run history** toho flow, tam je skutečná příčina |
| flow hlásí `WorkflowTriggerIsNotEnabled` | flow je vypnuté, zapni ho (F.1) |
| import sešitu hlásí `403 OpenWorkbookAccessDenied` | citlivostní štítek sešitu, ne oprávnění — přeštítkuj na „Interní" |
| přesun spadl uprostřed | obnov ze zálohy z kroku I.15 (**Data ▾ → Obnova**) a pošli mi run history |
| počty na kartách nesedí po přesunu | něco zůstalo viset — pošli mi obsah `HistorieKodu` a `AktivitaDilciProces` |
