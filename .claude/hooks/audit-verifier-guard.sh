#!/usr/bin/env bash
# Hook: audit-verifier-guard (PreToolUse, matcher Bash)
# Registered by: .claude/agents/audit-verifier.md, for that subagent only.
# Purpose: refuse write-shaped, network, and install commands from the audit's
#          verifier, as a second layer under the worktree isolation the runtime
#          already enforces. Exit 2 blocks the call; the reason on stderr reaches
#          the model. Anything the guard cannot parse is refused — it fails closed.
#
# Not registered in settings.json on purpose: this guard is scoped to one
# subagent. The audit's deterministic stage knows that and does not flag it.
set -uo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "audit-verifier-guard: python3 is required to inspect the command; refusing" >&2
  exit 2
fi

# The hook's JSON arrives on stdin; capture it before anything else reads stdin.
INPUT="$(cat)"

read -r -d '' GUARD <<'PY' || true
import json, re, sys
try:
    payload = json.load(sys.stdin)
except ValueError:
    print("audit-verifier-guard: hook input is not JSON; refusing", file=sys.stderr)
    sys.exit(2)
if payload.get("tool_name") != "Bash":
    sys.exit(0)
command = str((payload.get("tool_input") or {}).get("command", ""))
denied = [
    (r"\bgit\s+push\b", "git push"),
    (r"\bgit\s+(commit|merge|rebase|reset\s+--hard|checkout|switch|stash|clean)\b", "git write"),
    (r"\brm\b", "rm"),
    (r"\b(curl|wget|ssh|scp|rsync|nc|ncat)\b", "network"),
    (r"\b(pip|pip3|npm|pnpm|yarn|cargo|go|gem|brew|apt|apt-get|dnf)\s+(install|add|get)\b", "package install"),
    (r"\b(sudo|chmod|chown|mkfs|dd)\b", "privilege or disk"),
    (r"\b(tee|truncate)\b|>>?\s*[^&|\s]", "redirect to file"),
    (r"\bmv\b|\bcp\b", "move or copy"),
]
for pattern, label in denied:
    if re.search(pattern, command):
        print(f"audit-verifier-guard: refused ({label}): the verifier reproduces findings with read-only commands only", file=sys.stderr)
        sys.exit(2)
sys.exit(0)
PY

printf '%s' "$INPUT" | python3 -c "$GUARD"
