# Plán: F2 — Brain API + skilly plugin

> Architekt: **otevření #2 · k=2 · r=2** (critic 7db484d6: §2=brain_vault+A60; F2-b/e; T6/T16 A62; g=1–g=12)
> Stav: **SCHVÁLENO** (critic 482a6562 · k=2 r=2)  
> Pipeline ledger: [2026-10-10-sb-operacni-model-f2.pipeline.md](2026-10-10-sb-operacni-model-f2.pipeline.md)  
> Parent F0 (SCHVÁLENO): [2026-10-10-sb-operacni-model-f0.md](2026-10-10-sb-operacni-model-f0.md) · F1 DONE cutover  
> Vault: **SB15 — Nový operační model SB — multi-klient, Grok orchestrace, GitHub vault** (**SB15-3**)  
> Profil: **SECOND_BRAIN**. Base (origin/main před pipeline): `ca95c2f1388c1b7605c27ef9113219821e58a1f1`.

## Zadání a požadavky

R1 — Po F0 SCHVÁLENO (B1–B22) a F1 cutover DONE (2026-10-10, soft A17 Free) spustit F2 pipeline. (uživatel „rovnou /rbu-pipeline na F2“)

R2 — F2 scope z F0 tabulky F2: **Brain API**; klienti vault **MCP write**; **plugin SSOT**; **serverová policy**; **FM kontrakt ID/slug**. (F0 F2 + brief)

R3 — Brain API = **nová HTTPS služba na Coolify**; remote MCP + tenké REST pro n8n a Claude artifact. `BRAIN_PUBLIC_URL` = MCP + OAuth + REST (ne dashboard). (F0 A2)

R4 — Po F2: zapisovatelé vaultu = Brain API + VPS crony přes `GitVault`. Klienti vault **jen MCP**. Dev-bypass default **neexistuje**. Mac clone = fetch/pull; žádný FS write ze skills. (F0 A3, R23, R25)

R5 — Auth: Google OAuth = IdP; allowlist `lukas@redbuttonedu.cz` + `lukas.cypra@gmail.com`. **Lidští klienti (Cursor / Claude / Grok) = jen user-bound OAuth** — F0 fail-path „API key pro lidské klienty“ **zrušen**. Service token **jen** machine; audit `service:`. Gmail scopes až F3. (F0 A19 + grill g=1 Q5 + g=2 Q4)

R6 — **Stejná vault tool sada** pro Cursor, Claude/Cowork a **Grok Bot** (vč. `create_task`). Grok = součást F2 DONE: private plugin smoke + MCP write + reminder chat delivery. (grill g=1 Q3 + g=2 Q1)

R7 — F1–F2: n8n INBOX writers **vypnuté**; stale Slack INBOX OK do F3 (R26). (F0)

R8 — Pokryté F0 R#: **R2–R6, R10, R16, R19, R23** (+ R25, R8 model). Reminder **doručení v F2** = chat zpráva. Odchylka od F0 A11: F2 = chat delivery, ne VPS→OS push. (grill g=1 Q1 + g=2)

R9 — Soft A17 Free neblokuje F2.

R10 — Schvalování plánu uživatelem: **ne**.

R11 — Po QA: odškrtnout **SB15-3**.

