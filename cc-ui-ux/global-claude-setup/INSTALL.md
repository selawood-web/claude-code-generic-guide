# Install: global design rules for Claude Code

This makes the design rules, the Next.js rules, and the agent pipeline rules load automatically in every project, with no copying per project.

## How it works

- The three rule files live once, in your global Claude Code folder, under `~/.claude/rules/`.
- Your global `~/.claude/CLAUDE.md` imports them, so every session in every project reads them.
- Each file says when it applies. The Next.js file only applies to Next.js projects. The pipeline file only applies where your five agents exist.
- A start-of-session hook checks the project and tells Claude which rules apply and whether `DESIGN.md` or `PRODUCT.md` is missing.
- Edit a rule file once, and every project picks up the change next session.

## Install

1. Unzip this folder anywhere.
2. Open a terminal in the unzipped folder and start Claude Code there.
3. Paste this prompt:

```
Install the global setup in this folder into my user-level Claude Code configuration. Do exactly this, and show me what you changed:

1. Create ~/.claude/rules/ and ~/.claude/hooks/ if they don't exist.
2. Copy the three files in rules/ into ~/.claude/rules/. If a file with the same name exists, show me the difference and ask before overwriting.
3. Copy hooks/design-context-check.sh into ~/.claude/hooks/ and make it executable.
4. Add the import lines from CLAUDE-global-imports.md to ~/.claude/CLAUDE.md. Create the file if it doesn't exist. Keep everything already in it. Don't add a line that is already there.
5. Merge the SessionStart hook from settings-hook.json into ~/.claude/settings.json. Keep every existing setting and hook. Don't duplicate the hook if it's already there. Validate that the result is valid JSON.
6. Run the hook script once from this folder and show me its output.
```

4. Restart Claude Code.

## Check it worked

Open any project and start Claude Code. Type `/memory` and confirm the three rule files appear as loaded. Then ask: which design rules apply to this project? It should answer from the files.

## Undo

Delete the three import lines from `~/.claude/CLAUDE.md` and remove the SessionStart entry from `~/.claude/settings.json`. The rule files can stay; nothing loads them.
