# Plán: F3 — Slack / Sembly / živá triáž / Gmail hybrid / briefy

> Architekt: **k=2 · r=3** (otevření #2; resume po kritice C15–C18; C1–C14 uzavřeny)  
> Parent F0 (SCHVÁLENO): [2026-10-10-sb-operacni-model-f0.md](2026-10-10-sb-operacni-model-f0.md) · F1 DONE · F2 DONE 2026-10-11  
> Pipeline ledger: [2026-10-10-sb-operacni-model-f3.pipeline.md](2026-10-10-sb-operacni-model-f3.pipeline.md)  
> Vault: **SB15 — Nový operační model SB** (**SB15-4**)  
> Profil: **SECOND_BRAIN**. Base tip před pipeline: `f893b01b6972b3fc55af6dd44639f1ae31e8548e`.  
> Pre-F3 smoke: MCP `get_context` OK; `create_task` → **SBD-S20** (Cancelled).  
> Schvalování plánu uživatelem: **ne**. Soft A17 Free. TESTER: přeskočeno (profil SECOND_BRAIN).  
> Grill g=1–g=5 (A19–A29) + **C1 apply UX** + **C9–C18** zapracováno. Meeting prep okno default **70 min**; cadence **`*/15`** (accepted).

## Zadání a požadavky

R1 — Po F2 DONE a krátkém smoke spustit F3 pipeline (uživatel: „ok, spusť krátký smoke a pak F3“; kotva **SB15-4**).

R2 — Scope F3 z F0 tabulky: Slack (live tool + dump parallel); Sembly n8n→brain→skill; Gmail hybrid L1/L2/apply; batch approve UX; OS notifikace gate; briefy / proaktivita; **jednotná meeting prep**. (F0 F3 + grill g=1/g=2)

R3 — F2 stubs (`f3_stub` → 501 REST i MCP) nahradit reálnými tools; žádný permanentní stub v DONE. (F2 A10)

R4 — Autonomie a mutate UX (**C1**):  
- Vault zapisovat přes Brain.  
- Navenek (Slack send, Gmail trash/archive/send, …): v **živé session** nejdřív **povinný** Brain `propose` + preview; pak chat schválení; teprve pak client apply. (**C11** — propose není optional.)  
- **Vratné** (archive, kopie, přesun, Gmail trash = obnovitelný koš): po „ano, udělej…“ → **1× confirm** → **client apply**.  
- **Nevratné** (odeslat Slack/e-mail, permanent delete): po prvním „ano“ → **druhá otázka ve stejné appce** → teprve pak **client apply**.  
- **Smíšený batch (A25 / C10):** po 1× „ano“ apply jen vratná id; nevratná id čekají na 2. otázku.  
- Soft A17 Free: žádné tiché trash/archive/send. (F0 R4, A17; Q9; Q11; **C1**)

R5 — Push: primár **nativní OS notifikace** Mac+iPhone zůstává v docs; gate B18 může **FAIL** a F3 je přesto **DONE s výhradou**; provozní fallback = Slack DM a/nebo chat. Nesmí se přepsat primár na Slack. (F0 R5, A11; Q1)

R6 — Cílová INBOX budoucnost (F0 R11): SSOT jen `daily` + `sembly`. **F3–F4 provozní default L1 triáže** = dump `01-INBOX/slack` (+ legacy `01-INBOX/email`); live Slack tool **opt-in**, ne default fronta. (F0 R11; Q4)

R7 — Slack signály (live tool + poll): DM/GDM, @zmínky, vlákna kam uživatel psal, `:eyes:` / `:gear:`. Ne Saved/To-dos/Remind me / jméno bez tagu. (F0 R12)

R8 — `slack_poll` dump do gitu **běží paralelně** do F4; F3 nepřepíná stop dump. Přidat `:eyes:` do poll discover. (F0 F3 závislosti)

R9 — Sembly: n8n thin webhook → Brain `ingest_sembly` **deterministicky** vyplní MD šablonu (`ŠABLONY/sembly-md-template.md`); **ingest ≠ LLM**. LLM DEEP = `agenda-zapis-ze-schuzky` / triáž. Ostatní n8n INBOX writers off. (F0 R13; Q7)

R10 — Gmail hybrid F3 MVP (**F0 P5 / A30 / C2 / C5 / C12**):  
- Scope: Inbox+Sent, oba mailboxy; ne All Mail/Spam.  
- L1: Brain prefer + P5 — **Inbox metadata ≤100 / mailbox / session**, řazení **Date ASC**, hinty nevyřazují; **Sent = jen thread-join** ke kandidátům z Inbox (bez samostatného Sent listu / bez druhého stropu 100); bodies ≤40 / session napříč mailboxy.  
- **Fail-path (F0 R27):** Brain L1 down / error → client connector list (Inbox+Sent); P5 pak jen skill convention (Riziko 16).  
- L2 trash/archive/needs_reply = **jen Inbox** (Sent není akční fronta).  
- **Apply primár = client** po UX z R4; Brain propose + audit **povinně před apply**. (F0 R12b, R27, P5, A30; Q8 **superseded C1**; Q12)

R11 — Proaktivita F3 MVP (**A19 / C3 / C14**):  
- Cron `proactivity_dispatch` = **3** okna: (1) ráno ~08:00 (2) due/Waiting tick = crontab **`0 9-17 * * 1-5`** (1×/h, Po–Pá, TZ Europe/Prague) (3) evening ~18:00.  
- Cron `meeting_prep_dispatch` = **oddělený** trigger „před schůzkou“ — cadence crontab **`*/15`** v okně dne; look-ahead default **70 min** před startem (**C13**, **A28**); jen prep pipeline, **ne** čtvrtý triage ping.  
- **Bez anomaly**. NE immediate.  
- Doručení: OS (B18 PASS) → fallback Slack/chat.  
- Proactivity smí jen **L1/L2 náhled** + „jdi do triáže“ — **nezakládá** propose/apply-batch. Propose až v živé session.  
- **Dry-run (C16):** `proactivity_dispatch` i `meeting_prep_dispatch` mají `--dry-run` / no-send — žádný OS push, Slack send ani Grok webhook. (Q3; Q11; Q15–Q18; A19; A22; A28)

R12 — Po QA: odškrtnout **SB15-4**; TESTER přeskočen. DONE dovoleno s výhradou při **B18 FAIL** a/nebo **B21/T13 FAIL** a/nebo **Claude/Grok client-apply neověřen** (**A24 / C9** — gate = Cursor). (Q1; Q14)

R13 — Zachovat F2 tip/PUSH/PAUSED/`error_reason` (A55–A64); F3 tools přes `brain_vault(mode=…)`.

R14 — **Jednotná meeting prep:** jeden obsah (rozsah skill/`prepare_meeting`); primární doručení **Grok** přes oddělený `GROK_BOT_MEETING_PREP_WEBHOOK_*`; supersede paralelní generátory. Cursor skill ad-hoc čte stejný SSOT. Cron: existující brief pro `event_id`+den → **skip**. Ad-hoc: `force=true` smí přepsat + volitelný re-send (**A21 / C8**). Okno před eventem default **70 min** (**C13**); cadence **`*/15 8-23`** (**A28**, **A37**). Meeting-Preps >14 dní mazat GC s `--dry-run` + CAS (**C6**). Dispatch cron: `--dry-run` = **0** Meeting-Preps write ∧ **0** Grok ∧ **0** deliver (**B37**, **A34**, **C16**). (Q10; Q15–Q18)

R15 — Slack send po approve (client apply, 2× confirm): **DM, GDM i kanál**. (Q6; C1)

R16 — Batch store (propose audit) = **in-memory / process-local** Brain; restart ztratí batch = OK. Ne vault, ne Redis. (**A23 / C7**: Coolify Brain `replicas=1`.) Po client apply **není** povinný `mark_applied` na Brain (**A27**). (Q2)

R17 — **Apply auth / path (**C1** + Q12):**  
- Brain `mailbox/propose` + `external/propose`: oauth **nebo** service OK; ukládá batch do RAM pro audit — **povinný krok před client apply** (R4/C11).  
- Brain `mailbox/apply` + `external/apply`: **service → 403** `human_oauth_required` (Q12=a zůstává).  
- **OAuth Brain apply** = **post-F3** (F3: při oauth cookie → **501** `oauth_brain_apply_post_f3`).  
- **Primár F3 mutate** = **client apply** po UX R4.  
- Propose, ingest, capture_daily, get_triage/slack_live, prepare_meeting, cron→Brain smí service.  
- Post-F3 dluh: OAuth Brain apply + signed approve token (Q12=c).  

R18 — Coolify Brain má **Universe read credentials** (+ **Drive** SA|OAuth dle **A29**) pro plný `prepare_meeting`. Klienty = **nové** moduly (ne falešné reuse — v repu neexistují). Bez Drive/Universe → degradace B31. (Q13; **C6**; **A29**)

R19 — Skills (`agenda-triage`, `agenda-reply`, případně capture):  
- **Brain propose povinné** před jakýmkoli external/mailbox mutate (ne „optional audit“).  
- **1× vs 2× confirm** + smíšený batch (A25).  
- **Client apply path** (ne Brain apply jako default).  
- **Partial client apply (A20 / C15):** report `succeeded[]` + `failed[{id,error_reason}]`; žádné tiché all-OK.  
- **Fail-path L1:** Brain down → client list + soft P5.  
- **A24:** Cursor = DONE gate pro mutate; Claude/Grok propose+UX povinné, mutate best-effort. (**C1**, **C9–C12**, **C15**)

R20 — Client-apply DONE gate (**A24 / C9**): T8/B14* PASS = **Cursor** (Gmail MCP + Slack). Claude/Grok connector mutate neověřený / best-effort / „proveď v Cursoru“ **neblokuje** F3 DONE ani SB15-4.

R21 — Cron dry-run profil SECOND_BRAIN (**C16**): `proactivity_dispatch` a `meeting_prep_dispatch` podporují `--dry-run` (no-send: žádný push/send/Grok). `meeting_preps_gc` už `--dry-run` má (C6). QA/gate T18 spouští dry-run před ostrým během kde dává smysl.

**Mimo rozsah:** F4 (stop dump jako default fronta, Drive jen R9, Claude artifact); F5 boti; bulk FM; Mac local vault edit/push; F2 tip-ahead/MCP auth znovu; n8n Gmail/mobile/Slack INBOX on; All Mail/Spam; anomaly trigger; LLM v ingest; **OAuth Brain apply** a **signed approve token** (post-F3); povinný Claude/Grok client-apply smoke (A24); povinný `mark_applied` po client apply (A27).

**Netýká se:** Alembic, RBAC Universe FE, subnav/hub dlaždice, `qa_gate.mjs`, Playwright-T6 / `rbu-tester`, Celery, Universe SQL P.

**Odchylky od F0 / dřívějšího F3 draftu:**  
- R18/B12 „5 triggerů vč. anomálie“ → F3 **3 proactivity + 1 meeting_prep** (Q3; A19).  
- R11 živá triáž jako cíl → F3 default dump do F4 (Q4).  
- A11 OS gate — B18 FAIL neblokuje DONE (Q1).  
- Q5=b → Q11=c: propose jen session.  
- Q8 „Brain apply primár“ → **C1: client apply primár**; Brain = propose + audit (povinně).  
- Client-apply multi-klient → A24: DONE gate = Cursor.  
- A20 partial report → **client path** (B33), ne Brain `*/apply` (C15).

---

## Předpoklady

A1 — F2 live: Brain `https://brain.cyprovi.cz`, MCP write Cursor+Claude+Grok, shared WC `/data/vault`, `GIT_VAULT_PUSH=1`.

A2 — Soft A17 Free + **C1 UX**: v session **propose (povinně)** → chat (1× vratné / 2× nevratné; smíšený batch A25) → **client apply**. Brain apply není provozní cesta F3.

A3 — **OS push (B18):** research Claude/Grok→OS notif. PASS = Mac∥iPhone. FAIL → Slack/chat fallback; docs primár OS; DONE s výhradou OK (Q1). F2 reminder webhook ≠ důkaz OS push.

A4 — Gmail: Coolify Brain 2× refresh-token (Workspace + osobní) pro **L1 read** (Inbox+Sent). Mutate scopes na Brain **nejsou nutné pro F3 DONE** (client apply); IdP MCP (`openid email profile`, `auth_google.py` L54) Gmail nemá. Pokud L1 běží na Brain, read scope offline consent zvlášť.

A5 — Sembly: n8n thin → Brain template fill; žádný LLM v ingest (Q7).

A6 — Slack: `SLACK_USER_TOKEN` na hub (poll) i tam, kde client/script send běží; bot token pro reminder/push fallback. Live tool na Brain čte user token.

A7 — Gmail objem: odhad desítky–nízké stovky Inbox/mailbox; P5 **Inbox 100 meta/mailbox**, Sent thread-join, **40 bodies** celkem. Ověřit `users.labels.get` INBOX counts před tvrzením P.

A8 — Slack poll budget beze změny (`slack_poll_core.py` L17–18: `MAX_NEW_THREADS=8`, `MAX_REFETCH_PER_TICK=40`).

A9 — Default triage L1 do F4: dump slack (+ email legacy). Live Slack opt-in. Gmail L1 = Brain tool; fail-path = client list (A26). (Q4; F0 R27)

A10 — **Proaktivita cron:** 3 okna; due = `0 9-17 * * 1-5`; L1/L2 náhled bez `batch_id` / propose / apply. Meeting prep = jiný cron, okno **70 min**, cadence **`*/15`**. (Q11; A19; A28; C13; C14)

A11 — `capture_daily` → `01-INBOX/daily/` Brain mutate (service OK).

A12 — Batch in-memory TTL 2 h; **Coolify Brain replicas=1** (A23); restart → znovu propose. (Q2; C7)

A13 — **Apply:** client primary; Grok (Bearer service) Brain apply **403**; OAuth Brain apply post-F3 (501). Mutate přes connector po UX; DONE gate Cursor (A24). (C1; Q12; C9)

A14 — Meeting prep SSOT: `prepare_meeting` → `00-System/Meeting-Preps/<event_id>-<YYYY-MM-DD>.md` + Grok přes **`GROK_BOT_MEETING_PREP_WEBHOOK_URL` + `_KEY`**. Cron: events se startem v následujících **70 min** (konfigurovatelné, default 70); crontab cadence **`*/15`**; skip if exists; ad-hoc `force=true` OK. Retention GC >14 dní. (Q15–Q18; A21; A28; C13)

A15 — Filtry prep = `agenda-meeting-prep` skill. Kalendář: `00-System/calendar-events.json` + API dle potřeby.

A16 — SB15-4 `[x]` po QA i při B18 a/nebo B21 FAIL a/nebo Claude/Grok apply neověřen (A24) (Q1, Q14, C9).

A17 — Brain env: Universe API read + Drive SA|OAuth (A29) pro přílohy prep; bez toho degradace sekcí + explicit log/flag (ne tiché prázdno). (Q13; A29)

A18 — **Post-F3 dluh:** OAuth Brain apply + signed approve token (Q12=c) — neblokuje F3 DONE.

A19 — Trigger „před schůzkou“ = jen `meeting_prep_dispatch`; `proactivity_dispatch` = ráno + due/Waiting + evening. (g=3)

A20 — Partial apply na **client path** (primár F3): best-effort per id; klient/skill vrátí `succeeded[]` + `failed[{id,error_reason}]`; žádné tiché all-OK. Brain `*/apply` F3 není provozní cesta (403/501) — partial report se netestuje přes Brain apply. (g=3; C4; **C15**)

A21 — Cron prep: skip pokud existuje; ad-hoc `force=true` přepíše. (g=3; C8)

A22 — Crontab TZ Europe/Prague: ráno ~08:00, evening ~18:00; due/Waiting = **`0 9-17 * * 1-5`**. (g=3; C14)

A23 — Coolify Brain `replicas=1`. (g=3; C7)

A24 — Client-apply gate pro DONE: T8/B14* = **Cursor** (Gmail MCP + Slack). Claude/Grok: propose + UX 1×/2× povinné; mutate best-effort / „proveď v Cursoru“ — **neblokuje** F3 DONE. (g=4; C9)

A25 — Smíšený batch: po jednom „ano“ apply jen vratné id; nevratné (send / permanent delete) jen po druhé otázce na ta id. (g=4; C10)

A26 — Fail-path Brain L1 → client connector list (Inbox+Sent, oba mailboxy); P5 soft skill convention; skills to pojmenují; frekvenci fail-path logovat/měřit kde jde. (F0 R27/Riziko 16; C12)

A27 — Propose audit = **RAM** (batch_store); po úspěšném **client apply** **není** povinný `mark_applied` / sync zpět do Brain. Restart Brain ztratí batch i po apply — OK. (g=5; **C17**)

A28 — `meeting_prep_dispatch` cadence crontab **`*/15`** (Europe/Prague, v okně dne dle implementace); look-ahead **`MEETING_PREP_WINDOW_MINUTES=70`**. (g=5; **C17**; sladěno s C13)

A29 — Drive pro prep: **SA nebo OAuth** (env na Coolify Brain); chybí-li obojí → **B31** degradace + explicit flag, ne crash / tiché prázdno. (g=5; **C17**)

A34 — `meeting_prep_dispatch --dry-run` = **0** volání Brain `prepare_meeting` se zápisem do Meeting-Preps, **0** Grok/deliver; jen spočítat kandidáty + log „would prepare/send“. (g=6; critic MINOR NEW-1/2 — ID A34 kvůli kolizi s F0 A30)

A35 — `proactivity_dispatch --dry-run` = smí **číst** dump/context; **0** OS/Slack/chat; **0** propose/batch. (g=6)

A36 — T7d helper: SSOT JSON `{succeeded[], failed[{id,error_reason}]}`; cesta souboru (Brain vs `scripts/lib`) = impl detail. (g=6)

A37 — crontab `meeting_prep` = **`*/15 8-23 * * *`** Europe/Prague (ne 24/7). (g=6; critic MINOR NEW-3)

---

## Současný stav (ověřeno v kódu)

| Fakt | Důkaz |
|---|---|
| REST `/v1/f3/{name}` → 501 | `vps/second-brain-brain/app/main.py` L212–218 |
| MCP `f3_stub` | `vps/second-brain-brain/app/mcp_app.py` L117–123 |
| `test_f3_stub_501` | `vps/second-brain-brain/tests/test_auth_rest.py` L52–58 |
| Auth: OAuth cookie → `oauth:{email}` str; Bearer → `ServicePrincipal` | `auth_deps.py` L17–37, L52; `auth_service.py` L10–18 |
| IdP scope jen `openid email profile` | `auth_google.py` L54 |
| slack_poll discover bez `:eyes:` (jen gear) | `cron/slack_poll.py` L71–79 |
| slack dump `01-INBOX/slack`; budget MAX_NEW=8 / REFETCH=40 | `slack_poll_core.py` L13–18; crontab `*/2 8-23` L66 |
| Reminder Grok webhook (`GROK_BOT_REMINDER_*`) | `lib/reminder_chat_delivery.py` `send_grok_chat` L45–67 |
| n8n Sembly → Drive, workflow `active: false` | `ŠABLONY/n8n/sembly-to-cowork.json` **L93** (`"active": false`) |
| Sembly MD šablona | `ŠABLONY/sembly-md-template.md` |
| Mutate tools přes `brain_vault` | `vault_deps.py`; `tools/create_task.py` L134 |
| **Žádný** `universe_client.py` / `drive_client.py` v SECOND_BRAIN | glob 0 hitů — F3 musí založit nové |
| GitVault CAS = `expect_oid` na write; `delete()` bez CAS parametru | `lib/git_io.py` L386–397, L470+, L579–592 |
| DriveVault CAS = `expect_mtime` na write; `delete` existuje | `lib/drive_io.py` L546+, L751 |
| Hub cron vzor `--dry-run` | např. `cron/archive_done_tasks.py` L44, L79–91 |
| Meeting-Preps složka / prepare_meeting v Brain | neexistuje (skill jen lokální MCP) |
| `config.example.env` bez Gmail/Universe/Drive/meeting-prep/replicas | `vps/second-brain-brain/config.example.env` L1–18 |
| Runbook Coolify Brain bez replicas | `docs/brain-api-runbook.md` L83–92 |
| F0 P5 Gmail + L1 fail-path | F0 L403 P5; F0 R27 / B7b fail-path client list |
| Quality checklists A+B | RB Universe `docs/agent_playbooks/quality-checklists.md` (SB adaptace) |

---

## Návrh

### 1. Brain — tools (R3, R6–R20)

| Soubor | Změna | R# |
|---|---|---|
| `app/main.py` | Smazat `/v1/f3/{name}`. REST: ingest_sembly, capture_daily, triage/candidates, slack/live, mailbox/propose, mailbox/apply, external/propose, external/apply, prepare_meeting (`force`), GET meeting_prep, push/test | R3+ |
| `app/mcp_app.py` | Stejné tools; bez `f3_stub` | R3 |
| `app/auth_apply.py` (nový) | Apply routes: `ServicePrincipal` → 403 `human_oauth_required`; `oauth:…` → 501 `oauth_brain_apply_post_f3` (C1); jiné → 401/403 | R17 |
| `app/tools/ingest_sembly.py` | Template → `01-INBOX/sembly/`; idempotence; no LLM; service OK | R9 |
| `app/tools/capture_daily.py` | daily mutate; service OK | R6 |
| `app/tools/get_triage_candidates.py` | Gmail L1 dle P5; při Gmail/Brain chybě vrátit `error_reason` + hint fail-path (ne tiché `[]` success); `include_live_slack` default false; L2 akční flag jen Inbox | R6, R10, C12 |
| `app/tools/slack_live.py` | Live search; 0 dump | R7 |
| `app/batch_store.py` | Process-local + TTL 2 h; propose payload značí `reversible` / `irreversible` per id (pro A25); **bez** povinného mark_applied po client apply (A27) | R16, A25, A27 |
| `app/tools/mailbox_propose_apply.py` | propose: oauth\|service, 0 mutate, flags vratné/nevratné; apply: gate `auth_apply` (403/501 — ne provozní partial report) | R4, R10, R17 |
| `app/tools/external_propose_apply.py` | totéž; cíle DM/GDM/channel | R15, R17 |
| `app/tools/prepare_meeting.py` | Plný rozsah přes **nové** klienty; zápis Meeting-Preps; Grok deliver; skip if exists unless `force=true`; Drive SA\|OAuth (A29) | R14, R18, A29 |
| `app/gmail_client.py` (**nový**) | Gmail API read L1, 2 účty; P5 enforce + audit | R10 |
| `app/universe_client.py` (**nový**, ne reuse) | Read-only prod Universe HTTP z env | R18, C6 |
| `app/drive_client.py` (**nový**, ne reuse) | Read příloh pozvánky; SA **nebo** OAuth z env (A29) | R18, C6, A29 |
| `app/push_dispatch.py` | OS → Slack/chat | R5 |
| `app/sembly_template.py` | Port n8n fill | R9 |
| `app/partial_apply_report.py` (nový, volitelně sdílený helper) | Normalizace tvaru `{succeeded: [...], failed: [{id, error_reason}]}` pro client/skill path (C15); **ne** volán z Brain apply gate | A20, C15 |
| `config.example.env` + runbook | Gmail×2 read, Slack, OS push, `GROK_BOT_MEETING_PREP_WEBHOOK_*`, `MEETING_PREP_WINDOW_MINUTES=70`, Universe/Drive SA\|OAuth, **replicas=1** | A4, A14, A17, A28, A29, C7, C13 |
| Tests | Stub pryč; apply 403/501; P5; L2 Inbox; propose flags; **unit helper partial report formát** (T7d); bez vazby B33→Brain apply | R3, R17, C2–C5, C10, C15 |

### 2. Hub cron (R8, R11, R14, R21)

| Soubor | Změna | R# |
|---|---|---|
| `cron/slack_poll.py` | + `hasmy::eyes:`; dump dál | R7, R8 |
| `cron/proactivity_dispatch.py` | **3** triggery; náhled + „jdi do triáže“; **žádný** propose/apply/batch_id; **`--dry-run`** = žádný OS push / Slack send / chat deliver | R11, R21, A10, C3, C16 |
| `cron/meeting_prep_dispatch.py` | Events se startem v **`MEETING_PREP_WINDOW_MINUTES` (default 70)**; Brain prepare; Grok webhook; skip if exists; **`--dry-run`** = **0** Meeting-Preps write ∧ **0** Grok ∧ **0** deliver (B37/A34); smí logovat „would prepare/send“ | R14, R21, C13, C16 |
| `cron/meeting_preps_gc.py` | >14 dní; `--dry-run` (už vzor); CAS (`expect_oid` — rozšířit `GitVault.delete` dle potřeby) | R14, C6 |
| `lib/push_dispatch.py` | OS→fallback; respektovat dry-run flag z calleru | R5, C16 |
| `deploy/crontab` | ráno ~08:00; **due `0 9-17 * * 1-5`**; evening ~18:00; **meeting_prep `*/15 8-23 * * *`** (A37; look-ahead 70 min v kódu); GC; bez anomaly; TZ Prague | R11, A22, A28, A37, C14 |
| `fetch_calendar.py` | Beze změny kontraktu | R14 |

### 3. n8n (R9)

| Soubor | Změna | R# |
|---|---|---|
| `sembly-to-brain.json` + README | Webhook → Brain ingest + Bearer service | R9 |
| `deploy_n8n_cowork_workflows.py` | Jen Sembly→brain active | R9 |
| Live `hKL04ATDDRSt0FOG` | Cutover z Drive | R9 |

### 4. Skills (R4, R6, R10, R14, R17, R19, R20)

| Soubor | Změna | R# |
|---|---|---|
| `agenda-triage/SKILL.md` | Default L1 dump; Gmail Brain L1 (P5); **fail-path → client list**; live Slack opt-in; **Brain propose povinné před mutate**; 1×/2× + **smíšený batch A25**; **client apply** + **partial report B33** (`succeeded[]`/`failed[]`); A24 Cursor gate; Sembly→DEEP | R6, R9, R10, R19, R20, C9–C12, C15 |
| `agenda-capture` / `agenda-reply` | capture_daily; send = propose → 2× confirm → client apply + partial report | R4, R19, C11, C15 |
| `agenda-meeting-prep/SKILL.md` | Ad-hoc = Brain SSOT (`force`); scheduled = VPS+Grok; zákaz třetí verze | R14, C8 |
| Runbook checklist T13 | Vypnout paralelní prep schedules | R14, Q14 |
| `install_agenda_skills.sh` | Po editaci | R12 |

### 5. Docs / vault / Coolify

| Soubor | Změna | R# |
|---|---|---|
| `docs/brain-api-runbook.md` | F3 tools; client apply primár; propose povinné; apply 403/501; replicas=1; meeting prep 70 min + `*/15`; due crontab; A24 Cursor gate; fail-path L1; partial client report; cron dry-run; A27–A29; B18/B21 výhrady; post-F3 dluh | R2+, C1, C7, C9, C12–C18 |
| Coolify UI `second-brain-brain` | **replicas=1** (F3-b); T18 | C7 |
| Tento plán | `docs/plans/2026-10-10-sb-operacni-model-f3.md` | R1 |
| Vault **SB15-4** | `[x]` po QA i s B18/B21/A24 výhradou | R12, C9 |

**DB/migrace / RBAC FE / Celery:** netýká se.

---

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | `f3_stub` / `/v1/f3/*` | Neexistuje | R3 | T1 |
| B2 | `ingest_sembly` (service OK) | MD v sembly/; 1 commit; no LLM | R9 | T2, T3 |
| B3 | Ingest 2× | 1 soubor; `deduped` | R9 | T3 |
| B4 | `capture_daily` | daily; tip gate | R6, R13 | T2 |
| B5 | Default triage | L1 = dump slack (+ email) + daily/sembly; ne auto live | R6 | T4, T8 |
| B6 | Live slack opt-in | Kandidáti; 0 dump | R7 | T5 |
| B7 | Saved / jméno bez @ | Není v live L1 | R7 | T5 |
| B8 | Gmail L1 | Inbox ≤100/mailbox, Date ASC; Sent jen thread-join; hinty nevyřazují | R10, C2 | T6 |
| B9 | Bodies | ≤40/session celkem | R10 | T6 |
| B10 | propose (oauth\|service) | batch_id RAM; per-id reversible flags; 0 mutate | R4, R16, A25 | T7 |
| B11 | Brain apply + service | **403** `human_oauth_required`; 0 mutate | R17 | T7b |
| B12 | apply unknown/expired batch | 404/409; 0 mutate | R16 | T7 |
| B13 | Brain apply + **oauth** cookie | **501** `oauth_brain_apply_post_f3`; 0 mutate | R17, C1 | T7c |
| B14 | **Cursor** client apply po UX (1× vratné) + po **propose** | Mutate OK v Cursoru; bez prior propose = FAIL skill path | R4, R10, R20, C9, C11 | T8 |
| B14b | Client apply nevratné bez 2. confirm | Neprovede send/permanent delete | R4, C1 | T8 |
| B14c | Client apply nevratné po 2. confirm | Send/delete OK (Cursor gate) | R4, R15, R20, C1 | T8 |
| B14d | Smíšený batch: 1× „ano“ | Apply jen vratná id; nevratná čekají na 2. otázku; žádný send v 1. kroku | A25, C10 | T8, T19 |
| B14e | Claude/Grok client apply | Propose + UX povinné; mutate best-effort / odkaz na Cursor; **FAIL neblokuje DONE** | A24, C9 | T8, T16 |
| B15 | external propose channel targets | DM/GDM/channel v payload | R15 | T9 |
| B16 | Proactivity cron | 3 okna (due = hourly WD); náhled + „jdi do triáže“; žádný batch_id/propose/apply; ne meeting-prep ping | R11, C3, C14 | T10 |
| B17 | Anomaly cron | Neexistuje | R11 | T10 |
| B18 | OS push smoke | PASS nebo FAIL+výhrada+DONE | R5 | T11 |
| B19 | Docs po B18 FAIL | Primár OS | R5 | T11 |
| B20 | prepare_meeting cron | Look-ahead **70 min**; cadence **`*/15`**; brief SSOT; Grok webhook; skip if exists | R14, A28, C13 | T12 |
| B20b | prepare_meeting `force=true` ad-hoc | Přepíše + volitelný re-send | R14, C8 | T12 |
| B21 | Paralelní prep vypnutí | PASS ideál; FAIL → DONE s výhradou | R14, Q14 | T13 |
| B22 | Ad-hoc meeting-prep skill | Čte/volá Brain SSOT | R14 | T13 |
| B23 | slack_poll | Dump + eyes | R8 | T14 |
| B24 | n8n non-Sembly INBOX | Off | R9 | T15 |
| B25 | Tip/PAUSED/PUSH mutate | 503 ∈ A58 | R13 | T1, T2 |
| B26 | Prázdná data | `[]` / prázdný náhled, ne 500 | checklist A1 | T5, T6 |
| B27 | Externí 5xx při L1 | `error_reason` (ne tiché success); skill smí přejít na client list (B35) | A9, C12 | T6, T8 |
| B28 | SB15-4 | [x] i při B18 a/nebo B21 FAIL a/nebo B14e (Claude/Grok apply neověřen); **vyžaduje B14*/T8 Cursor PASS** | R12, A24, C9 | T16 |
| B29 | Soft A17 + C1 + propose-before-apply | Skills: propose **povinné** před client apply; 1×/2×; smíšený batch; žádné tiché mutate | R4, R19, C11 | T8, T19 |
| B30 | Meeting-Preps >14d | GC; `--dry-run`; CAS konflikt → skip+log | R14, C6 | T12b |
| B31 | prepare_meeting bez Universe/Drive env (SA ani OAuth) | Degradace + explicit flag; ne crash (A29) | R18, A29 | T12 |
| B32 | L2 na Sent-only id | Odmítnuto; 0 mutate | R10, C5 | T6b |
| B33 | **Client/skill** partial apply report | Po částečném client apply: `succeeded[]` + `failed[{id,error_reason}]`; preview/skill **nesmí** tvrdit all-OK když `failed` neprázdné. **Netýká se** Brain `*/apply` (F3 = 403/501). | A20, C4, **C15** | **T8, T19** (+ volitelně T7d formát) |
| B34 | Coolify Brain replicas | =1 | R16, C7 | T18 |
| B35 | Brain Gmail L1 down / hard error | Skill: client connector list (Inbox+Sent); soft P5; označeno fail-path v preview | R10, A26, C12 | T8, T19 |
| B36 | `proactivity_dispatch --dry-run` | Spočítá/náhledne; **0** OS push, **0** Slack send, **0** chat deliver | R11, R21, **C16** | T10, T18 |
| B37 | `meeting_prep_dispatch --dry-run` | Spočítá kandidáty / log „would…“; **0** volání Brain `prepare_meeting` se zápisem do Meeting-Preps; **0** Grok webhook; **0** jiný deliver (**A34**) | R14, R21, **C16** | T12, T18 |
| B38 | Po client apply | Brain batch smí zůstat v RAM bez `mark_applied`; další session = nový propose (A27) | R16, A27 | T7, T8 |

**Checklist A (RB Universe playbook → SB):**  
1→B26; 2→B12/B11/B13/B27/B33/B35; 3 TZ→B16/B20/A22/A28/C13–C14; 4 měny **netýká se**; 5 auth→B11/B13; 6 tip→B25; 7 trash/GC CAS→B30; 8→B3/B12/B20/B20b; 9→B27/B33/B35; 10 dump+live→B5/B23; 11 Universe FE **netýká se**; dry-run cron→B36/B37/B30.

---

## Výkonový rozpočet (P)

Objemy: Gmail A7 (ověřit label counts); Slack A8; Sembly jednotky/den; Meeting-Preps 1/event/den; batch propose ≤100 RAM.

| Tělo | 1 Objem | 2 SQL | 3 Load | 4 Externí | 5 Page | 6 Payload | 7 Cache | 8 Násobení | 9 FE | 10 Worker | 11 Cíl |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 Gmail L1 | Inbox ≤100/mailbox; Sent = join | n/a | meta Inbox (+ join Sent) | Gmail×2 | cursor | ≤256 KB | none | 1 session | n/a | Brain 1 replica | cold ≤3 s/mailbox; warm ≤1 s |
| P2 bodies | ≤40 celkem | n/a | bodies | Gmail get | — | ≤1 MB | — | — | n/a | — | ≤15 s |
| P3 slack live | ≤ poll budget | n/a | — | Slack | — | ≤128 KB | — | 1 | n/a | — | ≤5 s |
| P4 ingest | 1 md | n/a | template | — | — | transcript | — | 1 commit | n/a | — | ≤5 s+push |
| P5 capture_daily | 1 md | n/a | — | — | — | <100 KB | — | 1 commit | n/a | — | ≤5 s+push |
| P6 propose | ≤100 ids RAM | n/a | RAM | 0 mutate | — | ≤128 KB | TTL 2 h | 1 | n/a | **replicas=1** | propose ≤1 s |
| P6b client apply | N akcí | n/a | — | Gmail/Slack u klienta | — | report succeeded/failed | — | 1 session | n/a | client | ≤2 s+0.3 s×N (orientační) |
| P7 prepare_meeting | events v 70 min okně; tick `*/15` | n/a | vault+cal+Universe+Drive | multi | — | brief limit | vault SSOT; skip if exists | ≤1 gen/event/day | n/a | cron | cold ≤20 s; deliver ≤3 s |
| P8 proactivity | light+dump counts | n/a | — | OS/Slack/chat (ne při dry-run) | — | náhled bez batch | context 15 min | 1/okno; due ≤9×/WD | n/a | cron | tick <30 s |
| P9 slack_poll | +eyes | n/a | dump | Slack | MAX_* | — | state | cron */2 | n/a | cron | stávající |
| P10 SQL/FE | netýká se | — | — | — | — | — | — | — | — | — | — |

**Ověření objemu (hlavní agent před T18):** `users.labels.get` INBOX messagesTotal/Unread pro oba mailboxy; zapsat do QA poznámky.

---

## Testy (T#)

| T# | Typ | Owner | Soubor | B# |
|---|---|---|---|---|
| T1 | pytest | gate | `vps/second-brain-brain/tests/test_f3_routes.py` | B1, B25 |
| T2 | pytest | gate | `tests/test_ingest_capture.py` | B2, B4, B25 |
| T3 | pytest | gate | `tests/test_ingest_no_llm_idempotent.py` | B2, B3 |
| T4 | pytest/skill | gate | default L1 sources | B5 |
| T5 | pytest | gate | `tests/test_slack_live.py` | B6, B7, B26 |
| T6 | pytest | gate | `tests/test_gmail_l1_p5.py` | B8, B9, B26, B27 |
| T6b | pytest | gate | `tests/test_gmail_l2_inbox_only.py` | B32 |
| T7 | pytest | gate | `tests/test_batch_memory.py` | B10, B12, B38 |
| T7b | pytest | gate | `tests/test_apply_service_403.py` | B11 |
| T7c | pytest | gate | `tests/test_apply_oauth_501_post_f3.py` | B13 |
| T7d | pytest | gate | `tests/test_partial_apply_report_format.py` — **unit helper** společného tvaru `succeeded[]`/`failed[]` (sdílený formát pro skills/client). **Neváže** B33 na Brain `*/apply` 403/501. | formát pro B33 (ne B11/B13) |
| T8 | ruční | gate | **Cursor:** propose→1×/2×→client apply (B14–B14d); **partial client apply → B33 report** (alespoň 1 succeeded + 1 failed, ne all-OK); fail-path L1 mock/down→client list (B35); Claude/Grok jen poznámka B14e | B5, B14, B14b, B14c, B14d, B14e, B29, **B33**, B35, B38 |
| T9 | pytest | gate | `tests/test_external_slack_targets.py` | B15 |
| T10 | pytest + crontab | gate | `tests/test_proactivity_three_triggers.py` — 3 slots; due line `0 9-17 * * 1-5`; meeting_prep odděleně; no propose; **`--dry-run` → 0 push/send (B36)** | B16, B17, **B36** |
| T11 | ruční | gate | OS smoke | B18, B19 |
| T12 | pytest + smoke | gate | `tests/test_prepare_meeting.py` — window default 70; skip; force; degrade (A29); **`meeting_prep_dispatch --dry-run` → 0 Meeting-Preps write ∧ 0 Grok ∧ 0 deliver (B37)**; crontab `*/15 8-23` (A37) | B20, B20b, B31, **B37** |
| T12b | pytest | gate | `tests/test_meeting_preps_gc.py` | B30 |
| T13 | ruční | gate | vypnutí paralelních prep | B21, B22 — FAIL→výhrada OK |
| T14 | pytest | gate | `tests/test_slack_poll_eyes.py` | B23 |
| T15 | ruční/n8n | gate | active flags | B24 |
| T16 | ruční | gate | SB15-4: Cursor B14* PASS stačí; B14e/B18/B21 výhrady OK | B28 |
| T17 | lokální gate | gate | `python3 -m pytest vps/second-brain-hub/tests scripts/tests vps/second-brain-brain/tests -q` | regrese |
| T18 | QA deploy | gate | Coolify; replicas=1; ingest; prep→Grok; push; apply 403/501; **dry-run proactivity + meeting_prep před ostrým** (B36/B37) | B2, B11, B13, B18/B19, B20, B34, **B36, B37** |
| T19 | ruční/docs | gate | Skills: propose povinné; 1×/2×; A25 smíšený; fail-path L1; A24 Cursor gate; **partial client report B33** (succeeded/failed, ne tiché all-OK) | B14d, B29, **B33**, B35 |
| T20 | Playwright-T6 | — | — | **netýká se** (SECOND_BRAIN; TESTER přeskočen) |

---

## Pořadí implementace

F3-a — OS push research → B18 PASS/FAIL (FAIL neblokuje DONE).  
F3-b — Gmail read OAuth×2 + Universe/Drive (SA\|OAuth) env na Brain; **Coolify replicas=1**; config (`MEETING_PREP_WINDOW_MINUTES=70`).  
F3-c — `batch_store` (reversible flags, A27 bez mark_applied) + propose + apply gate (403/501); partial report **helper** (T7d); T7, T7b, T7c, T7d, T9.  
F3-d — ingest_sembly + capture_daily; smazat stub; T1–T3.  
F3-e — n8n Sembly→brain; T15.  
F3-f — Gmail L1 + P5 + L2 Inbox-only + L1 error_reason pro fail-path; T6, T6b.  
F3-g — Slack live + poll eyes; triage default dump; T4, T5, T14.  
F3-h — nové Universe/Drive klienty + prepare_meeting (70 min) + `meeting_prep_dispatch` (**`--dry-run`**, cadence `*/15`) + GC + Grok webhook; T12, T12b; T13.  
F3-i — proactivity 3× + crontab due `0 9-17 * * 1-5` + **`--dry-run`**; T10.  
F3-j — Skills: **propose povinné**, 1×/2×, A25, fail-path L1, A24 Cursor gate, client apply, **B33 partial report**; install; T19.  
F3-k — Runbook; T17; push main; Coolify; QA T18 (vč. dry-run B36/B37); **T8 Cursor B14* + B33**; SB15-4 T16 (B28); ledger DONE (+ výhrady B18/B21/B14e).

Závislosti: F3-d→F3-e; F3-b→F3-c/f/h; F3-a před B18; F3-j po F3-c; T8 Cursor před T16/B28.

---

## Rizika a zpětná kompatibilita

1. **B18 FAIL** — akceptováno (Q1).  
2. **B21/T13 FAIL** — akceptováno (Q14).  
3. **In-memory batch + replicas>1** — mitigace replicas=1 (B34).  
4. **Client-only apply / Claude·Grok pluginy** — A24: DONE = Cursor; Claude/Grok best-effort (C9; F0 Riziko 17).  
5. **Default dump do F4** — stale Slack (F0 R26).  
6. **prepare_meeting závislosti** — degradace B31 (A29 SA\|OAuth).  
7. **Gmail OAuth expiry** na Brain L1 read.  
8. **P5 soft na client L1 fail-path** (F0 Riziko 16; B35).  
9. **Sembly cutover** downtime.  
10. **Slack rate limit** live+poll.  
11. **F0 anomaly** odloženo.  
12. **Post-F3:** OAuth Brain apply + signed token.  
13. **GitVault.delete bez CAS dnes** — doplnit `expect_oid` pro B30/C6.  
14. **Smíšený batch** — agent musí splitnout apply; mitigace B14d + skills T19.  
15. **Partial client apply bez reportu** — tiché all-OK; mitigace B33 + T8/T19 (C15).  
16. **Cron bez dry-run** — náhodný push/Grok při QA; mitigace B36/B37 + T10/T12/T18 (C16).  
17. **A27** — po apply nelze z Brain zjistit „už applied“; OK (nový propose).

---

## Otevřené otázky pro uživatele

*(Q1–Q18 + C1 UX + A24–A29 + 70 min + `*/15` uzavřeny. Žádné blokující.)*

1. **NEBLOKUJÍCÍ — post-F3 priorita:** výchozí A18 (OAuth Brain apply až po F3 DONE). *Jinak:* urychlit OAuth Brain apply do F3 → zrušit B13=501, vrátit server mutate pod oauth (mění R17/C1 techniku).

---

## Q1–Q10 → jak zapracováno

| Q# | Rozhodnutí | Zapracováno |
|---|---|---|
| Q1 | DONE při B18 FAIL; OS primár docs | R5, R12, A3, A16, B18, B19, B28 |
| Q2 | In-memory batch | R16, A12, B10–B12, B34, A27 |
| Q3 | triggery bez anomaly | R11 (3+1), B17 |
| Q4 | Default dump; live opt-in | R6, A9, B5, B6 |
| Q5 | prakticky Q11 | R11, A10, B16 |
| Q6 | Slack DM/GDM/channel | R15, B15, B14c |
| Q7 | Deterministický ingest; no LLM | R9, B2, T3 |
| Q8 | ~~Brain apply primár~~ → **C1 client apply** | R4, R10, R17, B14*, B13 |
| Q9 | Chat approve | R4 (1×/2× + A25), B14*, B29 |
| Q10 | Jeden prep → Grok | R14, B20–B22 |

## Q11–Q18 → jak zapracováno

| Q# | Rozhodnutí | Zapracováno |
|---|---|---|
| Q11=(c) | Cron nepropose | R11, A10, B16, P8, F3-i, T10 |
| Q12=(a)+(c) later | Service 403; OAuth Brain apply post-F3 (501) | R17, A13, A18, B11, B13, T7b, T7c |
| Q13=(b) | Universe (+ Drive) na Brain | R18, A17, A29, nové clienty, B31, F3-b/h |
| Q14=(b) | DONE s výhradou T13/B21 | R12, A16, B21, B28 (+ A24) |
| Q15 | Oddělený meeting-prep webhook | A14, R14, B20 |
| Q16 | GC >14d | A14, B30, T12b, C6 |
| Q17 | Skip if exists | A14, B20; force=B20b |
| Q18 | Proactivity bez batch id | A10, B16, P8 |

## A19–A29 → jak zapracováno

| A# | Zapracováno |
|---|---|
| A19 | R11, B16, F3-i, T10 |
| A20 | **B33 client/skill**; T8 + T19 (+ T7d formát); ne Brain apply (**C15**) |
| A21 | B20 / B20b, T12 |
| A22 | crontab + C14 due schedule |
| A23 | A12, B34, F3-b, T18 |
| A24 | R12, R20, A16, B14/B14e, B28, T8, T16 (**C9**) |
| A25 | R4, B10 flags, **B14d**, T8, T19 (**C10**) |
| A26 | R10, **B35**, T8, T19 (**C12**) |
| A27 | R16, A27, **B38**, batch_store bez povinného mark_applied (**C17**) |
| A28 | R11/R14/A10/A14, crontab **`*/15`**, B20, P7, T12 (**C17**) |
| A29 | R18, A17, drive_client SA\|OAuth, B31, T12 (**C17**) |

---

## C# → jak vyřešeno

| C# | Závažnost | Stav | Jak vyřešeno |
|---|---|---|---|
| **C1** | BLOCKER | uzavřeno | Client apply + 1×/2×; Brain propose+audit; service 403; OAuth apply post-F3 (501). |
| **C2** | MAJOR | uzavřeno | P5 Inbox ≤100/mailbox; Sent thread-join; Date ASC; B8, P1, T6. |
| **C3** | MAJOR | uzavřeno | 3 proactivity + oddělený meeting_prep; B16, T10. |
| **C4** | MAJOR | uzavřeno | A20 partial report — provozní cesta = client (viz C15). |
| **C5** | MAJOR | uzavřeno | B32 + T6b L2 jen Inbox. |
| **C6** | MAJOR | uzavřeno | Nové Universe/Drive klienty; GC `--dry-run`+CAS; B30, T12b. |
| **C7** | MINOR | uzavřeno | replicas=1; B34, T18, F3-b. |
| **C8** | MINOR | uzavřeno | B20b `force=true` + T12. |
| **C9** | MAJOR | **uzavřeno** | A24 → R12, R20, A16, **B14/B14e**, **B28** (Cursor PASS povinný; Claude/Grok neblokuje), T8/T16. |
| **C10** | MAJOR | **uzavřeno** | A25 → **B14d** + propose flags v B10; T8 + T19. |
| **C11** | MAJOR | **uzavřeno** | Skills: propose **povinné** (ne optional); R4/R19; **B29 propose-before-apply**; B14 vyžaduje prior propose; F3-j/T19. |
| **C12** | MAJOR | **uzavřeno** | F0 fail-path → A26, **B35**, get_triage `error_reason`, skills; T8 + T19. |
| **C13** | MINOR | **uzavřeno** | Default meeting prep okno **70 min** (`MEETING_PREP_WINDOW_MINUTES`); R11/R14/A14/B20/P7/T12; accepted. |
| **C14** | MINOR | **uzavřeno** | Due tick default crontab **`0 9-17 * * 1-5`**; A10/A22/B16/T10/crontab. |
| **C15** | MAJOR | **vyřešeno** | B33 = **client/skill** kontrakt `succeeded[]`/`failed[]`; primární pokrytí **T8 + T19**; T7d = jen unit helper formátu (ne Brain `*/apply`). A20 přepsáno. |
| **C16** | MAJOR | **vyřešeno** | `proactivity_dispatch` + `meeting_prep_dispatch` → `--dry-run` / no-send; **B36/B37**; T10/T12/T18; GC dry-run beze změny (C6). R21. |
| **C17** | MINOR | **vyřešeno** | A27–A29 v Předpokladech + B38/B20 cadence `*/15`/B31 SA\|OAuth; tabulka A19–A29. |
| **C18** | MINOR | **vyřešeno** | Citace Sembly `active: false` → `ŠABLONY/n8n/sembly-to-cowork.json` **L93** (ne L53–55). |

---

## C# → vyřešeno (kolo 3)

| C# | Stav | Kde v plánu |
|---|---|---|
| **C15** | vyřešeno | A20; R19/R21; B33 (client, ne Brain apply); T7d = formát only; T8+T19 primár B33; skills F3-j |
| **C16** | vyřešeno | R11/R14/R21; hub cron `--dry-run`; **B36/B37**; T10/T12/T18; F3-h/i/k |
| **C17** | vyřešeno | A27–A29 v Předpokladech; B38; B20 `*/15`; B31+A29; tabulka A19–A29 |
| **C18** | vyřešeno | Současný stav: `sembly-to-cowork.json` **L93** |

C9–C14 zůstávají uzavřené (nerušeny).
