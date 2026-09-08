"""Běhový test mapy v headless prohlížeči — ovládací prvky se opravdu kliknou.

Statická brána (src/check_mapa_html.py) hlídá, že prvky a pravidla existují.
Tenhle test spustí stránku v Edge/Chrome, provede v ní úkony (přepnutí stupně
rozbalení, odškrtnutí kódu, změna velikosti písma, klik na aktivitu) a přečte
výsledný DOM. Chytá to, co statická kontrola nemůže: že přepínač nic nedělá.

Spouštět z kořene projektu:  python src/check_mapa_beh.py
Návratový kód 0 = v pořádku, 1 = nalezena chyba.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

STRANKA = Path("viz/mapa_prototyp.html")
PRACOVNI = Path("runs/mapa_beh")
PROHLIZECE = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
)

# Úkony se dělají v pořadí a každý zapíše, co po něm v DOM zbylo. Držet je
# v jednom průchodu je schválně — testuje se i to, že se volby nepřebíjejí.
SCENAR = """
<script id="test-scenar">
(function(){
  const out = {};
  const vidi = el => el && !el.classList.contains("hide");
  const kids = lvl => document.querySelector(".lvl-" + lvl + " > .kids");

  /* Scénář zkouší STROM, ale výchozím zobrazením je od F21/F22 rozklad —
     bez tohohle přepnutí je `#tree` prázdný a všechno níž padá na prázdném
     DOM. Zobrazení se čte z aria-pressed, tak se tlačítko musí kliknout. */
  out.vychoziZobrazeni = document.querySelector(
      "#fZobrazeni button[aria-pressed=true]").dataset.zobrazeni;
  document.querySelector("#fZobrazeni button[data-zobrazeni=strom]").click();

  out.vychoziKod       = !document.body.classList.contains("bez-kodu");
  out.vychoziUroven    = document.getElementById("fUroven").value;
  out.vychoziProcesy   = vidi(kids("a"));
  out.vychoziDilci     = vidi(kids("p"));
  out.titulekAgendy    = (document.querySelector(".lvl-a > .row") || {}).title || "";
  out.titulekAktivity  = "";
  out.pocetKodu        = document.querySelectorAll(".kod").length;

  // 1) stupeň rozbalení 3 = dílčí procesy vidět, aktivity ne
  const uroven = document.getElementById("fUroven");
  uroven.value = "3"; uroven.dispatchEvent(new Event("change"));
  out.u3Dilci    = vidi(kids("p"));
  out.u3Aktivity = vidi(kids("d"));

  // 2) stupeň 4 = i aktivity
  uroven.value = "4"; uroven.dispatchEvent(new Event("change"));
  out.u4Aktivity = vidi(kids("d"));

  // 3) stupeň 1 = sbaleno hned pod agendami
  uroven.value = "1"; uroven.dispatchEvent(new Event("change"));
  out.u1Procesy = vidi(kids("a"));

  uroven.value = "4"; uroven.dispatchEvent(new Event("change"));
  const aktRow = document.querySelector(".lvl-k > .row");
  out.titulekAktivity = aktRow ? aktRow.title : "";

  // 4) vypnutí kódu
  const cKod = document.getElementById("cKod");
  cKod.checked = false; cKod.dispatchEvent(new Event("change"));
  out.poVypnutiKod = document.body.classList.contains("bez-kodu");
  out.kodStaleVDom = document.querySelectorAll(".kod").length;   // skrývá se CSS, ne mazáním

  // 5) velikost písma
  document.querySelector('#fVelikost button[data-fs="19"]').click();
  out.fs = document.documentElement.style.getPropertyValue("--fs").trim();
  out.fsPressed = document.querySelector('#fVelikost button[aria-pressed="true"]').dataset.fs;

  // 6) klik na aktivitu naplní detail
  if (aktRow) aktRow.click();
  out.detail = document.getElementById("detailBody").textContent.slice(0, 120);

  // 7) hledání rozbaluje bez ohledu na stupeň
  uroven.value = "1"; uroven.dispatchEvent(new Event("change"));
  const q = document.getElementById("q");
  q.value = "informa"; q.dispatchEvent(new Event("input"));
  out.hledaniRozbalilo = vidi(kids("a"));
  out.hledaniNaslo = document.querySelectorAll("mark").length;

  // 8) filtr stavu aktivit (nahradil filtr zmapované/nezmapované)
  q.value = ""; q.dispatchEvent(new Event("input"));
  uroven.value = "4"; uroven.dispatchEvent(new Event("change"));
  const fStav = document.getElementById("fStav");
  /* Uvnitř #tree, ne globálně: rozklad kreslí karty s TÝMIŽ třídami
     (`rz-uzel lvl-k`) a zůstává v DOM i po přepnutí na strom, takže
     globální selektor sčítal obě zobrazení a "vše" vycházelo dvojnásobně. */
  const aktivit = () => document.querySelectorAll("#tree .lvl-k").length;
  const vetvi   = () => document.querySelectorAll("#tree .lvl-d").length;
  out.stavVolby   = [...fStav.options].map(o => o.value);
  out.stavVse     = aktivit();
  out.vetviVse    = vetvi();
  fStav.value = "schváleno"; fStav.dispatchEvent(new Event("change"));
  out.stavSchvaleno = aktivit();
  out.vetviSchvaleno = vetvi();
  fStav.value = "pracovní"; fStav.dispatchEvent(new Event("change"));
  out.stavPracovni = aktivit();
  fStav.value = ""; fStav.dispatchEvent(new Event("change"));

  // 9) chip osiřelých
  const cOsirele = document.getElementById("cOsirele");
  out.osireleVychozi = cOsirele.checked;
  out.osireleZakazany = cOsirele.disabled;
  if (!cOsirele.disabled){
    cOsirele.checked = true; cOsirele.dispatchEvent(new Event("change"));
    out.osireleKorenu = document.querySelectorAll("#tree > .node").length;
    out.osireleJenNezarazene = [...document.querySelectorAll("#tree > .node > .row > .nm")]
      .every(x => x.textContent.startsWith("Nezařazené"));
    cOsirele.checked = false; cOsirele.dispatchEvent(new Event("change"));
  }
  out.korenuPoVraceni = document.querySelectorAll("#tree > .node").length;

  // 10) hlavička neuvádí jméno osoby
  out.meta = document.getElementById("meta").textContent;

  /* Buňka s víc útvary („111; 113") se musí rozpadnout na jednotlivé kódy.
     Do 08.09.2026 mapa dělila čárkou, takže dvojice zůstala v nabídce vcelku
     a filtrovat podle jednoho z nich nešlo. V datech to vidět nebylo —
     žádná aktivita víc útvarů nemá —, proto se to zkouší na hodnotě
     dosazené sem, ne na tom, co je v rejstříku. */
  out.utvarySeznam = (typeof utvarySeznam === "function")
      ? utvarySeznam("111; 113") : ["<funkce chybí>"];
  out.utvaryCarka  = (typeof utvarySeznam === "function")
      ? utvarySeznam("111,113") : ["<funkce chybí>"];

  const pre = document.createElement("pre");
  pre.id = "vysledek-testu";
  pre.textContent = JSON.stringify(out);
  document.body.appendChild(pre);
})();
</script>
"""

chyby = []
kontrol = 0


def overit(podminka, popis):
    global kontrol
    kontrol += 1
    if not podminka:
        chyby.append(popis)


def main():
    if not STRANKA.exists():
        print(f"CHYBA: chybí {STRANKA} — spusť nejdřív src/build_mapa.py")
        return 1
    prohlizec = next((p for p in PROHLIZECE if p.exists()), None)
    if prohlizec is None:
        print("CHYBA: nenalezen Edge ani Chrome pro headless běh")
        return 1

    PRACOVNI.mkdir(parents=True, exist_ok=True)
    testovaci = PRACOVNI / "test.html"
    html = STRANKA.read_text(encoding="utf-8")
    assert html.count("</body>") == 1
    testovaci.write_text(html.replace("</body>", SCENAR + "</body>"), encoding="utf-8")

    beh = subprocess.run(
        [str(prohlizec), "--headless", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=4000", "--dump-dom", testovaci.resolve().as_uri()],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    dom = beh.stdout
    m = re.search(r'<pre id="vysledek-testu">(.*?)</pre>', dom, re.S)
    if not m:
        print("CHYBA: scénář v prohlížeči nedoběhl — v DOM není výsledek.")
        print("stderr:", beh.stderr[-800:])
        return 1
    r = json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")
                   .replace("&lt;", "<").replace("&gt;", ">"))

    overit(r["vychoziKod"] is True, "kódy nejsou ve výchozím stavu zapnuté")
    overit(r["pocetKodu"] > 0, "ve stromu nejsou žádné kódy")
    overit(r["vychoziZobrazeni"] == "rozkladH",
           f"výchozím zobrazením není vodorovný rozklad ({r['vychoziZobrazeni']})")
    overit(r["vychoziUroven"] == "4",
           f"výchozí stupeň rozbalení není 4 ({r['vychoziUroven']})")
    overit(r["vychoziProcesy"] is True, "při výchozím stupni nejsou vidět procesy")
    overit(r["vychoziDilci"] is True,
           "při výchozím stupni 4 nejsou vidět dílčí procesy")
    overit(r["u3Dilci"] is True, "stupeň 3 nerozbalil dílčí procesy")
    overit(r["u3Aktivity"] is False, "stupeň 3 rozbalil i aktivity")
    overit(r["u4Aktivity"] is True, "stupeň 4 nerozbalil aktivity")
    overit(r["u1Procesy"] is False, "stupeň 1 nesbalil procesy")

    overit(r["titulekAgendy"].startswith("Agenda "),
           f"nápověda agendy neříká typ: {r['titulekAgendy'][:60]!r}")
    overit(r["titulekAktivity"].startswith("Aktivita "),
           f"nápověda aktivity neříká typ: {r['titulekAktivity'][:60]!r}")

    overit(r["poVypnutiKod"] is True, "odškrtnutí kódu nepřepnulo třídu bez-kodu")
    overit(r["kodStaleVDom"] == r["pocetKodu"],
           "kódy se při vypnutí mažou z DOM místo skrytí — hledání podle kódu by přestalo fungovat")

    overit(r["fs"] == "19px", f"přepínač velikosti nenastavil --fs ({r['fs']!r})")
    overit(r["fsPressed"] == "19", "aktivní stupeň velikosti není zvýrazněný")

    overit(len(r["detail"]) > 20 and "Klikni" not in r["detail"],
           f"klik na aktivitu nenaplnil detail: {r['detail'][:60]!r}")

    overit(r["utvarySeznam"] == ["111", "113"],
           f"buňka „111; 113\" se nerozdělila na jednotlivé útvary "
           f"({r['utvarySeznam']}) — filtr útvaru by na ně nenašel nic")
    overit(r["utvaryCarka"] == ["111", "113"],
           f"čárkou oddělené útvary se nerozdělily ({r['utvaryCarka']}) — "
           f"import je propustí, takže je mapa musí umět taky")

    overit(r["hledaniRozbalilo"] is True, "hledání nerozbalilo strom navzdory stupni 1")
    overit(r["hledaniNaslo"] > 0, "hledání nic nezvýraznilo")

    # Filtr stavu aktivit — od 24.08.2026 místo zmapované/nezmapované, aby
    # mapa filtrovala touž věcí jako přehled v appce.
    overit(r["stavVolby"] == ["", "schváleno", "pracovní"],
           f"volby filtru stavu nejsou vše/schváleno/pracovní ({r['stavVolby']})")
    overit(r["stavVse"] > 0, "při stavu „vše“ nejsou vidět žádné aktivity")
    overit(r["stavSchvaleno"] + r["stavPracovni"] == r["stavVse"],
           f"schválené ({r['stavSchvaleno']}) a pracovní ({r['stavPracovni']}) nedají "
           f"dohromady všechny aktivity ({r['stavVse']}) — aktivita bez vyplněného "
           f"stavu se ztrácí v obou filtrech")
    overit(r["vetviSchvaleno"] <= r["vetviVse"],
           "filtr stavu neschoval větve, ve kterých po odfiltrování nic nezbylo")

    # Chip osiřelých
    overit(r["osireleVychozi"] is False, "chip osiřelých je zapnutý hned po otevření")
    if not r["osireleZakazany"]:
        overit(r["osireleJenNezarazene"] is True,
               "zapnutý chip osiřelých nechal ve stromu i větve s živým předkem")
        overit(r["osireleKorenu"] < r["korenuPoVraceni"],
               "zapnutý chip osiřelých strom nezúžil")
    overit(r["korenuPoVraceni"] > 0, "po vypnutí chipu osiřelých zůstal strom prázdný")

    # A-08: jméno správce v hlavičce mapy
    overit("správce" not in r["meta"] and "Ing." not in r["meta"],
           f"hlavička mapy uvádí jméno osoby: {r['meta'][:80]!r}")

    print(f"kontrol: {kontrol}, chyb: {len(chyby)}   (prohlížeč: {prohlizec.name})")
    if chyby:
        for c in chyby:
            print("CHYBA:", c)
        print("\nNEPROŠLO")
        return 1
    print("\nOK — ovládací prvky mapy v prohlížeči fungují")
    return 0


if __name__ == "__main__":
    sys.exit(main())
