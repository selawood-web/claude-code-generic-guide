---
id: F005
title: GBB measured stranger tests
status: ready
owner: repository owner
target: unscheduled
---

# F005 — GBB measured stranger tests

## Summary
GBB's five stranger tests stop being timed by the walking agent. Each becomes a scripted
check on the running product: action counts, page state, a graph of the spatial map,
computed target sizes. A replayable Playwright walk records them, so a rerun of an
unchanged product returns the same numbers and a rung moves only on a real change.

## Problem
GBB's rerun promotes a rung only when the rung's stranger test meets its target
(`.claude/skills/gbb/gbb-ladder.md`, *Rerun rules*, rule 2). Three of the five pass bars
are in seconds: first success under 60 seconds, where-am-I within 3 seconds, recovery
under 20 seconds. The seconds are timed by the agent walking the product, so they
measure model and tool latency, not a person's hesitation. Two reruns of an unchanged
product can therefore disagree, and the ladder's central mechanism, a bar that moves
only on evidence, moves on noise. F003 names the risk (`features/F003-gbb.md`,
*Dependencies and risks*) and mitigates it only by reusing the same protocol, which does
not help when the clock is the problem.

The runs that did happen show a second, larger gap. GBB has run twice on CabiCAD
(`design/GBB-canvas-colour.md` on 2026-09-20, `design/GBB-icons-visuals.md` on
2026-10-16), and in both almost every stranger test reported `not run`: the first was a
paper run, and the second could not sign in because it looked for production
credentials, while the project already ships a local sign-up path for its own Playwright
user-flow tests. One hand read `n/a (desk)` on a desktop CAD tool. The numbers those runs
did produce were mechanical (a lint count of about 800 emoji glyphs in 212 files, a
greyscale export check), which is the direction this feature takes.

## Outcome
- Metric: stranger-test results that agree between two consecutive reruns of an
  unchanged product, from unmeasured today to 5 of 5, measured by the two score-history
  rows the reruns write
- Metric: model spend of a rerun on an unchanged ten-screen product, from a full
  re-walk (unmeasured) to under 1 USD, measured by the session's own cost report
- Metric: Better rungs handed to `/feature` whose acceptance criterion is a runnable
  check, from 0 to every one, measured by the feature files naming the replay command

## Scope
- The walk records a replayable Playwright script and a machine-readable spatial map
  under `design/walks/YYYY-MM-DD/`, beside the screenshots and the log it already writes
- Each stranger test has a deterministic measure and a pass bar with no seconds in it:

  | Test | Measure | Default pass bar |
  |------|---------|------------------|
  | First success | Actions on the recorded path from cold start to the core action done, and off-path actions taken on the first walk | No more than the intent's target; 7 actions when the intent sets none; no off-path action on replay |
  | Where am I | On every screen in the map: one visible page title, and the current place marked in the navigation (`aria-current` or the selected state) | Every screen |
  | Back out | In the map graph, a path from every screen back to the start using in-app controls; each back or close control lands where the map says | No dead end; no control lands elsewhere |
  | Recovery | After the provoked error: a visible message tied to the field or announced as an alert, the entered values still present, and the task then completes | All three |
  | One hand | At 200% text size and 320 CSS px width: interactive targets at least 24 CSS px (WCAG 2.2 SC 2.5.8, AA), the core action's targets at least 44 CSS px (SC 2.5.5), and the core action reachable with no horizontal scroll (SC 1.4.10) | Every target; core action reached |

- `/gbb --rerun` replays the recorded walk instead of re-walking. The agent walks again
  only where a replay step no longer matches, or on screens added since, and says which
- The mechanical intent tests, colour contrast and target size, run through axe-core in
  the same script; the council keeps the tests that need judgment
- A Better rung handed to `/feature` carries its check as the acceptance criterion: the
  replay command, the measure, the baseline and the target
- `tools/test_gbb.py` holds the contract: no stranger-test pass bar is in seconds, and
  every test names its measure
- A wired project receives the changed skill files through `install.sh` and `update.sh`
  like every other skill

## Non-goals
- Not a replacement for the council: hesitation, taste and feel stay qualitative findings
  from the Stranger and the other members, never a pass bar
- Not real-user testing: a human-timed study is still the deferred slice in F003's ledger
- Not native apps: this slice measures web products through Playwright; a device
  simulator is a later slice
- Not wall-clock timing kept alongside: seconds leave the pass bars, so two clocks never
  disagree about one rung
- Not a runtime in the guide: the walk script and its dev dependencies live in the walked
  project, and CCGG's own tooling stays standard-library Python and bash

## Acceptance criteria
- Given a running web product and a completed walk, when `/gbb` finishes, then
  `design/walks/YYYY-MM-DD/` holds a replay script and a map file, and the score-history row
  has a result or `not run` for each of the five tests, none of them in seconds
- Given an unchanged product, when `/gbb --rerun` runs twice, then the two
  score-history rows are identical on all five tests
- Given a product whose page title is removed from one screen between runs, when
  `/gbb --rerun` runs, then Where am I fails for that screen alone, and no rung it proves
  is promoted
