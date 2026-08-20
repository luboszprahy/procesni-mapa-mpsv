"""Vloží zdroje z src/app_src/ do exportované solution a vyrobí zip k importu.

Postup: rozbalí vstupní solution -> pac canvas unpack (layout SourceCode) ->
vymění Src/*.pa.yaml za naše -> pac canvas pack -> složí solution zpět.

Spouštět z kořene projektu:
    python src/build_app.py
    python src/build_app.py --verze 1.0.0.3

Cesta k pac.exe: přepínač --pac nebo proměnná PAC_EXE. Bez ní se hledá
v rozšíření Power Platform Tools ve VS Code.
"""

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

APP_SRC = Path("src/app_src")
VYCHOZI_SOLUTION = Path("input/procesnimapa_1_0_0_1.zip")
VYSTUP = Path("deploy")
PRACOVNI = Path("runs/app_build")
SABLONY = Path("src/control_templates.json")

OBRAZOVKY = ["scr_Seznam", "scr_Detail", "scr_Vazby"]




def najdi_pac(zadana):
    if zadana:
        return Path(zadana)
    if os.environ.get("PAC_EXE"):
        return Path(os.environ["PAC_EXE"])

    # rozšíření VS Code dodává pac jako nupkg; rozbalený bývá vedle něj
    koren = Path.home() / ".vscode" / "extensions"
    for kandidat in sorted(koren.glob("microsoft-isvexptools.powerplatform-vscode-*/dist/pac/tools/pac.exe")):
        return kandidat
    for kandidat in sorted(koren.glob("microsoft-isvexptools.powerplatform-vscode-*/dist/pac/*.nupkg")):
        cil = PRACOVNI / "pac"
        if not (cil / "tools" / "pac.exe").exists():
            cil.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(kandidat) as balik:
                balik.extractall(cil)
        return cil / "tools" / "pac.exe"
    return None


def spust(prikaz):
    vysledek = subprocess.run(prikaz, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if vysledek.returncode != 0:
        print(vysledek.stdout)
        print(vysledek.stderr, file=sys.stderr)
        raise SystemExit(f"CHYBA: selhalo {prikaz[0]} {prikaz[1] if len(prikaz) > 1 else ''}")
    return vysledek.stdout


def rozbal(zdroj, cil):
    """Rozbalí zip; msapp/solution používají zpětná lomítka, unzip by je nezvládl."""
    cil.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zdroj) as balik:
        for polozka in balik.namelist():
            cesta = cil / polozka.replace("\\", "/")
            cesta.parent.mkdir(parents=True, exist_ok=True)
            if not polozka.endswith("/"):
                cesta.write_bytes(balik.read(polozka))


def zabal(adresar, cil):
    with zipfile.ZipFile(cil, "w", zipfile.ZIP_DEFLATED) as balik:
        for cesta in sorted(adresar.rglob("*")):
            if cesta.is_file():
                balik.write(cesta, cesta.relative_to(adresar).as_posix())


def doplnit_sablony(cesta_msapp):
    """Doplní do balíku definice controlů, které původní appka neobsahovala.

    Prázdná appka ze Studia nese v References/Templates.json jen šablony, které
    sama používala. Studio pak odmítne otevřít appku s controlem, jehož definici
    nezná, a ohlásí to jako chybu YAML. Definice jsou nezávislé na tenantu
    (ověřeno shodou sdílených šablon), takže je stačí přiložit.
    """
    data = json.loads(Path(SABLONY).read_text(encoding="utf-8"))
    zasoba = {s["Name"]: s for s in data["sablony"]}
    typy = data["typy"]

    with zipfile.ZipFile(cesta_msapp) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klic = next(n for n in polozky if n.replace("\\", "/").endswith("References/Templates.json"))
    templates = json.loads(polozky[klic].decode("utf-8-sig"))
    pritomne = {s["Name"] for s in templates["UsedTemplates"]}

    potreba = set()
    for jmeno, obsah in polozky.items():
        if jmeno.replace("\\", "/").endswith(".pa.yaml"):
            for control in re.findall(r"Control:\s*(\S+)", obsah.decode("utf-8-sig")):
                if control not in typy:
                    raise SystemExit(f"CHYBA: neznámý typ controlu '{control}' — doplň ho do {SABLONY}")
                potreba.add(typy[control])

    chybi = sorted(potreba - pritomne)
    nemam = [s for s in chybi if s not in zasoba]
    if nemam:
        raise SystemExit(f"CHYBA: pro šablony {nemam} nemám definici v {SABLONY}")

    doplnene = []
    for sablona in chybi:
        templates["UsedTemplates"].append(zasoba[sablona])
        doplnene.append(f"{sablona}@{zasoba[sablona]['Version']}")

    if not doplnene:
        return []

    polozky[klic] = json.dumps(templates, ensure_ascii=False).encode("utf-8")
    with zipfile.ZipFile(cesta_msapp, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)
    return doplnene


