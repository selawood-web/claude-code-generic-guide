---
id: F003
title: GBB — vision-to-product design gap
status: building
owner: repository owner
target: unscheduled
---

# F003 — GBB — vision-to-product design gap

## Summary
One command, `/gbb`, takes a running app and returns a ranked Good / Better / Best
ladder: evidence-based portraits of who it is for, a stranger walk with screenshots and
a spatial map, a ten-member design council, and a timed test on every rung. Top rungs leave as feature definitions; a rerun moves the bar.

## Problem
Two projects built with this repository's process are correct, well-tested and
deployed, and the owner reports a large gap between the vision and the product as
used — layout, usability, and whether a user knows where they are. The build loop has
a gate for correctness (`tools/validate.py`, the code gate, `/ccgg-audit`) and no
gate for how the product feels. Today the only check is the owner's own reaction after
shipping, which arrives late, is one person's taste, and produces no test that a later
change can be measured against. The evidence is the owner's own report on 2026-09-18;
no measured number exists yet, which is itself the first finding.

## Outcome
An owner learns, in one run, the ten changes that would move their product from good
to spectacular, each with a number that proves when it has been reached.

- Metric: time to first success for a stranger on the primary portrait, from
  unmeasured today to measured on every run and under 60 seconds after the top three
  Better rungs ship, measured by the walk log's stranger tests
- Metric: screens on which the where-am-I test passes, from unmeasured to every
  screen in the spatial map, measured by the walk log
- Metric: ladder rungs passed per rerun, from 0 to at least 3 after one build cycle,
  measured by the score history in the product's ladder file under `design/`
- Metric: wall-clock and spend per full run on a ten-screen app, under 40 minutes
  and under 8 USD, measured by the session's own cost report

## Scope
- An owner can run `/gbb` on a named app and receive a ladder file in `design/` with, for every
  row, the Good rung as observed, a Better rung sized for one feature, a Best rung
  traced to a spectacular reference or an adjacent-field finding, and the stranger
  test that proves each
- An owner can run `/gbb --intent` before a product or surface is built and receive
  the intent file under `design/`: who it is for, the environment and its constraints, the
  feeling and anti-feeling, the references' borrowed mechanisms, and the colour, type,
  icon, layout, motion and voice decisions each with a reason and a measurable test
- A builder can treat a user-facing change as done only when the intent's tests pass
  in the running product with screenshots, and a feature for a surface names the
  intent file under Dependencies
- An owner can scope a run to one screen or flow with `--screen`, which runs three
  council members instead of ten
- An owner can run `--rerun` after changes and see every stranger test re-timed, passed
  Better rungs promoted to Good, and a new score-history row
- A council member can be edited in `design-council.md` without touching the skill
- The top three Better rungs are handed to `/feature` with the stranger test already
  written as an acceptance criterion
- The five design principles a full run derives are promoted to memory so later
  features inherit them
- A project wired with CCGG receives the skill and its companions through `install.sh`
  and `update.sh` like every other skill

## Non-goals
- Not a builder — the ladder ranks and hands off; changes ship through `/feature` and
  the ordinary code gate
- Not a product-viability verdict — `/product-brief` decides whether to build;
  GBB assumes the product exists and is worth improving
- Not a mockup critic — the full path requires the product running; a council judging
  descriptions produces a ladder nobody can verify, so that path stops and offers the
  light path on owner-supplied screenshots
- Not an automated usability lab — the stranger tests are timed by the walking agent
  adopting a portrait, not by recruited users; real user sessions would supersede
  them and are a later slice
- Not a design system generator — the principles are five sentences, not tokens or
  components

## Acceptance criteria
- Given a running app and a vision captured in Step 1, when `/gbb` completes,
  then the product's ladder file under `design/` exists with a score-history row containing a number or
  `not run` for each of the five stranger tests, every kill question answered, and at
  most ten ladder rows each carrying a Good, a Better with a test and target, and a Best
  with a cited reference or transfer
- Given a product that cannot be started in the session, when the full path is
  invoked, then the run stops before the council with a pick-list offering the light
  path on supplied screenshots, and no ladder is written
