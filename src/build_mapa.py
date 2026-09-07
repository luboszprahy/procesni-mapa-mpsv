"""Sestaveni HTML procesni mapy: sablona + zapecena data (FloorPlan pattern).

Kotvy v sablone se nahrazuji prave jednou, jinak build selze.
Stejny postup pouzije pozdeji Power Automate flow pri publikaci do Site Assets.
"""
import argparse
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ANCHORS = ("__DATA_JSON__", "__GEN__")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="runs/normalize/model.json")
    ap.add_argument("--template", default="src/mapa_template.html")
    ap.add_argument("--out", default="viz/mapa_prototyp.html")
    args = ap.parse_args()

    model = json.loads(Path(args.model).read_text(encoding="utf-8"))
    tpl = io.open(args.template, encoding="utf-8").read()

    for a in ANCHORS:
        n = tpl.count(a)
        if n != 1:
            sys.exit("kotva %s je v sablone %dx, ocekava se prave 1x" % (a, n))

    html = tpl.replace("__DATA_JSON__", json.dumps(model, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("__GEN__", json.dumps(
        "vygenerováno " + datetime.now().strftime("%d.%m.%Y %H:%M"), ensure_ascii=False))

    # smoke testy: zadna kotva nezbyla, zadny externi zdroj, data opravdu uvnitr
    left = [a for a in ANCHORS if a in html]
    if left:
        sys.exit("v vystupu zustaly kotvy: %s" % left)
    ext = re.findall(r"""(?:src|href)\s*=\s*["']https?://[^"']+""", html)
    if ext:
        sys.exit("externi zdroje nejsou povoleny: %s" % ext[:3])
    for klic in ("agendy", "procesy", "dilci_procesy", "aktivity", "vazby"):
        if ('"%s":' % klic) not in html:
            sys.exit("v datech chybi klic %s" % klic)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    io.open(out, "w", encoding="utf-8", newline="\n").write(html)

    # Do Site Assets se nahrava kopie z runs/build/, ne src/ a viz/. Driv se
    # delala rucne a 21.08.2026 se rozesla: sablona v src/ mela nove ovladaci
    # prvky, ta v runs/build/ (a tim i publikovana mapa) byla o den stara.
    # Proto ji prepisuje build, ne clovek.
    if args.template == "src/mapa_template.html":
        build = Path("runs/build")
        build.mkdir(parents=True, exist_ok=True)
        io.open(build / "mapa_template.html", "w", encoding="utf-8", newline="\n").write(tpl)
        io.open(build / "procesni_mapa.html", "w", encoding="utf-8", newline="\n").write(html)
        print("runs/build/mapa_template.html + runs/build/procesni_mapa.html aktualizovany")

    print("%s  (%.1f kB)" % (out, out.stat().st_size / 1024))
    print("agendy=%d procesy=%d dílčí=%d aktivity=%d vazby=%d"
          % tuple(len(model[k]) for k in
                  ("agendy", "procesy", "dilci_procesy", "aktivity", "vazby")))


if __name__ == "__main__":
    main()
