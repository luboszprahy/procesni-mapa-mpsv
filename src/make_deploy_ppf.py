# -*- coding: utf-8 -*-
"""Sestaví deploy/ppf/ — všechno, co je potřeba k nasazení na PPF DEV.

Zrcadlo `make_deploy_mpsv.py`, se kterým sdílí výběr balíku, bránu proti GUIDům
a popisy flow. Liší se ve dvou věcech, a obě jsou podstatné:

  * data jsou **anonymizovaná** (`runs/anonym`) — do cizího vývojového tenantu
    reálné útvary, předpisy ani znění činností nepatří,
  * README vzniká z `src/sablona_instalace_ppf.md`, takže čísla (verze balíku,
    počet flow, obrazovek a proměnných) pocházejí z balíku, ne z paměti.

Druhý bod je celý důvod, proč tenhle skript existuje: ručně udržovaná
`deploy/INSTALACE.md` zaostala o třináct verzí a nikdo to nepoznal, protože
návod vypadal pořád stejně.

Spouštět z kořene projektu:
    python src/make_deploy_ppf.py
"""

import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402
from make_deploy_mpsv import (  # noqa: E402
    FLOW, VYPIS_GUIDU, overuj_bez_guidu, posledni_balik, spust,
)

CIL = Path("deploy/ppf")
DATA = Path("runs/anonym")
SABLONA = Path("src/sablona_instalace_ppf.md")
PY = Path(".venv/Scripts/python.exe")

CISLOVKY = {1: "jeden", 2: "dva", 3: "tři", 4: "čtyři", 5: "pět", 6: "šest",
            7: "sedm", 8: "osm", 9: "devět", 10: "deset", 11: "jedenáct",
            12: "dvanáct"}


def slovy(pocet):
    """Číslovka slovem; nad rámec tabulky číslicí, ať návod nelže."""
    return CISLOVKY.get(pocet, str(pocet))


def tabulka_promennych(schema):
    """Řádky tabulky proměnných — co se u které vybírá v průvodci importem."""
    knihovny = {k["name"] for k in schema["libraries"]}
    display = {l["name"]: l.get("display") or l["name"]
               for l in schema["lists"] + schema["libraries"]}

    radky = ["| proměnná | zobrazí se jako | vybírá se |", "|---|---|---|"]
    for schema_name, nazev, _, klic, _ in ep.DEFINICE:
        if klic == "dataset":
            vybira = "web"
        else:
            interni = schema_name.split("list", 1)[-1]
            if interni in knihovny:
                vybira = f"**knihovna** `{display[interni]}`"
            else:
                vybira = f"list `{display.get(interni, interni)}`"
        radky.append(f"| `{schema_name}` | {nazev} | {vybira} |")
    return "\n".join(radky)


def tabulka_flow(flow):
    radky = ["| flow | co dělá | trigger |", "|---|---|---|"]
    for jmeno in flow:
        popis, trigger = FLOW.get(jmeno, ("—", "—"))
        radky.append(f"| `{jmeno}` | {popis} | {trigger} |")
    return "\n".join(radky)


def readme(balik, flow, obrazovky, schema):
    """Vyplní šablonu. Nevyplněná kotva je chyba, ne kosmetika."""
    if not SABLONA.exists():
        raise SystemExit(f"CHYBA: {SABLONA} neexistuje")

    text = SABLONA.read_text(encoding="utf-8")
    text = re.sub(r"<!-- ŠABLONA.*?-->\n+", "", text, count=1, flags=re.S)

    verze = ".".join(re.findall(r"\d+", balik.stem)[-4:])
    hodnoty = {
        "balik": balik.name,
        "verze": verze,
        "obrazovky_slovy": slovy(obrazovky),
        "pocet_flow_slovy": slovy(len(flow)),
        "pocet_listu_slovy": slovy(len(schema["lists"])),
        "pocet_promennych_slovy": slovy(len(ep.DEFINICE)),
        "pocet_promennych_slovy_velka": slovy(len(ep.DEFINICE)).upper(),
        "pocet_promennych_bez_webu_slovy": slovy(len(ep.DEFINICE) - 1),
        "tabulka_promennych": tabulka_promennych(schema),
        "tabulka_flow": tabulka_flow(flow),
    }
    for klic, hodnota in hodnoty.items():
        text = text.replace("{{" + klic + "}}", str(hodnota))

    zbyle = sorted(set(re.findall(r"\{\{\w+\}\}", text)))
    if zbyle:
        raise SystemExit(
            f"CHYBA: šablona má kotvy, které generátor neumí vyplnit: {', '.join(zbyle)}")

    hlavicka = (
        "<!-- GENEROVÁNO src/make_deploy_ppf.py — needituj ručně.\n"
        f"     Zdroj textu: {SABLONA.as_posix()}, čísla z balíku {balik.name}. -->\n\n")
    return hlavicka + text


