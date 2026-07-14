---
name: testing
description: Generate comprehensive tests for code. Use when the user says "write tests", "add tests", "test coverage", "unit tests", "integration tests", or "test this function/module".
when-to-use: write tests, add tests, test coverage, unit tests, integration tests, TDD
allowed-tools: powershell, bash
argument-hint: "[file, module, or function to test]"
---

# Testing Skill

## Testing Pyramid (apply proportionally)

```
        /\
       /E2E\        <- Few, slow, expensive. Test critical user flows only.
      /------\
     /Integr. \     <- Medium count. Test component interactions.
    /----------\
   / Unit Tests \   <- Many, fast, cheap. Test individual functions/classes.
  /--------------\
```

## Step-by-Step Process

### Step 1 — Understand what to test
Read the code. Identify:
- **Public API** — what does this expose?
- **Critical paths** — what must work for the feature to have value?
- **Failure modes** — what happens with bad/missing input?
- **External dependencies** — what needs mocking?

### Step 2 — Choose the right test type
| Scenario | Test Type |
|----------|-----------|
| Pure function with no side effects | Unit |
| Class with dependencies | Unit + mock |
| Two modules interacting | Integration |
| Database queries | Integration (real or in-memory DB) |
| API endpoints | Integration/Contract |
| Critical user workflow | E2E |

### Step 3 — Structure each test
```
// Arrange — set up preconditions and inputs
// Act — call the code under test
// Assert — verify the expected outcome
```

### Step 4 — Cover these cases for every public function
1. **Happy path** — valid input, expected output
2. **Edge case** — boundary values (0, -1, empty string, max int)
3. **Failure path** — invalid/null/missing input → expect specific error
4. **Side effects** — verify external calls were made with correct args

### Step 5 — Write tests first for new code (TDD)
```
RED   → write a failing test for the behavior
GREEN → write the minimum code to make it pass
REFACTOR → clean up without breaking the test
```

### Step 6 — Review test quality
Bad test signs:
- Asserts on implementation details (internal method calls), not behavior
- Test only passes on specific machine or time zone
- Mocks so much that there's nothing left to actually test
- No assertion (test can never fail)
- Test name doesn't describe the scenario

Good test signs:
- Can run in any order independently
- Fails for the right reason when code is broken
- Name reads like a specification: `should return 404 when user not found`

## Framework Quick Reference (fill in for your stack)

```
# JavaScript/TypeScript
vitest, jest: describe/it/expect
@testing-library/react: render, userEvent, screen

# Python
pytest: def test_*, assert, fixtures
unittest.mock: Mock, patch

# Go
testing: t.Run, t.Fatal, t.Helper

# Java/Kotlin
JUnit5: @Test, @BeforeEach, Assertions.*
Mockito: mock(), when().thenReturn()
```

## Knowledge Extraction
After writing tests, note any patterns for this codebase:
```
remember: [project] test patterns — [framework setup, mocking approach, fixture strategy]
```
