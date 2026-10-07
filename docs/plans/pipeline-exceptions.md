# Výjimky z pipeline subagentů

Zapisuje agent při každém vynechání pipeline (pravidlo `subagent-pipeline`, hook `pipeline_gate`). Povolené výjimky: typo, copy, čistě docs / text skillu nebo pravidla, jednořádkový fix s jasnou příčinou, jednorázový skript, uživatel řekl „bez agentů“.

| Datum | Soubory | Výjimka | Kdo rozhodl |
|---|---|---|---|
| 2026-10-07 | `ŠABLONY/skills/rbe-writing-style/`, `scripts/install_agenda_skills.sh` | čistě text skillu — port z Claude ZIP; jen firemní/veřejná audience, ne chat/git/SB | agent (+ uživatel) |
| 2026-10-07 | `ŠABLONY/skills/agenda-strategy-dialog/SKILL.md` | čistě text skillu — sjednocení s verzí z Claude Team (širší trigger, hranice vůči grilling) | uživatel |
| 2026-10-07 | `ŠABLONY/skills/tymovy-disk/SKILL.md`, `ŠABLONY/skills/tymovy-disk/templates.md` | čistě text skillu — úkoly/ file-per-task (0.6); grill + architect hotové, uživatel: pusť se do toho | agent (+ uživatel) |
| 2026-10-06 | `ŠABLONY/skills/tymovy-disk/`, `ŠABLONY/cursor-rules/no-agents-md-init.mdc`, `scripts/install_agenda_skills.sh`, `docs/claude-project-instructions.md`, `docs/rbu-universe-cursor-rule-install.md` | čistě text skillu a pravidla — skill týmového disku, výjimka AGENTS.md jen na sdíleném disku | agent (plán schválil kritik kolo 5) |
| 2026-10-06 | `scripts/lib/agent_write_guard.py`, `scripts/tests/test_agent_write_guard.py`, návod ve vaultu | uživatel: varianta C, vzdálený režim jen nový daily; přesný patch | uživatel |
| 2026-10-05 | `scripts/lib/agent_write_guard.py`, `scripts/agent_write_guard.py`, `scripts/tests/test_agent_write_guard.py` | uživatel dodal přesný patch: schedule + čitelná složka = morning_schedule bez ohledu na desktop_open, sladění s už schváleným návodem | uživatel |
| 2026-10-05 | `ŠABLONY/skills/mrluc-loader/SKILL.md`, `scripts/install_external_skills.sh`, `docs/plans/pipeline-exceptions.md` (+ RBU: `rbu-stoural` agent, `subagent-orchestration`, `rbu-pipeline`, install.sh, `subagent-pipeline.mdc`) | čistě docs / text skillu a agentů — n8n-io skills + Šťoural (grill-me) před kritikem v /rbu-pipeline; bez app runtime | agent (uživatel: IAD-S8) |
| 2026-10-05 | `scripts/lib/agent_write_guard.py`, `scripts/agent_write_guard.py`, `scripts/tests/test_agent_write_guard.py`, návod ve vaultu, `docs/claude-project-instructions.md` | jasná příčina: výchozí `today` bylo zmrzlé na 2026-10-04 (Cowork ověřil `deny_old_bus_day`); tenký CLI k témuž modulu; srovnání textu projektu s návodem. Pipeline už DONE, tohle je oprava po ní. | agent |
| 2026-09-25 | Ad-hoc `Allfred_reporty EDU/allfred-expenses-fy2026/*.gs` (mimo SECOND_BRAIN git) + vault AF33 | Změna kódu mimo `vps/second-brain-hub/` a mimo `scripts/` SECOND_BRAIN; plná architect↔critic pipeline na Ad-hoc GAS neběží. Review+QA na žádost uživatele přes rbu-diff-reviewer / rbu-qa-verifier. | agent (+ uživatel: povinný review+QA) |
| 2026-09-25 | scripts/slack_send_message.py | `--thread-ts` (odpověď do vlákna); drobná feature | agent |
| 2026-10-01 | ŠABLONY/n8n/gmail-starred-to-inbox-{personal,workspace}.json + live n8n | uživatel: rovnou bez rbu pipeline, s testem | uživatel |
| 2026-10-01 | ŠABLONY/n8n error→Slack + live | uživatel: live rovnou (všechna workflow, C0C5VRU59UZ, 1×/10min) | uživatel |
| 2026-10-01 | Coolify→Slack channel C0C5VRU59UZ errors/warnings only | uživatel: live rovnou | uživatel |
| 2026-10-01 | scripts/fio_import_personal.py + .cursor/rules/fio-personal-payments.mdc | utility skript (Fio personal import, nemění vault) + čistě rule text; jednorázový upload Twisto | agent |
| 2026-10-01 | today_priority + build_agent_context + Bases + skills (deadline vs review_deadline) | uživatel: 1–4 ano, 5 rovnou | uživatel |
| 2026-10-04 | scripts/tests/test_wiki_firemni_priority_bundle.py | čistě text skillu: test jen zrcadlí přejmenované nadpisy v create-bundle (Definition of Done, Stav plnění jako H2, Přehled milníků), žádná nová logika | agent |
