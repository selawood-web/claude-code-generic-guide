# Headless Mode and Scripting

Headless mode runs Claude Code non-interactively from the command line. It accepts a single prompt, executes it with full tool access, and returns the result. Use headless mode when you need to:

- **Automate tasks** -- CI/CD pipelines, pre-commit hooks, cron jobs
- **Script workflows** -- batch process files, chain with other tools
- **Build integrations** -- spawn as a sub-agent, embed in larger systems
- **Parse output programmatically** -- JSON output for downstream processing

---

## Basic Usage

The `-p` flag (short for `--single`) triggers headless mode:

```bash
claude -p "Your prompt here"
```

Claude Code processes the prompt, runs any necessary tools, and prints the result to stdout. The process exits when the response is complete.

---

## Command-Line Options

| Flag                    | Description                                           |
| ----------------------- | ----------------------------------------------------- |
| `-p, --single <PROMPT>` | The prompt to send (required for headless mode)       |
| `-m, --model <MODEL>`   | Model to use (e.g., `claude-sonnet`)              |
| `-s, --session-id <ID>` | Create or resume a headless session with this ID      |
| `-r, --resume <ID>`     | Resume an existing session (errors if not found)      |
| `-c, --continue`        | Continue the most recent session in current directory  |
| `--cwd <PATH>`          | Set working directory                                 |
| `--output-format <FMT>` | Output format: `plain`, `json`, `streaming-json`      |
| `--yolo`                | Auto-approve all tool executions                      |
| `--rules <TEXT>`        | Custom rules for the system prompt                    |
| `--tools <TOOLS>`       | Allowlist of built-in tools (comma-separated). Only listed tools are available. Headless only. |
| `--disallowed-tools <TOOLS>` | Denylist of built-in tools to remove (comma-separated). Supports `Agent` entries. Headless only. |
| `--max-turns <N>`       | Maximum number of agentic turns before stopping. Headless only. |
| `--effort <LEVEL>`      | Effort level (`low`, `medium`, `high`). Headless only. |
| `--permission-mode <MODE>` | Permission mode for tool approvals. Headless only. |
| `--allow <RULE>`        | Permission allow rule with glob patterns (repeatable). Works in TUI and headless. |
| `--deny <RULE>`         | Permission deny rule with glob patterns (repeatable). Works in TUI and headless. |
| `--prompt-json <JSON>`  | Prompt as JSON content blocks                         |
| `--prompt-file <PATH>`  | Prompt from a file                                    |
| `--verbatim`            | Send prompt exactly as given                          |
| `--no-auto-update`      | Disable update checks for this session                |
| `--sandbox <PROFILE>`   | Sandbox profile for filesystem/network access         |

