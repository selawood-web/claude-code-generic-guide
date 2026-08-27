# Permissions and Safety Controls

Claude Code can perform powerful actions on your behalf — reading files, searching code, editing files, and running arbitrary shell commands. The permission system gives you fine-grained control over what the agent is allowed to do, with multiple layers you can combine for strong safety.

This guide explains how permissions work, the available locked-down modes (especially `dontAsk`), how to configure them via CLI, native config, or Claude settings, and how to use **PreToolUse hooks** to create hard allow-lists such as "only `git` and `gh` commands".

---

## Decision Flow (How a Tool Call Is Authorized)

When the model requests a tool, the following checks happen in order:

1. **PreToolUse Hooks** (if any) — Registered hooks can deny a tool call before any other checks. See [10-hooks.md](10-hooks.md) for how to write and install them. Hooks run earliest and take precedence.

2. **Policy Rules** (from config, Claude settings, or `--allow`/`--deny` flags)
   - Explicit `deny` rules win (even over allow rules).
   - `ask` rules force a prompt.
   - `allow` rules short-circuit to approval.

3. **Built-in Fast Paths** (no prompt needed)
   - Read-class tools (`read_file`, `list_dir`, `web_search`, `todo_write`, skills, subagent control, etc.)
   - Grep-class tools
   - A curated set of safe, read-only shell commands (see below)

4. **Prompt Policy** (controlled by `--permission-mode` or `defaultMode`)
   - `default` → prompt the user for anything not pre-approved
   - `dontAsk` → silently deny anything not pre-approved (ideal for headless/CI)
   - `bypassPermissions` → auto-allow almost everything
   - `acceptEdits` → auto-allow file edits
   - `plan` → special behavior for plan mode

5. **User Prompt** (in interactive TUI) or denial (in `dontAsk` / headless)

This layered approach lets you combine broad policy with very specific hooks.

---

## Always-Safe Operations (Never Prompt)

Certain operations are intentionally side-effect-free and are **always allowed** without prompting, even under `dontAsk`.

### Read-Class Tools

The following tools are auto-approved because they are considered read-only:

- `read_file`
- `list_dir`
- `web_search`
- `todo_write`
- `get_task_output` / `wait_tasks` / `kill_task` (subagent control)
- Invoking skills
- Various IDE extension and plugin read operations
- Most future plugin / dynamic tools (treated conservatively as reads)

### Grep-Class Tools

- `grep` (ripgrep content search)

### Safe Shell Commands

After parsing and splitting chained commands (for `&&`, `||`, `;`, pipes, etc.), the following commands are recognized as safe when they appear as the **primary command** (word-boundary matched, so `ls` does not match `lsof` or `less`).

**Filesystem (read-only viewing):**
- `ls`, `cat`, `pwd`, `date`, `whoami`, `hostname`, `uptime`, `ps`
- `head`, `tail`, `wc`, `sort`, `uniq`, `tr`, `cut`

**Git (read-only):**
- `git status`, `git branch`, `git log`, `git diff`, `git ls-files`, `git show`, `git rev-parse`

**Search & Inspection:**
- `grep`

**Build & Check (read-only):**
- `cargo check`

**Kubernetes (read-only):**
- `kubectl get`, `kubectl logs`, `kubectl describe`

**Internal tooling:**
- `bin/explorer ls`

**Note:** `tee` is not included in the safe list because it can write its input to arbitrary files.

These checks are applied **per segment**. A command like `ls && rm -rf /` will have its `rm` segment rejected even though `ls` is safe.

---

## Permission Modes

Use `--permission-mode MODE` (headless) or set it persistently in the TUI.

Valid values:

| Mode                | Behavior                                                                 | Typical Use                     |
|---------------------|--------------------------------------------------------------------------|---------------------------------|
| `default`           | Normal prompting for anything not pre-approved                           | Daily interactive use           |
| `dontAsk`           | Silently deny anything without an explicit allow rule or fast-path       | Headless, CI, high-security     |
| `bypassPermissions` | Auto-approve almost everything (very permissive)                         | Trusted environments            |
| `acceptEdits`       | Auto-approve file edits (`search_replace`, `write`, etc.)                | "Accept edits" workflows        |
| `plan`              | Plan-mode specific behavior                                              | Structured planning sessions    |
| `auto`              | Background safety classifier (experimental / forward-compat)             | Future use                      |

You can also set the mode persistently via the TUI (it saves to your config). Claude settings `defaultMode` is also supported for compatibility.

---

## Configuring Permissions

Claude Code supports three compatible configuration sources. They are merged with well-defined precedence.

### 1. CLI Flags

```bash
claude -p "Review the API changes" \
  --permission-mode dontAsk \
  --allow 'Bash(git *)' \
  --allow 'Bash(gh *)' \
  --allow 'Read' \
  --allow 'Grep' \
  --deny 'Bash(rm -rf *)'
```

- `--permission-mode` sets the base policy
- `--allow RULE` and `--deny RULE` can be repeated

Rule syntax examples:
- `Bash(git *)` — any command starting with `git `
- `Bash(npm run build)` — exact command (or prefix)
- `Read(src/**)` — read access under `src/`
- `Edit(**/*.rs)` — edit any Rust file
- `Grep` — all grep operations
- `Mcp(my-server__*)` — MCP tools from a specific server

### 2. Native Configuration (`~/.claude/config.toml` and `.claude/config.toml`)

