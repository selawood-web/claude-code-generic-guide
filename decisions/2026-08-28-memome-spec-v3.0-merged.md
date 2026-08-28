# MemoMe — Canonical Product Specification v3.0 (Merged)

> Appendix to [2026-08-28-memome-product-brief.md](2026-08-28-memome-product-brief.md).
> Merges **PRD v0.3** (Hebrew, April 2026 — full vision, ADHD interaction design,
> preserved verbatim in [2026-08-28-memome-prd-v0.3.md](2026-08-28-memome-prd-v0.3.md))
> with the **Reconciled V2.1 spec** (English, April 2026 — MVP scope, stack, business
> model). Where the two conflict, V2.1's scope decisions win (it is the later,
> deliberately reconciled document, and the viability debate in the brief independently
> reached the same conclusions); v0.3's interaction mechanics win wherever V2.1 thinned
> them out, because they are the ADHD-first substance of the product.

- **Version:** 3.0 — single source of truth going forward
- **Date:** 2026-08-28
- **Product owner:** שחר (Shachar)
- **Supersedes:** PRD v0.3 and Reconciled Spec v2.1 as specs (both kept as sources)

---

## 1. Vision, Problem, Personas

One app that captures any thought — voice, text, list (camera post-MVP) — in under
3 seconds and classifies it automatically, with zero decisions at the moment of
capture. Designed from the ground up for people with ADHD; **Hebrew-first**.

**Problem statement (v0.3, verbatim):**
> "כשאני נזכר במשהו, אין לי דרך פשוטה מספיק ללכוד אותו ברגע שבו אני נזכר.
> עד שאני מוצא איפה לרשום — זה כבר אבד."

**Core failures addressed** (ADHD expert, v0.3): Working Memory (a thought vanishes
in seconds), Prospective Memory (intention without execution), energy dysregulation
(short motivation windows, long shutdowns).

**Persona — Shachar, 32, Product Manager.** ADHD; ideas appear randomly (shower,
driving, meetings) and vanish; "list anxiety" at 50+ open tasks; work bleeds into
home; feels unaccomplished despite being busy. Prefers speaking over typing;
photographs things to remember; short high-energy windows. *"If it takes more than
5 seconds — I won't do it."*

**Anti-persona — Daniel, 35, Project Manager.** Needs Gantt, dependencies,
assignment, audit trails. MemoMe is explicitly not for him. Any feature that serves
Daniel but adds cognitive load for Shachar is rejected.

## 2. Success Metrics

**North Star:** items captured **and completed/closed in the same week**, rising
week over week. Capture without closure = a warehouse app.

| Metric | Target | Source spec |
|--------|--------|-------------|
| Capture latency | < 3s local feel, < 8s including AI round-trip | merged (v0.3 "<5s open-to-saved" + V2.1 latency split) |
| AI acceptance rate | > 75% classifications accepted without manual edit | V2.1 (v0.3 aimed 80% — 75% is the gate, 80% the goal) |
| Smart Triage cost | < 3 taps when triage fires | v0.3 |
| Completion rate | > 60% of captured tasks closed | v0.3 |
| Daily Check-in usage | ≥ 3 times/week | V2.1 |
| Retention | 35% D7 (beta gate 30%), 15% D30 | V2.1 |
| Stability | 0 crashes reported in Sentry | V2.1 |
| Digest/notification open rate | > 70% | v0.3 |

## 3. MVP Scope (12-week build)

The MVP proves one loop: **capture → auto-classify → surface small → close**.
Everything else waits.

### In (P0)
1. **Voice-first capture** — long-press FAB, wave animation (no timer), live
   transcription within ~1.5s, haptic within 2s of tap, auto-save when AI is
   confident. Release = stop.
2. **Text capture** — open field, dynamic placeholder ("מה רצית לזכור?"),
   auto-save after 3s, manual `#hashtag` bypasses triage.
3. **Manual list capture** — Enter = new line, no "add" button; quick-target
   chips (קניות / משימות / רעיונות); AI splits mixed lists.
