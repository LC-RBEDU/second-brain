---
id: {{ID}}
type: story
title: "{{Title}}"
project: "[[{{HubFilename}}]]"
slug: {{slug}}
aliases: [{{ID}}]
status: Next  # Doing | Next | Backlog | Waiting | Done | Cancelled
parent: "[[{{EpicID}} — …]]"  # nová story má epic. Prázdný parent jen u epicu a u type task bez story.
focus:
agent: none
ice_i: 5
ice_c: 5
ice_e: 5
deadline:  # jen reálný externí závazek
review_deadline:  # jen když není deadline — kdy se k tomu vracím (měkké)
waitUntil:
created: {{date}}
updated: {{date}}
materials: []
source: manual
company_priorities: []  # volitelné [[CP8 — …]]; prázdné OK
blocked_by: []
---

<!-- Cancelled = už není potřeba / převzal to někdo jiný. Ne Done, a soubor nemazat —
     cron ho archivuje sám a ID zůstane obsazené. Detail: task-convention.md -->

# {{ID}} — {{Title}}

**Z:** …
**Detail:** …

## Operativní kroky
- [ ] **{{ID}}-1** …
- [ ] **{{ID}}-2** …

## Poznámky / log
- {{date}}: Založeno.

<!--
Nová story má parent na epic. Prázdný parent jen u epicu a u type task bez story.
Epic: použij epic-template.md. Brain při create zapíše ICE 5/5/5 a **ID-1**.
GitHub (RBU): commit "Closes {{ID}}-1 — popis" na větev dev.
-->
