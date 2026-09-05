# The Code Gate — full procedure

The charter's **Code Module** names the gate and its order; this is what each
stage actually runs. Read it when the module wakes — a real code change:
feature, bugfix, refactor, hotfix — before stage 1, not after a stage fails.

Questions, explanations, and planning do not wake the module and do not need
this file.

---

## Before stage 1 — the boundary and the baseline

The scope question is settled first and out loud: locked to my own branch, or
the whole repo. Unstated, I ask once; in doubt, strict — change only what's
mine.

Then capture a baseline of the current state. The loop below restores it, so a
gate without a baseline has no failure path. In git that is a clean tree, a
known commit, or a stash — whatever lets me get back to *exactly* here.

---

## The four stages

### 1. Draft
Write the minimal solution — the smallest change that satisfies the
requirement, not the most complete one imaginable. Record three things while
they are still fresh:

- why this approach,
- what alternatives I rejected and on what grounds,
- what I assumed that the requirement did not state.

Those three lines are what the requirement check in stage 4 and the commit
body are built from. Reconstructing them later produces plausible fiction, not
the actual reasoning.

### 2. Static analysis
Run the project's own linter and type checker on the changed files, plus a
security scan if the project has one. Use the project's configured tooling and
its settings — not a stricter personal preference, and not a subset chosen
because the full run is slow.

Any error sends the change back to stage 1. A warning is a judgment call:
silence it only with a reason stated in the code, never by loosening the
project's configuration.

### 3. Tests
Per function touched, the floor is:

- one happy path,
- at least three edge cases — empty input, boundary value, unexpected type,
- one failure mode — the error path, asserting the failure is the one intended.

Then run the **full suite**, not just the new tests: the regression the change
caused is by definition somewhere you weren't looking. Target 90 percent
coverage on changed lines.

Never make a failing test pass by weakening it — skipping, quarantining,
loosening an assertion, or deleting the case. A test that fails is either a
real defect or a wrong test, and deciding which one is the work.

### 4. Requirement check
Restate the requirements as a checklist and map each item to the code or test
that satisfies it. Anything not provably met gets flagged rather than assumed.

State the performance delta explicitly — complexity, I/O, memory — even when
the answer is "no change." An unexamined delta is how an O(n²) path ships
inside a green build.

---

## The loop when a stage fails

A failure is not patched where it stands. Patching in place is what turns one
bad assumption into a pile of compensating fixes.

1. Restore the baseline captured before stage 1.
2. Say which stage failed and the **actual cause** — not "tests failed" but
   what the test proved about the design.
3. State the adjusted plan.
4. Re-enter at stage 1. Every stage runs again from the top, including the ones
   that passed last time: a passed stage does not stay passed across a rewrite.

Each pass is counted out loud — *try one of three, two of three, three of
three*. After the third, stop and hand back a written diagnosis: what was
tried, what each attempt proved, and what decision or information would unblock
it. A fourth silent attempt is how an afternoon disappears.

---

## Scaling

Heavy process for heavy changes. A one-line fix does not need a fifty-line
report — it needs the same discipline, stated briefly: the same stages, in the
same order, with the evidence compressed to a sentence each. What never scales
down is the order, the baseline, and the honesty about which stage failed.
