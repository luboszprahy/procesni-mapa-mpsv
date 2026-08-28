# -*- coding: utf-8 -*-
"""Kontrola flow MapaPublishFlow v hotovém solution zipu.

Tři vrstvy:
1. struktura — trigger beze změny, spojení, řetěz runAfter, viditelnost odkazů,
2. kontrakt — každý Select mapuje na klíče, které šablona čeká; Choice sloupce
   mají ?['Value']; každý Get items má zapnuté stránkování,
3. význam — výraz akce Stranka se **vytáhne z balíku**, vyhodnotí nad skutečnou
   šablonou a vzorovými daty a výsledek projde stejným sítem jako build_mapa.py.
   Testuje se tím to, co se opravdu nasazuje, ne kopie logiky v Pythonu.

Spouštět z kořene projektu:
    python src/check_mapa_flow.py --solution deploy/procesnimapa_1_0_0_20.zip
"""

import argparse
import io
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402
from build_mapa_flow import LISTY  # noqa: E402

# název kroku ve flow -> zobrazovaný název listu, podle kterého se hledá proměnná
KROK_LIST = {krok: zobrazovany for zobrazovany, krok, _ in LISTY}

SABLONA = Path("src/mapa_template.html")
MODEL = Path("runs/anonym/model.json")
KOTVY = ("__DATA_JSON__", "__GEN__")
KLICE_MODELU = ("agendy", "procesy", "dilci_procesy", "aktivity", "vazby")

# Klíče, které šablona z dat opravdu čte. Kdyby Select některý vynechal,
# strom se postaví prázdný a nic nespadne.
OCEKAVANE_KLICE = {
    "Map_Agendy": {"kod", "nazev", "vlastnik"},
    "Map_Procesy": {"kod", "nazev", "agenda_kod", "vlastnik"},
    "Map_DilciProcesy": {"kod", "nazev", "proces_kod", "vlastnik"},
    "Map_Aktivity": {"kod", "nazev", "dilci_proces_kod", "vykonava",
                     "spolupracuje", "vnitrni_predpis", "sekce"},
    "Map_Vazby": {"aktivita_kod", "dilci_proces_kod"},
}

CHOICE_KLICE = set()   # choice sloupec uz do mapy nejde

chyby = []
kontrol = 0


def overit(podminka, popis):
    global kontrol
    kontrol += 1
    if not podminka:
        chyby.append(popis)


def dvojce(polozky, rucni_klic, rucni):
    """Plánované dvojče MapaPublishScheduled musí dělat totéž a lišit se jen triggerem.

    Flow má jen jeden trigger, takže denní běh a ruční spuštění z appky nejdou
    v jednom. Dvojče je klon; kdyby se jeho akce rozešly s ručním flow, mapa by
    se v noci publikovala jinak než po stisku tlačítka a nikdo by si toho
    nevšiml — proto se porovnávají celé.
    """
    klice = [n for n in polozky if n.replace("\\", "/").startswith("Workflows/MapaPublishScheduled")]
    overit(len(klice) == 1, f"čekám právě jedno MapaPublishScheduled, je jich {len(klice)}")
    if len(klice) != 1:
        return
    klic = klice[0]
    overit(klic != rucni_klic, "dvojče má stejný soubor jako ruční flow")

    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    definice = flow["properties"]["definition"]
    rucni_def = rucni["properties"]["definition"]

    overit(definice.get("contentVersion") == "1.0.0.0",
           f"dvojče má contentVersion {definice.get('contentVersion')!r}; s 'undefined' "
           "import projde, ale flow nejde otevřít v designeru")
    overit(definice.get("actions") == rucni_def.get("actions"),
           "akce dvojčete se liší od ručního flow — mapa by se v noci publikovala jinak")
    overit(flow["properties"].get("connectionReferences")
           == rucni["properties"].get("connectionReferences"),
           "dvojče nemá stejné connection reference, akce by neměly čím běžet")

    triggery = definice.get("triggers") or {}
    overit(list(triggery) == ["Recurrence"],
           f"dvojče musí mít jediný trigger Recurrence, má {list(triggery)}")
    spousteni = (triggery.get("Recurrence") or {}).get("recurrence") or {}
    overit(spousteni.get("frequency") == "Day" and spousteni.get("interval") == 1,
           f"dvojče se nespouští denně: {spousteni.get('frequency')} / {spousteni.get('interval')}")
    overit(spousteni.get("timeZone") == "Central Europe Standard Time",
           f"dvojče má časové pásmo {spousteni.get('timeZone')!r}; bez něj by UTC posunulo "
           "běh o hodinu nebo dvě podle letního času")
    hodiny = (spousteni.get("schedule") or {}).get("hours")
    overit(hodiny == ["7"], f"dvojče se nespouští v 7:00, ale v {hodiny}")

    # Ruční spuštění z appky nesmí zmizet — appka volá právě tohle flow.
    overit((rucni_def.get("triggers") or {}).get("manual", {}).get("kind") == "PowerAppV2",
           "ruční flow přišlo o trigger PowerAppV2, appka by ho nespustila")

    # Bez zápisu v obou XML se flow do prostředí vůbec nedostane.
    guid = re.search(r"-([0-9A-Fa-f-]{36})\.json$", klic).group(1).lower()
    customizations = polozky["customizations.xml"].decode("utf-8-sig")
    overit(f'<Workflow WorkflowId="{{{guid}}}" Name="MapaPublishScheduled">' in customizations,
           "dvojče chybí v customizations.xml")
    overit(klic.replace("\\", "/") in customizations.replace("/Workflows", "Workflows"),
           "customizations.xml neodkazuje na soubor dvojčete")
    solution = polozky["solution.xml"].decode("utf-8-sig")
    overit(f'<RootComponent type="29" id="{{{guid}}}"' in solution,
           "dvojče není v RootComponents solution.xml, do balíku se nezahrne")


