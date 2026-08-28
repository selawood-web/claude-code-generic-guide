# User Manual — AI Development Infrastructure

**Version 1.0 · July 2026**

This manual explains how to install, configure, and use the generic AI development infrastructure in this repository. It is written for software developers who want an AI coding assistant that gets smarter the longer they use it.

---

## Table of Contents

1. [What This Is](#1-what-this-is)
2. [How It Works — The Big Picture](#2-how-it-works--the-big-picture)
3. [Prerequisites](#3-prerequisites)
4. [Installation](#4-installation)
5. [First Session — Getting Started](#5-first-session--getting-started)
6. [Skills Reference](#6-skills-reference)
7. [Memory System](#7-memory-system)
8. [Session Lifecycle](#8-session-lifecycle)
9. [Customizing for Your Project](#9-customizing-for-your-project)
10. [Critics and Knowledge Base](#10-critics-and-knowledge-base)
11. [Daily Workflow Cheatsheet](#11-daily-workflow-cheatsheet)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. What This Is

This repository is a **plug-in infrastructure layer** you drop on top of any software project to give your AI coding assistant (Claude Code, GitHub Copilot CLI, or any compatible tool) the behavior of a senior principal engineer.

Out of the box, every AI session starts from zero — no memory of previous decisions, no knowledge of your codebase, no understanding of your conventions. **This infrastructure fixes that.**

What you get:

| Component | What it does |
|-----------|-------------|
| `AGENTS.md` | Tells the AI how to behave: professional, concise, self-critical |
| 21 Skill workflows | Step-by-step procedures for every common dev task |
| Memory system | Knowledge that persists and grows across every session |
| Session protocol | A ritual that turns sessions into compounding knowledge |
| Knowledge base | Pre-seeded engineering wisdom (patterns, principles, pitfalls) |
| Critics & knowledge base | Review rubrics inside the skills, plus seeded engineering wisdom in `knowledge-base/` |

**The core promise:** By month 3, your AI starts sessions knowing your project's architecture, conventions, and history — instead of starting from scratch every time.

---

## 2. How It Works — The Big Picture

```
┌─────────────────────────────────────────────────────────┐
│                    Your Project                          │
│                                                         │
│  ┌──────────┐   ┌─────────────┐   ┌────────────────┐   │
│  │ AGENTS.md│   │ .claude/    │   │ ~/.claude/     │   │
│  │          │   │ skills/     │   │ memory/        │   │
│  │ WHO the  │   │             │   │                │   │
│  │ AI is    │   │ WHAT it     │   │ WHAT it        │   │
│  │          │   │ can do      │   │ remembers      │   │
│  └──────────┘   └─────────────┘   └────────────────┘   │
│       ↓                ↓                   ↓            │
│  ┌───────────────────────────────────────────────────┐  │
│  │              AI Coding Assistant                  │  │
│  │         (Claude Code / Copilot CLI)               │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Three layers, working together:**

1. **Identity layer (`AGENTS.md`)** — Rules that shape every response. The AI behaves as a senior principal engineer: direct, self-critical, concise, and always extracting knowledge.

2. **Skills layer (`.claude/skills/`)** — Executable workflows. When you say "review this code" or "commit my changes," the AI follows a professional, step-by-step procedure instead of improvising.

3. **Memory layer (`~/.claude/memory/`)** — Persistent knowledge. Decisions, patterns, and findings are saved between sessions. Each session builds on the last.

---

## 3. Prerequisites

| Requirement | Notes |
|-------------|-------|
| Claude Code **or** GitHub Copilot CLI | Either works. Claude Code: `npm install -g @anthropic-ai/claude-code`. Copilot CLI: install from VS Code. |
| Git | Required for version control skills |
| `gh` CLI (optional) | Required for PR and GitHub-related skills. Install: [cli.github.com](https://cli.github.com) |
| Memory feature enabled | See [Installation](#4-installation) |

---

## 4. Installation

**The fast way:** run `./install.sh /path/to/your-project` from this repo — it
performs steps 1–2 below in one command, never overwrites existing files, and
prints what remains for you. The manual steps, for understanding each piece:

### Step 1 — Copy `AGENTS.md` and `CLAUDE.md` into your project

```bash
cp /path/to/this-repo/AGENTS.md /path/to/this-repo/CLAUDE.md /path/to/your-project/
```

Both files are needed: Claude Code reads `CLAUDE.md` (which imports
`@AGENTS.md`); other assistants read `AGENTS.md` directly. Without the bridge,
Claude Code never loads the rules at all.

This is the single most important file. It immediately gives the AI professional behavior for your project. **Commit it to version control** so your whole team benefits.

> **Tip:** Edit the "Project Conventions" section at the bottom of `AGENTS.md` to describe your actual tech stack, test runner, branch naming, etc. The AI will follow these conventions automatically.

---

### Step 2 — Copy the `.claude/` directory

```bash
cp -r /path/to/this-repo/.claude/ /path/to/your-project/.claude/
```

This installs:
- All 21 skill workflows
- `settings.json`, which registers the session lifecycle hooks
- The hook scripts themselves (they reference only `$HOME`, so they are portable)

> **Tip:** Commit the whole `.claude/` directory to version control — skills, `settings.json`, and hooks are all portable.

---

### Step 3 — Memory needs no enabling

Memory is what makes sessions accumulate knowledge, and in Claude Code it is
on by default: Claude keeps per-project notes at
`~/.claude/projects/<project>/memory/` and loads the `MEMORY.md` index there
every session. Your curated context loads from `CLAUDE.md` and
`~/.claude/CLAUDE.md`. The `/flush` and `/dream` skills add the session-log
layer on top.

Verify what loaded in any session:
```
/context   ← lists the memory files in context
/memory    ← browse and edit them; toggle auto memory
```

---

### Step 4 — Seed your global memory

Append the engineering wisdom template to your user-level instructions:

```bash
cat /path/to/this-repo/MEMORY.md >> ~/.claude/CLAUDE.md
```

`~/.claude/CLAUDE.md` is loaded at the start of every session in every project, so this pre-loads principles about architecture, code quality, security, performance, and operations everywhere. **Edit this file anytime** (`/memory` opens it) — the next session picks up your changes.

---

### Step 5 — Verify installation

Start a new AI session in your project directory and ask:

```
what skills are available?
```

You should see the 21 installed skills listed (typing `/` also filters through everything invocable). Then:

```
what do you remember?
```

You should see the global engineering principles you seeded into `~/.claude/CLAUDE.md`.

If skills don't appear, check that `.claude/skills/` exists in the project root and that each `SKILL.md` has valid frontmatter — a malformed header fails silently. `python3 tools/validate.py` checks exactly this.

---

## 5. First Session — Getting Started

### Starting a session

```bash
# In your project directory:
claude

# Or with Copilot CLI:
# Open VS Code terminal and start a new Copilot chat
```

### The first thing to say

Tell the AI your goal for this session:

> "I want to build a user authentication system with email/password login. Start with requirements."

The AI will invoke the **requirements skill** automatically and walk you through a structured process.

### What the AI does automatically

- Reads `AGENTS.md` — knows your project conventions
- Searches memory — loads any relevant knowledge from previous sessions
- Selects the right skill — matches your request to the best workflow

---

## 6. Skills Reference

Skills are invoked by typing `/skill-name` or just describing what you want — the AI picks the right skill automatically.

---

### `/commit` — Git Commit

**Use when:** You want to commit changes.

**What it does:**
1. Inspects staged and unstaged changes
2. Determines the right commit type (`feat`, `fix`, `refactor`, etc.)
3. Writes a conventional commit message
4. Commits and confirms

**Examples:**
```
commit my changes
/commit
save my work
```

**Sample output:**
```
feat(auth): add JWT token refresh endpoint

Adds a POST /auth/refresh route that accepts a valid refresh token
and returns a new access token. Refresh tokens expire after 30 days.
```

---

### `/pr` — Pull Request

**Use when:** You want to create a GitHub pull request.

**What it does:**
1. Verifies all changes are committed
2. Pushes the branch if not already pushed
3. Generates a structured PR description (summary, changes, testing notes)
4. Creates the PR via `gh pr create`

**Examples:**
```
create a PR
open a pull request
/pr
```

---

### `/code-review` — Code Review

**Use when:** You want professional feedback on code.

**What it does:**
Reviews code across 6 dimensions: correctness, security, performance, maintainability, test coverage, and style. Issues are categorized by severity:

| Level | Meaning |
|-------|---------|
| 🔴 BLOCKER | Must fix before merge |
| 🟡 IMPORTANT | Should fix — significant quality concern |
| 🔵 SUGGESTION | Optional improvement |
| ✅ GOOD | Acknowledges quality work |

**Examples:**
```
review my code
review the last commit
/code-review
review PR #42
```

---

### `/architecture` — System Architecture Design

**Use when:** You need to design or plan a system.

**What it does:**
Follows a structured process:
1. Requirements extraction (scale, latency, constraints)
2. High-level component design
3. Technology choices with rationale and rejected alternatives
4. Trade-off analysis table
5. Risk identification
6. MVP scope definition

The architecture critic runs automatically — any critical issues are addressed before the design is presented.

**Examples:**
```
design an architecture for a real-time chat app
how should I structure a multi-tenant SaaS backend?
/architecture
```

---

### `/requirements` — Requirements Gathering

**Use when:** You have a vague idea and need to turn it into a specification.

**What it does:**
Conducts a structured interview to extract:
- The actual problem (not the stated solution)
- Success criteria
- MVP scope vs. v2 features
- User stories with acceptance criteria
- Constraints and open questions

Produces a spec document precise enough to implement without ambiguity.

**Examples:**
```
I want to build a notification system
help me plan this feature
/requirements
I have an idea for...
```

---

### `/testing` — Test Suite Generation

**Use when:** You need to write tests.

**What it does:**
Selects the appropriate test type (unit, integration, E2E), generates tests following the Arrange-Act-Assert structure, covers happy path + edge cases + failure paths, and integrates with your existing test framework.

**Examples:**
```
write tests for this function
add test coverage
/testing
unit tests for the auth module
```

---

### `/debug` — Systematic Debugging

**Use when:** Something is broken or not behaving as expected.

**What it does:**
Follows a systematic process:
1. Reproduce the bug reliably
2. Narrow the scope (binary search)
3. Form a hypothesis
4. Test the hypothesis
5. Find the root cause (not just the symptom)
6. Write a regression test

**Examples:**
```
this function isn't working
/debug
I'm getting a 500 error when...
why is this happening?
```

---

### `/refactor` — Code Refactoring

**Use when:** Code needs to be cleaned up without changing behavior.

**What it does:**
1. Writes characterization tests first (if none exist)
2. Identifies the specific problem (too long, duplicated, unclear, etc.)
3. Applies one refactoring at a time
4. Runs tests after each step
5. Commits each working step

**Examples:**
```
refactor this class
clean up this file
/refactor
this code is too complex
```

---

### `/learn` — Knowledge Capture

**Use when:** You discover something worth remembering for future sessions.

**What it does:**
Extracts the reusable principle (not just the raw fact), categorizes and tags it, and writes it to the appropriate memory file (project-specific or global).

**Examples:**
```
learn! the JWT library doesn't throw on missing claims
remember this pattern
/learn
```

**Format for explicit capture:**
```
remember: [principle] — reason: [why it matters]
remember globally: [universal principle]
```

---

### `/standup` — Session Summary

**Use when:** You want a summary of what was accomplished.

**What it does:**
Generates a structured standup report:
- ✅ Done
- 🔄 In Progress
- 🔜 Next
- 💡 Notes

**Examples:**
```
standup
what did we do today?
/standup
session summary
```

---

### `/deploy` — Deployment

**Use when:** You want to deploy to an environment.

**What it does:**
Runs through a pre-deployment checklist, executes the deployment (adapted to your platform), verifies the deployment succeeded, and monitors for the first 15 minutes.

**Examples:**
```
deploy to staging
/deploy
ship this
```

---

### `/security-review` — Security Audit

**Use when:** You want to check code for security vulnerabilities.

**What it does:**
Reviews against the OWASP Top 10:
- SQL/command injection
- Broken authentication
- Sensitive data exposure
- Security misconfigurations
- Broken access control
- XSS
- Insecure dependencies
- Insecure deserialization
- SSRF

Findings are rated CRITICAL / HIGH / MEDIUM / LOW.

**Examples:**
```
security review
check for vulnerabilities
/security-review
is this secure?
```

---

### `/code-generation` — Production-Ready Implementation

**Use when:** You want code implemented to the full quality bar, not just "working".

**What it does:**
1. Reads existing patterns in the codebase first
2. Writes interface, happy path, edge cases, and explicit error handling in that order
3. Writes tests to the charter's bar (happy path, three edge cases, one failure mode)
4. Runs the code critic checklist before presenting — no unfixed BLOCKERs

**Examples:**
```
implement the refresh endpoint
write code for this
/code-generation
```

---

### `/flush` — Session Summary to Memory

**Use when:** A productive session is ending, or before `/compact`.

**What it does:**
1. Resolves the project's session-log directory under `~/.claude/memory/`
2. Gathers the session's facts from git and the conversation
3. Writes a structured summary: goal, what happened, decisions with rationale, files changed, open threads
4. Prompts you to promote durable findings via `/learn`

**Examples:**
```
/flush
save this session
flush before we compact
```

---

### `/dream` — Memory Consolidation

**Use when:** Five or more session logs have accumulated, or weekly.

**What it does:**
1. Reads all session logs and the project `MEMORY.md`
2. Merges: dedupes (keeping the version with rationale), groups by section, flags contradictions and staleness instead of dropping them
3. Archives processed logs — nothing is ever deleted
4. Reports entries before → after and anything marked `[VERIFY:]`

Stops by itself if there are fewer than two logs to consolidate.

**Examples:**
```
/dream
consolidate memory
clean up what you know
```

---

### `/skillify` — Capture a Workflow as a Skill

**Use when:** You just finished a multi-step process the team will repeat.

**What it does:**
1. Checks the workflow deserves to be a skill (repeatable, not already covered)
2. Extracts the steps actually taken — including what went wrong, so the skill encodes the corrected path
3. Writes `.claude/skills/<name>/SKILL.md` in the house format and validates the frontmatter
4. Registers it in the catalog tables and reminds you to commit it

**Examples:**
```
/skillify
make this a skill
capture this workflow
```

---

### `/reconcile-docs` — One Home Per Rule

**Use when:** Two documents state the same rule differently, or duplication has crept across docs.

**What it does:**
1. Finds every statement of the rule, including rewordings
2. Picks the authoritative home; resolves conflicts before rewriting (never averages two versions)
3. Rewrites every other site as a reference, using verified-unique replacements
4. Re-sweeps for stragglers, then runs the repo's validator and states the evidence

**Examples:**
```
/reconcile-docs
these two files disagree
remove the duplication between the README and the manual
```

---

### `/decide` — Structured Decision

**Use when:** Choosing between tools, frameworks, or approaches; a go/no-go call; any "X vs Y" or "should we" question.

**What it does:**
1. Frames the decision (type, reversibility, stakes) and picks a light or full path
2. Recalls prior decisions from `decisions/` and memory before re-litigating anything
3. Elicits weighted criteria first, researches current options live (never from stale memory), then builds a trade-off table that always includes doing nothing
4. Debates the options through five personas (Champion, Skeptic, Economist, User Advocate, Operator) and answers every strongest objection in the synthesis
5. Writes a durable record to `decisions/` with a revisit trigger, and promotes the conclusion to memory

**Examples:**
```
/decide SQLite vs Postgres for this project
help me decide which auth provider to use
should we rewrite this service in Go?
```

---

### `/product-brief` — Product Idea Evaluation

**Use when:** You have an app, tool, or feature idea and want to know if it is worth building — before any spec is written.

**What it does:**
1. Classifies the idea and digs for the trigger behind it (the real problem)
2. Researches the market live: competitors, pricing, real differentiation
3. Runs the five-persona viability debate, then delivers an explicit **Go / No-go / Pivot** verdict — "maybe later" is not allowed
4. On Go, hands MVP definition to `/requirements` and links the spec
5. Records the brief in `decisions/` so a returning idea meets its old objections

**Examples:**
```
/product-brief a meal-planning app for shift workers
I have an app idea — is it worth building?
evaluate this feature idea
```

---

### `/git-steward` — Project Bootstrap & Automatic Git

**Use when:** Starting a new project that needs a name and a GitHub repo, or when you want git handled automatically from here on.

**What it does:**
1. For a new project: proposes 2–3 kebab-case names, initializes git with a stack-appropriate `.gitignore`, and creates the GitHub repository (private by default)
2. From then on, acts as standing steward: working branch before the first code change, a conventional commit (via `/commit`) at each verified milestone, a push after each commit
3. Offers `/pr` when work is review-ready — opening the PR is proposed, never assumed
4. Hard boundaries stay: no force-push, no direct pushes to main, no committing unverified work, no going public without your say-so

**Examples:**
```
/git-steward a CLI that tracks my reading list
set up git and a repo for this project
handle git for me automatically
```

---

### `/deploy-steward` — Deploy Target & Execution Obligation

**Use when:** Setting up where a project runs (Railway by default), or when a project has working code but no deploy target.

**What it does:**
1. Provisions Railway: `railway init`, a staging environment, secrets via `railway variables` (never git), a required health endpoint — after confirming plan/cost
2. Enforces the execution obligation: every milestone deploys to staging and must pass a health check and smoke test — "works on my machine" is not done
3. Hooks into the whole lifecycle: deployability is checked at brainstorm (`/product-brief`), definition (`/requirements`), design (`/architecture`), bootstrap (`/git-steward`), and ship (`/deploy`)
4. Production stays gated: explicit confirmation + the `/deploy` checklist; destructive acts (tearing down environments) always ask first

**Examples:**
```
/deploy-steward
set up deployment on railway
make this run in the cloud from day one
```

---

## 7. Memory System

Memory is the most powerful feature of this infrastructure. It is what makes sessions accumulate knowledge instead of resetting.

### Where memory lives

```
~/.claude/memory/
  MEMORY.md                          ← Global (all projects)
  <project-slug>-<hash>/
    MEMORY.md                        ← This project only
    sessions/
      2026-07-15.md                  ← Session summaries
      2026-07-14.md
```

### Saving to memory

**Automatic:** At the end of each session, a metadata summary is saved automatically (message counts, topics, files touched).

**Semi-automatic (recommended):** Run `/flush` before ending a session or before compaction. This generates a rich LLM-written summary of decisions, patterns, and findings — indexed and searchable.

**Manual — explicit fact:**
```
remember: always use parameterized queries in this codebase — reason: the ORM has a known escape issue with special characters
```

**Manual — global principle:**
```
remember globally: always enable strict mode in TypeScript — reason: catches null/undefined errors at compile time
```

**Manual — via skill:**
```
/learn
```

### Reading from memory

**Automatic:** At the start of each session, `CLAUDE.md`, `~/.claude/CLAUDE.md`, and the auto-memory `MEMORY.md` index are loaded; topic files are read on demand.

**Manual queries:**
```
what do you remember about this project?
what do you know about authentication in this codebase?
search memory for "database migration"
```

**Browse all memory files:**
```
/memory
```

### Consolidating memory (weekly task)

After 5+ sessions, run:
```
/dream
```

This consolidates scattered session logs into an organized, deduplicated knowledge base. Reduces noise and improves search quality.

### Memory quality rules

Good memory entries are:
- **Specific** — not "we use React" but "we use React 18 with the App Router — pages go in `app/`, not `pages/`"
- **Rationale-bearing** — include the *why*, not just the *what*
- **Durable** — written as permanent statements, not "today we decided X"

Bad memory entries:
- Vague or context-free
- Sensitive data (credentials, PII)
- One-off facts that won't repeat

---

## 8. Session Lifecycle

### Starting a session (checklist)

1. Open your project directory
2. Start the AI tool (`claude` or Copilot chat)
3. `CLAUDE.md` and the auto-memory index load automatically — verify with:
   ```
   what do you remember about this project?
   ```
4. State your goal for this session explicitly
5. Review any open work:
   ```
   git --no-pager log --oneline -10
   gh issue list --assignee @me
   ```

### During a session

**When context gets large:** Run `/compact` before the tool forces it:
```
/compact focus on [what's most important to preserve]
```

**When you discover something important:** Capture it immediately:
```
remember: [discovery] — reason: [why it matters]
```

Don't wait until the end of the session. Memory is most accurate when captured in the moment.

### Ending a session (checklist)

Run these before closing:

```
# 1. Flush session summary to memory
/flush

# 2. Capture key learnings
/learn

# 3. Commit any open work
/commit

# 4. Weekly: consolidate memory
/dream
```

### Resuming a session

```bash
# Continue the most recent session for this directory
claude -c

# Resume a specific session by ID
claude --resume <session-id>

# Browse all sessions (in TUI)
/resume
```

### The knowledge growth curve

| Time | What the AI knows |
|------|------------------|
| Day 1 | Global engineering principles (from `MEMORY.md`) |
| Week 1 | Your tech stack, architecture decisions |
| Week 2 | Bug patterns, API quirks, debugging paths |
| Month 1 | Team conventions, domain knowledge |
| Month 3+ | Deep project history — the AI "knows this codebase" |

---

## 9. Customizing for Your Project

### 1. Edit `AGENTS.md` — Project Conventions

Find the "Project Conventions" section and replace the example with your actual stack:

```markdown
## Project Conventions

- Language: TypeScript (strict mode)
- Framework: Next.js 14 (App Router)
- Database: PostgreSQL via Prisma ORM
- Tests: Vitest + React Testing Library
- Style: ESLint + Prettier (configured in root)
- Branch naming: feature/<JIRA-ticket>-short-description
- PR size limit: 400 lines (excluding generated/migration files)
- Commit format: conventional commits (see examples in git log)
```

### 2. Add your own skills

Create a new skill for any repeatable workflow:

```bash
mkdir -p .claude/skills/my-workflow
```

Create `.claude/skills/my-workflow/SKILL.md`:

```markdown
---
name: my-workflow
description: [What this does and when to invoke it — be specific about trigger phrases]
when-to-use: [trigger phrase 1], [trigger phrase 2]
---

# My Workflow

## Steps

1. [First step with specific commands]
2. [Second step]
3. [Verify it worked]
```

Or use the built-in skill creator:
```
/skillify
```

### 3. Capture project conventions in memory

After establishing a convention with your team, save it:

```
remember: we use kebab-case for API route paths (e.g. /user-profile not /userProfile) — reason: REST convention and consistent with our nginx config
```

### 4. Update global memory with your principles

Edit `~/.claude/CLAUDE.md` directly (or via `/memory`) to add your own engineering principles. Changes load at the start of the next session.

### 5. Project-specific AGENTS.md in subdirectories

For monorepos or projects with distinct parts, add AGENTS.md files in subdirectories:

```
my-repo/
  AGENTS.md              ← repo-wide rules
  packages/
    frontend/
      AGENTS.md          ← "Use React. Components in src/components/"
    backend/
      AGENTS.md          ← "Use Express. REST conventions."
```

Rules accumulate — the AI sees all of them, with deeper files taking precedence.

---

## 10. Critics and Knowledge Base

The AI's self-review rubrics and seeded engineering wisdom live inside the
structures that actually use them — there is no separate orchestration layer.
The identity and rules are `AGENTS.md` (loaded via `CLAUDE.md`); skill
selection is the assistant's native auto-invocation from each skill's
description; the operating agreement is `WORKING-CHARTER.md`.

### Critics (inside the skills that run them)

| File | Purpose |
|------|---------|
| `.claude/skills/code-review/code-critic.md` | Full code review rubric: 6 dimensions, severity scale |
| `.claude/skills/architecture/architecture-critic.md` | Full architecture rubric: 7 dimensions, checklist |
| `.claude/skills/testing/strategy.md` | Test strategy by project phase, coverage targets by code type |
| `.claude/skills/learn/extraction-rules.md` | What to capture to memory, what to skip, entry format |

Each is referenced from its skill's `SKILL.md` and travels with the skill when
you copy `.claude/` into a project.

### Knowledge base (`knowledge-base/entries/`)

Pre-seeded with engineering wisdom:

| File | Contents |
|------|----------|
| `architecture-patterns.md` | Monolith vs. microservices, CQRS, repository pattern, hexagonal architecture |
| `engineering-principles.md` | Naming, error handling, SRP, composition, fail fast, immutability |
| `common-pitfalls.md` | N+1 queries, race conditions, JWT attacks, IDOR, migration mistakes |

**Add your own entries** by creating new `.md` files in this directory. Use the same format:

```markdown
## [Category]

### [Topic Title]
**Principle**: [The rule in one sentence]
**Context**: [When this applies]
**Rationale**: [Why — the reasoning]
**Tags**: #tag1 #tag2
```

### Operating modes

The AI automatically selects a mode based on your request:

| Mode | Trigger words | What happens |
|------|--------------|-------------|
| **Planner** | "I want to build", "help me", vague idea | `/requirements` skill |
| **Architect** | "design", "structure", "how should I..." | `/architecture` skill + its critic file |
| **Builder** | "implement", "write code", "add feature" | `/code-generation` skill + the code critic |
| **Reviewer** | "review", "check my code" | `/code-review` skill + its critic file |
| **Debugger** | "bug", "error", "not working" | `/debug` skill |

---

## 11. Daily Workflow Cheatsheet

### Starting work

```bash
claude -c                          # resume last session
```
```
what do you remember about this project?   # verify memory loaded
I want to: [your goal today]               # state the goal
```

### Common tasks

```
/requirements    ← new feature idea
/architecture    ← design a system
/debug           ← something is broken
/code-review     ← review changes
/refactor        ← clean up code
/testing         ← write tests
/security-review ← audit for vulnerabilities
```

### Git workflow

```
/commit          ← stage and commit with conventional message
/pr              ← create a pull request
/deploy          ← deploy to an environment
```

### Knowledge management

```
remember: [fact] — reason: [why]   ← save something now
/learn                             ← structured knowledge capture
/flush                             ← save session summary (before ending)
/dream                             ← consolidate memory (weekly)
/memory                            ← browse all memory files
```

### Context management

```
/compact [focus]       ← compress history before it auto-compacts
/context               ← see what's loaded and how much context it uses
/memory                ← browse and edit memory files
```

---

## 12. Troubleshooting

### Skills not appearing

```bash
# Verify the skills directory exists and every SKILL.md parses
ls .claude/skills/
python3 tools/validate.py
```

A skill with malformed frontmatter does not error — it just never loads.

Skills require a `SKILL.md` file inside each skill directory. Check that the file exists and has valid YAML frontmatter (`---` delimiters and `name`/`description` fields).

---

### Memory not working

In a session, run `/context` to see which memory files actually loaded, and
`/memory` to browse them. Auto memory can be toggled from `/memory` (it stores
`autoMemoryEnabled` in `~/.claude/settings.json`); check it was not switched
off. If a file is missing from `/context`, Claude cannot see it.

---

### AI not following AGENTS.md rules

Claude Code reads `CLAUDE.md`, not `AGENTS.md`. Check that the project root has
a `CLAUDE.md` importing `@AGENTS.md` (this repo ships one), then run `/context`
in a session and confirm the files appear under **Memory files**. If they are
listed and still ignored, make the instructions more specific — vague rules get
vague compliance.

---

### `/flush` not saving anything useful

Flush works best when the session has substantial history. If you just started or the session was compacted, flush will save minimal content. Use `/learn` for targeted knowledge capture instead.

---

### Context window fills up too fast

Use `/compact` proactively with a focus hint:
```
/compact focus on [the most important current context]
```

For very long sessions, `/compact` multiple times is fine. The project-root `CLAUDE.md` is re-injected after each compaction, so your standing instructions survive; conversation-only context does not, which is why `/flush` before compacting matters.

---

### The AI is ignoring my instructions

Check precedence order:
1. AGENTS.md rules (highest — always active)
2. Skill SKILL.md instructions (active when skill is invoked)
3. Your in-session prompt

If the AI is overriding your request, it may be following a rule in AGENTS.md that conflicts. Edit AGENTS.md to resolve conflicts.

---

### Knowledge is not accumulating across sessions

Verify you are:
1. Running `/flush` before ending sessions
2. Starting new sessions in the same directory (memory is directory-scoped)
3. Using `claude -c` to resume rather than starting a fresh session

Check what's in memory:
```bash
ls ~/.claude/projects/*/memory/           # auto memory — Claude's own notes
ls ~/.claude/memory/*/sessions/           # session logs written by /flush
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Start AI | `claude` or `claude -c` (resume) |
| List skills | ask "what skills are available?" |
| Commit | `/commit` |
| Pull Request | `/pr` |
| Code review | `/code-review` |
| Design system | `/architecture` |
| Gather requirements | `/requirements` |
| Write tests | `/testing` |
| Debug | `/debug` |
| Refactor | `/refactor` |
| Security audit | `/security-review` |
| Save knowledge | `/learn` or `remember: ...` |
| Session summary | `/standup` |
| Save session | `/flush` |
| Consolidate memory | `/dream` |
| Browse memory | `/memory` |
| Compress context | `/compact [focus]` |
| Check what's loaded | `/context` |
| Create new skill | `/skillify` |

---

*For the full Claude Code / Copilot CLI reference, see the `docs/` directory (22 chapters covering every feature).*
