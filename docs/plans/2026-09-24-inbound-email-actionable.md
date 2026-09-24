# Plán: Inbound e-mail actionable → add_task (ne jen archiv)

> Retroaktivní kontrakt chování pro diff review. **PLAN ↔ CRITIC v této pipeline neproběhly** — implementace šla rovnou po zadání uživatele. Tento soubor = B#/T# odvozené ze zadání + decisions, aby reviewer měl proti čemu kontrolovat.

**Repo:** SECOND_BRAIN (hub + skill), ne RB Universe API.  
**Base:** `ee17b3da` (HEAD před touto změnou)

## Zadání uživatele (doslovně)

> Podívej se do konverzace 605e41ac… — řeším e-mail od Jany Kočové. Tento e-mail neměl skončit pouze v archivu, ale měl z něj vypadnout konkrétní úkol, totiž zaplatit daň… Uprav pravidla triáže tak, aby e-maily od konkrétních lidí, se kterými komunikuji a obsahují pro mě nějaký úkol, byly navrženy v triáži jako úkol a nepadaly pouze do archivu.

## Rozhodnutí

1. Třída chyby (ne jen DPH): inbound se splatností/platbou/žádostí o akci → vždy `add_task`.
2. Heuristika v hubu + skill `agenda-triage` + LLM prompt; lesson LL-2026-09-24 (vault, mimo git).
3. Silné signály (daň/splatnost/údaje k platbě) → task i bez karty v `lide/`.
4. Soft signály → task když známý kontakt NEBO `mailbox: personal`.
5. Bulk/noreply → archive přípustný.
6. `email/sent/` mimo scope (vlastní commitment path).
7. Cron: vždy `add_task` `agent: solo` (i s přílohami); LLM post-filter stejně.
8. Manuální triáž: email gate **před** complex/DEEP (skill Batch krok 3).

## Mimo rozsah

- Vytvoření OS11 / oprava Agent-Log (vault).
- Slack relevance (už existuje).
- `upload_personal_receipt` flow (doklad ≠ platba; skill jen upozorňuje).

## Chování B#

| ID | Chování |
|----|---------|
| B1 | Inbound e-mail (ne `email/sent/`) se **silným** signálem (daňová povinnost, DPH+splatnost, datum splatnosti, VS+platba, údaje k platbě, částka+splatnost) → `must_propose_task=True` (i bez known contact). |
| B2 | Soft signál + (e-mail v `lide/` NEBO personal mailbox / `sb-personal-*`) → `must_propose_task=True`. |
| B3 | From noreply/newsletter/bulk → `must_propose_task=False` i při silném textu. |
| B4 | `email/sent/` → funkce neaplikuje gate (False). |
| B5 | Ze „Datum splatnosti: D.M.YYYY“ vypočti `deadline_hint` ISO `YYYY-MM-DD`. |
| B6 | ~~`triage_run`: při True → vždy `add_task`…~~ **SUPERSEDED 2026-09-24** — cron pending writer odstraněn. Stejné chování v **chat** `agenda-triage` BATCH (gate před complex/DEEP) + `lib/triage_email_actionable.py`. |
| B7 | ~~Skill + LLM prompt; `triage_llm_run` post-filter…~~ **SUPERSEDED 2026-09-24** — `triage_llm_run` smazán. Chat-only: skill `agenda-triage` + `lib/triage_email_actionable`. |
| B8 | Platební `solo` task má v body částku / účet / VS / splatnost (pokud jsou v mailu). |

## Výkon P

| ID | Rozpočet |
|----|----------|
| P1 | Heuristika CPU-only regex na body; žádné síťové volání. Načtení `lide/*.md` jen když `lide_dir` předán (cron default = empty set → soft+no-lide fallback B2-alt). |

Pozn.: cron dnes nevolá `lide_dir` → spoléhá na silné signály + personal + soft empty-known fallback. To je záměr B1/B2 fallback.

## Testy T#

| ID | Test |
|----|------|
| T1 | Jana DPH fixture → True + deadline 2026-09-25 |
| T2 | Strong bez known → True |
| T3 | noreply + splatnost → False |
| T4 | sent/ → False |
| T5 | soft + known → True |
| T6 | FYI known bez akce → False |

## Soubory

- `vps/second-brain-hub/lib/triage_email_actionable.py` (new)
- `vps/second-brain-hub/tests/test_triage_email_actionable.py` (new)
- ~~`vps/second-brain-hub/cron/triage_run.py`~~ — removed 2026-09-24 (chat-only)
- ~~`vps/second-brain-hub/cron/triage_llm_run.py`~~ — removed 2026-09-24
- `ŠABLONY/skills/agenda-triage/SKILL.md`
- `.cursor/rules/lessons-learned.mdc` (situační řádek)
