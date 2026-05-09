#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_HOME="${CLAUDE_SKILLS_HOME:-$HOME/.claude/skills}"

echo "==> Project dir: $PROJECT_DIR"
echo "==> Skills home: $SKILLS_HOME"

mkdir -p "$SKILLS_HOME"

installed=0
skipped=0

for skill_dir in "$PROJECT_DIR"/*/SKILL.md; do
  [ -f "$skill_dir" ] || continue
  skill_path="$(dirname "$skill_dir")"
  skill_name="$(basename "$skill_path")"
  link_path="$SKILLS_HOME/$skill_name"

  if [ -L "$link_path" ]; then
    current_target="$(readlink "$link_path")"
    if [ "$current_target" = "$skill_path" ]; then
      echo "  [SKIP] $skill_name (already linked)"
      skipped=$((skipped + 1))
      continue
    fi
    echo "  [REPLACE] $skill_name ($current_target -> $skill_path)"
    rm "$link_path"
  elif [ -e "$link_path" ]; then
    echo "  [WARN] $skill_name: $link_path exists and is not a symlink, skipping"
    skipped=$((skipped + 1))
    continue
  fi

  ln -s "$skill_path" "$link_path"
  echo "  [OK] $skill_name -> $skill_path"
  installed=$((installed + 1))
done

echo ""
echo "Done: $installed installed, $skipped skipped."
