# Plán: F1 — Vault → GitHub; crony Drive → git

> Architekt: **k=2 · r=3** (+ patchy po kritikách)  
> Stav: **DONE** (kód nasazen, QA PASS na `9ed0da3`; cutover F1-e…h = runbook)  
> Pipeline ledger: [2026-10-10-sb-operacni-model-f1.pipeline.md](2026-10-10-sb-operacni-model-f1.pipeline.md)  
> Parent F0 (SCHVÁLENO): [2026-10-10-sb-operacni-model-f0.md](2026-10-10-sb-operacni-model-f0.md)  
> Vault: **SB15 — Nový operační model SB — multi-klient, Grok orchestrace, GitHub vault** (**SB15-2**)  
> Profil: **SECOND_BRAIN**. Base (origin/main před pipeline): `674a82a9373cc02a790e24a2ecf48222ccd61719`.

## Zadání a požadavky

R1 — Po F0 DONE (B1–B22 schváleno) pokračovat na F1: Vault SSOT → privátní GitHub `LC-RBEDU/second-brain-vault`. (uživatel „go“ + F0 F1 scope)

R2 — Repo `LC-RBEDU/second-brain-vault` k 2026-10-10 **neexistuje** (`gh repo view` fail) → F1 ho **založí** (private). (brief)

R3 — Tooling zůstává v `LC-RBEDU/second-brain` (tento repo). **Ne** un-ignore `OBSIDIAN/` v tooling. (F0 A1 + brief)

R4 — `GitVault` náhrada `DriveVault`: path API, CAS `expect_oid` + `FileMeta.oid`, commit konvence, lock, push **jen** VPS deploy key; **všechny** vault write call-site přes factory (vč. C23 `inbox_inventory`). (F0 vrstva 3 + R25)

R5 — Preflight před writer cutover: Obsidian Sync + Drive Desktop jako writer **off**; n8n INBOX writers **všechny** vypnout (žádný Drive→git bridge). (F0 R24, A10, migrace 1–2)

R6 — Mac: clone = fetch/pull only + **no local edits** (A24); výjimka zápisu mimo VPS = GitHub **web UI** PR (branch → PR → Merge; ne `gh`/API push z Macu). (F0 R25 / A24 + Q7a)

R7 — Klienti F1: vault **read-only** (klon / snapshot). Brain API / klientský vault write až F2. (F0 F1 závislosti)

R8 — Migrace kroky **1–6** z F0 lineární mapy; F2+ kroky 7–10 mimo F1. (F0 migrace)

R9 — Pokryté F0 R#: **R7, R8, R14, R19, R25, R26**. Model projektů/md/hierarchie zachovat (R8). Lifecycle zůstává VPS cron (R14, R19). Stale Slack INBOX F1–F2 akceptováno (R26). (brief + F0)

R10 — LFS práh F0 nezamykal (Q13b) → F1 nasadí **konkrétní gate** před importem; prahy **schváleny grill Q2a / A4**. (brief + grill g=1)

R11 — Coolify: push `main` → ostrý cron nad živým vaultem → **feature flag / dry-run / cutover pořadí** + **writer freeze** dle A26. (brief + grill)

R12 — Po schválení + implementaci: odškrtnout / posunout vault krok **SB15-2** na **SB15**. (brief)

R13 — Schvalování plánu uživatelem: **ano** (cutover živého vaultu). (ledger)

