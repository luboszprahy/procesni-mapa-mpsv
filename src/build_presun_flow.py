# -*- coding: utf-8 -*-
"""Přidá do solution flow PresunFlow — přesun procesu nebo dílčího procesu
pod jiného rodiče, variantou C (zánik a vznik).

Vstup je jeden text:

    {"kod": "07-08", "uroven": "proces" | "dilci_proces",
     "cil": "03", "duvod": "…", "rezim": "nahled" | "zapis"}

Odpověď má týž tvar jako ImportFlow a RestoreFlow — čtyři řetězce, aby appka
nepotřebovala `ParseJSON` (má `dynamicschema = False`):

    stav      "nahled" | "zapsano" | "plno"
    hlaseni   text chyby, jinak prázdno
    porizeno  nový prefix, pod kterým větev ožije
    prehled   řádky "stary|~|novy|~|uroven|~|nazev" spojené |#|

## Proč to dělá flow a ne appka

Kaskáda je řádově dvě stě zápisů. V appce by běžela v prohlížeči a zavření
okna nebo výpadek sítě uprostřed by nechal rejstřík rozpůlený; `Foreach`
v Logic Apps doběhne na serveru a je vidět v run history. Appka navíc nemá
jak uložit protokol, který metodika u změny kódu vyžaduje.

`$batch` se schválně NEPOUŽÍVÁ — ze stejného důvodu jako v `RestoreFlow`:
multipart changeset se v Logic Apps skládá ručně z hranic a hlaviček a chyba
v něm se pozná až za běhu. `Foreach` běží paralelně, takže i po jednom je to
otázka sekund.

## Jak se počítá nový kód

Přečísluje se JEN přesouvaná úroveň; potomci dědí nový prefix a nechají si
své pořadové číslo:

    proces  07-08              → 03-05
      dílčí proces 07-08-001   → 03-05-001
        aktivita 07-08-001-0006 → 03-05-001-0006

Díky tomu je celá kaskáda jediná náhrada prefixu a jde vyjádřit jedním
výrazem, který platí pro všechny tři úrovně naráz:

    novy = concat(novyPrefix, zbytek(stary))

U potomků je zbytek konec kódu za přesouvaným prefixem, u přesouvané položky
samotné je prázdný. `substring(stary, length(kod))` se na to použít NEDÁ:
Logic Apps vyžadují start index MENŠÍ než délka řetězce, takže na položce,
jejíž kód JE přesouvaný kód, spadne celý běh na

    'substring' parameter is out of range: 'start index' must be non-negative
    integer and should be less than the length of the string

(zjištěno 04.09.2026 na prvním ostrém běhu, akce `Mapa`). Proto se zbytek
bere jen tehdy, když nějaký je — viz `zbytek()`.

Hledat pod novým rodičem volná čísla pro potomky není potřeba — číslují se
v rámci svého rodiče a ten je nový, takže jsou volná všechna.

Nové číslo pro přesouvanou úroveň se hledá jako maximum přes ŽIVÝ list
I PŘES HISTORII (pravidlo F10/1: uzavřený kód se nikdy nerecykluje). Bez
historie by přesun zpátky tam, odkud položka přišla, oživil kód, který už
jednou něco znamenal.

## Zápis přes SendHTTPRequest, ne PatchItem

Totéž rozhodnutí jako v `RestoreFlow`: konektorová zápisová akce s rozloženým
tělem `item/<sloupec>` vyžaduje `table` jako GUID natvrdo, jinak flow nejde
zapnout. REST adresuje list interním názvem ze schématu, který je na všech
tenantech stejný.

## Pořadí zápisu je závazné

Nejdřív VZNIK (nové záznamy a vazby), pak HISTORIE, teprve nakonec ZÁNIK.
V opačném pořadí by výpadek uprostřed smazal větev, která ještě nikde jinde
neexistuje. Takhle je nejhorší možný výsledek duplicita, ne ztráta.

Pořadí buildu je závazné: **nejdřív tenhle generátor, teprve pak
`build_app.py`.** Deklarace použitých parametrů doplňuje jedno místo
(`dorovnej_deklarace_parametru`), takže flow přidané až do hotového balíku
by je nemělo a spadlo by za běhu na `InvalidTemplate`.

    copy deploy/procesnimapa_1_0_0_92.zip runs/vstup_93.zip
    python src/build_presun_flow.py --solution runs/vstup_93.zip
    python src/build_app.py --solution runs/vstup_93.zip --verze 1.0.0.93
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402
from build_restore_flow import (  # noqa: E402
    HLAVICKY_ZAPIS, ODD_POLE, ODD_RADKU, STRANKOVANI,
    lit, rest_adresa, sp_akce, uzel_workflow,
)

ZDROJ = "MapaPublishFlow"
FLOW = "PresunFlow"
# Pevné GUID: opakovaný build musí dát TOTÉŽ flow, jinak by v prostředí
# přibývali sirotci a každý z nich by blokoval import se stejným ID.
FLOW_GUID = "5b2e9a41-7c36-4d18-a9f2-3e4c81b70d56"

SCHEMA = Path("src/schema.json")

REZIM_NAHLED = "nahled"
REZIM_ZAPIS = "zapis"
# Třetí stav odpovědi, ne třetí režim vstupu: pod cílovým rodičem došla čísla.
STAV_PLNO = "plno"

# Zobrazované názvy listů — musí sedět s tím, jak je appka připojená,
# protože `ep.list_param` z nich odvozuje proměnnou prostředí.
L_PROCESY = "Procesy"
L_DILCI = "Dílčí procesy"
L_AKTIVITY = "Aktivity"
L_VAZBY = "Vazba aktivita–dílčí proces"
L_HISTORIE = "Historie kódů"

# Interní názvy pro REST — na všech tenantech stejné (konvence projektu:
# interní názvy bez diakritiky).
I_PROCESY = "Procesy"
I_DILCI = "DilciProcesy"
I_AKTIVITY = "Aktivity"
I_VAZBY = "AktivitaDilciProces"
I_HISTORIE = "HistorieKodu"


def nacti_schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def v(pole):
    """Hodnota pole ze vstupního JSONu."""
    return f"outputs('Vstup')?['{pole}']"


def je_proces():
    """Podmínka „přesouvá se proces" jako výraz Logic Apps."""
    return f"equals({v('uroven')}, {lit('proces')})"


