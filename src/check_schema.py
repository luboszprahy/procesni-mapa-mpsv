"""Kontrola schematu SharePoint listu proti normalizovanym datum.

Overuje, ze se schema (src/schema.json) a data (runs/<sada>/*.csv) neshoduji
jen nahodou: pokryti sloupcu obema smery, delky, hodnoty Choice, unikatnost
klice a referencni integritu textovych odkazu.

Vedlejsi vystup: deploy/sharepoint_schema.md - dokumentace se generuje ze
schematu, aby nemohla zestarnout proti kodu.
"""
import argparse
import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path

TYP_POPIS = {
    "Text": "Jeden řádek textu",
    "Note": "Více řádků textu (prostý text)",
    "Choice": "Volba",
    "DateTime": "Datum a čas",
}


def zkratit(text, maxlen):
    """Usekni na hranici slova a doplnu vypustku; kratsi text vrat beze zmeny.

    Slouzi k odvozeni radiciho sloupce z Note sloupce, ktery SharePoint neumi
    indexovat ani radit.
    """
    t = " ".join((text or "").split())
    if len(t) <= maxlen:
        return t
    rez = t[:maxlen - 1]
    mezera = rez.rfind(" ")
    if mezera > maxlen // 2:
        rez = rez[:mezera]
    return rez.rstrip(" ,;.") + "…"


def read_csv(path):
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def zkontroluj_razeni(lst, errors, warnings):
    """Overi default_sort proti sloupcum listu - nezavisle na datech."""
    name = lst["name"]
    srt = lst.get("default_sort")
    if not srt:
        return
    if not any(c["name"] == srt["column"] for c in lst["columns"]):
        errors.append("%s: default_sort odkazuje na neexistujici sloupec %r"
                      % (name, srt["column"]))
    else:
        sc = next(c for c in lst["columns"] if c["name"] == srt["column"])
        if sc["type"] == "Note":
            errors.append("%s: default_sort je nad sloupcem %r typu Note - "
                          "SharePoint podle Note neradi" % (name, sc["name"]))
        elif not sc.get("indexed"):
            warnings.append("%s: sloupec %r se pouziva k razeni, ale neni indexovany"
                            % (name, sc["name"]))
    if srt.get("pak") and not any(c["name"] == srt["pak"] for c in lst["columns"]):
        errors.append("%s: druhotne razeni odkazuje na neexistujici sloupec %r"
                      % (name, srt["pak"]))


