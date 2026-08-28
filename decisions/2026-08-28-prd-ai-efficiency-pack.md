# PRD — CCGG AI-Efficiency Pack

- **Date:** 2026-08-28
- **Status:** Proposed (awaiting owner review)
- **Source research:** [AI efficiency techniques 2026](../knowledge-base/research/ai-efficiency-techniques-2026.md) (+ summary deck in the same folder)
- **Type:** Product requirements document — defines *what* to build; implementation follows the charter gate

## Problem Statement

CCGG makes every session smarter, but not cheaper. The 2026 efficiency research
shows that the largest savings available to a Claude Code infrastructure layer —
cache-friendly context ordering, proactive compaction with retention rules,
subagent isolation, and model right-sizing — are all behaviors CCGG could encode
in its rules, skills, and validator, yet today none of them are systematized.
Users of CCGG-equipped projects burn tokens on re-sent volatile context, heavy
exploration inside the main context window, and frontier-model defaults for
tasks a smaller model handles. The research is done; this PRD turns its four
applicable conclusions into CCGG requirements.

Two research layers are explicitly **not** CCGG's job: serving infrastructure
(quantization, speculative decoding, disaggregation) and model training
(MoE, distillation) — CCGG neither hosts nor trains models.

## Success Criteria

- [ ] Auto-loaded context (`CLAUDE.md`, `AGENTS.md`, charter, memory index) is
      cache-stable: no volatile content (dates, counters, session-specific
      text) in any file loaded at session start; validator enforces it.
- [ ] A session following the new rules performs heavy exploration only in
      subagents; the main context receives bounded summaries.
- [ ] An `/efficiency` audit runs on any CCGG-equipped project and produces a
      concrete findings list with at least the four checks defined below.
- [ ] All existing repo validations stay green; docs/skill catalog/validator
      remain consistent (the "one home per rule" invariant holds).
- [ ] Rollout to other repos requires no new manual steps — `install.sh` and
      `/wire` carry the pack automatically.

## User Stories (MVP scope)

### 1. Cache-friendly context ordering
As a **CCGG user**, I want the auto-loaded rule files to be maximally
prompt-cache-friendly, so that repeated context is billed at the ~10% cached
rate instead of full price every session.

Acceptance criteria:
- Given the rules chain (`CLAUDE.md` → `AGENTS.md` → charter), when any of
  these files is edited, then a validator check fails if it contains
  session-volatile content (current date macros, "last updated" lines that
  churn per session, generated counters).
- Given a project's `AGENTS.md`, when conventions are filled in, then stable
  content (identity, principles, catalog) precedes volatile per-project
  sections, and the docs state why (cache prefix stability).
- Given the memory layer, when `/flush` or `/dream` writes files, then
  session-varying output goes only to on-demand files, never to the
  auto-loaded `MEMORY.md` index beyond genuinely durable facts.

### 2. Compaction with retention rules
As a **CCGG user**, I want compaction guidance that preserves decisions and
constraints while dropping stale narration, so that long sessions stay cheap
without losing the facts that prevent re-work.

Acceptance criteria:
- Given a long session, when context approaches the auto-compact threshold,
  then the rules direct running `/flush` first (durable facts to memory) and
  `/compact` second — order stated in one home and referenced elsewhere.
- Given compaction guidance, when it is written, then it names what must
  survive (branch boundary, standing constraints, open gate state, decisions
  made) and includes the research caveat: over-aggressive summarizing causes
  re-work; compression must earn its place.

### 3. Subagent isolation for exploration
As a **CCGG user**, I want repo-wide searches, research, and multi-file
exploration delegated to subagents by default, so that tens of thousands of
exploration tokens never enter the main context.

Acceptance criteria:
- Given a task requiring broad exploration (unknown codebase area, fan-out
  search, external research), when the rules are followed, then the work runs
  in a subagent that returns a bounded summary (target ≤ ~2K tokens), and the
  main agent proceeds from the summary.
- Given a single-fact lookup (known file/symbol), when the rules are followed,
  then no subagent is spawned — direct lookup, no ceremony.
- Given the charter's Skill Checker, when the new rule is added, then it lives
  in exactly one place (charter *or* AGENTS.md, per the division of labor) and
  the other file references it.

