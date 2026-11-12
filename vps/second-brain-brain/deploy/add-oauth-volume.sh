#!/usr/bin/env bash
# Add the Claude OAuth SQLite volume to the live Brain app and queue one deploy.
# Does not copy env and does not touch BRAIN_SERVICE_TOKEN.
# Pepper (BRAIN_OAUTH_TOKEN_PEPPER) must already be in Coolify, or OAuth returns 503.
set -euo pipefail

APP_NAME="second-brain-brain"
PROJECT_NAME="Second Brain"

gen_uuid() {
  openssl rand -hex 12
}

PSQL='docker exec coolify-db psql -U coolify -d coolify -q -t -A'

ENV_ID=$($PSQL -c "SELECT id FROM environments WHERE project_id=(SELECT id FROM projects WHERE name='${PROJECT_NAME}' LIMIT 1) AND name='production' LIMIT 1;")
if [[ -z "${ENV_ID}" ]]; then
  echo "ERROR: project '${PROJECT_NAME}' / production environment missing" >&2
  exit 1
fi

APP_ID=$($PSQL -c "SELECT id FROM applications WHERE environment_id=${ENV_ID} AND name='${APP_NAME}' LIMIT 1;")
if [[ -z "${APP_ID}" ]]; then
  echo "ERROR: application ${APP_NAME} missing" >&2
  exit 1
fi

EXISTING=$($PSQL -c "SELECT id FROM local_persistent_volumes WHERE resource_id=${APP_ID} AND mount_path='/data/oauth' LIMIT 1;")
if [[ -n "${EXISTING}" ]]; then
  echo "OAuth volume already present id=${EXISTING}"
else
  VOL_UUID=$(gen_uuid)
  $PSQL -c "INSERT INTO local_persistent_volumes (uuid, name, mount_path, host_path, resource_type, resource_id, created_at, updated_at)
    VALUES ('${VOL_UUID}', 'second-brain-oauth', '/data/oauth', '/data/second-brain-oauth', 'App\Models\Application', ${APP_ID}, NOW(), NOW());"
  echo "Inserted OAuth volume uuid=${VOL_UUID} mount=/data/oauth host=/data/second-brain-oauth"
fi

echo "Queue deployment..."
DEPLOY_UUID=$(gen_uuid)
QUEUE_ID=$($PSQL -c \
  "INSERT INTO application_deployment_queues (
     application_id, deployment_uuid, status, created_at, updated_at, commit,
     pull_request_id, force_rebuild, is_webhook, restart_only,
     server_id, destination_id, application_name, server_name
   )
   SELECT '${APP_ID}', '${DEPLOY_UUID}', 'queued', NOW(), NOW(), 'HEAD',
     0, true, false, false,
     0, '0', '${APP_NAME}', 'DEVELOPMENT SERVER'
   WHERE NOT EXISTS (
     SELECT 1 FROM application_deployment_queues
     WHERE application_id='${APP_ID}' AND status IN ('queued','in_progress')
   )
   RETURNING id;")
if [[ -n "${QUEUE_ID}" ]]; then
  echo "Queued deployment id=${QUEUE_ID} uuid=${DEPLOY_UUID} restart_only=false"
else
  echo "Deploy already queued/in_progress — skip new queue row"
fi
