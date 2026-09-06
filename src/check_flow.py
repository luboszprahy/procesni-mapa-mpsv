# -*- coding: utf-8 -*-
"""Kontrola flow AktualizaceKratkehoNazvu v hotovém solution zipu.

Dvě vrstvy:
1. struktura — trigger, proměnné místo GUIDů, řetěz runAfter, tvar REST zápisu,
2. význam — výrazy se **vytáhnou z balíku a vyhodnotí** mini-interpretem
   a porovnají s kanonickou zkratit() z check_schema.py. Testuje se tím to,
   co se opravdu nasazuje, ne kopie logiky v Pythonu.

Spouštět z kořene projektu:
    python src/check_flow.py --solution deploy/procesnimapa_1_0_0_9.zip
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_schema import zkratit  # noqa: E402
import env_promenne as ep  # noqa: E402

GUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"

MAXLEN = 150

# Adresa, kterou brána dosadí za proměnnou webu při vyhodnocení výrazů.
TESTOVACI_WEB = "https://tenant.sharepoint.com/sites/procesnimapa"
CESTA_WEBU = "/sites/procesnimapa"

chyby = []
kontrol = 0


def overit(podminka, popis):
    global kontrol
    kontrol += 1
    if not podminka:
        chyby.append(popis)


# ---------------------------------------------------------------- interpret

def tokenizuj(vyraz):
    vzor = re.compile(r"""\s*(?:('(?:[^']|'')*')|(-?\d+)|([A-Za-z_][A-Za-z0-9_]*)|(\?\[)|(.))""")
    tokeny, pozice = [], 0
    while pozice < len(vyraz):
        shoda = vzor.match(vyraz, pozice)
        if not shoda:
            break
        pozice = shoda.end()
        retezec, cislo, jmeno, index, znak = shoda.groups()
        if retezec is not None:
            tokeny.append(("str", retezec[1:-1].replace("''", "'")))
        elif cislo is not None:
            tokeny.append(("num", int(cislo)))
        elif jmeno is not None:
            tokeny.append(("id", jmeno))
        elif index is not None:
            tokeny.append(("idx", "?["))
        elif znak.strip():
            tokeny.append(("sym", znak))
    return tokeny


class Parser:
    def __init__(self, tokeny):
        self.t, self.i = tokeny, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def vezmi(self):
        token = self.peek()
        self.i += 1
        return token

    def vyraz(self):
        druh, hodnota = self.vezmi()
        if druh in ("str", "num"):
            uzel = ("lit", hodnota)
        elif druh == "id":
            argumenty = []
            if self.peek() == ("sym", "("):
                self.vezmi()
                while self.peek() != ("sym", ")"):
                    argumenty.append(self.vyraz())
                    if self.peek() == ("sym", ","):
                        self.vezmi()
                self.vezmi()
            uzel = ("call", hodnota, argumenty)
        else:
            raise ValueError(f"necekany token {(druh, hodnota)}")
        while self.peek() == ("idx", "?["):
            self.vezmi()
            klic = self.vezmi()[1]
            self.vezmi()  # ]
            uzel = ("index", uzel, klic)
        return uzel


