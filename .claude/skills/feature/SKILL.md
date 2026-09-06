---
name: feature
description: Turn a feature idea into a complete, checkable definition — a versioned file in features/, enforced by a linter, rendered into whatever tracker the team uses. Use when the user says "define this feature", "write it up", "what exactly are we building", or hands over a rough capability idea.
when-to-use: define a feature, feature definition, write up a feature, what are we building, feature brief, project overview, scope this, definition of done
allowed-tools: powershell, bash
argument-hint: "[feature idea, or the id of an existing definition]"
purpose: Feature idea into a checked, tracked definition
---

# Feature Definition Skill

## Goal
Produce a definition precise enough that two engineers build the same thing from it —
and prove it, with a linter, rather than claiming it.

The artifact is `features/<id>-<slug>.md`, in the repository, versioned with the code it
describes. Schema, field rules, and the status lifecycle live in
[`feature-template.md`](feature-template.md); tracker renderings live in
[`tracker-views.md`](tracker-views.md).

## Routing — this skill or another
| The question | The skill |
|--------------|-----------|
| Is this worth building at all? | `/product-brief` — verdict first, definition after |
| Which option do we pick? | `/decide` |
| **What exactly are we building, and when is it done?** | **this skill** |
| How do we implement it? | `/architecture`, then `/code-generation` |

`/requirements` is not a competitor: it is the interview this skill calls in Step 3 when
detail is missing. It asks; this skill files the answers, checks them, and keeps them.

## Process

### Step 0 — Resuming work on a feature that already has a definition
Read the file first, then say in one line what is still open — blocking questions, and
ideas tagged `[open]`. Do this at the start of every session that touches a feature with a
definition, not only when `/feature` is typed by name. A definition nobody re-reads is a
kickoff document; a definition read at each resume is a working ledger.

### Step 1 — Size it first (the cheap path)
State in one line whether this needs a definition at all. One-liners, copy fixes,
dependency bumps, and bugs with an obvious correct behaviour do not — say so and go do
the work. The test is in [`feature-template.md`](feature-template.md), *Sizing*: if two
reasonable engineers could build different things from the request, define it.

### Step 2 — Recall before writing
- `features/README.md` — is this already defined, or a slice of something defined?
  An existing definition gets *edited*, never duplicated; a related one gets linked.
- `decisions/` — a decision or product brief on this topic sets constraints the
  definition must respect rather than re-open.
- Memory, for domain rules already learned.

### Step 3 — Draft from what is known, then interview the gaps
Fill every section of the template from the request, the codebase, and recall. Mark what
is genuinely unknown; do not invent it. Then close the gaps by running `/requirements`
Steps 1–5 (problem, success, MVP scope, user stories, constraints) against only the
sections still empty — the interview is defined there, and is not restated here.

Ask by the charter: one question per turn, as a pick-list with a recommended default
first, and never a question whose answer the codebase already holds.

### Step 4 — Write the file
- Allocate the next id: the highest in `features/` plus one, or the team's tracker key
  when one exists (`CAB-42`). The filename starts with the id.
- Write `features/<id>-<slug>.md` from the template, status `draft`.
- Create `features/README.md` from the index shape in this skill on first use, and add
  the row. The index is a table: id, title, status, owner, target.

### Step 5 — Check it (the gate)
```bash
python3 tools/feature_lint.py features/<id>-<slug>.md
```
Errors are structural and always fail. Gaps are readiness findings, tolerated while the
status is `draft` and fatal after it. An idea still tagged `[open]` is an error at `shipped`
only — open ideas are expected while the work is live. Fix and re-run until clean — a definition reported
as ready without a clean run is exactly the failure this skill exists to prevent.

### Step 6 — Readiness verdict
Report one of two, never a hedge:
- **Ready** — linter clean, no `blocks: yes` question left. Move status to `ready` and
  name the next skill (`/architecture` for design-heavy work, `/code-generation` for
  clear work).
- **Draft, blocked on N** — list exactly the blocking questions, each with the owner who
  can answer it and what happens the moment it lands.

### Step 7 — Render the tracker view, if asked
Produce the paste-ready view from [`tracker-views.md`](tracker-views.md). Rendered, never
posted — this system does not hand off to external applications, and no tracker
credentials are used.

### Step 8 — Capture every idea in the turn it is raised
This is the step that stops work from leaking. An idea, scope change, or cut raised mid-build
— by the owner, by a reviewer, or by me — is appended to `## Ideas and changes` **in the same
turn it is raised**, with a disposition tag. Acknowledging it in conversation is not capture:
the conversation is compacted, the session ends, and the container is recycled; the file is
the only part that survives all three.

Capture is not deciding. `[open]` costs one line and never interrupts the build; the decision
happens at the next natural pause, and the tag changes to `[in]`, `[deferred]` or `[dropped]`
with its reason. Tags and their rules live in
[`feature-template.md`](feature-template.md), *The ledger*.

At close-out, no idea may still read `[open]` — the linter refuses `shipped` while one does.
That is the whole mechanism: forgetting an idea now requires someone to actively write
`[dropped]` next to it and say why.

### Step 9 — Keep it true
The definition is live, not an artifact of the kickoff:
- Scope changes during the build are edits to this file, in the same commit as the code.
- `shipped` requires the acceptance criteria verified in a deployed environment
  (`/deploy-steward` owns that obligation), not merely merged.
- Once shipped, record what the outcome metric actually did. A definition whose outcome
  is never measured taught nobody anything.

### Step 10 — Extract what generalizes
```
remember: [domain rule discovered while defining] — reason: [why it constrains future work]
```

## `features/README.md` — index shape
```markdown
# Feature Definitions

Definitions of what we are building, written by the `/feature` skill and checked by
`tools/feature_lint.py`. Schema and lifecycle live with the skill.

| Id | Title | Status | Owner | Target |
|----|-------|--------|-------|--------|
| [F001](F001-slug.md) | Title | draft | owner | target |
```

## Anti-patterns

| Anti-pattern | Correct approach |
|--------------|-----------------|
| Definition that describes the implementation | Describe the capability; the design is `/architecture`'s job |
| "Success: users like it" | A number, a baseline, and where it is read from |
| No non-goals | Name the excluded thing everyone will otherwise assume is included |
| Acceptance criteria as a feature list | Given / When / Then, testable as written |
| Open questions left implicit in prose | One bullet each, with an owner and a `blocks` marker |
| Definition written once and abandoned | It is edited in the same commit as the code that changes its scope |
| "Good idea, noted" — and it lives only in the chat | Append it to the ledger in that turn, tagged `[open]` if the decision has to wait |
| Quietly not building something | `[dropped]` with a reason — the record of a cut is worth as much as the cut |
| Marking ready without running the linter | The linter is the evidence — verify before claiming |

## The quality bar
A finished definition passes four readers: an engineer builds it without asking a
question, a QA engineer writes tests from it alone, a designer sketches the flow from it,
and the owner can tell, at review, whether it is done.