def zkontroluj(text, balik, flow):
    """Brána: README musí sedět na balík, se kterým se předává.

    Počet flow se čte z balíku, ne ze slovníku FLOW — jinak by brána ověřovala
    generátor sama sebou.
    """
    if balik.name not in text:
        raise SystemExit(f"CHYBA: README neuvádí balík {balik.name}")
    for jmeno in flow:
        if f"`{jmeno}`" not in text:
            raise SystemExit(f"CHYBA: README neuvádí flow {jmeno}")
        if FLOW.get(jmeno) is None:
            raise SystemExit(
                f"CHYBA: flow {jmeno} nemá popis ve FLOW v make_deploy_mpsv.py")
    if f"všech **{slovy(len(flow))}** má stav" not in text:
        raise SystemExit(
            f"CHYBA: README nežádá zapnutí {slovy(len(flow))} flow — počet se rozešel")


def main():
    if not (DATA / "model.json").exists():
        raise SystemExit(
            f"CHYBA: {DATA}/model.json neexistuje — spusť src/anonymize.py")

    CIL.mkdir(parents=True, exist_ok=True)
    schema = json.loads(Path("src/schema.json").read_text(encoding="utf-8"))

    # 1) provisioning — týž skript jako pro MPSV, web si odvodí z adresy stránky
    spust([str(PY), "src/make_setup.py"])
    shutil.copy("src/setup_sharepoint.js", CIL / "01_zaloz_listy.js")

    # 2) import ANONYMIZOVANÝCH dat — bez --povolit-realna-data, takže kontrola
    #    anonymity v make_import.py ostrá data odmítne
    spust([str(PY), "src/make_import.py", "--data", str(DATA),
           "--out", str(CIL / "02_import_dat.js")])

    # 3) výpis GUIDů listů (nepovinné, jen kontrola)
    nazvy = [l.get("display") or l["name"] for l in schema["lists"]]
    (CIL / "03_vypis_guidy.js").write_text(
        VYPIS_GUIDU % (json.dumps(nazvy, ensure_ascii=False), len(nazvy), len(nazvy)),
        encoding="utf-8")

    balik = posledni_balik()
    overuj_bez_guidu(balik)
    for stary in CIL.glob("procesnimapa_*.zip"):
        stary.unlink()
    shutil.copy(balik, CIL / balik.name)

    for jmeno in ("sharepoint_schema.md", "navod_sprava.md",
                  "navod_publikace_mapy.md", "TESTOVACI_SCENAR.md"):
        shutil.copy(f"deploy/{jmeno}", CIL / jmeno)
    for kontrakt in sorted(Path("deploy").glob("flow_*.md")):
        shutil.copy(kontrakt, CIL / kontrakt.name)

    assets = CIL / "site_assets"
    shutil.rmtree(assets, ignore_errors=True)
    assets.mkdir()
    for jmeno in ("mapa_template.html", "procesni_mapa.html",
                  "sablona_import_aktivit.xlsx"):
        shutil.copy(f"deploy/{jmeno}", assets / jmeno)

    with zipfile.ZipFile(balik) as zip_balik:
        flow = sorted(n.split("/")[1].rsplit("-", 5)[0]
                      for n in zip_balik.namelist() if n.startswith("Workflows/"))
    obrazovky = len(list(Path("src/app_src").glob("scr_*.pa.yaml")))

    text = readme(balik, flow, obrazovky, schema)
    zkontroluj(text, balik, flow)
    (CIL / "README.md").write_text(text, encoding="utf-8")

    print(f"\nHOTOVO: {CIL}")
    for cesta in sorted(CIL.rglob("*")):
        if cesta.is_file():
            popis = str(cesta.relative_to(CIL)).replace("\\", "/")
            print(f"  {popis:34} {cesta.stat().st_size:>9} B")
    print(f"\nbalík appky: {balik.name} · {len(flow)} flow · {obrazovky} obrazovek "
          f"· {len(ep.DEFINICE)} proměnných")
    print("data: ANONYMIZOVANÁ (runs/anonym) — pro cizí vývojový tenant")
    return 0


if __name__ == "__main__":
    sys.exit(main())
