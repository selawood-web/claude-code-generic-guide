# Product brief — "Shop OS" for small cabinet & furniture shops

- **Date:** 2026-08-28
- **Status:** decided
- **Type:** product-brief
- **Deciders:** selawood (confirmed 2026-08-28)
- **Supersedes / superseded by:** —

## Context
Session research into the woodworking industry surfaced three app candidates; this
brief evaluates the strongest: an affordable web app for 1–5 person cabinet and
custom furniture shops combining material-aware quoting, job costing, material +
offcut inventory, and cut optimization, with an AI photo-to-quote engine pitched as
the flagship feature. Trigger: an observed market gap (not a personal pain), which
raises the evidence bar — no firsthand user to validate against. Reversible
decision; stakes are 1–2 builders' time for several months.

## Criteria
| Criterion | Weight |
|-----------|--------|
| Problem is real and users will pay | 35% |
| Differentiation survives contact with incumbents | 25% |
| Buildable + operable by a 1–2 person team | 20% |
| Distribution is reachable (CAC vs LTV) | 20% |

Hard constraints: small team, no enterprise sales motion, subscription pricing.

## Research findings
See [knowledge-base/research/woodworking-shop-software-market.md](../knowledge-base/research/woodworking-shop-software-market.md)
(as of 2026-08-28). Key facts: ~6,000 US cabinet manufacturers (~$9B revenue) plus a
long tail of solo makers; Cabinet Vision ~$30k and disliked; Mozaik $95–295/mo with a
training-gated learning curve; Allmoxy from ~$65/mo; cut optimization commoditized by
free tools; contractor tools (JobTread/Buildxact) not material-aware; pricing work is
the trade's admitted #1 business pain; four small 2025–26 entrants (JoineryCore,
EZNESTING, ProCabinet.App, Cutlistor) attack slices of the same gap. Caveat: the
clearest articulation of the gap comes from a competitor's marketing blog.

## Market landscape
The gap between "spreadsheets + QuickBooks" and "$30k CAM suite" is real and
newly contested. Nobody closes the full loop customer-request → material cost →
quote → actual margin; entrants each own one slice. Differentiation of the
deterministic core is execution speed and onboarding ease, not concept novelty;
the AI photo-to-quote concept is unique but unproven anywhere in the market.

## Options considered
| Option | Benefit | Cost | Risk |
|--------|---------|------|------|
| Build Shop OS, AI photo-to-quote flagship | Unique wedge; closes full loop | Highest R&D + accuracy engineering | Wrong quotes destroy trust in the whole app |
| Build deterministic core first, AI as labeled draft estimator later | Fast time-to-revenue; safe to operate | Launches as 5th entrant in the slice war | Differentiation deferred |
| Don't build (do nothing) | Zero cost | Misses a validated, monetizable pain | The full-loop category gets owned by an entrant |

Rejected early: lumber/slab marketplace (two-sided liquidity risk, weakest fit for a
1–2 person team); standalone AI plan generator (already crowded with hobbyist toys).

## Debate summary
- Champion: full-loop data compounds per customer; window closing as entrants converge → accepted, drives Go-shaped verdict.
- Skeptic: differentiator and trust model in direct conflict — a wrong AI quote causes the #1 pain it promises to fix → answered by demoting AI from flagship to draft estimator.
- Economist: distribution economics may never close (offline niche, ~$540k ARR ceiling at heroic capture) → accepted as named risk; staged spend mitigates.
- User Advocate: photo-to-quote is the builder's interesting problem; the shop's problem is margin visibility and faster quoting with QuickBooks sync → accepted, reorders the roadmap.
- Operator: AI-priced quotes are an uninsured liability a 1–2 person team can't carry; only operable shape is deterministic core + confirmed-line-by-line draft → accepted, sets the product shape.

Tension: Champion says the AI wedge is the moat; the other four say it cannot lead.
Resolved by sequencing — the moat argument survives as a later, retention-gated bet.

## Verdict: Pivot
The problem is real and worth building; the pitched shape is wrong. Four of five
personas independently converged on the same reshape:

**Build the deterministic core as the product** — quoting, job costing (quoted vs
actual margin), material/offcut inventory, cut optimization, QuickBooks sync, with
onboarding finishable in one evening. **Demote AI photo-to-quote to a clearly
labeled draft estimator** (spec + materials draft the owner confirms line by line,
never an autonomous price), funded only after retention data proves the core
sticks. Differentiate on closing the full loop and on onboarding speed, not on AI.

Core reason: every quote is a commercial commitment; a photo underdetermines what
drives its price, so an AI-led quote fails exactly where user tolerance is lowest.

## MVP definition
Spec: [specs/2026-08-28-shop-os-mvp-requirements.md](../specs/2026-08-28-shop-os-mvp-requirements.md)
(the brief holds *why build*; the spec holds *what*). The value-testing slice: a shop enters
its hourly rate + material price list in under one evening, produces a branded quote
faster than its spreadsheet, and sees quoted-vs-actual margin on its first completed
job. Deployable from the first milestone (deploy-steward owns that).

## Consequences & accepted risks
- Accepted (Economist): niche TAM with offline distribution; this is a solid-margin
  lifestyle-scale business unless the long tail of makers proves reachable.
- Accepted (Skeptic): launching the core means competing with four early entrants;
  the bet is execution and full-loop scope, not concept exclusivity.
- Committed: shop-entered prices are the system of record; AI outputs are always
  drafts requiring confirmation; data export is a day-one obligation.

## Revisit trigger
- Verdict confirmation by the owner turns status → decided.
- Re-verify volatile pricing facts after ~2026-09-27 if work hasn't started.
- The deferred AI bet reopens when the core shows ≥3-month retention on paying shops.
- No-go reopens if a competitor ships a trusted full-loop product first.

## Outcome
[Empty — filled when a revisit trigger fires.]
