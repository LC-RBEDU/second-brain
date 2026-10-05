#!/usr/bin/env bash
# Symlink vendor skills (skills.sh → ~/.agents/skills) into ~/.cursor/skills for Cursor discovery.
# Reinstall packages first if missing:
#   npx skills add n8n-io/skills -g -a cursor \
#     -s n8n-debugging-official -s n8n-credentials-and-security-official \
#     -s n8n-error-handling-official -s n8n-workflow-lifecycle-official \
#     -s using-n8n-skills-official -y
#   npx skills add mattpocock/skills -g -a cursor -s grill-me -s grilling -y
set -euo pipefail

SRC="${HOME}/.agents/skills"
DEST="${HOME}/.cursor/skills"
mkdir -p "$DEST"

skills=(
  n8n-credentials-and-security-official
  n8n-debugging-official
  n8n-error-handling-official
  n8n-workflow-lifecycle-official
  using-n8n-skills-official
  grill-me
  grilling
)

for s in "${skills[@]}"; do
  if [ ! -d "$SRC/$s" ]; then
    echo "missing: $SRC/$s (run npx skills add … first)" >&2
    continue
  fi
  rm -rf "${DEST:?}/$s"
  ln -sfn "$SRC/$s" "$DEST/$s"
  echo "linked $DEST/$s -> $SRC/$s"
done

echo "done: external skills → $DEST"
