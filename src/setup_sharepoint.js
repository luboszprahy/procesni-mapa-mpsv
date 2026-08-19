/* setup_sharepoint.js -- GENEROVANO src/make_setup.py ze src/schema.json.
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

const SCHEMA = {
 "verze": "1.0",
 "poznamka": "Jediny zdroj pravdy o strukture SharePoint listu. Cte ho check_schema.py (validace dat + generovani deploy/sharepoint_schema.md), make_setup.py (provisioning) a make_import.py (import dat). Nikde jinde strukturu nedeklaruj.",
 "prefix": "mpsv_",
 "publisher": "mpsv",
 "lists": [
  {
   "name": "Agendy",
   "csv": "agendy.csv",
   "popis": "Ciselnik agend (uroven AA). Zdroj: centralni rejstrik.",
   "ignoruj_csv": {
    "pocet_aktivit": "odvozeny udaj - pocita se az v mape z vazebni tabulky, neuklada se"
   },
   "columns": [
    {
     "name": "Title",
     "display": "Kód",
     "type": "Text",
     "maxlen": 20,
     "required": true,
     "indexed": true,
     "csv": "kod",
     "popis": "Identifikacni kod AA. Prirozeny klic."
    },
    {
     "name": "nazev",
     "display": "Název",
     "type": "Text",
     "maxlen": 255,
     "required": true,
     "csv": "nazev"
    },
    {
     "name": "vlastnik",
     "display": "Vlastník agendy",
     "type": "Text",
     "maxlen": 255,
     "csv": "vlastnik",
     "popis": "Sekce. Vice vlastniku je pripustny stav - oddelovac '; '."
    },
    {
     "name": "stav_mapovani",
     "display": "Stav mapování",
     "type": "Choice",
     "indexed": true,
     "csv": "stav_mapovani",
     "choices": [
      "zmapováno",
      "zmapováno jiným útvarem",
      "nezmapováno"
     ]
    },
    {
     "name": "zdroj",
     "display": "Zdroj",
     "type": "Choice",
     "csv": "zdroj",
     "choices": [
      "rejstrik",
      "karta"
     ],
     "popis": "Odkud polozka prisla - rejstrik nebo evidencni karta utvaru."
    }
   ],
   "display": "Agendy"
  },
  {
   "name": "Procesy",
   "csv": "procesy.csv",
   "popis": "Ciselnik procesu (uroven AA-BB).",
   "ignoruj_csv": {
    "pocet_aktivit": "odvozeny udaj - pocita se az v mape"
   },
   "columns": [
    {
     "name": "Title",
     "display": "Kód",
     "type": "Text",
     "maxlen": 20,
     "required": true,
     "indexed": true,
     "csv": "kod",
     "popis": "Identifikacni kod AA-BB."
    },
    {
     "name": "nazev",
     "display": "Název",
     "type": "Text",
     "maxlen": 255,
     "required": true,
     "csv": "nazev"
    },
    {
     "name": "agenda_kod",
     "display": "Agenda (kód)",
     "type": "Text",
     "maxlen": 20,
     "required": true,
     "indexed": true,
     "csv": "agenda_kod",
     "ref": "Agendy",
     "popis": "Textovy odkaz na Agendy.Title - ne lookup ID (prenositelnost mezi tenanty)."
    },
    {
     "name": "vlastnik",
     "display": "Vlastník procesu",
     "type": "Text",
     "maxlen": 255,
     "csv": "vlastnik",
     "popis": "Odbor. Vice vlastniku pripustne - oddelovac '; '."
    },
    {
     "name": "stav_mapovani",
     "display": "Stav mapování",
     "type": "Choice",
     "indexed": true,
     "csv": "stav_mapovani",
     "choices": [
      "zmapováno",
      "zmapováno jiným útvarem",
      "nezmapováno"
     ]
    },
    {
     "name": "zdroj",
     "display": "Zdroj",
     "type": "Choice",
     "csv": "zdroj",
     "choices": [
      "rejstrik",
      "karta"
     ]
    }
   ],
   "display": "Procesy"
  },
  {
   "name": "DilciProcesy",
   "csv": "dilci_procesy.csv",
   "popis": "Ciselnik dilcich procesu (uroven AA-BB-CCC).",
   "ignoruj_csv": {
    "pocet_aktivit": "odvozeny udaj - pocita se az v mape"
   },
   "columns": [
    {
     "name": "Title",
     "display": "Kód",
     "type": "Text",
     "maxlen": 20,
     "required": true,
     "indexed": true,
     "csv": "kod",
     "popis": "Identifikacni kod AA-BB-CCC."
    },
    {
     "name": "nazev",
     "display": "Název",
     "type": "Text",
     "maxlen": 255,
     "required": true,
     "csv": "nazev",
     "popis": "Nejdelsi namereny nazev 166 znaku - rezerva do 255 je mala, ale sloupec musi zustat Text kvuli razeni a indexaci."
    },
    {
     "name": "proces_kod",
     "display": "Proces (kód)",
     "type": "Text",
     "maxlen": 20,
     "required": true,
     "indexed": true,
     "csv": "proces_kod",
     "ref": "Procesy"
    },
    {
     "name": "vlastnik",
     "display": "Vlastník dílčího procesu",
     "type": "Text",
     "maxlen": 255,
     "csv": "vlastnik",
     "popis": "Odbor. Vice vlastniku pripustne - oddelovac '; '."
    },
    {
     "name": "stav_rejstrik",
     "display": "Stav v rejstříku",
     "type": "Choice",
     "csv": "stav_rejstrik",
     "choices": [
      "využitý",
      "využitý-S4",
      "nevyužitý"
     ],
     "popis": "Barevne odliseni v puvodnim rejstriku."
    },
    {
     "name": "stav_mapovani",
     "display": "Stav mapování",
     "type": "Choice",
     "indexed": true,
     "csv": "stav_mapovani",
     "choices": [
      "zmapováno",
      "zmapováno jiným útvarem",
      "nezmapováno"
     ]
    },
    {
     "name": "zdroj",
     "display": "Zdroj",
     "type": "Choice",
     "csv": "zdroj",
     "choices": [
      "rejstrik",
      "karta"
     ]
    }
   ],
   "display": "Dílčí procesy"
  },
  {
   "name": "Aktivity",
   "csv": "aktivity.csv",
   "popis": "Aktivity (uroven AA-BB-CCC-DDDD). Jeden radek evidence = jedna aktivita.",
   "default_sort": {
    "column": "nazev_kratky",
    "vzestupne": true,
    "pak": "Title"
   },
   "ignoruj_csv": {
    "zdroj_radek": "cislo radku ve zdrojove evidencni karte - artefakt importu, do rejstriku nepatri"
   },
   "columns": [
    {
     "name": "Title",
     "display": "Kód",
     "type": "Text",
     "maxlen": 20,
     "required": true,
     "indexed": true,
     "csv": "kod",
     "popis": "Identifikacni kod AA-BB-CCC-DDDD."
    },
    {
     "name": "nazev",
     "display": "Název aktivity (úplný)",
     "type": "Note",
     "required": true,
     "csv": "nazev",
     "popis": "Uplny nazev. Note (vice radku, prosty text) - namereno 220 znaku, hranice 255 je blizko. Note nejde indexovat ani radit, proto vedle nej stoji nazev_kratky."
    },
    {
     "name": "nazev_kratky",
     "display": "Název",
     "type": "Text",
     "maxlen": 255,
     "indexed": true,
     "csv": null,
     "derive_truncate": {
      "from": "nazev",
      "maxlen": 150
     },
     "popis": "Odvozeny ze sloupce nazev - useknuty na hranici slova na 150 znaku, s vypustkou. Slouzi k razeni a indexaci ve view, ktere Note neumi. Udrzuje ho import a porizovaci appka pri kazde zmene nazvu."
    },
    {
     "name": "dilci_proces_kod",
     "display": "Primární dílčí proces (kód)",
     "type": "Text",
     "maxlen": 20,
     "required": true,
     "indexed": true,
     "csv": "dilci_proces_kod",
     "ref": "DilciProcesy",
     "popis": "Primarni zarazeni. Vsechna zarazeni vc. tohoto drzi list AktivitaDilciProces."
    },
    {
     "name": "vykonava",
     "display": "Vykonává útvar",
     "type": "Text",
     "maxlen": 255,
     "indexed": true,
     "csv": "vykonava",
     "popis": "Oddeleni."
    },
    {
     "name": "spolupracuje",
     "display": "Spolupracuje",
     "type": "Note",
     "csv": "spolupracuje"
    },
    {
     "name": "vnitrni_predpis",
     "display": "Vnitřní předpis",
     "type": "Note",
     "csv": "vnitrni_predpis",
     "popis": "Vice predpisu oddeleno '; '. Namereno 293 znaku - proto Note."
    },
    {
     "name": "text_pro_or",
     "display": "Text pro OŘ",
     "type": "Note",
     "csv": null,
     "popis": "V evidencni karte neexistuje - zaklada se prazdny, plni se rucne pro budouci generovani organizacniho radu."
    },
    {
     "name": "sekce",
     "display": "Sekce",
     "type": "Text",
     "maxlen": 20,
     "indexed": true,
     "csv": "sekce"
    },
    {
     "name": "stav",
     "display": "Stav",
     "type": "Choice",
     "indexed": true,
     "csv": null,
     "choices": [
      "pracovní",
      "schváleno"
     ],
     "default": "pracovní",
     "popis": "V evidencni karte neexistuje - pri importu se plni hodnotou 'pracovní'."
    },
    {
     "name": "datum_aktualizace",
     "display": "Datum aktualizace",
     "type": "DateTime",
     "csv": null,
     "popis": "V evidencni karte neexistuje - pri importu se plni datem importu, dal ji udrzuje porizovaci appka."
    }
   ],
   "display": "Aktivity"
  },
  {
   "name": "AktivitaDilciProces",
   "csv": "aktivita_dilciproces.csv",
   "popis": "Vazebni tabulka M:N - aktivita muze patrit do vice dilcich procesu.",
   "ignoruj_csv": {},
   "columns": [
    {
     "name": "Title",
     "display": "Klíč",
     "type": "Text",
     "maxlen": 40,
     "required": true,
     "indexed": true,
     "csv": null,
     "derive": "{aktivita_kod}__{dilci_proces_kod}",
     "popis": "Odvozeny klic - zajistuje idempotenci importu a brani duplicitni vazbe."
    },
    {
     "name": "aktivita_kod",
     "display": "Aktivita (kód)",
     "type": "Text",
     "maxlen": 20,
     "required": true,
     "indexed": true,
     "csv": "aktivita_kod",
     "ref": "Aktivity"
    },
    {
     "name": "dilci_proces_kod",
     "display": "Dílčí proces (kód)",
     "type": "Text",
     "maxlen": 20,
     "required": true,
     "indexed": true,
     "csv": "dilci_proces_kod",
     "ref": "DilciProcesy"
    },
    {
     "name": "primarni",
     "display": "Primární",
     "type": "Choice",
     "csv": "primarni",
     "choices": [
      "ano",
      "ne"
     ]
    }
   ],
   "display": "Vazba aktivita–dílčí proces"
  }
 ]
};

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

WEB = await urciWeb();
DIGEST = await digest();

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
           // _ColorTag a ComplianceAssetId zaklada SharePoint sam pri vytvoreni
           // listu (overeno 19.08.2026 v PPF). Bez nich by tabulka hlasila
           // 10 sloupcu "navic" a skutecna anomalie by v tom sumu zanikla.
           !["_ColorTag", "ComplianceAssetId",
             "ContentType", "Attachments", "Edit", "LinkTitleNoMenu", "LinkTitle",
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
