#!/usr/bin/env python3
"""Deterministic stage of /ccgg-audit — every fact a model would otherwise rediscover.

Reads the repository at HEAD, runs the checks below without any model, and writes
two files into the report directory:

  inventory.json   what the repository is: stack, rule files, skills, hooks, agents,
                   tests, CI, permission surface
  facts.json       one record per check outcome, status ok | finding | skipped, with
                   the location and evidence a specialist or verifier can act on

Checks (the four the 2026-09-16 audit found missing come first):
  hook-registration   settings.json ↔ .claude/hooks/ in both directions; unknown events
  hook-stdout         hooks that print for the model on an event whose stdout never reaches it
                      (PreCompact stdout feeds the compaction summarizer, nothing else)
  hidden-characters   zero-width, bidi, soft hyphen, BOM in files read as instructions
  frontmatter         skill and agent keys against the documented vocabulary; tool names;
                      empty descriptions; specifiers in fields that cannot take them
  command-resolution  every `/name` in rule files resolves to a skill or a built-in
  network-exec        fetch-and-execute patterns in hooks and shell scripts
  permission-surface  what the committed settings grant, listed for review
  gate                the repository's own gate, tests, feature lint, catalog — as run

    python3 tools/audit_facts.py --out CCGG-AUDIT-<stamp>/ [--scope all|harness|process|product]

Exit 0 when the stage ran; the verdict belongs to the report. Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import tempfile
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audit_env  # noqa: E402  (same directory, installed together)
from dataclasses import asdict, dataclass

HIDDEN_RE = re.compile("[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff\u00ad\u2066-\u2069]")
COMMAND_REF_RE = re.compile(r"`/([a-z][a-z0-9-]*)`")
HOOK_PATH_RE = re.compile(r"\.claude/hooks/([\w.-]+)")
TOOL_ENTRY_RE = re.compile(r"^([A-Za-z_][\w]*)(\(.*\))?$")
NETWORK_PATTERNS = (
    (re.compile(r"\bcurl\b"), "curl"),
    (re.compile(r"\bwget\b"), "wget"),
    (re.compile(r"\|\s*(sh|bash)\b"), "pipe to shell"),
    (re.compile(r"\bgit\s+clone\b"), "git clone"),
    (re.compile(r"\beval\b"), "eval"),
    (re.compile(r"\bsource\s+\$|\.\s+\$"), "source from variable"),
)
RULE_FILES = ("CLAUDE.md", "AGENTS.md", "WORKING-CHARTER.md", "MEMORY.md")
# Every tracked file whose content reaches the model as instructions. Kept
# character-for-character identical to tools/validate.py's INSTRUCTION_GLOBS —
# the two scans had drifted apart, and the hidden-character scan here saw the
# rule files, references, hooks, agents and SKILL.md only, so a skill's
# companion pages, decisions/ and knowledge-base/ went unread (findings R-007
# and R-014). tools/test_validate.py compares the two tuples.
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
STACK_MARKERS = {
    "package.json": "javascript", "pyproject.toml": "python", "requirements.txt": "python",
    "go.mod": "go", "Cargo.toml": "rust", "pom.xml": "java", "build.gradle": "java",
    "Gemfile": "ruby", "composer.json": "php",
}
SCOPES = ("all", "harness", "process", "product")
VOCAB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_vocab.json")


@dataclass
class Fact:
    id: str
    kind: str
    status: str  # ok | finding | skipped
    location: str
    evidence: str
    detail: str = ""


class Facts:
    """Accumulates facts with stable ids per kind."""

    def __init__(self) -> None:
        self.items: list[Fact] = []
        self._counts: dict[str, int] = {}

    def add(self, kind: str, status: str, location: str, evidence: str, detail: str = "") -> Fact:
        if status not in ("ok", "finding", "skipped"):
            raise ValueError(f"bad status {status!r}")
        n = self._counts.get(kind, 0) + 1
        self._counts[kind] = n
        fact = Fact(f"{kind}-{n:03d}", kind, status, location, evidence, detail)
        self.items.append(fact)
        return fact


# --------------------------------------------------------------------------- pure checks


def hidden_characters(text: str) -> list[tuple[int, list[str]]]:
    """Line numbers and code points of invisible characters that survive review."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    hits = []
    for no, line in enumerate(text.splitlines(), 1):
        found = [f"U+{ord(c):04X}" for c in line if HIDDEN_RE.match(c)]
        if found:
            hits.append((no, found))
    return hits


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Top-level `key: value` pairs of a frontmatter block, or None when there is none.

    Mirrors what the product does: the block counts only when `---` is line 1.
    Nested YAML (an indented block under `hooks:`) is kept as the key with an empty
    value; this stage needs the keys and the scalar values, not a YAML parser.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if not line or line[0] in " \t" or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return None  # never closed — the product treats the whole file as content


