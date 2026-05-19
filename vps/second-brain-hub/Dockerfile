FROM python:3.12-slim-bookworm

ARG SUPERCRONIC_VERSION=v0.2.33

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64" \
      -o /usr/local/bin/supercronic \
    && chmod +x /usr/local/bin/supercronic

WORKDIR /app

COPY cron/ /app/cron/
COPY web/ /var/www/html/
COPY deploy/nginx.conf /etc/nginx/sites-available/default
COPY deploy/crontab /etc/cron.d/second-brain
COPY deploy/entrypoint.sh /entrypoint.sh

RUN chmod 0644 /etc/cron.d/second-brain \
    && chmod +x /entrypoint.sh \
    && ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default \
    && mkdir -p /data/mrluc /var/log/second-brain \
    && chown -R www-data:www-data /var/www/html

ENV VAULT_PATH=/data/mrluc \
    TZ=Europe/Prague \
    DASHBOARD_JSON=/var/www/html/dashboard-data.json \
    LEGACY_TASKS=/data/mrluc/00-System/dashboard-tasks-source.json \
    PYTHONUNBUFFERED=1

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
