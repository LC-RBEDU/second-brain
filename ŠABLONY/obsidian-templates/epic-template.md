---
id: {{ID}}
type: epic
title: "{{Title}}"
project: "[[{{HubFilename}}]]"
slug: {{slug}}
aliases: [{{ID}}]
status: Next
parent:
focus:  # volitelné — téma týdne (ISO); ICE na epicu ne
agent: none
deadline:  # jen reálný externí závazek
review_deadline:  # jen když není deadline — kdy se k epicu vrátím (měkké)
created: {{date}}
updated: {{date}}
materials: []
source: manual
company_priorities: []  # volitelné [[CP8 — …]]; prázdné OK
blocked_by: []
---

# {{ID}} — {{Title}}

**Z:** roadmap / charter
**Detail:** Výsledek na měsíce — ne doručení v jednom sprintu. Děti = `type: story` s `parent: '[[{{ID}} — {{Title}}]]'`. ID epicu má tvar `<PREFIX>-E<N>`, story `<PREFIX>-S<N>`.

## Definition of done (epic)
- [ ] …

## Stories

Otevřené story jsou soubory s `parent` na tento epic. Embed Bases se nepřidává.

## Poznámky / log
- {{date}}: Založen epic.
