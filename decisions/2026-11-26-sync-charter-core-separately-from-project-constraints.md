# The charter's core syncs separately from project constraints

- **Date:** 2026-11-26
- **Status:** decided
- **Type:** architecture
- **Deciders:** repository owner
- **Supersedes / superseded by:** —

## Context

`WORKING-CHARTER.md` holds two kinds of content in one file. Part One (core), Part Two
(code module) and the general standing constraints are meant for every project. The
section "This repository" is the guide's own, and an installed project is told to replace
it. `update.sh` never rewrites the charter (`update.sh:13`), so after installation no
improvement to the core ever reaches a wired project. The file is also full: 13,240 of
its 13,312-byte budget (`tools/validate.py:613`).

Reversibility: mostly a one-way door. It changes what installed projects carry and how
their rules load. Stakes: every wired project's always-on rules.

## Criteria

Owner-approved weights:

- a. Core improvements reach already-wired projects without manual edits: 35%
- b. Always-loaded bytes do not grow, and the budget gets headroom: 20%
- c. Migration risk for existing installs, including a project that edited its core: 20%
- d. Simple for a fresh reader; one obvious place per rule: 15%
- e. Size of the change to the validator, install/update scripts and tests: 10%

Hard constraints: `AGENTS.md`, `WORKING-CHARTER.md`, `.claude/` and `MEMORY.md` stay where
they are. A rule file links only to a file `install.sh` copies. Each rule has one home. A
project's own constraints are never overwritten.

## Research findings

Verified on 2026-11-26 against code.claude.com/docs/en/memory:

- `@` imports resolve relative to the importing file, recurse up to four hops, and load
  at launch with the importing file. Imports inside the project get no approval dialog.
- `.claude/rules/*.md` without `paths:` frontmatter load at launch with no import.
- Imports organise a file but do not reduce what loads.

Verified in this repository: `update.sh` overwrites `.claude/references/` (line 126) and
has no handling for `.claude/rules/`. `install.sh` writes the `CLAUDE.md` bridge only
when none exists.

## Options considered

| Option | Benefit | Cost | Risk |
|---|---|---|---|
| S. Status quo | Nothing to build | Core never reaches wired projects; 72 bytes of headroom | Cores drift per project; no room for the next rule |
| **R. Core moves to `.claude/references/charter-core.md`, imported at the top of `WORKING-CHARTER.md`** (chosen) | Uses the sync path that already works; nothing changes in a project until it opts in; separate budgets | One manual edit per existing project | Projects that never migrate stay frozen, as today |
| L. Core moves to `.claude/rules/ccgg-charter.md`, auto-loaded | No edit needed in any project | New synced directory; validator must budget and scan it | Every existing project loads the old and new core together, about 13 KB twice, until it trims its charter |
| M. `update.sh` rewrites a marked core block inside `WORKING-CHARTER.md` | Automatic once markers exist | Reverses the rule that update.sh never rewrites always-loaded files; budget unsolved | A project's edits inside the markers are overwritten silently |
| D. Shrink only | Frees budget | Portability untouched | The main problem stays |

Rejected early: overwriting the whole charter on sync, which breaks a hard constraint.

## Debate summary

All five personas independently ranked R first. Four raised the same objection, and the
Skeptic sharpened it.

- Champion: R is the only option that rides an existing sync path without overriding
  project edits. Objection: criterion a is only partly met. → Mitigated, see below.
- Skeptic: the benefit may reach few or none of the installs that matter, since no one
  knows how many will migrate; also, bytes do not shrink, and edited cores need a hand
  merge. → Mitigated for a; accepted for b and c.
- Economist: R has the lowest total cost, and the lowest exit cost, since the import can
  be inlined back in one edit. Objection: projects that never migrate stay frozen. → Same
  as above.
- User Advocate: one predictable edit beats L's duplicated rules and M's silent
  overwrites. Objection: criterion a only partly met. → Same as above.
- Operator: the smallest mechanism, and the most reversible. Ship the detection with the
  change, not after. Objection: the benefit is opt-in. → Adopted: detection ships in the
  same change.

## Decision & rationale

Option R. The core of the charter moves to `.claude/references/charter-core.md`, which
`update.sh` already keeps current. `WORKING-CHARTER.md` keeps the path the drop-in
contract names, and holds an `@.claude/references/charter-core.md` import, followed by
the standing constraints and the project's own section. `CLAUDE.md` does not change.
Import depth is two hops.

Answers to the objections:

- **Criterion a, opt-in migration** (all five). Mitigated, not removed. New installs get
  the split automatically. For existing ones, `update.sh` detects a charter without the
  import and prints the exact edit on every sync, not once. The validator in a wired
  project warns, without failing, while the charter still carries the old core, so the
  gap shows in that project's CI on every pull request. A project that ignores both
  stays where it is today: no worse.
- **Criterion b, bytes do not shrink** (Skeptic). Accepted. The criterion asks that bytes
  do not grow and that the budget gains headroom. The import keeps bytes flat, and each
  file gets its own budget.
- **Criterion c, edited cores** (Skeptic). Accepted as a named risk. The printed migration
  step tells the owner to move any local change to the core into their own section
  before replacing it. Nothing is overwritten automatically.

Scores (out of 5, weighted): R 3.9, L 3.1, M 3.0, S 2.4, D 2.0. Confidence: medium-high.
Every persona converged; the residual uncertainty is how many projects will migrate.

## What to build

1. Move lines 8-202 of `WORKING-CHARTER.md` (Part One, Part Two, the general standing
   constraints) to `.claude/references/charter-core.md`, unchanged.
2. `WORKING-CHARTER.md` becomes: a short header, the import, and "This repository".
3. Validator: budget the core file; add it to `ALWAYS_LOADED`, so the import-graph check
   proves it is reachable; warn in a project whose charter still holds the old core.
4. `update.sh`: detect a pre-split charter and print the migration edit on every run.
5. References stay valid: no file links to a charter anchor (checked: zero
   `WORKING-CHARTER.md#` links), and the 14 files that say "the charter's *Efficiency*"
   and similar still mean the charter, which now includes the core by import.
6. Tests and probes: the import is reachable; a pre-split charter is detected; the core
   budget is enforced.

## Consequences & accepted risks

- Existing wired projects stay frozen until each makes one edit.
- A project that edited its core must move those edits by hand.
- Always-loaded bytes stay the same; this frees budget per file, not tokens.
- `.claude/references/` now holds one always-loaded file among on-demand pages. The file
  header and the validator say which is which.

## Revisit trigger

Any of: two pin moves after this ships with no wired project migrated; Claude Code
changes how `@` imports or `.claude/rules/` load; the core file nears its budget.

## Outcome

_Empty at creation._
