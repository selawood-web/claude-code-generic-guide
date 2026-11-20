---
name: bonanza
description: "Find an unexpected, calculated way for a business to make money — wide idea generation, blind number and risk gates, one sharpened move with a cheap test. Not for judging an idea that already exists."
when_to_use: brainstorm, business brainstorm, out of the box, business idea, idea to make money, grow revenue, new business model, סיעור מוחות, מחשבה מחוץ לקופסא, רעיון לעסק, רעיון עסקי, רעיון לעשות כסף
argument-hint: "[the business, or the money question]"
purpose: "Money-making ideas: wide generation, blind gates, one sharpened move"
---

# Bonanza Skill

## Goal
Answer "where is the money nobody is looking at?" for a real business, and leave with
one move that is unexpected, backed by numbers, limited in what it can lose, and
explainable in one sentence.

This skill *generates*. Every other skill in the idea family starts from an idea that
already exists. Which one a request belongs to is settled before anything runs —
[`../../references/tool-choice.md`](../../references/tool-choice.md), *The idea family*.

The skill plays one character, a creative financial mind built from six components.
Each stage loads only the component it needs, and the stages are kept apart on
purpose: the part that invents never sees the part that judges.

Companion files beside this one:
- [`character.md`](character.md) — the core, the six components, the honesty contract. The only file every stage and every subagent receives.
- [`knowledge-map.md`](knowledge-map.md) — the ten knowledge domains. Intake and the logic gate.
- [`imagination.md`](imagination.md) — the twelve perception and thinking tools, the lens packs, the generator's contract. Generators only.
- [`judges.md`](judges.md) — the Logic and Caution judges and their contracts. Judges only.
- [`sharpening.md`](sharpening.md) — focus, simplicity, the one-sentence test, the story.
- [`idea-record.md`](idea-record.md) — the fact sheet, the record template, naming and the status lifecycle.

## Process

### Step 1 — Route
Run the routing question from *The idea family* when the request does not already say
what it is. A request that plainly asks for new ways to make money skips the question.
Any other answer hands the request to the skill it names, or to no skill at all.

Success: the owner's request is confirmed as a search for an idea, in their words.

### Step 2 — Intake (with the owner)
The character listens before it invents. The owner brings the market; the skill does
not pretend to know it.

- **Recall.** Read `ideas/README.md` and `ideas/business-facts.md` if they exist, then
  `decisions/README.md` and memory. A killed idea returning meets its old reason first.
- **Fact sheet.** Build or refresh `ideas/business-facts.md` per
  [`idea-record.md`](idea-record.md): what the business sells, to whom, how money comes
  in today, what it owns, what it cannot afford to lose. Every line carries one honesty
  tag from [`character.md`](character.md). Ask only for what the sheet is missing —
  as one coded pick-list, never one question a turn.
- **Question.** One sentence: the money question this run answers.

Then pick the path:
- **Light path** (a narrow question, or the owner wants a quick pass): no subagents.
  Steps 3 to 5 run in the main thread as three separate passes — generate at least
  fifteen ideas, then judge, never both in one pass.
- **Full path** (the business itself is the question): Steps 3 to 5 fan out. Say the
  size in one line — how many subagents, roughly how long — and start only on the
  owner's yes. The fan-out is the expensive part; intake alone costs almost nothing.

Success: a dated fact sheet exists, every line tagged, and the path is chosen.

### Step 3 — Diverge (generators)
Fan out one generator per lens pack in [`imagination.md`](imagination.md), as the
charter's *Efficiency* says. Each receives exactly three things: `character.md`, the
fact sheet, and its own lens pack with the generator's contract.

- A generator never receives `judges.md`, `sharpening.md`, or another generator's
  output. It does not score, rank, or discard.
- Generators run on the session's main model. Divergence is where this skill's
  judgment lives; the charter sends *mechanical* fan-out to a smaller model, and this
  is not that.
- The main thread merges exact duplicates and nothing else. No idea is dropped for
  quality here.

Success: one merged list, each idea in the contract's format, none carrying a verdict.

### Step 4 — Logic gate (blind)
A fresh subagent that did not see Step 3 receives `character.md`, the fact sheet,
`knowledge-map.md`, the Logic judge from [`judges.md`](judges.md), and the idea list
stripped of which lens produced each idea.

It tests every idea in numbers and returns the verdict the contract defines. Every
number carries an honesty tag. Most ideas die here; a gate that passes most of the
list has not been run.

Success: every idea has a pass or a kill with the number that decided it.

### Step 5 — Caution gate
The survivors go to a second fresh subagent with the Caution judge from
[`judges.md`](judges.md): the worst realistic loss, whether the move can be undone,
and the cheapest test that would show early that it is wrong.

An idea whose worst case touches what the fact sheet lists under *cannot afford to
lose* is killed, whatever its upside.

Success: each survivor has a bounded loss, a reversibility call, and a named cheap test.

### Step 6 — Sharpen (with the owner)
Back in the main thread, with [`sharpening.md`](sharpening.md). Choose one. Reduce it
to what is necessary. State it in one sentence anyone understands. Runners-up are
parked, not built alongside — two good ideas pursued together are a small business
pulled in two directions.

Success: one move passes the four rules in `character.md`, *Decision rules*.

### Step 7 — The decision is the owner's
The character recommends; it does not decide. End on a pick-list: run the cheap test,
park the idea, or kill it — recommendation first, one line of trade-off each. State
confidence and what would change the recommendation.

Success: the owner has answered with a code.

### Step 8 — Record and hand off
1. Write `ideas/YYYY-MM-DD-<slug>.md` from the template in
   [`idea-record.md`](idea-record.md), and add the index row. Ideas killed at either
   gate are kept in the record with the reason that killed them.
2. Promote what generalizes:
   ```
   remember: [finding about the business or its market] — reason: [why it outlives this run]
   ```
3. Hand off, never build here:
   - the move is a new product or app → `/product-brief` for market research and a verdict
   - two finalists the owner cannot choose between → `/decide`
   - the move is a capability in a product that exists → `/feature`

Success: the record exists, is indexed, and names where the idea went next.

## Anti-Patterns to Avoid

| Anti-pattern | Correct approach |
|--------------|-----------------|
| Inventing and judging in one pass | Separate passes, separate context — judgment censors invention |
| Generating before listening | Intake first; the owner brings the market |
| A number with no tag | Every number is `[known]`, `[assumed]` or `[hoped]` |
| Letting a strong feeling outvote the numbers | Intuition generates and sharpens; it does not decide |
| Shipping the three best ideas | One move; the rest are parked with a reason |
| Fanning out on auto-invoke | Intake only, until the owner says yes to the full path |
| Dropping killed ideas | The record keeps them and why — or they return in six months |
| Deciding for the owner | Recommend, name the cheap test, end on a pick-list |

## Knowledge Extraction
Beyond the chosen move, save what the run taught about the business:
```
remember: [what customers actually pay for, or an asset the business did not count] — reason: [why it matters next time]
```
