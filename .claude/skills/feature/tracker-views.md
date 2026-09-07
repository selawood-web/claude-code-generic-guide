# Tracker views — one definition, several audiences

The definition file is the source of truth. A tracker item is a *view* of it: the same
content, arranged the way that tool expects. Nothing here is a second home for a rule —
every view is rendered from the file, and the file is what gets edited.

**Rendered, not posted — except where the charter names an exception.** By default
these views are produced as paste-ready text in the conversation or written to a
file, and the owner pastes: this system does not hand work off to external
applications — no tracker API calls, no browser automation, no credentials.

The charter's *Standing Constraints* is where that rule lives and where any
exception is named. Where a project's charter names a tracker as an agreed review
channel, render the view and post it there; everywhere else, render and hand it to
the owner. Check the charter rather than assuming either way — and a posted item is
still a view, so the definition file remains the source of truth and wins whenever
the two disagree. How a post actually happens — the preconditions, the
`features/tracker.json` config, and how the reviewer is notified rather than merely
assigned — is [`tracker-handoff.md`](tracker-handoff.md).

Include the definition's path and id in every view, so a tracker item can always be
walked back to the file that owns it.

## Field mapping

| Definition | Project/epic tracker | Issue tracker | Plain document |
|------------|---------------------|---------------|----------------|
| `title` | Project name | Issue title, prefixed with `id` | Document title |
| `id` | Name suffix or a custom field | Title prefix | Header line |
| `owner` | Lead | Assignee | Owner line |
| `target` | Target date | Milestone / due date | Target line |
| `status` | Project status | Issue state | Status line |
| Summary | Description | Issue body, first paragraph | Abstract |
| Problem + Outcome | Overview body | Issue body sections | Body |
| Scope | Milestones or child issues | Task list | Body |
| Non-goals | Overview, "Out of scope" | Issue body section | Body |
| Acceptance criteria | Definition of done | Task list checkboxes | Body |
| Open questions | Overview, "Open questions" | Issue comments or checklist | Body |

Trackers differ in the names, not the content — a project overview, an epic, and a PRD
all want the same eight sections. Map to whatever the team's tool calls them; never drop
a section to make it fit.

## View — project overview (project/epic level)

For a tracker's project or epic description field. One screen, no nesting.

```markdown
**[id] — [title]** · owner [owner] · target [target] · status [status]
Source of truth: `features/[id]-[slug].md`

[Summary paragraph]

**Why now**
[Problem, tightened to three sentences]

**What success looks like**
[Outcome metrics, as a list]

**In scope**
[Scope bullets]

**Out of scope**
[Non-goals bullets]

**Done means**
[Acceptance criteria, as checkboxes]

**Open**
[Open questions, blocking ones first]
```

## View — implementation issue (one unit of work)

One issue per Scope bullet, each carrying only the acceptance criteria that apply to it.
A scope bullet that cannot carry at least one criterion is not yet a unit of work — it is
a heading, and it needs splitting before it becomes an issue.

```markdown
Title: [id] [scope bullet, as a capability]

From `features/[id]-[slug].md` ([title]).

**Context**
[Summary, one paragraph]

**Done when**
- [ ] Given [context], when [action], then [result]
- [ ] Given [edge case], when [action], then [result]

**Notes**
[Only the dependencies and risks that touch this unit]
```

## View — one-page brief (for people who do not use the tracker)

The whole definition, in reading order, with the frontmatter rendered as a header line
and the sections unchanged. Used for a stakeholder who wants the document, not the tool.

## Round-tripping

The tracker will drift — someone edits the description in place. When that happens the
definition file wins, and the correction is made there first, then re-rendered. If the
tracker edit was right, copy it into the file in the same turn and say which section
changed; a view that silently disagrees with its source is worse than no view at all.