def zbytek(stary_vyraz):
    """Konec kódu za přesouvaným prefixem; u samotné přesouvané položky prázdno.

    Holé `substring(stary, length(kod))` tu selže: Logic Apps chtějí start
    index menší než délka řetězce, takže na položce, jejíž kód JE přesouvaný
    kód, spadne celý běh (`start index ... should be less than the length`).
    Netýká se to jen `Mapa` — stejná past je u dílčího procesu v
    `Zaloz_aktivity` a u vazby, jejíž `dilci_proces_kod` se rovná
    přesouvanému kódu.

    Mezera v `concat` je tam kvůli meznímu případu: bez ní by u přesouvané
    položky vyšel start index roven délce, což je právě to zakázané. S ní je
    text o znak delší, délka výřezu je nula a výsledek prázdný řetězec.
    """
    # Podmínkou to ošetřit NEJDE: Logic Apps vyhodnocují VŠECHNY argumenty
    # funkce `if()`, tedy i větev, která se nepoužije — `substring` by tak
    # spadl bez ohledu na test délky. Řeší se to délkou: `sub()` dá u
    # přesouvané položky nulu, takže se substring drží v mezích.
    return (f"substring(concat({stary_vyraz}, ' '), length({v('kod')}),"
            f" sub(length({stary_vyraz}), length({v('kod')})))")


def novy_kod(stary_vyraz):
    """Náhrada prefixu — jediný vzorec pro všechny tři úrovně kaskády."""
    return f"concat(outputs('Novy_prefix'), {zbytek(stary_vyraz)})"