```toml
[permission]
rules = [
  { action = "allow", tool = "bash", pattern = "git *" },
  { action = "allow", tool = "bash", pattern = "gh *" },
  { action = "allow", tool = "read" },
  { action = "allow", tool = "grep" },
  { action = "deny",  tool = "bash", pattern = "*" },   # catch-all deny for bash
  { action = "ask",   tool = "edit" },
]
```

Project-level `.claude/config.toml` takes precedence over the global one (whole-section override).

### 3. Claude Code Compatibility (`.claude/settings.json`)

Claude Code reads `~/.claude/settings.json`, `<project>/.claude/settings.json`, and their `.claude` equivalents.

Example:

```json
{
  "defaultMode": "dontAsk",
  "permissions": {
    "allow": [
      "Read",
      "Grep",
      "Bash(git *)",
      "Bash(gh *)"
    ],
    "deny": [
      "Bash(rm -rf *)"
    ]
  }
}
```

Supported `defaultMode` values match the `--permission-mode` table above.

`permissions.allow` and `permissions.deny` entries are translated into native rules. You can import existing Claude settings interactively with **Ctrl+I** ("Import Claude settings").

---

## Restrictive Hooks — The `git + gh` Only Example

For the strongest control, use a `PreToolUse` hook that acts as a hard allow-list on the `Bash` tool. Hooks are evaluated before the permission system.

### Global `git-gh-only` Hook

This example only permits `git` and `gh` commands:

**`~/.claude/hooks/git-gh-only.json`**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "git-gh-only.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**`~/.claude/hooks/git-gh-only.sh`**

```bash
#!/bin/sh
# Allow only commands whose first word is "git" or "gh".

set -eu

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.toolInput.command // empty' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

if [ -z "$CMD" ]; then
  echo '{"decision": "deny", "reason": "Empty command is not allowed"}'
  exit 2
fi

FIRST_WORD=$(echo "$CMD" | awk '{print $1}')

case "$FIRST_WORD" in
  git|gh)
    echo '{"decision": "allow"}'
    exit 0
    ;;
  *)
    echo '{"decision": "deny", "reason": "Only git and gh commands are permitted. Blocked: '"$CMD"'"}'
    exit 2
    ;;
esac
```

```bash
chmod +x ~/.claude/hooks/git-gh-only.sh
```

With this hook active, combined with `--permission-mode dontAsk` and narrow allow rules, the agent is restricted to `git`/`gh` plus safe read operations.

For full details on hook installation, the JSON format, trust model for project hooks, and other events, see [10-hooks.md](10-hooks.md) (which also contains a complementary "block dangerous patterns" example).

---

## Example Configurations

### Headless "git + gh only" (recommended for CI / automation)

```bash
claude -p "Implement the feature using only git and GitHub CLI" \
  --permission-mode dontAsk \
  --allow 'Read' \
  --allow 'Grep' \
  --allow 'Bash(git *)' \
  --allow 'Bash(gh *)'
```

Plus the `git-gh-only` hook for additional restrictions.

### Read-only code reviewer

```toml
# .claude/config.toml
[permission]
rules = [
  { action = "allow", tool = "read" },
  { action = "allow", tool = "grep" },
  { action = "deny",  tool = "edit" },
  { action = "deny",  tool = "bash" },
]
```

### Daily driver

Use `default` mode plus narrow `Bash(...)` allow rules for common safe commands (`git`, `cargo test`, `rg`, etc.).

---

## Combining with Sandbox

Permissions control *what the model is allowed to request*. The OS-level sandbox (see [18-sandbox.md](18-sandbox.md)) controls what the actual process can do even if a command is approved.

Recommended stack for untrusted code:

1. `dontAsk` + narrow allow rules or restrictive hook
2. `--sandbox strict` or a custom profile
3. Project trust + careful review of any `SessionStart` hooks

---

## Managing Permissions in the TUI

- **Ctrl+L** (or `/hooks`) — View and manage loaded hooks (including trust for project hooks). See [10-hooks.md](10-hooks.md) for details.
- Permission decisions appear in the transcript.
- The current permission mode can be changed and saved from within the TUI.

---

## Best Practices

1. **Prefer narrow patterns** — `Bash(git *)` is much safer than a broad `Bash` allow rule.
2. **Combine layers** — `dontAsk` + explicit narrow allows + restrictive hook + sandbox provides strong restrictions.
3. **Review project hooks** — See the security notes in [10-hooks.md](10-hooks.md). Never blindly trust hooks from untrusted repositories.
4. **Test your policy** — Run commands with `--permission-mode dontAsk` and observe what gets blocked.
5. **The safe bash list is for convenience, not a security boundary** — It only covers obviously read-only commands. Do not rely on it alone for dangerous environments.

---

## Summary

- Multiple independent layers (hooks → policy → fast-paths → prompt policy) work together.
- `dontAsk` + explicit narrow allow rules is the most common way to run the agent safely in non-interactive contexts.
- The `git-gh-only` hook pattern is a proven, minimal example of a positive allow-list for shell.
- Native TOML, Claude JSON, and CLI flags all work together.

Use these controls to run the agent with only the privileges it needs.

---

Cross-references:
- [10-hooks.md](10-hooks.md) — Full hook authoring guide
- [14-headless-mode.md](14-headless-mode.md) — All headless flags including permission-related ones
- [18-sandbox.md](18-sandbox.md) — OS-level isolation profiles
- [05-configuration.md](05-configuration.md) — Native `config.toml` structure