#!/usr/bin/env python3
"""Check feature definition files against the house schema. Stdlib only.

A feature definition (`features/<id>-<slug>.md`, written by the `/feature`
skill) is only useful if it is *complete*: a definition missing its non-goals
or its acceptance criteria reads finished and is not. This script is the
machine half of that promise — the same reading a reviewer would do, run in a
second, in CI, on every change.

Two levels of finding, because a draft and a committed definition are not held
to the same bar:

  error — structural. The file does not parse as a definition at all
          (frontmatter broken, a required section absent or empty).
          Always fails.
  gap   — readiness. The file is well-formed but not decided yet
          (a TBD left in, no measurable outcome, a blocking open question,
          an idea in the ledger with no disposition). Fails once `status:`
          has moved past `draft`, or under --strict.

The ledger ("## Ideas and changes") is the close-out: every idea raised while
the work is in flight is appended there with a bracketed disposition tag, and
a definition cannot reach `shipped` while any of them still reads [open]. That
is the difference between an idea consciously cut and one quietly forgotten —
after the fact, the two are indistinguishable without this.

Usage:
  python3 tools/feature_lint.py                    # every features/*.md
  python3 tools/feature_lint.py features/F001-x.md # named files
  python3 tools/feature_lint.py --strict           # gaps fail in drafts too
"""
from __future__ import annotations

import glob
import os
import re
import sys
from typing import NamedTuple

REQUIRED_KEYS = ("id", "title", "status", "owner", "target")
STATUSES = ("draft", "ready", "building", "shipped", "dropped")

# Presence is enforced; order is not — teams reorder, and a reordered
# definition is still a complete one.
REQUIRED_SECTIONS = (
    "Summary",
    "Problem",
    "Outcome",
    "Scope",
    "Non-goals",
    "Acceptance criteria",
    "Dependencies and risks",
    "Open questions",
    "Ideas and changes",
)

SUMMARY_WORD_CAP = 60

ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*-?\d+$")
PLACEHOLDER_RE = re.compile(
    r"\bTBD\b|\bTODO\b|\bFIXME\b|\bXXX\b|\?\?\?|<[a-z][a-z0-9 _/-]*>|lorem ipsum",
    re.I,
)
# "at least one number with a unit" — 40%, 2 seconds, 500 users, 3x, $10k.
MEASURABLE_RE = re.compile(r"\d+\s*(%|x\b|[a-z$€£]+)|[$€£]\s*\d", re.I)
BLOCKS_RE = re.compile(r"\bblocks:\s*(yes|no)\b", re.I)
EMPTY_ANSWER_RE = re.compile(r"^(none|none yet|n/a|nothing)\.?$", re.I)

# The ledger's disposition tag. Bracketed on purpose: "in" as a bare word
# appears in half the sentences people write, and a tag that can be confused
# with prose is a tag that silently passes when it should fail.
DISPOSITION_RE = re.compile(r"\[(open|in|deferred|dropped)\]", re.I)
NEEDS_REASON = ("deferred", "dropped")


class Finding(NamedTuple):
    level: str  # "error" | "gap"
    line: int
    message: str


