# -*- coding: utf-8 -*-
"""Vyjme flow ze solution zipu — definici, uzel <Workflow> i RootComponent.

Vzniklo kvůli `importnewdata` (01.09.2026): testovací flow, kterým se ověřoval
DLP pro Excel Online. Do balíku nepatří — veze v sobě natvrdo adresu webu PPF
(parametry Excel konektoru jsou neprůhledná ID vázaná na tenant), takže by
balík neprošel bránou přenositelnosti a na MPSV by mířil nikam.

**Connection reference se ZÁMĚRNĚ nechává.** Kvůli ní to flow vzniklo:
spojení na Excel Online se dá založit jen v prostředí, ne vygenerovat, a
`ImportFlow` ho bude potřebovat.

Odebrání z balíku flow v prostředí NESMAŽE — u unmanaged solution zůstane
jako sirotek. Smazat se musí ručně v Power Automate.

Spouštět z kořene projektu:
    python src/odeber_flow.py --solution runs/vstup.zip --flow importnewdata
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path


def odeber(polozky, nazev):
    """Vrátí (nové položky, GUID odebraného flow)."""
    klice = [n for n in polozky
             if n.replace("\\", "/").startswith(f"Workflows/{nazev}")]
    if len(klice) != 1:
        raise SystemExit(f"CHYBA: čekám právě jedno {nazev}, je jich {len(klice)}")
    klic = klice[0]
    guid = re.search(r"-([0-9A-Fa-f-]{36})\.json$", klic).group(1)
    del polozky[klic]

    customizations = polozky["customizations.xml"].decode("utf-8-sig")
    zacatek = customizations.lower().index(f'<workflow workflowid="{{{guid.lower()}}}"')
    konec = customizations.index("</Workflow>", zacatek) + len("</Workflow>")
    uzel = customizations[zacatek:konec]
    customizations = customizations.replace("\n    " + uzel, "").replace(uzel, "")
    polozky["customizations.xml"] = customizations.encode("utf-8")

    solution = polozky["solution.xml"].decode("utf-8-sig")
    novy = re.sub(r'\s*<RootComponent type="29" id="\{' + guid + r'\}"[^>]*/>',
                  "", solution, flags=re.I)
    if novy == solution:
        raise SystemExit(f"CHYBA: RootComponent flow {nazev} v solution.xml nenalezen")
    polozky["solution.xml"] = novy.encode("utf-8")
    return polozky, guid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True)
    parser.add_argument("--flow", required=True, help="prefix názvu souboru ve Workflows/")
    argumenty = parser.parse_args()

    cesta = Path(argumenty.solution)
    if not cesta.exists():
        raise SystemExit(f"CHYBA: solution {cesta} neexistuje")
    with zipfile.ZipFile(cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    polozky, guid = odeber(polozky, argumenty.flow)

    with zipfile.ZipFile(cesta, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)

    zbyva = sorted(n.split("/")[-1].split("-")[0] for n in polozky
                   if n.replace("\\", "/").startswith("Workflows/"))
    print(f"odebráno flow: {argumenty.flow} ({guid})")
    print(f"  v balíku zbývá: {', '.join(zbyva)}")
    print("  connection reference zůstávají — spojení na Excel bude potřeba")
    print("  POZOR: v prostředí flow zůstává, smaž ho ručně v Power Automate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
