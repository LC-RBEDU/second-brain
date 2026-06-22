# Email forward → Cowork INBOX

> Cíl: cokoli, co přepošleš na `lukas.cypra+cowork@gmail.com`, padne jako .md do `INBOX/email/`.

## Jak to funguje

Gmail má vestavěné **plus-addressing**: cokoli ve formátu `lukas.cypra+ANYTHING@gmail.com` chodí do schránky `lukas.cypra@gmail.com`. Není potřeba nic ve Gmailu nastavovat.

n8n workflow `email-to-cowork.json` pollne Gmail s filtrem `to:lukas.cypra+cowork@gmail.com` a každou novou zprávu zformátuje do .md a uloží na Drive.

## Setup

### 1. Gmail OAuth pro n8n

- n8n → Credentials → New → **Gmail OAuth2 API**
- Klikni "Sign in with Google" → přihlas se na **`lukas.cypra@gmail.com`** (NE firemní)
- Allow scope: `gmail.readonly` (na čtení emailů a download attachmentů)
- Save

### 2. Import workflow

- n8n → Workflows → Import from File → `ŠABLONY/n8n/email-to-cowork.json`
- V Gmail Trigger nodu vlož credential z bodu 1
- V Drive Save nodu vlož Drive credential + Folder ID `INBOX/email/`
- Activate

### 3. Test

- Z jiného účtu (nebo z firemního) pošli e-mail na `lukas.cypra+cowork@gmail.com`
- Počkej max 1 min (poll interval)
- Zkontroluj `INBOX/email/` na Drive

## Tipy

### Použití v praxi

- **Forward e-mailu**, který chceš zachytit → adresa do To: nebo Cc: → odeslat. n8n to vyzvedne.
- **Bcc**: funguje taky — pošleš e-mail komu chceš a do Bcc dáš `lukas.cypra+cowork@gmail.com`. Zachycení je tiché.
- **Označení tématu předem**: do Subject přidej `[téma: rb-universe]` — capture skill toho využije při třídění

### Filter, ať to nesype všechno

n8n workflow má filter `to:lukas.cypra+cowork@gmail.com`. Pokud chceš ještě vyloučit:
- `-from:me` — neuloží to, co posíláš sám sobě (test)
- `-label:newsletter` — vyloučí newslettery, pokud máš label

### Gmail label "Cowork" (volitelné)

Pokud chceš ve Gmailu mít přehled, co se uložilo:
- Vytvoř Gmail label `Cowork`
- Vytvoř Gmail filter: `to:(lukas.cypra+cowork@gmail.com)` → Apply label `Cowork`
- Pak vidíš ve Gmailu složku Cowork s vším, co prošlo do INBOXu

### Přílohy

Workflow `email-to-cowork.json` stahuje přílohy na Drive a do `.md` vkládá kanonický blok:

```markdown
## Přílohy

- [soubor.pdf](https://drive.google.com/.../view) — application/pdf, 1.2 MB
```

Flow: Gmail download → upload → `Code: Finalize ## Přílohy` → save `.md`. Viz `ŠABLONY/n8n/README.md` a helper `ŠABLONY/n8n/lib/attachments-markdown.js`.

## Bezpečnost

- Adresa `lukas.cypra+cowork@gmail.com` je **veřejně předvídatelná** (kdokoli, kdo zná tvoji základní adresu, ji uhodne)
- Workflow ukládá **vše**, co přijde — pokud někdo zlomyslně pošle obří přílohu, plní ti to Drive
- **Mitigation**:
  - V Gmailu si přidej filter, který nepouští do schránky známé spam patterny
  - Workflow má max. limit (n8n executions / minute) — nesype tam fakt všechno najednou
  - Pokud bys měl problém, zruš plus-alias a uděláme dedikovanou e-mail adresu na vlastní doméně
