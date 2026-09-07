# -*- coding: utf-8 -*-
"""Přidá do solution flow ImportFlow — hromadné pořízení aktivit z .xlsx.

Čte vyplněný sešit z knihovny `Import` konektorem Excel Online (Business),
zkontroluje řádky proti rejstříku a v režimu zápisu založí aktivity i jejich
primární vazbu. Vstup je jeden text:

    {"soubor": "karta_s3.xlsx", "rezim": "nahled" | "zapis"}

Odpověď nese rozpad „co vznikne / co je duplicita / co je chyba" a u chybných
řádků i **číslo řádku v sešitě**, aby je správce našel.

Co se o konektoru ověřilo měřením (01.09.2026, PPF DEV), ne odhadem:

- `file` **smí být dynamický** — bere `Id` z `Get file metadata using path`;
- `table` **stačí jménem** (`Aktivity`), konektor tabulky vyhledává podle názvu;
- `drive` **musí být Graph ID `b!…`** — jméno knihovny skončí na
  `The provided drive id appears to be malformed`;
- `_api/v2.0/drives` na webu **odpovídá**, takže si flow to ID najde samo
  a balík nepotřebuje žádnou novou proměnnou prostředí. Hledá se podle
  **URL segmentu** knihovny, ne podle zobrazovaného názvu: ten nese diakritiku
  a mění se přejmenováním, kdežto segment je interní název ze schématu.

Prázdný řádek, se kterým se šablona vydává, se musí přeskočit — jinak by první
použití šablony založilo prázdnou aktivitu.

`nazev_kratky` se NEZAPISUJE: dopočítá ho flow `AktualizaceKratkehoNazvu`,
které visí na „item is created or modified" nad listem Aktivity.

Pořadí je závazné: **nejdřív tenhle generátor, teprve pak `build_app.py`**
(deklarace parametrů doplňuje jedno místo v buildu).

    copy input/<export>.zip runs/vstup_85.zip
    python src/odeber_flow.py --solution runs/vstup_85.zip --flow <testovaci>
    python src/build_import_flow.py --solution runs/vstup_85.zip
    python src/build_app.py --solution runs/vstup_85.zip --verze 1.0.0.85
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402

ZDROJ = "MapaPublishFlow"
FLOW = "ImportFlow"
FLOW_GUID = "7d3a9f52-46c1-4e88-b0d7-19e6c4a35f10"

SCHEMA = Path("src/schema.json")
KNIHOVNA = "Import"          # URL segment i zobrazovaný název — schválně bez diakritiky
TABULKA = "Aktivity"         # jméno Tabulky v šabloně; generuje ji make_sablona.py
LIST_AKTIVITY = "Aktivity"
LIST_DILCI = "DilciProcesy"
LIST_VAZBY = "AktivitaDilciProces"
LIST_AGENDY = "Agendy"
LIST_PROCESY = "Procesy"

# Vlastníci nadřazených úrovní: sešit je nese u KAŽDÉ aktivity, protože jinou
# cestu než appku sekce nemá. Kód rodiče se odvodí z kódu dílčího procesu na
# témž řádku — `01-01-001` dá agendu `01` a proces `01-01`.
#
# Cena té volby: hodnota se opakuje na každém řádku téže agendy, takže si dva
# řádky mohou odporovat. Rozpor se OHLÁSÍ a vlastníci té úrovně se nezapíšou;
# aktivity se založí normálně. Tiché „poslední vyhrává" by znamenalo, že
# vlastník závisí na pořadí řádků v sešitu.
UROVNE_VLASTNIKU = [
    {"klic": "agendy", "sloupec": "_vlastnik_agendy", "list": LIST_AGENDY,
     "delka": 2, "popis": "agendy"},
    {"klic": "procesu", "sloupec": "_vlastnik_procesu", "list": LIST_PROCESY,
     "delka": 5, "popis": "procesu"},
    {"klic": "dilcich", "sloupec": "_vlastnik_dilciho", "list": LIST_DILCI,
     "delka": 9, "popis": "dílčího procesu"},
]

# Technický rodič nezařazených aktivit. Vlastník se k němu nepřipisuje —
# není to skutečná agenda.
NEZARAZENY_PREFIX = "00"

HOST_SP = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"
HOST_XLS = "/providers/Microsoft.PowerApps/apis/shared_excelonlinebusiness"

STRANKOVANI = 5000
REZIM_ZAPIS = "zapis"
# Třetí režim: vrátí jen seznam sešitů v knihovně. Appka nemá knihovnu
# `Import` připojenou jako datový zdroj a připojit ji jde jedině ve Studiu,
# tedy dalším kolem. Schéma odpovědi se tím nemění (pořád čtyři řetězce),
# takže flow nepotřebuje novou registraci.
REZIM_SEZNAM = "seznam"

# Pořadí čísel v přehledu je součástí kontraktu s obrazovkou náhledu.
# `Nezarazene` je podmnožina `K_zalozeni`, ne další skupina rozkladu — proto
# je na konci a v součtu se nezapočítává.
POCTY = ("Ocistene", "Prazdne", "K_zalozeni", "Duplicitni",
         "Chybne", "Neznamy_dilci", "Nezarazene")
VYCHOZI_STAV = "pracovní"

# Sloupec, do kterého se dosazuje technický rodič, když správce nahraje
# aktivitu bez zařazení.
KOD_RODICE_SLOUPEC = "dilci_proces_kod"

# Kód technického dílčího procesu „Nezařazeno". Čte se ze schématu, protože
# tutéž hodnotu zakládá provisioning (make_setup.py) — dvě místa s natvrdo
# psaným kódem by se rozešla a import by zakládal sirotky pod dílčí proces,
# který v rejstříku není.
KOD_NEZARAZENO = json.loads(
    SCHEMA.read_text(encoding="utf-8"))["seed"]["prefix_nezarazeno"]

# Oddělovač odvozeného klíče vazby. Týž tvar zakládá appka na obrazovce vazeb
# (`varAktivita.Title & "__" & ThisItem.Title`) — kdyby se lišil, vyrobil by
# import duplicitní vazby, které by appka neuměla najít.
SPOJKA_VAZBY = "__"

# Odpovědi jdou appce jako ODDĚLOVANÝ TEXT, ne JSON. Canvas app má
# `dynamicschema = False`, takže by na `ParseJSON` neměla co navázat;
# `Split()` funguje vždycky. Oddělovače jsou zvolené tak, aby se nemohly
# potkat v názvu aktivity ani souboru.
ODD_POLE = "|~|"
ODD_RADKU = "|#|"


HLAVICKY_ZAPIS = {
    "Accept": "application/json;odata=nometadata",
    "Content-Type": "application/json;odata=nometadata",
}
HLAVICKY_CTENI = {"Accept": "application/json;odata=nometadata"}


def nacti_schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def lit(hodnota):
    return "'" + str(hodnota).replace("'", "''") + "'"


def list_ze_schematu(schema, jmeno):
    return next(l for l in schema["lists"] if l["name"] == jmeno)


def sloupce_sablony(schema):
    """Tytéž sloupce, jaké generuje make_sablona.py — systémové v šabloně nejsou."""
    systemove = {"Title", "nazev_kratky", "datum_aktualizace", "puvodni_kod"}
    return [c for c in list_ze_schematu(schema, LIST_AKTIVITY)["columns"]
            if c["name"] not in systemove]


def sloupce_vlastniku():
    """Sloupce vlastníků tak, jak je do sešitu píše make_sablona.py.

    Bere se odtamtud, ne z vlastní kopie: kdyby se hlavičky rozešly, flow by
    četlo prázdno a import by tiše nezapsal nic.
    """
    from make_sablona import VLASTNICI_NADRAZENYCH
    return VLASTNICI_NADRAZENYCH


def sp_akce(operace, parametry, po):
    return {
        "type": "OpenApiConnection",
        "inputs": {
            "parameters": parametry,
            "host": {"apiId": HOST_SP, "operationId": operace,
                     "connectionName": "shared_sharepointonline"},
        },
        "runAfter": {po: ["Succeeded"]} if po else {},
    }


def rest(metoda, uri, po, telo=None, hlavicky=None):
    parametry = {
        "dataset": ep.web(),
        "parameters/method": metoda,
        "parameters/uri": uri,
        "parameters/headers": hlavicky or HLAVICKY_CTENI,
    }
    if telo is not None:
        parametry["parameters/body"] = telo
    return sp_akce("HttpRequest", parametry, po)


def rest_list(jmeno_listu, uvnitr=""):
    """REST adresa listu podle interního názvu — na všech tenantech stejná."""
    return (f"@concat('_api/web/GetList(''', outputs('Cesta_webu'),"
            f" {lit('/Lists/' + jmeno_listu)}, ''')/items{uvnitr}')")


def bunka(sloupec):
    """Hodnota buňky sešitu. Klíčem je hlavička, tedy zobrazovaný název sloupce."""
    return (f"trim(string(coalesce(body('Radky')?['value'][item()]"
            f"?[{lit(sloupec['display'])}], '')))")


class Kroky(dict):
    """Akce flow; tiché přepsání jména je chyba, ne přepis.

    F16/2 zavedlo `Kody_dilcich` podruhé a smazalo tím validační akci téhož
    jména. Generátor doběhl, brány prošly a projevilo se to až tím, že flow
    nešlo zapnout: `The circular dependency detected in template language
    expressions` (07.09.2026, PPF DEV).
    """

    def __setitem__(self, klic, hodnota):
        if klic in self:
            raise SystemExit(
                f"CHYBA: akce '{klic}' se v definici objevila podruhé — "
                f"jméno už patří jiné akci, zvol jiné")
        super().__setitem__(klic, hodnota)


def akce(schema):
    kroky = Kroky()
    sloupce = sloupce_sablony(schema)
    podle_jmena = {c["name"]: c for c in sloupce}

    kroky["Vstup"] = {"type": "Compose",
                      "inputs": "@json(triggerBody()['text'])", "runAfter": {}}

    kroky["Cesta_webu"] = {
        "type": "Compose",
        "inputs": f"@concat('/', join(skip(split({ep.vyraz(ep.WEB)}, '/'), 3), '/'))",
        "runAfter": {"Vstup": ["Succeeded"]},
    }

    # Režim seznamu končí vlastní odpovědí a ukončením běhu — dál se nepokračuje,
    # protože bez názvu souboru by `Soubor` neměl co dohledat.
    kroky["Rezim_seznam"] = {
        "type": "If",
        "expression": {"equals": ["@outputs('Vstup')?['rezim']", REZIM_SEZNAM]},
        "actions": {
            "Soubory": rest(
                "GET",
                ("@concat('_api/web/GetList(" + chr(39) * 3 + ", outputs('Cesta_webu'), "
                 + lit("/" + KNIHOVNA) + ", " + chr(39) * 3
                 + ")/items?$select=FileLeafRef&$top=500&$orderby=Modified desc')"),
                None),
            "Jmena": {
                "type": "Select",
                "inputs": {
                    "from": "@coalesce(body('Soubory')?['value'], createArray())",
                    "select": "@item()?['FileLeafRef']",
                },
                "runAfter": {"Soubory": ["Succeeded"]},
            },
            "Odpoved_seznam": {
                "type": "Response",
                "kind": "PowerApp",
                "inputs": {
                    "statusCode": 200,
                    "body": {
                        "stav": REZIM_SEZNAM,
                        "soubor": "",
                        "prehled": ("@join(body('Jmena'), "
                                    + lit(ODD_RADKU) + ")"),
                        "chyby": "[]",
                    },
                    "schema": {"type": "object", "properties": {
                        "stav": {"type": "string"},
                        "soubor": {"type": "string"},
                        "prehled": {"type": "string"},
                        "chyby": {"type": "string"},
                    }},
                },
                "runAfter": {"Jmena": ["Succeeded"]},
            },
            "Konec": {
                "type": "Terminate",
                "inputs": {"runStatus": "Succeeded"},
                "runAfter": {"Odpoved_seznam": ["Succeeded"]},
            },
        },
        "runAfter": {"Cesta_webu": ["Succeeded"]},
    }

    # ---------- parametry excelového konektoru se skládají za běhu ----------
    kroky["Site_id"] = rest("GET", "@'_api/site/id'", "Rezim_seznam")
    kroky["Web_id"] = rest("GET", "@'_api/web/id'", "Site_id")
    kroky["Disky"] = rest("GET", "@'_api/v2.0/drives'", "Web_id")

    kroky["Zdroj"] = {
        "type": "Compose",
        "inputs": ("@concat('sites/', split(" + ep.vyraz(ep.WEB) + ", '/')[2], ','"
                   ", toLower(replace(replace(string(body('Site_id')?['value']),"
                   " '{', ''), '}', '')), ','"
                   ", toLower(replace(replace(string(body('Web_id')?['value']),"
                   " '{', ''), '}', '')))"),
        "runAfter": {"Disky": ["Succeeded"]},
    }

    # Hledá se podle URL segmentu, ne podle zobrazovaného názvu: ten nese
    # diakritiku a přejmenováním se mění, kdežto segment je interní název.
    kroky["Disk_kandidati"] = {
        "type": "Query",
        "inputs": {
            "from": "@coalesce(body('Disky')?['value'], createArray())",
            "where": (f"@endsWith(toLower(string(item()?['webUrl'])),"
                      f" {lit('/' + KNIHOVNA.lower())})"),
        },
        "runAfter": {"Zdroj": ["Succeeded"]},
    }
    kroky["Disk"] = {
        "type": "Compose",
        "inputs": "@first(body('Disk_kandidati'))?['id']",
        "runAfter": {"Disk_kandidati": ["Succeeded"]},
    }

    kroky["Soubor"] = sp_akce(
        "GetFileMetadataByPath",
        {"dataset": ep.web(),
         "path": f"@concat({lit('/' + KNIHOVNA + '/')}, outputs('Vstup')?['soubor'])"},
        "Disk")

    kroky["Radky"] = {
        "type": "OpenApiConnection",
        "inputs": {
            "parameters": {
                "source": "@outputs('Zdroj')",
                "drive": "@outputs('Disk')",
                "file": "@body('Soubor')?['Id']",
                "table": TABULKA,
            },
            "host": {"apiId": HOST_XLS, "operationId": "GetItems",
                     "connectionName": "shared_excelonlinebusiness"},
        },
        "runAfter": {"Soubor": ["Succeeded"]},
    }

    # ---------- řádky sešitu na tvar rejstříku ----------
    # Prochází se přes index, ne přímo přes pole: jedině tak jde do výsledku
    # dostat ČÍSLO ŘÁDKU v sešitě (+2 kvůli hlavičce), a bez něj by správce
    # chybný řádek hledal očima.
    vyber = {"radek": "@add(item(), 2)"}
    for sloupec in sloupce + sloupce_vlastniku():
        vyber[sloupec["name"]] = "@" + bunka(sloupec)
    kroky["Ocistene"] = {
        "type": "Select",
        "inputs": {
            "from": "@range(0, length(coalesce(body('Radky')?['value'], createArray())))",
            "select": vyber,
        },
        "runAfter": {"Radky": ["Succeeded"]},
    }

    predchozi = "Ocistene"
    for jmeno in (LIST_AGENDY, LIST_PROCESY, LIST_DILCI, LIST_AKTIVITY):
        lst = list_ze_schematu(schema, jmeno)
        akce_jmeno = f"Nacti_{jmeno}"
        kroky[akce_jmeno] = sp_akce(
            "GetItems",
            {"dataset": ep.web(),
             "table": ep.list_param(lst.get("display") or lst["name"]),
             "$top": STRANKOVANI},
            predchozi)
        kroky[akce_jmeno]["runtimeConfiguration"] = {
            "paginationPolicy": {"minimumItemCount": STRANKOVANI}}
        predchozi = akce_jmeno

    kroky["Kody_dilcich"] = {
        "type": "Select",
        "inputs": {"from": f"@outputs('Nacti_{LIST_DILCI}')?['body/value']",
                   "select": "@item()?['Title']"},
        "runAfter": {predchozi: ["Succeeded"]},
    }
    # Klíč duplicity: dílčí proces + název. Týž tvar se počítá i z sešitu.
    kroky["Klice_aktivit"] = {
        "type": "Select",
        "inputs": {
            "from": f"@outputs('Nacti_{LIST_AKTIVITY}')?['body/value']",
            "select": ("@concat(coalesce(item()?['dilci_proces_kod'], ''), "
                       + lit(SPOJKA_VAZBY) + ", trim(coalesce(item()?['nazev'], '')))"),
        },
        "runAfter": {"Kody_dilcich": ["Succeeded"]},
    }
    kroky["Kody_aktivit"] = {
        "type": "Select",
        "inputs": {"from": f"@outputs('Nacti_{LIST_AKTIVITY}')?['body/value']",
                   "select": "@item()?['Title']"},
        "runAfter": {"Klice_aktivit": ["Succeeded"]},
    }

    # ---------- rozdělení řádků ----------
    # Rozklad je úplný: každý řádek sešitu padne právě do jedné skupiny.
    # Kdyby se skupiny překrývaly, sedělo by v náhledu něco jiného než ve
    # skutečnosti a správce by opravoval podle špatných čísel.
    vsechny_prazdne = " ".join(
        f"empty(item()?['{c['name']}']),"
        for c in sloupce + sloupce_vlastniku()).rstrip(",")
    kroky["Prazdne"] = {
        "type": "Query",
        "inputs": {"from": "@body('Ocistene')",
                   "where": f"@and({vsechny_prazdne})"},
        "runAfter": {"Kody_aktivit": ["Succeeded"]},
    }
    kroky["S_obsahem"] = {
        "type": "Query",
        "inputs": {"from": "@body('Ocistene')",
                   "where": f"@not(and({vsechny_prazdne}))"},
        "runAfter": {"Prazdne": ["Succeeded"]},
    }
    # Aktivita nahraná BEZ zařazení je legitimní vstup: správce nahraje holé
    # činnosti a zařadí je až v aplikaci. Kód se ale odvozuje od kódu rodiče
    # a Title je povinný, takže rodiče mít musí — dosadí se technický
    # `00-00-000 Nezařazeno`, který zakládá provisioning.
    #
    # POŘADÍ JE PODSTATNÉ: náhrada smí přijít až ZA `S_obsahem`. Kdyby se
    # dosadilo dřív, přestaly by být prázdné řádky prázdné (`vsechny_prazdne`
    # by neplatilo) a šablona by při každém importu založila dvě stě sirotků
    # z prázdných řádků pod tabulkou.
    doplneny = {"radek": "@item()?['radek']"}
    for sloupec in sloupce:
        jmeno = sloupec["name"]
        if jmeno == KOD_RODICE_SLOUPEC:
            doplneny[jmeno] = (f"@if(empty(item()?['{jmeno}']), "
                               f"{lit(KOD_NEZARAZENO)}, item()?['{jmeno}'])")
        else:
            doplneny[jmeno] = f"@item()?['{jmeno}']"
    kroky["Doplneny_rodic"] = {
        "type": "Select",
        "inputs": {"from": "@body('S_obsahem')", "select": doplneny},
        "runAfter": {"S_obsahem": ["Succeeded"]},
    }

    povinne = [c["name"] for c in sloupce if c.get("required")]
    ma_povinne = " ".join(f"not(empty(item()?['{n}']))," for n in povinne).rstrip(",")
    kroky["Chybne"] = {
        "type": "Query",
        "inputs": {"from": "@body('Doplneny_rodic')",
                   "where": f"@not(and({ma_povinne}))"},
        "runAfter": {"Doplneny_rodic": ["Succeeded"]},
    }
    kroky["Uplne"] = {
        "type": "Query",
        "inputs": {"from": "@body('Doplneny_rodic')", "where": f"@and({ma_povinne})"},
        "runAfter": {"Chybne": ["Succeeded"]},
    }
    kroky["Neznamy_dilci"] = {
        "type": "Query",
        "inputs": {
            "from": "@body('Uplne')",
            "where": ("@not(contains(body('Kody_dilcich'),"
                      " item()?['dilci_proces_kod']))"),
        },
        "runAfter": {"Uplne": ["Succeeded"]},
    }
    kroky["Zarazene"] = {
        "type": "Query",
        "inputs": {
            "from": "@body('Uplne')",
            "where": "@contains(body('Kody_dilcich'), item()?['dilci_proces_kod'])",
        },
        "runAfter": {"Neznamy_dilci": ["Succeeded"]},
    }
    klic_radku = ("concat(item()?['dilci_proces_kod'], " + lit(SPOJKA_VAZBY)
                  + ", item()?['nazev'])")
    kroky["Duplicitni"] = {
        "type": "Query",
        "inputs": {"from": "@body('Zarazene')",
                   "where": f"@contains(body('Klice_aktivit'), {klic_radku})"},
        "runAfter": {"Zarazene": ["Succeeded"]},
    }
    kroky["K_zalozeni"] = {
        "type": "Query",
        "inputs": {"from": "@body('Zarazene')",
                   "where": f"@not(contains(body('Klice_aktivit'), {klic_radku}))"},
        "runAfter": {"Duplicitni": ["Succeeded"]},
    }

    # Kolik z nich je bez zařazení. Není to další skupina rozkladu, ale
    # podmnožina `K_zalozeni` — správce musí vidět, kolik aktivit bude po
    # importu čekat na zařazení, jinak se na ně zapomene.
    kroky["Nezarazene"] = {
        "type": "Query",
        "inputs": {"from": "@body('K_zalozeni')",
                   "where": ("@equals(item()?['" + KOD_RODICE_SLOUPEC + "'], "
                             + lit(KOD_NEZARAZENO) + ")")},
        "runAfter": {"K_zalozeni": ["Succeeded"]},
    }

    # Kódy už přidělené v tomhle běhu musí být vidět při přidělování dalšího,
    # jinak by dvě aktivity pod týmž dílčím procesem dostaly stejný kód.
    # ---------- vlastníci nadřazených úrovní ----------
    predchozi_vl = "Nezarazene"
    for uroven in UROVNE_VLASTNIKU:
        k = uroven["klic"]
        sloupec = uroven["sloupec"]
        # Jen řádky, kde je vlastník vyplněný a rodič je skutečný. Nezařazené
        # aktivity visí pod technickým 00-00-000 a tomu se vlastník nepřipisuje.
        kroky[f"S_vlastnikem_{k}"] = {
            "type": "Query",
            "inputs": {
                "from": "@body('Zarazene')",
                "where": (f"@and(not(empty(item()?['{sloupec}'])),"
                          f" not(startsWith(item()?['dilci_proces_kod'],"
                          f" {lit(NEZARAZENY_PREFIX + '-')})))"),
            },
            "runAfter": {predchozi_vl: ["Succeeded"]},
        }
        # `<kód rodiče>|~|<vlastníci>`; union sám se sebou zahodí duplicity,
        # takže co zbude víc než jednou pro týž kód, je rozpor.
        kroky[f"Klice_{k}"] = {
            "type": "Select",
            "inputs": {
                "from": f"@body('S_vlastnikem_{k}')",
                "select": (f"@concat(substring(item()?['dilci_proces_kod'], 0,"
                           f" {uroven['delka']}), {lit(ODD_POLE)},"
                           f" item()?['{sloupec}'])"),
            },
            "runAfter": {f"S_vlastnikem_{k}": ["Succeeded"]},
        }
        kroky[f"Unikatni_{k}"] = {
            "type": "Compose",
            "inputs": f"@union(body('Klice_{k}'), body('Klice_{k}'))",
            "runAfter": {f"Klice_{k}": ["Succeeded"]},
        }
        # Jméno musí být `Kody_vlastniku_*`, ne `Kody_*`: pro úroveň `dilcich`
        # by z toho vyšlo `Kody_dilcich`, což je akce, která existuje odjinud
        # (seznam existujících dílčích procesů pro validaci). Přepsání se
        # neprojevilo chybou generátoru, ale zacyklením runAfter — 07.09.2026.
        kroky[f"Kody_vlastniku_{k}"] = {
            "type": "Select",
            "inputs": {"from": f"@outputs('Unikatni_{k}')",
                       "select": f"@split(item(), {lit(ODD_POLE)})[0]"},
            "runAfter": {f"Unikatni_{k}": ["Succeeded"]},
        }
        # Počet výskytů kódu: `split(A, B)` vrátí o jeden díl víc, než kolikrát
        # se B v A vyskytuje. Kód obalený oddělovači se v seznamu unikátních
        # dvojic objeví právě tolikrát, kolik RŮZNÝCH vlastníků k němu sešit
        # uvádí — víc než jednou tedy znamená rozpor.
        vyskyty = (f"length(split(concat({lit(ODD_RADKU)},"
                   f" join(body('Kody_vlastniku_{k}'), {lit(ODD_RADKU)}), {lit(ODD_RADKU)}),"
                   f" concat({lit(ODD_RADKU)}, split(item(), {lit(ODD_POLE)})[0],"
                   f" {lit(ODD_RADKU)})))")
        kroky[f"Rozpor_{k}"] = {
            "type": "Query",
            "inputs": {"from": f"@outputs('Unikatni_{k}')",
                       "where": f"@greater({vyskyty}, 2)"},
            "runAfter": {f"Kody_vlastniku_{k}": ["Succeeded"]},
        }
        kroky[f"K_zapisu_{k}"] = {
            "type": "Query",
            "inputs": {"from": f"@outputs('Unikatni_{k}')",
                       "where": f"@equals({vyskyty}, 2)"},
            "runAfter": {f"Rozpor_{k}": ["Succeeded"]},
        }
        predchozi_vl = f"K_zapisu_{k}"

    kroky["Pouzite_kody"] = {
        "type": "InitializeVariable",
        "inputs": {"variables": [{"name": "pouziteKody", "type": "array",
                                  "value": "@body('Kody_aktivit')"}]},
        "runAfter": {predchozi_vl: ["Succeeded"]},
    }

    # Vlastníci se zapisují až ZA aktivitami: kdyby import spadl uprostřed,
    # je lepší mít aktivity bez vlastníka než vlastníka bez aktivit.
    vetev_zapisu = zapisove_akce(sloupce, podle_jmena)
    posledni_zapis = "Zaloz"
    for jmeno, definice in zapis_vlastniku().items():
        definice["runAfter"] = {posledni_zapis: ["Succeeded"]}
        vetev_zapisu[jmeno] = definice
        posledni_zapis = jmeno
    kroky["Zapis"] = {
        "type": "If",
        "expression": {"equals": ["@outputs('Vstup')?['rezim']", REZIM_ZAPIS]},
        "actions": vetev_zapisu,
        "runAfter": {"Pouzite_kody": ["Succeeded"]},
    }

    # Důvod se přiřazuje TAM, kde skupina vzniká, ne dodatečným zpětným
    # dohledáváním řádku v obou polích: `contains()` by porovnával celé objekty
    # a stačilo by, aby dva řádky sešitu byly shodné, a důvod by se přehodil.
    kroky["Popis_chybne"] = {
        "type": "Select",
        "inputs": {
            "from": "@body('Chybne')",
            "select": ("@concat(string(item()?['radek']), " + lit(ODD_POLE)
                       + ", item()?['nazev'], " + lit(ODD_POLE) + ", "
                       + lit("chybí povinný údaj (název nebo kód dílčího procesu)")
                       + ")"),
        },
        "runAfter": {"Zapis": ["Succeeded"]},
    }
    kroky["Popis_neznamy"] = {
        "type": "Select",
        "inputs": {
            "from": "@body('Neznamy_dilci')",
            "select": ("@concat(string(item()?['radek']), " + lit(ODD_POLE)
                       + ", item()?['nazev'], " + lit(ODD_POLE)
                       + ", 'dílčí proces ', item()?['dilci_proces_kod'],"
                       " ' v rejstříku není')"),
        },
        "runAfter": {"Popis_chybne": ["Succeeded"]},
    }
    # Rozpor ve vlastnících musí být VIDĚT. Bez tohohle by import vlastníka
    # té úrovně mlčky přeskočil a správce by se to dozvěděl až tím, že
    # v rejstříku nic nepřibylo.
    predchozi_popis = "Popis_neznamy"
    for uroven in UROVNE_VLASTNIKU:
        k = uroven["klic"]
        kroky[f"Popis_rozpor_{k}"] = {
            "type": "Select",
            "inputs": {
                "from": f"@body('Rozpor_{k}')",
                "select": ("@concat('—', " + lit(ODD_POLE)
                           + f", split(item(), {lit(ODD_POLE)})[0], " + lit(ODD_POLE)
                           + f", 'vlastník {uroven['popis']} se v sešitu liší"
                           f" řádek od řádku (jedna z hodnot: ',"
                           f" split(item(), {lit(ODD_POLE)})[1],"
                           " '); sjednoť je a spusť import znovu — vlastník"
                           " se zatím nezapsal')"),
            },
            "runAfter": {predchozi_popis: ["Succeeded"]},
        }
        predchozi_popis = f"Popis_rozpor_{k}"

    vsechny_popisy = ", ".join(
        [f"body('Popis_rozpor_{u['klic']}')" for u in UROVNE_VLASTNIKU])
    kroky["Chybne_radky"] = {
        "type": "Compose",
        "inputs": ("@join(union(body('Popis_chybne'), body('Popis_neznamy'), "
                   + vsechny_popisy + "), " + lit(ODD_RADKU) + ")"),
        "runAfter": {predchozi_popis: ["Succeeded"]},
    }

    # Pořadí čísel je součástí kontraktu — appka je bere podle indexu.
    # Mění-li se, musí se změnit i obrazovka náhledu; hlídá to brána.
    kroky["Prehled"] = {
        "type": "Compose",
        "inputs": "@concat(" + (", " + lit(ODD_POLE) + ", ").join(
            f"string(length(body('{skupina}')))"
            for skupina in POCTY) + ")",
        "runAfter": {"Chybne_radky": ["Succeeded"]},
    }

    kroky["Odpoved"] = {
        "type": "Response",
        "kind": "PowerApp",
        "inputs": {
            "statusCode": 200,
            "body": {
                "stav": f"@if(equals(outputs('Vstup')?['rezim'], {lit(REZIM_ZAPIS)}),"
                        f" 'zapsano', 'nahled')",
                "soubor": "@outputs('Vstup')?['soubor']",
                "prehled": "@outputs('Prehled')",
                "chyby": "@outputs('Chybne_radky')",
            },
            "schema": {"type": "object", "properties": {
                "stav": {"type": "string"},
                "soubor": {"type": "string"},
                "prehled": {"type": "string"},
                "chyby": {"type": "string"},
            }},
        },
        "runAfter": {"Prehled": ["Succeeded"]},
    }
    return kroky


def zapis_vlastniku():
    """MERGE vlastníka k agendě, procesu a dílčímu procesu.

    Zapisuje se jen tam, kde se sešit sám se sebou neshodl — rozporné kódy
    odfiltroval `K_zapisu_*`. MERGE mění jediný sloupec, takže se nedotkne
    názvu ani zařazení; kdyby se použil `PostItem`, založil by nový řádek.
    """
    kroky = {}
    for uroven in UROVNE_VLASTNIKU:
        k = uroven["klic"]
        smycka = f"Zapis_vlastniku_{k}"
        polozka = f"items('{smycka}')"
        kod = f"split({polozka}, {lit(ODD_POLE)})[0]"
        vlastnik = f"split({polozka}, {lit(ODD_POLE)})[1]"
        kroky[smycka] = {
            "type": "Foreach",
            "foreach": f"@body('K_zapisu_{k}')",
            "actions": {
                # ID se dohledává podle kódu v načteném listu. Kód, který
                # v rejstříku není, se přeskočí - `first()` nad prázdným polem
                # dá null a podmínka zápis nepustí.
                f"Najdi_{k}": {
                    "type": "Query",
                    "inputs": {
                        "from": f"@outputs('Nacti_{uroven['list']}')?['body/value']",
                        "where": f"@equals(coalesce(item()?['Title'], ''), {kod})",
                    },
                    "runAfter": {},
                },
                f"Pokud_existuje_{k}": {
                    "type": "If",
                    "expression": {"not": {"equals": [f"@length(body('Najdi_{k}'))", 0]}},
                    "actions": {
                        f"Uloz_vlastnika_{k}": sp_akce(
                            "HttpRequest",
                            {"dataset": ep.web(),
                             "parameters/method": "POST",
                             "parameters/uri": rest_list(
                                 uroven["list"],
                                 f"(', string(first(body('Najdi_{k}'))?['ID']), ')"),
                             "parameters/headers": dict(
                                 HLAVICKY_ZAPIS,
                                 **{"X-HTTP-Method": "MERGE", "IF-MATCH": "*"}),
                             "parameters/body": {"vlastnik": f"@{vlastnik}"}},
                            None),
                    },
                    "else": {"actions": {}},
                    "runAfter": {f"Najdi_{k}": ["Succeeded"]},
                },
            },
            "runAfter": {},
        }
    return kroky


def zapisove_akce(sloupce, podle_jmena):
    """Založení aktivit. Sekvenčně — kódy se přidělují ze sdílené proměnné."""
    smycka = "Zaloz"
    polozka = f"items('{smycka}')"
    prefix = f"{polozka}?['dilci_proces_kod']"

    telo_aktivity = {"Title": "@outputs('Novy_kod')"}
    for sloupec in sloupce:
        jmeno = sloupec["name"]
        if jmeno == "stav":
            telo_aktivity[jmeno] = (f"@if(empty({polozka}?['{jmeno}']),"
                                    f" {lit(VYCHOZI_STAV)}, {polozka}?['{jmeno}'])")
        else:
            telo_aktivity[jmeno] = f"@coalesce({polozka}?['{jmeno}'], '')"
    # Razítko importu; nazev_kratky schválně chybí — dopočítá ho
    # AktualizaceKratkehoNazvu, které visí na vzniku i změně položky.
    telo_aktivity["datum_aktualizace"] = "@utcNow()"

    telo_vazby = {
        "Title": f"@concat(outputs('Novy_kod'), {lit(SPOJKA_VAZBY)}, {prefix})",
        "aktivita_kod": "@outputs('Novy_kod')",
        "dilci_proces_kod": f"@{prefix}",
        "primarni": "ano",
    }

    return {
        smycka: {
            "type": "Foreach",
            "foreach": "@body('K_zalozeni')",
            # Souběžnost 1: smyčka si předává použité kódy proměnnou, takže
            # paralelní průchody by dvěma aktivitám přidělily týž kód.
            "runtimeConfiguration": {"concurrency": {"repetitions": 1}},
            "actions": {
                "Sourozenci": {
                    "type": "Query",
                    "inputs": {
                        "from": "@variables('pouziteKody')",
                        "where": f"@startsWith(string(item()), concat({prefix}, '-'))",
                    },
                    "runAfter": {},
                },
                "Cisla": {
                    "type": "Select",
                    "inputs": {
                        "from": "@body('Sourozenci')",
                        "select": ("@int(substring(string(item()),"
                                   f" add(length({prefix}), 1), 4))"),
                    },
                    "runAfter": {"Sourozenci": ["Succeeded"]},
                },
                # max() nad prázdným polem spadne, proto if(empty(...), 0, …).
                "Novy_kod": {
                    "type": "Compose",
                    "inputs": (
                        "@concat(" + prefix + ", '-', substring(concat('000',"
                        " string(add(if(empty(body('Cisla')), 0, max(body('Cisla'))), 1))),"
                        " sub(length(concat('000', string(add(if(empty(body('Cisla')), 0,"
                        " max(body('Cisla'))), 1)))), 4), 4))"),
                    "runAfter": {"Cisla": ["Succeeded"]},
                },
                "Vloz_aktivitu": rest("POST", rest_list(LIST_AKTIVITY), "Novy_kod",
                                      telo_aktivity, HLAVICKY_ZAPIS),
                "Vloz_vazbu": rest("POST", rest_list(LIST_VAZBY), "Vloz_aktivitu",
                                   telo_vazby, HLAVICKY_ZAPIS),
                "Zapamatuj_kod": {
                    "type": "AppendToArrayVariable",
                    "inputs": {"name": "pouziteKody", "value": "@outputs('Novy_kod')"},
                    "runAfter": {"Vloz_vazbu": ["Succeeded"]},
                },
            },
            "runAfter": {},
        }
    }


def trigger():
    return {"manual": {
        "type": "Request",
        "kind": "PowerAppV2",
        "inputs": {"schema": {
            "type": "object",
            "properties": {"text": {
                "title": "pozadavek",
                "type": "string",
                "x-ms-dynamically-added": True,
                "description": ('JSON: {"soubor": "…xlsx", '
                                '"rezim": "nahled" | "zapis"}'),
            }},
            "required": ["text"],
        }},
    }}


def excelove_spojeni(customizations):
    """Logický název connection reference na Excel — z balíku, ne natvrdo.

    Spojení vzniká v prostředí, ne v generátoru; kdyby v balíku nebylo, flow
    by se sice naimportovalo, ale excelová akce by neměla čím běžet.
    """
    for m in re.finditer(
            r'connectionreferencelogicalname="([^"]+)">(.*?)</connectionreference>',
            customizations, re.S):
        if "shared_excelonlinebusiness" in m.group(2):
            return m.group(1)
    raise SystemExit(
        "CHYBA: v balíku není connection reference na Excel Online (Business). "
        "Spojení vzniká v prostředí — založ ve Studiu flow s excelovou akcí "
        "a exportuj solution znovu.")


def definice_flow(vzor, kroky, excel_logicky):
    spojeni = dict(vzor["properties"]["connectionReferences"])
    spojeni["shared_excelonlinebusiness"] = {
        "api": {"name": "shared_excelonlinebusiness"},
        "connection": {"connectionReferenceLogicalName": excel_logicky},
        # embedded, ne invoker: flow běží pod servisním účtem stejně jako
        # ostatní, takže appka nebude po uživatelích chtít vlastní spojení.
        "runtimeSource": "embedded",
    }
    return {
        "properties": {
            "connectionReferences": spojeni,
            "definition": {
                "$schema": vzor["properties"]["definition"].get(
                    "$schema",
                    "https://schema.management.azure.com/providers/Microsoft.Logic/"
                    "schemas/2016-06-01/workflowdefinition.json#"),
                "contentVersion": "1.0.0.0",
                "parameters": vzor["properties"]["definition"].get("parameters", {}),
                "triggers": trigger(),
                "actions": kroky,
                "outputs": {},
            },
        },
        "schemaVersion": vzor.get("schemaVersion", "1.0.0.0"),
    }


def uzel_workflow(customizations, guid):
    zacatek = customizations.index(f'<Workflow WorkflowId="{{{guid}}}"')
    konec = customizations.index("</Workflow>", zacatek) + len("</Workflow>")
    return customizations[zacatek:konec]


def pridej_uzel(customizations, zdroj_guid, cil_guid, cil_nazev):
    if f'Name="{cil_nazev}"' in customizations:
        stary = uzel_workflow(customizations, cil_guid)
        customizations = customizations.replace("\n    " + stary, "").replace(stary, "")
    uzel = uzel_workflow(customizations, zdroj_guid)
    novy = (uzel.replace(zdroj_guid, cil_guid)
                .replace(zdroj_guid.upper(), cil_guid.upper())
                .replace(ZDROJ, cil_nazev))
    if novy == uzel:
        raise SystemExit("CHYBA: klon uzlu Workflow se od předlohy neliší")
    return customizations.replace(uzel, uzel + "\n    " + novy, 1)


def pridej_rootcomponent(solution, zdroj_guid, cil_guid):
    solution = re.sub(r'\s*<RootComponent type="29" id="\{' + cil_guid + r'\}"[^>]*/>',
                      "", solution)
    zdrojovy = f'<RootComponent type="29" id="{{{zdroj_guid}}}" behavior="0" />'
    if zdrojovy not in solution:
        raise SystemExit("CHYBA: RootComponent zdrojového flow nenalezen")
    return solution.replace(
        zdrojovy,
        zdrojovy + f'\n      <RootComponent type="29" id="{{{cil_guid}}}" behavior="0" />', 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True)
    argumenty = parser.parse_args()

    cesta = Path(argumenty.solution)
    if not cesta.exists():
        raise SystemExit(f"CHYBA: solution {cesta} neexistuje")
    with zipfile.ZipFile(cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    zdrojove = [n for n in polozky if n.replace("\\", "/").startswith(f"Workflows/{ZDROJ}")]
    if len(zdrojove) != 1:
        raise SystemExit(f"CHYBA: čekám právě jedno {ZDROJ}, našel jsem {len(zdrojove)}")
    zdroj_klic = zdrojove[0]
    zdroj_guid = re.search(r"-([0-9A-Fa-f-]{36})\.json$", zdroj_klic).group(1).lower()
    vzor = json.loads(polozky[zdroj_klic].decode("utf-8-sig"))

    customizations = polozky["customizations.xml"].decode("utf-8-sig")
    solution = polozky["solution.xml"].decode("utf-8-sig")
    excel_logicky = excelove_spojeni(customizations)

    schema = nacti_schema()
    flow = definice_flow(vzor, akce(schema), excel_logicky)

    for stary in [n for n in polozky
                  if n.replace("\\", "/").startswith(f"Workflows/{FLOW}")]:
        del polozky[stary]
    polozky[f"Workflows/{FLOW}-{FLOW_GUID.upper()}.json"] = json.dumps(
        flow, ensure_ascii=False, indent=1).encode("utf-8")
    customizations = pridej_uzel(customizations, zdroj_guid, FLOW_GUID, FLOW)
    solution = pridej_rootcomponent(solution, zdroj_guid, FLOW_GUID)

    polozky["customizations.xml"] = customizations.encode("utf-8")
    polozky["solution.xml"] = solution.encode("utf-8")

    with zipfile.ZipFile(cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)

    sloupce = sloupce_sablony(schema)
    print(f"přidáno flow: {FLOW}")
    print(f"  GUID: {FLOW_GUID}")
    print(f"  akcí nejvyšší úrovně: {len(flow['properties']['definition']['actions'])}")
    print(f"  čte: knihovna {KNIHOVNA}, tabulka {TABULKA}, {len(sloupce)} sloupců")
    print(f"  excelové spojení: {excel_logicky}")
    print(f"  zakládá do: {LIST_AKTIVITY} + {LIST_VAZBY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
