# Plugins

Plugins are packages that bundle skills, agents, hooks, MCP server configurations, and LSP server configurations into a single installable unit. They provide a way to share and distribute Claude Code extensions across teams and the community.

---

## What Are Plugins?

A plugin is a directory containing any combination of:

- **Skills** -- `skills/` directory with SKILL.md files
- **Agents** -- `agents/` directory with agent definitions
- **Hooks** -- `hooks/hooks.json` file with lifecycle hooks. When hooks come from a plugin, they receive `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` (see the [Hooks guide](10-hooks.md) for all environment variables available to hooks).
- **MCP servers** -- `.mcp.json` file with server configurations
- **LSP servers** -- `.lsp.json` file with language server configurations

Plugins let you package related functionality together. For example, a "team-tools" plugin might include a deploy skill, a code review agent, pre-commit hooks, and a Linear MCP server -- all installed in one step.

## Environment Variables in Plugin Hooks

Plugin-provided hooks receive two additional environment variables beyond the standard ones set for all hooks:

| Variable             | Description |
|----------------------|-------------|
| `CLAUDE_PLUGIN_ROOT`   | Absolute path to the plugin's installed directory. |
| `CLAUDE_PLUGIN_DATA`   | Absolute path to the plugin's writable data directory (for storing plugin state, caches, logs, etc.). |

These values are managed by the plugin system. They override any user-declared values for the same keys in the hook JSON's `env` map. See the [Hooks guide](10-hooks.md) for the complete list of environment variables passed to hooks.

---

## Plugin Locations

Claude Code discovers plugins from these directories:

| Location | Scope |
|----------|-------|
| `.claude/plugins/` | Project -- shared with the team via version control |
| `~/.claude/plugins/` | User -- personal plugins for all projects |
| `--plugin-dir <PATH>` (CLI) | Session -- temporary for one session |

---

## Managing Plugins in the TUI

### Opening the Plugins Modal

| Method | Opens on tab |
|--------|-------------|
| `Ctrl+L` | Plugins (works from any pane) |
| `/plugins` | Plugins tab |

The modal has three tabs: **Hooks**, **Plugins**, and **Marketplace**. Switch between them with `Tab` / right-arrow (forward) or `Shift+Tab` / left-arrow (backward).

### Plugins Tab

Each plugin shows (when expanded with Space):

- **Name** and **version**
- **Scope** -- `user`, `project`, `cli`, or marketplace source name
- **Skills** -- names or count
- **Agents** -- names or count
- **Hooks** -- count
- **MCP servers** -- count (or "blocked" if not trusted)
- **Description**
- **Conflicts** -- warning if any

Keyboard shortcuts in the Plugins tab:

| Key | Action |
|-----|--------|
| `r` | Reload all plugins |
| `i` | Install plugin from path |
| `e` | Enable / disable selected plugin |
| `Space` | Expand / collapse plugin details |
| `/` | Search plugins by name |

### Marketplace Tab

Browse and install plugins from configured marketplace sources.

Keyboard shortcuts in the Marketplace tab:

| Key | Action |
|-----|--------|
| `i` | Install selected plugin |
| `d` | Uninstall selected plugin |
| `r` | Refresh marketplace sources (re-clone/pull git repos) |
| `u` | Update all installed marketplace plugins |
| `Space` | Expand / collapse source or plugin |
| `/` | Search plugins by name |

---

## CLI Commands

Manage plugins without starting an interactive session.

### Plugin commands

```bash
claude plugin list [--json] [--available]   # List plugins (--available requires --json)
claude plugin install <source> --trust      # Git URL, GitHub shorthand (user/repo), or local path
claude plugin uninstall <name> [--confirm] [--keep-data]
claude plugin update [<name>]               # Omit name to update all
claude plugin enable <name>
claude plugin disable <name>
claude plugin details <name>                # Show skills, agents, hooks, MCP, LSP
claude plugin validate [<path>]             # Check plugin.json (default: current dir)
claude plugin tag [<path>] [--push] [--force] [--dry-run]
```

