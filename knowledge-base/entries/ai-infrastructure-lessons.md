# AI Infrastructure Lessons — Knowledge Base

Learnings extracted from the 2026-08-27 infrastructure overhaul (PRs #1–#4),
in which every documented mechanism in this repo was tested against the real
product and made functional or honest.

---

## Conventions

### Claude Code reads CLAUDE.md, not AGENTS.md
**Principle**: An `AGENTS.md` alone is invisible to Claude Code — a root `CLAUDE.md` containing the `@AGENTS.md` import is required for the rules to load at all.
**Context**: Any project using `AGENTS.md` as the shared rules file across multiple assistants.
**Evidence**: This repo shipped for months with instructions no Claude Code session ever read; the official memory docs state the mechanism explicitly and recommend the import bridge. Verify with `/context` — the file must appear under Memory files.
**Tags**: #claude-code #agents-md #configuration

---

## Debugging

### Skill loading fails silently
**Principle**: A `SKILL.md` with malformed frontmatter does not error — the skill just never appears. Validate frontmatter mechanically; never assume a skill loaded because the file exists.
**Context**: Any `.claude/skills/` directory, especially after hand-editing or generating skill files.
**Evidence**: The failure mode was confirmed while building the CI validator; `tools/validate.py` now checks the five frontmatter keys on every PR because nothing else would ever surface the breakage.
**Tags**: #claude-code #skills #silent-failure

### Wiring beats intention — a hook has two silent failure points
**Principle**: A hook script only runs if it is registered in `.claude/settings.json` AND carries the executable bit; missing either fails silently, and the script sitting in `.claude/hooks/` proves nothing.
**Context**: Any repo shipping lifecycle hooks (PreCompact, SessionEnd, etc.).
**Evidence**: Both hook scripts in this repo were inert since the initial commit — no `settings.json` existed and both files were mode 644. Nothing reported it; the knowledge system's "automatic" tier simply never happened.
**Tags**: #claude-code #hooks #silent-failure

---

## Workflow

### Never document a tool's behavior from memory
**Principle**: Before writing any instruction a user will run, verify it against the tool's current official docs — the cost is one fetch; the cost of skipping it is instructions that fail at step 3.
**Context**: Any README, manual, or protocol that names commands, flags, config files, or paths.
**Evidence**: This repo's Quick Start told users to enable memory via a `config.toml` and a flag that do not exist; the verification pass that replaced them also surfaced the CLAUDE.md bridge — the largest defect in the repo — as a side effect.
**Tags**: #documentation #currency #verification

### Config that nothing reads is worse than no config
**Principle**: Every mechanism a repo documents must be executable or explicitly labeled as illustrative — a config file no tool parses teaches users a false model of how the system works.
**Context**: Settings files, hook directories, and command references in any tooling repo.
**Evidence**: `.claude/config.toml` was parsed by nothing while presenting itself as the memory configuration; it was first labeled as illustrative, then deleted once the owner confirmed nothing needed it.
**Tags**: #configuration #honesty #documentation

### One home per rule
**Principle**: State a rule in exactly one document and reference it everywhere else — parallel documents restating the same system will drift, and the drift is invisible until the two copies disagree somewhere expensive.
**Context**: Behavior rules, test standards, process definitions — anywhere two files describe one system.
**Evidence**: The repo carried two skill catalogs, two identity prompts, and two test standards ("happy path + one failure" vs. the charter's full bar); reconciling and then folding the duplicate system (Flow-Studio) took two PRs that a single-home convention would have made unnecessary.
**Tags**: #documentation #drift #single-source-of-truth

### In ephemeral cloud sessions, the repo is the only memory
**Principle**: A cloud container's `~/.claude/` dies with the session — durable knowledge from remote sessions must land in the repository itself: knowledge-base entries, commit messages carrying rationale, and updated docs.
**Context**: Claude Code on the web / remote sessions; anything run in a throwaway environment.
**Evidence**: This entry exists because a `/flush` to local memory in the authoring session would have persisted nothing.
**Tags**: #memory #cloud-sessions #persistence

### The first install is the real test of the guide
**Principle**: A reusable layer is only proven when it lands in a project unlike its home — install it somewhere real early, treat every downstream finding as an upstream bug report, and port the fix upstream the same day so no later adopter inherits it.
**Context**: Any template, starter kit, or drop-in infrastructure meant to be copied into other repositories; anything whose CI can only exercise it in its own repo.
**Evidence**: The first install of this infrastructure (psychexpert) was reviewed by a third-party bot within minutes and surfaced three defects the guide's own CI could never see — a skill hardcoding a default branch the guide itself does not use, a GNU-only date flag that fails on macOS, and a log write into a directory that does not exist on fresh machines. All three were fixed upstream and downstream within the hour; the installer that now automates adoption carries those fixes for every future project.
**Tags**: #workflow #portability #dogfooding #feedback-loop

---
