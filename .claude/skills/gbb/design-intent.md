# Design Intent — nothing is built without a direction

The philosophy in one line: **nothing is built with no intended direction.** Before the
first screen exists, the product has a written intent — who it is for, the environment
it will be met in, the feeling it must leave, and the concrete language (colour, type,
icons, layout, motion, voice) chosen *from* those, each with a reason and a test. The
ladder in [`gbb-ladder.md`](gbb-ladder.md) measures what *is*; the intent says what
*should be*. The gap GBB closes is the distance between the two, and without an
intent there is nothing to measure the gap from.

The intent is a living file: `design/INTENT-<slug>.md`, indexed from
`design/README.md`. It is written in the order a designer's mind works — the
person first, the pixels last — and verified in the order the user's mind meets a
screen — sense, attention, recognition, feeling, action.

## When it runs
- **Before building** a new product, or a feature that adds a user-facing surface:
  `/gbb --intent <product or surface>`. Full path for a product; light path — the
  same order of thought, one surface, the Language section only where it deviates
  from the product intent — for a feature.
- **Before a ladder** — Step 1 of [`SKILL.md`](SKILL.md) reads the intent first; a
  product without one gets the intent written before the walk, because a council
  judging a product with no stated direction judges against its own taste.
- **On a rerun** — a Best rung that contradicts the intent either loses, or the intent
  is revised with a dated ledger entry. The intent changes on purpose, never by drift.

## The order of thought

Each part answers one question and feeds the next. A part that cannot be answered
from evidence is answered from the owner, as a pick-list, and tagged `[ASSUMED]`
until evidence replaces it.

### 1. Who — the person, not the segment
The primary portrait from [`research-protocol.md`](research-protocol.md) A1, plus
three things the language must serve:
- **What they carry in their head** — how much map, how many numbers, which words.
- **What they are afraid of** — losing work, looking foolish, being slow, being wrong.
  The feeling in Part 3 is chosen against this fear.
- **What they already know** — the products, conventions and vocabulary they arrive
  with. The language borrows from these before it invents.

### 2. Where and when — the environment that gives the best feel
The context table from A2, turned into constraints. This is where "which environment
gives the best feel" is answered from evidence rather than preference:

| Context finding | Constraint on the language |
|-----------------|----------------------------|
| Bright light, outdoors | High contrast, no thin type, no colour-only meaning, dark mode is not the default |
| Dim light, evening use | Dark surfaces, warm accents, lower luminance contrast for long reading |
| One hand, standing or walking | Primary action in the thumb zone, large targets, no precision gestures |
| Interrupted every minute | Every screen self-titled, state survives leaving, one step per screen |
| Long focused sessions | Higher density is allowed, keyboard paths, quieter chrome |
| Stress, hurry, pain | Fewer choices, larger type, calm colour, error copy that says what to do |
| Noise, gloves, wet hands | No sound-only feedback, oversized targets, no hover-only affordances |

Write the constraints that apply as sentences. They are the reasons the Language
section will cite.

### 3. The feeling — and the anti-feeling
Three words for what the person feels after five minutes, and three for what it must
never feel like. "Calm, capable, cared for" is a direction; "not clinical, not
childish, not loud" is a fence. Both are needed: the anti-feeling is what stops a
good choice being dragged into a wrong one by a reference.

Map each feeling word to the parts of the language that carry it, so a later change
to a colour or a typeface can be checked against the word it was chosen for.

### 4. The references — borrowed mechanisms, not moods
The owner's spectacular references from vision capture and the adjacent-field
transfers from A4. For each: the **one** mechanism borrowed and the sentence that
says how it appears here. A reference with no named mechanism is a mood board and is
dropped.

### 5. The language — every choice with a reason and a test
The concrete decisions. Each row is a decision, the reason traced to Parts 1–4, and
the test that proves it in the running product. A choice without a reason is
decoration; a choice without a test is a hope.

**Colour**
- Roles, not swatches: background, surface, text, primary action, secondary action,
  danger, success, warning, focus. One accent. Dark and light variants of every role.
- Reason: from Part 2 (light) and Part 3 (feeling); name which.
- Tests: text contrast at least 4.5:1 and interface contrast 3:1 against every
  surface it appears on, measured, not eyeballed; the same screen through
  deuteranopia and protanopia simulation with every meaning still readable; every
  status also carried by shape or text; the core screen in the lighting from Part 2.

**Type**
- One family, two at most; a scale of no more than four sizes on any one screen;
  line length 45–75 characters; weights and their meanings.
- Reason: from Part 1 (what they read, how fast) and Part 3.
- Tests: readable at the portrait's real viewing distance — arm's length on a phone,
  further on a wall-mounted tablet; the largest system text size breaks no layout;
  the squint test — blurred, every screen still shows exactly one headline.

**Icons**
- The set and its style (outline or filled, stroke weight, corner radius), when an
  icon is labelled (always, for any action with a consequence), and the metaphors that
  are off limits because the portrait would not recognise them.
