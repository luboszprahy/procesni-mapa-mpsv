# -*- coding: utf-8 -*-
"""Kontrola flow AktualizaceKratkehoNazvu v hotovém solution zipu.

Dvě vrstvy:
1. struktura — trigger, GUID listu, řetěz runAfter, tvar zápisové akce,
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

MAXLEN = 150
LIST_AKTIVITY = "9dfbb5a1-65a6-4fd4-b9f9-fdd35fa246cd"

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
    overit(trigger["inputs"]["parameters"]["table"] == LIST_AKTIVITY,
           "trigger nemíří na list Aktivity")
    overit("shared_sharepointonline" in json.dumps(flow["properties"].get("connectionReferences", {})),
           "chybí connection reference na SharePoint")

    zapis = akce.get("Lisi_se", {}).get("actions", {}).get("Zapsat_kratky_nazev")
    overit(zapis is not None, "chybí zápisová akce Zapsat_kratky_nazev")
    if zapis:
        parametry = zapis["inputs"]["parameters"]
        overit(zapis["inputs"]["host"]["operationId"] == "PatchItem",
               "zápis není PatchItem (Update item)")
        overit(parametry.get("table") == LIST_AKTIVITY,
               "zápisová akce nemá GUID listu natvrdo — s runtime výrazem nejde flow zapnout")
        overit(not str(parametry.get("dataset", "")).startswith("@"),
               "zápisová akce má web jako runtime výraz")
        overit(parametry.get("item/nazev_kratky") == "@outputs('Cil')",
               "zápis neplní nazev_kratky výstupem Cil")
        # Flow smí do řádku poslat jen to, co samo spočítalo, a `Title`, podle
        # kterého SharePoint řádek najde. `nazev` a `dilci_proces_kod` odsud
        # 23.08.2026 zmizely (auditní nález A-07): posílaly se ze snímku
        # triggeru starého až o minutu, takže opravu názvu uloženou krátce po
        # prvním zápisu flow tiše vrátilo na starou hodnotu. Odebírá je
        # `oprav_flow_kratky_nazev()` v build_app.py — kontrola tady tedy musí
        # čekat dvojici, ne původní čtveřici, jinak si obě strany odporují
        # (rozešly se a spadlo to až 24.08.2026).
        polozky = {k: v for k, v in parametry.items() if k.startswith("item/")}
        overit(set(polozky) == {"item/Title", "item/nazev_kratky"},
               f"zápis nemá právě Title + nazev_kratky: {sorted(polozky)}")
        for sloupec, hodnota in polozky.items():
            if sloupec == "item/nazev_kratky":
                continue
            ocekavano = "@triggerBody()?['%s']" % sloupec.split("/", 1)[1]
            overit(hodnota == ocekavano,
                   f"{sloupec} se nevrací beze změny z triggeru (je tam '{hodnota}')")

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
