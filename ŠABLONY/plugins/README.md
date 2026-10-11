# Plugin SSOT (F2-j)

Skills žijí v [`ŠABLONY/skills/`](../skills/). Tento strom drží **manifesty klientů** (Cursor / Claude / Grok), které ukazují na Brain MCP (`BRAIN_PUBLIC_URL`) a na stejnou tool sadu.

| Klient | Manifest |
|---|---|
| Cursor | [`cursor/mcp.json.example`](cursor/mcp.json.example) |
| Claude | [`claude/mcp.json.example`](claude/mcp.json.example) |
| Grok Bot | [`grok/mcp.json.example`](grok/mcp.json.example) |

Live Brain: `https://brain.cyprovi.cz/mcp/` (trailing slash). Token = Coolify app **second-brain-brain** → `BRAIN_SERVICE_TOKEN`.

| Klient | Auth tvar |
|---|---|
| Cursor / Grok | native `url` + `headers.Authorization: Bearer …` |
| Claude Desktop | jen `command`/`args`/`env` (schema odmítne `url`) → `npx mcp-remote` + `--header Authorization:${BRAIN_AUTHORIZATION}` a token v `env` |

OAuth cookie = browser session; remote MCP ho typicky nepošle.
