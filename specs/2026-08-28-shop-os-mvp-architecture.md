# Shop OS MVP — Architecture

- **Date:** 2026-08-28
- **Status:** accepted (owner delegated to recommendations)
- **Source spec:** [2026-08-28-shop-os-mvp-requirements.md](2026-08-28-shop-os-mvp-requirements.md)

## Requirements extraction

**Functional core (from spec):** shop setup + material list; material-aware
versioned quoting; branded PDF/link output; job costing (quoted vs actual);
inventory with offcuts; cut optimization; CSV export.

**Non-functional:** scale is small and known — hundreds of shops, 1–5 users each,
tens of quotes/shop/month; no burst traffic. "Too slow" = quote editing that lags
a spreadsheet; optimizer runs may take seconds (async is fine). Availability:
business-hours critical for quoting; a short nightly window is acceptable.
Consistency over availability (money numbers must be right). Compliance: none
beyond standard data protection; no card data stored (Stripe hosted checkout).

**Constraints:** 1–2 builders; Railway deploy; subscription ~$75/mo; optimizer
built in-house behind an interface ([decision](../decisions/2026-08-28-cut-optimizer-build-vs-buy.md)).

## Architecture style: modular monolith

One deployable Next.js app + one Postgres. Justification: single domain, tiny
team, no independent-scaling need; every extra service is 3am operational cost
with no payoff at this scale. Modules are enforced by folder boundary + lint
rule, not by network.

```
                        ┌─────────────────────────────────────────┐
                        │        Railway                          │
 Shop owner ──HTTPS──▶  │  ┌───────────────────────────────────┐  │
 Client (quote link) ─▶ │  │ Next.js app (TypeScript, strict)  │  │
                        │  │ ┌───────────┐ ┌────────────────┐  │  │
                        │  │ │ web/ui    │ │ modules/       │  │  │
                        │  │ │ (App      │ │  quoting       │  │  │
                        │  │ │  Router)  │ │  costing       │  │  │
                        │  │ └───────────┘ │  inventory     │  │  │
                        │  │               │  optimizer ────┼──┼──┼── OptimizerEngine
                        │  │               │  pdf           │  │  │   interface (in-house
                        │  │               │  export (CSV)  │  │  │   guillotine engine;
                        │  │               │  billing       │  │  │   swappable)
                        │  │               └────────────────┘  │  │
                        │  └──────────────┬────────────────────┘  │
                        │                 │ Prisma                │
                        │        ┌────────▼────────┐              │
                        │        │ Postgres        │              │
                        │        │ (daily backups) │              │
                        │        └─────────────────┘              │
                        └─────────────────────────────────────────┘
                          External: Stripe (checkout/webhooks),
                                    Resend (magic-link email), Sentry
```

## Technology choices

| Component | Choice | Why | Rejected |
|-----------|--------|-----|----------|
| App | Next.js (App Router), TypeScript strict | One deployable, SSR for quote links, largest AI-assisted-dev ecosystem; matches repo conventions | Rails/Django (context-switch cost for TS team); separate SPA+API (two deployables, no benefit) |
| DB | Postgres (Railway managed) via Prisma | Relational money data; managed backups; migrations built in | SQLite — the [prior SQLite-vs-Postgres record](../decisions/2026-08-28-sqlite-vs-postgres-next-app.md) chose it for a solo VPS where self-managed Postgres ops were the decisive objection; Railway *managed* Postgres removes that ops tax, and a paying-SaaS ledger warrants it. Not a reversal — a different context. NoSQL (data is inherently relational) |
| Auth | Auth.js, email magic links | Shops hate passwords; no per-user vendor fee | Clerk (per-MAU cost vs $75/shop revenue); passwords (support burden) |
| Billing | Stripe Checkout + customer portal, one price | No card data in-house; portal handles cancel/update | Custom billing UI (needless scope) |
| PDF | @react-pdf/renderer server-side | No headless Chromium in the container; deterministic output | Playwright print (heavy image, slower cold start) — fallback if layout fidelity disappoints |
| Optimizer | In-house TS module, worker thread, behind `OptimizerEngine` | Per build-vs-buy decision; worker keeps event loop free | — |
| Email | Resend | Magic links + quote-sent notifications, trivial API | SES (setup friction disproportionate at this scale) |
| Observability | Sentry + structured pino logs + `/healthz` | Architecture defaults: non-optional | — |

