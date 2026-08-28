---
name: deploy-steward
description: Provision a real deployment target — Railway by default — and enforce the execution obligation across the whole lifecycle, so every project runs deployed from its first milestone, not just at the end. Use when the user says "set up deployment", "deploy this", "railway", "make it run in the cloud", or when a project reaches a working milestone with no deploy target.
when-to-use: set up deployment, railway, deploy target, run in the cloud, hosting, make it live, execution environment, deploy from the start
allowed-tools: powershell, bash
argument-hint: "[optional: platform override, or environment to provision]"
purpose: Provision Railway, enforce "done = executing deployed" at every milestone
---

# Deploy Steward Skill

## Goal
Make deployment and execution an obligation, not an afterthought: every project gets
a real deploy target early — **Railway is the preferred platform** — and from then
on, "done" means *verified running in a deployed environment*, at every milestone.
"Works on my machine" is not a milestone.

Related skills (referenced, not duplicated): `deploy` owns the production-deployment
checklist and rollback procedure; `git-steward` owns commits and pushes; `debug`
owns whatever a failed deploy uncovers. Secrets rules live in AGENTS.md → Security.

## The Execution Obligation
A milestone is complete only when all three hold:
1. The quality gate passed locally (charter).
2. The commit is pushed (`git-steward`).
3. **The code executes in a deployed environment** — deployed to staging,
   health-checked, and smoke-tested. A milestone that cannot be deployed is not
   done; it is a `debug` session waiting to start.

## Process

### Step 1 — Detect state
- No deploy config (`railway.toml` / linked project) → provision (Step 2).
- Existing deploy target → adopt it as-is and enforce the obligation (Step 3);
  never switch platforms silently — a platform change is a `/decide` decision.

### Step 2 — Provision (Railway, unless the user overrides)
1. Verify access: the Railway CLI is installed and authenticated (`railway login`
   / an active token). **Cost check first:** Railway bills by usage — confirm the
   user's plan and expected cost *before* creating anything.
2. `railway init` — creates the project and `railway.toml`, links the local repo.
3. `railway environment new staging` — staging exists before production matters.
4. Secrets go to `railway variables`, never into git (AGENTS.md → Security).
5. The app must expose a health endpoint before first deploy — this is the
   AGENTS.md observability default made concrete, and it is what every later
   verification curls.
6. First deploy: `railway up` to staging; verify with `railway status`,
   `railway logs`, and a request to the health endpoint. The provisioning isn't
   done until this first execution is verified.

**Degraded path:** no Railway CLI, no token, or no network → say so plainly,
finish everything local (health endpoint, config), and record the provisioning as
an open thread. Never fake a deploy or skip the report of what didn't happen.

### Step 3 — Enforce, milestone by milestone
After each milestone commit is pushed:
```bash
railway up            # deploy the milestone to staging
railway status && railway logs   # did it start?
curl -f <staging-url>/health     # does it execute?
# smoke-test the critical path the milestone touched
```
Deploy failed or health check red → the milestone reopens; run `debug`. Do not
stack new work on an undeployable head.

### Step 4 — Production
Production deploys run through the `deploy` skill's checklist, always with explicit
user confirmation, targeting the production environment. Rollback on Railway:
redeploy the previous deployment (`railway redeploy`); the `deploy` skill's
rollback rules apply.

## Lifecycle checkpoints (where this skill hooks in)
The obligation starts before any code exists — each stage's skill carries a
one-line checkpoint pointing here:

| Stage | Skill | Checkpoint |
|-------|-------|-----------|
| Brainstorm/evaluate | `product-brief` | An MVP that cannot be deployed is not an MVP — the Go verdict implies a deployable slice |
| Define | `requirements` | The deploy target is a constraint, captured with the others |
| Design | `architecture` | The MVP slice must be deployable on the chosen target from day one |
| Bootstrap | `git-steward` | Repo exists → provision the deploy target next |
| Build | this skill | Every milestone executes on staging (Step 3) |
| Ship | `deploy` | Production, checklist, rollback |

## Boundaries that never move
- No secrets in git, ever — environment variables live on the platform.
- Production deploys always get explicit confirmation; staging deploys don't need it.
- Never `railway down`, delete an environment, or destroy infrastructure without
  explicit confirmation (AGENTS.md → Escalate).
- Never switch deployment platforms silently; Railway is the default, a change is a
  recorded decision.
- Costs are surfaced before they are incurred, not after.

## Anti-Patterns to Avoid

| Anti-pattern | Correct approach |
|--------------|-----------------|
| Deploying for the first time at the end | Deploy target provisioned at bootstrap; first `railway up` at the first milestone |
| "Works on my machine" as done | Done = verified executing on staging |
| Secrets committed "temporarily" | `railway variables` from the first secret |
| Staging drifts from production | Same config file, same build path, different environment |
| Piling milestones onto a broken deploy | An undeployable head reopens the milestone |
| Silent platform switch | Platform changes go through `/decide` |

## Knowledge Extraction
```
remember: [project] deploys to Railway project <name>, envs <staging/production>, health at <path> — reason: every milestone verification needs it
```
Capture deployment quirks discovered along the way (build args, region, cold-start
behavior) the same way.
