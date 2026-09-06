# Feature Definitions

Definitions of what we are building — one file per feature, versioned with the code it
describes. Written by the `/feature` skill, checked by `tools/feature_lint.py`, and run
in CI through `tools/validate.py`.

Schema, field rules, and the status lifecycle live with the skill:
[`.claude/skills/feature/feature-template.md`](../.claude/skills/feature/feature-template.md).
Tracker renderings live in
[`.claude/skills/feature/tracker-views.md`](../.claude/skills/feature/tracker-views.md).

Lifecycle in one line: `draft → ready → building → shipped`, or `dropped` with the reason
kept in the file. Gaps are tolerated in `draft` and fatal after it.

Downstream note: this folder is *not* copied by `install.sh`. Projects that adopt the
skills get their own `features/` folder created by `/feature` on first use.

## Index

| Id | Title | Status | Owner | Target |
|----|-------|--------|-------|--------|
| [F001](F001-feature-definition-tool.md) | Feature definition tool | building | repository owner | unscheduled |
