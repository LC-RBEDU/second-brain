# Pipeline: SB operační model F2

Stav: AWAITING_USER (z: grill)
Plán: docs/plans/2026-10-10-sb-operacni-model-f2.md
Schvalování plánu uživatelem: ne
Architekt: 69a6222d… · otevření #1 · k=1/3 · r=1/3
Šťoural: ec5513b7… · kolo grill g=1 · POTŘEBUJE ODPOVĚDI (Q1–Q4 BLOKUJÍCÍ)
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main před pipeline): ca95c2f1388c1b7605c27ef9113219821e58a1f1 · Kódový SHA: — · Review SCHVÁLENO na: — · QA PASS na: — · TESTER PASS na: přeskočeno (profil SECOND_BRAIN)
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
- Fail-path Grok plugin: Claude+Cursor first (F0). Grok private plugin smoke před F2 není v ledgeru jako PASS → MVP předpoklad = Claude + Cursor; Grok opt-in po smoke.
- F1–F2: n8n INBOX zůstává vypnuté; stale Slack INBOX OK do F3.
- Schvalování plánu: ne (uživatel neřekl `se schválením`).

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-10-10 | PLAN | 69a6222d… | draft plán | — | F2 Brain API + plugin SSOT |
| 2 | 2026-10-10 | GRILL | ec5513b7… | POTŘEBUJE ODPOVĚDI | — | Q1–Q4 BLOKUJÍCÍ; Q5–Q8 NEBLOKUJÍCÍ defaulty |
| 3 | 2026-10-10 | AWAITING_USER | — | grill | — | Goal paused; čeká odpovědi Q1–Q4 |

## Grill Q (čeká odpověď)

BLOKUJÍCÍ (Šťoural doporučení →):
1. Remind tool F2 — **(a)** přidat schedule/cancel MCP
2. get_context stale — **(a)** sync rebuild pod flock
3. Cowork create_task — **(a)** rovnocenně Cursoru
4. T8 smoke vault — **(b)** oddělený WC / dry-run (ne live tip)

NEBLOKUJÍCÍ defaulty (A# pokud OK): Q5a+c allowlist; Q6 brain.redbuttonedu.cz; Q7 bez bulk FM; Q8 Brain retry 1–2× pak 503.

## Otevřené nálezy

| ID | Závažnost | Typ | Stav | Kolikrát |
|---|---|---|---|---|
