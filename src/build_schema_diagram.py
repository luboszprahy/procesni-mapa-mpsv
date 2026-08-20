"""Schematicky obrazek datoveho modelu (SharePoint listy) ze schema.json -> viz/db_schema.html."""
import csv
import json
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "src" / "schema.json"
DATA = ROOT / "runs" / "normalize"
OUT = ROOT / "viz" / "db_schema.html"

BOX_W = 470
ROW_H = 26
HEAD_H = 48
GAP = 60
COL1_X = 40
COL2_X = 630
LANE_LEFT = 20      # svisly koridor pro vazby v leve kolone
LANE_MID = 550      # koridor vazebni tabulka -> hierarchie
LANE_VYK = 580      # koridor vykonava -> Utvary
LANE_SELF = 1120     # koridor self-reference Utvary

# rozmisteni: hierarchicky retezec vlevo pod sebou, vazebni tabulka a ciselnik utvaru vpravo
LAYOUT = {
    "Agendy": (COL1_X, 30),
    "Procesy": (COL1_X, None),
    "DilciProcesy": (COL1_X, None),
    "Aktivity": (COL1_X, None),
    "Utvary": (COL2_X, 30),
    "AktivitaDilciProces": (COL2_X, None),
}
CHAIN = ["Agendy", "Procesy", "DilciProcesy", "Aktivity"]


def pocty_zaznamu(schema):
    out = {}
    for lst in schema["lists"]:
        f = DATA / (lst.get("csv") or "")
        if f.is_file():
            with f.open(encoding="utf-8-sig", newline="") as fh:
                out[lst["name"]] = max(0, sum(1 for _ in csv.reader(fh)) - 1)
    return out


def rozmisti(schema):
    boxes = {}
    for lst in schema["lists"]:
        boxes[lst["name"]] = {
            "list": lst,
            "h": HEAD_H + len(lst["columns"]) * ROW_H,
            "x": LAYOUT[lst["name"]][0],
            "y": LAYOUT[lst["name"]][1],
        }
    y = boxes["Agendy"]["y"]
    for name in CHAIN:
        boxes[name]["y"] = y
        y += boxes[name]["h"] + GAP
    boxes["AktivitaDilciProces"]["y"] = boxes["Aktivity"]["y"]
    return boxes


def anchor(boxes, list_name, col_name):
    """Stred radku sloupce: (x leve hrany, x prave hrany, y)."""
    b = boxes[list_name]
    idx = [c["name"] for c in b["list"]["columns"]].index(col_name)
    return b["x"], b["x"] + BOX_W, b["y"] + HEAD_H + idx * ROW_H + ROW_H / 2


def path_left(boxes, src, src_col, dst, dst_col, lane):
    """Vazba uvnitr leve kolony - obchazi bloky vlevo."""
    lx, _, y1 = anchor(boxes, src, src_col)
    dx, _, y2 = anchor(boxes, dst, dst_col)
    return f"M {lx} {y1} H {lane} V {y2} H {dx}"


def path_right(boxes, src, src_col, dst, dst_col, lane):
    """Vazba z prave kolony do leve."""
    lx, _, y1 = anchor(boxes, src, src_col)
    _, rx, y2 = anchor(boxes, dst, dst_col)
    return f"M {lx} {y1} H {lane} V {y2} H {rx}"


def badges(col):
    out = []
    if col["name"] == "Title":
        out.append(("pk", "klic"))
    if col.get("required"):
        out.append(("req", "povinne"))
    if col.get("indexed"):
        out.append(("idx", "index"))
    if col.get("ref"):
        out.append(("ref", "-> " + col["ref"]))
    if col.get("derive") or col.get("derive_truncate"):
        out.append(("der", "odvozene"))
    if col.get("csv") is None and not (col.get("derive") or col.get("derive_truncate")):
        out.append(("new", "mimo kartu"))
    return out


