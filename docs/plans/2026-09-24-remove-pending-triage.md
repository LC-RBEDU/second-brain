# Plán: Odstranit mrtvou PENDING / cron triáž

> Verze po kritice kolo 3 (NEW-1…7 + C1–C5). Architekt generace 1, kolo 4.

## Zadání a požadavky

| R# | Požadavek |
|---|---|
| R1 | Chat `agenda-triage` BATCH+DEEP; PENDING pryč odevšad (kód, vault, skills, rules, agent docs) |
| R2 | Smazat `triage_llm_run.py` + zmínky |
| R3 | Smazat `triage_run.py` pending-batch writer |
| R4 | Ponechat `lib/triage_{email_actionable,slack_relevance,complexity}.py` + `cron/triage_commitments.py` + testy |
| R5 | `inbox_inventory` → `lib/inbox_scan.iter_inbox_items` |
| R6 | Reminders-Pending / Lessons-Pending NESAHAT |
| R7 | priority-review: zrušit export do Triage-Pending |
| R8 | Vault: smazat Triage-Pending; Applied = cold archive; žádný zápis nesmí složku znovu vytvořit |
| R9 | F4: smazat cron soubory i s uncommitted diffem; ponechat email-actionable + `:gear:`; inbound B6/B7 cron **superseded v inbound plánu** → chat-only |
| R10 | Gate pytest; deploy Coolify hub; RBU FE/API netýká se |

## Předpoklady

A1 Applied ponechat · A2 Pending smazat vč. assistant-inbox + priority-review · A3 priority export zrušit · A4 `_open_pending_source_files` smazat · A5 jen inbox_scan helpers · A6 Dockerfile bez cursor-agent · A7 CURSOR_API_KEY secret nechat · A8 inbound ledger uzavřít + B6/B7 superseded v inbound `.md` · A9 triage_commitments ponechat · A10 QA nikdy nespouštět live inventory (purge maže sent) · A11 `--dry-run` inventory mimo scope

## Návrh F#

| F# | Obsah |
|---|---|
| F1 | `lib/inbox_scan.py` + `tests/test_inbox_scan.py` |
| F2 | `inbox_inventory.py` → `iter_inbox_items` z `inbox_scan`; **odstranit** filtr přes `_open_pending_source_files` (pořadí F1→F2→F4) |
| F3 | `weekly_summary` / `next_task_id` bez Pending; **`smoke_drive_io.py`**: cesta `00-System/_smoke/_smoke_{stamp}.json` (NE Triage-Pending) |
| F4 | Smazat `cron/triage_run.py` + `cron/triage_llm_run.py` (+ uncommitted diff) |
| F5 | `deploy/crontab` + **`deploy/crontab.example`**: pryč `triage_run` / `triage_llm_run`; inventory-only; Dockerfile bez cursor-agent |
| F6 | Full scrub (chat BATCH/DEEP only; ID ceiling bez Pending): skills `agenda-triage` + `agenda-priority-review`; `slack-inbox-triage.mdc` (globs); `second-brain-bootstrap.mdc`; `agent-bootstrap.md`; `install_agenda_skills.sh`; `docs/claude-project-instructions.md`; root + hub `README.md`; **vault Memory:** `Jak čtu vault MrLUC.md`, `agenda-system.md`, `procesy-mrluc.md`, `agenda-skill-cheatsheet.md`; **vault Templates:** `agenda-system.md`, `id-generation-spec.md`, `task-convention.md`, `konvence-a-slovnik.md`. Cold archive (weekly drafty, Triage-Applied, sync historie) nechat. |
| F7 | Hub README; inbound ledger abandoned; **inbound plán** `2026-09-24-inbound-email-actionable.md`: B6/B7 označit superseded → chat-only (`agenda-triage` + `lib/triage_email_actionable`) |
| F8 | Vault: `ls` Triage-Pending → smazat contents vč. assistant-inbox + priority-review JSON; NESAHAT Reminders/Lessons; Applied cold archive |
| F9 | pytest → commit (email-actionable + gear + remove-pending v jednom nebo dvou commit-ech dle diff state) |
| F10 | push → Coolify deploy → T4 (bez live inventory) |

## B#

| B# | Kontrakt |
|---|---|
| B1 | image bez `triage_run` / `triage_llm_run` |
| B2 | crontab (+ example) jen inventory (+ ostatní non-triage) |
| B3 | `inbox_inventory` importuje `inbox_scan`, bez pending filter |
| B4–B5 | inventory skip README/ZPRACOVÁNO |
| B6 | weekly bez `count_pending` / Triage-Pending |
| B7 | `next_task_id` bez Pending |
| B8 | skill jen B/D/R (žádné PENDING / schvál pending) |
| B9 | priority-review bez exportu do Triage-Pending |
| B10 | vault bez open Triage-Pending (Applied OK) |
| B11 | `smoke_drive_io` píše do `00-System/_smoke/…`, **ne** Triage-Pending |
| B12 | Dockerfile bez cursor-agent |
| B13 | heuristiky green; ne revert email-actionable / `:gear:` |
| B14 | rules + agent docs scrub (bootstrap, claude-project-instructions, README, vault Memory/Templates výše) — žádná live cesta cron→Triage-Pending |
| B15 | zákaz live `inbox_inventory` v QA |

## T#

| T# | Gate |
|---|---|
| T1 | `pytest tests/test_inbox_scan.py` (+ regression email/gear/commitments) |
| T2 | rg deny: `triage_run` / `triage_llm_run` / `Triage-Pending` v cron, crontab, crontab.example, smoke_drive_io, skills, rules, docs/claude*, root+hub README (mimo Applied / historické sync poznámky / tento plán) |
| T3 | rg assert: `inbox_scan` import v inventory; smoke path `_smoke` |
| T4 | post-deploy: image `ls`/`grep` bez triage_*_run; import `inbox_scan` |
| T5 | = T1 + T4 only (žádný live inventory) |
| T6 | deny jen **Triage** pending: `Triage-Pending`, `agenda-triage` PENDING mód, „schval pending **triáž**“ / cron→Pending. **Výjimka:** `Lessons-Pending` / `Reminders-Pending` + `agenda-lessons` „schval pending“ (R6) |
| T7 | vault: Triage-Pending prázdná/smazaná; Reminders/Lessons existují |
| T8 | full hub pytest |
| T9 | rg: žádný import smazaných modulů; smoke bez `Triage-Pending` |

## C# / NEW → vyřešeno v tomto plánu

| ID | Stav | Oprava |
|---|---|---|
| C1–C5 | ano | kolo 1–2 |
| NEW-1 | ano | B11/F3: smoke → `00-System/_smoke/` |
| NEW-2 | ano | F6: claude-project-instructions + README scrub + T2/T6 |
| NEW-3 | ano | F7: inbound plán B6/B7 superseded |
| NEW-4 | ano | F5: crontab.example |
| NEW-5 | ano | F2: drop pending filter; F1→F2→F4 |
| NEW-6 | ano | F6/B14: vault Memory + Templates scrub |
| NEW-7 | ano | T6 zúžen — výjimka Lessons-/Reminders-Pending |

## Otevřené otázky (default OK)

Applied cold archive · dry-run inventory ne teď · CURSOR secret nechat · inbound B6/B7 supersede v plánu