def nacitani():
    """Pět listů, které kaskáda potřebuje. Bez pagination načte konektor jen
    prvních 100 položek a přesun by tiše minul většinu podstromu."""
    kroky = {}
    predchozi = "Cesta_webu"
    for jmeno, zobrazovany in (("Procesy", L_PROCESY), ("DilciProcesy", L_DILCI),
                               ("Aktivity", L_AKTIVITY), ("Vazby", L_VAZBY),
                               ("Historie", L_HISTORIE)):
        krok = f"Nacti_{jmeno}"
        kroky[krok] = sp_akce(
            "GetItems",
            {"dataset": ep.web(), "table": ep.list_param(zobrazovany),
             "$top": STRANKOVANI},
            predchozi)
        kroky[krok]["runtimeConfiguration"] = {
            "paginationPolicy": {"minimumItemCount": STRANKOVANI}
        }
        predchozi = krok
    return kroky, predchozi


def cislo_kodu(vyraz):
    """Poslední segment kódu jako číslo. Platí pro obě úrovně naráz:
    '03-05' → 5, '03-05-001' → 1."""
    return f"int(last(split({vyraz}, '-')))"


def vypocet_prefixu(po):
    """Nové číslo = maximum přes živý list I historii, plus jedna.

    `max()` nad prázdným polem spadne, proto se do sjednocení vždycky přidá
    nula — prázdný rodič pak dá číslo 1, což je dnešní chování zakládání.
    """
    kroky = {}
    kroky["Sourozenci"] = {
        "type": "Query",
        "inputs": {
            "from": (f"@if({je_proces()}, outputs('Nacti_Procesy')?['body/value'],"
                     " outputs('Nacti_DilciProcesy')?['body/value'])"),
            "where": (f"@equals(coalesce(item()?[if({je_proces()},"
                      f" 'agenda_kod', 'proces_kod')], ''), {v('cil')})"),
        },
        "runAfter": {po: ["Succeeded"]},
    }
    kroky["Cisla_ziva"] = {
        "type": "Select",
        "inputs": {"from": "@body('Sourozenci')",
                   "select": f"@{cislo_kodu(chr(105) + chr(116) + 'em()?[' + lit('Title') + ']')}"},
        "runAfter": {"Sourozenci": ["Succeeded"]},
    }
    # Historie se filtruje POČTEM SEGMENTŮ, ne sloupcem `uroven`: Choice může
    # přijít jako objekt i jako text podle toho, čím byl řádek založený,
    # kdežto počet pomlček v kódu je vlastnost samotného kódu.
    kroky["Uzavrene"] = {
        "type": "Query",
        "inputs": {
            "from": "@outputs('Nacti_Historie')?['body/value']",
            "where": ("@and(startsWith(coalesce(item()?['Title'], ''),"
                      f" concat({v('cil')}, '-')),"
                      " equals(length(split(coalesce(item()?['Title'], ''), '-')),"
                      f" if({je_proces()}, 2, 3)))"),
        },
        "runAfter": {"Cisla_ziva": ["Succeeded"]},
    }
    kroky["Cisla_uzavrena"] = {
        "type": "Select",
        "inputs": {"from": "@body('Uzavrene')",
                   "select": f"@{cislo_kodu(chr(105) + chr(116) + 'em()?[' + lit('Title') + ']')}"},
        "runAfter": {"Uzavrene": ["Succeeded"]},
    }
    kroky["Nove_cislo"] = {
        "type": "Compose",
        "inputs": ("@add(max(union(body('Cisla_ziva'), body('Cisla_uzavrena'),"
                   " createArray(0))), 1)"),
        "runAfter": {"Cisla_uzavrena": ["Succeeded"]},
    }
    kroky["Novy_prefix"] = {
        "type": "Compose",
        "inputs": (f"@concat({v('cil')}, '-', formatNumber(outputs('Nove_cislo'),"
                   f" if({je_proces()}, 'D2', 'D3')))"),
        "runAfter": {"Nove_cislo": ["Succeeded"]},
    }
    return kroky, "Novy_prefix"


def polozka(vyraz):
    """`item()?['<vyraz>']` — zabalené, ať se v generátoru nemíchají uvozovky."""
    return f"item()?['{vyraz}']"


