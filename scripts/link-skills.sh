#!/usr/bin/env bash
set -euo pipefail
# Maintainer script: symlink every skill in this repo into the local harness
# skill directories (~/.claude/skills for Claude Code, ~/.agents/skills for
# Codex and other Agent Skills harnesses). Pass extra destination dirs as
# arguments, e.g. a project's .claude/skills. A `git pull` then keeps every
# linked skill current; re-run after adding, removing or renaming a skill.
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DESTS=("$HOME/.claude/skills" "$HOME/.agents/skills" "$@")
for DEST in "${DESTS[@]}"; do
  if [ -L "$DEST" ]; then
    case "$(readlink -f "$DEST")" in "$REPO"|"$REPO"/*)
      echo "error: $DEST resolves into this repo; remove it and re-run" >&2; exit 1;; esac
  fi
  mkdir -p "$DEST"
  for skill_md in "$REPO"/skills/*/SKILL.md; do
    src="$(dirname "$skill_md")"; name="$(basename "$src")"; target="$DEST/$name"
    if [ -e "$target" ] && [ ! -L "$target" ]; then rm -rf "$target"; fi
    ln -sfn "$src" "$target"; echo "linked $name -> $src ($DEST)"
  done
done
