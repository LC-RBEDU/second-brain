#!/usr/bin/env bash
# Run ON coolify-dev as user ops (docker access).
# Third app in the Second Brain project. Does not mount the vault.
# Redirect URI is printed for the existing Google client. No new client.
set -euo pipefail

PROJECT_NAME="Second Brain"
APP_NAME="second-brain-dashboard"
BRAIN_APP_NAME="second-brain-brain"
GIT_REPO="LC-RBEDU/second-brain"
GIT_BRANCH="main"
BASE_DIR="/vps"
DOCKERFILE_LOCATION="/second-brain-dashboard/Dockerfile"
PORTS="8000"
HEALTH_PATH="/healthz"
GITHUB_APP_SOURCE_ID=5
SERVER_DESTINATION_ID=0
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

BRAIN_APP_ID=$($PSQL -c "SELECT id FROM applications WHERE environment_id=${ENV_ID} AND name='${BRAIN_APP_NAME}' LIMIT 1;")
if [[ -z "${BRAIN_APP_ID}" ]]; then
  echo "ERROR: ${BRAIN_APP_NAME} missing in this environment" >&2
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
      '0', '0', '60', '0', '0', 1024, 'exited:unknown', '{{pr_id}}.{{domain}}',
      'App\Models\StandaloneDocker', ${SERVER_DESTINATION_ID},
      'App\Models\GithubApp', ${GITHUB_APP_SOURCE_ID}, ${ENV_ID},
      true, '${DOCKERFILE_LOCATION}', '${FQDN}',
      'vps/second-brain-dashboard/**',
      NOW(), NOW(), 'Second Brain — dashboard (browser export, no vault)', 'http'
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
     VALUES (false, false, false, true, true, false, false, ${APP_ID}, NOW(), NOW(), false, false, 'nvidia',
      false, true, false, false, false, true, true, false, true, false, true, false, false, false, true, false,
      false, true, false, 2);"
fi

if $PSQL -c "SELECT id FROM local_persistent_volumes WHERE resource_id=${APP_ID} AND mount_path='/data/vault' LIMIT 1;" | grep -q .; then
  echo "ERROR: dashboard must not mount /data/vault" >&2
  exit 1
fi

FQDN=$($PSQL -c "SELECT fqdn FROM applications WHERE id=${APP_ID};")
DASHBOARD_PUBLIC_URL="${FQDN%/}"

bool_sql() {
  case "$1" in
    t|true|TRUE|1) echo true ;;
    *) echo false ;;
  esac
}

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

copy_env_from_brain() {
  local src_key="$1"
  local dest_key="$2"
  local preview row value is_literal value_sql existing lit
  for preview in false true; do
    row=$($PSQL -c "SELECT value, is_literal FROM environment_variables WHERE resourceable_type='App\Models\Application' AND resourceable_id=${BRAIN_APP_ID} AND key='${src_key}' AND is_preview=${preview} LIMIT 1;")
    if [[ -z "${row}" ]]; then
      if [[ "${preview}" == "false" ]]; then
        echo "ERROR: Brain is missing ${src_key}" >&2
        exit 1
      fi
      continue
    fi
    value="${row%|*}"
    is_literal="${row##*|}"
    lit=$(bool_sql "$is_literal")
    value_sql=${value//\'/\'\'}
    existing=$($PSQL -c "SELECT id FROM environment_variables WHERE resourceable_type='App\Models\Application' AND resourceable_id=${APP_ID} AND key='${dest_key}' AND is_preview=${preview} LIMIT 1;")
    if [[ -n "${existing}" ]]; then
      docker exec coolify-db psql -U coolify -d coolify -q -c \
        "UPDATE environment_variables SET value='${value_sql}', is_literal=${lit}, updated_at=NOW() WHERE id=${existing};"
    else
      docker exec coolify-db psql -U coolify -d coolify -q -c \
        "INSERT INTO environment_variables (uuid, key, value, is_preview, is_shown_once, is_multiline, is_literal, is_runtime, is_buildtime, is_shared, resourceable_type, resourceable_id, created_at, updated_at)
         VALUES ('$(gen_uuid)', '${dest_key}', '${value_sql}', ${preview}, false, false, ${lit}, true, true, false, 'App\Models\Application', ${APP_ID}, NOW(), NOW());"
    fi
  done
}

copy_env_from_brain "BRAIN_PUBLIC_URL" "BRAIN_BASE_URL"
copy_env_from_brain "BRAIN_SERVICE_TOKEN" "BRAIN_SERVICE_TOKEN"
copy_env_from_brain "GOOGLE_CLIENT_ID" "GOOGLE_CLIENT_ID"
copy_env_from_brain "GOOGLE_CLIENT_SECRET" "GOOGLE_CLIENT_SECRET"
upsert_env "DASHBOARD_PUBLIC_URL" "${DASHBOARD_PUBLIC_URL}"
if ! $PSQL -c "SELECT id FROM environment_variables WHERE resourceable_id=${APP_ID} AND key='DASHBOARD_SESSION_SECRET' AND is_preview=false LIMIT 1;" | grep -q .; then
  upsert_env "DASHBOARD_SESSION_SECRET" "$(openssl rand -hex 32)"
  echo "Generated DASHBOARD_SESSION_SECRET (stored in Coolify env; not printed)."
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
  echo "Queued deployment id=${QUEUE_ID} uuid=${DEPLOY_UUID}"
else
  echo "Deploy already queued/in_progress — skip new queue row"
fi

echo "Done."
echo "App UUID: ${APP_UUID}"
echo "DASHBOARD_PUBLIC_URL: ${DASHBOARD_PUBLIC_URL}"
echo "OAuth callback: ${DASHBOARD_PUBLIC_URL}/oauth/callback"
echo "Add that redirect URI on the existing Google client. Do not create a new client."
echo "Health: ${DASHBOARD_PUBLIC_URL}/healthz"
