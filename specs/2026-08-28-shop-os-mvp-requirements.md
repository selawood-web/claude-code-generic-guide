# Shop OS MVP — Requirements

- **Date:** 2026-08-28
- **Status:** accepted (owner went with recommendations, 2026-08-28)
- **Source verdict:** [Product brief — Shop OS](../decisions/2026-08-28-shop-os-product-brief.md) (Pivot, decided)

## Problem Statement
Owners of 1–5 person cabinet and custom furniture shops quote jobs, track materials,
and do the books at night with spreadsheets and QuickBooks. Pricing is the trade's
admitted #1 pain: quotes take hours, material costs drift, and nobody knows whether
the last job actually made money. Existing tools are either enterprise CAM suites
(~$30k, CNC-oriented) or point tools (free cut optimizers, one-time cut-list apps)
that don't connect quoting to real costs. Shop OS closes the loop: material-aware
quote → job execution → quoted-vs-actual margin, in one affordable web app.

## Success Criteria
- [ ] A new shop completes setup (hourly rate + material price list) in under one
      evening (~2 hours), unassisted.
- [ ] Producing a branded quote is measurably faster than the shop's spreadsheet
      (target: a typical cabinet/furniture quote in under 15 minutes).
- [ ] The shop sees quoted-vs-actual margin on its first completed job.
- [ ] All shop data (materials, quotes, jobs) exportable as CSV from day one.
- [ ] Running deployed (Railway) from the first milestone — "done = executing deployed".

## User Stories (MVP scope)

### 1. Shop setup
As a shop owner, I want to enter my shop hourly rate, overhead markup, and material
price list quickly, so that quotes are grounded in my real costs.

Acceptance criteria:
- Given a new account, when I finish the guided setup, then I have a shop rate,
  a default margin %, and ≥1 material entered, and I can immediately start a quote.
- Given a supplier price sheet as CSV, when I import it, then materials (name, unit:
  sheet/board-foot/linear-foot/each, cost) are created without retyping.
- Given an empty or malformed CSV row, when I import, then the row is flagged and
  skipped — never silently dropped or zero-priced.

### 2. Material-aware quoting
As a shop owner, I want to build a quote from parts (materials + labor hours), so
that the price protects my margin instead of being a gut guess.

Acceptance criteria:
- Given my material list, when I add a line item (e.g. 3 sheets ¾" maple ply +
  6 shop hours), then material cost, labor cost, markup, and price compute live.
- Given a finished quote, when I mark it sent, then it is locked as version 1;
  edits create a new version (quotes are commercial commitments — history is kept).
- Given a material whose price I update later, then existing quotes keep the price
  they were quoted at (no silent retro-pricing).
- Edge: a quote with zero labor hours or zero materials warns before sending.

### 3. Branded quote output
As a shop owner, I want to send the client a clean branded quote (PDF or link), so
that I look professional without leaving the tool.

Acceptance criteria:
- Given a quote, when I export, then a PDF with my logo, line items (client-facing
  descriptions, not internal costs), total, and validity date is produced.
- Given a quote link, when the client opens it, then they see the client-facing
  view only — internal costs and margin are never exposed.

### 4. Job costing (the retention feature)
As a shop owner, I want to log actual materials and hours against a job, so that I
see the true margin and quote the next job better.

Acceptance criteria:
- Given an accepted quote, when I convert it to a job, then quoted amounts become
  the baseline and I can log actuals against it.
- Given logged actuals, when I view the job, then quoted vs actual (materials,
  labor, margin) is shown, updating as I log.
- Given a completed job, then it appears in a job history list with final margin —
  green/red at a glance.
- Edge: actuals can exceed quoted without blocking (reality wins); a job with no
  actuals logged after its end date is flagged, not auto-closed.

### 5. Material & offcut inventory
As a shop owner, I want to know what sheet goods and lumber I own, including usable
offcuts, so that I stop re-buying material I already have.

Acceptance criteria:
- Given a job consuming materials, when I log actuals, then on-hand quantities
  decrement; receiving a purchase increments them.
- Given a cut plan leaving a usable offcut (≥ shop-configurable minimum size), when
  the job completes, then the offcut can be added to inventory in one tap.
- Given a new quote, when a required material is in stock (full stock or offcut
  large enough), then the quote flags it — "you already own this".
- Edge: negative on-hand is allowed but visibly flagged (shops won't log perfectly).

### 6. Cut optimization
As a shop owner, I want a sheet layout for a quote's parts list, so that the quote's
material count is realistic, not a guess.

Acceptance criteria:
- Given a quote's parts list (L×W×qty per material), when I run optimize, then I
  get sheet layouts, sheet count, waste %, and the quote's material lines update to
  the computed count on confirmation.
- Given kerf width and grain-direction constraints per part, the layout respects them.
- Edge: a part larger than the stock sheet errors clearly, naming the part.

### 7. Data out
As a shop owner, I want my numbers in my accounting system without retyping, so that
the tool fits my existing bookkeeping.

Acceptance criteria:
- Given any list view (quotes, jobs, materials, inventory), when I export, then I
  get a well-formed CSV.
- Given a completed job, when I export it, then a QuickBooks-importable invoice CSV
  is produced. (Direct QuickBooks Online API sync: see Open Questions.)

## Out of Scope (v1)
- **AI photo-to-quote** — deferred by verdict; reopens at ≥3-month paid retention.
- CNC output (DXF/G-code), CAD/design of any kind — quotes are parts lists, not drawings.
- Scheduling/calendar, CRM, email marketing, client messaging.
- Multi-shop/multi-location, roles & permissions beyond owner + employee.
- Native mobile apps (responsive web only), offline mode.
- Payments/deposits collection, e-signatures.
- Analytics dashboards beyond the job-margin history list.
- Lumber price feeds — shop-entered prices are the system of record (verdict commitment).

## Resolved Questions (owner accepted recommendations, 2026-08-28)
1. **Beachhead**: cabinet shops first — workflow is more uniform and the documented
   gap is theirs; furniture makers follow.
2. **QuickBooks**: CSV export at launch; QBO API sync is the top v1.1 retention
   follow-up.
3. **Pricing**: single tier ~$75/mo at launch; split tiers only with evidence.
4. **Cut optimizer**: settled by build-vs-buy `/decide` pass — see
   [decisions/2026-08-28-cut-optimizer-build-vs-buy.md](../decisions/2026-08-28-cut-optimizer-build-vs-buy.md).

## Constraints
- Team: 1–2 builders, AI-assisted; no enterprise sales motion; subscription $50–100/mo.
- Deployment: Railway from first milestone (deploy-steward owns this); structured
  logging, error tracking, health endpoint non-optional (architecture defaults).
- Trust rules from the verdict: shop-entered prices are the system of record; any
  future AI output is a labeled draft requiring line-by-line confirmation; data
  export is a day-one obligation.
- Quoting is business-critical: quote creation and viewing must degrade gracefully —
  a failed PDF render or optimizer run never blocks seeing/sending the numbers.
- Onboarding budget: the entire first-run flow must fit one evening; every required
  setup field must justify itself against that budget.