def split_tools(value: str) -> list[str]:
    """`Read, Grep Bash(git *)` -> ['Read', 'Grep', 'Bash(git *)'] — comma or space separated."""
    if not value:
        return []
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    out, buf, depth = [], "", 0
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch in ", " and depth == 0:
            if buf:
                out.append(buf)
            buf = ""
            continue
        buf += ch
    if buf:
        out.append(buf)
    return [t.strip().strip("'\"") for t in out if t.strip()]


def tool_name(entry: str) -> str:
    m = TOOL_ENTRY_RE.match(entry.strip())
    return m.group(1) if m else entry.strip()


def has_specifier(entry: str) -> bool:
    return "(" in entry


def spelling_variant(key: str, documented: list[str]) -> str | None:
    """The documented key this one is a hyphen/underscore/case variant of, if any."""
    norm = key.replace("-", "").replace("_", "").lower()
    for doc in documented:
        if doc.replace("-", "").replace("_", "").lower() == norm and doc != key:
            return doc
    return None


def frontmatter_facts(path: str, text: str, kind: str, vocab: dict, facts: Facts,
                      tooling_keys: set[str] | None = None) -> None:
    """Skill (`kind='skill'`) or agent (`kind='agent'`) frontmatter against the vocabulary.

    `tooling_keys` are keys the repository's own scripts read (a catalog generator, a
    validator); the product ignores them but they are not dead.
    """
    documented = vocab["skill_keys"] if kind == "skill" else vocab["agent_keys"]
    tooling_keys = tooling_keys or set()
    fields = parse_frontmatter(text)
    if fields is None:
        facts.add("frontmatter", "finding", path,
                  "no frontmatter block starting on line 1 — the product reads the whole file as content",
                  "class: dead-mechanism")
        return
    if not fields.get("description"):
        facts.add("frontmatter", "finding", path, "description missing or empty",
                  "the product uses the first non-empty content line instead; auto-invocation matches on it")
    for key in fields:
        if key in documented:
            continue
        variant = spelling_variant(key, documented)
        if variant:
            facts.add("frontmatter", "finding", path,
                      f"key '{key}' is not read by the product; the documented key is '{variant}'",
                      "class: dead-key; the value is silently ignored")
        elif key in tooling_keys:
            facts.add("frontmatter", "ok", path, f"key '{key}' is not a product key but repository tooling reads it")
        else:
            facts.add("frontmatter", "finding", path, f"key '{key}' is not a documented {kind} key",
                      "class: dead-key; no product surface and no repository tooling reads it")
    tool_fields = ("allowed-tools", "disallowed-tools") if kind == "skill" else ("tools", "disallowedTools")
    known_tools = set(vocab["tools"])
    for field in tool_fields:
        if field not in fields:
            continue
        for entry in split_tools(fields[field]):
            name = tool_name(entry)
            if name.startswith("mcp__") or name == "*":
                continue
            if name not in known_tools:
                facts.add("frontmatter", "finding", path,
                          f"{field} names '{entry}', which is not a Claude Code tool",
                          "the grant or restriction applies to nothing")
            if kind == "agent" and has_specifier(entry):
                facts.add("frontmatter", "finding", path,
                          f"{field} entry '{entry}' carries a specifier",
                          "an agent tools/disallowedTools specifier removes the whole tool; narrow with permissions rules instead")
    if not any(f.location == path and f.kind == "frontmatter" and f.status == "finding" for f in facts.items):
        facts.add("frontmatter", "ok", path, "keys and tool names match the documented vocabulary")


