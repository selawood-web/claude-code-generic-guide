# Feature Definition — schema and template

The one canonical shape for a feature definition in this repository. Files live at
`features/<id>-<slug>.md`; `tools/feature_lint.py` enforces everything marked
**required** below, so a definition is checkable, not just well-intentioned.

## The template

Copy this whole block, fill it, delete nothing.

```markdown
---
id: F001
title: Short capability name
status: draft
owner: name or role accountable for the outcome
target: a date, a quarter, or unscheduled
---

# F001 — Short capability name

## Summary
One paragraph, 60 words maximum: what changes, for whom, and the shape of the change.
Someone who reads only this paragraph should be able to repeat it correctly.

## Problem
Who hurts, how often, and what they do today instead. Evidence over assertion — a
support thread, a measured number, a named user. If the only evidence is "it would be
nice", say that plainly; it is a real finding about the priority.

## Outcome
The measurable difference once this ships. At least one number with a unit — a rate, a
duration, a count, a currency amount — and how it will be observed.

- Metric: [what], from [baseline] to [target], measured by [source]

## Scope
The user-visible capabilities included, as short statements of what someone can do.

- A [role] can [capability]

## Non-goals
What this deliberately does not do, especially the things a reader would otherwise
assume. Every entry here is an argument that does not need to happen twice.

- Not [excluded capability] — [why not, or where it belongs instead]

## Acceptance criteria
At least two, each testable as written, in Given / When / Then form. These are what QA
writes tests from and what the owner checks at review.

- Given [context], when [action], then [observable result]
- Given [edge case], when [action], then [observable result]

## Dependencies and risks
Systems, teams, third-party services, and data this needs. For each risk: what happens
if it lands badly, and the cheapest thing that would tell us early.

## Open questions
Every unknown, each with an owner and a blocking marker. `blocks: yes` on any question
holds the definition in `draft` — the linter enforces that.

- [Question]? — owner: [who], blocks: no

## Ideas and changes
Append-only. Every idea, scope change, or cut raised while the work is in flight, written
here in the turn it is raised, each carrying a bracketed disposition.

- [date] — [the idea, in one line] — [in]
- [date] — [the idea] — [deferred] until [what has to happen first]
- [date] — [the idea] — [dropped] [why]
- [date] — [the idea] — [open]
- [date] — [an idea raised after this shipped] — [next] [which later definition takes it]
```

## Field rules

| Field | Rule |
|-------|------|
| `id` | Tracker-style and stable — `F001`, `CAB-42`. The filename must start with it, so a file and its tracker item never drift apart. |
| `title` | The capability, not the implementation. "Bulk invoice export", not "add CSV writer". |
| `status` | `draft` → `ready` → `building` → `shipped`, or `dropped`. Gaps are tolerated in `draft` only. |
| `owner` | A person or role accountable for the outcome, not the author of the document. |
| `target` | A date, a quarter, or the literal `unscheduled`. An empty target is a decision nobody made. |
| `tracker` | Optional, and written by the skill rather than by hand: the URL of the tracker item this definition was posted to. Its presence is what stops a second item being created for the same `id` — see [`tracker-handoff.md`](tracker-handoff.md). The linter ignores it. |

## The ledger — why the ninth box exists

The first eight boxes describe the work at the moment it was defined. The ninth keeps it
true afterwards. An idea raised at turn 40 of a build session lives only in that
conversation, and a conversation is the one part of this system that does not persist:
it gets compressed, the session ends, the machine is recycled. Written into the file, the
idea survives all three.

| Tag | Means | Rule |
|-----|-------|------|
| `[open]` | Captured, not yet decided | Costs nothing to write — capture first, decide later. Blocks `shipped`. |
| `[in]` | Folded into the work | The Scope and Acceptance criteria above should now reflect it. |
| `[deferred]` | Real, but not now | Must say what it waits on, so it can be found again. |
| `[dropped]` | Not doing it | Must say why — that reason is the answer when the idea returns. |
| `[next]` | Raised after shipping; belongs to a later definition | Allowed **only** on `shipped` and `dropped`. Must name where it goes. An error before shipping, where the honest word is `[open]`. |

Capture is not a decision. Writing `[open]` in the turn an idea is raised takes seconds
and never interrupts the build; the deciding happens at the next natural pause. What is
not allowed is the third option people actually take — nodding at the idea in
conversation and moving on, which is indistinguishable from forgetting it.

### Shipping does not close the ledger

`[open]` blocks `shipped` because an idea nobody decided before shipping is the failure
this ledger exists to catch. But a live feature keeps receiving ideas, and this file is
append-only, so they have to land somewhere legal. That is `[next]`: it says the idea is
real, it is not this definition's, and here is the one that takes it. Before shipping it
is an error — a `draft` writing `[next]` is `[open]` with the blocking filed off, and the
linter says so.

An idea raised after shipping and then *built* is not `[next]`. It is `[in]`, like any
other change folded into the work, and Scope and Acceptance criteria are updated with it.
`[next]` is for what is going somewhere else.

### Your own words, alongside the canonical tag

Real ledgers record decisions in a richer vocabulary than five words — `[accepted]`,
`[added]`, `[decided: fold]`, `[reversed the 2026-03-01 drop]`. Keep them. An entry may
carry any bracketed words it likes **as long as one canonical tag is also there**. House
style is canonical first, so the word a reader scans down the column for is the leftmost:

```
- 2026-03-04 — Owner asked for reactions — [in] [added] `comment_reactions`, a fixed set,
  mirrored web ↔ server with a selftest.
```

The linter searches for the canonical tag anywhere in the entry and ignores the rest.

### Verification records live in the ledger

"Verified on prod", and its honest companion "not exercised from this seat", are not
ideas — but they are exactly what a ledger should hold, and a separate section would be
one more thing to forget. They stay here as an `[in]` entry, with the verification detail
as the reason:

```
- 2026-03-06 — [in] Shipped in three PRs (`abc1234` … ), each verified on prod.
  [verified] the anchor rule, the size and count checks, the browser spec.
  [not exercised from this seat] the email arriving (the sandbox org has one user).
```

Say what was *not* exercised as plainly as what was. A verification record that only
lists successes is a claim, not a record.

## Status lifecycle

| Status | Means | Entry condition |
|--------|-------|-----------------|
| `draft` | Being written; gaps expected | Created |
| `ready` | Buildable as written | Linter clean and no `blocks: yes` question remains |
| `building` | Implementation in progress | Work started; scope changes are edits to this file, in the same commit |
| `shipped` | Live, outcome being measured | Acceptance criteria all verified in a deployed environment, and no idea left `[open]` — the close-out the linter enforces. Ideas that arrive afterwards are `[next]`, or `[in]` if they get built. |
| `dropped` | Not being built | Reason recorded in Summary; the file stays as the record |

## Sizing — when a definition is not warranted

A definition is for work whose *shape* is in question. Skip it, and say so in one line,
when the change is a one-liner, a copy fix, a dependency bump, or a bug with an
obvious correct behaviour. Writing a definition for those is ceremony, and ceremony is
a cost. When in doubt: if two reasonable engineers could build different things from
the request, it needs a definition.
