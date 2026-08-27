---
name: reconcile-docs
description: Find every place a rule or fact is restated across the repository's documents, give it a single home, and turn all other statements into references. Use when the user says "reconcile the docs", "these files disagree", "remove duplication between documents", or when two documents state the same rule differently.
when-to-use: reconcile docs, docs disagree, duplicate rules, doc drift, single source of truth, align documents
allowed-tools: powershell, bash
argument-hint: "[the rule, topic, or pair of files that disagree]"
---

# Reconcile Docs Skill — One Home Per Rule

## Purpose
Two documents stating the same rule will drift, and the drift is invisible until the copies disagree somewhere expensive. This skill finds every restatement, picks one home, and rewrites the rest as references — so the rule can only ever change in one place.

## Steps

### Step 1 — Find every statement of the rule
Search for the rule's key phrases and their likely rewordings — not just the exact wording you were shown:
```bash
grep -rn "key phrase\|alternate wording\|related term" --include="*.md" .
```
Success: a list of every file and line that states, restates, or paraphrases the rule. If only one site exists, stop — there is nothing to reconcile.

### Step 2 — Pick the single home
The home is the most authoritative document for that kind of rule — the one a reader would expect to be canonical (an operating charter for behavior rules, a skill for procedure, a README for structure). Where an explicit precedence rule exists between the documents, it decides.
Success: one file named as the home; every other site is now a reference candidate.

### Step 3 — Resolve conflicts before rewriting
Where two statements differ, decide which is correct *first* — usually the stricter or more specific one — and record why. Never average two versions into a third.
Success: a single agreed wording, with the losing version's difference noted in the commit message.

### Step 4 — Rewrite each other site as a reference
Keep only what is unique to that site (its local context), and point to the home for the rule itself. Make each replacement against an exact, verified-unique match:
```bash
# pattern: assert the old text appears exactly once before replacing it
python3 - <<'PY'
s = open("FILE.md").read()
old, new = "...", "..."
assert s.count(old) == 1, "not unique - refine the match"
open("FILE.md", "w").write(s.replace(old, new))
PY
```
Success: every edit landed where intended; no accidental second-site replacements.

### Step 5 — Re-sweep for stragglers
**The trap:** the drifted rule almost always appears in more places than the first search suggested — tables, mode rows, structure trees, and manuals restate rules in different words. After editing, search again for the *old* wording and the rule's synonyms:
```bash
grep -rn "old wording\|old path\|old command" --include="*.md" .
```
Success: zero hits for the superseded wording anywhere in the repository.

### Step 6 — Validate and state the evidence
Run the repository's checker and say exactly what was verified:
```bash
python3 tools/validate.py
```
Success: links, anchors, and frontmatter green — and the claim "one home, N references, zero stragglers" is backed by the step 5 sweep, not assumed.

## Scale
One drifted sentence needs steps 1, 4, and 5 stated in a line each. A parallel document system needs the full pass, and possibly a decision about whether the duplicate document should exist at all — that decision belongs to the owner, not this skill.
