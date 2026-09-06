---
id: F001
title: Feature definition tool
status: building
owner: repository owner
target: unscheduled
---

# F001 — Feature definition tool

## Summary
A single house format for defining a feature, a linter that checks it, and a skill that
drives both. Any project running CCGG gets the same definition file, the same readiness
bar, and paste-ready views for whatever tracker the team already uses.

## Problem
Feature definitions arrived as prose — a tracker project description, a chat message, a
half-remembered call. Each one was shaped differently, so the missing parts were invisible:
no non-goals meant the same scope argument twice, no acceptance criteria meant "done" was
decided at review, and open questions sat inside paragraphs where nobody owned them. The
existing `/requirements` skill ran a good interview and then left the result in the
conversation, where the next session could not find it and no check could read it.

## Outcome
Definitions become checkable artifacts instead of prose, the check runs without anyone
remembering to ask for it, and an idea raised mid-build cannot leave the record silently.

- Metric: definitions reaching status `ready` with a missing required section or an
  unresolved placeholder, from unknown today to 0 findings, measured by
  `tools/feature_lint.py` on every push
- Metric: a reader gets from the definition to a build decision without asking a question,
  measured at review of the first 3 definitions written with it
- Metric: ideas raised mid-build that reach `shipped` with no recorded decision, from
  unmeasured today to 0 items, measured by the ledger check at close-out

## Scope
- An author can write a definition into `features/` in one canonical schema
- An author can run one command and learn exactly which parts are missing
- A reviewer sees the same check run in CI on every pull request
- An owner can render the definition as a tracker project overview or as one issue per
  scope bullet, paste-ready
- A drafter keeps gaps while the status is `draft`, and is blocked from calling it `ready`
  while any question still blocks
- An author can capture an idea raised mid-build in the definition itself, with the decision
  attached, and cannot mark the work `shipped` while any captured idea is still undecided

## Non-goals
- Not a tracker integration — no API calls, no credentials, no automated posting; views
  are rendered and the owner pastes them, per the charter's standing constraints
- Not a replacement for `/requirements` — that skill runs the interview and this one files,
  checks, and keeps the result
- Not a project-management layer — no estimates, no burndown, no assignment workflow
- Not a schema per project — one house shape; teams change the tracker mapping instead

## Acceptance criteria
- Given a definition with every required section filled, when `tools/feature_lint.py` runs
  against it, then it reports OK and exits 0
- Given a definition whose status is `ready` with a `blocks: yes` open question, when the
  linter runs, then it reports an error and exits 1
- Given a draft with unresolved placeholders, when the linter runs, then the gaps are
  listed and the exit code stays 0, because drafts are allowed to be incomplete
- Given a repository with no `features/` directory, when `tools/validate.py` runs, then it
  passes unchanged, so installed projects are never broken by adopting the validator
- Given a definition at status `shipped` carrying an idea still tagged `[open]`, when the
  linter runs, then it reports an error and exits 1

## Dependencies and risks
- Depends on `tools/validate.py`, which calls the linter when `features/` exists — a wired
  project that copies the validator without the linter must degrade to skipping, not error
- Risk: the schema is heavier than a small team wants, and definitions stop being written.
  Early signal — the sizing rule in the template gets ignored, or files land half-filled and
  stay `draft` forever
- Risk: the definition and its tracker copy drift. Mitigated by the round-trip rule in
  `tracker-views.md`, which makes the file authoritative and the tracker a view

## Open questions
- Should the linter also enforce section order, not only presence? — owner: repository owner, blocks: no
- Do teams need a per-project override for the required section list? — owner: repository owner, blocks: no

## Ideas and changes
Append-only. Every idea raised while this work is in flight, with what was decided.

- 2026-09-06 — An append-only ledger as the ninth section, so an idea raised on turn 40
  lands in the file rather than in the conversation — [in]
- 2026-09-06 — The linter refuses `shipped` while any idea still reads `[open]`, which is
  what turns capture into close-out — [in]
- 2026-09-06 — The skill re-reads the definition when work on a feature resumes, and says
  in one line what is still open — [in]
- 2026-09-06 — Render the ledger into the tracker views as a change history — [deferred]
  until the first three real definitions show what teams actually paste
- 2026-09-06 — Have the ledger carry an owner per idea, like open questions do — [dropped]
  the disposition is the decision; an owner on a decided item is ceremony