> **Note:** `--tools`, `--disallowed-tools`, `--max-turns`, `--effort`, and `--permission-mode` are headless-only flags. If used in the interactive TUI, a warning is printed and the flag is ignored. `--allow` and `--deny` work in both modes. For more flags (agents, verification, worktrees), see [Additional Headless Flags](#additional-headless-flags).

### Tool Filtering

Use `--tools` to restrict the agent to an explicit set of tools (allowlist), or `--disallowed-tools` to remove specific tools from the default set (denylist). Both accept comma-separated tool names.

Tool names are internal tool IDs (e.g. the shell tool is `run_terminal_cmd`, not `bash`).

```bash
# Only allow read-only tools
claude -p "Explain this codebase" --tools "read_file,grep,list_dir"

# Remove web access and file editing
claude -p "Review this code" --disallowed-tools "web_search,web_fetch,search_replace"

# Remove shell access
claude -p "Review this code" --disallowed-tools "run_terminal_cmd"
```

`--disallowed-tools` also supports special `Agent` entries to control subagent spawning:

| Entry                  | Effect                                  |
| ---------------------- | --------------------------------------- |
| `Agent`                | Block all subagent spawning             |
| `Agent(explore)`       | Block the `explore` subagent type only  |
| `Agent(explore, plan)` | Block multiple specific types           |

```bash
# Prevent the agent from spawning any subagents
claude -p "Fix this bug" --disallowed-tools "Agent"

# Block only the explore subagent
claude -p "Refactor this module" --disallowed-tools "Agent(explore)"
```

When `--tools` is set, only the listed tools are available and default tool injection is disabled. When both flags are present, `--disallowed-tools` runs after `--tools`.

### Permission Rules (`--allow` / `--deny`)

Permission rules control whether specific tool invocations are auto-approved, denied, or require user confirmation. Unlike `--disallowed-tools` (which removes tools entirely), permission rules leave tools available but gate their execution.

Rules use `ToolPrefix(glob_pattern)` syntax:

| Prefix        | What it controls                   |
| ------------- | ---------------------------------- |
| `Bash(...)`   | Shell command execution            |
| `Edit(...)`   | File editing (path glob)           |
| `Write(...)`  | File writing (path glob)           |
| `Read(...)`   | File reading (path glob)           |
| `Grep(...)`   | Search operations (path glob)      |
| `WebFetch(...)` | URL fetching (glob or `domain:host`) |
| `MCPTool(...)` | MCP tool invocations              |

Glob patterns support `*` (single-level wildcard) and `**` (recursive). A bare prefix without parentheses matches all invocations of that type.

```bash
# Deny shell commands matching "rm*"
claude -p "Clean up this project" --deny "Bash(rm*)"

# Allow npm commands, deny sudo
claude -p "Set up the project" --allow "Bash(npm*)" --deny "Bash(sudo*)"

# Allow all bash commands (auto-approve without prompting)
claude -p "Build the project" --allow "Bash"
```

`--allow` and `--deny` can be repeated. Deny rules take precedence over allow rules.

---

## Output Formats

Headless mode supports three output formats, selected with `--output-format`.

### plain (default)

Human-readable text, suitable for direct display or piping:

```
Here's a summary of the codebase...
```

### json

A single JSON object emitted after the response completes. Contains the full response text, stop reason, session ID, and request ID:

```json
{
  "text": "Here's a summary of the codebase...",
  "stopReason": "EndTurn",
  "sessionId": "abc123",
  "requestId": "xyz789"
}
```

The `sessionId` field is useful for resuming the conversation later.

### streaming-json

Newline-delimited JSON events emitted in real time. Each line is a self-contained JSON object with a `type` field:

```json
{"type":"text","data":"Here's"}
{"type":"text","data":" a summary"}
{"type":"thought","data":"Analyzing the directory structure..."}
{"type":"end","stopReason":"EndTurn","sessionId":"abc123","requestId":"xyz789"}
```

Event types:

| Type       | Description                           |
| ---------- | ------------------------------------- |
| `text`     | A chunk of the agent's response text  |
| `thought`  | Internal reasoning (thinking tokens)  |
| `end`      | Final event with metadata             |

---

## Session Management in Headless Mode

By default, each `claude -p` invocation creates a fresh session. To maintain context across calls, use session flags.

### Named Sessions (`-s`)

The `-s/--session-id` flag lets you choose your own session ID. If the session already exists, it picks up where you left off. If not, a new one is created:

```bash
# Start a session namespaced to a PR
claude -p "Review the changes in this PR" -s "critique-myrepo-pr-123"

# Continue in the same session
claude -p "Now check for security issues" -s "critique-myrepo-pr-123"
```

This is the recommended approach for CI and automation workflows where you need multi-turn conversations.

> **Note:** `-s/--session-id` is for headless mode (`-p/--single`) only.
> In the interactive TUI, use `/load` or `--resume`.

### Resume (`-r`)

The `-r/--resume` flag resumes a specific session by ID. Unlike `-s`, it errors if the session does not exist:

```bash
# Get the session ID from a previous JSON response
claude -p "Remember: the secret number is 42" --output-format json
# Output includes "sessionId": "abc123"

# Resume that exact session
claude -p "What's the secret number?" --resume abc123
```

### Continue (`-c`)

The `-c/--continue` flag continues the most recent session in the current working directory:

```bash
claude -p "Continue where we left off" -c
```

### Extracting Session IDs

Use `--output-format json` and parse the `sessionId` field:

```bash
claude -p "Hello" --output-format json | jq -r '.sessionId'
```

---

## Piping Input and Output

Headless mode works naturally with Unix pipes and redirection.

### Standard Output

```bash
# Pipe output to a file
claude -p "Generate a README" > README.md

# Parse JSON output with jq
claude -p "List files" --output-format json | jq -r '.text'
```

### Standard Input

You can pipe content into Claude Code by including it in the prompt:

```bash
# Pipe git diff as context
git diff --staged | claude -p "Write a concise commit message for these changes"
```

---

## CI/CD Integration Examples

### Automated Code Review

```bash
claude -p "Review changes for bugs and security issues." \
  --output-format json --yolo | jq -r '.text' > review.md
```

### Pre-Commit Hook

```bash
claude -p "Review staged changes for obvious bugs. Reply OK if fine, or list issues." \
  --yolo --output-format json | jq -r '.text' | grep -q "^OK" || exit 1
```

### Batch Processing

```bash
for file in src/*.js; do
  claude -p "Migrate $file from CommonJS to ES modules." --yolo
done
```

---

## Scripting Patterns

### Python Wrapper

Claude Code's headless mode can be wrapped as an OpenAI-compatible chat completion API:

```python
import asyncio
import json
import os

class GrokChat:
    """Simple OpenAI-compatible wrapper using headless mode."""

    def __init__(self, cwd="."):
        self.cwd = cwd
        self.env = {**os.environ}

    def _build_cmd(self, prompt, model, stream):
        return ["claude", "-p", prompt, "-m", model, "--cwd", self.cwd,
                "--output-format", "streaming-json" if stream else "json",
                "--yolo"]

    async def create(self, messages, model="claude-sonnet", stream=False):
        prompt = messages[-1]["content"] if len(messages) == 1 else "\n".join(
            f"{m['role']}: {m['content']}" for m in messages
        )
        cmd = self._build_cmd(prompt, model, stream)

        if stream:
            return self._stream(cmd)

        proc = await asyncio.create_subprocess_exec(
            *cmd, env=self.env, stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        data = json.loads(stdout.decode()) if stdout else {"text": ""}
        return {
            "choices": [{
                "message": {"role": "assistant", "content": data.get("text", "")},
                "finish_reason": "stop"
            }]
        }

    async def _stream(self, cmd):
        proc = await asyncio.create_subprocess_exec(
            *cmd, env=self.env, stdout=asyncio.subprocess.PIPE
        )
        async for line in proc.stdout:
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get("type") == "text":
                yield {"choices": [{"delta": {"content": event["data"]}}]}
            elif event.get("type") == "end":
                yield {"choices": [{"delta": {}, "finish_reason": "stop"}]}


async def main():
    client = GrokChat(cwd=".")
    response = await client.create(
        [{"role": "user", "content": "What files are here?"}]
    )
    print(response["choices"][0]["message"]["content"])

asyncio.run(main())
```

### Shell Script

```bash
#!/bin/bash
# Run a code review and exit with failure if issues are found

RESULT=$(claude -p "Review this PR for bugs. Output JSON with 'issues' array." \
  --output-format json --yolo | jq -r '.text')

ISSUE_COUNT=$(echo "$RESULT" | jq '.issues | length' 2>/dev/null || echo "0")

if [ "$ISSUE_COUNT" -gt 0 ]; then
  echo "Found $ISSUE_COUNT issues"
  echo "$RESULT" | jq '.issues[]'
  exit 1
fi

echo "No issues found"
```

---

## Fully Automated Runs with --yolo

The `--yolo` flag auto-approves all tool executions (file writes, command execution, etc.) without prompting for confirmation. This is required for unattended automation:

```bash
# Format all files without asking
claude -p "Format all files" --yolo

# Run tests and fix failures
claude -p "Run the tests and fix any failures" --cwd ~/projects/my-app --yolo
```

**Use `--yolo` with care.** It grants the agent full autonomy to modify files and run commands. Only use it in trusted environments or with well-scoped prompts.

---

## Environment Variables for Headless

Key environment variables that affect headless mode:

| Variable                        | Description                                                   |
| ------------------------------- | ------------------------------------------------------------- |
| `ANTHROPIC_API_KEY`        | API key for authentication (required when no browser login)   |
| `CLAUDE_HOME`                    | Override config directory (default: `~/.claude`)                |
| `CLAUDE_LOG_FILE`                | Enable file logging: `1` for default path, or a custom path  |
| `CLAUDE_LOG_FILTER`              | Log level filter (default: `info`)                            |
| `RUST_LOG`                     | Logging level for stderr (headless mode only)                 |

For CI environments without browser access, set `ANTHROPIC_API_KEY` with an API key from [console.anthropic.com](https://console.anthropic.com):

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
claude -p "Run the test suite" --yolo
```

---

## Exit Codes

| Code | Meaning                              |
| ---- | ------------------------------------ |
| `0`  | Success -- prompt completed normally |
| `1`  | Error -- authentication failure, network error, or runtime error |
| `130` | Interrupted by SIGINT (Ctrl+C)                                   |
| `143` | Terminated by SIGTERM                                            |

---

## Authentication for Headless Environments

For headless use, authenticate with one of:

- **`ANTHROPIC_API_KEY`** — simplest for CI. See [Environment Variables](#environment-variables-for-headless) above.
- **`claude login --device-auth`** (or `--device-code`) — no browser needed on the target machine.
  See [Authentication > Device Code Flow](02-authentication.md#device-code-flow).
- **`claude login`** — browser-based OAuth2 on machines with a GUI.

If you've previously logged in, cached credentials are used automatically.

---

## Tips

- Headless mode starts a **fresh session by default**. Use `-s <id>` to maintain context across calls.
- The `--output-format json` response always includes a `sessionId` you can use with `--resume` or `-s` for follow-up calls.
- Combine `--yolo` with `--rules` to set guardrails: `claude -p "..." --yolo --rules "Never delete files"`.
- For debugging, enable logging: `CLAUDE_LOG_FILE=1 CLAUDE_LOG_FILTER=debug claude -p "..."`.

---

## Project Root Discovery

When Claude Code starts, it discovers the project root by walking upward from `--cwd`
(or the current directory) looking for a `.git` directory.

| Flag / Variable            | Effect |
| -------------------------- | ------ |
| `--project-root <PATH>`   | Use `PATH` as the project root (skip git discovery) |
| `--no-project-root`       | Do not discover a project root; use `--cwd` only |
| `--cwd-only`              | Alias for `--no-project-root` |
| `GIT_CEILING_DIRECTORIES` | Standard git env var; limits upward traversal |

**Pitfall:** If `cwd` is nested inside a large monorepo, Claude Code may discover that
ancestor. Use `--no-project-root` to avoid this.

---

## File Locations

Claude Code stores data in `~/.claude` (override with `CLAUDE_HOME`; see [Environment Variables for Headless](#environment-variables-for-headless)):

| Path                     | Contents                              |
| ------------------------ | ------------------------------------- |
| `config.toml`            | User configuration                    |
| `auth.json`              | Cached OAuth2/API credentials         |
| `version.json`           | Version cache for update checks       |
| `sessions/`              | Session transcripts (SQLite)          |
| `memory/`                | Cross-session memory store            |
| `logs/`                  | Log files (when `CLAUDE_LOG_FILE` set)  |
| `logs/mcp/`              | MCP server logs                       |
| `skills/`                | User skill definitions                |
| `personas/`              | User-scoped agent personas            |
| `crash/`                 | Crash reports                         |
| `trace-exports/`         | Session trace exports                 |
| `worktrees/`             | Git worktree metadata                 |

### Read-Only `~/.claude`

For containers or CI, mount `~/.claude` read-only:

- Pre-populate `auth.json` or use `ANTHROPIC_API_KEY`
- Session persistence fails silently (ephemeral)
- Update checks log a warning and skip

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export CLAUDE_DISABLE_UPDATE_CHECK=1
claude -p "..." --no-project-root --no-auto-update
```

---

## Update Check Suppression

| Method                          | Scope     |
| ------------------------------- | --------- |
| `--no-auto-update`              | Session   |
| `CLAUDE_DISABLE_UPDATE_CHECK=1`   | Process   |
| Non-TTY stderr (auto-detected)  | Automatic |
| `[cli] auto_update = false`     | Persistent|

Update messages go to **stderr**. Stdout stays clean for `--output-format json`. See also [Environment Variables for Headless](#environment-variables-for-headless).

---

## Additional Headless Flags

These flags supplement the [Command-Line Options](#command-line-options) table above. Flags already listed there (`--prompt-json`, `--prompt-file`, `--verbatim`, `--sandbox`, `--no-auto-update`) are not repeated here.

| Flag                          | Description                                       |
| ----------------------------- | ------------------------------------------------- |
| `--agent <NAME>`              | Agent name or definition file path                |
| `--agents <JSON>`             | Inline subagent definitions as JSON               |
| `--system-prompt-override`    | Override the agent's system prompt                |
| `--reasoning-effort <EFFORT>` | Reasoning effort for reasoning models             |
| `--check` / `--self-verify`   | Append verification loop (headless only)          |
| `--best-of-n <N>`             | Run task N ways, pick best (headless only)         |
| `--no-plan`                   | Disable plan mode                                 |
| `--no-subagents`              | Disable subagent spawning                         |
| `--no-memory`                 | Disable cross-session memory                      |
| `--disable-web-search`        | Disable web search and fetch tools                |
| `--no-alt-screen`             | Run inline (no alternate screen)                  |
| `--worktree [NAME]`           | Start session in a new git worktree               |

---

## Interrupted Headless Runs

On SIGINT/SIGTERM:

- Session state saved up to the last completed tool call
- File modifications by tools are **not rolled back**
- Exit code is **130** for SIGINT (`128 + 2`) and **143** for SIGTERM (`128 + 15`); CI pipelines can distinguish these from a normal error (exit code `1`)
- Resume: `claude -p "continue" -s "my-task"` or `claude -p "continue" --continue`

See [Session Management in Headless Mode](#session-management-in-headless-mode) for details on named sessions and the `-s`/`-r`/`-c` flags.