R14 — Lokální gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q`. Tester přeskočen (profil SECOND_BRAIN). (brief)

R15 — Writer freeze **F1-e→F1-f** (`VAULT_WRITERS_PAUSED=1`, A19). **F1-e/f:** `CRONTAB_MODE=pause` + `VAULT_BACKEND=drive` (ještě). **F1-f konec:** WC clone + **`VAULT_BACKEND=git`** ještě při PAUSED (A35). **F1-g:** `git` + **`PAUSED=0`** + `DRY_RUN=1` + `CRONTAB_MODE=pause` + one-shot (A26, A30, A33). **F1-h:** `git` + `CRONTAB_MODE=live` + **`PAUSED=0`** + `DRY_RUN=0` + `PUSH=1`. Import = finální tip; žádný re-sync.

R16 — Pre-import secrets scan (gitleaks/rg) = **hard gate** F1-f; fail při high-confidence token; exclude jen s OK uživatele. (grill Q6a → A15)

R17 — GitHub ruleset na `main`: require PR pro human actors; **deploy key / Coolify má bypass** pro direct push (B2). Lidé: branch → PR → Merge v web UI (B11 / R25). (grill Q7a)

R18 — Job start dirty WT: **pouze skip+log** — žádný auto `reset --hard HEAD` ani `@{upstream}` na startu (A18 lock).

R19 — Mac `scripts/build_agent_context.py` **nezapisuje** do git klonu; skills F1 = pull + read only (žádný FS write do klonu). (A7, A23, A31)

R20 — `slack_poll` po cutoveru: attachment odkazy = vault-rel path nebo Slack permalink — **ne** `drive.google.com/file/d/…`.

R21 — Mac `scripts/schedule_reminder.py` (schedule + cancel) **fail-on-git-clone** stejně jako B23; list smí read-only. (A31 / B24)

Mimo rozsah F1: F2 Brain API/MCP; F3 živá triáž/Sembly/push/Gmail hybrid; F4 úklid Obsidian/Drive/poll; F5 boti; un-ignore `OBSIDIAN/` v tooling; FM migrace wikilinky→ID/slug (F0 krok 10); změna botů.

Netýká se: Alembic, RBAC, frontend subnav, `qa_gate.mjs`, Playwright-T6, Celery, MCP Brain.

---

## Předpoklady

A1 — Org/owner GitHub vaultu = `LC-RBEDU`; privátní repo; default branch `main`. Lukáš má práva vytvořit repo + deploy key (write) jen pro Coolify host.

A2 — Coolify app `second-brain-hub` (application_id `11`, base dir `vps/second-brain-hub`) dostane **persistent volume** ≥ ~3 GB pro git working copy (A16). Dnes Dockerfile/README: stateless, žádný `/data/vault`.

A3 — Default `VAULT_BACKEND=drive` po deployi kódu GitVault — **žádná změna chování** dokud cutover výslovně nepřepne flag. Ostrý git writer až po freeze + import + smoke.

A4 — **LFS gate schváleno (Q2a):** `*.md` vždy běžný blob; non-md **≤ 1 MiB** blob; **> 1 MiB a ≤ 40 MiB** Git LFS; **> 40 MiB** neimportovat (Drive / R9 + inventář). Google-native (Docs/Sheets) neexportovat jako binárky — zůstávají Drive.

A5 — Import zdroj = Drive Desktop mirror `…/SECOND_BRAIN/OBSIDIAN/` po **klidu Drive Desktop sync** (A22), v okně **F1-e→f freeze**. **Initial import = Mac one-shot write** (dočasný PAT/deploy key), pak **revoke** — write jen Coolify deploy key (A16). Import = finální tip; **žádný re-sync** před cutoverem (Q1a).

A6 — Crony zůstanou na stejném staggeru (`deploy/crontab`) mimo freeze okno; mění se I/O přes factory. `focus` cron nikdy nezapisuje.

A7 — Lokální Mac po cutoveru: git clone `~/GitHub/second-brain-vault`. Env SSOT pro cestu = **`SECOND_BRAIN_VAULT`** (dnes už v `scripts/build_agent_context.py` L89–94). Volitelný alias `SB_VAULT_PATH` → stejná hodnota (jeden resolver, bez rozdvojení). Skills = **pull + read** z klonu; **žádný** FS zápis do klonu (A23, A31). Tooling `OBSIDIAN/` zůstává gitignored.

A8 — `slack_poll` F1 dál dumpá do `01-INBOX/slack/` (stale OK do F3, R26) — **až po F1-h** (během freeze e→f pauza; F1-g one-shot bez slack_poll — A30). Gmail/Sembly/mobile n8n **vypnuté**. Attachment linky po cutoveru dle B14 / R20.

A9 — Calendar SA zůstává pro kalendář; Drive OAuth po cutoveru pro vault I/O nepotřeba (ponechat pro rollback ≤ 24 h, A13).

A10 — Initial vault commit bez secrets; vault `.gitignore` vyloučí `.obsidian/workspace*`, cache, `Icon?`, `.DS_Store`.

A11 — Objem A7 (2026-10-10): ~782 MB / ~7432 souborů — před importem znovu inventář (T3); drift >10 % → přehodnotit LFS/Drive split (prahy A4 beze změny).

A12 — SB15-2 text ve vaultu doplní hlavní agent po schválení plánu / po cutoveru.

A13 — **Rollback Drive bez re-sync ≤ 24 h po F1-h** (Q4a). Po 24 h jen git restore / opravný commit přes VPS nebo web UI PR — ne návrat k Drive jako SSOT bez vědomé re-sync strategie.

A14 — **DRY_RUN vs PUSH odděleně (Q5a):** `GIT_VAULT_DRY_RUN=1` = **žádný** working-tree zápis, jen log `would-write` (žádný commit/push). `GIT_VAULT_PUSH=0` = WT zápis + **lokální commit**, **bez** push. `PUSH=1` = commit + ff-only push **jen pokud je dirty** (dirty-only push, A25).

A15 — **Pre-import secrets scan = hard gate F1-f (Q6a):** gitleaks a/nebo `rg` na high-confidence token patterns; fail → import nepokračuje; exclude konkrétního false-positive jen s **explicitním OK uživatele** v runbooku/ledgeru.

A16 — Potvrzené defaults: Mac one-shot import + revoke; volume ≥ ~3 GB; Obsidian Sync **off** po F1; Mac clone `~/GitHub/second-brain-vault`. **Writers na `main`:** viz A17 (Q7a).

A17 — **GitHub ruleset `main` (Q7a):** require pull request pro **human** actors; **deploy key / Coolify = bypass** → direct `git push` na `main` (B2). Lidé: nová branch → PR → **Merge v GitHub web UI** (B11 / R25); ne direct push, ne `gh`/API push z Macu.

A18 — **Dirty WT na startu jobu:** po `fetch`, pokud WT dirty vůči `HEAD` → **výhradně skip+log**. **Zakázáno** jakékoli auto `git reset --hard` (včetně `HEAD`) a `git clean` na startu. Crash → dirty WT → skip až do manuálního clean (runbook + log alert). **Nikdy** `reset --hard @{upstream}` na startu. Reset na upstream **jen** po failed `push --ff-only` (B6).

A19 — **Kill-switch:** `VAULT_WRITERS_PAUSED=1` blokuje zápis na **třech** místech: (1) `open_vault()` / write path (vč. `delete` / purge), (2) `entrypoint.sh` (skip initial `build_agent_context` + pause keep-alive), (3) Coolify env přetrvá **restart/redeploy** během F1-e→f. Coolify app stop = **nouzová** alternativa (B5).

A20 — **F1-g:** `GIT_VAULT_DRY_RUN=1` na volume; **nehromadit** `PUSH=0` commity na Coolify před F1-h. Smoke = **one-shot** dle A30 (ne plný crontab s */2 Slack joby).

A21 — **Git author:** pevné `user.name` / `user.email` v image nebo Coolify env pro cron commity (např. `Second Brain Hub` / `second-brain-hub@noreply.redbuttonedu.cz` — konkrétní řetězce v runbooku/config.example.env).

A22 — **Pre-import:** po F1-e freeze **počkat na klid Drive Desktop sync**, teprve pak inventář + secrets scan + initial commit (F1-f).

A23 — **Mac snapshot (B23):** `scripts/build_agent_context.py` při cíli = git clone (detekce `.git` v kořeni vaultu **nebo** `SECOND_BRAIN_VAULT_READONLY=1`) → default **exit ≠0** s jasnou hláškou („snapshot píše jen VPS“); `--dry-run` povolen (stdout, žádný zápis). Snapshot SSOT po cutoveru = VPS `cron/build_agent_context.py` + `git pull` na Macu.

A24 — **CAS dual:** `FileMeta.oid: str | None` — u `GitVault` = git blob SHA aktuálního obsahu; u `DriveVault` = `None` (CAS dál přes `expect_mtime`). `write_*` přijímají `expect_oid` i `expect_mtime`. Helper `cas_from_meta(meta) -> dict`. Blind write (`expect_*=None`) zůstává. Git mismatch → `DriveConflictError` (A28).

A25 — **Dirty-only push + P budget */2:** po ops `commit_if_dirty` — pokud není diff, **žádný** commit ani push. `slack_poll` / `reminders_dispatch` (`*/2`) sdílejí flock; budget viz sekce P. Platí až po F1-h (live); F1-g je bez těchto jobů (A30).

A26 — **Fáze freeze vs smoke vs live (Q1a wording):**  
- **Do F1-d včetně:** `CRONTAB_MODE=live` (default) + `PAUSED=0` — chování jako dnes (B1).  
- **F1-e→F1-f (mid):** `PAUSED=1` + `CRONTAB_MODE=pause` + ještě `VAULT_BACKEND=drive`.  
- **F1-f (end):** clone WC + `VAULT_BACKEND=git` + stále PAUSED (A35).  
- **F1-g:** `git` + `PAUSED=0` + `DRY_RUN=1` + `CRONTAB_MODE=pause` + one-shot (A30).  
- **F1-h:** `git` + `CRONTAB_MODE=live` + `PAUSED=0` + `DRY_RUN=0` + `PUSH=1`.  
B5 „import zakázán bez PAUSED“ platí pro F1-e/f, ne pro g smoke.

A27 — **Dirty-WT skip exit:** start skip+log → **exit 0** (nebo kód, který supercronic nehlásí jako fail); manuální clean v runbooku (A18).

A28 — **CAS error typ:** Git `expect_oid` mismatch → stejná výjimka `DriveConflictError` (nebo alias) — žádný nový typ jen kvůli přejmenování (B3).

A29 — **`inbox_inventory` = write-capable (C23):** volá `triage_commitments.purge_dropped_sent_inbox` → `vault.delete`; musí `open_vault()`; **PAUSED blokuje purge**. Není čistý reader. (`cron/inbox_inventory.py` L36–39)

A30 — **F1-g / T4 = one-shot bez Slack mutate (default b):** spustit jen bezpečné writery v DRY_RUN (např. `build_agent_context`, vybraný lifecycle no-op, `fetch_calendar` would-write) — **nespouštět** `reminders_dispatch` ani `slack_poll` během F1-g/T4.  
B7 doplněk: pokud by někdy běžel **plný** crontab s `DRY_RUN=1`, **nesmí** volat Slack API mutate (post message / download+write inbox) — jen would-write log nebo skip.  
*Alternativa (a) — DRY_RUN potlačí Slack uvnitř jobů — nezvoleno; jen poznámka.*

A31 — **Mac reminder + skills (B24):** `scripts/schedule_reminder.py` `schedule` i `cancel` při git-clone vaultu → exit ≠0 (stejná detekce jako B23); `list` smí read-only. F1-d2: skills seznam níže = **pull/read only**, zákaz FS write do klonu (tasky, reminders, capture, triage commit do klonu → až F2 / web UI PR).

A32 — **`mkdir` ≡ `mkdir_p`:** `DriveVault` dnes má jen `mkdir_p` (`drive_io.py` L636); `reminders_dispatch.py` L53 volá `vault.mkdir` (AttributeError risk). F1: `mkdir = mkdir_p` alias na **DriveVault i GitVault** (T1). Alternativa C17→jen `mkdir_p` je OK jako implementační zkratka, preferován alias kvůli API parity.

A33 — **Cron mode oddělený od PAUSED (kritik kolo 4):** env `CRONTAB_MODE=pause|live`. **Code default = `live`** (unset → live) — F1-d s `VAULT_BACKEND=drive` nesmí spadnout do heartbeat (B1/A3). Entrypoint: `crontab.pause` když `CRONTAB_MODE=pause` **nebo** `VAULT_WRITERS_PAUSED=1`; plný `/app/crontab` jen `CRONTAB_MODE=live` ∧ `PAUSED=0`. **F1-d:** Coolify `CRONTAB_MODE=live` + `PAUSED=0`. **F1-e/f/g:** explicitně `CRONTAB_MODE=pause` (+ e/f PAUSED=1). **F1-g:** `PAUSED=0` + `DRY_RUN=1` + pause + manuální one-shot T4 (A30). **F1-h:** `CRONTAB_MODE=live` + `PAUSED=0` + `DRY_RUN=0` + `PUSH=1`. Dockerfile `COPY deploy/crontab.pause`. T2: assert pause při `pause`∧`PAUSED=0` i při `PAUSED=1`; plný crontab jen `live`∧`PAUSED=0`. T6: Coolify restart drží mode; po h assert plný `/app/crontab`.

A34 — **Mac write mimo B23/B24:** hard-fail jen `build_agent_context` + `schedule_reminder` schedule/cancel. Ostatní Mac writery (`archive_inbox_item`, `create_project_hub`, `sort_operational_steps`, …) = **F1 Forbidden** přes F1-d2 skill rewrite + runbook; žádné nové R#.

A35 — **`VAULT_BACKEND=git` + WC bootstrap (kritik kolo 5):**  
1. Mac import → tip na GitHub.  
2. Coolify: volume + deploy key → **`git clone` + `git lfs pull` do `GIT_VAULT_ROOT`** (`/data/vault`); prázdný root bez `.git` = clone (ne silent fail).  
3. T6: `git rev-parse HEAD` == import tip.  
4. Teprve pak Coolify **`VAULT_BACKEND=git`** (stále `PAUSED=1` + `CRONTAB_MODE=pause`).  
5. **F1-g:** `PAUSED=0` až když backend=`git` — jinak one-shot znovu píše Drive (rozbíjí Q1a).  
6. Bootstrap clone **jen F1-f** (B25). Při `DRY_RUN=1` a chybějícím `.git` → fail, ne silent clone.  

---


## Současný stav (ověřeno v kódu)

| Fakt | Důkaz |
|---|---|
| Drive = SSOT; hub stateless přes Drive API | `vps/second-brain-hub/README.md` L1–24; `vps/second-brain-hub/docs/sync-architecture.md` L1–35 |
| `OBSIDIAN/` git-ignored v tooling | `.gitignore` L8–11 |
| `DriveVault` path API + CAS `expect_mtime` → `DriveConflictError` | `lib/drive_io.py` L139–140, L519–578 |
| `FileMeta` **bez** `oid` | `drive_io.py` L143–157 |
| Public API: `mkdir_p` (ne `mkdir`) | `drive_io.py` L636+; grep `def mkdir` = 0 |
| `reminders_dispatch` volá `vault.mkdir` | `cron/reminders_dispatch.py` L53 |
| Crony = přímý `DriveVault(...)` — žádná factory | např. `build_agent_context.py` L331–335; `inbox_inventory.py` L35–39 |
| `inbox_inventory` → `purge_dropped_sent_inbox` (delete) | `inbox_inventory.py` L21, L39 |
| `task_io.update_task` CAS jen `expect_mtime` | `lib/task_io.py` L164–168 |
| `slack_poll` attachment = Drive URL | `cron/slack_poll.py` L98–102 |
| Crontab: slack_poll `*/2 8-23`; reminders `*/2` | `deploy/crontab` L57–65 |
| Dockerfile: bez git/git-lfs; bez volume | `Dockerfile` L1–37 |
| Entrypoint: vždy `build_agent_context` + supercronic; žádný PAUSED | `deploy/entrypoint.sh` L1–11 |
| `config.example.env` VAULT_PATH mýtus | L40–43; `drive_io.py` VAULT_PATH = 0 hitů |
| Mac snapshot / reminders: `SECOND_BRAIN_VAULT`; default write | `scripts/build_agent_context.py` L89–94; `scripts/schedule_reminder.py` L29–49, L74–89 |
| `scripts/slack_watch_ignore.py` = přímý DriveVault | L38–54 |

### Kompletní mapa vault write call-site (factory + CAS A24)

| # | Soubor | Write ops dnes |
|---|---|---|
| C1 | `lib/task_io.py` | `write_text` + `expect_mtime` |
| C2 | `lib/github_rbu_closes.py` | `write_text` state (blind) |
| C3 | `cron/build_agent_context.py` | `write_json` ×3 (blind) |
| C4 | `cron/build_sources_routing.py` | `write_text` (blind) |
| C5 | `cron/lifecycle_hub_state.py` | `write_text` + `expect_mtime` |
| C6 | `cron/lifecycle_sort_steps.py` | `write_text` + CAS |
| C7–C12 | `lifecycle_done_from_checkboxes`, `_waiting_to_next`, `_waiting_default_waituntil`, `_waituntil_hygiene`, `_overdue_flag`, `_github_rbu_closes` | přes `task_io` / vlastní write |
| C13 | `cron/lifecycle_recurring.py` | `mkdir_p`, `move`, `write_text` |
| C14 | `cron/lifecycle_extra_edu_news.py` | `write_text` + `expect_mtime` |
| C15 | `cron/archive_done_tasks.py` | `mkdir_p`, `move` |
| C16 | `cron/slack_poll.py` | `write_bytes`, `write_json` state, `write_text` md |
| C17 | `cron/reminders_dispatch.py` | **`mkdir`** (→ alias A32), `move`, `write_json` |
| C18 | `cron/weekly_summary_draft.py` | `write_text` (blind) |
| C19 | `cron/fetch_calendar.py` | `write_json` |
| C20 | `cron/triage_commitments.py` | `delete` (purge) — PAUSED blokuje |
| C21 | `scripts/slack_watch_ignore.py` | `write_json` + `expect_mtime` |
| C22 | `scripts/smoke_drive_io.py` | smoke — factory / docs |
| **C23** | **`cron/inbox_inventory.py`** | **`open_vault()`** + purge `delete` přes C20; PAUSED blokuje purge (A29) |

Read-only bootstrap: `check_edu_news_state.py` — `open_vault()` OK, žádný mutate.

Mac FS write (mimo hub factory, B23/B24): `scripts/build_agent_context.py`, `scripts/schedule_reminder.py` (schedule/cancel).

### Mapa I/O po F1 (cíl)

| # | Actor | Mechanismus |
|---|---|---|
| W1–W6 | Lifecycle / agent-context / sources / slack_poll / reminders / weekly | `GitVault` + deploy key direct push `main` (A17) — **až F1-h** |
| W7 | n8n INBOX | vypnuto (F1-e) |
| W8–W10 | Cursor FS / Obsidian Sync / Drive Desktop writer | zakázáno |
| W-web | Člověk | branch → PR → Merge web UI |
| W-ignore | `slack_watch_ignore.py` | `open_vault()`; PAUSED → fail |
| W-inv | `inbox_inventory` (C23) | `open_vault()`; purge jen mimo PAUSED |

**F1-e→f:** PAUSED=1 + CRONTAB_MODE=pause; konec f = WC clone + `VAULT_BACKEND=git` (A35). **F1-g:** git + PAUSED=0 + DRY_RUN + pause + one-shot. **F1-h:** git + CRONTAB_MODE=live + PAUSED=0 + DRY_RUN=0 + PUSH=1.

**Čtenáři po cutoveru:** crony + Mac clone (skills pull/read) + později F2 Brain.

---

## Návrh

### 0) Feature flag, freeze a cutover (R11, R15, A19, A26, A30)

| Env | Hodnoty | Chování |
|---|---|---|
| `VAULT_BACKEND` | `drive` (default) \| `git` | factory → `DriveVault` / `GitVault` |
| `GIT_VAULT_ROOT` | `/data/vault` | working copy |
| `GIT_VAULT_REMOTE` | `git@github.com:LC-RBEDU/second-brain-vault.git` | origin |
| `GIT_VAULT_BRANCH` | `main` | ff-only |
| `GIT_VAULT_DRY_RUN` | `0` \| `1` | `1` = žádný WT zápis, jen `would-write` (A14) |
| `GIT_VAULT_PUSH` | `0` \| `1` | dirty-only push když `1` (A25); ignorováno při `DRY_RUN=1` |
| `VAULT_WRITERS_PAUSED` | `0` \| `1` | kill-switch (A19) — **F1-e→f** |
| `CRONTAB_MODE` | `pause` \| `live` | A33 — default **`live`**; pause = `crontab.pause` (jen F1-e/f/g); live = plný crontab (F1-d + F1-h) |
| `GIT_AUTHOR_*` | pevné | A21 |
| `SECOND_BRAIN_VAULT` | Mac clone path | A7; alias `SB_VAULT_PATH` |
| `SECOND_BRAIN_VAULT_READONLY` | `0` \| `1` | vynutí B23/B24 |

**Kill-switch (F1-e→f):** factory mutate → `VaultPausedError` (vč. `delete`/purge C20/C23); entrypoint skip agent-context + `crontab.pause`; Coolify restart drží PAUSED (T6).

**Cutover:**

1. **F1-e freeze:** Sync/Drive writer/n8n off; `PAUSED=1` + `CRONTAB_MODE=pause` + `VAULT_BACKEND=drive` + keep-alive.  
2. A22 sync-klid → inventář + LFS.  
3. Secrets hard gate (F1-f).  
4. Založit repo + ruleset A17; Mac one-shot import; revoke; Coolify deploy key.  
5. Deploy tooling + volume `/data/vault`; stále PAUSED + pause crontab.  
5b. **Bootstrap WC (A35):** `git clone` + `git lfs pull` → `GIT_VAULT_ROOT`; T6 `HEAD` == import tip.  
5c. Coolify **`VAULT_BACKEND=git`** (ještě `PAUSED=1` — žádný mutate).  
6. **F1-g:** `VAULT_BACKEND=git` + `PAUSED=0` + `DRY_RUN=1` + `CRONTAB_MODE=pause` + manuální one-shot T4 (A30).  
7. **F1-h live:** `VAULT_BACKEND=git` + `CRONTAB_MODE=live` + `PAUSED=0` + `DRY_RUN=0` + `PUSH=1`; T5 plný crontab + dirty push; Mac clone; skills pull/read.  
8. Rollback ≤24 h → `VAULT_BACKEND=drive` + `CRONTAB_MODE=live`.

### 1) Vault repo + LFS + ruleset (R1, R2, R10, R17)

Vault repo: `.gitattributes` (LFS), `.gitignore`, `README.md`, kořen = layout `OBSIDIAN/`.  
Ruleset `main`: require PR humans; deploy-key bypass (T6).  
LFS A4; `scripts/vault_import_inventory.py`.

### 2) Secrets hard gate (R16 / A15)

`scripts/vault_secrets_scan.sh` (+ runbook F1-f).

### 3) `GitVault` + factory + CAS + mkdir (R4, R18, A18, A24, A25, A32)

| Soubor | Změna | R# |
|---|---|---|
| `lib/drive_io.py` | `FileMeta.oid`; `expect_oid`; `cas_from_meta`; **`mkdir = mkdir_p` alias** (A32) | R4 |
| `lib/git_io.py` | `GitVault`; CAS oid; flock; dirty→skip+log; dirty-only push; **`mkdir` ≡ `mkdir_p`**; author | R4, R18 |
| `lib/vault_factory.py` | `open_vault()`; DRY_RUN/PUSH; PAUSED → mutate fail (vč. delete) | R15 |
| `lib/task_io.py` | `cas_from_meta` | R4 |
| **C1–C23** | `open_vault()` + CAS; **C23 `inbox_inventory.py`** povinně | R4 |
| `cron/slack_poll.py` | factory; attachment vault-rel / permalink | R20 |
| `cron/reminders_dispatch.py` | factory; `mkdir`/`mkdir_p` funguje (A32) | R4 |
| `Dockerfile` | git + git-lfs; author | R4 |
| `deploy/entrypoint.sh` | `CRONTAB_MODE=pause` ∨ PAUSED → `crontab.pause` + skip agent-context; default unset/`live` = plný crontab (B1) | R15, A33 |
| `deploy/crontab.pause` | heartbeat-only (nový; Dockerfile COPY) | A33 |
| `config.example.env` | flagy; pryč VAULT_PATH mýtus | — |
| `vps/second-brain-hub/docs/sync-architecture.md` | git SSOT | — |
| `README.md` + `deploy/crontab` | volume, flags, dirty-only | — |

**Job start (A18):** flock → fetch → dirty ⇒ **skip+log only** (exit 0) → ops → commit_if_dirty → push if dirty∧PUSH=1 → reject ⇒ B6. T1 FAIL při `reset --hard` na startu.

### 4) Coolify / volume

Volume `/data/vault` ≥ ~3 GB; deploy key + ruleset bypass; **F1-f: clone+LFS bootstrap (A35)**; po F1-h: `git` + `CRONTAB_MODE=live` + **`PAUSED=0`** + `DRY_RUN=0` + `PUSH=1`.

### 5) Mac + skills + runbooky (R6, R19, R21, A23, A31)

| Soubor | Obsah |
|---|---|
| `docs/git-vault-runbook.md` | freeze e→f; g=DRY_RUN one-shot; h=live; A30; B23/B24; ruleset; rollback |
| `docs/f1-inbox-outage.md` | Sembly/Gmail/mobile; stale Slack |
| `scripts/build_agent_context.py` | B23 |
| `scripts/schedule_reminder.py` | B24: schedule/cancel fail-on-git-clone; list OK |
| Skills F1-d2 (pull/read only, **zákaz FS write do klonu**) | `agenda-work`, `agenda-capture`, `agenda-triage`, `agenda-status-update`, `agenda-priority-review`, `agenda-co-ted`, `agenda-remind` (ne `schedule_reminder` write), `agenda-cursor-inbox`, `agenda-weekly-review`, `agenda-edu-news`, `agenda-analyze`, `agenda-lessons`, `agenda-proces`, `agenda-zapis-ze-schuzky`, `mrluc-loader` — vault path = `SECOND_BRAIN_VAULT` clone; snapshot jen VPS + `git pull`; lidský zápis = web UI PR; zápis skillů až F2 |

### 6) Vault úkol SB15 (R12)

Po cutoveru: **SB15-2** odškrtnuto; VPS `build_agent_context`.

### Checklist A

| A bod | F1 |
|---|---|
| 1 Prázdná data | no-op (B8) |
| 2 None | expect_oid conflict (B3); blind OK (B6) |
| 3 TZ | Europe/Prague |
| 4 Měny | netýká se |
| 5 Oprávnění | deploy key bypass + human PR |
| 6 Sync stav | freeze e→f; dirty skip A18; push reject B6 |
| 7 Smazané | git rm + commit; purge pod PAUSED fail |
| 8 CAS / lock | B3, B4, B6; C1–C23 |
| 9 Externí chyba | push fail → B6 |
| 10 Zpětná komp | default drive; rollback ≤24 h |
| 11 Konzistence | B5/B21/B23/B24; F1-g A30 |

---

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | Deploy hub, `VAULT_BACKEND=drive` | Crony jako dnes; žádný git push vaultu | R11 | T1, T2 |
| B2 | `git` + `PUSH=1` + live, čistý ff | dirty-only commit → direct push `main` (bypass) | R4, R17, A25 | T5, T6 |
| B3 | `expect_oid` ≠ blob | `DriveConflictError`; necommitnuto | R4 | T1 |
| B4 | Dva crony současně | flock ≤5 s nebo skip | R4 | T1 |
| B5 | F1-e/f: writers ne off nebo `PAUSED≠1` | Import zakázán. PAUSED: factory mutate fail (vč. purge C23); keep-alive; Coolify restart. F1-g ≠ PAUSED (A26) | R5, R15, A19, A26 | T2, T6 |
| B6 | push ff-only reject | `reset --hard @{upstream}` jen zde; log | R4, Q3a | T1 |
| B7 | `GIT_VAULT_DRY_RUN=1` | 0 WT zápis; `would-write`. **F1-g/T4 = one-shot bez** `reminders_dispatch`/`slack_poll` (A30). Plný crontab+DRY_RUN **nesmí** Slack mutate (B7 doplněk). Alt. (a) nezvoleno | R11, Q5a, A30 | T2, T4 |
| B8 | Lifecycle bez změny | žádný empty commit/push | R14, A25 | T1 |
| B9 | Import LFS A4 | md/≤1MiB blob; 1–40 LFS; >40 Drive-only | R10 | T3 |
| B10 | Mac clone | pull OK; no push creds; no local edit | R6 | T6 |
| B11 | Lidský zápis | branch → PR → Merge web UI | R6, R17 | T6 |
| B12 | Klienti F1 | vault read-only | R7 | T6 |
| B13 | n8n INBOX | inactive po F1-e | R5 | T6 |
| B14 | `slack_poll` po F1-h | GitVault dump; odkaz vault-rel / Slack permalink; ne Drive URL | R9, R20 | T5, T11 |
| B15 | Sembly/Gmail/mobile | žádné n8n dropy | R5 | T6 |
| B16 | e→f freeze; g smoke; h live | e/f: PAUSED + pause crontab. f-end: WC clone + `VAULT_BACKEND=git` (A35). g: **git** + **PAUSED=0** + DRY_RUN + pause + one-shot. h: git + CRONTAB_MODE=live + **PAUSED=0** + DRY_RUN=0 + PUSH=1 + dirty push | R8, R15, A26, A30, A33, A35 | T4, T6 |
| B25 | Prázdný `GIT_VAULT_ROOT` | Clone+LFS **jen F1-f** (mimo DRY_RUN). Při `DRY_RUN=1` a chybějícím `.git` → **fail** (ne silent clone). Po F1-f clone: `HEAD` == tip | A35 | T1, T4, T6 |
| B17 | Model vaultu | projekty, `.md`, hierarchy | R9 | T3 |
| B18 | Tooling gitignore | `OBSIDIAN/` ignored | R3 | T7 |
| B19 | Rollback | ≤24 h Drive bez re-sync | R11, Q4a | T6 |
| B20 | SB15 | SB15-2 odškrtnuto | R12 | T8 |
| B21 | Secrets scan | fail F1-f bez user OK | R16, Q6a | T10 |
| B22 | Dirty WT start | skip+log only; žádný auto reset | R18, A18 | T1 |
| B23 | Mac `build_agent_context` → git clone | exit ≠0 bez `--dry-run`; 0 zápis | R19, A23 | T12 |
| B24 | Mac `schedule_reminder` schedule/cancel → git clone | exit ≠0; 0 zápis; `list` OK; skills pull/read only | R21, A31 | T13 |

Nerelevantní checklist A: měny/DPH, RBAC, Alembic, FE — netýká se.

---

## Výkonový rozpočet (P)

Objem (A11): ~782 MB, ~7.4k souborů.

### Společné

| # | Bod | Rozpočet F1 |
|---|---|---|
| P1 | objem | inventář; full clone+LFS; volume ≥3 GB |
| P2 | SQL | netýká se |
| P3 | RAM | FS walk; ne celý tree v RAM |
| P4 | externí | ≤1 fetch + ≤1 push / úspěšný job; 0 push pokud clean; po cutoveru 0 Drive vault I/O |
| P5 | stránkování | netýká se |
| P6 | payload | diff-only commits; agent-context.json ≪ 5 MB |
| P7 | cache | git odb; path meta per process |
| P8 | násobení | flock; dirty skip; PAUSED = 0 I/O |
| P9 | FE | netýká se |
| P10 | worker | lifecycle &lt; 120 s; agent-context &lt; 30 s |
| P11 | měření | log timestamps + `git log -1` |

### */2 joby (až F1-h live; F1-g je bez nich — A30)

| Job | P budget | Mechanismy |
|---|---|---|
| `slack_poll` | &lt; 45 s warm p95; ≤1 fetch/push; push jen dirty | A25; CAS oid |
| `reminders_dispatch` | &lt; 20 s warm p95; 0 due → no commit/push | A25 |

T4: one-shot DRY_RUN → 0 WT. T5: klidný interval bez empty commit.

---

## Testy (T#)

| T# | Typ | Owner | Soubor | B# |
|---|---|---|---|---|
| T1 | pytest | gate | `tests/test_git_io.py` — CAS oid, flock, dirty skip (FAIL při reset), B6, empty commit, dirty-only push, **`mkdir`≡`mkdir_p`** | B3, B4, B6, B8, B22 |
| T2 | pytest | gate | factory; DRY_RUN; PAUSED mutate (vč. delete/purge); **grep C1–C23** factory; entrypoint: `crontab.pause` při `CRONTAB_MODE=pause`∧`PAUSED=0` i při `PAUSED=1`; plný crontab jen `live`∧`PAUSED=0`; unset→live (B1) | B1, B5, B7, A33 |
| T3 | pytest + ruční | gate | LFS A4 | B9, B17 |
| T4 | dry-run / container | gate | F1-g: assert `VAULT_BACKEND=git` + **`PAUSED=0`** + `.git` + HEAD tip; **one-shot** DRY_RUN bez Slack */2 (A30); 0 WT; **ne** Drive write; bez `.git` → fail (B25) | B7, B16, B25, A35 |
| T5 | QA po cutover | gate | live log + `git log -1`; deploy-key; empty-commit silence; B14 links | B2, B14 |
| T6 | ruční | gate + user | freeze e→f; WC clone + HEAD tip před g; Coolify restart drží `CRONTAB_MODE`+backend; po h plný crontab + git push; n8n/Sync; Mac pull; ruleset; Merge UI; rollback; A22 | B2, B5, B10–B13, B15, B16, B19, B25, A33, A35 |
| T7 | ruční / git | gate | `OBSIDIAN/` ignored | B18 |
| T8 | ruční vault | gate | SB15-2 | B20 |
| T9 | pytest | gate | `test_drive_io.py` + oid None + mkdir alias | B1 |
| T10 | ruční / skript | gate | secrets fail path | B21 |
| T11 | pytest | gate | slack_poll attachment bez Drive URL | B14 |
| T12 | pytest | gate | build_agent_context git clone → fail write | B23 |
| T13 | pytest | gate | `scripts/tests/test_schedule_reminder_readonly.py` — schedule/cancel fail-on-git-clone; list OK | B24 |
| — | Tester | — | přeskočeno (SECOND_BRAIN) | — |

Gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q`.

