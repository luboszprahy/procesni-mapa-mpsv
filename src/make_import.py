"""Generator importniho skriptu pro SharePoint.

Ze src/schema.json a runs/<sada>/*.csv vyrobi src/import_data.js - skript do
konzole prohlizece, ktery zalozi polozky ve vsech peti listech.

Hodnoty se dopocitavaji TADY, ne v prohlizeci: odvozeny nazev_kratky pouziva
tutez funkci zkratit() jako validator schematu, takze se obe strany nemuzou
rozejit. JS uz jen posila hotove zaznamy.

Pojistka: vychozi sada je runs/anonym. Beh nad neanonymizovanymi daty vyzaduje
explicitni prepinac - do ciziho vyvojoveho tenantu smi jen anonymizovana data.
"""
import argparse
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from anonymize import RE_PREDPIS, RE_SEKCE, RE_UTVAR, TOKENY, UTVARY  # noqa: E402
from check_schema import check, read_csv, zkratit  # noqa: E402

# Identifikacni kody (07-11, 07-12-003) nejsou identifikujici udaj - jsou to
# strukturalni klice a vypada v nich cokoli. Kdyby se skenovaly, hlasil by
# vzor utvaru falesne poplachy na kazdem druhem kodu.
KODOVE_SLOUPCE = {"Title", "kod", "zdroj_radek"}


def _datova_pole(data, schema):
    """Hodnoty, ktere nesou obsah - bez identifikacnich kodu a datumu.

    Datumy se preskakuji podle TYPU ve schematu, ne podle jmena: razitko
    '2026-08-19T11:28:00Z' obsahuje '11' a vzor utvaru se do nej trefi.
    Typova podminka zaruci, ze stejnou past nezalozi ani pristi datumovy sloupec.
    """
    typy = {c["name"]: c["type"] for l in schema["lists"] for c in l["columns"]}
    for tab in data:
        for radek in tab["rows"]:
            for klic, hodnota in radek.items():
                if klic in KODOVE_SLOUPCE or klic.endswith("_kod"):
                    continue
                if typy.get(klic) == "DateTime":
                    continue
                if isinstance(hodnota, str) and hodnota:
                    yield klic, hodnota


def neanonymizovane_tokeny(data, schema):
    """Vrat identifikujici udaje, ktere v datech zbyly.

    Kontrola musi byt OBSAHOVA. Prvni verze se ridila nazvem slozky
    ('anonym'), coz je pojistka jen naoko - staci realna data do takove slozky
    zkopirovat a projdou.

    Kontroluji se vsechny tri kategorie, ktere anonymize.py anonymizuje:
    nazvy (TOKENY), cisla utvaru a cisla vnitrnich predpisu. Kdyby se hlidaly
    jen nazvy, prosla by data s realnym cislem utvaru - a prave utvary jsou to,
    co o organizacni strukture prozradi nejvic. Vzory se importuji
    z anonymize.py, aby se obe strany nemohly rozejit.
    """
    nalezy = []
    blob = json.dumps(data, ensure_ascii=False)
    nalezy += [p for p, _ in TOKENY if re.search(p, blob)]

    utvary, predpisy = set(), set()
    for klic, hodnota in _datova_pole(data, schema):
        utvary |= set(RE_UTVAR.findall(hodnota))
        utvary |= {m[2] for m in RE_SEKCE.findall(hodnota)}
        predpisy |= {"%s %s/%s" % m for m in RE_PREDPIS.findall(hodnota)}
        # sloupec sekce nese cislo sekce samo o sobe, bez slova "sekce"
        if klic == "sekce" and hodnota in UTVARY:
            utvary.add(hodnota)

    if utvary:
        nalezy.append("čísla útvarů: " + ", ".join(sorted(utvary)))
    if predpisy:
        nalezy.append("vnitřní předpisy: " + ", ".join(sorted(predpisy)[:5]))
    return nalezy

