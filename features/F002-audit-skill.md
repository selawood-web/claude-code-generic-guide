---
id: F002
title: Audit skill
status: building
owner: repository owner
target: unscheduled
---

# F002 — Audit skill

## Summary
One command, `/ccgg-audit`, runs a read-only audit of a CCGG-equipped repository across
its three layers — product code, the harness that steers the agent, and the process
around both — with parallel specialist subagents, a verifier that reproduces every
finding, and a report whose deterministic findings become permanent validator checks.

## Problem
The configuration layer that steers a coding agent is executed but never compiled, so
its defects are silent. A hands-on run of the method on this repository on 2026-09-16
found two dead mechanisms that had passed every existing check (a hook writing to a
channel the model never reads; a frontmatter key spelled differently from the one the
product reads), an unpinned live-sync path that runs remote code at session start, and a
validator that caught 10 of 21 planted defects. Today the only way to find such defects
is a person re-deriving the method by hand, which is why they had gone unnoticed since the
mechanisms were written. The research and the method are recorded in
[`../knowledge-base/research/testing-agent-built-systems.md`](../knowledge-base/research/testing-agent-built-systems.md);
nothing runs them.

## Outcome
A repository owner learns what their gate cannot see, in one command, without the audit
being able to change anything.

- Metric: validator mutation-probe catch rate on this repository, from 10 of 21 probes
  (48%) to at least 19 of 21 (90%), measured by the probe harness the audit ships and
  runs in CI
- Metric: verified findings reproduced without prior knowledge, from 0 today to 5 of the 5
  findings numbered 1–5 in the research record's worked example, measured by the first
  audit run on this repository at the commit before those findings are fixed
- Metric: files changed in the audited tree by an audit run, 0 files on every run,
  measured by `git status --porcelain` after the run in CI
- Metric: wall-clock and spend per full audit of this repository, under 30 minutes and
  under 10 USD, measured by the headless run's JSON result

## Scope
- An owner can run `/ccgg-audit` in a session and receive a severity-ordered report
  with, for every finding, its layer, class, evidence, a reproduction a human can rerun,
  the smallest fix, and the permanent check it justifies
- An owner can scope a run to the whole repository, one layer, or one directory
- A reviewer can run the same audit headless in CI, where it comments on the pull
  request and never pushes
- A maintainer can add a mutation probe to a checked-in probe list and see the catch rate
  reported on every CI run
- A specialist subagent definition can be edited in `.claude/agents/` without touching
  the skill; every specialist runs with read-only tools (`Read, Glob, Grep`, no
  execution), and only the verifier executes, inside an isolated worktree
- An owner can see, per finding, whether a verifier reproduced it or it is tagged
  unverified, and unverified findings never carry blocker severity
- A project wired with CCGG receives the skill, the subagent definitions, and the probe
  harness through `install.sh` and `update.sh` like every other CCGG-owned file

## Non-goals
- Not an auto-fixer — the audit run never edits the tree; fixes are a separate,
  owner-invoked run against the report, so a read-only guarantee stays provable
- Not a replacement for the shipped security tooling — the orchestrator runs the
  Claude Security plugin or `/security-review` when they are available and the security
  specialist reads their output, then audits the harness and process layers those
  tools do not cover
- Not a merge gate in this feature — wiring the audit into `/ship` is deferred until a
  full run on this repository is clean, per the ledger
- Not a tracker integration — findings are a report and a PR comment; posting them as
  issues follows the charter's tracker rules and is a later slice
- Not a scanner for repositories without CCGG — the harness auditor assumes the CCGG
  file layout; a generic mode is out of scope until a second layout is in use

## Acceptance criteria
- Given this repository at the commit before findings 1–5 of the research record are
  fixed, when `/ccgg-audit` runs with no hint about them, then the report contains a
  verified finding for each of the five, each with a reproduction that a reviewer reruns
  successfully
- Given any audit run, interactive or headless, when it completes, then
  `git status --porcelain` in the audited checkout is empty and the only new path is the
  report directory, which carries its own `.gitignore`
