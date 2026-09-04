# PresunFlow — kaskádový přesun procesu a dílčího procesu

Flow provádí přesun podle **varianty C (zánik a vznik)**: starý kód se uzavře
v listu `HistorieKodu`, pod novým rodičem vznikne nový a obě strany na sebe
ukazují. Mění se prefix celého podstromu, takže přesun procesu s osmi dílčími
procesy a čtyřiceti aktivitami uzavře 49 kódů a založí 49 nových.

Generuje ho `src/build_presun_flow.py`, hlídá `src/check_presun_flow.py`
(111 kontrol) a `src/mutace_presun.py` (13/13).

---

## Kontrakt

**Vstup** — jeden text, JSON:

```json
{"kod": "07-08", "uroven": "proces", "cil": "03",
 "duvod": "organizační změna k 1.1.2027", "rezim": "nahled"}
```

| pole | význam |
|---|---|
| `kod` | co se stěhuje — kód procesu (`AA-BB`) nebo dílčího procesu (`AA-BB-CCC`) |
| `uroven` | `proces` \| `dilci_proces` |
| `cil` | kód nového rodiče — agenda (`AA`) u procesu, proces (`AA-BB`) u dílčího procesu |
| `duvod` | zapíše se ke každému uzavřenému kódu; metodika ho vyžaduje |
| `rezim` | `nahled` (nic nezapíše) \| `zapis` |

**Odpověď** — čtyři řetězce, jako u ostatních flow (appka má
`dynamicschema = false` a rozebírá je `Split`):

| pole | obsah |
|---|---|
| `stav` | `nahled` \| `zapsano` \| `plno` |
| `hlaseni` | text chyby, jinak prázdno |
| `porizeno` | nový prefix, pod kterým větev ožije (např. `03-06`) |
| `prehled` | řádky `stary\|~\|novy\|~\|uroven\|~\|nazev` spojené `\|#\|` |

Stav `plno` znamená, že pod cílovým rodičem došla čísla (99 procesů v agendě,
999 dílčích procesů v procesu). Flow v tom případě **nezapíše nic**.

---

## Co dělá krok za krokem

1. `Vstup`, `Cesta_webu` — rozebere požadavek, složí server-relativní cestu.
2. `Nacti_*` — pět listů (Procesy, DilciProcesy, Aktivity, Vazby, Historie),
   všechny se stránkováním na 5 000.
3. `Sourozenci` → `Cisla_ziva`, `Uzavrene` → `Cisla_uzavrena` → `Nove_cislo`
   → `Novy_prefix` — první volné číslo **přes živý list i přes historii**.
4. `Kontrola_mista` — došlá čísla odmítne a běh ukončí.
5. `Vlastni`, `Deti`, `Vnuci`, `Vazby_dotcene` → `Mapa` — co se kaskádou mění.
6. `Prehled_radky` → `Prehled` → `Je_nahled` — v režimu náhledu odpoví a skončí.
7. Zápis v pevném pořadí: `Zaloz_proces` → `Mapa_dilci` → `Zaloz_dilci` →
   `Zaloz_aktivity` → `Zaloz_vazby` → `Zapis_historii` → `Smaz_vazby` →
   `Smaz_aktivity` → `Smaz_deti` → `Smaz_vlastni` → `Odpoved`.

**Pořadí je závazné.** Nejdřív vznik, pak historie, teprve nakonec zánik.
V opačném pořadí by výpadek uprostřed smazal větev, která ještě nikde jinde
neexistuje; takhle je nejhorší možný výsledek duplicita, ne ztráta.

---

## Pravidlo přečíslování

Přečísluje se **jen přesouvaná úroveň**. Potomci dědí nový prefix a nechají
si své pořadové číslo:

```
proces        07-08            →  03-05
  dílčí proces  07-08-001      →  03-05-001
    aktivita     07-08-001-0006 → 03-05-001-0006
```

Hledat pod novým rodičem volná čísla pro potomky není potřeba — číslují se
v rámci svého rodiče a ten je nový, takže jsou volná všechna. Celá kaskáda
je proto jediná náhrada prefixu:

```
novy = concat(novyPrefix, substring(stary, length(kod)))
```

**Uzavřený kód se nikdy nerecykluje.** Nové číslo se hledá jako maximum přes
živý list *i přes historii* (pravidlo F10/1). Kdyby se historie nezapočítala,
přesun zpátky tam, odkud položka přišla, by oživil kód, který už jednou něco
znamenal.

---

## Vazby

Dotčená je vazba, které se mění kód aktivity **nebo** kód dílčího procesu.
Každý z těch dvou kódů se přepisuje samostatně, takže projdou obě křížové
situace, na které se zapomíná:

- cizí aktivita zařazená **dovnitř** přesouvané větve — kód se jí nemění,
  ale vazba musí ukázat na nový dílčí proces;
- naše aktivita zařazená **ven** — kód se mění, cizí dílčí proces zůstává.

---

## Registrace flow — HOTOVO (04.09.2026)

`PresunFlow` je od balíku 1.0.0.94 zaregistrované jako datový zdroj appky
(`FlowNameId` 4d71c7b1-…), takže obrazovka `scr_Presun` volá flow doopravdy.
Volání je v `btn_SpocitatP.OnSelect` (režim `nahled`) a v
`btn_ModalProvestP.OnSelect` (záloha + režim `zapis`); přechodný popisek
`lbl_CekaNaTokP` je pryč.

Postup, kterým se tam registrace dostala — pro případ přenosu na jiné
prostředí, kde se musí zopakovat (nové prostředí přidělí vlastní `FlowNameId`):

1. Naimportovat balík jako upgrade.
2. V Power Automate **zapnout `PresunFlow`** (po importu bývá vypnuté).
3. Vyzkoušet ho **samostatně**, bez appky: Power Automate → PresunFlow → Test →
   Manually → do pole `pozadavek` vložit
   `{"kod":"07-08","uroven":"proces","cil":"03","duvod":"zkouška","rezim":"nahled"}`.
   V režimu `nahled` se nic nezapisuje.
4. Otevřít appku ve Studiu → **Add data → PresunFlow**.
5. Mikro-změna, **Save**, **Publish**, export solution (unmanaged).
6. Do exportu doplnit volání flow a poslat zpátky jako další balík.

`varPresunVysledek` a `varPresunZapis` se v `App.OnStart` **neinicializují** —
stejně jako `varNahledVysledek` u importu. Prázdný řetězec v OnStart by jim dal
typ textu a záznam z `Flow.Run()` by se do nich pak nevešel; brána
`kontrola_promennych` hlídá jen proměnné, které v OnStart jsou.

---

## Na co si dát pozor

- **Po importu flow ručně zapnout.** Import stav zapnutí nemění; flow, které
  se jednou nepodařilo zapnout, zůstane vypnuté i po importu opravené verze
  a appka pak hlásí `WorkflowTriggerIsNotEnabled`.
- **Náhled je povinný krok**, ne pohodlí. Tlačítko *Provést* je zhasnuté,
  dokud náhled neproběhl právě nad tímhle cílem — jinak by se zapisovalo
  podle čísel, která platila pro jiný cíl.
- **Technická větev `00`** se v nabídce cílů neobjevuje a přesouvat ji nelze;
  je to provizorium pro import holých aktivit, ne kus rejstříku.
