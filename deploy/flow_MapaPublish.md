# Flow `MapaPublish` — publikace procesní mapy

Vezme šablonu `mapa_template.html`, zapeče do ní aktuální data z pěti
SharePoint listů a uloží výsledek do Site Assets. Mapa tak nemusí nic
stahovat za běhu.

> **Od 20.08.2026 je flow vygenerované, ne klikané.** Akce doplňuje
> `src/build_mapa_flow.py` do kostry, kterou uživatel založil v designeru
> (úprava exportovaného zipu, ne stavba od nuly — to je postup, který se
> u druhého flow osvědčil). Kontroluje ho `src/check_mapa_flow.py`
> (126 kontrol, 12 mutačně ověřených). Nasazení řeší
> `deploy/navod_publikace_mapy.md`.
>
> Tenhle dokument dál platí jako **datový kontrakt** (sekce níže) a jako
> **klikací fallback**, kdyby se generovaný zip nepodařilo naimportovat.

Návod je **klikací, pro designer**. Generované zipy flow se opakovaně
ukázaly jako nespolehlivé — importují se, ale nejdou otevřít nebo zapnout.
Postavit flow ručně je rychlejší než hledat, proč zip neprošel.

## Proč mapa data nefetchuje

SharePoint servíruje HTML z knihovny v sandboxovaném iframu (`about:srcdoc`,
origin `null`) s `connect-src 'none'`. JavaScript se spustí, ale `fetch`
ani `XHR` neprojdou; blokovaný je i `img-src`. Obejít to v kódu nelze —
omezení je v tom, jak SharePoint soubory z knihovny servíruje, a `.aspx`
místo `.html` to neřeší. Proto data **zapékáme** už při publikaci.

> **Neověřeno:** že tenant HTML ze Site Assets vůbec zobrazí a nestáhne ho
> (Strict browser file handling). Ověření bylo vědomě odloženo
> (`PLAN.md` krok 10). Pokud se ukáže, že tenant soubor stahuje, publikační
> flow propadne a zobrazení se přesune do canvas appky. Do tohoto flow proto
> neinvestuj víc, než je nutné, dokud to není ověřené.

## Předpoklady

- Listy `Agendy`, `Procesy`, `DilciProcesy`, `Aktivity`, `AktivitaDilciProces`
  založené podle `deploy/sharepoint_schema.md` a naplněné.
- `src/mapa_template.html` nahraný do Site Assets jako `mapa_template.html`.
- Účet, pod kterým flow běží, má **Contribute na Site Assets**. Bez toho
  poslední krok selže až za běhu, ne při ukládání.

## Datový kontrakt (nutno dodržet přesně)

Šablona má dvě kotvy, `__DATA_JSON__` a `__GEN__`, a obě musí být nahrazeny.
Když zůstane jedna, stránka se rozbije. `__GEN__` se nahrazuje **řetězcem
v uvozovkách** (je to JS výraz), `__DATA_JSON__` objektem:

```json
{
  "meta":          { "sekce": "3", "spravce": "Ing. Tomáš Kroutil" },
  "agendy":        [ { "kod", "nazev", "vlastnik", "stav_mapovani" } ],
  "procesy":       [ { "kod", "nazev", "agenda_kod", "vlastnik", "stav_mapovani" } ],
  "dilci_procesy": [ { "kod", "nazev", "proces_kod", "vlastnik", "stav_mapovani" } ],
  "aktivity":      [ { "kod", "nazev", "dilci_proces_kod", "vykonava",
                       "spolupracuje", "vnitrni_predpis", "sekce" } ],
  "vazby":         [ { "aktivita_kod", "dilci_proces_kod" } ]
}
```

Dvě věci, na kterých se to nejsnáz rozbije:

1. **`kod` je v SharePointu uložený ve sloupci `Title`.** Každý `Select`
   musí mapovat `Title` → `kod`, jinak strom zůstane prázdný.
2. **`pocet_aktivit` se neposílá.** Šablona si počty ve větvích počítá sama
   (`aktCount`); uložený počet by v listech zastarával.

## Kroky v designeru

### 1. Trigger — `Recurrence`
Frekvence 1× denně. Přidej i `Manually trigger a flow`, ať jde publikaci
vynutit hned po hromadné úpravě.

### 2. `Get file content using path` → přejmenuj na `Sablona`
- Site Address: proměnná prostředí s adresou webu (**nehardcoduj URL**)
- File Path: `/SiteAssets/mapa_template.html`

### 3. Pětkrát `Get items` → `Nacti_Agendy`, `Nacti_Procesy`, `Nacti_DilciProcesy`, `Nacti_Aktivity`, `Nacti_Vazby`

U **každého**:
- Top Count: `5000`
- Settings → **Pagination: On**, Threshold `5000`

Výchozí stránka je 100 položek. Bez tohoto nastavení flow tiše načte jen
prvních 100 dílčích procesů a mapa bude vypadat, že v rejstříku chybí data.
Limit 5 000 je zároveň view threshold SharePointu — až se k němu rejstřík
přiblíží, bude potřeba jiné řešení, ne vyšší číslo.

