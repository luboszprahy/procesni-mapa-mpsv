# -*- coding: utf-8 -*-
"""Brána nad PresunFlow — kaskádový přesun procesu a dílčího procesu.

Dvě vrstvy, jako u ostatních flow v projektu:

1. **tvar** — kroky, jejich pořadí, režimy, zápis přes REST, stránkování;
2. **význam** — výrazy se **vytáhnou z balíku** a pustí mini-interpretem nad
   vzorovým rejstříkem. Neporovnává se s kopií logiky v Pythonu: kdyby se
   generátor a brána počítaly stejnou chybou, obojí by souhlasilo. Porovnává
   se se seznamem dvojic starý → nový kód napsaným **ručně**.

Vzorový rejstřík je zvolený tak, aby chytil to, co se dá snadno pokazit:

  - v cílové agendě `03` existují živé procesy `03-01`..`03-04`,
  - a v historii je **uzavřený** `03-05`.

Správná odpověď je proto `03-06`. Kdyby se historie do výpočtu nezapočítala,
vyjde `03-05` — tedy recyklovaný kód, což je přesně to, co varianta C zakazuje
(pravidlo F10/1). Historie zároveň obsahuje `03-05-002`, tedy uzavřený DÍLČÍ
proces pod týmž prefixem, a to s vysokým posledním segmentem: do maxima
procesů se započítat nesmí, a kdyby se započetl, vyjde 100 místo 6.

Vazby vzorku obsahují obě křížové situace, na které se zapomíná:
cizí aktivitu zařazenou dovnitř přesouvané větve (kód se jí nemění, ale vazba
musí ukázat na nový dílčí proces) a naši aktivitu zařazenou ven (kód se mění,
cizí dílčí proces zůstává).

    python src/check_presun_flow.py --solution deploy/procesnimapa_1_0_0_93.zip
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402
from build_presun_flow import FLOW, FLOW_GUID, REZIM_NAHLED, REZIM_ZAPIS  # noqa: E402
from build_restore_flow import ODD_POLE, ODD_RADKU, STRANKOVANI  # noqa: E402
from check_export_flow import Chyba, spust  # noqa: E402

kontrol = 0
chyby = []


def overit(podminka, popis):
    global kontrol
    kontrol += 1
    if not podminka:
        chyby.append(popis)


# ------------------------------------------------------------- vzorový rejstřík

def proces(kod, nazev, agenda, ident):
    return {"ID": ident, "Title": kod, "nazev": nazev,
            "agenda_kod": agenda, "vlastnik": "72"}


def dilci(kod, nazev, rodic, ident):
    return {"ID": ident, "Title": kod, "nazev": nazev,
            "proces_kod": rodic, "vlastnik": "721"}


def aktivita(kod, nazev, dp, ident):
    return {"ID": ident, "Title": kod, "nazev": nazev + " — úplné znění",
            "nazev_kratky": nazev, "dilci_proces_kod": dp, "vykonava": "7211",
            "spolupracuje": "7212", "vnitrni_predpis": "SM 12/2026",
            "text_pro_or": "Text pro organizační řád.", "sekce": "7",
            "stav": {"Value": "pracovní"}}


def vazba(akt, dp, primarni, ident):
    return {"ID": ident, "Title": f"{akt}__{dp}", "aktivita_kod": akt,
            "dilci_proces_kod": dp, "primarni": {"Value": primarni}}


PROCESY = [
    proces("03-01", "Cizí jedna", "03", 11),
    proces("03-02", "Cizí dvě", "03", 12),
    proces("03-03", "Cizí tři", "03", 13),
    proces("03-04", "Cizí čtyři", "03", 14),
    proces("07-08", "Řízení kvality", "07", 20),
]
DILCI = [
    dilci("07-08-001", "Plánování", "07-08", 31),
    dilci("07-08-002", "Provádění", "07-08", 32),
    dilci("07-08-003", "Vyhodnocení", "07-08", 33),
    dilci("03-01-001", "Cizí dílčí", "03-01", 34),
]
AKTIVITY = [
    aktivita("07-08-001-0001", "Sestavuje plán", "07-08-001", 41),
    aktivita("07-08-001-0002", "Schvaluje plán", "07-08-001", 42),
    aktivita("07-08-001-0003", "Zveřejňuje plán", "07-08-001", 43),
    aktivita("07-08-002-0001", "Provádí kontrolu", "07-08-002", 44),
    aktivita("07-08-002-0002", "Zaznamenává zjištění", "07-08-002", 45),
    aktivita("07-08-003-0001", "Vyhodnocuje", "07-08-003", 46),
    aktivita("07-08-003-0002", "Reportuje", "07-08-003", 47),
    aktivita("03-01-001-0001", "Cizí aktivita", "03-01-001", 48),
]
VAZBY = [vazba(a["Title"], a["dilci_proces_kod"], "ano", 50 + i)
         for i, a in enumerate(AKTIVITY)]
# Cizí aktivita zařazená DOVNITŘ přesouvané větve — kód se jí nemění,
# ale vazba musí po přesunu ukazovat na nový dílčí proces.
VAZBY.append(vazba("03-01-001-0001", "07-08-002", "ne", 60))
# Naše aktivita zařazená VEN — kód se mění, cizí dílčí proces zůstává.
VAZBY.append(vazba("07-08-003-0002", "03-01-001", "ne", 61))
HISTORIE = [
    {"ID": 71, "Title": "03-05", "nazev": "Zrušený proces", "nastupce_kod": ""},
    # Uzavřený DÍLČÍ proces pod týmž prefixem. Do maxima procesů se započítat
    # nesmí — kdyby ano, vyšlo by číslo podle jeho posledního segmentu.
    # Poslední segment je schválně VYSOKÝ: kdyby filtr na počet segmentů
    # chyběl, vyšlo by nové číslo 100 místo 6 a bylo by to hned vidět.
    # S nízkým číslem by se chyba schovala za maximum ze živých procesů.
    {"ID": 72, "Title": "03-05-099", "nazev": "Zrušený dílčí", "nastupce_kod": ""},
]

# Ručně napsaná očekávaná mapa. Tohle je ten skutečný test — kdyby se
# přepisovala z výstupu generátoru, netestovala by nic.
OCEKAVANA_MAPA_PROCES = [
    ("07-08", "03-06", "proces"),
    ("07-08-001", "03-06-001", "dilci_proces"),
    ("07-08-002", "03-06-002", "dilci_proces"),
    ("07-08-003", "03-06-003", "dilci_proces"),
    ("07-08-001-0001", "03-06-001-0001", "aktivita"),
    ("07-08-001-0002", "03-06-001-0002", "aktivita"),
    ("07-08-001-0003", "03-06-001-0003", "aktivita"),
    ("07-08-002-0001", "03-06-002-0001", "aktivita"),
    ("07-08-002-0002", "03-06-002-0002", "aktivita"),
    ("07-08-003-0001", "03-06-003-0001", "aktivita"),
    ("07-08-003-0002", "03-06-003-0002", "aktivita"),
]

# Přesun dílčího procesu 07-08-002 pod proces 03-01, kde je živý 03-01-001
# a v historii nic → první volné je 002.
OCEKAVANA_MAPA_DILCI = [
    ("07-08-002", "03-01-002", "dilci_proces"),
    ("07-08-002-0001", "03-01-002-0001", "aktivita"),
    ("07-08-002-0002", "03-01-002-0002", "aktivita"),
]

WEB = "https://tenant.sharepoint.com/sites/DigiData_D/procesnimapa"


# ------------------------------------------------------------------- runner

def kontext_pro(vstup):
    return {
        "item": None,
        "triggerBody": {"text": json.dumps(vstup, ensure_ascii=False)},
        "parametry": {ep.WEB: WEB},
        "akce": {
            "Nacti_Procesy": {"body/value": PROCESY},
            "Nacti_DilciProcesy": {"body/value": DILCI},
            "Nacti_Aktivity": {"body/value": AKTIVITY},
            "Nacti_Vazby": {"body/value": VAZBY},
            "Nacti_Historie": {"body/value": HISTORIE},
        },
    }


# Kroky, které runner umí spočítat. Zápisové akce a podmínky se nespouštějí —
# ty ověřuje vrstva tvaru.
POCITANE = ("Compose", "Query", "Select")


def spust_kroky(akce, kontext, jmena):
    """Projde vyjmenované kroky v daném pořadí a uloží jejich výstupy.

    `body('X')` i `outputs('X')` míří v interpretu do téhož slovníku, což
    odpovídá tomu, jak se ty dvě funkce u Compose/Query/Select chovají.
    """
    for jmeno in jmena:
        krok = akce[jmeno]
        typ = krok["type"]
        if typ not in POCITANE:
            raise Chyba(f"krok {jmeno} je {typ}, ten runner nepočítá")
        if typ == "Compose":
            kontext["akce"][jmeno] = spust(krok["inputs"], kontext)
            continue
        zdroj = spust(krok["inputs"]["from"], kontext)
        if typ == "Query":
            vysledek = []
            for prvek in zdroj:
                dilci_kontext = dict(kontext, item=prvek)
                if spust(krok["inputs"]["where"], dilci_kontext):
                    vysledek.append(prvek)
        else:
            vyber = krok["inputs"]["select"]
            vysledek = []
            for prvek in zdroj:
                dilci_kontext = dict(kontext, item=prvek)
                if isinstance(vyber, dict):
                    vysledek.append({k: spust(v, dilci_kontext)
                                     for k, v in vyber.items()})
                else:
                    vysledek.append(spust(vyber, dilci_kontext))
        kontext["akce"][jmeno] = vysledek


KROKY_VYPOCTU = ["Vstup", "Sourozenci", "Cisla_ziva", "Uzavrene",
                 "Cisla_uzavrena", "Nove_cislo", "Novy_prefix",
                 "Vlastni", "Deti", "Vnuci", "Vazby_dotcene", "Mapa",
                 "Prehled_radky", "Prehled"]


def spocitej(akce, vstup):
    kontext = kontext_pro(vstup)
    spust_kroky(akce, kontext, KROKY_VYPOCTU)
    return kontext["akce"]


# -------------------------------------------------------------------- tvar

OCEKAVANE_KROKY = (
    "Vstup", "Cesta_webu",
    "Nacti_Procesy", "Nacti_DilciProcesy", "Nacti_Aktivity", "Nacti_Vazby",
    "Nacti_Historie",
    "Sourozenci", "Cisla_ziva", "Uzavrene", "Cisla_uzavrena", "Nove_cislo",
    "Novy_prefix", "Kontrola_mista",
    "Vlastni", "Deti", "Vnuci", "Vazby_dotcene", "Mapa",
    "Prehled_radky", "Prehled", "Je_nahled",
    "Zaloz_proces", "Mapa_dilci", "Zaloz_dilci", "Zaloz_aktivity",
    "Zaloz_vazby", "Zapis_historii",
    "Smaz_vazby", "Smaz_aktivity", "Smaz_deti", "Smaz_vlastni", "Odpoved",
)

# Zápis MUSÍ jít v tomhle pořadí. Kdyby se mazalo dřív, než je založeno,
# výpadek uprostřed smaže větev, která nikde jinde neexistuje.
PORADI_ZAPISU = ["Zaloz_proces", "Mapa_dilci", "Zaloz_dilci", "Zaloz_aktivity",
                 "Zaloz_vazby", "Zapis_historii",
                 "Smaz_vazby", "Smaz_aktivity", "Smaz_deti", "Smaz_vlastni"]

MAZACI = ("Smaz_vazby", "Smaz_aktivity", "Smaz_deti", "Smaz_vlastni")


def kontrola_tvaru(flow, akce):
    definice = flow["properties"]["definition"]
    overit(definice.get("contentVersion") == "1.0.0.0",
           "contentVersion musí být 1.0.0.0 — s jinou hodnotou import projde, "
           "ale flow pak nejde otevřít v designeru")

    spousteni = definice.get("triggers", {})
    overit(list(spousteni) == ["manual"], f"čekám jediný trigger 'manual', je {list(spousteni)}")
    manual = spousteni.get("manual", {})
    overit(manual.get("kind") == "PowerAppV2",
           "trigger musí být PowerAppV2, jinak ho appka nezavolá")
    vlastnosti = (manual.get("inputs", {}).get("schema", {})
                  .get("properties", {}))
    overit(list(vlastnosti) == ["text"],
           f"trigger má mít jediný textový vstup, má {list(vlastnosti)}")

    for jmeno in OCEKAVANE_KROKY:
        overit(jmeno in akce, f"chybí krok {jmeno}")
    prebyva = set(akce) - set(OCEKAVANE_KROKY)
    overit(not prebyva, f"flow má kroky navíc: {sorted(prebyva)}")

    for jmeno, po in zip(PORADI_ZAPISU[1:], PORADI_ZAPISU[:-1]):
        if jmeno not in akce:
            continue
        overit(list(akce[jmeno].get("runAfter", {})) == [po],
               f"{jmeno} musí běžet až po {po} — pořadí vzniku, historie "
               f"a zániku je to jediné, co brání ztrátě dat při výpadku")

    # Načítání: bez pagination vrátí konektor jen prvních 100 položek a přesun
    # by tiše minul většinu podstromu — nic by nespadlo.
    for jmeno, zobrazovany in (("Nacti_Procesy", "Procesy"),
                               ("Nacti_DilciProcesy", "Dílčí procesy"),
                               ("Nacti_Aktivity", "Aktivity"),
                               ("Nacti_Vazby", "Vazba aktivita–dílčí proces"),
                               ("Nacti_Historie", "Historie kódů")):
        if jmeno not in akce:
            continue
        parametry = akce[jmeno]["inputs"]["parameters"]
        overit(akce[jmeno]["inputs"]["host"]["operationId"] == "GetItems",
               f"{jmeno}: čekám GetItems")
        overit(parametry.get("$top", 0) >= STRANKOVANI,
               f"{jmeno}: $top musí být aspoň {STRANKOVANI}")
        overit((akce[jmeno].get("runtimeConfiguration", {})
                .get("paginationPolicy", {}).get("minimumItemCount", 0)) >= STRANKOVANI,
               f"{jmeno}: bez pagination načte konektor jen 100 položek a "
               "přesun tiše mine většinu podstromu")
        overit(parametry.get("table") == ep.list_param(zobrazovany),
               f"{jmeno}: table nebere list z proměnné prostředí")

    # Zápis jde přes REST, ne přes konektorové zápisové akce: ty vyžadují
    # `table` jako GUID natvrdo a flow by pak nešlo zapnout.
    for jmeno, krok in akce.items():
        for vnorena in (krok.get("actions") or {}).values():
            host = (vnorena.get("inputs") or {}).get("host") or {}
            if not host:
                continue
            overit(host.get("operationId") == "HttpRequest",
                   f"{jmeno}: zápis přes {host.get('operationId')} — musí to být "
                   "HttpRequest (REST), jinak flow nepůjde zapnout")

    for jmeno in MAZACI:
        if jmeno not in akce:
            continue
        vnorene = list((akce[jmeno].get("actions") or {}).values())
        overit(len(vnorene) == 1, f"{jmeno}: čekám jedinou vnořenou akci")
        if not vnorene:
            continue
        parametry = vnorene[0]["inputs"]["parameters"]
        overit(parametry.get("parameters/headers", {}).get("X-HTTP-Method") == "DELETE",
               f"{jmeno}: mazání musí mít hlavičku X-HTTP-Method: DELETE")
        overit("['ID']" in str(parametry.get("parameters/uri", "")),
               f"{jmeno}: maže se podle ID z načteného listu, ne podle kódu — "
               "pod tím kódem už může být nový záznam z tohoto běhu")

    # Náhled nesmí propadnout do zápisu.
    vetev = (akce.get("Je_nahled") or {}).get("actions") or {}
    overit("Konec_nahledu" in vetev,
           "Je_nahled: po odpovědi musí následovat Terminate, jinak náhled "
           "propadne do zápisu a přesune, co měl jen ukázat")
    overit(any(a.get("type") == "Terminate" for a in vetev.values()),
           "Je_nahled: chybí Terminate")

    for jmeno in ("Odpoved", "Odpoved_nahled", "Odpoved_plno"):
        krok = akce.get(jmeno) or vetev.get(jmeno) or (
            (akce.get("Kontrola_mista") or {}).get("actions") or {}).get(jmeno)
        if krok is None:
            overit(False, f"chybí odpověď {jmeno}")
            continue
        telo = krok["inputs"]["body"]
        overit(sorted(telo) == ["hlaseni", "porizeno", "prehled", "stav"],
               f"{jmeno}: odpověď musí mít právě čtyři pole, má {sorted(telo)}")
        schema = krok["inputs"]["schema"]["properties"]
        overit(all(v.get("type") == "string" for v in schema.values()),
               f"{jmeno}: všechna pole odpovědi musí být string — appka má "
               "dynamicschema false a rozebírá je Splitem")


# ------------------------------------------------------------------ význam

def kontrola_vyznamu(akce):
    vstup = {"kod": "07-08", "uroven": "proces", "cil": "03",
             "duvod": "organizační změna", "rezim": REZIM_NAHLED}
    try:
        vysledky = spocitej(akce, vstup)
    except Chyba as chyba:
        overit(False, f"výpočet přesunu procesu selhal: {chyba}")
        return

    overit(vysledky["Nove_cislo"] == 6,
           f"nové číslo je {vysledky['Nove_cislo']}, čekám 6 — v agendě 03 jsou "
           "živé procesy do 03-04 a v historii uzavřený 03-05, takže první "
           "volné je 06; kdyby vyšlo 5, historie se do maxima nezapočítává")
    overit(vysledky["Novy_prefix"] == "03-06",
           f"nový prefix je {vysledky['Novy_prefix']!r}, čekám '03-06'")

    mapa = [(r["stary"], r["novy"], r["uroven"]) for r in vysledky["Mapa"]]
    overit(sorted(mapa) == sorted(OCEKAVANA_MAPA_PROCES),
           f"mapa přesunu nesedí:\n  je:    {sorted(mapa)}\n"
           f"  čekám: {sorted(OCEKAVANA_MAPA_PROCES)}")

    # Vazby: obě křížové situace musí být v dotčených, cizí vazba mimo větev ne.
    dotcene = {(v["aktivita_kod"], v["dilci_proces_kod"])
               for v in vysledky["Vazby_dotcene"]}
    overit(("03-01-001-0001", "07-08-002") in dotcene,
           "cizí aktivita zařazená dovnitř přesouvané větve mezi dotčenými "
           "vazbami chybí — po přesunu by ukazovala na dílčí proces, který "
           "už neexistuje")
    overit(("07-08-003-0002", "03-01-001") in dotcene,
           "naše aktivita zařazená ven mezi dotčenými vazbami chybí — "
           "vedlejší zařazení by se přesunem ztratilo")
    overit(("03-01-001-0001", "03-01-001") not in dotcene,
           "vazba zcela mimo přesouvanou větev se považuje za dotčenou — "
           "přesun by přepsal něco, čeho se netýká")

    radky = vysledky["Prehled"].split(ODD_RADKU)
    overit(len(radky) == len(OCEKAVANA_MAPA_PROCES),
           f"přehled má {len(radky)} řádků, čekám {len(OCEKAVANA_MAPA_PROCES)}")
    overit(all(len(r.split(ODD_POLE)) == 4 for r in radky),
           "každý řádek přehledu musí mít čtyři pole oddělená " + ODD_POLE)

    # Táž kaskáda o úroveň níž. Ověřuje, že filtry nejsou napsané jen pro
    # proces — `Deti` musí u dílčího procesu vrátit prázdno a `Vnuci` pořád
    # najít jeho aktivity.
    vstup_dp = {"kod": "07-08-002", "uroven": "dilci_proces", "cil": "03-01",
                "duvod": "organizační změna", "rezim": REZIM_NAHLED}
    try:
        vysledky_dp = spocitej(akce, vstup_dp)
    except Chyba as chyba:
        overit(False, f"výpočet přesunu dílčího procesu selhal: {chyba}")
        return
    overit(vysledky_dp["Novy_prefix"] == "03-01-002",
           f"prefix dílčího procesu je {vysledky_dp['Novy_prefix']!r}, "
           "čekám '03-01-002'")
    overit(vysledky_dp["Deti"] == [],
           "u přesunu dílčího procesu nesmí krok Deti vrátit nic — jinak by "
           "kaskáda přečíslovala cizí dílčí procesy")
    mapa_dp = [(r["stary"], r["novy"], r["uroven"]) for r in vysledky_dp["Mapa"]]
    overit(sorted(mapa_dp) == sorted(OCEKAVANA_MAPA_DILCI),
           f"mapa přesunu dílčího procesu nesedí:\n  je:    {sorted(mapa_dp)}\n"
           f"  čekám: {sorted(OCEKAVANA_MAPA_DILCI)}")

    # Došlá čísla: v agendě, kde je proces 99, se musí přesun odmítnout.
    globals()["PROCESY"] = PROCESY + [proces("09-99", "Poslední", "09", 99)]
    vstup_plno = dict(vstup, cil="09")
    try:
        vysledky_plno = spocitej(akce, vstup_plno)
        overit(vysledky_plno["Nove_cislo"] == 100,
               f"pod plnou agendou vyšlo {vysledky_plno['Nove_cislo']}, čekám 100 "
               "— kontrola místa se pak spustí a přesun odmítne")
    except Chyba as chyba:
        overit(False, f"výpočet nad plnou agendou selhal: {chyba}")
    finally:
        globals()["PROCESY"] = [p for p in PROCESY if p["Title"] != "09-99"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True)
    argumenty = parser.parse_args()

    cesta = Path(argumenty.solution)
    if not cesta.exists():
        raise SystemExit(f"CHYBA: solution {cesta} neexistuje")
    with zipfile.ZipFile(cesta) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}

    klice = [n for n in polozky
             if n.replace("\\", "/").startswith(f"Workflows/{FLOW}")]
    overit(len(klice) == 1, f"čekám právě jedno {FLOW}, je jich {len(klice)}")
    if not klice:
        vypis()
        return 1
    overit(FLOW_GUID.upper() in klice[0].upper(),
           f"GUID flow se změnil — import by nebyl upgrade, ale nové flow, "
           f"a v prostředí by zůstal sirotek blokující další importy")

    flow = json.loads(polozky[klice[0]].decode("utf-8-sig"))
    akce = flow["properties"]["definition"]["actions"]

    kontrola_tvaru(flow, akce)
    kontrola_vyznamu(akce)

    # Deklarace parametru webu doplňuje build_app.py; bez ní flow spadne
    # za běhu na InvalidTemplate a appka uvidí jen 502 BadGateway.
    parametry = flow["properties"]["definition"].get("parameters", {})
    overit(any(ep.WEB in jmeno for jmeno in parametry),
           f"flow nedeklaruje parametr webu ({ep.WEB}) — za běhu "
           "spadne na InvalidTemplate a appka uvidí jen 502 BadGateway")

    vypis()
    return 1 if chyby else 0


def vypis():
    print(f"kontrol: {kontrol}")
    for chyba in chyby:
        print(f"CHYBA: {chyba}")
    print("NEPROŠLO" if chyby else
          f"OK — {FLOW} počítá kaskádu podle pravidla F10/1 "
          f"(režimy {REZIM_NAHLED} | {REZIM_ZAPIS})")


if __name__ == "__main__":
    sys.exit(main())
