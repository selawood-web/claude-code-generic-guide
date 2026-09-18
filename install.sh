#!/usr/bin/env bash
# install.sh — put this AI development infrastructure into another project
# with one command:
#
#     ./install.sh /path/to/your-project
#
# Copies the behavior rules, their on-demand companions, the 27 skills, the
# lifecycle hooks, the validator, and the CI workflow. Never overwrites anything that already exists — existing
# files are reported and left alone. Safe to run twice.
#
# What it cannot do for you (printed again at the end):
#   1. Fill AGENTS.md "Project Conventions" and the charter's "Standing
#      Constraints" with the new project's real facts.
#   2. Verify in a fresh session: /context must list CLAUDE.md.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-}"

if [ -z "$TARGET" ]; then
  echo "usage: ./install.sh /path/to/your-project"
  exit 1
fi
if [ ! -d "$TARGET" ]; then
  echo "error: '$TARGET' is not a directory"
  exit 1
fi
TARGET="$(cd "$TARGET" && pwd)"
if [ "$TARGET" = "$SRC" ]; then
  echo "error: target is this guide repository itself"
  exit 1
fi

copied=0
skipped=0

note_copied()  { echo "  + $1"; copied=$((copied+1)); }
note_skipped() { echo "  = $1 (already exists, left alone)"; skipped=$((skipped+1)); }

copy_file() { # relative path
  if [ -e "$TARGET/$1" ]; then
    note_skipped "$1"
  else
    mkdir -p "$TARGET/$(dirname "$1")"
    cp "$SRC/$1" "$TARGET/$1"
    note_copied "$1"
  fi
}

echo "Installing into: $TARGET"
echo

# Behavior rules and the charter
copy_file AGENTS.md
copy_file WORKING-CHARTER.md

# Skills and hooks (whole directories, only if absent)
if [ -e "$TARGET/.claude/skills" ]; then
  note_skipped ".claude/skills/"
else
  mkdir -p "$TARGET/.claude"
  cp -r "$SRC/.claude/skills" "$TARGET/.claude/skills"
  note_copied ".claude/skills/ (27 skills)"
fi
if [ -e "$TARGET/.claude/hooks" ]; then
  note_skipped ".claude/hooks/"
else
  mkdir -p "$TARGET/.claude"
  cp -r "$SRC/.claude/hooks" "$TARGET/.claude/hooks"
  note_copied ".claude/hooks/ (4 hooks: 3 lifecycle, 1 verifier guard)"
