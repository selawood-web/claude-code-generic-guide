# Project memory lives in the repository

- **Date:** 2026-11-03
- **Status:** decided
- **Type:** decision
- **Deciders:** repository owner
- **Supersedes / superseded by:** —

## Context

`/flush` and `/dream` wrote project memory to `~/.claude/memory/<project>/`, outside
the repository. Cloud sessions run in containers that are thrown away when they end, so
everything written there was lost with the container. Checked in this repository's own
cloud session: that directory held only the session-end timestamp, with no session log
and no consolidated memory. The capture was manual too. Nothing ran `/flush` unless
someone remembered to. Easy to reverse: the layout is a path in two skills and one hook.

## Criteria

| Criterion | Weight |
|-----------|--------|
| Memory survives a discarded container | 40% |
| No new service, credential or connector | 25% |
| Fits the branch boundary (no direct writes to the default branch) | 20% |
| Small change to existing skills and hooks | 15% |

Hard constraints: no external application (charter, *Standing Constraints*); nothing from
the tree is printed into the prompt by a hook.

## Research findings

- 2026-11-03: Claude Code `Stop` hooks fire each time the main agent finishes a reply,
  not for subagents (`SubagentStop`). Exit 2 hands stderr to Claude as its reason to
  continue, and `stop_hook_active` is true when Claude is already continuing because of a
  stop hook. No hook input carries the context token count, so it is read from the
  transcript. Source: code.claude.com/docs/en/hooks. Whether `Stop` fires under
  `claude -p` was not confirmed.

## Options considered

| Option | Benefit | Cost | Risk |
|--------|---------|------|------|
| Repo-tracked `memory/` folder | Survives any container; reviewed through PRs like the code | Logs are visible to anyone with the repository | Secrets written into a log get committed |
| Write into Claude Code's own auto-memory folder | Loads automatically every session | Still outside the repository, still lost in the cloud | Mixes curated and model-written notes |
| Status quo | None | Memory never accumulates in the cloud | — |

Rejected early: a separate memory branch. It needs its own push path and merge rules, and
the default-branch boundary would still apply to it.

## Debate summary

- Champion: one place, versioned, reviewed. Memory reaches the default branch through the same pull request as the work it describes.
- Skeptic: a planted log in a PR becomes something the agent reads. Answer: it has the same trust as `CLAUDE.md` and `decisions/`, which come from the same tree. `tools/validate.py` scans `memory/` for hidden characters like any other instruction file, and the hook prints only digit-only names.
- Operator: two sessions flushing on the same day on different branches would conflict. Answer: one file per flush, named by its UTC stamp to the second.

## Decision & rationale

Project memory lives at `memory/` in the repository. `/flush` writes
`memory/sessions/YYYY-MM-DD-HHMMSS.md` (UTC) and commits that one file on the session's
own branch, never the default branch. `/dream` consolidates the logs into
`memory/PROJECT-MEMORY.md`, archives them under `memory/sessions/archive/`, and migrates
anything still at the old location. A `Stop` hook, `.claude/hooks/flush-guard.sh`, asks
for `/flush` once per session when the context is past 150k tokens and nothing has been
logged today. The machine-local session-end marker stays where it was: it is only a
timestamp.

## Consequences & accepted risks

- Memory reaches the default branch only when a session's PR merges. A session that
  never opens a PR keeps its log on its branch.
- A log is readable by everyone with the repository. The flush and dream skills forbid
  secrets and personal data in it. This is a stated rule, not a check.
- The flush guard can make a reply run `/flush` and commit a file unasked, once per
  session. `CCGG_FLUSH_GUARD=off` disables it.

## Revisit trigger

Three merged PRs with a session log in them, or the first log that has to be scrubbed for
sensitive content.

## Outcome
