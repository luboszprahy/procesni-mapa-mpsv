"""Normalizace podkladu MPSV (rejstrik + evidencni karta) do relacniho modelu.

Vstup : input/REJSTRIK_MAPA_A-P-DP_*.xlsx  (ciselnik agend/procesu/dilcich procesu)
        input/VZOR_Evidencni karta*.xlsx    (aktivity jedne sekce)
Vystup: runs/<out>/ *.csv + model.json + report.md
"""
import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import openpyxl

# fill motivu 3 = zahlavi (agenda / proces), 8 = "jiz vyuzity" dilci proces
THEME_HEADER = 3
THEME_USED = 8
ARGB_S4 = "FFFFFFCC"


def clean(v):
    """Orez, sjednot bile znaky a unicode; 'x' a '-' znamenaji prazdno."""
    if v is None:
        return ""
    s = unicodedata.normalize("NFC", str(v))
    s = s.replace(" ", " ").replace("​", "")
    s = re.sub(r"\s+", " ", s).strip()
    return "" if s.lower() in {"x", "-", "n/a"} else s


def clean_multi(v):
    """Jako clean(), ale radky bunky zustanou oddelene strednikem."""
    if v is None:
        return ""
    parts = [clean(p) for p in str(v).replace("\r\n", "\n").split("\n")]
    return "; ".join(p for p in parts if p)


