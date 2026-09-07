/* Test chování rozkladového diagramu bez prohlížeče.
 *
 * Spouští SKUTEČNOU funkci `renderRozklad()` z hotové stránky nad minimálním
 * DOM stubem — brána `check_mapa_html.py` kontroluje strukturu, ne chování,
 * a právě chybu v chování (tři prázdné sloupce s hláškou „Tady rejstřík
 * končí") jsme 07.09.2026 poslali uživateli.
 *
 * Spouštět z kořene projektu:  node src/test_rozklad.js
 */
const fs = require("fs");
const path = require("path");

const STRANKA = path.join("runs", "build", "procesni_mapa.html");

/* ---- minimální DOM ---- */
function mkEl(tag){
  const el = {
    tagName: tag, children: [], attrs: {}, dataset: {},
    style: {setProperty(){}, removeProperty(){}},
    _text: "", hidden: false, checked: false, value: "",
    classList: {
      _s: new Set(),
      add(...c){ c.forEach(x => this._s.add(x)); },
      remove(...c){ c.forEach(x => this._s.delete(x)); },
      toggle(c, on){ on ? this._s.add(c) : this._s.delete(c); },
      contains(c){ return this._s.has(c); }
    },
    get className(){ return [...this.classList._s].join(" "); },
    set className(v){ this.classList._s = new Set(String(v).split(/\s+/).filter(Boolean)); },
    get textContent(){
      return this.children.length
        ? this.children.map(c => c.textContent).join("")
        : this._text;
    },
    set textContent(v){ this._text = String(v); this.children = []; },
    appendChild(c){ this.children.push(c); c.parent = this; c.parentElement = this; return c; },
    removeChild(c){ this.children = this.children.filter(x => x !== c); },
    remove(){ if (this.parent) this.parent.removeChild(this); },
    setAttribute(k, v){ this.attrs[k] = String(v); },
    getAttribute(k){ return this.attrs[k]; },
    addEventListener(){},
    getBoundingClientRect(){ return {top:0,left:0,right:0,bottom:0,width:0,height:0}; },
    querySelector(sel){ return this.querySelectorAll(sel)[0] || null; },
    querySelectorAll(sel){
      const out = [];
      const sedi = el => {
        if (sel.startsWith(".")) {
          const [tridy, atr] = sel.split("[");
          if (!tridy.slice(1).split(".").every(t => el.classList.contains(t))) return false;
          if (atr){
            const m = atr.replace("]", "").split("=");
            return el.attrs[m[0]] === m[1].replace(/['"]/g, "");
          }
          return true;
        }
        return el.tagName === sel;
      };
      const projdi = n => n.children.forEach(c => { if (sedi(c)) out.push(c); projdi(c); });
      projdi(this);
      return out;
    }
  };
  return el;
}

const prvky = {};
function prvek(id, nastav){
  const el = mkEl("div");
  el.id = id;
  Object.assign(el, nastav || {});
  prvky[id] = el;
  return el;
}

prvek("q", {value: ""});
prvek("fUtvar", {value: ""});
prvek("fStav", {value: ""});
prvek("fUroven", {value: "4"});
prvek("cKod", {checked: true});
prvek("cOsirele", {checked: false, parentElement: mkEl("label"), disabled: false});
prvek("tree");
prvek("detail");
prvek("detailBody");
prvek("meta");
prvek("counts");
prvek("rozklad");
prvek("rzSpojnice");
prvek("fVelikost");
prvek("fZobrazeni");

const elSloupceStub = prvek("rzSloupce");
/* Aktivní zobrazení; test si ho přepíná sám. */
const tlacitkoZobrazeni = mkEl("button");
tlacitkoZobrazeni.dataset.zobrazeni = "rozklad";
const hlavicky = [];
for (let i = 0; i < 4; i++){ const h = mkEl("div"); hlavicky.push(h); }

global.document = {
  body: mkEl("body"),
  documentElement: mkEl("html"),
  getElementById: id => prvky[id] || prvek(id),
  createElement: mkEl,
  createElementNS: (ns, tag) => mkEl(tag),
  createDocumentFragment: () => mkEl("#fragment"),
  createTextNode: t => { const el = mkEl("#text"); el.textContent = t; return el; },
  querySelector: sel => global.document.querySelectorAll(sel)[0] || null,
  querySelectorAll: sel => {
    if (sel === ".rz-hlavicky div") return hlavicky;
    if (sel.startsWith("#fZobrazeni")) return [tlacitkoZobrazeni];
    return [];
  },
  addEventListener(){}
};
global.window = {addEventListener(){}, getComputedStyle: () => ({})};
global.localStorage = {getItem: () => null, setItem(){}};
global.console = console;

/* ---- načtení skriptu stránky ---- */
const html = fs.readFileSync(STRANKA, "utf8");
const skript = html.match(/<script>([\s\S]*?)<\/script>/)[1];
/* Init na konci sahá na věci, které stub nemá; test volá renderRozklad sám. */
const bezInitu = skript.replace(/\nprekresli\(\);\s*$/, "\n");
const modul = new Function(bezInitu + "\nreturn {renderRozklad, rzCesta, TREE, filtruj, norm};");
const M = modul();

/* ---- kontroly ---- */
let chyb = 0;
const overit = (podminka, popis) => {
  console.log((podminka ? "OK   " : "CHYBA") + "  " + popis);
  if (!podminka) chyb++;
};

const sloupce = () => elSloupceStub.querySelectorAll(".rz-sloupec");
const uzly = s => s.querySelectorAll(".rz-uzel");
const prazdno = s => s.querySelectorAll(".rz-prazdno").map(p => p.textContent);

M.renderRozklad();
let s = sloupce();
overit(s.length === 4, `vykreslily se čtyři sloupce (${s.length})`);
overit(uzly(s[0]).length === 7, `sloupec agend má 7 položek (${uzly(s[0]).length})`);

// jádro nálezu z 07.09.2026: sloupce nesmí být prázdné hned po otevření
const prazdnych = s.filter(x => uzly(x).length === 0).length;
overit(prazdnych === 0, `žádný sloupec není po otevření prázdný (prázdných: ${prazdnych})`);

const hlasky = s.flatMap(prazdno);
overit(!hlasky.some(h => h.includes("Tady rejstřík končí")),
       "nikde nesvítí hláška o konci rejstříku tam, kde data jsou");

/* Pozor na `every()`: v řídkém poli DÍRY PŘESKAKUJE, takže nad [ , , ] vrátí
   true. Přesně tak byl tenhle test zprvu slepý k chybě, kvůli které vznikl.
   Spread díry rozbalí na undefined a kontrola je pak poctivá. */
overit(M.rzCesta.length >= 3 && [...M.rzCesta].every(k => typeof k === "string"),
       `předvybraná cesta je úplná a bez děr (${JSON.stringify(M.rzCesta)})`);

// volba úrovně řídí počet sloupců
prvky.fUroven.value = "2";
M.renderRozklad();
overit(sloupce().length === 2, `volba dvou urovni necha dva sloupce (${sloupce().length})`);
overit(hlavicky.filter(h => !h.hidden).length === 2,
       "skryly se i hlavičky sloupců, které nejsou vidět");

prvky.fUroven.value = "4";
M.renderRozklad();
overit(sloupce().length === 4, "návrat na čtyři sloupce");

// filtr, kterému nic neodpovídá
prvky.q.value = "nexistujicivyraz";
M.renderRozklad();
const h2 = sloupce().flatMap(prazdno);
overit(h2.some(h => h.includes("Nic neodpovídá")), "prázdný výsledek hledání to řekne");
/* Když filtr odřízne všechno, cesta se má vyprázdnit — ne natáhnout o prázdné
   prvky. `rzCesta.length = i` na kratším poli ho totiž NATÁHNE a sloupec pak
   tvrdí, že výběr existuje („Tady rejstřík končí" místo „Vyber položku vlevo").
   Předvýběr první větve tenhle bug maskuje, proto se zkouší až tady. */
overit([...M.rzCesta].every(k => typeof k === "string"),
       `po prázdném filtru nemá cesta díry (${JSON.stringify(M.rzCesta)})`);
overit(!sloupce().flatMap(prazdno).some(h => h.includes("Tady rejstřík končí")),
       "prázdný filtr nehlásí konec rejstříku, ale prázdný výsledek");
prvky.q.value = "";

// filtr zkrátí cestu, ale nesmí ji natáhnout o prázdné prvky
prvky.fStav.value = "schváleno";
M.renderRozklad();
overit([...M.rzCesta].every(k => typeof k === "string"),
       `cesta po filtru nemá díry (${JSON.stringify(M.rzCesta)})`);
prvky.fStav.value = "";

console.log(chyb ? `\nNEPROŠLO — ${chyb} chyb` : "\nOK — rozkladový diagram se chová podle zadání");
process.exit(chyb ? 1 : 0);
