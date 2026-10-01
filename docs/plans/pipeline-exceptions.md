# Výjimky z pipeline subagentů

Zapisuje agent při každém vynechání pipeline (pravidlo `subagent-pipeline`, hook `pipeline_gate`). Povolené výjimky: typo, copy, čistě docs / text skillu nebo pravidla, jednořádkový fix s jasnou příčinou, jednorázový skript, uživatel řekl „bez agentů“.

| Datum | Soubory | Výjimka | Kdo rozhodl |
|---|---|---|---|
| 2026-09-25 | Ad-hoc `Allfred_reporty EDU/allfred-expenses-fy2026/*.gs` (mimo SECOND_BRAIN git) + vault AF33 | Změna kódu mimo `vps/second-brain-hub/` a mimo `scripts/` SECOND_BRAIN; plná architect↔critic pipeline na Ad-hoc GAS neběží. Review+QA na žádost uživatele přes rbu-diff-reviewer / rbu-qa-verifier. | agent (+ uživatel: povinný review+QA) |
| 2026-09-25 | scripts/slack_send_message.py | `--thread-ts` (odpověď do vlákna); drobná feature | agent |
| 2026-10-01 | ŠABLONY/n8n/gmail-starred-to-inbox-{personal,workspace}.json + live n8n | uživatel: rovnou bez rbu pipeline, s testem | uživatel |
| 2026-10-01 | ŠABLONY/n8n error→Slack + live | uživatel: live rovnou (všechna workflow, C0C5VRU59UZ, 1×/10min) | uživatel |
| 2026-10-01 | Coolify→Slack channel C0C5VRU59UZ errors/warnings only | uživatel: live rovnou | uživatel |
| 2026-10-01 | scripts/fio_import_personal.py + .cursor/rules/fio-personal-payments.mdc | utility skript (Fio personal import, nemění vault) + čistě rule text; jednorázový upload Twisto | agent |
| 2026-10-01 | today_priority + build_agent_context + Bases + skills (deadline vs review_deadline) | uživatel: 1–4 ano, 5 rovnou | uživatel |