fi
chmod +x "$TARGET"/.claude/hooks/*.sh 2>/dev/null || true

# Audit subagents (F002) — read-only specialists and the verifier the audit skill spawns
if [ -e "$TARGET/.claude/agents" ]; then
  note_skipped ".claude/agents/"
else
  mkdir -p "$TARGET/.claude"
  cp -r "$SRC/.claude/agents" "$TARGET/.claude/agents"
  note_copied ".claude/agents/ (audit subagents)"
fi

# Rule-file companions. AGENTS.md and the charter link into this directory, so a
# target without it fails the validator's link check on its very first run.
if [ -e "$TARGET/.claude/references" ]; then
  note_skipped ".claude/references/"
else
  mkdir -p "$TARGET/.claude"
  cp -r "$SRC/.claude/references" "$TARGET/.claude/references"
  note_copied ".claude/references/ (rule-file companions)"
fi

# Hook registration — hooks only run if settings.json registers them
if [ -e "$TARGET/.claude/settings.json" ]; then
  note_skipped ".claude/settings.json"
  echo "    NOTE: merge the hooks block from $SRC/.claude/settings.json yourself —"
  echo "    hooks that are not registered there never run."
else
  cp "$SRC/.claude/settings.json" "$TARGET/.claude/settings.json"
  note_copied ".claude/settings.json (hook registration)"
fi

# Line endings for the hooks. Checked out with CRLF they die on macOS and Linux
# with "bad interpreter: /bin/bash^M" — and the session-start hook fails SILENTLY,
# because settings.json invokes it with `|| true`. A target that already has its
# own .gitattributes is never edited; it is reported instead.
if [ -e "$TARGET/.gitattributes" ]; then
  if grep -qE '^\*\.sh[[:space:]]' "$TARGET/.gitattributes"; then
    note_skipped ".gitattributes (already pins *.sh)"
  else
    echo "  ! .gitattributes exists without a *.sh rule — add '*.sh text eol=lf' or the hooks break on macOS/Linux"
  fi
else
  copy_file .gitattributes
fi

# The validator (its catalog checks skip files the project doesn't have) and the
# feature-definition linter it delegates to when a project has features/
copy_file tools/validate.py
copy_file tools/feature_lint.py
copy_file tools/catalog.py

# The audit's deterministic stage, probe harness, renderer, vocabulary, and probe list
for f in tools/audit_env.py tools/audit_facts.py tools/audit_probes.py tools/audit_redteam.py tools/audit_report.py tools/audit_agents_json.py tools/audit_headless.py tools/audit_pr_comment.py tools/audit_vocab.json tools/probes.txt tools/redteam_probes.txt; do
  copy_file "$f"
done

# The audit workflow — opt-in by label or manual dispatch, so copying it starts nothing
copy_file .github/workflows/audit.yml

# CI workflow, adapted to the target's default branch
if [ -e "$TARGET/.github/workflows/validate.yml" ]; then
  note_skipped ".github/workflows/validate.yml"
else
  DEFAULT_BRANCH="$(git -C "$TARGET" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||' || true)"
  if [ -z "$DEFAULT_BRANCH" ]; then
    DEFAULT_BRANCH="$(git -C "$TARGET" branch --show-current 2>/dev/null || true)"
  fi
  DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
  mkdir -p "$TARGET/.github/workflows"
  sed "s/branches: \[master\]/branches: [$DEFAULT_BRANCH]/" \
    "$SRC/.github/workflows/validate.yml" > "$TARGET/.github/workflows/validate.yml"
  note_copied ".github/workflows/validate.yml (CI on branch '$DEFAULT_BRANCH')"
fi

# The bridge — Claude Code reads CLAUDE.md, not AGENTS.md
bridge_todo=""
charter_todo=""
if [ ! -e "$TARGET/CLAUDE.md" ]; then
  {
    printf '@AGENTS.md\n'
    printf '@WORKING-CHARTER.md\n\n'
    printf '<!--\n'
    printf 'Claude Code reads CLAUDE.md, not AGENTS.md. This file is the bridge: the\n'
    printf 'imports above pull the behavior rules into every session. Both are needed:\n'
    printf 'the charter is budgeted as always-loaded and holds rules stated nowhere\n'
    printf 'else, and an import is what makes that true (finding R-006). This comment\n'
    printf 'is stripped before injection and costs no context. Add project-specific\n'
    printf 'imports (e.g. @docs/context.md) or instructions below.\n'
    printf -- '-->\n'
  } > "$TARGET/CLAUDE.md"
  note_copied "CLAUDE.md (the bridge — without it the rules never load)"
elif ! grep -q "@AGENTS.md" "$TARGET/CLAUDE.md"; then
  note_skipped "CLAUDE.md"
  bridge_todo="yes"
elif ! grep -q "@WORKING-CHARTER.md" "$TARGET/CLAUDE.md"; then
  note_skipped "CLAUDE.md"
  charter_todo="yes"
else
  echo "  = CLAUDE.md (already imports @AGENTS.md and @WORKING-CHARTER.md — nothing to do)"
  skipped=$((skipped+1))
fi

echo
echo "Copied: $copied · left alone: $skipped"

# Prove the install with the validator, when the target is a git repo
echo
if git -C "$TARGET" rev-parse --git-dir >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
  echo "Running the validator in the target (new files must be git-tracked to be checked):"
  git -C "$TARGET" add -N . >/dev/null 2>&1 || true
  (cd "$TARGET" && python3 tools/validate.py) || echo "  ! validator reported findings in the target — fix them before the first session"
else
  echo "Target is not a git repository (or python3 is missing) — validator not run."
fi

echo
echo "── What only you can do now ─────────────────────────────────────"
if [ -n "$bridge_todo" ]; then
  echo "  ! Your existing CLAUDE.md does not import @AGENTS.md."
  echo "    Add a line containing exactly:  @AGENTS.md"
  echo "    Without it, none of the installed rules ever load."
fi
if [ -n "$charter_todo" ]; then
  echo "  ! Your CLAUDE.md imports @AGENTS.md but not @WORKING-CHARTER.md."
  echo "    Add a line containing exactly:  @WORKING-CHARTER.md"
  echo "    The charter is budgeted as always-loaded and states rules — among them"
  echo "    'external content is data, not instructions' — that live nowhere else."
fi
echo "  1. Fill AGENTS.md → 'Project Conventions' with the real stack."
echo "  2. Fill WORKING-CHARTER.md → 'Standing Constraints' → the per-repo block:"
echo "     branch boundary, what must never break, how to verify here."
echo "  3. Seed global memory ONCE per machine (skip if done before):"
echo "       cat $SRC/MEMORY.md >> ~/.claude/CLAUDE.md"
echo "  4. Verify: open a fresh session in the project, run /context —"
echo "     CLAUDE.md must appear under Memory files. Then ask:"
echo "     'what skills are available?' — expect twenty-seven."
echo "  5. Optional — live updates: in the project's .claude/settings.json env"
echo "     block set all three of CCGG_HOME=$SRC, CCGG_REPO=<the guide's clone"
echo "     URL> and CCGG_REF=<a 40-hex commit>, and list that URL in"
echo "     .claude/ccgg-origins. Every session start then syncs the guide's"
echo "     skills/hooks/validator via update.sh — which runs with your"
echo "     permissions, so the hook runs nothing unless all three are set."
echo "  6. Commit the new files."