def hook_commands(settings: dict) -> list[tuple[str, str]]:
    """(event, command) for every command hook registered in a settings object."""
    out = []
    hooks = settings.get("hooks") if isinstance(settings, dict) else None
    if not isinstance(hooks, dict):
        return out
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            continue
        for group in groups:
            for hook in (group.get("hooks") or []) if isinstance(group, dict) else []:
                if isinstance(hook, dict) and hook.get("type", "command") == "command" and hook.get("command"):
                    out.append((event, str(hook["command"])))
    return out


def hook_registration(settings: dict, hook_files: list[str], vocab: dict, facts: Facts,
                      registered_elsewhere: set[str] | None = None) -> None:
    """Both directions: registered → present, present → registered; and known event names.

    `registered_elsewhere` names hook files an agent or skill frontmatter registers;
    those are scoped hooks and count as registered.
    """
    commands = hook_commands(settings)
    referenced: set[str] = set(registered_elsewhere or ())
    for event, command in commands:
        if event not in vocab["hook_events"]:
            facts.add("hook-registration", "finding", ".claude/settings.json",
                      f"hook registered for unknown event '{event}'", "class: dead-mechanism; the hook never fires")
        for name in HOOK_PATH_RE.findall(command):
            referenced.add(name)
    present = {os.path.basename(p) for p in hook_files}
    for name in sorted(referenced - present):
        facts.add("hook-registration", "finding", f".claude/hooks/{name}",
                  "registered in settings.json but the file does not exist", "class: dead-mechanism")
    for name in sorted(present - referenced):
        facts.add("hook-registration", "finding", f".claude/hooks/{name}",
                  "present but no settings.json hook references it", "class: dead-mechanism; nothing runs it")
    if referenced and referenced == present:
        facts.add("hook-registration", "ok", ".claude/settings.json", f"{len(present)} hook file(s) registered and present")
    elif not commands and not present:
        facts.add("hook-registration", "skipped", ".claude/settings.json", "no hooks registered and no hook files")


def hook_stdout_facts(settings: dict, read_script, vocab: dict, facts: Facts) -> None:
    """A hook that prints for the model on an event whose stdout only reaches the debug log."""
    reaches = set(vocab["hook_stdout_reaches_model"])
    for event, command in hook_commands(settings):
        if event in reaches:
            continue
        for name in HOOK_PATH_RE.findall(command):
            text = read_script(name)
            if text is None:
                continue
            prints = [ln.strip() for ln in text.splitlines()
                      if re.match(r"\s*(echo|printf)\b", ln) and not re.search(r">\s*\S", ln)]
            if not prints:
                continue
            if event == "PreCompact":
                # PreCompact stdout is handed to the compaction model as summary
                # instructions; it is dead only when it addresses the agent.
                commands = COMMAND_REF_RE.findall(" ".join(prints)) or re.findall(r"(?<![\w/])/([a-z][a-z0-9-]+)\b", " ".join(prints))
                if commands:
                    facts.add("hook-stdout", "finding", f".claude/hooks/{name}",
                              f"prints on PreCompact an instruction to the agent (/{commands[0]}); PreCompact stdout only reaches the compaction summarizer",
                              "class: dead-mechanism; write summary instructions instead, and move any agent-facing reminder to a SessionStart matcher")
                else:
                    facts.add("hook-stdout", "ok", f".claude/hooks/{name}", "PreCompact stdout shapes the compaction summary")
                continue
            facts.add("hook-stdout", "finding", f".claude/hooks/{name}",
                      f"prints on {event}, whose stdout goes to the debug log, never to the model: {prints[0][:80]}",
                      "class: dead-mechanism; only SessionStart, UserPromptSubmit, UserPromptExpansion and PostModelSwitch stdout reach the model")


def command_references(text: str) -> set[str]:
    return set(COMMAND_REF_RE.findall(text))


def resolve_commands(refs: set[str], skill_names: set[str], builtins: list[str]) -> list[str]:
    known = skill_names | set(builtins)
    return sorted(r for r in refs if r not in known)


