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
```

## Field rules

| Field | Rule |
|-------|------|
| `id` | Tracker-style and stable — `F001`, `CAB-42`. The filename must start with it, so a file and its tracker item never drift apart. |
| `title` | The capability, not the implementation. "Bulk invoice export", not "add CSV writer". |
| `status` | `draft` → `ready` → `building` → `shipped`, or `dropped`. Gaps are tolerated in `draft` only. |
| `owner` | A person or role accountable for the outcome, not the author of the document. |
| `target` | A date, a quarter, or the literal `unscheduled`. An empty target is a decision nobody made. |

## Status lifecycle

| Status | Means | Entry condition |
|--------|-------|-----------------|
| `draft` | Being written; gaps expected | Created |
| `ready` | Buildable as written | Linter clean and no `blocks: yes` question remains |
| `building` | Implementation in progress | Work started; scope changes are edits to this file, in the same commit |
| `shipped` | Live, outcome being measured | Acceptance criteria all verified in a deployed environment |
| `dropped` | Not being built | Reason recorded in Summary; the file stays as the record |

## Sizing — when a definition is not warranted

A definition is for work whose *shape* is in question. Skip it, and say so in one line,
when the change is a one-liner, a copy fix, a dependency bump, or a bug with an
obvious correct behaviour. Writing a definition for those is ceremony, and ceremony is
a cost. When in doubt: if two reasonable engineers could build different things from
the request, it needs a definition.
