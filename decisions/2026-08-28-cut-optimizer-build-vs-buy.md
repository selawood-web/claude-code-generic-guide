# Cut optimizer engine: build vs buy

- **Date:** 2026-08-28
- **Status:** decided
- **Type:** decision
- **Deciders:** selawood (delegated: "go with recommendations")
- **Supersedes / superseded by:** —

## Context
The Shop OS MVP spec (story 6) needs 2D guillotine sheet optimization with kerf and
grain-direction constraints, feeding realistic sheet counts back into quotes.
Reversible decision: the engine sits behind an internal interface, so a swap later
costs an adapter, not a rewrite. Fast-path decision (no full persona debate) for
that reason.

## Criteria
| Criterion | Weight |
|-----------|--------|
| Meets spec constraints (guillotine, kerf, grain) | 40% |
| No licensing drag on a commercial SaaS | 30% |
| Buildable/maintainable by 1–2 people | 30% |

Hard constraints: server-side callable from a web app; commercial use allowed.

## Research findings (2026-08-28)
- [CutGLib](https://www.optimalon.com/cutting_optimization_library.htm) — mature
  commercial embeddable library; handles kerf; licensing cost/terms require a sales
  conversation (undetermined).
- Open-source options are app-shaped, not library-shaped:
  [freecut](https://github.com/geri1701/freecut) (Rust GUI → PDF),
  [cutlet](https://github.com/mru00/cutlet) (Java, old). Grain support exists in
  commercial [CutStock](https://worldgate.de/en/cutstock-en/).
- Guillotine 2D heuristics (shelf/split-tree, first-fit decreasing) are
  well-documented, and free consumer tools ([CutOptim](https://cutoptim.com/)) set
  the "good enough" expectation bar — shops need realistic sheet counts for quoting,
  not best-in-class nesting.

## Options considered
| Option | Benefit | Cost | Risk |
|--------|---------|------|------|
| Build in-house (guillotine heuristics) | Full control; no license; exact fit for kerf/grain spec | ~1–2 weeks incl. tests | Waste % worse than best-in-class initially |
| License CutGLib | Proven engine | Unknown fee; vendor dependency; sales-gated | Terms drag on SaaS margins |
| Wrap open-source app code | Free | Adaptation cost ≈ build cost; GPL-family contamination risk | License audit burden |

Rejected early: OR-Tools exact optimization — overkill for MVP; revisit if waste %
becomes a competitive complaint.

## Decision & rationale
**Build in-house.** A shelf/split-tree guillotine heuristic with kerf and grain
constraints satisfies every MVP acceptance criterion, carries no license risk, and
is within a 1–2 person team's capacity. The engine goes behind an
`OptimizerEngine` interface so CutGLib (or OR-Tools) can replace it later without
touching quoting.

## Consequences & accepted risks
- Accepted: early waste-% quality below commercial engines; mitigated by the
  interface seam and by quoting needing realism, not perfection.
- Committed: optimizer failures never block quote creation/sending (spec constraint).

## Revisit trigger
User complaints comparing waste % unfavorably to free tools, or the optimizer
exceeding 2 weeks of build effort — either reopens the CutGLib option.

## Outcome
[Empty — filled when the revisit trigger fires.]
