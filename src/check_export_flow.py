# -*- coding: utf-8 -*-
"""Kontrola flow ExportFlow v hotovém solution zipu.

Tři vrstvy jako u check_mapa_flow.py:
1. struktura — jeden trigger PowerAppV2 s jedním textovým vstupem, řetěz
   runAfter bez děr, viditelnost odkazů, zápis souboru necílí na runtime
   výraz, zápis flow na všech třech místech balíku,
2. kontrakt — oba Selecty čtou právě klíče kontraktu, každé textové pole je
   HTML escapované, kód má v excelové tabulce vynucený text, Response vrací
   adresu,
3. význam — výrazy `Html_radky`, `Xls_radky`, `Jmeno` a `Dokument` se
   **vytáhnou z balíku** a vyhodnotí mini-interpretem nad vzorovým zobrazením,
   pro oba formáty. Testuje se tím to, co se opravdu nasazuje, ne kopie
   logiky v Pythonu.

Interpret umí jen funkce, které flow používá. Co nezná, shodí kontrolu —
tiché vrácení prázdna by z brány udělalo divadlo.

Spouštět z kořene projektu:
    python src/check_export_flow.py --solution deploy/procesnimapa_1_0_0_56.zip
"""

import argparse
import html.parser
import json
import re
import sys
import urllib.parse
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402

FLOW = "ExportFlow"
FLOW_GUID = "3f2b6d41-8c55-4a37-9d21-5b8e0c47a9f2"
AKCE = ["Vstup", "Html_radky", "Xls_radky", "Jmeno", "Dokument", "Ulozeni",
        "Cesta_webu", "Adresa", "Odpoved"]
# Zápis souboru je jediná akce uvnitř podmínky `Ulozeni`: v režimu mapy se
# nesmí provést, jinak by export přepsal samotnou mapu.
VNORENA_ZAPISOVA = "Uloz"
REZIM_MAPA = "__mapa__"
REZIM_SABLONA = "__sablona__"
# Vyexportované dokumenty mají od 1.0.0.82 vlastní knihovnu; statické soubory
# webu (mapa, vzorová tabulka) zůstávají v Site Assets. Kdyby se to smíchalo
# zpátky, knihovna s mapou se zas začne plnit odpadem z každého exportu.
SLOZKA_EXPORTU = "/Exporty"
SLOZKA_ASSETS = "/SiteAssets"
SABLONA_SOUBOR = "sablona_import_aktivit.xlsx"
KLICE_RADKU = {"uroven", "kod", "nazev", "vlastnik", "stav"}
TEXTOVA_POLE = ("kod", "nazev", "vlastnik", "stav")
ODSAZENI_PT = 18
SLOUPCU = 5
SLOUPCE = ("Úroveň", "Kód", "Název", "Vlastník / vykonává", "Stav")
# vynucený text v Excelu; bez něj se kód 01-01 uloží jako datum
TEXT_HODNOTA = '"' + chr(92) + '@"'          # hodnota vlastnosti = vynucený text
TEXTOVY_FORMAT = "mso-number-format:" + TEXT_HODNOTA

RAZITKO = "01.01.2026 00:00"
RAZITKO_SOUBOR = "20260101_000000"

chyby = []
kontrol = 0

# Adresa webu z canvas appky. Interpret ji dosazuje za proměnnou prostředí,
# aby šlo ověřit adresu, kterou flow vrací appce.
WEB_APPKY = ""


def overit(podminka, popis):
    global kontrol
    kontrol += 1
    if not podminka:
        chyby.append(popis)


# ---------------------------------------------------------------- interpret

class Chyba(Exception):
    pass


def tokenizuj(vyraz):
    tokeny = []
    i = 0
    while i < len(vyraz):
        znak = vyraz[i]
        if znak.isspace():
            i += 1
        elif znak == "'":
            j = i + 1
            hodnota = []
            while j < len(vyraz):
                if vyraz[j] == "'":
                    if j + 1 < len(vyraz) and vyraz[j + 1] == "'":
                        hodnota.append("'")
                        j += 2
                        continue
                    break
                hodnota.append(vyraz[j])
                j += 1
            if j >= len(vyraz):
                raise Chyba("neuzavřený řetězcový literál")
            tokeny.append(("str", "".join(hodnota)))
            i = j + 1
        elif znak in "(),[]?":
            tokeny.append((znak, znak))
            i += 1
        elif znak.isdigit():
            j = i
            while j < len(vyraz) and vyraz[j].isdigit():
                j += 1
            tokeny.append(("num", int(vyraz[i:j])))
            i = j
        elif znak.isalpha() or znak == "_":
            j = i
            while j < len(vyraz) and (vyraz[j].isalnum() or vyraz[j] == "_"):
                j += 1
            tokeny.append(("ident", vyraz[i:j]))
            i = j
        else:
            raise Chyba(f"neznámý znak {znak!r} ve výrazu")
    return tokeny