- Given a replay step whose locator no longer matches, when `/gbb --rerun` runs, then the
  run names the broken step, walks again from it, and never reports that step's test as
  passed on the strength of the old walk
- Given a spatial map with a screen that has no in-app path back to the start, when the
  checks run, then Back out fails and names the screen
- Given an interactive target under 24 CSS px at 200% text size, when One hand runs, then
  it fails and names the element and the screen
- Given a Better rung handed to `/feature`, when the feature file is written, then its
  acceptance criterion names the replay command, the measure, the baseline and the target
- Given the paper path, when it runs, then every stranger test still reports `not run`
- Given the repository's validator and `tools/test_gbb.py`, when they run, then no
  stranger-test pass bar in `gbb-ladder.md` is expressed in seconds and every test names
  its measure

## Dependencies and risks
- Playwright, present in the remote environment (1.63.0 at definition time); to be
  confirmed locally on first use, as F003 already requires
- `@axe-core/playwright`, pinned to 4.14.0 (released 2026-10-15; 4.14.1 was two days old at
  definition time). It is installed as a dev dependency of the walked project, not the
  guide, and adding it is an owner gate per AGENTS.md, *Escalate instead of proceeding*
- Risk: recorded locators break on small UI changes, so most reruns fall back to a walk.
  Mitigation: record role and text locators (`getByRole`, `getByLabel`), never CSS paths.
  Early signal: more than one broken step per rerun
- Risk: the measured tests miss what a clock would have caught, such as a screen a person
  stares at. Mitigation: the Stranger still reports hesitation as a finding with its
  screenshot. Early signal: the owner disagrees with a rung that passed
- Risk: the default of 7 actions for first success fits no real product. Mitigation: the
  intent sets it per product; the default applies only when the intent is silent. Early
  signal: the first run's baseline is far from 7 either way
- Depends on a product that can be started in the session; F003's first-run question
  (which project goes first) is also this feature's

## Open questions
- Is 7 actions the right default first-success bar when the intent sets none, or should
  the first run's baseline set it? — owner: repository owner, blocks: no
- Which project and screen take the first run? — owner: repository owner, blocks: no
- Does a later slice cover native apps through a device simulator? — owner: repository owner, blocks: no

## Ideas and changes
Append-only. Every idea raised while this work is in flight, with what was decided.

- 2026-11-26 — Defined from the GBB review in the structure analysis: agent-timed seconds
  make rerun deltas noise, so the tests become scripted measures — [in]
- 2026-11-26 — Contrast and target size checked by axe-core inside the walk script, so
  only judgment tests reach the council — [in]
- 2026-11-26 — Send each council member only the screens and crops its discipline needs,
  and run members on the smaller model — [deferred] until this feature's first run
  measures what a council pass costs
- 2026-11-27 — Correction: GBB had already run twice on CabiCAD, both runs blocked from the
  in-app stranger tests. The Problem section now says so; earlier text here and in F003's
  ledger claiming no run had happened was wrong — [in]
- 2026-11-27 — Sign in through the project's own local test path (CabiCAD's user-flow
  config boots the API on a throwaway database and allows an unverified local sign-up),
  and save the signed-in session for replay, so a walk is never blocked on production
  credentials — [open]
- 2026-11-27 — Each stranger test declares when it applies, from the intent's context of
  use, and reports `n/a` with the reason (One hand on a desktop-only product), so `n/a` and
  `not run` stop being confused — [open]
- 2026-11-27 — [in] First measured run: CabiCAD's dashboard and the seven screens one hop
  from it, signed in through the project's own local user-flow path (API on a throwaway
  Postgres, unverified local sign-up), four replays from a fresh shop each.
  [verified] two consecutive replays identical on all five tests, twice: before and after
  a walker fix. Results: first success 3 actions; recovery passes (an invalid client email
  blocks the submit with a message tied to the field, the entered name is kept, the task
  then completes); back out 0 dead ends in 7 screens; where am I 5 of 8 screens (`/rejects`
  and `/help` mark no current place, `/hardware` shows its title but not as a heading);
  one hand `n/a (desktop product)`, with one target under 24 CSS px ("Set a status",
  71×21, spacing exception not checked). Replays make no model calls.
  [not exercised from this seat] contrast, since adding axe-core to CabiCAD is the owner's
  call; the council and ladder; criteria 3, 4, 7 and 8; the walk saved inside the project
  under `design/walks/`, since writing to CabiCAD is outside this branch
- 2026-11-27 — A failing check is confirmed against its screenshot before it reaches the
  ladder: the first walker reported two dead ends that were a Projects link outside the
  navigation landmark and a Back button, both real ways back — [open]
- 2026-11-27 — "Title" means a heading, not only visible text: report both, since a title a
  screen reader cannot find as a heading fails people the visible check passes — [open]
- 2026-11-27 — Where am I on a screen outside the app shell (`/help`, `/rejects` drop the
  global navigation): decide whether the current-place marker applies there, or a
  way-back control replaces it — [open]
- 2026-11-27 — A replay step that no longer matches failed loudly instead of re-walking: the
  empty-state "New Project" button disappears once a project exists. Criterion 4's
  automatic re-walk is not built yet — [open]