def render_box(name, b, pocet):
    lst = b["list"]
    rows = []
    for col in lst["columns"]:
        typ = col["type"]
        if typ == "Text" and col.get("maxlen"):
            typ = f"Text({col['maxlen']})"
        elif typ == "Choice":
            typ = "Choice/" + str(len(col.get("choices", [])))
        bd = "".join(
            f'<span class="b b-{k}">{html.escape(v)}</span>' for k, v in badges(col)
        )
        rows.append(
            f'<div class="row"><span class="cn">{html.escape(col["name"])}</span>'
            f'<span class="cd" title="{html.escape(col.get("popis") or col["display"])}">{html.escape(col["display"])}</span>'
            f'<span class="ct">{html.escape(typ)}</span>{bd}</div>'
        )
    cnt = f'<span class="cnt">{pocet} zázn.</span>' if pocet is not None else ""
    return (
        f'<div class="box" style="left:{b["x"]}px;top:{b["y"]}px;width:{BOX_W}px">'
        f'<div class="head"><span class="hn">{html.escape(lst["display"])}</span>'
        f'<span class="hi">{html.escape(name)}</span>{cnt}</div>'
        + "".join(rows)
        + "</div>"
    )


def main():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    boxes = rozmisti(schema)
    pocty = pocty_zaznamu(schema)

    width = LANE_SELF + 30
    height = max(b["y"] + b["h"] for b in boxes.values()) + 40

    _, ru, yu = anchor(boxes, "Utvary", "nadrizeny_kod")
    _, _, yut = anchor(boxes, "Utvary", "Title")
    _, rx_vyk, y_vyk = anchor(boxes, "Aktivity", "vykonava")

    edges = [
        ("solid", path_left(boxes, "Procesy", "agenda_kod", "Agendy", "Title", LANE_LEFT), "N:1"),
        ("solid", path_left(boxes, "DilciProcesy", "proces_kod", "Procesy", "Title", LANE_LEFT), "N:1"),
        ("solid", path_left(boxes, "Aktivity", "dilci_proces_kod", "DilciProcesy", "Title", LANE_LEFT), "N:1 primarni zarazeni"),
        ("solid", path_right(boxes, "AktivitaDilciProces", "aktivita_kod", "Aktivity", "Title", LANE_MID), "N:1"),
        ("solid", path_right(boxes, "AktivitaDilciProces", "dilci_proces_kod", "DilciProcesy", "Title", LANE_MID), "N:1"),
        ("dash", f"M {ru} {yu} H {LANE_SELF} V {yut} H {ru}", "hierarchie utvaru"),
        ("dash", f"M {rx_vyk} {y_vyk} H {LANE_VYK} V {yut} H {boxes['Utvary']['x']}", "logicka vazba"),
    ]
    paths = "".join(
        f'<path class="e e-{kind}" d="{d}" marker-end="url(#a-{kind})"><title>{html.escape(t)}</title></path>'
        for kind, d, t in edges
    )
    boxes_html = "".join(render_box(n, boxes[n], pocty.get(n)) for n in LAYOUT)

    OUT.write_text(TEMPLATE.format(
        width=width, height=height, paths=paths, boxes=boxes_html,
        verze=html.escape(schema["verze"]), prefix=html.escape(schema["prefix"]),
    ), encoding="utf-8")
    print(f"zapsano: {OUT.relative_to(ROOT)}  ({width}x{height})")