class Parser:
    def __init__(self, tokeny):
        self.tokeny = tokeny
        self.i = 0

    def nahled(self):
        return self.tokeny[self.i] if self.i < len(self.tokeny) else (None, None)

    def vezmi(self, typ=None):
        druh, hodnota = self.nahled()
        if typ and druh != typ:
            raise Chyba(f"čekám {typ}, je {druh}")
        self.i += 1
        return hodnota

    def vyraz(self):
        uzel = self.primarni()
        while True:
            druh, _ = self.nahled()
            if druh == "?":
                self.vezmi("?")
                self.vezmi("[")
                klic = self.vyraz()
                self.vezmi("]")
                uzel = ("pristup", uzel, klic, True)
            elif druh == "[":
                self.vezmi("[")
                klic = self.vyraz()
                self.vezmi("]")
                uzel = ("pristup", uzel, klic, False)
            else:
                return uzel

    def primarni(self):
        druh, hodnota = self.nahled()
        if druh == "str":
            self.vezmi()
            return ("konst", hodnota)
        if druh == "num":
            self.vezmi()
            return ("konst", hodnota)
        if druh == "ident":
            jmeno = self.vezmi()
            self.vezmi("(")
            argumenty = []
            if self.nahled()[0] != ")":
                argumenty.append(self.vyraz())
                while self.nahled()[0] == ",":
                    self.vezmi(",")
                    argumenty.append(self.vyraz())
            self.vezmi(")")
            return ("volani", jmeno, argumenty)
        raise Chyba(f"nečekaný token {druh}")


def _text(hodnota):
    if hodnota is None:
        raise Chyba("concat dostal null — chybí coalesce")
    if isinstance(hodnota, bool):
        return "true" if hodnota else "false"
    return str(hodnota)


def vyhodnot(uzel, kontext):
    druh = uzel[0]
    if druh == "konst":
        return uzel[1]
    if druh == "pristup":
        zaklad = vyhodnot(uzel[1], kontext)
        klic = vyhodnot(uzel[2], kontext)
        if zaklad is None:
            if uzel[3]:
                return None
            raise Chyba("přístup do null bez ?")
        if isinstance(zaklad, dict):
            return zaklad.get(klic)
        return zaklad[klic]

    jmeno, argumenty = uzel[1], uzel[2]
    if jmeno == "item":
        return kontext["item"]
    if jmeno == "utcNow":
        return "2026-01-01T00:00:00Z"
    if jmeno == "triggerBody":
        return kontext["triggerBody"]

    hodnoty = [vyhodnot(a, kontext) for a in argumenty]

    if jmeno == "concat":
        return "".join(_text(h) for h in hodnoty)
    if jmeno == "replace":
        return _text(hodnoty[0]).replace(hodnoty[1], hodnoty[2])
    if jmeno == "coalesce":
        for h in hodnoty:
            if h is not None:
                return h
        return None
    if jmeno == "if":
        return hodnoty[1] if hodnoty[0] else hodnoty[2]
    if jmeno == "equals":
        return hodnoty[0] == hodnoty[1]
    if jmeno == "or":
        return any(hodnoty)
    if jmeno == "and":
        return all(hodnoty)
    if jmeno == "not":
        return not hodnoty[0]
    if jmeno == "string":
        return _text(hodnoty[0])
    if jmeno == "int":
        return int(hodnoty[0])
    if jmeno == "sub":
        return hodnoty[0] - hodnoty[1]
    if jmeno == "mul":
        return hodnoty[0] * hodnoty[1]
    if jmeno == "join":
        return hodnoty[1].join(_text(h) for h in hodnoty[0])
    if jmeno == "split":
        return _text(hodnoty[0]).split(hodnoty[1])
    if jmeno == "skip":
        return hodnoty[0][hodnoty[1]:]
    if jmeno == "encodeUriComponent":
        return urllib.parse.quote(_text(hodnoty[0]), safe="")
    if jmeno == "json":
        return json.loads(hodnoty[0])
    if jmeno == "decodeUriComponent":
        return urllib.parse.unquote(hodnoty[0])
    if jmeno == "formatDateTime":
        return RAZITKO_SOUBOR if hodnoty[1] == "yyyyMMdd_HHmmss" else RAZITKO
    if jmeno in ("outputs", "body"):
        if hodnoty[0] not in kontext["akce"]:
            raise Chyba(f"odkaz na akci {hodnoty[0]}, kterou interpret nezná")
        return kontext["akce"][hodnoty[0]]
    # --- funkce doplněné pro kaskádu přesunu (check_presun_flow) ---
    # Interpret je společný; kdyby si každá brána držela vlastní, rozešly by
    # se v tom, co která funkce dělá, a shoda s Logic Apps by se ověřovala
    # dvakrát. Vytažení do vlastního modulu je na příště.
    if jmeno == "substring":
        text = _text(hodnoty[0])
        start = hodnoty[1]
        if len(hodnoty) == 2:
            # Logic Apps chtějí start index MENŠÍ než délka řetězce; Python
            # naproti tomu vrátí text[len(text):] jako prázdno a chybu skryje.
            # Tímhle rozdílem prošla brána nad vadným PresunFlow (04.09.2026):
            # výraz `Mapa` počítal `substring(kod, length(presouvanyKod))`
            # a na položce, jejíž kód JE ten přesouvaný, spadl ostrý běh na
            # 'start index ... should be less than the length of the string'.
            # Trojargumentová varianta zůstává na původní kontrole — u ní
            # se hranice start == délka v provozu nepotvrdila a přísnější
            # pravidlo by shodilo výrazy, které běží (build_flow.py).
            if start < 0 or start >= len(text):
                raise Chyba(
                    f"substring({text!r}, {start}) je mimo rozsah — Logic Apps "
                    "vyžadují start index menší než délka řetězce a běh na tom "
                    "spadne; ošetři to podmínkou (viz zbytek() v "
                    "build_presun_flow.py)")
            return text[start:]
        if start < 0 or hodnoty[2] < 0 or start + hodnoty[2] > len(text):
            raise Chyba(f"substring({text!r}, {start}, {hodnoty[2]}) je mimo rozsah")
        return text[start:start + hodnoty[2]]
    if jmeno == "length":
        return len(hodnoty[0])
    if jmeno == "startsWith":
        return _text(hodnoty[0]).startswith(_text(hodnoty[1]))
    if jmeno == "last":
        return hodnoty[0][-1] if hodnoty[0] else None
    if jmeno == "first":
        return hodnoty[0][0] if hodnoty[0] else None
    if jmeno == "take":
        return hodnoty[0][:hodnoty[1]]
    if jmeno == "empty":
        return not hodnoty[0]
    if jmeno == "add":
        return hodnoty[0] + hodnoty[1]
    if jmeno == "greater":
        return hodnoty[0] > hodnoty[1]
    if jmeno == "max":
        polozky = hodnoty[0] if len(hodnoty) == 1 and isinstance(hodnoty[0], list) else hodnoty
        if not polozky:
            raise Chyba("max nad prázdným polem — chybí createArray(0)")
        return max(polozky)
    if jmeno == "createArray":
        return list(hodnoty)
    if jmeno == "union":
        spojene = []
        for pole in hodnoty:
            for prvek in pole:
                if prvek not in spojene:
                    spojene.append(prvek)
        return spojene
    if jmeno == "formatNumber":
        mist = int(_text(hodnoty[1])[1:])
        return str(hodnoty[0]).rjust(mist, "0")

    if jmeno == "parameters":
        # Proměnná prostředí. Za běhu ji dosadí platforma; tady dosadíme web,
        # na který je připojená appka, aby se složená adresa dala ověřit.
        if hodnoty[0] not in kontext["parametry"]:
            raise Chyba(f"odkaz na proměnnou {hodnoty[0]}, kterou balík nedeklaruje")
        return kontext["parametry"][hodnoty[0]]
    raise Chyba(f"interpret nezná funkci {jmeno}()")