- Given an existing ladder and a rerun, when a Better rung's test meets its target,
  then that rung becomes the row's Good, the Best becomes the Better, the score history
  gains a dated row, and no rung is marked passed on the strength of a merged pull
  request alone
- Given a product with no intent file, when `/gbb` starts, then the intent is written
  before the stranger walk and the council never runs without one
- Given an intent file, when any Language decision in it is read, then it carries the
  part of the intent it was derived from and a test with a measurable pass bar
- Given the light path on one screen, when it completes, then exactly three council
  members ran, chosen from the surface table in `design-council.md`, and the ladder
  gains or updates only rows for that surface
- Given a full run with web tools unavailable, when the ladder is written, then every
  portrait, convention and competitor claim carries `[UNVERIFIED]` and no Best rung
  rests on an unverified claim alone
- Given the repository's validator, when it runs, then the skill's frontmatter carries
  the five house keys and every link in the four skill files resolves to a file
  `install.sh` copies

## Dependencies and risks
- Depends on a way to run the product and take screenshots in the session: the
  project's own run path plus a browser or simulator; Playwright and Chromium are
  present in the remote environment and must be confirmed locally on first use
- Depends on web search for Part A of the research; without it the ladder is
  conservative by rule
- Depends on subagents for a parallel council; sequential passes work but cost wall
  clock
- Risk: the council converges on the same three findings and the ladder reads as one
  reviewer. Mitigation: members are briefed with evidence only and required to
  disagree; early signal is ten identical top gaps
- Risk: "Best" collapses into taste the owner does not share. Mitigation: Best must
  trace to the owner's own spectacular references or a cited adjacent-field mechanism;
  early signal is `[UNTRACED]` Best moves outnumbering traced ones
- Risk: the stranger tests are timed by an agent and drift from real users.
  Mitigation: the numbers are reported as agent-measured and the same walk protocol is
  reused, so the delta between runs is meaningful even if the absolute value is not;
  early signal is a passed rung the owner disagrees with
- Risk: cost per full run grows with screen count. Mitigation: smaller model for the
  council fan-out, light path for single surfaces; early signal is the spend metric

## Open questions
- Should `design/` be a new top-level folder or should ladders live under `decisions/`
  with a type marker? — owner: repository owner, blocks: no
- Which of the owner's two projects is the first full run, and does it run in a
  session with a browser? — owner: repository owner, blocks: no
- Should the light path be the default when the argument names a single screen, or
  always require the flag? — owner: repository owner, blocks: no

## Ideas and changes
Append-only. Every idea raised while this work is in flight, with what was decided.

- 2026-09-18 — Name the project GBB, from the owner's motto: "good, better, best — I
  will never rest until the good is better and the better is best" — [in]
- 2026-09-18 — The council draws its members from outside software on purpose:
  wayfinding, choreography, editing, game design, cognitive science, accessibility,
  the primary portrait, brand direction, craft — [in]
- 2026-09-18 — Owner asked where the UI/UX and usability specialist is: added as the
  tenth member, the one chair from inside the interface craft, running the heuristic
  pass and owning information architecture and form design; it takes the Cognitive
  Scientist's seat in two light-path surfaces — [in]
- 2026-09-18 — The rerun promotes rungs, so the ladder never runs out of a top rung;
  this is the motto as a mechanism — [in]
- 2026-09-18 — The full path refuses to judge a product it cannot run — [in]
- 2026-09-18 — Real user sessions replacing agent-timed stranger tests — [deferred]
  until three reruns on one product show which rungs the agent's timing gets wrong
- 2026-09-18 — A visual diff of screenshots between runs as regression evidence —
  [open]
- 2026-09-18 — Owner's philosophy: nothing is built with no intended direction. Added
  the intent half — `--intent` writes the intent file under `design/` before building, in a
  designer's order of thought (who, where, feeling, references, language) and verified
  in the order the user's mind meets a screen (sense, attention, recognition, feeling,
  action); done means the tests pass in the running product, not that it renders — [in]
- 2026-09-18 — Lint that a feature touching a user-facing surface names an intent file
  under Dependencies — [deferred] until two products carry an intent and the check can
  be tested against them
- 2026-09-18 — Ladders live in a new `design/` folder, created on first use like
  `features/`, because a ladder is a living file rewritten on every rerun and a
  decision record is not — [in]
