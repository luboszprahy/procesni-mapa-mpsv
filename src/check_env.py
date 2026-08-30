# -*- coding: utf-8 -*-
"""Brána nad src/env_promenne.py — tvar definic proměnných prostředí.

Chyba v definici projde importem a projeví se až tím, že flow nejde zapnout,
takže se hlídá offline. Vzorem je Clearstream (produkce PPF), z něhož je tvar
převzatý.

Spouštět z kořene projektu:
    python src/check_env.py
"""

import re
import sys
from xml.etree import ElementTree

sys.path.insert(0, "src")
import env_promenne as ep  # noqa: E402

VERZE = "1.0.0.62"
# Web + jeden list na každou tabulku, kterou používá flow nebo appka.
# Číslo je psané ručně schválně: kdyby proměnná někde přibyla nedopatřením,
# průvodce importem se na ni zeptá a nikdo nebude vědět proč.
POCET = 7

chyby = []


def overit(podminka, popis):
    if not podminka:
        chyby.append(popis)


def zkontroluj_definice():
    overit(len(ep.DEFINICE) == POCET,
           f"čekám {POCET} proměnných, modul jich má {len(ep.DEFINICE)}")
    schemata = [d[0] for d in ep.DEFINICE]
    overit(len(set(schemata)) == len(schemata), "schema name se opakuje")
    for schema in schemata:
        overit(schema.startswith("mpsv_"),
               f"{schema}: prefix musí odpovídat publisherovi balíku (mpsv_)")

    for schema, nazev, popis, klic, rodic in ep.DEFINICE:
        text = ep.xml(schema, VERZE)
        try:
            uzel = ElementTree.fromstring(text)
        except ElementTree.ParseError as chyba:
            chyby.append(f"{schema}: XML není well-formed — {chyba}")
            continue

        overit(uzel.tag == "environmentvariabledefinition", f"{schema}: špatný kořenový uzel")
        overit(uzel.get("schemaname") == schema, f"{schema}: schemaname v atributu nesedí")

        def hodnota(jmeno):
            nalezeny = uzel.find(jmeno)
            return None if nalezeny is None else (nalezeny.text or "").strip()

        overit(hodnota("type") == "100000004",
               f"{schema}: typ {hodnota('type')} — textová proměnná (100000000) se "
               f"jako dataset ani table nepoužije, konektor ji nepřijme")
        overit(hodnota("apiid") == ep.API_ID,
               f"{schema}: apiid neodkazuje na SharePoint konektor")
        overit(hodnota("parameterkey") == klic,
               f"{schema}: parameterkey {hodnota('parameterkey')!r}, čekám {klic!r}")
        overit(hodnota("secretstore") == "0", f"{schema}: secretstore musí být 0")
        overit(hodnota("iscustomizable") == "1", f"{schema}: iscustomizable musí být 1")
        overit(hodnota("introducedversion") == VERZE,
               f"{schema}: introducedversion {hodnota('introducedversion')!r}")

        # Výchozí hodnota je zakázaná schválně: s ní by import na cizí tenant
        # tiše prošel s adresou původního webu a průvodce by se nezeptal.
        overit(uzel.find("defaultvalue") is None,
               f"{schema}: má <defaultvalue> — import na cizí tenant by tiše "
               f"převzal původní web a nikdo by si toho nevšiml")

        rodicovsky = uzel.find("parentdefinitionid")
        if rodic:
            overit(rodicovsky is not None and
                   (rodicovsky.findtext("schemaname") or "").strip() == rodic,
                   f"{schema}: parentdefinitionid nemíří na {rodic} — průvodce by "
                   f"u listu nenabídl výběr z listů toho webu")
        else:
            overit(rodicovsky is None, f"{schema}: web nesmí mít rodiče")

        overit(nazev == nazev.encode("ascii", "ignore").decode(),
               f"{schema}: zobrazovaný název má diakritiku — jde do @parameters "
               f"uvnitř JSON definice flow, kde se špatně dohledává")


