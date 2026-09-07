# Nasazení HTML mapy — co udělat po importu 1.0.0.21

Tři kroky, každý má vlastní ověření. Dělej je v pořadí — druhý bez prvního
selže až za běhu flow, ne při ukládání.

## 1. Nahrát dva soubory do Site Assets

Otevři knihovnu **Site Assets** cílového webu:

```
https://ppfbanka.sharepoint.com/sites/DigiData_D/testovaci_subsajta/procesnimapa/SiteAssets/Forms/AllItems.aspx
```

Přetáhni do ní z `deploy/`:

| soubor | k čemu je |
|---|---|
| `mapa_template.html` | šablona s kotvami, ze které flow skládá výslednou stránku |
| `procesni_mapa.html` | hotová mapa z dnešních (anonymizovaných) dat — aby bylo co otevřít hned, než flow poprvé proběhne |

**Ověření:** oba soubory jsou v knihovně vidět a mají nenulovou velikost
(94 kB a 13 kB).

## 2. Najít adresu, kterou se mapa ZOBRAZÍ (ne stáhne)

**Ověřeno 20.08.2026: klik na soubor v knihovně mapu zobrazí.** Publikační
flow tedy smysl má a hlavní riziko projektu padlo. Zbývá dílčí, ale otravná
věc: **tlačítko „Zobrazit v HTML" v appce soubor stáhne do Downloads.**

Rozdíl není v souboru, ale v adrese. Knihovna otevírá soubor náhledovou
stránkou SharePointu, kdežto appka volá `Launch()` na přímou cestu
`…/SiteAssets/procesni_mapa.html` — a na tu SharePoint kvůli *Strict browser
file handling* pošle `Content-Disposition: attachment`, tedy „stáhni".

### Cesta A — najít funkční adresu (zkus první, je to na dvě minuty)

Vlož do konzole (F12) na libovolné stránce cílového webu obsah
**`src/zjisti_url_mapy.js`**. Skript si web odvodí z adresy stránky, u šesti
kandidátních adres **změří hlavičku odpovědi** a vypíše tabulku
`varianta → ZOBRAZÍ SE / STÁHNE SE`.

Pošli řádek té varianty, která se zobrazí — dosadí se do `varMapaUrl`
v `App.OnStart`. Je to **jediné místo v appce**, kde je adresa mapy zapsaná.

Rychlejší varianta téhož, když se ti nechce spouštět skript: klikni na soubor
v knihovně, počkej, až se mapa zobrazí, a **zkopíruj adresu z adresního
řádku**. Ta je z definice ta správná.

### Cesta B — stránka s web partem Vložit (když se stáhne úplně všechno)

Spolehlivější v tom smyslu, že nezávisí na tom, jak tenant servíruje soubory
z knihoven: **stránky se nestahují nikdy.**

1. Na webu **Nová → Stránka**, pojmenovat „Procesní mapa".
2. Přidat web part **Vložit (Embed)** a vložit:
   ```html
   <iframe src="/sites/DigiData_D/testovaci_subsajta/procesnimapa/SiteAssets/procesni_mapa.html"
           style="width:100%;height:900px;border:0"></iframe>
   ```
3. Publikovat a adresu stránky dát do `varMapaUrl`.

Mapa v iframu poběží: SharePoint ho sice servíruje jako sandbox
(`about:srcdoc`, `connect-src 'none'`), ale **data jsou zapečená přímo
ve stránce**, takže nic nefetchuje a CSP jí nevadí. Přesně tuhle cestu
nakonec zvolil FloorPlan.

Cena: náhledová oblast bývá užší než celá šířka okna — modern pages ani
full-width sekce v tomhle tenantu k dispozici nejsou. Mapa je responzivní,
takže to není vada, jen menší plocha.

### Ještě zkontroluj konzoli

Až mapa poběží, otevři F12 → Console a ověř, že tam není
`securitypolicyviolation`. Mapa žádná externí data netahá, takže by být
neměla — ale je to levné ověření.

## 3. Zapnout a spustit MapaPublishFlow

Flow je v balíku hotové (14 akcí), ale importem se **nezapne** — import stav
zapnutí nemění.

1. Power Automate → Solutions → *procesnimapa* → `MapaPublishFlow` → **Turn on**.
2. **Run** (ruční spuštění, trigger je PowerApps V2).

**Ověření po běhu:**

| co zkontrolovat | očekávaný výsledek |
|---|---|
| běh doběhl zeleně | ano |
| výstup kroku `Nacti_DilciProcesy` | **250 položek**, ne 100 — tohle je nejpravděpodobnější tichá chyba |
| `procesni_mapa.html` v Site Assets | změněný čas úpravy |
| stáhni soubor a hledej v něm | žádné `__DATA_JSON__` ani `__GEN__`; přítomné `"agendy":`, `"procesy":`, `"dilci_procesy":`, `"aktivity":`, `"vazby":` |
| hlavička mapy | razítko „vygenerováno DD.MM.RRRR HH:MM" s časem běhu |
| `Create file` nad existujícím souborem | přepsal, nezaložil `procesni_mapa1.html`. Kdyby zakládal kopii, vyměň akci za `Update file` |

**Změna se propíše:** změň název jedné aktivity v listu `Aktivity`, spusť flow
znovu, nová hodnota musí být v mapě.

## Co v tomto balíku ještě není

**Tlačítko „Obnovit mapu" v appce.** `MapaPublishFlow` není v canvas appce
zaregistrované jako datový zdroj — v `.msapp` jsou jen SharePoint listy —
takže vzorec `MapaPublishFlow.Run()` by Studio odmítlo hláškou „Name isn't
valid". Doplní se takto:

1. Ve Studiu otevři appku → **Power Automate** → **Add flow** → `MapaPublishFlow`.
2. Ulož, publikuj, exportuj solution jako unmanaged a dodej zip.
3. Do souhrnné karty na `scr_Seznam` přibude třetí tlačítko:

```
btn_ObnovitMapu.OnSelect:
    =Set(varPublikuji, true);
    IfError(
        MapaPublishFlow.Run();
        Notify("Mapa se přegenerovala z aktuálních dat.", NotificationType.Success),
        Notify("Publikace selhala: " & FirstError.Message, NotificationType.Error)
    );
    Set(varPublikuji, false)

btn_ObnovitMapu.DisplayMode:
    =If(varPublikuji, DisplayMode.Disabled, DisplayMode.Edit)
```

`DisplayMode` je proti dvojímu kliknutí — flow běží několik sekund a bez toho
se dá spustit dvakrát za sebou.

## Kdy publikaci automatizovat

Flow má dnes jen ruční trigger, protože ho tak založil designer. Až bude
zobrazení ověřené (krok 2) a tlačítko v appce hotové, dává smysl přidat
`Recurrence` 1× denně — pak je mapa nanejvýš den stará i bez toho, aby na
tlačítko někdo klikl. Trigger v Power Automate může být jen jeden, takže to
znamená **druhé** flow se stejnými akcemi, ne úpravu tohoto.
