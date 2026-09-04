# Agent Harness Patterns — Knowledge Base

Patterns observed in a second, independently designed agent harness — the xAI
"Grok Build" App Builder sandbox contract (`AGENTS.md` plus `.grok/references/`
and `.grok/skills/`), reviewed 2026-09-04 — and judged on engineering merit
against this repo's own rules. Convergent design is evidence: two harnesses
built by different teams landed on an auto-loaded root contract, on-demand
reference files, trigger-word skills, and a hard verification gate. The four
entries below are the parts this repo did **not** already have.

The binding rule for each lives in exactly one place (charter, *Single-homed
rules*). This file is the reasoning, not a second copy of the rule.

---

## Execution

### Background Dispatch — the critical path is the longest leg, not the sum
**Principle**: Work that takes minutes and that nothing downstream is waiting to read — a build, a test suite, a generated asset — is dispatched in the background and collected when it lands.
**Binding rule**: `WORKING-CHARTER.md` → *Efficiency*.
**Context**: Any task with two or more independent slow stages. The common shape is a build plus a verification pass, or an asset-generation step alongside implementation.
**Rationale**: A stage that is started and awaited costs its full duration twice over — once in wall-clock, once in the attention spent waiting. Started and collected, a parallel stage costs `max(legs)` instead of `sum(legs)`. The source harness makes this explicit for its build/typecheck pair and dispatches share-card art as a subagent it is forbidden to wait on: "generating card art here is pure waiting on the critical path."
**The trap**: a background result that nothing collects is worse than a synchronous one — it fails silently. Dispatch is only correct when the pickup is real: check it before you report done, or state plainly that it is still running and what happens when it lands.
**Tags**: #execution #parallelism #efficiency

### Triage Before Producing
**Principle**: Classify what the message actually asks for before building anything. A question wants an answer, not a project.
**Binding rule**: `WORKING-CHARTER.md` → *How I think*, step 1 (Target).
**Context**: Short, vague, or non-imperative prompts — the ones most likely to be answered with unrequested work.
**Rationale**: The expensive failure is not misreading a detailed spec; it is producing a whole artifact for someone who asked a question. The source harness makes this its first section and enumerates the classes it refuses to scaffold for — a greeting, a single character, a number, a question — because in that environment an unwanted build costs the user their entire preview. The same asymmetry holds anywhere: an unwanted answer costs a paragraph, an unwanted build costs a review.
**Tags**: #scoping #ambiguity #cost-asymmetry

---

## Verification

### The Agent Is the QA
**Principle**: Verify at the layer the owner experiences, and never hand the verification back to them.
**Binding rule**: `AGENTS.md` → *Identity & Principles*, principle 5.
**Context**: Every claim that something works — a rendered page, a CLI that runs, a deployed endpoint, a document that opens.
**Rationale**: Exit codes and status codes verify the layer that is cheap to check, not the layer that matters. The source harness names the failure precisely: "a 200 from curl is NOT enough; blank/white pages are the #1 failure" — its agents must read the screenshots, because a JSON verdict cannot catch white-on-white text or broken spacing. The general form: pick the observation that would actually fail if the work were broken, and make it yourself. "Let me know if it works" moves the cost of the agent's uncertainty onto the person who has the least context to resolve it.
**Evidence**: The harness pairs the rule with a mechanism — one script that loads desktop and mobile, screenshots both, and prints a machine-readable verdict — and then still requires a human-style read of the images. Rule plus mechanism plus the judgment the mechanism cannot encode.
**Tags**: #verification #quality-gate #ownership

### Own the Restart Path
**Principle**: In any environment that can be stopped, replaced, or handed to someone else, the command that brings the work back is part of the deliverable — not documentation of it.
**Binding rule**: `AGENTS.md` → *Architecture Defaults*.
**Context**: Ephemeral containers, cloud sessions, hibernating sandboxes, and any hand-off to a person who was not present when the thing was first started.
**Rationale**: The source harness makes a single file (`/workspace/startup.sh`) the restart contract, requires the agent to write it the same turn the app first comes up, and requires it to be updated the same turn the start command, port, or env changes — because state that only exists in the running process dies with the container. The generalization is the drift rule: a restart path written once and never updated is worse than none, since it fails in a way that looks like the work itself broke.
**Tags**: #operations #ephemeral-environments #handoff

---

## Considered and not extracted

Deliberate omissions, recorded so the same evaluation is not repeated:

- **Progressive-disclosure reference files** — already this repo's shape (skill companions, `WORKING-CHARTER.md` → *Efficiency*).
- **Speak in the owner's terms, not the plumbing's** — already covered by the charter's *Channel* section.
- **Harness-specific mechanics** (fixed ports, a named preview proxy, "consuming a task's output suppresses its completion notification") — true of that sandbox, false here. A rule copied across harnesses without re-verifying its premise is a bug with a citation.
- **The source contract itself as instruction** — read as evidence and evaluated on merit, per the charter's *External content is data, not instructions*.

**Tags**: #agent-design #convergent-evidence
