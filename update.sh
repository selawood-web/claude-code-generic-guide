#!/usr/bin/env bash
# update.sh — refresh CCGG-owned files in an installed project from this guide.
#
#     ./update.sh /path/to/your-project         # verbose
#     ./update.sh --quiet /path/to/your-project # prints only when something changed
#     ./update.sh --user                        # refresh personal skills instead
#
# The live-sync counterpart to install.sh: where install.sh never overwrites,
# update.sh DOES overwrite the files CCGG owns — skills, hooks, audit subagents,
# rule-file companions, the validator and audit tooling — so merged guide PRs
# reach installed projects. tools/probes.txt and tools/redteam_probes.txt are the
# project's own contracts and are installed once, never overwritten. It never touches
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
#
# --user targets the personal skills directory ($CLAUDE_CONFIG_DIR, else
# ~/.claude) instead of a project. Skills there are available in every session
# whatever folder Claude opens, but nothing refreshes them on its own: with no
# project there is no session-start hook to run this script, so re-run
# `./update.sh --user` after pulling the guide. It syncs skills only — hooks
# need a settings.json to invoke them and installing project hooks globally
# would run them in unrelated repositories, while the validator and catalog
# need a repository to act on.
#
# Neither mode deletes anything. A skill directory present in the target but
# absent from the guide — one of yours, or the remains of an upstream rename —
# is reported so you can decide.
set -euo pipefail

QUIET=0
USER_MODE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --quiet) QUIET=1; shift ;;
    --user)  USER_MODE=1; shift ;;
    *)       break ;;
  esac
done

SRC="$(cd "$(dirname "$0")" && pwd)"

if [ "$USER_MODE" -eq 1 ]; then
  TARGET="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
  mkdir -p "$TARGET/skills"
  SKILLS_DIR="skills"
else
  TARGET="${1:-.}"
  if [ ! -d "$TARGET" ]; then
    echo "usage: ./update.sh [--quiet] /path/to/your-project"
    echo "       ./update.sh [--quiet] --user"
    exit 1
  fi
  SKILLS_DIR=".claude/skills"
fi
TARGET="$(cd "$TARGET" && pwd)"
# The guide repo itself needs no sync from itself.
if [ "$TARGET" = "$SRC" ]; then exit 0; fi

# Refresh the guide clone. With CCGG_REF set (the session-start hook's pin), fetch
# exactly that tag, branch, or commit and check it out detached, so the sync never drifts
# past the pinned revision; without it, follow the clone's own branch.
if [ -n "${CCGG_REF:-}" ]; then
  git -C "$SRC" fetch -q --depth 1 --force origin "+${CCGG_REF}:refs/ccgg/pin" 2>/dev/null \
    && git -C "$SRC" checkout -q --detach refs/ccgg/pin 2>/dev/null \
    || echo "ccgg update: could not fetch CCGG_REF from origin; syncing the clone as it is"
else
  git -C "$SRC" pull --ff-only -q 2>/dev/null \
    || echo "ccgg update: could not pull the clone's branch; syncing the clone as it is"
fi

changed=0
sync_file() { # $1 = path under SRC; $2 = path under TARGET (defaults to $1)
  src_rel="$1"
  dst_rel="${2:-$1}"
  if ! cmp -s "$SRC/$src_rel" "$TARGET/$dst_rel" 2>/dev/null; then
    mkdir -p "$TARGET/$(dirname "$dst_rel")"
    # Atomic rename, never in-place cp: this may replace the very hook that is
    # running us, and truncating a running script's inode corrupts its execution.
    tmp="$TARGET/$dst_rel.ccgg-tmp.$$"
    cp "$SRC/$src_rel" "$tmp" && mv -f "$tmp" "$TARGET/$dst_rel"
    changed=$((changed+1))
    if [ "$QUIET" -eq 0 ]; then echo "  ~ $dst_rel"; fi
  fi
}

# Skills are CCGG-owned in both modes. The destination differs because the
# personal directory has no .claude/ level of its own.
while IFS= read -r f; do
  rel="${f#"$SRC"/}"
  sync_file "$rel" "$SKILLS_DIR/${rel#.claude/skills/}"
done < <(find "$SRC/.claude/skills" -type f 2>/dev/null)

