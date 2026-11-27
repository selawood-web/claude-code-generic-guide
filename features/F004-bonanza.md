---
id: F004
title: Bonanza — finding the money idea
status: building
owner: repository owner
target: unscheduled
---

# F004 — Bonanza — finding the money idea

## Summary
One command, `/bonanza`, searches for an unexpected, calculated way for a business to
make money. Generators invent without judging, two blind gates test numbers and risk,
and the owner leaves with one move in one sentence, a cheap test, and a record. A
routing question keeps the idea-family skills from running for nothing.

## Problem
The owner runs a small software business and uses this repository's process on every
project. The process can evaluate an idea (`/product-brief`), choose between options
(`/decide`) and define a capability (`/feature`). Nothing in it *produces* an idea, so
that step happens in open conversation, where one voice invents and judges in the
same breath and the cautious, average idea wins. The evidence is the owner's own
session of 2026-11-20: a creative financial character was specified by hand, in
six components, across one long session, precisely because no skill held it. A second finding
from the same session: the trigger words for an idea — "brainstorm", "I have an
idea" — overlap across five skills, and the owner asked for a rule so that none of
them runs for nothing. No measured number exists yet for either problem.

## Outcome
An owner gets, in one run, one money-making move that passed a number gate and a risk
gate it could not influence, with the cheapest test that would prove it wrong.

- Metric: ideas reaching the logic gate per full run, from 0 (no generation step
  exists) to at least 30 after duplicates are merged, measured by the run's record
  under `ideas/`
- Metric: figures in a record that carry an honesty tag, target 100 percent, measured
  by reading the record's *The numbers* table
- Metric: runs of an idea-family skill that the owner stops as the wrong skill, target
  0 per 10 invocations, measured by the owner's report — not yet measured
- Metric: wall clock and spend per full run, target under 20 minutes and under 5 USD,
  measured by the session's own cost report — a target, not yet measured

## Scope
- An owner can run `/bonanza` on a business or a money question and receive one move
  stated in one sentence, with its deciding number, worst realistic loss, and cheapest
  test
- An owner can take a light path that runs in one thread with no subagents, or a full
  path that fans out, and the full path starts only after the owner says yes to its
  stated size
- An owner answers intake questions once: the answers are kept in the fact sheet under
  `ideas/` and refreshed, not asked again, on the next run
- An owner can see every idea a run killed and the reason, in that run's record, and
  every runner-up as parked with what would bring it back
- An owner decides: the skill ends on a pick-list — run the cheap test, park, or kill —
  and never chooses for them
- A chosen move is handed to `/product-brief`, `/decide` or `/feature`; the skill
  builds nothing
- A component of the character can be edited in its own companion file without
  touching the skill's process
- An owner whose request does not say what kind of idea work it is gets one routing
  question, once, before any idea-family skill starts — and no question when the
  request already says
- A project wired with CCGG receives the skill and its companions through `install.sh`
  and `update.sh` like every other skill

## Non-goals
- Not an evaluator of an idea that already exists — that is `/product-brief`
- Not a chooser between named options — that is `/decide`
- Not a builder or a spec writer — the move leaves as a hand-off
- Not a source of market facts — the owner brings the market at intake; a run without
  the owner's knowledge is refused rather than filled with generic ideas
- Not a guarantee of revenue — the skill raises the odds of an unusual, tested idea
  and says plainly when no idea survives both gates
- Not a persona for ordinary conversation — the character lives inside the skill's
  stages and is not loaded into every session
- Not six skills — the components do not work alone, and six descriptions would be
  paid for in every session

## Acceptance criteria
- Given a request that names a business and asks for ways to make money, when
  `/bonanza` runs the full path, then a record exists under `ideas/` with one move in
  one sentence, a numbers table in which every row carries `[known]`, `[assumed]` or
  `[hoped]`, a worst realistic loss, a reversibility call, a cheap test, and a section
  listing every killed idea with the judge and reason that killed it
- Given the skill woke on a trigger phrase without the command being typed, when
  intake completes, then no subagent has been started and the reply ends on a
  pick-list that waits for the owner's yes to the full path
- Given a generator subagent, when it is briefed, then it receives the character file,
  the fact sheet and one lens pack, and its return contains no score, ranking, risk
  assessment or recommendation
- Given an idea whose worst case reaches a line under *Cannot afford to lose* in the
  fact sheet, when the Caution judge returns, then the idea is killed and no later
  step revives it
- Given no idea survives both gates, when the run ends, then it says so, records what
  was learned, and names no winner
- Given a request that says only "let's brainstorm", when any idea-family skill is
  about to start, then one pick-list of at most four coded options is asked once and
  nothing runs until a code arrives
