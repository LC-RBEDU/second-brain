# Pipeline: SB operační model F2

Stav: AWAITING_USER (z: ENV B25 Grok webhook + OAuth redirect)
Plán: docs/plans/2026-10-10-sb-operacni-model-f2.md
Schvalování plánu uživatelem: ne
Architekt: 1346c52e… · otevření #2 · k=2/3 · r=2/3 · SCHVÁLENO
Šťoural: 91285bfd… · g=13 HOTOVÝ
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 1/5 · kola QA 1/5 · kola TESTER 0/5 · ENV opravy 1/2
Base (origin/main před pipeline): ca95c2f1388c1b7605c27ef9113219821e58a1f1 · Kódový SHA: f4514a6 · Review SCHVÁLENO na: 4d8ab9f · QA PASS na: 494bda9 · TESTER PASS na: přeskočeno (profil SECOND_BRAIN)
Plán schválen uživatelem: nevyžadováno
Goal: paused-awaiting-user
Profil: SECOND_BRAIN

## Zadání (doslovně)

rovnou /rbu-pipeline na F2

(kontext: F0 SCHVÁLENO; F1 cutover hotov 2026-10-10; soft A17 Free; další krok SB15-3)

## Rozhodnutí z konverzace

- Parent: F0 `docs/plans/2026-10-10-sb-operacni-model-f0.md` (B1–B22), F1 DONE cutover.
- Vault SSOT = `LC-RBEDU/second-brain-vault`; Coolify `VAULT_BACKEND=git` live.
- F2 scope z F0 tabulky: Brain API; klienti vault MCP write; plugin SSOT; serverová policy; FM kontrakt ID/slug.
- F1–F2: n8n INBOX zůstává vypnuté; stale Slack INBOX OK do F3.
- Schvalování plánu: ne.
- Soft A17 Free.
- `BRAIN_PUBLIC_URL` = MCP + OAuth + REST (ne dashboard UI; UI = Claude artifact).

### Grill g=1 odpovědi (2026-10-10)

- **Q1 (remind) = (a)** Brain MCP `schedule_reminder` / cancel / list.  
  **Doručení ping = (C) už ve F2:** Grok Bot je **plnohodnotná součást** — primární app-notification na mobil při due. Sekundárně Claude. **Cursor vynechat**. Slack a/nebo systémové To-do/Reminder = volitelná záloha.  
  **Důsledek pro F2 DONE:** Grok plugin smoke + reminder→Grok notification path je **v scope F2** (ne odklad na F3). Slack DM cron může zůstat fallback, ale primár je Grok. Fail Grok push = FAIL B# / ne tichý „jen Slack OK“ bez zmínky.
