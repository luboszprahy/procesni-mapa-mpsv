/* fake_sharepoint.js -- minimalni napodobenina SharePoint REST pro smoke testy.

   Sdili ji src/check_setup.js (zakladani listu a sloupcu) a src/check_import.js
   (zakladani polozek). Umi jen to, co ty dva skripty opravdu volaji - kdyz na
   neco narazi, vyhodi chybu misto tiche odpovedi, aby test spadl adresne.
*/
"use strict";

const WEB = "https://tenant.sharepoint.com/sites/X/procesnimapa";

function falesnySharePoint(predpripraveneListy) {
  const listy = new Map();
  const log = [];
  let guid = 0, itemId = 0;

  function novyList(nazev, popis, baseTemplate) {
    // 101 = knihovna dokumentu. Sedi v korenu webu, ne pod /Lists/ - a prave
    // na tom rozdilu stoji hledani knihovny v setup_sharepoint.js.
    const bt = baseTemplate || 100;
    const l = {
      Id: "guid-" + (++guid), Title: nazev, BaseTemplate: bt,
      url: "/sites/X/procesnimapa/" + (bt === 101 ? "" : "Lists/") + nazev,
      typ: "SP.Data." + nazev + "ListItem",
      popis: popis || "",
      // SharePoint zaklada tyhle dva sloupce sam pri vytvoreni listu
      // (overeno 19.08.2026 v PPF) - mock je ma taky, aby test chytil,
      // kdyby vypadly z vyjimek a zacaly se hlasit jako "navic".
      fields: new Map([
        ["Title", { InternalName: "Title", TypeAsString: "Text",
                    Hidden: false, Indexed: false, Title: "Title" }],
        ["_ColorTag", { InternalName: "_ColorTag", TypeAsString: "Text",
                        Hidden: false, Indexed: false, Title: "Color Tag" }],
        ["ComplianceAssetId", { InternalName: "ComplianceAssetId", TypeAsString: "Text",
                                Hidden: false, Indexed: false, Title: "Compliance Asset Id" }],
      ]),
      viewFields: ["LinkTitle"], viewQuery: "", verzovani: false,
      items: [],
    };
    listy.set(nazev, l);
    return l;
  }

  // volitelne predpripravene listy vc. sloupcu (pro test importu)
  (predpripraveneListy || []).forEach((spec) => {
    const l = novyList(spec.name, spec.popis);
    l.Title = spec.display || spec.name;
    spec.columns.forEach((c) => {
      if (c.name === "Title") return;
      l.fields.set(c.name, {
        InternalName: c.name, TypeAsString: c.type, Hidden: false,
        Indexed: !!c.indexed, Title: c.display || c.name,
      });
    });
  });

  function listPodleGuid(id) {
    for (const l of listy.values()) if (l.Id === id) return l;
    throw new Error("neznamy list guid " + id);
  }

  async function fetchMock(url, opts) {
    opts = opts || {};
    const m = (opts.method || "GET").toUpperCase();
    const h = opts.headers || {};
    const telo = opts.body ? JSON.parse(opts.body) : null;
    const cesta = url.replace(WEB + "/_api/", "");
    log.push({ m, cesta, h, telo });

    const ok = (data) => ({
      ok: true, status: 200,
      json: async () => data,
      text: async () => JSON.stringify(data),
    });
    const chyba = (kod, text) => ({
      ok: false, status: kod,
      json: async () => ({}),
      text: async () => text,
    });

    if (cesta.startsWith("web?$select=ServerRelativeUrl")) {
      return ok({ ServerRelativeUrl: "/sites/X/procesnimapa" });
    }
    if (cesta === "contextinfo") {
      return ok({ d: { GetContextWebInformation: { FormDigestValue: "DIGEST123" } } });
    }
    if (cesta.startsWith("web/lists?$select=Id,Title")) {
      return ok({
        value: [...listy.values()].map((l) => ({
          Id: l.Id, Title: l.Title, BaseTemplate: l.BaseTemplate,
          ListItemEntityTypeFullName: l.typ,
          RootFolder: { ServerRelativeUrl: l.url },
        })),
      });
    }
    if (cesta === "web/lists" && m === "POST") {
      if (listy.has(telo.Title)) throw new Error("list uz existuje: " + telo.Title);
      novyList(telo.Title, telo.Description, telo.BaseTemplate);
      return ok({});
    }

    const g = cesta.match(/^web\/lists\(guid'([^']+)'\)(.*)$/);
    if (g) {
      const l = listPodleGuid(g[1]);
      const zbytek = g[2];

      if (zbytek === "" && m === "POST") {
        l.Title = telo.Title;
        l.verzovani = !!telo.EnableVersioning;
        return ok({});
      }
      if (zbytek.startsWith("/fields?$select=")) {
        return ok({ value: [...l.fields.values()] });
      }
      if (zbytek === "/fields/createfieldasxml") {
        const p = telo.parameters;
        const xml = p.SchemaXml;
        const nazev = /Name="([^"]+)"/.exec(xml.replace(/DisplayName="[^"]*"/, ""))[1];
        const typ = /<Field Type="([^"]+)"/.exec(xml)[1];
        l.fields.set(nazev, {
          InternalName: nazev, TypeAsString: typ, Hidden: false,
          Indexed: /Indexed="TRUE"/.test(xml), Title: nazev,
        });
        if ((p.Options & 4) === 4) l.viewFields.push(nazev);
        return ok({});
      }
      const f = zbytek.match(/^\/fields\/getbyinternalnameortitle\('([^']+)'\)$/);
      if (f && m === "POST") {
        const pole = l.fields.get(f[1]);
        if (!pole) throw new Error("MERGE nad neexistujicim polem " + f[1]);
        pole.Title = telo.Title;
        pole.Indexed = !!telo.Indexed;
        return ok({});
      }
      if (zbytek === "/DefaultView/ViewFields") {
        return ok({ Items: l.viewFields.slice() });
      }
      const a = zbytek.match(/^\/DefaultView\/ViewFields\/AddViewField\('([^']+)'\)$/);
      if (a) { l.viewFields.push(a[1]); return ok({}); }
      if (zbytek === "/DefaultView" && m === "POST") {
        l.viewQuery = telo.ViewQuery;
        return ok({});
      }

      // polozky
      if (zbytek.startsWith("/items?$select=Title")) {
        const top = Number((/\$top=(\d+)/.exec(zbytek) || [0, 100])[1]);
        const skip = Number((/\$skiptoken=(\d+)/.exec(zbytek) || [0, 0])[1]);
        const cast = l.items.slice(skip, skip + top);
        const odpoved = { value: cast.map((i) => ({ Title: i.Title })) };
        if (skip + top < l.items.length) {
          odpoved["odata.nextLink"] = WEB + "/_api/web/lists(guid'" + l.Id +
            "')/items?$select=Title&$top=" + top + "&$skiptoken=" + (skip + top);
        }
        return ok(odpoved);
      }
      if (zbytek === "/items" && m === "POST") {
        if (!telo.__metadata || telo.__metadata.type !== l.typ) {
          return chyba(400, "spatny __metadata.type: " + JSON.stringify(telo.__metadata));
        }
        for (const k of Object.keys(telo)) {
          if (k === "__metadata") continue;
          if (!l.fields.has(k)) {
            return chyba(400, "sloupec '" + k + "' v listu " + l.Title + " neexistuje");
          }
        }
        if (telo.Title && l.items.some((i) => i.Title === telo.Title)) {
          return chyba(400, "duplicitni klic " + telo.Title);
        }
        const it = Object.assign({ Id: ++itemId }, telo);
        delete it.__metadata;
        l.items.push(it);
        return ok({});
      }
    }
    throw new Error("falesny SharePoint neumi: " + m + " " + cesta);
  }

  return { fetchMock, listy, log, WEB };
}

module.exports = { falesnySharePoint, WEB };
