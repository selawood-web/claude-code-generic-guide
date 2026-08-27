#!/usr/bin/env python3
"""Repository validator — the executable quality gate for this documentation repo.

Checks, in order:
  1. No tracked markdown file is empty.
  2. Every relative markdown link resolves to a real file.
  3. Every heading anchor referenced in a link exists in the target file.
  4. Every .claude/skills/*/SKILL.md has valid frontmatter with the five house keys.
  5. .claude/config.toml parses as TOML.
  6. .claude/settings.json and .vscode/*.json parse as JSON.
  7. Hook scripts pass bash -n and carry the executable bit in the git index.

Exit code 0 = clean, 1 = findings (each printed with file and reason).
Stdlib only — no dependencies to install.
"""

import json
import os
import re
import subprocess
import sys
import tomllib

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
    toml_path = os.path.join(ROOT, ".claude", "config.toml")
    if os.path.exists(toml_path):
        try:
            tomllib.load(open(toml_path, "rb"))
        except tomllib.TOMLDecodeError as exc:
            fail(f".claude/config.toml: invalid TOML — {exc}")
    for path in tracked(".claude/settings.json") + tracked(".vscode/*.json"):
        try:
            json.load(open(os.path.join(ROOT, path), encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"{path}: invalid JSON — {exc}")


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
    check_configs()
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
