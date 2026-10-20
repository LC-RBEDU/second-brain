# Plán: rbedu-grammar-nazi (rename + scope)

Autor: rbu-architect · otevření #1 · k=1 · r=1  
Ledger: [docs/plans/2026-10-08-rbedu-grammar-nazi-rename.pipeline.md](./2026-10-08-rbedu-grammar-nazi-rename.pipeline.md)  
Parent DONE: [docs/plans/2026-10-07-grammar-nazi-zapisy.md](./2026-10-07-grammar-nazi-zapisy.md) (R1–R21, A18/A33, GN-1/GN-2)

## Zadání a požadavky

| R# | Požadavek | Zdroj |
|---|---|---|
| R1 | Přejmenovat skill `grammar-nazi` → `rbedu-grammar-nazi` (složka, `name:` ve frontmatter, odkazy, Claude ZIP). | Zadání doslovně; D2 |
| R2 | Rozšířit scope na obecné texty týmu RB EDU: e-maily, Slack (delší), dokumenty, wiki, prezentace, artefakty (+ zápisy). | Zadání; WIP `SKILL.md` description |
| R3 | Zachovat **přísný režim zápisu** s fingerprint CLI (parent A18/A33, GN-1/GN-2 flow, whitelist faktů). | Zadání; parent R5/R9/R13/R17/R21; D1 |
| R4 | Průchod **vždy in-process** — bez Cursor agenta `grammar-nazi`. | Zadání; D2; WIP `agenda-zapis` |
| R5 | Aktualizovat `install_agenda_skills.sh`, pytest cestu, napojení `agenda-zapis-ze-schuzky`, Claude `dist/` + ZIP. | Zadání |
| R6 | Odstranit starý skill `ŠABLONY/skills/grammar-nazi/**` a `ŠABLONY/cursor-agents/grammar-nazi.md`. | Zadání |
| R7 | Fingerprint algoritmus **neměnit** (jen cesty / docstring rename). | Brief mimo rozsah; D5 |
| R8 | IMPLEMENT = dovést/opravit WIP dle plánu, ne greenfield. | D5 |
| R9 | TESTER přeskočen (profil SECOND_BRAIN). | D4 |
| R10 | Schvalování plánu uživatelem: ne. | D3 |

**Mimo rozsah:** Coolify / `vps/second-brain-hub` cron; wiki-firemni-priority WIP; nový Cursor agent; změna A18 fingerprint logiky; RB Universe / Alembic / RBAC; přepis historických parent plánů `2026-10-07-*`.

**Delta vs parent:**

| Zůstává (parent kontrakt) | Mění se (tato delta) |
|---|---|
| A18 pole fingerprintu, exit 0/1/2 (A33), fixtures semantics | Cesty `grammar-nazi` → `rbedu-grammar-nazi` |
| GN-1/GN-2 flow, merge A26+A31, Krok 8 A32, meta A29 | Scope: režim **obecný** + `language-rules.md` |
| Whitelist faktů, citáty, cardinality | In-process only; **smazání** Cursor agenta |
| `rbe-writing-style` exclusion zápisů (parent R10) | ZIP jméno/obsah + `language-rules.md`; install orphan cleanup |

## Předpoklady

| A# | Předpoklad | Proč |
|---|---|---|
| A1 | Diff `md_fingerprint.py` HEAD↔WIP = **jen docstring** (`grammar-nazi gate` → `rbedu-grammar-nazi gate`). **Ověřeno 2026-10-08** `diff -u` exit 0, jediný hunk docstring. | R7 |
| A2 | Správný název stylového skillu je **`rbe-writing-style`**, ne `rbedu-writing-style` v WIP. | Existuje `ŠABLONY/skills/rbe-writing-style/` |
| A3 | Globální `~/.cursor/rules/mrluc-agent-skills.mdc` se musí sladit s repo `.cursor/rules/` (repo už má `rbedu-grammar-nazi`). | Sync |
| A4 | Stale symlinky `~/.cursor/skills/grammar-nazi` a `~/.cursor/agents/grammar-nazi.md` po delete zůstanou, dokud je install **explicitně neuklidí**. | Install jen linkuje |
| A5 | `HANDOFF_cowork.md` je historický — default: krátká hlavička „DONE/superseded“. | Konflikt s R6 |
| A6 | Claude ZIP musí obsahovat kořen `rbedu-grammar-nazi/` + `language-rules.md` + meeting-language + CLI + SKILL; ne `dist/` uvnitř. | INSTALL |
| A7 | Parent B# pro zápis zůstávají; ruční T3 GN jazyk se v deltě neopakuje jako gate, pokud se nemění language text smysluplně. | D1 |
| A8 | Historické `docs/plans/2026-10-07-*` se nepřepisují. | Historie |

## Současný stav (ověřeno)

| Soubor | Fakta |
|---|---|
| `grammar-nazi/**` | Deleted ve WT |
| `cursor-agents/grammar-nazi.md` | Deleted ve WT |
| `rbedu-grammar-nazi/SKILL.md` | Širší scope; režimy; **typo** `rbedu-writing-style` ř. 72–74 |
| `meeting-language.md` ř. 15 | Typo `rbedu-writing-style` |
| `md_fingerprint.py` | Jen docstring rename (A1) |
| `install_agenda_skills.sh` | Loop `rbedu-grammar-nazi/`; chybí orphan cleanup |
| `test_md_fingerprint.py` | CLI path rbedu |
| `agenda-zapis-ze-schuzky/SKILL.md` | In-process; cesty rbedu |
| Repo `.cursor/rules/mrluc-agent-skills.mdc` | Už rbedu |
| Globál `~/.cursor/rules/…` | Stále grammar-nazi — mezera |
| `HANDOFF_cowork.md` | Stale |