4. **Async AI triage pipeline** — Whisper (Hebrew-tuned, see §5) + GPT-4o-mini
   JSON-schema output: category, urgency, due-date extraction ("עד יום שלישי"),
   multi-intent splitting ("buy milk and schedule doctor" → two items).
5. **Smart Triage bottom sheet** (v0.3 mechanics, kept in full) — fires only when
   confidence < 75%; 30% screen; domain row → subcategory → AI suggestion;
   "save uncategorized" escape at every step; 5s ignore → auto-file to
   General/Unsorted, sheet closes; after 3 similar choices, auto-mode for that
   content type.
6. **5-category model** — עבודה / בית / בריאות / רעיונות / כללי (Work, Home,
   Health, Ideas, General). Subcategories exist inside domains (v0.3 §5.3) but are
   never required at capture time.
7. **Filtered task list** — top bar: max 3 most-urgent tasks, large; "today" list
   with big checkboxes; "this week" collapsed; always sorted by priority, never by
   entry order. AI proposes priority (דחוף / היום / השבוע / אחר כך), user can
   override.
8. **Ideas folder** — "יש לי רעיון ל..." openers auto-route to Ideas; full
   transcript + date + auto-tag (app / feature / business / creative); browse by
   tag/date/untouched; swipe right = interesting, left = no longer relevant.
9. **Adaptive Daily Check-in** — one gentle prompt/day ("בוקר טוב! מה השתנה?"),
   timing adapts to user activity (default 9:00); **one question per board**, never
   item-by-item: tasks / shopping / meetings / todo, each answerable "הכל בסדר" or
   "פתח ועדכן" (opens the board for direct edit, returns to check-in). Ideas,
   documents, inspiration are never asked about — they are collections, not tasks.
   ≤ 30 seconds if all-OK. Easy time change + Quiet Mode.
10. **Wall of Fame (weekly archive)** — "מה עשיתי השבוע": every completed task with
    timestamp, celebratory animation. Positive reinforcement, never shaming.
11. **Micro-interactions** (v0.3 §5.5, in full) — save: dissolving checkmark 800ms
    + 40ms haptic; category tag slides in 0.5s after save; **Undo toast (4s), never
    a confirm modal**; subtle ring spinner on FAB while AI works (never a blocking
    screen); folder icon pulse showing where an item went; completion: swipe +
    double haptic.
12. **Minimal onboarding** — exactly 3 steps (name → profile choice: "פשוט לכוד" /
    "מאורגן" / "עם תזכורות" → widget install, skippable). No tour. Empty state
    shows the capture buttons + "מה אתה רוצה לזכור היום?"
13. **Progressive disclosure** (v0.3 §4.2) — Tier 1: capture only; Tier 2 after
    first item: bottom nav + folders; Tier 3 after 5 items: Smart Sort; Tier 4
    after 7 days: AI settings, custom categories, bulk ops, Brain Dump.
14. **Graceful degradation / auto-decay** — after 3 days away: "ברוך שובך. AI מיין
    בשבילך — יש לך 3 דברים שצריכים אותך." AI quietly archives stale items; the app
    never shows negative counts or scolds.
15. **Offline-first architecture** — local save always succeeds instantly; AI and
    sync happen async when network allows (see §5).
16. **Manual calendar export** — "Copy to Calendar" copies text + date for manual
    paste. No OAuth2 in MVP.
