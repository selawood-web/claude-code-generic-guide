# Keyboard Shortcuts

Complete reference for all key bindings in the Claude Code TUI. Bindings are defined in `src/actions/defaults.rs` and cannot currently be remapped.

---

## Input Modes

Claude Code has two input modes that control how you navigate the scrollback:

- **Simple mode** (default): Arrow keys for navigation, `Shift+Arrow` for turn navigation, `Space` to focus the prompt, and any printable key auto-focuses the prompt.
- **Vim mode** (opt-in): `j`/`k` for navigation, `H`/`L` for turn navigation, `h`/`l` for fold, `e`/`E` for expand/collapse, and `i`/`Tab`/`Space` to focus the prompt.

Simple mode is active by default. To switch to Vim mode, set `simple_mode = false` under `[ui]` in `~/.claude/config.toml`. See [Configuration](05-configuration.md) for details.

The tables below document bindings for both modes. The "Key" column shows the Vim-mode binding, and the "Alt Key" column shows the equivalent in simple mode (arrow keys, etc.).

> **Vim-mode required**: Single-letter and `Shift+letter` bindings in the
> **Scrollback** context (`j/k`, `h/l`, `g/G`, `L/H`, `y/Y`, `o/O`, `r`,
> `x`, `e/E`, and the `i` insert-mode alt) require `[ui].vim_mode = true`
> in `~/.claude/config.toml` (or `/vim-mode` to toggle). Arrow keys, `Tab`,
> `Esc`, `Space`, `PageUp/Down`, and every `Ctrl+letter` shortcut work in
> both modes.

---

## Navigation (Scrollback Focused)

Move through conversation entries in the scrollback pane.

| Key | Alt Key | Action |
|-----|---------|--------|
| `j` | `Down` | Select next entry |
| `k` | `Up` | Select previous entry |
| `⇧L` | `Shift+Right` | Jump to next turn (user prompt) |
| `⇧H` | `Shift+Left` | Jump to previous turn (user prompt) |
| `g` | | Go to top of scrollback |
| `⇧G` | | Go to bottom of scrollback |
| `Ctrl+K` | | Scroll up one line (without changing selection) |
| `Ctrl+J` | | Scroll down one line (without changing selection) |
| `PageUp` | | Scroll up one page |
| `PageDown` | | Scroll down one page |
| `Ctrl+U` | | Scroll up half page |
| `Ctrl+D` (`Shift+D` in VSCode) | | Scroll down half page |

---

## View (Scrollback Focused)

Control how entries are displayed in the scrollback.

| Key | Alt Key | Action |
|-----|---------|--------|
| `h` | `Left` | Collapse selected entry |
| `l` | `Right` | Expand selected entry |
| `e` | | Toggle fold on selected entry |
| `⇧E` | | Expand all / collapse all entries |
| `Ctrl+⇧E` | | Expand/collapse all thinking blocks |
| `r` | | Toggle raw markdown on selected entry |

### Block Content

| Key | Action |
|-----|--------|
| `y` | Copy block content to clipboard |
| `⇧Y` | Copy block metadata (e.g., the shell command) to clipboard |
| `Enter` | Open block content in fullscreen viewer |
| `Ctrl+F` | Open block content in fullscreen viewer (alt binding) |

---

## Focus

Switch between the prompt input and scrollback pane.

| Key | Alt Key | Context | Action |
|-----|---------|---------|--------|
| `Tab` | `i` | Scrollback focused | Focus the prompt input |
| `Esc` | `Tab` | Prompt focused | Focus the scrollback |
| `Enter` | | Prompt focused | Send the current prompt |

---

## Agent-Level

Actions that affect the agent session, available from the agent screen.

