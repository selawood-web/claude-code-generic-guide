#!/usr/bin/env python3
"""Render REPORT.md for a /ccgg-audit run from the report directory's artifacts.

Reads findings.jsonl (the verifier's output, one JSON object per line), facts.json,
probes.json, and REVISION-*.json when present. A candidate in candidates/*.json
that no verifier record covers is rendered as an unverified finding rather than
dropped, and the commit falls back to inventory.json when no REVISION stamp exists. Every finding is validated against
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


def candidates_as_unverified(candidates: list[dict]) -> list[dict]:
    """Findings the verifier never saw, rendered as what they are: unverified.

    A run whose verifier delivered nothing used to render an empty report — a
    clean bill for a repository nobody checked. Every candidate a specialist
    produced becomes an unverified finding capped at important, with the
    falsifier the specialist wrote as the reproduction still to run.
    """
    out = []
    for cand in candidates:
        if not isinstance(cand, dict) or not str(cand.get("id", "")).strip():
            continue
        severity = cand.get("severity") if cand.get("severity") in SEVERITIES else "important"
        if severity == "blocker":
            severity = "important"
        layer = cand.get("layer") if cand.get("layer") in LAYERS else "harness"
        out.append({
            "id": str(cand["id"]),
            "layer": layer,
            "class": str(cand.get("class") or "unclassified"),
            "severity": severity,
            "confidence": "unverified",
            "location": str(cand.get("location") or "unknown"),
            "claim": str(cand.get("claim") or "(no claim)"),
            "evidence": str(cand.get("evidence") or "(specialist gave no evidence)"),
            "reproduction": "",
            "fix": "unverified — the verifier did not deliver on this candidate; falsifier still to run: "
                   + str(cand.get("falsifier") or "(none written)"),
            "becomes_check": None,
        })
    return out


def load_candidates(report_dir: str) -> list[dict]:
    found: list[dict] = []
    for path in sorted(glob.glob(os.path.join(report_dir, "candidates", "*.json"))):
        data = read_json(path)
        if isinstance(data, list):
            found.extend(c for c in data if isinstance(c, dict))
    return found


def revision_of(report_dir: str) -> dict | None:
    """The run's REVISION stamp, or the inventory's head/dirty when no stamp was written."""
    revisions = sorted(glob.glob(os.path.join(report_dir, "REVISION-*.json")))
    if revisions:
        return read_json(revisions[-1])
    inventory = read_json(os.path.join(report_dir, "inventory.json"))
    if inventory and "head" in inventory:
        return {"head": inventory.get("head"), "dirty": inventory.get("dirty"), "scope": "(no REVISION stamp)"}
    return None


def read_json(path: str) -> dict | list | None:
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
        with open(findings_path, encoding="utf-8") as fh:
            findings, problems = load_findings(fh.read())
    if problems:
        print(f"audit-report: findings.jsonl violates the schema — {len(problems)} problem(s):")
        for p in problems:
            print(f"  {p}")
        return 1
    # Candidates the verifier never turned into a record are still findings — unverified ones.
    seen = {rec["id"] for rec in findings}
    synthesized = [rec for rec in candidates_as_unverified(load_candidates(args.dir)) if rec["id"] not in seen]
    findings += synthesized
    text = render(findings, read_json(os.path.join(args.dir, "facts.json")),
                  read_json(os.path.join(args.dir, "probes.json")),
                  revision_of(args.dir))
    with open(os.path.join(args.dir, "REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    note = f" ({len(synthesized)} candidate(s) without a verifier record rendered unverified)" if synthesized else ""
    print(f"audit-report: {len(findings)} finding(s){note} -> {os.path.join(args.dir, 'REPORT.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
