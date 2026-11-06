# Design rules for the product-definition agent pipeline

Apply this file only when the project contains the agent pipeline: a `.claude/agents/` folder with the planner, researcher, spec-writer, critic, and prototyper agents. Ignore it otherwise.

The orchestrator passes the relevant lines below to each subagent when it delegates.

## Per phase

**Planner**
- When the idea has a user interface, each proposed approach states its design direction in one line (for example: calm and minimal, dense and data-heavy, playful). The human picks at the plan gate.

**Researcher**
- Checks `knowledge/` for brand material, design systems, or screenshots first.
- For a redesign, collects the current screens and lists the UX problems the human has named. No design skill runs in this phase.

**Spec writer**
- No `DESIGN.md` yet: runs UI UX Pro Max with the chosen direction, product type, and audience, then writes the result into `DESIGN.md`. The spec references `DESIGN.md` instead of repeating it.
- `DESIGN.md` exists: follows it. Any change is listed as an explicit decision for the human.
- For every screen, the spec states its loading, empty, error, and success states, and whether it needs RTL.

**Critic**
- For any spec or screen with UI, runs `/impeccable critique` and folds the findings into `review.md`, ranked by severity.
- Reports only. Never applies fixes.

**Prototyper**
- Builds against `DESIGN.md` tokens and the design and UX rules. No hardcoded values.
- Runs `/impeccable audit` on what it built, fixes critical and high findings, and lists the rest in `state.md`.
- Does not run `/impeccable polish`. Polish is for real builds after the build decision.

## Gates

- Spec gate: the human approves `DESIGN.md` together with the spec.
- Prototype gate: the human sees the audit summary, what was fixed, what was deferred, and why.

## Tool access

The spec-writer, critic, and prototyper agent files must include `Skill` in their `tools` list, or they cannot run the design skills. If an agent needs a skill it cannot reach, it says so instead of skipping the step silently.
