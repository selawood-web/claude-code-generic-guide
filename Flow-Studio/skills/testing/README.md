# Testing Skill

## Purpose
Automatically create and manage testing strategies, test cases, and quality assurance.

## Testing Philosophy
Tests are not a quality gate — they are a **design tool**. Writing tests first forces clarity about what the code should do.

A test suite is only as good as its ability to:
1. **Catch real bugs** before production
2. **Enable refactoring** without fear
3. **Document behavior** for future engineers

## Strategy by Project Phase

### Greenfield (new project)
- Default to TDD: write the test, then the implementation
- Set up test infrastructure in day 1 (CI, coverage reporting)
- Establish the testing pyramid: many unit, some integration, few E2E

### Legacy codebase
- Write characterization tests before refactoring
- Prioritize tests for the highest-risk, most-changed code
- Do not require 100% coverage retroactively — focus on critical paths

### Bug fixing
- Always write a regression test that reproduces the bug BEFORE fixing it
- The test must FAIL before the fix and PASS after

## Coverage Targets (guidelines, not laws)
| Code type | Target |
|-----------|--------|
| Business logic / domain | 90%+ |
| API handlers | 80%+ |
| Utilities / helpers | 70%+ |
| Generated code | 0% (don't test what you didn't write) |
| Glue code / config | Integration tests only |

## Process
See full procedure in `.claude/skills/testing/SKILL.md`.

## Knowledge Storage
After establishing the test strategy for a project:
```
remember: [project] test strategy — [framework, patterns, mocking approach, coverage targets]
```