def check(schema, datadir, errors, warnings):
    keys = {}          # list -> set kodu (pro kontrolu referenci)
    rows_by_list = {}

    for lst in schema["lists"]:
        name = lst["name"]
        zkontroluj_razeni(lst, errors, warnings)

        if not lst.get("csv"):
            # list se zaklada prazdny a plni ho az aplikace (HistorieKodu) -
            # data neexistuji, ma smysl overit jen tvar
            rows_by_list[name] = []
            if not any(c["name"] == "Title" for c in lst["columns"]):
                errors.append("%s: schema nema sloupec Title (prirozeny klic)" % name)
            for col in lst["columns"]:
                if col.get("csv") or col.get("derive") or col.get("derive_truncate"):
                    errors.append("%s.%s: list nema zdrojova data, sloupec z nich tedy "
                                  "nemuze cerpat" % (name, col["name"]))
            continue

        path = datadir / lst["csv"]
        if not path.exists():
            errors.append("%s: chybi zdrojovy soubor %s" % (name, path))
            continue
        rows = read_csv(path)
        rows_by_list[name] = rows
        if not rows:
            errors.append("%s: %s je prazdny" % (name, path))
            continue

        csv_cols = set(rows[0].keys())
        mapped = {c["csv"] for c in lst["columns"] if c.get("csv")}
        ignored = set(lst.get("ignoruj_csv", {}))

        # pokryti obema smery
        for extra in sorted(csv_cols - mapped - ignored):
            errors.append("%s: sloupec %r je v CSV, ale schema pro nej nema cil "
                          "ani duvod v 'ignoruj_csv'" % (name, extra))
        for missing in sorted(mapped - csv_cols):
            errors.append("%s: schema cte CSV sloupec %r, ktery v datech neni"
                          % (name, missing))
        for dead in sorted(ignored - csv_cols):
            warnings.append("%s: 'ignoruj_csv' uvadi %r, ktery uz v datech neni"
                            % (name, dead))

        # klic
        kc = next((c for c in lst["columns"] if c["name"] == "Title"), None)
        if kc is None:
            errors.append("%s: schema nema sloupec Title (prirozeny klic)" % name)
        elif kc.get("csv"):
            vals = [r[kc["csv"]] for r in rows]
            dup = [v for v, n in Counter(vals).items() if n > 1]
            if dup:
                errors.append("%s: klic neni unikatni - %d duplicit, napr. %s"
                              % (name, len(dup), dup[:3]))
            if any(not v for v in vals):
                errors.append("%s: klic je u nekterych radku prazdny" % name)
            keys[name] = set(vals)
        elif kc.get("derive"):
            vals = [kc["derive"].format(**r) for r in rows]
            dup = [v for v, n in Counter(vals).items() if n > 1]
            if dup:
                errors.append("%s: odvozeny klic %r neni unikatni - napr. %s"
                              % (name, kc["derive"], dup[:3]))
            keys[name] = set(vals)

        # odvozene zkraceni (radici sloupec nad Note)
        for col in lst["columns"]:
            d = col.get("derive_truncate")
            if not d:
                continue
            zdroj = d["from"]
            zc = next((c for c in lst["columns"] if c["name"] == zdroj), None)
            if zc is None or not zc.get("csv"):
                errors.append("%s.%s: odvozuje se z %r, ktery ve schematu neni "
                              "nebo nema zdroj v CSV" % (name, col["name"], zdroj))
                continue
            vals = [zkratit(r[zc["csv"]], d["maxlen"]) for r in rows]
            lim = col.get("maxlen", 255)
            over = [v for v in vals if len(v) > lim]
            if over:
                errors.append("%s.%s: odvozena hodnota presahuje %d znaku (nejdelsi %d)"
                              % (name, col["name"], lim, max(len(v) for v in over)))
            kolize = [v for v, n in Counter(v for v in vals if v).items() if n > 1]
            druhotne = (lst.get("default_sort") or {}).get("pak")
            if kolize and not druhotne:
                warnings.append("%s.%s: %d ruznych zaznamu ma po zkraceni shodnou "
                                "hodnotu a razeni nema druhotny klic - jejich vzajemne "
                                "poradi ve view neni urcene, napr. %r"
                                % (name, col["name"], len(kolize), kolize[0][:60]))

        # hodnoty sloupcu
        for col in lst["columns"]:
            src = col.get("csv")
            if not src:
                continue
            vals = [r[src] for r in rows]
            if col.get("required") and any(not v for v in vals):
                n = sum(1 for v in vals if not v)
                errors.append("%s.%s: povinny sloupec je prazdny u %d radku"
                              % (name, col["name"], n))
            if col["type"] == "Text":
                lim = col.get("maxlen", 255)
                over = [v for v in vals if len(v) > lim]
                if over:
                    errors.append("%s.%s: %d hodnot prekracuje %d znaku (nejdelsi %d) "
                                  "- typ Text nestaci, zvaz Note"
                                  % (name, col["name"], len(over), lim,
                                     max(len(v) for v in over)))
                elif vals:
                    m = max(len(v) for v in vals)
                    if m > lim * 0.8:
                        warnings.append("%s.%s: nejdelsi hodnota %d znaku je nad 80 %% "
                                        "limitu %d" % (name, col["name"], m, lim))
            if col["type"] == "Choice":
                bad = sorted({v for v in vals if v and v not in col["choices"]})
                if bad:
                    errors.append("%s.%s: hodnoty mimo ciselnik %s -> %s"
                                  % (name, col["name"], col["choices"], bad))

    # referencni integrita textovych odkazu
    for lst in schema["lists"]:
        rows = rows_by_list.get(lst["name"])
        if not rows:
            continue
        for col in lst["columns"]:
            ref, src = col.get("ref"), col.get("csv")
            if not ref or not src:
                continue
            if ref not in keys:
                errors.append("%s.%s: odkazuje na %s, ktery se nepodarilo nacist"
                              % (lst["name"], col["name"], ref))
                continue
            missing = sorted({r[src] for r in rows if r[src] and r[src] not in keys[ref]})
            if missing:
                errors.append("%s.%s: %d odkazu nema protejsek v %s, napr. %s"
                              % (lst["name"], col["name"], len(missing), ref, missing[:3]))

    return rows_by_list


