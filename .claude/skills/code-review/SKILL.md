---
name: code-review
description: Perform a thorough professional code review of staged changes, unstaged changes, or a specific PR. Use when the user asks to "review code", "check my code", "review PR", or "give feedback on changes".
when-to-use: review code, code review, review PR, check changes, review diff
allowed-tools: powershell, bash
argument-hint: "[optional: PR number or file path]"
purpose: Multi-dimension review with severity levels
---

# Code Review Skill

The full review rubric — six dimensions with a severity scale — lives in
[`code-critic.md`](code-critic.md) beside this file. Use it for deep reviews;
the steps below are the working procedure.

## Review Dimensions (in order of priority)

1. **Correctness** — Does it do what it claims? Does it handle edge cases?
2. **Security** — Injection, auth, secrets, input validation, dependency risks
3. **Performance** — Obvious bottlenecks, N+1 queries, unnecessary allocations
4. **Maintainability** — Is it readable? Does naming communicate intent? Is complexity justified?
5. **Test coverage** — Are critical paths tested? Are failure cases covered?
6. **Style** — Only flag style if it causes real friction; never subjective preference

## Steps

1. **Get the diff**
   ```
   git --no-pager diff --staged    # staged changes
   git --no-pager diff HEAD~1      # last commit
   gh pr diff <number>             # PR diff
   ```

2. **For each changed file, evaluate**
   - What is the intent of this change?
   - What could go wrong?
   - What is missing?

3. **Categorize findings**
   | Level | Meaning |
   |-------|---------|
   | 🔴 BLOCKER | Must fix before merge. Correctness or security issue. |
   | 🟡 IMPORTANT | Should fix. Significant quality or maintainability concern. |
   | 🔵 SUGGESTION | Optional improvement. Not blocking. |
   | ✅ GOOD | Explicitly call out what is done well. |

4. **Write review**
   - Lead with blockers.
   - Be specific: quote the code, explain the problem, suggest the fix.
   - Never soften criticism — be direct and professional, not harsh.

5. **Summary verdict**
   - ✅ APPROVE — no blockers, good to merge
   - 🔄 REQUEST CHANGES — blockers or important issues found
   - 💬 COMMENT — observations only, no verdict

## Review anti-patterns to catch
- `catch (e) {}` — swallowed errors
- Hardcoded credentials, tokens, or environment values
- Missing null/undefined checks on external data
- Mutable shared state without synchronization
- SQL/command injection via string interpolation
- Unreachable error handling (error thrown but never surfaced)
- Tests that only test the happy path
