# Test Strategy Reference

Companion to `SKILL.md` — strategy by project phase and coverage targets.
The per-change bar is the gate's stage 3, stated in
`../../references/code-gate.md`; the targets below are per-codebase guidelines
that sit alongside it.

## Strategy by Project Phase

### Greenfield (new project)
- Default to TDD: write the test, then the implementation
- Set up test infrastructure on day 1 (CI, coverage reporting)
- Establish the testing pyramid: many unit, some integration, few E2E

### Legacy codebase
- Write characterization tests before refactoring
- Prioritize tests for the highest-risk, most-changed code
- Do not require full coverage retroactively — focus on critical paths

### Bug fixing
- Always write a regression test that reproduces the bug BEFORE fixing it
- The test must FAIL before the fix and PASS after

## Coverage Targets by Code Type (guidelines, not laws)

| Code type | Target |
|-----------|--------|
| Business logic / domain | 90%+ |
| API handlers | 80%+ |
| Utilities / helpers | 70%+ |
| Generated code | 0% (don't test what you didn't write) |
| Glue code / config | Integration tests only |

## Knowledge Storage
After establishing the test strategy for a project:
```
remember: [project] test strategy — [framework, patterns, mocking approach, coverage targets]
```