| Key | Context | Action |
|-----|---------|--------|
| `Ctrl+P` | Agent screen | Open the command palette |
| `?` (Shift+/) | Agent screen | Open the command palette (alt binding) |
| `Ctrl+M` | Agent screen | Open the model picker / switch model |
| `Ctrl+M` | Prompt focused | Toggle multiline input mode |
| `Ctrl+C` | Agent screen | Cancel the current turn |
| `Ctrl+O` | Agent screen | Toggle auto-approve (YOLO) mode |
| `Ctrl+S` | Agent screen | Open the session picker (resume a previous session) |
| `Ctrl+;` (alt: `Ctrl+'`) | Agent screen | Toggle the prompt queue pane (when non-empty) |
| `Ctrl+Shift+A` | Agent screen | Toggle the subagent catalog (agent types and personas) |

**Note:** `Ctrl+M` is context-dependent. When the prompt is focused, it toggles multiline input mode. Otherwise, it opens the model picker.

**Note:** `Ctrl+'` is a Windows alt for `Ctrl+;` — some Windows consoles drop the `Ctrl` modifier on punctuation keys.

---

## Image Paste & Drag-and-Drop

| Action | macOS | Linux | Windows |
|---|---|---|---|
| Drag image from file manager into the prompt | Finder ✓ | Files / Dolphin ✓ | Explorer ✓ |
| Copy a file in the file manager, then paste | `Cmd+V` | `Ctrl+V` | `Ctrl+V` |
| Screenshot or "Copy Image" in clipboard, then paste | `Cmd+V` | `Ctrl+V` | **`Alt+V`** |

Non-image files insert their absolute path as text instead of a chip.

> **`Alt+V` on Windows** is claude-specific. Windows Terminal's default `Ctrl+V` only pastes plain text and silently drops image clipboards; `Alt+V` bypasses the interceptor. To use `Ctrl+V` for images too, add `{ "command": null, "keys": "ctrl+v" }` to `actions` in your Windows Terminal `settings.json`.

---

## During an active turn (agent running)

When the agent is generating, `Ctrl+Enter` from the prompt sends a mid-turn interjection without cancelling the turn.

| Key          | Alt Key    | Action                                      |
|--------------|------------|---------------------------------------------|
| `Ctrl+Enter` | `Ctrl+I`   | Interject (continues the current turn)      |

In `/multiline` mode, `Ctrl+Enter` (or `Shift+Enter`) sends while plain `Enter` just inserts a newline.

