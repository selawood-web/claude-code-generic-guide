#!/usr/bin/env bash
# update.sh — refresh CCGG-owned files in an installed project from this guide.
#
#     ./update.sh /path/to/your-project        # verbose
#     ./update.sh --quiet /path/to/your-project # prints only when something changed
#
# The live-sync counterpart to install.sh: where install.sh never overwrites,
# update.sh DOES overwrite the files CCGG owns — skills, hooks, and the
# validator — so merged guide PRs reach installed projects. It never touches
# project-customized files (AGENTS.md, CLAUDE.md, WORKING-CHARTER.md,
# settings.json) and leaves skills the project added under its own names alone.
#
# Wired into every session automatically: the session-start hook runs
# `"$CCGG_HOME/update.sh" --quiet .` when the CCGG_HOME environment variable
# points at a local clone of this guide. Skills refresh mid-session on their
# next invocation; behavior rules load at the next session start.
#
# If you customized a CCGG skill in place, rename its directory (making it
# yours) or don't set CCGG_HOME — update.sh overwrites CCGG names.
set -euo pipefail

QUIET=0
if [ "${1:-}" = "--quiet" ]; then QUIET=1; shift; fi
SRC="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-.}"
if [ ! -d "$TARGET" ]; then
  echo "usage: ./update.sh [--quiet] /path/to/your-project"
  exit 1
fi
TARGET="$(cd "$TARGET" && pwd)"
# The guide repo itself needs no sync from itself.
if [ "$TARGET" = "$SRC" ]; then exit 0; fi

# Refresh the guide clone so the sync carries the latest merged master.
git -C "$SRC" pull --ff-only -q 2>/dev/null || true

changed=0
sync_file() { # $1 = path relative to both roots
  if ! cmp -s "$SRC/$1" "$TARGET/$1" 2>/dev/null; then
    mkdir -p "$TARGET/$(dirname "$1")"
    # Atomic rename, never in-place cp: this may replace the very hook that is
    # running us, and truncating a running script's inode corrupts its execution.
    tmp="$TARGET/$1.ccgg-tmp.$$"
    cp "$SRC/$1" "$tmp" && mv -f "$tmp" "$TARGET/$1"
    changed=$((changed+1))
    if [ "$QUIET" -eq 0 ]; then echo "  ~ $1"; fi
  fi
}

# CCGG-owned surface: every skill file, every hook, the validator.
while IFS= read -r f; do
  sync_file "${f#"$SRC"/}"
done < <(find "$SRC/.claude/skills" "$SRC/.claude/hooks" -type f 2>/dev/null)
sync_file "tools/validate.py"
sync_file "tools/catalog.py"

chmod +x "$TARGET"/.claude/hooks/*.sh 2>/dev/null || true

# Regenerate the target's marked catalog tables and counts from the synced
# skills (no-op where the markers are absent or python3 is missing).
if [ -f "$TARGET/tools/catalog.py" ] && command -v python3 >/dev/null 2>&1; then
  (cd "$TARGET" && python3 tools/catalog.py --write >/dev/null 2>&1) || true
fi

REV="$(git -C "$SRC" rev-parse --short HEAD 2>/dev/null || echo unknown)"
if [ "$changed" -gt 0 ]; then
  echo "-- ccgg update: $changed file(s) refreshed to guide@$REV --"
elif [ "$QUIET" -eq 0 ]; then
  echo "ccgg update: already current with guide@$REV"
fi
