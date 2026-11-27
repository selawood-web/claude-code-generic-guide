# The GBB Ladder — record template, scoring and the stranger tests

The ladder is the product's living design file: `design/GBB-<slug>.md`, indexed from
`design/README.md`, created on first use. One row per moment or surface; three rungs
per row; a test and a number on every rung. It is rewritten on every `/gbb --rerun`
and never deleted — the score history at the top is the record that the bar moved.

## The stranger tests

Five tasks, run as the primary portrait during the walk and replayed on every rerun.
Each is a check the recorded walk runs against the product, so it returns the same
result for the same product: counts and pass or fail, never seconds. Seconds timed by
the walking agent measure the model and its tools, not a person's hesitation, and a
rung promoted on them moves on noise (F005). Hesitation is still recorded, as a
finding in the walk log with its screenshot; it is never a pass bar.

| Test | Task | Measure | Pass bar |
|------|------|---------|----------|
| **First success** | From a cold start, complete the core action with no instructions | Actions on the recorded path to the core action done, and off-path actions taken on the first walk | No more than the intent's target, 7 actions where it sets none; no off-path action on replay |
| **Where am I** | Land on any screen in the map and say where you are | On every screen: one visible page title, and the current place marked in the navigation (`aria-current` or the selected state) | Every screen in the map |
| **Back out** | From every screen, return to the start without the system back gesture | In the map graph, a path from every screen back to the start through in-app controls; each back or close control lands where the map says | No dead end; no control lands elsewhere |
| **Recovery** | Provoke the most likely error, then finish the task anyway | After the error: a visible message tied to the field or announced as an alert, the entered values still present, the task then completed | All three |
| **One hand** | Complete the core action at 200% text size and 320 CSS px width | Interactive targets at least 24 CSS px (WCAG 2.2 SC 2.5.8); the core action's targets at least 44 CSS px (SC 2.5.5); the core action reached with no horizontal scroll (SC 1.4.10) | Every target; core action reached |

A test is reported as measured, or as **not run** with the reason: no way to start the
product, no way to sign in, a step the replay could not reach. A test the product
cannot be put through is never passed.

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
| YYYY-MM-DD | 9 actions / 3 off-path | 6 of 9 screens | dead end at S07 | values lost | 2 targets under 24 px | 0 of 10 |

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
| YYYY-MM-DD | <portrait> | [walk log](walks/YYYY-MM-DD/log.md) | `walks/YYYY-MM-DD/` (screenshots, `walk.spec.ts`, `map.json`) |
```

## Rerun rules

1. Replay the recorded walk and re-measure all five stranger tests; add a score-history row.
   Where a replay step no longer matches, walk again from that step and say which; its
   test is not passed on the strength of the old walk.
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
- the row's stranger test as an acceptance criterion in Given / When / Then form: the
  replay command, the measure, and the baseline and target;
- the screenshot ids from the walk as the "Problem" evidence;
- a link back to the ladder row, so a change to the row is a change to the feature
  in the same commit, per the feature skill's capture rule.

The `Feature:` line in the row links forward. A rung whose feature ships stays
unpassed until a rerun measures it — a merged pull request is not a passed test.