def network_patterns(text: str) -> list[tuple[int, str, str]]:
    hits = []
    for no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#") or re.search(r"\(r[\"\']", stripped):
            continue  # a comment, or a regex literal that names the pattern rather than running it
        for pattern, label in NETWORK_PATTERNS:
            if pattern.search(line):
                hits.append((no, label, stripped[:100]))
    return hits


def permission_surface(settings: dict) -> dict:
    perms = settings.get("permissions", {}) if isinstance(settings, dict) else {}
    return {
        "allow": list(perms.get("allow", []) or []),
        "deny": list(perms.get("deny", []) or []),
        "additionalDirectories": list(perms.get("additionalDirectories", []) or []),
        "defaultMode": perms.get("defaultMode"),
        "env": sorted((settings.get("env") or {}).keys()) if isinstance(settings, dict) else [],
        "enableAllProjectMcpServers": settings.get("enableAllProjectMcpServers") if isinstance(settings, dict) else None,
        "hooks": sorted({e for e, _ in hook_commands(settings)}),
    }


# --------------------------------------------------------------------------- repository IO


def git(repo: str, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True, encoding="utf-8", errors="replace").strip()


def tracked(repo: str, pattern: str) -> list[str]:
    out = git(repo, "ls-files", pattern)
    return [p for p in out.splitlines() if p]


def instruction_files(repo: str) -> list[str]:
    """The tracked files INSTRUCTION_GLOBS names, sorted and deduplicated."""
    found: set[str] = set()
    for pattern in INSTRUCTION_GLOBS:
        found.update(tracked(repo, pattern))
    return sorted(found)


def read(repo: str, path: str) -> str:
    with open(os.path.join(repo, path), encoding="utf-8", errors="replace") as fh:
        return fh.read()


def load_json(repo: str, path: str) -> dict | None:
    try:
        return json.loads(read(repo, path))
    except (OSError, ValueError):
        return None


def tooling_referenced_keys(repo: str) -> set[str]:
    """Every quoted identifier in tools/*.py — the keys repository scripts might read."""
    keys: set[str] = set()
    for path in tracked(repo, "tools/*.py"):
        keys |= set(re.findall(r"[\"\']([a-z][a-z0-9_-]{2,})[\"\']", read(repo, path)))
    return keys


def run_gate(repo: str, label: str, cmd: list[str], facts: Facts, execute: bool = False) -> None:
    """Run the audited tree's own gate command, or record that it was not run.

    Two things this function is careful about, both audit finding S-005.

    It executes code out of the checkout, so it does not do that by default: the
    caller passes execute=True, which tools/audit_facts.py only does for
    --run-gates. Pointing the audit at a repository somebody handed you should
    not run that repository's Python. A gate that was not run is still recorded,
    so the omission is visible in facts.json rather than looking like a clean
    result nobody measured.

    When it does execute, the command gets the allow-list from tools/audit_env.py
    and a throwaway HOME — previously it inherited os.environ, so the tree's own
    test suite ran with the operator's tokens in scope.
    """
    if not execute:
        facts.add("gate", "skipped", " ".join(cmd),
                  f"{label} not run: pass --run-gates to execute the audited tree's own code",
                  "class: not-measured")
        return
    home = tempfile.mkdtemp(prefix="ccgg-gate-home-")
    try:
        proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=900,
                              env=audit_env.sandbox_env(home, actor="ccgg-gate"))
    except (OSError, subprocess.TimeoutExpired) as exc:
        facts.add("gate", "finding", " ".join(cmd), f"{label} could not run: {exc}")
        return
    finally:
        shutil.rmtree(home, ignore_errors=True)
    tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-5:])
    status = "ok" if proc.returncode == 0 else "finding"
    facts.add("gate", status, " ".join(cmd), f"{label} exited {proc.returncode}", tail[:600])


