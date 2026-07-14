# Terminal Support and Troubleshooting

Claude Code is a full-screen TUI. Due to the nature of rendering a full-screen TUI, problems may arise when using certain terminals, multiplexers, and SSH as they interact with escape sequences the TUI uses for colors, clipboard, mouse, and fullscreen.

## Quick Fixes

### Truecolor / Washed-out or wrong colors

```bash
# Add to ~/.zshrc or ~/.bashrc
export COLORTERM=truecolor
```

Inside tmux or over SSH, also add to your tmux config:

```tmux
# ~/.tmux.conf or ~/.byobu/.tmux.conf
set -g default-terminal "tmux-256color"
set -as terminal-features ",*:RGB"
```

### Recommended tmux settings (clipboard + passthrough)

```tmux
set -g set-clipboard on
set -g allow-passthrough on
```

After editing, run:

```bash
tmux source-file ~/.tmux.conf
# or detach and reattach
```

### Live diagnostics inside Claude Code

Type this slash command:

```
/terminal-check
```

It shows exactly what Claude Code detected and the precise fix for your environment.

---

## Detected Terminals

Claude Code explicitly detects these terminal emulators via env vars:

- **Apple Terminal** (Terminal.app)
- **Ghostty**
- **iTerm2**
- **Warp**
- **VS Code** integrated terminal
- **WezTerm**
- **Kitty**
- **Alacritty**

However, some current limitations include:
- Tmux doesn't pass through the required variables to detect the terminal.
- Over SSH, many terminal variables are not forwarded.
- tmux global config (`tmux -g`) reflects the first client that attached to the server, not your current session.

---

## Common Problems and Fixes

### Problem: Colors look wrong or lack truecolor

**Cause**: `COLORTERM` not set or tmux not configured for 24-bit RGB.

**Fix**: The two settings above + restart Claude Code.

### Problem: Clipboard problems

Claude Code uses a multi-leg clipboard system:

- Native clipboard always attempted via the OS first.
- When inside tmux, also writes to `tmux load-buffer`.
- Emits OSC 52, an escape sequence, so the outer terminal can update its clipboard. In tmux this is always enabled; outside tmux it is only sent over SSH.

**Known limitation — Apple Terminal + SSH**:
Apple Terminal **does not accept OSC 52 over SSH**. This means nothing can be copy-pasted from within Apple Terminal when connected over SSH. We are actively working on a fix.

**Temporary workaround**: Use `claude ssh` instead of plain `ssh`. It wraps the connection in a local PTY that _only_ intercepts OSC 52 sequences and writes them to your local clipboard.

> **Warning**: `claude ssh` is **not fully stable**. It can break during terminal resizing. It is intended as a temporary solution until a more robust fix lands.

**iTerm2 setting**:
iTerm2 requires explicit permission for OSC 52:

1. iTerm2 → **Settings** → **General** → **Selection**
2. Enable **"Applications in terminal may access clipboard"**

This setting is off by default for security reasons. Without it, OSC 52 writes from Claude Code (or any TUI) will be ignored.

**Fix for other cases**:
- `set -g set-clipboard on` in tmux config
- For other terminals over SSH → switch to iTerm2, Ghostty, WezTerm, or Kitty for native OSC 52 support

### Problem: Fullscreen / alternate screen not activating (inline mode)

**Cause**: Zellij, tmux control mode (`tmux -CC`), or config set to `never`.

**Fix**:
- In Zellij or control mode, Claude Code intentionally runs inline (no alt screen).
- Set `[terminal] alt_screen = "always"` in `~/.claude/pager.toml` to force fullscreen.
- Use the CLI flag `--no-alt-screen` to disable alt-screen mode entirely (useful for debugging or when the alternate screen causes issues in your terminal).

### Problem: Zellij keybindings interfere with Claude Code (Ctrl+g, Ctrl+o, etc.)

Zellij intercepts many Ctrl/Alt key combinations before they reach full-screen TUIs like Claude Code.

**Best fix** (Zellij 0.41+): Switch to the **"Unlock-First (non-colliding)"** preset:

1. Press `Ctrl+o` → `c` (open Configuration)
2. Go to **"Change Mode Behavior"**
3. Select **"Unlock-First (non-colliding)"**
4. Press `Enter` (or `Ctrl+a` to save permanently)

After this, Zellij starts **locked**. Most keys pass through to Claude Code. Press `Ctrl+g` to temporarily unlock Zellij when you need its pane/session management.

This is the officially recommended approach for TUI users.

### Problem: `Ctrl+Enter` doesn't interject in WezTerm

**Cause**: WezTerm ships with Kitty keyboard protocol disabled. Claude Code relies on it to tell `Ctrl+Enter` (interject) and `Shift+Enter`/`Ctrl+Enter` (in multiline mode) apart from plain `Enter`. Most other terminals turn it on by default.

Apple Terminal gets a built-in `Ctrl+O` fallback for interject for the same reason.

**Fix**:

Add this after `config = wezterm.config_builder()` in `~/.config/wezterm/wezterm.lua`:

```lua
config.enable_kitty_keyboard = true
```

Reload (`Cmd+Shift+R` or restart WezTerm) and restart `claude`.

**Verify**: Run `/terminal-setup` inside Claude Code. When a turn is active you should see the interject hint and `Ctrl+Enter` should work.

**Quick workaround** (no global change):

```lua
table.insert(config.keys, {
  key = "Enter",
  mods = "CTRL",
  action = wezterm.action.SendString("\x1b[13;5u"),
})
```

### Problem: Mouse scrolling stops working (native scrollbar takes over)

If Claude Code's mouse-driven scrolling stops responding and your terminal falls back to its native scrollbar, mouse reporting has been disabled.

**Apple Terminal**: Go to **View > Allow Mouse Reporting** (keyboard shortcut `Cmd+R`) to re-enable it. A checkmark appears next to the option when active.

**iTerm2**: Open **Settings** (`Cmd+,`) → **Profiles** → **Terminal** → ensure **"Enable mouse reporting"** is checked. Alternatively, restart iTerm2.

### Problem: Byobu + GNU screen

Byobu on screen has best-effort support only. Prefer Byobu on tmux.

---

## Still Stuck?

Claude Code it!