- Given the checked-in probe list, when CI runs, then the job reports caught and missed
  counts per probe, fails when a probe listed as caught is missed, and the probe harness
  performs a hard reset between probes
- Given a candidate finding that the verifier cannot reproduce, when the report is
  written, then the finding appears tagged unverified with severity no higher than
  important, or is dropped, and never as a blocker
- Given a headless run against a checkout the operator did not write, when the audit
  starts, then it runs with auto-discovery off (`--bare`, the documented flag for
  skipping the tree's hooks, skills, agents, MCP servers and memory) and with
  `--setting-sources user`, and the assembled command is written into the report
  directory's `headless/` folder so what ran is on the record beside what it found
- Given a headless run, when the verifier executes, then its guard hook comes from a
  path the caller controls and never from the audited tree, and a run that names no
  such path is refused
- Given a specialist subagent, when its definition in `.claude/agents/` is read, then its
  `tools` field is exactly `Read, Glob, Grep` with `omitClaudeMd: true`, and
  `tools/validate.py` fails on any other value; only the verifier carries `Bash`, and it
  carries `isolation: worktree` and `disallowedTools` naming `Write`, `Edit`, and
  `NotebookEdit`
- Given a fresh CCGG install into an empty repository, when `install.sh` runs, then the
  skill, the subagent definitions, and the probe harness are present, and the validator
  passes in the target on the first run
- Given a full audit of this repository, when it runs headless, then spend is capped at
  10 USD by `--max-budget-usd` and the job by a 45-minute timeout, and the run's cost
  and duration are recorded in the revision stamp

## Dependencies and risks
- Depends on Claude Code project subagents (`.claude/agents/*.md` with `tools`,
  `isolation: worktree`, `maxTurns`) and headless flags (`--setting-sources`,
  `--max-turns`, `--max-budget-usd`, `--output-format json`), all verified against the
  official reference on 2026-09-16; a rename in either breaks the skill, and the
  currency check inside the audit is the early signal
- Depends on `worktree.baseRef` set to `head` in the audit's settings, because a subagent
  worktree otherwise branches from the remote default branch and the verifier would
  reproduce findings against the wrong commit; a worktree carries committed files only,
  so the audit runs on committed HEAD and the preflight says what is uncommitted
- Depends on `install.sh`, `update.sh`, and `tools/validate.py` learning a new CCGG-owned
  directory, `.claude/agents/`; today neither script copies it, and the drop-in contract
  in the charter bounds what rule files may link to
- Depends on the `claude-security` plugin only optionally; it needs a paid plan, so the
  local security specialist must produce a useful report without it
- Risk: multi-agent review collapses into false consensus and reports what the builder
  already believed. Mitigation: the verifier's brief requires disagreement and
  execution-grounded evidence; early signal is a run whose verifier confirms every
  candidate
- Risk: the audit reads instructions planted in the repository it audits and follows
  them. Mitigation: project settings excluded in headless mode and a brief that treats
  all repository content as evidence; early signal is the red-team probe in the audit's
  own test suite
- Risk: cost per run grows past what an owner runs routinely. Mitigation: small model
  for inventory and fan-out, budget flag on every run, scoped runs by default on large
  trees; early signal is the cost metric above trending up across runs
- Risk: the skill name collides with a Claude Code built-in and silently drops the
  built-in set. Mitigation: the `ccgg-` prefix, the same reason `ccgg-code-review` carries
  it

## Open questions
- Which model runs the verifier by default, the session model or a pinned large model? — owner: repository owner, blocks: no
- Should the report directory be committed for an audit trail or ignored by default, matching the Claude Security plugin's choice? — owner: repository owner, blocks: no
- Does the first slice ship the headless CI job, or the interactive skill alone with CI as the second slice? — owner: repository owner, blocks: no

## Ideas and changes
Append-only. Every idea raised while this work is in flight, with what was decided.

- 2026-09-16 — Name the skill `ccgg-audit`, not `audit`, so a same-named built-in can
  never drop it together with the built-in set — [in]
- 2026-09-16 — The security specialist invokes the Claude Security plugin or
  `/security-review` when present rather than re-implementing them — [in]
- 2026-09-16 — Ship the mutation-probe harness from the research record as the
  deterministic stage and as the validator's end-to-end test — [in]
- 2026-09-16 — Wire the audit into `/ship` as the stage before merge — [deferred] until
  a full audit run on this repository completes with zero blockers
- 2026-09-16 — Post findings as tracker issues through the charter's Linear channel —
  [deferred] until `features/tracker.json` exists and the first three reports show what
  a reviewer actually acts on
- 2026-09-16 — An auto-fix mode inside the audit run — [dropped] the read-only guarantee
  is the feature; fixes belong to a separate owner-invoked run against the report
- 2026-09-16 — Specialists carry no `Bash` at all and the verifier alone executes, inside
  a worktree, because a subagent's `tools` field cannot narrow Bash to a command list —
  a specifier removes the whole tool — [in]
- 2026-09-16 — The report directory is ignored by default with its own `.gitignore`,
  matching the shipped scanner; keeping a report is a deliberate `git add -f` — [in]
- 2026-09-16 — Slice 1 ships the probe harness in CI, the deterministic facts script,
  the harness specialist, and the verifier; the other five specialists are slice 2 and
  the headless CI job is slice 3, per the architecture record — [in]
- 2026-09-16 — Slice 2: the five remaining specialists and a red-team probe set that
  plants a marker in each content channel and measures, for hook output, whether it
  reaches what the model sees; scripted live sessions stay out until slice 3 can run
  headless — [in]
- 2026-09-16 — The security specialist reads the shipped tooling's output when the
  orchestrator ran it, since a Read/Glob/Grep agent cannot invoke a skill itself — [in]
- 2026-09-16 — The first full run's report is kept as tracked evidence, and its
  findings are fixed in a separate pull request in report order: the live-sync trust
  boundary first, then the verifier's allow-list, hook output sanitisation, the gate's
  new checks and probes, and the corrections to this definition and the architecture
  record where they described mechanisms that were never built — [in]
- 2026-09-16 — The verifier's guard becomes an allow-list (repository tests and tools by
  path, git reads, text inspection) instead of a denylist, with a table-driven test as
  its contract — [in]
