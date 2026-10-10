# Plán: F2 — Brain API + skilly plugin

> Architekt: **k=1 · r=1**  
> Stav: **DRAFT** (k zápisu do `docs/plans/2026-10-10-sb-operacni-model-f2.md`)  
> Pipeline ledger: [2026-10-10-sb-operacni-model-f2.pipeline.md](2026-10-10-sb-operacni-model-f2.pipeline.md)  
> Parent F0 (SCHVÁLENO): [2026-10-10-sb-operacni-model-f0.md](2026-10-10-sb-operacni-model-f0.md) · F1 DONE cutover  
> Vault: **SB15 — Nový operační model SB — multi-klient, Grok orchestrace, GitHub vault** (**SB15-3**)  
> Profil: **SECOND_BRAIN**. Base (origin/main před pipeline): `ca95c2f1388c1b7605c27ef9113219821e58a1f1`.

## Zadání a požadavky

R1 — Po F0 SCHVÁLENO (B1–B22) a F1 cutover DONE (2026-10-10, soft A17 Free) spustit F2 pipeline. (uživatel „rovnou /rbu-pipeline na F2“ + kontext)

R2 — F2 scope z F0 tabulky F2: **Brain API**; klienti vault **MCP write**; **plugin SSOT**; **serverová policy**; **FM kontrakt ID/slug**. (F0 F2 výstupy + brief)

R3 — Brain API = **nová HTTPS služba na Coolify** (ne cron process hubu); remote MCP + tenké REST pro n8n a Claude artifact. (F0 A2)

R4 — Po F2: zapisovatelé vaultu = Brain API + VPS crony přes `GitVault` (deploy key). Klienti vault **jen MCP**. Dev-bypass default **neexistuje**. Mac clone zůstává fetch/pull; **žádný FS write** do klonu ze skills. (F0 A3, R23, R25; brief R23/A3)

R5 — Auth: Google OAuth = IdP; klient→Brain **user-bound OAuth**. Scopes F2 = vault; Gmail scopes až F3. (F0 A19)

R6 — Fail-path Grok plugin: **Claude + Cursor first**. Grok private plugin smoke **není** doložen PASS → MVP = Claude + Cursor; Grok opt-in po smoke. (F0 F2 fail-path + brief)

R7 — F1–F2: n8n INBOX writers **zůstávají vypnuté**; stale Slack INBOX OK do F3 (R26). (F0 R13, R26 + brief)

R8 — Pokryté F0 R# z F2 tabulky: **R2–R6, R10, R16, R19, R23** (+ vazby R4 autonomie vault, R25 writers, R8 model md). (F0)

R9 — Soft A17 Free (hard ruleset odložen) **neblokuje** F2. (brief + F1 A17 amend)

R10 — Schvalování plánu uživatelem: **ne**. (brief / ledger)

R11 — Po implementaci + QA: posunout vault krok **SB15-3**. (brief)