- **Q2 = (a)** `get_context` při stale (>15 min): sync rebuild pod flock; flock busy → 503/retry, ne tichý starý TOP.
- **Q3 = (a)+** všichni OAuth klienti stejná vault tool sada včetně **`create_task`**: Cursor **a** Claude/Cowork **a** Grok Bot. Grok MCP write + plugin smoke = **povinné pro F2 DONE** (ne opt-in mimo DONE).
- **Q4 = (a)** T8/B10 smoke proti **live tipu**, ale jen do projektu **`TEST`** (hub + tasks dle potřeby); nic „ostrého“ mimo TEST. Po smoke lze Cancelled/archivovat.
- **Q5 NEBLOKUJÍCÍ:** allowlist Workspace + osobní Gmail; service token audit jako `service:`.
- **Q6 NEBLOKUJÍCÍ:** hostname **nezamykat** — veřejné HTTPS + OAuth `https://<host>/oauth/callback` pro MCP/REST (ne UI dashboard); host doplní uživatel (`BRAIN_PUBLIC_URL`).
- **Q7 NEBLOKUJÍCÍ:** bez bulk FM apply v F2 DONE.
- **Q8 NEBLOKUJÍCÍ:** Brain retry flock 1–2×, pak 503.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-10-10 | PLAN | 69a6222d… | draft plán | — | F2 Brain API + plugin SSOT |
| 2 | 2026-10-10 | GRILL | ec5513b7… | POTŘEBUJE ODPOVĚDI | — | Q1–Q4 BLOKUJÍCÍ |
| 3 | 2026-10-10 | AWAITING_USER | — | grill | — | Goal paused |
| 4 | 2026-10-10 | PLAN | 69a6222d… (r=2) | draft plán | — | Grok C + Q1–Q8 zapracováno |
| 5 | 2026-10-10 | GRILL | 9d497573… (g=2) | POTŘEBUJE ODPOVĚDI | — | Q1–Q4 BLOKUJÍCÍ |
| 6 | 2026-10-10 | AWAITING_USER | — | grill | — | Goal paused |
| 7 | 2026-10-10 | PLAN | 69a6222d… (r=3) | draft plán | — | chat model + Q1–Q4 g=2 |
| 8 | 2026-10-10 | GRILL | 77b76c52… (g=3) | HOTOVÝ | — | A22–A28 NEBLOKUJÍCÍ → critic |
| 9 | 2026-10-10 | CRITIC | 2e635fca… | K PŘEPRACOVÁNÍ | 0B / 5M / 2m | r=3 vyčerpáno → architekt k=2 |
| 10 | 2026-10-10 | PLAN | 129b44c5… (k=2 r=1) | draft plán | — | NEW-1…7 zapracováno |
| 11 | 2026-10-10 | GRILL | 2ccbeb5d… (g=4) | HOTOVÝ | — | A32–A36 → critic |
| 12 | 2026-10-10 | CRITIC | 5de0b7f0… | K PŘEPRACOVÁNÍ | 2B / 3M / 2m | NEW-7/8 BLOCKER → architekt r=2 |
| 13 | 2026-10-10 | PLAN | 129b44c5… (r=2) | draft plán | — | NEW-5,7–12 opraveno |
| 14 | 2026-10-10 | GRILL | b0c07443… (g=5) | HOTOVÝ | — | A37 → critic |
| 15 | 2026-10-10 | CRITIC | 6150b0b4… | K PŘEPRACOVÁNÍ | 3B / 3M / 3m | session/push/builder → r=3 |
| 16 | 2026-10-10 | PLAN | 129b44c5… (r=3) | draft plán | — | session/push/builder/plugin |
| 17 | 2026-10-10 | GRILL | d927723e… (g=6) | HOTOVÝ | — | A43–A45 → critic |
| 18 | 2026-10-10 | CRITIC | 4b4fcecf… | K PŘEPRACOVÁNÍ | 1B / 2M / 1m | dirty WT + B8 + PUSH=0 → k=3 |
| 19 | 2026-10-10 | PLAN | 416e4fae… (k=3 r=1) | draft plán | — | dirty discard + B8 + PUSH runtime |
| 20 | 2026-10-10 | GRILL | eef1256d… (g=7) | POTŘEBUJE ODPOVĚDI | — | Q1 dirty WT BLOKUJÍCÍ |
| 21 | 2026-10-10 | AWAITING_USER | — | grill | — | Goal paused |
| 22 | 2026-10-10 | CRITIC | 8cf5f1e3… | K PŘEPRACOVÁNÍ | 1B / 2M / 2m | discard guard + factory + reminders → r=2 |
| 23 | 2026-10-10 | PLAN | 416e4fae… (r=2) | draft plán | — | discard guard + factory + reminders |
| 24 | 2026-10-10 | CRITIC | 6bf34c5e… | K PŘEPRACOVÁNÍ | 1B / 0M / 2m | nested open_vault → r=3 |
| 25 | 2026-10-10 | PLAN | 416e4fae… (r=3) | draft plán | — | R29 bundle bez session |
| 26 | 2026-10-10 | CRITIC | d28e95c7… | K PŘEPRACOVÁNÍ | 1B / 2M / 1m | strop → AWAITING_USER |
| 27 | 2026-10-10 | AWAITING_USER | — | critic | — | strop; defaulty zamčeny hlavním agentem (doporučení kritika) |
| 28 | 2026-10-10 | PLAN | 0fa2eeed… | draft plán | — | otevření #2: C1–C4 zapracováno |
| 29 | 2026-10-10 | GRILL | 73ca74a8… | HOTOVÝ | — | A52–A54 NEBLOKUJÍCÍ → critic |
| 30 | 2026-10-10 | CRITIC | a218008b… | K PŘEPRACOVÁNÍ | 0B / 1M / 1m | NEW-1 A52≠B42 → r=2 |
| 31 | 2026-10-10 | PLAN | 0fa2eeed… | r=2 | — | A52 ahead≠B42; A29 hub full |
| 32 | 2026-10-10 | GRILL | 3f6af45b… | POTŘEBUJE ODPOVĚDI | — | Q1 BLOKUJÍCÍ tip ahead |
| 33 | 2026-10-10 | AWAITING_USER | — | grill | — | g=9 Q1 (a/b/c) |
| 34 | 2026-10-10 | PLAN | 0fa2eeed… | r=3 | — | R30/A55/B45/B46 |
| 35 | 2026-10-10 | GRILL | 95076034… | POTŘEBUJE ODPOVĚDI | — | Q1 get_context+rebuild |
| 36 | 2026-10-10 | AWAITING_USER | — | grill | — | g=10 Q1 |
| 37 | 2026-10-10 | PLAN | 0fa2eeed… | r=3 delta g=10 | — | Q1=a + A57/A58 |
| 38 | 2026-10-10 | GRILL | 57549dc1… | HOTOVÝ | — | A58+=vault_paused → critic |
| 39 | 2026-10-10 | CRITIC | b87a8d22… | K PŘEPRACOVÁNÍ | 1B / 2M / 1m | skip_reason → k=2 |
| 40 | 2026-10-10 | PLAN | 1346c52e… | k=2 r=1 | — | A59–A61 |
| 41 | 2026-10-10 | GRILL | db21dcc5… | HOTOVÝ | — | A62–A64 → critic |
| 42 | 2026-10-10 | CRITIC | 7db484d6… | K PŘEPRACOVÁNÍ | 0B / 2M / 1m | §2/F2-b vs A60 → r=2 |
| 43 | 2026-10-10 | PLAN | 1346c52e… | r=2 | — | §2/F2-b brain_vault |
| 44 | 2026-10-10 | GRILL | 91285bfd… | HOTOVÝ | — | → critic |
| 45 | 2026-10-10 | CRITIC | 482a6562… | SCHVÁLENO | 0B / 0M / 1m | A38 editorial → IMPLEMENT |
| 46 | 2026-10-10 | IMPLEMENT | — | F2-b partial | — | skip_reason + strict_push + factory kwargs; test_git_io 14 passed |
| 47 | 2026-10-10 | IMPLEMENT | — | F2-b done | — | agent_context_build + thin cron; tombstone; task_id_allocate; reminders A51; Brain scaffold + brain_vault A60–A64; pytest 356 passed; commit d6be833 |
| 48 | 2026-10-10 | IMPLEMENT | — | F2-a+c+e | — | runbook Grok webhook; auth B37; get_context/read_file + REST stubs; commit b5f97d6; pytest 361 |
| 49 | 2026-10-10 | IMPLEMENT | — | F2-e/f tools | — | create_task, allocate, reminders REST + service auth; F3 501; brain venv tests 17 |
| 50 | 2026-10-10 | IMPLEMENT | — | F2-i+j | — | reminders_dispatch Grok→Claude→Slack (C4); plugin manifest examples; hub pytest 351 |
| 51 | 2026-10-10 | REVIEW | d5ed336d… | K OPRAVĚ | 2B / 6M / 3m | NEW-1 MCP; NEW-2 OAuth → IMPLEMENT |
| 52 | 2026-10-10 | IMPLEMENT | — | review fixes | — | MCP /mcp + OAuth + agenda-remind; brain tests 20 |
| 53 | 2026-10-10 | REVIEW | ee0c0d0a… | K OPRAVĚ | 1B MCP auth | NEW-3 → IMPLEMENT |
| 54 | 2026-10-10 | IMPLEMENT | — | MCP auth+tools | — | McpAuthMiddleware; list_dir/update_task/set_focus; B34b+paused tests; → REVIEW |
| 55 | 2026-10-10 | REVIEW | 35945c7e… | K OPRAVĚ | 0B / 3M / 2m | B35b/CAS/T# → IMPLEMENT |
| 56 | 2026-10-10 | IMPLEMENT | — | MAJOR fixes | — | get_context→503; CAS 409; tip/B34 skipped tests; pytest brain 28 / hub 354 |
| 57 | 2026-10-10 | REVIEW | 23c7ece6… | K OPRAVĚ | 0B / 3M | T3/B5/A56 tests → IMPLEMENT |
| 58 | 2026-10-10 | IMPLEMENT | — | T3/B5/A56 | — | B35b+CAS pytest; A56 misconfig≠dirty; runbook dual-session; brain 30 / hub 354 |
| 59 | 2026-10-10 | REVIEW | 9ba70927… | SCHVÁLENO | 0B / 0M / 2m | tip 4d8ab9f → push/QA |
| 60 | 2026-10-10 | QA | 68fe5424… | PASS | — | hub Coolify `494bda9`; pytest 354+28; B# gate OK |
| 61 | 2026-10-10 | TESTER | — | přeskočeno | — | profil SECOND_BRAIN |
| 62 | 2026-10-10 | AWAITING_USER | — | ENV | — | F2 DONE blokuje: Coolify Brain + BRAIN_PUBLIC_URL + Grok webhook (B11/B25 hard) |
| 63 | 2026-10-10 | IMPLEMENT | — | ENV F2-h | — | Coolify app `second-brain-brain` uuid `23c9620d…`; sslip FQDN; vault+SSH mounts; deploy fail = image bez curl → Dockerfile +curl |
| 64 | 2026-10-10 | IMPLEMENT | — | ENV F2-h PASS | — | tip `f4514a6` healthy; `/healthz` 200; `BRAIN_PUBLIC_URL=https://23c9620dbd341d2716acec9b.72.62.152.9.sslip.io` |
| 65 | 2026-10-10 | AWAITING_USER | — | ENV | — | B25: Grok routine webhook URL+key → hub env; Google OAuth redirect = `{BRAIN_PUBLIC_URL}/oauth/callback` |
| 66 | 2026-10-10 | IMPLEMENT | — | ENV FQDN | — | `brain.cyprovi.cz` + LE; sslip pryč; OAuth redirect už v GCP; zbývá Grok webhook (B25) |
| 67 | 2026-10-11 | IMPLEMENT | — | B25 hub | — | hub redeploy + smoke `B25-smoke-20261011T000551` → `grok=ok http=200` → Reminders-Sent; čeká potvrzení zprávy v Bot chatu + B11 MCP |

