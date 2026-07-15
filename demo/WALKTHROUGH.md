# Demo: A Full AI-Assisted Development Session

> **Scenario**: A real-world debugging session on a Node.js/TypeScript REST API called `user-service`.  
> **Bug report**: "Users are getting logged out randomly after ~30 minutes even though the JWT should last 24 hours."  
> **What this demonstrates**: session start → debug → fix → code review → commit → knowledge capture → session end

---

## The Project

```
user-service/
├── src/
│   ├── auth/
│   │   ├── jwt.ts           ← JWT creation and verification
│   │   └── middleware.ts    ← Express auth middleware
│   ├── routes/
│   │   └── users.ts
│   └── index.ts
├── tests/
│   └── auth.test.ts
├── AGENTS.md
└── .claude/
    └── skills/
```

`AGENTS.md` has been customized for this project:
```markdown
## Project Conventions
- Language: TypeScript (strict mode)
- Framework: Express 5
- Auth: JWT with RS256 (asymmetric keys)
- Tests: Vitest
- Branch: feature/<ticket-id>-short-description
```

---

## Step 1 — Session Start

The developer opens the terminal and types:

```
claude
```

**AI (automatic, from memory injection):**
```
Session started. Loading project memory...

From previous sessions I know:
- user-service uses RS256 asymmetric JWT (private key signs, public key verifies)
- The public key is loaded from PUBLIC_KEY_PATH env var at startup
- Vitest is the test runner: `npm test`
- Last session (2 days ago): added refresh token endpoint, tests passing

Open work from last session:
  → None committed — clean git status

What are we working on today?
```

**Developer:**
```
There's a bug: users get logged out after ~30 min even though tokens should last 24h.
Ticket: AUTH-142
```

---

## Step 2 — Debug Skill Invoked

The `debug` skill auto-invokes on "bug" + problem description.

**AI:**
```
Invoking /debug for AUTH-142.

Let me start systematically.

STEP 1 — What should happen vs. what does happen?
  EXPECTED: Token valid for 24h (86400s)
  ACTUAL: Users logged out after ~30 min

STEP 2 — Can we reproduce reliably?
  Question: Is it exactly 30 min, or roughly? And is it all users, or specific ones?
```

**Developer:**
```
It's roughly 30 min. Affects all users. Started after last week's deploy.
```

**AI:**
```
"Started after last week's deploy" — that narrows the scope to recent changes.

Let me check what changed in auth last week.
```

```bash
git --no-pager log --oneline --since="8 days ago" -- src/auth/
```

```
a3f92c1 feat(auth): add refresh token endpoint
b7d4e08 chore(auth): rotate signing keys for quarterly rotation
```

**AI:**
```
Two candidates. Key rotation (b7d4e08) is more likely to affect token validity.
Let me look at that commit and the current jwt.ts.
```

```bash
git --no-pager show b7d4e08 -- src/auth/jwt.ts
```

```diff
// src/auth/jwt.ts
- const TOKEN_TTL = '24h';
+ const TOKEN_TTL = 1800;  // 30 minutes — testing value, forgot to revert
```

**AI:**
```
Root cause found.

HYPOTHESIS CONFIRMED:
  b7d4e08 changed TOKEN_TTL from '24h' (string, parsed by jsonwebtoken)
  to 1800 (number, interpreted as seconds = 30 minutes).
  This was a testing value that was never reverted before shipping.

IMPACT:
  All tokens issued after b7d4e08 merged expire in 30 min.
  Tokens issued before that commit are unaffected until they expire naturally.

Fix: restore TOKEN_TTL to '24h' (or use 86400 as a number — both work with jsonwebtoken).
I'll use the string form '24h' as it's more readable and matches existing convention.
```

---

## Step 3 — The Fix

**AI:**
```
Making the change:
```

```typescript
// src/auth/jwt.ts  (before)
const TOKEN_TTL = 1800;  // 30 minutes — testing value, forgot to revert

// src/auth/jwt.ts  (after)
const TOKEN_TTL = '24h';
```

```bash
npm test
```

```
✓ auth/jwt.ts > sign and verify token > creates valid 24h token (12ms)
✓ auth/jwt.ts > sign and verify token > rejects expired token (8ms)
✓ auth/middleware.ts > rejects missing token (5ms)
✓ auth/middleware.ts > rejects tampered token (6ms)
✓ auth/middleware.ts > accepts valid token (9ms)

Test Files  1 passed
Tests       5 passed
Duration    0.31s
```

**AI:**
```
All tests pass. One more check — I want to add a regression test so this specific bug
cannot ship again undetected.
```

```typescript
// tests/auth.test.ts  (added)
it('token TTL is at least 1 hour', async () => {
  const token = signToken({ userId: 'u1' });
  const decoded = jwt.decode(token) as jwt.JwtPayload;
  const ttlSeconds = decoded.exp! - decoded.iat!;
  expect(ttlSeconds).toBeGreaterThanOrEqual(3600);  // guard against test values
});
```

```bash
npm test
```

```
✓ auth/jwt.ts > sign and verify token > creates valid 24h token (12ms)
✓ auth/jwt.ts > sign and verify token > rejects expired token (8ms)
✓ auth/jwt.ts > token TTL is at least 1 hour (4ms)  ← NEW
✓ auth/middleware.ts > ... (3 tests)

Test Files  1 passed
Tests       6 passed
```

---

## Step 4 — Code Review

**Developer:**
```
/code-review
```

