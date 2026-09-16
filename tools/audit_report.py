#!/usr/bin/env python3
"""Render REPORT.md for a /ccgg-audit run from the report directory's artifacts.

Reads findings.jsonl (the verifier's output, one JSON object per line), facts.json,
probes.json, and REVISION-*.json when present. Every finding is validated against
the F002 schema in code, and one rule is enforced here rather than in any brief:
an `unverified` finding may not carry `blocker` severity. A violation names the
line and fails the render, so a report that exists is a report that obeys the
contract.

    python3 tools/audit_report.py --dir CCGG-AUDIT-<stamp>/

Stdlib only.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

REQUIRED = ("id", "layer", "class", "severity", "confidence", "location", "claim",
            "evidence", "reproduction", "fix", "becomes_check")
LAYERS = ("harness", "product", "process")
SEVERITIES = ("blocker", "important", "suggestion")
CONFIDENCES = ("verified", "unverified")
SEVERITY_MARK = {"blocker": "🔴", "important": "🟡", "suggestion": "🔵"}


def validate_record(rec: object) -> list[str]:
    """Every way one finding fails the schema, as messages; empty means valid."""
    if not isinstance(rec, dict):
        return ["finding is not a JSON object"]
    problems = [f"missing field '{k}'" for k in REQUIRED if k not in rec]
    if problems:
        return problems
    if rec["layer"] not in LAYERS:
        problems.append(f"layer must be one of {LAYERS}, got {rec['layer']!r}")
    if rec["severity"] not in SEVERITIES:
        problems.append(f"severity must be one of {SEVERITIES}, got {rec['severity']!r}")
    if rec["confidence"] not in CONFIDENCES:
        problems.append(f"confidence must be one of {CONFIDENCES}, got {rec['confidence']!r}")
    for key in ("id", "class", "location", "claim", "evidence", "fix"):
        if not isinstance(rec[key], str) or not rec[key].strip():
            problems.append(f"'{key}' must be a non-empty string")
    if rec.get("confidence") == "unverified" and rec.get("severity") == "blocker":
        problems.append("an unverified finding cannot be a blocker")
    if rec.get("confidence") == "verified" and not (isinstance(rec["reproduction"], str) and rec["reproduction"].strip()):
        problems.append("a verified finding needs a non-empty reproduction")
    if rec["becomes_check"] is not None and not isinstance(rec["becomes_check"], str):
        problems.append("'becomes_check' must be a string or null")
    return problems


def load_findings(text: str) -> tuple[list[dict], list[str]]:
    """Parse JSONL; returns (valid records, problems with line numbers)."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    records, problems = [], []
    for no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError as exc:
            problems.append(f"line {no}: not JSON ({exc})")
            continue
        bad = validate_record(rec)
        if bad:
            problems.extend(f"line {no}: {b}" for b in bad)
        else:
            records.append(rec)
    return records, problems


def sort_key(rec: dict) -> tuple[int, int, str]:
    return (SEVERITIES.index(rec["severity"]), CONFIDENCES.index(rec["confidence"]), rec["id"])


def render(findings: list[dict], facts: dict | None, probes: dict | None, revision: dict | None) -> str:
    out = ["# CCGG audit report", ""]
    if revision:
        out.append(f"- **Commit:** `{revision.get('head', '?')}`" + (" (uncommitted changes present)" if revision.get("dirty") else ""))
        out.append(f"- **Scope:** {revision.get('scope', 'all')}")
        if revision.get("cost_usd") is not None:
            out.append(f"- **Cost:** {revision['cost_usd']} USD · **Duration:** {revision.get('duration_s', '?')} s")
        out.append("")
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in SEVERITIES}
    unverified = sum(1 for f in findings if f["confidence"] == "unverified")
    out.append(f"**{len(findings)} finding(s):** {counts['blocker']} blocker, {counts['important']} important, "
               f"{counts['suggestion']} suggestion — {unverified} unverified.")
    out.append("")
    if probes:
        s = probes.get("summary", {})
        out.append(f"**Gate catch rate:** {s.get('caught', '?')}/{s.get('total', '?')} probes"
                   + (f" — {len(s['regressions'])} regression(s)" if s.get("regressions") else "")
                   + (f" — {len(s['promotions'])} promotion(s) to record" if s.get("promotions") else "") + ".")
        out.append("")
    if facts:
        items = facts.get("facts", [])
        n_find = sum(1 for f in items if f.get("status") == "finding")
        out.append(f"**Deterministic stage:** {len(items)} fact(s), {n_find} flagged (facts.json).")
        out.append("")

    out += ["## Findings", ""]
    if not findings:
        out += ["_None verified._", ""]
    for rec in sorted(findings, key=sort_key):
        tag = "" if rec["confidence"] == "verified" else " · *unverified*"
        out.append(f"### {SEVERITY_MARK[rec['severity']]} {rec['id']} — {rec['claim']}")
        out.append(f"`{rec['layer']}` · `{rec['class']}` · {rec['location']}{tag}")
        out.append("")
        out.append(f"**Evidence.** {rec['evidence']}")
        out.append("")
        if rec["reproduction"]:
            out += ["**Reproduce.**", "```", rec["reproduction"].strip(), "```", ""]
        out.append(f"**Smallest fix.** {rec['fix']}")
        out.append("")

    checks = [(rec["id"], rec["becomes_check"]) for rec in sorted(findings, key=sort_key) if rec["becomes_check"]]
    out += ["## Proposed checks", ""]
    if checks:
        out += [f"- {cid}: {text}" for cid, text in checks]
    else:
        out.append("_No finding proposes a permanent check._")
    out.append("")
    return "\n".join(out)


def read_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", required=True, help="the CCGG-AUDIT-<stamp>/ directory")
    args = parser.parse_args(argv)
    if not os.path.isdir(args.dir):
        print(f"audit-report: {args.dir} is not a directory")
        return 2
    findings_path = os.path.join(args.dir, "findings.jsonl")
    findings, problems = ([], [])
    if os.path.exists(findings_path):
        findings, problems = load_findings(open(findings_path, encoding="utf-8").read())
    if problems:
        print(f"audit-report: findings.jsonl violates the schema — {len(problems)} problem(s):")
        for p in problems:
            print(f"  {p}")
        return 1
    revisions = sorted(glob.glob(os.path.join(args.dir, "REVISION-*.json")))
    text = render(findings, read_json(os.path.join(args.dir, "facts.json")),
                  read_json(os.path.join(args.dir, "probes.json")),
                  read_json(revisions[-1]) if revisions else None)
    with open(os.path.join(args.dir, "REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"audit-report: {len(findings)} finding(s) -> {os.path.join(args.dir, 'REPORT.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
