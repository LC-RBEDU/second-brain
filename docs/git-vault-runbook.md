# Git vault runbook (F1)

Plán: [docs/plans/2026-10-10-sb-operacni-model-f1.md](plans/2026-10-10-sb-operacni-model-f1.md)

## Flag matice

| Fáze | VAULT_BACKEND | PAUSED | CRONTAB_MODE | DRY_RUN | PUSH |
|---|---|---|---|---|---|
| F1-d (deploy kódu) | drive | 0 | live | — | — |
| F1-e / f-mid | drive | 1 | pause | — | — |
| F1-f end | **git** | 1 | pause | — | — |
| F1-g smoke | git | 0 | pause | 1 | — |
| F1-h live | git | 0 | live | 0 | 1 |

## Cutover stav (2026-10-10)

**Hotovo:** F1-e → F1-h live.

| Položka | Stav |
|---|---|
| Import tip | `7aded9a` (initial) → live tip `84ba887` (+ další hub commits) |
| Repo | `https://github.com/LC-RBEDU/second-brain-vault` (private) |
| Coolify WC | host bind `/data/second-brain-vault` → `/data/vault` |
| Deploy key | `coolify-second-brain-hub` (read-write) + `openssh-client` v image |
| Push | `git -c push.ff=only push` (Debian 2.39 nemá `push --ff-only`) |
| Mac clone | `~/GitHub/second-brain-vault` — pull/read only |
| Ruleset A17 | **otevřený dluh** — Free private → 403 Pro. Soft: deploy key write + README Write policy + `.github/PULL_REQUEST_TEMPLATE.md`. Hard ruleset až Pro/Team. |

## Tooling před importem

```bash
# Inventář blob / LFS / Drive-only (B9)
python3 scripts/vault_import_inventory.py /path/to/OBSIDIAN --tsv /tmp/vault-inv.tsv

# Secrets hard gate (B21) — fail = neimportovat
bash scripts/vault_secrets_scan.sh /path/to/OBSIDIAN
```

## Cutover (stručně)

1. Freeze: Sync/Drive writer/n8n off; `PAUSED=1` + `CRONTAB_MODE=pause`.
2. Secrets scan hard gate → založit `LC-RBEDU/second-brain-vault` + ruleset (PR humans, deploy-key bypass).
3. Mac one-shot import; revoke Mac push; Coolify deploy key.
4. Volume `/data/vault` → `git clone` + LFS; `HEAD` == import tip.
5. Coolify `VAULT_BACKEND=git` (ještě PAUSED).
6. F1-g: `PAUSED=0` + `DRY_RUN=1` + manuální one-shot (ne slack_poll / reminders).
7. F1-h: `CRONTAB_MODE=live` + `DRY_RUN=0` + `PUSH=1`.
8. Mac: clone `~/GitHub/second-brain-vault`; skills = pull/read only.

## Mac

- Klon: `~/GitHub/second-brain-vault`
- Env: `export SECOND_BRAIN_VAULT="$HOME/GitHub/second-brain-vault"` (volitelně `SB_VAULT_PATH` stejná hodnota)
- Žádný lokální zápis do git klonu (`build_agent_context`, `schedule_reminder` schedule/cancel → exit ≠0).
- Snapshot píše jen VPS; Mac `git pull`.
- Lidský zápis = GitHub web UI PR → Merge (ruleset až Pro).
- Drive Desktop `…/SECOND_BRAIN/OBSIDIAN/` už **není** SSOT — po cutoveru jen legacy mirror.

## Coolify env (live)

| Key | Value |
|---|---|
| `VAULT_BACKEND` | `git` |
| `VAULT_WRITERS_PAUSED` | `0` |
| `CRONTAB_MODE` | `live` |
| `GIT_VAULT_ROOT` | `/data/vault` |
| `GIT_VAULT_REMOTE` | `git@github.com:LC-RBEDU/second-brain-vault.git` |
| `GIT_VAULT_BRANCH` | `main` |
| `GIT_VAULT_DRY_RUN` | `0` |
| `GIT_VAULT_PUSH` | `1` |
| `GIT_SSH_COMMAND` | `ssh -i /root/.ssh/sb-vault-deploy -o IdentitiesOnly=yes -o UserKnownHostsFile=/tmp/sb_known_hosts -o StrictHostKeyChecking=accept-new` |

## Rollback ≤24 h

Coolify: `VAULT_BACKEND=drive` + `CRONTAB_MODE=live` + `PAUSED=0`.