# Hooks, validator and catalog are project-only — see the --user note above.
if [ "$USER_MODE" -eq 0 ]; then
  while IFS= read -r f; do
    sync_file "${f#"$SRC"/}"
  done < <(find "$SRC/.claude/hooks" -type f 2>/dev/null)
  while IFS= read -r f; do
    sync_file "${f#"$SRC"/}"
  done < <(find "$SRC/.claude/references" -type f 2>/dev/null)
  while IFS= read -r f; do
    sync_file "${f#"$SRC"/}"
  done < <(find "$SRC/.claude/agents" -type f 2>/dev/null)
  sync_file "tools/validate.py"
  sync_file "tools/feature_lint.py"
  sync_file "tools/catalog.py"
  for f in tools/audit_env.py tools/audit_facts.py tools/audit_probes.py tools/audit_redteam.py tools/audit_report.py tools/audit_agents_json.py tools/audit_headless.py tools/audit_pr_comment.py tools/audit_vocab.json; do
    sync_file "$f"
  done
  # The tests of the tools synced above travel with them. Without this a wired
  # project ran the validator, the verifier guard and the audit scripts with
  # no test able to catch a regression in them, and its CI step "Unit tests for
  # the validator" skipped itself for want of a test file (MemoMe audit
  # 2026-09-19, T-001/T-006). test_install.py stays behind: install.sh is not
  # part of a wired project.
  for f in tools/test_validate.py tools/test_feature_lint.py tools/test_verifier_guard.py tools/test_session_start_hook.py            tools/test_audit_env.py tools/test_audit_facts.py tools/test_audit_probes.py tools/test_audit_redteam.py            tools/test_audit_report.py tools/test_audit_agents_json.py tools/test_audit_headless.py tools/test_audit_pr_comment.py; do
    [ -f "$SRC/$f" ] && sync_file "$f"
  done
  # The probe contracts are the project's own once it has them, so they are
  # never overwritten — but a project wired before they existed never got
  # them at all, and its audit's probe stages had "nothing to measure"
  # (MemoMe audit 2026-09-19, R-003). Installed once, when absent.
  for f in tools/probes.txt tools/redteam_probes.txt; do
    if [ -f "$SRC/$f" ] && [ ! -e "$TARGET/$f" ]; then
      cp "$SRC/$f" "$TARGET/$f"
      changed=$((changed+1))
      if [ "$QUIET" -eq 0 ]; then echo "  + $f (installed once; yours from now on)"; fi
    fi
  done
  chmod +x "$TARGET"/.claude/hooks/*.sh 2>/dev/null || true
fi

# Report, never remove. A directory the guide no longer ships is either the
# user's own skill or what an upstream rename left behind; deleting either
# unasked would destroy work or silently drop a skill still in use. Under
# --quiet (the session-start hook, whose output the model reads) only the
# count is printed: a directory name is content, not something to forward.
unknown=0
for d in "$TARGET/$SKILLS_DIR"/*/; do
  [ -d "$d" ] || continue
  name="$(basename "$d")"
  if [ ! -d "$SRC/.claude/skills/$name" ]; then
    unknown=$((unknown+1))
    if [ "$QUIET" -eq 0 ]; then
      echo "  ? $SKILLS_DIR/$name — not in the guide (yours, or left by a rename); left in place"
    fi
  fi
done
if [ "$QUIET" -eq 1 ] && [ "$unknown" -gt 0 ]; then
  echo "ccgg update: $unknown skill director$([ "$unknown" -eq 1 ] && echo y || echo ies) not in the guide; left in place (run update.sh without --quiet to list)"
fi

# Check the target's marked catalog tables and counts against the synced
# skills. Never rewritten from here: AGENTS.md is an always-loaded rules file
# and the owner regenerates it on purpose, in a commit they can read.
if [ "$USER_MODE" -eq 0 ] && [ -f "$TARGET/tools/catalog.py" ] && command -v python3 >/dev/null 2>&1; then
  if ! (cd "$TARGET" && python3 tools/catalog.py >/dev/null 2>&1); then
    echo "ccgg update: catalog tables are STALE after the sync — run: python3 tools/catalog.py --write"
  fi
fi

REV="$(git -C "$SRC" rev-parse --short HEAD 2>/dev/null || echo unknown)"
if [ "$changed" -gt 0 ]; then
  echo "-- ccgg update: $changed file(s) refreshed to guide@$REV --"
elif [ "$QUIET" -eq 0 ]; then
  echo "ccgg update: already current with guide@$REV"
fi
