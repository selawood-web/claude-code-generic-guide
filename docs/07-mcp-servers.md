# MCP Servers

MCP (Model Context Protocol) servers extend Claude Code with external tool integrations. They let Claude Code interact with databases, APIs, file systems, issue trackers, and any other service that implements the MCP standard.

---

## What Are MCP Servers?

An MCP server is a process that exposes tools to Claude Code over a standardized protocol. When you configure an MCP server, its tools become available to the model alongside Claude Code's built-in tools. The model can discover and call these tools during a session.

For example, a GitHub MCP server might expose tools like `create_issue`, `list_pull_requests`, and `search_code`. A database server might expose `query`, `list_tables`, and `describe_schema`.

See the [MCP specification](https://modelcontextprotocol.io) for protocol details.

---

## Configuration

MCP servers are configured in `~/.claude/config.toml` under `[mcp_servers.<name>]` sections.

### stdio Transport (Local Process)

The most common configuration -- Claude Code spawns a local process and communicates over stdin/stdout:

```toml
[mcp_servers.my-server]
command = "/path/to/server"           # Server executable
args = ["--flag", "value"]            # Command arguments
env = { API_KEY = "sk-..." }          # Environment variables
enabled = true                        # Enable/disable (default: true)
startup_timeout_sec = 10              # Startup timeout in seconds (default: 10)
tool_timeout_sec = 60                 # Default tool call timeout (default: 60)
tool_timeouts = { slow_op = 120 }     # Per-tool timeout overrides
```

### HTTP/SSE Transport (Remote Server)

For remote MCP servers accessible over HTTP:

```toml
[mcp_servers.remote-api]
url = "https://mcp.example.com/api"
headers = { "Authorization" = "Bearer token" }
```

### Streamable HTTP with Session ID

```toml
[mcp_servers.nebula]
url = "http://localhost:5000/api/mcp"
headers = { "x-nebula-mcp-session-id" = "{{session_id}}" }
```

---

## CLI Management

Manage MCP servers from the command line without editing config files:

```bash
# List configured MCP servers
claude mcp list
claude mcp list --json          # Machine-readable output

# Add a stdio server
claude mcp add my-server --command npx --args "-y @modelcontextprotocol/server-filesystem /tmp"

# Add an HTTP server
claude mcp add remote-api --url https://mcp.example.com/api

# Add with environment variables
claude mcp add github --command npx --args "-y @modelcontextprotocol/server-github" \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx

# Remove a server
claude mcp remove my-server
```

---

## Project-Scoped MCP Servers

MCP servers can be configured per-project by placing a `.claude/config.toml` in your repository:

```
my-project/
  .claude/
    config.toml
  src/
  ...
```

```toml
# .claude/config.toml
[mcp_servers.linear]
url = "https://mcp.linear.app/mcp"
enabled = true
```

When a server exposes a native HTTP/SSE endpoint, prefer the `url` form over wrapping it in a stdio proxy such as `npx mcp-remote <url>`. Claude Code speaks HTTP/SSE and OAuth directly, so the native form skips an extra subprocess per session and runs Claude Code's own OAuth client registration against the provider (proxies register their own client, which is what the provider's consent screen then shows).

Claude Code walks from the current directory up to the git repo root, loading `.claude/config.toml` at each level:

| Location | Scope | Priority |
|----------|-------|----------|
| `~/.claude/config.toml` | All projects | Lowest |
| `<repo-root>/.claude/config.toml` | This repository | Medium |
| `<cwd>/.claude/config.toml` | Current directory | Highest |

If a project defines a server with the same name as a global one, the project version replaces it entirely (fields are not merged).

Only `[mcp_servers]` is supported in project-scoped config files. Other config sections are only read from `~/.claude/config.toml`.

---

## Tool Naming

MCP tools are namespaced with the server name to avoid collisions:

- Server `filesystem` with tool `read_file` becomes `filesystem__read_file`
- Server `github` with tool `create_issue` becomes `github__create_issue`

---

## Live Toggle at Runtime

You can enable or disable MCP servers during a session without restarting Claude Code.

### The /mcps Modal

Open the MCP servers modal in the TUI:

- Run `/mcps` as a slash command
- Or use `Ctrl+L` and navigate to the appropriate tab

From the modal you can:

- View the status of each configured server (running, stopped, error)
- Enable or disable individual servers at runtime
- See which tools each server provides

### Tool Discovery

The model has access to two built-in tools for working with MCP servers:

- `search_tool` -- Discover available integration tools across all enabled MCP servers. Use this to find tools by name or description.
- `use_tool` -- Call an integration tool discovered via `search_tool`. Specify the fully-qualified tool name (e.g., `github__create_issue`).

