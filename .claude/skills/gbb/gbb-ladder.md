# The GBB Ladder — record template, scoring and the stranger tests

The ladder is the product's living design file: `design/GBB-<slug>.md`, indexed from
`design/README.md`, created on first use. One row per moment or surface; three rungs
per row; a test and a number on every rung. It is rewritten on every `/gbb --rerun`
and never deleted — the score history at the top is the record that the bar moved.

## The stranger tests

Five timed tasks, run by the primary portrait during the walk and again on every
rerun. Each has a pass bar; the ladder's rows say which test proves each rung.

| Test | Task | Measured | Pass bar |
|------|------|----------|----------|
| **First success** | From a cold start, complete the core action with no instructions | Seconds, and the count of wrong taps | Under 60 seconds and no more than two wrong taps, unless the vision sets a tighter bar |
| **Where am I** | Interrupted three screens deep, return after a minute and name the screen | Correct or not, and seconds to answer | Correct within 3 seconds, on every screen in the map |
| **Back out** | From the deepest screen, return to the start without the system back gesture | Taps, and whether any landed somewhere unexpected | No dead end; every tap goes where the body expected |
| **Recovery** | Provoke the most likely error, then finish the task anyway | Seconds from error to completion; whether the entered work survived | Work survives; recovery under 20 seconds; the error says what to do |
| **One hand** | Complete the core action with one thumb at the largest text size | Completed or not; targets missed | Completed; no target missed twice |

Numbers from a walk are reported as measured, with the moment where the time went.
A test the product cannot be put through is reported as **not run**, never as passed.

## Scoring a row

```
score = reach × impact / effort
```
- **reach** — 1 to 3: how many portraits hit this moment, and how often.
- **impact** — 1 to 3: how far the Better rung moves its stranger test.
- **effort** — 1 to 3: the Better rung's size, where 1 fits one feature definition.

The top ten rows by score are the ladder. The rest are the backlog section, ranked
the same way, kept so a rerun can promote them.

## Template

Copy the whole block; delete nothing.

```markdown
# GBB — <Product>

- **Slug:** <slug>
- **North star:** <one sentence, the owner's words>
- **The feeling:** <three words>
- **The moments:** <first open · core action · first failure — or the owner's three>
- **Spectacular references:** <product — why>; <product — why>
- **Primary portrait:** <one line>, from [research](../knowledge-base/research/gbb-<slug>.md)

## Score history
| Date | First success | Where am I | Back out | Recovery | One hand | Rungs passed |
|------|---------------|------------|----------|----------|----------|--------------|
| YYYY-MM-DD | 84s / 3 wrong | 6 of 9 screens | dead end at S07 | work lost | 2 targets missed | 0 of 10 |

## Design principles
Five sentences the product now obeys. Every future feature inherits them.
1. <principle — the council finding it came from>
2. …

## Kill questions
| Member | Question | Answer | Row |
|--------|----------|--------|-----|
| Wayfinder | <question> | No — S04, S07, S09 carry no title | 1 |

## The ladder
Ranked by reach × impact / effort. Top ten.

### 1. <Moment or surface> — <screens by walk id>
- **Score:** reach 3 × impact 3 / effort 1
- **Raised by:** Wayfinder, Stranger
- **Good (now):** <what is there, honestly, with the screenshot>
- **Better:** <one change, small enough for one feature> — proves with **<test>**: from <baseline> to <target>
- **Best:** <the spectacular version> — from <reference or transfer>, proves with **<test>**: <target>
- **Disagreement:** <member — position>, if any
- **Feature:** [F0xx](../features/F0xx-<slug>.md), once opened

### 2. …

## Backlog
Rows below the top ten, same shape, one line each: `<moment> — Better: <change> — score <n>`.
Best moves without a traced reference are listed here as `[UNTRACED]`.

## Walks
| Date | Portrait | Log | Screenshots |
|------|----------|-----|-------------|
| YYYY-MM-DD | <portrait> | [walk log](walks/YYYY-MM-DD/log.md) | `walks/YYYY-MM-DD/` |
```

## Rerun rules

1. Re-time all five stranger tests; add a score-history row.
2. For every ladder row: the Better rung's test met its target → the row's Good
   becomes that Better, the Best becomes the new Better, and the council member who
   raised the row is asked for a new Best. Not met → the row stays and its feature
   is not done, whatever its status says.
3. Re-rank; promote from the backlog into any vacated top-ten slot.
4. Kill questions are asked again in full. A kill question that flips to "no" on a
   rerun is a regression and goes to the top of the ladder.
5. The design principles change only on a full run, never on a rerun.

## Handoff to the build loop

The top three Better rungs leave as `/feature` definitions. Each carries:
- the row's stranger test, verbatim, as an acceptance criterion in Given / When /
  Then form with the baseline and target numbers;
- the screenshot ids from the walk as the "Problem" evidence;
- a link back to the ladder row, so a change to the row is a change to the feature
  in the same commit, per the feature skill's capture rule.

The `Feature:` line in the row links forward. A rung whose feature ships stays
unpassed until a rerun measures it — a merged pull request is not a passed test.
