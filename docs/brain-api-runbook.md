# Brain API runbook (F2 + F4)

Plán: [docs/plans/2026-10-10-sb-operacni-model-f2.md](plans/2026-10-10-sb-operacni-model-f2.md) · F4: [docs/plans/2026-10-10-sb-operacni-model-f4.md](plans/2026-10-10-sb-operacni-model-f4.md)  
Git vault: [docs/git-vault-runbook.md](git-vault-runbook.md) · Artifact: [docs/claude-artifact-dashboard.md](claude-artifact-dashboard.md)

## F4 — Slack dump off + light context

| Položka | Stav |
|---|---|
| `slack_poll` dump | Off (crontab + `SLACK_POLL_DUMP=0`) |
| Triáž L1 Slack | `GET /v1/triage/candidates` default `include_live_slack=true` / `slack_live` |
| Light dashboard | `GET /v1/context/light` — **human OAuth only** (service → 403 `human_oauth_required`) |
| Light stale / trio mismatch | **503** `context_light_stale` — nerestartuje; nejdřív full `get_context` / cron |
| MCP light | **Není** — MCP fail-path = plný `get_context` |
| Archiv residual dump | `cron/archive_slack_inbox.py --dry-run` / `--no-dry-run` (CAS move) |

## F2-a preflight

| # | Položka | Stav / akce |
|---|---|---|
| 1 | Privacy | Vault private (`LC-RBEDU/second-brain-vault`); Brain secrets jen Coolify env; žádné tokeny v chatu/gitu |
| 2 | n8n INBOX writers | vypnuté do F3 (B17) |
| 3 | Stale Slack INBOX | OK do F3 (B18) |
| 4 | soft A17 Free | schváleno F1 (B19) |
| 5 | `BRAIN_PUBLIC_URL` | Live: `https://brain.cyprovi.cz` — callback = `{URL}/oauth/callback` (B37) |
| 6 | OAuth Google | allowlist `lukas@redbuttonedu.cz` + `lukas.cypra@gmail.com`; lidský API key → 401/403 |
| 7 | Service token | jen machine; audit `service:` |
| 8 | Grok chat kontrakt | § níže — **hard gate před F2-i** (R22 / B36) |

Double ping (B32): at-least-once OK; po success v ticku další kanály ne; race double ping akceptovatelný.

## Sdílený volume

Brain a hub = **jeden** WC `/data/vault`. Oddělený clone zakázán. Coolify Brain: `GIT_VAULT_PUSH=1`.

## Session vs bundle

- Hub cron: `with open_vault() as vault: build_and_write_context_bundle(vault, side_failure="warn")`
- Brain: `with brain_vault(mode=…) as vault:` → tools / `bundle(vault, side_failure="raise")`
- Lib `agent_context_build` **nemá** session API
- **`get_context` dual-session (odchylka A45 / R30):** nejdřív `mode=read` (warm + tip ahead OK), při `needs_rebuild` druhá session `mode=rebuild` (tip/PUSH gate). Důvod: warm tip-ahead nesmí spadnout na tip gate.
- Rebuild / light-charters fail → HTTP **503** s `error_reason` (často `vault_push_reset_failed` + message prefix `context rebuild failed` — nejde o tip reset, ops čti message).

## Tip ahead / dirty / push (ops SSH)

| Symptom | `error_reason` | Ops |
|---|---|---|
| Porcelain dirty na begin | `vault_dirty_start` | Ukliď WT; **ne** auto start reset |
| Flock busy | `vault_flock_busy` | Retry; Brain 1–2× jen tento reason |
| Tip `HEAD ≠ @{upstream}` | `vault_tip_ahead` | Mutate/rebuild 503; warm read OK; `git fetch && git reset --hard @{upstream}` (nebo merge) dle situace |
| Push fail + reset OK | `vault_push_reset_ok` | Tip sync; klient retry |
| Push fail + reset fail | `vault_push_reset_failed` | Kritický; tip může zůstat ahead |

Formát: MCP `isError` text i REST JSON `{ "error_reason", "message" }`.

## Grok chat send kontrakt (A31 / R22 / B25)

**Cíl F2:** při due reminderu dorazí **zpráva do Grok Bot chatu** (primární kanál). OS push = user setting v Grok appce — ne VPS→OS stack.

### Transport (zamčeno 2026-10-10)

Oficiální cesta server → Grok Bot chat: **Routine webhook trigger** (ne xAI Responses/Chat Completions LLM API — to není doručení do uživatelského Bot chatu).

