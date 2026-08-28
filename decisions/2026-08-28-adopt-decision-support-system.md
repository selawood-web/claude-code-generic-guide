# Adopt a decision-support system

- **Date:** 2026-08-28
- **Status:** decided
- **Type:** decision
- **Deciders:** repository owner
- **Supersedes / superseded by:** —

## Context
CCGG helped build things well but had nothing that helped decide *what* to build or
*which option* to pick: no decision records, no tool-comparison workflow, no
product-idea evaluation. Every rubric in the repo reviewed artifacts already
produced. Reversible in structure (skills and folders can be removed), but the
record format is a one-way door once records accumulate — worth deciding carefully.

## Criteria
| Criterion | Weight |
|-----------|--------|
| Covers all four decision types (product/feature, tool selection, go/no-go, idea evaluation) | 35% |
| Minimal skill-count growth; composable over overlapping | 25% |
| Survives downstream installs (no broken links, no leaked records) | 25% |
| Closes the learning loop (decisions recallable and scorable later) | 15% |

Hard constraints: must pass `tools/validate.py` (catalog sync, frontmatter, links);
must not duplicate rules single-homed in AGENTS.md or the `requirements` skill.

## Research findings
Internal survey of the repo (2026-08-28): 17 existing skills, critic-companion-file
house pattern (`architecture-critic.md`, `code-critic.md`), `install.sh` copies
`.claude/skills/` wholesale, validator fails on relative links to missing files.

## Options considered
| Option | Benefit | Cost | Risk |
|--------|---------|------|------|
| 2 skills: `/decide` + `/product-brief` | Each decision type has a clear entry; shared personas/template | 2 catalog updates | Trigger overlap with `/requirements` |
| 1 mega-skill | Single entry point | One skill doing two different jobs (choice vs. evaluation) | Bloated, hard to trigger correctly |
| 3–4 skills (per decision type) | Precise triggers | Tool-selection, go/no-go, trade-off are the same workflow | Overlap, catalog churn |
| Status quo / do nothing | Zero cost | Gap remains; decisions stay unrecorded | Rationale keeps evaporating between sessions |

Rejected early: separate `products/` folder for briefs — two indexes and two hook
greps for one concept; a `Type` field on one folder does the same job.

## Debate summary
- Champion: one universal decision shape (frame → criteria → research → debate → record) covers three of the four types → adopted as `/decide`.
- Skeptic: templates in `decisions/` would break downstream installs via dead links → answered by homing template and personas inside `.claude/skills/decide/`.
- Economist: every new skill costs four coordinated catalog edits forever → answered by stopping at two skills.
- User Advocate: idea evaluation is a different mental act than choosing between options → answered by keeping `/product-brief` separate, in front of `/requirements`.
- Operator: records without a revisit mechanism rot into folklore → answered by mandatory Revisit trigger + Outcome section in the template.

## Decision & rationale
Add exactly two skills — `/decide` (universal: tool selection, go/no-go,
prioritization, trade-offs) and `/product-brief` (idea → evaluated definition,
handing MVP specification to `/requirements` by reference) — sharing one persona
file and one record template homed in `.claude/skills/decide/`, writing to a single
`decisions/` folder with one index. Scores highest on all four criteria; the only
answered-by-mitigation risk is trigger overlap, handled by description wording and
explicit cross-routing in each skill's Step 1.

## Consequences & accepted risks
- Every future skill addition still requires the four-place catalog update (accepted; validator enforces it loudly).
- `/product-brief` vs `/requirements` routing depends on trigger phrasing (accepted; both skills cross-route explicitly).
- SYSTEM-OVERVIEW.md and install.sh skill counts are not validator-enforced and can drift (accepted; grep check documented in the skills' verification).

## Revisit trigger
After ~10 real records exist: review whether the light/full path split and the
five personas match how decisions are actually being made.

## Outcome
_To be filled when the revisit trigger fires._