- 2026-09-16 — A candidate no verifier record covers is rendered unverified rather than
  dropped, so a run whose verifier delivered nothing never reads as clean — [in]
- 2026-09-16 — Slice 3: the headless run is assembled by `tools/audit_headless.py` from
  the skill and the agent files rather than written out in YAML, so CI and a session
  cannot drift and the assembly is unit-tested — [in]
- 2026-09-16 — The verifier's guard must not come from the tree under audit: a pull
  request could otherwise ship a guard that permits everything to the one agent that
  executes. The launcher refuses to start without `--guard`, and CI takes the guard
  from the base branch — [in]
- 2026-09-16 — Headless grants are read from the skill's own `allowed-tools`, with the
  report-directory Write grant pinned to the run's directory, rather than a second list
  in the workflow — [in]
- 2026-09-16 — `--json-schema` and a committed result schema from the architecture
  record's sketch — [dropped] the run's own artifacts, `findings.jsonl` and the revision
  stamp, already are the source of truth, and a second schema would be a second place
  for the contract to drift
- 2026-09-16 — The CI job runs the CLI directly rather than through
  `anthropics/claude-code-action`: `--agents` takes only literal JSON, which an argv
  element carries cleanly and a YAML argument string does not — [in]
- 2026-09-16 — The audit workflow is invoked, never automatic: manual dispatch, or the
  `audit` label on a pull request, and never on a fork, where GitHub withholds the
  secret the run needs — [in]
- 2026-09-16 — Whether `--bare` with inline `--agents` honours `isolation: worktree` is
  undocumented; the first authenticated CI run is the check, and the fallback the
  architecture record names (one `claude -p` per specialist) still stands — [open]
