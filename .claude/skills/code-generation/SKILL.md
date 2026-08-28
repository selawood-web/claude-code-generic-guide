---
name: code-generation
description: Generate production-ready code with explicit error handling, edge cases, and tests. Use when the user says "implement", "write code", "build this function/module", or "add this feature".
when-to-use: implement, write code, generate code, build feature, add function
allowed-tools: powershell, bash
argument-hint: "[what to implement]"
purpose: Production-ready implementation with critic pass
---

# Code Generation Skill

## Purpose
Generate high-quality, clean, and well-documented code that is production-ready, not just "working".

This skill's process is the *draft* stage of the working charter's gate — static analysis, tests, and
the requirement check still run after it, and a failure at any stage restores the baseline and comes
back here. See `WORKING-CHARTER.md`, *Code Module*.

## Standards

### Code Quality Checklist (apply to every generated file)
- [ ] Naming communicates intent (variables, functions, classes)
- [ ] Functions do one thing (single responsibility)
- [ ] Error handling is explicit — no swallowed errors
- [ ] Edge cases are handled (null, empty, out-of-range)
- [ ] No hardcoded values that belong in config/constants
- [ ] No TODO comments without context (why and when)
- [ ] Security: no injection points, no secret in code

### Structure Guidelines
```
# Good function structure:
1. Validate inputs (fail fast, fail loudly)
2. Execute the core logic
3. Return result or throw explicit error

# Never:
- Return null to signal error (use Result type or throw)
- Catch all exceptions silently
- Mix IO and business logic in the same function
```

## Process

1. **Understand before writing** — Read existing patterns in the codebase first
2. **Write the interface first** — function signature, types, and docstring
3. **Write the happy path** — make it work for the normal case
4. **Add edge case handling** — inputs that could break it
5. **Add error handling** — explicit, not catch-all
6. **Write tests** — per function touched: one happy path, at least three edge cases (empty input,
   boundary value, unexpected type), and one failure mode. Run the full suite, not just the new tests;
   target 90 percent coverage on changed lines
7. **Run critic** — apply the checklist in `../code-review/code-critic.md` before presenting

## Output Format
- Use language-appropriate idiomatic patterns
- Code blocks labeled with the language
- If generating multiple files, list them first, then generate each
- Explain non-obvious decisions inline with comments

## Critic Integration
After generating significant code, run the `../code-review/code-critic.md` checklist.
Do not present code with BLOCKER-level issues unfixed.
