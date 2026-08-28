---
name: debug
description: Systematically debug an issue, error, or unexpected behavior. Use when the user describes a bug, an error message, "this doesn't work", "something is wrong", or "why is this happening".
when-to-use: debug, fix bug, error, exception, not working, broken, unexpected behavior
allowed-tools: powershell, bash
argument-hint: "[error message or description of the problem]"
purpose: Systematic root cause analysis
---

# Debug Skill

## Debugging Mindset
Bugs are symptoms, not the problem. The goal is to understand the root cause, not just make the symptom disappear.

## Systematic Process

### Step 1 — Reproduce reliably
Before touching any code:
- Confirm the bug is reproducible
- Document exact reproduction steps
- Identify: always? sometimes? only in production?

If you cannot reproduce, you cannot verify the fix.

### Step 2 — Understand the expected behavior
- What SHOULD happen?
- What DOES happen?
- What is the delta?

### Step 3 — Narrow the scope (binary search approach)
Start wide and narrow:
1. Which component/service is involved?
2. Which function/layer?
3. Which specific line or condition?

Use logs, breakpoints, or print statements to find the exact boundary where reality diverges from expectation.

### Step 4 — Form a hypothesis
Before making changes:
> "I believe the bug is caused by [X] because [evidence Y]. If correct, then [Z] will fix it."

### Step 5 — Test the hypothesis
- Make ONE change at a time
- Verify it fixes the bug
- Verify it does not break anything else (run tests)

### Step 6 — Find the root cause (not just the symptom)
After fixing: ask "why did this happen?"
- Was there a missing validation?
- Was there a wrong assumption about a library's behavior?
- Was there a race condition?
- Was there missing error handling?

Root causes often reveal a class of bugs, not just one.

### Step 7 — Write a regression test
```
// Test that reproduces the bug before the fix
// Must FAIL without the fix, PASS with the fix
```

### Step 8 — Document the finding
If this bug revealed a non-obvious behavior or a systemic issue:
```
remember: [bug class] — [root cause and how to detect/prevent]
```

## Common Bug Categories

| Category | Signs | Tools |
|----------|-------|-------|
| Off-by-one | Wrong count, array out of bounds | Print boundary values |
| Null/undefined | Null pointer, cannot read property | Add null checks at boundaries |
| Async/race | Intermittent, order-dependent | Add locks, check async sequences |
| Type coercion | Wrong comparison result | Explicit type checks, strict equality |
| State mutation | Works in isolation, fails combined | Isolate state, check for shared references |
| Environment | Works locally, fails in CI/prod | Compare env vars, dependencies, OS |

## Diagnostic Commands

```bash
# View recent logs
journalctl -f -n 100
docker logs -f --tail 100 <container>

# Check process state
ps aux | grep <process>
netstat -tlnp | grep <port>

# Network debugging
curl -v <url>
dig <domain>

# Memory/CPU
top -b -n 1
free -h

# File permissions
ls -la <path>
```
