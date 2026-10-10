#!/usr/bin/env bash
# A17 — GitHub ruleset on second-brain-vault main:
#   humans = require pull request; Coolify deploy keys = bypass always.
# Requires GitHub Pro (personal) or Team/Enterprise (org) on the repo owner.
# Usage: bash scripts/vault_apply_ruleset_a17.sh
set -euo pipefail

REPO="${VAULT_GITHUB_REPO:-LC-RBEDU/second-brain-vault}"
NAME="main-human-pr-deploykey-bypass"

probe="$(gh api "repos/${REPO}/rulesets" 2>&1)" || true
if echo "$probe" | grep -qi 'Upgrade to GitHub Pro'; then
  echo "vault_apply_ruleset_a17: FAIL — ${REPO} still on Free private (rulesets 403 Pro)." >&2
  echo "Upgrade: https://github.com/settings/billing/plans  (account that owns ${REPO})" >&2
  echo "Then re-run: bash scripts/vault_apply_ruleset_a17.sh" >&2
  exit 2
fi

# Idempotent: update existing ruleset with same name, else create.
existing_id="$(gh api "repos/${REPO}/rulesets" --jq ".[] | select(.name==\"${NAME}\") | .id" | head -1 || true)"

body="$(cat <<'JSON'
{
  "name": "main-human-pr-deploykey-bypass",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [
    {
      "actor_id": null,
      "actor_type": "DeployKey",
      "bypass_mode": "always"
    }
  ],
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
      }
    },
    {
      "type": "non_fast_forward"
    }
  ]
}
JSON
)"

if [[ -n "${existing_id}" ]]; then
  echo "Updating ruleset id=${existing_id} on ${REPO}"
  echo "$body" | gh api -X PUT "repos/${REPO}/rulesets/${existing_id}" --input -
else
  echo "Creating ruleset on ${REPO}"
  echo "$body" | gh api -X POST "repos/${REPO}/rulesets" --input -
fi

echo "vault_apply_ruleset_a17: OK"
gh api "repos/${REPO}/rulesets" --jq '.[] | {id,name,enforcement,target}'