def sber_dotcenych(po):
    """Tři množiny, které kaskáda zasáhne: přesouvaná položka, její dílčí
    procesy a aktivity pod ní.

    Filtry jsou napsané tak, aby platily pro OBĚ úrovně bez větvení:
      - `Deti` u přesunu dílčího procesu nevrátí nic (žádný dílčí proces
        nemá `proces_kod` rovný kódu jiného dílčího procesu),
      - `Vnuci` chytí aktivity v obou případech, protože `dilci_proces_kod`
        buď kódem začíná (proces), nebo se mu rovná (dílčí proces).
    """
    kroky = {}
    kroky["Vlastni"] = {
        "type": "Query",
        "inputs": {
            "from": (f"@if({je_proces()}, outputs('Nacti_Procesy')?['body/value'],"
                     " outputs('Nacti_DilciProcesy')?['body/value'])"),
            "where": f"@equals(coalesce({polozka('Title')}, ''), {v('kod')})",
        },
        "runAfter": {po: ["Succeeded"]},
    }
    kroky["Deti"] = {
        "type": "Query",
        "inputs": {
            "from": "@outputs('Nacti_DilciProcesy')?['body/value']",
            "where": f"@equals(coalesce({polozka('proces_kod')}, ''), {v('kod')})",
        },
        "runAfter": {"Vlastni": ["Succeeded"]},
    }
    kroky["Vnuci"] = {
        "type": "Query",
        "inputs": {
            "from": "@outputs('Nacti_Aktivity')?['body/value']",
            "where": (f"@or(equals(coalesce({polozka('dilci_proces_kod')}, ''), {v('kod')}),"
                      f" startsWith(coalesce({polozka('dilci_proces_kod')}, ''),"
                      f" concat({v('kod')}, '-')))"),
        },
        "runAfter": {"Deti": ["Succeeded"]},
    }
    # Vazba je dotčená, když se mění kód aktivity NEBO kód dílčího procesu.
    # Druhá půlka podmínky je ta, na kterou se zapomíná: aktivita zařazená
    # vedlejší vazbou zvenčí do přesouvaného dílčího procesu svůj kód nemění,
    # ale vazba na nový kód ukazovat musí.
    kroky["Vazby_dotcene"] = {
        "type": "Query",
        "inputs": {
            "from": "@outputs('Nacti_Vazby')?['body/value']",
            "where": (f"@or(startsWith(coalesce({polozka('aktivita_kod')}, ''),"
                      f" concat({v('kod')}, '-')),"
                      f" equals(coalesce({polozka('dilci_proces_kod')}, ''), {v('kod')}),"
                      f" startsWith(coalesce({polozka('dilci_proces_kod')}, ''),"
                      f" concat({v('kod')}, '-')))"),
        },
        "runAfter": {"Vnuci": ["Succeeded"]},
    }
    # Mapa starý → nový přes celý podstrom. Úroveň se odvozuje z počtu
    # segmentů kódu, ne z toho, ze kterého kroku řádek přišel — je to táž
    # informace a nemůže se rozejít.
    kroky["Mapa"] = {
        "type": "Select",
        "inputs": {
            "from": ("@union(body('Vlastni'), body('Deti'), body('Vnuci'))"),
            "select": {
                "stary": f"@coalesce({polozka('Title')}, '')",
                "novy": f"@{novy_kod('coalesce(' + polozka('Title') + chr(44) + chr(32) + chr(39) + chr(39) + ')')}",
                "uroven": ("@if(equals(length(split(coalesce("
                           f"{polozka('Title')}, ''), '-')), 2), 'proces',"
                           " if(equals(length(split(coalesce("
                           f"{polozka('Title')}, ''), '-')), 3), 'dilci_proces',"
                           " 'aktivita'))"),
                "nazev": (f"@coalesce({polozka('nazev_kratky')},"
                          f" {polozka('nazev')}, '')"),
            },
        },
        "runAfter": {"Vazby_dotcene": ["Succeeded"]},
    }
    return kroky, "Mapa"


