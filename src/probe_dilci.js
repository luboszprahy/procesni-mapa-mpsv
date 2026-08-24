/* Sonda: proč appka nevidí vazbu dílčí proces -> proces (24.08.2026)
 *
 * Přehled v appce ukazuje u všech procesů POLOŽKY = 0 a v číselníku je všech
 * 251 dílčích procesů osiřelých, zatímco publikovaná mapa tytéž vazby vidí.
 * Appka a flow tedy nečtou totéž. Sonda vypíše, co v listech doopravdy je:
 * interní názvy sloupců, prvních pár řádků a kolik hodnot se spáruje.
 *
 * POUŽITÍ: otevři v prohlížeči libovolnou stránku webu, na kterém appka běží
 *   https://<tenant>/sites/.../procesnimapa
 * dej F12 -> Console, vlož celý tenhle soubor a odešli. Výsledek se vypíše
 * do konzole; pošli mi ho jako snímek nebo text.
 *
 * Skript jen ČTE (GET), nic nemění.
 */
(async () => {
  const web = location.pathname.split("/_layouts")[0].split("/SitePages")[0]
                .split("/Lists")[0].replace(/\/[^/]*\.aspx$/, "").replace(/\/$/, "");
  const api = (cesta) => fetch(web + "/_api/" + cesta, {
    headers: { Accept: "application/json;odata=nometadata" },
    credentials: "same-origin"
  }).then(r => r.ok ? r.json() : Promise.reject(r.status + " " + r.statusText));

  const vypis = (nadpis, data) => { console.log("%c" + nadpis, "font-weight:bold;color:#110B7A"); console.table(data); };

  console.log("web:", web);

  for (const nazev of ["DilciProcesy", "Procesy", "Aktivity"]) {
    let list;
    try {
      list = await api(`web/lists/getbytitle('${nazev}')?$select=Title,Id,ItemCount`);
    } catch (e) {
      console.warn(`list '${nazev}' se nepodařilo najít podle názvu (${e}) — zkouším podle URL`);
      try {
        list = await api(`web/GetList('${web}/Lists/${nazev}')?$select=Title,Id,ItemCount`);
      } catch (e2) { console.error(`  ani podle URL: ${e2}`); continue; }
    }
    console.log(`%c${nazev}: ${list.ItemCount} položek, GUID ${list.Id}`, "color:#0C5F70");

    // interní názvy vlastních sloupců — právě těmi pracuje appka i flow
    const pole = await api(`web/lists(guid'${list.Id}')/fields?$select=InternalName,Title,TypeAsString,Hidden&$filter=Hidden eq false`);
    vypis(`  sloupce ${nazev}`, pole.value
      .filter(f => !["ContentType", "Attachments", "Edit", "LinkTitleNoMenu", "LinkTitle", "DocIcon", "ItemChildCount", "FolderChildCount", "_UIVersionString", "AppAuthor", "AppEditor"].includes(f.InternalName))
      .map(f => ({ internalName: f.InternalName, zobrazovany: f.Title, typ: f.TypeAsString })));
  }

  // Tři řádky z každého listu — vidět, jestli jsou vazební sloupce vyplněné
  const ukazka = async (nazev, select) => {
    try {
      const d = await api(`web/lists/getbytitle('${nazev}')/items?$select=${select}&$top=3`);
      vypis(`  ukázka ${nazev}`, d.value);
      return d.value;
    } catch (e) { console.error(`ukázka ${nazev} selhala: ${e}`); return []; }
  };
  await ukazka("Procesy", "Id,Title,agenda_kod");
  await ukazka("DilciProcesy", "Id,Title,proces_kod");
  await ukazka("Aktivity", "Id,Title,dilci_proces_kod");

  // Kolik dílčích procesů má proces_kod, který v listu Procesy opravdu existuje
  try {
    const dp = await api("web/lists/getbytitle('DilciProcesy')/items?$select=Title,proces_kod&$top=1000");
    const pr = await api("web/lists/getbytitle('Procesy')/items?$select=Title&$top=1000");
    const kody = new Set(pr.value.map(x => x.Title));
    const prazdne = dp.value.filter(x => !x.proces_kod).length;
    const nesparovane = dp.value.filter(x => x.proces_kod && !kody.has(x.proces_kod));
    console.log("%cVÝSLEDEK", "font-weight:bold;font-size:14px;color:#110B7A");
    console.log("  dílčích procesů:", dp.value.length,
                "| bez proces_kod:", prazdne,
                "| s kódem, který v Procesech není:", nesparovane.length,
                "| spárovaných:", dp.value.length - prazdne - nesparovane.length);
    if (nesparovane.length) vypis("  prvních 5 nespárovaných", nesparovane.slice(0, 5));
  } catch (e) { console.error("porovnání selhalo:", e); }
})();
