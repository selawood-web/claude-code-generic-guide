# Architecture — the `/ccgg-audit` skill (F002)

- **Date:** 2026-09-16
- **Status:** decided
- **Type:** architecture
- **Deciders:** repository owner
- **Supersedes / superseded by:** —
- **Source feature:** [F002 — Audit skill](../features/F002-audit-skill.md)
- **Source research:** [Testing agent-built systems](../knowledge-base/research/testing-agent-built-systems.md)

## Context

F002 is `ready`: one command runs a read-only, three-layer audit of a CCGG-equipped
repository with parallel specialists, a verifier that reproduces every finding, and a
report whose deterministic findings become validator checks. This record fixes *how*:
the components, their boundaries, the data that flows between them, and what is built
first. Every product fact below was checked against the official Claude Code reference
today; two of them changed the design before it was drawn (see *Research findings*).

Reversibility: mostly a two-way door. Subagent briefs, the findings schema, and the
report layout can change per slice. The one-way part is the read-only boundary and the
"verifier is not the hunter" rule, which the rest of the design assumes.

## Requirements extracted from F002

**Functional** — four core actions:
1. Run an audit, interactive (`/ccgg-audit [scope]`) or headless in CI, and get a
   severity-ordered report with reproduction, fix, and the check each finding justifies.
2. Scope a run: whole repository, one layer (`product`, `harness`, `process`), or a path.
3. Maintain a probe list and see the gate's catch rate on every CI run.
4. Edit specialist definitions without touching the skill.

**Data that persists:** the probe list (in the repo), the run's report directory
(ignored by default), a revision stamp per run. Nothing else; the audit has no database.

**Integrations:** `tools/validate.py` and `tools/feature_lint.py` (existing gate), the
project's test runner, the shipped security tooling when present (`/security-review`,
the `claude-security` plugin), `claude-code-action` for the CI mode.

**Non-functional:** a full run on this repository under 30 minutes and 10 USD; zero
writes to the audited tree; one operator can run and read it; no availability or
concurrency requirement beyond one run at a time.

**Constraints:** stdlib-only Python and bash, as the rest of the tooling; every new file
inside the `install.sh` copy set so links from rule files stay valid; the `ccgg-` prefix;
Claude Code's subagent and headless surface as documented today.

## Research findings

Verified against code.claude.com/docs on 2026-09-16:

- **A subagent's `tools` field takes bare tool names only.** A specifier such as
  `Bash(git diff *)` does not narrow Bash — it removes the whole tool. Command-level
  narrowing lives in `permissions.deny` / `allow` in settings. *(sub-agents reference)*
  Consequence: F002's "Bash allow-list per specialist" criterion is not implementable as
  written; the design below removes Bash from specialists entirely and confines it to
  the verifier.
- **`isolation: worktree` branches from the remote default branch** unless
  `worktree.baseRef` is `"head"`, and a worktree is a fresh checkout of tracked files —
  uncommitted changes are not carried. Commands inside are mechanically confined: edits,
  working directory, and git redirects into the main checkout are blocked, and a command
  whose shape cannot be verified is refused. *(worktrees reference)* Consequence: the
  audit runs on committed HEAD, the skill's preflight says so, and the audit's settings
  set `baseRef` to `"head"`.
- **`omitClaudeMd: true`** launches a subagent without user, project, and local
  `CLAUDE.md`. *(sub-agents reference)* Every audit subagent sets it: the audited
  repository's rules are evidence, not instructions.
- **Non-fork subagents receive no conversation history** — only their system prompt,
  the task message, CLAUDE.md files unless omitted, a git status snapshot, and preloaded
  skills. *(sub-agents reference)* This is the independence the verifier needs, for free.