### Grill g=10 odpověď (2026-10-10)

- **Q1 = (a)** tip ahead ∧ needs_rebuild → **503** `vault_tip_ahead` (+ message do chatu); žádný warm/stale snapshot, žádný rebuild. Warm get_context (needs_rebuild=false) při tip ahead OK.
- **Q2 = (a) / A57:** MCP `isError` + text `content` nese `error_reason` i `message`; REST 503 JSON stejně.
- **Q3 = (a) / A58:** enum ⊇ A55 + `vault_flock_busy` + `vault_push_disabled`; B46 = všechny vault 503.

### Grill g=9 odpověď (2026-10-10)

- **Q1 = (b)** Brain mutate když `HEAD ≠ @{upstream}` → **503** `vault_tip_ahead`, žádný nový commit; read-only OK. Ops = Lukáš/agent SSH uklidí tip.
- **Signál povinný:** error musí dorazit **do chatu** klienta (MCP/tool error body), ne jen Coolify log. Reason + krátká hláška („tip ahead — ukliď vault / SSH“).
- **Q2 / A55:** stabilní `error_reason` v 503: `vault_dirty_start` | `vault_push_reset_ok` | `vault_push_reset_failed` | `vault_tip_ahead`.

### Grill g=8 (HOTOVÝ) — NEBLOKUJÍCÍ A52–A54