def viditelne(akce, jmeno):
    """Množina akcí, na které smí akce odkazovat: ona sama ne, ale vše
    v jejím řetězu runAfter směrem nahoru. Odkaz mimo tuto množinu se
    naimportuje, ale flow pak nejde zapnout."""
    videt, fronta = set(), list(akce[jmeno].get("runAfter", {}))
    while fronta:
        krok = fronta.pop()
        if krok in videt or krok not in akce:
            continue
        videt.add(krok)
        fronta.extend(akce[krok].get("runAfter", {}))
    return videt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True)
    parser.add_argument("--base", default="deploy/procesnimapa_1_0_0_61.zip",
                        help="výchozí export, proti kterému se hlídá, co se nesmělo změnit")
    argumenty = parser.parse_args()

    with zipfile.ZipFile(argumenty.solution) as balik:
        polozky = {n: balik.read(n) for n in balik.namelist()}
    with zipfile.ZipFile(argumenty.base) as balik:
        zaklad = {n: balik.read(n) for n in balik.namelist()}

    klice = [n for n in polozky if n.replace("\\", "/").startswith("Workflows/MapaPublishFlow")]
    overit(len(klice) == 1, f"čekám právě jedno MapaPublishFlow, je jich {len(klice)}")
    if not klice:
        vypis()
        return 1
    klic = klice[0]

    # GUID flow je v názvu souboru. Kdyby se změnil, import by nebyl upgrade,
    # ale nové flow — a v prostředí by zůstal sirotek blokující další importy.
    zaklad_klic = [n for n in zaklad if n.replace("\\", "/").startswith("Workflows/MapaPublishFlow")]
    overit(len(zaklad_klic) == 1 and zaklad_klic[0] == klic,
           "název souboru flow (a v něm GUID) se proti základu změnil")

    # Druhé flow se tímhle skriptem nesmí dotknout ani o bajt.
    for jmeno in zaklad:
        if jmeno.replace("\\", "/").startswith("Workflows/AktualizaceKratkehoNazvu"):
            overit(jmeno in polozky, f"{jmeno} z balíku zmizelo")

    flow = json.loads(polozky[klic].decode("utf-8-sig"))
    zakl_flow = json.loads(zaklad[klic].decode("utf-8-sig"))
    definice = flow["properties"]["definition"]

    # ---------------------------------------------------------- 1. struktura
    overit(definice.get("contentVersion") == "1.0.0.0",
           f"contentVersion je {definice.get('contentVersion')!r}; s 'undefined' "
           "import projde, ale flow nejde otevřít v designeru")
    overit(definice.get("triggers") == zakl_flow["properties"]["definition"].get("triggers"),
           "trigger se proti základu změnil — musí zůstat, jak ho založil uživatel")

    spojeni = flow["properties"].get("connectionReferences") or {}
    overit("shared_sharepointonline" in spojeni,
           "flow nemá connection reference na SharePoint, akce by neměly čím běžet")
    if "shared_sharepointonline" in spojeni:
        logicky = spojeni["shared_sharepointonline"]["connection"]["connectionReferenceLogicalName"]
        druhe = [n for n in polozky
                 if n.replace("\\", "/").startswith("Workflows/AktualizaceKratkehoNazvu")]
        vzor = json.loads(polozky[druhe[0]].decode("utf-8-sig"))
        overit(logicky == vzor["properties"]["connectionReferences"]
               ["shared_sharepointonline"]["connection"]["connectionReferenceLogicalName"],
               "obě flow musí sdílet totéž spojení, jinak úklid connection reference "
               "rozbije jen jedno z nich")

    akce = definice.get("actions", {})
    ocekavane = ({"Sablona", "Model", "Stranka", "Uloz_mapu"}
                 | {f"Nacti_{k}" for k in ("Agendy", "Procesy", "DilciProcesy", "Aktivity", "Vazby")}
                 | set(OCEKAVANE_KLICE))
    overit(set(akce) == ocekavane,
           f"jiné akce, než čekám: chybí {sorted(ocekavane - set(akce))}, "
           f"navíc {sorted(set(akce) - ocekavane)}")

    # každá akce kromě první musí mít runAfter a odkazovat jen na viditelné akce
    for jmeno, telo in akce.items():
        po = telo.get("runAfter", {})
        overit(bool(po) or jmeno == "Sablona",
               f"{jmeno}: prázdný runAfter — akce by běžela paralelně s první")
        for predchudce in po:
            overit(predchudce in akce, f"{jmeno}: runAfter míří na neexistující '{predchudce}'")
        videt = viditelne(akce, jmeno)
        for odkaz in re.findall(r"(?:body|outputs)\('([^']+)'\)", json.dumps(telo, ensure_ascii=False)):
            overit(odkaz in videt,
                   f"{jmeno} odkazuje na '{odkaz}', který není v jeho runAfter cestě — "
                   "import projde, ale flow nepůjde zapnout")

    # jeden web pro všechny akce; kdyby se lišil, mapa by mísila data dvou webů
    datasety = {t["inputs"]["parameters"]["dataset"] for t in akce.values()
                if t.get("type") == "OpenApiConnection"}
    overit(len(datasety) == 1, f"akce míří na {len(datasety)} různých webů: {datasety}")

    # ------------------------------------------------------------ 2. kontrakt
    for krok in ("Agendy", "Procesy", "DilciProcesy", "Aktivity", "Vazby"):
        jmeno = f"Nacti_{krok}"
        if jmeno not in akce:
            continue
        parametry = akce[jmeno]["inputs"]["parameters"]
        overit(akce[jmeno]["inputs"]["host"]["operationId"] == "GetItems",
               f"{jmeno}: čekám operaci GetItems")
        overit(parametry.get("$top", 0) >= 5000, f"{jmeno}: $top musí být aspoň 5000")
        strankovani = (akce[jmeno].get("runtimeConfiguration", {})
                       .get("paginationPolicy", {}).get("minimumItemCount", 0))
        overit(strankovani >= 5000,
               f"{jmeno}: bez pagination načte konektor jen 100 položek a mapa "
               "bude tiše neúplná")
        # Od 1.0.0.62 je list proměnná prostředí, ne GUID: s GUID vývojového
        # listu se flow na cizím tenantu nedá zapnout ani opravit v designeru.
        overit(parametry.get("table") == ep.list_param(KROK_LIST[krok]),
               f"{jmeno}: table nebere list z proměnné {ep.LIST_PROMENNA[KROK_LIST[krok]]}")

    tabulky = [akce[f"Nacti_{k}"]["inputs"]["parameters"]["table"]
               for k in ("Agendy", "Procesy", "DilciProcesy", "Aktivity", "Vazby")
               if f"Nacti_{k}" in akce]
    overit(len(set(tabulky)) == len(tabulky), "dva dotazy míří na tentýž list")

    for jmeno, klice_ocek in OCEKAVANE_KLICE.items():
        if jmeno not in akce:
            continue
        vyber = akce[jmeno]["inputs"]["select"]
        overit(set(vyber) == klice_ocek,
               f"{jmeno}: klíče {sorted(set(vyber))} != kontrakt {sorted(klice_ocek)}")
        if "kod" in klice_ocek:
            overit(vyber.get("kod") == "@item()?['Title']",
                   f"{jmeno}: 'kod' musí brát ze sloupce Title, jinak zůstane strom prázdný")
        for klic, vyraz in vyber.items():
            if klic in CHOICE_KLICE:
                overit(vyraz.endswith("?['Value']"),
                       f"{jmeno}.{klic}: Choice sloupec bez ?['Value'] pošle objekt, "
                       "ne řetězec")
            else:
                overit(not vyraz.endswith("?['Value']"),
                       f"{jmeno}.{klic}: textový sloupec nesmí mít ?['Value']")
        zdroj = akce[jmeno]["inputs"]["from"]
        overit(zdroj == f"@outputs('Nacti_{jmeno[4:]}')?['body/value']",
               f"{jmeno}: čte z jiného kroku, než odpovídá jeho názvu ({zdroj})")

    if "Map_Aktivity" in akce:
        overit(akce["Map_Aktivity"]["inputs"]["select"]["nazev"] == "@item()?['nazev']",
               "Map_Aktivity musí posílat nazev, ne nazev_kratky — zkrácený slouží "
               "jen k řazení v SharePoint listu")

    if "Model" in akce:
        model = akce["Model"]["inputs"]
        overit(set(model) == {"meta"} | set(KLICE_MODELU),
               f"Model má klíče {sorted(set(model))}, kontrakt čeká meta + {list(KLICE_MODELU)}")
        overit("pocet_aktivit" not in json.dumps(model),
               "pocet_aktivit se neposílá, šablona si počty počítá sama")

    if "Uloz_mapu" in akce:
        parametry = akce["Uloz_mapu"]["inputs"]["parameters"]
        overit(akce["Uloz_mapu"]["inputs"]["host"]["operationId"] == "CreateFile",
               "Uloz_mapu: čekám operaci CreateFile")
        overit(parametry.get("name") == "procesni_mapa.html",
               f"Uloz_mapu ukládá jako {parametry.get('name')!r}")
        overit(parametry.get("folderPath") == "/SiteAssets",
               f"Uloz_mapu ukládá do {parametry.get('folderPath')!r}, ne do /SiteAssets")
        overit(parametry.get("body") == "@outputs('Stranka')",
               "Uloz_mapu neukládá výstup kroku Stranka")

    # -------------------------------------------------------------- 3. význam
    if "Stranka" in akce and SABLONA.exists() and MODEL.exists():
        vyraz = akce["Stranka"]["inputs"]
        # Ověřeno během 20.08.2026: Get file content s inferContentType=true
        # vrací u .html rovnou řetězec, ne objekt. Výběr property nad ním
        # shodí celý běh — a chytit se to dá jedině tady, protože import
        # i zapnutí flow projdou.
        overit("?['$content']" not in vyraz,
               "Stranka: body('Sablona') je řetězec, ne objekt — výběr "
               "?['$content'] běh shodí ('Property selection is not supported "
               "on values of type String')")
        overit("base64ToString" not in vyraz,
               "Stranka: base64ToString nad už dekódovaným řetězcem selže")
        overit("body('Sablona')" in vyraz,
               "Stranka: nečte obsah šablony z kroku Sablona")
        sablona_akce = akce.get("Sablona", {})
        overit(sablona_akce.get("inputs", {}).get("parameters", {})
               .get("inferContentType") is True,
               "Sablona: inferContentType musí být true — na tom stojí, že "
               "body() vrátí řetězec, se kterým výraz v kroku Stranka počítá")
        sablona = io.open(SABLONA, encoding="utf-8").read()
        for kotva in KOTVY:
            overit(sablona.count(kotva) == 1,
                   f"kotva {kotva} je v šabloně {sablona.count(kotva)}×, čekám právě 1×")

        model = json.loads(io.open(MODEL, encoding="utf-8").read())
        html = vyhodnot(vyraz, sablona, model)
        if html is None:
            overit(False, "výraz kroku Stranka nemá tvar, který umím vyhodnotit")
        else:
            for kotva in KOTVY:
                overit(kotva not in html, f"po vyhodnocení zůstala v HTML kotva {kotva}")
            for klic in KLICE_MODELU:
                overit(f'"{klic}":' in html, f"ve vypublikovaném HTML chybí klíč {klic}")
            externi = re.findall(r"""(?:src|href)\s*=\s*["']https?://[^"']+""", html)
            overit(not externi, f"externí zdroje nejsou povoleny: {externi[:3]}")
            overit(html.count('"vygenerováno ') == 1,
                   "razítko __GEN__ se nenahradilo řetězcem v uvozovkách "
                   "(je to JS literál, bez uvozovek se stránka rozbije)")

    dvojce(polozky, klic, flow)

    vypis()
    return 1 if chyby else 0


