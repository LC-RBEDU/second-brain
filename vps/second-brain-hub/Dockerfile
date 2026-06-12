FROM python:3.12-slim-bookworm

ARG SUPERCRONIC_VERSION=v0.2.33

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl procps tini \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64" \
      -o /usr/local/bin/supercronic \
    && chmod +x /usr/local/bin/supercronic \
    && curl -fsSL https://cursor.com/install | bash \
    && ln -sf /root/.local/bin/cursor-agent /usr/local/bin/cursor-agent \
    && ln -sf /root/.local/bin/agent /usr/local/bin/agent

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY lib/ /app/lib/
COPY cron/ /app/cron/
COPY deploy/crontab /app/crontab
COPY deploy/entrypoint.sh /entrypoint.sh

RUN chmod 0644 /app/crontab \
    && chmod +x /entrypoint.sh \
    && mkdir -p /var/log/second-brain

# Stateless: no /data/mrluc volume. Vault I/O is via Google Drive API (lib/drive_io.py).
# Required runtime env (set in Coolify):
#   VAULT_DRIVE_ID            = OBSIDIAN folder ID in Drive
#   GOOGLE_DRIVE_OAUTH_JSON   = OAuth user creds (refresh token) for Drive API
#   GOOGLE_DRIVE_SA_JSON      = Service Account JSON for Calendar API (DWD)
#   CALENDAR_USER_EMAIL       = subject email for SA delegation
ENV TZ=Europe/Prague \
    PYTHONUNBUFFERED=1

# Cron-only — no HTTP; no HEALTHCHECK (avoids Coolify rollback when supercronic is PID 1)

ENTRYPOINT ["/usr/bin/tini", "-g", "--", "/entrypoint.sh"]
