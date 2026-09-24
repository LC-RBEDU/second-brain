# Pipeline: Odstranit mrtvou cron/PENDING triáž

Stav: IMPLEMENT  
Plán: docs/plans/2026-09-24-remove-pending-triage.md  
Schvalování plánu uživatelem: ne (implicitně přes „vyhoď… rbu pipeline“)  
Architekt: k=1 r=4 · Kritik plánu: SCHVÁLENO (kolo 4)  
Počítadla: návraty PLAN 3/3 · REVIEW 0/5 · QA 0/5 · ENV 0/2  
Base: ee17b3da (+ uncommitted email-actionable + gear)  
Goal: bez goalu

## Zadání (doslovně)

> ok, vyhoď vše, co je vypnuté a nefunkční. očividně mi nejvíc sedí vyvolání triáže z chatu, pending nepoužívám takže vyhoď z vaultu, VPS, kódu odevšad.... a protože je to změna v kódu, chci použít rbu pipeline a agenty architekt/kritik atd.

## Rozhodnutí

1. Live = chat agenda-triage BATCH/DEEP. PENDING pryč.
2. Smazat triage_llm_run + triage_run.
3. Nechat lib/triage_* + triage_commitments + email-actionable + :gear:.
4. Reminders-/Lessons-Pending NESAHAT.
5. QA nikdy live inbox_inventory (purge).

## Průběh

| # | Čas | Stav | Agent | Verdikt |
|---|-----|------|-------|---------|
| 1–4 | 2026-09-24 | PLAN | architect↔critic | SCHVÁLENO kolo 4 |
| 5 | 2026-09-24 | IMPLEMENT | parent | F1–F10 |

## Otevřené nálezy

(žádné — plán SCHVÁLENO)
