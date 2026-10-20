# Build context = vps/ (Coolify). The dashboard container has no vault mount.
FROM node:22-bookworm-slim AS web

WORKDIR /web
COPY second-brain-dashboard/web/package.json second-brain-dashboard/web/package-lock.json ./
RUN npm ci
COPY second-brain-dashboard/web/index.html second-brain-dashboard/web/vite.config.js ./
COPY second-brain-dashboard/web/src ./src
RUN npm run build

FROM python:3.12-slim-bookworm

WORKDIR /app
COPY second-brain-dashboard/bff/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY second-brain-dashboard/bff/dashboard_bff /app/dashboard_bff
COPY --from=web /web/dist /app/web/dist

ENV TZ=Europe/Prague \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DASHBOARD_DIST=/app/web/dist

EXPOSE 8000

CMD ["uvicorn", "dashboard_bff.asgi:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