- Reason: from Part 1 (what they already know).
- Tests: recognition — five portraits, adopted one at a time, name the icon's action
  without its label; four of five must agree; no unlabelled icon on the core path.

**Layout and spacing**
- The grid, the spacing scale, the reach map for the device (thumb zone, stretch zone,
  dead zone), the density rule from Part 2, and the one persistent landmark that
  anchors orientation.
- Reason: from Part 2 (hands, attention).
- Tests: the primary action inside the thumb zone on every core screen; the
  one-hand stranger test; the where-am-I test on every screen.

**Motion**
- Durations (responses under 100 milliseconds, transitions under 300), easing,
  what moves and what never moves, the reduced-motion version of each.
- Reason: from Part 3 and the Choreographer's rule of continuity.
- Tests: every touch answered visibly within a tenth of a second; reduced-motion
  setting honoured with no lost information; nothing moves that the user did not cause
  or is not waiting for.

**Voice and copy**
- Person and tense, the tone in one sentence, the error formula — what happened,
  what to do, in that order — the empty-state formula, and the words never used.
- Reason: from Part 1 (their vocabulary) and Part 3.
- Tests: every error message read aloud says what to do next; every label on the
  core path is a word from the portrait's vocabulary; no screen holds more words than
  the portrait would read in the attention window from Part 2.

**Sound and haptics** — if any
- When each fires, and why it earns its interruption.
- Test: the product is complete with sound off.

**The signature**
- The one distinctive decision, consistently kept, that the Brand Director's kill
  question asks for. Named here so every later feature carries it.

### 6. The rules the build obeys
Five sentences a builder can follow without reading the rest — the design principles.
They are the same five the ladder promotes to memory; a full `/gbb` run may revise
them, a rerun may not.

### 7. The tests — testing, not just executing
A user-facing change is **done when the intent's tests pass in the running product**,
with a screenshot as evidence — not when the code runs, not when the pull request is
green. The tests from Part 5 are collected into one table, grouped by how the user's
mind meets the screen:

| Layer of the mind | What it meets | Tests from Part 5 |
|-------------------|---------------|-------------------|
| Sense — the first tenth of a second | Colour, contrast, shape, density | contrast, colour-blind simulation, lighting check, squint test |
| Attention — the first second | Where the eye lands, what moves | one headline, motion causes, response time |
| Recognition — the first five seconds | Icons, patterns, where am I | icon recognition, landmark, where-am-I, platform conventions |
| Feeling — the first minute | Tone, pace, calm or alarm | anti-feeling review, voice read-aloud, reduced motion |
| Action — the first task | Affordance, reach, feedback, recovery | thumb zone, one-hand, first success, recovery, error copy |

Each test is written with its pass bar and run in the code gate's requirement stage
for any change touching a surface; the screenshots go to `design/walks/<date>/`. A
feature definition for a user-facing surface names this file under Dependencies and
copies the tests its surface touches into its acceptance criteria.

## Template

Copy the whole block; delete nothing.

```markdown
# Design intent — <Product or surface>

- **Slug:** <slug>
- **Status:** draft | active | revised YYYY-MM-DD
- **Ladder:** [GBB-<slug>.md](GBB-<slug>.md), once one exists

## 1. Who
<primary portrait, one line> — from [research](../knowledge-base/research/gbb-<slug>.md)
- Carries in their head: …
- Afraid of: …
- Already knows: …

## 2. Where and when
| Finding | Constraint |
|---------|------------|
| … | … |

## 3. The feeling
- **Feels:** <word> · <word> · <word>
- **Never feels:** <word> · <word> · <word>
- <word> is carried by: <colour role / type weight / motion / voice>

## 4. References
| Reference | Mechanism borrowed | How it appears here |
|-----------|-------------------|---------------------|

## 5. The language
### Colour
| Role | Light | Dark | Reason (Part) |
|------|-------|------|---------------|
Tests: …
### Type
…
### Icons
…
### Layout and spacing
…
### Motion
…
### Voice and copy
…
### Sound and haptics
…
### The signature
…

## 6. The rules the build obeys
1. …
5. …

## 7. Tests
| Layer | Test | Pass bar | Last run | Result |
|-------|------|----------|----------|--------|

## Ledger
Append-only, dated. Every revision of a decision above, with why.
- YYYY-MM-DD — <decision changed> — because <evidence> — [revised]
```

## Anti-patterns

| Anti-pattern | Correct approach |
|--------------|-----------------|
| Choosing colours and fonts first | Parts 1–4 first; the language is derived, and each row cites its part |
| A palette with no roles | Roles with light and dark variants; a swatch list is not a decision |
| A feeling with no anti-feeling | Both, so a reference cannot drag the direction |
| Tests that say "looks right" | Measured contrast, timed responses, named portraits agreeing on an icon |
| Done when it renders | Done when the Part 7 tests pass in the running product, with screenshots |
| Intent revised by whoever last touched the CSS | Revised only with a dated ledger entry and a reason |