def strip_code_blocks(lines: list[str]) -> list[str]:
    """Blank out fenced code so examples inside a definition are never linted."""
    out, in_fence = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return out


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[Finding]]:
    """YAML-ish `key: value` frontmatter — the subset a definition may use.

    Deliberately not a YAML parser: the schema is flat strings, and a
    dependency-free checker is one that still runs in a downstream project.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, [Finding("error", 1, "frontmatter must start with --- on line 1")]
    fields: dict[str, str] = {}
    for no, line in enumerate(lines[1:], 2):
        if line.strip() == "---":
            return fields, []
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep or not key.strip() or key != key.strip():
            return fields, [Finding("error", no, f"frontmatter line does not parse: {line.strip()[:60]}")]
        fields[key.strip().lower()] = value.strip().strip("\"'")
    return fields, [Finding("error", len(lines), "frontmatter never closed with ---")]


def split_sections(text: str) -> dict[str, tuple[int, list[str]]]:
    """Map each `## Heading` (lowercased) to its line number and body lines."""
    sections: dict[str, tuple[int, list[str]]] = {}
    current: str | None = None
    for no, line in enumerate(strip_code_blocks(text.splitlines()), 1):
        if line.startswith("## "):
            current = line[3:].strip().rstrip(":").lower()
            sections[current] = (no, [])
        elif line.startswith("# "):
            current = None
        elif current is not None:
            sections[current][1].append(line)
    return sections


def bullets(body: list[str]) -> list[str]:
    """Bullet items, each joined with its indented continuation lines."""
    items: list[str] = []
    for line in body:
        stripped = line.strip()
        if re.match(r"^([-*+]|\d+\.)\s+", stripped):
            items.append(re.sub(r"^([-*+]|\d+\.)\s+", "", stripped))
        elif items and line.startswith((" ", "\t")) and stripped:
            items[-1] += " " + stripped
    return items


def prose(body: list[str]) -> str:
    return " ".join(line.strip() for line in body if line.strip())


def lint_text(text: str, filename: str = "") -> list[Finding]:
    """Every finding for one definition file. Pure — the unit-testable core."""
    findings: list[Finding] = []
    fields, problems = parse_frontmatter(text)
    findings.extend(problems)

    for key in REQUIRED_KEYS:
        if not fields.get(key):
            findings.append(Finding("error", 1, f"frontmatter missing or empty key '{key}'"))

    status = fields.get("status", "").lower()
    if status and status not in STATUSES:
        findings.append(
            Finding("error", 1, f"status '{status}' is not one of: {', '.join(STATUSES)}")
        )

    ident = fields.get("id", "")
    if ident and not ID_RE.match(ident):
        findings.append(Finding("error", 1, f"id '{ident}' is not a tracker-style id (F001, CAB-42)"))
    base = os.path.basename(filename)
    if ident and base and not base.lower().startswith(ident.lower() + "-"):
        findings.append(
            Finding("error", 1, f"filename '{base}' does not start with the id '{ident}-'")
        )

    lines = strip_code_blocks(text.splitlines())
    if not any(line.startswith("# ") for line in lines):
        findings.append(Finding("error", 1, "no H1 title line"))
    elif ident:
        h1 = next(line for line in lines if line.startswith("# "))
        if ident.lower() not in h1.lower():
            findings.append(Finding("gap", lines.index(h1) + 1, f"H1 does not carry the id '{ident}'"))

    sections = split_sections(text)
    for heading in REQUIRED_SECTIONS:
        if heading.lower() not in sections:
            findings.append(Finding("error", 1, f"missing required section '## {heading}'"))
            continue
        no, body = sections[heading.lower()]
        if not prose(body):
            findings.append(Finding("error", no, f"section '## {heading}' is empty"))

    for no, line in enumerate(lines, 1):
        hit = PLACEHOLDER_RE.search(line)
        if hit:
            findings.append(Finding("gap", no, f"unresolved placeholder: {hit.group(0)}"))

    if "summary" in sections:
        no, body = sections["summary"]
        words = len(prose(body).split())
        if words > SUMMARY_WORD_CAP:
            findings.append(
                Finding("gap", no, f"summary is {words} words — the cap is {SUMMARY_WORD_CAP}")
            )

    if "outcome" in sections:
        no, body = sections["outcome"]
        if not MEASURABLE_RE.search(prose(body)):
            findings.append(
                Finding("gap", no, "outcome states no measurable target (a number with a unit)")
            )

    if "non-goals" in sections:
        no, body = sections["non-goals"]
        if not bullets(body):
            findings.append(Finding("gap", no, "non-goals lists nothing — name what this is not"))

    if "acceptance criteria" in sections:
        no, body = sections["acceptance criteria"]
        testable = [
            item for item in bullets(body)
            if all(word in item.lower() for word in ("given", "when", "then"))
        ]
        if len(testable) < 2:
            findings.append(
                Finding("gap", no, f"{len(testable)} Given/When/Then criteria — at least 2 are needed")
            )

    if "open questions" in sections:
        no, body = sections["open questions"]
        items = bullets(body)
        if not items and not EMPTY_ANSWER_RE.match(prose(body)):
            findings.append(Finding("gap", no, "open questions is neither a list nor 'None.'"))
        for item in items:
            marker = BLOCKS_RE.search(item)
            if not marker:
                findings.append(
                    Finding("gap", no, f"open question has no 'blocks: yes|no' marker: {item[:50]}")
                )
            elif marker.group(1).lower() == "yes" and status not in ("", "draft", "dropped"):
                findings.append(
                    Finding("error", no, f"status '{status}' with a blocking open question: {item[:50]}")
                )

    if "ideas and changes" in sections:
        no, body = sections["ideas and changes"]
        items = bullets(body)
        if not items and not EMPTY_ANSWER_RE.match(prose(body)):
            findings.append(
                Finding("gap", no, "ideas and changes is neither a list nor 'None yet.'")
            )
        for item in items:
            tag = DISPOSITION_RE.search(item)
            if not tag:
                findings.append(
                    Finding("gap", no, f"idea has no [open|in|deferred|dropped] tag: {item[:50]}")
                )
                continue
            disposition = tag.group(1).lower()
            if disposition in NEEDS_REASON and not item[tag.end():].strip(" .—-–:"):
                findings.append(
                    Finding("gap", no, f"[{disposition}] idea gives no reason: {item[:50]}")
                )
            # The close-out. An idea nobody decided on is the failure this
            # ledger exists to catch, so shipping over one is an error, not a gap.
            if disposition == "open" and status == "shipped":
                findings.append(
                    Finding("error", no, f"status 'shipped' with an undecided idea: {item[:50]}")
                )

    return sorted(findings, key=lambda f: (f.line, f.level))


def counts_as_failure(finding: Finding, status: str, strict: bool) -> bool:
    """Errors always fail; gaps fail once the definition has left draft."""
    return finding.level == "error" or strict or status not in ("", "draft")


def lint_file(path: str, strict: bool) -> tuple[list[Finding], bool]:
    text = open(path, encoding="utf-8", errors="replace").read()
    findings = lint_text(text, path)
    status = parse_frontmatter(text)[0].get("status", "").lower()
    failed = any(counts_as_failure(f, status, strict) for f in findings)
    return findings, failed


def default_paths() -> list[str]:
    return [
        p for p in sorted(glob.glob("features/*.md"))
        if os.path.basename(p).lower() != "readme.md"
    ]


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    paths = [a for a in argv if not a.startswith("-")] or default_paths()
    if not paths:
        print("feature-lint: no feature definitions found (features/*.md)")
        return 0

    failures = 0
    for path in paths:
        if not os.path.exists(path):
            print(f"feature-lint: {path}: no such file")
            failures += 1
            continue
        findings, failed = lint_file(path, strict)
        for level, line, message in findings:
            print(f"{path}:{line}: {level}: {message}")
        if failed:
            failures += 1
        elif findings:
            print(f"{path}: draft with {len(findings)} gap(s) — allowed while status is draft")
        else:
            print(f"{path}: OK")
    print(f"feature-lint: {len(paths)} file(s), {failures} failing")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