def spust(vyraz, kontext):
    if not isinstance(vyraz, str) or not vyraz.startswith("@"):
        raise Chyba("výraz akce nezačíná @")
    return vyhodnot(Parser(tokenizuj(vyraz[1:])).vyraz(), kontext)


# ------------------------------------------------------------------ vzorek

VZOREK = [
    {"uroven": 1, "kod": "01", "nazev": "Řízení & správa", "vlastnik": "Sekce 3", "stav": ""},
    {"uroven": 2, "kod": "01-01", "nazev": "Proces <A>", "vlastnik": "Odbor 31", "stav": ""},
    {"uroven": 3, "kod": "01-01-001", "nazev": "Dílčí; s středníkem", "vlastnik": None, "stav": ""},
    {"uroven": 4, "kod": "01-01-001-0001", "nazev": 'Aktivita "v uvozovkách"',
     "vlastnik": "Oddělení 311", "stav": "schváleno"},
]
NADPIS = "vše · bez hledání"


def priprav_kontext(akce_def, radky, nadpis, format_, text=None):
    """Projde akce v pořadí řetězu a spočítá je stejně, jako to udělá Logic Apps.

    `text` dovolí poslat vstup, který není JSON — tak si appka říká o adresu
    mapy (`__mapa__`). Kdyby ho `Vstup` nechytil, `json()` by na něm spadl.
    """
    vstup = {"nadpis": nadpis, "format": format_, "radky": radky}
    kontext = {
        "item": None,
        "triggerBody": {"text": text if text is not None
                        else json.dumps(vstup, ensure_ascii=False)},
        "akce": {},
        "parametry": {ep.klic(ep.WEB): WEB_APPKY},
    }
    kontext["akce"]["Vstup"] = spust(akce_def["Vstup"]["inputs"], kontext)

    for jmeno in ("Html_radky", "Xls_radky"):
        vyraz = akce_def[jmeno]["inputs"]["select"]
        zdroj = spust("@" + akce_def[jmeno]["inputs"]["from"].lstrip("@"), kontext)
        vybrane = []
        for polozka in zdroj:
            kontext["item"] = polozka
            vybrane.append(spust(vyraz, kontext))
        kontext["item"] = None
        kontext["akce"][jmeno] = vybrane

    for jmeno in ("Jmeno", "Dokument", "Cesta_webu", "Adresa"):
        kontext["akce"][jmeno] = spust(akce_def[jmeno]["inputs"], kontext)
    return kontext


