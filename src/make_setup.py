"""Generator provisioning skriptu pro SharePoint.

Ze src/schema.json vyrobi src/setup_sharepoint.js - skript, ktery se vlozi do
konzole prohlizece (F12) na strance ciloveho SharePoint webu a zalozi tam
listy, sloupce, indexy, verzovani a vychozi zobrazeni.

Proc konzole a ne PnP: bezi pod prihlasenou session, nepotrebuje registraci
aplikace ani souhlas spravce tenantu. Web se neurcuje z konfigurace, ale
z adresy stranky, na ktere skript bezi - proto v nem neni zadna URL natvrdo.
"""
import io
import json
import sys
from pathlib import Path

SABLONA = r"""/* setup_sharepoint.js -- GENEROVANO src/make_setup.py ze src/schema.json.
   Needituj rucne: uprav schema a spust `python src/make_setup.py`.

   POUZITI
   1. Otevri v prohlizeci cilovy SharePoint web (libovolnou jeho stranku).
   2. F12 -> Console -> vloz cely tento soubor -> Enter.
   3. Skript je idempotentni: co uz existuje, preskoci; co chybi, dolozi.
      Muzes ho spustit opakovane.
   4. Na konci vypise tabulku za KAZDY sloupec schematu. REST vysledek v UI
      nevidis, takze ta tabulka je jediny doklad, co se opravdu stalo.
*/
(async () => {
"use strict";

const SCHEMA = __SCHEMA__;

// ---------- REST zaklady ----------

const VERBOSE = "application/json;odata=verbose";
let WEB = null, DIGEST = null;

async function urciWeb() {
  // Prednostne kontext stranky; jinak zkracuj cestu, dokud /_api/web neodpovi.
  if (typeof _spPageContextInfo === "object" && _spPageContextInfo &&
      _spPageContextInfo.webAbsoluteUrl) {
    return _spPageContextInfo.webAbsoluteUrl.replace(/\/$/, "");
  }
  const u = new URL(location.href);
  let casti = u.pathname.split("/").filter(Boolean);
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
    method: "POST",
    headers: { Accept: VERBOSE },
    credentials: "same-origin",
  });
  if (!r.ok) throw new Error("contextinfo selhalo: HTTP " + r.status);
  const j = await r.json();
  return j.d.GetContextWebInformation.FormDigestValue;
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

async function post(cesta, telo, merge) {
  // POZOR: createfieldasxml a MERGE vyzaduji odata=verbose. S nometadata
  // server casti pozadavku TISE ignoruje a nevrati chybu.
  const h = {
    Accept: VERBOSE,
    "X-RequestDigest": DIGEST,
  };
  if (telo !== null) h["Content-Type"] = VERBOSE;
  if (merge) { h["X-HTTP-Method"] = "MERGE"; h["IF-MATCH"] = "*"; }
  const r = await fetch(WEB + "/_api/" + cesta, {
    method: "POST",
    headers: h,
    credentials: "same-origin",
    body: telo === null ? undefined : JSON.stringify(telo),
  });
  if (!r.ok) throw new Error("POST " + cesta + " -> HTTP " + r.status + " " +
                             (await r.text()).slice(0, 400));
  const t = await r.text();
  return t ? JSON.parse(t) : null;
}

// ---------- schema XML sloupcu ----------

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
                            .replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function fieldXml(c) {
  // DisplayName se zamerne rovna INTERNIMU nazvu: SharePoint z nej odvozuje
  // internal name (mezera by se stala _x0020_, diakritika _x00e1_ apod.).
  // Zobrazovany nazev se nastavi az potom pres MERGE - viz nastavZobrazeni().
  const spol = 'DisplayName="' + esc(c.name) + '" Name="' + esc(c.name) +
               '" StaticName="' + esc(c.name) + '"' +
               (c.required ? ' Required="TRUE"' : "") +
               (c.indexed ? ' Indexed="TRUE"' : "");
  if (c.type === "Text") {
    return '<Field Type="Text" ' + spol + ' MaxLength="' + (c.maxlen || 255) + '" />';
  }
  if (c.type === "Note") {
    return '<Field Type="Note" ' + spol +
           ' NumLines="6" RichText="FALSE" RichTextMode="Compatible" AppendOnly="FALSE" />';
  }
  if (c.type === "Choice") {
    const v = c.choices.map((x) => "<CHOICE>" + esc(x) + "</CHOICE>").join("");
    return '<Field Type="Choice" ' + spol + ' Format="Dropdown"><CHOICES>' + v +
           "</CHOICES>" + (c.default ? "<Default>" + esc(c.default) + "</Default>" : "") +
           "</Field>";
  }
  if (c.type === "DateTime") {
    return '<Field Type="DateTime" ' + spol + ' Format="DateTime" Calendar="1" />';
  }
  throw new Error("neznamy typ sloupce: " + c.type);
}

// ---------- listy ----------

async function najdiList(nazev) {
  const j = await get("web/lists?$select=Id,Title,RootFolder/ServerRelativeUrl" +
                      "&$expand=RootFolder&$top=500");
  const konec = "/lists/" + nazev.toLowerCase();
  return (j.value || []).find(
    (l) => l.RootFolder && l.RootFolder.ServerRelativeUrl.toLowerCase().endsWith(konec)) || null;
}

async function zalozList(lst) {
  // Title pri zalozeni = interni nazev -> cista URL /Lists/<Name>.
  // Zobrazovany nazev se nastavi az potom, URL uz se tim nemeni.
  await post("web/lists", {
    __metadata: { type: "SP.List" },
    BaseTemplate: 100,
    Title: lst.name,
    Description: lst.popis || "",
  });
  return najdiList(lst.name);
}

async function nastavList(id, lst) {
  await post("web/lists(guid'" + id + "')", {
    __metadata: { type: "SP.List" },
    Title: lst.display || lst.name,
    EnableVersioning: true,
    MajorVersionLimit: 500,
  }, true);
}

async function nastavZobrazeni(id, c, typOdata) {
  const zobraz = c.display || c.name;
  if (zobraz === c.name && !c.indexed) return;
  await post("web/lists(guid'" + id + "')/fields/getbyinternalnameortitle('" +
             c.name + "')", {
    __metadata: { type: typOdata },
    Title: zobraz,
    Indexed: !!c.indexed,
  }, true);
}

async function dorovnejZobrazeni(id, sloupce, stav) {
  // Bit 4 v Options plati jen pro prave zakladany sloupec - co vzniklo driv,
  // se jim neopravi. Proto dorovnani pres AddViewField.
  const vf = await get("web/lists(guid'" + id + "')/DefaultView/ViewFields");
  const jsou = new Set(vf.Items || vf.SchemaXml || []);
  for (const c of sloupce) {
    // Title je ve ViewFields veden jako LinkTitle (pripadne LinkTitleNoMenu).
    const uz = c.name === "Title"
      ? (jsou.has("LinkTitle") || jsou.has("LinkTitleNoMenu") || jsou.has("Title"))
      : jsou.has(c.name);
    stav[c.name].ve_zobrazeni = uz ? "ano" : "doplneno";
    if (!uz) {
      await post("web/lists(guid'" + id + "')/DefaultView/ViewFields/AddViewField('" +
                 c.name + "')", null);
    }
  }
}

async function nastavRazeni(id, lst) {
  if (!lst.default_sort) return;
  const s = lst.default_sort;
  const fr = (n, asc) => '<FieldRef Name="' + n + '" Ascending="' +
                         (asc ? "TRUE" : "FALSE") + '" />';
  const q = "<OrderBy>" + fr(s.column, s.vzestupne !== false) +
            (s.pak ? fr(s.pak, true) : "") + "</OrderBy>";
  await post("web/lists(guid'" + id + "')/DefaultView", {
    __metadata: { type: "SP.View" },
    ViewQuery: q,
  }, true);
}

// ---------- hlavni beh ----------

const zprava = [];
const radky = [];

for (const lst of SCHEMA.lists) {
  let list = await najdiList(lst.name);
  const zalozen = !list;
  if (!list) list = await zalozList(lst);
  if (!list) throw new Error("list " + lst.name + " se nepodarilo zalozit ani najit");
  await nastavList(list.Id, lst);
  zprava.push(lst.name + ": " + (zalozen ? "zalozen" : "existoval") + " (" + list.Id + ")");

  const pole = await get("web/lists(guid'" + list.Id + "')/fields" +
                         "?$select=InternalName,TypeAsString,Hidden,Indexed,Title");
  const mam = new Map((pole.value || []).map((f) => [f.InternalName, f]));

  const stav = {};
  for (const c of lst.columns) {
    stav[c.name] = { typ: c.type, ve_zobrazeni: "?", skryty: "?", stav: "?" };
    if (c.name === "Title") {
      stav[c.name].stav = "vestaveny";
    } else if (mam.has(c.name)) {
      stav[c.name].stav = "existoval";
    } else {
      await post("web/lists(guid'" + list.Id + "')/fields/createfieldasxml", {
        parameters: {
          __metadata: { type: "SP.XmlSchemaFieldCreationInformation" },
          SchemaXml: fieldXml(c),
          // 1 = do content type, 4 = do vychoziho zobrazeni, 8 = internal name hint
          Options: 13,
        },
      });
      stav[c.name].stav = "zalozen";
    }
  }

  // zobrazovane nazvy a indexy (az po zalozeni, aby internal name zustal ASCII)
  const poPolich = await get("web/lists(guid'" + list.Id + "')/fields" +
                             "?$select=InternalName,TypeAsString,Hidden,Indexed,Title");
  const ted = new Map((poPolich.value || []).map((f) => [f.InternalName, f]));
  for (const c of lst.columns) {
    const f = ted.get(c.name);
    if (!f) { stav[c.name].stav = "CHYBI"; continue; }
    stav[c.name].skryty = f.Hidden ? "ano" : "ne";
    const typOdata = "SP.Field" + (f.TypeAsString === "Text" ? "Text"
                    : f.TypeAsString === "Note" ? "MultiLineText"
                    : f.TypeAsString === "Choice" ? "Choice"
                    : f.TypeAsString === "DateTime" ? "DateTime" : "");
    try {
      await nastavZobrazeni(list.Id, c, typOdata);
    } catch (e) {
      zprava.push("  ! " + lst.name + "." + c.name + " zobrazovany nazev/index: " + e.message);
    }
  }

  await dorovnejZobrazeni(list.Id, lst.columns, stav);
  await nastavRazeni(list.Id, lst);

  // sloupce navic, ktere do schematu nepatri
  const ocekavane = new Set(lst.columns.map((c) => c.name));
  const navic = (poPolich.value || []).filter(
    (f) => !f.Hidden && !ocekavane.has(f.InternalName) &&
           !["ContentType", "Attachments", "Edit", "LinkTitleNoMenu", "LinkTitle",
             "DocIcon", "ItemChildCount", "FolderChildCount", "AppAuthor", "AppEditor",
             "_ComplianceFlags", "_ComplianceTag", "_ComplianceTagWrittenTime",
             "_ComplianceTagUserId", "_IsRecord", "TaxCatchAll", "TaxCatchAllLabel",
             "ID", "Modified", "Created", "Author", "Editor", "_UIVersionString",
             "_CopySource", "_ModerationComments", "ContentTypeId", "FileLeafRef",
             "FileDirRef", "FSObjType", "SortBehavior", "PermMask", "UniqueId",
             "ProgId", "ScopeId", "MetaInfo", "_Level", "_IsCurrentVersion", "owshiddenversion",
             "InstanceID", "Order", "GUID", "WorkflowVersion", "WorkflowInstanceID",
             "ParentVersionString", "ParentLeafName", "ServerRedirectedEmbedUrl"].includes(
               f.InternalName));

  for (const c of lst.columns) {
    radky.push({
      list: lst.name, sloupec: c.name, stav: stav[c.name].stav,
      typ: stav[c.name].typ, ve_zobrazeni: stav[c.name].ve_zobrazeni,
      skryty: stav[c.name].skryty,
      zobrazovany_nazev: c.display || c.name,
    });
  }
  for (const f of navic) {
    radky.push({
      list: lst.name, sloupec: f.InternalName, stav: "NAVIC (neni ve schematu)",
      typ: f.TypeAsString, ve_zobrazeni: "-", skryty: f.Hidden ? "ano" : "ne",
      zobrazovany_nazev: f.Title,
    });
  }
}

// ---------- zaverecny vypis ----------

console.log("web: " + WEB);
zprava.forEach((z) => console.log(z));
console.table(radky);

const chybne = radky.filter((r) => r.stav === "CHYBI" || r.ve_zobrazeni === "?");
const navicPocet = radky.filter((r) => r.stav.startsWith("NAVIC")).length;
console.log(chybne.length === 0
  ? "HOTOVO: vsech " + radky.length + " radku v poradku" +
    (navicPocet ? " (z toho " + navicPocet + " sloupcu navic mimo schema)" : "")
  : "POZOR: " + chybne.length + " sloupcu neni v poradku - viz tabulka vyse");

// inicializace kontextu musi probehnout drive nez cokoli vyse; zajisti ji wrapper
})().catch((e) => console.error("setup_sharepoint selhal:", e));
"""

def main():
    schema = json.loads(io.open("src/schema.json", encoding="utf-8").read())
    js = SABLONA

    kotva = "__SCHEMA__"
    if js.count(kotva) != 1:
        sys.exit("kotva %s musi byt v sablone prave jednou, je %dx" % (kotva, js.count(kotva)))
    js = js.replace(kotva, json.dumps(schema, ensure_ascii=False, indent=1))

    # WEB a DIGEST se plni az za definicemi funkci, tesne pred hlavnim behem
    beh = "// ---------- hlavni beh ----------\n"
    if js.count(beh) != 1:
        sys.exit("nenalezena jedinecna znacka hlavniho behu")
    js = js.replace(beh, beh + "\nWEB = await urciWeb();\nDIGEST = await digest();\n")

    out = Path("src/setup_sharepoint.js")
    io.open(out, "w", encoding="utf-8", newline="\n").write(js)

    sloupcu = sum(len(l["columns"]) for l in schema["lists"])
    print("%s (%.1f kB) - %d listu, %d sloupcu"
          % (out, out.stat().st_size / 1000.0, len(schema["lists"]), sloupcu))


if __name__ == "__main__":
    main()
