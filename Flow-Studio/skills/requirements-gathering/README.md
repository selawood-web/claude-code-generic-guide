# Requirements Gathering Skill

## Purpose
Conduct deep, structured requirements gathering to turn vague ideas into clear, actionable specifications.

## Core Insight
Users describe solutions, not problems. Your job is to dig until you understand the problem, then help design the right solution — which may be different from what they described.

## Anti-Patterns to Avoid

| Anti-pattern | Correct approach |
|--------------|-----------------|
| Building what the user asked for literally | Understand the underlying problem first |
| Assuming a requirement is obvious | Ask explicitly — it rarely is |
| Writing requirements as tasks ("the system shall...") | Write as user outcomes ("as a user, I can...") |
| Gold-plating MVP | Aggressively scope to the minimum viable outcome |
| Ignoring non-functional requirements | Explicitly ask about scale, reliability, compliance |

## The 5 Questions That Unlock Every Requirement

1. **Who** is experiencing the problem? (role/persona)
2. **What** is the current workflow without this solution?
3. **Why** is the current workflow broken or inadequate?
4. **What** does success look like to the user?
5. **What** happens if we get this wrong?

## Process
See full procedure in `.claude/skills/requirements/SKILL.md`.

## Output Standard
A completed requirements session produces a spec document that:
- A developer can implement without asking additional questions
- A product owner can use to verify the implementation
- A designer can use to sketch the UX
- A QA engineer can use to write acceptance tests

## Knowledge Storage
Domain knowledge discovered during requirements gathering is high-value:
```
remember: [domain concept] — [business rules, edge cases, constraints]
```
