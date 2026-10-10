# Brain API runbook (F2)

Plán: [docs/plans/2026-10-10-sb-operacni-model-f2.md](plans/2026-10-10-sb-operacni-model-f2.md)  
Git vault: [docs/git-vault-runbook.md](git-vault-runbook.md)

## F2-a preflight

| # | Položka | Stav / akce |
|---|---|---|
| 1 | Privacy | Vault private (`LC-RBEDU/second-brain-vault`); Brain secrets jen Coolify env; žádné tokeny v chatu/gitu |
| 2 | n8n INBOX writers | vypnuté do F3 (B17) |
| 3 | Stale Slack INBOX | OK do F3 (B18) |
| 4 | soft A17 Free | schváleno F1 (B19) |
| 5 | `BRAIN_PUBLIC_URL` | Coolify veřejné HTTPS **bez** trailing slash preference; callback = `{URL.rstrip('/')}/oauth/callback` (B37) |
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
| `BRAIN_PUBLIC_URL` | `https://…` (doplní uživatel) |
| `VAULT_BACKEND` | `git` |
| `GIT_VAULT_ROOT` | `/data/vault` |
| `GIT_VAULT_PUSH` | `1` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth |
| `BRAIN_SERVICE_TOKEN` | machine only |

Build context: `vps/` — image [`vps/second-brain-brain/Dockerfile`](../vps/second-brain-brain/Dockerfile).
