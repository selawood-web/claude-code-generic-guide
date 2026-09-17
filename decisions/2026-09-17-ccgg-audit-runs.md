# Audit runs on this repository — what they reproduced (F002)

- **Date:** 2026-09-17
- **Status:** decided
- **Type:** evidence
- **Deciders:** repository owner
- **Supersedes / superseded by:** —
- **Source feature:** [F002 — Audit skill](../features/F002-audit-skill.md)
- **Source research:** [Testing agent-built systems](../knowledge-base/research/testing-agent-built-systems.md)

## Context

F002's first acceptance criterion is measured by a run, and the ledger promised the
run's report as tracked evidence. That promise was reversed: commit `ec7dc2d`
untracked the report because a committed `candidates/` directory sits in every later
verifier worktree under exactly the filenames a verifier looks for, and one was
observed reading the previous week's batch instead of its own. Reports now stay on
disk, ignored.

This record replaces them as the tracked evidence. It quotes numbers and nothing
else — no `candidates/`, no `findings.jsonl`, no filename a verifier searches for —
so it can never be mistaken for a run's own batch.

## The runs

| | Run 1 | Run 2 |
|---|---|---|
| Stamp | `CCGG-AUDIT-20260916T172615Z` | `CCGG-AUDIT-20260917T182722Z` |
| Commit | `fddcb92` | `9493533` |
| Scope | all | all |
| Findings | 56 — 1 blocker, 33 important, 22 suggestion | 47 — 1 blocker, 21 important, 25 suggestion |
| Unverified | 0 | 3 |
| Gate catch rate at the time | 14 of 23 probes | 41 of 42 probes |
| Duration | 1201 s | ~1670 s |
| Cost | not recorded — an interactive run has no result JSON | same |

Both runs were interactive, which is why neither recorded a cost. Run 1's report and
revision stamp are recoverable from git history at `ec7dc2d^` for anyone who wants the
detail.

## Acceptance criterion 1, measured honestly

The criterion reads: *given this repository at the commit before findings 1–5 of the
research record are fixed, when `/ccgg-audit` runs with no hint about them, then the
report contains a verified finding for each of the five.*

**It is partly met, and the shortfall is in the criterion's premise rather than in the
audit.** By the time a run existed, three of the five were no longer plantable: the
commit "before they are fixed" had passed.

| Research finding | Reproduced by a run? |
|---|---|
| 1 — live sync runs unpinned remote code at session start | **Yes**, run 1, repeatedly and more sharply than the research: a pre-created `CCGG_HOME` supplies both the script and the ref it is checked against (blocker), and `CCGG_REF` accepts a movable name |
| 2 — the pre-compact hook prints to a channel the agent never reads | **No.** Already corrected before run 1, and the research record carries the correction inline |
| 3 — `when-to-use` is not the key the product reads | **No.** Already fixed; the repository now ships `when_to_use`, and a probe holds the hyphenated spelling as a defect |
| 4 — the validator misses 11 of 21 planted defects | **Measured, not found.** The probe harness the audit ships is the mechanised form of this finding; it read 14 of 23 at run 1 |
| 5 — the coverage rule has no enforcement | **Yes**, run 2, as P-003 — no coverage runner, configuration or threshold exists anywhere |

So: two of five reproduced as findings, one mechanised into the harness, two already
fixed before the first run. The criterion as written cannot now be met by any future
run, because it names a commit that is behind us.

## Consequence

- F002's ledger records the reversal and points at this record.
- Acceptance criterion 1 is kept as written for the history it carries, and this record
  is the answer to it. It is not re-openable: a criterion that names a commit already
  passed is measured once.
- The standing measurement of the same property is the probe list, which is enforced on
  every run and grows with every check that lands. That is the criterion worth keeping.

## Revisit trigger

A future audit run on this repository that reproduces research finding 2 or 3 — which
would mean a fix regressed. Otherwise this record is final.

## Outcome

Recorded 2026-09-17. The two runs between them closed 15 findings across pull requests
#63–#70, took the probe catch rate from 14 of 23 to every probe caught, and the test
suite from 352 to over 500.
