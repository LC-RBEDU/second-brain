---
id: {{ID}}
type: story
title: "{{Title}}"
project: "[[{{HubFilename}}]]"
slug: {{slug}}
aliases: [{{ID}}]
status: Next
parent:  # "[[RBU23 — …]]" nebo prázdné (standalone / flat projekty: type task)
focus:
agent: none
ice_i: 5
ice_c: 5
ice_e: 5
deadline:
waitUntil:
created: {{date}}
updated: {{date}}
materials: []
source: manual
blocked_by: []
---

# {{ID}} — {{Title}}

**Z:** …
**Detail:** …

## Operativní kroky
- [ ] **{{ID}}-1** …
- [ ] **{{ID}}-2** …

## Poznámky / log
- {{date}}: Založeno.

<!--
Mimo hierarchy projekty (ne RBU): nastav type: task a parent smaž.
Epic: použij epic-template.md — ICE/focus sem nepatří.
GitHub (RBU): commit "Closes {{ID}}-1 — popis" na větev dev.
-->
