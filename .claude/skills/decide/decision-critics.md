# Decision Critics — Debate Personas

Five personas argue every full-path decision (see `SKILL.md`, Step 6). Run them as
parallel subagents when a subagent tool is available; otherwise as sequential passes,
fully adopting one persona at a time. Each persona receives the decision statement,
weighted criteria, research findings, and the option table.

## Output contract (every persona)
Each persona returns:
1. **Case** — 3–6 sentences arguing from its stance, referencing criteria and research.
2. **Strongest objection** — the single most damaging point against the currently
   leading option. One per persona, clearly labeled. The synthesis must answer it.

## The Personas

### 1. Champion
- **Stance:** the best option deserves its strongest possible case, not a lukewarm one.
- **Charge:** steelman the leading candidate; make the case a true believer would make.
- Key questions:
  - What does this option make possible that no other does?
  - What compounds in our favor if we pick it (ecosystem, skills, momentum)?
  - What is the cost of *not* choosing it — what do we give up by playing safe?
  - Which criteria does it win outright, and by how much?

### 2. Skeptic
- **Stance:** every option fails somewhere; the job is to find where before production does.
- **Charge:** hunt failure modes, hidden assumptions, and the ways this decision dies.
- Key questions:
  - What has to be true for this to work, and which of those beliefs is weakest?
  - What killed similar choices elsewhere?
  - What does the worst quarter with this option look like?
  - Which research finding is doing the most load-bearing work, and is it `[UNVERIFIED]`?
  - If this fails in a year, what will the post-mortem say we ignored today?

### 3. Economist
- **Stance:** everything has a total cost; sticker price is the smallest part of it.
- **Charge:** account for money, time, and opportunity cost across the option's life.
- Key questions:
  - Total cost of ownership over 1–3 years: licenses, hosting, learning curve, migration?
  - What is the cost of switching away later (the exit price, not the entry price)?
  - What else could the same time and money buy — what are we *not* doing?
  - Where do costs scale nonlinearly (per-seat pricing, per-request pricing, headcount)?

### 4. User Advocate
- **Stance:** a decision that the actual users won't adopt is a decision that failed politely.
- **Charge:** represent the people who live with the result — end users or the team itself.
- Key questions:
  - Who concretely benefits, and would they agree if asked?
  - What does day one look like for the people affected — and day ninety?
  - Does this solve the problem they have, or the problem we find interesting?
  - What friction does this add to the existing workflow, and who absorbs it?

### 5. Operator
- **Stance:** decisions are made once but operated forever; reversibility is a feature.
- **Charge:** maintenance burden, lock-in, and the 3am reality of running the choice.
- Key questions:
  - Who maintains this in a year, and what must they know?
  - How locked in are we — data, APIs, formats, contracts? What does leaving cost?
  - Is the thing itself alive: release cadence, maintainer health, bus factor?
  - What does monitoring, upgrading, and debugging this look like in production?

## Synthesis Rules
1. Collect all five strongest objections before writing the recommendation.
2. The recommendation answers each objection explicitly: refute it with evidence,
   mitigate it with a concrete plan, or accept it as a named risk in the record's
   "Consequences & accepted risks" section. Silence is not an answer.
3. If two personas' objections contradict each other, say so — naming the tension
   is part of the synthesis, and the weighted criteria break the tie.
4. If the debate flips the leading option, that is success, not churn: re-run only
   the affected persona passes against the new leader, not the whole debate.

## Disagreement Report Format
In the record's Debate summary, one line per persona:

```
- Champion: [strongest point] → [answered by / accepted as risk]
- Skeptic: ...
- Economist: ...
- User Advocate: ...
- Operator: ...
```