def vymen_zdroje_bez_pac(cesta_msapp):
    """Vymění Src/*.pa.yaml přímo v .msapp, bez pac.

    Balík zabalený z YAML má v packed.json LoadFromYaml=true, takže Studio čte
    Src/*.pa.yaml a Controls/*.json si dogeneruje samo — výměna zdrojů je pak
    obyčejná úprava zipu. Na stroji bez pac je to jediná cesta, jak vydat opravu.
    Nefunguje na balíku exportovaném ze Studia (ten YAML nenese).
    """
    with zipfile.ZipFile(cesta_msapp) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    def klic_koncici(pripona):
        nalezene = [n for n in polozky if n.replace("\\", "/").endswith(pripona)]
        if len(nalezene) != 1:
            raise SystemExit(f"CHYBA: v .msapp není právě jeden {pripona} (nalezeno {len(nalezene)})")
        return nalezene[0]

    packed = json.loads(polozky[klic_koncici("packed.json")].decode("utf-8-sig"))
    if packed.get("LoadConfiguration", {}).get("LoadFromYaml") is not True:
        raise SystemExit(
            "CHYBA: balík nemá LoadFromYaml=true — Studio by četlo Controls/*.json,\n"
            "       ne vyměněné YAML. Bez pac se dá upravit jen balík už zabalený z YAML."
        )

    for nazev in ["App"] + OBRAZOVKY:
        polozky[klic_koncici(f"Src/{nazev}.pa.yaml")] = (APP_SRC / f"{nazev}.pa.yaml").read_bytes()

    stav = polozky[klic_koncici("Src/_EditorState.pa.yaml")].decode("utf-8-sig")
    for obrazovka in OBRAZOVKY:
        if obrazovka not in stav:
            raise SystemExit(f"CHYBA: _EditorState neuvádí obrazovku {obrazovka}")

    with zipfile.ZipFile(cesta_msapp, "w", zipfile.ZIP_DEFLATED) as balik:
        for jmeno, data in polozky.items():
            balik.writestr(jmeno, data)
    return len(OBRAZOVKY) + 1


