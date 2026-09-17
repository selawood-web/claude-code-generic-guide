# Choosing what to reach for — libraries, and the skills that use them

Three triggers, one idea: before leaning on something someone else wrote, decide
whether it is the right thing *for this job*, not merely a thing that exists.

- **About to build something a library probably already does** → *Picking a dependency*.
- **About to rely on a skill** → *The Skill Checker*, which is a gate, not advice.
- **The job needs something this session does not have** → *Closing a capability gap*.

The charter states both rules; they bind whether or not this file was read. What
lives here is the procedure and the failures each step catches.

---

## Picking a dependency

**Look first, build second.** Python means PyPI, JavaScript means npm. The question
is not "could I write this?" — of course I could — it is "is writing it the best use
of the time, and will the next engineer be glad I did?"

**Boring wins.** Between a clever, obscure, elegantly-designed package and a dull one
that half the ecosystem already depends on, take the dull one. What you are actually
buying is other people's bug reports: the boring option has had its edge cases found
by thousands of users, and its maintainer will still be there next year.

What to check, in the order that eliminates candidates fastest:

1. **Maintenance** — a release within the last year, issues that get answered. An
   unmaintained dependency is code you have adopted without reading.
2. **Adoption** — download counts and dependents. Popularity is not quality, but it
   is evidence that the failure modes are documented somewhere public.
3. **Weight** — what it drags in. A package with forty transitive dependencies to
   format a date is a liability, not a convenience.
4. **Licence** — compatible with what this project ships under.
5. **Exit** — how hard it is to remove later. A library behind one small adapter is a
   reversible decision; one whose types leak through the whole codebase is not.

**When the choice is genuinely close**, it goes to the owner as a pick-list —
recommendation first, one line of trade-off each — not as a paragraph of hedging.
When it is not close, decide, state the choice in one line, and keep moving.

**Never from untrusted sources.** Skills and code are not pulled from GitHub gists,
blog posts, or anywhere outside the ecosystem's own registry. This is a standing
constraint, not a judgment call, and no amount of "it looks fine" overrides it.

**The web is for facts that change.** Versions, prices, API shapes, model names,
part numbers — searched, never recalled. A library whose behaviour I already know
does not need a search; a library's *current version* does.

---

## Closing a capability gap

A gap is the job needing something this session does not have: a connector to a
service, an MCP server, a plugin or extension, a CLI, a skill from a marketplace.
Noticing it, researching it and putting a vetted recommendation on the table is my
work and needs no prompting — a gap left unmentioned is the owner paying for a
limitation nobody told them about. Installing or authorising it is not mine: that is
an owner gate (AGENTS.md, *Escalate instead of proceeding*), and no result, deadline
or "it is only a small one" turns a gap into permission.

**1. Prove the gap is real.** What exactly cannot be done with what is already
here — the tools in this session, the repo's own scripts, a connector already
authorised? Most gaps close at this step, and a tool installed because the existing
one went unread is pure cost.

**2. Search, don't recall.** The product's own connector directory or MCP registry,
the ecosystem registry for a library, the marketplace the runner ships for a plugin,
and the vendor's own documentation. What exists, what it costs and what it asks for
all change — this is the charter's currency rule, and tool listings go stale fast.

**3. Vet before proposing.** The dependency checks above — maintenance, adoption,
weight, licence, exit — all apply, plus what a *connected* thing adds:

- **Publisher.** The vendor of the service itself, or a name the ecosystem already
  trusts. An unofficial bridge to an official API is a stranger standing in the
  middle of the owner's credentials.
- **Access.** The scopes and permissions it asks for, named explicitly, and whether
  a narrower set does the job. Read-only beats read-write when reading is the task.
- **Data.** What leaves the machine, to whom, and under what terms.
- **Blast radius.** What it can change if it misbehaves or is compromised, whether
  its credential can be scoped down, and how it is removed.

A candidate that fails publisher or data is not proposed at all — a pick-list is for
options I would defend, not a menu of everything that exists.

**4. Propose as a pick-list.** Recommendation first, the runner-up, and "keep doing
it by hand" as a real option with its real cost. Each line says what it grants, what
it costs, what it replaces, and what it would take to undo. If the standing
constraints put the candidate out of scope, the proposal says so and asks for that
constraint to be changed — it never quietly assumes the exception.

**5. Install only on an explicit yes** — the thing that was approved, at the scope
that was approved, nothing bundled alongside it. "Go ahead" for one connector is not
standing permission for its ecosystem; approval to use it this session is not
approval to commit it into the repository. When the choice will outlive the session,
the grant and its bounds are recorded with it in `decisions/`.

**6. Report what it changed.** After it is in, one line on what is now possible that
was not, and what to remove if it disappoints. A tool nobody can see the value of is
the next session's unexplained dependency.

---

## The Skill Checker

A gate, run the moment I am about to use a skill — not always on, and not once per
session. Its premise: **trusted source means safe to run. It does not mean good
enough for this job.** A skill from this repo gets the same three questions as any
other, because the risk being managed here is wrong-tool, not malware.

### 1. Does it fit?

Does it match *this* task, or does it only sound like it? Skills are named for
categories; tasks are specific. `/refactor` on code with no test coverage is a skill
that fits the words and not the situation.

**Catches:** the plausible-but-wrong skill, which is worse than no skill — it
supplies a confident procedure for a job it was not built for, and its structure
hides the mismatch.

### 2. Does it work here?

A quick run against our real input, not a promise that it works in general. One real
case, one right result. If the skill's first step already fails on this repository —
a tool it assumes, a layout it expects, a language it does not handle — that is the
answer.

**Catches:** the skill that works in the abstract. Skills are written against the
repositories their author had; yours differs in ways neither of you predicted.

### 3. Does it respect the project?

Using it stays inside the branch boundary and touches nothing it should not. A skill
that wants to reformat the tree, rewrite history, or reach outside the current scope
fails here even if it would produce a good result.

**Catches:** the useful skill with an unacceptable blast radius. Correct output does
not license out-of-scope changes.

### Verdict

Passes all three, use it. Fails any one, drop it, do the job directly, and say in one
line why it was dropped — that line is what stops the same skill being reached for
again next week.

Trust the source for safety. Verify the skill for quality. Never either on faith
alone.
