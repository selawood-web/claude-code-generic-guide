# pm-skills marketplace — approved at user scope, kept out of CCGG

- **Date:** 2026-11-18
- **Status:** decided
- **Type:** decision
- **Deciders:** repository owner
- **Supersedes / superseded by:** —

## Context

The owner added the `phuryn/pm-skills` Claude Code marketplace and asked whether it
belongs in CCGG. The charter's standing constraints put skills pulled from GitHub out of
scope, so adding any such source is an owner gate (`.claude/references/tool-choice.md`,
*Closing a capability gap*), and the grant has to be recorded with its bounds. Two-way
door: a marketplace is removed with one command and leaves nothing in a repository.

## Criteria

| Criterion | Weight |
|-----------|--------|
| Safety — what the source can execute or exfiltrate | 40% |
| Fit — does CCGG, a generic drop-in layer, gain from it | 30% |
| Cost — context tokens and install-contract complexity added to every wired project | 30% |

Hard constraints: no code or skill from an untrusted source runs; nothing is committed
to CCGG that would land unevenly through `install.sh`.

## Research findings

Vetted on 2026-11-18 from a fresh clone of `phuryn/pm-skills` at v2.3.0
(released 2026-11-08):

- 72 skills in 9 plugins, all plain Markdown. No hooks, no `.mcp.json`, no scripts,
  no shell or install instructions inside any `SKILL.md`. The only executable file is
  the repository's own `validate_plugins.py`, which no plugin loads.
- MIT licence. Single author (Paweł Huryn, productcompass.pm). Outward links are the
  author's newsletter and a few Google Docs templates.
- `live-qa` and `live-polls` default to AskOne, the author's own product, disclosed in
  the changelog. `pm-ai-shipping` is a stub: its skills only say they moved to
  `phuryn/product-engineering`.
- Overlap with CCGG's own `/product-brief`, `/requirements`, `/feature`, `/gbb` and
  `/decide`, which write to `features/` and `decisions/` in CCGG's form; the pm-skills
  PRD, OKR and roadmap skills produce documents outside those conventions.
- Mechanics: a marketplace enters a repository only through `extraKnownMarketplaces`
  and `enabledPlugins` in `.claude/settings.json`. `install.sh` copies that file only
  when the target has none, so a repo-level entry would reach some wired projects and
  not others.

## Options considered

| Option | Benefit | Cost | Risk |
|--------|---------|------|------|
| A. User scope on the owner's machine, recorded here | PM skills in every project the owner opens; nothing enters any repo | One command per machine; this record | Skills bypass CCGG's `features/` and `decisions/` conventions unless the owner routes output there |
| B. Commit into CCGG's `settings.json` | Automatic for wired projects | Charter constraint edited; 72 PM descriptions in every wired project's context; uneven landing via `install.sh` | Wrong altitude for a generic layer; efficiency rule violated |
| Status quo — do not add | No new surface | PM frameworks rebuilt by hand each time | None |

Rejected early: committing it into a single downstream project's settings — not a CCGG
decision; that project records it itself.

## Debate summary

- Champion: safe, well-maintained, fills a real PM gap → accepted.
- Skeptic: GitHub source is out of scope by the charter → true; the owner grants an
  exception for this source only, bounded below.
- Economist: 72 skill descriptions per session is real context cost → accepted at
  user scope, where the owner chooses which plugins to install; rejected at repo scope.
- User Advocate: PM output should land in `features/` and `decisions/` → noted as the
  accepted risk; the owner routes it.
- Operator: `pm-ai-shipping` is dead weight → not installed.

## Decision & rationale

**Option A.** The marketplace `phuryn/pm-skills` is approved as a user-scope install
on the owner's machines. Plugins installed: `pm-execution` and `pm-product-discovery`
first; others from the same marketplace may follow without a new record.
`pm-ai-shipping` is not installed. Nothing from it is committed into CCGG, and the
charter's constraint on GitHub-sourced skills stays as written: this is a bounded
exception for one vetted source, not a change of rule.

Scores: A 90 (safe, fits the owner, cheap); B 45 (safe, poor fit, costly); status quo 60.

## Consequences & accepted risks

- CCGG's catalogue, `install.sh` and `settings.json` are unchanged.
- The grant covers this marketplace at v2.3.0 and later versions of the same source;
  a change of publisher or the appearance of hooks, scripts or MCP servers in it
  re-opens vetting.
- PM documents the plugins produce are not checked by `tools/feature_lint.py`;
  anything that is a feature or a decision still goes through `/feature` or `/decide`.
- Removal: `claude plugin marketplace remove pm-skills` on each machine.

## Revisit trigger

A pm-skills release adds hooks, scripts or an MCP server; or a wired project asks for
the PM skills to be committed, which would be that project's own record.

## Outcome

[Empty at creation.]