| Položka | Kontrakt |
|---|---|
| URL | `GROK_BOT_REMINDER_WEBHOOK_URL` — „POST to“ z Routines panelu po save |
| Auth | `Authorization: Bearer <key>` — klíč z panelu; env `GROK_BOT_REMINDER_WEBHOOK_KEY` (nikdy do gitu/chatu) |
| Method | `POST` + `Content-Type: application/json` |
| Body (min.) | `{"task":"<reminder text>","request_id":"<reminder.id>","source":"second-brain-hub"}` |
| Success | HTTP **200** = run **accepted** (B25 PASS důkaz = 200 + Run history / zpráva v Bot chatu). 200 ≠ „finished“. |
| Failure | non-200 / timeout / chybějící env → Grok krok **fail** → Claude → Slack (B26–B27). Chybějící secret = fail v řetězci + error log (ne tichý skip). |
| Bot | Stejný Bot jako plugin MCP (A25) |
| Routine instruction (uživatel nastaví jednou) | Po webhooku: vypiš `request_id` a text připomínky do **tohoto** Bot chatu; nic veřejně / e-mail / nákup bez potvrzení |

### Provisioning (Lukáš, jednou)

1. V Grok Bot vytvoř routine s webhook triggerem (instruction výše).
2. Save → Active → zkopíruj POST URL + key do Coolify hub (dispatch) env.
3. Zapni Bot Notifications, pokud chceš mobilní pípnutí (mimo Brain scope).

### Eskalace (B36)

Pokud webhook credentials **nejsou** v Coolify před F2-i: **zastav F2-i**, eskaluj uživateli — **neoslabuj B25** na „jen Slack OK“.

### Mimokontrakt (zakázáno jako B25 důkaz)

- Holé `POST https://api.x.ai/v1/responses` / chat completions bez Bot webhooku
- Tiché „Grok skip, Slack OK“ bez fail záznamu Grok kroku

## Claude chat (sekundární)

Bez API = skip+log → Slack (A4). Kontrakt doplní F2-i po research; neblokuje F2-a Grok hard gate.

## Coolify Brain (náčrt)

| Key | Value |
|---|---|
| `BRAIN_PUBLIC_URL` | `https://brain.cyprovi.cz` (Coolify app `second-brain-brain`) |
| `VAULT_BACKEND` | `git` |
| `GIT_VAULT_ROOT` | `/data/vault` |
| `GIT_VAULT_PUSH` | `1` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth |
| `BRAIN_SERVICE_TOKEN` | Coolify Brain env — Bearer pro MCP klienty bez OAuth cookie (Grok Bot, n8n). **Ne** do chatu. |

## MCP klienti (Grok / Cursor / Claude)

| Položka | Hodnota |
|---|---|
| URL | `https://brain.cyprovi.cz/mcp/` (s trailing slash; bez slash dřív hrozilo přesměrování na http — opraveno proxy headers) |
| Auth hlavička | `Authorization: Bearer <token>` |
| Token | Coolify → projekt **Second Brain** → app **second-brain-brain** → env `BRAIN_SERVICE_TOKEN` (Reveal). Stejný token jako service REST. |
| OAuth (browser) | `https://brain.cyprovi.cz/oauth/authorize` → session cookie — remote MCP u Groku typicky **nepoužije**; proto Bearer. |
| Grok konektory | Sdílené **napříč celým Grok účtem** — Bearer token uvidí i ostatní boti stejného účtu. Neukládat do chatu; jen do connector pole. |

Build context: `vps/` — image [`vps/second-brain-brain/Dockerfile`](../vps/second-brain-brain/Dockerfile).

## F3 (Slack / Sembly / Gmail hybrid / briefy)

Plán: [docs/plans/2026-10-10-sb-operacni-model-f3.md](plans/2026-10-10-sb-operacni-model-f3.md)

| Položka | Hodnota |
|---|---|
| Stub `/v1/f3/*` | **pryč** — reálné routes `/v1/ingest_sembly`, `/v1/capture_daily`, `/v1/triage/candidates`, `/v1/slack/live`, `/v1/mailbox/{propose,apply}`, `/v1/external/{propose,apply}`, `/v1/prepare_meeting`, `/v1/meeting_prep`, `/v1/push/test` |
| Apply path | **Client apply** po propose + 1×/2× UX. Brain `*/apply`: service → **403** `human_oauth_required`; oauth → **501** `oauth_brain_apply_post_f3` |
| Propose | oauth \| service OK; batch in-memory TTL 2 h; **replicas=1** na Coolify Brain |
| Default L1 triáž | **F4:** live Slack + Gmail + daily/sembly (`include_live_slack=true`). Dump `01-INBOX/slack` = residual only (historicky F3 default dump) |
| Meeting prep | `MEETING_PREP_WINDOW_MINUTES=70`; cron `*/15 8-23`; Grok `GROK_BOT_MEETING_PREP_WEBHOOK_*`; dry-run = 0 vault write ∧ 0 Grok |
| Proactivity | ráno 08:00 / due `0 9-17 * * 1-5` / evening 18:00; **bez** propose; `--dry-run` no-send |
| B18 OS push | `/v1/push/test` → FAIL + fallback Slack/chat je **DONE s výhradou** (primár v docs zůstává OS) |
| Partial client apply | report `{succeeded[], failed[{id,error_reason}]}` — ne tiché all-OK |