def odpoved(jmeno, stav, hlaseni, po, prehled="@outputs('Prehled')"):
    return {
        "type": "Response",
        "kind": "PowerApp",
        "inputs": {
            "statusCode": 200,
            "body": {
                "stav": stav,
                "hlaseni": hlaseni,
                "porizeno": "@outputs('Novy_prefix')",
                "prehled": prehled,
            },
            "schema": {"type": "object", "properties": {
                "stav": {"type": "string"},
                "hlaseni": {"type": "string"},
                "porizeno": {"type": "string"},
                "prehled": {"type": "string"},
            }},
        },
        "runAfter": {po: ["Succeeded"]},
    }


def telo(pary):
    """Tělo REST zápisu jako výraz — `json(concat(...))` se skládá špatně,
    proto se posílá objekt a Logic Apps si ho serializuje sám."""
    return pary


def zapis(po):
    """Vznik → historie → zánik. Pořadí je závazné, viz hlavička modulu."""
    kroky = {}

    kroky["Zaloz_proces"] = {
        "type": "If",
        "expression": {"and": [{"equals": [f"@{je_proces()}", True]}]},
        "actions": {
            "Vloz_proces": sp_akce(
                "HttpRequest",
                {"dataset": ep.web(),
                 "parameters/method": "POST",
                 "parameters/uri": rest_adresa(I_PROCESY),
                 "parameters/headers": HLAVICKY_ZAPIS,
                 "parameters/body": {
                     "Title": "@outputs('Novy_prefix')",
                     "nazev": ("@coalesce(first(body('Vlastni'))?['nazev'], '')"),
                     "agenda_kod": f"@{v('cil')}",
                     "vlastnik": ("@coalesce(first(body('Vlastni'))?['vlastnik'], '')"),
                     "puvodni_kod": f"@{v('kod')}",
                 }},
                None),
        },
        "runAfter": {po: ["Succeeded"]},
    }

    # Dílčí procesy: u přesunu procesu jsou to jeho děti, u přesunu dílčího
    # procesu je to on sám. Obojí pokryje filtr na dvě úrovně v Mapě.
    kroky["Mapa_dilci"] = {
        "type": "Query",
        "inputs": {
            "from": "@body('Mapa')",
            "where": f"@equals({polozka('uroven')}, {lit('dilci_proces')})",
        },
        "runAfter": {"Zaloz_proces": ["Succeeded"]},
    }
    kroky["Zaloz_dilci"] = {
        "type": "Foreach",
        "foreach": "@body('Mapa_dilci')",
        "actions": {
            "Vloz_dilci": sp_akce(
                "HttpRequest",
                {"dataset": ep.web(),
                 "parameters/method": "POST",
                 "parameters/uri": rest_adresa(I_DILCI),
                 "parameters/headers": HLAVICKY_ZAPIS,
                 "parameters/body": {
                     "Title": "@items('Zaloz_dilci')?['novy']",
                     "nazev": "@items('Zaloz_dilci')?['nazev']",
                     "proces_kod": ("@join(take(split(items('Zaloz_dilci')?['novy'],"
                                    " '-'), 2), '-')"),
                     "puvodni_kod": "@items('Zaloz_dilci')?['stary']",
                 }},
                None),
        },
        "runAfter": {"Mapa_dilci": ["Succeeded"]},
    }

    # Aktivity se zakládají z PŮVODNÍCH řádků listu, ne z Mapy: Mapa nese jen
    # kód a název, kdežto aktivita má ještě spolupracuje, vnitrni_predpis
    # a text_pro_or. Kdyby se braly z Mapy, přesun by ta pole tiše vyprázdnil.
    kroky["Zaloz_aktivity"] = {
        "type": "Foreach",
        "foreach": "@body('Vnuci')",
        "actions": {
            "Vloz_aktivitu": sp_akce(
                "HttpRequest",
                {"dataset": ep.web(),
                 "parameters/method": "POST",
                 "parameters/uri": rest_adresa(I_AKTIVITY),
                 "parameters/headers": HLAVICKY_ZAPIS,
                 "parameters/body": {
                     "Title": "@" + novy_kod(
                         "items('Zaloz_aktivity')?['Title']"),
                     "nazev": "@coalesce(items('Zaloz_aktivity')?['nazev'], '')",
                     "nazev_kratky": ("@coalesce(items('Zaloz_aktivity')?"
                                      "['nazev_kratky'], '')"),
                     "dilci_proces_kod": "@" + novy_kod(
                         "items('Zaloz_aktivity')?['dilci_proces_kod']"),
                     "vykonava": "@coalesce(items('Zaloz_aktivity')?['vykonava'], '')",
                     "spolupracuje": ("@coalesce(items('Zaloz_aktivity')?"
                                      "['spolupracuje'], '')"),
                     "vnitrni_predpis": ("@coalesce(items('Zaloz_aktivity')?"
                                         "['vnitrni_predpis'], '')"),
                     "text_pro_or": ("@coalesce(items('Zaloz_aktivity')?"
                                     "['text_pro_or'], '')"),
                     "sekce": "@coalesce(items('Zaloz_aktivity')?['sekce'], '')",
                     "stav": ("@coalesce(items('Zaloz_aktivity')?['stav']?['Value'],"
                              " items('Zaloz_aktivity')?['stav'], '')"),
                     "puvodni_kod": "@items('Zaloz_aktivity')?['Title']",
                 }},
                None),
        },
        "runAfter": {"Zaloz_dilci": ["Succeeded"]},
    }

    # Vazby: každý ze dvou kódů se přepisuje samostatně. Ten, který do
    # přesouvaného podstromu nepatří, zůstane — právě tím se přenesou
    # vedlejší vazby ven i dovnitř.
    novy_akt = ("if(startsWith(coalesce(items('Zaloz_vazby')?['aktivita_kod'], ''),"
                f" concat({v('kod')}, '-')),"
                " " + novy_kod("items('Zaloz_vazby')?['aktivita_kod']") + ","
                " items('Zaloz_vazby')?['aktivita_kod'])")
    novy_dp = ("if(or(equals(coalesce(items('Zaloz_vazby')?['dilci_proces_kod'], ''),"
               f" {v('kod')}),"
               " startsWith(coalesce(items('Zaloz_vazby')?['dilci_proces_kod'], ''),"
               f" concat({v('kod')}, '-'))),"
               " " + novy_kod("items('Zaloz_vazby')?['dilci_proces_kod']") + ","
               " items('Zaloz_vazby')?['dilci_proces_kod'])")
    kroky["Zaloz_vazby"] = {
        "type": "Foreach",
        "foreach": "@body('Vazby_dotcene')",
        "actions": {
            "Vloz_vazbu": sp_akce(
                "HttpRequest",
                {"dataset": ep.web(),
                 "parameters/method": "POST",
                 "parameters/uri": rest_adresa(I_VAZBY),
                 "parameters/headers": HLAVICKY_ZAPIS,
                 "parameters/body": {
                     "Title": f"@concat({novy_akt}, '__', {novy_dp})",
                     "aktivita_kod": f"@{novy_akt}",
                     "dilci_proces_kod": f"@{novy_dp}",
                     "primarni": ("@coalesce(items('Zaloz_vazby')?['primarni']?"
                                  "['Value'], items('Zaloz_vazby')?['primarni'], '')"),
                 }},
                None),
        },
        "runAfter": {"Zaloz_aktivity": ["Succeeded"]},
    }

    kroky["Zapis_historii"] = {
        "type": "Foreach",
        "foreach": "@body('Mapa')",
        "actions": {
            "Vloz_historii": sp_akce(
                "HttpRequest",
                {"dataset": ep.web(),
                 "parameters/method": "POST",
                 "parameters/uri": rest_adresa(I_HISTORIE),
                 "parameters/headers": HLAVICKY_ZAPIS,
                 "parameters/body": {
                     "Title": "@items('Zapis_historii')?['stary']",
                     "nazev": "@items('Zapis_historii')?['nazev']",
                     "nastupce_kod": "@items('Zapis_historii')?['novy']",
                     "duvod": f"@{v('duvod')}",
                     "datum": "@utcNow()",
                     "kdo": "@triggerOutputs()?['headers']?['x-ms-user-email-encoded']",
                 }},
                None),
        },
        "runAfter": {"Zaloz_vazby": ["Succeeded"]},
    }

    # ZÁNIK až úplně nakonec. Maže se podle ID dohledaného v načteném listu —
    # nikdy podle kódu naslepo, protože pod tím kódem už mezitím může být
    # nový záznam z tohoto samého běhu.
    kroky["Smaz_vazby"] = {
        "type": "Foreach",
        "foreach": "@body('Vazby_dotcene')",
        "actions": {
            "Smaz_vazbu": sp_akce(
                "HttpRequest",
                {"dataset": ep.web(),
                 "parameters/method": "POST",
                 "parameters/uri": rest_adresa(
                     I_VAZBY, "(', string(items('Smaz_vazby')?['ID']), ')"),
                 "parameters/headers": dict(HLAVICKY_ZAPIS,
                                            **{"X-HTTP-Method": "DELETE",
                                               "IF-MATCH": "*"}),
                 "parameters/body": {}},
                None),
        },
        "runAfter": {"Zapis_historii": ["Succeeded"]},
    }
    kroky["Smaz_aktivity"] = {
        "type": "Foreach",
        "foreach": "@body('Vnuci')",
        "actions": {
            "Smaz_aktivitu": sp_akce(
                "HttpRequest",
                {"dataset": ep.web(),
                 "parameters/method": "POST",
                 "parameters/uri": rest_adresa(
                     I_AKTIVITY, "(', string(items('Smaz_aktivity')?['ID']), ')"),
                 "parameters/headers": dict(HLAVICKY_ZAPIS,
                                            **{"X-HTTP-Method": "DELETE",
                                               "IF-MATCH": "*"}),
                 "parameters/body": {}},
                None),
        },
        "runAfter": {"Smaz_vazby": ["Succeeded"]},
    }
    kroky["Smaz_deti"] = {
        "type": "Foreach",
        "foreach": "@body('Deti')",
        "actions": {
            "Smaz_dite": sp_akce(
                "HttpRequest",
                {"dataset": ep.web(),
                 "parameters/method": "POST",
                 "parameters/uri": rest_adresa(
                     I_DILCI, "(', string(items('Smaz_deti')?['ID']), ')"),
                 "parameters/headers": dict(HLAVICKY_ZAPIS,
                                            **{"X-HTTP-Method": "DELETE",
                                               "IF-MATCH": "*"}),
                 "parameters/body": {}},
                None),
        },
        "runAfter": {"Smaz_aktivity": ["Succeeded"]},
    }
    kroky["Smaz_vlastni"] = {
        "type": "Foreach",
        "foreach": "@body('Vlastni')",
        "actions": {
            "Smaz_polozku": sp_akce(
                "HttpRequest",
                {"dataset": ep.web(),
                 "parameters/method": "POST",
                 "parameters/uri": (
                     "@concat('_api/web/GetList(''', outputs('Cesta_webu'),"
                     f" if({je_proces()}, '/Lists/{I_PROCESY}', '/Lists/{I_DILCI}'),"
                     " ''')/items(', string(items('Smaz_vlastni')?['ID']), ')')"),
                 "parameters/headers": dict(HLAVICKY_ZAPIS,
                                            **{"X-HTTP-Method": "DELETE",
                                               "IF-MATCH": "*"}),
                 "parameters/body": {}},
                None),
        },
        "runAfter": {"Smaz_deti": ["Succeeded"]},
    }
    return kroky, "Smaz_vlastni"