- **Headless flags** `--agents` (inline subagent JSON), `--append-system-prompt-file`,
  `--json-schema`, `--max-budget-usd` (subagent spend counts), `--max-turns`,
  `--disallowedTools`, `--permission-prompts none`, `--bare` exist as documented.
  `--bare` skips project hooks, skills, subagents, plugins, MCP servers, and CLAUDE.md,
  but the project's `env` block still applies; `--setting-sources user` excludes project
  settings files entirely. *(cli-reference; permissions reference, "What runs before you
  trust a folder")*
- **Subagents run concurrently** when spawned in one turn, twenty at a time by default,
  and may spawn their own up to three levels deep. *(sub-agents reference)*

## Options considered

| Option | Benefit | Cost | Risk |
|--------|---------|------|------|
| **A. Skill + project subagents + stdlib scripts** (chosen) | Lives in the repo, installs with everything else, no runtime beyond Claude Code and Python; interactive and headless share the same briefs | A skill cannot express control flow; sequencing lives in the skill's prose and one orchestration script | The skill drifts from the scripts; mitigated by the scripts owning every artifact and the skill owning only the order |
| B. Dynamic workflow (the `Workflow` runtime the Claude Security plugin uses) | Deterministic orchestration, phases, resume | Needs a paid plan and dynamic workflows enabled; not available to every wired project; a second orchestration language to maintain | Excludes the projects most in need of the audit; revisit when the runtime is generally available |
| C. Agent SDK program (`claude-agent-sdk`) | Typed findings, tool-level hooks enforcing read-only, testable in Python | A second runtime and dependency in a repo that ships stdlib only; not invocable as `/ccgg-audit` from a session | Over-built for slice 1; the natural slice 3 if the CI mode outgrows a shell job |
| D. One big auditor prompt, no subagents | Simplest possible | One context for everything; the hunter grades itself; no parallelism; cost scales with repo size in one window | Exactly the false-consensus failure the research warns about |
| Status quo — run the method by hand | Nothing to build | Found four real defects once and will not be run again unprompted | The defects recur silently |

Rejected early: a GitHub App or hosted service — the charter forbids external hand-offs
and credentials in the repo; `claude-code-action` in the project's own CI is the bounded
form.

## Design

### Component diagram

```
 /ccgg-audit [scope]                     CI: claude -p (see "Headless mode")
        │                                       │
        ▼                                       ▼
 ┌──────────────────────────────────────────────────────────┐
 │  ORCHESTRATOR  (the skill's turn; small model; no Bash   │
 │  beyond the two scripts; holds summaries only)           │
 └──┬──────────────┬───────────────────────────┬────────────┘
    │ 1            │ 3 (parallel, one turn)    │ 5
    ▼              ▼                           ▼
 ┌────────────┐  ┌────────────────────────┐  ┌────────────────┐
 │ tools/     │  │ .claude/agents/        │  │ .claude/agents/│
 │ audit_facts│  │  audit-harness.md      │  │  audit-verifier│
 │ .py        │  │  audit-security.md     │  │  .md           │
 │ + audit_   │  │  audit-tests.md        │  │                │
 │ probes.py  │  │  audit-spec.md         │  │ tools: Read,   │
 │            │  │  audit-consistency.md  │  │  Glob, Grep,   │
 │ stdlib,    │  │  audit-redteam.md      │  │  Bash          │
 │ read-only, │  │                        │  │ disallowed:    │
 │ writes to  │  │ tools: Read,Glob,Grep  │  │  Write, Edit,  │
 │ report dir │  │ omitClaudeMd: true     │  │  NotebookEdit  │
 │ only       │  │ maxTurns, model: small │  │ isolation:     │
 └─────┬──────┘  └───────────┬────────────┘  │  worktree      │
       │ 2 facts.json        │ 4 candidates   │ omitClaudeMd   │
       │   inventory.json    │   /<name>.json │ model: large   │
       └──────────┬──────────┘                └───────┬────────┘
                  ▼                                   │ 6 findings.jsonl
          CCGG-AUDIT-<stamp>/  ◄──────────────────────┘
          ├─ .gitignore   ├─ facts.json  ├─ candidates/*.json
          ├─ inventory.json ├─ probes.json ├─ findings.jsonl
          ├─ REPORT.md    └─ REVISION-<sha>.json
```

Numbered flow: (1) the orchestrator runs the two scripts; (2) they write the
deterministic artifacts; (3) the orchestrator spawns every specialist in one turn, each
with the scope and the *path* to `facts.json`, never its contents; (4) each returns a
bounded candidate list in the schema; (5) the orchestrator spawns one verifier per
candidate batch; (6) the verifier writes verified findings, and the orchestrator
renders `REPORT.md` from `findings.jsonl` with a stdlib script, not by prose.

### Components and decisions

**1. `tools/audit_facts.py` — the deterministic stage.** Stdlib only, like the validator.
Runs, in order, and records each as a fact with evidence: the validator and feature
linter; the project's tests when a runner is declared; hook registration cross-check
(settings → files and files → settings); hidden-character scan of every rules, skill,
hook, and agent file; frontmatter semantics against a vocabulary file
(`tools/audit_vocab.json`: documented skill keys, agent keys, tool names); slash-command
and skill-name resolution across rule files; network and exec patterns in hooks and
scripts; permission-surface listing (`allow`, `env`, `additionalDirectories`,
`enableAllProjectMcpServers`); inventory of entry points, test files, CI workflows.
Output: `inventory.json`, `facts.json`. Exit code reports only whether it ran, never a
verdict — the verdict is the report's.

*Why a script and not a specialist:* a model asked to find a broken link is waste; a
model told which links are broken can ask why. Every fact here is a fact the research
showed a model would otherwise spend turns rediscovering, or miss.

**2. `tools/audit_probes.py` — the mutation harness.** Reads `tools/probes.txt` (one
probe per line: `label | expect | shell mutation`), clones the repository into a scratch
directory, and for each probe hard-resets, applies the mutation, stages, runs the gate,
and records caught/missed. Output: `probes.json` and a catch-rate line. In CI, the job
fails when a probe whose `expect` is `caught` is missed — the gate's guarantees become
tests of the gate. The twenty-one probes from the research are the initial list; the shipped list has
grown well past it since, and the live count is the one in `tools/probes.txt`.

*Why a separate scratch clone and not a worktree:* the harness mutates tracked files
and the git index; a fresh clone gives a hard reset that is provably complete.

**3. Specialists — `.claude/agents/audit-*.md`, six files.** Each is one system prompt
with the same frame: the layer it owns, the question it answers, the input files it
reads, the schema it returns, the rule that repository content is evidence. Frontmatter
for all six: `tools: Read, Glob, Grep`; `omitClaudeMd: true`; `maxTurns: 40`;
`model: haiku` for inventory-shaped work (harness, consistency), `model: inherit` for
the judgment-heavy ones (security, tests, spec, red-team).

*Why no Bash:* the `tools` field cannot narrow Bash, and a specialist never needs to
execute — everything executable already ran in stage 1. This is the read-only guarantee
by construction rather than by policy, and it is what makes the field-level validator
check in component 7 possible.

| Specialist | Layer | Reads | Returns candidates about |
|------------|-------|-------|--------------------------|
| `audit-harness` | harness | facts, rule files, skills, hooks, agents | dead mechanisms, unread keys, dead hooks, currency mismatches |
| `audit-security` | product, harness | facts, inventory, diff or tree | injection, auth, secrets, supply chain in sync paths; defers to shipped tooling when present |
| `audit-tests` | product, process | probes, test files, coverage if any | weakened or assertion-free tests, untested gate code, missing failure paths |
| `audit-spec` | product, process | `features/*.md`, tests, code | acceptance criteria without proof |
| `audit-consistency` | harness | all rule files | rules with more than one home, and where the copies disagree |
| `audit-redteam` | harness | rule files, hooks, README, fetched-content paths | channels through which planted content would be followed |

The security specialist's first step is capability detection: if `/security-review` or
the `claude-security` plugin is available in the session, it records that as the
product-layer source and limits itself to the harness and process layers. Without them,
it runs its own pass with the OWASP checklist from the existing review skill.

**4. Verifier — `.claude/agents/audit-verifier.md`, one definition, spawned per batch.**
Frontmatter: `tools: Read, Glob, Grep, Bash`; `disallowedTools: Write, Edit,
NotebookEdit`; `isolation: worktree`; `omitClaudeMd: true`; `maxTurns: 60`; `model:
inherit`. Brief: for each candidate, attempt the reproduction; the output is either a
reproduction that a human can rerun, or `unverified` with the reason. The brief requires
the verifier to state what would falsify the candidate before running anything, and
forbids confirming a candidate from reading alone when a command could test it.

*Why Bash here and nowhere else:* reproduction needs execution — running the validator
against a mutated copy, running a test, tracing a hook. The worktree confines every
command mechanically; `disallowedTools` removes the write tools; the audit's own
settings deny `Bash(git push *)`, `Bash(rm *)`, `Bash(curl *)`, `Bash(wget *)` as a
second layer.

*Why `baseRef: "head"`:* the default worktree base is the remote default branch, which
would make the verifier reproduce findings against `master` while the specialists read
the feature branch. The audit's settings fragment sets `worktree.baseRef` to `"head"`.

**5. The skill — `.claude/skills/ccgg-audit/SKILL.md`.** Owns the order and nothing
else: preflight (git clean or say what is uncommitted; scope parsed; report directory
created with its `.gitignore`), stage 1, stage 3 in one turn, stage 5, render, then the
close-out: for every verified finding with `becomes_check` set, an entry in the report's
"proposed checks" section. `disable-model-invocation: true` — an audit is invoked, never
auto-triggered. `allowed-tools: Bash(python3 tools/audit_facts.py *) Bash(python3
tools/audit_probes.py *) Bash(python3 tools/audit_report.py *)`, the three commands the
orchestrator runs, and nothing else.

**6. `tools/audit_report.py` — the renderer.** Reads `findings.jsonl`, validates every
record against the schema (a stdlib check, no `jsonschema` dependency), sorts by
severity then confidence, and writes `REPORT.md`. An `unverified` record with severity
`blocker` is a schema violation and fails the render — the guarantee in F002 lives in
code, not in a brief.

**7. Validator and installer changes.** `tools/validate.py` gains one check: every
`.claude/agents/*.md` has frontmatter with `name` and `description`; any `audit-*` agent
except the verifier has `tools` equal to exactly `Read, Glob, Grep` and
`omitClaudeMd: true`; the verifier has `isolation: worktree` and `disallowedTools`
covering the three write tools. `install.sh` and `update.sh` gain `.claude/agents/` and
the three `tools/audit_*.py` files plus `probes.txt` and `audit_vocab.json` as
CCGG-owned paths; `catalog.py --write` picks the skill up from its frontmatter.

### Data model

```
inventory.json   { repo, head, scope, stack[], entry_points[], test_runner, rule_files[],
                   skills[], hooks[], agents[], ci_workflows[], permission_surface{} }
facts.json       { generated_at, facts: [ { id, kind, status: ok|finding|skipped,
                   location, evidence, detail } ] }
probes.json      { total, caught, missed, probes: [ { label, expect, result } ] }
candidates/<specialist>.json
                 [ { id, layer, class, severity, location, claim, evidence, hypothesis,
                     falsifier } ]                           # what would disprove it
findings.jsonl   one object per line, the F002 schema:
                 { id, layer, class, severity, confidence: verified|unverified, location,
                   claim, evidence, reproduction, fix, becomes_check, source_candidate }
REVISION-<sha>.json
                 { head, dirty: bool, scope, models{}, cost_usd, duration_s,
                   specialists_run[], verifier_batches }
```

Source of truth for a run is `findings.jsonl`; `REPORT.md` is a view. Source of truth for
the gate's guarantees is `tools/probes.txt`; `probes.json` is a measurement.

### Headless mode (CI)

One job in the wired project's workflow, after the validator:

```bash
claude -p --bare --setting-sources user \
  --agents "$(python3 tools/audit_agents_json.py)" \
  --append-system-prompt-file .claude/skills/ccgg-audit/orchestrator.md \
  --disallowedTools "Write" "Edit" "NotebookEdit" "WebFetch" "WebSearch" \
  --permission-prompts none --max-turns 80 --max-budget-usd 10 \
  --output-format json --json-schema "$(cat tools/audit_result.schema.json)" \
  "Audit this repository at HEAD, scope: $AUDIT_SCOPE"
```

`--bare` plus `--setting-sources user` means nothing in the audited checkout configures
the run: not its hooks, not its `env`, not its skills or agents. The agents therefore
arrive inline, generated from the same `.claude/agents/audit-*.md` files by a small
script, so interactive and headless runs share one set of briefs. The skill body itself
is passed as the appended system prompt. The job posts `REPORT.md` as a pull-request
comment through `claude-code-action`'s inline-comment tool and never pushes.

Open implementation check, first CI run: confirm that `--bare` with inline `--agents`
still honours `isolation: worktree` and `omitClaudeMd` from the JSON definitions. If
not, the fallback is a second `claude -p` per specialist with `--disallowedTools Bash`,
which keeps the guarantee at the cost of parallelism.

### Trade-offs

| Decision | Benefit | Cost | Risk |
|----------|---------|------|------|
| Specialists without Bash | Read-only by construction; validator can enforce it | Specialists cannot run a quick check; they must ask the verifier | A specialist reasons from stale facts if stage 1 is skipped — the skill never skips it |
| One verifier definition, many batches | Independence per batch; parallel verification | More subagent spawns per run; budget must cover them | Budget cap hit mid-verification leaves findings unverified — they are reported as such, never dropped silently |
| Scratch clone for probes, worktree for verifier | Each mechanism fits its job | Two isolation mechanisms to explain | Confusion in the skill text; one sentence per mechanism in the skill |
| Report directory ignored by default | No accidental commits; matches the shipped scanner | Audit trail needs a deliberate `git add -f` | Owners lose history; the revision stamp makes any kept report attributable |
| Inline `--agents` in CI generated from the same files | One set of briefs | One more script | Field support in inline JSON differs from file frontmatter — checked on the first CI run |

## Critic pass

Run against the seven dimensions in the architecture critic.

- 🟡 **Failure mode — budget exhaustion during verification.** With
  `--max-budget-usd`, spawning stops and running subagents are killed. The renderer
  therefore treats a candidate with no verifier record as `unverified` and the report
  names the cut. Accepted with that mitigation.
- 🟡 **Security boundary — interactive mode trusts the folder already.** In a session,
  the audited project's hooks and `env` ran at session start before `/ccgg-audit` was
  typed; the audit cannot undo that. The boundary the skill *can* hold is the read-only
  one, and the headless mode is the one to use on a checkout nobody trusts. Stated in
  the skill and in F002's criteria.
- 🔵 **Simplicity — six specialists is the ceiling, not the floor.** Slice 1 ships two.
  A specialist that produces no verified finding in three consecutive runs on this
  repository is merged into a neighbour.
- 🔵 **Data — candidates are model output.** The `falsifier` field is what keeps them
  honest: a candidate without one is rejected by the verifier before any work.
- 💡 **Operability.** Debugging a run means reading the report directory; every
  artifact is plain JSON or markdown, and the revision stamp ties it to a commit and a
  cost. Rollback is deleting the directory. The whole audit can be removed by deleting
  seven files and one validator check, so the migration path away from it is trivial.
- 💡 **Single point of failure.** The orchestrator's turn. If it dies, the report
  directory holds whatever stages completed, and re-running the skill resumes from
  the artifacts present (the skill checks for `facts.json` before re-running stage 1).

Checklist: simplest design that meets the requirements — yes, given that option D fails
the verifier-independence requirement; every external dependency analysed — Claude Code
surfaces are listed with their references and the shipped security tooling is optional;
data model matches access — one directory per run, read sequentially; recovery plan —
re-run resumes from artifacts; one operator can run it — yes; security boundaries drawn
— above; expected scale — one repository, one run at a time.

## Decision & rationale

Option A. It is the only option that installs with the rest of CCGG, runs without a paid
runtime, and lets a validator check enforce the read-only boundary at the definition
level. Options B and C are the migration paths if orchestration in prose proves too
fragile (B) or the CI mode needs typed, tested control flow (C).

## What to build first — slice 1

Deployable on this repository's CI from the first pull request:

1. `tools/audit_probes.py` + `tools/probes.txt` with the twenty-one probes, wired into
   `.github/workflows/validate.yml` as a job that prints the catch rate and fails on a
   missed `expect: caught`. All twenty-one start as `expect: missed` or `caught` per the
   research table, so the first run is green and the table becomes a living contract.
   (As planned on 2026-09-16. The list has grown with every check that landed since;
   `tools/probes.txt` is the count, and no number here is a current claim.)
2. `tools/audit_facts.py` with the hook cross-check, hidden-character scan, frontmatter
   vocabulary, and command resolution — the four checks the research found missing.
3. `.claude/agents/audit-harness.md` and `audit-verifier.md`, the validator check for
   agent frontmatter, and `install.sh` / `update.sh` learning the new paths.
4. `.claude/skills/ccgg-audit/SKILL.md` running stages 1, 3 (harness only), 5, and the
   renderer. Acceptance test: on the commit before findings 2 and 3 of the research are
   fixed, the run reports both, verified, with reproductions.

Slice 2 adds the other five specialists and the red-team probe set. Slice 3 adds the
headless CI job and the pull-request comment.

## Consequences & accepted risks

- The repository grows a second executable surface (`.claude/agents/`) that the
  installer, updater, and validator must all know about; forgetting one is exactly the
  documented-but-dead class, so the validator check lands in slice 1, not later.
- Findings depend on model judgment and are nondeterministic run to run; the revision
  stamp and the probe catch rate are the two numbers that are not.
- Cost is bounded per run but not per month; the skill prints the run's cost at the end
  so the owner sees it every time.

## Revisit trigger

Any of: the first full run on this repository exceeds 10 USD or 30 minutes; the inline
`--agents` path fails to honour worktree isolation on the first CI run; dynamic
workflows become available on every plan (re-open option B); a specialist produces no
verified finding in three consecutive runs.

## Corrections

Recorded while building slice 3, against the headless sketch above:

- *Headless command.* `--agents` accepts a literal JSON string only — no file
  reference — so the run is launched by `tools/audit_headless.py`, which passes the
  JSON as one argument. The sketch's `--json-schema` and `tools/audit_result.schema.json`
  are dropped: `findings.jsonl` and the revision stamp already are the source of truth.
- *What excludes the tree.* `--bare` is the documented flag for skipping a project's
  hooks, skills, agents, MCP servers and memory; the exclusion semantics of
  `--setting-sources user` are not documented. The run passes both and leans on `--bare`.
  **Corrected again after the first authenticated run** (see the next section): `--bare`
  also caps the built-in tool set, `--setting-sources user` carries the exclusion on its
  own, and the run no longer passes `--bare`.
- *The guard.* The sketch did not say where the verifier's guard hook comes from in a
  headless run. Taking it from the audited tree would hand the one executing agent a
  guard written by whoever wrote the tree, so the launcher requires a path the caller
  controls and CI takes it from the base branch.
- *Authentication.* In bare mode Claude Code reads `ANTHROPIC_API_KEY` and never an
  OAuth credential or the keychain, so the workflow requires that secret and skips the
  model run without it. **Corrected:** the run is no longer bare, so a local operator's
  own credential may be used; CI has none, so the secret is still what the job requires.

## Corrections — measured against the installed CLI (2.1.273), first run with a model

The first authenticated run spent 1.38 USD over 42 turns, spawned zero specialists, and
reported that it had no `Agent` tool. A one-turn probe asked the run to name its tools;
the answer was `Bash` and `Read`. What the flags actually do, each line reproduced by
starting a run against a planted tree and reading its `system/init` event and transcript:

- **`--bare` caps the built-in tool set to `Bash, Edit, Read`.** `--tools` can narrow
  that set but cannot widen it, and `--tools default` in bare mode returns the same
  three. `--bare` *does* register inline `--agents`, so the run loads seven briefs and
  holds no tool that can invoke one. The help text does not say this.
- **`--setting-sources user` excludes the tree by itself**, with the full tool set
  intact: against a planted `.claude/settings.json` hook, `CLAUDE.md`, `.claude/agents/`
  entry and `.claude/skills/` entry, the hook did not fire, the rules never reached the
  prompt, and neither the agent nor the skill was listed. `--setting-sources ''` behaves
  identically; `user` keeps the operator's own configuration, which is theirs to trust.
- **`--allowedTools` only pre-approves; `--tools` names what exists.** The run now names
  its built-in set from the skill's own grants, so the two cannot drift.
- **`Agent` and `Task` are aliases in the permission flags** — denying `Agent` removes
  `Task` — but `--tools` accepts only `Task`.
- **`--add-dir <tree>` re-enables discovery of that tree's agents.** The audited tree is
  read from the working directory, never added.

Recorded after the first full audit run, which verified two statements above against
what was built:

- *Component 4, second layer.* "The audit's own settings deny `Bash(git push *)`,
  `Bash(rm *)`, `Bash(curl *)`, `Bash(wget *)`" — no such settings exist. The second
  layer is the verifier's PreToolUse guard hook, `.claude/hooks/audit-verifier-guard.sh`,
  an allow-list of read-only command forms tested by `tools/test_verifier_guard.py`.
- *Component 5, grants.* "The three commands the orchestrator runs, and nothing else" —
  the skill grants four scripts (`audit_facts`, `audit_probes`, `audit_redteam`,
  `audit_report`), `Write` scoped to `CCGG-AUDIT-*/**` for the report directory, and
  `Read`, `Glob`, `Grep`, `Agent`. The validator pins that exact set.

## Outcome

_Empty at creation._