def vyhodnot(vyraz, sablona, model):
    """Provede to, co udělá Logic Apps: dvě vnořené náhrady kotev.

    Ověřuje se tvar výrazu z balíku; když nesedí, vrací None místo toho, aby
    kontrola tiše prošla nad něčím jiným, než se nasazuje.
    """
    if not re.search(r"replace\(\s*replace\(\s*body\('Sablona'\)\s*,", vyraz):
        return None
    if "'__DATA_JSON__'" not in vyraz or "'__GEN__'" not in vyraz:
        return None
    if "string(outputs('Model'))" not in vyraz:
        return None
    razitko = re.search(r"concat\('\"vygenerováno ', formatDateTime\(utcNow\(\), '([^']+)'\)",
                        vyraz)
    if not razitko:
        return None
    data = json.dumps(model, ensure_ascii=False, separators=(",", ":"))
    html = sablona.replace("__DATA_JSON__", data)
    return html.replace("__GEN__", '"vygenerováno 01.01.2026 00:00"')


def vypis():
    print(f"kontrol: {kontrol}")
    for chyba in chyby:
        print(f"CHYBA: {chyba}")
    print("NEPROŠLO" if chyby else "OK — MapaPublishFlow odpovídá kontraktu")


if __name__ == "__main__":
    sys.exit(main())