**AI (code-review skill):**
```
Reviewing staged changes for AUTH-142.

FILES CHANGED:
  src/auth/jwt.ts        +1 / -1
  tests/auth.test.ts     +7 / -0

─────────────────────────────────────────────

src/auth/jwt.ts

✅ GOOD — TOKEN_TTL restored to '24h'. The string form is idiomatic for jsonwebtoken
   and more readable than a raw second count.

─────────────────────────────────────────────

tests/auth.test.ts

✅ GOOD — Regression test added. Asserts TTL ≥ 1 hour, which will catch any future
   "testing value" being accidentally shipped.

🔵 SUGGESTION — Consider naming the constant:
     const ONE_HOUR_SECONDS = 3600;
     expect(ttlSeconds).toBeGreaterThanOrEqual(ONE_HOUR_SECONDS);
   Minor — not blocking.

─────────────────────────────────────────────

VERDICT: ✅ APPROVE — No blockers. Small suggestion only.
```

**Developer applies the suggestion, then:**

```
/commit
```

---

## Step 5 — Commit Skill

**AI (commit skill):**
```
Inspecting staged changes...

git diff --staged
  src/auth/jwt.ts     | TOKEN_TTL '24h' restored
  tests/auth.test.ts  | regression test: TTL ≥ 1 hour guard

Proposed commit:

  fix(auth): restore JWT token TTL to 24h

  TOKEN_TTL was accidentally set to 1800 (30 min) during key rotation
  testing (b7d4e08) and was not reverted before shipping. All users
  were affected from that deploy onward.

  Adds regression test asserting TTL ≥ 1 hour to prevent recurrence.

  Closes AUTH-142

  Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

Commit? [Y/n]
```

**Developer:** `Y`

```bash
$ git --no-pager log --oneline -3
f1a88d2 fix(auth): restore JWT token TTL to 24h
a3f92c1 feat(auth): add refresh token endpoint
b7d4e08 chore(auth): rotate signing keys for quarterly rotation
```

---

## Step 6 — Knowledge Capture

**Developer:**
```
/learn
```

**AI (learn skill):**
```
Worth capturing from this session:

DISCOVERY: jsonwebtoken accepts both string ('24h') and number (seconds) for expiresIn.
The number form is silently valid — no error is thrown — making this class of bug
invisible until users start logging out.

Extracting the reusable principle...

  remember: jsonwebtoken silently accepts expiresIn as a number (seconds) with no
  validation — a testing value like 1800 ships cleanly and only manifests as
  "random logouts". Always use the string form ('24h', '7d') for readability,
  and add a TTL lower-bound test as a guard.
  — tags: #auth #jwt #typescript

Saved to project memory.

Also worth noting: key rotation commits are high-risk surface area. Consider adding
a checklist item to the rotation runbook: "verify TOKEN_TTL is not a debug value".
```

---

## Step 7 — Session End

**Developer:**
```
/flush
```

**AI:**
```
Writing session summary to memory...

─── SESSION LOG — 2026-07-15 ────────────────────

TICKET: AUTH-142 — Users logged out after 30 minutes

ROOT CAUSE: TOKEN_TTL set to 1800 (seconds) instead of '24h' (string) in b7d4e08.
Introduced during key rotation testing, not reverted before shipping.

RESOLUTION:
  - Restored TOKEN_TTL = '24h' in src/auth/jwt.ts
  - Added regression test (TTL ≥ 1h guard) in tests/auth.test.ts
  - Committed as fix(auth): restore JWT token TTL to 24h

FILES CHANGED:
  src/auth/jwt.ts, tests/auth.test.ts

KNOWLEDGE CAPTURED:
  - jsonwebtoken TTL gotcha (silent number/string ambiguity)
  - Recommendation to add TTL guard to key rotation runbook

SKILLS USED: debug, code-review, commit, learn
DURATION: ~25 minutes

─────────────────────────────────────────────────

Session log saved. See you next session.
```

---

## What Just Happened

| Phase | Time | Value delivered |
|-------|------|-----------------|
| Session start | 10s | Memory injected automatically — AI knew the stack, last session's work, and git state |
| `/debug` | 8 min | Systematic root cause analysis led straight to the commit that introduced the bug |
| Fix + regression test | 5 min | One-line fix + guard test preventing recurrence |
| `/code-review` | 2 min | Caught a minor naming improvement before commit |
| `/commit` | 1 min | Properly formatted conventional commit with ticket reference |
| `/learn` | 1 min | jsonwebtoken TTL gotcha saved to memory — next session won't re-discover this |
| `/flush` | 10s | Full session summary indexed for future search |

**Total: ~17 minutes from bug report to committed fix with regression test, documented root cause, and persistent knowledge.**

---

## What Happens Next Session

When a new session opens on this project, the AI will automatically surface:

```
From memory:
  - jsonwebtoken TTL gotcha: use string form ('24h'), not number — silent failure
    if numeric value left from testing. Guard with TTL lower-bound test.
  - Key rotation runbook should verify TOKEN_TTL is not a debug value.
  - Recent: AUTH-142 fixed in f1a88d2
```

**The next session starts smarter. That's the whole point.**

---

## Running This Yourself

```bash
# 1. Copy infrastructure into your project
cp AGENTS.md /your-project/
cp -r .claude/ /your-project/.claude/

# 2. Customize project conventions in AGENTS.md

# 3. Start a session
claude          # Claude Code
# or open VS Code with GitHub Copilot Chat

# 4. Describe your problem — skills invoke automatically
# Or use explicit slash commands: /debug, /commit, /code-review, /learn
```

See [session-protocol.md](../session-protocol.md) for the full session management guide.
