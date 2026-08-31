# -*- coding: utf-8 -*-
"""Proměnné prostředí, přes které se solution napojuje na SharePoint.

Jediný zdroj pravdy o tom, jaké proměnné balík deklaruje a jak se na ně
odkazují flow. Čtou ho oba generátory flow, build_app.py (vkládá definice
do zipu) i brána check_env.py.

Proč vůbec: do 1.0.0.61 měla všechna flow adresu vývojového webu a GUIDy
listů natvrdo — na cizím tenantu jsou takové akce neplatné, flow nejde
zapnout a designer list ani nenabídne k přepnutí. S proměnnými se web
a listy vybírají v průvodci importem.

Typ 100000004 (datový zdroj), ne 100000000 (text): textovou proměnnou
konektor jako dataset/table nepřijme. Dvojice `apiid` + `parameterkey`
říká průvodci, že má nabídnout výběr webu; `parentdefinitionid` u listů
zúží nabídku na listy toho webu.

Definice ZÁMĚRNĚ nemá <defaultvalue> a balík nesmí obsahovat
environmentvariablevalues.json. S výchozí hodnotou by import na cizí
tenant tiše prošel s adresou původního webu — přesně ta chyba, kvůli
které tyhle proměnné vznikly. Bez ní se průvodce zeptat musí. Prostředí
si vyplněnou hodnotu drží, další import už se neptá.

Doloženo produkčními balíky PPF (repo powerApps-vzory-aplikaci-pro-claude):
Clearstream, Průvodní list, Správa notifikací, MiddleOffice a MessageCenter
mají takto dataset i table včetně PatchItem, PostItem a triggeru nad listem.
"""

API_ID = "/providers/microsoft.powerapps/apis/shared_sharepointonline"
WEB = "mpsv_procesnimapaSite"

# schema, zobrazovaný název, popis, parameterkey, rodič
DEFINICE = [
    (WEB, "Procesni mapa - web", "Adresa SharePoint webu s rejstrikem.", "dataset", None),
    ("mpsv_listAgendy", "Procesni mapa - Agendy", "List Agendy.", "table", WEB),
    ("mpsv_listProcesy", "Procesni mapa - Procesy", "List Procesy.", "table", WEB),
    ("mpsv_listDilciProcesy", "Procesni mapa - Dilci procesy", "List Dilci procesy.", "table", WEB),
    ("mpsv_listAktivity", "Procesni mapa - Aktivity", "List Aktivity.", "table", WEB),
    ("mpsv_listVazby", "Procesni mapa - Vazby",
     "Vazebni list aktivita - dilci proces.", "table", WEB),
    ("mpsv_listUtvary", "Procesni mapa - Utvary", "Ciselnik utvaru.", "table", WEB),
]

# Zobrazovaný název listu v appce -> proměnná. Klíč je týž, jakým listy
# adresuje LISTY v build_mapa_flow.py a ConnectionReferences canvas appky.
LIST_PROMENNA = {
    "Agendy": "mpsv_listAgendy",
    "Procesy": "mpsv_listProcesy",
    "Dílčí procesy": "mpsv_listDilciProcesy",
    "Aktivity": "mpsv_listAktivity",
    "Vazba aktivita–dílčí proces": "mpsv_listVazby",
    "Útvary": "mpsv_listUtvary",
}

# Zdroj, který appka má v napojení, ale žádný vzorec ho nepoužívá. Knihovna
# Dokumenty přibyla ze Studia při zakládání appky. Kdyby zůstala, musela by
# dostat vlastní proměnnou (v jednom `dataSets` bloku nesmí být zdroj bez
# overridu), a to jen proto, aby ji nikdo nepoužil. Odebírá se při buildu.
NEPOUZIVANE_ZDROJE = ["Dokumenty"]

_PODLE_SCHEMA = {d[0]: d for d in DEFINICE}

SLOZKA = "environmentvariabledefinitions"


def klic(schema):
    """Název, pod kterým proměnnou vidí Logic Apps: '<zobrazovaný název> (<schema>)'."""
    if schema not in _PODLE_SCHEMA:
        raise SystemExit(f"CHYBA: neznámá proměnná {schema}")
    return f"{_PODLE_SCHEMA[schema][1]} ({schema})"


