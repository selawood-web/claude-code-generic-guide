---
name: eli10
description: "Re-explain the last reply, a list of items, or a set of steps in plain words — one ELI10 card per item, in the order to act, with one-step-per-turn Manuals. Use when the user says \"eli10\", \"explain like I'm 10\", \"simpler\", \"one by one\", \"I don't understand\", \"why 2\", or asks what to do next."
when_to_use: eli10, explain like I'm 10, simpler, plain words, one by one, I don't understand, what does this mean, why 2, what to do next, step by step
argument-hint: "[optional: the thing to explain, an item number, or \"steps\" for one-by-one instructions]"
purpose: Plain-words explanation or instructions, one ELI10 card at a time
---

# ELI10 Skill — One Card at a Time

## Purpose
Turn whatever the owner is looking at into something they understand on the first
read and can act on without looking anything up. The card format, the one-by-one
rule and the reply codes all live in
[`../../references/dialogue.md`](../../references/dialogue.md) — *The fast-reply
system*. Read that section first; this skill is only the procedure for applying it
on request.

## Procedure

1. **Pick the target.** With no argument: the last reply. With a number (`why 2`,
   `eli10 1B`): that item only. With a topic: that topic. With `steps`: the owner
   steps of the current task.
2. **Split it into items** the owner acts on or decides about — not into every fact
   that was mentioned. Items that are mine to do become one card saying so, or are
   dropped if the owner does not need to know.
3. **Order them** the way the owner should act: blocking first, optional last.
4. **Write one card per item** — title with `N of M`, **What**, **Why**, **Watch out**
   when there is a hazard, **You do**, **Done when** — in the plain-words rules of *Reply layout*. No term survives that
   the owner would have to look up.
5. **Owner steps go one by one** when *One by one* says so: step 1 only, ending in
   `done` / `stuck`; the next step comes on `done`, the same step is fixed on `stuck`.
6. **End as the charter requires** — a Next step, a coded Pick-list, or Done. A
   decision inside the cards is asked as a coded pick-list, not left inside a card.

## Not this skill
- Deciding anything new. It re-explains; the decisions stay where they were made.
- Shortening by dropping facts the owner needs. Simpler words, same truth — if a
  simplification would mislead, keep the precise term and explain it in six words.