def zkontroluj_odkazy():
    tvar = re.compile(r"^@parameters\('[A-Za-z0-9 .,\-]+ \(mpsv_[A-Za-z]+\)'\)$")
    for schema, nazev, *_ in ep.DEFINICE:
        odkaz = ep.param(schema)
        overit(tvar.match(odkaz) is not None, f"{schema}: odkaz {odkaz!r} nemá čekaný tvar")
        overit(f"({schema})" in odkaz, f"{schema}: odkaz neuvádí schema name")
        overit(odkaz.startswith(f"@parameters('{nazev} ("),
               f"{schema}: odkaz neuvádí zobrazovaný název přesně tak, jak zní v definici")

    overit(ep.web() == ep.param(ep.WEB), "web() a param(WEB) se rozcházejí")


def zkontroluj_listy():
    from build_mapa_flow import LISTY
    zobrazovane = [l[0] for l in LISTY]
    # Publikační flow čte podmnožinu listů — Útvary potřebuje jen appka, která
    # si od F9 bere napojení z týchž proměnných. Rovnost by tu proto byla
    # falešná; každý list flow ale svou proměnnou mít musí.
    overit(set(zobrazovane) <= set(ep.LIST_PROMENNA),
           f"LISTY v build_mapa_flow nemají proměnnou: "
           f"{sorted(set(zobrazovane) - set(ep.LIST_PROMENNA))}")
    schemata = {d[0] for d in ep.DEFINICE}
    for zobrazovany, schema in ep.LIST_PROMENNA.items():
        overit(schema in schemata, f"{zobrazovany}: proměnná {schema} není deklarovaná")
        overit(schema != ep.WEB, f"{zobrazovany}: list nesmí ukazovat na proměnnou webu")


def zkontroluj_vlozeni():
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as docasny:
        koren = Path(docasny)
        (koren / "solution.xml").write_text("x", encoding="utf-8")
        hodnoty = koren / ep.SLOZKA / "mpsv_listAgendy" / "environmentvariablevalues.json"
        hodnoty.parent.mkdir(parents=True)
        hodnoty.write_text("{}", encoding="utf-8")

        vlozene, smazane = ep.vloz_do_slozky(koren, VERZE)
        overit(len(vlozene) == POCET, f"vloženo {len(vlozene)} definic místo {POCET}")
        overit(len(smazane) == 1,
               "environmentvariablevalues.json v balíku zůstal — s uloženou hodnotou "
               "by každý import přepsal nastavení cílového prostředí adresou z balíku")
        overit(not list(koren.rglob("environmentvariablevalues.json")),
               "v balíku zůstal soubor s hodnotami proměnných")
        overit((koren / "solution.xml").read_text(encoding="utf-8") == "x",
               "vloz_do_slozky sáhlo na cizí soubor")

        def snimek():
            return {str(p.relative_to(koren)): p.read_bytes()
                    for p in sorted(koren.rglob("*")) if p.is_file()}

        prvni = snimek()
        ep.vloz_do_slozky(koren, VERZE)
        overit(prvni == snimek(), "vloz_do_slozky není idempotentní")

        for schema, *_ in ep.DEFINICE:
            overit((koren / ep.cesta_definice(schema)).exists(),
                   f"{schema}: definice se do balíku nevložila")


def main():
    zkontroluj_definice()
    zkontroluj_odkazy()
    zkontroluj_listy()
    zkontroluj_vlozeni()

    if chyby:
        for text in chyby:
            print(f"CHYBA: {text}")
        print(f"\nSELHALO: {len(chyby)} chyb")
        return 1
    print(f"proměnných: {len(ep.DEFINICE)}   listů namapováno: {len(ep.LIST_PROMENNA)}")
    for schema, nazev, _, klic, rodic in ep.DEFINICE:
        print(f"  {schema:24} {klic:8} {'(pod ' + rodic + ')' if rodic else ''}")
    print("\nOK — definice mají tvar, který průvodci importem nabídne výběr webu a listů")
    return 0


if __name__ == "__main__":
    sys.exit(main())
