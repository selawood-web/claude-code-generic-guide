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

Exit code 0 = clean, 1 = findings (each printed with file and reason).
Stdlib only — no dependencies to install.
"""

import json
import os
import re
import subprocess
import sys

ROOT = subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True
).strip()
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
SKILL_KEYS = ("name", "description", "when-to-use", "allowed-tools", "argument-hint")

findings: list[str] = []


def fail(msg: str) -> None:
    findings.append(msg)


def tracked(pattern: str) -> list[str]:
    out = subprocess.check_output(["git", "ls-files", pattern], cwd=ROOT, text=True)
    return [line for line in out.splitlines() if line]


def heading_slugs(path: str) -> set[str]:
    slugs = set()
    with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("#"):
                text = line.lstrip("#").strip().lower()
                text = re.sub(r"[^\w\s-]", "", text)
                slugs.add(re.sub(r"\s+", "-", text))
    return slugs


def check_markdown() -> None:
    for path in tracked("*.md"):
        full = os.path.join(ROOT, path)
        if os.path.getsize(full) == 0:
            fail(f"{path}: file is empty")
            continue
        content = open(full, encoding="utf-8", errors="replace").read()
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
        keys = {ln.split(":", 1)[0].strip() for ln in lines[1:end] if ":" in ln}
        for key in SKILL_KEYS:
            if key not in keys:
                fail(f"{path}: frontmatter missing key '{key}'")


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
    Catalog files the project does not have are skipped, so this validator is
    safe to copy into repos that adopt the skills without the guide's docs.
    """
    skills = sorted(
        os.path.basename(os.path.dirname(p))
        for p in tracked(".claude/skills/*/SKILL.md")
    )

    def read_if_present(name: str) -> str | None:
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            return None
        return open(path, encoding="utf-8").read()

    readme = read_if_present("README.md")
    agents = read_if_present("AGENTS.md")
    manual = read_if_present("USER-MANUAL.md")

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


def check_claude_md_bridge() -> None:
    """AGENTS.md only loads into Claude Code via the CLAUDE.md import bridge."""
    path = os.path.join(ROOT, "CLAUDE.md")
    if not os.path.exists(path):
        fail("CLAUDE.md: missing — AGENTS.md never loads into Claude Code without it")
    elif "@AGENTS.md" not in open(path, encoding="utf-8").read():
        fail("CLAUDE.md: does not import @AGENTS.md — the behavior rules never load")


def check_hooks() -> None:
    index = subprocess.check_output(
        ["git", "ls-files", "-s", ".claude/hooks/"], cwd=ROOT, text=True
    )
    for line in index.splitlines():
        mode, _, _, path = line.split(None, 3)
        if path.endswith(".sh"):
            if mode != "100755":
                fail(f"{path}: not executable in the git index (mode {mode})")
            probe = subprocess.run(
                ["bash", "-n", os.path.join(ROOT, path)], capture_output=True, text=True
            )
            if probe.returncode != 0:
                fail(f"{path}: bash syntax error — {probe.stderr.strip()}")


def main() -> int:
    check_markdown()
    check_skills()
    check_catalogs()
    check_configs()
    check_claude_md_bridge()
    check_hooks()
    if findings:
        print(f"FAIL — {len(findings)} finding(s):")
        for f in findings:
            print(f"  {f}")
        return 1
    print("OK — markdown links, skills frontmatter, configs, and hooks all valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