---

## Pořadí implementace

F1-a — Inventář + LFS (T3).  
F1-b — `FileMeta.oid` + `expect_oid` + GitVault A18 + mkdir alias A32 + T1.  
F1-c — factory + PAUSED; migrace **C1–C23** (vč. `inbox_inventory`); slack_poll B14; T2 grep + T9/T11.  
F1-d — Dockerfile + `COPY crontab.pause`; entrypoint respektuje `CRONTAB_MODE` (default live); Coolify `CRONTAB_MODE=live` + `PAUSED=0` + `VAULT_BACKEND=drive` (B1); docs; push tooling.  
F1-d2 — B23 + B24 + skills seznam pull/read only (A31); T12/T13.  
F1-e — Preflight + `PAUSED=1` + `CRONTAB_MODE=pause` + restart keep-alive (T6).  
F1-f — A22 → secrets → repo + ruleset → import → revoke → volume → **clone+LFS do `/data/vault`** → `VAULT_BACKEND=git` (stále PAUSED + pause crontab) (A35).  
F1-g — `VAULT_BACKEND=git` + **`PAUSED=0`** + `CRONTAB_MODE=pause` + **one-shot** `DRY_RUN=1` (A30 / T4).  
F1-h — `VAULT_BACKEND=git` + `CRONTAB_MODE=live` + **`PAUSED=0`** + `DRY_RUN=0` + `PUSH=1`; T5; Mac clone.  
F1-i — SB15-2 + outage docs.  
F1-j — QA PASS; TESTER přeskočen.

