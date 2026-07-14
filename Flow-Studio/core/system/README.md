# Core System Files

## Files

- `core-prompt.md` — The master system prompt for Workflow Studio. Defines identity, rules, session protocol, operating modes, and self-criticism triggers.

## How it works

This prompt is loaded at the start of every Workflow Studio session. It establishes the AI's identity as a Senior Principal Engineer / Technical CEO and sets the non-negotiable rules:

1. Professional purity — no approval optimization
2. Brevity — no filler
3. Self-criticism — run critics before presenting major outputs
4. Knowledge extraction — save learnings in real-time
5. Verify first — prove it works before claiming it works

## Connecting to the rest of the system

The core-prompt references and delegates to:
- `../orchestrator/` — for skill dispatch logic
- `../critics/` — for code and architecture review
- `../memory/` — for knowledge storage protocol
- `../knowledge-base/` — for extraction rules

See `core-prompt.md` for the full system prompt.
