---
name: agenda-reply
description: >-
  Návrh odpovědi na inbound e-mail nebo Slack ve vaultu. Gmail = existující
  draft (neposílat). Slack = pointer v 01-INBOX/drafts plus text, který
  uživatel odešle sám. Triggers: odpověz, draft odpovědi, agenda-reply.
---

# Agenda reply

Hub už smí založit Gmail draft a pointer. Tyhle kroky jsou pro ruční úpravu v Cursoru nebo Coworku. **Neodesílej.** `00-System/send-policy.yaml` je `draft_only`.

## Než napíšeš

1. Přečti zdroj (`source_rel` v pointeru, nebo soubor v `01-INBOX/email/` / `slack/`).
2. Celé vlákno, ne jen poslední větu. U mailu `gmail_thread_id`.
3. `00-System/reply-playbook.md`, `05-RESOURCES/lide/` protistrany, writing-style.
4. Když `status: handled_by_user`, draft nepiš — už je odpovězeno.

## Výstup

- Mail: uprav Gmail draft (stejné vlákno). Do pointeru nic nového, pokud text v Gmailu stačí.
- Slack: uprav `## Návrh` v `01-INBOX/drafts/`. Uživatel to pošle sám. API drafty ve Slacku nejsou.
- Externí účastník zápisu schůzky: jen Gmail draft.

## Po úpravě

Když se styl má opakovat, jeden řádek do `00-System/reply-playbook.md`. Ne do tohoto SKILL.md.

Žádný nový task, pokud o to uživatel neřekne.