# ----------------------------------------------------------------- kontroly

def struktura(flow, web):
    definice = flow["properties"]["definition"]
    triggery = definice.get("triggers", {})
    overit(len(triggery) == 1, f"flow musí mít právě jeden trigger, má {len(triggery)}")
    trigger = next(iter(triggery.values())) if triggery else {}
    overit(trigger.get("kind") == "PowerAppV2",
           f"trigger je '{trigger.get('kind')}', čekám PowerAppV2")
    vlastnosti = (trigger.get("inputs", {}).get("schema", {}).get("properties") or {})
    overit(len(vlastnosti) == 1, f"trigger má {len(vlastnosti)} vstupů, čekám právě jeden")
    if len(vlastnosti) == 1:
        jmeno, popis = next(iter(vlastnosti.items()))
        overit(popis.get("type") == "string", f"vstup {jmeno} není typu string")
        overit(jmeno in (trigger["inputs"]["schema"].get("required") or []),
               f"vstup {jmeno} není povinný — appka by mohla zavolat Run() bez dat")

    overit(definice.get("contentVersion") == "1.0.0.0",
           "contentVersion není 1.0.0.0 — flow by po importu nešlo otevřít v designeru")

    akce = definice.get("actions", {})
    overit(sorted(akce) == sorted(AKCE), f"akce {sorted(akce)} != {sorted(AKCE)}")
    if sorted(akce) != sorted(AKCE):
        return None

    zacatky = [j for j, a in akce.items() if not a.get("runAfter")]
    overit(zacatky == ["Vstup"], f"bez předchůdce má být jen Vstup, je {zacatky}")
    poradi = {jmeno: index for index, jmeno in enumerate(AKCE)}
    for index, jmeno in enumerate(AKCE[1:], start=1):
        po = akce[jmeno].get("runAfter", {})
        overit(list(po) == [AKCE[index - 1]] and list(po.values()) == [["Succeeded"]],
               f"{jmeno} nenavazuje na {AKCE[index - 1]} se stavem Succeeded (je {po})")

    # viditelnost odkazů: akce smí číst jen to, co je v řetězu před ní
    for jmeno, definice_akce in akce.items():
        text = json.dumps(definice_akce, ensure_ascii=False)
        for odkaz in set(re.findall(r"(?:outputs|body)\('([^']+)'\)", text)):
            overit(odkaz in poradi and poradi[odkaz] < poradi[jmeno],
                   f"{jmeno} čte {odkaz}, které v řetězu není před ní")

    # Web bere zápis z proměnné prostředí. Do 1.0.0.61 se tu naopak vyžadovala
    # konkrétní adresa — s odvoláním na pravidlo PatchItem, které ale pro
    # CreateFile neplatí: Clearstream i Průvodní list mají v produkci CreateFile
    # s datasetem z proměnné. Složka zůstává literál, je relativní k webu.
    ulozeni = akce["Ulozeni"]
    overit(ulozeni.get("type") == "If",
           "zápis souboru není v podmínce — v režimu mapy by přepsal samotnou mapu")
    vnorene = (ulozeni.get("actions") or {})
    overit(list(vnorene) == [VNORENA_ZAPISOVA],
           f"v podmínce Ulozeni čekám jen {VNORENA_ZAPISOVA}, je {list(vnorene)}")
    if list(vnorene) != [VNORENA_ZAPISOVA]:
        return None
    podminka = json.dumps(ulozeni.get("expression"), ensure_ascii=False)
    for rezim in (REZIM_MAPA, REZIM_SABLONA):
        overit(rezim in podminka and '"not"' in podminka,
               f"podmínka zápisu nevylučuje režim {rezim}: {podminka}")

    parametry = vnorene[VNORENA_ZAPISOVA]["inputs"]["parameters"]
    overit(parametry.get("dataset") == ep.web(),
           "dataset zápisové akce nebere web z proměnné mpsv_procesnimapaSite — "
           "s natvrdo zadanou adresou se flow na cizím tenantu nedá zapnout")
    overit(not str(parametry.get("folderPath", "")).startswith("@"),
           "folderPath zápisové akce je runtime výraz")
    # Zápis do Site Assets by se mísil s publikovanou mapou a její šablonou —
    # přesně to se dělo do 1.0.0.81 a knihovna kvůli tomu přestala být čitelná.
    overit(parametry.get("folderPath") == SLOZKA_EXPORTU,
           f"export se ukládá do {parametry.get('folderPath')!r}, "
           f"čekám vlastní knihovnu {SLOZKA_EXPORTU}")
    overit(vnorene[VNORENA_ZAPISOVA]["inputs"]["host"]["operationId"] == "CreateFile",
           "zápis souboru nepoužívá CreateFile")

    spojeni = flow["properties"].get("connectionReferences") or {}
    overit("shared_sharepointonline" in spojeni,
           "flow nemá spojení na SharePoint — akce by neměly čím běžet")

    odpoved = akce["Odpoved"]
    overit(odpoved.get("kind") == "PowerApp",
           f"Response je druhu '{odpoved.get('kind')}', appka čeká PowerApp")
    overit(list(odpoved["inputs"]["body"]) == ["adresa"],
           "Response nevrací právě klíč 'adresa'")
    overit(list(odpoved["inputs"]["schema"]["properties"]) == ["adresa"],
           "schéma odpovědi neodpovídá vrácenému tělu — appka by hodnotu nepřečetla")
    return akce


