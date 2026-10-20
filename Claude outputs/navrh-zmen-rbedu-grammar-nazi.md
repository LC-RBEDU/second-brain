# Návrh změn: sjednocení na `rbedu-grammar-nazi` (k potvrzení)

Nic z toho zatím není zapsané. Po tvém „ano“ změny aplikuji.

## A. Úpravy existujících souborů (vždy 1:1 náhrada názvu, pokud není uvedeno jinak)

| # | Soubor | Změna |
|---|---|---|
| 1 | `.cursor/rules/mrluc-agent-skills.mdc` ř. 19 | `grammar-nazi` (jen zápisy; agent `ŠABLONY/cursor-agents/grammar-nazi.md`) → `rbedu-grammar-nazi` (jazykový průchod textů; v zápisech GN-1/GN-2) |
| 2 | `docs/claude-project-instructions.md` ř. 149 | `grammar-nazi (jen zápisy; … ZIP ŠABLONY/skills/grammar-nazi/dist/grammar-nazi-claude.zip)` → `rbedu-grammar-nazi (jazykový průchod textů; v zápisech …; ZIP ŠABLONY/skills/rbedu-grammar-nazi/dist/rbedu-grammar-nazi-claude.zip)` |
| 3 | `scripts/install_agenda_skills.sh` ř. 11 | `"$SRC"/grammar-nazi/` → `"$SRC"/rbedu-grammar-nazi/` |
| 4 | `scripts/tests/test_md_fingerprint.py` ř. 13 | cesta `ŠABLONY/skills/grammar-nazi/scripts/md_fingerprint.py` → `ŠABLONY/skills/rbedu-grammar-nazi/scripts/md_fingerprint.py` |
| 5 | `ŠABLONY/skills/README.md` ř. 15 | řádek `grammar-nazi` → `rbedu-grammar-nazi` — Jazykový průchod textů týmu (automaticky při tvorbě textu; režim zápis volá `agenda-zapis-ze-schuzky`, GN-1/GN-2 + fingerprint) |
| 6 | `ŠABLONY/skills/agenda-zapis-ze-schuzky/references/struktura-vystupu.md` ř. 196 | `grammar-nazi` → `rbedu-grammar-nazi` |
| 7 | `ŠABLONY/skills/agenda-zapis-ze-schuzky/SKILL.md` | viz sekce B |

## B. `agenda-zapis-ze-schuzky/SKILL.md` (varianta B)

1. Zdroj pravdy: doplněno `jazykový průchod: ŠABLONY/skills/rbedu-grammar-nazi/`.
2. „Co skill dělá“: nový bod 2a — jazykový průchod přes `rbedu-grammar-nazi` (GN-1 / GN-2, s fingerprint kontrolou), běží u `full` i `shared`.
3. Odkaz „Krok Preview / grammar-nazi“ a nadpis sekce → `rbedu-grammar-nazi`.
4. Úvod sekce GN-1/GN-2 — původní text:

   > Skill: `ŠABLONY/skills/grammar-nazi/SKILL.md`. Cursor agent: `grammar-nazi` (readonly — vrátí MD; ty zapíšeš). Bez agenta / Claude / soft-fail Cursor agenta: stejný pass **in-process** (A4). Soft-fail = „bez agenta“, ne skip language pass. Až když selže i in-process (nejde načíst skill/MD) → **1 věta + stop write** (ne tichý skip).

   nový text:

   > Skill: `ŠABLONY/skills/rbedu-grammar-nazi/SKILL.md` (volá ho tento skill, ne naopak). Režim **zápis** (skill ho pozná podle `## 0. Meta`); běží u `variant: full` i `shared`. Průchod běží **vždy in-process**, bez Cursor agenta: načti SKILL + `references/language-rules.md` + `references/meeting-language.md`, přepiš celý MD, vrať jen MD, zapiš ty. Nejde-li skill/MD načíst → **1 věta + stop write** (ne tichý skip).

5. Dva příkazy `capture` / `compare`: cesta → `ŠABLONY/skills/rbedu-grammar-nazi/scripts/md_fingerprint.py`.
6. GN-1 krok 2: „GN-1 (agent; při soft-fail → in-process)“ → „GN-1 (in-process)“.
7. Preview: nový řádek „Jazykový průchod: proběhl / přeskočen (důvod)“.
8. Checklist: položka GN-1 / GN-2 doplněna o `rbedu-grammar-nazi`, in-process.

## C. Mazání (vyžaduje tvoje výslovné potvrzení)

| Co | Proč |
|---|---|
| `ŠABLONY/cursor-agents/grammar-nazi.md` | Cursor agent už nikdo nevolá (průchod je in-process). Install skript by ho jinak dál linkoval do `~/.cursor/agents/`. |
| `ŠABLONY/skills/grammar-nazi/` (celá složka) | Nahrazeno `rbedu-grammar-nazi/`. Doporučuju smazat až po nahrání zipu do Claude a ověření. |

## D. Záměrně nechávám

- `docs/plans/2026-10-07-grammar-nazi-zapisy.md` a `.pipeline.md`: historický plán a ledger, kde je starý název správně v kontextu své doby. Uvedu to jako *Inference*: přepisovat historii nedoporučuju, ale pokud chceš, přidám na začátek poznámku „přejmenováno na rbedu-grammar-nazi“.

## E. Pozor: pytest a git

- Úpravy 3 a 4 jsou kód. Pytest ani commit v tomto sezení nespouštím; `pytest scripts/tests/test_md_fingerprint.py` pusť v Cursoru po aplikaci. Ve `git status` jsou už teď jiné neuložené změny (nejsou moje).
