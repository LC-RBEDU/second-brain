# Second Brain Brain API

HTTPS služba (Coolify): remote MCP + OAuth + tenké REST. Sdílí `/data/vault` s hubem — oddělený clone zakázán.

- `BRAIN_PUBLIC_URL` = veřejné HTTPS (MCP + OAuth callback `{URL}/oauth/callback` + REST). Ne dashboard UI.
- Vault: jen přes `app.vault_deps.brain_vault(mode=…)` — nikdy přímý `open_vault` z tools/rest.
- `GIT_VAULT_PUSH=1` povinné; mutate bez úspěšného push → 503.

Build context Coolify: **`vps/`** (Dockerfile `COPY second-brain-hub/lib/` + `second-brain-brain/app/`).

Lokálně:

```bash
cd vps
export BRAIN_ALLOW_NO_PUSH=1 GIT_VAULT_ROOT=/path/to/vault PYTHONPATH=second-brain-brain:second-brain-hub/lib
uvicorn app.main:app --reload --app-dir second-brain-brain
```