R12 — Lokální gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q` (+ nové testy Brain). TESTER: přeskočeno (profil SECOND_BRAIN). (brief)

R13 — Mimo rozsah: F3 Slack/Sembly/živá triáž/Gmail hybrid/OS push; F4 úklid Obsidian/Drive/poll + artifact dashboard jako samostatná pipeline; F5 boti; zapnutí n8n INBOX; hard GitHub ruleset / Pro; un-ignore `OBSIDIAN/` v tooling. (brief)

Netýká se: Alembic, RBAC Universe, frontend subnav, `qa_gate.mjs`, Playwright-T6, Celery.

---

## Předpoklady

A1 — F1 live platí dle [docs/git-vault-runbook.md](../git-vault-runbook.md): `VAULT_BACKEND=git`, Coolify WC host bind `/data/second-brain-vault` → `/data/vault`, deploy key write, Mac `~/GitHub/second-brain-vault` pull/read only, soft A17.

A2 — Brain = **samostatná Coolify app** (base dir `vps/second-brain-brain/`), sdílí **stejný persistent volume** `/data/vault` s hubem, aby `GitVault` flock (`second-brain-vault.lock`, timeout 5 s) serializoval dual-writer hub↔Brain. Oddělený clone = nepřijatelný race na `main`.

A3 — Grok private plugin smoke ≠ PASS → F2 MVP **bez** Grok pluginu / bez tvrzení B# pro Grok write. Skills text může zmínit Grok jako opt-in; enforce write = MCP (který Grok zatím nepřipojuje).

A4 — Claude routines MCP bug (F0 A8): proaktivita zůstává na VPS (F3+ push); F2 nevyžaduje Claude Schedules/routines. Interaktivní Claude Desktop/Cowork + remote MCP stačí.

A5 — Privacy / no-train (Cursor + Claude Team): považováno za **preflight checklist** F2-a; pokud fail → blokovat napojení klientů, ne blokovat vývoj služby. Grok Privacy = součást Grok opt-in.

A6 — Objem vaultu: F0 A7 (~782 MB / ~7432 souborů) zůstává řádově platný po F1; P rozpočet F0 P1/P2/P7 platí. Exact recount = QA T# inventář `du`/`find` na Coolify WC.

A7 — **FM kontrakt (R10) v F2** = (i) dokumentovaný kontrakt, (ii) dual-read starých wikilinků ve FM + nových `slug`/`id`, (iii) **nové zápisy** bez `aliases` a bez wikilinku v `project:` / `parent:` (jen slug / ID). **Hromadná migrace** všech existujících task FM = až když čtenáři (Brain + snapshot + skills) umí ID/slug (F0 migrace krok 10) — F2 dodá čtenáře + kontrakt; bulk rewrite = volitelný F2-late skript se dry-run, default **ne** auto-apply na celý vault.

A8 — Allowlist OAuth subjektů F2: `lukas@redbuttonedu.cz` (primární). `lukas.cypra@gmail.com` = stejný člověk, povolen jako alternativní Google účet pro IdP (stejný Brain user). Žádní další uživatelé.

A9 — Machine REST (artifact / budoucí n8n): **service token** (Bearer) s scope `vault` — oddělený od user OAuth. F2 nenasazuje n8n writers; token připraven, n8n off.

A10 — F2 MCP tool surface = **vault** (+ get_context). F3 tool stubs (`ingest_sembly`, `get_triage_candidates`, `propose_external_send` / mailbox mutate) vrací **501** s jasnou hláškou — žádná tichá no-op „úspěch“.

A11 — Mac: skills po F2 **píší jen přes Brain MCP**; lokální `git pull` + read klonu zůstává povolený pro rychlé čtení (snapshot, preview). `scripts/build_agent_context.py` a `schedule_reminder` schedule/cancel zůstávají fail-on-git-clone (F1 B23/B24); reminder schedule → Brain tool.

A12 — Rozpočet ≤50: F2 nesmí zavést nové usage-based bez explicitního OK; Coolify app + Google OAuth client = existující / provozní base mimo strop (F0 A6/A20). Žádný nový placený MCP hosting.

A13 — Doména Brain: `brain.redbuttonedu.cz` (nebo Coolify generated HTTPS) — veřejné HTTPS nutné pro OAuth redirect (F0 riziko 2). Konkrétní hostname potvrdí deploy; plán počítá s veřejným TLS.

A14 — `agent_write_guard` (Cowork/Grok FS policy) **nezaniká** hned: F2 server policy ho **superseduje** pro vault write path; guard zůstane pro případný legacy FS, ale skills default = MCP-only.

---

## Současný stav (ověřeno v kódu)

| Fakt | Důkaz |
|---|---|
| F1 cutover live, `VAULT_BACKEND=git`, Mac pull-only, soft A17 | [docs/git-vault-runbook.md](../git-vault-runbook.md) L15–27, L59–71 |
| `GitVault` + flock + CAS `expect_oid` + dirty-only commit/push | `vps/second-brain-hub/lib/git_io.py` L1–4, L36–37, L133–169, L336–365, L443–479, L551–579 |
| Factory `open_vault()` + `VAULT_WRITERS_PAUSED` | `vps/second-brain-hub/lib/vault_factory.py` L59–85 |
| Hub Dockerfile: supercronic + git/lfs, `/data/vault`, **bez** HTTP/MCP serveru | `vps/second-brain-hub/Dockerfile` L1–38 |
| Brain / MCP pod `vps/` **neexistuje** | glob `vps/**` = jen `second-brain-hub/` |
| Skills SSOT + Cursor symlink only | `scripts/install_agenda_skills.sh` L1–22; F0 L157 |
| Skills F1 banner: pull/read only, write až F2 | např. `ŠABLONY/skills/agenda-work/SKILL.md` L12; `agenda-capture/SKILL.md` L6 |
| Mac write guard git clone | `scripts/lib/vault_readonly.py` L8–21; `scripts/build_agent_context.py` L740–747 |
| Client write policy (FS, ne I/O) | `scripts/lib/agent_write_guard.py` L1–50 |
| Task FM šablona: `project: "[[…]]"`, `aliases: [ID]` | `ŠABLONY/obsidian-templates/task-template.md` L5–7 |
| `task_io.update_task` CAS přes `cas_from_meta` | `vps/second-brain-hub/lib/task_io.py` L132–169 |
| `next_task_id.py` skenuje lokální `OBSIDIAN/` (legacy path) | `scripts/next_task_id.py` L36–38 |
| Focus: cron nikdy, limit 5 | `vps/second-brain-hub/lib/focus.py` L1–20 |
| Light context helper | `vps/second-brain-hub/lib/agent_context_light.py` L1–36 |
| F0 Brain tools (cíl) + P1/P2/P7 | F0 L256, L399–406 |
| Claude project instructions stále Drive SSOT (legacy text) | `docs/claude-project-instructions.md` L9–19 |
| Hub requirements: Google auth + PyYAML, **bez** FastAPI/MCP | `vps/second-brain-hub/requirements.txt` |

### Mapa zapisovatelů po F2 (cíl)

| # | Actor | Mechanismus |
|---|---|---|
| W-cron | Lifecycle / agent-context / slack_poll / … | `GitVault` na shared WC, deploy key (beze změny F1) |
| W-brain | Cursor / Claude (+ Grok opt-in) přes MCP | Brain → `GitVault` stejný WC + flock |
| W-web | Člověk | GitHub web UI PR → Merge (soft A17) |
| W-n8n | — | vypnuto do F3 |
| W-mac-fs | Cursor/Cowork/Grok FS do klonu | **zakázáno** (skills + readonly scripts) |

---

## Návrh

### 0) Preflight (R6, A4, A5) — bez změny vault dat

- Checklist Privacy Mode / no-train (Cursor, Claude Team); výsledek do ledgeru.  
- Grok plugin smoke: pokud stále ne PASS → explicitní „Grok deferred“ v runbooku + B# mimo MVP.  
- Google Cloud OAuth client (Web) pro Brain: redirect `https://<brain-host>/oauth/callback`, scopes `openid email profile` (F2 vault identity only).

### 1) Sdílená vault vrstva (R3, R4)

| Soubor / místo | Co | Proč | R# |
|---|---|---|---|
| Reuse `git_io.py`, `vault_factory.py`, `drive_io.py` (errors/FileMeta), `task_io.py`, `focus.py`, `agent_context_light.py`, `hierarchy.py`, … | Brain image `COPY` z `vps/second-brain-hub/lib/` (ne fork logiky) | jedna CAS/flock pravda | R4, R19 |
| Coolify Brain volume | mount **stejný** host path jako hub → `/data/vault` | flock serializace | R4 |
| Env Brain | `VAULT_BACKEND=git`, `GIT_VAULT_*` stejně jako hub live; `GIT_AUTHOR_NAME=Second Brain Brain` | audit commit author | R4 |
| `VAULT_WRITERS_PAUSED` | Brain respektuje stejný kill-switch přes `open_vault()` | F1 A19 zachovat | R4 |

Úprava hubu jen pokud nutná pro sdílení (např. README dual-app); **žádná** změna cron chování.

### 2) Nová služba `vps/second-brain-brain/` (R2, R3, R5)

Struktura (nová):

```
vps/second-brain-brain/
  Dockerfile
  requirements.txt          # fastapi, uvicorn, mcp, authlib/httpx, PyJWT, PyYAML, …
  config.example.env
  README.md
  app/
    main.py                 # FastAPI + MCP mount
    auth_google.py          # OAuth + allowlist A8
    auth_service.py         # machine Bearer
    policy.py               # serverová policy (viz §4)
    fm_contract.py          # ID/slug normalize + dual-read
    tools/
      get_context.py
      vault_read.py
      task_ops.py           # allocate_id, create, update, get
      capture_daily.py
      stubs_f3.py
    rest.py                 # tenké REST zrcadlo tools
  tests/                    # pytest (temp git repo, jako test_git_io)
```

**Transport**

- MCP: Streamable HTTP (remote) na `/mcp` (nebo SDK default) — Cursor + Claude Desktop connectors.  
- REST: `/v1/context`, `/v1/tasks`, `/v1/capture/daily`, health `/healthz`.  
- OAuth: `/oauth/login`, `/oauth/callback`, token refresh.

**Auth (R5, A8, A9)**

- User: Google OAuth → session/JWT s `sub`+email; deny mimo allowlist → 403.  
- Machine: `BRAIN_SERVICE_TOKEN` Bearer, scope `vault:read|vault:write`.  
- **Žádný** default dev-bypass; volitelně `BRAIN_AUTH_DISABLED=1` jen v pytest.

### 3) MCP / REST tool kontrakt F2 (R2, R4, A10)

| Tool | Chování | R# |
|---|---|---|
| `get_context` | Čte `00-System/agent-context.json` (+ light volitelně). Pokud `generated_at` > 15 min → 1× refresh přes sdílenou logiku hub `build_agent_context` **nebo** vrátit stale + `stale: true` a doporučit pull (prefer: sync refresh pod flock, budget P1/P4). Payload light ≤ 256 KB. | R2, R15 F0 |
| `read_file` / `list_dir` | Path API přes `GitVault` read (bez commit). Deny path escape. | R4 |
| `allocate_task_id` | Server-side ceiling (port logiky `next_task_id.py`) nad vault WC pod flock; `--type` epic\|story\|task. | R8, R10 |
| `create_task` | Preview payload → write FM dle FM kontraktu + body; 1 session → 1 commit; CAS N/A (create). Filename `<ID> — <title>.md`. | R4, R8, R10 |
| `update_task` | Patch FM/body; CAS `expect_oid` povinné když klient poslal oid; retry ≤ 3. Zakázané: `focus` bez `user_said_focus`; zápis `## Stav (auto)`; Done jen z checkboxů bez explicit status. | R4, F0 focus |
| `capture_daily` | Append/create pod `01-INBOX/daily/`; policy jako allow_daily_create. | R4 |
| `write_material` | materials/ + sidecar konvence (R9 F0); bez `files/`. | R9 F0 |
| `set_focus` | Jen při `user_said_focus` + focus_count &lt; 5; jinak deny. | F0 focus |
| F3 stubs | `ingest_sembly`, `get_triage_candidates`, `propose_external_send`, mailbox mutate → **501** | A10, R13 |

Commit message: `brain: <tool> <short>` (odlišit od `hub:`).

Po úspěšném mutate: invalidace kontextu — buď inline refresh snapshotu (P7), nebo bump marker `agent-context.stale`; `get_context` musí nevracet tiše starý TOP po create_task bez upozornění.

### 4) Serverová policy (R2, R4, A14)

Port + zpřísnění `agent_write_guard` do `policy.py` (SSOT pro Brain):

- Deny: FS escape, zápis mimo allowlist kořenů (`01-INBOX/`, `02-PROJEKTY/`, `05-RESOURCES/`, `07-ARCHIV/…` dle operace, `00-System/` jen povolené podsložky).  
- Deny: `## Stav (auto)`, `focus` bez user flag, new task create mimo `create_task` tool, prefix-cut overwrite, Done-from-checkboxes-only bez explicit.  
- Allow: vault writes autonomně (F0 R4) — **bez** druhého „preview gate“ na serveru; preview zůstává ve skillu (klient). Server důvěřuje OAuth user + tool args.  
- Externí Slack/Gmail mutate: **ne v F2** (501).  
- Audit log (JSON lines): actor, tool, paths, oid, commit sha, deny reason — rotace na volume nebo stdout Coolify.

### 5) FM kontrakt ID/slug (R2, R8/R10 F0)

| Položka | F2 pravidlo |
|---|---|
| `id` | povinné, kanonické |
| `slug` | povinné u task/hub |
| `project` | **nové zápisy:** bare slug string (ne `[[Hub]]`); dual-read: pokud `[[…]]`, rozparsovat na hub filename → slug |
| `parent` | **nové:** bare ID (`RBU-E23`); dual-read wikilink |
| `aliases` | **nové zápisy:** pole vynechat / prázdné; dual-read ignorovat |
| Body wikilinky | beze změny (lidský text); migrace FM ≠ mazání body odkazů |
| Šablony | `ŠABLONY/obsidian-templates/task-template.md` + vault kopie dokumentovat v runbooku (vault edit = Brain/web UI) |
| Snapshot | `build_agent_context` umí číst dual FM (minimální patch hub pokud dnes předpokládá jen wikilink) |

Bulk migrátor: `scripts/fm_migrate_id_slug.py --dry-run` (tooling); ostrý běh jen po T# dual-read PASS — default mimo auto cutover.

### 6) Plugin SSOT (R2, R6, R16 F0)

| Klient | Distribuce F2 MVP |
|---|---|
| **Cursor** | `install_agenda_skills.sh` symlink beze změny zdroje; skills přepsat: write → Brain MCP tools; read = pull klonu OK. `~/.cursor/mcp.json` (nebo projekt) → remote Brain URL + OAuth. |
| **Claude** | Plugin/marketplace v tooling (`ŠABLONY/claude-plugin/` nebo `.claude-plugin/`): skills balík + odkaz na managed MCP URL; instructions nahradit Drive SSOT → git vault + Brain (`docs/claude-project-instructions.md`). |
| **Grok** | Dokumentovaný opt-in po smoke; do PASS neblokuje F2 DONE. |

Skill rewrite (všechny F1 bannery → F2):

- „Vault write jen Brain MCP tools X/Y; FS write do `SECOND_BRAIN_VAULT` zakázán.“  
- `next_task_id.py` lokálně: jen diagnostika / offline; **create** vždy `allocate_task_id` + `create_task` na Brain.  
- `agenda-remind`: schedule přes Brain tool (ne Mac script).  
- Cowork guide (`agent-guide-mimo-cursor`): denní capture může jít přes `capture_daily` MCP; nové tasky smí Cowork přes Brain `create_task` (ruší F1 „jen daily text“) — **A15**: po F2 Cowork/Claude rovnocenní Cursoru vůči vault write (F0 R2).

### 7) Docs / runbook / SB15 (R11)

| Soubor | Co |
|---|---|
| `docs/brain-api-runbook.md` | deploy Coolify, OAuth, env, dual volume, smoke, rollback |
| `docs/git-vault-runbook.md` | doplnit W-brain + shared volume |
| `docs/claude-project-instructions.md` | git vault + MCP |
| Vault **SB15-3** | odškrtnout po QA PASS |
| F0 sync-architecture odkaz | Brain vrstva |

### 8) Coolify / deploy (R3, R12)

- Nová app Auto Deploy z `main`, base `vps/second-brain-brain`.  
- Env z `config.example.env` (OAuth client id/secret, allowlist, service token, `GIT_SSH_COMMAND` stejný deploy key mount).  
- Healthcheck `/healthz`.  
- Hub app **neměnit** crontab při Brain deployi.

---

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | Neautentizovaný MCP/REST mutate | 401 | R5 | T2 |
| B2 | OAuth email mimo allowlist | 403 | R5, A8 | T2 |
| B3 | Platný user OAuth + `get_context` | JSON snapshot; P1 latence; při stale &gt;15 min refresh nebo explicit `stale` | R2 | T3, T10 |
| B4 | `create_task` validní payload | soubor v `02-PROJEKTY/<slug>/tasks/`; FM bez `aliases`; `project`=slug; 1 git commit+push; author Brain | R4, R10 | T4 |
| B5 | `update_task` se špatným `expect_oid` | konflikt (409 / structured error); žádný commit | R4 | T4 |
| B6 | `update_task` `focus` bez `user_said_focus` | deny policy; žádný zápis | R4 | T5 |
| B7 | Pokus zapsat `## Stav (auto)` | deny | R4 | T5 |
| B8 | `allocate_task_id` 2× paralelně (flock) | unikátní ID, žádná kolize | R8 | T6 |
| B9 | Skill na Macu provede FS write do git klonu | zakázáno skill textem + readonly scripts fail; write cesta = MCP | R4, R23 | T7 |
| B10 | Cursor + Claude připojení na remote MCP | list tools obsahuje F2 sadu; create_task smoke OK | R2, R6, R16 | T8 |
| B11 | Grok bez smoke PASS | není požadavek na B10; dokument deferred | R6 | T1 |
| B12 | F3 stub tool | 501 + zpráva „F3“ | A10 | T2 |
| B13 | `VAULT_WRITERS_PAUSED=1` | Brain mutate → VaultPausedError / 503 | R4 | T4 |
| B14 | Hub cron běží + Brain write současně | jeden flock holder; druhý skip/retry; žádný rozbitý push | R4 | T6, T9 |
| B15 | Service token REST `GET /v1/context` | 200; write s tokenem OK; bez tokenu 401 | A9 | T2 |
| B16 | FM dual-read: starý `project: "[[Hub]]"` | update_task/get najde task; nový create už slug | R10, A7 | T5 |
| B17 | n8n INBOX stále off | žádný Brain ingest z n8n v F2 | R7 | T1 |
| B18 | Stale Slack INBOX | akceptováno; žádná F2 povinnost čistit | R7 / R26 | T1 |
| B19 | Soft A17 | F2 nepožaduje hard ruleset | R9 | T1 |
| B20 | SB15-3 po DONE | checkbox odškrtnut | R11 | T11 |
| B21 | Computer use zápis souborů klonu | stále zakázán; vault jen MCP | R3 F0 / R25 | T7 |
| B22 | Externí Slack send přes Brain F2 | 501 (ne tichý send) | R4 F0 autonomie | T2 |

Checklist A (RB Universe) — SECOND_BRAIN mapování:

1. Prázdná data — B3 prázdný/missing context → jasná chyba.  
2. None hodnoty — B5/B16 chybějící oid/FM.  
3. Hranice období — `focus` ISO week Europe/Prague (B6).  
4. Měny/DPH — **netýká se**.  
5. Oprávnění — B1/B2/B15 (Google allowlist + service token), ne Universe RBAC.  
6. Stav syncu — B3 stale snapshot / P7.  
7. Smazané entity — Cancelled/archiv ID ceiling v allocate (B8).  
8. Duplicitní akce — B8/B14 flock; idempotentní capture dle path.  
9. Chyba externí služby — Google OAuth down → 503 login; git push fail → error klientovi (ne tichý OK).  
10. Zpětná kompatibilita — B16 dual FM; Mac pull read.  
11. Konzistence systémů — **netýká se** Pipedrive/Allfred.

CAS/idempotence/focus — B5–B7, B13–B14.

---

## Výkonový rozpočet (P)

Objem (A6): ~7–8k souborů / &lt;1 GB WC — ověřit `du -sh /data/vault` na Coolify (T9).

| Tělo | 1 Objem | 2 Dotazy | 3 Load | 4 Externí | 5 Stránkování | 6 Payload | 7 Cache | 8 Násobení | 9 FE | 10 Worker | 11 Cíl měření |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 `get_context` | 1× JSON snapshot | 0 SQL; 1 file read (+ opt 1 rebuild) | jen agent-context(+light) | ne | N/A | ≤256 KB light | TTL align 15 min; invalidace po Brain write | 1 req | N/A | uvicorn | cold ≤2 s, warm ≤500 ms (F0 P1) |
| P2 `create/update_task` | 1–N file ops | 0 SQL | task file + id scan omezený na prefix cesty | ne | N/A | request &lt; 1 MB text | N/A | 1 session/commit | N/A | flock ≤5 s; CAS retry ≤3; 1 push | wall ≤5 s typicky (F0 P2) |
| P3 hub cron | beze změny F1 | — | — | — | — | — | — | — | — | — | F0 P3 |
| P4 refresh context | celý vault scan jako dnes | — | — | — | — | — | — | max 1 / get_context když stale | — | — | &lt;30 s VPS (F0 P4) |
| P5 triáž Gmail/Slack live | **netýká se F2** (F3) | | | | | | | | | | |
| P6 Sembly | **netýká se F2** | | | | | | | | | | |
| P7 invalidace | po mutate | — | — | — | — | — | povinná | — | — | — | get_context po create vidí nový task nebo `stale` |
| P8 SQL | netýká se | | | | | | | | | | |
| P9 binárky | materials dle F1 LFS gate | — | — | — | — | odmítnout &gt;40 MiB | — | — | — | — | 413 |
| P10 idempotence | capture stejná cesta | — | — | — | — | — | — | — | — | — | druhý zápis CAS/overwrite dle tool |
| P11 | netýká se F2 push | | | | | | | | | | |

Anti-patterny Universe PERF — netýká se (žádný SQL/Allfred). Anti-pattern SB: full-repo walk na každý `read_file` = zakázán; `allocate_task_id` skenuje jen relevantní stropy (jako `next_task_id`).

---

## Testy (T#)

| T# | Typ | Owner | Soubor | B# |
|---|---|---|---|---|
| T1 | ruční checklist | gate | runbook + ledger preflight (Privacy, Grok deferred, n8n off, A17 soft) | B11, B17–B19 |
| T2 | pytest | gate | `vps/second-brain-brain/tests/test_auth_policy_stubs.py` | B1, B2, B12, B15, B22 |
| T3 | pytest | gate | `…/test_get_context.py` (temp vault) | B3 |
| T4 | pytest | gate | `…/test_task_ops_cas.py` | B4, B5, B13 |
| T5 | pytest | gate | `…/test_policy_fm.py` | B6, B7, B16 |
| T6 | pytest | gate | `…/test_allocate_id_flock.py` | B8, B14 |
| T7 | pytest + ruční | gate | skills grep F2 banner; `vault_readonly` beze regrese | B9, B21 |
| T8 | ruční smoke | gate | Cursor + Claude Desktop → OAuth → `create_task` na tip vaultu (nebo dry-run env) | B10 |
| T9 | QA Coolify | gate | deploy image; `/healthz`; shared volume flock; `du` objem; log commit `brain:` | B14, P* |
| T10 | smoke latence | gate | měření get_context cold/warm proti P1 | B3, P1 |
| T11 | ruční vault | gate | SB15-3 odškrtnuto | B20 |
| T12 | pytest hub regress | gate | stávající `vps/second-brain-hub/tests` + `scripts/tests` | regrese F1 |

TESTER: přeskočeno (profil SECOND_BRAIN).  
Playwright-T6-full: netýká se.

---

## Pořadí implementace

F2-a — Preflight Privacy + Grok deferred zápis; OAuth client; hostname.  
F2-b — Scaffold `vps/second-brain-brain/` + Dockerfile + shared lib COPY + healthz.  
F2-c — Auth Google allowlist + service token.  
F2-d — Policy + FM contract dual-read/write.  
F2-e — Tools: get_context, read/list, allocate, create/update, capture_daily, set_focus; F3 stubs 501.  
F2-f — REST zrcadlo + audit log.  
F2-g — Pytest T2–T6, T12 zelená lokálně.  
F2-h — Coolify app + shared volume + deploy key mount; T9.  
F2-i — Skill rewrite + `install_agenda_skills.sh` (beze změny mechanismu) + Claude plugin/instructions + Cursor MCP config docs.  
F2-j — Šablony FM + runbooky; volitelný `fm_migrate_id_slug.py --dry-run`.  
F2-k — T8 klient smoke Cursor+Claude; T10 latence; T11 SB15-3.  
F2-l — Grok opt-in (mimo MVP DONE) až po samostatném smoke.

Závislosti: F2-b→c→d→e; F2-h po F2-g; F2-i po F2-h (URL); F2-k uzavírá.

---

## Rizika a zpětná kompatibilita

1. **Dual-writer hub↔Brain** — mitigace shared volume + flock; při skip Brain retry; monitoring dirty-WT skip (F1 A18).  
2. **OAuth / veřejné HTTPS** — bez TLS klienti nepřípojí; fail = jen Cursor service token dočasně **ne** (dev-bypass zakázán) → blokovat cutover klientů.  
3. **Grok plugin** — odloženo; riziko F0 #1 akceptováno fail-pathem.  
4. **Claude routines bug** — F2 neřeší proaktivitu; A4.  
5. **FM dual-read drift** — staré wikilinky vs nové slug; bulk migrate odložen (A7) → dokumentovat.  
6. **Mac agents obejdou MCP FS writem** — skill + readonly scripts; CU zákaz zůstává; soft A17 nechrání před lokálním commitem pokud někdo přidá push URL (F1 riziko).  
7. **Snapshot race** — create_task vs cron build_agent_context; P7 invalidace.  
8. **Service token únik** — Coolify secret; rotace v runbooku.  
9. **Legacy `next_task_id.py` path `OBSIDIAN/`** — po F1 klon jinde → skript musí respektovat `SECOND_BRAIN_VAULT` (součást F2-i), jinak špatný ceiling.  
10. **Návod 2026-10-04** — po F2 MCP write superseded (F0 riziko 10); aktualizovat guide.  
11. **Rozpočet** — žádné nové usage-based v F2 (A12).

---

## Otevřené otázky pro uživatele

1. **Hostname Brain** — předpoklad `brain.redbuttonedu.cz` (A13). Jiná subdoména → jen DNS/Coolify, plán toolů beze změny.  
2. **OAuth allowlist** — default Workspace + osobní Gmail (A8). Jen Workspace → osobní Claude login nesmí; plán auth zúžit.  
3. **Cowork `create_task` rovnocenně Cursoru** — A15 ano (F0 R2). Ne → policy deny create pro actor≠Cursor a návrat k daily-only pro Cowork.  
4. **get_context při stale** — prefer sync rebuild pod flock (P1/P4). Alternativa: vždy vracet stale JSON + flag (rychlejší, slabší UX) → změna B3/T3.  
5. **Bulk FM migrace v F2** — default ne (A7). Ano → přibude F2-m ostrý migrátor + T# na vzorek vaultu.  
6. **Grok opt-in termín** — mimo F2 DONE; až bude smoke PASS, malá pipeline na plugin wiring bez změny Brain tools.

---

*Profil SECOND_BRAIN: po SCHVÁLENO kritika → implementace na `main`, gate pytest, Coolify deploy Brain + hub regress, TESTER přeskočen.*
