# Generic AI Development Infrastructure

A complete, generic infrastructure for software development with AI coding assistants (Claude Code, GitHub Copilot CLI, and compatible tools). Designed to make every session smarter than the last through persistent knowledge, structured workflows, and professional engineering standards.

---

## See It In Action

→ **[SYSTEM-OVERVIEW.md](SYSTEM-OVERVIEW.md)** — How it all fits together: a plain-language visual map of every skill, hook, and guard, the flows connecting them, and the idea behind the system.

→ **[demo/WALKTHROUGH.md](demo/WALKTHROUGH.md)** — A full session walkthrough: debugging a JWT auth bug using `/debug`, `/code-review`, `/commit`, and `/learn`, from bug report to committed fix in ~17 minutes.

---

## What This Is

A **plug-in infrastructure layer** you drop into any project to get:
- A senior principal engineer mindset embedded in your AI assistant
- 21 production-ready skill workflows (commit, PR, code review, architecture, code generation, decision-making, deployment, memory capture, etc.)
- Automatic knowledge capture across sessions — context that accumulates over time
- Self-criticism and quality gates built into every workflow
- A seeded knowledge base with architecture patterns, engineering principles, and common pitfalls

---

## Quick Start

### The fast way — one command
```bash
./install.sh /path/to/your-project
```
Copies everything below in one step — rules, bridge, all 21 skills, hooks,
validator, and CI — without overwriting anything that already exists, then
prints the only steps that need a human: filling in your project's conventions
and constraints, and the `/context` verification. Prefer to understand each
piece first? The manual steps:

### 1. Drop AGENTS.md and CLAUDE.md into your project root
```bash
cp AGENTS.md CLAUDE.md /path/to/your-project/
```
This gives your AI assistant professional engineering behavior. Both files are
needed: Claude Code reads `CLAUDE.md` (which imports `@AGENTS.md`), while other
assistants read `AGENTS.md` directly — without the `CLAUDE.md` bridge, Claude
Code never loads the rules at all.

### 2. Copy the .claude/ directory
```bash
cp -r .claude/ /path/to/your-project/.claude/
```
This installs all 21 skill workflows, their critic and strategy references, and the hook wiring (`settings.json`).

### 3. Memory needs no enabling
Claude Code's auto memory is on by default: Claude keeps per-project notes at
`~/.claude/projects/<project>/memory/` and loads the `MEMORY.md` index there at
the start of every session. Curated instructions load from `CLAUDE.md` (which
imports `AGENTS.md` here) and from `~/.claude/CLAUDE.md`. On top of that, this
repo's `/flush` and `/dream` skills maintain the session-log layer. Nothing to
switch on.

### 4. Seed your global memory
```bash
# Append the global memory seed to your user-level instructions
cat MEMORY.md >> ~/.claude/CLAUDE.md
```
`~/.claude/CLAUDE.md` is loaded at the start of every session in every project,
so this pre-loads engineering wisdom everywhere.

### 5. Use the session protocol
Read `session-protocol.md` to understand how to start, manage, and end sessions to maximize knowledge retention.

### Keeping installed projects current (live sync)
Set `CCGG_HOME` to your local clone of this guide (e.g. in each project's
`.claude/settings.json` under `"env"`, or your shell profile):
```json
{ "env": { "CCGG_HOME": "/path/to/claude-code-generic-guide" } }
```
The session-start hook then runs `update.sh` on every session start, resume, and
compact: it pulls the guide's latest master and overwrites the **CCGG-owned**
files (skills, hooks, validator) in the project. Rules files you customized
(`AGENTS.md`, `CLAUDE.md`, `WORKING-CHARTER.md`, `settings.json`) are never
touched. Skill updates apply mid-session on the next invocation; behavior-rule
updates load at the next session start. Customized a CCGG skill in place?
Rename its directory (it becomes yours) or leave `CCGG_HOME` unset.

### 6. Adopt the working charter
```bash
cp WORKING-CHARTER.md /path/to/your-project/WORKING-CHARTER.md
```
`WORKING-CHARTER.md` is the standing agreement for every session: the pre-execution checks, how answers are phrased, when to ask instead of decide, the skill vetting rule, and the four-stage quality gate that wakes only for real code changes. Fill in its **Standing Constraints** section per project.

---

## Repository Structure