SABLONA = r"""/* import_data.js -- GENEROVANO src/make_import.py. Needituj rucne.

   POUZITI
   1. Nejdriv musi probehnout src/setup_sharepoint.js (listy a sloupce).
   2. Otevri cilovy SharePoint web, F12 -> Console -> vloz tento soubor.
   3. Skript je idempotentni: polozky, ktere uz v listu jsou (podle klice
      ve sloupci Title), preskoci. Muzes ho spustit opakovane.
   4. Jedna polozka = jeden POST. Chyba jedne polozky beh nezastavi -
      nasbira se a vypise na konci, aby bylo videt, co presne selhalo.

   SADA DAT: __SADA__
   POCTY:    __POCTY__
*/
(async () => {
"use strict";

const DATA = __DATA__;

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
"""


def hodnoty_radku(lst, radek, ted):
    """Slozi jeden zaznam pro SharePoint podle schematu."""
    out = {}
    for c in lst["columns"]:
        jm = c["name"]
        if c.get("csv"):
            out[jm] = radek[c["csv"]]
        elif c.get("derive"):
            out[jm] = c["derive"].format(**radek)
        elif c.get("derive_truncate"):
            d = c["derive_truncate"]
            zdroj = next(x for x in lst["columns"] if x["name"] == d["from"])
            out[jm] = zkratit(radek[zdroj["csv"]], d["maxlen"])
        elif c.get("default"):
            out[jm] = c["default"]
        elif c["type"] == "DateTime":
            out[jm] = ted
        else:
            out[jm] = ""
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default="src/schema.json")
    ap.add_argument("--data", default="runs/anonym")
    ap.add_argument("--out", default="src/import_data.js")
    ap.add_argument("--povolit-realna-data", action="store_true",
                    help="dovol jinou sadu nez runs/anonym (do cizího tenantu NIKDY)")
    a = ap.parse_args()

    datadir = Path(a.data)
    schema = json.loads(io.open(a.schema, encoding="utf-8").read())

    # referencni integritu hlida validator schematu - bez nej by se poskozena
    # data (kod mimo ciselnik) tise zapekla do importniho skriptu
    chyby, varovani = [], []
    check(schema, datadir, chyby, varovani)
    if chyby:
        for e in chyby:
            print("CHYBA: %s" % e)
        sys.exit("\nODMITNUTO: %s nesedi na schema (%d chyb). Sprav data nebo schema\n"
                 "a spust znovu; kontrolu delá src/check_schema.py." % (datadir, len(chyby)))
    # jen datum, ne cas: pole znamena "kdy byl zaznam naposledy aktualizovan"
    # a den je dost jemny. S presnosti na sekundy menila kazda regenerace
    # razitko u vsech 46 aktivit a delala zbytecny diff.
    ted = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")

    data, popis = [], []
    for lst in schema["lists"]:
        rows = read_csv(datadir / lst["csv"])
        data.append({"list": lst["name"],
                     "rows": [hodnoty_radku(lst, r, ted) for r in rows]})
        popis.append("%s=%d" % (lst["name"], len(rows)))

    zbytky = neanonymizovane_tokeny(data, schema)
    if zbytky and not a.povolit_realna_data:
        sys.exit("ODMITNUTO: v %s jsou identifikujici udaje (%s).\n"
                 "Do vyvojoveho tenantu smi jen anonymizovana data (NFR-4).\n"
                 "Spust src/anonymize.py, nebo - pokud opravdu importujes na cilovy\n"
                 "tenant MPSV - spust znovu s --povolit-realna-data."
                 % (datadir, ", ".join(zbytky)))
    if not zbytky and a.povolit_realna_data:
        print("poznamka: --povolit-realna-data nebylo potreba, data jsou anonymizovana")

    js = SABLONA
    for kotva, hodnota in (("__DATA__", json.dumps(data, ensure_ascii=False, indent=1)),
                           ("__SADA__", str(datadir).replace("\\", "/")),
                           ("__POCTY__", ", ".join(popis))):
        if js.count(kotva) != 1:
            sys.exit("kotva %s musi byt v sablone prave jednou, je %dx"
                     % (kotva, js.count(kotva)))
        js = js.replace(kotva, hodnota)

    out = Path(a.out)
    io.open(out, "w", encoding="utf-8", newline="\n").write(js)
    print("%s (%.1f kB) - %s" % (out, out.stat().st_size / 1000.0, ", ".join(popis)))


if __name__ == "__main__":
    main()
