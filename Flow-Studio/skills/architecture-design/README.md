# Architecture Design Skill

## Purpose
Design scalable, maintainable, and appropriate system architecture with clear trade-off analysis.

## Process Summary
See the full procedure in `.claude/skills/architecture/SKILL.md`.

## Design Principles

1. **Simplicity first** — choose the simplest architecture that meets stated requirements
2. **Proven over novel** — use battle-tested technology for foundational components
3. **Explicit over clever** — clear intent beats optimized obscurity
4. **Operability is a feature** — the team must run this at 3am; design for that
5. **Data model defines everything** — bad data modeling is the root of most architectural failures

## Output Artifacts

Every architecture design produces:
1. Component diagram (text/ASCII)
2. Technology decisions with rationale and rejected alternatives
3. Data model (key entities and relationships)
4. Top 3 risks with mitigations
5. MVP scope definition

## Critic Integration
After producing an architecture, run `architecture-critic.md` checklist before presenting.
Any CRITICAL findings must be addressed before output is shown to the user.

## Knowledge Storage
After architecture is agreed upon:
```
remember: [project] architecture — [key decisions, technology choices, and rationale]
```
