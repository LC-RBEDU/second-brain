#!/usr/bin/env bash
# Install agenda skills as symlinks from ŠABLONY/skills/ → ~/.cursor/skills/
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO_ROOT/ŠABLONY/skills"
DEST="$HOME/.cursor/skills"

mkdir -p "$DEST"

for skill_dir in "$SRC"/agenda-*/; do
  skill="$(basename "$skill_dir")"
  target="$DEST/$skill"
  if [ -L "$target" ]; then
    rm "$target"
  elif [ -d "$target" ]; then
    rm -rf "$target"
  fi
  ln -s "$skill_dir" "$target"
  echo "linked $target -> $skill_dir"
done

# Remove deprecated Claude copies
if [ -d "$HOME/.claude/skills" ]; then
  for skill_dir in "$HOME/.claude/skills"/agenda-*/; do
    [ -d "$skill_dir" ] || continue
    rm -rf "$skill_dir"
    echo "removed $skill_dir"
  done
fi

echo "done: agenda skills → symlinks in $DEST"