def build_inventory(repo: str, settings: dict | None) -> dict:
    files = set(tracked(repo, "*"))
    head = git(repo, "rev-parse", "HEAD")
    dirty = bool(git(repo, "status", "--porcelain"))
    return {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "head": head,
        "dirty": dirty,
        "stack": sorted({lang for marker, lang in STACK_MARKERS.items() if marker in files}),
        "rule_files": [f for f in RULE_FILES if f in files],
        "skills": sorted(p.split("/")[2] for p in files if p.startswith(".claude/skills/") and p.endswith("/SKILL.md")),
        "agents": sorted(p for p in files if p.startswith(".claude/agents/") and p.endswith(".md")),
        "hooks": sorted(p for p in files if p.startswith(".claude/hooks/")),
        "references": sorted(p for p in files if p.startswith(".claude/references/")),
        "tests": sorted(p for p in files if re.search(r"(^|/)(test_[^/]+\.py|[^/]+_test\.(py|go)|[^/]+\.(test|spec)\.[jt]sx?)$", p)),
        "ci_workflows": sorted(p for p in files if p.startswith(".github/workflows/")),
        "features": sorted(p for p in files if p.startswith("features/") and p.endswith(".md") and not p.endswith("README.md")),
        "permission_surface": permission_surface(settings or {}),
        "file_count": len(files),
    }


def ensure_report_dir(repo: str, out: str | None) -> str:
    if out is None:
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = os.path.join(repo, f"CCGG-AUDIT-{stamp}")
    os.makedirs(out, exist_ok=True)
    ignore = os.path.join(out, ".gitignore")
    if not os.path.exists(ignore):
        with open(ignore, "w", encoding="utf-8") as fh:
            fh.write("# Audit reports are ignored by default. `git add -f` keeps one, but a\n"
                     "# committed report's candidates/ is then present in every later verifier\n"
                     "# worktree under the same filenames, and a verifier that cannot find its\n"
                     "# own run's batch has been observed reading the committed one instead.\n*\n")
    return out


