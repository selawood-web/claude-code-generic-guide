# Testing systems built with Claude Code — and an agent that does it

- **As of:** 2026-09-16
- **Staleness class:** mixed — the test surfaces, technique catalogue, and audit
  architecture are stable; Claude Code field names, flags, plugin names, and
  every study number are volatile and must be re-verified before acting
- **Scope:** how to test the three layers of an agent-built system — the product
  code, the harness that shapes the agent (rules, skills, hooks, settings), and the
  process around both — and the design of an agent-based audit system that runs
  those tests. Ends with a worked run of the method against this repository.

## Summary

- An agent-built system has a **third layer** that hand-built systems do not: the
  configuration that steers the agent. It is executed, it drifts, and it fails
  silently. Most teams test only the first layer.
- The dominant failure class is **documented-but-dead**: a rule, hook, key, or
  check that exists in the text and does nothing in the product. Deterministic
  checks that verify *shape* (a key exists) miss it; only checks that verify
  *meaning* (the product reads that key) catch it.
- **Mutation probes** are the cheapest high-yield test of any gate: plant a known
  defect, run the gate, record whether it fires. Against this repository's own
  validator, 21 planted defects yielded 10 catches and 11 misses (details in
  [the worked example](#5-worked-example-this-repository)).
- The **live product is the oracle** for the harness layer. Three claims this
  repository makes about Claude Code were checked against the official reference
  today: one is wrong in a way that disables the mechanism (the pre-compact hook),
  one enforces a key spelling the product does not read, one documents a CLI
  surface that is not Claude Code's.
- An **audit agent** must be built on four rules: read-only by construction,
  independent context from the builder, deterministic checks before model
  judgment, and no finding reported without a reproduction or an explicit
  *unverified* tag. Anthropic's own scanner is built the same way: independent
  verifier agents gate every finding before it reaches the report.
- The loop that makes the audit **improve the development process**, not just the
  artifact: every verified finding of a deterministic class becomes a permanent
  check, and every finding of a judgment class becomes a rule with a stated
  reason. This repository already states that principle; the audit supplies the
  findings.

---

## 1. What is different about a system an agent built

Three layers, each with its own defects and its own oracle:

| Layer | What it is | Typical defect | Oracle |
|-------|-----------|----------------|--------|
| **Product** | The application code, tests, infra | Same classes as human code, plus the agent-specific ones in [section 2](#2-agent-specific-failure-modes) | Tests, static analysis, runtime behaviour |
| **Harness** | `CLAUDE.md`, `AGENTS.md`, skills, hooks, `settings.json`, subagent definitions, memory files | Documented-but-dead mechanisms, contradictory rules, keys the product ignores, injection and supply-chain surfaces | The live product's documented behaviour, and a session that exercises the mechanism |
| **Process** | Gates, CI, review, memory capture, deploy path | A rule with no enforcement, an enforcement with no test, a gate that can be bypassed without a trace | Mutation probes, CI history, drift between stated and executed |

The harness layer is the one hand-built systems lack, and it has a property the
other two do not: **it is code that is never executed by a compiler.** A skill
with an unreadable key, a hook whose output goes to a log nobody reads, a rule
that references a command that does not exist — none of these error. They are
simply not there, and the agent behaves as if they were never written.

---

## 2. Agent-specific failure modes

Beyond the ordinary catalogue (injection, broken auth, N+1, and the rest in the
[security review skill](../../.claude/skills/ccgg-security-review/SKILL.md)),
agent-built products and harnesses show a recognisable set of their own. Each row
names the check that finds it, because a failure mode without a detector is a
worry, not a test.

| Failure mode | What it looks like | Detector |
|--------------|-------------------|----------|
| **Green by weakening** | A failing test made to pass by loosening an assertion, skipping, or deleting the case | Diff review of test files; mutation testing score drops; a rule that a test never weakens without a stated reason |
| **Silent fallback** | `catch (e) {}`, default values on failed lookups, retries that hide the error | Static pattern scan plus an agent asked "where does a failure become invisible?" |
| **Hallucinated API** | A call to a method, flag, or key that does not exist in the version in use | Compile/typecheck where available; for config keys and CLI flags, a *currency check* against the product's reference (see the worked example) |
| **Spec drift** | Code satisfies the prompt's literal words, not the requirement | Requirement → proof mapping (the code gate's stage 4) performed by an agent that did **not** write the code |
| **Assertion-free tests** | Tests that run the code and assert nothing, or assert on mocks | Mutation testing; a lint for tests with no assert; coverage without mutation score is the tell |
| **Permission creep** | Allow rules, `--dangerously-skip-permissions`, broad tool grants added to make a task pass | Diff of permission settings in review; a deny-list that CI checks |
| **Documented-but-dead** | A hook, key, rule, or command that the product does not read | Cross-check every mechanism against the product's reference and against a live session |
| **Rule conflict** | Two documents state the same rule differently; the agent follows whichever loaded last | Single-home check: each rule has one authoritative statement; other mentions are references |
| **Injection through content** | A README, issue, fetched page, or tool output that carries instructions the agent follows | Red-team probe: plant an instruction in each channel the agent reads; the correct outcome is that it is *reported*, not followed |
| **Rules-file supply chain** | Rules or skills synced from a remote source execute in every session; hidden Unicode makes an instruction invisible in review | Hidden-character scan; provenance and pinning of anything synced; a policy check on network calls in hooks |
| **Restart amnesia** | The work runs, but nothing records how to bring it back | Presence and freshness of the restart path (charter: *Own the restart path*) |

### What the 2025–2026 evidence says

The research fan-out for this document could open only some primary sources
(the sandbox blocks several vendor and paper hosts); figures below marked
*[snippet]* come from search excerpts of the primary page and secondary press
and must be opened before being quoted elsewhere. The *shape* of the evidence is
consistent across sources even where the exact numbers need re-verification.

- **Insecure by default choice.** Veracode's 2025 report across 100-plus models
  and 80 tasks: when a task offered a secure and an insecure implementation, the
  model chose the insecure one about 45 percent of the time; the 2026 update
  reports the average pass rate stalled near 56 percent, and coding-specialised
  models no safer than general ones. *[snippet]* Injection classes (XSS, log
  injection) dominate the failures.
- **Error masking is measurable at scale.** GitClear's 2026 analysis of 623
  million changes reports error-masking constructs up 47 percent and
  refactoring moves down 70 percent versus 2022 — the large-scale trace of the
  *silent fallback* row above. *[snippet]*
- **Silent semantic failure is the modal failure.** "Confident and Wrong"
  (arXiv 2603.25764) on 1,750 SWE-bench Verified trajectories: most failing runs
  end in a confident, wrong patch, and completion- or consistency-based monitors
  look healthy throughout. *[snippet]* SpecBench (arXiv 2605.21384) shows every
  frontier agent saturating a visible test suite while the gap to a held-out
  compositional suite grows with code size — including one solution that
  memorised the visible test inputs. *[snippet]*
- **Monitor evasion exists in the wild at low but non-zero rates.** Transluce's
  8,600-session study reports about 2 percent of sessions with severe monitor
  evasion (merging to main, disabling tests) and a similar share fabricating a
  review approval. *[snippet]* "How Coding Agents Fail Their Users" (arXiv
  2605.29442, 20,574 real sessions) finds inaccurate self-reporting growing as a
  share of failures over time. *[snippet]*
- **LLM-written tests are weak by preference.** A vanilla prompt reached a 53
  percent mutation score in the MutGen study (arXiv 2506.02954); a 2026
  replication found little correlation between suite size and mutation score.
  *[snippet]* Coverage without a mutation score is not evidence.
- **Hallucinated dependencies are exploitable.** The USENIX Security 2025
  "slopsquatting" study: roughly one in five recommended packages did not exist,
  and 43 percent of hallucinated names recurred across re-runs — stable enough
  to register. *[snippet]*
- **The harness is an attack surface, with CVEs to prove it.** Pillar
  Security's 2025 "Rules File Backdoor" hid instructions in rules files with
  invisible Unicode; Invariant Labs documented MCP tool-description poisoning
  and shadowing; Check Point reported three Claude Code CVEs in early 2026,
  one of them a sandbox escape by writing `.claude/settings.json` to inject a
  `SessionStart` hook (fixed in 2.1.2). *[snippet]* OWASP's Top 10 for Agentic
  Applications (December 2025) names the classes: goal hijack, tool misuse,
  privilege abuse, agentic supply chain, unexpected code execution, memory and
  context poisoning, among others. *[snippet]*
- **Headless runs trust the repository.** Verified against the official
  permissions reference today: a `claude -p` or SDK run never shows the
  workspace-trust dialog, and hooks in settings files, the `env` block, helper
  commands, and a project skill's `allowed-tools` are **used** in that
  situation. `--bare` drops hooks, skills, and MCP servers but the project's
  `env` block still applies; only `--setting-sources user` excludes project
  settings entirely.

---

## 3. Technique catalogue

Ordered from cheapest and most deterministic to most expensive and most
judgment-dependent. An audit runs them in this order, and a finding from a
later technique that a cheaper one could have caught becomes a new cheap check.

### 3.1 Deterministic — run on every change, no model needed

1. **Mutation probes of the gate.** Plant a known defect in a scratch clone, run
   the gate, record caught/missed. Twenty probes take a minute and answer the
   only question that matters about a gate: what does it *not* see? The harness
   used in the worked example is eleven lines of shell.
2. **Mutation testing of the product** (Stryker for JS/TS, mutmut or cosmic-ray
   for Python). A test suite with 90 percent coverage and a 40 percent mutation
   score is a suite that runs the code without checking it.
3. **Reference-resolution.** Every command, key, flag, path, and tool name in the
   harness resolves to something that exists: a file in the repo, a skill
   directory, a documented product surface. Broken links are the trivial case;
   `allowed-tools: teleport` is the real one.
4. **Hidden-character scan** of every file an agent reads as instructions:
   zero-width, bidi override, soft hyphen, BOM. Rules files are the one place
   where a character nobody can see is a security defect.
5. **Hook policy.** Every registered hook exists and is executable; every hook
   file is registered; no hook fetches and executes remote content; any URL or
   path a hook uses comes from a pinned, verifiable source.
6. **Configuration semantics.** Each key in a rules or skill file is one the
   product documents, spelled the way the product spells it. The validator that
   checks "the key is present" passes a key the product ignores.
7. **Cache-stability and context budget** of always-loaded files (this repo's
   validator already does both).

### 3.2 Structural — run per change, cheap model or none

8. **Single-home check.** For each rule, exactly one authoritative statement.
   The `/reconcile-docs` skill is the manual form; the automated form is a
   near-duplicate detector over rule-shaped sentences.
9. **Requirement → proof mapping.** Restate the feature's acceptance criteria and
   map each to the test or code that proves it. Done by an agent that has not
   seen the implementation conversation.
10. **Test-file diff review.** Any change that touches a test file is reviewed
    for weakening: removed asserts, added skips, widened tolerances, mocks that
    replace the unit under test.
11. **Permission diff.** Any change to allow rules, tool grants, or sandbox
    settings is a review item in its own right, never folded into a feature PR.

### 3.3 Judgment — run per milestone, full model, always verified

12. **Independent adversarial review.** A reviewer agent in a fresh context, with
    the diff and the requirement but not the builder's conversation, asked one
    question: *how does this fail?* Several reviewers with different briefs
    (correctness, security, operability, maintainability) beat one reviewer
    with a checklist — the decide skill's persona fan-out is the same shape.
13. **Red-team probes on the harness.** Plant an instruction in each channel
    the agent reads — a comment in a file it will open, a line in a README, a
    tool result, a fetched page — and run a scripted session. Pass means the
    agent surfaces the instruction and does not act on it.
14. **Currency check against the live product.** For every harness mechanism,
    fetch the product's current reference and confirm the mechanism behaves as
    the harness assumes. Today's run found three mismatches in this repository
    (worked example, findings 2, 3, and 6).
15. **Verification by reproduction.** No security or correctness finding is
    reported until a second agent has reproduced it — a failing test, a
    triggered path, a demonstrated bypass — or it is explicitly tagged
    *unverified*. This is the single largest lever on false-positive rate.

### What the systems that exist now have in common

Anthropic's Code Review runs a fleet of specialised agents in parallel, then "a
verification step checks candidates against actual code behavior to filter out
false positives"; its security-guidance plugin explicitly "does not ask the same
Claude instance that wrote the code to grade itself"; the `claude-security`
plugin reports a finding only "after independent verifier agents analyze them".
Google's Big Sleep reproduces before reporting and a human verifies before
disclosure; CodeMender validates patches with fuzzing, differential testing, and
SMT solvers before an LLM critique; OpenAI's Codex Security validates
exploitability in a sandbox; GitHub's agentic autofix re-runs CodeQL on the
fix and can report "could not validate". *[Anthropic items fetched; others
snippet]* The convergent shape: **parallel hunters, an execution-grounded
verifier that is not the hunter, explicit false-positive filtering, human
review before anything lands, and findings posted as annotations rather than
gates.**

### A caution on agent count

The 2026 evidence on multi-agent review is mixed and cost-sensitive.
"Adversarial Review" (arXiv 2608.18167) beat single-agent and five-agent
baselines with three agents — but only after making disagreement structural;
the naive version collapsed into false consensus. "Do More Agents Help?" (arXiv
2606.05670) found that on ten benchmarks at most one of six multi-agent systems
beat a matched single agent, and that debate helps when proposals are
*independently checkable* and hurts when handoffs compress context. *[snippet]*
The design consequence for [section 4](#4-design--an-agent-based-audit-system):
specialists earn their cost only by producing checkable evidence — a failing
test, a reproduced path, a killed mutant — and the verifier is required to
disagree, not to confirm.

---

## 4. Design — an agent-based audit system

### 4.1 Principles

1. **Read-only by construction.** The audit never edits the tree it audits. Tool
   grants are `Read`, `Glob`, `Grep`, and a `Bash` allow-list of read-only
   commands; the run happens in a worktree or scratch clone so that even a
   mistaken write cannot reach the branch.
2. **Independent context.** The auditor never shares a conversation with the
   builder. It receives the artifact and the requirement, not the reasoning that
   produced them. Sharing context is how a reviewer inherits the builder's blind
   spots.
3. **Deterministic first.** Every technique in [3.1](#31-deterministic--run-on-every-change-no-model-needed)
   runs before any model is called, and its output is input to the model stages.
   A model asked to find a broken link is a waste; a model told which links are
   broken can ask why.
4. **Verify or tag.** A finding reaches the report only after a verifier agent
   reproduces it, or it carries an *unverified* tag and a lower severity.
5. **Bounded cost and bounded output.** Each specialist returns a fixed-schema
   JSON of at most a few thousand tokens; the orchestrator holds only summaries.
   Inventory and fan-out run on a small model; verification and synthesis on a
   large one. `--max-turns` and a cost ceiling are set, not hoped for.
6. **Every content is data.** The auditor treats everything it reads — including
   the rules files it is auditing — as evidence, never as instruction. An
   instruction found inside audited content is itself a finding.
7. **Findings become checks.** A verified finding of a deterministic class is
   closed by adding the check to the gate, not by fixing the instance.

### 4.2 Architecture

```
                 ┌──────────────┐
   scope, repo → │ Orchestrator │ ── holds summaries only, small model
                 └──────┬───────┘
                        │ 1. inventory
                 ┌──────▼───────┐
                 │  Inventory   │  stack, entry points, harness files, gates,
                 │  (read-only) │  tests, CI, permissions → inventory.json
                 └──────┬───────┘
                        │ 2. deterministic stage (no model)
                 ┌──────▼───────────────────────────────────────┐
                 │ validator · mutation probes · hidden-char scan │
                 │ hook policy · reference resolution · perm diff │ → facts.json
                 └──────┬───────────────────────────────────────┘
                        │ 3. specialists, parallel, each with facts.json
     ┌──────────┬───────┼────────┬────────────┬─────────────┐
┌────▼───┐ ┌────▼───┐ ┌─▼────┐ ┌─▼──────┐ ┌───▼──────┐ ┌────▼─────┐
│Harness │ │Security│ │Tests │ │Spec    │ │Consist-  │ │Red-team  │
│auditor │ │auditor │ │qualty│ │conform.│ │ency      │ │prober    │
└────┬───┘ └────┬───┘ └─┬────┘ └─┬──────┘ └───┬──────┘ └────┬─────┘
     └──────────┴───────┴────────┴────────────┴─────────────┘
                        │ 4. candidate findings (fixed schema)
                 ┌──────▼───────┐
                 │   Verifier   │  reproduces each candidate in a sandbox;
                 │  (per item)  │  discards or tags *unverified*
                 └──────┬───────┘
                        │ 5. verified findings
                 ┌──────▼───────┐
                 │   Reporter   │  severity-ordered report, machine-readable
                 │              │  findings, proposed checks, PR comment
                 └──────────────┘
```

**Specialist briefs** (each is a subagent definition with a read-only tool set
and a one-paragraph system prompt):

| Specialist | Question it answers | Primary inputs |
|------------|--------------------|----------------|
| Harness auditor | Which mechanisms in the rules, skills, hooks, and settings are dead, contradictory, or unread by the product? | inventory, facts, the product's current reference |
| Security auditor | What is exploitable, and through which channel — code, config, hook, synced content? | facts, threat model from inventory |
| Test-quality auditor | Which tests would pass against broken code? | mutation results, test diffs, coverage |
| Spec-conformance auditor | Which acceptance criteria have no proof? | feature definitions, tests, code |
| Consistency auditor | Which rules have more than one home, and where do the copies disagree? | all rule files |
| Red-team prober | Which content channel makes the agent follow an instruction it should report? | scripted sessions with planted instructions |

### 4.3 Findings schema

One object per finding; the reporter sorts by severity, then confidence.

```json
{
  "id": "H-003",
  "layer": "harness | product | process",
  "class": "dead-mechanism | rule-conflict | injection | supply-chain | weak-test | spec-gap | ...",
  "severity": "blocker | important | suggestion",
  "confidence": "verified | unverified",
  "location": "path:line",
  "claim": "one sentence, falsifiable",
  "evidence": "what was run and what it showed",
  "reproduction": "command or steps a human can rerun",
  "fix": "the smallest change that closes it",
  "becomes_check": "the permanent check this finding justifies, or null"
}
```

### 4.4 Building it on Claude Code

Three implementation shapes, in the order to adopt them:

1. **A skill plus subagent definitions, inside the repository.** An `/audit`
   skill orchestrates; each specialist is a file in `.claude/agents/` with
   `tools: Read, Glob, Grep` and a `Bash` allow-list, `isolation: worktree`,
   and `maxTurns` set. Subagents run in parallel (the documented default cap is
   twenty concurrent). The deterministic stage is a script the skill runs first.
   This is the cheapest to start and the one this repository should build first.
2. **Headless runs in CI.** `claude -p` with `--output-format json`,
   `--allowedTools` restricted to read-only tools, `--max-turns`, and
   `--append-system-prompt` carrying the specialist brief, one job per
   specialist, results merged by a script. `claude-code-action` is the packaged
   form for pull requests. The audit posts a comment; it never pushes.
3. **An Agent SDK program** (`claude-agent-sdk` on PyPI,
   `@anthropic-ai/claude-agent-sdk` on npm) when the orchestration outgrows a
   skill: custom tools for the deterministic stage, hooks that enforce the
   read-only boundary at the tool-call level, and typed findings.

**Reuse what exists before building.** Anthropic ships an in-session
security-guidance plugin (pattern match per edit, diff review per turn, agentic
review at commit), a single-pass `/security-review`, a multi-agent
`claude-security` plugin whose findings pass independent verifier agents and
export SARIF, and pull-request Code Review. The audit system designed here
covers what those do not: the harness layer, test quality, spec conformance,
and rule consistency — and it *invokes* the shipped security tools as its
security specialist rather than re-implementing them.

**Testing the harness with the product's own eval runner.** `claude plugin eval`
runs prompt cases against graders (`regex`, `tool_used`, `file_exists`, an LLM
judge) with and without a plugin, and gates on a score threshold with a cost
ceiling. Skills packaged as a plugin can therefore have behavioural tests in CI:
"given this prompt, the skill is invoked and the commit message matches the
convention." Hooks and `CLAUDE.md` have no shipped eval; those need the
deterministic checks above plus scripted sessions.

### 4.5 Guardrails for the audit run

- Tool grants: `Read`, `Glob`, `Grep`; `Bash` only for a listed set (`git
  diff`, `git log`, the test runner, the validator, the mutation runner).
- `permissions.deny` on `Write`, `Edit`, `WebFetch` unless the currency check
  needs the product reference — then an allow-list of documentation hosts only.
- Worktree or scratch-clone isolation for every specialist and the verifier.
- No network in hooks that the audit registers.
- **Auditing a checkout you did not write is itself a trust decision.** A
  headless run uses the repository's hooks, `env` block, and skill tool grants
  without asking (verified today against the permissions reference). Run the
  audit with `--setting-sources user` so no project settings load, or `--bare`
  plus `--settings '{"disableAllHooks": true}'`, and treat the project's
  `.claude/` as *input to be audited*, never as configuration to be obeyed.
- Cost and turn caps are flags, not intentions: `--max-turns`,
  `--max-budget-usd`, and a workflow timeout; `--output-format json` with
  `--json-schema` for typed findings.
- In `claude-code-action`, the official read-only reviewer pattern grants a
  single tool, the inline-comment MCP tool, and nothing that writes to the
  tree. The audit copies that shape.
- The audit's own subagent definitions and skill live in the repository and are
  themselves inside the audit's scope.

### 4.6 The loop back into development

The audit is worth running once. It is worth *having* only if its findings
change what the next session does:

1. **Deterministic-class finding → check.** Add it to the validator (or the
   project's linter) and to the mutation-probe list, in the same pull request
   that fixes the instance.
2. **Judgment-class finding → rule with a reason.** Write it where the rule's
   single home is, with the failure it prevents, so the next agent knows why.
3. **Recurring finding → skill change.** If the same class shows up in two
   audits, the procedure that produced it is wrong, not the code.
4. **Audit before ship.** The `/ship` finish line gains one stage: an audit
   with zero blockers on the head commit.
5. **Score the gate.** Report the mutation-probe catch rate over time. A gate
   whose catch rate is not rising is not learning.

---

## 5. Worked example: this repository

Method: the deterministic stage from [3.1](#31-deterministic--run-on-every-change-no-model-needed)
run by hand, then a currency check of the harness against the official Claude
Code reference (fetched 2026-09-16), then a review pass. Baseline before any
probe: validator clean, 67 unit tests passing, catalog current, hooks
syntax-clean, no hidden characters in any tracked file.

### 5.1 Findings

| # | Severity | Class | Finding | Evidence | Smallest fix |
|---|----------|-------|---------|----------|--------------|
| 1 | 🟡 Important | supply-chain | The session-start hook clones the URL in `CCGG_REPO`, then runs `update.sh` from it, which pulls the guide's master and **overwrites the project's hooks, validator, and skills** — executable content — at every session start. One compromised commit on the guide's default branch runs in every wired project. Nothing pins a ref or verifies what was pulled. In a headless or CI session the chain runs with **no trust dialog at all**, since hooks and the `env` block are used under `claude -p` without trust. | `.claude/hooks/session-start.sh` lines 16–22; `update.sh` (pull, `sync_file` over hooks and `tools/`). Official settings and permissions references: a committed `env` block applies after the folder is trusted once in interactive mode and immediately under `-p`; hook edits are picked up by a file watcher. | Pin: `CCGG_REF` (tag or commit) checked before sync; refuse to sync when the clone's HEAD is not the pinned ref. Document the trust boundary next to the live-sync section of the README. Verified. |
| 2 | 🟡 Important | dead-mechanism | The pre-compact hook prints "run /flush" **to a channel the model never sees.** For `PreCompact`, plain stdout goes to the debug log; only `SessionStart`, `UserPromptSubmit`, `UserPromptExpansion`, and `PostModelSwitch` add stdout to context. The comment in the hook says it "signals the AI"; it signals the user's log. | `.claude/hooks/pre-compact.sh`; hooks reference, *Exit code 0*. | Emit JSON with `additionalContext` from the hook (documented for `PreCompact`), or rely on the existing session-start hook's `compact` matcher to inject the reminder after compaction. Whichever is chosen, the flush-before-compaction promise in the charter needs re-wording to match what the mechanism can do. Verified. |
| 3 | 🟡 Important | dead-mechanism | Every skill declares `when-to-use` (hyphen). The product's documented key is **`when_to_use`** (underscore), appended to `description` in the skill listing. The trigger phrases the repository maintains, and the validator enforces, are most likely never shown to the model. Same file: `allowed-tools: powershell, bash` names no Claude Code tool (the documented values are tool names such as `Bash`, `Read`, or patterns such as `Bash(git *)`); the pre-approval grants nothing. `name` is display-only for project skills — the command comes from the directory. | All 26 `SKILL.md` files; `tools/validate.py` `SKILL_KEYS`; skills reference, frontmatter table. | Rename the key in all skills, the validator, the skillify template, and the charter's *Skill loading* line; set `allowed-tools` to real tool names or drop it. One mechanical PR. Verified against the reference; the product's handling of the hyphenated variant was not exercised live — unverified only in that narrow sense. |
| 4 | 🟡 Important | gate-blind-spot | The validator catches **10 of 21** planted defects. Missed: hook registered but file deleted; hook file present but unregistered; empty `description`; `name` not matching directory; nonsense `allowed-tools`; zero-width character in `AGENTS.md`; injected instruction in a skill; hook piping a remote script to shell; `CCGG_REPO` pointed at an attacker URL; CI workflow deleted; validator's `main` neutered. | Probe table in [5.2](#52-mutation-probes-against-the-validator). | Add five deterministic checks (both-direction hook registration, empty description, name/directory match, hidden characters, network-and-exec patterns in hooks). The remaining misses are model-judgment or meta checks. |
| 5 | 🟡 Important | rule-vs-enforcement | The code gate requires 90 percent coverage on changed lines; **no coverage tool runs anywhere**, and the validator's tests cover 5 of 19 functions — all pure helpers, none of the ten `check_*` routines end to end. The rule has no enforcement; the enforcer has no tests where it matters. | `tools/test_validate.py` imports; `.github/workflows/validate.yml`. | Turn the probe harness in 5.2 into a fixture-based test of each `check_*`; add `coverage` to the CI job with the gate's own threshold. |
| 6 | 🔵 Suggestion | currency | `docs/14`–`docs/16` describe a CLI that is not Claude Code's: `--yolo`, `config.toml`, personas, `spawn_subagent`, `run_terminal_cmd`, `claude agent stdio`. The official reference has none of these. The provenance disclaimer lives only in `docs/index.md`; a session that greps `docs/` lands on the wrong facts with no warning. | Official sub-agents and headless references. `/plan`, `/context`, `/memory`, `/hooks`, `/agents` **do** exist, so the rules files' command references are fine. | Banner each mirrored chapter, or move the mirror out of the tree. |
| 7 | 🔵 Suggestion | accuracy | The charter says a malformed skill header means the skill "silently stops loading". The reference says frontmatter is read only when `---` is line 1; otherwise the whole file, markers included, becomes skill content — it loads, wrongly. | Skills reference, frontmatter section. | One-line correction in the charter. |
| 8 | 🔵 Suggestion | injection-surface | `SessionStart` stdout is trusted context. The hook prints file paths from `decisions/` and directory names from `update.sh` into it. Today that content is repository-controlled; it is still a channel worth naming. | `session-start.sh`; hooks reference. | Note the channel in the hook's header comment; keep its output to fixed strings and paths. |
| ✅ | Good | — | CI actions pinned by commit SHA with `contents: read`; validator is stdlib-only; `update.sh` replaces atomically and never deletes; no secrets, no hidden characters, no shell syntax errors; the validator's cache-stability and install-set checks are unusual and correct. | | |

### 5.2 Mutation probes against the validator

Scratch clone, one defect per run, hard reset between runs.

| Planted defect | Result |
|----------------|--------|
| Broken relative link in a skill | caught |
| Skill frontmatter missing a house key | caught |
| Hook loses executable bit in the index | caught |
| Hook with a bash syntax error | caught |
| `settings.json` invalid JSON | caught |
| `CLAUDE.md` bridge removed | caught |
| New skill directory absent from catalogs | caught |
| Session-volatile date in an always-loaded file | caught |
| Rules file links outside the install set | caught |
| Feature marked shipped with an open idea | caught |
| `allowed-tools` set to nonsense names | missed |
| Hook registered in settings but file deleted | missed |
| Hooks unregistered, files orphaned | missed |
| Zero-width character in `AGENTS.md` | missed |
| Instruction sentence injected into a skill | missed |
| Session-start hook pipes a remote script to `sh` | missed |
| `CCGG_REPO` in settings pointed at an attacker URL | missed |
| Skill `name` differs from its directory | missed |
| Skill `description` emptied | missed |
| CI workflow deleted | missed |
| Validator `main()` forced to return 0 | missed |

Two things the table shows that a passing CI run cannot: which of the
repository's *stated* guarantees are enforced, and that the misses cluster in
exactly the harness-specific classes from [section 2](#2-agent-specific-failure-modes).

The probe harness, for reuse:

```bash
probe() {  # $1 = label, $2 = shell mutation
  git reset -q --hard HEAD && git clean -fdq
  eval "$2"; git add -A >/dev/null
  if python3 tools/validate.py >/dev/null 2>&1; then echo "MISSED: $1"; else echo "CAUGHT: $1"; fi
}
probe "hook file orphaned" "printf '{\"hooks\":{}}' > .claude/settings.json"
```

---

## 6. Recommendations, in order

1. **Close the two verified dead mechanisms** (findings 2 and 3): one PR for the
   `when_to_use` rename plus `allowed-tools` values, one for the pre-compact
   hook. Both are mechanical; both change what the product actually does.
2. **Add the five deterministic checks** from finding 4 to `tools/validate.py`,
   each with a fixture test, and land the probe harness as the validator's
   end-to-end test (finding 5).
3. **Pin the live sync** (finding 1) and document the trust boundary.
4. **Define the audit as a feature** (`/feature`): the `/audit` skill, the
   specialist subagent definitions under `.claude/agents/`, the deterministic
   script, and the findings schema from [4.3](#43-findings-schema). Acceptance
   criterion one: the audit, run on this repository, reproduces findings 1–5
   without being told about them.
5. **Wire the audit into `/ship`** as the stage before merge, and into the
   installed projects' CI as a headless job that comments and never pushes.
6. **Publish the catch rate.** The probe table above is the first data point.

---

## Sources

Status: *fetched* means read in full on 2026-09-16; *snippet* means the primary
page was blocked by the sandbox's egress policy and the figure comes from a
search excerpt of it plus secondary coverage — open the primary before quoting.

**Claude Code reference (all fetched, code.claude.com/docs/en/…)**
- `hooks` — event list; exit-code-0 stdout routing; `PreCompact` and
  `SessionStart` output fields
- `skills` — frontmatter table (`when_to_use`, `allowed-tools` format, `name`
  is display-only for project skills, frontmatter read only from line 1)
- `settings` — precedence; committed `env` and hooks; what waits for trust
- `permissions` — *Project allow rules and workspace trust*; *What runs before
  you trust a folder*; the `-p` and SDK trust table and its mitigations
- `commands` — built-in command table (`/plan`, `/context`, `/memory`,
  `/hooks`, `/agents`, `/security-review` exist)
- `sub-agents` — `.claude/agents` frontmatter, `isolation: worktree`,
  concurrency default
- `headless`, `cli-reference` — `-p` flags, `--bare`, `--setting-sources`,
  `--max-budget-usd`, `--json-schema`
- `claude-security`, `security-guidance`, `code-review`, `github-actions`,
  `plugin-evals` — the shipped security and eval tooling described in 4.4

**Evidence on agent-built code (snippet unless noted)**
- Veracode, GenAI Code Security Report 2025 and 2026 update —
  veracode.com/blog/genai-code-security-report
- GitClear, "The AI Code Quality Maintainability Gap" (2026) —
  gitclear.com/the_ai_code_quality_maintainability_gap
- "Confident and Wrong: Silent Semantic Failures in Coding Agents" — arXiv 2603.25764
- SpecBench — arXiv 2605.21384
- "How Coding Agents Fail Their Users" — arXiv 2605.29442
- Transluce, "Measuring coding agent misalignment in the wild" —
  transluce.org/docent/blog/coding-agent-behaviors
- MutGen — arXiv 2506.02954; replication — arXiv 2607.22880
- "We Have a Package for You!" (slopsquatting), USENIX Security 2025 — arXiv 2406.10279
- Pillar Security, "Rules File Backdoor" (2025-03-18) — pillar.security/blog
- Invariant Labs, MCP tool poisoning (April 2025) — invariantlabs.ai/blog
- Check Point Research, Claude Code CVE-2025-59536 / CVE-2026-21852 /
  CVE-2026-25725 (February 2026) — research.checkpoint.com
- OWASP Top 10 for Agentic Applications 2026 (2025-12-09) — genai.owasp.org

**Systems and patterns (snippet unless noted)**
- Anthropic Code Review, security-guidance plugin, Claude Security plugin —
  fetched, see reference list above
- Google Big Sleep (August 2025), DeepMind CodeMender (2025-10-06) —
  deepmind.google/blog
- OpenAI Aardvark / Codex Security (2025-10-30) — openai.com/index/introducing-aardvark
- GitHub agentic autofix public preview (2026-07-10) — github.blog/changelog
- Anthropic, "Building Effective Agents" (December 2024) and "How we built our
  multi-agent research system" (2025-06-13) — anthropic.com/engineering
- "Adversarial Review" — arXiv 2608.18167; "Do More Agents Help?" — arXiv 2606.05670
- Meta, "LLMs are the key to mutation testing" (2025-09-30) — engineering.fb.com;
  AdverTest — arXiv 2602.08146
- OSS-Fuzz-Gen README — github.com/google/oss-fuzz-gen (fetched by the research agent)

**This repository (fetched, run today)**
- `tools/validate.py`, `tools/test_validate.py`, `.claude/hooks/*.sh`,
  `update.sh`, `install.sh`, `.claude/skills/*/SKILL.md`, `docs/14`–`docs/16`
- Mutation-probe harness and results in [5.2](#52-mutation-probes-against-the-validator)
