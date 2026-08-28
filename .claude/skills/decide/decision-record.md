# Decision Record — Template & Lifecycle

The single home for the record format used by `/decide` and `/product-brief`.
Records live in the project root at `decisions/`, versioned in git. The skill
creates the folder and its index on first use.

## Naming
`decisions/YYYY-MM-DD-<slug>.md` — date decided (or proposed), short kebab-case slug.

## Status lifecycle
```
proposed → decided → validated   (outcome confirmed the decision)
                   → reversed    (outcome contradicted it — fill Outcome with why)
         → superseded            (a newer record replaces this one — link it)
```
A decided record is never edited into a different decision — it is superseded by a
new record that links back. The Outcome section is the learning loop: revisit when
the Revisit trigger fires and score what actually happened.

## Index
`decisions/README.md` holds one table row per record:

```markdown
| Date | Title | Type | Status |
|------|-------|------|--------|
| YYYY-MM-DD | Title, linked to YYYY-MM-DD-slug.md | decision | proposed |
```

## Record template

```markdown
# [Decision title]

- **Date:** YYYY-MM-DD
- **Status:** proposed | decided | validated | reversed | superseded
- **Type:** decision | product-brief
- **Deciders:** [who confirmed it]
- **Supersedes / superseded by:** [link, or —]

## Context
[2-4 sentences: the situation, why a decision is needed now, reversibility and stakes]

## Criteria
| Criterion | Weight |
|-----------|--------|
| [criterion] | [%] |

Hard constraints: [deal-breakers, budget, timeline]

## Research findings
[Dated findings with sources. Claims from model knowledge without live research are
tagged `[UNVERIFIED as of model knowledge cutoff]`.]

## Options considered
| Option | Benefit | Cost | Risk |
|--------|---------|------|------|
| [option A] | | | |
| Status quo / do nothing | | | |

Rejected early: [option — one line why]

## Debate summary
- Champion: [strongest point] → [answered by / accepted as risk]
- Skeptic: …
- Economist: …
- User Advocate: …
- Operator: …

## Decision & rationale
[The choice, scored against the criteria, answering each unanswered objection]

## Consequences & accepted risks
[What this commits us to; the named risks we accept with eyes open]

## Revisit trigger
[The condition that re-opens this decision — a date, a metric, or an event]

## Outcome
[Empty at creation. Filled when the revisit trigger fires: what actually happened,
and whether the status becomes validated or reversed.]
```

## For product briefs, add these sections
Between "Research findings" and "Decision & rationale":

```markdown
## Market landscape
[Competitors/alternatives, their pricing, and the differentiation this idea has]

## Verdict: Go | No-go | Pivot
[The call and its core reason]

## MVP definition
[On Go: link to the requirements spec produced via the requirements skill, or the
smallest scope that tests the core value proposition]
```
