#!/usr/bin/env bash
# Install agenda skills as symlinks from ŠABLONY/skills/ → ~/.cursor/skills/
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO_ROOT/ŠABLONY/skills"
DEST="$HOME/.cursor/skills"

mkdir -p "$DEST"

for skill_dir in "$SRC"/agenda-*/ "$SRC"/mrluc-loader/ "$SRC"/wiki-firemni-priority/ "$SRC"/tymovy-disk/ "$SRC"/rbe-writing-style/ "$SRC"/grammar-nazi/; do
  [ -d "$skill_dir" ] || continue
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

# Cursor agents (ŠABLONY/cursor-agents/*.md → ~/.cursor/agents/)
AGENTS_SRC="$REPO_ROOT/ŠABLONY/cursor-agents"
AGENTS_DEST="$HOME/.cursor/agents"
mkdir -p "$AGENTS_DEST"
if [ -d "$AGENTS_SRC" ]; then
  for agent_md in "$AGENTS_SRC"/*.md; do
    [ -f "$agent_md" ] || continue
    name="$(basename "$agent_md")"
    target="$AGENTS_DEST/$name"
    if [ -L "$target" ] || [ -f "$target" ]; then
      rm -f "$target"
    fi
    ln -s "$agent_md" "$target"
    echo "linked $target -> $agent_md"
  done
fi

# Remove deprecated Claude copies
if [ -d "$HOME/.claude/skills" ]; then
  for skill_dir in "$HOME/.claude/skills"/agenda-*/; do
    [ -d "$skill_dir" ] || continue
    rm -rf "$skill_dir"
    echo "removed $skill_dir"
  done
fi

echo "done: agenda skills + cursor-agents → symlinks in $DEST and $AGENTS_DEST"
