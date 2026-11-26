# Project memory

## Learned

- Probe runs test committed HEAD: `tools/audit_probes.py` unpacks `git archive HEAD`, so a run started before the commit does not cover the change. Commit first, then run probes. A probe can also pass only because of a bug, so re-read any probe whose mutation a fix touches. — tags: #tooling #testing