R12 — Gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q` (+ Brain tests). TESTER: přeskočeno.

R13 — Reminder store Brain MCP: `schedule_reminder`, `cancel_reminder`, `list_reminders`. Skill `agenda-remind` → tyto tools. (grill g=1 Q1)

R14 — Připomínka = **zpráva do chatu** Grok → Claude → Slack. OS push = user setting. PASS = jeden chat kanál; primary = Grok chat. Cursor mimo řetězec; systémové To-do mimo F2. (grill g=2)

R15 — `get_context` **needs_rebuild** (sjednoceno s §3 / A32 / A37 / **C2**):  
missing full ∨ **bad `generated_at` ∨ stale = `generated_at` starší než přesně 15 minut** ∨ light/charters chybí ∨ `light.generated_at ≠ full.generated_at` (charters stejně) → sync rebuild **celým** shared builderem; busy → 503; nikdy tichý stale TOP. (grill g=1 Q2 + g=5 A37 + critic d28e95c7 C2)

R16 — Live smoke jen projekt **TEST**. (grill g=1 Q4)

R17 — `BRAIN_PUBLIC_URL`; OAuth callback = `{BRAIN_PUBLIC_URL.rstrip('/')}/oauth/callback`. (grill g=1 Q6)

R18 — Bez bulk FM v F2 DONE. (grill g=1 Q7)

R19 — Brain: 503 s `error_reason` z **`skip_reason`** (ne holé `skipped`). Retry 1–2× **jen** `vault_flock_busy` (**A62**); `vault_dirty_start` → okamžitě 503. Hub cron retry policy beze změny. (grill g=1 Q8 + NEW-1 + g=12)

R20 — Notify-first; at-least-once; double ping OK. (grill g=2 Q2)

R21 — All-fail: pending + `last_error` (+ dual-read `error`) + backoff; K=5; pak `Reminders-Failed/`; `attempt_count` default 0. (grill g=2 Q3)

R22 — F2-a hard exit: Grok chat send kontrakt v runbooku před F2-i; jinak eskalace; B25 neoslabovat. (grill + A28)

R23 — Brain každý MCP/REST request = **request-scoped** `brain_vault` → uvnitř `open_vault` (enter→ops→commit/push→exit). Zakázán process-global vault a přímý `open_vault` z tools/rest. Coolify Brain `GIT_VAULT_PUSH=1`; mutate bez úspěšného push → **503**.  
**Brain `strict_push=True` (C1):** po fail ff-only push nejdřív `git reset --hard @{upstream}` (stejně jako dnešní hub B6 v `lib/git_io.py` `_push_ff_only` L563–580), **pak** raise `GitPushError` (nebo ekvivalent) → HTTP 503. Po **úspěšném** resetu nesmí zůstat dirty WT.  
**Hub bez `strict_push`:** jen log+reset (beze změny F1) — žádný raise.  
**Po selhání resetu** viz A52 (ahead/divergent ≠ B42).

R24 — `allocate_task_id` = ceiling logika z `scripts/next_task_id.py` portovaná do `lib/` nad vault API, pod flock. (A40; preview = A43)

R25 — Plugin SSOT: `ŠABLONY/skills/` + plugin manifesty Cursor / Claude / Grok; F2-j; B11/T12.

R26 — Brain session: dirty na startu = skip→503 **bez** reset (g=7 Q1=b), `skip_reason=vault_dirty_start`. Flock busy = `skip_reason=vault_flock_busy` (B14). Discard jen po vlastní výjimce v non-skipped session. Atomické trio + guarded error-path `reset --hard HEAD`. **B42 = jen porcelain dirty** — ne tip ahead, **ne** flock. Holé `skipped` nestačí (**NEW-1** / A59).

R27 — Brain otevírá vault **jen** přes `open_vault(..., strict_push=, discard_dirty_on_error=)` ve `vault_factory.py` (kwargs do `GitVault` **před** `_PausedVault`).

R28 — Reminder schema/helpers v `lib/reminders.py`: `FAILED_DIR`, `attempt_count=0` při create, `is_due` respektuje `next_attempt_at`, dual-read `last_error||error`; status normalizace (A51). (R21)

R29 — Shared builder **bez session**: `lib/agent_context_build.py` neobsahuje `open_vault` / `begin_session` / `end_session`. Caller (thin cron i Brain) drží **jednu** session a volá `build_and_write_context_bundle(vault, …)`. (critic 6bf34c5e NEW-1)

R30 — **Brain tip-ahead gate (g=9 Q1=b + g=10 Q1=a):** při `strict_push`, pokud `HEAD ≠ @{upstream}`:
- **mutate** (vč. `create_task`, schedule/cancel reminder, a **`get_context` když `needs_rebuild=true`**) → HTTP **503**, `error_reason=vault_tip_ahead`, **žádný** commit, **žádný** rebuild, **žádný** tichý stale TOP;
- **read-only** vč. warm `get_context` (`needs_rebuild=false`) → **smí**.
Ops = manuální SSH uklidění tipu (runbook). Formát chyb → **A57**; úplný seznam reasons → **A55+A58**. Gate tip+PUSH **centrálně** v `vault_deps` (A60).

R31 — **F2-i PAUSED před HTTP (NEW-2):** před krokem 0b (Grok/Claude/Slack HTTP) zjistit `VAULT_WRITERS_PAUSED` → **0 sends**, **no attempt++**, žádný 0b. Stejně jako vault skipped (A34).

Mimo rozsah: F3 Slack live / Sembly / Gmail hybrid / R18 triggery; F4 dashboard; F5 boti; n8n INBOX on; hard ruleset; un-ignore `OBSIDIAN/`; bulk FM; VPS→OS push; systémové To-do; API key pro lidské MCP; sjednocení Mac `scripts/build_agent_context.py` s hub builderem (mimo F2 DONE); start-of-session `git reset`.

Netýká se: Alembic, RBAC Universe, frontend subnav, `qa_gate.mjs`, Playwright-T6, Celery.

---

## Předpoklady

A1 — F1 live: `VAULT_BACKEND=git`, WC `/data/vault`, deploy key, soft A17.

A2 — Brain Coolify `vps/second-brain-brain/`, **sdílený** volume s hubem. Oddělený clone zakázán.

A3 — Grok chat delivery = hard gate F2 DONE. F2-a bez Grok chat API → eskalace (R22), ne oslabení B25.

A4 — Claude chat chybí → skip+log → Slack.

A5 — Privacy preflight F2-a.

A6 — Objem ~ F0 A7; T9 `du -sh /data/vault`.

A7 — FM dual-read; nové bez `aliases`; bez bulk.

A8 — OAuth allowlist: oba e-maily.

A9 — `BRAIN_SERVICE_TOKEN` jen machine; lidský API key → 401/403.

A10 — F3 stubs → 501. Reminder tools nejsou stub.

A11 — Mac write jen Brain MCP.

A12 — Rozpočet: žádné nové usage-based bez OK.

A13 — `BRAIN_PUBLIC_URL`; callback `{BRAIN_PUBLIC_URL.rstrip('/')}/oauth/callback`.

A14 — `agent_write_guard` supersedován server policy.

A15 — Cursor / Claude / Grok rovnocenní vault tools.

A16 — Reminder store = Brain MCP; dispatch = hub cron `*/2`.

A17 — Hub TEST / slug `test`.

A18 — F2 nestaví VPS→OS push stack.

A19 — At-least-once: po success v ticku další kanály ne; race OK.

A20 — Backoff: `attempt_count` default 0; `last_error || error`; K=5; `Reminders-Failed/`.

A21 — Mutate tombstone = `delete_if_exists` ×3 (full/light/charters); žádný marker.

A22 — REST min: `healthz` + vault tools za service token.

A23 — Backoff `next_attempt_at = now + min(60, 2^attempt) min`; env `REMINDER_MAX_ATTEMPTS`.

A24 — P7 lazy: mutate = tombstone; rebuild při get_context; mutate ≤5 s.

A25 — Grok chat = stejný Bot jako plugin.

A26 — Supersede návodů „Cowork/Grok nezakládají task“; F2-j.

A27 — **Chybějící Slack token (C4):** early-return / skip **jen pro Slack krok**, a **až po** pokusu Grok a Claude. Nesmí abortovat celý dispatch před Grok/Claude (dnešní `reminders_dispatch.py` L59–62 early-return na startu je **zakázaný vzor** pro F2 chat dispatch). B33.

A28 — B11+B25 hard gate pro DONE; runtime fallback B26–B30.

A29 — **Shared context builder — bez session (critic 6bf34c5e + C3 + a218008b NEW-2):** do `lib/agent_context_build.py` přesunout:  
- konstanty **`LESSON_TAKEAWAY_RE` L51** + **L80–84** (`OUTPUT_REL`, `OUTPUT_LIGHT_REL`, `OUTPUT_CHARTERS_REL`, `HUB_TITLE_RE`, `FRONTMATTER_RE`) + `TZ` dle potřeby;  
- helpers **L87–330** (`parse_frontmatter` … `collect_areas`) — včetně použití `LESSON_TAKEAWAY_RE` ~L246;  
- tělo **uvnitř** dnešního `with open_vault` — tj. logika **L333–619** (collect → snapshot → in-memory light/charters → write), **ne** řádek `with open_vault()` L332 ani jakýkoli `begin_session`/`end_session`/`open_vault`.  

Veřejné API: `build_and_write_context_bundle(vault, *, tz=…, side_failure: "warn"|"raise" = "warn") -> snapshot_dict`.  
- **Pořadí výpočtu:** (1) spočítat v paměti `snapshot`, pak `light`/`charters` se **sdíleným `generated_at`** při úspěšném dopočtu (`agent_context_light.py` L136–137, L171–173); (2) teprve pak zápis.  
- **„Trio“** = tři soubory se stejným `generated_at` **jen když** light i charters úspěšně dopočítány a zapsány.  
- **`side_failure="warn"` (hub):** zachovat dnešní soft chování (`build_agent_context.py` **L600–612**): **vždy zapsat full**; fail light/charters = WARNING, full zůstane zapsaný i bez light/charters.  
- **`side_failure="raise"` (Brain):** fail light/charters → raise; post-verify timestamps → jinak 503 (A36).  
- **Hub thin cron:** `with open_vault() as vault: build_and_write_context_bundle(vault, side_failure="warn")`.  
- **Brain rebuild:** uvnitř již otevřené request session: `build_and_write_context_bundle(vault, side_failure="raise")` — **žádná** druhá session.  
- Zakázáno: lib volá `open_vault` / nestuje session.  
Mac `scripts/build_agent_context.py` mimo F2 DONE.

A30 — Vault skip gate před chat send; no attempt++ (A34).

A31 — Grok chat kontrakt v runbooku před F2-i.

A32 — Tombstone delete-if-exists ×3; **needs_rebuild** = §3 (včetně A37 + **TTL 15 min C2**); žádný prázdný/marker.

A33 — PAUSED → 0 sends; B34b.

A34 — Skip/PAUSED ≠ pokus (no attempt++ / no backoff).

A35 — Docker context `vps/`; `COPY second-brain-hub/lib/ /app/lib/`; zakázán `COPY ../`.

A36 — Soft/hard side files: hub soft WARNING (full zapisuje i bez light/charters — A29); Brain hard raise + post-verify timestamps → jinak 503.

A37 — Warm: vyžaduj `light.generated_at == full.generated_at` (charters stejně); nesoulad → needs_rebuild (B3d).

A38 — **Request-scoped vault:** Brain MCP/REST: `with brain_vault(mode=…) as vault:` (uvnitř `open_vault`). Hub cron: `with open_vault()`. Zakázán process-global vault. Důkaz session: `git_io.py` L133–169.

A39 — **Brain push + strict_push (C1, zamčeno):**  
- `GIT_VAULT_PUSH=1`; Brain `open_vault(strict_push=True, …)`.  
- `_push_ff_only` po fail ff-only: **vždy** `git reset --hard @{upstream}` (důkaz dnešní hub B6: `git_io.py` L563–580 — reset už existuje, raise ne).  
- **`strict_push=True`:** po **úspěšném** resetu + porcelain clean (A52 větev 1) **raise `GitPushError`** → Brain mapuje na HTTP 503.  
- **`strict_push=False` (hub default):** po resetu jen log, **bez** raise — F1 chování beze změny.  
- Reset `@{upstream}` po fail push ≠ start-of-session reset (R26 / g=7 Q1=b zůstává).  
- Pozn.: A46 `reset --hard HEAD` je error-path po body výjimce (A53); C1 reset `@{upstream}` je fail-push path uvnitř `_push_ff_only` — A46 se na `GitPushError` nespouští.  
- **Mezistav po `commit_if_dirty` + fail push (před resetem):** WT je typicky **porcelain clean**, lokální tip **ahead of @{upstream}** — `_is_dirty` (`git status --porcelain`, L267–269) to **neskipne**. Viz A52.

A40 — **Task ID ceiling v lib:** `lib/task_id_allocate.py` port z `scripts/next_task_id.py` L61–162 přes vault API.

A41 — **Plugin SSOT:** `ŠABLONY/skills/` + `ŠABLONY/plugins/{cursor,claude,grok}/`; F2-j + T12.

A42 — Brain `requirements.txt` ⊇ hub lib deps + FastAPI/MCP.

A43 — **Allocate preview (g=6):** non-reserving; B8/T6 = concurrent `create_task`.

A44 — **strict_push jen Brain (g=6).**

A45 — **Rebuild = mutate (g=6 + g=10 Q1=a)** v **stejné** request session jako `get_context` (volá `bundle(vault)`).  
- `needs_rebuild=false` + tip ahead → warm OK (B3b).  
- `needs_rebuild=true` + tip ahead → **503 `vault_tip_ahead`** (B45); **ne** rebuild, **ne** návrat stale snapshotu jako success (B3e).  
Tip sync → teprve pak rebuild dle R15.

A46 — **Error-path discard — úzký guard:**  
`discard_dirty_on_error and exc_type is not None and not self.skipped` **a** lock držen → `git reset --hard HEAD` před unlock.  
**Nikdy** při dirty-start / flock-busy / `skipped=True` / hub.  
**Ano** při vlastní raise po čistém startu → WT clean (B41).  
Fail-push path řeší **A39/C1** (`@{upstream}`), ne tento HEAD discard.

A47 — **`GIT_VAULT_PUSH≠1` = runtime fail:** 503 na mutate vč. rebuild. B40 = runtime B#.

A48 — **F2-i flock scope:** flock jen read pending+due + archive; HTTP mimo session.

A49 — **Dirty na startu (g=7 Q1 = b):** skip+log, žádný reset → Brain 503, `error_reason=vault_dirty_start` (B42). **B42 = výhradně porcelain dirty na begin_session** — ne ahead tip (B45).

A50 — **Factory kwargs:** `open_vault(..., strict_push=, discard_dirty_on_error=)` → `GitVault` **před** `_PausedVault`. Brain jen přes factory. (`vault_factory.py` L59–85 dnes bez kwargs.)

A51 — **`is_due` / status normalizace (NEW-2):** Dnes `is_due` vyžaduje `status == "pending"` (`lib/reminders.py` L94–96). F2:  
- **Výchozí:** `is_due` true když `status in {"pending", "failed"}` ∧ deliver_at≤now ∧ (`next_attempt_at` chybí ∨ ≤now). Tím pádem legacy JSON se `status=failed` ještě v Pending zůstane retryable.  
- **Nové zápisy** po all-fail v Pending: držet `status=pending` + `last_error` + `next_attempt_at` (R21); po K → move `FAILED_DIR` se `status=failed`.  
- Alternativa (ekvivalentní T15): při read migrace `failed`→`pending`+zachovat `last_error` — pokud implementace zvolí migraci, `is_due` smí zůstat jen `pending`, ale T15 musí pokrýt legacy soubor.  
Výchozí předpoklad plánu = větev `status in {pending, failed}` (bez povinné migrace na disku).

A52 — **C1 recovery + tip-ahead follow-up (a218008b + g=9):**  
Po `commit_if_dirty` + fail ff-only: WT typicky **clean**, tip **ahead**. `_is_dirty` (L267–269) ahead **neskipne** — **≠ B42**.  

| Větev | Podmínka | Výsledek (Brain `strict_push`) |
|---|---|---|
| **(1) reset OK** | `reset --hard @{upstream}` OK + porcelain clean + tip=upstream | 503, `error_reason=vault_push_reset_ok` (+ lidská message); tip sync |
| **(2) reset fail** | reset rc≠0 / tip stále ahead nebo divergent | 503, `error_reason=vault_push_reset_failed`; kritický log; tip zůstane ahead; **ne** B42; **ne** auto start reset |

**Po větvi (2) / jakémkoli `HEAD ≠ @{upstream}` na Brainu:** další **mutate** i **`get_context` needs_rebuild** → **503** `vault_tip_ahead` (B45/B3e); warm read/`get_context` smí; ops = manuální SSH (runbook). Hub: F1 log+reset, bez tip-ahead gate.


A53 — **C1 vs A46 (g=8):** A46 `reset --hard HEAD` jen při body `exc_type is not None` ∧ `discard_dirty_on_error` ∧ `not skipped` ∧ lock. Fail-push běží při `exc_type is None` (tělo OK → commit → `_push_ff_only`); po C1 raise z `end_session` se A46 **nesmí** spouštět kvůli `GitPushError`. Důkaz pořadí: `git_io.py` L158–169.

A54 — **C4 vs B29 (g=8):** Chybějící Slack token = skip jen Slack po Grok i Claude. Když Grok+Claude fail/skip a Slack skip (no token) → bez success = **B29** (attempt++, backoff, po K → Failed). Neplést s A34 (vault skip/PAUSED = 0 sends, no attempt++). T13: B33 + all-fail bez tokenu.

A55 — **Základní `error_reason` čtveřice (g=9 Q2):** `vault_dirty_start` | `vault_push_reset_ok` | `vault_push_reset_failed` | `vault_tip_ahead`. Příklad tip_ahead: „Vault tip není sync s remote (HEAD ≠ @{upstream}). Mutate/rebuild blokováno — ukliď tip přes SSH dle runbooku.“ Úplný set → **A58**. Formát → **A57**.

A56 — **Dirty vs flock vs tip (NEW-1 + g=10):**  
Dnes `begin_session` nastaví jen `skipped=True` pro flock i dirty (`git_io.py` L138–156) bez reason. F2:  

| Stav | `skipped` | `skip_reason` | Brain |
|---|---|---|---|
| flock busy | True | `vault_flock_busy` | 503 B14 |
| porcelain dirty begin | True | `vault_dirty_start` | 503 B42 |
| tip ahead, not skipped | False | `None` | warm OK; mutate/rebuild → 503 `vault_tip_ahead` (A60) |

**Zakázáno:** `if vault.skipped → vault_dirty_start`. Mapovat **výhradně** podle `skip_reason`.

A57 — **Error transport (g=10 Q2=a):** MCP `isError=true` + **content text** s `error_reason` i `message`. REST 503 JSON `{ "error_reason", "message" }`. B46.

A58 — **Úplný stabilní set `error_reason` (g=10/g=11):** ⊇ A55 + `vault_flock_busy` + `vault_push_disabled` + `vault_paused`. B46 = všechny Brain vault 503. **T16 assertuje celý set včetně `vault_paused` (NEW-4)**.

A59 — **`skip_reason` na `GitVault` (NEW-1):** `self.skip_reason` vedle `skipped`. begin_session: flock → `"vault_flock_busy"`; dirty → `"vault_dirty_start"`. `VaultSessionSkipped` nese reason. `_PausedVault` forwarduje `skipped`/`skip_reason`.

A60 — **Centrální pre-tool gate tip+PUSH ve `vault_deps` (NEW-3):** tools jen přes `brain_vault(mode: read|mutate|rebuild)`. Po open: (1) skipped → 503(`skip_reason`); (2) PAUSED mutate/rebuild → `vault_paused`; (3) mode mutate/rebuild: PUSH≠1 → `vault_push_disabled`; tip ahead → `vault_tip_ahead`; (4) mode=read: tip/PUSH gate ne. Zakázáno per-tool tip/PUSH bez společného helperu. B47.

A61 — **F2-i PAUSED gate před HTTP (NEW-2):** před 0b pokud `VAULT_WRITERS_PAUSED` nebo 0a skipped → 0 sends, no attempt++. A33/B34b/T13.

A62 — **Retry jen flock (g=12):** Brain retry 1–2× **jen** při `skip_reason == "vault_flock_busy"`; `vault_dirty_start` (a jiné skip) → okamžitě 503 bez retry. (R19)

A63 — **PAUSED detekce v brain_vault (g=12):** env `VAULT_WRITERS_PAUSED` (nebo `isinstance(_PausedVault)`) ve kroku A60 (2) **před** tip/PUSH; ne až catch po mutate.

A64 — **§2 / request scope (g=12 + critic 7db484d6):** v Návrh §2 **jen** `brain_vault(mode=…)` (A60 + A62 + A63). Zakázáno: bare `with open_vault` v Brain app; bare `if vault.skipped → dirty_start`. `vault_deps.py` = `brain_vault`, ne holý re-export `open_vault`.


---

## Současný stav (ověřeno v kódu)

| Fakt | Důkaz |
|---|---|
| F1 cutover live | [docs/git-vault-runbook.md](../git-vault-runbook.md) |
| Session lifecycle | `lib/git_io.py` L4, L133–169, L551–580 |
| Dirty start → skip, bez reset | `git_io.py` L150–156 |
| **`skip_reason` dnes neexistuje** — flock i dirty jen `skipped=True` | `git_io.py` L112, L144, L156; `_require_mutate` L330–334 |
| `end_session` + `exc_type` → no commit | `git_io.py` L158–169 |
| Flock busy → skipped | `git_io.py` L138–145 |
| `_is_dirty` = jen porcelain (`status --porcelain`), **ne** ahead tip | `git_io.py` **L267–269** |
| Push fail = **log + `reset --hard @{upstream}`**, **ne raise** | `git_io.py` `_push_ff_only` **L563–580** (B6 hub) |
| `GitPushError` / `strict_push` dnes **neexistují** | grep hub: žádný hit |
| `main` full write L600 vždy; light/charters try/WARN L602–612 | `cron/build_agent_context.py` |
| `open_vault()` bez kwargs | `vault_factory.py` L59–85 |
| `LESSON_TAKEAWAY_RE` | `cron/build_agent_context.py` **L51**; použití ~**L246** |
| OUTPUT_* + HUB/FRONTMATTER regex | `cron/build_agent_context.py` **L80–84** |
| Helpers | `cron/build_agent_context.py` L87–330 |
| `main`: **`with open_vault()` L332**, tělo L333–619 (write full L600, light/charters WARN L602–612) | `cron/build_agent_context.py` |
| Light/charters `generated_at` z full | `lib/agent_context_light.py` L136–137, L171–173 |
| Reminders: bez FAILED_DIR; `is_due` jen `pending` | `lib/reminders.py` L10–12, L94–99 |
| Dispatch: **early-return pokud chybí `SLACK_BOT_TOKEN` před jakoukoli prací** | `cron/reminders_dispatch.py` **L59–62** (C4: tento vzor nesmí F2 chat dispatch opakovat) |
| Dispatch fail → pole `error` | `cron/reminders_dispatch.py` L104–114 |
| next_task_id ceiling | `scripts/next_task_id.py` L61–162 |
| Brain / plugin manifests chybí | jen `second-brain-hub/` |
| Grill g=1 Q2 | stale **>15 min** → sync rebuild (ledger F2) |

### Zapisovatelé po F2

| # | Actor | Mechanismus |
|---|---|---|
| W-cron | Lifecycle / context / slack_poll / reminder | `open_vault()` → ops / `bundle(vault)` |
| W-brain | OAuth MCP/REST | `brain_vault(mode=…)` → A60 → `open_vault(strict_push=True, discard_dirty_on_error=True)` → tools / `bundle(vault)` |
| W-web | Člověk | GitHub web UI PR |
| W-machine | service token | stejný `brain_vault` / vault_deps |
| W-n8n inbox / W-mac-fs | — | off / zakázáno |

---

## Návrh

### 0) Preflight (F2-a)

Privacy; `BRAIN_PUBLIC_URL`; OAuth; Claude research; **Grok chat kontrakt** (R22).

### 1) Shared lib extrakce

| Soubor | Změna | R# |
|---|---|---|
| `lib/agent_context_build.py` (**nový**) | Konstanty **L51 `LESSON_TAKEAWAY_RE` + L80–84** + helpers L87–330 + tělo L333–619 jako `build_and_write_context_bundle(vault,…)`; in-memory trio→write; `side_failure`; **žádný** import/volání `open_vault` / session API | R15, R29, C3 |
| `lib/context_tombstone.py` | tombstone ×3 | A21 |
| `lib/task_id_allocate.py` (**nový**) | ceiling nad vault API | R24 |
| `lib/reminders.py` | `FAILED_DIR`; `attempt_count=0`; `is_due` + `next_attempt_at` + A51 status; `reminder_error` dual-read | R21, R28 |
| `cron/build_agent_context.py` | Thin: `with open_vault() as vault: build_and_write_context_bundle(vault, side_failure="warn")` | R15, R29 |
| `scripts/next_task_id.py` | Thin CLI → lib | R24 |
| `git_io.py` | `strict_push`; `GitPushError`; `_push_ff_only`; guarded discard; **`skip_reason` A59** | R23, R26, C1, NEW-1 |
| `vault_factory.py` | kwargs → `GitVault` před `_PausedVault` | R27 |

### 2) Služba Brain

Coolify context = `vps/`.

```
vps/second-brain-brain/
  Dockerfile / requirements.txt / config.example.env / README.md
  app/
    main.py                  # PUSH=1 assert; no global vault
    vault_deps.py            # brain_vault(mode=read|mutate|rebuild) — A60/A62/A63/A64; uvnitř open_vault(strict_push=True, discard_dirty_on_error=True)
    # tools/rest: jen přes brain_vault; zakázán přímý open_vault
    auth_google.py / auth_service.py / policy.py / fm_contract.py
    flock_retry.py / context_freshness.py   # TTL = 15 min exact (C2)
    tools/… / rest.py
  tests/
