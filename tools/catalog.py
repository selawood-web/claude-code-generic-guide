#!/usr/bin/env python3
"""Generate the skill catalogs from skill frontmatter — one command, zero drift.

Sources of truth: each skill's `name` and `purpose` frontmatter keys in
.claude/skills/*/SKILL.md. From those this script rewrites:

  - the skills table in README.md and AGENTS.md, inside the
    `<!-- ccgg:skills:start -->` / `<!-- ccgg:skills:end -->` markers
  - every stated skill count in README.md, USER-MANUAL.md,
    SYSTEM-OVERVIEW.md, and install.sh (plus install.sh's spelled-out count)

Files without the markers keep their tables untouched (a downstream project's
own README); files that are absent are skipped. Long-form docs (USER-MANUAL
per-skill entries, SYSTEM-OVERVIEW group tables) stay hand-written — this
script only maintains the mechanical surface. `tools/validate.py` remains the
enforcement; this is the fixer.

Usage:
  python3 tools/catalog.py            # check: exit 1 if anything is stale
  python3 tools/catalog.py --write    # apply the regeneration
"""
from __future__ import annotations

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

START, END = "<!-- ccgg:skills:start -->", "<!-- ccgg:skills:end -->"

COUNT_RE = re.compile(
    r"\b(\d+)(\s+(?:production-ready\s+|reusable\s+|installed\s+)?[Ss]kill(?:s\b| workflows\b))"
)
WORDS = {
    18: "eighteen", 19: "nineteen", 20: "twenty", 21: "twenty-one",
    22: "twenty-two", 23: "twenty-three", 24: "twenty-four", 25: "twenty-five",
    26: "twenty-six", 27: "twenty-seven", 28: "twenty-eight", 29: "twenty-nine",
    30: "thirty",
}


def read_skills() -> list[tuple[str, str]]:
    skills = []
    for path in sorted(glob.glob(os.path.join(ROOT, ".claude/skills/*/SKILL.md"))):
        text = open(path, encoding="utf-8").read()
        name = re.search(r"^name:\s*(\S+)", text, re.M)
        purpose = re.search(r"^purpose:\s*(.+?)\s*$", text, re.M)
        if not name or not purpose:
            sys.exit(f"catalog: {path} missing name or purpose frontmatter")
        skills.append((name.group(1), purpose.group(1)))
    if not skills:
        sys.exit("catalog: no skills found under .claude/skills/")
    return skills


def render_table(skills: list[tuple[str, str]], with_invoke: bool) -> str:
    if with_invoke:
        head = "| Skill | Invoke | Purpose |\n|-------|--------|---------|\n"
        rows = "".join(f"| `{n}` | `/{n}` | {p} |\n" for n, p in skills)
    else:
        head = "| Skill | Purpose |\n|-------|---------|\n"
        rows = "".join(f"| `/{n}` | {p} |\n" for n, p in skills)
    return head + rows


def replace_region(text: str, table: str) -> str | None:
    if START not in text or END not in text:
        return None
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    return pattern.sub(START + "\n" + table + END, text)


def update_counts(text: str, n: int) -> str:
    text = COUNT_RE.sub(lambda m: f"{n}{m.group(2)}", text)
    if n in WORDS:
        text = re.sub(r"expect [a-z-]+\.", f"expect {WORDS[n]}.", text)
    return text


def main() -> None:
    write = "--write" in sys.argv
    skills = read_skills()
    n = len(skills)
    stale: list[str] = []

    plans = {
        "README.md": (True, True),        # (has marked table, has counts)
        "AGENTS.md": (False, False),
        "USER-MANUAL.md": (None, True),
        "SYSTEM-OVERVIEW.md": (None, True),
        "install.sh": (None, True),
    }
    # AGENTS.md: marked table without the Invoke column, no counts
    plans["AGENTS.md"] = (False, False)

    for fname, (invoke_style, has_counts) in plans.items():
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            continue
        original = open(path, encoding="utf-8").read()
        updated = original
        if invoke_style is not None:
            table = render_table(skills, with_invoke=invoke_style)
            replaced = replace_region(updated, table)
            if replaced is not None:
                updated = replaced
        if has_counts or invoke_style is not None:
            updated = update_counts(updated, n)
        if updated != original:
            stale.append(fname)
            if write:
                open(path, "w", encoding="utf-8").write(updated)

    if stale:
        verb = "regenerated" if write else "STALE (run: python3 tools/catalog.py --write)"
        print(f"catalog: {n} skills; {verb}: {', '.join(stale)}")
        if not write:
            sys.exit(1)
    else:
        print(f"catalog: {n} skills; all catalogs current")


if __name__ == "__main__":
    main()
