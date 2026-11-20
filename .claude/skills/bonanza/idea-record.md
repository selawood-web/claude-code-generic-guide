# Idea Record — Fact Sheet, Template, Lifecycle

The single home for what `/bonanza` writes. Everything lives in the project root at
`ideas/`, versioned in git. The skill creates the folder and its index on first use.
This repository ships no `ideas/` folder of its own; a project gets one the first
time the skill runs there.

## The fact sheet — `ideas/business-facts.md`

One file per project, refreshed at every intake rather than rewritten. It is the only
description of the business that generators and judges receive, so a line missing
here is a fact no stage knows.

Every line carries one honesty tag from [`character.md`](character.md). Keep it under
sixty lines: it is paid for once per subagent.

```markdown
# Business facts

- **Last refreshed:** YYYY-MM-DD
- **The question this run answers:** [one sentence]

## What it sells, and to whom
- [line] [known]

## How money comes in today
- [line, with the figure and its unit] [known]

## What it owns
[Customers, data, know-how, trust, access, by-products — counted or not.]
- [line] [assumed]

## The market, in the owner's words
- [line] [known]

## Cannot afford to lose
[What no move may put at risk. The Caution judge's hard kill reads this section.]
- [line] [known]

## Constraints
[Time, money, people, law.]
- [line] [known]
```

A line that changes is updated in place and its tag re-set. A `[hoped]` line that a
test later confirms becomes `[known]`, with the date.

## Naming
`ideas/YYYY-MM-DD-<slug>.md` — the date of the run, then a slug of at most seven
lowercase words joined by hyphens. One record per run: the chosen move, with every
other idea of that run inside it.

## Status lifecycle
```
proposed → testing → proven     (the cheap test met its bar)
                   → killed     (the test, or a gate, said no — the reason stays)
         → parked               (real, but not now — says what would bring it back)
```
A killed record is never deleted and never edited into a different idea. An idea that
returns starts a new record that links the old one and says what changed.

## Index
`ideas/README.md` holds one table row per record:

```markdown
| Date | Move, in one sentence | Status | Went to |
|------|-----------------------|--------|---------|
| YYYY-MM-DD | The sentence, linked to YYYY-MM-DD-slug.md | proposed | — |
```

*Went to* names the hand-off: a product brief or decision record under `decisions/`,
a feature definition under `features/`, or a dash.

## Record template

```markdown
# [The move, in one sentence]

- **Date:** YYYY-MM-DD
- **Status:** proposed | testing | proven | killed | parked
- **Path:** light | full
- **Decided by:** [who answered the pick-list, and with which code]
- **Follows / followed by:** [link, or —]

## The question
[The money question this run answered, from the fact sheet.]

## The move
[One sentence: who pays, for what, and why they would.]

## Why it matters
[One sentence, for the person who has to say yes.]

## The numbers
| Figure | Value | Tag |
|--------|-------|-----|
| [what] | [value and unit] | [known] / [assumed] / [hoped] |

Weakest assumption: [one line, tagged]

## The risk
- Worst realistic loss: [figure, unit, tag]
- Reversible: yes | partly | no — [one line]

## The cheap test
[What to do, what it costs, how long it takes, and the result that would kill the idea.]

## Parked
- [idea, one line] — comes back when [condition]

## Killed, and why
- [idea, one line] — [Logic | Caution]: [the number or the loss that killed it]

## Outcome
[Empty at creation. Filled when the cheap test has run: what actually happened, and
whether the status becomes proven or killed.]
```