## Návrh

### F0 — Gate fingerprint (R7)
- Diff ověřen (A1). Před pushem: `python3 -m pytest scripts/tests/test_md_fingerprint.py -q`.

### F1 — Opravy WIP
| Soubor | Co |
|---|---|
| `SKILL.md` | `rbedu-writing-style` → `rbe-writing-style` |
| `meeting-language.md` | totéž |
| `HANDOFF_cowork.md` | hlavička DONE/superseded |
| ZIP | přegenerovat pokud listing selže (T8) |

**ZIP (A23'):** `ŠABLONY/skills/rbedu-grammar-nazi/dist/rbedu-grammar-nazi-claude.zip` — root `rbedu-grammar-nazi/` = SKILL + language-rules + meeting-language + md_fingerprint (+ fixtures) ; ne HANDOFF, ne nested dist.

### F2 — Deletes (R6) — potvrdit ve status
### F3 — Install orphan cleanup
Doplnit do `install_agenda_skills.sh`: rm `$DEST/grammar-nazi` a `$AGENTS_DEST/grammar-nazi.md` pokud existují.
### F4 — Audit agenda-zapis — žádný návrat Cursor agenta
### F5 — Sync globál mrluc rule na znění repo
### F6 — Plný pytest gate

### Commit set (include)
`rbedu-grammar-nazi/**`, deletes grammar-nazi + cursor-agent, install, test_md_fingerprint, agenda-zapis SKILL + struktura-vystupu, skills README, repo mrluc rule, claude-project-instructions, tento plán + ledger.

### Exclude
wiki-firemni-priority WIP, Claude outputs, playwright, nesouvisející M.

### Mezery WIP (G#)
| # | Nález | Fix |
|---|---|---|
| G1 | typo rbedu-writing-style | F1 |
| G2 | globál mrluc starý | F5 |
| G3 | install orphan | F3 |
| G4 | HANDOFF stale | F1 |
| G5 | ZIP listing | F1 T8 |

## Kontrakt chování (B#)

| B# | Očekávání | R# | T# |
|---|---|---|---|
| B1 | DEEP#1: capture→GN-1 in-process→compare 0 | R3 | T2 |
| B6′ | In-process; ZIP A23'; žádný cursor-agent grammar-nazi | R4,R1 | T4,T8,T1 |
| B10–B15,B17,B19,B23–B24,B26 | Fingerprint CLI stejné exit/pole; cesta rbedu | R3,R7 | T6,T7 |
| B16 | compare fail → 1× retry in-process; 2. fail → stop | R3,R4 | T2 |
| B20 | rbe-writing-style exclusion zápisů | parent | T5 |
| B27 | Bez Meta → režim obecný; bez fingerprint | R2 | T9 |
| B28 | S Meta / meeting_summary → zápis + fingerprint | R2,R3 | T2,T9 |
| B29 | Žádná instrukce volat Cursor agent grammar-nazi | R4 | T5 |
| B30 | Po install: symlink rbedu; neexistuje grammar-nazi skill/agent | R5,R6 | T1 |
| B31 | Konflikt claim/hlas → vyhrává rbe-writing-style | R2 | T9 |
| B32 | Uživatelský text bez žádosti → nabídnout, nepřepisovat | R2 | T9 |
| B33 | Chat/UI short → nespouštět | R2 | T9 |
| B34 | grep grammar-nazi v aktivních skills/rules = 0 (exclude docs/plans/2026-10-07*) | R1,R6 | T5 |

Parent B2–B5, B7–B9, B18, B21–B22, B25 zůstávají (reuse).

## Výkonový rozpočet (P)
CLI capture+compare &lt; 1 s na `valid-full.md`; 0 SQL; 0 Coolify.

## Testy (T#)

| T# | Typ | Co |
|---|---|---|
| T1 | shell | install + existence rbedu symlink + absence grammar-nazi |
| T2 | ruční | agenda-zapis GN flow (reuse parent) |
| T3 | ruční | jen při změně language textu |
| T4 | ruční | Claude ZIP upload poznámka |
| T5 | grep | B20,B29,B34 |
| T6/T7 | pytest | test_md_fingerprint.py |
| T8 | shell | unzip -l ZIP listing |
| T9 | doc | B27,B31–B33 |
| T10 | shell | F0 diff (hotovo) |

**TESTER: přeskočeno (profil SECOND_BRAIN)**  
Gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q`

## Pořadí implementace
1 F0 (done) → 2 F1 → 3 F2 → 4 F3+T1 → 5 F4+T5 → 6 F5 → 7 F6 pytest → 8 commit (až na žádost) → REVIEW → QA → TESTER skip → DONE

## Rizika
1. Orphan symlinky 2. Starý Claude ZIP 3. Typo rbe 4. HANDOFF 5. Širší auto-trigger obecného režimu 6. Historické plány v grep 7. Nečekaný fingerprint diff (mitigováno A1)

## Otevřené otázky pro uživatele
1. HANDOFF: default DONE hlavička. 2. Parent plány: default ne. 3. Claude re-upload: default po merge ručně.
