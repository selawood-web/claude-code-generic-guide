---
name: product-brief
description: Evaluate a product, app, or feature idea before committing to build it — market research, multi-perspective viability debate, an explicit Go/No-go/Pivot verdict, and a durable brief. Use when the user says "I have an app idea", "is this worth building", "evaluate this idea", or "should I build".
when-to-use: app idea, product idea, is this worth building, evaluate this idea, should I build, validate my idea, market fit
allowed-tools: powershell, bash
argument-hint: "[the product or feature idea]"
---

# Product Brief Skill

## Goal
Answer "is this idea worth building, and in what shape?" *before* any spec is written.
This skill evaluates; the `requirements` skill specifies. If the user already knows
they are building it and needs a spec, route to `/requirements` instead. If the
question is a choice between existing options, route to `/decide`.

Shared companions (in the `decide` skill directory, which travels with this one):
- [`../decide/decision-critics.md`](../decide/decision-critics.md) — debate personas
- [`../decide/decision-record.md`](../decide/decision-record.md) — record template ("For product briefs" sections)

## Process

### Step 1 — Intake & classify
- Restate the idea in one sentence: "[product] that does [what] for [whom]."
- Classify: **new product/app** or **feature on something existing**?
- Ask what triggered the idea — a personal pain, an observed gap, a competitor move?
  The trigger often reveals the real problem better than the pitch does.

### Step 2 — Prior art recall
- Check `decisions/README.md` (if present) for earlier briefs or decisions on related
  ideas — a previously no-go'd idea returning deserves the old record's reasons first.
- Search memory for related domain knowledge and past criteria.

### Step 3 — Market research (mandatory)
Current facts are searched, never recalled — per AGENTS.md → Never → "Answer 'what
exists now' from memory". Research:
- Who already solves this problem, and how (direct competitors, workarounds)?
- What do the incumbents charge? Where do their users complain?
- What would make someone switch — is the differentiation real or cosmetic?

If web tools are unavailable: say so, and tag every market claim
`[UNVERIFIED as of model knowledge cutoff]` in conversation and in the brief.

### Step 4 — Viability debate
Run the five personas from [`../decide/decision-critics.md`](../decide/decision-critics.md)
against the idea, framed as: *build this vs. don't build this vs. build something
adjacent*. Same mechanics as `/decide` Step 6 — parallel subagents when available,
sequential persona passes otherwise; each persona returns a case plus its single
strongest objection; the synthesis answers all five.

### Step 5 — Verdict: Go / No-go / Pivot
State one of three explicitly — "interesting, maybe later" is not a verdict:
- **Go** — the problem is real, the differentiation holds, the effort is worth it.
- **No-go** — record *why*, so the idea's return in six months meets its old objections.
- **Pivot** — the underlying problem is real but the proposed shape is wrong; state
  the adjacent shape worth evaluating.

If the verdict is contested (personas split, user disagrees), settle it with the full
`/decide` workflow — the verdict is itself a go/no-go decision.

### Step 6 — On Go: define the MVP
Do not write a spec here. Run the `requirements` skill (Steps 1–4: problem, success
criteria, Jobs-to-be-Done MVP scoping, user stories) and link the resulting spec from
the brief. The brief holds the *why build*; the spec holds the *what to build*.
An MVP that cannot be deployed is not an MVP — the Go verdict implies a deployable
slice (the `deploy-steward` skill owns that obligation).

### Step 7 — Record
Write `decisions/YYYY-MM-DD-<slug>.md` from the template in
[`../decide/decision-record.md`](../decide/decision-record.md) with **Type:
product-brief** and its extra sections (Market landscape, Verdict, MVP definition).
Create `decisions/` and its index on first use; add the index row. Status `proposed`
until the user confirms the verdict, then `decided`.

### Step 8 — Promote to memory
```
remember: [idea] verdict [go/no-go/pivot] — reason: [core rationale]
```
Set the Revisit trigger — for no-go ideas especially: what change in the market or
the user's situation would reopen this?

## Anti-Patterns to Avoid

| Anti-pattern | Correct approach |
|--------------|-----------------|
| Defining the product before evaluating it | Verdict first; spec only on Go |
| Skipping the no-go option | No-go is a first-class outcome, recorded with reasons |
| Market claims from memory | Research live, or tag `[UNVERIFIED]` |
| Duplicating the requirements spec in the brief | Brief links the spec; each has one home |
| Evaluating the pitch instead of the problem | Step 1's trigger question finds the real problem |
| "Maybe later" as a verdict | Go, No-go, or Pivot — with a revisit trigger |

## Knowledge Extraction
Market structure outlives individual ideas — save it:
```
remember: [market/domain insight] — reason: [why it applies beyond this idea]
```
