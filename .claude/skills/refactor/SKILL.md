---
name: refactor
description: Refactor code to improve structure, readability, or performance without changing behavior. Use when the user says "refactor", "clean up", "improve code quality", "too complex", or "hard to read".
when-to-use: refactor, clean up code, simplify, reduce complexity, improve quality
allowed-tools: powershell, bash
argument-hint: "[file or module to refactor]"
purpose: Safe refactoring with regression safety
---

# Refactor Skill

## The Golden Rule
**Behavior must not change.** If there are no tests, write them BEFORE refactoring, not after.

## Process

### Step 1 — Establish a safety net
```
# Run existing tests
# Verify they pass BEFORE you start
# If no tests exist for this code: write characterization tests first
```

Characterization tests capture current behavior (even bugs). They exist to catch regressions during refactoring.

### Step 2 — Understand the code completely
Read it all before changing anything.
- What is the intent?
- What are the inputs/outputs?
- What are the side effects?
- What is the data flow?

### Step 3 — Identify the problems (one at a time)
Common refactoring targets:

| Problem | Refactoring |
|---------|-------------|
| Function does too much | Extract function |
| Duplicated logic | Extract and reuse |
| Long parameter list | Introduce parameter object |
| Nested conditions | Early return, guard clauses |
| Magic numbers/strings | Named constants |
| Unclear variable names | Rename |
| Long class | Extract class |
| Switch on type | Polymorphism |
| Comments explaining bad code | Rewrite the code |

### Step 4 — Refactor in small, safe steps
- One refactoring at a time
- Run tests after each step
- Commit after each successful step

Never refactor + add features in the same commit.

### Step 5 — Final check
After refactoring:
```
# All tests pass?
# Any new tests needed?
# Is the code simpler than before?
# Is any existing behavior affected?
```

## Refactoring Patterns

### Extract Function
```
BEFORE: 100-line function with a comment "// validate user"
AFTER: validateUser() function called from the original
```

### Guard Clauses (flatten nesting)
```
BEFORE:
if (user) {
  if (user.active) {
    if (user.hasPermission) {
      doWork();
    }
  }
}

AFTER:
if (!user) return;
if (!user.active) return;
if (!user.hasPermission) return;
doWork();
```

### Replace Magic Values
```
BEFORE: if (status === 3) { ... }
AFTER:  if (status === STATUS.REJECTED) { ... }
```

### Separate concerns
```
BEFORE: fetchAndTransformAndStoreData()
AFTER:  
  const raw = await fetchData();
  const transformed = transformData(raw);
  await storeData(transformed);
```

## What NOT to refactor
- Code that is about to be deleted
- Code you don't fully understand (explore first)
- Working stable code with no maintainability issues

## Knowledge Extraction
If you discover a recurring pattern or a better idiom for this codebase:
```
remember: [project] refactoring pattern — [before/after and why]
```
