# SQLite vs Postgres for single-server web apps

- **As of:** 2026-08-28
- **Staleness class:** stable (WAL mechanics, hosting landscape shape) with volatile details (free-tier caps, versions)
- **Searched for:** [SQLite vs Postgres for the next app](../../decisions/2026-08-28-sqlite-vs-postgres-next-app.md)

## Findings
- SQLite WAL mode: unlimited concurrent readers, exactly one writer at a time;
  lock errors negligible under ~20 concurrent writers, p99 degrades beyond;
  comfortable for single-server apps to roughly ~10k DAU. Production pragmas:
  `journal_mode=WAL`, `busy_timeout=5000`, `synchronous=NORMAL`.
- Use SQLite ≥ 3.51.3 — a WAL-reset corruption bug in 3.7.0–3.51.2 was fixed
  2026-03 (volatile: version floor will move).
- Mainstream frameworks (Rails, Laravel, Phoenix) ship production-grade SQLite
  support; Litestream makes streamed backup to object storage routine — but
  replication is not a *tested restore*.
- Postgres is the only option for multi-instance deployment, read replicas,
  multi-region, or thousands of concurrent write tx/s.
- Self-hosted Postgres on an existing VPS: $0 extra cash; operator owns backups
  (pgBackRest/WAL-G + restore drills), major-version upgrades, pooling
  (PgBouncer), disk.
- Managed Postgres free tiers (Neon, Supabase, Aiven): permanent but 0.5–5 GB
  caps, compute suspends when idle, limited/no automated backups; 5–20x cost
  premium vs self-hosted once outgrown (volatile: tiers change often).

Sources: sqlite.org/wal, intuitem, javacodegeeks, mako.ai, goilerplate,
adhdecode, sesamedisk, koyeb, bytebase, swyftstack, selfhost.dev (2026-08-28).
