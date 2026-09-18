#!/usr/bin/env python3
"""Repository validator — the executable quality gate for this documentation repo.

Checks, in order:
  1. No tracked markdown file is empty.
  2. Every relative markdown link resolves to a real file.
  3. Every heading anchor referenced in a link exists in the target file.
  4. Every .claude/skills/*/SKILL.md has valid frontmatter with the five house keys.
  5. Every skill appears in every catalog, and stated skill counts match reality.
  6. .claude/settings.json and .vscode/*.json parse as JSON.
  7. The root CLAUDE.md exists and imports @AGENTS.md (the bridge).
  8. Hook scripts pass bash -n and carry the executable bit in the git index.
  9. Always-loaded files carry no session-volatile content (cache stability).
 10. Always-loaded files link only into install.sh's copy set (drop-in contract).
 11. Feature definitions in features/ meet the schema (via tools/feature_lint.py).
 12. Subagent definitions in .claude/agents/ parse, and the audit's agents keep the
     read-only boundary F002 promises (no Bash outside the verifier, worktree
     isolation and write tools removed on the verifier, CLAUDE.md omitted).
 13. Skill frontmatter means what it says: no key that is a spelling variant of a
     documented product key (`when-to-use` for `when_to_use`), and every tool a
     skill grants is a tool the product has (`powershell, bash` grants nothing).
 14. No hook or shell script clones without a pinned ref, or pipes a download into
     a shell — a session-start hook that does either executes remote code unseen.
 15. No hidden characters (zero-width, bidirectional controls, Unicode tags, C0
     controls) in an always-loaded file or anything under .claude/ — text the model
     reads and the reviewer cannot see is an instruction channel.
 16. Every hook file is registered (settings.json or a subagent's hooks) and every
     registered hook file exists — a hook on one side only never fires or never runs.
 17. The settings.json env block that drives live sync is sane: CCGG_REPO carries
     a CCGG_REF, and CCGG_HOME is not under a shared temporary directory.
 18. Every @import in CLAUDE.md or AGENTS.md resolves to a tracked file.
 21. Every GitHub Actions `uses:` is pinned to a commit SHA — a tag moves, and a
     moved tag runs new code with the workflow's permissions.
 20. Every audit subagent still serializes into the inline JSON a headless run
     needs — a brief that only an interactive run can load is a boundary CI loses.
 24. Something runs the validator automatically — a repository that ships this
     gate must not rely on someone remembering to invoke it.
 23. No audit tool builds a child environment out of os.environ — code from the
     audited tree runs with an allow-list, never the operator's credentials.
 22. No workflow job both exposes a secret and runs a script from the checkout —
     tree code and a credential must not share a runner.
 19. Skill grants stay pinned: no bare Write, Edit, Bash, or NotebookEdit in
     allowed-tools; the audit skill's grants are exactly the audit's four commands
     and its report directory; skills that act outward (push, PR, merge, deploy,
     wire) carry disable-model-invocation: true, so only a typed command starts them.

Exit code 0 = clean, 1 = findings (each printed with file and reason).
Stdlib only — no dependencies to install.
"""

import ast
import io
import json
import os
import re
import shutil
import subprocess
import tokenize
import sys

ROOT = subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True, encoding="utf-8"
).strip()
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
SKILL_KEYS = ("name", "description", "when_to_use", "argument-hint", "purpose")
VOCAB_PATH = os.path.join("tools", "audit_vocab.json")
# A hook that clones without a pinned ref, or pipes a download into a shell, runs
# whatever the remote serves at that moment — with the user's permissions.
GIT_CLONE_RE = re.compile(r"\bgit\s+clone\b")
CLONE_PIN_RE = re.compile(r"(--branch|-b\s|--revision)")
FETCH_TO_SHELL_RE = re.compile(r"\b(curl|wget)\b[^|\n]*\|\s*(sudo\s+)?(sh|bash|zsh)\b")
# A skill's `description` is shown to the model in every session's listing,
# before any invocation, so whatever it says is context nobody asked for
# (finding R-005). Its job is matching a request: that needs no URL, no
# backtick, no shell substitution and no pipe. Patterns are kept as strings so
# tools/audit_facts.py can carry the identical tuple and a test can compare them.
DESCRIPTION_BANNED = (
    (r"https?://|\bwww\.", "a URL"),
    (r"`", "a backtick"),
    (r"\$\(|\$\{", "a shell substitution"),
    (r"\||&&", "a shell operator"),
)
DESCRIPTION_MAX = 600


def description_problems(path: str, description: str) -> list[str]:
    """Content rules for a frontmatter description, as messages.

    Deliberately not a rule: "no imperative sentences". Every description in
    this repository is one — "Design system architecture...", "Use when the
    user asks to..." — so that test would fail all twenty-seven skills and
    teach the next person to switch the check off.
    """
    if not isinstance(description, str):
        raise TypeError("description must be a string")
    problems = []
    for pattern, what in DESCRIPTION_BANNED:
        if re.search(pattern, description):
            problems.append(f"{path}: frontmatter 'description' contains {what} — the field loads in every session and is matched against a request, never followed")
    if len(description) > DESCRIPTION_MAX:
        problems.append(f"{path}: frontmatter 'description' is {len(description)} characters, over {DESCRIPTION_MAX} — a matcher, not a place to put instructions")
    return problems

findings: list[str] = []
cautions: list[str] = []


def fail(msg: str) -> None:
    findings.append(msg)


def warn(msg: str) -> None:
    """A configuration that works but gives up a guarantee the repository states.

    Kept out of `findings` on purpose: the exit code is the gate, and a gate
    that fails on a supported-but-weaker setting stops being a gate people run.
    A caution is printed every time and never changes the verdict.
    """
    cautions.append(msg)


def tracked(pattern: str) -> list[str]:
    """Files git knows or would add: the index plus untracked, minus ignored.

    The index alone made a skill that update.sh had just dropped into
    .claude/skills/ — real, on disk, listed in the catalog — invisible to the
    frontmatter checks and "does not exist" to the catalog check, until
    somebody staged it (MemoMe audit 2026-09-17, H-5). Ignored files stay
    out, so scratch and build output never count.
    """
    out = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", pattern],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    return sorted({line for line in out.splitlines() if line})


def strip_code_blocks(lines: list[str]) -> list[str]:
    """The lines outside fenced code blocks, blanked rather than dropped.

    A fenced block is a transcript, not prose. A regex such as the one for
    imperial measurements is also valid markdown link syntax, so a documented
    pattern gets chased as a link to a file named after its capture group.
    Blanking instead of removing keeps line numbers aligned with the file.
    """
    out: list[str] = []
    fence: str | None = None
    for line in lines:
        marker = re.match(r"\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)[0]
            if fence is None:
                fence = token
                out.append("")
                continue
            if token == fence:
                fence = None
                out.append("")
                continue
        out.append("" if fence is not None else line)
    return out


INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")


def blank_inline_code(text: str) -> str:
    """Inline code spans replaced by spaces of the same length.

    A backticked `[x](path)` is a quoted example, not a link — an audit report
    that documents a probe line, or a skill that shows link syntax, must not be
    chased as a reference. Same-length blanks keep column positions stable.
    """
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), text)


def slugify(heading: str) -> str:
    """The anchor GitHub generates for a heading.

    Two details decide whether a link resolves, and getting either wrong
    reports correct links as broken:

    * An inline link in a heading contributes only its text. Slugging the raw
      line folds the URL in too, producing a slug nobody would write by hand.
    * Each space becomes its own hyphen. Punctuation is deleted in place, so
      "Registration + dispatch" leaves two spaces behind and renders as
      "registration--dispatch". Collapsing runs of whitespace to a single
      hyphen — the obvious reading — breaks every heading holding "&", "+"
      or an em dash.
    """
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s", "-", text)


def heading_slugs(path: str) -> set[str]:
    slugs = set()
    with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as fh:
        for line in strip_code_blocks(fh.read().splitlines()):
            if line.startswith("#"):
                slugs.add(slugify(line.lstrip("#")))
    return slugs


def check_markdown() -> None:
    for path in tracked("*.md"):
        full = os.path.join(ROOT, path)
        if os.path.getsize(full) == 0:
            fail(f"{path}: file is empty")
            continue
        raw = open(full, encoding="utf-8", errors="replace").read()
        content = blank_inline_code("\n".join(strip_code_blocks(raw.splitlines())))
        for match in LINK_RE.finditer(content):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            file_part, _, anchor = target.partition("#")
            if not file_part:
                continue
            dest = os.path.normpath(os.path.join(os.path.dirname(path), file_part))
            if not os.path.exists(os.path.join(ROOT, dest)):
                fail(f"{path}: broken link -> {target}")
            elif anchor and dest.endswith(".md") and anchor not in heading_slugs(dest):
                fail(f"{path}: missing anchor -> {target}")


def frontmatter_scalar_problem(line: str) -> str | None:
    """Why this frontmatter line fails to parse as YAML, or None.

    An unquoted scalar containing ": " ends the key at the *first* colon and
    leaves a second mapping-looking fragment behind, so the whole block is
    invalid and every key in it — description included — is lost. Skills stay
    listed but lose the description the model matches on, which silently
    disables auto-invocation. Stdlib only, so this checks the one construct
    that actually bit us rather than parsing YAML in full.
    """
    if ": " not in line:
        return None
    value = line.split(": ", 1)[1].strip()
    if value[:1] in ('"', "'") or not value:
        return None
    if ": " in value:
        return f"unquoted value contains ': ' — wrap it in double quotes: {line.strip()}"
    return None


