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

## 2. Ověřit, že tenant HTML zobrazí a nestáhne

**Tohle je jediná neověřená věc celého řešení a rozhoduje o tom, jestli
publikační flow má vůbec smysl.** V PPF tenantu se `.html` ze Site Assets
kvůli nastavení *Strict browser file handling* může místo zobrazení stáhnout;
u FloorPlanu se to tak chovalo.

V knihovně klikni na `procesni_mapa.html`.

| co se stane | co to znamená |
|---|---|
| stránka se otevře a strom jde rozbalovat | funguje, pokračuj krokem 3 |
| prohlížeč soubor **stáhne** | tudy cesta nevede — zobrazení se musí přesunout do canvas appky (HTML viewer control) a publikační flow se zahodí |

Když se stránka otevře, ještě otevři F12 → Console a zkontroluj, že tam není
`securitypolicyviolation`. Mapa žádná externí data netahá (vše je zapečené),
takže by být neměla — ale je to levné ověření.

**Tlačítko „Zobrazit v HTML"** v appce míří přesně na tento soubor. Adresu drží
`varMapaUrl` v `App.OnStart` a je to jediné místo, kde je zapsaná.

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
