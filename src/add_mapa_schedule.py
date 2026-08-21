# -*- coding: utf-8 -*-
"""Přidá do solution plánované dvojče publikačního flow (MapaPublishScheduled).

Power Automate flow má právě JEDEN trigger, takže „PowerApps + Recurrence"
v jednom flow neexistuje. Ruční spouštění z appky (`MapaPublishFlow.Run()`)
musí zůstat, a proto vzniká druhé flow se stejnými akcemi a triggerem
Recurrence. Logika se nezdvojuje ve zdroji — akce se KLONUJÍ z hotového
MapaPublishFlow, takže obě flow dělají prokazatelně totéž.

Klon je zároveň nejbezpečnější lokální úprava exportu, jakou skill připouští:
mění se jen GUID a název, ostatní zůstává bajt v bajt. Nové GUID navíc
zaručí, že import nenarazí na sirotka po starším pokusu.

Skript je idempotentní — když už dvojče v balíku je, jen ho přepíše.

Spouštět z kořene projektu:
    python src/add_mapa_schedule.py --solution input/procesnimapa_1_0_0_24.zip
    python src/add_mapa_schedule.py --solution ... --hodina 7
"""

import argparse
import json
import re
import sys
import uuid
import zipfile
from pathlib import Path

ZDROJ = "MapaPublishFlow"
CIL = "MapaPublishScheduled"
# Pevné GUID: opakované spuštění skriptu musí dát TOTÉŽ flow, jinak by každý
# build zakládal nové a v prostředí by se hromadili sirotci.
CIL_GUID = "7c1e5220-0b4d-4f2a-9a51-6f0f2f4a1d3e"
CASOVE_PASMO = "Central Europe Standard Time"


def klic_flow(polozky, prefix):
    nalezene = [n for n in polozky if n.replace("\\", "/").startswith(f"Workflows/{prefix}")]
    if len(nalezene) != 1:
        raise SystemExit(f"CHYBA: čekám právě jedno {prefix}, našel jsem {len(nalezene)}")
    return nalezene[0]


def trigger(hodina):
    """Denní Recurrence. startTime bez pásma — timeZone si ho určuje sám."""
    return {
        "Recurrence": {
            "type": "Recurrence",
            "recurrence": {
                "frequency": "Day",
                "interval": 1,
                "timeZone": CASOVE_PASMO,
                "startTime": f"2026-01-01T{hodina:02d}:00:00",
                "schedule": {"hours": [str(hodina)], "minutes": [0]},
            },
        }
    }


def uzel_workflow(customizations, guid):
    """Vystřihne <Workflow> zdrojového flow — klon se z něj vyrobí náhradami."""
    zacatek = customizations.index(f'<Workflow WorkflowId="{{{guid}}}"')
    konec = customizations.index("</Workflow>", zacatek) + len("</Workflow>")
    return customizations[zacatek:konec]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True)
    parser.add_argument("--hodina", type=int, default=7, help="hodina denního běhu (0-23)")
    argumenty = parser.parse_args()
    if not 0 <= argumenty.hodina <= 23:
        raise SystemExit("CHYBA: --hodina musí být 0 až 23")

    cesta = Path(argumenty.solution)
    with zipfile.ZipFile(cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    zdroj_klic = klic_flow(polozky, ZDROJ)
    zdroj_guid = re.search(r"-([0-9A-Fa-f-]{36})\.json$", zdroj_klic).group(1).lower()

    # --- 1. definice flow: klon akcí, vlastní trigger ---
    flow = json.loads(polozky[zdroj_klic].decode("utf-8-sig"))
    definice = flow["properties"]["definition"]
    if not definice.get("actions"):
        raise SystemExit("CHYBA: zdrojové flow nemá akce — nejdřív spusť build_mapa_flow.py")
    if json.dumps(flow).count("triggerBody") or json.dumps(flow).count("triggerOutputs"):
        raise SystemExit("CHYBA: akce se odkazují na trigger, klon s Recurrence by je rozbil")
    definice["triggers"] = trigger(argumenty.hodina)
    definice["contentVersion"] = "1.0.0.0"

    cil_klic = f"Workflows/{CIL}-{CIL_GUID.upper()}.json"
    for stary in [n for n in polozky if n.replace("\\", "/").startswith(f"Workflows/{CIL}")]:
        del polozky[stary]
    polozky[cil_klic] = json.dumps(flow, ensure_ascii=False, indent=1).encode("utf-8")

    # --- 2. customizations.xml: klon uzlu <Workflow> ---
    customizations = polozky["customizations.xml"].decode("utf-8-sig")
    if f'Name="{CIL}"' in customizations:
        stary = uzel_workflow(customizations, CIL_GUID)
        customizations = customizations.replace("\n    " + stary, "").replace(stary, "")
    uzel = uzel_workflow(customizations, zdroj_guid)
    novy = (uzel.replace(zdroj_guid, CIL_GUID)
                .replace(zdroj_guid.upper(), CIL_GUID.upper())
                .replace(ZDROJ, CIL))
    if novy == uzel:
        raise SystemExit("CHYBA: klon uzlu Workflow se od předlohy neliší")
    customizations = customizations.replace(uzel, uzel + "\n    " + novy, 1)
    polozky["customizations.xml"] = customizations.encode("utf-8")

    # --- 3. solution.xml: RootComponent, jinak se flow do balíku nezahrne ---
    solution = polozky["solution.xml"].decode("utf-8-sig")
    solution = re.sub(r'\s*<RootComponent type="29" id="\{' + CIL_GUID + r'\}"[^>]*/>', "", solution)
    zdrojovy_rc = f'<RootComponent type="29" id="{{{zdroj_guid}}}" behavior="0" />'
    if zdrojovy_rc not in solution:
        raise SystemExit("CHYBA: RootComponent zdrojového flow nenalezen")
    solution = solution.replace(
        zdrojovy_rc,
        zdrojovy_rc + f'\n      <RootComponent type="29" id="{{{CIL_GUID}}}" behavior="0" />', 1)
    polozky["solution.xml"] = solution.encode("utf-8")

    with zipfile.ZipFile(cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)

    print(f"přidáno flow: {CIL}")
    print(f"  GUID: {CIL_GUID}")
    print(f"  akcí: {len(definice['actions'])} (klon z {ZDROJ})")
    print(f"  spouští se: denně v {argumenty.hodina}:00, {CASOVE_PASMO}")
    print(f"  ruční spuštění z appky zůstává na {ZDROJ}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