- **A52:** C1 recovery → porcelain clean před raise; fail recovery = 503 + log, ne start reset.
- **A53:** A46 nesmí sahat na `GitPushError` z fail-push path.
- **A54:** no Slack token po fail Grok/Claude = B29 attempt++.

### Critic strop d28e95c7 — zamčené defaulty (otevření #2)

- **C1 (BLOCKER NEW-1):** `strict_push` + fail push → nejdřív `git reset --hard @{upstream}` (jako F1 B6), **pak** raise `GitPushError` → Brain 503. Nesmí zůstat dirty WT po fail push.
- **C2 (MAJOR):** `stale` = `generated_at` starší než **15 minut** (grill g=1 Q2); explicitně v R15 / §3 / B3.
- **C3 (MAJOR):** A29 přesun konstant musí zahrnout i `LESSON_TAKEAWAY_RE` (`cron/build_agent_context.py` L51) — ne jen L80–84.
- **C4 (MINOR):** A27/B33 — early-return při chybějícím Slack tokenu až **po** Grok/Claude pokusu (ne před nimi).

### Grill g=7 odpověď (2026-10-10)

- **Q1 = (b)** Dirty WT na startu Brain session → skip + 503, **žádný** reset/discard (jako F1). Cizí dirty na sdíleném volume se nemaže. A46 discard jen po vlastní výjimce uprostřed Brain requestu.