Závislosti: F1-b→c; F1-e před f/h; F1-d před g. Freeze = e→f; g = DRY_RUN; h = live.

---

## Rizika a zpětná kompatibilita

1. Push main = ostrý vault — default drive + freeze e→f + DRY_RUN g.  
2. Dual-writer — PAUSED tři vrstvy + n8n/Sync off.  
3. Volume / LFS ≥3 GB.  
4. Lock contention po h — skip+log; */2 budgets.  
5. CAS vs web UI PR — další tick OK.  
6. >40 MiB mimo git — TSV.  
7. Mac write únik — B23/B24 + skills zákaz FS write.  
8. Rollback ≤24 h.  
9. Stale Slack R26.  
10. n8n znovu active.  
11. git missing in image — T4.  
12. Secrets hard gate.  
13. Freeze > hodiny.  
14. Blind write po B6 reset — idempotence T1.  
15. Ruleset bypass — T6.  
16. Auto-reset na startu — zakázáno; T1 FAIL.  
17. Import během Drive sync — A22.  
18. Call-site opomenutí — C1–**C23** + T2 grep.  
19. Coolify restart bez PAUSED během e→f.  
20. Legacy Drive URL ve starých MD — neměnit historii.  
21. F1-g plný crontab + Slack API side-effect — mitigace A30 one-shot.  
22. `vault.mkdir` bez aliasu — A32 / T1.

