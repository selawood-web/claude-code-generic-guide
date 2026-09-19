# GBB Research Protocol — who it is for, and what it is like to be them

Two parts. Part A is desk research and runs before anyone looks at the product.
Part B is the stranger walk and produces the evidence the council judges. Both feed
[`gbb-ladder.md`](gbb-ladder.md); the orchestration is in [`SKILL.md`](SKILL.md).

The rule that binds both: **evidence, cited**. A portrait, a convention or a
competitor claim that cannot point at where it came from is tagged `[UNVERIFIED]`
and cannot justify a Best rung on its own.

---

## Part A — Field research

### A1. Who it is for, from evidence
Build two or three **portraits**, not personas from a template. Sources, in the order
that gives the most signal per search:
1. Reviews of the two nearest competitors — the one-star and two-star reviews say
   what people were trying to do when the product failed them.
2. Forum and community threads where people ask for a product like this one.
3. Support threads and issue trackers, ours and theirs.
4. Job listings and role descriptions, when the app is for a profession.

Each portrait records:
- **Who** — one line, concrete: "a night-shift nurse charting between rounds", not
  "a healthcare user".
- **Reaching for it** — what they were doing the moment before they opened the app.
- **Winning** — what "it worked" looks like to them, in their words when quotable.
- **Losing** — the failure they complain about most, cited.
- **Spatial ability** — how much map they hold in their head. A portrait that lives in
  one screen all day tolerates a deep hierarchy; one that arrives interrupted needs
  every screen to say where it is.

Mark the **primary** portrait: the one the stranger walk adopts.

### A2. Context of use
One table, filled from the portraits and the product's own analytics or logs if any:

| Dimension | Finding | Source |
|-----------|---------|--------|
| Device and viewport | | |
| Posture — sitting, standing, walking, lying down | | |
| Hands — one, two, gloved, wet | | |
| Light and noise | | |
| Attention — focused, interrupted every minute, glancing | | |
| State — calm, hurried, stressed, in pain | | |
| Session length and frequency | | |
| Connectivity | | |

An empty cell is a finding: the product is being designed for a context nobody looked at.

### A3. Platform conventions — current, searched
The current version of what the platform expects: Apple's Human Interface
Guidelines, Material, the web platform's accessibility level (WCAG version and level
the product claims or should claim), system gestures and reserved edges, dynamic type
and reduced-motion settings. Record the version and date. A product that fights a
platform convention pays for it on every screen; a Better rung that adopts one is
almost free.

### A4. Best-in-class from adjacent fields
This is the out-of-the-box step, run on purpose. Take the product's hardest moment
from the vision (Step 1) and ask how five fields that never ship software solve it:

| Moment | Ask |
|--------|-----|
| Orientation — where am I | airport and hospital wayfinding, museum floor plans, subway maps, video-game level design |
| Feedback — did that work | cockpits and control rooms, cash registers, musical instruments, arcade cabinets |
| First five minutes | game tutorials, hotel check-in, a good restaurant's first minute, IKEA's entrance |
| Recovery — I made a mistake | undo in physical tools, aviation checklists, a kitchen's mise en place |
| Delight — I want to show someone | packaging, theatre, magic, a well-made tool's heft |

For each: the mechanism (not the aesthetic), and the one-line transfer — what it
would mean on our screen. Three transfers is enough; ten is a mood board.

### A5. Competitor teardown
The two nearest products. For each of the three moments in the vision: one
screenshot, what they do, and the one thing they do better than us. No feature
inventory — the council needs to see the moment, not the list.

### A6. Write it back
Findings go to `knowledge-base/research/gbb-<slug>.md` per
[`../decide/research-cache.md`](../decide/research-cache.md), staleness `volatile`
for conventions and competitors, `stable` for portraits and adjacent-field findings.

---

## Part B — The stranger walk

The product, running, walked by someone who has never seen it, with no instructions.
The "someone" is the primary portrait: adopt their goal, their context and their
patience, and say so at the top of the walk log.

### B0. Accounts, data, and the paper path
**Walk a seeded account, never a real one.** Screenshots go into the repository under
`design/walks/<date>/` and are committed, so whatever is on screen is published to
everyone with repository access. Use test or seeded data. Where real data is
unavoidable, redact it in the image before saving, and never save a screen showing a
token, a session URL, or another person's details.

**When the product cannot be started** (the paper path, `/gbb --paper`): the owner
supplies screenshots and one line per screen saying what reaches it and what returns.
B1 and B2's timings are skipped, B3's spatial map is built from those two inputs and
marked `from supplied screens`, and B4's five tests all report `not run`. Every ladder
row a paper run produces carries `unmeasured` until a real walk measures it. A paper
run never passes a rung.

### B1. Start it for real
Use the project's own run path — its README, tasks, or a `run` skill if the session
has one — and a browser or simulator that can take screenshots (Playwright is
usually present). Match the context table: the viewport, a throttled network if the
portrait's connectivity says so, reduced motion if the platform offers it. A walk on
a wide desktop of a product used one-handed on a phone is not a walk.

### B2. Log every state
For each screen reached, one entry:
```
S07  /orders/new           reached from: S03 (tap "New")   back: header arrow → S03
     tells me where I am:  title "New order"; breadcrumb absent
     states seen:          empty ✔  loading ✔  error ✘ (could not provoke)  success ✔
     hesitation:           4s — "Save" vs "Submit", unclear which finishes
     screenshot:           walk/S07-new-order-empty.png
```
Every screenshot is saved under `design/walks/<date>/` and referenced from the log.
The council sees these, not this file's prose.

### B3. The spatial map
From the log, draw the map as a list or a diagram: every screen, its parents, its
exits, and the **orientation cue** on each — the thing that says where you are. Then
mark:
- **Dead ends** — a screen with no obvious way back.
- **Teleports** — a transition that moved the user without showing the move.
- **Twins** — two screens that look the same and are not.
- **Unlabelled rooms** — a screen with no title, or a title that repeats the parent's.

The map is the artifact the Wayfinder on the council critiques first.

### B4. Time the stranger tests
Run the five tests defined in [`gbb-ladder.md`](gbb-ladder.md), record the number
and the moment where the time went. These are the baseline the ladder moves.

### B5. Provoke the bad day
Turn the network off mid-action. Enter something wrong. Come back after the session
expired. Rotate the device. Turn on the largest dynamic type size. Every product is
good on its best day; the gap between vision and product is widest on the bad one.

### B6. Hand over
Deliver to the council: the vision, the portraits and context table, the platform
conventions, the adjacent-field transfers, the competitor moments, the walk log, the
screenshots, the spatial map and the stranger-test baseline. Nothing else — a
council briefed with the spec judges the spec.
