# Build context = vps/ (Coolify), not this directory (A35 — no COPY ../).
FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates curl git git-lfs openssh-client \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install --system

WORKDIR /app

COPY second-brain-brain/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY second-brain-hub/lib/ /app/lib/
COPY second-brain-brain/app/ /app/app/

ENV TZ=Europe/Prague \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    VAULT_BACKEND=git \
    GIT_VAULT_ROOT=/data/vault \
    GIT_VAULT_PUSH=1 \
    GIT_AUTHOR_NAME="Second Brain Brain" \
    GIT_AUTHOR_EMAIL="second-brain-brain@noreply.redbuttonedu.cz"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