def vyraz(schema):
    """Odkaz bez zavináče — pro vnoření do jiného výrazu (concat, if, …)."""
    return f"parameters('{klic(schema)}')"


def param(schema):
    """Odkaz jako celá hodnota parametru akce: @parameters('<název> (<schema>)')."""
    return "@" + vyraz(schema)


def web():
    return param(WEB)


def list_param(zobrazovany):
    """Proměnná listu podle jeho zobrazovaného názvu v appce."""
    if zobrazovany not in LIST_PROMENNA:
        raise SystemExit(f"CHYBA: pro list '{zobrazovany}' není proměnná")
    return param(LIST_PROMENNA[zobrazovany])


def schema_z_klice(k):
    """Z klíče 'Zobrazovaný název (schema)' vrátí schema, jinak None."""
    for d in DEFINICE:
        if k == f"{d[1]} ({d[0]})":
            return d[0]
    return None


def deklarace(schema):
    """Deklarace parametru do `definition.parameters` flow.

    `metadata.schemaName` je vazba na proměnnou prostředí — bez ní by
    parametr existoval, ale hodnotu by do něj prostředí nedosadilo.
    Tvar je 1:1 podle deklarace, kterou do AktualizaceKratkehoNazvu dopsal
    designer. Bez `defaultValue`: hodnota patří do prostředí, ne do balíku.
    """
    _, _, popis, _, _ = _PODLE_SCHEMA[schema]
    return {"type": "String",
            "metadata": {"schemaName": schema, "description": popis}}


def xml(schema, verze):
    """Obsah environmentvariabledefinition.xml pro jednu proměnnou."""
    _, nazev, popis, klic, rodic = _PODLE_SCHEMA[schema]
    for hodnota in (nazev, popis):
        if any(z in hodnota for z in '<>&"\''):
            raise SystemExit(f"CHYBA: {schema} má v textu znak, který se musí v XML escapovat")
    radky = [
        f'<environmentvariabledefinition schemaname="{schema}">',
        f"  <apiid>{API_ID}</apiid>",
        f'  <description default="{popis}">',
        f'    <label description="{popis}" languagecode="1033" />',
        "  </description>",
        f'  <displayname default="{nazev}">',
        f'    <label description="{nazev}" languagecode="1033" />',
        "  </displayname>",
        f"  <introducedversion>{verze}</introducedversion>",
        "  <iscustomizable>1</iscustomizable>",
        "  <isrequired>0</isrequired>",
        f"  <parameterkey>{klic}</parameterkey>",
    ]
    if rodic:
        radky += [
            "  <parentdefinitionid>",
            f"    <schemaname>{rodic}</schemaname>",
            "  </parentdefinitionid>",
        ]
    radky += [
        "  <secretstore>0</secretstore>",
        "  <type>100000004</type>",
        "</environmentvariabledefinition>",
    ]
    return "\n".join(radky) + "\n"


def cesta_definice(schema):
    return f"{SLOZKA}/{schema}/environmentvariabledefinition.xml"


def vloz_do_slozky(koren, verze):
    """Zapíše definice do rozbalené solution. Idempotentní.

    Soubory s uloženou hodnotou (environmentvariablevalues.json) maže: kdyby
    v balíku zůstaly, každý import by hodnoty v cílovém prostředí přepsal
    tou z balíku, tedy adresou webu, ze kterého se exportovalo.
    """
    from pathlib import Path

    koren = Path(koren)
    smazane = []
    slozka = koren / SLOZKA
    if slozka.exists():
        for soubor in sorted(slozka.rglob("environmentvariablevalues.json")):
            soubor.unlink()
            smazane.append(str(soubor.relative_to(koren)).replace("\\", "/"))

    vlozene = []
    for schema, *_ in DEFINICE:
        cil = koren / cesta_definice(schema)
        cil.parent.mkdir(parents=True, exist_ok=True)
        cil.write_text(xml(schema, verze), encoding="utf-8")
        vlozene.append(schema)
    return vlozene, smazane