### 4. Pětkrát `Select` → přemapování na kontrakt

`Nacti_Agendy` → `Map_Agendy`, From `@outputs('Nacti_Agendy')?['body/value']`:

| klíč | hodnota |
|---|---|
| `kod` | `@item()?['Title']` |
| `nazev` | `@item()?['nazev']` |
| `vlastnik` | `@item()?['vlastnik']` |
| `stav_mapovani` | `@item()?['stav_mapovani']?['Value']` |

**Sloupce typu Choice vracejí objekt, ne řetězec** — proto `?['Value']`.
Bez toho se do JSON dostane `{"Value":"zmapováno"}` a filtr stavu v mapě
přestane fungovat.

Obdobně:
- `Map_Procesy`: `kod`←`Title`, `nazev`, `agenda_kod`, `vlastnik`,
  `stav_mapovani`←`…?['Value']`
- `Map_DilciProcesy`: `kod`←`Title`, `nazev`, `proces_kod`, `vlastnik`,
  `stav_mapovani`←`…?['Value']`
- `Map_Aktivity`: `kod`←`Title`, `nazev`, `dilci_proces_kod`, `vykonava`,
  `spolupracuje`, `vnitrni_predpis`, `sekce`
- `Map_Vazby`: `aktivita_kod`, `dilci_proces_kod`

`Map_Aktivity` posílá **`nazev`, ne `nazev_kratky`** — v mapě se zobrazuje
úplný název, zkrácený slouží jen k řazení v SharePoint listu.

### 5. `Compose` → `Model`

```
{
  "meta": { "sekce": "3", "spravce": "Ing. Tomáš Kroutil" },
  "agendy": @{body('Map_Agendy')},
  "procesy": @{body('Map_Procesy')},
  "dilci_procesy": @{body('Map_DilciProcesy')},
  "aktivity": @{body('Map_Aktivity')},
  "vazby": @{body('Map_Vazby')}
}
```

> **Slabé místo:** `meta` je natvrdo. Dokud je zmapovaná jen sekce 3, sedí to;
> jakmile přibudou další sekce, hlavička „Sekce 3 · sekční správce…" přestane
> dávat smysl. Až to nastane, buď hlavičku ze šablony odstranit, nebo přidat
> list `Nastaveni` a číst ji odtud. Nechávat to natvrdo déle znamená, že mapa
> bude tvrdit něco nepravdivého.

### 6. `Compose` → `Stranka`

```
@{replace(
    replace(
      base64ToString(body('Sablona')?['$content']),
      '__DATA_JSON__',
      string(outputs('Model'))
    ),
    '__GEN__',
    concat('"vygenerováno ', formatDateTime(utcNow(), 'dd.MM.yyyy HH:mm'), '"')
  )}
```

`Get file content` vrací binárku — bez `base64ToString` by se nahrazování
nechytlo. Uvozovky kolem `__GEN__` jsou povinné, je to JS řetězcový literál.

### 7. `Create file` → `Uloz_mapu`
- Site Address: proměnná prostředí
- Folder Path: `/SiteAssets`
- File Name: `procesni_mapa.html`
- File Content: `@outputs('Stranka')`

## Jak se ověří, že to funguje

1. **Ruční spuštění** — flow doběhne zeleně, v Site Assets vznikne
   `procesni_mapa.html`.
2. **Data jsou uvnitř** — stáhni soubor a ověř, že neobsahuje řetězce
   `__DATA_JSON__` ani `__GEN__` a že obsahuje `"agendy":`, `"procesy":`,
   `"dilci_procesy":`, `"aktivity":`, `"vazby":`. Přesně tyhle kontroly dělá
   i `src/build_mapa.py`, takže výsledek flow musí projít stejným sítem.
3. **Počty sedí** — počet výskytů `"kod":` v bloku aktivit odpovídá počtu
   položek v listu `Aktivity`.
4. **Stránkování** — v běhu flow zkontroluj výstup `Nacti_DilciProcesy`:
   musí mít **250** položek, ne 100. Tohle je nejpravděpodobnější tichá chyba.
5. **Změna se propíše** — změň název jedné aktivity v listu, spusť flow,
   nová hodnota musí být v HTML.
6. **Zobrazení** — otevři soubor ze Site Assets a v konzoli zkontroluj,
   že nepadá `securitypolicyviolation`. Tohle je odložené ověření z kroku 10
   plánu; dokud neproběhne, není publikace hotová.

## Na co si dát pozor

- **Choice sloupce**: `?['Value']`, jinak se do dat dostane objekt.
- **Stránkování**: bez zapnuté pagination tichých 100 položek místo 250.
- **Contribute na Site Assets**: chybí-li, selže až poslední krok.
- **`Create file` nad existujícím souborem**: ověř, že přepíše a nezaloží
  `procesni_mapa1.html`. Pokud zakládá kopii, použij místo toho
  `Update file` a `Create file` nech jen pro první běh.
- **Po každém importu, který skončil hláškou „one or more flows may not have
  turned on", flow ručně zapni.** Import stav zapnutí nemění a appka pak
  hlásí chybu, která vypadá jako její vlastní.
