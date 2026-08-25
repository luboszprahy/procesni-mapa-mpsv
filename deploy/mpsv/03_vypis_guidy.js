// Vypíše GUIDy listů rejstříku — potřebné pro src/build_flow.py.
// Vložit do konzole prohlížeče (F12) na stránce cílového webu MPSV.
// Jen čte, nic nemění.
(async () => {
  const web = location.pathname.replace(/\/(SitePages|Lists|_layouts)\/.*$/i, "")
                              .replace(/\/$/, "");
  const api = (cesta) =>
    fetch(web + "/_api/" + cesta, {
      headers: { Accept: "application/json;odata=nometadata" },
      credentials: "same-origin",
    }).then((r) => r.json());

  const data = await api("web/lists?$select=Title,Id,ItemCount&$filter=Hidden eq false");
  const radky = data.value
    .filter((l) => ["Agendy", "Procesy", "Dílčí procesy", "Aktivity", "Vazba aktivita–dílčí proces", "Útvary"].includes(l.Title))
    .map((l) => ({ list: l.Title, GUID: l.Id, polozek: l.ItemCount }));
  console.log("web: " + web);
  console.table(radky);
  console.log(
    radky.length === 6
      ? "OK - nalezeny vsechny listy rejstriku"
      : "POZOR - ceka se " + 6 + " listu, nalezeno " + radky.length
  );
})();