---

## Compatibility

Claude Code loads MCP server configurations from multiple sources for compatibility:

| Source | Format | Location |
|--------|--------|----------|
| `config.toml` | Native Claude Code config | `~/.claude/config.toml`, `.claude/config.toml` |
| `.claude.json` | Claude Code format | `~/.claude.json` (user), project root |
| `.mcp.json` | MCP standard format | Project root |

All sources are merged. Servers from `config.toml` take precedence over compatibility sources when names conflict.

---

## MCP OAuth

For MCP servers that require OAuth authentication, Claude Code handles the credential flow automatically. When an MCP server requests OAuth credentials, Claude Code opens a browser-based authorization flow and stores the resulting tokens for future use.

---

## Example Configurations

Use the `url` form for hosted MCP servers and the `command` / `args` form for local stdio tools.

### Native HTTP (hosted services)

OAuth-based MCP servers must be authenticated before they're usable. Tokens are persisted under `~/.claude/mcp_credentials.json`. In the `/mcps` modal, press `r` to refresh the server list after editing `config.toml`.

```toml
[mcp_servers.linear]
url = "https://mcp.linear.app/mcp"
enabled = true

[mcp_servers.sentry]
url = "https://mcp.sentry.dev/mcp"
enabled = true

[mcp_servers.mixpanel]
url = "https://mcp.mixpanel.com/mcp"
enabled = true
```

For internal or self-hosted servers that authenticate with a static bearer token rather than OAuth, set the `Authorization` header explicitly:

```toml
[mcp_servers.internal-tools]
url = "https://mcp.internal.example.com/mcp"
enabled = true

[mcp_servers.internal-tools.headers]
Authorization = "Bearer <token>"
```

To avoid putting secrets in the config file, reference an environment variable with `${VAR}` (or `${VAR:-default}`). String fields in `[mcp_servers.*]` (including `url`, `command`, `args`, `env`, and `headers` values) are expanded at load time:

```toml
[mcp_servers.internal-tools]
url = "https://mcp.internal.example.com/mcp"
enabled = true
headers = { "Authorization" = "Bearer ${INTERNAL_MCP_TOKEN}" }
```

### Local stdio

Use stdio for tools that have to run locally (filesystem access, local databases, in-house servers).

```toml
# Filesystem access scoped to a directory
[mcp_servers.filesystem]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]

# Local Postgres
[mcp_servers.postgres]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:pass@localhost/db"]

# Custom server with longer timeouts for slow operations
[mcp_servers.my-tools]
command = "/usr/local/bin/my-mcp-server"
args = ["--config", "/etc/my-mcp.json"]
startup_timeout_sec = 30
tool_timeout_sec = 120
tool_timeouts = { slow_analysis = 300, quick_lookup = 10 }
```

---

## Available MCP Servers

A non-exhaustive list of MCP servers that work out of the box with the `url` or `command` forms above:

| Server | Transport | Endpoint / Package |
|--------|-----------|--------------------|
| Linear | HTTP (OAuth) | `https://mcp.linear.app/mcp` |
| Sentry | HTTP (OAuth) | `https://mcp.sentry.dev/mcp` |
| Mixpanel | HTTP (OAuth) | `https://mcp.mixpanel.com/mcp` |
| Filesystem | stdio | `@modelcontextprotocol/server-filesystem` |
| Git | stdio | `@modelcontextprotocol/server-git` |
| GitHub | stdio | `@modelcontextprotocol/server-github` |
| GitLab | stdio | `@modelcontextprotocol/server-gitlab` |
| PostgreSQL | stdio | `@modelcontextprotocol/server-postgres` |
| SQLite | stdio | `@modelcontextprotocol/server-sqlite` |
| Puppeteer | stdio | `@modelcontextprotocol/server-puppeteer` |

See the [MCP Server Registry](https://github.com/modelcontextprotocol/servers) for the full list of community servers and the [MCP specification](https://modelcontextprotocol.io) for protocol details.

---

## Troubleshooting

### Server Not Starting

```bash
# Test the server command manually
npx -y @modelcontextprotocol/server-filesystem /path

# Increase startup timeout
# In config.toml:
[mcp_servers.filesystem]
startup_timeout_sec = 30
```

### Viewing Server Status

Use `claude inspect` to see all loaded MCP servers and their sources:

```bash
claude inspect          # Human-readable
claude inspect --json   # Machine-readable
```

### Debug Logging

```bash
CLAUDE_LOG_FILE=1 CLAUDE_LOG_FILTER=debug claude
tail -f ~/.claude/logs/tracing.log
```

Look for log entries containing `mcp` to trace server startup, tool discovery, and tool call execution.