def write_doc(schema, rows_by_list, path):
    L = ["# Schéma SharePoint listů — rejstřík agend a procesů MPSV", "",
         "Generováno z `src/schema.json` skriptem `src/check_schema.py`. **Needituj ručně** —",
         "uprav schéma a skript spusť znovu.", "",
         "Publisher solution `%s`, prefix `%s`." % (schema["publisher"], schema["prefix"]), "",
         "## Zásady", "",
         "- Interní názvy sloupců **bez diakritiky** — přejmenování zobrazovaného názvu",
         "  interní název nemění a REST `$select` pracuje s interními.",
         "- Vztahy nesou **textový kód**, ne SharePoint lookup ID. Důvod: přenositelnost",
         "  mezi tenanty a migrovatelnost do Dataverse bez ztráty vazeb. Cenou je, že",
         "  referenční integritu nehlídá platforma — hlídá ji `src/check_schema.py`",
         "  a pořizovací aplikace.",
         "- `Title` v SharePointu nelze vypnout, proto nese identifikační kód.",
         "- Odvozené údaje (počet aktivit ve větvi) se **neukládají** — počítají se",
         "  až v mapě ze zapečených dat, jinak by v listech zastarávaly.", "",
         "## Listy", ""]

    for lst in schema["lists"]:
        rows = rows_by_list.get(lst["name"]) or []
        L += ["### `%s`" % lst["name"], "",
              lst["popis"], "",
              "Zdroj dat: `%s` (%d řádků). Verzování: zapnuto.%s" % (
                  lst["csv"], len(rows),
                  " Výchozí řazení: `%s`%s." % (
                      lst["default_sort"]["column"],
                      ", pak `%s`" % lst["default_sort"]["pak"]
                      if lst["default_sort"].get("pak") else "")
                  if lst.get("default_sort") else ""), "",
              "| Interní název | Zobrazovaný název | Typ | Povinný | Indexovaný | Zdroj v CSV |",
              "|---|---|---|---|---|---|"]
        for c in lst["columns"]:
            if c.get("csv"):
                src = c["csv"]
            elif c.get("derive"):
                src = "odvozeno: `%s`" % c["derive"]
            elif c.get("derive_truncate"):
                src = "odvozeno z `%s`, zkráceno na %d znaků" % (
                    c["derive_truncate"]["from"], c["derive_truncate"]["maxlen"])
            else:
                src = "— (zakládá se prázdné)"
            L.append("| `%s` | %s | %s | %s | %s | %s |" % (
                c["name"], c["display"], TYP_POPIS[c["type"]],
                "ano" if c.get("required") else "ne",
                "ano" if c.get("indexed") else "ne", src))
        L.append("")
        for c in lst["columns"]:
            if c["type"] == "Choice":
                L.append("- `%s` — hodnoty: %s" % (
                    c["name"], ", ".join("`%s`" % x for x in c["choices"])))
        for c in lst["columns"]:
            if c.get("popis"):
                L.append("- `%s` — %s" % (c["name"], c["popis"]))
        if lst.get("ignoruj_csv"):
            L += ["", "Sloupce CSV, které se **záměrně neukládají**:"]
            for k, v in lst["ignoruj_csv"].items():
                L.append("- `%s` — %s" % (k, v))
        L.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    io.open(path, "w", encoding="utf-8", newline="\r\n").write("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default="src/schema.json")
    ap.add_argument("--data", default="runs/normalize")
    ap.add_argument("--doc", default="deploy/sharepoint_schema.md")
    a = ap.parse_args()

    schema = json.loads(io.open(a.schema, encoding="utf-8").read())
    errors, warnings = [], []
    rows = check(schema, Path(a.data), errors, warnings)

    for w in warnings:
        print("VAROVANI: %s" % w)
    for e in errors:
        print("CHYBA: %s" % e)

    if errors:
        print("\nschema NESEDI na data v %s - %d chyb" % (a.data, len(errors)))
        return 1

    write_doc(schema, rows, Path(a.doc))
    print("schema OK proti %s: %s" % (a.data, ", ".join(
        "%s=%d" % (l["name"], len(rows.get(l["name"]) or [])) for l in schema["lists"])))
    print("-> %s" % a.doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
