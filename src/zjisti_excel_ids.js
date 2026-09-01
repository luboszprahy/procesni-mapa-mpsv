/* Zjistí hodnoty `source` a `drive`, které chce konektor Excel Online (Business).
 *
 * Proč to vůbec řešit: akce `List rows present in a table` bere čtyři parametry
 * a dva z nich jsou neprůhledná ID vázaná na tenant:
 *
 *   source  sites/<host>,<siteId>,<webId>     (Graph site id)
 *   drive   b!<base64>                        (Graph drive id knihovny)
 *   file    lze předat dynamicky              OVĚŘENO 01.09.2026
 *   table   lze zadat jménem ("Aktivity")     OVĚŘENO 01.09.2026
 *
 * Jménem knihovny to nejde: `drive` = "Sdilene dokumenty" skončilo na
 * `The provided drive id appears to be malformed, or does not represent a
 * valid drive` (ověřeno 01.09.2026). Musí to být to `b!…`.
 *
 * Skript odpovídá na dvě otázky naráz:
 *   1. jaké ty hodnoty pro tenhle web jsou (kdyby z nich měly být proměnné),
 *   2. jestli je SharePoint vydá přes /_api/v2.0/drives — protože pak si je
 *      ImportFlow dotáhne za běhu samo a balík nepotřebuje žádnou novou
 *      proměnnou prostředí ani ruční krok při instalaci.
 *
 * Použití: F12 → Console na libovolné stránce cílového SharePoint webu →
 * vložit → Enter. Web si skript odvodí z adresy, nic se nezadává.
 */
(async () => {
  "use strict";

  const JSON_HLAVICKY = {
    headers: { Accept: "application/json;odata=nometadata" },
    credentials: "same-origin",
  };

  // Web = nejdelsi prefix cesty, na kterem /_api/web odpovi. Zkracuje se
  // odzadu, takze to funguje i pro podweby libovolne hloubky.
  async function najdiWeb() {
    const casti = location.pathname.split("/").filter(Boolean);
    for (let i = casti.length; i > 0; i--) {
      const prefix = "/" + casti.slice(0, i).join("/");
      try {
        const r = await fetch(prefix + "/_api/web?$select=ServerRelativeUrl", JSON_HLAVICKY);
        if (r.ok) return (await r.json()).ServerRelativeUrl.replace(/\/$/, "");
      } catch (e) { /* zkousime kratsi prefix */ }
    }
    throw new Error("web se nepodarilo urcit z adresy " + location.pathname);
  }

  async function jsonNeboChyba(url) {
    const r = await fetch(url, JSON_HLAVICKY);
    if (!r.ok) throw new Error(r.status + " " + r.statusText + " na " + url);
    return r.json();
  }

  const web = await najdiWeb();
  console.log("web:", location.origin + web);

  // ---------- source ----------
  // Graph site id ma tvar <host>,<siteId>,<webId>. Oba GUIDy vydava REST,
  // takze `source` jde slozit vzdycky a proměnnou na nej neni potreba.
  const siteId = (await jsonNeboChyba(web + "/_api/site/id")).value;
  const webId = (await jsonNeboChyba(web + "/_api/web/id")).value;
  const ocisti = (g) => String(g).replace(/[{}]/g, "").toLowerCase();
  const source = "sites/" + location.hostname + "," + ocisti(siteId) + "," + ocisti(webId);

  console.log("");
  console.log("source =", source);
  console.log("  (slozitelne za behu: host z adresy webu + /_api/site/id + /_api/web/id)");

  // ---------- drive ----------
  // Tohle je ta otazka, kvuli ktere skript vznikl. Kdyz /_api/v2.0/drives
  // odpovi, umi si ImportFlow drive id dotahnout samo pres SendHTTPRequest
  // a v balicku nezustane nic vazaneho na tenant.
  console.log("");
  let drives = null;
  try {
    drives = await jsonNeboChyba(web + "/_api/v2.0/drives");
    console.log("ANO: /_api/v2.0/drives odpovida — flow si drive id dotahne za behu");
  } catch (chyba) {
    console.warn("NE: /_api/v2.0/drives nedostupne —", chyba.message);
    console.warn("    drive id bude muset byt textova promenna prostredi;");
    console.warn("    hodnoty vypsane nize opis do ni pri instalaci.");
  }

  if (drives && Array.isArray(drives.value)) {
    console.log("");
    console.table(drives.value.map((d) => ({
      knihovna: d.name,
      drive: d.id,
      webUrl: d.webUrl || "",
    })));
    const dulezite = ["Import", "Zalohy", "Exporty", "Dokumenty", "Sdilene dokumenty"];
    for (const jmeno of dulezite) {
      const nalezena = drives.value.find(
        (d) => (d.name || "").toLowerCase() === jmeno.toLowerCase()
          || String(d.webUrl || "").toLowerCase().endsWith("/" + jmeno.toLowerCase()));
      console.log((nalezena ? "  " : "  chybi ") + jmeno + ": "
                  + (nalezena ? nalezena.id : "(knihovna na webu neni)"));
    }
  }

  console.log("");
  console.log("Posli mi cely tenhle vypis. Kdyby /_api/v2.0/drives neodpovedelo,");
  console.log("staci hodnota `drive` z libovolneho behu excelove akce (Show raw inputs).");
})().catch((e) => console.error("zjisti_excel_ids selhal:", e));
