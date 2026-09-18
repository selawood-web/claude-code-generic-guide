# Design Quality Patterns — Knowledge Base

Durable lessons from building GBB (Good, Better, Best), the design gate in
[`../../.claude/skills/gbb/SKILL.md`](../../.claude/skills/gbb/SKILL.md), as of the
session that created it. Each entry is a principle with the failure it answers; the
full mechanism lives in the skill's companion files.

---

## Process

### A build loop with no gate for feel ships "good enough" by construction
**Principle**: Correctness gates (tests, lint, audit) cannot see usability, orientation or taste, so a process with only those gates converges on products that work and disappoint. The gap between vision and product is the missing gate, not a missing talent.
**Learned from**: Two projects built with a full correctness pipeline, both correct, both far from the owner's vision in layout, usability and spatial orientation. Nothing in the loop was accountable for how the product felt.
**Detection**: Ask what stage would have rejected a screen that works but leaves a stranger lost. If the answer is "the owner, after shipping", there is no gate.
**Tags**: #design #process #quality-gate

### Nothing is built with no intended direction
**Principle**: The intent — who, environment, feeling, then colour, type, icons, layout, motion, voice, each with a reason and a test — is written before the first screen. Without it a review measures the gap from the reviewer's taste, not from the product's direction.
**Learned from**: The first GBB draft only reviewed after the fact; the owner's philosophy exposed that a council judging a product with no stated intent judges against itself. The intent half was added and the ladder now refuses to run without one.
**Detection**: A user-facing feature whose definition names no intent file.
**Tags**: #design #intent #architecture

### Order of thought: person first, pixels last; verify in the order the mind meets the screen
**Principle**: Decide in a designer's order (who → where and when → feeling and anti-feeling → borrowed mechanisms → language) and test in the user's (sense → attention → recognition → feeling → action). Every visual choice cites the part it came from; a choice without a reason is decoration, a choice without a test is a hope.
**Learned from**: Colour and font chosen first drift with every reference; the anti-feeling ("never clinical, never loud") is what stops a good choice being dragged by a reference.
**Detection**: A palette with no roles, a feeling with no anti-feeling, a test that says "looks right".
**Tags**: #design #intent #testing

### Testing, not just executing
**Principle**: A user-facing change is done when the intent's tests pass in the running product with screenshots — measured contrast, timed responses, named portraits agreeing on an icon — not when the code runs or CI is green.
**Learned from**: The owner's own phrase; the whole gap was products that executed. It matches the charter's "verify at the layer the owner experiences".
**Detection**: A pull request on a styled path with no before-and-after screenshots.
**Tags**: #testing #design #verification

---

## Evidence

### Judge the running product, never its description
**Principle**: A design review reads screenshots, a spatial map and timed stranger tests from the product actually running; a review of the spec or a description reviews the spec. If the product cannot be started, stop and say so rather than judge mockups.
**Learned from**: Every prior review in the projects was of intent and code; none had walked the product as a stranger.
**Detection**: A review with no screenshot ids in its findings.
**Tags**: #design #evidence #review

### Portraits from evidence, not imagination
**Principle**: Build who-it-is-for from one-star reviews of competitors, forum asks, support threads and job descriptions, cited. A persona from a template describes the designer.
**Learned from**: GBB's research protocol; the charter's Currency rule applied to people instead of versions.
**Detection**: A portrait with no source.
**Tags**: #research #design #users

### Manufacture "out of the box" on purpose
**Principle**: Take the product's hardest moment and ask how five fields that never ship software solve it — airports and hospitals for orientation, cockpits and cash registers for feedback, game tutorials and hotel check-in for the first five minutes, aviation checklists for recovery, packaging and theatre for delight. Borrow the mechanism, not the aesthetic; three transfers is enough, ten is a mood board.
**Learned from**: Asking for creativity produces more of the same polish; asking a named adjacent field a specific question produces a mechanism.
**Detection**: A "Best" rung that reads as "more polish" and cites no reference or transfer.
**Tags**: #design #creativity #research

---

## Structure

### A council is only as wide as its disciplines, and one chair must own the craft
**Principle**: Many reviewers from outside the field (wayfinding, choreography, editing, game design, cognition, accessibility, the user, brand, craft) find what one designer's taste cannot; but one seat must belong to the discipline itself — the usability specialist running the heuristic pass — or the findings have no names and no known fixes. Each member returns three ranked gaps, one Best move and one kill question; kill questions are answered before anything is ranked.
**Learned from**: The first council drew everyone from outside software and the owner asked where the UI/UX specialist was. Adding that seat made the Better rungs mostly known patterns applied correctly.
**Detection**: Ten identical top gaps means the council was briefed with a conclusion; re-brief with evidence only.
**Tags**: #design #review #multi-agent

### The ladder moves the bar: a passed Better becomes the new Good
**Principle**: Rank findings as Good (now), Better (one feature), Best (spectacular, traced) with a re-runnable timed test per rung; on rerun, a passed Better becomes Good, Best becomes Better and a new Best is asked for. The review never runs out of a top rung, so "good enough" has no stable state to settle into.
**Learned from**: The owner's motto, turned into a mechanism so it does not depend on anyone's stamina.
**Detection**: A ladder file with no score-history row after a build cycle.
**Tags**: #design #iteration #measurement

### Ownership is a wish until the repository refuses the merge
**Principle**: A design rule binds when a CODEOWNERS file routes every styled path to a design reviewer, the pull-request template demands the intent's test results and screenshots, and branch protection requires code-owner review. Without the last setting the file is a suggestion; on a one-person project the author cannot approve their own pull request, so plan the second reviewer or the `/ship` gate deliberately.
**Learned from**: The owner's CODEOWNERS proposal, aligned to GBB's `design/` folder and shipped with the checklist that gives the review something to check.
**Detection**: A CODEOWNERS file in a repository whose default branch does not require code-owner review.
**Tags**: #github #governance #design