### 4. Model right-sizing and effort control
As a **CCGG user**, I want documented defaults for routing work to the
smallest sufficient model and dialing effort per task, so that frontier-model
pricing applies only where frontier capability is needed.

Acceptance criteria:
- Given the docs, when a user reads the new efficiency page, then it explains:
  smaller/faster models for exploration subagents, effort/reasoning dials for
  routine tasks, frontier models reserved for gate-critical work — with the
  escalate-on-failure rule (route up only when the cheaper tier fails evals or
  the gate).
- Given a skill that spawns subagents, when its instructions are updated, then
  exploration steps state the model-tier default explicitly.

### 5. `/efficiency` audit skill
As a **CCGG user**, I want a single skill that audits my project against all
of the above, so that adopting the pack is one command, not a reading
assignment.

Acceptance criteria:
- Given a CCGG-equipped project, when `/efficiency` runs, then it reports
  findings for at least: (a) volatile content in auto-loaded files,
  (b) auto-loaded context size (flag when the always-loaded set exceeds a
  documented budget), (c) missing subagent-isolation rule, (d) model-routing
  defaults absent from project conventions — each finding with the concrete fix.
- Given zero findings, when the audit runs, then it says so in one line
  (charter voice: no filler).
- Given the skill catalog in `AGENTS.md` and `docs/08-skills.md`, when the
  skill is added, then both list it and the repo validator passes.

## Out of Scope (v1)

- Serving-stack and training-layer guidance (quantization, speculative
  decoding, MoE, distillation) — not CCGG's layer; the research note covers it.
- Batch-API integration for CCGG workflows (e.g. batched eval runs) — defer to
  v2; interactive coding sessions rarely have batchable work.
- Automated token-usage telemetry/dashboards — audit is static analysis only.
- Hook-enforced hard blocks on context size — v1 informs and audits; it does
  not interrupt sessions.
- Retrofitting every existing skill's prose — only skills that spawn subagents
  get the model-tier default; the rest inherit via the one-home rule.

## Constraints

- **One home per rule** — every new rule gets exactly one home (charter for
  *how*, `AGENTS.md` for *what applies here*); all other mentions are
  references. `/reconcile-docs` must pass afterward.
- **Validator discipline** — new checks join the existing repo validator and
  session-start hook; CI and `install.sh`/`/wire` must carry them unchanged.
- **Generic by design** — nothing provider-priced or model-version-pinned in
  rules; volatile specifics (prices, model names) stay in the research note,
  which is marked for re-verification.
- **Charter gate applies** — implementation runs draft → static analysis →
  tests → requirement check; validator changes need the standard edge-case
  tests.
- **No deploy target** — this is a docs/rules/skill change inside a
  documentation repo; the deploy-steward obligation does not attach.

## Risks

- **Rule bloat**: adding efficiency rules grows the always-loaded context —
  the very thing being optimized. Mitigation: rules budget — the pack may add
  at most ~40 lines across auto-loaded files; details live in the skill and
  docs page, loaded on demand.
- **Over-delegation**: subagent-by-default applied to trivial lookups adds
  latency and tokens. Mitigation: the single-fact exception is part of the
  rule, not a footnote.
- **Staleness**: cache mechanics and pricing shift. Mitigation: rules state
  behavior ("stable content first"), never prices; the research note carries
  the volatile numbers and its staleness class.

## Open Questions

1. Auto-loaded context budget: what threshold should the `/efficiency` audit
   flag? Proposal: warn above ~15K tokens for the always-loaded set; owner to
   confirm.
2. Should `/wire` run `/efficiency` automatically as part of rollout
   validation, or leave it manual? Proposal: run it, report-only.
3. Does the subagent-isolation rule belong in the charter (it is a *how*) or
   in `AGENTS.md` (session lifecycle)? Proposal: charter, with a one-line
   reference from the lifecycle section.

## Milestones

1. **M1 — Rules & docs**: charter/AGENTS.md amendments (stories 1–4 rule
   text), new `docs/` efficiency page, `/reconcile-docs` pass.
2. **M2 — Audit skill**: `.claude/skills/efficiency/` with the four checks,
   catalog updates, validator green.
3. **M3 — Enforcement & rollout**: volatile-content validator check with
   tests, `install.sh`/`/wire` verification against a scratch repo.

Each milestone lands independently; M1 alone already delivers most of the
value (behavioral rules), M2–M3 make it verifiable and portable.
