#!/usr/bin/env bash
# Hook: skill-usage (PostToolUse on Skill, UserPromptExpansion)
# Registered by: .claude/settings.json.
# Purpose: count which skills actually run, so /efficiency can name the ones
#          that never do. Every skill's description is paid for in every
#          session's context; which of them earn that was a guess.
#
# Two events, because they do not overlap (measured on CLI 2.1.317): a skill the
# model calls arrives as PostToolUse with tool_name "Skill" and the name in
# tool_input.skill; a skill the user types as /name arrives as
# UserPromptExpansion with command_name, and does not also fire PostToolUse.
#
# Each use appends one line — "<UTC stamp> <name> <model|typed>" — to
# ~/.claude/memory/<project>/skill-usage.log, a machine-local file. /flush
# tallies the lines since its last marker into the committed session log, which
# is what survives a discarded container. A typed command is recorded only when
# a skill by that name exists (project or user level); a name outside
# [A-Za-z0-9:._-], or longer than 64 characters, is not recorded at all.
#
# This script prints nothing and always exits 0: it observes, never steers.
# CCGG_SKILL_USAGE=off disables it.
set -uo pipefail

[ "${CCGG_SKILL_USAGE:-}" = "off" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0

PROJECT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG_DIR="${HOME}/.claude/memory/$(basename "$PROJECT")"

# The program goes in through -c, never on stdin: stdin is the hook's payload.
# -I: isolated mode, so nothing in the project directory is imported.
read -r -d '' PROGRAM <<'PY' || true
import datetime, json, os, re, sys

project, log_dir, home = sys.argv[1:4]
try:
    data = json.loads(sys.stdin.read())
except ValueError:
    sys.exit(0)
if not isinstance(data, dict):
    sys.exit(0)

event = data.get("hook_event_name")
name = source = None
if event == "PostToolUse" and data.get("tool_name") == "Skill":
    tool_input = data.get("tool_input")
    if isinstance(tool_input, dict):
        name, source = tool_input.get("skill"), "model"
elif event == "UserPromptExpansion":
    name, source = data.get("command_name"), "typed"

if not isinstance(name, str):
    sys.exit(0)
name = name.lstrip("/")
if not re.fullmatch(r"[A-Za-z0-9:._-]{1,64}", name) or name.startswith("."):
    sys.exit(0)
if source == "typed" and ":" not in name:
    homes = (os.path.join(project, ".claude", "skills"), os.path.join(home, ".claude", "skills"))
    if not any(os.path.isfile(os.path.join(d, name, "SKILL.md")) for d in homes):
        sys.exit(0)   # a slash command, not a skill

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
try:
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "skill-usage.log"), "a", encoding="utf-8") as fh:
        fh.write(f"{stamp} {name} {source}\n")
except OSError:
    pass
PY
python3 -I -c "$PROGRAM" "$PROJECT" "$LOG_DIR" "${HOME}" 2>/dev/null || true
exit 0
