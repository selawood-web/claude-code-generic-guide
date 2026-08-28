# MemoMe — ADHD-first thought capture and closure app

- **Date:** 2026-08-28
- **Status:** decided
- **Type:** product-brief
- **Deciders:** שחר (product owner) — confirmed 2026-08-28, with one amendment:
  Cart Mode pulled back into the MVP
- **Supersedes / superseded by:** —

## Context

The product owner, who has ADHD and memory difficulties, wrote two specs for
"MemoMe": a Hebrew PRD v0.3 (full vision — 4 capture modes, AI auto-classification,
~22 features marked P0, 7-week solo prototype, React Native + local-only SQLite)
and a later English "Reconciled V2.1" spec (12-week MVP, camera/OCR and cart mode
deferred, Flutter + Supabase, freemium model). The question this brief answers:
is MemoMe worth building, and in what shape? The trigger is a personal pain — the
owner is the primary persona — which makes the problem real by construction but
makes generalization the open question. Stakes: months of solo build time;
reversibility is high pre-launch, low once real user data accumulates.

## Criteria

| Criterion | Weight |
|-----------|--------|
| Solves the owner's capture-to-closure problem in daily use | 40% |
| Buildable within the owner's real energy/time budget | 25% |
| Differentiated vs. existing tools (real, not cosmetic) | 20% |
| Path to other users / revenue | 15% |

Hard constraints: capture must feel < 5s end-to-end; the builder has ADHD — the
build plan itself must survive ADHD energy windows; Hebrew is the product's first
language.

## Research findings

Researched live 2026-08-28:

