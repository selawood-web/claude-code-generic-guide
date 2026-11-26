# Claude Code memory: imports and rules files

- **As of:** 2026-11-26
- **Staleness class:** volatile
- **Searched for:** [The charter's core syncs separately from project constraints](../../decisions/2026-11-26-sync-charter-core-separately-from-project-constraints.md)

## Findings

Source: code.claude.com/docs/en/memory ("How Claude remembers your project").

- `@path` imports take relative or absolute paths. A relative path resolves from the file that holds the import, not the working directory. Imports inside code spans or fenced blocks are skipped.
- Imports are recursive, to a maximum depth of four hops. The page does not define a hop further.
- Imported files load at launch with the CLAUDE.md that imports them. Imports organise a long file but do not reduce what loads.
- `.claude/rules/*.md` files are discovered recursively. A rule without `paths:` frontmatter loads at launch with the same priority as `.claude/CLAUDE.md`; one with `paths:` loads only when a matching file is read or edited.
- An import that resolves outside the working directory triggers a one-time approval dialog. Imports inside the project do not, by implication; the page does not say so outright.
- Guidance: keep a CLAUDE.md under 200 lines. A CLAUDE.md over 4 MiB is skipped. Imports in subdirectory CLAUDE.md files and on-demand rules are capped per file (40,000 characters at 200K context). Block-level HTML comments are stripped before injection.