def vyhodnot(uzel, vystupy, polozka):
    """Vyhodnocuje **hladově** — obě větve if(), jak to dělá Logic Apps."""
    druh = uzel[0]
    if druh == "lit":
        return uzel[1]
    if druh == "index":
        zaklad = vyhodnot(uzel[1], vystupy, polozka)
        return zaklad.get(uzel[2]) if isinstance(zaklad, dict) else None
    _, jmeno, args = uzel
    a = [vyhodnot(x, vystupy, polozka) for x in args]

    if jmeno == "triggerBody":
        return polozka
    if jmeno == "body":
        # Nacti_aktivitu vrací tentýž řádek, jen čtený těsně před zápisem —
        # pro vyhodnocení výrazů je to stejná položka jako z triggeru.
        if a[0] != "Nacti_aktivitu":
            raise ValueError(f"body('{a[0]}') — neznámá akce")
        return polozka
    if jmeno == "parameters":
        # Testovací hodnota proměnné webu — konkrétní tenant je jedno,
        # ověřuje se tvar složené adresy, ne adresa sama.
        if a[0] != ep.klic(ep.WEB):
            raise ValueError(f"parameters('{a[0]}') — čekal jsem proměnnou webu")
        return TESTOVACI_WEB
    if jmeno == "split":
        return a[0].split(a[1])
    if jmeno == "skip":
        return a[0][a[1]:]
    if jmeno == "join":
        return a[1].join(a[0])
    if jmeno == "string":
        return str(a[0])
    if jmeno == "outputs":
        if a[0] not in vystupy:
            raise ValueError(f"outputs('{a[0]}') — takova akce pred nim neni")
        return vystupy[a[0]]
    if jmeno == "coalesce":
        return next((x for x in a if x not in (None, "")), a[-1])
    if jmeno == "trim":
        return a[0].strip()
    if jmeno == "replace":
        return a[0].replace(a[1], a[2])
    if jmeno == "decodeUriComponent":
        return re.sub(r"%([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), a[0]) \
            if "%E2" not in a[0] else "…"
    if jmeno == "length":
        return len(a[0])
    if jmeno == "substring":
        start, delka = a[1], a[2]
        if start < 0 or delka < 0 or start + delka > len(a[0]):
            raise ValueError(f"substring mimo rozsah: delka={len(a[0])} start={start} n={delka}")
        return a[0][start:start + delka]
    if jmeno == "min":
        return min(a)
    if jmeno == "max":
        return max(a)
    if jmeno == "sub":
        return a[0] - a[1]
    if jmeno == "if":
        return a[1] if a[0] else a[2]
    if jmeno == "greater":
        return a[0] > a[1]
    if jmeno == "lessOrEquals":
        return a[0] <= a[1]
    if jmeno == "lastIndexOf":
        return a[0].rfind(a[1])
    if jmeno == "contains":
        return a[1] in a[0]
    if jmeno == "concat":
        return "".join(a)
    if jmeno == "equals":
        return a[0] == a[1]
    if jmeno == "not":
        return not a[0]
    raise ValueError(f"neznama funkce {jmeno}()")


def spocitej(akce, nazev, nazev_kratky=""):
    """Projde Compose akce v pořadí runAfter a vrátí hodnotu Cil."""
    polozka = {"nazev": nazev, "nazev_kratky": nazev_kratky, "ID": 1}
    vystupy = {}
    for jmeno in poradi(akce):
        definice = akce[jmeno]
        if definice.get("type") != "Compose":
            continue
        vyraz = definice["inputs"]
        if not vyraz.startswith("@"):
            raise ValueError(f"{jmeno}: vstup neni vyraz")
        strom = Parser(tokenizuj(vyraz[1:])).vyraz()
        vystupy[jmeno] = vyhodnot(strom, vystupy, polozka)
    return vystupy["Cil"], vystupy


def poradi(akce):
    """Akce seřazené podle runAfter; cyklus nebo osiřelý odkaz je chyba."""
    hotove, zbyva, vysledek = set(), dict(akce), []
    while zbyva:
        volne = [j for j, d in zbyva.items() if set(d.get("runAfter") or {}) <= hotove]
        if not volne:
            raise ValueError(f"runAfter nevede k porade — zbyva {sorted(zbyva)}")
        for jmeno in sorted(volne):
            vysledek.append(jmeno)
            hotove.add(jmeno)
            zbyva.pop(jmeno)
    return vysledek


# ---------------------------------------------------------------- vzorky

HRANICNI = [
    "", "   ",
    "Vede spisovou sluzbu.",
    "A" * MAXLEN,
    "A" * (MAXLEN + 1),
    "A" * 200 + " konec",
    ("slovo " * 40).strip(),
    "Prvni  cast   se    tremi     mezerami " + "z" * 200,
    "Radek\nzalomeny\ta tabulatorem " + "q" * 200,
    "a" * 100 + " konec, " + "b" * 100,
    "a" * 100 + " konec., " + "b" * 100,
    "a" * 100 + " konec.;, " + "b" * 100,
]


def nazvy_z_csv(cesta):
    if not os.path.exists(cesta):
        return []
    with io.open(cesta, encoding="utf-8-sig", newline="") as soubor:
        return [r["nazev"] for r in csv.DictReader(soubor, delimiter=";")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True)
    argumenty = parser.parse_args()

    with zipfile.ZipFile(argumenty.solution) as balik:
        workflow = [n for n in balik.namelist()
                    if n.replace("\\", "/").startswith("Workflows/AktualizaceKratkehoNazvu")]
        overit(len(workflow) == 1,
               f"v balíku není právě jedno flow AktualizaceKratkehoNazvu (nalezeno {len(workflow)})")
        if not workflow:
            print("CHYBA: flow v balíku chybí")
            return 1
        flow = json.loads(balik.read(workflow[0]).decode("utf-8-sig"))

    definice = flow["properties"]["definition"]
    akce = definice["actions"]

    # --- struktura ---
    overit(definice.get("contentVersion") == "1.0.0.0",
           "contentVersion není '1.0.0.0' — flow by po importu nešlo otevřít v designeru")
    trigger = next(iter(definice["triggers"].values()))
    overit(trigger["inputs"]["host"]["operationId"] == "GetOnUpdatedItems",
           "trigger není 'when an item is created or modified'")
    # Trigger, čtení i zápis berou list z proměnné prostředí. Do 1.0.0.97
    # tu byl GUID natvrdo kvůli PatchItem; od F14 zapisuje REST, který
    # proměnnou snese, a balík je tím pro každý tenant stejný.
    overit(trigger["inputs"]["parameters"]["table"] == ep.list_param("Aktivity"),
           f"trigger nebere list z proměnné mpsv_listAktivity (je tam "
           f"'{trigger['inputs']['parameters']['table']}')")
    overit(trigger["inputs"]["parameters"]["dataset"] == ep.web(),
           "trigger nebere web z proměnné mpsv_procesnimapaSite")
    overit("shared_sharepointonline" in json.dumps(flow["properties"].get("connectionReferences", {})),
           "chybí connection reference na SharePoint")

    # Žádný GUID v celém flow — přesně to F14 ruší. Balík s GUIDem cizího
    # tenantu odešel do MPSV třikrát (naposledy 1.0.0.96) a flow tam nešlo
    # zapnout: "GetTable … List not found".
    guidy = sorted(set(re.findall(GUID, json.dumps(definice, ensure_ascii=False))))
    overit(not guidy, f"v definici flow je GUID natvrdo: {guidy[:2]}")

    zapis = akce.get("Lisi_se", {}).get("actions", {}).get("Zapsat_kratky_nazev")
    overit(zapis is not None, "chybí zápisová akce Zapsat_kratky_nazev")
    if zapis:
        parametry = zapis["inputs"]["parameters"]
        # `Send an HTTP request to SharePoint`, ne PatchItem: ten si schéma
        # rozloženého těla `item/<sloupec>` odvozuje z konkrétního listu,
        # takže `table` musel být GUID natvrdo (MPSV 28.08.2026, 1.0.0.64).
        overit(zapis["inputs"]["host"]["operationId"] == "HttpRequest",
               f"zápis není HttpRequest, ale "
               f"'{zapis['inputs']['host'].get('operationId')}'")
        overit(parametry.get("dataset") == ep.web(),
               "zápisová akce nebere web z proměnné mpsv_procesnimapaSite")
        overit(parametry.get("parameters/method") == "POST",
               f"metoda zápisu není POST (je '{parametry.get('parameters/method')}')")

        hlavicky = parametry.get("parameters/headers") or {}
        # Bez X-HTTP-Method: MERGE by POST na /items(ID) nezměnil řádek,
        # ale pokusil se založit další.
        overit(str(hlavicky.get("X-HTTP-Method", "")).upper() == "MERGE",
               f"chybí hlavička X-HTTP-Method: MERGE (je {hlavicky.get('X-HTTP-Method')!r})")
        overit(hlavicky.get("IF-MATCH") == "*",
               f"chybí hlavička IF-MATCH: * (je {hlavicky.get('IF-MATCH')!r})")
        overit("nometadata" in str(hlavicky.get("Content-Type", "")),
               "Content-Type není odata=nometadata — tělo by muselo nést __metadata.type")
        overit("nometadata" in str(hlavicky.get("Accept", "")),
               "Accept není odata=nometadata")

        telo = parametry.get("parameters/body")
        # MERGE mění jen uvedené sloupce. Povinná pole listu se posílat
        # nesmí: PatchItem je vyžadoval, tady by jen zvyšovaly riziko, že
        # zápis vrátí novější editaci na hodnotu čtenou před výpočtem.
        overit(isinstance(telo, dict) and set(telo) == {"nazev_kratky"},
               f"tělo zápisu není právě {{nazev_kratky}}, ale {sorted(telo) if isinstance(telo, dict) else telo!r}")
        if isinstance(telo, dict):
            overit(telo.get("nazev_kratky") == "@outputs('Cil')",
                   f"zápis neplní nazev_kratky výstupem Cil (je "
                   f"'{telo.get('nazev_kratky')}')")
        overit(not any("triggerBody" in str(v) for v in (telo or {}).values()),
               "zápis bere hodnotu ze snímku triggeru — přepíše novější editaci")

    # Čtení čerstvého stavu řádku. Bez něj by se porovnávalo se snímkem
    # triggeru, starým až o minutu.
    nacti = akce.get("Nacti_aktivitu")
    overit(nacti is not None, "chybí akce Nacti_aktivitu (čerstvý stav řádku)")
    if nacti:
        overit(nacti["inputs"]["host"]["operationId"] == "GetItem",
               "Nacti_aktivitu není GetItem")
        overit(nacti["inputs"]["parameters"].get("table") == ep.list_param("Aktivity"),
               "Nacti_aktivitu nebere list z proměnné mpsv_listAktivity")
        overit(nacti["inputs"]["parameters"].get("dataset") == ep.web(),
               "Nacti_aktivitu nebere web z proměnné mpsv_procesnimapaSite")
        overit(nacti["inputs"]["parameters"].get("id") == "@triggerBody()?['ID']",
               "Nacti_aktivitu nečte řádek podle ID z triggeru")

    podminka = json.dumps(akce.get("Lisi_se", {}).get("expression", {}), ensure_ascii=False)
    overit("not" in podminka and "Cil" in podminka and "nazev_kratky" in podminka,
           "podmínka neporovnává uložený nazev_kratky s vypočteným Cil (hrozí cyklení)")

    try:
        overit(poradi(akce) is not None, "")
    except ValueError as chyba:
        overit(False, f"řetěz runAfter je rozbitý: {chyba}")

    # --- význam: vyhodnotit výrazy z balíku ---
    vzorky = list(HRANICNI)
    for zdroj in ("runs/normalize/aktivity.csv", "runs/anonym/aktivity.csv"):
        vzorky += nazvy_z_csv(zdroj)

    neshody, pady = [], []
    for vzorek in vzorky:
        try:
            cil, _ = spocitej(akce, vzorek)
        except ValueError as chyba:
            pady.append((vzorek[:40], str(chyba)))
            continue
        if cil != zkratit(vzorek, MAXLEN):
            neshody.append((vzorek[:40], zkratit(vzorek, MAXLEN)[-40:], cil[-40:]))

    # REST adresa zápisu se VYHODNOTÍ, ne jen porovná textem. Chytí to
    # špatně zdvojený apostrof (Logic Apps escapují ''), zapomenuté /items
    # i cestu skládanou z něčeho jiného než z proměnné webu.
    _, vystupy = spocitej(akce, "Vede spisovou sluzbu.")
    overit(vystupy.get("Cesta_webu") == CESTA_WEBU,
           f"Cesta_webu nedává server-relativní cestu webu "
           f"(je '{vystupy.get('Cesta_webu')}', čekám '{CESTA_WEBU}')")
    if zapis:
        uri_vyraz = str(zapis["inputs"]["parameters"].get("parameters/uri", ""))
        ocekavana = f"_api/web/GetList('{CESTA_WEBU}/Lists/Aktivity')/items(1)"
        try:
            strom = Parser(tokenizuj(uri_vyraz[1:])).vyraz()
            uri = vyhodnot(strom, vystupy, {"ID": 1})
        except ValueError as chyba:
            uri = f"<nevyhodnotitelné: {chyba}>"
        overit(uri == ocekavana,
               f"REST adresa zápisu je '{uri}', čekám '{ocekavana}'")

    overit(not pady, f"výraz spadl na {len(pady)} vzorcích: {pady[:2]}")
    overit(not neshody, f"výsledek se liší od zkratit() na {len(neshody)} vzorcích: {neshody[:2]}")

    # idempotence: druhý průchod nad vlastním výstupem nesmí chtít další zápis
    nestabilni = []
    for vzorek in vzorky:
        try:
            cil, _ = spocitej(akce, vzorek)
            znovu, _ = spocitej(akce, vzorek, nazev_kratky=cil)
        except ValueError:
            continue
        if znovu != cil:
            nestabilni.append(vzorek[:40])
    overit(not nestabilni, f"výpočet není stabilní — flow by cyklilo na {nestabilni[:2]}")

    print(f"kontrol: {kontrol}, chyb: {len(chyby)}   vzorků vyhodnoceno: {len(vzorky)}")
    for text in chyby:
        print(f"CHYBA: {text}")
    if chyby:
        print("\nNEPROŠLO — flow neimportovat")
        return 1
    print("\nOK — flow odpovídá zadání a jeho výrazy počítají totéž co zkratit()")
    return 0


if __name__ == "__main__":
    sys.exit(main())