---

## Otevřené otázky pro uživatele

**Žádné blokující.** Grill Q1–Q7a rozhodnutí beze změny; wording Q1a = e→f freeze / g DRY_RUN / h live (A26).

| Q / A | Rozhodnutí | Kam |
|---|---|---|
| Q1a | Freeze **e→f**; **g=DRY_RUN**; **h=live**; finální tip; no re-sync | R15, A26, B5, B16 |
| Q2a | LFS A4 | A4, B9 |
| Q3a | Reject→reset upstream; blind OK | B6, T1 |
| Q4a | Rollback ≤24 h | A13, B19 |
| Q5a | DRY vs PUSH | A14, B7 |
| Q6a | Secrets hard gate | A15, B21 |
| Q7a | Ruleset PR humans + deploy-key bypass | R17, A17, B2, B11 |
| A18 | Dirty WT = skip+log only | B22, T1 |
| A19 | PAUSED tři vrstvy (e→f) | B5 |
| A20/A30 | F1-g one-shot DRY_RUN bez Slack */2 | B7, T4 |
| A21 | Pevný git author | Dockerfile/env |
| A22 | Sync-klid | F1-f |
| A23–A25, A31–A32 | Mac readonly; CAS; dirty-only; reminders B24; mkdir alias | B23, B24, T1 |

