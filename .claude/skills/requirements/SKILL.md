---
name: requirements
description: Gather and formalize requirements from vague ideas into actionable specifications. Use when the user says "I want to build", "help me plan", "I have an idea", or provides a vague description of something to build.
when-to-use: gather requirements, plan a feature, I want to build, help me design, requirements
allowed-tools: powershell, bash
argument-hint: "[feature or product idea]"
---

# Requirements Gathering Skill

## Goal
Transform a vague idea into a specification precise enough to implement without ambiguity.

## Process

### Step 1 — Understand the Problem (not the solution)
Ask:
- What problem does this solve for the user?
- Who experiences this problem? (persona/role)
- How is this problem solved today? (existing workflow or workaround)
- What is wrong with the current solution?

Do NOT jump to technology choices yet.

### Step 2 — Define Success
Ask:
- How do we know this is working?
- What does "done" look like from the user's perspective?
- What are the 1-3 most important user outcomes?

### Step 3 — Scope the MVP
Apply the **Jobs-to-be-Done** framework:
- What is the minimum that creates real value?
- What can be deferred to v2 without breaking the core value proposition?

Ruthlessly defer: nice-to-haves, edge cases, admin tooling, and analytics.

### Step 4 — Write User Stories
Format:
```
As a <role>, I want to <action>, so that <outcome>.

Acceptance criteria:
- Given <context>, when <action>, then <result>
- [repeat for edge cases]
```

### Step 5 — Identify Constraints and Risks
- Technical constraints (legacy systems, existing infra)
- Business constraints (timeline, budget, regulatory)
- Unknown risks (dependencies on third parties, unclear data)

### Step 6 — Output Document
Produce a requirements spec:

```markdown
# [Feature/Product Name] Requirements

## Problem Statement
[1 paragraph — what problem, for whom, and why now]

## Success Criteria
- [ ] [measurable outcome 1]
- [ ] [measurable outcome 2]

## User Stories (MVP scope)
[stories from Step 4]

## Out of Scope (v1)
[explicit list of what is NOT included]

## Open Questions
[blockers that need answers before implementation]

## Constraints
[technical and business constraints]
```

### Step 7 — Validate
Before moving to architecture:
- Read the spec back to the user in plain language
- Ask: "Does this capture what you meant?"
- Resolve any open questions

## Knowledge Extraction
Save reusable domain knowledge discovered during requirements:
```
remember: [domain concept] — [definition and business rules]
```
