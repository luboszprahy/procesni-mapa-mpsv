/* check_setup.js -- smoke test provisioning skriptu bez SharePointu.

   Spusteni z korene projektu:  node src/check_setup.js

   Podstrci falesny SharePoint (fetch + _spPageContextInfo), pusti
   src/setup_sharepoint.js dvakrat a overi to, co se v konzoli neprojevi:
   hlavicky, Options, idempotenci a LinkTitle past ve ViewFields.
*/
"use strict";
const fs = require("fs");
const vm = require("vm");
const { falesnySharePoint, WEB } = require("./fake_sharepoint.js");

const SCHEMA = JSON.parse(fs.readFileSync("src/schema.json", "utf8"));

async function beh(sp, tichy) {
  const kod = fs.readFileSync("src/setup_sharepoint.js", "utf8");
  const zachyt = { log: [], error: [], table: [] };
  const ctx = {
    fetch: sp.fetchMock,
    URL, location: { href: WEB + "/SitePages/Home.aspx", origin: "https://tenant.sharepoint.com",
                     pathname: "/sites/X/procesnimapa/SitePages/Home.aspx" },
    _spPageContextInfo: { webAbsoluteUrl: WEB },
    console: {
      log: (...a) => { zachyt.log.push(a.join(" ")); if (!tichy) console.log("   ", ...a); },
      error: (...a) => { zachyt.error.push(a.join(" ")); console.error("   CHYBA:", ...a); },
      table: (r) => zachyt.table.push(r),
    },
  };
  vm.createContext(ctx);
  await vm.runInContext(kod + "\n;globalThis.__hotovo;", ctx);
  // IIFE je asynchronni - pockej, az dobehnou vsechny mikroulohy
  for (let i = 0; i < 200; i++) await new Promise((r) => setImmediate(r));
  return zachyt;
}

function tvrd(podminka, popis) {
  if (!podminka) { console.log("SELHALO: " + popis); process.exitCode = 1; }
  else console.log("ok: " + popis);
}

