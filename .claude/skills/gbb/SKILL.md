---
name: gbb
description: Close the gap between a product's vision and what it actually feels like to use. Researches who the app is for and how they use it, walks the running product as a stranger, convenes a council of design minds from different disciplines, and returns a ranked Good / Better / Best ladder with a re-runnable test per rung. Use when the user says "GBB", "make this spectacular", "the UX is only good enough", "design review", or "why does it feel worse than the vision".
when_to_use: GBB, good better best, make it spectacular, design gap, UX review, design review, feels worse than the vision, usability, orientation, polish
argument-hint: "[app name, path, or URL] [--intent | --rerun | --screen <name>]"
purpose: "Vision-to-product design gap: research, stranger walk, design council, GBB ladder"
---

# GBB — Good, Better, Best

*"I will never rest until the good is better and the better is best."*

## Goal
A product that works is not a product that is spectacular. The build loop — spec,
code, tests, ship — has a gate for *correct* and none for *how it feels*: whether a
stranger knows where they are, what to do next, how to get back, and whether the thing
has a point of view. GBB is that gate. It takes an app, finds out who it is really
for, walks it the way they would, puts it in front of a council of design minds from
outside software, and returns a **ladder**: for every moment that matters, what is there
(Good), the next concrete step (Better), and the version that would make someone tell
a friend (Best) — each rung with a test that can be re-run after every change.

GBB has two halves. **Intent** runs before anything is built: who the product is for,
the environment it is met in, the feeling it must leave, and the colour, type, icons,
layout, motion and voice derived from those, each with a reason and a test — in
[`design-intent.md`](design-intent.md). **The ladder** runs on the built product and
measures the gap from that intent. Nothing is built with no intended direction, and
nothing is done until the intent's tests pass in the running product.

This skill judges and ranks; it does not build. The moves it produces become
`/feature` definitions with the acceptance test already written, so the ordinary build
loop picks them up. It does not decide whether the product should exist — that is
`/product-brief` — and it does not write the spec — that is `/requirements`.

Companions in this directory:
- [`design-intent.md`](design-intent.md) — the intent written before building: who, where, feeling, language, tests
- [`research-protocol.md`](research-protocol.md) — who it is for, context of use, the stranger walk, the spatial map
- [`design-council.md`](design-council.md) — the ten council members and their output contract
- [`gbb-ladder.md`](gbb-ladder.md) — the ladder record: template, scoring, the stranger tests
- [`design-ownership.md`](design-ownership.md) — CODEOWNERS and the pull-request checklist that make the intent enforceable in a project

## Modes
| Invocation | Path | What runs |
|------------|------|-----------|
| `/gbb --intent <product or surface>` | intent | writes or revises `design/INTENT-<slug>.md` before anything is built |
| `/gbb <app>` | full | every step below |
| `/gbb --screen <name>` | light | Steps 1 and 3 on one screen or flow, three council members, a ladder for that surface only |
| `/gbb --rerun` | rerun | Steps 3, 6 and 7 against the existing ladder — re-scores every rung, promotes what passed |

The light path is the default for a single screen or a change already in review;
the full path is for a product, a release, or the first run. Say which path in one line.

## Process

### Step 1 — Vision capture
Find the vision before measuring the gap from it. Read `design/INTENT-<slug>.md`
first — if it does not exist, write it now via the intent mode, because a council
judging a product with no stated direction judges against its own taste. Then
`design/GBB-<slug>.md` if it exists (a rerun starts from it), `decisions/`,
`features/`, README, and any design doc. What must be written down, in the owner's words where possible:
- **North star** — one sentence: what this product is for, and for whom.
- **The feeling** — three words the owner wants a user to have after five minutes.
- **The moments** — the three moments that decide whether it is loved: usually first
  open, the core action, and the first time something goes wrong.
- **Spectacular references** — two or three products, from any field, the owner
  considers spectacular, and *why*. These calibrate "Best"; without them, Best means
  the model's taste, not the owner's.

Missing pieces get at most three questions, asked as a pick-list where options are
inferable. Do not invent a vision; a vision guessed is a gap measured from nowhere.

### Step 2 — Field research (full path; mandatory)
Run [`research-protocol.md`](research-protocol.md), Part A. Live search, never memory
— the charter's Currency rule; cache and reuse per
[`../decide/research-cache.md`](../decide/research-cache.md). What comes back:
- **Who, from evidence** — two or three user portraits built from reviews, forum
  complaints, and support threads of competing or adjacent products, not from
  imagination. Each carries what they were doing when they reached for the app.
- **Context of use** — device, posture, light, one hand or two, interrupted or
  focused, calm or stressed. A ladder for a desk is wrong for a kitchen.
- **Platform conventions** — the current human interface guidelines, Material,
  WCAG level, and system gestures the product must not fight.