def kontrakt(akce):
    for jmeno in ("Html_radky", "Xls_radky"):
        overit(akce[jmeno]["inputs"]["from"] == "@outputs('Vstup')?['radky']",
               f"{jmeno} nečte 'radky' ze vstupu")
        ctene = set(re.findall(r"item\(\)\?\['([^']+)'\]", akce[jmeno]["inputs"]["select"]))
        overit(ctene == KLICE_RADKU,
               f"{jmeno} čte {sorted(ctene)}, kontrakt je {sorted(KLICE_RADKU)}")

    html = akce["Html_radky"]["inputs"]["select"]
    for polozka in TEXTOVA_POLE:
        vzorek = (r"replace\(replace\(replace\(coalesce\(item\(\)\?\['" + polozka +
                  r"'\], ''\), '&'")
        overit(re.search(vzorek, html) is not None,
               f"pole {polozka} není HTML escapované — název se znakem < rozbije dokument")

    xls = akce["Xls_radky"]["inputs"]["select"]
    for polozka in TEXTOVA_POLE:
        vzorek = (r"replace\(replace\(replace\(coalesce\(item\(\)\?\['" + polozka +
                  r"'\], ''\), '&'")
        overit(re.search(vzorek, xls) is not None,
               f"pole {polozka} není v excelové tabulce escapované")
    overit("td {" + TEXTOVY_FORMAT in akce["Dokument"]["inputs"],
           "textový formát není v pravidle td — na hlavičkách (th) je Excelu k ničemu "
           "a z kódu 01-01 zase udělá datum (v provozu 25.08.2026 přesně tak)")

    jmeno = akce["Jmeno"]["inputs"]
    overit("'.doc'" in jmeno and "'.xls'" in jmeno,
           "název souboru nerozlišuje formáty .doc a .xls")
    overit("yyyyMMdd_HHmmss" in jmeno,
           "název souboru nenese časové razítko — souběžné exporty se přepíšou")
    overit("outputs('Vstup')?['format']" in akce["Dokument"]["inputs"],
           "Dokument nerozlišuje formát — appka by dostala pořád totéž")


def vyznam_word(akce, web):
    try:
        kontext = priprav_kontext(akce, VZOREK, NADPIS, "word")
    except Chyba as chyba:
        overit(False, f"wordový výraz z balíku se nepodařilo vyhodnotit: {chyba}")
        return
    overit(True, "wordové výrazy z balíku jdou vyhodnotit")

    dokument = kontext["akce"]["Dokument"]
    overit(dokument.startswith("﻿"),
           "dokument nezačíná BOM — Word by u .doc rozsypal diakritiku")
    overit("<html" in dokument[:200], "dokument nezačíná HTML hlavičkou")
    overit(dokument.endswith("</html>"), "dokument nekončí </html>")
    overit(dokument.count("<tr>") == len(VZOREK) + 1,
           f"dokument má {dokument.count('<tr>')} řádků, čekám {len(VZOREK) + 1} (s hlavičkou)")

    for radek in VZOREK:
        overit(radek["kod"] in dokument, f"kód {radek['kod']} v dokumentu chybí")
    overit("Řízení &amp; správa" in dokument,
           "znak & není escapovaný — Word by dokument četl jako poškozený")
    overit("Proces &lt;A&gt;" in dokument, "znaky < > nejsou escapované")
    overit("<A>" not in dokument, "do dokumentu se dostala neescapovaná značka")
    overit(NADPIS in dokument, "hlavička dokumentu neuvádí, jaké zobrazení se exportovalo")
    overit(RAZITKO in dokument, "dokument neuvádí, kdy vznikl")

    overit(f"padding-left:{ODSAZENI_PT * 3}pt" in dokument,
           f"aktivita (4. úroveň) nemá odsazení {ODSAZENI_PT * 3} pt")
    overit("padding-left:0pt;font-weight:bold" in dokument,
           "agenda (1. úroveň) není tučná ani bez odsazení")
    overit("<td></td>" in dokument,
           "chybějící vlastník nedal prázdnou buňku — null by běh shodil")

    overit(kontext["akce"]["Jmeno"].endswith(".doc"),
           f"formát word dal soubor {kontext['akce']['Jmeno']}")
    overit(kontext["akce"]["Adresa"] == f"{web}{SLOZKA_EXPORTU}/{kontext['akce']['Jmeno']}",
           f"vrácená adresa {kontext['akce']['Adresa']} nemíří na uložený soubor "
           f"v knihovně {SLOZKA_EXPORTU}")


