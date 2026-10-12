# Plán: Evening L1 digest → digests/ + Saturnin (k=2, r=2+restore)

## Zadání a požadavky

R1 — Vault (git): souvislosti e-mail/Slack/… k otevřeným úkolům + nabídka založit úkol.  
R2 — Shrnutí ~18:00 Po–Pá.  
R3 — Jen Saturnin (ne Slack DM).  
R4 — L1 přes Brain (ne hvězdička n8n).  
R5 — MD v `00-System/digests/YYYY-MM-DD-evening-l1.md`; bez tichého logu do tasků.  
R6 — Evening = **stejný** crontab řádek `0 18 * * 1-5 … proactivity_dispatch.py --trigger evening` (`deploy/crontab` L71). **Crontab se nemění.** Evening větev kódu = digest (místo starého nudge).  
R7 — 0 propose/apply/auto-create.  
R8 — Morning/due beze změny.  
R9 — `--dry-run` = 0 write, 0 Grok, 0 CAS. Brain GET jen na first/`--force` rebuild větví (ne při B2 skip ani B2b Saturnin-only).  
R10 — `deliver: OK` → skip; ≠OK → Saturnin-only; `--force` → full rebuild i při OK.  
R11 — Deploy hub Coolify.  
R12 — Match všechny Brain sources.  
R13 — MD strukturovaný; Saturnin = soft-truncate MD (~28k).  
R14 — Pool = všechny open excl. epic; display 40/40/8 + truncated.  
R15 — Match = ID word-boundary + title tokeny ≥3 + body tokeny ≥4 z 3072 B.  
R16 — Wire Gmail = ne.

## Předpoklady

A1 `lib/evening_l1_digest.py` + evening větev `proactivity_dispatch.py` · A3/A30 `GET {BRAIN_PUBLIC_URL}/v1/triage/candidates` + `Authorization: Bearer {BRAIN_SERVICE_TOKEN}` timeout **120s** mimo vault · tick budget **&lt;180s** (Brain≤120 + vault + Grok) · A4 partial `error_reason` · A9 missing env/HTTP fail → total degrade **s MD** · A5 `send_grok_chat` · A6 digests path · A8 Tester skip · A10 FAIL exit 0 · A11 CTA · A13 no epic · A14 full pool · A15/A25/A27–A29 deliver OK|FAIL · A16 disclaimer · A17 path heads = match-input via vault `read_text` · A18 soft 28k · A19 git · A20 empty day · A21 `iter_active_tasks` ∩ ¬terminal ∩ ¬epic · A22 multi-hit · A23 evening nevolá `dispatch_proactivity` (crontab stejný) · A26 hybrid later · A31 PAUSED · A32 HTTP mimo flock + CAS · A33 body 3072 B · A34 gmail subject · A35 CLI `--force` · A36 ID `(?<![A-Za-z0-9])id(?![A-Za-z0-9])` casefold · A37–A41 Brain/deliver/Saturnin/env/force.

### Haystack per source (R12)

| Source | Haystack pro match |
|---|---|
| `live_slack` | `text` (+ permalink jen link) |
| `gmail` | `subject` (=snippet alias) |
| `slack_dump` / `email_dump` / `daily` / `sembly` | vault `read_text(path)` head ≤8 KiB (stem+body); **všechny** path z Brain odpovědi (ne cap 30/120 — P dle reality) |

## Návrh evening

```
PAUSED → exit 0
peek deliver (read-only)
exists && deliver==OK && !force → skip
exists && deliver≠OK && !force:
  if dry-run: return          # 0 Grok, 0 CAS
  Grok(body) outside + CAS patch deliver
  return
# first run (no file) OR --force:
Brain GET outside
vault read-only: pool + enrich (read all dump paths) + match + render MD string
if dry-run: log counts; return   # 0 write, 0 Grok  (R9/B4)
vault: write MD (deliver absent)
Grok outside
vault: CAS patch deliver OK|FAIL
```

### Match
1. ID: casefold word-boundary (A36); S12 ≠ S120.  
2. Title: tokens `[a-z0-9á-ž]+` len≥3 casefold, minus stop-list; hit ≥1 token ⊆ haystack.  
3. Body: first 3072 B; tokens len≥4; hit ≥1.  
4. Multi-hit OK (≤8 shown). Display 40 matched / 40 unmatched + truncated.

### Deliver
| Stav | Akce |
|---|---|
| **soubor neexistuje** | full rebuild (first run) |
| exists + `deliver` FAIL/missing + !force | Saturnin-only + CAS (B2b) |
| exists + `deliver` OK + !force | skip (B2) |
| exists + `--force` (jakýkoli deliver) | full rebuild (B3) |
| Grok fail | `deliver: FAIL`, exit 0 |

### MD outline
YAML FM · Stav zdrojů · Matched · Unmatched/CTA · Prázdný den. Saturnin = soft-truncated MD.

## B#

| B# | Vstup | Výsledek | T# |
|---|---|---|---|
| B1 | first, Grok 200 | MD + deliver OK + Saturnin | T1 |
| B2 | exists OK, no force | 0 write, 0 Grok | T2 |
| B2b | exists FAIL/absent | Saturnin-only + patch | T3 |
| B3 | `--force` + OK | full rebuild + Grok | T4 |
| B4 | `--force --dry-run` (nebo first, soubor není) | Brain ano; 0 write; 0 Grok | T5 |
| B4b | exists FAIL/absent + dry-run (no force) | 0 Brain, 0 write, 0 Grok, 0 CAS | T5b |
| B5 | morning/due | stávající CTA; 0 digest | T6 |
| B6 | whole ID as word | hit | T7 |
| B6n | S120 in text, pool has S12+S120 | only S120 | T8b |
| B7 | title token ≥3 | hit | T7 |
| B8 | body token in 3072 B | hit/no-hit by cap | T8 |
| B9 | no overlap | unmatched + CTA | T7 |
| B10 | Grok fail | deliver FAIL, exit 0 | T3 |
| B11 | crontab L71 | unchanged; evening branch = digest | T6 |
| B12 | MD >28k | soft truncate | T9 |
| B13 | light miss | banner vault_scan; pool iter | T10 |
| B14 | epic | excluded | T7 |
| B15 | disclaimer | in MD | T1 |
| B16 | 0 candidates | short MD + Grok | T11 |
| B17 | >40/>40/>8 | display caps + truncated | T12 |
| B18 | evening | no dispatch_proactivity | T6 |
| B19 | gmail_api_not_wired + slack | partial; slack matches | T13 |
| B20 | missing Brain env / HTTP fail | total MD (ne-dry), not silent skip | T11 |
| B21 | PAUSED | 0 write, 0 Grok, exit 0 | T14 |
| B22 | CAS fail | no false OK; exit 0 | T15 |
| B23 | gmail | match text = subject | T13 |
| B24 | dump/sembly path | haystack = vault file head, not path-only | T13b |

## P
Tick **&lt;180s** · Brain timeout 120s · 0–1 Grok · ≤3 vault sessions · ~160×3KiB · path heads = všechny z Brain (8 KiB/file)

## T#
T1–T15 + T5b (B4b) + T8b + T13b · T16 Coolify `--force --dry-run --trigger evening` · T17 TESTER skip  
Gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q`

## Pořadí
F1 lib+tests → F2 evening branch+`--force` (crontab beze změny) → F3 docs → F4 gate → F5 push → F6 QA → F7 TESTER skip

## C# / NEW uzavřeno
C1–C7 · force · Brain auth · deliver · MD outline · haystack dumps (B24) · crontab = keep L71