17. **Time externalization** — deadlines shown as relative distance ("בעוד 3
    ימים"), not static dates.
18. **Shopping Cart Mode** (v0.3 module C, in full — owner decision 2026-08-28
    overriding V2.1's deferral; low complexity, daily value) — normal mode: a
    shopping list in בית/קניות, add by voice ("תוסיף חלב") / text / list. "אני
    בסופר" switches to shopping mode: every item large with a bold checkbox; tap =
    item dims to light grey + green ✓ ("בעגלה") but **stays in the list**; untapped
    items stay white and prominent — what's missing is obvious; tap again = back to
    white ("טעות, לא לקחתי"). Finish: "כל הפריטים בעגלה!" → "לשמור כרשימה קבועה?"
    → clear. Recurring staples loadable into a new list in one tap.

### P1 (in MVP if timeline holds, first out if it slips)
- **Home-screen widget** — capture without opening the app.
- **Smart Daily Digest** — morning push: the 3-5 most urgent items, AI-chosen.
  (The Daily Check-in is the P0 habit loop; the Digest is its push-notification
  complement.)
- **Brain Dump Mode** — long-press > 3s: continuous recording, wider wave as the
  visual cue; AI splits by pauses and content; review list; "save all" in one tap.
- **Friction-free snooze** — "מחר בבוקר" in two taps ("כשאני בבית" needs GPS —
  deferred with it).

### Deferred (v1.1+, in priority order)
1. **Camera capture + OCR** — product recognition, handwritten-list splitting,
   **document → task with attachment** (municipal fine → "תשלום קנס" with the photo
   attached; invoice, prescription, business card). Highest-complexity module;
   deferred by V2.1 and by the viability debate. (Adding a product to the shopping
   list by camera waits with this module; voice/text/list entry cover the MVP.)
2. Weekly Sweep ("עדיין רלוונטי?" swipe review) and Recurring Detection.
3. Automatic 2-way Google Calendar sync (OAuth2).
4. v2+: voice search, GPS contextual reminders, in-camera product price search,
   list sharing, comfort mode (large font / high contrast), repeated-idea
   detection.

### Never (anti-persona guardrail)
Gantt/dependencies, task assignment, audit trails, gamification scores
(anxiety-inducing), confirm-before-save modals, mandatory category selection at
capture.

## 4. ADHD-First Design Principles (binding for every UX decision)

1. **Zero-friction capture** — no category selection before recording; everything
   can land in inbox first.
2. **Visual simplicity** — one dominant primary action per screen; ≤ 5 top
   categories; functional colors only (cool blues = work, warm oranges = home);
   buttons ≥ 48dp; minimal text.
3. **Positive reinforcement** — haptics, micro-animations, confetti on completion;
   "נשמר", never "אשר"; no shaming, ever.
4. **Contextual isolation** — work does not bleed into home.
5. **Graceful degradation** — absence is met with triage done *for* the user, not
   a backlog count.
6. **Time externalization** — relative time everywhere.
7. **Triage after capture, never during** — and never a confirm dialog where an
   undo toast will do.
8. **Empty states instruct** — an empty screen shows the way to capture, never
   just "אין פריטים".

## 5. Technical Architecture

| Component | Technology | Rationale / conflict resolution |
|-----------|------------|--------------------------------|
| Frontend | **Flutter (Dart 3.x)** | V2.1 decision stands over v0.3's React Native — single codebase, strong animation support. Verify RTL/Hebrew layout quality in week 1 spike. |
| Backend / DB | **Supabase (PostgreSQL)** + local store | V2.1 decision stands over v0.3's local-only SQLite. Resolves the debate's hardest objection: a memory-impaired user's external memory must survive a lost phone. Offline-first: local write first, sync when online. |
| Transcription | **OpenAI Whisper**, evaluated against **ivrit.ai Hebrew fine-tunes** and ElevenLabs Scribe in a week-1 bake-off on real noisy phone Hebrew | v0.3 named Whisper; Hebrew accuracy on real-world audio is the single most load-bearing technical assumption — measure before committing. Local on-device fallback when offline. |
| Classification | **OpenAI GPT-4o-mini**, JSON-schema output | Both specs agree. Confidence score drives triage (< 75% → bottom sheet). |
| Vision/OCR | — (v1.1+) | Deferred with camera capture. |
| Error monitoring | **Sentry** | Backs the 0-crash exit criterion. |
| Analytics | **PostHog** | Funnel drop-offs, retention, and the v0.3 KPI events (`classification_accepted`, `triage_steps_count`, `capture_source`, `completion_rate`, `notification_open_rate`). |

**Data model — `items` table** (merged): `id`, `user_id`, `type`
(voice/text/list/task/idea), `raw_audio_path`, `transcript`, `body`, `title` (AI),
`category` + `folder_path`, `priority`, `status`
(captured/processed/classified/completed/archived — v0.3's `done` folded into
status), `due_date`, `confidence_score` (0-1), `triage_status`
(auto/confirmed/manual/unsorted), `hashtags[]`, `ai_tags[]`,
`detected_entities[]`, `attachments[{file_url, file_type, thumbnail_url}]`
(schema ready now, populated when camera ships), `items[{text, order, done}]` +
`is_split` for lists, `language`, `duration_sec`, timestamps.

## 6. Business Model

Freemium (V2.1):
- **Phase 1 (launch):** 100% free through the 12-week rollout and beta, to the
  1,000-user milestone.
- **Phase 2:** Free tier — 30 captures/month, basic triage. **Pro $4.99/month** —
  unlimited captures and voice, priority AI processing. (Undercuts Numo ~$16/mo
  and Voicenotes ~$8.33/mo-equivalent; see brief's market landscape.)

## 7. Timeline (12 weeks)

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Setup + spikes | Flutter project, Supabase schema, CI/CD; **two de-risking spikes: Hebrew ASR bake-off on noisy phone audio; Flutter RTL layout check** |
| 2-4 | Core loop | Capture Hub UI (voice/text/list), local storage, voice recording, micro-interactions + undo toast (v0.3's "week 1: does haptic+checkmark create the 'saved' feeling?" test happens here, before any AI logic) |
| 5-6 | AI pipeline | Whisper + GPT-4o-mini edge functions, offline queue, error fallbacks, Smart Triage sheet with confidence threshold |
| 7-8 | Features | Item splitting, tagging, Ideas folder, Daily Check-in, Wall of Fame, filtered task list, Shopping Cart Mode |
| 9-10 | Polish | Haptics, completion animations, bug fixes, Sentry + PostHog, P1 features if green |
| 11 | Beta | Closed beta, 20 ADHD users, watch PostHog drop-offs |
| 12 | Launch | App Store + Google Play |

## 8. Risk Management (merged)

| Risk | Level | Mitigation |
|------|-------|-----------|
| Hebrew ASR/classification accuracy on real speech | High | Week-1 bake-off (Whisper vs ivrit.ai vs Scribe); preview before save; Smart Triage as fallback; triage learning; misclassified → General + one-tap correction |
| Solo/lean-team timeline slips | High | P1 list is the pre-agreed cut line; scope discipline is the mitigation, not overtime |
| Onboarding drop-off | High | Max 3 steps, no tour; PostHog pinpoints the friction step |
| Inbox anxiety / unclassified pile-up | High | Check-in + digest + auto-decay; item unclassified 2 hours → AI forces a classification |
| AI latency > 3s | Medium | Local-first save, skeleton UI, async processing, subtle FAB spinner |
| Whisper API too slow | Medium | Local on-device transcription fallback |
| Notifications annoy | Medium | One check-in/day, adjustable time, Quiet Mode |
| No loop closure (warehouse app) | Medium | Completion ritual + check-in + Wall of Fame; North Star tracks it weekly |
| API model deprecation/pricing churn | Medium | Single classification provider behind an edge function; swappable |

## 9. Exit Criteria for V1 Launch

1. 1,000 registered beta users
2. 30% retention at day 7
3. 75% AI classification acceptance (no manual edits)
4. Zero crashes in Sentry
5. 20 pieces of positive qualitative beta feedback

**Personal gate (precedes all of the above):** the product owner's own North Star —
his items captured *and closed* in the same week — rises for 3 consecutive weeks of
self-use. If the app doesn't survive its own builder's Tuesday, the beta doesn't
start.