def dokonci(solution_dir, verze):
    """Přepíše verzi v manifestu a složí solution zip."""
    manifest = solution_dir / "solution.xml"
    text = manifest.read_text(encoding="utf-8-sig")
    novy, pocet = re.subn(r"<Version>[^<]+</Version>", f"<Version>{verze}</Version>", text, count=1)
    if pocet != 1:
        raise SystemExit("CHYBA: verzi v solution.xml se nepodařilo přepsat")
    manifest.write_text(novy, encoding="utf-8")

    VYSTUP.mkdir(parents=True, exist_ok=True)
    vystupni_zip = VYSTUP / f"procesnimapa_{verze.replace('.', '_')}.zip"
    zabal(solution_dir, vystupni_zip)

    print(f"\nHOTOVO: {vystupni_zip}  ({vystupni_zip.stat().st_size} B), verze {verze}")
    print("Import: Power Apps > Solutions > Import solution (upgrade). Po importu appku")
    print("jednou otevřít v Power Apps Studiu — z YAML zabalená appka se validuje až tam.")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", default=str(VYCHOZI_SOLUTION), help="vstupní solution zip z Power Apps")
    parser.add_argument("--verze", default="1.0.0.2", help="verze výsledné solution")
    parser.add_argument("--pac", default=None, help="cesta k pac.exe")
    parser.add_argument("--bez-pac", action="store_true",
                        help="vyměnit YAML přímo v už zabaleném balíku (stroj bez pac)")
    argumenty = parser.parse_args()

    vstupni_zip = Path(argumenty.solution)
    if not vstupni_zip.exists():
        raise SystemExit(f"CHYBA: solution {vstupni_zip} neexistuje")

    pac = None
    if not argumenty.bez_pac:
        pac = najdi_pac(argumenty.pac)
        if pac is None or not pac.exists():
            raise SystemExit(
                "CHYBA: pac.exe nenalezen. Nainstaluj rozšíření Power Platform Tools do VS Code\n"
                "       (code --install-extension microsoft-IsvExpTools.powerplatform-vscode)\n"
                "       nebo předej cestu přes --pac / PAC_EXE.\n"
                "       Máš-li balík už zabalený z YAML, jde použít --bez-pac."
            )
        print(f"pac: {pac}")

    if PRACOVNI.exists():
        for polozka in PRACOVNI.iterdir():
            if polozka.name != "pac":
                shutil.rmtree(polozka) if polozka.is_dir() else polozka.unlink()
    PRACOVNI.mkdir(parents=True, exist_ok=True)

    solution_dir = PRACOVNI / "solution"
    rozbal(vstupni_zip, solution_dir)

    msappy = list((solution_dir / "CanvasApps").glob("*.msapp"))
    if len(msappy) != 1:
        raise SystemExit(f"CHYBA: čekal jsem právě jeden .msapp, našel {len(msappy)}")
    msapp = msappy[0]
    print(f"canvas app: {msapp.name}")

    if argumenty.bez_pac:
        vlozeno = vymen_zdroje_bez_pac(msapp)
        print(f"vloženo zdrojů (bez pac): {vlozeno}")
        doplneno = doplnit_sablony(msapp)
        if doplneno:
            print(f"doplněné šablony controlů: {', '.join(doplneno)}")
        return dokonci(solution_dir, argumenty.verze)

    zdroje = PRACOVNI / "sources"
    spust([str(pac), "canvas", "unpack", "--msapp", str(msapp),
           "--sources", str(zdroje), "--layout", "SourceCode"])

    src_dir = zdroje / "Src"
    for stara in src_dir.glob("*.pa.yaml"):
        if stara.name != "_EditorState.pa.yaml":
            stara.unlink()

    for nazev in ["App"] + OBRAZOVKY:
        shutil.copy(APP_SRC / f"{nazev}.pa.yaml", src_dir / f"{nazev}.pa.yaml")
    print(f"vloženo zdrojů: {len(OBRAZOVKY) + 1}")

    stav = src_dir / "_EditorState.pa.yaml"
    text = stav.read_text(encoding="utf-8-sig")
    poradi = "  ScreensOrder:\n" + "".join(f"    - {o}\n" for o in OBRAZOVKY)
    novy, pocet = re.subn(r"  ScreensOrder:\n(?:    - .*\n)+", poradi, text)
    if pocet != 1:
        raise SystemExit(f"CHYBA: ScreensOrder nahrazen {pocet}x, čekal jsem 1x")
    stav.write_text(novy, encoding="utf-8")

    novy_msapp = PRACOVNI / "app.msapp"
    vystup_pac = spust([str(pac), "canvas", "pack", "--sources", str(zdroje), "--msapp", str(novy_msapp)])
    print(vystup_pac.strip().splitlines()[-1])

    doplneno = doplnit_sablony(novy_msapp)
    if doplneno:
        print(f"doplněné šablony controlů: {', '.join(doplneno)}")

    shutil.copy(novy_msapp, msapp)

    return dokonci(solution_dir, argumenty.verze)


if __name__ == "__main__":
    sys.exit(main())
