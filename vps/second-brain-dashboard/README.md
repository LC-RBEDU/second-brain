# Second Brain dashboard

Třetí Coolify aplikace v projektu Second Brain, vedle hubu a Brainu. Prohlížeč bere jeden export otevřených tasků (`include_closed_days=0`) a Brain nevolá. Done, Cancelled a archiv v přehledu nejsou.

Vault v tomhle kontejneru není. Žádný mount `/data/vault`. Zápis jde na Brain service tokenem. Autor commitu ve vaultu zůstává Brain.

- `DASHBOARD_PUBLIC_URL` = veřejné HTTPS tohoto sslip. OAuth callback je `{URL}/oauth/callback`.
- Redirect URI se přidá na stávajícího Google klienta (`GOOGLE_CLIENT_ID` stejné jako u Brainu). Nový klient ani vlastní doména se nezakládají.
- `BRAIN_BASE_URL` = veřejné HTTPS Brainu. `BRAIN_SERVICE_TOKEN` je ten samý token, který Brain už má.
- `DASHBOARD_SESSION_SECRET` podepisuje cookie `sb_dashboard_session`.

Build context Coolify: **`vps/`**. Dockerfile: `second-brain-dashboard/Dockerfile`.

Setup na `coolify-dev` jako uživatel `ops`, až je kód na `main`:

```bash
bash vps/second-brain-dashboard/deploy/setup-coolify.sh
```

Skript aplikaci založí, env zkopíruje z Brainu, vault nemountuje a vypíše redirect URI. Nasazení zařadí do fronty. URI z výpisu přidej do stávajícího Google klienta.
