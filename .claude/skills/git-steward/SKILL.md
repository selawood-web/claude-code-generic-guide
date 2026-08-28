---
name: git-steward
description: Bootstrap and automatically manage a project's git lifecycle — name a new project, create its GitHub repository, and take ongoing responsibility for commits, branches, and pushes without being asked each time. Use when the user says "new project", "set up git", "create a repo", "put this on GitHub", or wants git handled automatically.
when-to-use: new project, set up git, create a repo, put this on github, init the project, handle git for me, git automatically
allowed-tools: powershell, bash
argument-hint: "[optional: project purpose or preferred name]"
---

# Git Steward Skill

## Goal
Take ownership of the project's git lifecycle: for a new project, name it, initialize
it, and create its GitHub repository; from then on, act as the standing git steward —
committing, branching, and pushing at the right moments automatically, so the user
never has to think about git unless a decision is genuinely theirs.

Related skills (referenced, not duplicated): `commit` writes each commit message,
`pr` opens pull requests. The escalation rules for destructive operations live in
AGENTS.md → "Escalate instead of proceeding" and apply unchanged here.

## Process

### Step 1 — Detect state
- **No `.git` directory** → full bootstrap (Steps 2–5).
- **Existing repository** → skip to Step 5 and adopt stewardship of what exists;
  never re-initialize or rename an existing project unasked.

### Step 2 — Name the project (new projects only)
If the project has no name, derive 2–3 candidates from its purpose — short,
kebab-case, unambiguous, available as a directory name. Present them with one line
of reasoning each and let the user pick or override. The chosen name becomes the
directory name and the repository name; don't proceed unnamed.

### Step 3 — Initialize locally
```bash
git init -b main
```
- Write a `.gitignore` appropriate to the stack (build output, dependencies, env
  files, OS noise). Never commit secrets or `.env` — per AGENTS.md security rules.
- Stub a `README.md` (name + one-line purpose) so the repo is never empty.
- First commit via the `commit` skill conventions: `chore: initial commit`.

### Step 4 — Create the GitHub repository
- Create the repo under the user's account with the chosen name, **private by
  default** — making it public is the user's explicit call, not a default.
- Use whatever GitHub access the session has (the `gh` CLI, or the GitHub tools in
  environments that provide them). Then:
```bash
git remote add origin <repo-url>
git push -u origin main
```
- **Degraded path:** no GitHub access available → say so plainly, finish the local
  setup, and record the repo creation as an open thread — never fake or skip the
  report of what wasn't done.
- Repo created → provision the deploy target next (the `deploy-steward` skill,
  Railway by default): a bootstrapped project without somewhere to run is half-born.

### Step 5 — Standing stewardship (the automatic part)
From this point on, the steward acts without being asked:

| Moment | Automatic act |
|--------|---------------|
| Before the first code change | Create/confirm the working branch per the project's branch convention (charter: fix the branch boundary first; never develop on `main` directly) |
| A milestone verifies (tests pass, feature works, bug fixed) | Commit via the `commit` skill — small, conventional, why in the body |
| After each commit | Push to the working branch (`git push -u origin <branch>`, retry with backoff on network failure) |
| Work is ready for review | Offer the `pr` skill — opening the PR is proposed, not assumed |
| Session ends | Working tree clean or explained: commit what's verified, name what's deliberately left uncommitted |

**Boundaries that never move**, regardless of "automatically":
- No force-push, history rewrite, branch deletion, or anything destructive without
  explicit confirmation first (AGENTS.md → Escalate).
- No pushes to `main`/`master` directly — changes land through a PR the user merges.
- No commit of unverified work — the quality gate runs first; broken code is not a milestone.
- No new public repository, and no publishing of an existing private one, without the user saying so.

### Step 6 — Remember
```
remember: [project] repo is <owner>/<name>, branch convention <pattern> — reason: steward acts need it every session
```

## Anti-Patterns to Avoid

| Anti-pattern | Correct approach |
|--------------|-----------------|
| One giant end-of-session commit | Commit at each verified milestone |
| Auto-committing broken code | The gate passes first; a red suite is not a milestone |
| Pushing straight to main | Working branch + PR, always |
| Silent force-push to "fix" history | Destructive acts get explicit confirmation, every time |
| Public repo by default | Private until the user says otherwise |
| Renaming/re-initializing an existing project | Bootstrap is for new projects; existing ones are adopted as-is |

## Knowledge Extraction
Save conventions the stewardship establishes:
```
remember: [branch/commit/release convention] — reason: [why the project settled on it]
```