class Tabulka(html.parser.HTMLParser):
    """Rozebere HTML tabulku na řádky buněk — ověřuje se struktura, ne text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.radky = []
        self.tridy = []
        self._radek = None
        self._bunka = None
        self._trida = None

    def handle_starttag(self, znacka, atributy):
        if znacka == "tr":
            self._radek, self._tridy_radku = [], []
        elif znacka in ("td", "th") and self._radek is not None:
            self._bunka = []
            self._trida = dict(atributy).get("class", "")

    def handle_data(self, data):
        if self._bunka is not None:
            self._bunka.append(data)

    def handle_endtag(self, znacka):
        if znacka in ("td", "th") and self._bunka is not None:
            self._radek.append("".join(self._bunka))
            self._tridy_radku.append(self._trida)
            self._bunka = None
        elif znacka == "tr" and self._radek is not None:
            self.radky.append(self._radek)
            self.tridy.append(self._tridy_radku)
            self._radek = None


def rozeber(dokument):
    parser = Tabulka()
    parser.feed(dokument)
    return parser


def css_hodnota(dokument, selektor, vlastnost):
    """Účinná hodnota vlastnosti pro selektor — poslední, jak to dělá kaskáda.

    Číst první pravidlo nestačí: druhé pravidlo se stejným selektorem to první
    přebije a Excel použije jeho hodnotu. Brána, která by se zastavila u první
    shody, by takové rušící pravidlo přehlédla — přesně ta mezera zůstala po
    první opravě B-02 (kolo 4, druhé kolo). Selektory oddělené čárkou se
    rozebírají, aby `td, th { … }` platilo pro obojí.
    """
    styl = re.search(r"<style>(.*?)</style>", dokument, re.S)
    if not styl:
        return None
    hodnota = None
    for pravidlo in re.finditer(r"([^{}]+)\{([^}]*)\}", styl.group(1)):
        if selektor not in [s.strip() for s in pravidlo.group(1).split(",")]:
            continue
        for shoda in re.finditer(re.escape(vlastnost) + r"\s*:\s*([^;}]*)", pravidlo.group(2)):
            hodnota = shoda.group(1).strip()
    return hodnota


def vyznam_excel(akce):
    try:
        kontext = priprav_kontext(akce, VZOREK, NADPIS, "excel")
    except Chyba as chyba:
        overit(False, f"excelový výraz z balíku se nepodařilo vyhodnotit: {chyba}")
        return
    overit(True, "excelové výrazy z balíku jdou vyhodnotit")

    dokument = kontext["akce"]["Dokument"]
    overit(dokument.startswith("﻿"),
           "tabulka nezačíná BOM")
    overit('xmlns:x="urn:schemas-microsoft-com:office:excel"' in dokument,
           "chybí excelový jmenný prostor — Excel by soubor otevřel jako web")
    overit("charset=utf-8" in dokument,
           "chybí hlavička charset — přesně tak se v .csv rozsypala diakritika")
    # Formát se čte jako účinná hodnota z kaskády, ne hledáním řetězce kdekoli
    # v dokumentu: `mso-number-format` na hlavičkách (th) neřekne nic o datových
    # buňkách a druhé pravidlo `td {}` by to první přebilo. Obojí branou prošlo
    # (nález B-02, obě kola).
    overit(css_hodnota(dokument, "td", "mso-number-format") == TEXT_HODNOTA,
           "datové buňky (td) nemají účinný textový formát — "
           "Excel udělá z kódu 01-01 datum")
    overit(css_hodnota(dokument, "td.n", "mso-number-format") == '"0"',
           "sloupec úrovně nemá číselný formát — v Excelu se nedá seřadit ani filtrovat")
    # inline styl buňky by kaskádu přebil a ve <style> bloku by nebyl vidět
    overit("<td style=" not in dokument,
           "buňka excelové tabulky má vlastní styl — ten pravidlo td přebije")
    overit("WordSection1" not in dokument, "do formátu excel se dostal wordový dokument")

    # struktura se čte parserem HTML, ne regulárem: v každém řádku musí sedět
    # počet buněk, i když je v názvu středník nebo uvozovka
    tabulka = rozeber(dokument)
    overit(len(tabulka.radky) == len(VZOREK) + 1,
           f"tabulka má {len(tabulka.radky)} řádků, čekám {len(VZOREK) + 1} (s hlavičkou)")
    overit(all(len(r) == SLOUPCU for r in tabulka.radky),
           f"ne každý řádek má {SLOUPCU} buněk: {sorted({len(r) for r in tabulka.radky})}")
    if len(tabulka.radky) == len(VZOREK) + 1:
        overit(tabulka.radky[0] == list(SLOUPCE),
               f"hlavička je {tabulka.radky[0]}, čekám {list(SLOUPCE)}")
        for vzor, radek, tridy in zip(VZOREK, tabulka.radky[1:], tabulka.tridy[1:]):
            overit(radek[0] == str(vzor["uroven"]), f"úroveň u {vzor['kod']} nesedí")
            overit(tridy[0] == "n",
                   "buňka úrovně nemá třídu s číselným formátem")
            overit(radek[1] == vzor["kod"],
                   f"kód v tabulce je {radek[1]}, čekám {vzor['kod']}")
            overit(radek[2] == vzor["nazev"],
                   f"název v tabulce je {radek[2]!r}, čekám {vzor['nazev']!r}")
            overit(radek[3] == (vzor["vlastnik"] or ""),
                   f"vlastník v tabulce je {radek[3]!r}, čekám {vzor['vlastnik'] or ''!r}")

    overit(NADPIS in dokument, "tabulka neuvádí, jaké zobrazení se exportovalo")
    overit(kontext["akce"]["Jmeno"].endswith(".xls"),
           f"formát excel dal soubor {kontext['akce']['Jmeno']}")


def vyznam_meze(akce):
    velke = [dict(VZOREK[3], kod=f"01-01-001-{i:04d}") for i in range(300)]
    try:
        kontext = priprav_kontext(akce, velke, NADPIS, "word")
    except Chyba as chyba:
        overit(False, f"velké zobrazení se nepodařilo vyhodnotit: {chyba}")
        return
    overit(kontext["akce"]["Dokument"].count("<tr>") == 301,
           "u 300 řádků nevznikl dokument o 300 řádcích")

    for format_, cekam in (("word", 1), ("excel", 1)):
        try:
            prazdny = priprav_kontext(akce, [], NADPIS, format_)
        except Chyba as chyba:
            overit(False, f"prázdné zobrazení ({format_}) shodilo výraz: {chyba}")
            continue
        overit(prazdny["akce"]["Dokument"].count("<tr>") == cekam,
               f"prázdné zobrazení ({format_}) nevyrobilo soubor se samotnou hlavičkou")


def zapis_v_baliku(polozky, klic):
    customizations = polozky["customizations.xml"].decode("utf-8-sig")
    overit(f'Name="{FLOW}"' in customizations,
           "customizations.xml neuvádí flow — import by ho přeskočil")
    overit(customizations.lower().count(f'workflowid="{{{FLOW_GUID}}}"') == 1,
           "uzel <Workflow> flow v customizations.xml není právě jednou")
    overit(klic.split("/")[-1] in customizations,
           "JsonFileName v customizations.xml neodpovídá souboru flow")

    solution = polozky["solution.xml"].decode("utf-8-sig")
    overit(solution.lower().count(f'id="{{{FLOW_GUID}}}"') == 1,
           "RootComponent flow v solution.xml není právě jednou — flow by se do balíku nezahrnulo")


def nacti_web(customizations):
    shoda = re.search(r"<ConnectionReferences>(.*?)</ConnectionReferences>",
                      customizations, re.S)
    data = json.loads(shoda.group(1).replace("&quot;", '"').replace("&amp;", "&"))
    for spojeni in data.values():
        datasety = spojeni.get("dataSets") or {}
        if datasety:
            klic, obsah = next(iter(datasety.items()))
            # S napojením přes proměnné nese klíč suffix se schemaname webu.
            # Do mini-interpretu patří hodnota, kterou bude mít proměnná
            # v provozu — jinak by se adresa měřila proti řetězci, který
            # nikde nevznikne, a kontroly by dokazovaly samy sebe.
            return (obsah.get("datasetOverride") or {}).get("name") or klic
    return None


def vyznam_mapa(akce, web):
    """Vstup `__mapa__` musí vrátit odkaz na náhled knihovny, ne na .html.

    Přímá cesta k souboru skončí kvůli Strict browser file handling stažením
    do Downloads místo zobrazení (ověřeno 20.08.2026), proto se kontroluje
    tvar `AllItems.aspx?id=`, ne jen to, že adresa vede na správný web.
    """
    kontext = priprav_kontext(akce, VZOREK, NADPIS, "word", text=REZIM_MAPA)
    adresa = kontext["akce"]["Adresa"]

    overit(adresa.startswith(web + "/"),
           f"adresa mapy nevede na web appky: {adresa}")
    overit("/SiteAssets/Forms/AllItems.aspx?id=" in adresa,
           f"adresa mapy není odkaz na náhled knihovny — soubor by se stáhl "
           f"místo zobrazení: {adresa}")
    overit(".html" not in adresa.split("?")[0],
           f"adresa mapy míří přímo na soubor, ne na náhled: {adresa}")

    cast_id = adresa.split("?id=")[1].split("&")[0] if "?id=" in adresa else ""
    cesta = urllib.parse.unquote(cast_id)
    overit(cesta.endswith("/SiteAssets/procesni_mapa.html"),
           f"parametr id nevede na publikovanou mapu: {cesta!r}")
    overit(cesta.startswith("/sites/"),
           f"parametr id není server-relative cesta: {cesta!r}")
    overit("%2F" in cast_id,
           "parametr id není URL-enkódovaný — SharePoint by cestu nerozpoznal")

    rodic = urllib.parse.unquote(adresa.split("&parent=")[1]) if "&parent=" in adresa else ""
    overit(rodic == cesta.rsplit("/", 1)[0],
           f"parent neukazuje na složku souboru: {rodic!r} vs {cesta!r}")

    # Exportní větev se tím nesmí rozbít: týž řetěz musí pro běžný vstup dál
    # vracet odkaz na vyexportovaný soubor, ne na mapu.
    bezny = priprav_kontext(akce, VZOREK, NADPIS, "word")["akce"]["Adresa"]
    overit("AllItems.aspx" not in bezny,
           f"běžný export dostal adresu mapy: {bezny}")


# Adresa z reálného kliknutí na mapu v knihovně (PPF DEV, 20.08.2026) — jediný
# tvar, o kterém je ověřeno, že mapu zobrazí místo stažení. `viewid` se
# vypouští: je to GUID zobrazení, v cizím prostředí neznámý, a náhled si
# bez něj vezme výchozí zobrazení.
VZOREK_WEB = "https://ppfbanka.sharepoint.com/sites/DigiData_D/testovaci_subsajta/procesnimapa"
VZOREK_MAPA = (
    VZOREK_WEB + "/SiteAssets/Forms/AllItems.aspx"
    "?id=%2Fsites%2FDigiData%5FD%2Ftestovaci%5Fsubsajta%2Fprocesnimapa"
    "%2FSiteAssets%2Fprocesni%5Fmapa%2Ehtml"
    "&parent=%2Fsites%2FDigiData%5FD%2Ftestovaci%5Fsubsajta%2Fprocesnimapa%2FSiteAssets"
)


def vyznam_mapa_vzorek(akce):
    """Skládaná adresa musí pro známý web vyjít znak po znaku jako ta ověřená.

    Kontroly tvaru výše projdou i adrese, která se liší enkódováním — a právě
    tím se pozná, jestli SharePoint mapu zobrazí, nebo pošle do Downloads.
    Proti hádání pomáhá jediné: porovnat s odkazem, který v prostředí
    prokazatelně fungoval.
    """
    global WEB_APPKY
    puvodni = WEB_APPKY
    WEB_APPKY = VZOREK_WEB
    try:
        adresa = priprav_kontext(akce, VZOREK, NADPIS, "word",
                                 text=REZIM_MAPA)["akce"]["Adresa"]
    finally:
        WEB_APPKY = puvodni

    overit(adresa == VZOREK_MAPA,
           "skládaná adresa mapy se liší od ověřeného odkazu z knihovny:\n"
           f"      čekám: {VZOREK_MAPA}\n"
           f"      mám:   {adresa}")


def vyznam_sablona(akce, web):
    """Vstup `__sablona__` musí vrátit přímou cestu k sešitu v Site Assets.

    Na rozdíl od mapy se má soubor stáhnout, ne zobrazit — přímá cesta je
    tedy správně, protože Strict browser file handling na ní pošle
    Content-Disposition: attachment. Zároveň se v tomhle režimu nesmí nic
    uložit: název by vyšel na .doc/.xls a v Site Assets by přibýval odpad
    při každém stažení šablony.
    """
    kontext = priprav_kontext(akce, VZOREK, NADPIS, "word", text=REZIM_SABLONA)
    adresa = kontext["akce"]["Adresa"]

    overit(adresa == f"{web}{SLOZKA_ASSETS}/{SABLONA_SOUBOR}",
           f"adresa vzorové tabulky není přímá cesta k souboru: {adresa}")
    overit("AllItems.aspx" not in adresa,
           f"adresa vzorové tabulky je odkaz na náhled — sešit by se otevřel "
           f"místo stažení: {adresa}")

    # Týž řetěz musí pro běžný vstup dál vracet vyexportovaný soubor.
    bezny = priprav_kontext(akce, VZOREK, NADPIS, "word")["akce"]["Adresa"]
    overit(not bezny.endswith(SABLONA_SOUBOR),
           f"běžný export dostal adresu vzorové tabulky: {bezny}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True)
    argumenty = parser.parse_args()

    cesta = Path(argumenty.solution)
    if not cesta.exists():
        raise SystemExit(f"CHYBA: solution {cesta} neexistuje")
    with zipfile.ZipFile(cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klice = [n for n in polozky if n.replace("\\", "/").startswith(f"Workflows/{FLOW}")]
    overit(len(klice) == 1, f"čekám právě jedno {FLOW}, je jich {len(klice)}")
    if len(klice) != 1:
        return vypis()
    klic = klice[0]
    overit(FLOW_GUID.upper() in klic, f"soubor flow nenese očekávané GUID: {klic}")

    web = nacti_web(polozky["customizations.xml"].decode("utf-8-sig"))
    global WEB_APPKY
    WEB_APPKY = web
    overit(web is not None, "v balíku není adresa webu canvas appky")

    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    akce = struktura(flow, web)
    if akce:
        kontrakt(akce)
        vyznam_word(akce, web)
        vyznam_excel(akce)
        vyznam_meze(akce)
        vyznam_mapa(akce, web)
        vyznam_mapa_vzorek(akce)
        vyznam_sablona(akce, web)
    zapis_v_baliku(polozky, klic)
    return vypis()


def vypis():
    print(f"kontrol: {kontrol}")
    for chyba in chyby:
        print(f"CHYBA: {chyba}")
    print("NEPROŠLO" if chyby else f"OK — {FLOW} odpovídá kontraktu")
    return 1 if chyby else 0


if __name__ == "__main__":
    sys.exit(main())
