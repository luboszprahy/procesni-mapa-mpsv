# STATUS — Procesní mapa MPSV

Aktualizováno: 2026-08-18

## Hotovo

- Založena projektová struktura (`input/`, `src/`, `deploy/`, `runs/`, `viz/`).
- Podklady přesunuty do `input/`, textové výtahy vygenerovány do `input/extracted/`.
- Prostudovány všechny podklady, doménový model shrnut v `CLAUDE.md`.
- Načten skill `power-Apps-skill` (pozor: popisuje prostředí PPF Banky, ne MPSV —
  platí technické vzory, ne naming/tenant).
- Git repozitář inicializován a pushnut na GitHub (privátní).

## Zbývá

- **Rozhodnout rozsah a cíl řešení** — probíhá diskuse s uživatelem.
  Otevřené otázky: cílový tenant a prostředí, kdo je uživatel (správce rámce vs.
  útvary), jestli se dělá jen mapa (read-only) nebo i editace, licence Power BI.
- PRD.md (podle pravidla #9) — až po dohodě o rozsahu.
- PLAN.md (podrobný implementační plán s testovacími kroky) — po schválení PRD.
- Implementace.

## Next step

Dohodnout s uživatelem cíl a rozsah první iterace, pak sepsat `PRD.md`.