Blokující pro cutover: T6 + T10 + krátké freeze e→f.

---

## Grill → jak zapracováno

| ID | Rozhodnutí | Úprava plánu |
|---|---|---|
| Q1a | Writer freeze; finální tip; no re-sync | **Wording:** freeze **e→f**; g=DRY_RUN; h=live (A26, R15) — rozhodnutí Q1a neměněno |
| Q2a | LFS A4 | A4, B9 |
| Q3a | Reject→reset upstream | B6, T1 |
| Q4a | Rollback ≤24 h | A13, B19 |
| Q5a | DRY vs PUSH | A14, B7 |
| Q6a | Secrets hard gate | A15, B21 |
| Q7a | Ruleset PR + deploy-key bypass | R17, A17, B2, B11 |

---

## NEW → jak vyřešeno (kritik kolo 2 → k=2 · r=2)

| ID | Závažnost | Jak vyřešeno |
|---|---|---|
| **NEW-1** | BLOCKER | **C23** = `cron/inbox_inventory.py` → `open_vault()` v tabulce call-site; F1-c + **T2 grep** C1–C23; PAUSED blokuje purge (A29, B5). |
| **NEW-2** | MAJOR | **Default (b):** F1-g/T4 = **one-shot bez** `reminders_dispatch`/`slack_poll` (A30). B7: plný crontab+DRY_RUN **nesmí** Slack mutate. Alt. (a) jen poznámka, nezvoleno. |
| **NEW-3** | MAJOR | A32: `mkdir` ≡ `mkdir_p` na GitVault **i** DriveVault alias; T1. (Alt. C17→mkdir_p OK jako zkratka.) |
| **NEW-4** | MAJOR | **B24** + A31: `schedule_reminder.py` schedule/cancel fail-on-git-clone; F1-d2 skills seznam = pull/read only, zákaz FS write do klonu; **T13**. |
| **NEW-5** | MINOR | Grill Q1a wording v R15/A26/tabulce Q: freeze **e→f**; g=DRY_RUN; h=live. |