- **Best-in-class from adjacent fields** — how a museum, an airport, a cockpit, a
  game tutorial, or a well-run restaurant solves *this product's* hardest moment.
  This is where "out of the box" is manufactured on purpose rather than hoped for.
- **Competitor teardown** — the two nearest products, one screen each for the same
  three moments, and the one thing each does better than us.

Web tools unavailable → say so, tag every claim `[UNVERIFIED as of model knowledge
cutoff]`, and keep the ladder's Best rungs conservative.

### Step 3 — The stranger walk (evidence, not description)
Run [`research-protocol.md`](research-protocol.md), Part B. Start the product for
real — the project's own run instructions, a Playwright script, a device simulator —
and walk it with no instructions, as the primary portrait from Step 2, at every state:
- Screenshot every screen and every state reached: empty, loading, error, success,
  first-run, populated. Council members critique pixels, not prose.
- Build the **spatial map**: every screen, how you reach it, how you get back, and
  what on the screen tells you where you are. Mark every place the walk got lost,
  hesitated, or backed out.
- Time the **stranger tests** from [`gbb-ladder.md`](gbb-ladder.md): first
  success, where-am-I, back-out, recovery, one-hand. These are the numbers the ladder
  moves.

If the product cannot be run, say so and stop the full path: a council judging
mockups produces a ladder nobody can verify. Offer the light path on screenshots the
owner supplies instead.

### Step 4 — The design council
Run the members in [`design-council.md`](design-council.md) against the vision, the
research, the screenshots and the spatial map. Parallel subagents on a smaller model
when available, sequential passes fully adopting one member at a time otherwise
(never blended). Each member returns its three ranked gaps, one Best move, and one
kill question, per the contract in that file. The full path runs all ten; the light
path runs the three whose discipline the surface calls for, named in the file.

### Step 5 — Kill questions first
Before synthesis, answer every kill question in one line each. A kill question that
cannot be answered is the top row of the ladder regardless of what else the council
found — it is the thing that makes the rest not matter.

### Step 6 — The ladder
Synthesize into `design/GBB-<slug>.md` from [`gbb-ladder.md`](gbb-ladder.md):
- One row per moment or surface. **Good** is what is there now, stated honestly.
  **Better** is a change small enough for one feature. **Best** is the spectacular
  version, traced to a spectacular reference or an adjacent-field finding — never
  "more polish". A rung that contradicts the intent either loses or revises the
  intent with a dated ledger entry.
- Every rung carries its stranger test and the number that proves it was reached.
- Rows ranked by reach × impact / effort. The top ten are the ladder; the rest are
  the backlog section, kept so a rerun can promote them.
- **Design principles** — five sentences the product now obeys, derived from what
  the council agreed on. Future features inherit them, which is how the gap stops
  reopening.

### Step 7 — Rerun: the bar moves
On `--rerun`, re-time every stranger test and re-score every rung. A Better that
passed becomes the row's new Good, and the old Best becomes the new Better — then the
council's one Best move for that row is asked for again. This is the mechanism behind
the motto: the ladder never runs out of a top rung. Record the score delta at the top
of the file with the date.

### Step 8 — Handoff and record
- The top three Better rungs become `/feature` definitions, each with the stranger
  test copied in as an acceptance criterion and the intent file named under
  Dependencies; the change is done when the intent's tests for that surface pass in
  the running product, with screenshots. Post to the tracker per the charter's
  channel rule; render, do not post, anywhere else.
- On a project's first intent, offer the CODEOWNERS file and the pull-request
  checklist from [`design-ownership.md`](design-ownership.md) as a pick-list.
- Add the ladder to `design/README.md`'s index (create both on first use, like
  `features/`).
- Promote the design principles to memory:
  ```
  remember: <product> design principles — <five, one line> — reason: every future feature inherits them
  ```

## Ending
Full path ends as a next step: the ladder path and the one `/feature` to open first.
Light path ends as Done with the row it produced. A run that could not start the
product ends as a pick-list: supply screenshots for the light path, or fix the run
path first.

## Anti-patterns

| Anti-pattern | Correct approach |
|--------------|-----------------|
| Building a surface with no written intent | `--intent` first; a feature touching a surface names the intent file |
| Done when it renders | Done when the intent's tests pass in the running product, with screenshots |
| Judging the spec or a description of the app | Step 3 runs the product; the council sees screenshots |
| Portraits from imagination | Step 2 builds them from evidence, cited |
| "Best" meaning more of the same polish | Best traces to a spectacular reference or an adjacent field |
| A ladder with no numbers | Every rung has a stranger test and a measurement |
| One design voice | Ten disciplines, each with a kill question the synthesis must answer |
| The ladder as a report | The top three Better rungs leave as `/feature` definitions |
| Running once | `--rerun` moves the bar; the ladder is a living file in `design/` |

## Knowledge extraction
Adjacent-field findings outlive the product they were found for:
```
remember: [field] solves [orientation/feedback/recovery problem] by [mechanism] — reason: [where it transfers]
```
