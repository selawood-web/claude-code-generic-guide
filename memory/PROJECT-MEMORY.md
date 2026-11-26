# Project memory

## Learned

- Probe runs test committed HEAD: `tools/audit_probes.py` unpacks `git archive HEAD`, so a run started before the commit does not cover the change. Commit first, then run probes. A probe can also pass only because of a bug, so re-read any probe whose mutation a fix touches. — tags: #tooling #testing
- Decided: the charter's portable core moves to `.claude/references/charter-core.md`, imported from `WORKING-CHARTER.md`, over `.claude/rules/` auto-loading and marker rewrites. Reason: `update.sh` already syncs `references/` and never rewrites rule files, so no project edit is overwritten and no rule loads twice. Record: `decisions/2026-11-26-sync-charter-core-separately-from-project-constraints.md`. — tags: #architecture #decision