### Grill g=2 odpovědi (2026-10-10)

- **Model připomínky (uživatel):** připomínka = **zpráva do chatu** (Grok / Claude / Slack). OS push / „pípnutí“ = nastavení aplikace u uživatele, **ne** požadavek na Brain/hub. Systém PASS = zpráva dorazila na jeden kanál dle priority (Grok → Claude → Slack).
- **Q1 = chat delivery (ne OS push API):** nový chat / zpráva v Grokovi stačí; push si řeší uživatel v Grok appce. B25/T13 = důkaz „Grok dostal/zobrazil zprávu o reminderu“, ne vlastní VPS→OS notification stack.
- **Q2 = (b)** notify-first OK; důležitější je že se Grok ozve na chatu; double ping akceptovatelný.
- **Q3 = (b)** pending + backoff, max K pokusů, pak failed.
- **Q4 = (a)** Cursor/Claude/Grok jen user-bound OAuth; service token jen machine/n8n.
- **NEBLOKUJÍCÍ default (a):** Claude bez API = skip+log; systémové To-do mimo F2; TEST prefix next_task_id; invalidace snapshotu na disku; chybějící Grok secret = fail v řetězci + error log.

## Otevřené nálezy

| ID | Závažnost | Typ | Stav | Kolikrát |
|---|---|---|---|---|
| NEW-1 | MAJOR | PLAN | closed (k=2) | 1 |
| NEW-2 | MAJOR | PLAN | closed (k=2) | 1 |
| NEW-3 | MAJOR | PLAN | closed (k=2) | 1 |
| NEW-4 | MAJOR | PLAN | closed (k=2) | 1 |
| NEW-5 | MAJOR | PLAN | closed (k=2) | 1 |
| NEW-6 | MINOR | PLAN | closed (k=2) | 1 |
| NEW-5 | MAJOR | PLAN | closed (r=2) | 2 |
| NEW-7 | BLOCKER | PLAN | closed (r=2) | 2 |
| NEW-8 | BLOCKER | PLAN | closed (r=2) | 1 |
| NEW-9 | MAJOR | PLAN | closed (r=2) | 1 |
| NEW-10 | MAJOR | PLAN | closed (r=2) | 1 |
| NEW-11 | MINOR | PLAN | closed (r=2) | 1 |
| NEW-12 | MINOR | PLAN | closed (r=2) | 1 |

### Critic 2e635fca (k=1 r=3) — shrnutí

1. **NEW-1:** sync rebuild není v `lib/` — vytáhnout builder do shared lib nebo Brain COPY cron modul; stejná build funkce jako hub.
2. **NEW-2:** před jakýmkoli chat send kontrolovat `vault.skipped` / flock (jako dnešní Slack); jinak žádný kanál.
3. **NEW-3:** B33 + T13 — chybějící Slack token nesmí abortovat před Grok/Claude (A27).
4. **NEW-4:** F2-a hard exit = kontrakt Grok chat send v runbooku (URL/env/target/failures) před F2-i; jinak eskalace (ne oslabit B25).
5. **NEW-5:** missing/tombstone snapshot → sync rebuild (ne jen stale TTL).
6. **NEW-6:** dual-read `last_error`\\|\\|`error`.
7. **NEW-7:** Brain rebuild = stejné trio (full + light + charters) jako hub.

NEBLOKUJÍCÍ default: F2-a bez Grok chat API → eskalace uživateli, ne oslabení B25 (A3/A28).
