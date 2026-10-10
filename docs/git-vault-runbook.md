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

- Žádný lokální zápis do git klonu (`build_agent_context`, `schedule_reminder` schedule/cancel → exit ≠0).
- Snapshot píše jen VPS; Mac `git pull`.
- Lidský zápis = GitHub web UI PR → Merge.

## Rollback ≤24 h

Coolify: `VAULT_BACKEND=drive` + `CRONTAB_MODE=live` + `PAUSED=0`.