def akce(schema):
    kroky = {}
    kroky["Vstup"] = {
        "type": "Compose",
        "inputs": "@json(triggerBody()?['text'])",
        "runAfter": {},
    }
    kroky["Cesta_webu"] = {
        "type": "Compose",
        "inputs": f"@concat('/', join(skip(split({ep.vyraz(ep.WEB)}, '/'), 3), '/'))",
        "runAfter": {"Vstup": ["Succeeded"]},
    }

    nacteni, po = nacitani()
    kroky.update(nacteni)

    prefix, po = vypocet_prefixu(po)
    kroky.update(prefix)

    # Pod cílovým rodičem došla čísla. Odmítnout je jediná správná reakce —
    # tříciferné BB by rozbilo formát kódu, na kterém stojí celý rejstřík.
    kroky["Kontrola_mista"] = {
        "type": "If",
        "expression": {"greater": ["@outputs('Nove_cislo')",
                                   f"@if({je_proces()}, 99, 999)"]},
        "actions": {
            "Odpoved_plno": odpoved(
                "Odpoved_plno", STAV_PLNO,
                (f"@concat('Pod ', {v('cil')}, ' už není volné číslo."
                 " Přesun nelze provést.')"),
                "", prehled=""),
            "Konec_plno": {
                "type": "Terminate",
                "inputs": {"runStatus": "Succeeded"},
                "runAfter": {"Odpoved_plno": ["Succeeded"]},
            },
        },
        "runAfter": {po: ["Succeeded"]},
    }
    kroky["Kontrola_mista"]["actions"]["Odpoved_plno"]["runAfter"] = {}

    sber, po = sber_dotcenych("Kontrola_mista")
    kroky.update(sber)

    kroky["Prehled_radky"] = {
        "type": "Select",
        "inputs": {
            "from": "@body('Mapa')",
            "select": (f"@concat({polozka('stary')}, {lit(ODD_POLE)},"
                       f" {polozka('novy')}, {lit(ODD_POLE)},"
                       f" {polozka('uroven')}, {lit(ODD_POLE)},"
                       f" {polozka('nazev')})"),
        },
        "runAfter": {po: ["Succeeded"]},
    }
    kroky["Prehled"] = {
        "type": "Compose",
        "inputs": f"@join(body('Prehled_radky'), {lit(ODD_RADKU)})",
        "runAfter": {"Prehled_radky": ["Succeeded"]},
    }

    # Náhled končí běh dřív, než se cokoli zapíše. Odpověď odchází z větve
    # `then` a `Terminate` za ní zaručuje, že zápisové kroky pod podmínkou
    # vůbec nezačnou — vnořovat je do `else` by znamenalo držet celou
    # kaskádu o úroveň hlouběji a Logic Apps se v tom hůř ladí.
    kroky["Je_nahled"] = {
        "type": "If",
        "expression": {"equals": [f"@{v('rezim')}", REZIM_NAHLED]},
        "actions": {
            "Odpoved_nahled": odpoved("Odpoved_nahled", REZIM_NAHLED, "", ""),
            "Konec_nahledu": {
                "type": "Terminate",
                "inputs": {"runStatus": "Succeeded"},
                "runAfter": {"Odpoved_nahled": ["Succeeded"]},
            },
        },
        "runAfter": {"Prehled": ["Succeeded"]},
    }
    kroky["Je_nahled"]["actions"]["Odpoved_nahled"]["runAfter"] = {}

    zapisove, po = zapis("Je_nahled")
    kroky.update(zapisove)

    kroky["Odpoved"] = odpoved("Odpoved", "zapsano", "", po)
    return kroky


