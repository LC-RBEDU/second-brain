#!/usr/bin/env bash
# Run ON coolify-dev as user ops (docker access). Creates Coolify Brain app next to hub.
# Shared WC: /data/second-brain-vault → /data/vault (+ same deploy key as hub).
set -euo pipefail

PROJECT_NAME="Second Brain"
APP_NAME="second-brain-brain"
GIT_REPO="LC-RBEDU/second-brain"
GIT_BRANCH="main"
BASE_DIR="/vps"
DOCKERFILE_LOCATION="/second-brain-brain/Dockerfile"
PORTS="8000"
HEALTH_PATH="/healthz"
GITHUB_APP_SOURCE_ID=5
SERVER_DESTINATION_ID=0
HUB_APP_ID=11
HOST_IP="72.62.152.9"

gen_uuid() {
  openssl rand -hex 12
}

encrypt() {
  local plain="$1"
  docker exec -i coolify php -r '
require "/var/www/html/vendor/autoload.php";
$app=require "/var/www/html/bootstrap/app.php";
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
$in=stream_get_contents(STDIN);
echo Illuminate\Support\Facades\Crypt::encrypt($in);
' <<<"${plain}"
}

PSQL='docker exec coolify-db psql -U coolify -d coolify -q -t -A'

ENV_ID=$($PSQL -c "SELECT id FROM environments WHERE project_id=(SELECT id FROM projects WHERE name='${PROJECT_NAME}' LIMIT 1) AND name='production' LIMIT 1;")
if [[ -z "${ENV_ID}" ]]; then
  echo "ERROR: project '${PROJECT_NAME}' / production environment missing" >&2
  exit 1
fi

APP_ID=$($PSQL -c "SELECT id FROM applications WHERE environment_id=${ENV_ID} AND name='${APP_NAME}' LIMIT 1;")
if [[ -n "${APP_ID}" ]]; then
  APP_UUID=$($PSQL -c "SELECT uuid FROM applications WHERE id=${APP_ID};")
  echo "Application already exists id=${APP_ID} uuid=${APP_UUID}"
