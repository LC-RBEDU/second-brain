FROM python:3.12-slim-bookworm

ARG SUPERCRONIC_VERSION=v0.2.33

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl procps tini \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64" \
      -o /usr/local/bin/supercronic \
    && chmod +x /usr/local/bin/supercronic

WORKDIR /app

COPY cron/ /app/cron/
COPY deploy/crontab /app/crontab
COPY deploy/entrypoint.sh /entrypoint.sh

RUN chmod 0644 /app/crontab \
    && chmod +x /entrypoint.sh \
    && mkdir -p /data/mrluc /var/log/second-brain

ENV VAULT_PATH=/data/mrluc \
    TZ=Europe/Prague \
    DASHBOARD_JSON=/data/mrluc/00-System/dashboard-data.json \
    LEGACY_TASKS=/data/mrluc/00-System/dashboard-tasks-source.json \
    PYTHONUNBUFFERED=1

# Cron-only container — no HTTP server exposed via Coolify/Traefik
HEALTHCHECK --interval=60s --timeout=5s --start-period=20s --retries=3 \
  CMD pgrep -x supercronic >/dev/null || exit 1

ENTRYPOINT ["/usr/bin/tini", "-g", "--", "/entrypoint.sh"]
