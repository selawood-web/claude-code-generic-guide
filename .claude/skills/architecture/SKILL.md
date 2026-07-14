---
name: architecture
description: Design system architecture with trade-off analysis. Use when the user wants to "design a system", "architect a solution", "plan the tech stack", or asks "how should I structure this".
when-to-use: design architecture, system design, tech stack, structure the app, design the system
allowed-tools: powershell, bash
argument-hint: "[system or feature to design]"
---

# Architecture Design Skill

## Process

### Phase 1 — Requirements Extraction (do not skip)
Before designing anything, answer these questions:

**Functional**
- What are the 3-5 core user actions this system must support?
- What data must persist? What is its shape?
- What integrates with what?

**Non-functional**
- Scale: how many users/requests at peak?
- Latency requirements: what is "too slow" for the user?
- Availability: what is the acceptable downtime?
- Consistency vs. availability trade-off (CAP theorem)?
- Compliance: GDPR, HIPAA, SOC2, or none?

**Constraints**
- Team size and experience?
- Timeline?
- Existing infrastructure or technology mandates?
- Budget (affects cloud vs. self-hosted decisions)?

### Phase 2 — High-Level Design

1. Draw the system boundary (what is in-scope vs. out-of-scope)
2. Identify the major components (services, databases, queues, caches)
3. Draw data flows between components
4. Choose the architecture style:
   - **Monolith** — default for small teams, single domain
   - **Modular monolith** — good balance when team < 10
   - **Microservices** — only when team autonomy and independent scaling are clearly needed
   - **Event-driven** — when components need temporal decoupling
   - **Serverless** — when traffic is spiky and unpredictable

### Phase 3 — Component Decisions

For each major component, document:
- **Technology choice** and why (not just what is popular)
- **Rejected alternatives** and why they were rejected
- **Key risks** with this choice

### Phase 4 — Trade-off Analysis

| Decision | Benefit | Cost | Risk |
|----------|---------|------|------|
| [fill in] | | | |

### Phase 5 — Output

Produce:
1. ASCII or text component diagram
2. Technology list with rationale
3. Data model sketch (key entities and relationships)
4. Top 3 risks and mitigations
5. What to build first (MVP slice)

## Architecture Critic Checklist
Run this before presenting the architecture:
- [ ] Is this the simplest architecture that meets the stated requirements?
- [ ] Could a team of the stated size operate this in production?
- [ ] What is the single point of failure? Is that acceptable?
- [ ] How does this scale (both up and down)?
- [ ] What does the operational runbook look like?
- [ ] Is there a migration path if a key technology choice proves wrong?

## Knowledge Extraction
After the architecture is agreed upon, save to memory:
```
remember: [project] architecture — [key decisions and rationale]
```