else
  APP_UUID=$(gen_uuid)
  FQDN="https://${APP_UUID}.${HOST_IP}.sslip.io"
  APP_ID=$($PSQL -c \
    "INSERT INTO applications (
      uuid, name, git_repository, git_branch, git_commit_sha, build_pack, static_image,
      ports_exposes, base_directory, publish_directory, health_check_path, health_check_host,
      health_check_method, health_check_return_code, health_check_scheme,
      health_check_interval, health_check_timeout, health_check_retries, health_check_start_period,
      limits_memory, limits_memory_swap, limits_memory_swappiness, limits_memory_reservation,
      limits_cpus, limits_cpu_shares, status, preview_url_template,
      destination_type, destination_id, source_type, source_id, environment_id,
      health_check_enabled, dockerfile_location, fqdn, watch_paths,
      created_at, updated_at, description, health_check_type
    ) VALUES (
      '${APP_UUID}', '${APP_NAME}', '${GIT_REPO}', '${GIT_BRANCH}', 'HEAD', 'dockerfile', 'nginx:alpine',
      '${PORTS}', '${BASE_DIR}', '/', '${HEALTH_PATH}', 'localhost', 'GET', 200, 'http',
      5, 5, 10, 30,
      '0', '0', 60, '0', '0', 1024, 'exited:unknown', '{{pr_id}}.{{domain}}',
      'App\Models\StandaloneDocker', ${SERVER_DESTINATION_ID},
      'App\Models\GithubApp', ${GITHUB_APP_SOURCE_ID}, ${ENV_ID},
      true, '${DOCKERFILE_LOCATION}', '${FQDN}',
      'vps/second-brain-brain/**
vps/second-brain-hub/lib/**',
      NOW(), NOW(), 'Second Brain — Brain API (MCP + OAuth + REST)', 'http'
    ) RETURNING id;")
  echo "Created application id=${APP_ID} uuid=${APP_UUID} fqdn=${FQDN}"

  docker exec coolify-db psql -U coolify -d coolify -q -c \
    "INSERT INTO application_settings (is_static, is_git_submodules_enabled, is_git_lfs_enabled,
      is_auto_deploy_enabled, is_force_https_enabled, is_debug_enabled, is_preview_deployments_enabled,
      application_id, created_at, updated_at, is_log_drain_enabled, is_gpu_enabled, gpu_driver,
      is_include_timestamps, is_swarm_only_worker_nodes, is_raw_compose_deployment_enabled,
      is_build_server_enabled, is_consistent_container_name_enabled, is_gzip_enabled,
      is_stripprefix_enabled, connect_to_docker_network, is_container_label_escape_enabled,
      is_env_sorting_enabled, is_container_label_readonly_enabled, is_preserve_repository_enabled,
      disable_build_cache, is_spa, is_git_shallow_clone_enabled, is_pr_deployments_public_enabled,
      use_build_secrets, inject_build_args_to_dockerfile, include_source_commit_in_build, docker_images_to_keep)
     VALUES (false, true, true, true, true, false, false, ${APP_ID}, NOW(), NOW(), false, false, 'nvidia',
      false, true, false, false, false, true, true, false, true, false, true, false, false, false, true, false,
      false, true, false, 2);"
fi

FQDN=$($PSQL -c "SELECT fqdn FROM applications WHERE id=${APP_ID};")
BRAIN_PUBLIC_URL="${FQDN%/}"

# Shared vault WC + hub deploy key paths (ops cannot copy root-owned key files)
HUB_UUID=$($PSQL -c "SELECT uuid FROM applications WHERE id=${HUB_APP_ID};")
HOST_HUB_DIR="/data/coolify/applications/${HUB_UUID}"

bool_sql() {
  case "$1" in
    t|true|TRUE|1) echo true ;;
    *) echo false ;;
  esac
}

# Persistent + file volumes (idempotent)
VOL_UUID=$(gen_uuid)
$PSQL -c "SELECT id FROM local_persistent_volumes WHERE resource_id=${APP_ID} AND mount_path='/data/vault' LIMIT 1;" | grep -q . || \
  $PSQL -c "INSERT INTO local_persistent_volumes (uuid, name, mount_path, host_path, resource_type, resource_id, created_at, updated_at)
    VALUES ('${VOL_UUID}', 'second-brain-vault-wc', '/data/vault', '/data/second-brain-vault', 'App\Models\Application', ${APP_ID}, NOW(), NOW());"

for pair in "sb-vault-deploy|/root/.ssh/sb-vault-deploy" "known_hosts|/root/.ssh/known_hosts"; do
  fname="${pair%%|*}"
  mpath="${pair##*|}"
  $PSQL -c "SELECT id FROM local_file_volumes WHERE resource_id=${APP_ID} AND mount_path='${mpath}' LIMIT 1;" | grep -q . || \
    $PSQL -c "INSERT INTO local_file_volumes (uuid, fs_path, mount_path, resource_type, resource_id, is_directory, created_at, updated_at)
      VALUES ('$(gen_uuid)', '${HOST_HUB_DIR}/${fname}', '${mpath}', 'App\Models\Application', ${APP_ID}, false, NOW(), NOW());"
done

upsert_env() {
  local key="$1"
  local plain="$2"
  local enc enc_sql existing
  enc=$(encrypt "${plain}")
  enc_sql=${enc//\'/\'\'}
  for preview in false true; do
    existing=$($PSQL -c "SELECT id FROM environment_variables WHERE resourceable_type='App\Models\Application' AND resourceable_id=${APP_ID} AND key='${key}' AND is_preview=${preview} LIMIT 1;")
    if [[ -n "${existing}" ]]; then
      docker exec coolify-db psql -U coolify -d coolify -q -c \
        "UPDATE environment_variables SET value='${enc_sql}', updated_at=NOW() WHERE id=${existing};"
    else
      docker exec coolify-db psql -U coolify -d coolify -q -c \
        "INSERT INTO environment_variables (uuid, key, value, is_preview, is_shown_once, is_multiline, is_literal, is_runtime, is_buildtime, is_shared, resourceable_type, resourceable_id, created_at, updated_at)
         VALUES ('$(gen_uuid)', '${key}', '${enc_sql}', ${preview}, false, false, false, true, true, false, 'App\Models\Application', ${APP_ID}, NOW(), NOW());"
    fi
  done
}

copy_env_from_hub() {
  local key="$1"
  local preview row value is_literal value_sql existing lit
  for preview in false true; do
    row=$($PSQL -c "SELECT value, is_literal FROM environment_variables WHERE resourceable_type='App\Models\Application' AND resourceable_id=${HUB_APP_ID} AND key='${key}' AND is_preview=${preview} LIMIT 1;")
    [[ -z "${row}" ]] && continue
    value="${row%|*}"
    is_literal="${row##*|}"
    lit=$(bool_sql "$is_literal")
    value_sql=${value//\'/\'\'}
    existing=$($PSQL -c "SELECT id FROM environment_variables WHERE resourceable_type='App\Models\Application' AND resourceable_id=${APP_ID} AND key='${key}' AND is_preview=${preview} LIMIT 1;")
    if [[ -n "${existing}" ]]; then
      docker exec coolify-db psql -U coolify -d coolify -q -c \
        "UPDATE environment_variables SET value='${value_sql}', is_literal=${lit}, updated_at=NOW() WHERE id=${existing};"
    else
      docker exec coolify-db psql -U coolify -d coolify -q -c \
        "INSERT INTO environment_variables (uuid, key, value, is_preview, is_shown_once, is_multiline, is_literal, is_runtime, is_buildtime, is_shared, resourceable_type, resourceable_id, created_at, updated_at)
         VALUES ('$(gen_uuid)', '${key}', '${value_sql}', ${preview}, false, false, ${lit}, true, true, false, 'App\Models\Application', ${APP_ID}, NOW(), NOW());"
    fi
  done
}

# Vault / git — same as hub live
for k in VAULT_BACKEND GIT_VAULT_ROOT GIT_VAULT_REMOTE GIT_VAULT_BRANCH GIT_VAULT_PUSH GIT_VAULT_DRY_RUN GIT_SSH_COMMAND GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL TZ; do
  copy_env_from_hub "$k" || true
done

# Brain-specific
upsert_env "BRAIN_PUBLIC_URL" "${BRAIN_PUBLIC_URL}"
if ! $PSQL -c "SELECT id FROM environment_variables WHERE resourceable_id=${APP_ID} AND key='BRAIN_SERVICE_TOKEN' AND is_preview=f LIMIT 1;" | grep -q .; then
  SERVICE_TOKEN=$(openssl rand -hex 32)
  upsert_env "BRAIN_SERVICE_TOKEN" "${SERVICE_TOKEN}"
  echo "Generated BRAIN_SERVICE_TOKEN (stored in Coolify env; not printed)."
else
  echo "BRAIN_SERVICE_TOKEN already set — left unchanged."
fi

# Google OAuth — copy from MCP_Claude (app 10) when present
MCP_ID=10
for k in GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET; do
  for preview in f t; do
    row=$($PSQL -c "SELECT value, is_literal FROM environment_variables WHERE resourceable_type='App\Models\Application' AND resourceable_id=${MCP_ID} AND key='${k}' AND is_preview=${preview} LIMIT 1;")
    [[ -z "${row}" ]] && continue
    value="${row%|*}"; is_literal="${row##*|}"
    existing=$($PSQL -c "SELECT id FROM environment_variables WHERE resourceable_type='App\Models\Application' AND resourceable_id=${APP_ID} AND key='${k}' AND is_preview=${preview} LIMIT 1;")
    if [[ -n "${existing}" ]]; then
      docker exec coolify-db psql -U coolify -d coolify -q -c \
        "UPDATE environment_variables SET value='${value}', updated_at=NOW() WHERE id=${existing};"
    else
      docker exec coolify-db psql -U coolify -d coolify -q -c \
        "INSERT INTO environment_variables (uuid, key, value, is_preview, is_shown_once, is_multiline, is_literal, is_runtime, is_buildtime, is_shared, resourceable_type, resourceable_id, created_at, updated_at)
         VALUES ('$(gen_uuid)', '${k}', '${value}', ${preview}, false, false, ${is_literal}, true, true, false, 'App\Models\Application', ${APP_ID}, NOW(), NOW());"
    fi
  done
done

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
  echo "Queued deployment id=${QUEUE_ID} uuid=${DEPLOY_UUID}"
else
  echo "Deploy already queued/in_progress — skip new queue row"
fi

echo "Done."
echo "App UUID: ${APP_UUID}"
echo "BRAIN_PUBLIC_URL: ${BRAIN_PUBLIC_URL}"
echo "OAuth callback: ${BRAIN_PUBLIC_URL}/oauth/callback"
echo "Health: ${BRAIN_PUBLIC_URL}/healthz"
echo "NOTE: Add OAuth redirect URI in Google Cloud Console; set GROK_BOT_REMINDER_* on hub for B25."