TEMPLATE = """<!DOCTYPE html>
<html lang="cs"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Datovy model - procesni mapa MPSV</title>
<style>
:root {{
  --bg:#f6f7f9; --fg:#16181d; --muted:#666e7a; --card:#fff; --line:#c9cfd8;
  --edge:#7b8794; --head:#1f3a5f; --headfg:#fff;
  --pk:#b45309; --req:#9f1239; --idx:#0f766e; --ref:#1d4ed8; --der:#6d28d9; --new:#4b5563;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg:#12141a; --fg:#e6e8ec; --muted:#98a1b0; --card:#1b1f27; --line:#333a46;
    --edge:#7d8798; --head:#24405f; --headfg:#eaf1fb;
    --pk:#f0b429; --req:#f472a0; --idx:#4ecdc4; --ref:#8ab4ff; --der:#c4a5ff; --new:#9aa3b2;
  }}
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:28px; background:var(--bg); color:var(--fg);
  font:14px/1.45 "Segoe UI",system-ui,sans-serif; }}
h1 {{ margin:0 0 4px; font-size:21px; }}
.sub {{ color:var(--muted); margin:0 0 14px; font-size:13px; }}
.sub code, .note code {{ font-family:Consolas,monospace; }}
.legend {{ display:flex; flex-wrap:wrap; gap:14px; margin:0 0 20px; font-size:12px; color:var(--muted); }}
.legend b {{ font-weight:600; color:var(--fg); }}
.wrap {{ overflow-x:auto; padding-bottom:12px; }}
.canvas {{ position:relative; }}
svg {{ position:absolute; inset:0; z-index:0; overflow:visible; }}
.e {{ fill:none; stroke:var(--edge); stroke-width:1.6; }}
.e-dash {{ stroke-dasharray:5 4; opacity:.75; }}
.box {{ position:absolute; z-index:1; background:var(--card); border:1px solid var(--line);
  border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,.12); overflow:hidden; }}
.head {{ height:48px; display:flex; align-items:center; gap:8px; padding:0 12px;
  background:var(--head); color:var(--headfg); }}
.hn {{ font-weight:600; font-size:15px; }}
.hi {{ font-family:Consolas,monospace; font-size:11px; opacity:.72; }}
.cnt {{ margin-left:auto; font-size:11px; opacity:.8; }}
.row {{ height:26px; display:flex; align-items:center; gap:7px; padding:0 12px;
  border-top:1px solid var(--line); font-size:12px; white-space:nowrap; }}
.cn {{ font-family:Consolas,monospace; min-width:118px; flex:none; }}
.cd {{ color:var(--muted); overflow:hidden; text-overflow:ellipsis; min-width:0; }}
.ct {{ margin-left:auto; color:var(--muted); font-size:11px; font-family:Consolas,monospace; flex:none; }}
.b {{ font-size:9.5px; text-transform:uppercase; letter-spacing:.4px; padding:1px 4px;
  border:1px solid currentColor; border-radius:3px; flex:none; }}
.b-pk {{ color:var(--pk); }} .b-req {{ color:var(--req); }} .b-idx {{ color:var(--idx); }}
.b-ref {{ color:var(--ref); }} .b-der {{ color:var(--der); }} .b-new {{ color:var(--new); }}
.note {{ margin-top:22px; max-width:960px; color:var(--muted); font-size:12.5px; }}
.note b {{ color:var(--fg); }}
</style></head><body>
<h1>Datový model — rejstřík agend a procesů</h1>
<p class="sub">SharePoint Online, 6 seznamů. Generováno ze <code>src/schema.json</code> (verze {verze}, prefix <code>{prefix}</code>), počty záznamů z <code>runs/normalize/</code>.</p>
<div class="legend">
  <span><b>KLIC</b> Title = přirozený identifikační kód</span>
  <span><b>POVINNE</b> required</span>
  <span><b>INDEX</b> indexovaný sloupec</span>
  <span><b>-&gt;</b> textový odkaz na Title cílového listu</span>
  <span><b>ODVOZENE</b> dopočítává import a appka</span>
  <span><b>MIMO KARTU</b> v evidenční kartě neexistuje</span>
  <span>—— vazba ze schématu &nbsp;&nbsp; - - - logická vazba</span>
</div>
<div class="wrap"><div class="canvas" style="width:{width}px;height:{height}px">
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs>
<marker id="a-solid" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
  <path d="M0 0 L9 4.5 L0 9 z" fill="var(--edge)"/></marker>
<marker id="a-dash" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
  <path d="M0 0 L9 4.5 L0 9 z" fill="var(--edge)" opacity=".75"/></marker>
</defs>
{paths}
</svg>
{boxes}
</div></div>
<p class="note">Vazby se drží <b>kódem</b> (<code>Title</code>), ne SharePoint lookup ID — model je tím
přenositelný mezi tenanty a migrovatelný do Dataverse. Zařazení aktivity do dílčích procesů je
<b>M:N</b> přes list <code>AktivitaDilciProces</code>; sloupec <code>dilci_proces_kod</code> v listu
Aktivity nese jen primární zařazení a je v M:N tabulce zopakován. Vazba
<code>Aktivity.vykonava</code> → <code>Útvary</code> je zatím jen logická — ve schématu není
deklarovaná jako <code>ref</code>, protože číselník útvarů se odvozuje z čísel v aktivitách.</p>
</body></html>
"""

if __name__ == "__main__":
    main()
