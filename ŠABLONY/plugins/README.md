# Plugin SSOT (F2-j)

Skills žijí v [`ŠABLONY/skills/`](../skills/). Tento strom drží **manifesty klientů** (Cursor / Claude / Grok), které ukazují na Brain MCP (`BRAIN_PUBLIC_URL`) a na stejnou tool sadu.

| Klient | Manifest |
|---|---|
| Cursor | [`cursor/mcp.json.example`](cursor/mcp.json.example) |
| Claude | [`claude/mcp.json.example`](claude/mcp.json.example) |
| Grok Bot | [`grok/mcp.json.example`](grok/mcp.json.example) |

Po F2 Coolify: nahraď `https://BRAIN_PUBLIC_URL` skutečnou hodnotou. OAuth = user-bound (ne service token v lidském klientovi).
