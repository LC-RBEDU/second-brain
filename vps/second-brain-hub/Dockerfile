FROM python:3.12-slim-bookworm

ARG SUPERCRONIC_VERSION=v0.2.33

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl procps tini git git-lfs \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64" \
      -o /usr/local/bin/supercronic \
    && chmod +x /usr/local/bin/supercronic \
    && git lfs install --system

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY lib/ /app/lib/
COPY cron/ /app/cron/
COPY deploy/crontab /app/crontab
COPY deploy/crontab.pause /app/crontab.pause
COPY deploy/entrypoint.sh /entrypoint.sh

RUN chmod 0644 /app/crontab /app/crontab.pause \
    && chmod +x /entrypoint.sh \
    && mkdir -p /var/log/second-brain /data/vault

# Vault I/O: VAULT_BACKEND=drive (default) or git (GIT_VAULT_ROOT=/data/vault).
# Coolify: mount persistent volume ≥3 GB on /data/vault for git WC.
ENV TZ=Europe/Prague \
    PYTHONUNBUFFERED=1 \
    VAULT_BACKEND=drive \
    CRONTAB_MODE=live \
    GIT_VAULT_ROOT=/data/vault \
    GIT_AUTHOR_NAME="Second Brain Hub" \
    GIT_AUTHOR_EMAIL="second-brain-hub@noreply.redbuttonedu.cz"

ENTRYPOINT ["/usr/bin/tini", "-g", "--", "/entrypoint.sh"]
