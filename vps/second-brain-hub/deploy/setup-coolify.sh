#!/usr/bin/env bash
# Run ON coolify-dev as user ops (docker access). Creates Coolify project + app if missing.
# Does NOT print API tokens.
set -euo pipefail

PROJECT_NAME="Second Brain"
APP_NAME="second-brain-hub"
GIT_REPO="LC-RBEDU/claude-cowork"
GIT_BRANCH="main"
BASE_DIR="/vps/second-brain-hub"
DOMAIN="https://second-brain.dev.redbuttonedu.cz"
GITHUB_APP_SOURCE_ID=4
TEAM_ID=0
SERVER_DESTINATION_ID=0

gen_uuid() {
  openssl rand -hex 12
}

PSQL='docker exec coolify-db psql -U coolify -d coolify -q -t -A'

exists=$($PSQL -c "SELECT id FROM projects WHERE name='${PROJECT_NAME}' LIMIT 1;" 2>/dev/null || echo "")

if [[ -n "${exists}" ]]; then
  echo "Project '${PROJECT_NAME}' already exists (id=${exists})"
  PROJECT_ID="${exists}"
else
  PROJECT_UUID=$(gen_uuid)
  PROJECT_ID=$($PSQL -c \
    "INSERT INTO projects (uuid, name, description, team_id, created_at, updated_at)
     VALUES ('${PROJECT_UUID}', '${PROJECT_NAME}', 'MrLUC dashboard + triage cron', ${TEAM_ID}, NOW(), NOW())
     RETURNING id;")
  echo "Created project id=${PROJECT_ID} uuid=${PROJECT_UUID}"
fi

ENV_ID=$($PSQL -c \
  "SELECT id FROM environments WHERE project_id=${PROJECT_ID} AND name='production' LIMIT 1;")
if [[ -z "${ENV_ID}" ]]; then
  ENV_UUID=$(gen_uuid)
  ENV_ID=$($PSQL -c \
    "INSERT INTO environments (uuid, name, project_id, created_at, updated_at)
     VALUES ('${ENV_UUID}', 'production', ${PROJECT_ID}, NOW(), NOW()) RETURNING id;")
  echo "Created environment id=${ENV_ID}"
fi

APP_ID=$($PSQL -c \
  "SELECT id FROM applications WHERE environment_id=${ENV_ID} AND name='${APP_NAME}' LIMIT 1;")
if [[ -n "${APP_ID}" ]]; then
  echo "Application already exists id=${APP_ID}"
  APP_UUID=$($PSQL -c "SELECT uuid FROM applications WHERE id=${APP_ID};")
else
  APP_UUID=$(gen_uuid)
  APP_ID=$($PSQL -c \
    "INSERT INTO applications (
      uuid, name, git_repository, git_branch, git_commit_sha, build_pack, static_image,
      ports_exposes, base_directory, publish_directory, health_check_path, health_check_host,
      health_check_method, health_check_return_code, health_check_scheme,
      health_check_interval, health_check_timeout, health_check_retries, health_check_start_period,
      limits_memory, limits_memory_swap, limits_memory_swappiness, limits_memory_reservation,
      limits_cpus, limits_cpu_shares, status, preview_url_template,
      destination_type, destination_id, source_type, source_id, environment_id,
      health_check_enabled, dockerfile_location, fqdn, custom_docker_run_options,
      created_at, updated_at, description, health_check_type
    ) VALUES (
      '${APP_UUID}', '${APP_NAME}', '${GIT_REPO}', '${GIT_BRANCH}', 'HEAD', 'dockerfile', 'nginx:alpine',
      '80', '${BASE_DIR}', '/', '/', 'localhost', 'GET', 200, 'http',
      5, 5, 10, 5,
      '0', '0', 60, '0', '0', 1024, 'exited:unknown', '{{pr_id}}.{{domain}}',
      'App\Models\StandaloneDocker', ${SERVER_DESTINATION_ID},
      'App\Models\GithubApp', ${GITHUB_APP_SOURCE_ID}, ${ENV_ID},
      true, '/Dockerfile', '${DOMAIN}',
      '-v /data/mrluc-second-brain:/data/mrluc',
      NOW(), NOW(), 'Second Brain — MrLUC dashboard + supercronic', 'http'
    ) RETURNING id;")
  echo "Created application id=${APP_ID} uuid=${APP_UUID}"

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

  echo "Env vars: defaults in Dockerfile; add overrides in Coolify UI if needed."
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
     0, false, false, false,
     0, '0', '${APP_NAME}', 'DEVELOPMENT SERVER'
   WHERE NOT EXISTS (
     SELECT 1 FROM application_deployment_queues
     WHERE application_id='${APP_ID}' AND status IN ('queued','in_progress')
   )
   RETURNING id;")
if [[ -n "${QUEUE_ID}" ]]; then
  echo "Queued deployment id=${QUEUE_ID} — trigger via Coolify UI or push to ${GIT_BRANCH}"
fi

echo "Done. App UUID: ${APP_UUID:-$($PSQL -c "SELECT uuid FROM applications WHERE id=${APP_ID};")}"
echo "Domain: ${DOMAIN}"
echo "Branch: ${GIT_BRANCH} (auto_deploy should be enabled in application_settings)"
