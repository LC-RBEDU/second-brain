---
name: agenda-reply
description: >-
  On-demand odpověď: Gmail draft (nikdy send) nebo Slack text → poslat až po
  „pošli / ano“ jako Lukáš. Živé Slack vlákno zároveň do vaultu + triage preview.
  Triggers: odpověz, draft, pošli na Slack, agenda-reply.
---

# Agenda reply (on-demand)

Žádné automatické drafty ani Slack karty. Hub cron je nebere. Tyhle kroky jsou jen když Lukáš řekne „odpověz“ / „draft“ / „pošli“.

`00-System/send-policy.yaml` = `draft_only` pro Gmail. Slack send jen po výslovném potvrzení.

## Společné

1. Zdroj: soubor v `01-INBOX/email/` nebo `01-INBOX/slack/`, **nebo** živé Slack vlákno (permalink / kanál+thread_ts) přes Slack MCP.
2. Celé vlákno, ne jen poslední větu. U mailu `gmail_thread_id` + `mailbox` (`workspace` | `personal`).
3. `00-System/reply-playbook.md` (sekce Mail / Slack), `05-RESOURCES/lide/` protistrany, writing-style.
4. Po úpravě stylu, který se má opakovat: jeden řádek do playbooku (správná sekce). Ne do tohoto SKILL.md.

## Mail

1. Návrh textu podle playbooku Mail.
2. Založ **Gmail draft** přes MCP `user-google-workspace` (`draft_gmail_message`) do správného vlákna.
   - DoD: Workspace `lukas@redbuttonedu.cz`.
   - Osobní `lukas.cypra@gmail.com` jen pokud existuje druhý MCP server s tím účtem; jinak řekni, že osobní draft z Cursoru nejde.
3. **Nikdy neodesílej.** Žádný pointer do `01-INBOX/drafts/` (složka se nepoužívá).
4. Cowork: stejné — Gmail connector = Workspace; osobní účet nenapojuje (jeden konektor).

## Slack

1. Návrh textu podle playbooku Slack. **Ukaž text v chatu.**
2. Pošli **až** po „pošli“ / „ano“ / ekvivalent. Bez potvrzení neposílej.
3. Post jako Lukáš (user Slack / MCP s jeho účtem), ne bot, ne n8n.
4. **Vault ve stejném tahu** (i když Cowork archiv ještě neběžel):
   - Zapiš vlákno do `01-INBOX/slack/` ve tvaru Cowork archivu (frontmatter `channel_id`, `thread_ts`, `kind`).
   - Dedup: jeden soubor na `channel_id` + `thread_ts` (večerní archiv nesmí udělat druhý).
   - Pak zpracuj jako položku `agenda-triage`: preview, kterých tasků/projektů se týká.
   - Zápis do tasku/hubu **až po schválení preview**. Když se netýká ničeho: řekni to a jen archivuj.

## Zakázané

- Auto-karty v `_lukas_ai-comm`, pointery v `01-INBOX/drafts/`, `assistant_ingest`, n8n Odpověz.
- `drafts.send` / `messages.send` u Gmailu.
- Tiché zápisy do tasků bez triage preview.
