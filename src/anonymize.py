"""Lehka anonymizace normalizovaneho modelu pro vyvoj v cizim tenantu (PPF).

Zachovava strukturu, pocty i kody; maze identifikaci uradu, osob, utvaru
a internich predpisu. Vystup je urcen k nahrani do vyvojoveho SharePointu.
"""
import argparse
import csv
import io
import json
import re
from pathlib import Path

# nazev uradu a jeho okoli
TOKENY = [
    (r"\bMPSV\b", "XÚ"),
    (r"\bÚP ČR\b", "KAG"),
    (r"\bSÚIP\b", "INSP"),
    (r"\bISoSS\b", "ISX"),
    (r"\bOSYS\b", "MODA"),
    (r"\bOPZ\+", "OPX+"),
    (r"\bOPZ\b", "OPX"),
    (r"\bESF\b", "EUF"),
    (r"\bEHP\b", "EHF"),
    (r"\bLRV\b", "PORV"),
    (r"\bEKLEP\b", "EDOC"),
    (r"\bVOS\b", "VOZ"),
    (r"Generali pojišťovna a\.s\.", "Pojišťovna A a.s."),
    (r"Kooperativa pojišťovna, a\.s\., Vienna Insurance Group", "Pojišťovna B a.s."),
    (r"Ing\. Tomáš Kroutil", "Ing. Jan Novák"),
]

# Organizacni struktura. Do 06.09.2026 tu bylo deset cisel napsanych rucne,
# protoze ciselnik utvaru byl zastupny a mel jen ty, ktere se objevily v datech.
# Od skutecneho MPSV listu jich je 44 a maji vlastni hierarchii, kterou z cisla
# odvodit nejde - mapovani proto vznika z ciselniku, ne z ruky.
#
# Anonymni kod se prideluje po urovnich: ministr = 1, sekce 7, 8, 9, a kazde
# dite dostane <kod rodice><poradi>. Deti jednoho rodice se cisluji spolecne
# bez ohledu na uroven, aby oddeleni bez odboru (O401 pod Sekci 4) nekolidovalo
# s odborem. Delka anonymniho cisla tak zustava vodítkem, ale zavazna je
# hierarchie v nadrizeny_kod - stejne jako u skutecnych dat.
# Anonymni prostor zacina devitkou, protoze zadny skutecny kod MPSV devitkou
# nezacina. Bez toho se anonymni cislo trefilo do skutecneho (O12 dostalo 11,
# coz je zaroven skutecny odbor O11) a pojistka v make_import.py takovou sadu
# spravne odmitla jako neanonymizovanou - rozlisit je od sebe totiz nejde.
UTVARY_CSV = "runs/normalize/utvary.csv"
KOD_MINISTRA_ANON = "9"