```
claude-code-generic-guide/
│
├── install.sh                   ← One-command install into another project
├── update.sh                    ← Live sync: push merged guide changes into installed projects
├── SYSTEM-OVERVIEW.md           ← Plain-language visual map of the whole system
├── AGENTS.md                    ← Master AI behavior rules (copy to your project)
├── CLAUDE.md                    ← Import bridge: how Claude Code loads AGENTS.md
├── MEMORY.md                    ← Global memory seed template
├── session-protocol.md          ← How to manage sessions for knowledge persistence
├── WORKING-CHARTER.md           ← Standing operating agreement: how the AI thinks, talks, and gates code
│
├── .claude/                     ← AI tooling configuration
│   ├── settings.json            ← Hook registration (SessionStart, PreCompact, SessionEnd)
│   ├── skills/                  ← 21 reusable skill workflows
│   │   ├── commit/              ← Conventional commits
│   │   ├── pr/                  ← Pull request creation
│   │   ├── code-review/         ← Systematic code review
│   │   ├── architecture/        ← System architecture design
│   │   ├── requirements/        ← Requirements gathering
│   │   ├── testing/             ← Test suite generation
│   │   ├── debug/               ← Systematic debugging
│   │   ├── refactor/            ← Safe refactoring
│   │   ├── learn/               ← Knowledge capture
│   │   ├── standup/             ← Session summaries
│   │   ├── deploy/              ← Deployment workflow
│   │   ├── security-review/     ← Security audit
│   │   ├── code-generation/     ← Production-ready code generation
│   │   ├── flush/               ← Session summary to memory log
│   │   ├── dream/               ← Memory consolidation
│   │   ├── skillify/            ← Workflow capture as new skill
│   │   ├── reconcile-docs/      ← One home per rule across documents
│   │   ├── decide/              ← Structured decisions with debate and records
│   │   ├── product-brief/       ← Product/app idea evaluation
│   │   ├── git-steward/         ← Project bootstrap + automatic git lifecycle
│   │   └── deploy-steward/      ← Deploy target (Railway) + execution obligation
│   └── hooks/                   ← Session lifecycle hooks
│
├── decisions/                   ← Durable decision records and product briefs
│
├── knowledge-base/              ← Seeded engineering wisdom (patterns, principles, pitfalls)
├── tools/                       ← validate.py — the repo's CI quality gate
├── .github/workflows/           ← CI: runs the validator on every PR
│
└── docs/                        ← Full Claude Code / Copilot CLI reference (22 chapters)
    ├── 01-getting-started.md
    ├── ...
    └── 22-permissions-and-safety.md
```

---

## Available Skills

| Skill | Invoke | Purpose |
|-------|--------|---------|
| `commit` | `/commit` | Conventional commits with staged diff review |
| `pr` | `/pr` | PR creation with structured description |
| `code-review` | `/code-review` | Multi-dimension review with severity levels |
| `architecture` | `/architecture` | System design with trade-off analysis |
| `requirements` | `/requirements` | Vague idea → actionable spec |
| `testing` | `/testing` | Test suite generation (unit/integration/E2E) |
| `debug` | `/debug` | Systematic root cause analysis |
| `refactor` | `/refactor` | Safe refactoring with regression safety |
| `learn` | `/learn` | Explicit knowledge capture to memory |
| `standup` | `/standup` | Session summary / daily report |
| `deploy` | `/deploy` | Deployment with pre-flight checklist |
| `security-review` | `/security-review` | OWASP-based security audit |
| `code-generation` | `/code-generation` | Production-ready implementation with critic pass |
| `flush` | `/flush` | Structured session summary written to the memory log |
| `dream` | `/dream` | Consolidate session logs into the knowledge base |
| `skillify` | `/skillify` | Capture a completed workflow as a new skill |
| `reconcile-docs` | `/reconcile-docs` | One home per rule: merge duplicated statements across docs |
| `decide` | `/decide` | Structured decision: research, debate, durable record |
| `product-brief` | `/product-brief` | Evaluate a product/app idea: market research, Go/No-go/Pivot |
| `git-steward` | `/git-steward` | Name a new project, create its GitHub repo, own the git lifecycle automatically |
| `deploy-steward` | `/deploy-steward` | Provision Railway, enforce "done = executing deployed" at every milestone |

---

## Knowledge Persistence System

The knowledge system has three layers:

### 1. Automatic (built-in)
- Auto memory: Claude writes and recalls per-project notes in `~/.claude/projects/<project>/memory/`; the index loads every session
- `CLAUDE.md` (importing `AGENTS.md`) and `~/.claude/CLAUDE.md` load every session
- Session-start, pre-compaction, and session-end hooks fire via `.claude/settings.json` — every session opens with repo health and memory pointers

### 2. Semi-automatic (you trigger it)
- `/flush` — write an LLM-generated session summary before compacting or closing
- `/dream` — consolidate scattered session logs into organized topics (run weekly)
- `learn` skill — capture a specific pattern or decision

### 3. Manual (curated)
- `MEMORY.md` in the repo — the seed you append to `~/.claude/CLAUDE.md`
- `~/.claude/CLAUDE.md` — global engineering principles, loaded every session
- Knowledge base entries in `knowledge-base/entries/`
- Decision records in `decisions/` — written by `/decide` and `/product-brief`, versioned in git

---

## Customizing for Your Project

### Project conventions (in AGENTS.md)
Edit the "Project Conventions" section of `AGENTS.md` with your actual stack:
```markdown
## Project Conventions
- Language: TypeScript (strict mode)
- Framework: Next.js 14
- Database: PostgreSQL via Prisma
- Tests: Vitest
- Branch: feature/<ticket-id>-description
```

### Adding skills
Create `.claude/skills/<name>/SKILL.md` with YAML frontmatter:
```markdown
---
name: my-workflow
description: [trigger description for auto-invocation]
---
# Steps
...
```

### Capturing learnings
After any significant session:
```
/flush           ← save session summary
/learn           ← capture key patterns
/dream           ← consolidate (weekly)
```

---

## Claude Code / Copilot CLI Reference

Full 22-chapter documentation in `/docs/` — a snapshot mirror (see the provenance note in `docs/index.md`); for current product behavior the canonical source is https://code.claude.com/docs:
- Sessions, memory, skills, agents, MCP servers, plugins, hooks, and more
- See `docs/index.md` for the full table of contents

---

## Philosophy

> Every session should be smarter than the last.

This infrastructure is built around one principle: **knowledge should compound**. Each debugging session, architecture decision, and discovered pattern is an asset. The goal is to make the AI's context richer over time — so that by month 3, it starts sessions knowing the project's architecture, conventions, and history, rather than starting from scratch every time.