def key(s):
    """Porovnavaci klic: bez diakritiky, bez interpunkce, lowercase."""
    s = unicodedata.normalize("NFD", clean(s).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def theme(cell):
    f = cell.fill
    if f is None or f.patternType is None or f.fgColor is None:
        return None, None
    fg = f.fgColor
    return (fg.theme if fg.type == "theme" else None,
            fg.rgb if fg.type == "rgb" else None)


def owners(counter):
    """Vsichni vlastnici, nejcastejsi prvni; vice vlastniku je pripustny stav."""
    return "; ".join(v for v, _ in counter.most_common() if v)


class Registry:
    """Ciselniky s prirazovanim kodu a evidenci variant zapisu.

    Kody se prideluji jednou a dal se nemeni: uz prideleny kod se cte ze
    zmrazeneho rejstriku (kody.json), nove polozky dostavaji prvni volne cislo
    v ramci sve urovne. Bez toho by vlozeni polozky doprostred precislovalo
    vse pod ni a rozbilo vazby, ktere na kodu stoji.
    """

    def __init__(self, frozen=None):
        self.agendy = {}       # key -> dict
        self.procesy = {}      # (agenda_key, proces_key) -> dict
        self.dilci = {}        # (agenda_key, proces_key, dp_key) -> dict
        self.variants = defaultdict(Counter)   # key -> Counter(raw)
        f = frozen or {}
        self.frozen = {"agendy": dict(f.get("agendy", {})),
                       "procesy": dict(f.get("procesy", {})),
                       "dilci": dict(f.get("dilci", {})),
                       "aktivity": dict(f.get("aktivity", {}))}
        self.kody_aktivit = {}   # aktivita_key -> kod

    @staticmethod
    def _fk(kk):
        return kk if isinstance(kk, str) else "||".join(kk)

    def _kod(self, uroven, kk, sirka, pouzite, prefix=""):
        """Vrat zmrazeny kod, jinak prvni volne cislo na teto urovni."""
        drive = self.frozen[uroven].get(self._fk(kk))
        if drive:
            return drive
        obsazena = {int(k.rsplit("-", 1)[-1]) for k in pouzite if k}
        n = next(i for i in range(1, 10 ** sirka) if i not in obsazena)
        return prefix + ("%0*d" % (sirka, n))

    def export_kody(self):
        return {
            "agendy": {self._fk(k): v["kod"] for k, v in self.agendy.items()},
            "procesy": {self._fk(k): v["kod"] for k, v in self.procesy.items()},
            "dilci": {self._fk(k): v["kod"] for k, v in self.dilci.items()},
            "aktivity": dict(self.kody_aktivit),
        }

    def _var(self, k, raw):
        if raw:
            self.variants[k][raw] += 1

    def agenda(self, raw, vlastnik="", zdroj=""):
        k = key(raw)
        if not k:
            return None
        self._var(k, clean(raw))
        a = self.agendy.get(k)
        if a is None:
            a = self.agendy[k] = {
                "key": k, "nazev": clean(raw),
                "kod": self._kod("agendy", k, 2,
                                 [a["kod"] for a in self.agendy.values()]),
                "vlastnici": Counter(), "zdroj": zdroj, "procesy": [],
            }
        if vlastnik:
            a["vlastnici"][vlastnik] += 1
        return a

    def proces(self, agenda, raw, vlastnik="", zdroj=""):
        k = key(raw)
        if not agenda or not k:
            return None
        self._var(k, clean(raw))
        kk = (agenda["key"], k)
        p = self.procesy.get(kk)
        if p is None:
            p = self.procesy[kk] = {
                "key": k, "nazev": clean(raw), "agenda": agenda["key"],
                "kod": self._kod("procesy", kk, 2,
                                 [self.procesy[x]["kod"] for x in agenda["procesy"]],
                                 agenda["kod"] + "-"),
                "vlastnici": Counter(), "zdroj": zdroj, "dilci": [],
            }
            agenda["procesy"].append(kk)
        if vlastnik:
            p["vlastnici"][vlastnik] += 1
        return p

    def dilci_proces(self, proces, raw, vlastnik="", zdroj="", stav=""):
        k = key(raw)
        if not proces or not k:
            return None
        self._var(k, clean(raw))
        kk = (proces["agenda"], proces["key"], k)
        d = self.dilci.get(kk)
        if d is None:
            d = self.dilci[kk] = {
                "key": k, "nazev": clean(raw), "agenda": proces["agenda"], "proces": proces["key"],
                "kod": self._kod("dilci", kk, 3,
                                 [self.dilci[x]["kod"] for x in proces["dilci"]],
                                 proces["kod"] + "-"),
                "vlastnici": Counter(), "zdroj": zdroj, "stav": stav, "aktivity": [],
            }
            proces["dilci"].append(kk)
        if vlastnik:
            d["vlastnici"][vlastnik] += 1
        if stav and not d["stav"]:
            d["stav"] = stav
        return d


def parse_rejstrik(path, reg, issues):
    """Sloupcove cteni mapy: r2 = agendy (slouceno), r3+ = procesy (motiv 3) a pod nimi DP."""
    ws = openpyxl.load_workbook(path).worksheets[0]
    spans = {}
    for mr in ws.merged_cells.ranges:
        if mr.min_row == 2:
            for c in range(mr.min_col, mr.max_col + 1):
                spans[c] = mr.min_col

    agenda_of_col = {}
    last_agenda = None
    for c in range(1, ws.max_column + 1):
        raw = clean(ws.cell(2, c).value)
        if key(raw) == "vysvetlivky":
            break
        src = spans.get(c, c)
        if src == c and raw:
            last_agenda = reg.agenda(raw, zdroj="rejstrik")
        if last_agenda and (raw or c in spans):
            agenda_of_col[c] = last_agenda

    n_p = n_d = 0
    for c, agenda in agenda_of_col.items():
        proces = None
        for r in range(3, ws.max_row + 1):
            cell = ws.cell(r, c)
            raw = clean(cell.value)
            if not raw:
                continue
            th, argb = theme(cell)
            if th == THEME_HEADER:
                proces = reg.proces(agenda, raw, zdroj="rejstrik")
                n_p += 1
            else:
                if proces is None:
                    issues.append(("rejstřík", "sloupec %d, řádek %d: dílčí proces %r nemá nad "
                                               "sebou proces - přeskočen" % (c, r, raw[:50])))
                    continue
                stav = ("využitý" if th == THEME_USED
                        else "využitý-S4" if argb == ARGB_S4 else "nevyužitý")
                reg.dilci_proces(proces, raw, zdroj="rejstrik", stav=stav)
                n_d += 1
    return n_p, n_d


def parse_karta(path, reg, issues):
    """Radkove cteni evidencni karty: 1 radek = 1 aktivita."""
    ws = openpyxl.load_workbook(path).worksheets[0]
    sekce = clean(ws.cell(2, 4).value) or clean(ws.cell(2, 3).value)
    spravce = clean(ws.cell(3, 4).value)
    hdr = next((r for r in range(1, 12) if clean(ws.cell(r, 2).value).lower() == "název"), 5)

    aktivity, vazby, by_key, seen = [], [], {}, set()

    def cell(r, c, multi=False):
        """Ocisti bunku a zaznamenej, kdyz se puvodni zapis od ocisteneho lisi."""
        v = ws.cell(r, c).value
        s = clean_multi(v) if multi else clean(v)
        if isinstance(v, str) and s and s != v:
            issues.append(("očištěné buňky", "řádek %d, sloupec %s: %r -> %r"
                           % (r, openpyxl.utils.get_column_letter(c), v, s)))
        return s

    for r in range(hdr + 1, ws.max_row + 1):
        a_naz, a_vl = cell(r, 2), cell(r, 3)
        p_naz, p_vl = cell(r, 5), cell(r, 6)
        d_naz, d_vl = cell(r, 8), cell(r, 9)
        k_naz, k_vyk = cell(r, 11), cell(r, 12)
        spolu, predpis = cell(r, 14), cell(r, 15, multi=True)
        if not any((a_naz, p_naz, d_naz, k_naz)):
            continue
        for label, val in (("agendu", a_naz), ("proces", p_naz),
                           ("dílčí proces", d_naz), ("aktivitu", k_naz)):
            if not val:
                issues.append(("karta", "řádek %d: chybí %s" % (r, label)))

        agenda = reg.agenda(a_naz, a_vl, zdroj="karta")
        proces = reg.proces(agenda, p_naz, p_vl, zdroj="karta")
        dp = reg.dilci_proces(proces, d_naz, d_vl, zdroj="karta")
        if dp is None:
            issues.append(("karta", "řádek %d: aktivitu %r nelze zařadit" % (r, k_naz[:50])))
            continue

        kk = key(k_naz)
        akt = by_key.get(kk)
        if akt is None:
            akt = by_key[kk] = {
                "key": kk, "nazev": k_naz, "kod": "", "primarni_dp": dp["kod"],
                "vykonava": k_vyk, "spolupracuje": spolu, "vnitrni_predpis": predpis,
                "radek": r, "sekce": sekce,
            }
            aktivity.append(akt)
        else:
            issues.append(("karta", "řádek %d: aktivita %r se opakuje (poprvé na řádku %d) "
                                    "-> vazba M:N" % (r, k_naz[:50], akt["radek"])))
            if k_vyk and k_vyk not in akt["vykonava"].split(", "):
                akt["vykonava"] += ", " + k_vyk

        if (kk, dp["kod"]) not in seen:
            seen.add((kk, dp["kod"]))
            dp["aktivity"].append(kk)
            if not akt["kod"]:
                akt["kod"] = reg._kod("aktivity", kk, 4,
                                      [by_key[x]["kod"] for x in dp["aktivity"]
                                       if by_key[x]["kod"].startswith(dp["kod"] + "-")],
                                      dp["kod"] + "-")
                reg.kody_aktivit[kk] = akt["kod"]
            vazby.append({"aktivita": kk, "dilci_proces": dp["kod"],
                          "primarni": akt["primarni_dp"] == dp["kod"]})
    return {"sekce": sekce, "spravce": spravce, "aktivity": aktivity, "vazby": vazby}


def near_duplicates(aktivity, prah):
    out = []
    for i in range(len(aktivity)):
        for j in range(i + 1, len(aktivity)):
            a, b = aktivity[i], aktivity[j]
            r = SequenceMatcher(None, a["key"], b["key"]).ratio()
            if r >= prah:
                out.append((round(r, 3), a, b))
    return sorted(out, key=lambda t: -t[0])


def write_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="input")
    ap.add_argument("--out", default="runs/normalize")
    ap.add_argument("--prah", type=float, default=0.85, help="práh podobnosti pro duplicity")
    ap.add_argument("--kody", default="kody.json",
                    help="zmrazený rejstřík identifikačních kódů (přidělený kód se už nemění)")
    args = ap.parse_args()

    inp, out = Path(args.input), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rej = next(iter(sorted(inp.glob("REJSTRIK*.xlsx"))), None)
    kar = next(iter(sorted(inp.glob("*Evidenční karta*.xlsx"))), None)
    if rej is None or kar is None:
        sys.exit("nenalezeny podklady v %s (rejstřík=%s, karta=%s)" % (inp, rej, kar))

    kody_path = Path(args.kody)
    frozen = (json.loads(kody_path.read_text(encoding="utf-8"))
              if kody_path.exists() else {})
    reg, issues = Registry(frozen), []
    n_p, n_d = parse_rejstrik(rej, reg, issues)
    karta = parse_karta(kar, reg, issues)

    for grp, kind in ((reg.agendy, "agenda"), (reg.procesy, "proces"), (reg.dilci, "dílčí proces")):
        for it in grp.values():
            if len(it["vlastnici"]) > 1:
                issues.append(("více vlastníků (přípustný stav)", "%s %r (%s): %s"
                               % (kind, it["nazev"][:60], it["kod"],
                                  ", ".join(sorted(it["vlastnici"])))))
    for k, c in reg.variants.items():
        if len(c) > 1:
            issues.append(("varianty zápisu",
                           " | ".join("%r (%dx)" % (v, n) for v, n in c.most_common())))

    # pocty aktivit se scitaji zdola nahoru
    akt_proces, akt_agenda = Counter(), Counter()
    for (ag, pr, _dp), d in reg.dilci.items():
        akt_proces[(ag, pr)] += len(d["aktivity"])
        akt_agenda[ag] += len(d["aktivity"])

    agendy = [{"kod": a["kod"], "nazev": a["nazev"], "vlastnik": owners(a["vlastnici"]),
               "pocet_aktivit": akt_agenda[a["key"]],
               "zdroj": a["zdroj"]} for a in reg.agendy.values()]
    procesy = [{"kod": p["kod"], "nazev": p["nazev"], "agenda_kod": reg.agendy[p["agenda"]]["kod"],
                "vlastnik": owners(p["vlastnici"]),
                "pocet_aktivit": akt_proces[(p["agenda"], p["key"])],
                "zdroj": p["zdroj"]}
               for p in reg.procesy.values()]
    dilci = [{"kod": d["kod"], "nazev": d["nazev"],
              "proces_kod": reg.procesy[(d["agenda"], d["proces"])]["kod"],
              "vlastnik": owners(d["vlastnici"]), "stav_rejstrik": d["stav"],
              "pocet_aktivit": len(d["aktivity"]),
              "zdroj": d["zdroj"]}
             for d in reg.dilci.values()]
    aktivity = [{"kod": a["kod"], "nazev": a["nazev"], "dilci_proces_kod": a["primarni_dp"],
                 "vykonava": a["vykonava"], "spolupracuje": a["spolupracuje"],
                 "vnitrni_predpis": a["vnitrni_predpis"], "sekce": karta["sekce"],
                 "zdroj_radek": a["radek"]} for a in karta["aktivity"]]
    kod_of = {a["key"]: a["kod"] for a in karta["aktivity"]}
    vazby = [{"aktivita_kod": kod_of[v["aktivita"]], "dilci_proces_kod": v["dilci_proces"],
              "primarni": "ano" if v["primarni"] else "ne"} for v in karta["vazby"]]

    write_csv(out / "agendy.csv", agendy,
              ["kod", "nazev", "vlastnik", "pocet_aktivit", "zdroj"])
    write_csv(out / "procesy.csv", procesy,
              ["kod", "nazev", "agenda_kod", "vlastnik", "pocet_aktivit", "zdroj"])
    write_csv(out / "dilci_procesy.csv", dilci,
              ["kod", "nazev", "proces_kod", "vlastnik", "stav_rejstrik", "pocet_aktivit",
               "zdroj"])
    write_csv(out / "aktivity.csv", aktivity,
              ["kod", "nazev", "dilci_proces_kod", "vykonava", "spolupracuje",
               "vnitrni_predpis", "sekce", "zdroj_radek"])
    write_csv(out / "aktivita_dilciproces.csv", vazby,
              ["aktivita_kod", "dilci_proces_kod", "primarni"])

    model = {"meta": {"sekce": karta["sekce"], "spravce": karta["spravce"],
                      "zdroj_rejstrik": rej.name, "zdroj_karta": kar.name},
             "agendy": agendy, "procesy": procesy, "dilci_procesy": dilci,
             "aktivity": aktivity, "vazby": vazby}
    (out / "model.json").write_text(json.dumps(model, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
    kody_path.write_text(json.dumps(reg.export_kody(), ensure_ascii=False,
                                    indent=1, sort_keys=True), encoding="utf-8")

    dups = near_duplicates(karta["aktivity"], args.prah)
    by_kind = defaultdict(list)
    for kind, msg in issues:
        by_kind[kind].append(msg)

    lines = ["# Report normalizace", "",
             "Zdroje: `%s`, `%s`" % (rej.name, kar.name),
             "Sekce: %s | Sekční správce: %s" % (karta["sekce"], karta["spravce"]), "",
             "## Počty", "",
             "- agendy: %d" % len(agendy),
             "- procesy: %d" % len(procesy),
             "- dílčí procesy: %d (z toho zavedené kartou: %d)"
             % (len(dilci), sum(1 for d in dilci if d["zdroj"] == "karta")),
             "- aktivity: %d" % len(aktivity),
             "- vazby aktivita-dílčí proces: %d" % len(vazby), "",
             "## Stav zmapování", ""]
    # Počítá se ze skutečnosti, ne z uloženého sloupce: `stav_mapovani`
    # 24.08.2026 zrušen, protože byl odvozený a od importu zamrzlý.
    for tab, nazev in ((agendy, "agendy"), (procesy, "procesy"), (dilci, "dílčí procesy")):
        s_aktivitami = sum(1 for x in tab if x["pocet_aktivit"])
        lines.append("- %s: %d s aktivitami, %d bez aktivit"
                     % (nazev, s_aktivitami, len(tab) - s_aktivitami))
    lines += ["", "## Nálezy", ""]
    for kind, msgs in by_kind.items():
        lines += ["### %s (%d)" % (kind, len(msgs)), ""] + ["- " + m for m in msgs] + [""]
    lines += ["### podobné aktivity, práh %s (%d)" % (args.prah, len(dups)), ""]
    lines += ["- %s: `%s` %s ~ `%s` %s" % (r, a["kod"], a["nazev"][:70], b["kod"], b["nazev"][:70])
              for r, a, b in dups] or ["- žádné"]
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("rejstřík: %d procesů, %d dílčích procesů" % (n_p, n_d))
    print("agendy=%d procesy=%d dílčí=%d aktivity=%d vazby=%d"
          % (len(agendy), len(procesy), len(dilci), len(aktivity), len(vazby)))
    print("nálezy=%d podobné dvojice=%d -> %s" % (len(issues), len(dups), out))


if __name__ == "__main__":
    main()