- Given a request that says "give me ways to grow revenue", when `/bonanza` is about
  to start, then no routing question is asked
- Given the repository's validator and unit tests, when they run, then the skill's
  frontmatter carries the five house keys, every link in the seven skill files
  resolves to a file `install.sh` copies, and `tools/test_bonanza.py` passes

## Dependencies and risks
- Depends on subagents for the full path; without them the light path runs the same
  stages as separate passes in one thread, with weaker isolation between inventing
  and judging
- Depends on the owner for the market. Risk: a thin fact sheet produces ideas that fit
  any business. Early signal: ideas whose *Rests on* line cites no `[known]` fact
- Risk: generators converge on the same handful of ideas and the run reads as one
  voice. Mitigation: one lens pack per generator, no shared output. Early signal: more
  than half the merged list is duplicates
- Risk: the Logic judge invents numbers with confidence. Mitigation: the honesty tags,
  and an untagged number counts as `[hoped]`. Early signal: a record whose deciding
  numbers are all `[assumed]`
- Risk: the routing question becomes a nuisance and gets skipped. Mitigation: it is
  never asked when the request already says what it is, and it is asked once
- Risk: generators run on the main model, which departs from the charter's default
  for fan-out and costs more. The reason is stated in the skill; the cost metric above
  is what would reverse it
- The rule's home is `.claude/references/tool-choice.md`; the five family skills point
  at it and do not restate it

## Open questions
- Do generators keep the main model after the first three real runs, or move to the
  smaller one? — owner: repository owner, blocks: no
- Does the fact sheet belong under `ideas/`, or beside the project's other standing
  facts once a second skill needs it? — owner: repository owner, blocks: no

## Ideas and changes
- 2026-11-20 — Honesty raised by the owner as a critical component of the character — [in] made the floor under every stage: three tags on every fact and number, not a stage of its own
- 2026-11-20 — Focus, simplicity and story, taken from a second character the owner supplied — [in] added as the sixth component, Sharpening, with a one-sentence rule in the decision rules
- 2026-11-20 — Trusting a strong feeling against the data, from the same second character — [dropped] it contradicts caution and honesty; intuition generates and sharpens, it does not decide
- 2026-11-20 — Tools given as examples narrowed the character's thinking — [in] the imagination tools are stated as ways of seeing and moving, with no examples, and the file says not to add any
- 2026-11-20 — Idea-family skills must ask what the request relates to before running — [in] one routing question, single-homed in the Skill Checker
- 2026-11-20 — Routing question drafted with six options — [in] cut to four, the pick-list maximum; `/decide` announces itself and `/requirements` is reached through `/feature`
- 2026-11-20 — Other skills waking this one, for example after a No-go verdict from `/product-brief` — [deferred] until the first real runs show whether a No-go usually wants a new search
- 2026-11-20 — Whether `/bonanza` joins the context guard's heavy-skill list — [in] added. The full path orchestrates six subagents and merges their returns, the pattern the guard was written for, and `/product-brief` in the same family is already listed. The block is once, on a typed command, over 100k tokens; a skill that woke by itself is not affected
- 2026-11-20 — Surface idea records still in `proposed` or `testing` at session start, the way open decisions are — [deferred] until the first records exist; a move left in `testing` with nobody reminded is the failure it would prevent
- 2026-11-20 — A fresh headless session to prove the routing question fires — [deferred] until a runner with credentials is available; the attempt from the build session failed on authentication, so the three routing criteria above are checked by hand on the first real run
- 2026-11-20 — [in] Built on `claude/bonanza-skill`. [verified] validator clean, catalog current, unit tests pass, feature lint clean. [not exercised from this seat] a real full-path run with subagents on a real business, and auto-invocation from a trigger phrase in a fresh session
- 2026-11-20 — [in] Routing checked after the merge, with three fresh subagents standing in for new sessions, each given one owner message and nothing else. [verified] "let's brainstorm" produced one waiting pick-list of four coded options and ran nothing; "give me ways to grow revenue for my small software business" started `/bonanza` with no routing question and stopped at intake with no idea generated; "let's brainstorm the layout of the settings screen" loaded no skill. [not exercised from this seat] the same three typed by the owner in the real app, where the headless runner still fails on authentication; and a full-path run with real generators and judges, which the probes were not allowed to start
- 2026-11-26 — Status reviewed against the acceptance criteria: stays `building`. Shipping
  needs a real full-path run that leaves a record under `ideas/`, and a fresh headless session proving the routing question fires. Neither has run — [deferred] until that run exists