---

## Delta oproti k=2 · r=1 (max 10)

1. C23 `inbox_inventory` v call-site tabulce; F1-c + T2 grep; PAUSED↔purge.  
2. F1-g/T4 = one-shot **bez** slack_poll/reminders (A30); B7 doplněk.  
3. `mkdir` ≡ `mkdir_p` (Drive+Git); T1 (A32).  
4. B24 + T13: `schedule_reminder` schedule/cancel fail-on-git-clone.  
5. F1-d2: explicitní skills seznam = pull/read only, zákaz FS write.  
6. Q1a wording: freeze e→f / g=DRY_RUN / h=live (A26).  
7. R21, A30–A32; B7/B16 zpřesněny.  
8. Rizika 21–22 (F1-g Slack side-effect; mkdir).  
9. Grill Q1–Q7a **rozhodnutí** beze změny.  
10. Architekt header **k=2 · r=3**.
11. A33: default `CRONTAB_MODE=live`; pause jen e/f/g; F1-h checklist + T2/T6 asserts.
12. P tabulka: jedna P5, jedna P6 (bez duplicit / mojibake).
13. A35 / B25: F1-f clone WC + `VAULT_BACKEND=git` **před** F1-g `PAUSED=0`; DRY_RUN bez `.git` → fail (clone jen F1-f).

---

*Profil: SECOND_BRAIN. Architekt k=2 · r=3 (+ patch kolo 5). Parent F0 SCHVÁLENO. F2+ mimo rozsah. Otevřené otázky: žádné blokující.*
