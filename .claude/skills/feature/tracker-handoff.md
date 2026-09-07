# Tracker hand-off — posting a view, and notifying the reviewer

[`tracker-views.md`](tracker-views.md) says what a view looks like. This says when a view
is *posted* rather than handed over, and how the person who has to act on it finds out it
exists. A view that reaches nobody has not been handed off — it has been filed.

Whether posting is allowed at all is not decided here. That rule lives in the charter's
*Standing Constraints*, and this file checks it rather than restating it.

## The three preconditions

Post only when all three hold. If any one fails, render the view paste-ready and say in
one line which one failed. Never skip silently, and never post half of something.

1. **The charter names this tracker as a review channel.** Read *Standing Constraints* in
   the project's own `WORKING-CHARTER.md` — not a sibling project's, and not the guide's.
   A carve-out that has been written but not merged does not count: check the branch you
   are on.
2. **`features/tracker.json` exists** and names where the item goes and who to notify.
3. **The tracker's tools are actually bound in this session.** Look at the tools you have;
   do not infer them from configuration. A connector that is configured but unauthorised
   binds nothing, and adding one mid-session binds nothing either — these tools bind when
   the session is created. "Connected" in a connector listing means the transport reached
   the server, not that you are authorised to call it.

Precondition 3 fails silently and is the one that will catch you. Check it before
promising a post, not after.

## The config — `features/tracker.json`

Names and identifiers only. No token, no API key, no URL carrying a secret: the connector
holds the authorisation, and the charter forbids a credential in the repository.

```json
{
  "tracker": "linear",
  "target": {
    "team": "CabiCAD",
    "project": "CabiCAD Projects Board",
    "url": "https://linear.app/<workspace>/project/<slug>/overview"
  },
  "notify": [
    { "name": "Idan Gorali", "handle": "idan", "as": "reviewer" }
  ],
  "view": "project-overview",
  "post_when_status": ["draft", "ready"]
}
```

| Field | Means |
|-------|-------|
| `tracker` | The tool's name. Must match the one the charter names, or precondition 1 fails. |
| `target` | Where the item lands. `url` is for humans; the tools resolve `team`/`project`. |
| `notify` | Everyone who must learn the item exists. `as` records why, for the reader. |
| `view` | Which view from `tracker-views.md` to render. Default `project-overview`. |
| `post_when_status` | Which definition statuses get posted. A `draft` blocked on the reviewer is exactly the thing worth posting — that is how the question reaches them. |

## Posting

1. **Render** the named view from `tracker-views.md`. Unchanged: posting is not a licence
   to write different content.
2. **Search before creating**, matching on the definition's `id`. An id that already has an
   item is an update, never a second item. Duplicates in a tracker are worse than staleness.
3. **Create or update** the item.
4. **Notify** every `notify` entry — see below.
5. **Write the item's URL back** into the definition's frontmatter as `tracker:` and commit
   it with the definition. That is what makes step 2 possible next time, and what lets a
   reader walk from the file to the item and back. The linter allows the extra key.

## Notifying — assignment is not notification

Do all three, in the same turn as the post:

- **Assign** to the `reviewer` entry where the tracker has an assignee field.
- **Subscribe** every `notify` entry, so later comments reach them too.
- **Mention** them once in the body.

Assignment alone can be silent depending on the person's own notification settings. A
mention is the one that reliably arrives. Doing only the first is the most common way an
"automatic" hand-off turns out to have notified nobody.

Then say, in the turn, what was posted and who was notified, with the item URL. The owner
should never have to open the tracker to find out whether it worked.

## When a precondition fails

Name the one that failed and fall back to a paste-ready render. Do not retry the
authorisation, do not ask for a token, do not reach for a browser or a raw API call — the
charter rules out all three, and a hand-off that breaks the charter to succeed has failed.

If the failure is precondition 3, say plainly that it needs an interactive authorisation
**and** a new session afterwards, since neither alone is enough.

## Round-tripping

The definition file remains the source of truth; a posted item is still a view. When the
two disagree, [`tracker-views.md`](tracker-views.md) governs what happens next.
