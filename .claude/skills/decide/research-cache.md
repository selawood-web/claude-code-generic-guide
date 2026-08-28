# Research Cache — dated findings, reused until stale

The single home for the research-cache contract used by `decide` (Step 4) and
`product-brief` (Step 3). The cache does not weaken the AGENTS.md rule that
"what exists now" is never answered from memory: a cache entry is *dated
evidence from a real search*, not model memory — and past its staleness window
it counts as memory again and must be re-searched.

## Location & naming
`knowledge-base/research/<topic-slug>.md` in the project root. One topic per
file, updated in place. Created lazily on first use (like `decisions/`); not
copied by the installer.

## Entry format
```markdown
# <Topic>

- **As of:** YYYY-MM-DD
- **Staleness class:** volatile | stable
- **Searched for:** [the decision/brief that triggered it, with link]

## Findings
[Dated findings with sources — the same content the record's Research section gets]
```

## Staleness classes
| Class | Covers | Re-search after |
|-------|--------|-----------------|
| volatile | prices, versions, free-tier limits, market offerings | ~30 days |
| stable | fundamentals: architecture limits, protocol behavior, market structure | ~90 days |

Either way: if the finding is load-bearing for a one-way-door decision, verify
it live regardless of age — the cache saves repeat searches, never diligence.

## Protocol
1. **Before searching:** check `knowledge-base/research/` for the topic. Fresh
   entry → use it, cite it as `[cached research, as of YYYY-MM-DD]` in the
   record, and skip the duplicate search. Stale entry → re-search, then update
   the file (keep the old date in a one-line history if the facts changed).
2. **After searching:** write or update the topic file with today's date. Ten
   minutes of research saved once pays for the file forever.
3. Cache entries feed decision records; they never replace them — the record
   snapshots what was known at decision time, the cache stays current.
