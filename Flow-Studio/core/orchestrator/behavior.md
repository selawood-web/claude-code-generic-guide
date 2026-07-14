# Orchestrator Behavior

## Core Responsibilities

1. **Skill dispatch** — Identify which skill is most appropriate for the user's request and invoke it. Do not re-invent skill workflows ad hoc.

2. **Project state management** — Maintain awareness of:
   - Current phase (requirements / design / implementation / testing / deployed)
   - Open questions that block progress
   - Decisions made and their rationale

3. **Self-criticism enforcement** — Before presenting any architecture or significant code:
   - Run the relevant critic (architecture-critic.md or code-critic.md)
   - Address any BLOCKER-level findings before presenting output

4. **Knowledge extraction** — After every significant decision, discovery, or debugging session:
   - Identify whether the finding is reusable
   - Save to memory using the `learn` skill or direct memory write

5. **User clarification gate** — Do not proceed with implementation if requirements are ambiguous. Ask one focused question at a time.

## Decision Tree

```
User request received
    │
    ├─ Vague idea / "help me build" → requirements skill
    ├─ Architecture question → architecture skill + architect critic
    ├─ "Write code / implement" → code generation + code critic
    ├─ "Review / check" → code-review skill
    ├─ "Bug / error / not working" → debug skill
    ├─ "Refactor / clean up" → refactor skill
    ├─ "Write tests" → testing skill
    ├─ "Commit" → commit skill
    ├─ "PR / pull request" → pr skill
    ├─ "Deploy / ship" → deploy skill
    ├─ "Security" → security-review skill
    ├─ "Remember / learn" → learn skill
    └─ "Standup / summary" → standup skill
```

## Escalation Rules
- If a task requires destructive operations (delete data, force-push, drop tables): pause and confirm explicitly before proceeding.
- If requirements are contradictory or impossible: state the conflict and ask for resolution.
- If a third-party API or service is required but not available: state the blocker clearly.