def load_vocab() -> dict | None:
    """tools/audit_vocab.json — the documented product surface checks 13 compare against."""
    try:
        with open(os.path.join(ROOT, VOCAB_PATH), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def key_spelling_variant(key: str, documented: list[str]) -> str | None:
    """The documented key this one is a hyphen/underscore/case variant of, or None."""
    norm = key.replace("-", "").replace("_", "").lower()
    for doc in documented:
        if doc != key and doc.replace("-", "").replace("_", "").lower() == norm:
            return doc
    return None


def skill_semantics_problems(path: str, fields: dict[str, str], vocab: dict) -> list[str]:
    """Check 13, as messages: variant keys and unknown tool names in one skill's frontmatter."""
    problems = []
    for key in fields:
        variant = key_spelling_variant(key, vocab["skill_keys"])
        if variant:
            problems.append(f"{path}: frontmatter key '{key}' is not read by Claude Code — the documented key is '{variant}'")
    known = set(vocab["tools"])
    for field in ("allowed-tools", "disallowed-tools"):
        value = fields.get(field, "")
        for entry in re.split(r"[,\s]+", re.sub(r"\([^)]*\)", "", value.strip("[] "))):
            entry = entry.strip().strip("'\"")
            if entry and entry != "*" and not entry.startswith("mcp__") and entry not in known:
                problems.append(f"{path}: {field} names '{entry}', which is not a Claude Code tool — the grant applies to nothing")
    return problems


def check_skill_semantics() -> None:
    skills = tracked(".claude/skills/*/SKILL.md")
    if not skills:
        return
    vocab = load_vocab()
    if vocab is None:
        fail(f"{VOCAB_PATH}: missing or unreadable — install.sh and update.sh ship it; skill semantics not checked")
        return
    for path in skills:
        lines = open(os.path.join(ROOT, path), encoding="utf-8").read().splitlines()
        fields, _ = parse_frontmatter_fields(lines)
        if fields is None:
            continue  # check_skills already reported the structural problem
        for problem in skill_semantics_problems(path, fields, vocab):
            fail(problem)


def fetch_exec_problems(path: str, text: str) -> list[str]:
    """Check 14, as messages: unpinned clones and download-to-shell pipes in one script."""
    problems = []
    for no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if GIT_CLONE_RE.search(line) and not CLONE_PIN_RE.search(line):
            problems.append(f"{path}:{no}: git clone without --branch/--revision — pin the ref a session executes")
        if FETCH_TO_SHELL_RE.search(line):
            problems.append(f"{path}:{no}: downloads and pipes into a shell — never execute what a remote serves unseen")
    return problems


def fetch_exec_paths() -> list[str]:
    """Scripts plus every file whose content reaches the model as instructions.

    An unpinned clone or a download-to-shell pipe is as live in a sentence a
    skill tells the agent to follow as it is in a hook, and check 14 read only
    hooks and *.sh files, so a skill body was never looked at (finding R-004,
    and the one probe the gate was missing, T-005).
    """
    return list(dict.fromkeys(tracked(".claude/hooks/*") + tracked("*.sh") + instruction_files()))


def check_fetch_exec() -> None:
    for path in fetch_exec_paths():
        text = open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read()
        for problem in fetch_exec_problems(path, text):
            fail(problem)


def check_skills() -> None:
    for path in tracked(".claude/skills/*/SKILL.md"):
        lines = open(os.path.join(ROOT, path), encoding="utf-8").read().splitlines()
        if not lines or lines[0].strip() != "---":
            fail(f"{path}: frontmatter must start with --- on line 1")
            continue
        try:
            end = lines[1:].index("---") + 1
        except ValueError:
            fail(f"{path}: frontmatter never closed with ---")
            continue
        for ln in lines[1:end]:
            problem = frontmatter_scalar_problem(ln)
            if problem:
                fail(f"{path}: {problem}")
        keys = {ln.split(":", 1)[0].strip() for ln in lines[1:end] if ":" in ln}
        for key in SKILL_KEYS:
            if key not in keys:
                fail(f"{path}: frontmatter missing key '{key}'")
        fields, _ = parse_frontmatter_fields(lines)
        for problem in skill_identity_problems(path, fields or {}):
            fail(problem)


def skill_identity_problems(path: str, fields: dict[str, str]) -> list[str]:
    """A skill with an empty name or description is a skill the model cannot pick.

    The description is what the model matches a request against; empty, the
    skill exists in the catalog and never auto-invokes. The name is display-only
    for project skills, so the directory is the command — a name that differs
    from it documents a `/command` that does not exist.
    """
    problems = []
    for key in ("name", "description"):
        if not fields.get(key, "").strip("'\" "):
            problems.append(f"{path}: frontmatter '{key}' is empty")
    problems += description_problems(path, fields.get("description", "").strip("'\" "))
    dirname = os.path.basename(os.path.dirname(path))
    name = fields.get("name", "").strip("'\" ")
    if name and dirname and name != dirname:
        problems.append(f"{path}: name '{name}' differs from its directory '{dirname}' — the command is /{dirname}")
    return problems


AGENT_REQUIRED_KEYS = ("name", "description")
SPECIALIST_TOOLS = {"Read", "Glob", "Grep"}
VERIFIER_DISALLOWED = {"Write", "Edit", "NotebookEdit"}


def parse_frontmatter_fields(lines: list[str]) -> tuple[dict[str, str] | None, str | None]:
    """Top-level key → value of a frontmatter block, or (None, why)."""
    if not lines or lines[0].strip() != "---":
        return None, "frontmatter must start with --- on line 1"
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return None, "frontmatter never closed with ---"
    fields: dict[str, str] = {}
    for ln in lines[1:end]:
        if not ln or ln[0] in " \t" or ":" not in ln:
            continue
        key, _, value = ln.partition(":")
        fields[key.strip()] = value.strip()
    return fields, None


def split_tool_list(value: str) -> set[str]:
    """`Read, Glob Grep` → {"Read", "Glob", "Grep"}; a specifier keeps its tool name."""
    bare = re.sub(r"\([^)]*\)", "", value.strip("[] "))
    return {t.strip() for t in re.split(r"[,\s]+", bare) if t.strip()}


def agent_frontmatter_problems(path: str, fields: dict[str, str]) -> list[str]:
    """The F002 boundary for audit agents, as messages; empty when it holds.

    Specialists (`audit-*` except the verifier) may hold only Read, Glob, Grep —
    the `tools` field cannot narrow Bash, so the only read-only Bash is no Bash.
    The verifier alone executes, inside a worktree, with the write tools removed.
    Every audit agent omits CLAUDE.md: the audited rules are evidence, not orders.
    """
    problems = [f"{path}: frontmatter missing key '{k}'" for k in AGENT_REQUIRED_KEYS if not fields.get(k)]
    problems += description_problems(path, fields.get("description", "").strip("'\" "))
    name = fields.get("name", "")
    if not name.startswith("audit-"):
        return problems
    if fields.get("omitClaudeMd", "").lower() != "true":
        problems.append(f"{path}: audit agents must set omitClaudeMd: true")
    if name == "audit-verifier":
        if fields.get("isolation") != "worktree":
            problems.append(f"{path}: the verifier must set isolation: worktree")
        missing = VERIFIER_DISALLOWED - split_tool_list(fields.get("disallowedTools", ""))
        if missing:
            problems.append(f"{path}: the verifier must disallow {', '.join(sorted(missing))}")
        return problems
    tools = split_tool_list(fields.get("tools", ""))
    if tools != SPECIALIST_TOOLS:
        problems.append(f"{path}: specialist tools must be exactly Read, Glob, Grep — got {', '.join(sorted(tools)) or 'nothing'}")
    return problems


def check_agents() -> None:
    for path in tracked(".claude/agents/*.md"):
        lines = open(os.path.join(ROOT, path), encoding="utf-8").read().splitlines()
        fields, why = parse_frontmatter_fields(lines)
        if fields is None:
            fail(f"{path}: {why}")
            continue
        for ln in lines[1:]:
            if ln.strip() == "---":
                break
            problem = frontmatter_scalar_problem(ln)
            if problem:
                fail(f"{path}: {problem}")
        for problem in agent_frontmatter_problems(path, fields):
            fail(problem)


def check_configs() -> None:
    for path in tracked(".claude/settings.json") + tracked(".vscode/*.json"):
        try:
            json.load(open(os.path.join(ROOT, path), encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"{path}: invalid JSON — {exc}")


def check_catalogs() -> None:
    """Every skill directory appears in every catalog, and stated counts match.

    Mechanizes the drift class caught by hand in review: counts bumped while
    catalog content lagged, or a skill added without its catalog rows.
    A file is treated as a catalog only when it actually contains the CCGG
    catalog marker — a downstream project's own README.md (or manual) without
    the skills table is skipped, so this validator is safe to copy into repos
    that adopt the skills without the guide's docs.
    """
    skills = sorted(
        os.path.basename(os.path.dirname(p))
        for p in tracked(".claude/skills/*/SKILL.md")
    )

    def read_catalog(name: str, marker: str) -> str | None:
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            return None
        text = open(path, encoding="utf-8").read()
        if marker not in text:
            return None  # the project's own doc, not a CCGG catalog
        return text

    readme = read_catalog("README.md", "| Skill | Invoke |")
    agents = read_catalog("AGENTS.md", "| Skill | Purpose |")
    manual = read_catalog("USER-MANUAL.md", "### `/")

    for name in skills:
        if readme is not None and f"| `{name}` | `/{name}` |" not in readme:
            fail(f"README.md: skill '{name}' missing from the Available Skills table")
        if agents is not None and f"| `/{name}` |" not in agents:
            fail(f"AGENTS.md: skill '{name}' missing from the skill table")
        if manual is not None and f"### `/{name}` —" not in manual:
            fail(f"USER-MANUAL.md: skill '{name}' has no per-skill entry in section 6")

    if readme is not None:
        for row_name in re.findall(r"^\| `([a-z0-9-]+)` \| `/[a-z0-9-]+` \|", readme, re.M):
            if row_name not in skills:
                fail(f"README.md: table lists skill '{row_name}' but .claude/skills/{row_name}/ does not exist")
    if agents is not None:
        for row_name in re.findall(r"^\| `/([a-z0-9-]+)` \|", agents, re.M):
            if row_name not in skills:
                fail(f"AGENTS.md: table lists skill '{row_name}' but .claude/skills/{row_name}/ does not exist")

    count_re = re.compile(
        r"\b(\d+)\s+(?:production-ready\s+|reusable\s+|installed\s+)?[Ss]kill(?:s\b| workflows\b)"
    )
    for doc_name, text in (("README.md", readme), ("USER-MANUAL.md", manual)):
        if text is None:
            continue
        for stated in count_re.findall(text):
            if int(stated) != len(skills):
                fail(
                    f"{doc_name}: states {stated} skills but .claude/skills/ contains {len(skills)}"
                )


def check_context_budget() -> None:
    """Always-loaded files are paid for in every session's context — keep them lean.

    CLAUDE.md, AGENTS.md, and the charter load at every session start. Detail
    belongs in on-demand companion files (skill bodies load only at invocation).
    Budgets are generous; exceeding one means structure, not trimming words.
    """
    budgets = {"CLAUDE.md": 2_048, "AGENTS.md": 13_312, "WORKING-CHARTER.md": 13_312}
    for name, budget in budgets.items():
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            continue
        size = os.path.getsize(path)
        if size > budget:
            fail(
                f"{name}: {size} bytes exceeds the {budget}-byte always-loaded "
                f"context budget — move detail into on-demand companion files"
            )


ALWAYS_LOADED = ("CLAUDE.md", "AGENTS.md", "WORKING-CHARTER.md")
# Every tracked file whose content reaches the model as instructions — not only
# the rule files, but everything the rules tell the agent to open: a skill's
# companion pages, a decision record recalled before re-deciding, a cached
# research note, a feature definition. The scan here reached the three
# always-loaded files and .claude/**/*.md; MEMORY.md, the hooks, decisions/,
# features/ and knowledge-base/ sat outside it, and the audit's own scan in
# tools/audit_facts.py was narrower still (findings R-007 and R-014). This is
# the one home for the set: audit_facts.py carries the identical tuple and
# tools/test_validate.py compares the two.
INSTRUCTION_GLOBS = (
    "CLAUDE.md",
    "AGENTS.md",
    "WORKING-CHARTER.md",
    "MEMORY.md",
    ".claude/agents/*.md",
    ".claude/hooks/*",
    ".claude/references/*.md",
    ".claude/skills/*.md",
    "decisions/*.md",
    "features/*.md",
    "knowledge-base/*.md",
)
# Markdown, not everything: knowledge-base/ also holds research artifacts such as
# a .pptx, whose compressed bytes are full of control characters and which no
# rule tells the agent to read as text. Hooks are the exception — every one is a
# shell script, and what they print reaches the model as context.


def instruction_files() -> list[str]:
    """The tracked files INSTRUCTION_GLOBS names, sorted and deduplicated."""
    found: set[str] = set()
    for pattern in INSTRUCTION_GLOBS:
        found.update(tracked(pattern))
    return sorted(found)
VOLATILE_RES = (
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\blast (updated|generated|synced|run)\b", re.I),
)


def volatile_lines(text: str) -> list[tuple[int, str]]:
    """Lines carrying session-volatile content — ISO dates, 'last updated' markers.

    Always-loaded files must stay byte-stable: any churn invalidates the
    provider's prompt cache for every following session (charter, Efficiency).
    Pure function so the check is unit-testable without a repository.
    """
    hits = []
    for no, line in enumerate(text.splitlines(), 1):
        if any(rx.search(line) for rx in VOLATILE_RES):
            hits.append((no, line.strip()))
    return hits


def check_volatile_content() -> None:
    for name in ALWAYS_LOADED:
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8", errors="replace").read()
        for no, line in volatile_lines(text):
            fail(
                f"{name}:{no}: session-volatile content in an always-loaded file "
                f"(invalidates the prompt cache) — move it on-demand: {line[:60]}"
            )


INSTALLED_LINK_ROOTS = (
    "AGENTS.md",
    "WORKING-CHARTER.md",
    "CLAUDE.md",
    ".claude",
    ".gitattributes",
    "tools/validate.py",
    ".github/workflows/validate.yml",
)


def link_leaves_install_set(link: str) -> bool:
    """True when a link from an always-loaded file points outside install.sh's copies.

    The drop-in contract (charter, *Must never break*) bounds where a rule file
    may point. A link to something install.sh does not copy — a decision record,
    knowledge-base entry, or docs page — resolves here and breaks the link check
    in every installed project, where the target was never delivered. The repo
    that ships the validator is the one place this cannot be caught by running it.

    External links, bare anchors, and links this repo alone can resolve are the
    three cases people actually write, so each is decided explicitly rather than
    by a catch-all.
    """
    if link.startswith(("http://", "https://", "mailto:", "#")):
        return False
    file_part = link.partition("#")[0]
    if not file_part:
        return False  # a bare anchor stays inside its own file
    if file_part.startswith("./"):
        file_part = file_part[2:]
    return not any(
        file_part == root or file_part.startswith(root + "/")
        for root in INSTALLED_LINK_ROOTS
    )


def check_rule_file_links() -> None:
    for name in ALWAYS_LOADED:
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            continue
        raw = open(path, encoding="utf-8", errors="replace").read()
        content = blank_inline_code("\n".join(strip_code_blocks(raw.splitlines())))
        for match in LINK_RE.finditer(content):
            target = match.group(1)
            if link_leaves_install_set(target):
                fail(
                    f"{name}: links to {target}, which install.sh does not copy — "
                    f"the link breaks in every installed project; move the target "
                    f"under .claude/references/ or drop the link"
                )


def check_claude_md_bridge() -> None:
    """AGENTS.md only loads into Claude Code via the CLAUDE.md import bridge."""
    path = os.path.join(ROOT, "CLAUDE.md")
    if not os.path.exists(path):
        fail("CLAUDE.md: missing — AGENTS.md never loads into Claude Code without it")
    elif "@AGENTS.md" not in open(path, encoding="utf-8").read():
        fail("CLAUDE.md: does not import @AGENTS.md — the behavior rules never load")


def usable_bash() -> str | None:
    """The path to a bash that can actually run, or None.

    Resolving the interpreter rather than invoking the bare name matters on
    Windows, where `bash` hits an App Execution Alias for WSL that cannot
    launch Git Bash scripts and reports a relay error instead of a syntax
    error — every hook would come back "broken". The resolved path runs the
    real interpreter; the probe then confirms it before we trust its verdict.
    """
    path = shutil.which("bash")
    if path is None:
        return None
    try:
        probe = subprocess.run(
            [path, "-c", "exit 0"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None
    return path if probe.returncode == 0 else None


def check_hooks() -> None:
    index = subprocess.check_output(
        ["git", "ls-files", "-s", ".claude/hooks/"], cwd=ROOT, text=True, encoding="utf-8"
    )
    bash = usable_bash()
    for line in index.splitlines():
        mode, _, _, path = line.split(None, 3)
        if path.endswith(".sh"):
            if mode != "100755":
                fail(f"{path}: not executable in the git index (mode {mode})")
            if bash is None:
                continue
            probe = subprocess.run(
                [bash, "-n", os.path.join(ROOT, path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if probe.returncode != 0:
                fail(f"{path}: bash syntax error — {probe.stderr.strip()}")


# --- 15. hidden characters --------------------------------------------------
# Invisible in a diff, present in what the model reads. The two scans in this
# repository had each caught what the other missed — the audit had no tag
# characters or C0 controls, this one had no soft hyphen or directional marks
# (finding S-006) — so the set has one home: tools/audit_facts.py carries this
# string character-for-character and tools/test_validate.py compares them.
HIDDEN_PATTERN = (
    "[\u00ad\u061c\u180e"                 # soft hyphen, Arabic letter mark, Mongolian vowel separator
    "\u200b-\u200f"                        # zero-width space/non-joiner/joiner, LRM, RLM
    "\u202a-\u202e\u2066-\u2069"          # bidi embeddings, overrides and isolates
    "\u2060-\u2064\ufeff"                  # word joiner, invisible operators, BOM
    "\U000e0000-\U000e007f"                # Unicode tag characters
    "\x00-\x08\x0b\x0c\x0e-\x1f]"       # C0 controls except tab, newline, carriage return
)
HIDDEN_RE = re.compile(HIDDEN_PATTERN)


def hidden_characters(text: str) -> list[tuple[int, str]]:
    """(line number, U+XXXX) for every hidden character in text.

    Split on "\\n", never str.splitlines(): that treats U+000B, U+000C and
    U+001C-U+001E as line boundaries and removes them, so the three of them
    this pattern names could never be reported.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    found = []
    for n, line in enumerate(text.split("\n"), 1):
        for m in HIDDEN_RE.finditer(line):
            found.append((n, f"U+{ord(m.group(0)):04X}"))
    return found


def check_hidden_characters() -> None:
    for path in instruction_files():
        text = open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read()
        for line, code in hidden_characters(text)[:5]:
            fail(f"{path}:{line}: hidden character {code} — invisible to a reviewer, read by the model")


# --- 16. hook registration ----------------------------------------------------
HOOK_REF_RE = re.compile(r"\.claude/hooks/([A-Za-z0-9._-]+\.sh)")


def hook_references(settings_text: str, agent_texts: dict[str, str]) -> dict[str, str]:
    """hook file name → where it is registered, from settings.json and agent frontmatter."""
    refs: dict[str, str] = {}
    for name in HOOK_REF_RE.findall(settings_text):
        refs.setdefault(name, ".claude/settings.json")
    for path, text in agent_texts.items():
        lines = text.splitlines()
        end = lines[1:].index("---") + 1 if lines and "---" in lines[1:] else 0
        for name in HOOK_REF_RE.findall("\n".join(lines[:end])):
            refs.setdefault(name, path)
    return refs


def check_hook_registration() -> None:
    files = {os.path.basename(p) for p in tracked(".claude/hooks/*.sh")}
    settings_path = os.path.join(ROOT, ".claude", "settings.json")
    settings_text = open(settings_path, encoding="utf-8").read() if os.path.exists(settings_path) else ""
    agents = {p: open(os.path.join(ROOT, p), encoding="utf-8", errors="replace").read()
              for p in tracked(".claude/agents/*.md")}
    if not files and not settings_text:
        return
    refs = hook_references(settings_text, agents)
    for name in sorted(files - set(refs)):
        fail(f".claude/hooks/{name}: not registered in .claude/settings.json or any agent's hooks — it never fires")
    for name in sorted(set(refs) - files):
        fail(f"{refs[name]}: registers .claude/hooks/{name}, which is not a tracked file — the hook never runs")


# --- 17. live-sync env --------------------------------------------------------
SHARED_TMP = ("/tmp", "/var/tmp", "/dev/shm")
# The hook's own test for an immutable pin: .claude/hooks/session-start.sh's
# ccgg_is_sha accepts 40 lowercase hex characters and nothing else, so anything
# this does not match resolves through a name that its owner can move.
COMMIT_RE = re.compile(r"\A[0-9a-f]{40}\Z")
# What .claude/hooks/session-start.sh's ccgg_ref_ok accepts, in the one other
# place that reads CCGG_REF. A refname cannot begin with '-' or hold '..'.
REF_NAME_RE = re.compile(r"\A(?!-)(?!.*\.\.)[A-Za-z0-9._/-]+\Z")
ORIGIN_RECORD = os.path.join(".claude", "ccgg-origins")


def ccgg_origins(root: str) -> list[str] | None:
    """The origins this repository has recorded as trusted, or None if it has not.

    One URL per line in .claude/ccgg-origins, `#` comments and blanks ignored.
    The record lives outside settings.json so that re-pointing the sync at
    another repository is a named change a reviewer sees, rather than one line
    inside an env block (finding R-003). None and [] are different answers:
    no record constrains nothing, an empty record allows nothing.
    """
    path = os.path.join(root, ORIGIN_RECORD)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        lines = (line.strip() for line in fh)
        return [line for line in lines if line and not line.startswith("#")]


def ccgg_env_problems(env: dict, origins: list[str] | None = None) -> list[str]:
    """Problems with a settings.json env block that drives the session-start sync.

    `origins` is the trusted-origin record (None when the repository keeps none).
    """
    problems = []
    home = str(env.get("CCGG_HOME", "") or "")
    repo = str(env.get("CCGG_REPO", "") or "")
    ref = str(env.get("CCGG_REF", "") or "")
    if home and not repo:
        problems.append("env sets CCGG_HOME without CCGG_REPO — the hook then runs that clone's update.sh with no origin to check it against, and update.sh syncs skills, hooks, agents and tools/ into this project on every session start; set CCGG_REPO and CCGG_REF, or unset CCGG_HOME")
    elif repo and not ref:
        problems.append("env sets CCGG_REPO without CCGG_REF — the hook refuses an unpinned clone, so live sync never starts; pin a 40-hex commit")
    if home and (home in SHARED_TMP or home.startswith(tuple(t + "/" for t in SHARED_TMP))):
        problems.append("env sets CCGG_HOME under a shared temporary directory — anyone on the host can pre-create it; use a path under your home such as ~/.claude/ccgg-guide")
    if repo.startswith("http://"):
        problems.append("env sets CCGG_REPO over http:// — code that runs at every session start fetched without TLS")
    if repo and origins is not None and repo not in origins:
        problems.append(f"env sets CCGG_REPO to {repo}, which {ORIGIN_RECORD} does not list — add it there deliberately, or correct the env block")
    if repo and origins is None:
        # Was a caution, which never changed the verdict, so a settings.json
        # pointing the sync at any repository passed the gate (finding S-005).
        # The record is cheap to add and the whole point of it is that adding it
        # is a reviewed change; absent it, nothing cross-checks which repository
        # executes code at every session start.
        problems.append(f"env sets CCGG_REPO but this repository keeps no {ORIGIN_RECORD} record — create it listing the origins this project accepts, so which repository executes code at every session start is a reviewed fact")
    if repo and ref and not COMMIT_RE.match(ref):
        # Also a caution before. The hook refuses a name before any git call
        # (finding R-001 of the 2026-09-18 audit: it used to follow one every
        # session, with this verdict as the only brake), so a project that
        # pins one ships settings its own hook will not act on. This check keeps
        # the pin a reviewed fact in the diff rather than a line in a hook's
        # output (finding R-003). A claim the gate does not enforce is a claim.
        problems.append(f"env pins CCGG_REF to '{ref}', a name its owner can move — pin the 40-hex commit instead; a tag or branch hands whoever can move it the contents of every sync")
    if repo and ref and not REF_NAME_RE.match(ref):
        # The hook refuses this before any git call; the gate says so earlier
        # (finding S-006).
        problems.append(f"env sets CCGG_REF to '{ref}', which is not a refname — a value starting with '-' reaches git in option position, where --upload-pack names a program to run")
    return problems


def ccgg_env_warnings(env: dict, origins: list[str] | None = None) -> list[str]:
    """Settings that work but give up a guarantee the repository states elsewhere.

    The movable-ref and missing-record cautions that used to live here are
    failures now (findings R-003 and S-005): both decide which repository's code
    runs at every session start, and a caution never changed the verdict.
    """
    cautions_found = []
    repo = str(env.get("CCGG_REPO", "") or "")
    if not repo:
        return cautions_found
    if origins == []:
        cautions_found.append(f"env sets CCGG_REPO but {ORIGIN_RECORD} lists no origin, so every sync will be refused until one is added")
    return cautions_found


def check_ccgg_env() -> None:
    path = os.path.join(ROOT, ".claude", "settings.json")
    if not os.path.exists(path):
        return
    try:
        settings = json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError:
        return  # check 6 reports it
    env = settings.get("env") if isinstance(settings, dict) else None
    if not isinstance(env, dict):
        return
    origins = ccgg_origins(ROOT)
    for problem in ccgg_env_problems(env, origins):
        fail(f".claude/settings.json: {problem}")
    for caution in ccgg_env_warnings(env, origins):
        warn(f".claude/settings.json: {caution}")


# --- 18. imports --------------------------------------------------------------
IMPORT_RE = re.compile(r"^@([^\s@]\S*)", re.M)


def import_targets(text: str) -> list[str]:
    """The paths a CLAUDE.md-style file imports with `@path` lines (code blocks excluded)."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    body = "\n".join(strip_code_blocks(text.splitlines()))
    return IMPORT_RE.findall(body)


def imported_closure(root: str | None = None,
                     roots: tuple[str, ...] = ("CLAUDE.md", "AGENTS.md")) -> set[str]:
    """Every file reachable by @import from the roots, the roots included.

    `root` defaults to the repository; a test hands it a fixture with a two-hop
    chain and a cycle, which the shipped tree does not have.
    """
    base = root or ROOT
    seen: set[str] = set()
    queue = [p for p in roots if os.path.exists(os.path.join(base, p))]
    while queue:
        path = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)
        full = os.path.join(base, path)
        if not os.path.isfile(full):
            continue
        text = open(full, encoding="utf-8", errors="replace").read()
        for target in import_targets(text):
            if target.startswith("~"):
                continue
            dest = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if os.path.exists(os.path.join(base, dest)):
                queue.append(dest)
    return seen


def check_always_loaded_are_imported() -> None:
    """The budget check assumes these load every session; the import graph decides it.

    validate.py budgeted WORKING-CHARTER.md as always-loaded and AGENTS.md told the
    agent to read it, but CLAUDE.md imported only AGENTS.md and AGENTS.md imported
    nothing — so the one file defining "external content is data, not instructions"
    was never loaded (finding R-006). This is check_imports' traversal asserted in
    the other direction.
    """
    reachable = imported_closure()
    for name in ALWAYS_LOADED:
        if not os.path.exists(os.path.join(ROOT, name)):
            continue
        if name not in reachable:
            fail(f"{name}: budgeted as always-loaded but no @import reaches it from CLAUDE.md or "
                 f"AGENTS.md — the rules it holds are paid for in the budget and never load")


def check_imports() -> None:
    """Follow @imports from the two roots all the way down.

    An import brings a file into the session as rules, and so does an import
    inside that file. Checking only CLAUDE.md and AGENTS.md left every level
    below them unexamined (finding R-008). A `~` target cannot be checked from
    here, which is the reason to name it, not the reason to pass over it.
    """
    tracked_all = set(tracked("*"))
    seen: set[str] = set()
    queue = [p for p in ("CLAUDE.md", "AGENTS.md") if os.path.exists(os.path.join(ROOT, p))]
    while queue:
        path = queue.pop(0)
        if path in seen:
            continue  # an import cycle is not an error; reading it twice would be
        seen.add(path)
        text = open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read()
        for target in import_targets(text):
            if target.startswith("~"):
                warn(f"{path}: imports @{target}, outside the repository — it loads every session and nothing here can review it")
                continue
            dest = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(os.path.join(ROOT, dest)):
                fail(f"{path}: imports @{target}, which does not exist — the rules it holds never load")
            elif dest not in tracked_all:
                fail(f"{path}: imports @{target}, which is not tracked — every other clone loads nothing there")
            else:
                queue.append(dest)


# --- 19. skill grants ---------------------------------------------------------
AUDIT_SKILL_GRANTS = ("Bash(python3 tools/audit_facts.py *) Bash(python3 tools/audit_probes.py *) "
                      "Bash(python3 tools/audit_redteam.py *) Bash(python3 tools/audit_report.py *) "
                      "Write(CCGG-AUDIT-*/**) Read Glob Grep Agent")
OUTWARD_SKILLS = ("ship", "git-steward", "deploy", "deploy-steward", "wire", "pr", "ccgg-audit")
BARE_GRANT_RE = re.compile(r"\b(Write|Edit|Bash|NotebookEdit)\b(?!\()")


def skill_grant_problems(path: str, fields: dict[str, str]) -> list[str]:
    """Grants a skill pre-approves: a bare write or shell grant approves everything."""
    problems = []
    name = os.path.basename(os.path.dirname(path))
    grants = fields.get("allowed-tools", "").strip("'\" ")
    for tool in sorted(set(BARE_GRANT_RE.findall(grants))):
        problems.append(f"{path}: allowed-tools grants bare {tool} — pre-approves every {tool} call; scope it with a specifier")
    if name == "ccgg-audit" and grants and grants != AUDIT_SKILL_GRANTS:
        problems.append(f"{path}: the audit's allowed-tools drifted from the pinned set (tools/validate.py AUDIT_SKILL_GRANTS)")
    if name in OUTWARD_SKILLS and fields.get("disable-model-invocation", "").strip().lower() != "true":
        problems.append(f"{path}: acts outward (push, PR, merge, deploy, wire) but lacks disable-model-invocation: true — the model can start it unasked")
    return problems


def check_skill_grants() -> None:
    for path in tracked(".claude/skills/*/SKILL.md"):
        lines = open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read().splitlines()
        fields, _ = parse_frontmatter_fields(lines)
        if fields is None:
            continue
        for problem in skill_grant_problems(path, fields):
            fail(problem)


# --- 20. agents survive the trip to a headless run ----------------------------
def check_agents_serialize() -> None:
    """The briefs a headless audit gets are built from these files; prove they build.

    Optional like the feature linter: a project that adopted the validator without
    the audit tooling has nothing to check here.
    """
    if not tracked(".claude/agents/audit-*.md"):
        return
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import audit_agents_json
    except ImportError:
        return
    try:
        definitions = audit_agents_json.build(
            ROOT, audit_agents_json.DEFAULT_DIR, audit_agents_json.DEFAULT_GLOB, None, None
        )
    except audit_agents_json.AgentFileError as exc:
        fail(f".claude/agents/: {exc}")
        return
    for name, definition in definitions.items():
        if not definition.get("prompt", "").strip():
            fail(f".claude/agents/{name}.md: no brief survives serialization")


# --- 21. workflow actions are pinned, and npm installs name an exact version ------------------------------------------
USES_RE = re.compile(r"^\s*-?\s*uses:\s*(\S+)", re.M)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


# A global install in a job that later holds a secret is a dependency nobody
# reviewed. `@latest`, a bare name, or a range all resolve to whatever the registry
# serves that minute; only an exact version is a decision someone made.
NPM_INSTALL_RE = re.compile(r"npm\s+(?:install|i|add)\s+(?:-g\s+|--global\s+)?([^\s;&|]+)", re.M)
EXACT_NPM_VERSION_RE = re.compile(r"^@?[^@]+@\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?$")


def unpinned_npm_installs(text: str) -> list[str]:
    """Every npm install target in a workflow that is not pinned to an exact version.

    A value interpolated from the workflow's own env (npm i -g "pkg@${VER}") counts
    as pinned: the pin has simply been named once instead of twice. The registry
    never sees the variable, so what matters is that a literal version exists in the
    file, which check_workflow_pins confirms separately.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    loose = []
    for raw in NPM_INSTALL_RE.findall(text):
        spec = raw.strip("\"'")
        if spec.startswith("-"):
            continue                       # a flag, not a package
        if "$" in spec:                    # pinned through a variable; checked below
            continue
        if not EXACT_NPM_VERSION_RE.match(spec):
            loose.append(spec)
    return loose


def unresolved_npm_version_vars(text: str) -> list[str]:
    """Env names an npm install pins through that the workflow never defines literally."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    missing = []
    for raw in NPM_INSTALL_RE.findall(text):
        spec = raw.strip("\"'")
        for name in re.findall(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?", spec):
            if not re.search(rf"^\s*{name}:\s*[\"']?\d+\.\d+\.\d+", text, re.M):
                missing.append(name)
    return missing


def unpinned_actions(text: str) -> list[str]:
    """Every `uses:` reference in a workflow that is not a 40-hex commit SHA."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    loose = []
    for ref in USES_RE.findall(text):
        ref = ref.strip("\"'")
        if ref.startswith(("./", "docker://")):
            continue  # a path in this repository, or an image with its own digest
        _, _, version = ref.partition("@")
        if not SHA_RE.match(version):
            loose.append(ref)
    return loose


def check_workflow_pins() -> None:
    for path in tracked(".github/workflows/*.yml") + tracked(".github/workflows/*.yaml"):
        with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for ref in unpinned_actions(text):
            fail(f"{path}: uses {ref} — pin the action to a commit SHA; a tag can be moved under you")
        for spec in unpinned_npm_installs(text):
            fail(f"{path}: installs {spec} — pin it to an exact version; this job holds a secret")
        for name in unresolved_npm_version_vars(text):
            fail(f"{path}: installs a package pinned through ${name}, which no env sets to an exact version")


# --- 22. tree code and a secret never share a runner ---------------------------
# The audit workflow once ran the audited head's own Python in the same job that
# later held ANTHROPIC_API_KEY, so a pull request could execute code on a runner
# with a credential on it and the whole workspace to rewrite in between. The fix
# is a job split; this is what keeps it split.
#
# GITHUB_TOKEN is deliberately not counted: every workflow has one whether it
# names it or not, so treating it as a secret to isolate would flag every job
# that can post a comment while protecting nothing.
JOB_KEY_RE = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$")
SECRET_REF_RE = re.compile(r"\$\{\{\s*secrets\.([A-Za-z_][A-Za-z0-9_]*)")
# `python tools/x.py` runs a file from the checkout. `python "$LAUNCHER"` runs
# whatever the job put at that path — by convention here, a trusted copy — so the
# variable form is not a checkout path and is not counted.
TREE_SCRIPT_RE = re.compile(r"python3?\s+(?![\"']?\$)([A-Za-z0-9_./-]+\.py)")


def workflow_jobs(text: str) -> dict[str, str]:
    """{job name: the lines belonging to it}, split on the two-space keys under `jobs:`."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip() == "jobs:")
    except StopIteration:
        return {}
    jobs: dict[str, list[str]] = {}
    name: str | None = None
    for line in lines[start + 1:]:
        if line.strip() and not line.startswith(" "):
            break                     # a new top-level key ends the jobs block
        match = JOB_KEY_RE.match(line)
        if match:
            name = match.group(1)
            jobs[name] = []
            continue
        if name is not None:
            jobs[name].append(line)
    return {k: "\n".join(v) for k, v in jobs.items()}


def secret_jobs_running_tree_code(text: str) -> list[tuple[str, list[str], list[str]]]:
    """(job, secrets it exposes, scripts it runs from the checkout) for each job doing both."""
    problems = []
    for name, body in workflow_jobs(text).items():
        secrets = sorted({s for s in SECRET_REF_RE.findall(body) if s != "GITHUB_TOKEN"})
        if not secrets:
            continue
        scripts = sorted(set(TREE_SCRIPT_RE.findall(body)))
        if scripts:
            problems.append((name, secrets, scripts))
    return problems


# --- 23. audit tools hand out an allow-list, never the operator's environment ---
# Findings S-004 and S-005: the red-team harness built its probe environment with
# dict(os.environ, HOME=...) minus three CCGG_* names, and the deterministic gate
# passed no env at all, so shell code and Python out of the audited tree ran with
# ANTHROPIC_API_KEY, GITHUB_TOKEN and every cloud credential in scope. The rule
# now has one home (tools/audit_env.py) and this keeps the tools pointed at it.
#
# What this catches is the shape both findings had: a child environment derived
# from the parent's. It does not catch a subprocess call that passes no env= at
# all — that one is the unit tests' job (tools/test_audit_env.py checks the
# environment each harness actually builds), because telling a command that runs
# tree code from one that runs git apart is not something a regex should try.
INHERITED_ENV_RE = re.compile(r"\bdict\(\s*os\.environ|\benv\s*=\s*os\.environ\b")


def blank_python_literals(text: str) -> str:
    """The source with string and comment spans blanked, positions preserved.

    tools/audit_env.py documents the defect this check looks for, in prose, and a
    docstring quoting `dict(os.environ, ...)` is not a use of it. Blanking rather
    than deleting keeps line numbers pointing at the real line.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    rows = [list(line) for line in text.splitlines(keepends=True)]
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text            # unparsable is the syntax checker's problem, not this one
    for token in tokens:
        if token.type not in (tokenize.STRING, tokenize.COMMENT):
            continue
        (start_row, start_col), (end_row, end_col) = token.start, token.end
        for row in range(start_row, end_row + 1):
            if row > len(rows):
                break
            line = rows[row - 1]
            first = start_col if row == start_row else 0
            last = end_col if row == end_row else len(line)
            for i in range(first, min(last, len(line))):
                if line[i] != "\n":
                    line[i] = " "
    return "".join("".join(row) for row in rows)


# --- 24. the gate has an automatic runner ------------------------------------
# Deleting .github/workflows/validate.yml was a defect the gate could not see:
# the only check for it lived in tools/audit_facts.py, which no CI step invokes,
# so a commit removing the workflow left every check green. `audit.yml` is not a
# substitute — it is label-gated and hand-started — so the property is not "a
# workflow file exists" but "something runs the validator without being asked".
#
# Installed projects are exempt. They receive tools/validate.py and decide their
# own CI; install.sh is the file that only the guide repository has.
GATE_COMMAND_RE = re.compile(r"tools/validate\.py")
AUTOMATIC_TRIGGER_RE = re.compile(r"^\s{2,}(push|pull_request):", re.M)


# The validator is not the whole gate. The detectors that exist only in
# audit_facts.py, and the unit tests that hold every check honest, ran on a
# manual trigger or not at all (findings T-008 and T-009).
# The command form, not the path: the step guards itself with
# `if [ -f tools/audit_facts.py ]`, and a workflow that only mentions the file
# runs nothing. (GATE_COMMAND_RE stays a bare path — tightening it would fail
# installed projects whose workflow spells the invocation some other way.)
FACTS_COMMAND_RE = re.compile(r"python[0-9.]*\s+tools/audit_facts\.py")
TESTS_COMMAND_RE = re.compile(r"unittest\s+discover[^\n]*\btools\b")
GATE_RUNNERS = (
    (GATE_COMMAND_RE, "tools/validate.py", "the gate would run only when someone remembers"),
    (FACTS_COMMAND_RE, "tools/audit_facts.py",
     "its hook-stdout, command-resolution and network-exec checks exist nowhere else"),
    (TESTS_COMMAND_RE, "the unit tests",
     "every check in this repository would be unproven on the commit that broke it"),
)


# A workflow that reads the event or a label decides for itself whether to do any
# work. audit.yml triggers on pull_request and then gates every job on an `audit`
# label — dependable for what it is, and not a runner anything else can rely on.
EVENT_GATED_RE = re.compile(r"github\.event_name|github\.event\.pull_request\.labels")


def runs_automatically(text: str, command: re.Pattern) -> bool:
    """True when this workflow runs `command` on a trigger nobody has to remember.

    Three things have to hold: the command is invoked, the workflow's own `on:`
    block names an automatic trigger — `pull_request` inside a job's `if:` is a
    condition, not a reason it started — and no job reads the event or a label to
    decide whether to run at all.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not command.search(text):
        return False
    if EVENT_GATED_RE.search(text):
        return False
    header = text.split("\njobs:", 1)[0]
    return bool(AUTOMATIC_TRIGGER_RE.search(header))


def runs_gate_automatically(text: str) -> bool:
    """True when this workflow runs the validator on a trigger nobody has to remember."""
    return runs_automatically(text, GATE_COMMAND_RE)


def check_gate_has_a_runner() -> None:
    if not tracked("install.sh"):
        return                      # an installed project chooses its own CI
    texts = []
    for path in tracked(".github/workflows/*.yml") + tracked(".github/workflows/*.yaml"):
        with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as fh:
            texts.append(fh.read())
    for command, name, why in GATE_RUNNERS:
        if not any(runs_automatically(text, command) for text in texts):
            fail(f"no workflow runs {name} on push or pull_request — {why}")


def inherited_env_uses(text: str) -> list[int]:
    """Line numbers where a child environment is built out of os.environ."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    code = blank_python_literals(text)
    return [no for no, line in enumerate(code.splitlines(), 1) if INHERITED_ENV_RE.search(line)]


def check_audit_env_allow_list() -> None:
    for path in tracked("tools/audit_*.py"):
        with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for no in inherited_env_uses(text):
            fail(f"{path}:{no}: builds a child environment from os.environ — code from the audited "
                 f"tree must get audit_env.sandbox_env(), not the operator's credentials")


def check_workflow_secret_isolation() -> None:
    for path in tracked(".github/workflows/*.yml") + tracked(".github/workflows/*.yaml"):
        with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for job, secrets, scripts in secret_jobs_running_tree_code(text):
            fail(
                f"{path}: job '{job}' exposes {', '.join(secrets)} and also runs "
                f"{', '.join(scripts)} from the checkout — split the job so code from the "
                f"audited tree never shares a runner with a credential"
            )


# --- 22. a headless audit can still invoke its specialists --------------------
def check_headless_can_spawn() -> None:
    """The briefs are worth nothing if the orchestrator has no tool to call them.

    A run once loaded seven specialists and spawned none: `--bare` caps the
    built-in set to Bash, Edit and Read, so the Task tool was never there. The
    two halves of that mistake are checked here — the mode, and the grant the
    tool set is derived from. Optional, like the other audit checks.
    """
    if not tracked("tools/audit_headless.py"):
        return
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import audit_headless
    except ImportError:
        return
    with open(os.path.join(ROOT, "tools/audit_headless.py"), encoding="utf-8", errors="replace") as fh:
        source = fh.read()
    if '"--bare"' in source or "'--bare'" in source:
        fail("tools/audit_headless.py: --bare caps the built-in tools to Bash, Edit and Read — "
             "the run would load the specialists and have no Task tool to invoke them")
    skill = os.path.join(ROOT, audit_headless.SKILL_PATH)
    if not os.path.exists(skill):
        return
    with open(skill, encoding="utf-8", errors="replace") as fh:
        skill_text = fh.read()
    try:
        exposed = audit_headless.tool_names(audit_headless.skill_grants(skill_text))
    except audit_headless.HeadlessError as exc:
        fail(f"{audit_headless.SKILL_PATH}: {exc}")
        return
    if "Task" not in exposed:
        fail(f"{audit_headless.SKILL_PATH}: allowed-tools grants no Agent, so a headless run "
             f"gets no Task tool and every specialist brief is dead weight (has: {', '.join(exposed)})")


def check_features() -> None:
    """Feature definitions, when a project has any, meet the house schema.

    Delegates to tools/feature_lint.py so the rules have one home. Both the
    directory and the linter are optional: a project that adopted the validator
    without them is not broken by this check, it simply has nothing to lint.
    """
    paths = tracked("features/*.md")
    paths = [p for p in paths if os.path.basename(p).lower() != "readme.md"]
    if not paths:
        return
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import feature_lint
    except ImportError:
        return  # linter not installed in this project — nothing to enforce
    for path in paths:
        text = open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read()
        status = feature_lint.parse_frontmatter(text)[0].get("status", "").lower()
        for finding in feature_lint.lint_text(text, path):
            if feature_lint.counts_as_failure(finding, status, strict=False):
                fail(f"{path}:{finding.line}: {finding.message}")



# --- the validator's check on itself -----------------------------------------
# This one is not numbered and is not called from main(), deliberately. A check
# inside main() cannot catch a main() that returns before calling it, and that
# was a live blind spot: tools/probes.txt recorded "validator main forced to
# return 0" as a defect the gate could not see, because the neutered validator
# is the thing asked whether anything is wrong.
#
# Prepending `return 0` to main does not remove the checks — it strands them, so
# the property worth testing is not "are the checks wired up" (they still parse
# as called) but "can they be reached". Unreachable code in the gate is a real
# defect in its own right, which is why this is a rule rather than a trap set
# for one sed command.
#
# It closes blunt neutering, not a determined one: anybody who can edit main()
# can edit this too. The control that does not share that weakness is CI running
# the base branch's validator against the head, which is a workflow's job.
def unreachable_after_return(source: str) -> list[int]:
    """Line numbers of statements that follow an unconditional return or raise."""
    if not isinstance(source, str):
        raise TypeError("source must be a string")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []               # a syntax error is not this check's to report
    dead: list[int] = []
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if not isinstance(block, list):
                continue
            for i, statement in enumerate(block):
                if isinstance(statement, (ast.Return, ast.Raise)) and i + 1 < len(block):
                    dead.append(block[i + 1].lineno)
    return sorted(set(dead))


# The scripts that make up the gate. `main forced to return 0` was caught in the
# validator's own source and nowhere else, so the same mutation one file across —
# in the harness that measures the gate — passed (finding T-006).
GATE_SOURCE_GLOBS = ("tools/validate.py", "tools/feature_lint.py", "tools/catalog.py",
                     "tools/audit_*.py")


def gate_sources() -> list[str]:
    """The tracked scripts self_check reads, sorted; tests excluded."""
    found: set[str] = set()
    for pattern in GATE_SOURCE_GLOBS:
        found.update(p for p in tracked(pattern)
                     if p.endswith(".py") and not os.path.basename(p).startswith("test_"))
    return sorted(found)


def source_problems(path: str) -> list[str]:
    """Unreachable code in one gate script, as messages naming the file."""
    label = os.path.relpath(path, ROOT) if os.path.isabs(path) else path
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            source = fh.read()
    except OSError as exc:
        return [f"{label}: cannot be read: {exc}"]
    return [f"{label}:{no}: unreachable code — a check that cannot be reached is not a check"
            for no in unreachable_after_return(source)]


def self_check(path: str | None = None) -> list[str]:
    """What the gate can tell about itself before main() gets a say.

    With no argument it reads every script in gate_sources(); with one it reads
    that file alone, which is how a test hands it a deliberately broken copy.
    """
    if path is not None:
        return source_problems(path)
    problems: list[str] = []
    for rel in gate_sources():
        problems += source_problems(os.path.join(ROOT, rel))
    return problems


# --- 25. probe contract -------------------------------------------------------
PROBE_CONTRACTS = (("tools/audit_probes.py", "tools/probes.txt"),
                   ("tools/audit_redteam.py", "tools/redteam_probes.txt"))


def probe_lines(text: str) -> list[str]:
    """The probe-carrying lines of a probes file: non-blank and not a comment.

    Deliberately not the harness's parser. Importing a module out of the tree to
    validate the tree would execute it, and the field-level contract is the
    harness's to enforce — both harnesses now exit 1 on a malformed line. What
    belongs here is the question neither of them could answer about itself: is
    there anything to measure at all.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return [line.strip() for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")]


def check_probe_contract() -> None:
    """A repository that ships a probe harness must ship probes for it to run.

    Both harnesses used to treat a missing or empty probes file as "nothing to
    measure" and exit 0, so the whole measured catch rate could be emptied with
    every gate still green (finding T-001).
    """
    present = set(tracked("tools/*"))
    for harness, data in PROBE_CONTRACTS:
        if harness not in present:
            continue
        if data not in present:
            fail(f"{harness} is tracked but {data} is not — the harness would measure nothing")
            continue
        with open(os.path.join(ROOT, data), encoding="utf-8", errors="replace") as fh:
            lines = probe_lines(fh.read())
        if not lines:
            fail(f"{data}: no probes — the contract {harness} measures is empty")


# --- 26. reference thresholds -------------------------------------------------
THRESHOLD_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:percent|%)")
MEASURED_RE = re.compile(r"measured by `[^`]+`|unmeasured")


def paragraphs(text: str) -> list[tuple[int, str]]:
    """Blank-line separated blocks, each with the line number it starts on."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    blocks, start, buf = [], 1, []
    for no, line in enumerate(text.splitlines(), 1):
        if line.strip():
            if not buf:
                start = no
            buf.append(line)
        elif buf:
            blocks.append((start, "\n".join(buf)))
            buf = []
    if buf:
        blocks.append((start, "\n".join(buf)))
    return blocks


def check_reference_thresholds() -> None:
    """A number the rules make binding has to name what measures it.

    The gate reference asked for 90 percent coverage on changed lines and AGENTS.md
    made it binding, while no coverage runner, configuration or threshold existed
    anywhere in the repository (finding P-003). A threshold states its measuring
    command in the same paragraph, or says in so many words that it is unmeasured.
    """
    for path in tracked(".claude/references/*.md"):
        with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for start, block in paragraphs(text):
            if THRESHOLD_RE.search(block) and not MEASURED_RE.search(block):
                fail(f"{path}:{start}: states a numeric threshold without naming what measures it "
                     f"— add \"measured by `<command>`\", or say it is unmeasured")


# --- 27. hook stdout, docs vs vocabulary --------------------------------------
# The guide's hooks chapter said stdout is ignored "for events like SessionStart",
# while tools/audit_vocab.json, tools/audit_facts.py, the red-team agent brief and
# this repository's own SessionStart hook all treat that stdout as text the model
# reads (finding C-CONFLICT-001). The vocabulary is the one source of truth; this
# check makes the prose answer to it.
STDOUT_DENIED_RE = re.compile(
    r"\bstdout\b[^.]{0,40}\b(?:is|are)\s+(?:ignored|discarded|dropped|unused|"
    r"not\s+read|thrown\s+away)", re.I)


def hook_stdout_reaches_model() -> list[str]:
    """The events whose stdout the product adds to the model's context."""
    path = os.path.join(ROOT, VOCAB_PATH)
    try:
        with open(path, encoding="utf-8") as fh:
            return list(json.load(fh).get("hook_stdout_reaches_model") or [])
    except (OSError, ValueError):
        return []


def sentences(text: str) -> list[str]:
    """Sentences, with wrapped lines joined — a claim split across two lines is one claim."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    flat = re.sub(r"\s+", " ", text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", flat) if s.strip()]


def hook_stdout_conflicts(path: str, text: str) -> list[str]:
    """Sentences that deny stdout reaches the model for an event where it does.

    Per sentence, not per file: a page may describe both kinds of event, and
    saying "every other passive event's stdout is ignored" is not a conflict.
    """
    reaching = hook_stdout_reaches_model()
    problems = []
    for sentence in sentences(text):
        if not STDOUT_DENIED_RE.search(sentence):
            continue
        named = [e for e in reaching if e in sentence]
        if named:
            problems.append(
                f"{path}: says hook stdout is ignored in a sentence naming "
                f"{', '.join(named)} — tools/audit_vocab.json lists it under "
                f"hook_stdout_reaches_model, and this repository's SessionStart hook "
                f"relies on that: \"{sentence[:110]}\"")
    return problems


def check_hook_stdout_docs() -> None:
    for path in tracked("docs/*.md"):
        with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for problem in hook_stdout_conflicts(path, text):
            fail(problem)


# --- 28. the verifier's guard canary ------------------------------------------
# The guard hook on the verifier was assumed to fire until a run measured it and
# found it did not (finding R-008). What replaced the assumption is a canary the
# verifier runs first and the report records. Delete it from the brief and every
# later run silently stops measuring, so the gate holds the wiring in place.
# Kept identical to tools/audit_report.py's GUARD_CANARY; a test compares them.
GUARD_CANARY = "uname -a"
GUARD_CANARY_MARKER = "GUARD-CANARY"
VERIFIER_BRIEF = os.path.join(".claude", "agents", "audit-verifier.md")


def guard_canary_problems(path: str, text: str) -> list[str]:
    """The verifier brief must tell the verifier to run the canary and report it."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    problems = []
    if GUARD_CANARY_MARKER not in text:
        problems.append(f"{path}: no {GUARD_CANARY_MARKER} line — the run would stop measuring "
                        "whether the verifier's guard fires, and nothing would say so")
    elif GUARD_CANARY not in text:
        problems.append(f"{path}: names a canary but not `{GUARD_CANARY}`, the command "
                        "tools/audit_report.py counts as proof the guard fired")
    return problems


def check_guard_canary() -> None:
    if VERIFIER_BRIEF not in tracked(VERIFIER_BRIEF):
        return                      # a project without the audit verifier
    with open(os.path.join(ROOT, VERIFIER_BRIEF), encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    for problem in guard_canary_problems(VERIFIER_BRIEF, text):
        fail(problem)


# --- 28b. the verifier guard is registered where hooks fire -------------------
# The frontmatter registration was measured not firing from inside a live
# interactive verifier on two separate days (findings R-008, H-001, S-003).
# settings.json hooks are the ones that demonstrably fire here, so the guard is
# registered there too, scoped to the verifier by name: a registration without
# `--only-agent audit-verifier` would put every agent's Bash behind the
# verifier's allow-list, and one on the wrong event or matcher never runs.
GUARD_AGENT = "audit-verifier"
GUARD_SCOPE_FLAG = f"--only-agent {GUARD_AGENT}"


def guard_registration_problems(settings: dict) -> list[str]:
    """Why settings.json's registration of the verifier guard would not hold."""
    hooks = settings.get("hooks") if isinstance(settings, dict) else None
    groups = hooks.get("PreToolUse") if isinstance(hooks, dict) else None
    found = []
    for group in groups if isinstance(groups, list) else []:
        if not isinstance(group, dict):
            continue
        for hook in group.get("hooks") or []:
            command = str(hook.get("command", "")) if isinstance(hook, dict) else ""
            if GUARD_PATH in command:
                found.append((str(group.get("matcher", "")), command))
    if not found:
        return [f".claude/settings.json: {GUARD_PATH} is not registered under hooks.PreToolUse — "
                f"the frontmatter registration alone was measured not firing for the verifier (H-001)"]
    problems = []
    for matcher, command in found:
        if matcher != "Bash":
            problems.append(f".claude/settings.json: the verifier guard's PreToolUse matcher is "
                            f"{matcher!r}, not 'Bash' — it never sees the verifier's commands")
        if GUARD_SCOPE_FLAG not in command:
            problems.append(f".claude/settings.json: the verifier guard is registered without "
                            f"'{GUARD_SCOPE_FLAG}' — every agent's Bash, the main session's included, "
                            f"would be held to the verifier's allow-list")
    return problems


def check_guard_settings_registration() -> None:
    if VERIFIER_BRIEF not in tracked(VERIFIER_BRIEF) or not tracked(GUARD_PATH):
        return                      # a project without the audit verifier
    path = os.path.join(ROOT, ".claude", "settings.json")
    if not os.path.exists(path):
        fail(f".claude/settings.json: missing, so {GUARD_PATH} has no registration that fires")
        return
    try:
        settings = json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError:
        return                      # check 6 reports it
    for problem in guard_registration_problems(settings):
        fail(problem)


# --- 29. the verifier guard's allow-lists match the tree ----------------------
# The guard names the scripts it will run. Before finding S-004 it matched a
# prefix, so a branch adding tools/test_anything.py was allowed by construction;
# and `-m unittest discover` imports whatever is in the directory whatever the
# list says. Holding the list equal to the tree is what makes adding a script to
# the gate a visible, named change to the guard rather than a silent one.
GUARD_PATH = os.path.join(".claude", "hooks", "audit-verifier-guard.sh")
GUARD_HEREDOC_RE = re.compile(r"<<'PY'[^\n]*\n(.*?)\nPY\n", re.S)
GUARD_LIST_NAMES = ("PY_SCRIPTS", "SH_SCRIPTS")


def guard_allow_lists(path: str | None = None) -> dict:
    """The guard's own script allow-lists, read from its embedded python."""
    full = path or os.path.join(ROOT, GUARD_PATH)
    with open(full, encoding="utf-8", errors="replace") as fh:
        match = GUARD_HEREDOC_RE.search(fh.read())
    if not match:
        return {}
    try:
        tree = ast.parse(match.group(1))
    except SyntaxError:
        return {}
    found = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id in GUARD_LIST_NAMES:
            value = node.value
            # The lists are written `frozenset((...))` — a call, not a literal.
            if (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
                    and value.func.id in ("frozenset", "set", "tuple") and len(value.args) == 1):
                value = value.args[0]
            try:
                found[target.id] = set(ast.literal_eval(value))
            except (ValueError, TypeError):
                continue
    return found


def guard_allow_list_problems(lists: dict, py_tree: set, sh_tree: set,
                              authored_here: bool = True) -> list[str]:
    """Differences between what the guard names and what the repository ships.

    The two directions are not symmetrical. A script in the tree the guard does
    not name is a finding everywhere: nobody decided to allow it. A name the guard
    keeps with no file behind it is a finding only where the list is authored —
    an installed project gets the guard and validate.py but neither tools/test_*.py
    nor install.sh/update.sh, and a list trimmed to each install would stop being
    one list.
    """
    problems = []
    for name, tree in (("PY_SCRIPTS", py_tree), ("SH_SCRIPTS", sh_tree)):
        listed = set(lists.get(name) or ())
        for missing in sorted(tree - listed):
            problems.append(f"{GUARD_PATH}: {missing} is in the tree but not in {name} — "
                            f"the verifier cannot run it, and a script the guard does not "
                            f"name is a script nobody decided to allow")
        if not authored_here:
            continue
        for stale in sorted(listed - tree):
            problems.append(f"{GUARD_PATH}: {name} allows {stale}, which the repository does "
                            f"not ship — a name kept after its file went is a name a branch "
                            f"can reintroduce")
    return problems


def check_guard_allow_lists() -> None:
    if not tracked(GUARD_PATH):
        return                      # a project without the audit verifier
    py_tree = {os.path.basename(p) for p in tracked("tools/*.py")
               if os.path.basename(p) != "__init__.py"}
    sh_tree = set(tracked(".claude/hooks/*.sh")) | set(tracked("*.sh"))
    for problem in guard_allow_list_problems(guard_allow_lists(), py_tree, sh_tree,
                                             authored_here=bool(tracked("install.sh"))):
        fail(problem)


AUDIT_WORKFLOW_PATH = ".github/workflows/audit.yml"
HEADLESS_PATH = "tools/audit_headless.py"
# The one grant shape that names a path the run may execute without a prompt.
PINNED_GRANT_SCRIPT_RE = re.compile(r"Bash\(python3 (tools/[A-Za-z0-9_]+\.py) \*\)")
RESCUE_FETCH_RE = re.compile(r'^\s*fetch "([^"]+)"', re.M)
LOCAL_IMPORT_RE = re.compile(r"^import ([A-Za-z_][A-Za-z0-9_]*)", re.M)


def pinned_grant_scripts(text: str) -> list[str]:
    """The repository paths PINNED_GRANTS lets a headless run execute unprompted.

    Read with ast, never by importing: validating a module by running it is how the
    audited tree would get its say back.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not (isinstance(target, ast.Name) and target.id == "PINNED_GRANTS"):
            continue
        value = node.value
        if (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
                and value.func.id in ("frozenset", "set", "tuple") and len(value.args) == 1):
            value = value.args[0]
        try:
            grants = ast.literal_eval(value)
        except (ValueError, TypeError):
            continue
        for grant in grants:
            match = PINNED_GRANT_SCRIPT_RE.fullmatch(str(grant).strip())
            if match and match.group(1) not in found:
                found.append(match.group(1))
    return found


def local_imports(path: str) -> set[str]:
    """Sibling modules under tools/ that `path` imports, one level deep."""
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        return set()
    with open(full, encoding="utf-8", errors="replace") as fh:
        names = set(LOCAL_IMPORT_RE.findall(fh.read()))
    return {f"tools/{n}.py" for n in names if os.path.isfile(os.path.join(ROOT, "tools", n + ".py"))}


def rescued_paths(text: str, job: str | None = None) -> set[str]:
    """The paths a trusted-copies step takes from the base ref.

    With `job`, only that job's own fetch lines count: the deterministic job now
    rescues its producers too, and a path rescued there is still the head's copy
    in the job that holds the key (finding R-002).
    """
    if job is not None:
        text = workflow_jobs(text).get(job, "")
    return set(RESCUE_FETCH_RE.findall(text))


def pinned_grant_rescue_problems(scripts: list[str], rescued: set[str]) -> list[str]:
    """Grant targets — and what they import — that the base-ref rescue leaves behind.

    A pinned grant is a pre-approval to run a path, and the headless run's cwd is the
    audited checkout. A target the workflow does not rescue is therefore the head's
    own code, executing unprompted in the job that holds the API key (finding S-007).
    """
    problems = []
    for script in scripts:
        needed = [script] + sorted(local_imports(script))
        for path in needed:
            if path in rescued:
                continue
            why = ("a pinned grant pre-approves it" if path == script
                   else f"{script} imports it and a pinned grant pre-approves that")
            problems.append(f"{AUDIT_WORKFLOW_PATH}: {path} is not in the base-ref rescue list, and "
                            f"{why} — the audited head would supply the code that runs")
    return problems


def check_pinned_grants_are_rescued() -> None:
    if not (tracked(HEADLESS_PATH) and tracked(AUDIT_WORKFLOW_PATH)):
        return                      # a project without the headless audit or its workflow
    with open(os.path.join(ROOT, HEADLESS_PATH), encoding="utf-8", errors="replace") as fh:
        scripts = pinned_grant_scripts(fh.read())
    if not scripts:
        fail(f"{HEADLESS_PATH}: PINNED_GRANTS names no script to run; either it moved or it "
             f"stopped being readable, and this check silently stopped checking")
        return
    with open(os.path.join(ROOT, AUDIT_WORKFLOW_PATH), encoding="utf-8", errors="replace") as fh:
        rescued = rescued_paths(fh.read(), job="model")
    for problem in pinned_grant_rescue_problems(scripts, rescued):
        fail(problem)


# The deterministic job is where the audited head's code is allowed to run — its
# gate, its probe mutations — but the three producers whose JSON the specialists
# read as measurement are not the head's to author. They ran from the checkout,
# so a pull request chose every fact, detail and channel string the model stage
# started from (finding R-002, 2026-09-18). The job now rescues them, what they
# import, and the data they read from beside themselves, and invokes only those.
DETERMINISTIC_JOB = "deterministic"
DETERMINISTIC_PRODUCERS = ("tools/audit_facts.py", "tools/audit_probes.py", "tools/audit_redteam.py")
# A data file a script opens next to itself: os.path.join(os.path.dirname(os.path.abspath(__file__)), "name")
LOCAL_DATA_RE = re.compile(r'os\.path\.join\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\),\s*"([^"/]+)"\)')
HEAD_PRODUCER_RUN_RE = re.compile(r"python3?\s+(tools/audit_(?:facts|probes|redteam)\.py)\b")
TRUSTED_PRODUCER_RUN_RE = re.compile(r'python3?\s+"\$[A-Z_]+/(tools/audit_(?:facts|probes|redteam)\.py)"')


def local_data_files(path: str) -> set[str]:
    """Sibling files under tools/ that `path` opens by its own location."""
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        return set()
    with open(full, encoding="utf-8", errors="replace") as fh:
        names = set(LOCAL_DATA_RE.findall(fh.read()))
    return {f"tools/{n}" for n in names if os.path.isfile(os.path.join(ROOT, "tools", n))}


def producer_rescue_problems(job_body: str) -> list[str]:
    """What the deterministic job still takes from the head that the specialists then read."""
    if not isinstance(job_body, str):
        raise TypeError("job_body must be a string")
    problems = []
    rescued = set(RESCUE_FETCH_RE.findall(job_body))
    for producer in DETERMINISTIC_PRODUCERS:
        needed = [producer] + sorted(local_imports(producer)) + sorted(local_data_files(producer))
        for path in needed:
            if path in rescued:
                continue
            why = ("the specialists read its output as measurement" if path == producer
                   else f"{producer} loads it from beside itself")
            problems.append(f"{AUDIT_WORKFLOW_PATH}: {path} is not in the {DETERMINISTIC_JOB} job's rescue list, "
                            f"and {why} — the audited head would supply it")
    for head_run in sorted(set(HEAD_PRODUCER_RUN_RE.findall(job_body))):
        problems.append(f"{AUDIT_WORKFLOW_PATH}: the {DETERMINISTIC_JOB} job runs {head_run} from the checkout — "
                        f"run the trusted copy, the head's version authors what the specialists read")
    trusted_runs = set(TRUSTED_PRODUCER_RUN_RE.findall(job_body))
    for producer in DETERMINISTIC_PRODUCERS:
        if producer not in trusted_runs:
            problems.append(f"{AUDIT_WORKFLOW_PATH}: the {DETERMINISTIC_JOB} job never runs the trusted copy of "
                            f"{producer} — its output is what the specialists start from")
    return problems


def check_deterministic_producers_are_rescued() -> None:
    if not (tracked(HEADLESS_PATH) and tracked(AUDIT_WORKFLOW_PATH)):
        return                      # a project without the headless audit or its workflow
    with open(os.path.join(ROOT, AUDIT_WORKFLOW_PATH), encoding="utf-8", errors="replace") as fh:
        jobs = workflow_jobs(fh.read())
    if DETERMINISTIC_JOB not in jobs:
        fail(f"{AUDIT_WORKFLOW_PATH}: no `{DETERMINISTIC_JOB}` job — it moved, and this check silently "
             f"stopped checking whose producers author the artifact")
        return
    for problem in producer_rescue_problems(jobs[DETERMINISTIC_JOB]):
        fail(problem)


# --- 31. decision record names ------------------------------------------------
# session-start.sh prints the name of every open decision record straight into
# the prompt. Its old allow-list forbade spaces, which read as safe, but hyphens
# join words as well as spaces do (finding R-001). The hook now requires the slug
# the /decide skill produces; this keeps the tree to names the hook will print,
# so a record does not go silently unlisted for being misnamed.
DECISION_SLUG_RE = re.compile(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(-[a-z0-9]+){0,6}\.md\Z")
DECISION_EXEMPT = ("README.md",)


def decision_name_problems(names: list[str]) -> list[str]:
    problems = []
    for name in names:
        base = os.path.basename(name)
        if base in DECISION_EXEMPT or DECISION_SLUG_RE.match(base):
            continue
        problems.append(f"decisions/{base}: not a date-prefixed slug (YYYY-MM-DD-words.md, at most 7 words) — "
                        f"session-start.sh counts a record it cannot name, so this one would never be listed")
    return problems


def check_decision_names() -> None:
    for problem in decision_name_problems(tracked("decisions/*.md")):
        fail(problem)


# --- 32. the audit workflow's trust anchor ------------------------------------
# The trusted set — guard, skill, agent briefs, launcher, grant targets — is read
# from pull_request.base.sha, and a pull request chooses its own base. Pinning
# base_ref to the default branch is what makes "the base branch the maintainers
# own" true rather than aspirational (finding S-008).
BASE_REF_PIN = "github.base_ref == github.event.repository.default_branch"
HEAD_REPO_PIN = "github.event.pull_request.head.repo.full_name == github.repository"


def job_condition(text: str, job: str) -> str:
    """The job-level `if:` of a named job, flattened to one line.

    Job-level means the four-space property indent, before `steps:`. The first
    version took the first `if:` at any depth, so a step's condition stood in
    for a job that had none (review of #75).
    """
    lines = text.splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.rstrip() == f"  {job}:")
    except StopIteration:
        return ""
    collecting = False
    block = False
    parts = []
    for ln in lines[start + 1:]:
        if ln.startswith("  ") and not ln.startswith("   ") and ln.rstrip().endswith(":"):
            break                       # the next job
        if ln.startswith("    steps:"):
            break                       # anything below is a step's, not the job's
        if ln.startswith("    if:"):
            collecting = True
            value = ln[len("    if:"):].strip()
            block = value in (">", ">-", "|", "|-")
            if not block:
                # A plain scalar's ` #` starts a YAML comment GitHub never evaluates.
                parts.append(re.split(r"\s#", value, 1)[0].strip())
                break
            continue
        if collecting and block:
            if not ln.strip() or re.match(r"^    [a-z-]+:", ln):
                break
            parts.append(ln.strip())
    return " ".join(p for p in parts if p)


def normalized_condition(condition: str) -> str:
    return re.sub(r"\s+", " ", condition).strip()


# The one condition the deterministic job may carry, whitespace-normalized. An
# equality test, not a substring test: `pin in condition` was satisfied by a
# pin inside a comment, OR-ed in, or negated (review of #75). Any rewrite fails
# and is reviewed, the way AUDIT_SKILL_GRANTS pins the skill's grants.
AUDIT_JOB_CONDITION = normalized_condition(
    "github.event_name == 'workflow_dispatch' || "
    "(contains(github.event.pull_request.labels.*.name, 'audit') && "
    f"{HEAD_REPO_PIN} && {BASE_REF_PIN})")


def audit_workflow_problems(text: str) -> list[str]:
    condition = job_condition(text, "deterministic")
    if not condition:
        return [f"{AUDIT_WORKFLOW_PATH}: the deterministic job has no job-level `if:` — every push "
                f"would start a run that reads a pull request's chosen base as its trusted source"]
    if normalized_condition(condition) != AUDIT_JOB_CONDITION:
        return [f"{AUDIT_WORKFLOW_PATH}: the deterministic job's condition is not the pinned one — "
                f"got `{normalized_condition(condition)[:120]}`; it must be exactly "
                f"`{AUDIT_JOB_CONDITION}` (a fork pull request, or one choosing its own base, "
                f"would otherwise reach the job that reads the trusted set)"]
    return []


def check_audit_workflow_trust_anchor() -> None:
    if not tracked(AUDIT_WORKFLOW_PATH):
        return
    with open(os.path.join(ROOT, AUDIT_WORKFLOW_PATH), encoding="utf-8", errors="replace") as fh:
        for problem in audit_workflow_problems(fh.read()):
            fail(problem)


# --- 33. hook headers promise only what their event delivers --------------------
# session-end.sh's header said it "reminds the AI to flush memory". SessionEnd
# stdout goes to the debug log and the script printed nothing anyway, so the
# reminder existed only in the comment (finding H-001). A header is what the
# next reader believes; on an event whose stdout never reaches the model it may
# not claim to tell the model anything.
HOOK_CLAIM_RE = re.compile(
    r"\b(remind(?:s|ed|ing)?|tell(?:s|ing)?|instruct(?:s|ed|ing)?|prompt(?:s|ed|ing)?|"
    r"inform(?:s|ed|ing)?|nudg(?:es|ed|ing))\s+(?:the\s+)?(AI|model|agent|assistant|Claude)\b", re.I)


def hook_header(text: str) -> str:
    """The leading comment block of a shell script, shebang excluded."""
    lines = []
    for line in text.splitlines():
        if line.startswith("#!"):
            continue
        if line.startswith("#"):
            lines.append(line.lstrip("#").strip())
        elif line.strip():
            break
    return " ".join(lines)


def registered_hook_events(settings: dict) -> dict[str, list[str]]:
    """{script name: [events]} for every .claude/hooks/*.sh settings.json registers."""
    out: dict[str, list[str]] = {}
    hooks = settings.get("hooks") if isinstance(settings, dict) else None
    if not isinstance(hooks, dict):
        return out
    for event, matchers in hooks.items():
        for matcher in matchers if isinstance(matchers, list) else []:
            for hook in (matcher.get("hooks") if isinstance(matcher, dict) else []) or []:
                command = hook.get("command", "") if isinstance(hook, dict) else ""
                for name in re.findall(r"\.claude/hooks/([A-Za-z0-9_.-]+\.sh)", str(command)):
                    out.setdefault(name, []).append(event)
    return out


def hook_header_problems(name: str, events: list[str], text: str, reaching: list[str]) -> list[str]:
    if any(e in reaching for e in events):
        return []
    claim = HOOK_CLAIM_RE.search(hook_header(text))
    if not claim:
        return []
    return [f".claude/hooks/{name}: its header says it {claim.group(0)!r}, but it runs on "
            f"{', '.join(events)}, whose stdout never reaches the model — say what the script "
            f"does, or move the message to a SessionStart hook"]


def check_hook_headers() -> None:
    path = os.path.join(ROOT, ".claude", "settings.json")
    if not os.path.exists(path):
        return
    try:
        settings = json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError:
        return                      # check 6 reports it
    reaching = hook_stdout_reaches_model()
    for name, events in registered_hook_events(settings).items():
        script = os.path.join(ROOT, ".claude", "hooks", name)
        if not os.path.isfile(script):
            continue                # check 11 reports it
        with open(script, encoding="utf-8", errors="replace") as fh:
            for problem in hook_header_problems(name, events, fh.read(), reaching):
                fail(problem)


# --- 34. the currency rule has one home -----------------------------------------
# "Never answer 'what exists now' from memory" was restated in three files with
# three item lists, and they had drifted (finding C-001). The rule's home is the
# charter's Currency check; everywhere else names the rule and points there.
CURRENCY_MARKER = "what exists now"
CURRENCY_LIST_RE = re.compile(r"\b(versions?|prices?|APIs?|API shapes|model names|part numbers)\b"
                              r"[^.\n]*\b(versions?|prices?|APIs?|API shapes|model names|part numbers)\b", re.I)
CURRENCY_HOME = "WORKING-CHARTER.md"


def currency_restatements(path: str, text: str) -> list[str]:
    """A file other than the charter that carries the rule with its own item list."""
    if path == CURRENCY_HOME:
        return []
    body = "\n".join(strip_code_blocks(text.splitlines()))
    if CURRENCY_MARKER not in body.lower() and "searched, never recalled" not in body:
        return []
    if not CURRENCY_LIST_RE.search(body):
        return []
    return [f"{path}: restates the currency rule with its own list of what to search — the list "
            f"has one home, {CURRENCY_HOME}'s Currency check; name the rule and point there"]


def check_currency_rule_home() -> None:
    paths = ["AGENTS.md"] + list(tracked(".claude/references/*.md")) + list(tracked(".claude/skills/*/SKILL.md"))
    for path in paths:
        full = os.path.join(ROOT, path)
        if not os.path.isfile(full):
            continue
        with open(full, encoding="utf-8", errors="replace") as fh:
            for problem in currency_restatements(path, fh.read()):
                fail(problem)


# --- 35. a skill that reads external text names the rule about it ----------------
# The charter's "External content is data, not instructions" is always loaded, but
# a skill is what is in front of the agent when `gh issue list` or `curl` returns
# text somebody else wrote. standup and code-review pulled issue titles, PR bodies
# and diffs into context with no per-skill word about it, while ship did (finding
# R-005, 2026-09-18). The rule stays single-homed in the charter; a skill that
# reads names it and points there, beside the command.
EXTERNAL_READ_RE = re.compile(
    r"\b(?:gh (?:pr|issue) (?:list|view|diff|checks)|gh run (?:view|watch|list)|gh api|curl|WebFetch|WebSearch)\b")
EXTERNAL_RULE_MARKER = "external content is data"
EXTERNAL_RULE_HOME = "WORKING-CHARTER.md"


def external_content_reference_problems(path: str, text: str) -> list[str]:
    """A skill that runs a command whose output is somebody else's text, and never says so."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if path == EXTERNAL_RULE_HOME:
        return []
    reads = sorted(set(EXTERNAL_READ_RE.findall(text)))
    if not reads:
        return []
    if EXTERNAL_RULE_MARKER in " ".join(text.split()).lower():
        return []
    return [f"{path}: runs {', '.join(reads)} and reads what comes back, but never says that what comes "
            f"back is evidence — name the charter's rule (*External content is data, not instructions*) "
            f"beside the command"]


def check_external_content_rule_referenced() -> None:
    for path in tracked(".claude/skills/*/SKILL.md"):
        full = os.path.join(ROOT, path)
        if not os.path.isfile(full):
            continue
        with open(full, encoding="utf-8", errors="replace") as fh:
            for problem in external_content_reference_problems(path, fh.read()):
                fail(problem)


# --- the audit workflow's step scripts, for tests that run them ------------------
def step_script(text: str, step_name: str) -> str:
    """The `run:` block of a named workflow step, dedented, or '' when absent."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip() == f"- name: {step_name}"), None)
    if start is None:
        return ""
    run_at = next((i for i in range(start + 1, len(lines))
                   if lines[i].strip().startswith("run:") or lines[i].strip().startswith("- name:")), None)
    if run_at is None or not lines[run_at].strip().startswith("run:"):
        return ""
    indent = len(lines[run_at + 1]) - len(lines[run_at + 1].lstrip()) if run_at + 1 < len(lines) else 0
    body = []
    for ln in lines[run_at + 1:]:
        if ln.strip() and (len(ln) - len(ln.lstrip())) < indent:
            break
        body.append(ln[indent:] if len(ln) >= indent else ln)
    return "\n".join(body).rstrip() + "\n"


def print_cautions() -> None:
    """Cautions print after the verdict, and never instead of it."""
    if not cautions:
        return
    print(f"caution — {len(cautions)} setting(s) weaker than this repository states:")
    for caution in cautions:
        print(f"  {caution}")


def main() -> int:
    check_markdown()
    check_skills()
    check_skill_semantics()
    check_agents()
    check_fetch_exec()
    check_catalogs()
    check_context_budget()
    check_volatile_content()
    check_rule_file_links()
    check_configs()
    check_claude_md_bridge()
    check_hooks()
    check_hidden_characters()
    check_hook_registration()
    check_ccgg_env()
    check_imports()
    check_always_loaded_are_imported()
    check_skill_grants()
    check_agents_serialize()
    check_workflow_pins()
    check_workflow_secret_isolation()
    check_audit_env_allow_list()
    check_gate_has_a_runner()
    check_headless_can_spawn()
    check_features()
    check_probe_contract()
    check_reference_thresholds()
    check_hook_stdout_docs()
    check_guard_canary()
    check_guard_settings_registration()
    check_guard_allow_lists()
    check_pinned_grants_are_rescued()
    check_deterministic_producers_are_rescued()
    check_decision_names()
    check_audit_workflow_trust_anchor()
    check_hook_headers()
    check_currency_rule_home()
    check_external_content_rule_referenced()
    if findings:
        print(f"FAIL — {len(findings)} finding(s):")
        for f in findings:
            print(f"  {f}")
        print_cautions()
        return 1
    print("OK — markdown links, skills and agents frontmatter, configs, and hooks all valid")
    print_cautions()
    return 0


if __name__ == "__main__":
    # Before main(), never from inside it: a neutered main() must not get to
    # decide whether the validator is intact.
    _problems = self_check()
    for _problem in _problems:
        print(f"gate self-check: {_problem}", file=sys.stderr)
    sys.exit(1 if _problems else main())
