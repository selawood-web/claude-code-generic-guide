---
name: efficiency
description: Audit a CCGG-equipped project against the charter's token-efficiency rules — cache-stable auto-loaded context, compaction retention, subagent isolation, model right-sizing — and report concrete fixes. Use when the user says "efficiency", "audit token usage", "why is this burning tokens", or "check the context budget".
when-to-use: efficiency, token audit, context budget, cache stability, token usage, reduce AI cost
allowed-tools: powershell, bash
argument-hint: "[optional: path to the project to audit; default is the current repo]"
purpose: Audit the project against the charter's token-efficiency rules
---

# Efficiency Skill — Token-Efficiency Audit

## Goal

One command that checks a CCGG-equipped project against the four efficiency
rules the charter states (*Efficiency — spend tokens where judgment lives*),
and reports each violation with its concrete fix. Report-only: the audit
changes nothing by itself.

The rules live in the charter; this skill is their on-demand companion — the
detail, the rationale, and the executable checks. Do not restate the rules
elsewhere (single-homed rules).

## Why these four checks

Auto-loaded context is re-sent with **every request of every session**, and
providers bill a cached prefix at roughly a tenth of the normal input rate —
but only while the prefix is byte-identical. Exploration transcripts and
oversized rules poison that cache and crowd the window. The savings stack:
cache-stable rules, bounded exploration, retention-safe compaction, and
right-sized models each cut a different multiplier of the bill. Full research
with sources: `knowledge-base/research/ai-efficiency-techniques-2026.md`
(volatile numbers there carry a staleness note — re-verify before quoting).

## The audit

Run all four checks; collect findings; report at the end, worst first.
Zero findings → one line: "Efficiency audit clean — N checks passed." Nothing else.

### Check 1 — Cache stability of auto-loaded files

Files: `CLAUDE.md`, `AGENTS.md`, `WORKING-CHARTER.md` (plus anything else the
project imports at session start).

```bash
grep -nE '\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b' CLAUDE.md AGENTS.md WORKING-CHARTER.md
grep -niE 'last (updated|generated|synced|run)' CLAUDE.md AGENTS.md WORKING-CHARTER.md
```

- **Finding:** any hit — an ISO date, "last updated" line, counter, or other
  session-varying text in an always-loaded file.
- **Fix:** move the volatile line into an on-demand file (a decision record,
  the memory layer, a research note) and leave a stable reference behind.
  `tools/validate.py` enforces this check in CI; a hit here will also fail there.

### Check 2 — Auto-loaded context size

Budget for the whole always-loaded set: **~15K tokens (≈ 60 KB)**. The set is
everything a session pays for before work begins: `CLAUDE.md` and its imports,
`AGENTS.md`, the charter, `~/.claude/CLAUDE.md`, and the auto-memory index.

```bash
wc -c CLAUDE.md AGENTS.md WORKING-CHARTER.md ~/.claude/CLAUDE.md \
  ~/.claude/projects/*/memory/MEMORY.md 2>/dev/null
```

- **Finding:** combined size above ~60 KB (≈ 4 bytes/token).
- **Fix:** structure, not trimming words — push detail into skill bodies and
  companion files that load only on invocation. The per-file byte budgets in
  `tools/validate.py` are the hard floor; this check watches the total.

### Check 3 — Subagent-isolation rule present

```bash
grep -n "subagent that returns a bounded summary" WORKING-CHARTER.md
```

- **Finding:** the charter copy in this project predates the rule (no hit).
- **Fix:** re-sync the charter from the guide (`update.sh` when live-sync is
  configured, else copy `WORKING-CHARTER.md` from an up-to-date guide clone).

### Check 4 — Model right-sizing defaults in project conventions

Read the *Project Conventions* section of the project's `AGENTS.md`.

- **Finding:** the section names no model-routing default (which model tier
  handles routine/mechanical work, and that escalation is on failure).
- **Fix:** add one line to the project's conventions, e.g.
  `# Models: small/fast tier for exploration and mechanical fan-out; escalate on failure.`
  The rule itself stays in the charter; the convention line only picks this
  project's tiers.

## Report format

```
Efficiency audit — <project> — <n> finding(s)
1. [check] <file:line> — <what> → fix: <the concrete fix>
...
```

One line per finding. No essay. If asked to apply fixes, that is a code/docs
change — the charter gate applies as usual.

## Where this runs automatically

`/wire` runs this audit (report-only) as part of rolling CCGG into another
repository and includes the findings in its report; adopting the fixes stays
the target owner's call.