def definice_flow(vzor, kroky):
    return {
        "properties": {
            "connectionReferences": vzor["properties"]["connectionReferences"],
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


def trigger():
    """PowerAppV2 s jedním textovým vstupem — týž tvar jako ExportFlow."""
    return {"manual": {
        "type": "Request",
        "kind": "PowerAppV2",
        "inputs": {"schema": {
            "type": "object",
            "properties": {"text": {
                "title": "pozadavek",
                "type": "string",
                "x-ms-dynamically-added": True,
                "description": ('JSON: {"kod": "07-08", "uroven": "proces" | '
                                '"dilci_proces", "cil": "03", "duvod": "…", '
                                '"rezim": "nahled" | "zapis"}'),
            }},
            "required": ["text"],
        }},
    }}


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

    schema = nacti_schema()
    flow = definice_flow(vzor, akce(schema))

    customizations = polozky["customizations.xml"].decode("utf-8-sig")
    solution = polozky["solution.xml"].decode("utf-8-sig")

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

    print(f"přidáno flow: {FLOW}")
    print(f"  GUID: {FLOW_GUID}")
    print(f"  akcí nejvyšší úrovně: {len(flow['properties']['definition']['actions'])}")
    print(f"  režimy vstupu: {REZIM_NAHLED} | {REZIM_ZAPIS}")
    print(f"  schéma rejstříku: {schema['verze']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
