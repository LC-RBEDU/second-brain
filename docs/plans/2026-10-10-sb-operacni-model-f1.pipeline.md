# Pipeline: SB operační model F1

Stav: DONE
Plán: docs/plans/2026-10-10-sb-operacni-model-f1.md
Schvalování plánu uživatelem: ano
Architekt: hlavní · k=2/3, r=3/3
Šťoural: 49b18383… g=5 · HOTOVÝ GRILL
Kritik: 169843ee… · SCHVÁLENO
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 3/5 · kola QA 1/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main před pipeline): 674a82a9373cc02a790e24a2ecf48222ccd61719 · Kódový SHA: 9ed0da32b1bffdbfe9f6314c42bce6b8e0a417f4 · Review SCHVÁLENO na: de7266c1d4fb4cc4a8f124699f717435744ce42a (+ hotfix 9ed0da3) · QA PASS na: 9ed0da32b1bffdbfe9f6314c42bce6b8e0a417f4 · TESTER PASS na: přeskočeno (profil SECOND_BRAIN)
Plán schválen uživatelem: ano (B1–B25) 2026-10-10
Goal: complete
Profil: SECOND_BRAIN

## Gate důkazy

- pytest: **341 passed** (`vps/second-brain-hub/tests` + `scripts/tests`)
- Review: SCHVÁLENO (5c6998a5…) na de7266c; hotfix 9ed0da3 = `vault_path` NameError
- Coolify image: `…:9ed0da32b1bffdbfe9f6314c42bce6b8e0a417f4`
- B1 smoke: `agent-context: projects=15 open=188 done7d=17 upcoming=4 → drive://00-System/agent-context.json`
- A33: `supercronic … /app/crontab` (live); reminders + slack_poll job succeeded
- Cutover F1-e…h **hotov** 2026-10-10: `VAULT_BACKEND=git` + `PUSH=1` + live crontab; Mac `~/GitHub/second-brain-vault`
- **A17 ruleset — jediný otevřený blocker cíle:** Free private → 403 Pro (ověřeno opakovaně). Soft control hotov. Po Pro na `LC-RBEDU`: `bash scripts/vault_apply_ruleset_a17.sh` → teprve pak goal complete.

## Průběh (zkráceně)

| # | Stav | Verdikt |
|---|---|---|
| … | PLAN→CRITIC→USER B# | SCHVÁLENO |
| 26–31 | IMPLEMENT→REVIEW×3 | SCHVÁLENO de7266c |
| 32 | QA | FAIL root_id |
| 33 | IMPLEMENT hotfix | 9ed0da3 |
| 34 | QA | **PASS** |
| 35 | TESTER | přeskočeno |
| 36 | DONE | |

## Poznámka

Cutover živého vaultu (F1-e…h, **SB15-2**) = **hotovo** 2026-10-10 — [docs/git-vault-runbook.md](../git-vault-runbook.md).