```

**Request scope (A60 + A64 — žádný bare `open_vault` / bare `skipped`):**

```
with brain_vault(mode="read"|"mutate"|"rebuild") as vault:
    # A60: (1) skipped → 503(skip_reason); A62 retry jen flock_busy
    # (2) A63 PAUSED mutate|rebuild → vault_paused
    # (3) mutate|rebuild: PUSH≠1 / tip ahead → 503
    # (4) read: tip/PUSH gate ne
    … tools …
    build_and_write_context_bundle(vault, side_failure="raise")  # mode=rebuild
# push fail: reset @{upstream} then GitPushError → 503 (C1)
```

### 3) MCP / REST tools

| Tool | Chování | R# |
|---|---|---|
| `get_context` | §3 (+ TTL 15 min); rebuild = `bundle(vault)` v request session; post-verify; PUSH | R15, R23, R29 |
| `read_file` / `list_dir` | allowlist | R4 |
| `allocate_task_id` | preview | R24, A43 |
| `create_task` | re-ceiling; tombstone; push | R6, R23 |
| `update_task` / capture / material / set_focus | CAS/policy + push | R4 |
| `schedule_reminder` | attempt_count=0; push | R13, R28 |
| `cancel_reminder` / `list_reminders` | + push u mutate | R13 |
| F3 stubs | 501 | A10 |

**Freshness §3 (C2):**  
(1) full missing  
(2) bad `generated_at` **nebo stale = `now - generated_at > 15 minut` přesně** (pražská/UTC konzistentně s builderem; dokumentovat v `context_freshness.py`)  
(3) light/charters missing  
(4) timestamp mismatch B3d  
(5) else warm ≤256 KB.  
Žádný marker. Nikdy tichý TOP ze stale snapshotu.

### 4) Reminder chat delivery (A48, A51, **C4**)

| Krok | Session? | Chování |
|---|---|---|
| 0a | short | list due; pokud skipped → exit 0 sends |
| 0a′ | — | **PAUSED gate (A61)** před 0b → 0 HTTP, no attempt++ |
| 0b | — | HTTP **Grok → Claude → Slack** mimo flock. Chybějící Slack token = **skip Slack až v tomto kroku**, po Grok/Claude (A27/C4). Zakázáno: abort na startu kvůli Slack tokenu. |
| 0c | short | Sent / pending+last_error+backoff / FAILED_DIR po K |

### 5) Policy + FM + Plugin SSOT (A41)

### 6) Docs / Coolify / SB15

Runbook: session vs bundle; discard A46; **strict_push A52 (1) clean+503 / (2) ahead≠B42**; factory+PAUSED; F2-i flock; reminder status; g=7 Q1=b; **TTL 15 min**; hub soft full (A29). SB15-3.

---

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | Neautentizovaný mutate | 401 | R5 | T2 |
| B2 | OAuth mimo allowlist | 403 | R5 | T2 |
| B2b | Lidský API key | 401/403 | R5 | T2 |
| B3 | needs_rebuild ∧ tip sync | sync rebuild `bundle(vault)`; busy→`vault_flock_busy`; nikdy tichý stale TOP | R15, R29, **C2** | T3 |
| B3e | needs_rebuild ∧ tip ahead | **503 `vault_tip_ahead`**; žádný rebuild; **žádný** success se stale TOP | R30, A45, A56, g=10 | T16 |
| B3b | trio OK + timestamps match + **age ≤ 15 min** | warm | R15 | T3, T10 |
| B3c | light/charters chybí | needs_rebuild | A32 | T3 |
| B3d | timestamp mismatch | needs_rebuild | A37 | T3 |
| B4 | create_task OK | FM + commit + push; push fail→A52/B44 | R6, R23, **C1** | T4, T8, T9, **T16** |
| B5 | špatný expect_oid | konflikt; no commit | R4 | T4 |
| B6 / B7 | focus / Stav auto | deny | R4 | T5 |
| B8 | paralel `create_task` | unikátní ID | R24, A43 | T6 |
| B9 / B21 | Mac FS / CU write | zakázáno | R4 | T7 |
| B10 | live smoke | jen TEST | R16 | T8 |
| B11 | Grok plugin + MCP write | PASS DONE | R6, R25 | T8, T12 |
| B12 / B22 | F3 stub / Slack send tool | 501 | A10 | T2 |
| B13 | PAUSED přes factory | mutate/rebuild → 503 `vault_paused`; warm read smí | R27, A58, A60 | T4, T16 |
| B14 | flock busy | 503 `vault_flock_busy` z `skip_reason` (≠ dirty_start); **no** reset | R19, A46, A56, A59 | T6, T16 |
| B15 | service token | OK + `service:` | R5 | T2 |
| B16 | dual-read FM | OK | R18 | T5 |
| B17–B19 | n8n off; stale Slack; soft A17 | OK | R7, R9 | T1 |
| B20 | SB15-3 | odškrtnuto | R11 | T11 |
| B23 | schedule_reminder | attempt_count=0; push | R13, R28 | T14, T9 |
| B24 | cancel_reminder | Cancelled + push | R13 | T14 |
| B25 | Grok chat OK | Sent; PASS důkaz | R14 | T13 |
| B26 | Grok fail | → Claude | R14 | T13 |
| B27 | Grok+Claude fail/skip | → Slack | R14, A27 | T13 |
| B28 | první success | Sent; další kanály ne | R14, A19 | T13 |
| B29 | all fail | Pending (nebo failed legacy); attempt++; last_error; next_attempt_at | R21, A51 | T13, T15 |
| B30 | attempt ≥ K | `Reminders-Failed/` | R21 | T13, T15 |
| B31 | mutate | tombstone ×3 | A21 | T3 |
| B32 | double ping | docs OK | R20 | T1 |
| B33 | no Slack token | **Grok i Claude se spustí**; Slack skip až po nich; dispatch neabortuje na startu | A27, **C4** | T13 |
| B34 / B34b | skipped **nebo** PAUSED před 0b | 0 HTTP sends; no attempt++ | A30–A34, A61, NEW-2 | T13 |
| B35 | hub `side_failure=warn`, light/charters fail | **full zapsán**; WARNING; light/charters chybí OK | A29, A36, **NEW-2** | T3 |
| B35b | Brain `side_failure=raise`, light/charters fail | raise → 503; žádný tichý partial warm | A29, A36 | T3 |
| B35c | úspěšný dopočet light+charters | sdílený `generated_at` na full/light/charters („trio“) | A29 | T3 |
| B36 | F2-a bez Grok kontraktu | eskalace | R22 | T1 |
| B37 | OAuth callback | rstrip | R17 | T2 |
| B38 | process-global vault | zakázáno | R23 | T16 |
| B39 | hub ∥ Brain | Brain 503 | R23 | T16 |
| B40 | PUSH≠1 | runtime 503 `vault_push_disabled` vč. rebuild | A47, A58 | T4, T9, T16 |
| B41 | vlastní raise, skipped=False | WT clean (`reset --hard HEAD`) | A46 | T3, T16 |
| B42 | porcelain dirty-start | 503, `error_reason=vault_dirty_start`; porcelain beze změny; **≠ tip ahead** | A49, A55, R26 | T16 |
| B43 | `agent_context_build` modul | neimportuje/nevolá `open_vault` / session API; obsahuje `LESSON_TAKEAWAY_RE` | R29, **C3** | T3 |
| B44 | fail push strict_push | **(1)** reset OK → 503 `vault_push_reset_ok`; **(2)** reset fail → 503 `vault_push_reset_failed` + tip ahead; hub jen log+reset | R23, A52, A55, C1 | T16 |
| B45 | tip ahead ∧ (mutate ∨ `get_context` needs_rebuild) | 503 `vault_tip_ahead` + message (A57); **žádný** commit/rebuild; warm get_context OK; **ne** stale TOP | R30, A45, A56, g=10 | T16 |
| B46 | jakýkoli Brain vault 503 | MCP isError text i REST JSON mají `error_reason`+`message` (A57); reason ∈ A58 (vč. vault_paused) | R30, A55, A57, A58 | T16 |
| B47 | tip/PUSH gate | pouze v `vault_deps` (A60); tools bez vlastní tip/PUSH logiky | NEW-3 | T16 |

**Checklist A (chování — SECOND_BRAIN profil):** sync rebuild B3 (+ TTL 15 min); CAS/`expect_oid` B5; TZ Prague; auth; ID B8; flock; chat B25–B30 + B33 pořadí; FM; push B40/B44; discard B41 vs B42; builder session boundary B43.  
**CAS:** mutate tools s `expect_oid` / mtime dle vault API (Git blob SHA).  
**Idempotence cronu:** thin builder + reminder dispatch at-least-once.  
**Měny / Pipedrive / Alembic / RBAC Universe / FE:** netýká se, protože profil SECOND_BRAIN + Brain API bez Universe stacku.

---

## Výkonový rozpočet (P)

| Tělo | 1 Objem | 2 SQL | 3 Load | 4 Externí | 5 Page | 6 Payload | 7 Cache | 8 Násobení | 9 FE | 10 Worker | 11 Cíl |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 get_context | snapshot (+rebuild) | 0 | scan při rebuild | ne | — | ≤256 KB | §3; **TTL 15 min**; delete ×3 | 1 session | — | flock | warm ≤500 ms; rebuild ≤P4 |
| P2 mutate (+push) | 1–N | 0 | cesty | git push | — | &lt;1 MB | — | 1 session | — | retry 1–2 | ≤5 s + push |
| P3 hub cron | F1 | — | — | — | — | — | — | — | — | — | F0 P3 |
| P4 rebuild | vault | 0 | bundle L333–619 logika (bez open_vault) | ne | — | — | — | ≤1 / needs_rebuild; **0** vnořených session | — | — | &lt;30 s |
| P5–P6 / P8 | netýká se (žádný FE/Universe SQL) | | | | | | | | | | |
| P7 | mutate | — | delete ×3 | ne | — | — | disk | — | — | flock | B31 |
| P9 | LFS | — | — | — | — | &gt;40MiB 413 | — | — | — | — | 413 |
| P10 | reminders | — | — | — | — | — | — | at-least-once | — | — | R20 |
| P11 dispatch | N due | 0 | JSON | HTTP mimo flock | — | brief | — | 2× short session | — | `*/2` | &lt;30 s |

Objem: T9 `du -sh /data/vault` + size `agent-context.json`. (Hlavní agent ověří na Coolify; odhad F0 A7 pokud SSH readonly.)

---

## Testy (T#)

| T# | Typ | Owner | Soubor | B# |
|---|---|---|---|---|
| T1 | ruční | gate | Privacy, URL, n8n, Grok kontrakt | B17–B19, B32, B36 |
| T2 | pytest | gate | auth + callback | B1, B2, B2b, B12, B15, B22, B37 |
| T3 | pytest | gate | hub warn **full bez light/charters (B35)**; Brain raise (B35b); sdílený generated_at (B35c); §3/**TTL 15 min**/B3d; tombstone; B41; **`assert` `agent_context_build` nevolá `open_vault` + obsahuje `LESSON_TAKEAWAY_RE` (B43)** | B3*, B31, B35*, B41, **B43** |
| T4 | pytest | gate | CAS; PAUSED+factory kwargs; PUSH=0→503 | B4, B5, B13, B40 |
| T5 | pytest | gate | policy + FM | B6, B7, B16 |
| T6 | pytest | gate | paralel create_task; flock → skip_reason=vault_flock_busy, no reset; **A62: retry 1–2× jen flock_busy; dirty_start → 0 retry** | B8, B14, A62 |
| T7 | pytest/ruční | gate | skills readonly | B9, B21 |
| T8 | ruční TEST | gate | 3× OAuth create | B4, B10, B11 |
| T9 | QA Coolify | gate | deploy; PUSH=1; remote tip | B4, B23, B40 |
| T10 | smoke | gate | P1 latence | B3b |
| T11 | ruční | gate | SB15-3 | B20 |
| T12 | ruční | gate | Grok plugin | B11 |
| T13 | pytest+smoke | gate | B25–B30; B33; **B34b: PAUSED i skipped → 0 HTTP před 0b, no attempt++** | B25–B30, B33, B34* |
| T14 | pytest | gate | reminder MCP; attempt_count=0 | B23, B24 |
| T15 | pytest | gate | `is_due`+`next_attempt_at`; dual-read; FAILED_DIR po K; **legacy `status=failed` v Pending je due (A51)** | R21, R28, B29, B30, A51 |
| T16 | pytest | gate | Assert celý A58 vč. vault_paused; dirty vs flock z skip_reason; **A62 retry jen flock_busy**; tip_ahead mutate+needs_rebuild; warm tip OK; push_disabled; B46/A57; B47 tip/PUSH jen brain_vault; A64 | B3e, B13, B14, B38–B42, B44–B47, A62, A64 |

TESTER: přeskočeno (profil SECOND_BRAIN).

---

## Pořadí implementace

F2-a — Privacy; URL; OAuth; Grok kontrakt.  
F2-b — Extrahovat `agent_context_build` (**L51 + L80–84 + L87–330 + L333–619**, bez session); tombstone; task_id_allocate; reminders R28+A51; thin cron `open_vault`→`bundle`; vault_factory kwargs; git_io flags + **GitPushError/strict_push (C1)** + **`skip_reason` (A59)**; Brain scaffold; **`vault_deps.brain_vault` = A60 + A62 + A63 + A64** — ne holý factory wrapper.  
F2-c — Auth + B37.  
F2-d — Policy + FM.  
F2-e — Tools **jen** přes `brain_vault(mode=…)`; get_context: warm=`read`, rebuild=`rebuild` + `bundle(vault)`; **freshness TTL 15 min (C2)**; zakázán přímý `open_vault` v tools/rest.  
F2-f — REST (stejně přes `brain_vault`).  
F2-g — Pytest T2–T6, T14–T16 (T3 B43; T15 A51; **T16 B44 + A58 + A62**; **T6 skip_reason + A62**).  
F2-h — Coolify; T9.  
F2-i — Dispatch flock scope; **Grok→Claude→Slack; Slack token skip až po Grok/Claude (C4)**; T13.  
F2-j — Skills + plugins; agenda-remind.  
F2-k — T8; T10; T12; cleanup; T11.

---

## Rizika a zpětná kompatibilita

1. Grok API — F2-a; B25 hard.  
2. Dual-writer flock — B14/B38/B39.  
3. Push fail → Brain 503 po resetu (C1); hub dál jen log+reset.  
4. Claude skip+log.  
5. FM dual-read.  
6. Mac FS bypass.  
7. Double ping OK.  
8. Backoff K=5; legacy `status=failed` — A51.  
9. next_task_id Path vs vault.  
10. Extrakce builderu — regres hub; T3/T15; **LESSON_TAKEAWAY_RE musí jít s modulem (C3)**.  
11. **Vnořená session v lib** by rozbila flock/discard — R29/B43 to zakazuje.  
12. Plugin drift — T12.  
13. Hub soft WARNING → B3d.  
14. TEST cleanup.  
15. Dirty po vlastním raise bez discard → permanent skip; A46.  
16. Discard nesmí mazat cizí dirty (g=7 Q1=b) — `not self.skipped`.  
17. F2-i split session — R20 OK.  
18. Brain mimo factory — R27/T4.  
19. **TTL 15 min** vs cron frekvence — častější rebuild při idle get_context; P1/P4.  
20. **C4:** refactor dispatch nesmí znovu early-return na Slack token před chat kanály.

---

## Otevřené otázky pro uživatele

Žádné blokující (grill g=1–g=7 uzavřen; C1–C4 zamčeny hlavním agentem po stropu d28e95c7).

| # | Uzavření |
|---|---|
| Chat / double ping / backoff / OAuth-only | R14, R20, R21, R5 |
| F2-a bez Grok API | R22, B36 |
| Tombstone / freshness / PAUSED / Docker / trio | A32–A36 |
| **stale TTL = přesně 15 min** | R15, §3, B3, **C2** |
| Warm timestamp | A37, B3d |
| Request-scoped + PUSH=1 | A38–A39 |
| **strict_push: reset @{upstream} pak raise** | A39, B44, **C1** |
| Allocate preview | A43, B8 |
| Rebuild = mutate v **stejné** session + bundle(vault) | A45, A29, R29 |
| Discard guard | A46, B41 |
| PUSH≠1 runtime | A47, B40 |
| F2-i flock | A48 |
| **g=7 Q1=(b)** dirty-start skip+503, no reset | A49, B42 |
| Factory kwargs před PAUSED | A50 |
| Legacy reminder `status=failed` | A51 (default: is_due accepts failed) |
| Slack token po Grok/Claude | A27, B33, **C4** |
| LESSON_TAKEAWAY_RE v shared builderu | A29, **C3** |
| **g=8 A52–A54** (opraveno r=2: ahead≠B42) | A52, A53, A54 |
| Hub full bez sides | A29, B35, **NEW-2** |
| **g=9 tip-ahead mutate→503; read OK; SSH ops; error do chatu** | R30, A52, A55, B45, B46 |

Volitelné: `REMINDER_MAX_ATTEMPTS` ∈ {3,4,5}.

---

## C# → vyřešeno (critic a218008b · k=1 r=2)

| ID | Závažnost | Stav | Kde |
|---|---|---|---|
| **NEW-1** | MAJOR | **vyřešeno** | A52/B44/T16: reset fail = ahead/divergent ≠ B42 |
| **NEW-2** | MINOR | **vyřešeno** | A29/A36/B35*: hub warn = full vždy; trio = sdílený generated_at při úspěchu |

---

## C1–C4 → jak vyřešeno (d28e95c7 · otevření #2)

| ID | Závažnost | Stav | Kam v plánu |
|---|---|---|---|
| **C1** | BLOCKER | **vyřešeno** | R23 + A39 přepsány: fail ff-only → `reset --hard @{upstream}` (důkaz L563–580) **pak** `GitPushError`→503 při `strict_push=True`; hub beze změny. Nové **B44** + T16. Návrh `git_io.py` + request-scope komentář. |
| **C2** | MAJOR | **vyřešeno** | R15: stale = `generated_at` starší než **přesně 15 minut**. Freshness §3 bod (2) explicitní. B3/B3b s TTL. P1 cache řádek TTL 15 min. |
| **C3** | MAJOR | **vyřešeno** | A29 + Současný stav: `LESSON_TAKEAWAY_RE` L51 (+ použití ~L246) v seznamu přesunu vedle L80–84. B43/T3 assert existence konstanty. F2-b pořadí. |
| **C4** | MINOR | **vyřešeno** | A27 + §4 dispatch + B33: chybějící Slack token = skip Slack **až po** Grok a Claude; zákaz early-return vzoru `reminders_dispatch.py` L59–62. T13 pokrývá B33. |

---

## Delta pro implementaci (jen C1–C4 oproti předchozí verzi k=3 r=3)

1. **C1 / `git_io._push_ff_only`:** po fail push vždy `reset --hard @{upstream}` (už dnes); **nově** při `strict_push=True` po resetu raise `GitPushError` (Brain→503). Hub default `strict_push=False` = jen log+reset. Test T16/B44: po simulovaném fail push je WT clean a Brain dostane 503.  
2. **C2 / `context_freshness`:** `needs_rebuild` když `generated_at` age **> 15 minut** (ne „bad/stale“ bez čísla). Warm path jen pokud age ≤ 15 min a timestamps match.  
3. **C3 / `agent_context_build`:** přesunout i `LESSON_TAKEAWAY_RE` z L51 (ne jen OUTPUT_*/HUB/FRONTMATTER L80–84).  
4. **C4 / reminder chat dispatch:** nevolat early-return na chybějící Slack token před Grok/Claude; Slack skip jen ve třetím kroku kanálového řetězce.

---

## NEW → zapracováno (critic d28e95c7 · otevření #2)

| ID | Závažnost | Kam | Stav |
|---|---|---|---|
| **C1 / NEW-1** | BLOCKER | R23, A39, B44, T16 | **zapracováno** |
| **C2 / NEW-2** | MAJOR | R15, §3, B3, B3b, P1 | **zapracováno** |
| **C3 / NEW-3** | MAJOR | A29, B43, T3 | **zapracováno** |
| **C4 / NEW-4** | MINOR | A27, B33, §4, T13 | **zapracováno** |

---

## g=9 → zapracováno (r=3)

| ID | Stav | Kam |
|---|---|---|
| Q1=(b) | zapracováno | R30, A52, B45 |
| Q2 / chat error | zapracováno | A55, B46, T16 |
| A56 dirty vs tip | zapracováno | A56 |

---

## g=10 → zapracováno

| ID | Stav | Kam |
|---|---|---|
| Q1=(a) | zapracováno | R30, A45, A56, B3e, B45 |
| Q2=(a) A57 | zapracováno | A57, B46 |
| Q3=(a) A58 | zapracováno | A58, B14, B40 |
