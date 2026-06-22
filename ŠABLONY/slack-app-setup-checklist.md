# Slack App setup — checklist

> Cíl: Slack appka se Socket Mode + n8n workflow **`slack-cowork-inbox-with-attachments.json`** — **nové zprávy v jednom vybraném kanálu** (typicky soukromý „capture“ kanál) se ukládají jako `.md` + přílohy na Google Drive. Jednotný postup: důležité věci **forwarduješ / napíšeš do toho kanálu**, nemusíš řešit DM vs. group DM pro bota.

## Předpoklad

- Přihlášení do **firemního Slack workspace**
- **n8n self-hosted**
- Práva na vytvoření Slack appky

## Kroky

### 1. Vytvoř Slack App

- [https://api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
- Name: např. `Cowork Capture`
- Workspace: **tvůj workspace**

### 2. Socket Mode

- **Socket Mode** → Enable
- App-Level Token: scope `**connections:write`** → zkopíruj `xapp-...` (v n8n *App Token*)

### 3. Bot scopes

**OAuth & Permissions** → *Bot Token Scopes* (minimálně pro capture z kanálu):

- `channels:history` — čtení zpráv ve **veřejných** kanálech
- `groups:history` — čtení zpráv v **soukromých** kanálech
- `channels:read`
- `groups:read`
- `reactions:write` — aby workflow mohl po uložení do Drive přidat **✅** k původní zprávě
- `files:read` — stažení příloh ze zpráv i z **forwardovaných unfurlů** (`url_private_download`)
- `im:history` — načtení vlákna z **DM forwardů** (`conversations.replies`)

Volitelné (už ne pro tento workflow nutné): `reactions:read` — jen pokud chceš appku používat i jinde.

> Po přidání nového scope vždy **Install App → Reinstall to Workspace**, jinak Slack token nový scope nezná.

### 4. Event Subscriptions

- **Event Subscriptions** → Enable
- *Subscribe to bot events* → přidej podle typu capture kanálu:


| Capture kanál | Přidej bot event       |
| ------------- | ---------------------- |
| Soukromý      | `**message.groups*`*   |
| Veřejný       | `**message.channels**` |
| Obojí možné   | přidej **obě**         |


`reaction_added` **nepotřebuješ**, pokud používáš jen nový workflow na zprávy.

- **Save Changes**

### 5. Install do workspace

- **Install App** → **Install to Workspace**
- Zkopíruj **Bot User OAuth Token** (`xoxb-...`)

### 6. Soukromý capture kanál

- Vytvoř **soukromý kanál** (např. `#cowork-capture`), kam budeš dávat věci z DM / jiných kanálů (**forward** nebo ruční přepis).
- Pozvi bota: `/invite` → **Apps** → vyber appku (ne „Invite people“).

### 7. n8n credential

- Credentials → **Slack API**
- Access Token: `xoxb-...`
- App Token: `xapp-...`
- Signing Secret (volitelné, doporučené): z **Basic Information** → App Credentials → *Signing Secret* (není to App-Level Token)

### 8. Import workflow

- Importuj `ŠABLONY/n8n/slack-cowork-inbox-with-attachments.json` (SSOT; starý `slack-reaction-capture.json` nemá přílohy)
- Ve **Slack: nová zpráva** nastav **Channel** = ten capture kanál (nebo vlož ID do `REPLACE_WITH_PRIVATE_CAPTURE_CHANNEL_ID` v JSON před importem).
- **Watch Whole Workspace** musí být **vypnuté** (workflow je vázaný na jeden kanál).
- Nastav Google Drive credential + `folderId` pro `INBOX/slack/`.
- Aktivuj workflow.

### 9. Test

- Pošli do capture kanálu běžnou zprávu.
- Pošli **odpověď ve vlákně** — v `.md` by měla být sekce `## Vlákno (Slack API)` (trigger zpráva + navazující odpovědi).
- **Forward** z jiného kanálu/DM — v `.md` je `## Forwardovaný obsah` (unfurl); **API vlákno se nestahuje** z cizích kanálů (bot tam není → dříve padal celý workflow bez ✅).
- Vlákno přes API jen pro **odpovědi v capture kanálu** (`## Vlákno (Slack API)`).
- V n8n **Executions** ověř běh; na Drive přibyde `.md` (+ přílohy ve stejné složce).
- U původní zprávy ve Slacku se objeví **✅** od bota — to znamená „uloženo do Drive".

> **Poznámka:** Bot musí mít přístup ke zdrojovému kanálu/DM (`groups:history` / `channels:history` / `im:history`). U soukromých kanálů musí být pozvaný.

## Troubleshooting

- **Workflow se nespustí**: aktivní toggle; Socket Mode; v Slack app správné **message.groups** / **message.channels** + *Reinstall* po změně scopes.
- **`channel_not_found` v `Slack: Načti vlákno`**: dříve při forwardu z cizího kanálu — opraveno (forward vlákna se nefetchují; uzel má `continueRegularOutput`). Pokud padá u odpovědi **v capture kanálu**, bot není v `#_claude-capture`.
- **`channel_not_found` (obecně)**: bot není v capture kanálu.
- `**missing_scope**` (zejména u reaction add): chybí `reactions:write`, dopln scope a **Reinstall App**.
- **Reakce ✅ se nepřidá, ostatní funguje**: Slack vrátil chybu jen v posledním uzlu — zkontroluj `reactions:write` scope a že bot je v kanálu.
- **Žádný výstup po triggeru**: otevři výstup **Slack: nová zpráva** — Code **Filtrovat zprávy** zahodí systémové zprávy a `bot_message`; případně uprav filtr v Code uzlu.

## Volitelně: emoji `:cowork:`

Starší varianta workflow běžela na reakci `:cowork:` — už není potřeba pro tento capture kanál. Emoji můžeš ve Slacku nechat pro lidi, ale n8n ho pro tento export nepotřebuje.