def collect(repo: str, scope: str, vocab: dict, run_gates: bool = False) -> tuple[dict, Facts]:
    facts = Facts()
    settings = load_json(repo, ".claude/settings.json")
    inventory = build_inventory(repo, settings)
    harness = scope in ("all", "harness")
    process = scope in ("all", "process")

    if harness:
        hook_files = inventory["hooks"]
        if settings is None and os.path.exists(os.path.join(repo, ".claude/settings.json")):
            facts.add("hook-registration", "finding", ".claude/settings.json", "settings.json does not parse as JSON")
        scoped: set[str] = set()
        for path in inventory["agents"] + [f".claude/skills/{s}/SKILL.md" for s in inventory["skills"]]:
            scoped |= set(HOOK_PATH_RE.findall(read(repo, path)))
        hook_registration(settings or {}, hook_files, vocab, facts, scoped)
        hook_stdout_facts(settings or {}, lambda n: read(repo, f".claude/hooks/{n}") if f".claude/hooks/{n}" in hook_files else None,
                          vocab, facts)

        scanned = instruction_files(repo)
        hidden_total = 0
        for path in scanned:
            for no, cps in hidden_characters(read(repo, path)):
                hidden_total += 1
                facts.add("hidden-characters", "finding", f"{path}:{no}", f"invisible characters {', '.join(cps)}",
                          "class: injection; review the line in a hex view before trusting it")
        if not hidden_total:
            facts.add("hidden-characters", "ok", "instruction files", f"{len(scanned)} file(s) scanned, none found")

        tooling_keys = tooling_referenced_keys(repo)
        for skill in inventory["skills"]:
            path = f".claude/skills/{skill}/SKILL.md"
            frontmatter_facts(path, read(repo, path), "skill", vocab, facts, tooling_keys)
            fields = parse_frontmatter(read(repo, path)) or {}
            if fields.get("name") and fields["name"] != skill:
                facts.add("frontmatter", "finding", path,
                          f"name '{fields['name']}' differs from directory '{skill}'",
                          "the command comes from the directory; name is display-only for project skills")
        for path in inventory["agents"]:
            frontmatter_facts(path, read(repo, path), "agent", vocab, facts, tooling_keys)

        refs: set[str] = set()
        for path in inventory["rule_files"] + inventory["references"]:
            refs |= command_references(read(repo, path))
        unresolved = resolve_commands(refs, set(inventory["skills"]), vocab["builtin_commands"])
        for name in unresolved:
            facts.add("command-resolution", "finding", "rule files", f"`/{name}` is neither a skill here nor a documented built-in",
                      "class: dead-mechanism unless it is a placeholder in prose")
        if not unresolved:
            facts.add("command-resolution", "ok", "rule files", f"{len(refs)} command reference(s) resolve")

        shell_files = inventory["hooks"] + sorted(p for p in tracked(repo, "*.sh"))
        net_total = 0
        for path in dict.fromkeys(shell_files):
            for no, label, snippet in network_patterns(read(repo, path)):
                net_total += 1
                facts.add("network-exec", "finding", f"{path}:{no}", f"{label}: {snippet}",
                          "class: supply-chain; pin, verify, or document the trust boundary")
        if not net_total:
            facts.add("network-exec", "ok", "hooks and scripts", "no fetch-or-execute patterns")

        surface = inventory["permission_surface"]
        facts.add("permission-surface", "finding" if (surface["allow"] or surface["env"] or surface["additionalDirectories"]) else "ok",
                  ".claude/settings.json", json.dumps(surface, sort_keys=True),
                  "grants in a committed file apply after trust in a session and without trust under -p")

    if process:
        if os.path.exists(os.path.join(repo, "tools/validate.py")):
            run_gate(repo, "validator", [sys.executable, "tools/validate.py"], facts, execute=run_gates)
        if any(t.startswith("tools/test_") for t in inventory["tests"]):
            run_gate(repo, "unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tools", "-p", "test_*.py"], facts, execute=run_gates)
        elif inventory["tests"]:
            facts.add("gate", "skipped", "tests", f"{len(inventory['tests'])} test file(s) found but no known runner — run them yourself")
        if inventory["features"] and os.path.exists(os.path.join(repo, "tools/feature_lint.py")):
            run_gate(repo, "feature lint", [sys.executable, "tools/feature_lint.py", "--strict"], facts, execute=run_gates)
        if os.path.exists(os.path.join(repo, "tools/catalog.py")):
            run_gate(repo, "catalog", [sys.executable, "tools/catalog.py"], facts, execute=run_gates)
        if not inventory["ci_workflows"]:
            facts.add("gate", "finding", ".github/workflows", "no CI workflow — the gate runs only when someone remembers")
        if not inventory["tests"]:
            facts.add("gate", "finding", "tests", "no test files detected", "class: weak-test")

    return inventory, facts


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=None)
    parser.add_argument("--out", default=None, help="report directory (default: CCGG-AUDIT-<stamp>/ in the repo)")
    parser.add_argument("--scope", default="all", choices=SCOPES)
    parser.add_argument("--run-gates", action="store_true",
                        help="run the audited tree's own validator, tests, feature lint and catalog. "
                             "Off by default: this executes code from the checkout. On, it runs with "
                             "a minimal environment and a throwaway HOME, never the operator's.")
    parser.add_argument("--vocab", default=VOCAB_PATH)
    args = parser.parse_args(argv)
    try:
        repo = args.repo or git(os.getcwd(), "rev-parse", "--show-toplevel")
    except subprocess.CalledProcessError:
        print("audit-facts: not inside a git repository")
        return 2
    try:
        vocab = json.load(open(args.vocab, encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"audit-facts: cannot read vocabulary {args.vocab}: {exc}")
        return 2
    out = ensure_report_dir(repo, args.out)
    inventory, facts = collect(repo, args.scope, vocab, run_gates=args.run_gates)
    with open(os.path.join(out, "inventory.json"), "w", encoding="utf-8") as fh:
        json.dump(inventory, fh, indent=2)
        fh.write("\n")
    with open(os.path.join(out, "facts.json"), "w", encoding="utf-8") as fh:
        json.dump({"scope": args.scope, "vocab_as_of": vocab.get("as_of"), "facts": [asdict(f) for f in facts.items]}, fh, indent=2)
        fh.write("\n")
    by_kind: dict[str, dict[str, int]] = {}
    for f in facts.items:
        by_kind.setdefault(f.kind, {"ok": 0, "finding": 0, "skipped": 0})[f.status] += 1
    print(f"audit-facts: {len(facts.items)} fact(s) -> {out}")
    for kind, counts in sorted(by_kind.items()):
        print(f"  {kind:20} ok {counts['ok']:3}  finding {counts['finding']:3}  skipped {counts['skipped']:3}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