(async () => {
  const sp = falesnySharePoint();

  console.log("--- 1. beh (prazdny web) ---");
  const b1 = await beh(sp, true);
  const radky1 = b1.table[0] || [];

  tvrd(b1.error.length === 0, "prvni beh nevyhodil chybu");
  tvrd(sp.listy.size === SCHEMA.lists.length,
       "zalozeno " + SCHEMA.lists.length + " listu (je " + sp.listy.size + ")");

  const ocekavanoSloupcu = SCHEMA.lists.reduce((n, l) => n + l.columns.length, 0);
  tvrd(radky1.length === ocekavanoSloupcu,
       "tabulka ma radek za kazdy sloupec schematu (" + ocekavanoSloupcu + ")");
  tvrd(radky1.every((r) => r.stav === "zalozen" || r.stav === "vestaveny"),
       "vsechny sloupce zalozeny nebo vestavene");
  tvrd(radky1.every((r) => r.ve_zobrazeni === "ano" || r.ve_zobrazeni === "doplneno"),
       "kazdy sloupec skoncil ve vychozim zobrazeni");

  const cfx = sp.log.filter((r) => r.cesta.endsWith("/fields/createfieldasxml"));
  tvrd(cfx.length === ocekavanoSloupcu - SCHEMA.lists.length,
       "createfieldasxml volan pro kazdy sloupec krome vestaveneho Title");
  tvrd(cfx.every((r) => r.telo.parameters.Options === 13),
       "Options = 13 u vsech zakladanych sloupcu");
  tvrd(cfx.every((r) => r.h["Content-Type"] === "application/json;odata=verbose"),
       "createfieldasxml posilan s odata=verbose");
  tvrd(cfx.every((r) => r.telo.parameters.__metadata.type ===
                        "SP.XmlSchemaFieldCreationInformation"),
       "createfieldasxml ma spravny __metadata.type");

  // interni nazvy zustaly ASCII bez diakritiky a mezer
  const vsechnyPole = [...sp.listy.values()].flatMap((l) => [...l.fields.keys()]);
  tvrd(vsechnyPole.every((n) => /^[A-Za-z_][A-Za-z0-9_]*$/.test(n)),
       "vsechny interni nazvy jsou ASCII bez mezer a diakritiky");

  // zobrazovane nazvy se nastavily az pres MERGE
  const agendy = sp.listy.get("Agendy");
  tvrd(agendy.fields.get("vlastnik").Title === "Vlastník agendy",
       "zobrazovany nazev s diakritikou nastaven pres MERGE");
  tvrd(agendy.Title === "Agendy" && sp.listy.get("DilciProcesy").Title === "Dílčí procesy",
       "listy prejmenovany na zobrazovany nazev, URL zustala ASCII");
  tvrd([...sp.listy.values()].every((l) => l.verzovani), "verzovani zapnuto na vsech listech");

  // indexy
  tvrd(agendy.fields.get("Title").Indexed === true,
       "vestaveny Title je po behu indexovany");
  const aktivity = sp.listy.get("Aktivity");
  tvrd(aktivity.fields.get("nazev_kratky").Indexed === true,
       "radici sloupec nazev_kratky je indexovany");
  tvrd(aktivity.fields.get("nazev").TypeAsString === "Note",
       "uplny nazev zustal Note");

  // razeni
  tvrd(/FieldRef Name="nazev_kratky"[^>]*Ascending="TRUE"/.test(aktivity.viewQuery) &&
       /FieldRef Name="Title"/.test(aktivity.viewQuery),
       "vychozi zobrazeni Aktivit radi podle nazev_kratky, pak Title");
  tvrd(sp.listy.get("Agendy").viewQuery === "",
       "listy bez default_sort zustaly bez zasahu do razeni");

  // LinkTitle past: Title uz ve view je, nesmi se pridat podruhe
  tvrd(aktivity.viewFields.filter((x) => x === "Title").length === 0,
       "Title se do ViewFields nepridal podruhe (je tam jako LinkTitle)");

  console.log("--- 2. beh (idempotence) ---");
  const pocetPredtim = sp.log.length;
  const b2 = await beh(sp, true);
  const radky2 = b2.table[0] || [];
  const novaVolani = sp.log.slice(pocetPredtim);

  tvrd(b2.error.length === 0, "druhy beh nevyhodil chybu");
  tvrd(sp.listy.size === SCHEMA.lists.length, "druhy beh nezalozil zadny list navic");
  tvrd(novaVolani.filter((r) => r.cesta.endsWith("/fields/createfieldasxml")).length === 0,
       "druhy beh nezaloz zadny sloupec");
  tvrd(novaVolani.filter((r) => /AddViewField/.test(r.cesta)).length === 0,
       "druhy beh nepridal nic do zobrazeni");
  tvrd(radky2.every((r) => r.stav === "existoval" || r.stav === "vestaveny"),
       "druhy beh hlasi u vsech sloupcu 'existoval'");
  tvrd(radky2.every((r) => r.ve_zobrazeni === "ano"),
       "druhy beh hlasi u vsech sloupcu 've zobrazeni: ano'");
  tvrd(radky2.filter((r) => String(r.stav).startsWith("NAVIC")).length === 0,
       "zadny sloupec navic mimo schema");

  // 3. beh: list zalozeny driv BEZ bitu 4 -> sloupce existuji, ale nejsou ve
  // vychozim zobrazeni. Presne stav, ktery bit 4 uz zpetne neopravi.
  console.log("--- 3. beh (oprava zobrazeni) ---");
  const proc = sp.listy.get("Procesy");
  proc.viewFields = ["LinkTitle"];              // vsechno krome Title vypadlo
  const pocetPredOpravou = sp.log.length;
  const b3 = await beh(sp, true);
  const radky3 = (b3.table[0] || []).filter((r) => r.list === "Procesy");
  const pridane = sp.log.slice(pocetPredOpravou)
    .filter((r) => /AddViewField/.test(r.cesta))
    .map((r) => /AddViewField\('([^']+)'\)/.exec(r.cesta)[1]);

  const cekane = SCHEMA.lists.find((l) => l.name === "Procesy").columns
    .filter((c) => c.name !== "Title").map((c) => c.name);
  tvrd(b3.error.length === 0, "treti beh nevyhodil chybu");
  tvrd(pridane.length === cekane.length && cekane.every((n) => pridane.includes(n)),
       "chybejici sloupce dorovnany pres AddViewField (" + pridane.length + ")");
  tvrd(!pridane.includes("Title") && !pridane.includes("LinkTitle"),
       "Title se pri oprave nepridal (uz tam je jako LinkTitle)");
  tvrd(radky3.filter((r) => r.ve_zobrazeni === "doplneno").length === cekane.length,
       "tabulka oznacila dorovnane sloupce jako 'doplneno'");
  tvrd(sp.log.slice(pocetPredOpravou)
         .filter((r) => r.cesta.endsWith("/fields/createfieldasxml")).length === 0,
       "oprava zobrazeni nezalozila zadny sloupec znovu");

  console.log(process.exitCode ? "\nSMOKE TEST SELHAL" : "\nsmoke test OK");
})();
