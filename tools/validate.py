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

Exit code 0 = clean, 1 = findings (each printed with file and reason).
Stdlib only — no dependencies to install.
"""

import json
import os
import re
import shutil
import subprocess
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

findings: list[str] = []


def fail(msg: str) -> None:
    findings.append(msg)


def tracked(pattern: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "ls-files", pattern], cwd=ROOT, text=True, encoding="utf-8"
    )
    return [line for line in out.splitlines() if line]


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


def check_fetch_exec() -> None:
    for path in dict.fromkeys(tracked(".claude/hooks/*") + tracked("*.sh")):
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
    check_features()
    if findings:
        print(f"FAIL — {len(findings)} finding(s):")
        for f in findings:
            print(f"  {f}")
        return 1
    print("OK — markdown links, skills and agents frontmatter, configs, and hooks all valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
