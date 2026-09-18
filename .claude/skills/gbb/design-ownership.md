# Design Ownership — the gate that bites in the repository

The intent in [`design-intent.md`](design-intent.md) says a surface is done when its
tests pass in the running product. A rule nobody enforces is a wish. This file makes
it enforceable in a project's own repository through two mechanisms that GitHub
already has: a `CODEOWNERS` file naming who must review every design-owned path, and a
pull-request checklist that asks for the intent's evidence. Neither is a CCGG file —
both are written into the *project* by `/gbb --intent` on first use, and edited there.

## What CODEOWNERS actually does
GitHub reads `.github/CODEOWNERS` (or `CODEOWNERS` at the root or under `docs/`) and
requests a review from the listed owner on any pull request touching a matching path.
It **only blocks a merge when branch protection on the base branch has "Require
review from Code Owners" switched on** — without that setting the file is a
suggestion. Later rules win over earlier ones for the same path. Verify the current
syntax against GitHub's documentation before writing product facts; the file below was
checked against the documented format at the time of writing.

## The template
Written to `.github/CODEOWNERS` in the project. Replace `@your-org/ui-ux-team` with the
real team or, on a one-person project, the owner's own handle — the owner reviewing
their own design change against the intent's tests is the point, not a formality.

```
# Design-owned paths — a change here is a design change and is reviewed as one.
# Enforced only when the base branch requires review from code owners.
# Later rules take precedence over earlier ones.

# 1. The intent, the ladder, and the evidence they rest on
design/                            @your-org/ui-ux-team
design/**                          @your-org/ui-ux-team
.github/PULL_REQUEST_TEMPLATE.md   @your-org/ui-ux-team

# 2. Tokens, themes and style configuration — the Language section made real
tailwind.config.*                  @your-org/ui-ux-team
postcss.config.*                   @your-org/ui-ux-team
**/styles/                         @your-org/ui-ux-team
**/theme/                          @your-org/ui-ux-team
**/tokens/                         @your-org/ui-ux-team
**/*.css                           @your-org/ui-ux-team
**/*.scss                          @your-org/ui-ux-team
**/*.less                          @your-org/ui-ux-team

# 3. Design-system components and icons
src/components/ui/                 @your-org/ui-ux-team
src/components/design-system/      @your-org/ui-ux-team
**/assets/icons/                   @your-org/ui-ux-team
**/*.svg                           @your-org/ui-ux-team

# 4. Design tool exports
**/*.fig                           @your-org/ui-ux-team
**/design-assets/                  @your-org/ui-ux-team
```

Adjust section 3 to where the project keeps its components; the paths above are the
common layouts, not a rule. A path that the intent's Language section governs and this
file does not list is a gap — add it in the same change that adds the path.

## The pull-request checklist
The owner review needs something to review against. The project's
`.github/PULL_REQUEST_TEMPLATE.md` gains a section that a design-owned change fills
in; a reviewer refuses a pull request that leaves it empty:

```markdown
## Design intent
<!-- Required when the change touches a path in CODEOWNERS sections 1–4. -->
- Intent file: `design/INTENT-<slug>.md`, part(s) this change serves: …
- Tests run in the running product (layer · test · result):
  - Sense · contrast on every surface touched · …
  - Attention · one headline, response under 100 ms · …
  - Recognition · icon recognition, where-am-I · …
  - Feeling · anti-feeling review, reduced motion · …
  - Action · thumb zone, one hand, recovery · …
- Screenshots: `design/walks/<date>/` — before and after, same viewport and lighting
- Intent revised? no / yes — ledger entry dated …
```

Only the layers the change touches need rows; a row that says "not run" is honest and
a reviewer decides whether it may merge. A row that is missing is the reviewer's refusal.

## Setting it up — the owner's steps
CCGG cannot switch branch protection on; that is a repository setting.
1. Commit `.github/CODEOWNERS` and the pull-request template section from this file.
2. Repository → Settings → Branches → the rule for the default branch → enable
   "Require a pull request before merging" and, under it, "Require review from Code
   Owners". Success looks like: a pull request touching any `*.css` file shows the
   owner as a requested reviewer and the merge button stays disabled until they approve.
3. On a one-person project, GitHub does not let an author approve their own pull
   request. Either add a second account or team as the owner, or keep the file for the
   review request and the checklist and rely on `/ship`'s gate for the intent tests.

## How GBB uses it
- `/gbb --intent` on first use offers to write both files into the project as a
  pick-list; they are project files, never CCGG-owned, and `update.sh` never touches them.
- The ladder's handoff names the intent tests in each feature; the checklist is where
  their results land on the pull request, so the review sees the evidence and not a claim.
- `/ship` treats a design-owned change without a filled checklist as a failing
  requirement check: the stage is not passed by a green CI alone.
