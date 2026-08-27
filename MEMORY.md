# Global Engineering Memory

> This file seeds the AI's global memory with durable engineering principles.
> Append it to `~/.claude/CLAUDE.md` (or pull it in with an `@` import) and
> customize with your own learnings. `~/.claude/CLAUDE.md` is loaded at the
> start of every session, in every project.

---

## Architecture

### Simplicity Default
Prefer the simplest architecture that meets stated requirements. Extract complexity only when a concrete need is proven. Never add components "for future scale" without a measured reason.

### Boring Technology for Foundations
Use battle-tested, widely-supported technology for databases, queues, and infrastructure. Save cutting-edge choices for differentiated application code.

### Team Size → Architecture
- 1-3 engineers: simple monolith, single database
- 4-10 engineers: modular monolith with strict module boundaries
- 10+ engineers per domain: consider service extraction for deployment autonomy

### Data Model Is Architecture
Bad data modeling is the root of most architectural failures. Get the data model right first. Schema migrations are expensive; get the relationships and cardinalities correct upfront.

---

## Code Quality

### Name for the Reader
Code is read 10x more than it is written. Names are the primary documentation. A variable, function, or class name that requires a comment to understand is a bad name.

### One Thing Per Function
A function should have one reason to change. If you find yourself writing "and" in its name, split it.

### Explicit Errors
Functions that can fail should make failure explicit in their signature. Never silently return null for an error — the caller loses the ability to distinguish failure types.

### Fail Fast at Boundaries
Validate all external input at the system boundary. Let bad data fail immediately rather than propagate deep into the system where the root cause becomes obscured.

### Tests Enable Change
Tests are not a quality gate; they are a refactoring enabler. Without tests, you cannot confidently improve code you didn't write. Write tests before refactoring legacy code.

---

## Security

### Parameterize All Queries
SQL injection is still the most common critical vulnerability. Never build query strings by concatenating user input. Always use parameterized queries or ORM.

### Secrets Never in Code
Credentials, API keys, and tokens belong in environment variables or secret management systems. Not in source code, not in logs, not in error messages.

### Authorization at Every Layer
Check permissions in the controller AND the service layer. Never rely on the UI to enforce access control. IDOR (insecure direct object reference) is found by checking the DB query, not the route.

### Constant-Time Token Comparison
Use `hmac.compare_digest` (Python) or equivalent for comparing secrets and tokens. String equality short-circuits and leaks timing information.

---

## Performance

### Measure Before Optimizing
Every performance optimization should be preceded by a measurement that proves the bottleneck exists. Optimize guesses are usually wrong guesses.

### N+1 Is Always Wrong
If you're making one database query per item in a list, you have an N+1 problem. Eager load related data or batch the queries.

### Indexes on Filtered/Sorted Columns
Any column used in WHERE, ORDER BY, or JOIN ON is a candidate for an index. EXPLAIN ANALYZE will tell you if a full table scan is happening.

---

## Operations

### Observability Is Not Optional
For any system in production:
- Structured logging (JSON, with request ID for correlation)
- Error tracking (Sentry, Rollbar, or equivalent)
- Uptime monitoring
- Key business metrics (not just technical metrics)

### Deployment Windows
Deploy Tuesday-Thursday, mid-morning. Never Friday. Never during high-traffic events. Always have a rollback command ready before deploying.

### Zero-Downtime Migrations
Database migrations must be backward-compatible with the previous application version. Use expand/contract pattern: add nullable, backfill, make required — across 3 separate deployments.

---

## Team and Process

### Small PRs Ship Faster
PRs under 400 lines changed receive thorough reviews and merge faster than large PRs. Split large features into incremental, independently deployable slices.

### Commit Messages Are Documentation
The git log is the primary record of why the code looks the way it does. Subject: what changed. Body: why it changed. The diff already shows what changed — don't repeat it.

### Decisions Need Rationale
A decision without its rationale becomes a mystery. Future engineers will change it without understanding the cost. Write the why in comments, ADRs, or memory.

---

## Development Workflow

### Read Before Writing
Before adding to a codebase, understand what's already there. Reading existing patterns takes 15 minutes; rebuilding a wheel takes a day and creates inconsistency.

### Test the Failure Path
The happy path is easy. The failure path is where real bugs live. Per function touched, the bar is one happy path, at least three edge cases (empty input, boundary value, unexpected type), and one failure mode — run against the full suite, not just the new tests.

### Reproduce Before Fixing
Never fix a bug you cannot reproduce. A fix without a reproduction is a guess. A regression test that fails before the fix and passes after is proof.
