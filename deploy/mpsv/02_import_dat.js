/* import_data.js -- GENEROVANO src/make_import.py. Needituj rucne.

   POUZITI
   1. Nejdriv musi probehnout src/setup_sharepoint.js (listy a sloupce).
   2. Otevri cilovy SharePoint web, F12 -> Console -> vloz tento soubor.
   3. Skript je idempotentni: polozky, ktere uz v listu jsou (podle klice
      ve sloupci Title), preskoci. Muzes ho spustit opakovane.
   4. Jedna polozka = jeden POST. Chyba jedne polozky beh nezastavi -
      nasbira se a vypise na konci, aby bylo videt, co presne selhalo.

   SADA DAT: runs/normalize
   POCTY:    Agendy=7, Procesy=46, DilciProcesy=250, Aktivity=46, AktivitaDilciProces=46, Utvary=44
*/
(async () => {
"use strict";

const DATA = [
 {
  "list": "Agendy",
  "rows": [
   {
    "Title": "01",
    "nazev": "Organizace a řízení MPSV a resortu",
    "vlastnik": "3",
    "zdroj": "rejstrik"
   },
   {
    "Title": "02",
    "nazev": "Sociální záležitosti",
    "vlastnik": "",
    "zdroj": "rejstrik"
   },
   {
    "Title": "03",
    "nazev": "Příjmová politika a sociální pojištění",
    "vlastnik": "",
    "zdroj": "rejstrik"
   },
   {
    "Title": "04",
    "nazev": "Zaměstnanost",
    "vlastnik": "",
    "zdroj": "rejstrik"
   },
   {
    "Title": "05",
    "nazev": "Pracovněprávní záležitosti",
    "vlastnik": "",
    "zdroj": "rejstrik"
   },
   {
    "Title": "06",
    "nazev": "EU a mezinárodní vztahy",
    "vlastnik": "",
    "zdroj": "rejstrik"
   },
   {
    "Title": "07",
    "nazev": "Zajištění chodu MPSV a resortu",
    "vlastnik": "3",
    "zdroj": "rejstrik"
   }
  ]
 },
 {
  "list": "Procesy",
  "rows": [
   {
    "Title": "01-01",
    "nazev": "Strategie a koncepce MPSV",
    "agenda_kod": "01",
    "vlastnik": "11; 33",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-02",
    "nazev": "Operativní řízení útvarů MPSV a resortních organizací",
    "agenda_kod": "01",
    "vlastnik": "33",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-03",
    "nazev": "Správa rozpočtové kapitoly",
    "agenda_kod": "01",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-04",
    "nazev": "Programové financování MPSV a resortu",
    "agenda_kod": "01",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-05",
    "nazev": "Boj proti korupci, oznamování",
    "agenda_kod": "01",
    "vlastnik": "33",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-06",
    "nazev": "Výzkum a vývoj",
    "agenda_kod": "01",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-07",
    "nazev": "Audit",
    "agenda_kod": "01",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-08",
    "nazev": "Kontrola",
    "agenda_kod": "01",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-09",
    "nazev": "Řízení rizik",
    "agenda_kod": "01",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-10",
    "nazev": "Krizové řízení",
    "agenda_kod": "01",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-01",
    "nazev": "Sociální politika",
    "agenda_kod": "02",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-02",
    "nazev": "Odškodňování",
    "agenda_kod": "02",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-03",
    "nazev": "Rodinná politika",
    "agenda_kod": "02",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-04",
    "nazev": "Rovné příležitosti",
    "agenda_kod": "02",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-05",
    "nazev": "Sociálně právní ochrana dětí",
    "agenda_kod": "02",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-06",
    "nazev": "Posudková služba",
    "agenda_kod": "02",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-07",
    "nazev": "Sociální služby",
    "agenda_kod": "02",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-01",
    "nazev": "Příjmová politika",
    "agenda_kod": "03",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-02",
    "nazev": "Pracovní úrazové pojištění",
    "agenda_kod": "03",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-03",
    "nazev": "Soukromé důchodové pojištění",
    "agenda_kod": "03",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-04",
    "nazev": "Důchodové pojištění",
    "agenda_kod": "03",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-05",
    "nazev": "Pojistné na sociální zabezpečení",
    "agenda_kod": "03",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-06",
    "nazev": "Nemocenské pojištění",
    "agenda_kod": "03",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-01",
    "nazev": "Politika zaměstnanosti",
    "agenda_kod": "04",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-02",
    "nazev": "Aktivní politika maněstnanosti",
    "agenda_kod": "04",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-03",
    "nazev": "Analýzy trhu práce a politik zaměstnanosti",
    "agenda_kod": "04",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-04",
    "nazev": "Mezinárodní pracovní mobilita a integrace cizinců",
    "agenda_kod": "04",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-05",
    "nazev": "Služby trhu práce a dalšího vzdělávání",
    "agenda_kod": "04",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-06",
    "nazev": "Zaměstnávání OZP a sociální podnikání",
    "agenda_kod": "04",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-01",
    "nazev": "Pracovněprávní legislativa a kolektivní vyjednávání",
    "agenda_kod": "05",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-02",
    "nazev": "Mzdová politika",
    "agenda_kod": "05",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-03",
    "nazev": "Bezpečnost práce a pracovní prostředí",
    "agenda_kod": "05",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-01",
    "nazev": "Řízení pomoci z fondů EU a EHP",
    "agenda_kod": "06",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-02",
    "nazev": "Mezinárodní vztahy",
    "agenda_kod": "06",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-01",
    "nazev": "Vnější komunikace",
    "agenda_kod": "07",
    "vlastnik": "33",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-02",
    "nazev": "Parlamentní agenda",
    "agenda_kod": "07",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-03",
    "nazev": "Vládní agenda",
    "agenda_kod": "07",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04",
    "nazev": "Právní podpora",
    "agenda_kod": "07",
    "vlastnik": "33",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-05",
    "nazev": "Finance",
    "agenda_kod": "07",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-06",
    "nazev": "Statistika",
    "agenda_kod": "07",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-07",
    "nazev": "Správa majetku",
    "agenda_kod": "07",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08",
    "nazev": "Řízení lidských zdrojů",
    "agenda_kod": "07",
    "vlastnik": "11; 33",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-09",
    "nazev": "Odborná podpora",
    "agenda_kod": "07",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-10",
    "nazev": "Administrativní podpora",
    "agenda_kod": "07",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-11",
    "nazev": "Náhrada škody",
    "agenda_kod": "07",
    "vlastnik": "33",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-12",
    "nazev": "ICT a digitalizace",
    "agenda_kod": "07",
    "vlastnik": "",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   }
  ]
 },
 {
  "list": "DilciProcesy",
  "rows": [
   {
    "Title": "01-01-001",
    "nazev": "Řízení strategie MPSV",
    "proces_kod": "01-01",
    "vlastnik": "33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-01-002",
    "nazev": "Řízení koncepce MPSV",
    "proces_kod": "01-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-01-003",
    "nazev": "Politika lidských zdrojů",
    "proces_kod": "01-01",
    "vlastnik": "11",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-01-004",
    "nazev": "Plánování lidských zdrojů",
    "proces_kod": "01-01",
    "vlastnik": "11",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-02-001",
    "nazev": "Organizace a řízení projektů",
    "proces_kod": "01-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-02-002",
    "nazev": "Řízení resortních organizací MPSV",
    "proces_kod": "01-02",
    "vlastnik": "33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-02-003",
    "nazev": "Tvorba a připomínkování metodik a interních řídících dokumentů MPSV",
    "proces_kod": "01-02",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-02-004",
    "nazev": "Analytická, statistická a prognostická činnost",
    "proces_kod": "01-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-03-001",
    "nazev": "Správa rozpočtu MPSV",
    "proces_kod": "01-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-03-002",
    "nazev": "Správa rozpočtu podřízených organizací MPSV",
    "proces_kod": "01-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-03-003",
    "nazev": "Správa rozpočtu ÚP ČR",
    "proces_kod": "01-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-03-004",
    "nazev": "Finanční kontrola podřízených organizací",
    "proces_kod": "01-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-04-001",
    "nazev": "Metodické řízení v oblasti programového financování MPSV a resortu.",
    "proces_kod": "01-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-04-002",
    "nazev": "Nastavení a kontrola podmínek realizace akcí a jejich evidence v ISPROFIN",
    "proces_kod": "01-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-04-003",
    "nazev": "Finanční řízení jednotlivých akcí.",
    "proces_kod": "01-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-04-004",
    "nazev": "Řízení a koordinace zpracování dokumentací programů kapitoly.",
    "proces_kod": "01-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-04-005",
    "nazev": "Správa programu dotací do sociální oblasti.",
    "proces_kod": "01-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-04-006",
    "nazev": "Zpracování dokumentace programu a řízení realizace akcí ÚP ČR.",
    "proces_kod": "01-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-05-001",
    "nazev": "Boj proti korupci",
    "proces_kod": "01-05",
    "vlastnik": "33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-05-002",
    "nazev": "Oznamování protiprávního jednání",
    "proces_kod": "01-05",
    "vlastnik": "33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-05-003",
    "nazev": "Lobbování",
    "proces_kod": "01-05",
    "vlastnik": "33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-06-001",
    "nazev": "Tvorba koncepcí a strategií v oblasti výzkumu a vývoje",
    "proces_kod": "01-06",
    "vlastnik": "",
    "stav_rejstrik": "využitý-S4",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-06-002",
    "nazev": "Koordinační a organizační činnosti v oblasti výzkumu a vývoje a odborná podpora",
    "proces_kod": "01-06",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-06-003",
    "nazev": "Poskytování finanční podpory v oblasti výzkumu a vývoje",
    "proces_kod": "01-06",
    "vlastnik": "",
    "stav_rejstrik": "využitý-S4",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-06-004",
    "nazev": "Organizace a řízení navazujících nevýzkumných potřeb v další činnosti resortní výzkumné organizace",
    "proces_kod": "01-06",
    "vlastnik": "",
    "stav_rejstrik": "využitý-S4",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-07-001",
    "nazev": "Plánování auditu",
    "proces_kod": "01-07",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-07-002",
    "nazev": "Výkon auditu",
    "proces_kod": "01-07",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-07-003",
    "nazev": "Reporting auditu",
    "proces_kod": "01-07",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-08-001",
    "nazev": "Plánování kontrol",
    "proces_kod": "01-08",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-08-002",
    "nazev": "Výkon finanční kontroly",
    "proces_kod": "01-08",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-08-003",
    "nazev": "Výkon kontroly státní správy",
    "proces_kod": "01-08",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-08-004",
    "nazev": "Výkon ostatních kontrol",
    "proces_kod": "01-08",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-08-005",
    "nazev": "Výkon státní správy v oblasti kontrol",
    "proces_kod": "01-08",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-08-006",
    "nazev": "Reporting kontrol",
    "proces_kod": "01-08",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-09-001",
    "nazev": "Tvorba koncepce a metodiky systému rizik MPSV",
    "proces_kod": "01-09",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-09-002",
    "nazev": "Metodické řízení v oblasti řídících a kontrolních mechanismů",
    "proces_kod": "01-09",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-09-003",
    "nazev": "Koordinace, správa a vedení systému řízení rizik",
    "proces_kod": "01-09",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-10-001",
    "nazev": "Realizace krizového řízení resortu práce a sociálních věcí",
    "proces_kod": "01-10",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-10-002",
    "nazev": "Zajištění ochrany utajovaných informací",
    "proces_kod": "01-10",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-10-003",
    "nazev": "Zajištění BOZP a PO MPSV",
    "proces_kod": "01-10",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "01-10-004",
    "nazev": "Zajištění ochrany a ostrahy objektu MPSV",
    "proces_kod": "01-10",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-01-001",
    "nazev": "Tvorba koncepce v oblasti sociální politiky včetně reformy veřejných financí",
    "proces_kod": "02-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-01-002",
    "nazev": "Tvorba právních předpisů v oblasti sociální politiky",
    "proces_kod": "02-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-01-003",
    "nazev": "Metodické řízení a koordinace v oblasti sociální politiky",
    "proces_kod": "02-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-01-004",
    "nazev": "Výkon státní správy v oblasti sociální politiky",
    "proces_kod": "02-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-01-005",
    "nazev": "Zpracování analýz a prognóz v oblasti sociální politiky",
    "proces_kod": "02-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-01-006",
    "nazev": "Zpracování statistik, analýz a prognóz v oblasti politiky sociálního začleňování",
    "proces_kod": "02-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-02-001",
    "nazev": "Tvorba koncepce v oblasti odškodňování",
    "proces_kod": "02-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-02-002",
    "nazev": "Tvorba právních předpisů v oblasti odškodňování",
    "proces_kod": "02-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-02-003",
    "nazev": "Metodické řízení v oblasti odškodňování",
    "proces_kod": "02-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-02-004",
    "nazev": "Výkon státní správy v oblasti odškodňování",
    "proces_kod": "02-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-02-005",
    "nazev": "Zpracování statistik, analýz a prognóz v oblasti odškodňování",
    "proces_kod": "02-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-03-001",
    "nazev": "Tvorba koncepce v oblasti rodinné politiky",
    "proces_kod": "02-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-03-002",
    "nazev": "Tvorba právních předpisů v oblasti rodinné politiky",
    "proces_kod": "02-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-03-003",
    "nazev": "Metodické řízení v oblasti rodinné politiky",
    "proces_kod": "02-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-03-004",
    "nazev": "Výkon státní správy v oblasti rodinné politiky",
    "proces_kod": "02-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-04-001",
    "nazev": "Tvorba koncepce v oblasti rovných příležitostí",
    "proces_kod": "02-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-04-002",
    "nazev": "Metodické řízení v oblasti rovných příležitostí",
    "proces_kod": "02-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-04-003",
    "nazev": "Tvorba právních předpisů v oblasti rovných příležitostí",
    "proces_kod": "02-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-04-004",
    "nazev": "Výkon státní správy v oblasti rovných příležitostí",
    "proces_kod": "02-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-05-001",
    "nazev": "Tvorba koncepce v oblasti sociálně právní ochrany dětí",
    "proces_kod": "02-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-05-002",
    "nazev": "Tvorba právních předpisů v oblasti sociálně právní ochrany dětí",
    "proces_kod": "02-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-05-003",
    "nazev": "Metodické řízení v oblasti sociálně právní ochrany dětí",
    "proces_kod": "02-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-05-004",
    "nazev": "Výkon státní správy v oblasti sociálně právní ochrany dětí",
    "proces_kod": "02-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-05-005",
    "nazev": "Zpracování analýz v oblasti sociálně právní ochrany dětí",
    "proces_kod": "02-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-06-001",
    "nazev": "Tvorba koncepce v oblasti posudkových kritérií a v oblasti organizace a řízení posudkové služby",
    "proces_kod": "02-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-06-002",
    "nazev": "Tvorba právních předpisů v oblasti posudkové služby",
    "proces_kod": "02-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-06-003",
    "nazev": "Metodické řízení v oblasti posudkové služby a v oblasti organizace a řízení posudkové služby",
    "proces_kod": "02-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-06-004",
    "nazev": "Organizace a řízení posudkové služby",
    "proces_kod": "02-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-06-005",
    "nazev": "Zpracování analýz v oblasti posudkové služby",
    "proces_kod": "02-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-06-006",
    "nazev": "Výkon státní správy v oblasti posudkové služby a v oblasti organizace a řízení posudkové služby",
    "proces_kod": "02-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-06-007",
    "nazev": "Výkon činnosti posudkových komisí",
    "proces_kod": "02-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-07-001",
    "nazev": "Tvorba koncepce v oblasti sociálních služeb a politiky sociálního začleňování",
    "proces_kod": "02-07",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-07-002",
    "nazev": "Metodické řízení v oblasti sociálních služeb a dalších systémů v oblasti sociálního začleňování",
    "proces_kod": "02-07",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-07-003",
    "nazev": "Tvorba právních předpisů v oblasti sociálních služeb a dalších systémů v oblasti sociálního začleňování",
    "proces_kod": "02-07",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-07-004",
    "nazev": "Výkon a koordinace veřejné správy v oblasti sociálních služeb a dalších systémů sociálního začleňování",
    "proces_kod": "02-07",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "02-07-005",
    "nazev": "Zpracování statistik, analýz a prognóz v oblasti politiky sociálního začleňování",
    "proces_kod": "02-07",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-01-001",
    "nazev": "Tvorba koncepce v oblasti příjmové politiky",
    "proces_kod": "03-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-01-002",
    "nazev": "Tvorba právních předpisů v oblasti příjmové politiky",
    "proces_kod": "03-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-01-003",
    "nazev": "Expertní, analytické a prognostické činnosti v oblasti příjmové politiky",
    "proces_kod": "03-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-02-001",
    "nazev": "Tvorba koncepce v oblasti úrazového pojištění",
    "proces_kod": "03-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-02-002",
    "nazev": "Tvorba právních předpisů v oblasti úrazového pojištění",
    "proces_kod": "03-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-02-003",
    "nazev": "Zpracování analýz v oblasti úrazového pojištění",
    "proces_kod": "03-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-02-004",
    "nazev": "Zabezpečení pojistně-matematických činností v oblasti úrazového pojištění",
    "proces_kod": "03-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-03-001",
    "nazev": "Tvorba koncepce v oblasti soukromého důchodového pojištění",
    "proces_kod": "03-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-03-002",
    "nazev": "Tvorba právních předpisů v oblasti soukromého důchodového pojištění",
    "proces_kod": "03-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-03-003",
    "nazev": "Metodické řízení v oblasti soukromého důchodového pojištění",
    "proces_kod": "03-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-03-004",
    "nazev": "Výkon státní správy v oblasti soukromého důchodového pojištění",
    "proces_kod": "03-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-03-005",
    "nazev": "Zpracování analýz v oblasti soukromého důchodového pojištění",
    "proces_kod": "03-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-03-006",
    "nazev": "Zabezpečení pojistně-matematických činností v oblasti soukromého důchodového pojištění",
    "proces_kod": "03-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-04-001",
    "nazev": "Tvorba koncepce v oblasti důchodového pojištění",
    "proces_kod": "03-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-04-002",
    "nazev": "Tvorba právních předpisů v oblasti důchodového pojištění",
    "proces_kod": "03-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-04-003",
    "nazev": "Metodické řízení v oblasti důchodového pojištění",
    "proces_kod": "03-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-04-004",
    "nazev": "Výkon státní správy v oblasti důchodového pojištění",
    "proces_kod": "03-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-04-005",
    "nazev": "Zpracování analýz v oblasti důchodového pojištění",
    "proces_kod": "03-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-04-006",
    "nazev": "Zabezpečení pojistně-matematických činností v oblasti důchodového pojištění",
    "proces_kod": "03-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-05-001",
    "nazev": "Tvorba koncepce v oblasti pojistného na sociální zabezpečení",
    "proces_kod": "03-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-05-002",
    "nazev": "Tvorba právních předpisů v oblasti pojistného na sociální zabezpečení",
    "proces_kod": "03-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-05-003",
    "nazev": "Metodické řízení v oblasti pojistného na sociální zabezpečení",
    "proces_kod": "03-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-05-004",
    "nazev": "Výkon státní správy v oblasti pojistného na sociální zabezpečení",
    "proces_kod": "03-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-05-005",
    "nazev": "Zpracování analýz v oblasti pojistného na sociální zabezpečení",
    "proces_kod": "03-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-05-006",
    "nazev": "Zabezpečení pojistně-matematických činností v oblasti pojistného na sociální zabezpečení",
    "proces_kod": "03-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-06-001",
    "nazev": "Tvorba koncepce v oblasti nemocenského pojištění",
    "proces_kod": "03-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-06-002",
    "nazev": "Tvorba právních předpisů v oblasti nemocenského pojištění",
    "proces_kod": "03-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-06-003",
    "nazev": "Metodické řízení v oblasti nemocenského pojištění",
    "proces_kod": "03-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-06-004",
    "nazev": "Výkon státní správy v oblasti nemocenského pojištění",
    "proces_kod": "03-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-06-005",
    "nazev": "Zpracování analýz v oblasti nemocenského pojištění",
    "proces_kod": "03-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "03-06-006",
    "nazev": "Zabezpečení pojistně-matematických činností v oblasti nemocenského pojištění",
    "proces_kod": "03-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-01-001",
    "nazev": "Tvorba koncepcí a strategií v oblasti politiky zaměstnanosti a inspekce práce",
    "proces_kod": "04-01",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-01-002",
    "nazev": "Tvorba právních předpisů v oblasti politiky zaměstnanosti a inspekce práce",
    "proces_kod": "04-01",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-01-003",
    "nazev": "Metodické řízení v oblasti politiky zaměstnanosti a inspekce práce",
    "proces_kod": "04-01",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-01-004",
    "nazev": "Metodické řízení ÚP ČR a SÚIP v oblasti politiky zaměstnanosti",
    "proces_kod": "04-01",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-01-005",
    "nazev": "Výkon státní správy v oblasti politiky zaměstnanosti a inspekce práce",
    "proces_kod": "04-01",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-01-006",
    "nazev": "Zpracování statistik, analýz a prognóz v oblasti politiky zaměstnanosti",
    "proces_kod": "04-01",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-01-007",
    "nazev": "Zpracování podkladů a vytváření stanovisek pro mezinárodní a vnitrostátní orgány v oblasti politiky zaměstnanosti",
    "proces_kod": "04-01",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-01-008",
    "nazev": "Věcná koordinace projektů v oblasti zaměstnanosti",
    "proces_kod": "04-01",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-02-001",
    "nazev": "Tvorba koncepcí a stragií v oblasti aktivní politiky zaměstnanosti",
    "proces_kod": "04-02",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-02-002",
    "nazev": "Tvorba nástrojů aktivní politiky zaměstnanosti",
    "proces_kod": "04-02",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-02-003",
    "nazev": "Tvorba právních předpisů v oblasti aktivní politiky zaměstnanosti",
    "proces_kod": "04-02",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-02-004",
    "nazev": "Metodické řízení ÚP ČR v oblasti aktivní politiky zaměstnanosti",
    "proces_kod": "04-02",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-02-005",
    "nazev": "Výkon státní správy v oblasti aktivní politiky zaměstnanosti",
    "proces_kod": "04-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-02-006",
    "nazev": "Zpracování podkladů a vytváření stanovisek v oblasti aktivní politiky zaměstnanosti",
    "proces_kod": "04-02",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-02-007",
    "nazev": "Tvorba věcných podkladů pro digitalizaci v oblasti aktivní politiky zaměstnanosti",
    "proces_kod": "04-02",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-03-001",
    "nazev": "Zpracování statistik, analýz trhu práce a politik zaměstnanosti",
    "proces_kod": "04-03",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-03-002",
    "nazev": "Rozvoj datové základny trhu práce a politik zaměstnanosti",
    "proces_kod": "04-03",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-03-003",
    "nazev": "Rozvoj modelové platformy trhu práce a politik zaměstnanosti",
    "proces_kod": "04-03",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-03-004",
    "nazev": "Rozvoj platformy pro vizualizaci dat trhu práce a politik zaměstnanosti",
    "proces_kod": "04-03",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-04-001",
    "nazev": "Tvorba koncepcí a stragií v oblasti mezinárodní pracovní mobility a integrace cizinců",
    "proces_kod": "04-04",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-04-002",
    "nazev": "Tvroba právních předpisů v oblasti mezinárodní pracovní mobility a integrace cizinců",
    "proces_kod": "04-04",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-04-003",
    "nazev": "Metodické řízení ÚP ČR v oblasti mezinárodní pracovní mobility a integrace cizinců",
    "proces_kod": "04-04",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-04-004",
    "nazev": "Výkon státní správy v oblasti mezinárodní pracovní mobility a integrace cizinců",
    "proces_kod": "04-04",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-04-005",
    "nazev": "Zpracování statistik, analýz a prognóz v oblasti mezinárodní pracovní mobility a integrace cizinců",
    "proces_kod": "04-04",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-04-006",
    "nazev": "Zpracování podkladů a vytváření stanovisek pro mezinárodní a vnitrostátní orgány v oblasti mezinárodní pracovní mobility a integrace cizinců",
    "proces_kod": "04-04",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-04-007",
    "nazev": "Tvorba věcných podkladů pro digitalizaci v oblasti mezinárodní pracovní mobility a integrace cizinců",
    "proces_kod": "04-04",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-05-001",
    "nazev": "Tvorba koncepcí a strategií v oblasti služeb trhu práce a dalšího vzdělávání",
    "proces_kod": "04-05",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-05-002",
    "nazev": "Tvorba právních předpisů v oblasti služeb trhu práce a dalšího vzdělávání",
    "proces_kod": "04-05",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-05-003",
    "nazev": "Metodické řízení ÚP ČR v oblasti služeb trhu práce a dalšího vzdělávání",
    "proces_kod": "04-05",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-05-004",
    "nazev": "Výkon státní správy v oblasti služeb trhu práce a dalšího vzdělávání",
    "proces_kod": "04-05",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-05-005",
    "nazev": "Tvorba věcných podkladů pro digitalizaci v oblasti služeb trhu práce a dalšího vzdělávání",
    "proces_kod": "04-05",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-06-001",
    "nazev": "Tvorba koncepcí a stragií v oblasti zaměstnávání OZP a sociálního podnikání",
    "proces_kod": "04-06",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-06-002",
    "nazev": "Tvorba právních předpisů v oblasti zaměstnávání OZP a sociálního podnikání",
    "proces_kod": "04-06",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-06-003",
    "nazev": "Metodické řízení ÚP ČR v oblasti zaměstnávání OZP a sociálního podnikání",
    "proces_kod": "04-06",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-06-004",
    "nazev": "Výkon státní správy v oblasti zaměstnávání OZP a sociálního podnikání",
    "proces_kod": "04-06",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-06-005",
    "nazev": "Zpracování podkladů a vytváření stanovisek pro mezinárodní a vnitrostátní orgány v oblasti zaměstnávání OZP a sociálního podnikání",
    "proces_kod": "04-06",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "04-06-006",
    "nazev": "Tvorba věcných podkladů pro digitalizaci v oblasti zaměstnávání OZP a sociálního podnikání",
    "proces_kod": "04-06",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-01-001",
    "nazev": "Tvorba koncepcí v oblasti pracovněprávních vztahů a kolektivního vyjednávání",
    "proces_kod": "05-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-01-002",
    "nazev": "Tvorba právních předpisů v oblasti pracovněprávní legislativy a kolektivního vyjednávání",
    "proces_kod": "05-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-01-003",
    "nazev": "Příprava podkladů a stanovisek v oblasti pracovněprávních otázek, kolektivních smluv a kolektivního vyjednávání pro mezinárodní orgány, správní orgány a jiné subjekty",
    "proces_kod": "05-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-01-004",
    "nazev": "Řízení agendy kolektivních smluv, kolektivního vyjednávání a vedení seznamu mediátorů",
    "proces_kod": "05-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-01-005",
    "nazev": "Výkon státní správy v oblasti pracovněprávní legislativy a kolektivního vyjednávání",
    "proces_kod": "05-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-02-001",
    "nazev": "Tvorba koncepcí v oblasti odměňování a cestovních náhrad",
    "proces_kod": "05-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-02-002",
    "nazev": "Tvorba právních předpisů v oblasti odměňování a cestovních náhrad",
    "proces_kod": "05-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-02-003",
    "nazev": "Metodické řízení v oblasti mzdové politiky",
    "proces_kod": "05-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-02-004",
    "nazev": "Výkon a správa agendy hodnocení práce",
    "proces_kod": "05-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-02-005",
    "nazev": "Zpracování podkladů a stanovisek pro provádění mzdové politiky a vyhodnocení vývoje mezd",
    "proces_kod": "05-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-02-006",
    "nazev": "Zpracování zdrojových informací pro státní rozpočet ČR",
    "proces_kod": "05-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-03-001",
    "nazev": "Tvorba koncepcí a strategií v oblasti bezpečnosti práce a pracovního prostředí",
    "proces_kod": "05-03",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-03-002",
    "nazev": "Tvorba právních předpisů v oblasti BOZP",
    "proces_kod": "05-03",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-03-003",
    "nazev": "Metodické řízení a koordinace činností podřízených organizací v oblasti inspekce práce a výzkumu bezpečnosti práce",
    "proces_kod": "05-03",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-03-004",
    "nazev": "Příprava podkladů a účast na jednání v národních orgánech a v mezinárodních organizacích k problematice BOZP",
    "proces_kod": "05-03",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-03-005",
    "nazev": "Správa agendy vydávání akreditací podle zákona č. 309/2006 Sb.",
    "proces_kod": "05-03",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "05-03-006",
    "nazev": "Výkon státní správy v oblasti bezpečnosti práce a pracovního prostředí",
    "proces_kod": "05-03",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-01-001",
    "nazev": "Tvorba koncepcí v oblasti řízení a realizace programů, opatření a projektů z ESF",
    "proces_kod": "06-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-01-002",
    "nazev": "Institucionální zajištění implementace programů z ESF včetně pracovních skupin",
    "proces_kod": "06-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-01-003",
    "nazev": "Řízení a implementace programů z ESF včetně technické asistence",
    "proces_kod": "06-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-01-004",
    "nazev": "Řízení a implementace projektů",
    "proces_kod": "06-01",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-01-005",
    "nazev": "Negociace a plnění informační povinnosti",
    "proces_kod": "06-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-01-006",
    "nazev": "Finanční řízení pomoci z ESF",
    "proces_kod": "06-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-01-007",
    "nazev": "Příprava podkladů a stanovisek v oblasti řízení a realizace projektů pro mezinárodní organizace, správní orgány a jiné subjekty",
    "proces_kod": "06-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-02-001",
    "nazev": "Tvorba koncepcí v oblasti mezinárodních vztahů",
    "proces_kod": "06-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-02-002",
    "nazev": "Příprava, koordinace a účast na projednávání mezinárodních dokumentů a národních pozic",
    "proces_kod": "06-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-02-003",
    "nazev": "Multilaterální a bilaterální spolupráce s členskými a nečlenskými zeměmi EU",
    "proces_kod": "06-02",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-02-004",
    "nazev": "Účast na mezinárodních jednáních v orgánech EU a v mezinárodních organizacích",
    "proces_kod": "06-02",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-02-005",
    "nazev": "Řízení a implementace programů a projektů",
    "proces_kod": "06-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "06-02-006",
    "nazev": "Výkon státní správy v oblasti mezinárodních vztahů",
    "proces_kod": "06-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-01-001",
    "nazev": "Zajišťování vztahů s médii",
    "proces_kod": "07-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-01-002",
    "nazev": "Příprava tiskových konferencí, tiskových zpráv a dalších podkladů",
    "proces_kod": "07-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-01-003",
    "nazev": "Poskytování informací veřejnosti, včetně vyřizování stížností, podnětů a oznámení",
    "proces_kod": "07-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-01-004",
    "nazev": "Poskytování informací veřejnosti dle zákona č. 106/1999 Sb.",
    "proces_kod": "07-01",
    "vlastnik": "33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-01-005",
    "nazev": "Tvorba a aktualizace webových stránek MPSV",
    "proces_kod": "07-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-01-006",
    "nazev": "Monitoring vybraného tisku",
    "proces_kod": "07-01",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-02-001",
    "nazev": "Příprava podkladů pro jednání ministra",
    "proces_kod": "07-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-02-002",
    "nazev": "Zajišťování účasti na jednání výborů a podvýborů PS a Senátu",
    "proces_kod": "07-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-02-003",
    "nazev": "Zajišťování odpovědí na interpelace",
    "proces_kod": "07-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-02-004",
    "nazev": "Sledování programu orgánů Parlamentu",
    "proces_kod": "07-02",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-03-001",
    "nazev": "Příprava a zpracování podkladů pro jednání ministra",
    "proces_kod": "07-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-03-002",
    "nazev": "Zajišťování účasti na jednání výborů a komisí LRV, vlády",
    "proces_kod": "07-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-03-003",
    "nazev": "Koordinace a plnění úkolů z vládních usnesení a kontrola jejich plnění",
    "proces_kod": "07-03",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-03-004",
    "nazev": "Plán legislativních prací a nelegislativních úkolů vlády",
    "proces_kod": "07-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-03-005",
    "nazev": "Zajištění a práce s EKLEP",
    "proces_kod": "07-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-03-006",
    "nazev": "Zajištění činností v rámci projektu „Cíle vlády ČR“",
    "proces_kod": "07-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-03-007",
    "nazev": "Zajištění činnosti rozkladové komise, včetně účasti a zpracování podkladů",
    "proces_kod": "07-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-03-008",
    "nazev": "Meziresortní připomínková řízení",
    "proces_kod": "07-03",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-001",
    "nazev": "Připomínkování návrhů smluv",
    "proces_kod": "07-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-002",
    "nazev": "Zastupování MPSV a resortu před soudy, popř. jinými institucemi",
    "proces_kod": "07-04",
    "vlastnik": "33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-003",
    "nazev": "Právní servis (vyřizování právních a majetkových záležitostí)",
    "proces_kod": "07-04",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-004",
    "nazev": "Stížnosti a petice",
    "proces_kod": "07-04",
    "vlastnik": "33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-005",
    "nazev": "Právní konzultace",
    "proces_kod": "07-04",
    "vlastnik": "33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-05-001",
    "nazev": "Tvorba koncepce financování resortu MPSV",
    "proces_kod": "07-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-05-002",
    "nazev": "Metodika financování a účetnictví",
    "proces_kod": "07-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-05-003",
    "nazev": "Účetní a finanční výkaznictví",
    "proces_kod": "07-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-05-004",
    "nazev": "Finanční řízení včetně realizace finančních operací",
    "proces_kod": "07-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-05-005",
    "nazev": "Vedení účetnictví a oběh účetních dokladů",
    "proces_kod": "07-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-05-006",
    "nazev": "Zpracování a kontrola vybraných rozpočtových položek",
    "proces_kod": "07-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-05-007",
    "nazev": "Evidence a inventarizace majetku",
    "proces_kod": "07-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-05-008",
    "nazev": "Platební styk",
    "proces_kod": "07-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-05-009",
    "nazev": "Výkon pokladní agendy",
    "proces_kod": "07-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-05-010",
    "nazev": "Správa pohledávek a závazků",
    "proces_kod": "07-05",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-05-011",
    "nazev": "Správa kaucí a poplatků",
    "proces_kod": "07-05",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-06-001",
    "nazev": "Zpracování statistik za kapitolu 313 a statistik v působnosti resortu MPSV",
    "proces_kod": "07-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-06-002",
    "nazev": "Zpracování statistik pro externí statistické systémy",
    "proces_kod": "07-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-06-003",
    "nazev": "Metodické řízení a konzultační činnost v oblasti statistických informací",
    "proces_kod": "07-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-06-004",
    "nazev": "Zpracování analýz statistických informací",
    "proces_kod": "07-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-06-005",
    "nazev": "Statistická zjišťování",
    "proces_kod": "07-06",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-07-001",
    "nazev": "Správa a údržba majetku",
    "proces_kod": "07-07",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-07-002",
    "nazev": "Obnova majetku - investice MPSV",
    "proces_kod": "07-07",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-07-003",
    "nazev": "Nákup",
    "proces_kod": "07-07",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-07-004",
    "nazev": "Autoprovoz",
    "proces_kod": "07-07",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-001",
    "nazev": "Personální správa",
    "proces_kod": "07-08",
    "vlastnik": "11; 33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-002",
    "nazev": "Personální controlling",
    "proces_kod": "07-08",
    "vlastnik": "11",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-003",
    "nazev": "Finanční řízení v oblasti lidských zdrojů",
    "proces_kod": "07-08",
    "vlastnik": "11",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-004",
    "nazev": "Odměňování",
    "proces_kod": "07-08",
    "vlastnik": "11",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-005",
    "nazev": "Péče o zaměstnance",
    "proces_kod": "07-08",
    "vlastnik": "11",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-006",
    "nazev": "Hodnocení zaměstnanců",
    "proces_kod": "07-08",
    "vlastnik": "11",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-007",
    "nazev": "Úřednické zkoušky",
    "proces_kod": "07-08",
    "vlastnik": "11",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-008",
    "nazev": "Vzdělávání a rozvoj zaměstnanců",
    "proces_kod": "07-08",
    "vlastnik": "11",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-009",
    "nazev": "Organizační vztahy a systemizace",
    "proces_kod": "07-08",
    "vlastnik": "33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-09-001",
    "nazev": "Analytické a expertní činnosti, které nejsou předmětem hlavní činnosti",
    "proces_kod": "07-09",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-09-002",
    "nazev": "Činnost v meziresortních a resortních pracovních skupinách a komisích",
    "proces_kod": "07-09",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-09-003",
    "nazev": "Vnitřní připomínková řízení - zpracování podkladů a stanovisek",
    "proces_kod": "07-09",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-09-004",
    "nazev": "Organizačně - technický servis pro jednání orgánů RHSD",
    "proces_kod": "07-09",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-10-001",
    "nazev": "Administrativní podpora - aktivity sekretariátu",
    "proces_kod": "07-10",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-10-002",
    "nazev": "Administrativní podpora - výroba prezentačního materiálu, tisk, zajišťování kancelářských potřeb, apod.",
    "proces_kod": "07-10",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-10-003",
    "nazev": "Organizace pracovních cest, návštěv a akcí, protokolární služby",
    "proces_kod": "07-10",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-10-004",
    "nazev": "Spisová služba",
    "proces_kod": "07-10",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-10-005",
    "nazev": "Správa archivu",
    "proces_kod": "07-10",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-10-006",
    "nazev": "Zajištění provozu podatelny",
    "proces_kod": "07-10",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-11-001",
    "nazev": "Náhrada škody podle zákona č. 82/1998 Sb.",
    "proces_kod": "07-11",
    "vlastnik": "33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-11-002",
    "nazev": "Náhrada škody podle zákona č. 262/2006 Sb.",
    "proces_kod": "07-11",
    "vlastnik": "33",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-12-001",
    "nazev": "Koncepční činnost v oblasti ICT včetně podřízených organizací",
    "proces_kod": "07-12",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-12-002",
    "nazev": "Provoz a rozvoj infrastruktury resortu, včetně napojení na externí prostředí",
    "proces_kod": "07-12",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-12-003",
    "nazev": "Provoz, údržba a rozvoj výpočetní techniky MPSV",
    "proces_kod": "07-12",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-12-004",
    "nazev": "Provoz, údržba a rozvoj výpočetní techniky ÚP ČR",
    "proces_kod": "07-12",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-12-005",
    "nazev": "Provoz, údržba a rozvoj výpočetní techniky obcí vykonávajících agendu hmotné nouze a sociálních služeb",
    "proces_kod": "07-12",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-12-006",
    "nazev": "Provoz, údržba a rozvoj informačních systémů, agend a databází MPSV",
    "proces_kod": "07-12",
    "vlastnik": "",
    "stav_rejstrik": "využitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-12-007",
    "nazev": "Provoz, údržba a rozvoj informačních systémů, agend a databází ÚP ČR",
    "proces_kod": "07-12",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-12-008",
    "nazev": "Provoz, údržba a rozvoj informačních systémů, agend a databází obcí vykonávajících agendu hmotné nouze a sociálních služeb",
    "proces_kod": "07-12",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-12-009",
    "nazev": "Finanční a smluvní zajištění výstavby a správy informačních systémů",
    "proces_kod": "07-12",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-12-010",
    "nazev": "Provoz, údržba a rozvoj komunikační infrastruktury resortu",
    "proces_kod": "07-12",
    "vlastnik": "",
    "stav_rejstrik": "nevyužitý",
    "zdroj": "rejstrik",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-006",
    "nazev": "Podezření ze spáchání protiprávního jednání",
    "proces_kod": "07-04",
    "vlastnik": "33",
    "stav_rejstrik": "",
    "zdroj": "karta",
    "puvodni_kod": ""
   }
  ]
 },
 {
  "list": "Aktivity",
  "rows": [
   {
    "Title": "01-02-002-0001",
    "nazev": "Koordinace plnění úkolů resortních služebních úřadů",
    "nazev_kratky": "Koordinace plnění úkolů resortních služebních úřadů",
    "dilci_proces_kod": "01-02-002",
    "vykonava": "331",
    "spolupracuje": "věcněpříslušné útvary MPSV, podřízené služební úřady",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-009-0001",
    "nazev": "Koordinace a schvalování návrhů systemizace resortních služebních úřadů v ISoSS (modul OSYS)",
    "nazev_kratky": "Koordinace a schvalování návrhů systemizace resortních služebních úřadů v ISoSS (modul OSYS)",
    "dilci_proces_kod": "07-08-009",
    "vykonava": "331",
    "spolupracuje": "odbor 11, sekce 6, podřízené služební úřady",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-009-0002",
    "nazev": "Tvorba Organizačního řádu MPSV a metodická činnost k vydávání služebních předpisů a metodických pokynů státního tajemníka",
    "nazev_kratky": "Tvorba Organizačního řádu MPSV a metodická činnost k vydávání služebních předpisů a metodických pokynů státního tajemníka",
    "dilci_proces_kod": "07-08-009",
    "vykonava": "331",
    "spolupracuje": "věcně příslušné útvary MPSV",
    "vnitrni_predpis": "SP 10/2021, SP 13/2025",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-009-0003",
    "nazev": "Tvorba Služebního řádu MPSV",
    "nazev_kratky": "Tvorba Služebního řádu MPSV",
    "dilci_proces_kod": "07-08-009",
    "vykonava": "332",
    "spolupracuje": "odbor 11",
    "vnitrni_predpis": "SP 7/2019",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-004-0001",
    "nazev": "Vyřizování stížností podle zákona o státní službě",
    "nazev_kratky": "Vyřizování stížností podle zákona o státní službě",
    "dilci_proces_kod": "07-04-004",
    "vykonava": "332",
    "spolupracuje": "věcněpříslušné útvary MPSV, podřízené služební úřady",
    "vnitrni_predpis": "SP 2/2024; SP 7/2019; SP 7/2021",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-001-0001",
    "nazev": "Realizace správního řízení v záležitostech státní služby (vybrané úkoly prvoinstančního služebního orgánu a postupování odvolacímu služebnímu orgánu)",
    "nazev_kratky": "Realizace správního řízení v záležitostech státní služby (vybrané úkoly prvoinstančního služebního orgánu a postupování odvolacímu služebnímu orgánu)",
    "dilci_proces_kod": "07-08-001",
    "vykonava": "332",
    "spolupracuje": "odbor 11",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-001-0002",
    "nazev": "Rozhodování státního tajemníka o odvoláních a v přezkumném řízení",
    "nazev_kratky": "Rozhodování státního tajemníka o odvoláních a v přezkumném řízení",
    "dilci_proces_kod": "07-08-001",
    "vykonava": "332",
    "spolupracuje": "podřízené služební úřady",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "01-01-001-0001",
    "nazev": "Koordinace řízení kvality v MPSV",
    "nazev_kratky": "Koordinace řízení kvality v MPSV",
    "dilci_proces_kod": "01-01-001",
    "vykonava": "331",
    "spolupracuje": "věcně příslušné útvary MPSV",
    "vnitrni_predpis": "PM 52/2019; MP ST 2/2022",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "01-01-001-0002",
    "nazev": "Koordinace strategického řízení v MPSV",
    "nazev_kratky": "Koordinace strategického řízení v MPSV",
    "dilci_proces_kod": "01-01-001",
    "vykonava": "331",
    "spolupracuje": "věcně příslušné útvary MPSV",
    "vnitrni_predpis": "PM 13/2023; SP 5/2023",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-01-004-0001",
    "nazev": "Vyřizování žádostí MPSV jako povinným subjektem podle zákona č. 106/1999 Sb.",
    "nazev_kratky": "Vyřizování žádostí MPSV jako povinným subjektem podle zákona č. 106/1999 Sb.",
    "dilci_proces_kod": "07-01-004",
    "vykonava": "331",
    "spolupracuje": "věcně příslušné útvary MPSV",
    "vnitrni_predpis": "PM 42/2016",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-01-004-0002",
    "nazev": "Rozhodování ministra o stížnostech na postup při vyřizování žádostí o informace podle zákona č. 106/1999 Sb.",
    "nazev_kratky": "Rozhodování ministra o stížnostech na postup při vyřizování žádostí o informace podle zákona č. 106/1999 Sb.",
    "dilci_proces_kod": "07-01-004",
    "vykonava": "332",
    "spolupracuje": "",
    "vnitrni_predpis": "PM 42/2016",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-01-004-0003",
    "nazev": "Činnosti MPSV jako odvolacího orgánu podle zákona č. 106/1999 Sb. (rozhodování ŘO 33, kontrolní činnost vůči podřízeným služebním úřadům)",
    "nazev_kratky": "Činnosti MPSV jako odvolacího orgánu podle zákona č. 106/1999 Sb. (rozhodování ŘO 33, kontrolní činnost vůči podřízeným služebním úřadům)",
    "dilci_proces_kod": "07-01-004",
    "vykonava": "331",
    "spolupracuje": "věcně příslušné útvary MPSV",
    "vnitrni_predpis": "PM 42/2016",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "01-05-001-0001",
    "nazev": "Tvorba Interního protikorupčního programu MPSV",
    "nazev_kratky": "Tvorba Interního protikorupčního programu MPSV",
    "dilci_proces_kod": "01-05-001",
    "vykonava": "331",
    "spolupracuje": "",
    "vnitrni_predpis": "PM 20/2018",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "01-05-002-0001",
    "nazev": "Tvorba a zajišťování Vnitřního oznamovacího systému MPSV pro podávání oznámení (korupce, obtěžování, zákon č. 171/2023 Sb.)",
    "nazev_kratky": "Tvorba a zajišťování Vnitřního oznamovacího systému MPSV pro podávání oznámení (korupce, obtěžování, zákon č. 171/2023 Sb.)",
    "dilci_proces_kod": "01-05-002",
    "vykonava": "331",
    "spolupracuje": "",
    "vnitrni_predpis": "VOS MPSV, PM 20/2018",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-004-0002",
    "nazev": "Koordinace vyřizování petic doručených MPSV",
    "nazev_kratky": "Koordinace vyřizování petic doručených MPSV",
    "dilci_proces_kod": "07-04-004",
    "vykonava": "331",
    "spolupracuje": "věcně příslušné útvary MPSV",
    "vnitrni_predpis": "PM 4/2021",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "01-05-003-0001",
    "nazev": "Průběžná aktualizace registru lobbovaných v MPSV v souladu se zákonem č. 168/2025 Sb.",
    "nazev_kratky": "Průběžná aktualizace registru lobbovaných v MPSV v souladu se zákonem č. 168/2025 Sb.",
    "dilci_proces_kod": "01-05-003",
    "vykonava": "331",
    "spolupracuje": "věcně příslušné útvary MPSV",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-004-0003",
    "nazev": "Metodická činnost pro vyřizování stížností podle správního řádu",
    "nazev_kratky": "Metodická činnost pro vyřizování stížností podle správního řádu",
    "dilci_proces_kod": "07-04-004",
    "vykonava": "332",
    "spolupracuje": "věcně příslušné útvary MPSV",
    "vnitrni_predpis": "PM 4/2021",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-11-001-0001",
    "nazev": "Vyřizování žádostí o náhradu škody podle zákona č. 82/1998 Sb.",
    "nazev_kratky": "Vyřizování žádostí o náhradu škody podle zákona č. 82/1998 Sb.",
    "dilci_proces_kod": "07-11-001",
    "vykonava": "332",
    "spolupracuje": "věcně příslušné útvary MPSV",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-11-002-0001",
    "nazev": "Projednávání nároků fyzických osob při pracovních úrazech a nemocech z povolání (§ 364 odst. 4 – 6 zák. č. 262/2006 Sb.)",
    "nazev_kratky": "Projednávání nároků fyzických osob při pracovních úrazech a nemocech z povolání (§ 364 odst. 4 – 6 zák. č. 262/2006 Sb.)",
    "dilci_proces_kod": "07-11-002",
    "vykonava": "332",
    "spolupracuje": "Generali pojišťovna a.s., Kooperativa pojišťovna, a.s., Vienna Insurance Group",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-11-002-0002",
    "nazev": "Koordinace odškodňování s pojišťovnami při pracovních úrazech a nemocech z povolání (§ 364 odst. 4 – 6 zák. č. 262/2006 Sb.)",
    "nazev_kratky": "Koordinace odškodňování s pojišťovnami při pracovních úrazech a nemocech z povolání (§ 364 odst. 4 – 6 zák. č. 262/2006 Sb.)",
    "dilci_proces_kod": "07-11-002",
    "vykonava": "332",
    "spolupracuje": "Generali pojišťovna a.s., Kooperativa pojišťovna, a.s., Vienna Insurance Group",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-002-0001",
    "nazev": "Zastupování před soudy - správní žaloby s výjimkou soudních sporů týkajících se zaměstnanosti a inspekce práce",
    "nazev_kratky": "Zastupování před soudy - správní žaloby s výjimkou soudních sporů týkajících se zaměstnanosti a inspekce práce",
    "dilci_proces_kod": "07-04-002",
    "vykonava": "332",
    "spolupracuje": "věcně příslušné útvary MPSV",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-002-0002",
    "nazev": "Zastupování před soudy - civilní žaloby s výjimkou soudních sporů týkajících se veřejných zakázek a smluv",
    "nazev_kratky": "Zastupování před soudy - civilní žaloby s výjimkou soudních sporů týkajících se veřejných zakázek a smluv",
    "dilci_proces_kod": "07-04-002",
    "vykonava": "332",
    "spolupracuje": "věcně příslušné útvary MPSV, podřízené služební úřady",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-002-0003",
    "nazev": "Zastupování před soudy - žaloby ve věcech týkajících se řídícího orgánu nebo zprostředkujícího subjektu OPZ/OPZ+",
    "nazev_kratky": "Zastupování před soudy - žaloby ve věcech týkajících se řídícího orgánu nebo zprostředkujícího subjektu OPZ/OPZ+",
    "dilci_proces_kod": "07-04-002",
    "vykonava": "332",
    "spolupracuje": "sekce evropských fondů a mezinárodní spolupráce",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-006-0001",
    "nazev": "Poskytování právní podpory při šetření záležitostí podezření ze spáchání protiprávního jednání ve služebním úřadu, jakož i vůči zaměstnancům MPSV, s výjimkou oblastí svěřených oddělení centrálních nákupů a právní podpory",
    "nazev_kratky": "Poskytování právní podpory při šetření záležitostí podezření ze spáchání protiprávního jednání ve služebním úřadu, jakož i vůči zaměstnancům MPSV, s…",
    "dilci_proces_kod": "07-04-006",
    "vykonava": "332",
    "spolupracuje": "věcně příslušné útvary MPSV",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-04-005-0001",
    "nazev": "Poskytování právněkonzultační podpory útvarům sekce státního tajemníka",
    "nazev_kratky": "Poskytování právněkonzultační podpory útvarům sekce státního tajemníka",
    "dilci_proces_kod": "07-04-005",
    "vykonava": "332",
    "spolupracuje": "O11, odd. 331",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "01-01-003-0001",
    "nazev": "příprava, zpracování a aktualizace materiálů (strategií, koncepcí, vnitřních řídicích aktů apod.) v rámci dílčího procesu Politika lidských zdrojů v působnosti personálního oddělení",
    "nazev_kratky": "příprava, zpracování a aktualizace materiálů (strategií, koncepcí, vnitřních řídicích aktů apod.) v rámci dílčího procesu Politika lidských zdrojů v…",
    "dilci_proces_kod": "01-01-003",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "SP Politika lidských zdrojů v MPSV; Služební řád MPSV; Pracovní řád MPSV; SP Strategie rozvoje služebního úřadu MPSV; SP Pravidla etiky státních zaměstnanců MPSV; PM Etický kodex zaměstnanců MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "01-01-003-0002",
    "nazev": "příprava, zpracování a aktualizace materiálů (strategií, koncepcí, vnitřních řídicích aktů apod.) v rámci dílčího procesu Politika lidských zdrojů v působnosti oddělení personálního rozvoje a metodik",
    "nazev_kratky": "příprava, zpracování a aktualizace materiálů (strategií, koncepcí, vnitřních řídicích aktů apod.) v rámci dílčího procesu Politika lidských zdrojů v…",
    "dilci_proces_kod": "01-01-003",
    "vykonava": "113",
    "spolupracuje": "",
    "vnitrni_predpis": "SP Politika lidských zdrojů v MPSV; Služební řád MPSV; Pracovní řád MPSV; SP Strategie rozvoje služebního úřadu MPSV; SP Pravidla etiky státních zaměstnanců MPSV; PM Etický kodex zaměstnanců MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "01-01-003-0003",
    "nazev": "příprava a zpracování organizačního uspořádání MPSV",
    "nazev_kratky": "příprava a zpracování organizačního uspořádání MPSV",
    "dilci_proces_kod": "01-01-003",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "SP, kterými se upravuje organizační struktura MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "01-01-004-0001",
    "nazev": "příprava a zpracování systemizace služebních a pracovních míst MPSV",
    "nazev_kratky": "příprava a zpracování systemizace služebních a pracovních míst MPSV",
    "dilci_proces_kod": "01-01-004",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "SP o systemizaci nebo změně systemizace služebních a pracovních míst; SP o charakteristice systemizovaného služebního/ pracovního místa státních zaměstnanců a zaměstnanců MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-001-0003",
    "nazev": "personální marketing, práce s uchazeči o zaměstnání, stáže",
    "nazev_kratky": "personální marketing, práce s uchazeči o zaměstnání, stáže",
    "dilci_proces_kod": "07-08-001",
    "vykonava": "113",
    "spolupracuje": "",
    "vnitrni_predpis": "SP Průběh a realizace odborných stáží",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-001-0004",
    "nazev": "výběrová řízení",
    "nazev_kratky": "výběrová řízení",
    "dilci_proces_kod": "07-08-001",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "SP MV o údajích zveřejňovaných v rámci výběrových řízení; MP NST, kterým se stanoví podrobnosti k provádění výběrových řízení",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-001-0005",
    "nazev": "nástupy nových zaměstnanců, převedení státních zaměstnanců z jiných služebních úřadů",
    "nazev_kratky": "nástupy nových zaměstnanců, převedení státních zaměstnanců z jiných služebních úřadů",
    "dilci_proces_kod": "07-08-001",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "Služební řád MPSV; Pracovní řád MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-001-0006",
    "nazev": "adaptační proces",
    "nazev_kratky": "adaptační proces",
    "dilci_proces_kod": "07-08-001",
    "vykonava": "113",
    "spolupracuje": "",
    "vnitrni_predpis": "SP Adaptační proces v MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-001-0007",
    "nazev": "slaďování rodinného a osobního života zaměstnanců",
    "nazev_kratky": "slaďování rodinného a osobního života zaměstnanců",
    "dilci_proces_kod": "07-08-001",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "Služební řád MPSV; Pracovní řád MPSV; SP pro sladění rodinného a osobního života s výkonem státní služby; SP, kterým se stanoví pružné rozvržení služební doby; PM Zásady režimu pružné pracovní doby na MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-001-0008",
    "nazev": "změny a skončení služebních/pracovních poměrů",
    "nazev_kratky": "změny a skončení služebních/pracovních poměrů",
    "dilci_proces_kod": "07-08-001",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "Služební řád MPSV; Pracovní řád MPSV; MP MV, kterým se stanoví podrobnosti ke změnám služebního poměru; MP MV, kterým se stanoví podrobnosti ke skončení služebního poměru",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-001-0009",
    "nazev": "správa dohod o pracovní činnosti a dohod o provedení práce",
    "nazev_kratky": "správa dohod o pracovní činnosti a dohod o provedení práce",
    "dilci_proces_kod": "07-08-001",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "Pracovní řád MPSV; Instrukce Postup schvalování a uzavírání dohod o pracích konaných mimo pracovní poměr na MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-002-0001",
    "nazev": "nastavení a zpracování personálních a platových ukazatelů, statistik, výkazů, přehledů apod., analýzy a predikce dat",
    "nazev_kratky": "nastavení a zpracování personálních a platových ukazatelů, statistik, výkazů, přehledů apod., analýzy a predikce dat",
    "dilci_proces_kod": "07-08-002",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-004-0001",
    "nazev": "stanovování platů",
    "nazev_kratky": "stanovování platů",
    "dilci_proces_kod": "07-08-004",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "Služební řád MPSV; Pracovní řád MPSV; SP, kterým se stanoví pravidla pro nastavení výše příplatků za vedení na MPSV; SP, kterým se stanoví pravidla pro určení výše zvláštních příplatků na MPSV; SP o označení klíčových služebních systemizovaných míst na MPSV a určení zvýšeného platového tarifu",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-004-0002",
    "nazev": "zpracování výplat, mzdové účetnictví",
    "nazev_kratky": "zpracování výplat, mzdové účetnictví",
    "dilci_proces_kod": "07-08-004",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "PM Zásady řídící kontroly v podmínkách MPSV; PM Oběh účetních dokladů na MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-003-0001",
    "nazev": "příprava rozpočtů, predikce čerpání, přehled skutečného čerpání",
    "nazev_kratky": "příprava rozpočtů, predikce čerpání, přehled skutečného čerpání",
    "dilci_proces_kod": "07-08-003",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "PM Zásady řídící kontroly v podmínkách MPSV; PM Oběh účetních dokladů na MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-005-0001",
    "nazev": "kolektivní dohoda, kolektivní smlouva, FKPS a benefity",
    "nazev_kratky": "kolektivní dohoda, kolektivní smlouva, FKPS a benefity",
    "dilci_proces_kod": "07-08-005",
    "vykonava": "111",
    "spolupracuje": "",
    "vnitrni_predpis": "Služební řád MPSV; Pracovní řád MPSV; Kolektivní dohoda MPSV; Kolektivní smlouva MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-005-0002",
    "nazev": "šetření spokojenosti zaměstnanců, výstupní dotazník",
    "nazev_kratky": "šetření spokojenosti zaměstnanců, výstupní dotazník",
    "dilci_proces_kod": "07-08-005",
    "vykonava": "113",
    "spolupracuje": "",
    "vnitrni_predpis": "MP ST Šetření spokojenosti zaměstnanců",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-007-0001",
    "nazev": "gestorství úřednických zkoušek v oborech státní služby spadajících pod MPSV",
    "nazev_kratky": "gestorství úřednických zkoušek v oborech státní služby spadajících pod MPSV",
    "dilci_proces_kod": "07-08-007",
    "vykonava": "113",
    "spolupracuje": "",
    "vnitrni_predpis": "SP NST o provádění a organizaci úřednických zkoušek",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-007-0002",
    "nazev": "realizace úřednických zkoušek",
    "nazev_kratky": "realizace úřednických zkoušek",
    "dilci_proces_kod": "07-08-007",
    "vykonava": "113",
    "spolupracuje": "",
    "vnitrni_predpis": "SP NST o provádění a organizaci úřednických zkoušek; SP, kterým se vydává jednací řád zkušebních komisí ÚZ v resortu MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-006-0001",
    "nazev": "nastavení, příprava a realizace metodik a aktivit v oblasti hodnocení zaměstnanců",
    "nazev_kratky": "nastavení, příprava a realizace metodik a aktivit v oblasti hodnocení zaměstnanců",
    "dilci_proces_kod": "07-08-006",
    "vykonava": "113",
    "spolupracuje": "",
    "vnitrni_predpis": "SP, kterým se stanoví postup při realizaci a zabezpečení průběhu služebního hodnocení státních zaměstnanců MPSV a vedoucích služebních úřadů v resortu MPSV; SP NST, kterým se stanoví postup při provádění služebního hodnocení státních zaměstnanců",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   },
   {
    "Title": "07-08-008-0001",
    "nazev": "nastavení, příprava a realizace metodik a aktivit v oblasti vzdělávání a rozvoje zaměstnanců",
    "nazev_kratky": "nastavení, příprava a realizace metodik a aktivit v oblasti vzdělávání a rozvoje zaměstnanců",
    "dilci_proces_kod": "07-08-008",
    "vykonava": "113",
    "spolupracuje": "",
    "vnitrni_predpis": "SP, kterým se stanoví Rámcová pravidla vzdělávání na MPSV; SP, kterým se stanoví Rámcová pravidla jazykového vzdělávání zaměstnanců MPSV",
    "text_pro_or": "",
    "sekce": "3",
    "stav": "pracovní",
    "datum_aktualizace": "2026-09-08T00:00:00Z",
    "puvodni_kod": ""
   }
  ]
 },
 {
  "list": "AktivitaDilciProces",
  "rows": [
   {
    "Title": "01-02-002-0001__01-02-002",
    "aktivita_kod": "01-02-002-0001",
    "dilci_proces_kod": "01-02-002",
    "primarni": "ano"
   },
   {
    "Title": "07-08-009-0001__07-08-009",
    "aktivita_kod": "07-08-009-0001",
    "dilci_proces_kod": "07-08-009",
    "primarni": "ano"
   },
   {
    "Title": "07-08-009-0002__07-08-009",
    "aktivita_kod": "07-08-009-0002",
    "dilci_proces_kod": "07-08-009",
    "primarni": "ano"
   },
   {
    "Title": "07-08-009-0003__07-08-009",
    "aktivita_kod": "07-08-009-0003",
    "dilci_proces_kod": "07-08-009",
    "primarni": "ano"
   },
   {
    "Title": "07-04-004-0001__07-04-004",
    "aktivita_kod": "07-04-004-0001",
    "dilci_proces_kod": "07-04-004",
    "primarni": "ano"
   },
   {
    "Title": "07-08-001-0001__07-08-001",
    "aktivita_kod": "07-08-001-0001",
    "dilci_proces_kod": "07-08-001",
    "primarni": "ano"
   },
   {
    "Title": "07-08-001-0002__07-08-001",
    "aktivita_kod": "07-08-001-0002",
    "dilci_proces_kod": "07-08-001",
    "primarni": "ano"
   },
   {
    "Title": "01-01-001-0001__01-01-001",
    "aktivita_kod": "01-01-001-0001",
    "dilci_proces_kod": "01-01-001",
    "primarni": "ano"
   },
   {
    "Title": "01-01-001-0002__01-01-001",
    "aktivita_kod": "01-01-001-0002",
    "dilci_proces_kod": "01-01-001",
    "primarni": "ano"
   },
   {
    "Title": "07-01-004-0001__07-01-004",
    "aktivita_kod": "07-01-004-0001",
    "dilci_proces_kod": "07-01-004",
    "primarni": "ano"
   },
   {
    "Title": "07-01-004-0002__07-01-004",
    "aktivita_kod": "07-01-004-0002",
    "dilci_proces_kod": "07-01-004",
    "primarni": "ano"
   },
   {
    "Title": "07-01-004-0003__07-01-004",
    "aktivita_kod": "07-01-004-0003",
    "dilci_proces_kod": "07-01-004",
    "primarni": "ano"
   },
   {
    "Title": "01-05-001-0001__01-05-001",
    "aktivita_kod": "01-05-001-0001",
    "dilci_proces_kod": "01-05-001",
    "primarni": "ano"
   },
   {
    "Title": "01-05-002-0001__01-05-002",
    "aktivita_kod": "01-05-002-0001",
    "dilci_proces_kod": "01-05-002",
    "primarni": "ano"
   },
   {
    "Title": "07-04-004-0002__07-04-004",
    "aktivita_kod": "07-04-004-0002",
    "dilci_proces_kod": "07-04-004",
    "primarni": "ano"
   },
   {
    "Title": "01-05-003-0001__01-05-003",
    "aktivita_kod": "01-05-003-0001",
    "dilci_proces_kod": "01-05-003",
    "primarni": "ano"
   },
   {
    "Title": "07-04-004-0003__07-04-004",
    "aktivita_kod": "07-04-004-0003",
    "dilci_proces_kod": "07-04-004",
    "primarni": "ano"
   },
   {
    "Title": "07-11-001-0001__07-11-001",
    "aktivita_kod": "07-11-001-0001",
    "dilci_proces_kod": "07-11-001",
    "primarni": "ano"
   },
   {
    "Title": "07-11-002-0001__07-11-002",
    "aktivita_kod": "07-11-002-0001",
    "dilci_proces_kod": "07-11-002",
    "primarni": "ano"
   },
   {
    "Title": "07-11-002-0002__07-11-002",
    "aktivita_kod": "07-11-002-0002",
    "dilci_proces_kod": "07-11-002",
    "primarni": "ano"
   },
   {
    "Title": "07-04-002-0001__07-04-002",
    "aktivita_kod": "07-04-002-0001",
    "dilci_proces_kod": "07-04-002",
    "primarni": "ano"
   },
   {
    "Title": "07-04-002-0002__07-04-002",
    "aktivita_kod": "07-04-002-0002",
    "dilci_proces_kod": "07-04-002",
    "primarni": "ano"
   },
   {
    "Title": "07-04-002-0003__07-04-002",
    "aktivita_kod": "07-04-002-0003",
    "dilci_proces_kod": "07-04-002",
    "primarni": "ano"
   },
   {
    "Title": "07-04-006-0001__07-04-006",
    "aktivita_kod": "07-04-006-0001",
    "dilci_proces_kod": "07-04-006",
    "primarni": "ano"
   },
   {
    "Title": "07-04-005-0001__07-04-005",
    "aktivita_kod": "07-04-005-0001",
    "dilci_proces_kod": "07-04-005",
    "primarni": "ano"
   },
   {
    "Title": "01-01-003-0001__01-01-003",
    "aktivita_kod": "01-01-003-0001",
    "dilci_proces_kod": "01-01-003",
    "primarni": "ano"
   },
   {
    "Title": "01-01-003-0002__01-01-003",
    "aktivita_kod": "01-01-003-0002",
    "dilci_proces_kod": "01-01-003",
    "primarni": "ano"
   },
   {
    "Title": "01-01-003-0003__01-01-003",
    "aktivita_kod": "01-01-003-0003",
    "dilci_proces_kod": "01-01-003",
    "primarni": "ano"
   },
   {
    "Title": "01-01-004-0001__01-01-004",
    "aktivita_kod": "01-01-004-0001",
    "dilci_proces_kod": "01-01-004",
    "primarni": "ano"
   },
   {
    "Title": "07-08-001-0003__07-08-001",
    "aktivita_kod": "07-08-001-0003",
    "dilci_proces_kod": "07-08-001",
    "primarni": "ano"
   },
   {
    "Title": "07-08-001-0004__07-08-001",
    "aktivita_kod": "07-08-001-0004",
    "dilci_proces_kod": "07-08-001",
    "primarni": "ano"
   },
   {
    "Title": "07-08-001-0005__07-08-001",
    "aktivita_kod": "07-08-001-0005",
    "dilci_proces_kod": "07-08-001",
    "primarni": "ano"
   },
   {
    "Title": "07-08-001-0006__07-08-001",
    "aktivita_kod": "07-08-001-0006",
    "dilci_proces_kod": "07-08-001",
    "primarni": "ano"
   },
   {
    "Title": "07-08-001-0007__07-08-001",
    "aktivita_kod": "07-08-001-0007",
    "dilci_proces_kod": "07-08-001",
    "primarni": "ano"
   },
   {
    "Title": "07-08-001-0008__07-08-001",
    "aktivita_kod": "07-08-001-0008",
    "dilci_proces_kod": "07-08-001",
    "primarni": "ano"
   },
   {
    "Title": "07-08-001-0009__07-08-001",
    "aktivita_kod": "07-08-001-0009",
    "dilci_proces_kod": "07-08-001",
    "primarni": "ano"
   },
   {
    "Title": "07-08-002-0001__07-08-002",
    "aktivita_kod": "07-08-002-0001",
    "dilci_proces_kod": "07-08-002",
    "primarni": "ano"
   },
   {
    "Title": "07-08-004-0001__07-08-004",
    "aktivita_kod": "07-08-004-0001",
    "dilci_proces_kod": "07-08-004",
    "primarni": "ano"
   },
   {
    "Title": "07-08-004-0002__07-08-004",
    "aktivita_kod": "07-08-004-0002",
    "dilci_proces_kod": "07-08-004",
    "primarni": "ano"
   },
   {
    "Title": "07-08-003-0001__07-08-003",
    "aktivita_kod": "07-08-003-0001",
    "dilci_proces_kod": "07-08-003",
    "primarni": "ano"
   },
   {
    "Title": "07-08-005-0001__07-08-005",
    "aktivita_kod": "07-08-005-0001",
    "dilci_proces_kod": "07-08-005",
    "primarni": "ano"
   },
   {
    "Title": "07-08-005-0002__07-08-005",
    "aktivita_kod": "07-08-005-0002",
    "dilci_proces_kod": "07-08-005",
    "primarni": "ano"
   },
   {
    "Title": "07-08-007-0001__07-08-007",
    "aktivita_kod": "07-08-007-0001",
    "dilci_proces_kod": "07-08-007",
    "primarni": "ano"
   },
   {
    "Title": "07-08-007-0002__07-08-007",
    "aktivita_kod": "07-08-007-0002",
    "dilci_proces_kod": "07-08-007",
    "primarni": "ano"
   },
   {
    "Title": "07-08-006-0001__07-08-006",
    "aktivita_kod": "07-08-006-0001",
    "dilci_proces_kod": "07-08-006",
    "primarni": "ano"
   },
   {
    "Title": "07-08-008-0001__07-08-008",
    "aktivita_kod": "07-08-008-0001",
    "dilci_proces_kod": "07-08-008",
    "primarni": "ano"
   }
  ]
 },
 {
  "list": "Utvary",
  "rows": [
   {
    "Title": "0",
    "nazev": "Ministr",
    "uroven": "ministr",
    "nadrizeny_kod": ""
   },
   {
    "Title": "12",
    "nazev": "O12",
    "uroven": "odbor",
    "nadrizeny_kod": "0"
   },
   {
    "Title": "121",
    "nazev": "O121",
    "uroven": "oddělení",
    "nadrizeny_kod": "12"
   },
   {
    "Title": "122",
    "nazev": "O122",
    "uroven": "oddělení",
    "nadrizeny_kod": "12"
   },
   {
    "Title": "3",
    "nazev": "Sekce 3",
    "uroven": "sekce",
    "nadrizeny_kod": "0"
   },
   {
    "Title": "11",
    "nazev": "O11",
    "uroven": "odbor",
    "nadrizeny_kod": "3"
   },
   {
    "Title": "111",
    "nazev": "O111",
    "uroven": "oddělení",
    "nadrizeny_kod": "11"
   },
   {
    "Title": "113",
    "nazev": "O113",
    "uroven": "oddělení",
    "nadrizeny_kod": "11"
   },
   {
    "Title": "33",
    "nazev": "O33",
    "uroven": "odbor",
    "nadrizeny_kod": "3"
   },
   {
    "Title": "331",
    "nazev": "O331",
    "uroven": "oddělení",
    "nadrizeny_kod": "33"
   },
   {
    "Title": "332",
    "nazev": "O332",
    "uroven": "oddělení",
    "nadrizeny_kod": "33"
   },
   {
    "Title": "4",
    "nazev": "Sekce 4",
    "uroven": "sekce",
    "nadrizeny_kod": "0"
   },
   {
    "Title": "401",
    "nazev": "O401",
    "uroven": "oddělení",
    "nadrizeny_kod": "4"
   },
   {
    "Title": "42",
    "nazev": "O42",
    "uroven": "odbor",
    "nadrizeny_kod": "4"
   },
   {
    "Title": "422",
    "nazev": "O422",
    "uroven": "oddělení",
    "nadrizeny_kod": "42"
   },
   {
    "Title": "424",
    "nazev": "O424",
    "uroven": "oddělení",
    "nadrizeny_kod": "42"
   },
   {
    "Title": "425",
    "nazev": "O425",
    "uroven": "odbor",
    "nadrizeny_kod": "42"
   },
   {
    "Title": "44",
    "nazev": "O44",
    "uroven": "odbor",
    "nadrizeny_kod": "4"
   },
   {
    "Title": "443",
    "nazev": "O443",
    "uroven": "oddělení",
    "nadrizeny_kod": "44"
   },
   {
    "Title": "445",
    "nazev": "O445",
    "uroven": "oddělení",
    "nadrizeny_kod": "44"
   },
   {
    "Title": "45",
    "nazev": "O45",
    "uroven": "odbor",
    "nadrizeny_kod": "4"
   },
   {
    "Title": "451",
    "nazev": "O451",
    "uroven": "oddělení",
    "nadrizeny_kod": "45"
   },
   {
    "Title": "452",
    "nazev": "O452",
    "uroven": "oddělení",
    "nadrizeny_kod": "45"
   },
   {
    "Title": "453",
    "nazev": "O453",
    "uroven": "oddělení",
    "nadrizeny_kod": "45"
   },
   {
    "Title": "6",
    "nazev": "Sekce 6",
    "uroven": "sekce",
    "nadrizeny_kod": "0"
   },
   {
    "Title": "601",
    "nazev": "O601",
    "uroven": "oddělení",
    "nadrizeny_kod": "6"
   },
   {
    "Title": "32",
    "nazev": "O32",
    "uroven": "odbor",
    "nadrizeny_kod": "6"
   },
   {
    "Title": "322",
    "nazev": "O322",
    "uroven": "oddělení",
    "nadrizeny_kod": "32"
   },
   {
    "Title": "323",
    "nazev": "O323",
    "uroven": "oddělení",
    "nadrizeny_kod": "32"
   },
   {
    "Title": "325",
    "nazev": "O325",
    "uroven": "oddělení",
    "nadrizeny_kod": "32"
   },
   {
    "Title": "34",
    "nazev": "O34",
    "uroven": "odbor",
    "nadrizeny_kod": "6"
   },
   {
    "Title": "341",
    "nazev": "O341",
    "uroven": "oddělení",
    "nadrizeny_kod": "34"
   },
   {
    "Title": "342",
    "nazev": "O342",
    "uroven": "oddělení",
    "nadrizeny_kod": "34"
   },
   {
    "Title": "35",
    "nazev": "O35",
    "uroven": "odbor",
    "nadrizeny_kod": "6"
   },
   {
    "Title": "351",
    "nazev": "O351",
    "uroven": "oddělení",
    "nadrizeny_kod": "35"
   },
   {
    "Title": "356",
    "nazev": "O356",
    "uroven": "oddělení",
    "nadrizeny_kod": "35"
   },
   {
    "Title": "357",
    "nazev": "O357",
    "uroven": "oddělení",
    "nadrizeny_kod": "35"
   },
   {
    "Title": "61",
    "nazev": "O61",
    "uroven": "odbor",
    "nadrizeny_kod": "6"
   },
   {
    "Title": "611",
    "nazev": "O611",
    "uroven": "oddělení",
    "nadrizeny_kod": "61"
   },
   {
    "Title": "612",
    "nazev": "O612",
    "uroven": "oddělení",
    "nadrizeny_kod": "61"
   },
   {
    "Title": "62",
    "nazev": "O62",
    "uroven": "odbor",
    "nadrizeny_kod": "6"
   },
   {
    "Title": "621",
    "nazev": "O621",
    "uroven": "oddělení",
    "nadrizeny_kod": "62"
   },
   {
    "Title": "622",
    "nazev": "O622",
    "uroven": "oddělení",
    "nadrizeny_kod": "62"
   },
   {
    "Title": "623",
    "nazev": "O623",
    "uroven": "oddělení",
    "nadrizeny_kod": "62"
   }
  ]
 }
];

const VERBOSE = "application/json;odata=verbose";
let WEB = null, DIGEST = null;

async function urciWeb() {
  if (typeof _spPageContextInfo === "object" && _spPageContextInfo &&
      _spPageContextInfo.webAbsoluteUrl) {
    return _spPageContextInfo.webAbsoluteUrl.replace(/\/$/, "");
  }
  const u = new URL(location.href);
  const casti = u.pathname.split("/").filter(Boolean);
  for (let i = casti.length; i >= 0; i--) {
    const kandidat = u.origin + (i ? "/" + casti.slice(0, i).join("/") : "");
    try {
      const r = await fetch(kandidat + "/_api/web?$select=ServerRelativeUrl",
                            { headers: { Accept: "application/json;odata=nometadata" },
                              credentials: "same-origin" });
      if (r.ok) return kandidat;
    } catch (e) { /* zkousime kratsi cestu */ }
  }
  throw new Error("nepodarilo se urcit SharePoint web z adresy " + location.href);
}

async function digest() {
  const r = await fetch(WEB + "/_api/contextinfo", {
    method: "POST", headers: { Accept: VERBOSE }, credentials: "same-origin",
  });
  if (!r.ok) throw new Error("contextinfo selhalo: HTTP " + r.status);
  return (await r.json()).d.GetContextWebInformation.FormDigestValue;
}

async function get(cesta) {
  const r = await fetch(WEB + "/_api/" + cesta, {
    headers: { Accept: "application/json;odata=nometadata" },
    credentials: "same-origin",
  });
  if (!r.ok) throw new Error("GET " + cesta + " -> HTTP " + r.status + " " +
                             (await r.text()).slice(0, 300));
  return r.json();
}

async function post(cesta, telo) {
  const r = await fetch(WEB + "/_api/" + cesta, {
    method: "POST",
    headers: { Accept: VERBOSE, "Content-Type": VERBOSE, "X-RequestDigest": DIGEST },
    credentials: "same-origin",
    body: JSON.stringify(telo),
  });
  if (!r.ok) throw new Error("HTTP " + r.status + " " + (await r.text()).slice(0, 300));
  const t = await r.text();
  return t ? JSON.parse(t) : null;
}

async function najdiList(nazev) {
  const j = await get("web/lists?$select=Id,Title,ListItemEntityTypeFullName," +
                      "RootFolder/ServerRelativeUrl&$expand=RootFolder&$top=500");
  const konec = "/lists/" + nazev.toLowerCase();
  return (j.value || []).find(
    (l) => l.RootFolder && l.RootFolder.ServerRelativeUrl.toLowerCase().endsWith(konec)) || null;
}

async function existujiciKlice(id) {
  // $top=5000 kvuli 250 dilcim procesum - vychozi stranka ma 100 polozek.
  const klice = new Set();
  let cesta = "web/lists(guid'" + id + "')/items?$select=Title&$top=5000";
  while (cesta) {
    const j = await get(cesta);
    (j.value || []).forEach((r) => { if (r.Title) klice.add(r.Title); });
    const dalsi = j["odata.nextLink"] || j.__next || null;
    cesta = dalsi ? dalsi.replace(WEB + "/_api/", "") : null;
  }
  return klice;
}

// ---------- hlavni beh ----------

WEB = await urciWeb();
DIGEST = await digest();
console.log("web: " + WEB);

const souhrn = [];
const chyby = [];

for (const tab of DATA) {
  const list = await najdiList(tab.list);
  if (!list) {
    chyby.push({ list: tab.list, klic: "-", chyba: "list neexistuje - spust nejdriv setup_sharepoint.js" });
    souhrn.push({ list: tab.list, ve_zdroji: tab.rows.length, zalozeno: 0,
                  preskoceno: 0, chyb: 1 });
    continue;
  }
  const typ = list.ListItemEntityTypeFullName;
  const uz = await existujiciKlice(list.Id);

  let zalozeno = 0, preskoceno = 0, chybnych = 0;
  for (const r of tab.rows) {
    if (uz.has(r.Title)) { preskoceno++; continue; }
    try {
      await post("web/lists(guid'" + list.Id + "')/items",
                 Object.assign({ __metadata: { type: typ } }, r));
      zalozeno++;
    } catch (e) {
      chybnych++;
      chyby.push({ list: tab.list, klic: r.Title, chyba: e.message });
    }
    if ((zalozeno + chybnych) % 25 === 0) {
      console.log("  " + tab.list + ": " + (zalozeno + chybnych) + "/" +
                  (tab.rows.length - preskoceno));
    }
  }
  souhrn.push({ list: tab.list, ve_zdroji: tab.rows.length, zalozeno: zalozeno,
                preskoceno: preskoceno, chyb: chybnych });
}

console.table(souhrn);
if (chyby.length) {
  console.log("CHYBY (" + chyby.length + "):");
  console.table(chyby.slice(0, 50));
}

const ocekavano = DATA.map((t) => t.list + "=" + t.rows.length).join(", ");
const skutecnost = souhrn.map((s) => s.list + "=" + (s.zalozeno + s.preskoceno)).join(", ");
console.log("ocekavano:  " + ocekavano);
console.log("v listech:  " + skutecnost);
console.log(chyby.length === 0 && ocekavano === skutecnost
  ? "HOTOVO: vsechny polozky jsou v listech"
  : "POZOR: vysledek nesedi na zdroj - viz tabulky vyse");

})().catch((e) => console.error("import_data selhal:", e));
