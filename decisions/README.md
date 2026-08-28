# Decision Records

Durable records of decisions and product briefs made in this repository — the
in-repo, versioned layer of the knowledge system. Written by the `/decide` and
`/product-brief` skills; recalled at the start of any new decision on the same
topic so nothing gets re-litigated from scratch.

Template, naming convention, and status lifecycle live with the skill:
[`.claude/skills/decide/decision-record.md`](../.claude/skills/decide/decision-record.md).

Lifecycle in one line: `proposed → decided → validated | reversed`, or
`superseded` by a newer linked record. Each record carries a **Revisit trigger**
and an **Outcome** section filled in later — decisions get scored, not just made.

Downstream note: this folder is *not* copied by `install.sh`. Projects that adopt
the skills get their own `decisions/` folder created by `/decide` on first use.

## Index

| Date | Title | Type | Status |
|------|-------|------|--------|
| 2026-08-28 | [Adopt a decision-support system](2026-08-28-adopt-decision-support-system.md) | decision | decided |
