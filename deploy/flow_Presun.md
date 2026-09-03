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

## CO JE POTŘEBA UDĚLAT — registrace flow (kolo 1 → 2)

Appka volání `PresunFlow.Run()` zatím **neobsahuje**. Nejde ho napsat dřív,
než je flow zaregistrované jako datový zdroj appky: záznam v
`References/DataSources.json` nese vedle `WorkflowEntityId` (to známe)
i `FlowNameId`, které přiděluje **až prostředí při importu**. Bez něj se
`.Run()` nemá na co navázat a appka by se neotevřela vůbec.

Postup:

1. Naimportovat `deploy/procesnimapa_1_0_0_93.zip` jako upgrade.
2. V Power Automate **zapnout `PresunFlow`** (po importu bývá vypnuté).
3. Vyzkoušet ho **samostatně**, bez appky: Power Automate → PresunFlow → Test →
   Manually → do pole `pozadavek` vložit
   `{"kod":"07-08","uroven":"proces","cil":"03","duvod":"zkouška","rezim":"nahled"}`
   (kód a cíl podle skutečných dat). Běh musí skončit zeleně a v posledním
   kroku `Odpoved_nahled` musí být `prehled` se seznamem dvojic.
   **V režimu `nahled` se nic nezapisuje**, takže je to bezpečné.
4. Otevřít appku ve Studiu → **Add data → PresunFlow**.
5. Udělat mikro-změnu (posunout prvek o pixel zpět), **Save** a **Publish**.
6. Export solution (unmanaged) a poslat zip.

Do balíku 94 se pak doplní volání flow — vzorce jsou hotové níž.

---

## Vzorce k doplnění do appky (balík 94)

`btn_SpocitatP.OnSelect` — místo dnešní notifikace:

```
=Set(varPresunBezi, true);
Set(varPresunHotovo, "");
Clear(colPresun);
IfError(
    Set(
        varPresunVysledek,
        PresunFlow.Run(
            "{""kod"":""" & varPresunKod &
            """,""uroven"":""" & varPresunUroven &
            """,""cil"":""" & If(
                varPresunUroven = "proces",
                Left(drp_CilAgendaP.Selected.Value, 2),
                Left(drp_CilProcesP.Selected.Value, 5)
            ) &
            """,""duvod"":""" & txt_DuvodP.Text &
            """,""rezim"":""nahled""}"
        )
    );
    Set(varPresunNovyPrefix, varPresunVysledek.porizeno);
    If(
        varPresunVysledek.stav = "plno",
        Notify(varPresunVysledek.hlaseni, NotificationType.Error, varNotifyChybaMs),
        ClearCollect(
            colPresun,
            ForAll(
                Split(varPresunVysledek.prehled, "|#|") As r,
                {
                    stary: First(Split(r.Value, "|~|")).Value,
                    novy: Last(FirstN(Split(r.Value, "|~|"), 2)).Value,
                    uroven: Last(FirstN(Split(r.Value, "|~|"), 3)).Value,
                    nazev: Last(Split(r.Value, "|~|")).Value
                }
            )
        );
        Set(varPresunHotovo, varPresunKod & "→" & varPresunNovyPrefix)
    ),
    Notify("Náhled se nepodařilo spočítat: " & FirstError.Message, NotificationType.Error, varNotifyChybaMs)
);
Set(varPresunBezi, false)
```

`btn_ModalProvestP.OnSelect`:

```
=Set(varPresunPotvrdit, false);
Set(varPresunBezi, true);
IfError(
    ZalohaFlow.Run();
    Set(
        varPresunZapis,
        PresunFlow.Run(
            "{""kod"":""" & varPresunKod &
            """,""uroven"":""" & varPresunUroven &
            """,""cil"":""" & If(
                varPresunUroven = "proces",
                Left(drp_CilAgendaP.Selected.Value, 2),
                Left(drp_CilProcesP.Selected.Value, 5)
            ) &
            """,""duvod"":""" & txt_DuvodP.Text &
            """,""rezim"":""zapis""}"
        )
    );
    Notify("Přesun hotov: " & varPresunKod & " je teď " & varPresunZapis.porizeno & ".", NotificationType.Success, varNotifyMs),
    Notify("Přesun selhal: " & FirstError.Message & " Zkontroluj rejstřík a případně ho obnov ze zálohy pořízené na začátku.", NotificationType.Error, varNotifyChybaMs)
);
Set(varPresunBezi, false);
Set(varAktStale, true);
Set(varPresunHotovo, "");
Clear(colPresun);
Set(varUrovenTyp, If(varPresunUroven = "proces", "proces", "dilci"));
Set(varCiselnikNova, true);
Set(varCiselnikKod, "");
Set(varRodicC, "");
Navigate(scr_Ciselnik, ScreenTransition.UnCover)
```

Zároveň se odstraní popisek `lbl_CekaNaTokP` (celý prvek) a do
`App.OnStart` přibudou `varPresunVysledek` a `varPresunZapis`.

**Záloha před zápisem je součást zadání**, ne opatrnost navíc: kaskáda není
transakce (SharePoint ji neumí ani přes flow) a metodika u změny kódu
vyžaduje doložitelnost.

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
