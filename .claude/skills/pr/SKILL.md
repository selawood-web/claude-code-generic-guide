---
name: pr
description: Create a pull request for the current branch. Use when the user says "create PR", "open pull request", "submit for review", or "push PR".
when-to-use: create PR, open pull request, submit PR, push PR
allowed-tools: powershell, bash
argument-hint: "[optional: PR title hint]"
purpose: PR creation with structured description
---

# Pull Request Skill

## Steps

1. **Detect the default branch — never assume `main`**
   ```
   DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
   DEFAULT=${DEFAULT:-main}
   git --no-pager status
   git --no-pager log "origin/${DEFAULT}..HEAD" --oneline
   ```
   Ensure all changes are committed. Count commits to be included.

2. **Push branch** (if not already pushed)
   ```
   git push -u origin HEAD
   ```

3. **Gather PR metadata**
   - Title: `<type>(<scope>): <concise description>` matching conventional commits
   - Body: use the template below
   - Base branch: the detected default (`$DEFAULT`), unless the team uses a develop branch
   - Draft: ask if this should be a draft PR

4. **PR body template**
   ```markdown
   ## Summary
   <!-- What this PR does and why -->

   ## Changes
   <!-- Bullet list of significant changes -->

   ## Testing
   <!-- How was this tested? -->

   ## Notes
   <!-- Breaking changes, migrations, follow-up items -->
   ```

5. **Create PR via gh CLI**
   ```
   gh pr create --title "<title>" --body "<body>" --base "$DEFAULT"
   ```
   Or for draft: add `--draft`

6. **Post-creation**
   - Share the PR URL
   - Check if CI is running: `gh pr checks <number>`
   - Request reviewers if known: `gh pr edit --add-reviewer <username>`

## Checklist before creating
- [ ] All tests pass locally
- [ ] No debug/temporary code left in
- [ ] PR is focused — not mixing unrelated concerns
- [ ] Description explains WHY, not just what