## Data model sketch

```
Shop 1─* User            Shop 1─* Client
Shop 1─* Material (name, unit, currentCost, grainRequired)
Shop 1─* Quote 1─* QuoteVersion (locked on send) 1─* QuoteLine
                                 (QuoteLine snapshots unitCost — no retro-pricing)
Quote *─1 Client
QuoteVersion 1─0..1 CutPlan (layouts JSON, sheetCount, wastePct)
Quote(accepted) 1─0..1 Job (baseline = accepted QuoteVersion)
Job 1─* ActualEntry (kind: material|labor, qty, cost, loggedAt)
Shop 1─* InventoryItem (material ref, qty, isOffcut, dims, sourceJob?)
```

Source of truth: Postgres for everything; Stripe for subscription state (mirrored
to `Shop.subscriptionStatus` via webhook, webhook-replay tolerant/idempotent).
Access patterns are shop-scoped — every table carries `shopId`, every query
filters by it (enforced in a repository layer; the security boundary).

## Security boundary
- Trust ends at: quote links (public, capability URL with unguessable token,
  client-facing fields only — spec story 3), Stripe webhooks (signature-verified),
  CSV imports (parsed, validated per-row, never executed).
- All other routes require a session bound to a `shopId`; cross-shop access is the
  vulnerability class to test for explicitly.
- No secrets in logs; costs/margins never serialized into the public quote view model.

## Trade-off analysis

| Decision | Benefit | Cost | Risk |
|----------|---------|------|------|
| Modular monolith | Operable by 1–2 people | Discipline needed at module seams | Seams erode → lint-enforced import rules |
| Single Postgres | Simplicity, consistency | SPOF | Railway daily backups + tested restore runbook; acceptable at this availability target |
| In-process optimizer worker | No queue infra | Long runs share the dyno | Cap parts count; async job row + polling UI; extract to service only if measured |
| react-pdf | Light container | Layout fidelity ceiling | Fallback path to Playwright documented |

## Failure modes & top risks
1. 🟡 **Postgres down = app down.** Accepted SPOF at this scale. Mitigation:
   backups verified by a monthly restore drill; recovery = Railway restore, RTO
   under an hour.
2. 🟡 **PDF/optimizer failure blocking quotes** — spec forbids this. Mitigation:
   both are isolated calls with explicit error states; the quote's numbers render
   and send as plain view even when PDF/optimizer fail (degrade path is a
   first-class UI state, tested).
3. 🔵 **Stripe webhook loss → wrong subscription state.** Mitigation: idempotent
   handlers + nightly reconciliation job against Stripe API.
4. 💡 **Migration path:** optimizer swappable by interface; PDF renderer
   swappable; Next.js/Postgres are the hard-to-reverse pair — both boring and
   proven, chosen deliberately.

## Critic checklist (passed)
Simplest design meeting requirements ✔ (one app, one DB); operable by stated team
✔; SPOF named and accepted ✔; scales vertically first, horizontally later via
stateless app ✔; runbook = Railway deploy/rollback + restore drill ✔; security
boundary drawn ✔; designed for actual scale, not hypothetical ✔.

## Build order (first deployable slice)
1. **Milestone 0 (deploy first):** scaffold app + Postgres + `/healthz` + Sentry,
   deployed on Railway before any feature code — deploy-steward obligation.
2. Auth + shop setup + material list w/ CSV import (spec story 1).
3. Quoting + versioning + snapshot pricing (story 2) — the spreadsheet-beating test.
4. Quote PDF + public link (story 3).
5. Job costing (story 4) — the retention feature.
6. Inventory + offcuts (story 5), cut optimizer (story 6), CSV export (story 7).
7. Stripe billing last before launch (no paywall while iterating with pilot shops).

**Note:** the application is a new project — it gets its own repository (via
`/git-steward`), not this guide repo. This document and its spec travel with the
decision records; the new repo links back.
