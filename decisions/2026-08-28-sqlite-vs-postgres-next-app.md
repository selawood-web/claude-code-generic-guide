# SQLite vs Postgres for the next app

- **Date:** 2026-08-28
- **Status:** proposed
- **Type:** decision
- **Deciders:** repository owner
- **Supersedes / superseded by:** —

## Context
Choosing the database for the owner's next app: a web app on a single server/VPS,
solo developer, stack already chosen (mainstream, supports both), write load
honestly unknown. Two-way door while data is small; hardens toward one-way as data
and db-specific features accumulate. Full path: the top criterion is room to grow.

## Criteria
| Criterion | Weight |
|-----------|--------|
| Room to scale/grow | 50% |
| Operational simplicity | 25% |
| Cost to start | 15% |
| Ecosystem & features | 10% |

Hard constraints: $0/month until the app earns something; stack already chosen
(assumed mainstream with first-class support for both — flagged for confirmation).

## Research findings
Researched live 2026-08-28:
- SQLite WAL mode: unlimited concurrent readers, exactly one writer at a time; lock
  errors negligible under ~20 concurrent writers, p99 latency degrades beyond that;
  comfortable for single-server apps up to roughly ~10k DAU. Production pragmas:
  `journal_mode=WAL`, `busy_timeout=5000`, `synchronous=NORMAL`. Use SQLite ≥3.51.3
  (WAL-reset corruption bug in 3.7.0–3.51.2, fixed 2026-03).
- Mainstream frameworks (Rails, Laravel, Phoenix, …) now ship strong production
  SQLite support; Litestream makes streamed replication/backup to object storage
  routine.
- Postgres is the only option for multi-instance deployment, read replicas,
  multi-region, or thousands of concurrent write tx/s.
- Self-hosted Postgres on an existing VPS: $0 additional cash, but the operator owns
  backups (pgBackRest/WAL-G with *tested* restores), major-version upgrades,
  connection pooling (PgBouncer), and disk management.
- Managed Postgres free tiers (Neon, Supabase, Aiven): permanent but capped at
  0.5–5 GB, compute suspends when idle, limited/no automated backups; 5–20x cost
  premium vs self-hosted once outgrown.

Sources: intuitem, javacodegeeks, mako.ai, goilerplate (SQLite vs Postgres 2026);
sqlite.org/wal, adhdecode, sesamedisk (WAL concurrency limits); koyeb, bytebase,
swyftstack, selfhost.dev (hosting/free-tier pricing).

## Options considered
| Option | Benefit | Cost | Risk |
|--------|---------|------|------|
| A. SQLite (WAL) + Litestream on the VPS | Zero infra: one file, one backup stream; $0; nothing to patch or pool | Single writer; single-box ceiling | Migration lands mid-growth if load spikes; backup is replication, not tested restore |
| B. Self-hosted Postgres on the VPS | Unbounded growth path (replicas, multi-instance); full SQL/extensions; $0 cash | Solo-owned backups, restore drills, upgrades, pooling — forever | Untested restore or botched upgrade loses data; ops tax paid weekly for scale that may never come |
| C. Managed Postgres free tier (Neon/Supabase/Aiven) | Zero ops; real Postgres | 0.5–5 GB cap; compute suspends when idle | Demo tier wearing a production label; 5–20x cost cliff exactly when the app succeeds |
| D. Status quo / defer (framework default) | No effort now | Decision made by default, without intent | Same migration risk, relocated to a busier, worse moment |

Rejected early: C — suspend-on-idle and the missing-backup caveats fail the
"room to grow" criterion outright; the free tier ends precisely when growth begins.
D — deferring doesn't defer the risk, it only removes intent from it.

## Debate summary
- Champion (argued B): Postgres is the only option never wrong as load grows; wins the 50% criterion outright → answered: raw headroom conceded, but weighted total still favors A once ops cost and realistic horizon are priced in.
- Skeptic (against A): Litestream is replication, not tested restore; a second app process on another box means re-architecture, and "unknown load" is A's worst case → answered by mitigation: quarterly restore drills + defined migration tripwires + portable data layer.
- Economist (against A): the SQLite→Postgres exit lands exactly when you're busiest; "easy exit" must be rehearsed, not assumed → answered by mitigation: migration dry-run rehearsed before the tripwire fires, not after.
- User Advocate (against B): B converts an unvalidated app into a part-time DBA job on day one → accepted as decisive against B at this stage.
- Operator (against B): B's theoretical scalability is worthless if a solo operator's untested backup fails when the VPS dies → accepted as decisive against B at this stage.

## Decision & rationale
**Option A — SQLite in WAL mode + Litestream**, with a rehearsed exit to Postgres.

Weighted scoring (0–10): room to grow — A 7, B 9 (B wins raw headroom; A covers the
realistic single-VPS horizon with a bounded, rehearsed exit); operational
simplicity — A 10, B 4; cost to start — A 10, B 9 (both $0 cash, B costs time);
ecosystem — A 7, B 9. Totals: **A 8.2, B 7.75**.

The deciding logic: with write load unknown, the question is which wrong guess is
cheaper. Guessing small with A and being wrong costs one rehearsed migration at the
moment growth proves real. Guessing big with B and being wrong costs a weekly ops
tax and a solo-operated data-loss risk paid from day one for scale that never
arrives. A's failure mode is a good problem arriving on schedule; B's is a silent
one arriving unannounced.

Conditions attached to the choice:
1. Pin SQLite ≥3.51.3; set `journal_mode=WAL`, `busy_timeout=5000`, `synchronous=NORMAL`.
2. Litestream restore drill in month 1, then quarterly — a backup is a tested restore.
3. Keep the data layer portable: schema migrations in tooling, standard SQL through
   the ORM/query builder, no SQLite-only cleverness in application code.
4. Rehearse the SQLite→Postgres migration dry-run once, early, while data is small.

## Consequences & accepted risks
- Accepted: if growth is sudden and steep, the migration happens under some time
  pressure — bounded by conditions 3 and 4.
- Accepted: no second app server or off-box background worker without migrating first.
- Answered-by-mitigation: restore integrity (condition 2), exit cost (conditions 3–4).

## Revisit trigger
Any of: sustained concurrent writers approaching ~15–20 or "database is locked" /
p99 write-latency alerts; a real need for a second app server, off-box worker, or
read replica; db file beyond a few GB with heavy analytical queries. On trigger:
execute the rehearsed migration and fill Outcome.

## Outcome
_To be filled when the revisit trigger fires._