The `<source>` argument accepts:

- `user/repo` -- GitHub shorthand
- `user/repo@v1.0` -- pinned to a ref
- `user/repo#subdir` -- subdirectory within the repo
- `https://github.com/user/repo.git` -- full URL
- `git@github.com:user/repo.git` -- SSH
- `./local-dir` or `/absolute/path` -- local directory

### Marketplace commands

```bash
claude plugin marketplace list [--json]
claude plugin marketplace add <url>         # Git URL or GitHub shorthand
claude plugin marketplace remove <url>
claude plugin marketplace update [<name>]   # Omit name to refresh all
```

### Example: set up a team marketplace

```bash
claude plugin marketplace add my-org/team-plugins
claude plugin marketplace list
claude plugin install my-org/team-plugins --trust
claude plugin list
claude plugin update
```

---

## Slash Commands

Manage plugins inside an interactive session:

```
/plugins list                       # List installed plugins
/plugins reload                     # Reload all plugins
/plugins install <source> --trust   # Install from URL or path
/plugins uninstall <name> --confirm
/plugins update [<name>]
/plugins add <path>                 # Add a local plugin directory
/plugins remove <path>
/plugins trust <path>
```

---

## Configuration

Configure plugin paths and disabled plugins in `~/.claude/config.toml`:

```toml
[plugins]
paths = ["~/my-plugins/custom-tools"]       # Additional plugin directories
disabled = ["user/a1b2c3d4/noisy-plugin"]   # Plugin IDs to skip
```

### Disabling Plugins UI

To hide the hooks and plugins UI entirely (hides `/hooks`, `/plugins` commands and scrollback annotations), set in `~/.claude/pager.toml`:

```toml
disable_plugins = true
```

---

## Marketplace Sources

Add git-based or local marketplace sources to discover and install plugins:

### In config.toml

```toml
[[marketplace.sources]]
name = "My Team Plugins"
git = "https://github.com/my-org/plugins.git"

[[marketplace.sources]]
name = "Local Dev"
path = "~/dev/my-plugins"
```

### In settings.json

```json
{
  "extraKnownMarketplaces": {
    "my-marketplace": {
      "source": { "source": "git", "url": "git@github.com:my-org/plugins.git" },
      "autoUpdate": true
    }
  }
}
```

Settings can be placed in `~/.claude/settings.json` or `~/.claude/settings.json`.

---

## Trust Model

Plugins must be trusted before their hooks and MCP servers execute. Skills and agents within plugins are always available, but components that run code (hooks, MCP server processes) require explicit trust.

Trust a plugin through:

- The Plugins modal in the TUI (press `e` to enable)
- The `/plugins trust <path>` slash command
- The confirmation prompt when first encountering an untrusted plugin

This prevents untrusted repositories from running arbitrary code on your machine.

---

## Inspecting Plugins

Use `claude inspect` to see all discovered plugins and what each provides:

```bash
claude inspect          # Shows plugins with their skills, agents, hooks, MCPs
claude inspect --json   # Machine-readable format
```

Plugin-provided components appear in their respective sections (Skills, Agents, MCP Servers, etc.) with a `[plugin: name]` tag, so you can see at a glance where each component originates.

---

## General Keyboard Shortcuts

These work across all tabs in the Hooks & Plugins modal:

| Key | Action |
|-----|--------|
| `Tab` / right-arrow | Next tab |
| `Shift+Tab` / left-arrow | Previous tab |
| `j` / down-arrow | Move selection down |
| `k` / up-arrow | Move selection up |
| `Space` | Toggle expand / collapse |
| `/` | Start search (Plugins and Marketplace) |
| `Backspace` | Delete search character, or re-enter search |
| `Esc` | Clear search, or close modal |
| `q` | Close modal |

Some actions (like uninstalling a plugin) ask for confirmation. Press `y` to confirm or `Esc` to cancel.
