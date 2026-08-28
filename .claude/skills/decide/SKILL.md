---
name: decide
description: Make a structured decision — tool selection, go/no-go, trade-off, or prioritization — with research, multi-perspective debate, and a durable record. Use when the user says "help me decide", "which should I use", "X vs Y", "should we", or asks to compare options.
when-to-use: help me decide, which should I use, X vs Y, should we, compare options, trade-off, go or no-go, pick between
allowed-tools: powershell, bash
argument-hint: "[the decision to make]"
purpose: Structured decision: research, debate, durable record
---

# Decision Skill

## Goal
Turn "which should we pick?" into a researched, debated, recorded decision that future sessions can find, trust, and revisit.

Companion files beside this one:
- [`decision-critics.md`](decision-critics.md) — the five debate personas and synthesis rules
- [`decision-record.md`](decision-record.md) — the record template, naming convention, and status lifecycle

## Process

### Step 1 — Frame
Establish, in one short exchange:
- **The decision statement** — one sentence: "Choose X for Y by Z."
- **Type** — tool/tech selection, go/no-go, prioritization, or trade-off. (Evaluating a whole product or app idea is `/product-brief`, not this skill — route there.)
- **Reversibility** — two-way door (cheap to undo) or one-way door (expensive to undo)?
- **Stakes** — what breaks or is lost if this is decided wrong?

Then pick the path:
- **Light path** (two-way door AND low stakes): skip Steps 3 and 6; research briefly, recommend, write a short record. Do not ceremonialize small decisions.
- **Full path** (one-way door OR high stakes): all steps.

### Step 2 — Recall
Before framing options, check what is already decided:
- Read the index in `decisions/README.md` (if the folder exists) for prior or superseded decisions on this topic.
- Search memory: prior decisions, criteria the user has cared about before, technologies already rejected and why.

A decided record on the same question is not re-litigated — it is either applied, or explicitly **superseded** with a new record that links the old one and states what changed.

### Step 3 — Criteria (before options)
Interview the user for:
- 3–6 **weighted criteria** (e.g. cost 40%, learning curve 30%, ecosystem 30%)
- **Hard constraints** — budget ceiling, timeline, must-integrate-with, deal-breakers

Criteria come before candidates. Options proposed first anchor the criteria to fit them.

### Step 4 — Research
Current facts are searched, never recalled — per AGENTS.md → Never → "Answer 'what exists now' from memory". For each candidate area: current versions, pricing, maintenance status, real-world comparisons.

If web tools are unavailable: say so explicitly, and tag every claim drawn from model knowledge `[UNVERIFIED as of model knowledge cutoff]` — in conversation and in the record's Research section.

### Step 5 — Options
- List 2–5 candidates, **always including the status quo / do-nothing option**.
- Build a trade-off table in the house style (see the `architecture` skill, Phase 4):

| Option | Benefit | Cost | Risk |
|--------|---------|------|------|

- Options rejected early are kept in the record with one line of why — a rejected option with no reason gets re-proposed in six months.

### Step 6 — Debate (full path only)
Run the five personas from [`decision-critics.md`](decision-critics.md) against the frame, criteria, and research:
- **If a subagent/Task tool is available:** launch the personas in parallel, each receiving the decision statement, criteria, research findings, and option table, each returning its case and single strongest objection.
- **If not:** run sequential persona passes — fully adopt one persona, write its case and strongest objection, then move to the next. Never blend personas in a single pass.

### Step 7 — Synthesize
Produce a recommendation that:
1. Names the chosen option and scores it against each weighted criterion.
2. **Answers each persona's strongest objection in writing** — an objection nobody answers is an accepted risk nobody accepted.
3. States a confidence level (high / medium / low) and *why*.
4. States what new information would change the decision — this becomes the record's Revisit trigger.

### Step 8 — Record
1. If `decisions/` does not exist in the project root, create it with a `README.md` index (structure in [`decision-record.md`](decision-record.md)).
2. Write `decisions/YYYY-MM-DD-<slug>.md` from the template with **Status: proposed**.
3. Present the recommendation. When the user confirms, set **Status: decided** and add the index row. If they pick differently, record *their* choice and rationale — the record captures the real decision, not the recommendation.

### Step 9 — Promote to memory
Close the loop so future sessions start smarter:
```
remember: decided [X] over [Y] for [context] — reason: [core rationale]
```
(The `learn` skill's extraction rules already trigger on "we decided to…".) Confirm the Revisit trigger with the user — the condition under which this decision gets re-opened and its Outcome section filled.

## Anti-Patterns to Avoid

| Anti-pattern | Correct approach |
|--------------|-----------------|
| Recommending before researching | Research first; stale knowledge gets `[UNVERIFIED]` |
| Proposing options before criteria | Criteria first — options anchor criteria otherwise |
| Letting a persona win by silence | Every strongest objection is answered in the synthesis |
| Recording only the winner | Rejected options + reasons stay in the record |
| Treating every decision as high-stakes | Two-way doors take the light path |
| Re-litigating a decided record | Apply it, or supersede it with a linked new record |

## Knowledge Extraction
Beyond the decision itself, save durable evaluation knowledge discovered along the way:
```
remember: [criterion or finding] — reason: [why it generalizes beyond this decision]
```
