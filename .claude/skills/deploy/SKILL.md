---
name: deploy
description: Execute a deployment workflow safely. Use when the user says "deploy", "ship", "release", "push to production", or "go live".
when-to-use: deploy, ship, release, push to production, go live, rollout
allowed-tools: powershell, bash
argument-hint: "[environment: staging|production, or service name]"
---

# Deploy Skill

## Pre-Deployment Checklist (never skip)

- [ ] All tests pass on the branch being deployed
- [ ] Code has been reviewed (at least self-reviewed for solo projects)
- [ ] Database migrations are backward-compatible (zero-downtime)
- [ ] Environment variables and secrets are verified in target environment
- [ ] Rollback plan is known
- [ ] Deployment window: is this a good time? (avoid Fridays, Monday mornings)
- [ ] Monitoring/alerting is active

## Steps

### Step 1 — Confirm environment
```bash
# Confirm target environment
# Confirm current state of what is deployed
# Confirm what is about to be deployed
git log production..HEAD --oneline    # or equivalent for your deploy method
```

### Step 2 — Run pre-deploy validation
```bash
# Run full test suite
npm test / pytest / cargo test / go test ./...

# Build artifacts
npm run build / make build

# Smoke test locally if possible
```

### Step 3 — Execute deployment
Adapt to your deployment system:

**GitHub Actions / CI:**
```bash
gh workflow run deploy.yml -f environment=production
gh run watch  # Monitor the deployment
```

**Docker / Kubernetes:**
```bash
docker build -t app:v<version> .
docker push app:v<version>
kubectl set image deployment/app app=app:v<version>
kubectl rollout status deployment/app
```

**Platform-as-a-Service (Railway — the house default via the `deploy-steward` skill — or Heroku, Render):**
```bash
railway up && railway status && railway logs   # Railway (see deploy-steward)
git push heroku main && heroku logs --tail     # Heroku
```

**SSH / Traditional:**
```bash
ssh user@server 'cd /app && git pull && npm install && pm2 restart app'
```

### Step 4 — Verify deployment
```bash
# Health check
curl -f https://yourapp.com/health

# Smoke test critical paths
curl https://yourapp.com/api/status

# Check logs for errors (first 5 minutes)
# Check error rate in monitoring
```

### Step 5 — Post-deployment
- Monitor error rate and latency for 15 minutes
- Create deployment record (version, time, deployer, changes)
- Update status page if applicable

## Rollback procedure
Know this BEFORE deploying:

```bash
# Git rollback
git revert HEAD && git push

# Docker rollback
kubectl rollout undo deployment/app

# Database: only backward-compatible changes allow rollback
# If migration is not backward-compatible: this is a breaking deployment
```

## Knowledge Extraction
After deployment, capture:
- Any deployment-specific quirks for this project
- Environment variable changes made
- Infrastructure changes that are not in code