> **WezTerm**: These modified Enter keys need `enable_kitty_keyboard = true` in your WezTerm config. Full steps and a one-line workaround are in the [terminal support guide](21-terminal-support.md#problem-ctrlenter-interject-or-modified-enter-keys-do-not-work-as-expected-wezterm).

> **Windows**: Some consoles drop the `Ctrl` modifier on `Ctrl+Enter` (it can collapse to bare `Enter` or `Ctrl+J`). Use `Ctrl+I` as the alt — letter-key Ctrl chords are stable everywhere.

---

## Global

Actions available from any screen.

| Key | Alt Key | Action | Confirmation |
|-----|---------|--------|-------------|
| `Ctrl+N` | | Create a new session | Yes (double-press within 1000ms) |
| `Ctrl+Shift+N` | | Create a new session in a git worktree | Yes |
| `Ctrl+H` | | Exit session and return to welcome screen | Yes |
| `Ctrl+Q` | `Ctrl+D` | Quit the application | Yes (double-press within 1000ms) |

**VSCode terminal:** In VSCode's integrated terminal, `Ctrl+Q` is captured by the editor. Claude Code automatically swaps the bindings so `Ctrl+D` is the primary quit key and `Ctrl+Q` is the alternate. Additionally, half-page-down is rebound to bare `Shift+D` in VSCode.

### Destructive Action Confirmation

Actions marked with "Yes" in the confirmation column require a double-press within 1000ms. Press the key once to see a confirmation prompt, then press again to confirm. This prevents accidental session loss.

---

## Welcome Screen

Bindings that only fire on the welcome screen (before any agent session is open).

| Key | Action |
|-----|--------|
| `Ctrl+S` | Resume session (open the session picker) |
| `Ctrl+W` | Toggle worktree mode |
| `Ctrl+I` | Import Claude settings (when available) |
| `Ctrl+Shift+I` | Dismiss the Claude import row (when available) |

`Ctrl+W`, `Ctrl+I`, and `Ctrl+Shift+I` are only active on the welcome screen. `Ctrl+S` opens the session picker on both the welcome screen and inside an agent session (where it opens as a modal overlay, same as the `/load` command). `Ctrl+Q` is the same global Quit binding documented above, not a welcome-specific handler.

---

## Command Palette

Press `Ctrl+P` or `?` to open the command palette -- a fuzzy-searchable list of all available actions. The palette shows:

- All keyboard shortcuts with their current bindings
- All slash commands
- Available skills

Type to filter, then press `Enter` to execute the selected action.

---

## Shortcuts Bar

The bottom of the TUI displays a contextual shortcuts bar showing the most relevant key bindings for the current state. The hints change based on:

- Which pane is focused (scrollback vs. prompt)
- Whether the agent is currently running
- What type of entry is selected

---

## Mouse Support

The TUI supports mouse interaction:

- **Click** on a scrollback entry to select it
- **Scroll wheel** to scroll through the scrollback
- **Click** on the prompt area to focus it
- **Hover** over the prompt to see a highlight (configurable via `pager.toml`)

---

## Quick Reference Card

### When scrollback is focused (Simple mode — default)

```
Navigation:       Up/Down (prev/next entry)  Shift+Left/Right (prev/next turn)
Scrolling:        Ctrl+J/K (line)  PgUp/PgDn (page)  Ctrl+U/D (half page)
Focus prompt:     Space or any printable key (auto-focuses and types)
```

### When scrollback is focused (Vim mode)

```
Navigation:       j/k (up/down)  H/L (prev/next turn)  g/G (top/bottom)
Scrolling:        Ctrl+J/K (line)  Ctrl+U/D (half page; D=Shift+D in VSCode)  PgUp/PgDn (page)
Folding:          h/l (collapse/expand)  e (toggle)  E (all)
Content:          y (copy)  Y (copy cmd)  Enter (fullscreen)
View:             r (raw markdown)  Ctrl+Shift+E (thinking)
Focus prompt:     i, Tab, or Space
```

### When prompt is focused

```
Send:             Enter
Newline:          Shift+Enter or Alt+Enter
Multiline:        Ctrl+M (toggle)
Paste:            Ctrl+V (text, files, screenshots on macOS/Linux)
Paste image:      Alt+V (Windows only — for screenshots / "Copy Image")
Select all:       Cmd+A (macOS, Ghostty only — see note below)
Leave:            Esc or Tab (back to scrollback)
```

> **Cmd+A is gated to Ghostty.** Claude Code's in-app `Cmd+A` handler is only
> wired up when the detected terminal is Ghostty. Other terminals
> either swallow `Cmd+A` at the terminal layer (Apple Terminal, default
> iTerm2) or have idiosyncratic in-terminal "Select All" behaviour we
> intentionally don't fight (Kitty, WezTerm). If you're on a non-Ghostty
> terminal, the binding is a no-op and the key falls through to the
> terminal's native behaviour.
>
> On Ghostty, add the one-line unbind to `~/.config/ghostty/config` so
> the keystroke reaches the running TUI:
>
> ```ini
> keybind = cmd+a=unbind
> ```
>
> After Ghostty reloads (it watches the config file), `Cmd+A` in the
> prompt selects every character in the prompt buffer, including pasted
> image chips. Image chip placeholders carry the file path
> (`[Image #N: /path/to/file]`), so cutting the selection with `Ctrl+X`
> after `Cmd+A` preserves the path through the system clipboard.

### Always available

```
Command palette:  Ctrl+P or ?
Model picker:     Ctrl+M (from scrollback)
Cancel:           Ctrl+C (stop current turn)
Auto-approve:     Ctrl+O (toggle YOLO)
New session:      Ctrl+N
Quit:             Ctrl+Q (or Ctrl+D in VSCode)
```

---

Copyright Anthropic. All rights reserved.
