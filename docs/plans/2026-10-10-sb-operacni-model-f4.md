# Plán: F4 — Úklid Obsidian/Drive/poll + Claude artifact dashboard

> Architekt: **k=1 · r=6** (otevření #1) · orphan CAS + dry-run  
> Parent F0 (SCHVÁLENO): [2026-10-10-sb-operacni-model-f0.md](2026-10-10-sb-operacni-model-f0.md) · F1 DONE · F2 DONE · F3 DONE 2026-10-11 tip `7e63304` (výhrady B18/T8/B21/Grok prep webhook — neblokují F4)  
> Pipeline ledger: [2026-10-10-sb-operacni-model-f4.pipeline.md](2026-10-10-sb-operacni-model-f4.pipeline.md)  
> Vault: **SB15 — Nový operační model SB** (**SB15-5** F4)  
> Profil: **SECOND_BRAIN**. Base tip před pipeline: `7e63304962eba5bb1f769d9d90ed40b6c71696f9`.  
> Schvalování plánu uživatelem: **ne**. TESTER: přeskočeno (profil SECOND_BRAIN).

## Zadání a požadavky

R1 — Po F3 DONE spustit F4 pipeline (uživatel: „ok a můžeme teď tedy dál na F4?“; kotva **SB15-5**).

R2 — Scope F4 z F0 tabulky F4: stop `slack_poll` dump; Drive jen R9 výjimky; Obsidian nepovinný pull-only; Claude artifact dashboard; sync-architecture docs. (F0 F4 L317–323)

R3 — Pokryté F0 R#: **R7, R9, R15, R24**. (F0 F4)

R4 — Vstup: F3 parity — živá Slack triáž (`slack_live` + eyes/gear) a Gmail hybrid L1 existují; dump byl F3 provozní default do F4 (F3 R6/R8/Q4). F4 **přepíná** default L1 Slack z dump → live. (F0 migrace krok 9; F3 R6)

R5 — Stop `slack_poll` dump = cron přestane zapisovat do `01-INBOX/slack/`; watchlist dump `_vN` už není SSOT fronta. Live tool `slack_live` / `get_triage_candidates(include_live_slack=…)` zůstává. (F0 R11, R7; F0 Riziko 8)

R6 — Drive: vault SSOT = git (F1 cutover hotovo). F4 = **žádný provozní vault write přes Drive**; Drive jen R9 (Google-native / sdílené / nad LFS limitem F1) + read příloh pro `prepare_meeting` (F3 A29). (F0 R7, R9)

R7 — Obsidian: nepovinný; pokud se používá, jen nad git klonem **fetch/pull only** (žádný Obsidian Sync writer, žádný Drive Desktop writer). Systém nesmí záviset na Obsidian runtime. (F0 R7, R24)

R8 — Dashboard = **Claude artifact** napojený na Brain API (`get_context` / light projection); fail-path = MCP App / chat `get_context` / Slack brief; **ne** VPS web dashboard. (F0 R15, A9, Q6a)

R9 — Docs: přepsat `vps/second-brain-hub/docs/sync-architecture.md` (+ odkazy v README/runbook) na cílový git SSOT + R9 Drive + pull-only Obsidian + artifact. Legacy Drive tok označit historicky. (brief)

R10 — Autonomie beze změny F3: vault přes Brain; navenek propose→approve→client apply. F4 nepřidává OAuth Brain apply (post-F3 dluh zůstává). (F3 R4/R17)

R11 — Schvalování plánu: **ne**. Po QA: odškrtnout **SB15-5**. TESTER přeskočen. (brief + profil)

R12 — Gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests vps/second-brain-brain/tests -q`; QA = Coolify hub+brain dle README + dry-run kde dává smysl. Ostrý vault write jen tam, kde T# výslovně říká (archiv dumpů).

R13 — F3 výhrady (B18 OS push, T8/Cursor apply díry, B21 prep schedules, Grok meeting-prep webhook) **neřeší** F4, pokud neblokují artifact/fail-path. (brief)

R14 — **agenda-reply:** žádný nový zápis do `01-INBOX/slack/`; zdroj = live Slack / permalink. (rozhodnutí 2026-10-11)

R15 — **CAS archiv:** rozšířit `GitVault.move(..., expect_oid=)`; one-shot archiv volá CAS; konflikt = žádný přesun. (rozhodnutí 2026-10-11)

**Mimo rozsah:** F5 boti / Saturnin; bulk FM wikilinky→ID/slug (F0 krok 10); Mac local vault edit/push; obnovení n8n Gmail/mobile/Slack INBOX writers; All Mail/Spam; anomaly proaktivita; OAuth Brain apply + signed approve token; povinný Claude/Grok client-apply smoke; hard GitHub ruleset A17 Pro; smazání `DriveVault` kódu (zůstává legacy/rollback); nové Universe FE.

**Netýká se:** Alembic, RBAC Universe FE, subnav/hub dlaždice, `qa_gate.mjs`, Playwright-T6 / `rbu-tester`, Celery, Universe SQL P.

**Odchylky / návaznost na F3:**  
- F3 B5 „default L1 = dump“ → F4 **default L1 Slack = live** (F0 R11 cíl).  
- F3 B23 „slack_poll dump + eyes“ → F4 dump **off**; eyes/gear zůstávají v `slack_live` queries.  
- F3 P9 slack_poll budget → F4 neplatí pro cron dump (poll cron off).

---

## Předpoklady

A1 — F3 tip `7e63304` live: Brain `https://brain.cyprovi.cz`, MCP write, `VAULT_BACKEND=git`, `GIT_VAULT_PUSH=1`, shared WC `/data/vault`. Coolify hub crontab stále spouští `slack_poll.py` (`*/2 8-23`).

A2 — `slack_live` už umí eyes/gear a **0 dump write** (`app/tools/slack_live.py`). Parita pro stop dump = skill + `get_triage_candidates` default flip + crontab off — ne nový Slack search engine.

A3 — Před stop dump: export/záloha `00-System/slack-poll-state.json` (F0 Riziko 8). Default: commit snapshot do tooling nebo vault `00-System/` s datem + ponechat soubor (cron ho přestane aktualizovat).

A4 — Existující `01-INBOX/slack/*.md` **+ co-located přílohy** přes `list_colocated_attachments`: dest **vždy** `inbox_archive_dest` → `07-ARCHIV/inbox-processed/<YYYY>/<MM>/slack/<name>`. Přesun `GitVault.move` + CAS (R15). **`expect_oid` vždy z `vault.stat(src)` — nikdy z `list_dir`.** Chybí oid / konflikt → skip+log. Session: `with open_vault()`. Legacy `01-INBOX/email/` beze změny.

A5 — Kill-switch dump: env `SLACK_POLL_DUMP=0` (default po F4) **nebo** odstranění řádku z crontab; kód `cron/slack_poll.py` + `slack_poll_core.py` zůstává pro rollback ≤14 dní. Preferovat **crontab off + flag v kódu** (no-op když dump off) — dvojitá pojistka.

A6 — Po F4: `get_triage_candidates` → `default_l1: "live"`; `include_live_slack` default **True**; dump složky smí listovat (prázdné / residual) ale skill je nepoužívá jako frontu. Skill `agenda-triage` textově: default live Slack + Gmail L1 + daily/sembly.

A7 — `:gear:` / `:eyes:` po F4: **bez** automatického `reactions.remove` z poll cronu. Unreact = volitelně skill po zpracování (assist), ne cron. (grill — výchozí)

A8 — Drive R9 provoz:  
- Vault I/O jen `GitVault` (`VAULT_BACKEND=git`).  
- Binárky: `materials/` + sidecar v gitu; LFS dle F1 (≤1 MiB blob, ≤40 MiB LFS, >40 MiB / Google-native → Drive).  
- `drive_client` (Brain) = **read** příloh schůzek, ne vault writer.  
- `VAULT_BACKEND=drive` rollback v runbooku zůstává dokumentovaný emergency ≤24 h, ne provoz.

A9 — Artifact MVP:  
- Zdroj v tooling: `docs/claude-artifact-dashboard.md` (+ volitelně HTML šablona v `ŠABLONY/claude-artifacts/dashboard.html`).  
- Data: Brain **`GET /v1/context/light`** (nové) = warm read `agent-context-light.json` (P1 ≤256 KB); při chybějícím light → 503/`error_reason`, ne tichý full dump do artifactu.  
- Auth artifactu: **OAuth human** (stejný IdP allowlist jako MCP); service token → **403** na light/dashboard (ne machine dashboard).  
- Pokud Claude Desktop artifact **neumí** spolehlivý authenticated fetch na Brain → B-artifact FAIL + výhrada; fail-path MCP/`get_context`/Slack brief = DONE OK (analogie F3 B18). Primár v docs zůstává artifact.

A10 — Fail-path dashboard (F0 Q6a): (1) MCP `get_context` v chatu (2) Slack brief z proactivity (F3) (3) ne VPS `web/`. Legacy `build_dashboard.py` zůstává zakomentovaný v crontab (už je).

A11 — Obsidian: runbook sekce „optional pull-only“ — otevřít `~/GitHub/second-brain-vault` (ne Drive mirror); Sync off; žádný zápis; refresh = `git pull`. Mobile Obsidian Sync **neobnovovat** jako writer.

A12 — Objem (odhad do ověření QA): vault F0 A7 ~7.4k souborů / ~782 MB; `agent-context.json` typicky stovky KB; light projekce cíl ≤256 KB (F0 P1). Počet aktivních `01-INBOX/slack` dumpů = ověřit před archivem (`list_dir`). Slack live budget ≈ search count 20 × 5 queries (stávající `slack_live`).

A13 — Soft A17 Free beze změny. Mac no local edit / no push (R25) beze změny.

A14 — SB15-5 `[x]` po QA: DoD = **B1–B11 + B14–B19 + B26–B29 PASS**. **B12/B13** (Claude artifact) smí výhradu — neblokují `[x]`.

A15 — Post-F4 dluh (neblokuje): plné Drive API wiring v `drive_client` (dnes degrade `drive_api_not_wired`); smazání dead `DriveVault` path; hard ruleset; FM migrace.

A16 — Proactivity (grill Q5): po F4 text „jdi do live triáže“ (eyes/gear); **ne** provozní závislost na `slack_dump_count`. Pole count smí zůstat v preview JSON. Kontrakt **B26** + **T18**.

A17 — `DriveVault.move` přijme `expect_oid`/`expect_mtime` pro paritu podpisu; F4 archiv běží na git.

---

## Současný stav (ověřeno v kódu)

| Fakt | Důkaz |
|---|---|
| F0 F4 výstupy + R7/R9/R15/R24 | `docs/plans/2026-10-10-sb-operacni-model-f0.md` L317–323, R7/R9/R15/R24 |
| crontab `slack_poll` live `*/2 8-23` | `vps/second-brain-hub/deploy/crontab` **L66** |
| `GitVault.move` bez CAS | `lib/git_io.py` L560–577 — F4 rozšíří `expect_oid` |
| agenda-reply dumpuje Slack do INBOX | `ŠABLONY/skills/agenda-reply/SKILL.md` — F4 R14 |
| `slack_poll` dump do `01-INBOX/slack`, eyes+gear discover | `cron/slack_poll.py` L71–80; `slack_poll_core.py` L13–18 (`INBOX_DIR`, `MAX_NEW_THREADS=8`) |
| `slack_live` 0 dump, eyes/gear queries | `vps/second-brain-brain/app/tools/slack_live.py` L35–64 |
| Triage default dump | `get_triage_candidates.py` L26–82 (`default_l1: "dump"`, `include_live_slack` default False) |
| Skill default dump | `ŠABLONY/skills/agenda-triage/SKILL.md` L15 |
| `get_context` warm/rebuild → full snapshot | `app/tools/get_context.py` L39–67; REST `GET /v1/context` `main.py` L132–134; MCP `mcp_app.py` L53–54 |
| Light bundle existuje | `agent_context_build.py` L68–69, L605–606 (`agent-context-light.json`) |
| **Žádný** Claude artifact / dashboard endpoint light | glob 0; Brain README: ne dashboard UI |
| `sync-architecture.md` stále Drive SSOT + Obsidian Sync | `vps/second-brain-hub/docs/sync-architecture.md` L1–47, L123–125 |
| Git SSOT cutover dokumentován | `docs/git-vault-runbook.md` L15–57; factory `vault_factory.py` L59–80 |
| `build_dashboard` crontab zakomentovaný | `deploy/crontab` L85–86 |
| Drive read stub pro prep | `app/drive_client.py` L15–31 (`drive_api_not_wired`) |
| F1 LFS / R9 limity | F1 plán A4; F0 R9 |
| Hub README odkazuje sync-architecture | `vps/second-brain-hub/README.md` L6 |
| Claude project instructions stále „Obsidian na Drive“ | `docs/claude-project-instructions.md` L9 |
| Quality checklists A+B | RB Universe `docs/agent_playbooks/quality-checklists.md` (SB adaptace) |

---

## Návrh

### 0. `GitVault.move` + CAS (R15) — před archivem

| Soubor | Změna | R# |
|---|---|---|
| `lib/git_io.py` | `move(src, dst, *, expect_oid=None, expect_mtime=None)` — CAS jako u `delete` | R15 |
| `lib/drive_io.py` | signature parity (A17) | R15 |
| `tests/test_git_vault_move_cas.py` | happy + conflict | R15 |

### 1. Stop `slack_poll` dump (R4, R5)

| Soubor | Změna | R# |
|---|---|---|
| `deploy/crontab` | Zakomentovat / odstranit řádek `slack_poll.py`; komentář „F4: dump off; live = Brain `slack_live`“ | R5 |
| `cron/slack_poll.py` | Na startu: pokud `SLACK_POLL_DUMP` ∈ {0,false,off} → log + exit 0 (no-op). Default v Coolify po F4 = `0`. | R5, A5 |
| `lib/slack_poll_core.py` | Beze změny logiky; jen případný komentář „dump path F4-off“ | R5 |
| `00-System/slack-poll-state.json` (vault) | Před cutoverem export/záloha (A3); po stop už neaktualizovat | R5, A3 |
| One-shot archiv script | `with open_vault()`; dest = `inbox_archive_dest`; přílohy = `list_colocated_attachments`; `oid = vault.stat(src).oid`; `vault.move(..., expect_oid=)`. Orphan přílohy (bez párového md): **stejný** kontrakt (`inbox_archive_dest` + `stat` + `move` + CAS); respekt `--dry-run` (0 write). **Nevolat** `archive_inbox_capture` ani `archive_orphan_inbox_attachments` (Path.rename bez CAS/dry-run). | R5, R15, A4 |
| Coolify env hub | `SLACK_POLL_DUMP=0` | R5 |

### 2. Brain — triage default live + light context (R4, R8)

| Soubor | Změna | R# |
|---|---|---|
| `app/tools/get_triage_candidates.py` | Default `include_live_slack=True`; `default_l1: "live"`; dump list jen jako `sources.slack_dump` (residual/empty) | R4 |
| `app/mcp_app.py` / REST triage | Default query/flag sladit s tool default | R4 |
| `app/tools/get_context_light.py` (nové) nebo větev v `get_context.py` | Warm read `OUTPUT_LIGHT_REL`; bez rebuild full; chybí/stale light dle stejného freshness trio → 503 `error_reason` (ne tichý partial) | R8, A9 |
| `app/main.py` | `GET /v1/context/light` → light tool; **service → 403** `human_oauth_required` (A9) | R8 |
| `app/mcp_app.py` | **Bez** MCP `get_context_light` ve F4 — light jen REST human OAuth (A9/B9); MCP zůstává plný `get_context` | R8 |
| Tests | Default live; dump off neovlivní `slack_live`; light endpoint auth + payload | R4, R8 |

### 3. Skills + klientské docs (R4, R7, R8)

| Soubor | Změna | R# |
|---|---|---|
| `ŠABLONY/skills/agenda-triage/SKILL.md` | Default L1 = **live Slack** + Gmail + daily/sembly; dump slack = legacy/residual only; eyes/gear přes live | R4 |
| `ŠABLONY/skills/agenda-reply/SKILL.md` | **0** nový dump do `01-INBOX/slack/`; live/permalink | R14 |
| `ŠABLONY/skills/agenda-co-ted/SKILL.md` | **Povinně:** primár = `GET /v1/context/light` (human OAuth); fail-path MCP = plný `get_context` (bez MCP light); **ne** local `agent-context.json` + `build_agent_context.py` jako primár | R8 |
| `cron/proactivity_dispatch.py` | Copy „jdi do live triáže“; ne CTA z `slack_dump≈N` | A16 |
| `docs/claude-artifact-dashboard.md` (nové) | UI + **join ID→tasks[]**; `/v1/context/light`; fail-path | R8 |
| `ŠABLONY/claude-artifacts/dashboard.html` (nové, volitelné) | Minimální read-only UI (bez VPS hostingu) — zdroj pro vložení do Claude artifact | R8 |
| `docs/claude-project-instructions.md` | Vault = git SSOT / Brain; ne „Obsidian na Drive“ | R7 |
| `docs/brain-api-runbook.md` | F4: dump off; `/v1/context/light`; artifact; fail-path | R8, R9 |
| `docs/git-vault-runbook.md` | Sekce optional Obsidian pull-only (A11); Drive R9 pointer | R6, R7 |
| `bash scripts/install_agenda_skills.sh` | Po editaci skillů | R11 |

### 4. Drive jen R9 + sync-architecture (R6, R9)

| Soubor | Změna | R# |
|---|---|---|
| `vps/second-brain-hub/docs/sync-architecture.md` | **Přepsat** na cílový tok: GitHub vault + GitVault + Brain + VPS deploy key write + Mac pull-only; mermaid; tabulka čtenářů/zapisovatelů; Drive = R9 + prep read; Obsidian optional; artifact; legacy Drive appendix | R7, R9, R6 |
| `vps/second-brain-hub/docs/sync-implementation-plan.md` | Banner „historický F0–F1 Drive plán; SSOT viz sync-architecture + git-vault-runbook“ | R9 |
| `vps/second-brain-hub/README.md` | Aktualizovat slack_poll popis (off); odkaz artifact; Drive R9 | R5, R9 |
| `docs/plans/…` / runbook | Explicitní R9 checklist: co smí zůstat na Drive (Docs/Sheets, shared, >40 MiB) vs musí být v `materials/` | R6 |
| Inventory (ruční/QA) | Žádný Coolify cron s `VAULT_BACKEND=drive` v provozu; n8n non-Sembly INBOX stále off (F3 B24) | R6 |

**DB/migrace / RBAC FE / Celery:** netýká se.

### 5. Vault / Coolify / SB15

| Položka | Změna | R# |
|---|---|---|
| Coolify hub | `SLACK_POLL_DUMP=0`; crontab bez poll (image) | R5 |
| Coolify brain | bez nutných nových secretů pro light (čte vault); OAuth už je | R8 |
| Vault **SB15-5** | `[x]` po QA (A14) | R11 |
| Tento plán | `docs/plans/2026-10-10-sb-operacni-model-f4.md` | R1 |

---

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | Crontab/env po F4 cutover | `slack_poll` **neběží** dump (exit no-op nebo řádek pryč); 0 nových zápisů do `01-INBOX/slack/` | R5 | T1, T10 |
| B2 | `SLACK_POLL_DUMP=0` + ruční spuštění cron skriptu | exit 0; 0 write; log „dump disabled“ | R5, A5 | T1 |
| B3 | `get_triage_candidates()` bez flags | `default_l1=="live"`; `live_slack` naplněno (nebo `error_reason`); dump není provozní fronta | R4 | T2 |
| B4 | Live Slack eyes/gear | Kandidáti v live; **0** dump write | R4, R5 | T3 |
| B5 | Saved / jméno bez @ | Není v live L1 (regrese F3 B7) | R4 | T3 |
| B6 | Archiv md+přílohy+orphan + CAS | Happy → `…/<YYYY>/<MM>/slack/<name>` (+ atts/orphan); `--dry-run` = 0 write vč. orphan; špatný oid → 0; ne Path.rename helpery | R5, R15, A4 | T4 |
| B26 | proactivity copy | User msg = live triáž; ne CTA z `slack_dump≈N` | A16 | T18 |
| B27 | agenda-reply Slack | 0 nový soubor v `01-INBOX/slack/` | R14 | T12, T19 |
| B28 | `GitVault.move` API | `expect_oid` signature; konflikt → 0 write | R15 | T20 |
| B7 | Záloha `slack-poll-state.json` | Existuje snapshot před/simultaneously s cutoverem | R5, A3 | T5 |
| B8 | `GET /v1/context/light` + OAuth | 200; body = light projection; size ≤256 KB (P1); mode warm | R8, A9 | T6 |
| B9 | `GET /v1/context/light` + service Bearer | **403** `human_oauth_required` | R8, A9 | T6 |
| B10 | Light chybí / trio mismatch / needs rebuild light | **503** + `error_reason`; ne tichá prázdná TOP | R8 | T6 |
| B11 | `GET /v1/context` (full) | Beze změny F2 chování (warm/rebuild) — regrese | R8 | T7 |
| B12 | Claude artifact happy path | UI ukáže TOP / needs_decision / due_soon ze light; zdroj Brain | R8 | T8 |
| B13 | Artifact auth/fetch FAIL v Claude Desktop | Docs primár = artifact; provoz = fail-path MCP/`get_context`/Slack brief; **DONE s výhradou OK** (A9/A14) | R8 | T8, T9 |
| B14 | Fail-path chat | `get_context` MCP vrátí context; agent umí stručný brief bez artifactu | R8, A10 | T9 |
| B15 | Drive jako vault SSOT | Provoz `VAULT_BACKEND=git`; žádný cron dump/write vaultu přes Drive | R6, R7 | T10 |
| B16 | R9 policy docs | sync-architecture + runbook: Drive jen native/shared/>limit; materials/+sidecar v gitu | R6, R9 | T11 |
| B17 | Obsidian optional pull-only | Runbook: klon git; Sync/Drive writer off; systém bez Obsidian dependency | R7, R24 | T11 |
| B18 | `sync-architecture.md` | Popisuje git SSOT + Brain + artifact; Drive tok označen legacy | R9 | T11 |
| B19 | Skill `agenda-triage` po install | Text default live; žádné „dump = default fronta“ | R4 | T12 |
| B29 | Skill `agenda-co-ted` | Primár light REST OAuth; fail-path MCP `get_context`; ne local rebuild jako primár | R8 | T21 |
| B20 | Tip/PAUSED/PUSH při light | Light = read-only warm; mutate gate se netýká light read; full rebuild path beze změny | R10 | T6, T7 |
| B21 | Prázdná live data / prázdný Inbox dump | `candidates: []` / prázdné seznamy; ne 500 | checklist A1 | T2, T3 |
| B22 | Slack API 5xx při live | `error_reason`; ne tiché success | checklist A9 | T3 |
| B23 | SB15-5 DoD | `[x]` = **B1–B11 + B14–B19 + B26–B29 PASS**; B12/B13 výhrada OK | R11, A14 | T13 |
| B24 | n8n non-Sembly INBOX | Stále off (regrese F3 B24) | R6 | T14 |
| B25 | Mac / Obsidian zápis do klonu | Stále zakázán (R25); F4 nemění | R7 | T11 |

---

## Výkonový rozpočet (P)

| Tělo | 1 Objem | 2 SQL | 3 Load | 4 Externí | 5 Page | 6 Payload | 7 Cache | 8 Násobení | 9 FE | 10 Worker | 11 Cíl |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 `/v1/context/light` | read freshness **trio** (full+light+charters); response body = light | n/a | read trio; **0 rebuild** (stale → 503) | 0 | — | read ≤ full+light+charters; **payload ≤256 KB** light | vault files; TTL 15 min trio | 1 req | artifact | Brain replica 1 | cold ≤2 s; warm ≤500 ms (F0 P1) |
| P2 `/v1/context` full | full snapshot | n/a | warm or rebuild | git při rebuild | — | stávající F2 | 15 min | 1 | n/a | Brain | regrese F2 |
| P3 `slack_live` / triage live | ≤5× search ×20 | n/a | — | Slack API | — | ≤128 KB | none | 1 session | n/a | Brain | ≤5 s (F3 P3) |
| P4 slack_poll cron | **0** po F4 | n/a | — | — | — | — | — | off | n/a | hub | n/a (off) |
| P5 archiv dump one-shot | N md + attachments | n/a | list+move | git push | — | — | CAS | 1 běh | n/a | hub/script | <30 s typicky |
| P6 Drive R9 | jen explicitní large/native | n/a | — | Drive read prep | — | — | — | — | n/a | — | prep degrade OK (F3 B31) |

**Ověření objemu (hlavní agent):** velikost `agent-context-light.json`; count slack INBOX; zapsat do QA poznámky.

---

## Testy (T#)

| T# | Typ | Owner | Soubor | B# |
|---|---|---|---|---|
| T1 | pytest | gate | `vps/second-brain-hub/tests/test_slack_poll_dump_flag.py` | B1, B2 |
| T2 | pytest | gate | `vps/second-brain-brain/tests/test_triage_default_live.py` | B3, B21 |
| T3 | pytest | gate | rozšířit `tests/test_slack_live.py` | B4, B5, B21, B22 |
| T4 | pytest + dry-run script | gate | `tests/test_archive_slack_inbox.py` + script `--dry-run` (dest `inbox_archive_dest`) | B6 |
| T5 | ruční/checklist | gate | existence state backup | B7 |
| T6 | pytest | gate | `tests/test_context_light.py` | B8, B9, B10, B20 |
| T7 | pytest | gate | existující get_context testy | B11 |
| T8 | ruční | gate | Claude Desktop artifact → light; nebo FAIL+výhrada | B12, B13 |
| T9 | ruční | gate | MCP `get_context` brief bez artifactu | B13, B14 |
| T10 | ruční/QA deploy | gate | Coolify: poll off; git backend; 0 nových slack dumps | B1, B15 |
| T11 | ruční/docs | gate | sync-architecture + runbooks R9/Obsidian/artifact | B16, B17, B18, B25 |
| T12 | ruční/docs | gate | skill text + `install_agenda_skills.sh` | B19 |
| T13 | ruční | gate | SB15-5 `[x]` | B23 |
| T14 | ruční/n8n | gate | non-Sembly INBOX active=false | B24 |
| T15 | lokální gate | gate | pytest hub + scripts + brain | regrese |
| T16 | QA deploy | gate | hub+brain image; light OAuth; dry-run archiv; poll no-op | B1, B8, B6, B15 |
| T17 | Playwright-T6 | — | — | **netýká se** (ne CAS) |
| T18 | pytest | gate | `tests/test_proactivity_live_copy.py` — copy live triáž, ne `slack_dump≈N` | B26 |
| T19 | docs/skill gate | gate | `agenda-reply` text: 0 dump INBOX; grep skill + install | B27 |
| T20 | pytest | gate | `tests/test_git_vault_move_cas.py` happy + conflict | B28 |
| T21 | docs/skill gate | gate | `agenda-co-ted`: light REST + MCP `get_context` fail-path; ne local rebuild primár | B29 |

---

## Pořadí implementace

F4-a — Záloha `slack-poll-state.json` (B7) + inventura dumpů.  
F4-b — **`GitVault.move` CAS** + T20 (B28); expect_oid jen ze `stat` — před ostrým archivem.  
F4-c — Brain triage default live + T2/T3.  
F4-d — Brain `/v1/context/light` + T6/T7 (bez MCP light).  
F4-e — Skills triage + **agenda-reply R14/T19** + **agenda-co-ted light/MCP fail-path (R8)** + proactivity A16/B26/T18 + install (T12/T21).  
F4-f — `SLACK_POLL_DUMP=0` + crontab off + T1.  
F4-g — Archiv md+přílohy přes `stat`+`move`+`open_vault` dry-run → ostrý (po F4-b+f).  
F4-h — Docs sync-architecture + runbooky + artifact join.  
F4-i — Claude artifact + T8/T9 (výhrada OK).  
F4-j — T15; push; QA; SB15-5 dle B23; DONE.

Závislosti: F4-b před F4-g; F4-f před F4-g; T8 neblokuje DONE při B13 výhradě.

---

## Rizika a zpětná kompatibilita

1. **Ztráta watchlist / stale state** — mitigace B7 export před cutoverem (F0 Riziko 8).  
2. **Mezera signálů bez dump** — live search není persistent watch; akceptováno F0 R11; mitigace eyes/gear.  
3. **`:gear:` bez unreact cronu** — reakce zůstanou; A7 default skill-unreact optional.  
4. **Claude artifact auth** — sandbox nemusí poslat OAuth cookie → B13 výhrada + fail-path.  
5. **Light >256 KB** — porušení P1; mitigace zúžit `project_light`.  
6. **Dual-writer při rollbacku dump** — zapnout poll jen s prázdným/archived INBOX.  
7. **Drive Desktop / Sync omylem zapnuté** — docs R24; ruční T11.  
8. **Legacy `sync-architecture` čtenáři** — banner + README.  
9. **Coolify push main = ostrý vault** — archiv jen po dry-run T4/T16.  
10. **F3 výhrady (OS push / Grok webhook)** — fail-path Slack brief.  
11. **`drive_client` stále unwired** — R9 read path degrade; neblokuje F4 (A15).  
12. **Proactivity dump count** — mitigace **A16**: upravit copy na live triáž v F4-e.

---

## Otevřené otázky pro uživatele

*(CAS move + agenda-reply rozhodnuté. Grill Q1–Q5 defaulty. Schvalování plánu: ne.)*

Žádné blokující.