- **ADHD-app cluster is crowded but complexity-driven churn is the norm.** Tiimo
  (visual planner, freemium), Inflow (CBT/education, subscription), Numo (~$16/mo),
  plus generic Todoist/TickTick. Multiple micro-apps (Focus One, Do-dono) exist
  explicitly because ADHD users abandon complex todo apps — the market's own
  failure mode confirms the PRD's core thesis. Sources:
  [Morgen ADHD apps 2026](https://www.morgen.so/blog-posts/adhd-productivity-apps),
  [Inflow's own roundup](https://www.getinflow.io/post/best-apps-for-adhd),
  [Tiimo alternatives](https://keptmind.com/blog/tiimo-alternatives-2026),
  [super-productivity comparison](https://super-productivity.com/blog/best-adhd-task-management-apps-2026/).
- **AI voice-capture cluster:** Voicenotes ($99.99/yr, strong mobile, multi-surface),
  AudioPen ($33/3mo–$99/yr, web-only, no native mobile). Both organize notes; neither
  closes a task loop, neither is ADHD-first, both are English-centric. Sources:
  [SpokenPlan pricing comparison](https://www.spokenplan.com/blog/voice-notes-pricing-compared),
  [Voicenotes vs AudioPen](https://speakwiseapp.com/blog/voicenotes-ai-vs-audiopen).
  Pricing figures are from secondary comparison sites — re-verify before building
  pricing pages.
- **Hebrew ASR is viable but the load-bearing numbers are clean-benchmark.**
  ivrit.ai publishes Hebrew fine-tunes of Whisper (large-v3 and turbo variants);
  ElevenLabs Scribe claims 3.1% WER on FLEURS Hebrew. Real-world accuracy on noisy,
  code-switched, ADHD-rambled phone audio is **[UNVERIFIED]** — no benchmark found
  for that distribution; must be measured in a week-1 spike. Sources:
  [ivrit.ai on Hugging Face](https://huggingface.co/ivrit-ai),
  [ElevenLabs Hebrew STT](https://elevenlabs.io/speech-to-text/hebrew),
  [Whisper vs Amazon Transcribe for Hebrew](https://medium.com/@DormanDaniel/comparing-whisper-whisper-ft-and-amazon-transcribe-for-hebrew-e297846bdd24).
- **No dominant Hebrew-first, ADHD-first, capture-to-closure app was found** in the
  searches performed. Absence of evidence, not proof of absence — but the niche
  appears open.

## Options considered

| Option | Benefit | Cost | Risk |
|--------|---------|------|------|
| A. Build PRD v0.3 full P0 scope (~22 features, 7 weeks) | Complete vision at once | 4 capture pipelines + OCR + 3 AI integrations, solo | Scope-to-timeline mismatch; ships half-tested everything; core loop unvalidated at week 7 |
| B. Don't build — combine Voicenotes + Tiimo/Todoist | Zero build cost | Daily integration friction forever; no Hebrew-first triage; no closure loop | The actual problem stays unsolved; ~$100-200/yr subscriptions |
| C. Build the narrow loop first: capture → triage → digest → closure; defer camera/OCR, cart mode | Clean signal on the one novel bet; buildable | Vision features wait | Deferred features might be the ones that delight |
| Status quo (WhatsApp/paper/Notes) | Nothing to do | The documented pain continues | — |

Rejected early: B — it fails the 40%-weight criterion (no closure loop, no Hebrew,
friction tax forever) and the owner has already voted against it with his feet.

## Debate summary

- **Champion:** the narrow loop (C) is the only version that answers, within weeks,
  whether zero-friction capture-to-closure changes the founder's own week — the
  micro-app graveyard proves complexity kills exactly this audience → adopted as
  the verdict's shape.
- **Skeptic:** "everything is P0" means there is no P0; Hebrew ASR numbers are
  clean-benchmark, not noisy-phone reality; option A spends its scarcest resource
  on features least connected to the north-star metric → answered by V2.1/v3.0
  scope cut + mandatory week-1 ASR bake-off spike.
- **Economist:** A's marginal features (OCR, widgets, cart mode) cost the most per
  unit of validation; C spends the budget proportionally to what is learned; but
  local-only SQLite quietly compounds a data-lock-in liability → answered by the
  merged spec's Supabase offline-first sync (V2.1 stack decision).
- **User Advocate:** the build plan itself must pass the "5 seconds or I won't do
  it" test — an 18-feature solo sprint is sized for a builder without ADHD, and
  the realistic outcome is abandonment at week 4 with no fallback app installed →
  answered by the 12-week timeline with a pre-agreed P1 cut line and week 2-4
  deliverables that are visible/dopamine-positive (micro-interactions before AI).
- **Operator:** local-only storage with no backup is a standing outage — a lost
  phone erases a memory-impaired user's entire external memory; every feature
  shipped before backup exists makes the eventual loss worse → answered by
  Supabase sync in P0 (offline-first, cloud-backed) rather than "backup later".

Tension noted: Champion/Skeptic argue for minimum surface area while the owner's
v0.3 marks cart mode and document→task as "critical". Resolution: the owner's own
V2.1 spec already deferred both — the debate independently confirmed his
reconciliation rather than fighting it. Amendment on confirmation: the owner
pulled Cart Mode back into the MVP (low complexity, daily value, no AI pipeline —
it widens UI scope, not risk surface); camera/OCR stays deferred.

## Market landscape

Two adjacent clusters, neither occupying MemoMe's position: ADHD planners (Tiimo,
Inflow, Numo — planning/education-first, capture is secondary) and AI voice
capture (Voicenotes, AudioPen — capture-first, no closure loop, no ADHD design
system, English-centric). Differentiation is real on three axes simultaneously:
(1) capture-to-**closure** as the product's spine and metric, (2) ADHD-first
interaction mechanics (undo-not-confirm, triage-after-capture, graceful
degradation, positive reinforcement), (3) Hebrew-first. Any one axis alone is
cosmetic; the combination is not currently served. Pricing headroom: $4.99/mo
undercuts Numo (~$16/mo) and Voicenotes (~$8.33/mo-equivalent).

## Verdict: Go

**Go — in the merged v3.0 shape** ([spec](2026-08-28-memome-spec-v3.0-merged.md)):
V2.1's scope, stack, and timeline as the spine; v0.3's ADHD interaction mechanics
(Smart Triage sheet, micro-interactions, progressive disclosure, per-board
check-in, undo toast, Cart Mode — the last restored to MVP by owner decision) as
the substance; camera/OCR deferred.

Core reason: the problem is real (owner-experienced, market-confirmed), the
differentiation is a genuine three-axis combination, and the narrow scope makes
the bet testable within the builder's actual constraints. The owner's own
progression from v0.3 to V2.1 already performed the pivot the debate would have
demanded; this brief ratifies it and merges the specs rather than re-litigating.

Conditions attached to the Go:
1. **Week-1 Hebrew ASR bake-off** on real noisy phone audio (Whisper vs ivrit.ai
   fine-tune vs ElevenLabs Scribe) — the single most load-bearing unverified
   assumption. If no option reaches usable accuracy, pause and reassess (this is
   the kill criterion, not a speed bump). Runnable kit with recording protocol
   and pass/kill thresholds: [memome-asr-bakeoff/](memome-asr-bakeoff/PROTOCOL.md)
   (prepared 2026-08-28; needs the owner's own recordings to produce the verdict).
2. **Cloud-backed offline-first storage in P0** — never local-only for this user
   population.
3. **The P1 list is the pre-agreed cut line** when the timeline slips — scope
   discipline, not overtime.
4. **Personal gate before beta:** the owner's own captured-and-closed-same-week
   count rises 3 consecutive weeks of self-use.

## MVP definition

The full MVP scope, architecture, timeline, and exit criteria live in the merged
canonical spec: [2026-08-28-memome-spec-v3.0-merged.md](2026-08-28-memome-spec-v3.0-merged.md)
(§3 scope, §5 architecture, §7 twelve-week plan, §9 exit criteria). Source specs:
[PRD v0.3 (Hebrew, verbatim)](2026-08-28-memome-prd-v0.3.md) and the Reconciled
V2.1 spec (provided by the owner; its content is fully folded into v3.0).

## Consequences & accepted risks

- Committing to Flutter + Supabase; switching frontend later is a rewrite.
- OpenAI dependency for classification (mitigated: behind an edge function,
  swappable; accepted: deprecation churn).
- Deferring document→task (camera/OCR) postpones a feature the owner rated
  critical — accepted as the price of a validated core loop; it heads the v1.1
  queue. Cart Mode, initially deferred for the same reason, was restored to the
  MVP by owner decision — the accepted cost is added UI scope in weeks 7-8,
  putting extra pressure on the pre-agreed P1 cut line.
- The 1,000-user beta exit criterion is ambitious for an unmarketed solo app —
  accepted as a launch gate, not a build gate; the personal gate comes first.
- N=1 persona risk: what works for the owner may not generalize — the 20-user
  ADHD beta (week 11) is the first real test.

## Revisit trigger

- Week 1: ASR bake-off fails to produce usable Hebrew accuracy → reopen (pivot
  candidate: text/list-first MVP, voice later).
- Week 6: core loop (capture → classify → close) not working end-to-end → reopen
  scope.
- After 3 weeks of self-use: personal North Star flat or falling → reopen before
  beta spend.
- Market event: a Hebrew-first ADHD capture app ships from a funded team →
  re-evaluate differentiation.

## Outcome

_Empty at creation. Filled when a revisit trigger fires._
