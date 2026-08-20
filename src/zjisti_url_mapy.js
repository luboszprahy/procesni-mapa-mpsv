/* Zjistí, kterou adresou se publikovaná mapa ZOBRAZÍ, a kterou se STÁHNE.
 *
 * Proč to vůbec řešit: klik na soubor v knihovně mapu zobrazí, ale přímý
 * odkaz z appky (Launch) ji stáhne do Downloads. Rozdíl je v tom, jakou
 * hlavičku SharePoint pošle — Strict browser file handling dává u .html
 * `Content-Disposition: attachment`. Tenhle skript to u každé kandidátní
 * adresy změří místo aby se hádalo.
 *
 * Použití: F12 → Console na LIBOVOLNÉ stránce cílového SharePoint webu
 * (klidně na samotné knihovně Site Assets) → vložit → Enter.
 * Web si skript odvodí z adresy stránky, nic se nezadává.
 */
(async () => {
  const SOUBOR = "procesni_mapa.html";
  const SLOZKA = "SiteAssets";

  // Web = nejdelší prefix cesty, na kterém /_api/web odpoví. Zkracuje se
  // odzadu, takže to funguje i pro podweby libovolné hloubky.
  async function najdiWeb() {
    const casti = location.pathname.split("/").filter(Boolean);
    for (let i = casti.length; i > 0; i--) {
      const prefix = "/" + casti.slice(0, i).join("/");
      try {
        const r = await fetch(prefix + "/_api/web?$select=ServerRelativeUrl", {
          headers: { Accept: "application/json;odata=nometadata" },
          credentials: "same-origin",
        });
        if (r.ok) return (await r.json()).ServerRelativeUrl.replace(/\/$/, "");
      } catch (e) { /* zkoušíme kratší prefix */ }
    }
    throw new Error("web se nepodařilo určit z adresy " + location.pathname);
  }

  const web = await najdiWeb();
  const cesta = `${web}/${SLOZKA}/${SOUBOR}`;
  console.log("web:  ", web);
  console.log("soubor:", cesta);

  // UniqueId potřebují všechny adresy přes _layouts. LinkingUrl je adresa,
  // kterou SharePoint sám považuje za "odkaz na tenhle soubor".
  const r = await fetch(
    `${web}/_api/web/GetFileByServerRelativeUrl('${cesta}')?$select=UniqueId,LinkingUrl,ServerRelativeUrl,Length,TimeLastModified`,
    { headers: { Accept: "application/json;odata=nometadata" }, credentials: "same-origin" });
  if (!r.ok) {
    console.error(`soubor ${cesta} nenalezen (HTTP ${r.status}) — je nahraný?`);
    return;
  }
  const f = await r.json();
  const guid = f.UniqueId;
  console.log("velikost:", (f.Length / 1024).toFixed(1), "kB   upraveno:", f.TimeLastModified);

  const puvod = location.origin;
  const kandidati = [
    ["přímý odkaz (co má appka dnes)", puvod + cesta],
    ["přímý + ?web=1", puvod + cesta + "?web=1"],
    ["Doc.aspx action=default", `${puvod}${web}/_layouts/15/Doc.aspx?sourcedoc=%7B${guid}%7D&file=${encodeURIComponent(SOUBOR)}&action=default`],
    ["Doc.aspx action=view", `${puvod}${web}/_layouts/15/Doc.aspx?sourcedoc=%7B${guid}%7D&file=${encodeURIComponent(SOUBOR)}&action=view`],
    ["embed.aspx", `${puvod}${web}/_layouts/15/embed.aspx?UniqueId=${guid}`],
    ["WopiFrame.aspx", `${puvod}${web}/_layouts/15/WopiFrame.aspx?sourcedoc=%7B${guid}%7D&action=view`],
  ];
  if (f.LinkingUrl) kandidati.push(["LinkingUrl (ze SharePointu)", f.LinkingUrl]);

  const vysledky = [];
  for (const [popis, url] of kandidati) {
    let stav = "", disp = "", typ = "", verdikt = "";
    try {
      // redirect:manual — přesměrování je samo o sobě informace; kdyby ho
      // fetch potichu následoval, měřili bychom hlavičky úplně jiné adresy.
      const o = await fetch(url, { method: "GET", credentials: "same-origin", redirect: "manual" });
      stav = o.status || (o.type === "opaqueredirect" ? "302 (přesměrování)" : "?");
      disp = o.headers.get("content-disposition") || "";
      typ = (o.headers.get("content-type") || "").split(";")[0];
      if (o.type === "opaqueredirect") verdikt = "přesměrovává — otevři ručně a podívej se, kde skončíš";
      else if (/attachment/i.test(disp)) verdikt = "STÁHNE SE";
      else if (typ === "text/html") verdikt = "ZOBRAZÍ SE";
      else verdikt = "nejisté (" + (typ || "bez typu") + ")";
    } catch (e) {
      verdikt = "chyba: " + e.message;
    }
    vysledky.push({ varianta: popis, verdikt, stav, "content-disposition": disp.slice(0, 40), url });
  }

  console.table(vysledky.map(({ url, ...zbytek }) => zbytek));
  console.log("\nOdkazy k ručnímu vyzkoušení (ctrl+klik otevře v novém panelu):");
  vysledky.forEach((v) => console.log(`${v.verdikt.padEnd(12)} ${v.varianta}\n    ${v.url}`));
  console.log(
    "\nHotovo. Pošli řádek té varianty, která se ZOBRAZÍ — dosadí se do varMapaUrl v App.OnStart.\n" +
    "Když se stáhne úplně všechno, je cesta přes stránku s web partem Vložit (viz deploy/navod_publikace_mapy.md)."
  );
})();
