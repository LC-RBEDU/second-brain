# Second Brain Brain API

HTTPS služba (Coolify): remote MCP + OAuth + tenké REST. Sdílí `/data/vault` s hubem — oddělený clone zakázán.

- `BRAIN_PUBLIC_URL` = veřejné HTTPS (MCP + OAuth callback `{URL}/oauth/callback` + REST). Ne dashboard UI.
- `BRAIN_SERVICE_TOKEN` = Bearer pro hub cron / service klienty (`GET /v1/triage/candidates`, …).
- `SLACK_USER_TOKEN` = `xoxp-` — povinné pro L1 live Slack (`slack_live` / triage). Bez něj Brain vrací `error_reason: slack_token_missing` a `live_slack: []`.
- Volitelně `SLACK_LUKAS_USER_ID` — přesnější search query (`to:<@U…>`); bez něj fallback `is:im` / `from:me`.
- Vault: jen přes `app.vault_deps.brain_vault(mode=…)` — nikdy přímý `open_vault` z tools/rest.
- `GIT_VAULT_PUSH=1` povinné; mutate bez úspěšného push → 503.

Build context Coolify: **`vps/`** (Dockerfile `COPY second-brain-hub/lib/` + `second-brain-brain/app/`).

Lokálně:

```bash
cd vps
export BRAIN_ALLOW_NO_PUSH=1 GIT_VAULT_ROOT=/path/to/vault PYTHONPATH=second-brain-brain:second-brain-hub/lib
uvicorn app.main:app --reload --app-dir second-brain-brain
```
