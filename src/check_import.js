/* check_import.js -- smoke test importniho skriptu bez SharePointu.

   Spusteni z korene projektu:  node src/check_import.js

   Overuje to, co se pri behu v konzoli spatne pozna: ze se zalozi presne
   ocekavane pocty, ze druhy beh nic nezdvoji, ze odvozene a doplnovane
   hodnoty sedi, ze se strankuje pres 100 polozek a ze chyba jedne polozky
   nezastavi zbytek.
*/
"use strict";
const fs = require("fs");
const vm = require("vm");
const { falesnySharePoint, WEB } = require("./fake_sharepoint.js");

const SCHEMA = JSON.parse(fs.readFileSync("src/schema.json", "utf8"));

async function beh(sp) {
  const kod = fs.readFileSync("src/import_data.js", "utf8");
  const zachyt = { log: [], error: [], table: [] };
  const ctx = {
    fetch: sp.fetchMock,
    URL, location: { href: WEB + "/SitePages/Home.aspx",
                     origin: "https://tenant.sharepoint.com",
                     pathname: "/sites/X/procesnimapa/SitePages/Home.aspx" },
    _spPageContextInfo: { webAbsoluteUrl: WEB },
    console: {
      log: (...a) => zachyt.log.push(a.join(" ")),
      error: (...a) => zachyt.error.push(a.join(" ")),
      table: (r) => zachyt.table.push(r),
    },
  };
  vm.createContext(ctx);
  await vm.runInContext(kod, ctx);
  for (let i = 0; i < 3000; i++) await new Promise((r) => setImmediate(r));
  return zachyt;
}

function tvrd(podminka, popis) {
  if (!podminka) { console.log("SELHALO: " + popis); process.exitCode = 1; }
  else console.log("ok: " + popis);
}

(async () => {
  const ocekavane = { Agendy: 7, Procesy: 46, DilciProcesy: 250, Aktivity: 46,
                      AktivitaDilciProces: 46 };

  console.log("--- 1. beh (prazdne listy) ---");
  const sp = falesnySharePoint(SCHEMA.lists);
  const b1 = await beh(sp);
  const souhrn1 = b1.table[0] || [];

  tvrd(b1.error.length === 0, "prvni beh nevyhodil chybu");
  tvrd(b1.log.some((l) => l.startsWith("HOTOVO")),
       "skript hlasi HOTOVO: " + (b1.log.find((l) => /^(HOTOVO|POZOR)/.test(l)) || "nic"));

  let pocty = true;
  for (const [nazev, n] of Object.entries(ocekavane)) {
    if (sp.listy.get(nazev).items.length !== n) {
      pocty = false;
      console.log("   " + nazev + ": ceka se " + n + ", je " +
                  sp.listy.get(nazev).items.length);
    }
  }
  tvrd(pocty, "pocty polozek sedi: 7 / 46 / 250 / 46 / 46");
  tvrd(souhrn1.every((s) => s.zalozeno === ocekavane[s.list] && s.chyb === 0),
       "souhrnna tabulka hlasi vse zalozene a nula chyb");

  // odvozene a doplnovane hodnoty
  const akt = sp.listy.get("Aktivity").items;
  tvrd(akt.every((i) => i.stav === "pracovní"), "stav doplnen hodnotou 'pracovní'");
  tvrd(akt.every((i) => /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(i.datum_aktualizace)),
       "datum_aktualizace je ISO UTC");
  tvrd(akt.every((i) => i.text_pro_or === ""), "text_pro_or zalozen prazdny");
  tvrd(akt.every((i) => i.nazev_kratky.length <= 150),
       "nazev_kratky nikde nepresahuje 150 znaku");
  tvrd(akt.every((i) => i.nazev.startsWith(i.nazev_kratky.replace(/…$/, "").slice(0, 40))),
       "nazev_kratky je opravdu zacatkem plneho nazvu");
  tvrd(akt.some((i) => i.nazev_kratky.endsWith("…")),
       "delsi nazvy jsou zkraceny s vypustkou");
  tvrd(akt.some((i) => !i.nazev_kratky.endsWith("…")),
       "kratke nazvy zustaly bez vypustky");

  // vazebni tabulka a odvozeny klic
  const vaz = sp.listy.get("AktivitaDilciProces").items;
  tvrd(vaz.every((i) => i.Title === i.aktivita_kod + "__" + i.dilci_proces_kod),
       "odvozeny klic vazby ma tvar <aktivita>__<dilciproces>");
  tvrd(new Set(vaz.map((i) => i.Title)).size === vaz.length,
       "klice vazeb jsou unikatni");

  // vice vlastniku prezilo do listu
  const proc = sp.listy.get("Procesy").items;
  tvrd(proc.some((i) => i.vlastnik.includes("; ")),
       "vice vlastniku ulozeno v jednom poli oddelene '; '");

  // strankovani: DilciProcesy maji 250 polozek, vychozi stranka je 100
  const dotazyNaKlice = sp.log.filter((r) => /\/items\?\$select=Title/.test(r.cesta));
  tvrd(dotazyNaKlice.every((r) => /\$top=5000/.test(r.cesta)),
       "dotaz na existujici klice pouziva $top=5000");

  console.log("--- 2. beh (idempotence) ---");
  const predtim = sp.log.length;
  const b2 = await beh(sp);
  const souhrn2 = b2.table[0] || [];
  const novePosty = sp.log.slice(predtim).filter(
    (r) => r.m === "POST" && /\/items$/.test(r.cesta));

  tvrd(b2.error.length === 0, "druhy beh nevyhodil chybu");
  tvrd(novePosty.length === 0, "druhy beh nezalozil ani jednu polozku");
  tvrd(souhrn2.every((s) => s.preskoceno === ocekavane[s.list] && s.zalozeno === 0),
       "druhy beh vse preskocil");
  tvrd(Object.entries(ocekavane).every(
         ([n, k]) => sp.listy.get(n).items.length === k),
       "pocty po druhem behu beze zmeny");

  console.log("--- 3. beh (jedna polozka selze) ---");
  const sp3 = falesnySharePoint(SCHEMA.lists);
  // odeber sloupec, ktery Aktivity potrebuji -> kazdy zapis do nich selze,
  // ostatni listy musi projit
  sp3.listy.get("Aktivity").fields.delete("vykonava");
  const b3 = await beh(sp3);
  const souhrn3 = b3.table[0] || [];
  const radekAkt = souhrn3.find((s) => s.list === "Aktivity");

  tvrd(b3.error.length === 0, "treti beh se nezhroutil, chybu jen nasbiral");
  tvrd(radekAkt && radekAkt.chyb === 46 && radekAkt.zalozeno === 0,
       "vsech 46 aktivit hlaseno jako chybnych");
  tvrd(sp3.listy.get("DilciProcesy").items.length === 250,
       "chyba v jednom listu nezastavila import ostatnich");
  tvrd(b3.log.some((l) => l.startsWith("POZOR")),
       "zaverecny vypis hlasi POZOR, ne HOTOVO");
  tvrd(b3.table.length >= 2, "chyby vypsany ve vlastni tabulce");

  console.log(process.exitCode ? "\nSMOKE TEST SELHAL" : "\nsmoke test OK");
})();
