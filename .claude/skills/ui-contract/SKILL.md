---
name: ui-contract
description: "Map and lint a product's interaction architecture — which commands exist, where each lives, when each is enabled, and how boards share one model with different outputs."
when_to_use: tools behave differently per screen, too many irrelevant buttons, same action reachable from several places, UI consistency, context-aware toolbar, interaction architecture, command map
argument-hint: "[--observe <app> | --target | --lint <contract.json> | --wire]"
purpose: "Interaction contract: one home per command, state per context, boards as output lenses"
---

# UI Contract — one map of what the user can do, where, and why

## Goal
An interface is learnable when three things hold everywhere: a tool means the same
thing wherever it appears, only what is relevant here can be used here, and every
command has one home. These are architecture, not polish — they break when each screen
is built on its own, and no screenshot review catches them, because each screen looks
fine alone. This skill makes them a **file**: the UI contract, one JSON document the
team edits, `tools/ui_contract_lint.py` checks, and the app itself reads at runtime.
The contract is to interaction what a schema is to data.

Where it sits: `/gbb` judges how the product *feels*; this judges whether its structure
is *coherent*. Run this first when the complaint is "confusing" rather than "ugly" —
a council cannot fix a tool that does three things on three boards.

Companions:
- [`contract-schema.md`](contract-schema.md) — the file format and every rule code (UC01–UC14)
- [`wiring.md`](wiring.md) — make the contract executable: the command registry and the test that keeps UI and contract equal
- [`example-contract.json`](example-contract.json) — a worked, lint-clean example for a cabinet CAD with four boards

## The model behind it
Four nouns, and the discipline is keeping them apart:

| Noun | Is | Is not |
|------|----|--------|
| **Model** | the one drawing: geometry, layers, measurements | owned by any board |
| **Board** | an output lens over the model: which layers show, which measurements, what deliverable | a separate set of tools |
| **Context** | where the user is: board × state (nothing selected, a cabinet selected, …) | a screen name |
| **Command** | one action with one sentence of behaviour, one home, a state in every context | different per board |

When a tool "does something different" on another board, one of two things is true:
the difference is *output* (dimension style, visible layers) and belongs in the board's
profile, or it is a *different action* and deserves its own name. The linter refuses
the third option — one name, behaviour that varies (UC14).

## Modes
| Invocation | What runs |
|------------|-----------|
| `/ui-contract --observe <app>` | Steps 1–2: inventory the running app as it is, lint it — the findings are the UX debt list |
| `/ui-contract --target` | Step 3: decide the intended contract with the owner |
| `/ui-contract --lint <file>` | the linter and the matrix only |
| `/ui-contract --wire` | Step 4: wire the contract into the codebase |
| `/ui-contract` | all four, in order |

## Process

### Step 1 — Observe: inventory what exists
Walk the running product (the app's own run path, Playwright where it is a web app;
the `/gbb` stranger-walk rules on whose code may be started apply here too) or, if it
cannot run, read the UI code. For **every context** — each board, each selection
state, each mode — record every control the user can see: its label, where it sits,
whether it responds, and what it actually did. Write it as
`design/ui-contract.observed.json` in the schema. Record behaviour as observed, even
when a command does different things on different boards — that is a finding, write
`does` as an object keyed by board so the linter flags it.

### Step 2 — Lint the observed contract
```bash
python3 tools/ui_contract_lint.py design/ui-contract.observed.json --matrix
```
Every finding is a concrete, located UX defect. Group them for the owner by the four
rules — same meaning, one home, only what is relevant, same model — and count each.
Those counts are the baseline the work is measured against.

### Step 3 — Decide the target
Copy the observed file to `design/ui-contract.json` and fix it *on paper* first. The
decisions that are the owner's go out together as one coded pick-list:
- each command whose behaviour varies by board: split into two names, or move the
  difference into the profiles
- each command with several entry points: which is home; which others earn a `why`
- the policy for commands of another board: `disabled` (grey, with "Available in
  Manufacture") or `hidden`
- the per-context budget of enabled commands

Everything else is technical and goes on the Decided list. The target must lint clean
with `--strict`. The diff between observed and target, command by command, is the work.

### Step 4 — Wire it, so it stays true
Follow [`wiring.md`](wiring.md): the app reads the contract to decide enabled, disabled
and hidden — it stops being a document and becomes the source — and one end-to-end test
walks every context and asserts the rendered controls equal the contract. From then
on a new tool is added by editing the contract first; CI rejects a UI that disagrees.

### Step 5 — Hand off
Each group of the diff becomes a `/feature` definition, with the lint result and the
matrix row as acceptance criteria. Done means the contract lints clean *and* the
end-to-end test passes against the running app — not that the JSON looks right.

## Ending
`--observe` ends as a next step: the baseline counts and the pick-list for Step 3.
`--target` ends when the target lints clean under `--strict`. `--wire` ends Done only
with the end-to-end test passing against the running app.

## Anti-patterns
| Anti-pattern | Correct approach |
|--------------|-----------------|
| Writing the target contract before observing | Observe first — the findings are the evidence and the baseline |
| One tool per board because the outputs differ | One tool; the board profile owns the output |
| Grey controls with no explanation | Every disabled state carries the reason and the way to enable it (UC12) |
| A second menu entry "for convenience" | Allowed only with a `why` the home cannot meet (UC04) |
| The contract as documentation | The app reads it; a test holds the UI to it |
| Hiding everything that is not relevant | Disable within the board; hide or disable other boards' tools by policy |
