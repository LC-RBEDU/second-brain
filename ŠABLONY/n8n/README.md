# n8n workflows pro Agenda systém

Workflows. Každý JSON je importovatelný do n8n.

## Git vault — INBOX (second-brain-vault)

**Vault INBOX:** git `~/GitHub/second-brain-vault/01-INBOX/`. n8n writers do té složky jsou off.

| Podsložka | Účel |
|-----------|------|
| `slack/` | Slack `:gear:` capture (hub `slack_poll`) + Cowork archiv |
| `sembly/` | Sembly webhook |
| `email/` | Gmail hvězdičky (celé vlákno) |
| `email/sent/` | Nové odeslané (ne reply) |
| `daily/` | Ruční / mobilní capture |
| `Clippings/` | Web Clipper — bez n8n |

## Workflows (produkční ID na n8n.redbuttonedu.cz)

| Soubor | n8n ID | Co dělá |
|--------|--------|---------|
| `gmail-starred-to-inbox-workspace.json` | `xtnI0PYaTp8Ou2la` | Hvězdičky + refresh SB Saved → `01-INBOX/email/` (Workspace), včetně příloh `sb-workspace-<thread>__soubor`; schedule **5 min** |
| `gmail-starred-to-inbox-personal.json` | `yuFyLHlioxuE2Jhj` | Totéž pro osobní Gmail (`lukas.cypra@gmail.com`); schedule **15 min** |
| `n8n-error-to-slack.json` | `PCmXS1X3xB8hWfy0` | Error Trigger → Slack `#…` (`C0C5VRU59UZ`); throttle **1×/10 min** per workflow |
| `coolify-to-slack-alerts.json` | `IuZgaUkHQJUXqfEP` | Coolify webhook → jen error/warning → `C0C5VRU59UZ` (`@claude_capture`) |
| `workspace-sent-to-inbox.json` | `7fhDXThOaxl1yNtE` | Nové odeslané (ne reply) → `email/sent/` + SB Saved |
| `slack-cowork-inbox-with-attachments.json` | `rCOoXlfbD1XcVmtn` | Slack capture + přílohy |
| `mobile-capture-to-cowork.json` | `k5p32VUAgaPL0KPe` | Webhook → daily/ |
| `sembly-to-cowork.json` | `hKL04ATDDRSt0FOG` | Sembly → Drive (legacy; **off**) |
| `sembly-to-brain.json` | `zZpTwhV8Z18OFaNO` | Sembly webhook → Brain `ingest_sembly` → git `01-INBOX/sembly/` (**active** 2026-10-12). Webhook path `sembly-cowork-transcript` (stejná URL jako legacy). |

**Smazáno:** `email-to-cowork` (`omQRpDBa48ePiKnT`, forward `+cowork`), Slack Odpověz (`jpeTZfRw42XujVw4`).

Deploy: `python3 scripts/deploy_n8n_cowork_workflows.py` (REST API, zachová credentials).

## Drop list odeslaných

SSOT: `workspace-sent-format-markdown.js` + `vps/second-brain-hub/cron/triage_commitments.py` (`_SENT_INBOX_DROP_RULES`).

## Kanonický formát `## Přílohy`

```markdown
## Přílohy

- [soubor.pdf](https://drive.google.com/.../view) — application/pdf, 1.2 MB
```

Helper: `ŠABLONY/n8n/lib/attachments-markdown.js`.
