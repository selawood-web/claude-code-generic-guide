# Working Charter

@.claude/references/charter-core.md

The core above is imported from CCGG and kept current by `update.sh`: how to think,
talk and end a turn, the code gate, and the standing constraints that travel with it.
Never edit it here. What follows is this project's own, and no sync overwrites it.

## This repository — claude-code-generic-guide

> Installing CCGG in another project? Replace this section with that project's own. The
> import above stays.

**What it is:** a drop-in documentation and configuration layer — markdown, seven bash
hooks, a JSON settings file, VS Code tasks, and the Python tooling in `tools/`
(validator, feature lint, catalog, audit) that CI runs on every pull request.

**Languages here:** Markdown, bash for `.claude/hooks/*.sh`, and Python for `tools/`.

**Branch boundary — strict.** Work happens on the branch the session was given, whatever its prefix.
`master` moves only through a pull request. Nothing outside the branch gets touched.

**Must never break:**

- **The drop-in contract.** README's Quick Start tells people to copy exact paths:
  `AGENTS.md`, `.claude/`, `MEMORY.md`, `WORKING-CHARTER.md`. Renaming or moving any of
  them invalidates every install instruction and every deployed copy.
  That set also bounds links: a rule file may point only at a file `install.sh` copies,
  or the link check fails in every installed project.
- **Skill loading.** Every `.claude/skills/<name>/SKILL.md` keeps its YAML frontmatter —
  `name`, `description`, `when_to_use`, `argument-hint`, and the catalog's `purpose`, spelled
  as the product spells them: a key it does not read is silently ignored, never an error.
- **Single-homed rules.** A rule stated in this charter, or in a companion it points at, is
  *referenced* from `AGENTS.md` and the skills, never restated there. Two copies drift, and
  that drift is what this charter was written to end. `MEMORY.md` is the one exception: it is
  copied into `~/.claude/CLAUDE.md` outside any repository, where a reference has nothing to
  resolve against, so it restates by design and its copies move when their homes do.

**Verification here.** `tools/validate.py` is the executable gate: links, anchors,
empty files, frontmatter, configs, budgets, the CLAUDE.md bridge and hook health —
run it locally before any push; CI runs it on every pull request. What it cannot check
stays a stated claim: no rule gained a second home, and instructions match the live
product (the charter's currency rule — verify against official docs before writing
product facts).
