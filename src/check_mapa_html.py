"""Kontrola šablony mapy a vygenerované stránky bez prohlížeče.

Chytá to, co by jinak odhalil až běh: překlep v id (JS sáhne na prvek, který
v HTML není), osiřelý ovládací prvek, syntaktickou chybu ve skriptu a velikost
písma zapsanou natvrdo v px, kterou by přepínač velikostí nezvětšil.

Spouštět z kořene projektu:  python src/check_mapa_html.py
Návratový kód 0 = v pořádku, 1 = nalezena chyba.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

SABLONA = Path("src/mapa_template.html")
STRANKA = Path("viz/mapa_prototyp.html")

# velikosti, které smějí zůstat v px: přepínač velikostí musí mít stálý rozměr
VYJIMKY_PX = (".fs button",)

chyby = []
kontrol = 0


def overit(podminka, popis):
    global kontrol
    kontrol += 1
    if not podminka:
        chyby.append(popis)


def skript(html):
    m = re.search(r"<script>(.*?)</script>", html, re.S)
    return m.group(1) if m else ""


def main():
    for cesta in (SABLONA, STRANKA):
        if not cesta.exists():
            print(f"CHYBA: chybí {cesta} — spusť nejdřív src/build_mapa.py")
            return 1

    tpl = SABLONA.read_text(encoding="utf-8")
    out = STRANKA.read_text(encoding="utf-8")

    # --- syntaxe skriptu: v šabloně i na hotové stránce ---
    # Šablona je zdroj pravdy, ale má v sobě kotvy — na dobu kontroly se za ně
    # dosadí zástupné hodnoty. Bez toho by chyba zapsaná do šablony prošla až
    # do chvíle, kdy někdo spustí build.
    def syntaxe(kod, kde):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(kod)
            docasny = f.name
        vysledek = subprocess.run(["node", "--check", docasny], capture_output=True, text=True)
        Path(docasny).unlink()
        overit(vysledek.returncode == 0, f"{kde} není platný JS:\n{vysledek.stderr.strip()}")

    syntaxe(skript(tpl).replace("__DATA_JSON__", "{}").replace("__GEN__", '""'),
            "skript šablony")
    syntaxe(skript(out), "skript vygenerované stránky")

    # stránka musí být z aktuální šablony, jinak se kontroluje včerejší výstup
    overit(STRANKA.stat().st_mtime >= SABLONA.stat().st_mtime,
           "viz/mapa_prototyp.html je starší než šablona — spusť src/build_mapa.py")

    # --- id: co JS hledá, musí v HTML být (a naopak) ---
    hledana = set(re.findall(r"getElementById\(\"([^\"]+)\"\)", tpl))
    v_html = set(re.findall(r"\sid=\"([^\"]+)\"", tpl))
    overit(hledana <= v_html, f"JS sahá na neexistující id: {sorted(hledana - v_html)}")
    overit(v_html <= hledana | {"tree", "detail", "detailBody"},
           f"v HTML je ovládací prvek, se kterým JS nepracuje: {sorted(v_html - hledana)}")

    # --- druhé zobrazení: rozkladový diagram (F20) ---
    # Kontroluje se kostra, ne popisky — přejmenování „Rozklad" bránu shodit nemá.
    overit('id="fZobrazeni"' in tpl and 'data-zobrazeni="rozklad"' in tpl,
           "chybí přepínač zobrazení strom/rozklad")
    overit('id="rozklad"' in tpl and 'id="rzSloupce"' in tpl and 'id="rzSpojnice"' in tpl,
           "chybí kontejner rozkladového diagramu, sloupců nebo spojnic")
    overit(tpl.count('class="rz-hlavicky"') == 1 and tpl.count("<div>") >= 4,
           "rozkladový diagram nemá hlavičky čtyř úrovní")
    # Obě zobrazení musí filtrovat týmž kódem, jinak ukážou jiná čísla téhož
    # rejstříku. Že `filtruj` existuje nestačí — musí ji volat oba renderery.
    overit(tpl.count("function filtruj(") == 1,
           "filtrovací funkce není společná (chybí, nebo je definovaná víckrát)")
    for kdo in ("render", "renderRozklad"):
        telo = tpl.split(f"function {kdo}(", 1)[-1].split(chr(10) + "function ", 1)[0]
        overit("filtruj(" in telo,
               f"{kdo}() nefiltruje přes společnou filtruj() — zobrazení se rozejdou")

    # --- ovládací prvky podle zadání F6/A ---
    overit('id="cKod"' in tpl and "bez-kodu" in tpl,
           "chybí zatržítko kódu nebo třída bez-kodu")
    overit('body.bez-kodu .kod{display:none}' in tpl,
           "vypnuté zatržítko kód neskryje — chybí CSS pravidlo")
    overit(tpl.count('id="fUroven"') == 1 and tpl.count("<option") >= 7,
           "chybí přepínač stupně rozbalení")
    overit(len(re.findall(r'data-fs="(\d+)"', tpl)) >= 3,
           "přepínač velikosti písma nemá aspoň tři stupně")
    overit("bExp" not in tpl and "bCol" not in tpl,
           "zůstal zbytek po tlačítkách Rozbalit/Sbalit vše")

    # --- velikost písma smí řídit jediná proměnná ---
    overit("--fs:" in tpl and "html{font-size:var(--fs)}" in tpl,
           "velikost písma neřídí proměnná --fs na html")
    natvrdo = []
    for radek in tpl.splitlines():
        if "font-size:" not in radek or "px" not in radek:
            continue
        if any(v in radek for v in VYJIMKY_PX):
            continue
        if re.search(r"font-size:\s*[\d.]+px", radek):
            natvrdo.append(radek.strip())
    overit(not natvrdo,
           "velikost písma v px mimo přepínač — stupně písma by ji nezvětšily:\n  "
           + "\n  ".join(natvrdo))

    # --- nápověda na řádku ---
    overit("row.title" in tpl and "TYPY" in tpl,
           "řádek stromu nemá nápovědu s typem prvku")
    for typ in ("Agenda", "Proces", "Dílčí proces", "Aktivita"):
        overit(f'"{typ}"' in tpl, f"v nápovědě chybí typ prvku {typ}")

    # --- vrstvy se liší i jinak než barvou písma ---
    for uroven in ("a", "p", "d"):
        overit(f".lvl-{uroven}>.row{{background:" in tpl,
               f"vrstva lvl-{uroven} nemá vlastní podklad řádku")

    # --- localStorage nesmí shodit stránku v náhledu bez úložiště ---
    # každé volání musí mít vlastní try/catch na svém řádku; hledat je v širším
    # okolí nestačí — sousední ošetřené volání by ho zakrylo
    for radek in skript(tpl).splitlines():
        if "localStorage." not in radek:
            continue
        overit("try" in radek and "catch" in radek,
               f"volání localStorage není v try/catch — sandbox bez úložiště shodí "
               f"stránku:\n  {radek.strip()}")

    # --- deploy kopie musí sedět na zdroj ---
    # Do Site Assets se nahrává kopie z runs/build/, takže rozejít se smí leda
    # tiše: appka i mapa vypadají v pořádku a jen se nic nezměnilo. Přesně to
    # se 21.08.2026 stalo.
    dep_tpl = Path("runs/build/mapa_template.html")
    dep_out = Path("runs/build/procesni_mapa.html")
    overit(dep_tpl.exists() and dep_tpl.read_text(encoding="utf-8") == tpl,
           "runs/build/mapa_template.html neodpovídá src/mapa_template.html — "
           "flow bere šablonu ze Site Assets, kam se nahrává tahle kopie")
    overit(dep_out.exists() and "__DATA_JSON__" not in dep_out.read_text(encoding="utf-8"),
           "runs/build/procesni_mapa.html chybí nebo v ní zbyla kotva")
    for prvek in ('id="cKod"', 'id="fUroven"', 'id="fVelikost"'):
        overit(prvek in dep_out.read_text(encoding="utf-8"),
               f"runs/build/procesni_mapa.html je zastaralá — chybí {prvek}")

    # --- hotová stránka: kotvy pryč, ovládání uvnitř ---
    overit("__DATA_JSON__" not in out and "__GEN__" not in out,
           "ve vygenerované stránce zbyla kotva")
    for prvek in ('id="cKod"', 'id="fUroven"', 'id="fVelikost"'):
        overit(prvek in out, f"ve vygenerované stránce chybí {prvek}")

    print(f"kontrol: {kontrol}, chyb: {len(chyby)}")
    if chyby:
        for c in chyby:
            print("CHYBA:", c)
        print("\nNEPROŠLO")
        return 1
    print("\nOK — šablona i vygenerovaná stránka odpovídají zadání")
    return 0


if __name__ == "__main__":
    sys.exit(main())
