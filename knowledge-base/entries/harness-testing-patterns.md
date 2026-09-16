# Harness Testing Patterns — Knowledge Base

Durable lessons from auditing the configuration layer that steers a coding
agent — rules files, skills, hooks, settings — extracted from the research in
[`../research/testing-agent-built-systems.md`](../research/testing-agent-built-systems.md)
(as of 2026-09-16). Each entry is a principle with the failure it was learned
from; the full evidence stays in the research file.

---

## Verification

### Documented-but-dead is the modal harness defect
**Principle**: A mechanism in a rules or config file is not present until the product is shown to read it. Text that the product ignores fails silently, and silent failure is the default for every file no compiler executes.
**Learned from**: This repository's pre-compact hook "signals the AI" on a channel that only reaches the compaction summarizer; every skill carried a `when-to-use` key while the product reads `when_to_use`; the tool grant named no tool the product has. All three passed the validator until checks 13 and 14 landed.
**Detection**: For each mechanism, name the product surface that consumes it and verify against the current reference, not memory. Then exercise it once in a live session.
**Tags**: #harness #verification #currency

### A validator that checks shape passes what the product ignores
**Principle**: "The key exists" is a different test from "the product reads this key, spelled this way, with a value it accepts." Enforce the second or state plainly that only the first is enforced.
**Learned from**: `SKILL_KEYS` in the validator enforces five house keys, one of which the product does not read and one whose value it cannot parse.
**Detection**: Mutation probe — set the value to nonsense and see whether the gate fires.
**Tags**: #validator #semantics #gate

### Mutation-probe every gate you rely on
**Principle**: The catch rate of a gate is a number, and it is only known after planting defects and counting. A gate that has never missed on purpose has never been measured.
**Learned from**: Twenty-one planted defects against a green validator: ten caught, eleven missed, and the misses clustered in exactly the harness-specific classes nobody had written a check for.
**Detection**: Eleven lines of shell in a scratch clone — hard reset, mutate, stage, run, record. Keep the probe list in the repo and grow it with every finding.
**Tags**: #mutation #gate #measurement

---

## Trust

### Anything synced into a rules directory is executable content
**Principle**: Skills, hooks, and validators pulled from a remote at session start are code the agent runs. Pin the ref, verify what arrived, and write the trust boundary down where the sync is documented.
**Learned from**: The live-sync hook clones a URL held in a committed settings file and runs the script it finds there. Under headless mode the whole chain runs with no trust dialog, because a `-p` run uses repository hooks and the `env` block without asking.
**Detection**: Hook policy check — network calls, remote execution, and env-sourced URLs in any hook are findings until pinned.
**Tags**: #supply-chain #hooks #trust

### The auditor reads the harness as evidence, never as configuration
**Principle**: An audit of a checkout must not load that checkout's settings. Run with project settings excluded, treat `.claude/` as input, and report any instruction found inside it rather than following it.
**Learned from**: The product's own permissions reference: hooks, `env`, and skill tool grants from the repository are used in headless runs; only excluding project settings entirely prevents it.
**Tags**: #audit #isolation #injection

---

## Design

### Findings need a verifier that is not the hunter
**Principle**: A second opinion from the same context is not verification. A finding is verified when something outside the model reproduces it — a failing test, a triggered path, a killed mutant — or it carries an *unverified* tag.
**Learned from**: Every shipped scanner that publishes a false-positive strategy converges on this: independent verifier agents, sandbox reproduction, re-running the analyser on the fix. Multi-agent review without checkable evidence collapses into false consensus. The first live run of this repository's own audit proved it: the specialist and the research both said PreCompact stdout is discarded; the verifier read the installed product and found it feeds the compaction summarizer — same defect, different mechanism, different fix.
**Tags**: #verification #multi-agent #false-positives

### A documentation summary is not the product
**Principle**: A fetched page summarised by a model is one more model output. When a claim about product behaviour decides a fix, the oracle is the product itself — its binary, a live session, or the reference quoted verbatim.
**Learned from**: The research's suggested fix for the pre-compact hook ("emit `additionalContext` JSON, documented for PreCompact") came from a lossy summary of the hooks reference; the verifier found no such output path in two installed versions.
**Tags**: #currency #verification #oracle

### A verified deterministic finding closes as a check, not a fix
**Principle**: Fixing the instance leaves the class. If the finding could have been caught by a script, the pull request that fixes it also adds the script and its fixture test.
**Learned from**: This repository's own rule — a problem found twice by a human becomes a check run forever by the machine — applied to the eleven probe misses.
**Tags**: #gate #feedback-loop #process
