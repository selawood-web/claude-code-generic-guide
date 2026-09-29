---
name: commit
description: Create a well-formatted git commit following conventional commits standard. Use when the user wants to commit changes, says "commit", "save my work", or asks to "check in code".
when_to_use: commit, save changes, check in, git commit
argument-hint: "[optional: scope or message hint]"
purpose: Conventional commits with staged diff review
---

# Git Commit Skill

## Steps

1. **Inspect staged and unstaged changes**
   ```
   git --no-pager diff --staged
   git --no-pager diff
   git --no-pager status
   ```
   Success: You understand what changed and why.

2. **Stage files** (if nothing staged yet)
   - Ask: "Stage all changes, or specific files?"
   - If all: `git add -A`
   - If specific: `git add <files>`

3. **Determine commit type and scope** — the types, subject rules and body rule are
   AGENTS.md's *Commit conventions*, in one place; pick from there.

4. **Compose message** by those conventions, then:
   - Footer: use your team's AI attribution convention if one exists (e.g. a
     `Co-authored-by:` trailer naming the assistant actually in use). Do not
     hardcode a specific assistant — attribution must match who did the work.

5. **Commit**
   ```
   git commit -m "<subject>" -m "<body if needed>"
   ```

6. **Confirm**
   Run `git --no-pager log --oneline -3` — verify commit appears correctly.

## Knowledge Extraction
After committing, check: did this session reveal a pattern worth remembering? If yes, note it in memory before ending the session.