def nacti_ciselnik(cesta):
    with io.open(cesta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def mapuj_utvary(radky):
    """Skutecny kod -> anonymni. Prochazi strom shora, aby dite znalo rodice."""
    deti = {}
    for r in radky:
        deti.setdefault(r["nadrizeny_kod"], []).append(r)

    mapa = {}
    koreny = [r for r in radky if r["uroven"] == "ministr"]
    for r in koreny:
        mapa[r["kod"]] = KOD_MINISTRA_ANON

    def sestup(kod):
        for i, dite in enumerate(deti.get(kod, []), start=1):
            mapa[dite["kod"]] = mapa[kod] + str(i)
            sestup(dite["kod"])

    for r in koreny:
        sestup(r["kod"])

    # Utvary mimo strom (ve zdroji je O33 nadrizeny sam sobe, takze zustal bez
    # rodice) se privesi za posledni dite ministra, at maji taky anonymni kod.
    dalsi = len(deti.get(koreny[0]["kod"], [])) if koreny else 0
    for r in radky:
        if r["kod"] not in mapa:
            dalsi += 1
            mapa[r["kod"]] = KOD_MINISTRA_ANON + str(dalsi)
            sestup(r["kod"])

    obraceny = {}
    for skutecny, anonymni in mapa.items():
        if anonymni in obraceny:
            raise SystemExit(
                "CHYBA: anonymni kod %s by patril utvarum %s i %s"
                % (anonymni, obraceny[anonymni], skutecny))
        obraceny[anonymni] = skutecny
    return mapa


def anonymni_nazev(radek, mapa):
    """Tvar 'Utvar 71 (odbor)', ne 'Sekce 7' ani 'O71'.

    Dva duvody, oba overene: kontrola anonymity hlida vzor 'sekce <cislice>'
    jako identifikujici udaj, takze 'Sekce 7' by ji spustil; a 'O71' je tvar,
    kterym se oznacuji SKUTECNE utvary MPSV - anonymni 'O11' by se dal splest
    s existujicim odborem, jen by znamenal neco jineho.
    """
    return "Utvar %s (%s)" % (mapa[radek["kod"]], radek["uroven"])


CISELNIK = nacti_ciselnik(UTVARY_CSV) if Path(UTVARY_CSV).exists() else []
UTVARY = mapuj_utvary(CISELNIK) if CISELNIK else {}

# jednociferne kody se nahrazuji jen za slovem "sekce" — jinak by se trefily
# do cisel v pravnich odkazech ("§ 364 odst. 4 - 6")
VICEMISTNE = sorted((k for k in UTVARY if len(k) > 1), key=len, reverse=True)
RE_UTVAR = re.compile(r"(?<![\d/])(" + "|".join(VICEMISTNE) + r")(?![\d/])")
RE_SEKCE = re.compile(r"\b(sekc\w*)(\s+)(\d)\b", re.IGNORECASE)
RE_PREDPIS = re.compile(r"\b(SP NST|MP NST|MP ST|SP MV|MP MV|SP|PM|MP)\s*(\d+)/(\d{4})")


class Predpisy:
    """Stabilni prejmenovani internich predpisu: SP 10/2021 -> VP 01/2020."""

    def __init__(self):
        self.map = {}

    def __call__(self, m):
        klic = m.group(0)
        if klic not in self.map:
            self.map[klic] = "VP %02d/20%02d" % (len(self.map) + 1, 15 + len(self.map) % 10)
        return self.map[klic]


def make_anon():
    predpisy = Predpisy()

    def anon(s):
        if not isinstance(s, str) or not s:
            return s
        if s.strip() in UTVARY:          # cele pole je kod utvaru (vlastnik, vykonava)
            return UTVARY[s.strip()]
        s = RE_PREDPIS.sub(predpisy, s)
        for pat, rep in TOKENY:
            s = re.sub(pat, rep, s)
        s = RE_SEKCE.sub(lambda m: m.group(1) + m.group(2) + UTVARY.get(m.group(3), m.group(3)), s)
        return RE_UTVAR.sub(lambda m: UTVARY[m.group(1)], s)

    return anon, predpisy


def write_csv(path, rows, cols):
    with io.open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="runs/normalize/model.json")
    ap.add_argument("--out", default="runs/anonym")
    args = ap.parse_args()

    model = json.loads(Path(args.model).read_text(encoding="utf-8"))
    anon, predpisy = make_anon()

    # kody a technicka pole zustavaji, textova se anonymizuji
    KEEP = {"kod", "agenda_kod", "proces_kod", "dilci_proces_kod", "aktivita_kod",
            "primarni", "pocet_aktivit", "zdroj", "zdroj_radek",
            "stav_rejstrik"}
    out_model = {"meta": {k: anon(v) for k, v in model["meta"].items()}}
    for tab in ("agendy", "procesy", "dilci_procesy", "aktivity", "vazby"):
        out_model[tab] = [{k: (v if k in KEEP else anon(v)) for k, v in row.items()}
                          for row in model[tab]]

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "agendy.csv", out_model["agendy"],
              ["kod", "nazev", "vlastnik", "pocet_aktivit", "zdroj"])
    write_csv(out / "procesy.csv", out_model["procesy"],
              ["kod", "nazev", "agenda_kod", "vlastnik", "pocet_aktivit", "zdroj"])
    write_csv(out / "dilci_procesy.csv", out_model["dilci_procesy"],
              ["kod", "nazev", "proces_kod", "vlastnik", "stav_rejstrik", "pocet_aktivit",
               "zdroj"])
    write_csv(out / "aktivity.csv", out_model["aktivity"],
              ["kod", "nazev", "dilci_proces_kod", "vykonava", "spolupracuje",
               "vnitrni_predpis", "sekce", "zdroj_radek"])
    write_csv(out / "aktivita_dilciproces.csv", out_model["vazby"],
              ["aktivita_kod", "dilci_proces_kod", "primarni"])
    # Ciselnik utvaru se anonymizuje taky - nese skutecnou organizacni
    # strukturu MPSV. Do 06.09.2026 ho pro anonymni sadu vyrabel
    # make_utvary.py z cisel v datech; ten uz ciselnik nestavi.
    write_csv(out / "utvary.csv",
              [{"kod": UTVARY[r["kod"]],
                "nazev": anonymni_nazev(r, UTVARY),
                "uroven": r["uroven"],
                "nadrizeny_kod": UTVARY.get(r["nadrizeny_kod"], "")}
               for r in CISELNIK],
              ["kod", "nazev", "uroven", "nadrizeny_kod"])
    (out / "model.json").write_text(json.dumps(out_model, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
    (out / "mapovani.json").write_text(json.dumps(
        {"utvary": UTVARY, "predpisy": predpisy.map,
         "tokeny": {p: r for p, r in TOKENY}}, ensure_ascii=False, indent=1), encoding="utf-8")

    # kontrola: v anonymizovanem modelu nesmi zbyt zadny zakazany token
    blob = json.dumps(out_model, ensure_ascii=False)
    zbytky = [p for p, _ in TOKENY if re.search(p, blob)]
    if zbytky:
        raise SystemExit("v anonymizovanych datech zustaly tokeny: %s" % zbytky)
    for tab in ("agendy", "procesy", "dilci_procesy", "aktivity", "vazby"):
        assert len(out_model[tab]) == len(model[tab]), tab

    print("anonymizováno -> %s" % out)
    print("útvary=%d přejmenovaných předpisů=%d, počty tabulek beze změny"
          % (len(UTVARY), len(predpisy.map)))


if __name__ == "__main__":
    main()
