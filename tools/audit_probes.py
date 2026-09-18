#!/usr/bin/env python3
"""Mutation probes against the repository's gate — measure what it does not see.

For each line in tools/probes.txt this script plants the described defect in a
scratch copy of the tree at HEAD, runs the gate, and records whether the gate
fired. The result is a catch rate and, in CI, a failure whenever a probe the
list marks `caught` is missed: the gate's guarantees become tests of the gate.

    python3 tools/audit_probes.py                       # print the table
    python3 tools/audit_probes.py --out CCGG-AUDIT-x/   # also write probes.json
    python3 tools/audit_probes.py --gate "python3 tools/validate.py"

The scratch copy is `git archive HEAD` unpacked into a temporary directory and
committed once, so a hard reset between probes is provably complete and the
harness works from a shallow CI checkout. Uncommitted changes are not probed.
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audit_env  # noqa: E402  (same directory, installed together)
import tempfile
import time
from dataclasses import asdict, dataclass

DEFAULT_GATE = "python3 tools/validate.py"
DEFAULT_GATE_NAME = "validator"
# Gates by name, never by command. A probe row may say which gate has to catch
# it, because the validator is not the whole gate: the verifier's guard is ~450
# lines of security decisions whose only enforcement is a unit table, so before
# this map no mutation of the guard could be measured at all — every probe
# written for one read `missed` against a validator that never looks at it
# (finding S-003's leftover). The names resolve here and nowhere else: probes.txt
# is a data file this harness already executes as shell, and a free-form gate
# command in it would be a second way out of the same file.
GATES = {
    DEFAULT_GATE_NAME: DEFAULT_GATE,
    "guard": "python3 -m unittest discover -s tools -t tools -p test_verifier_guard.py -q",
    "hooks": "python3 -m unittest discover -s tools -t tools -p test_session_start_hook.py -q",
    # The deterministic fact stage's own tests, which run collect() on the tree
    # and assert each surface still produces its fact: a surface nobody
    # inventories is one the audit reports nothing about, which reads exactly
    # like a clean one. --fail-on-findings is not this gate: it fails on the
    # gating kinds only, and an inventory fact is for review, not a verdict.
    "facts": "python3 -m unittest discover -s tools -t tools -p test_audit_facts.py -q",
}
DEFAULT_PROBES = os.path.join("tools", "probes.txt")
EXPECTATIONS = ("caught", "missed")
RESULTS = ("caught", "missed", "skipped", "error")
SKIP_EXIT = 3  # a mutation exits 3 to say "not applicable in this repository"


@dataclass(frozen=True)
class Probe:
    label: str
    expect: str
    mutation: str
    line: int
    gate: str = DEFAULT_GATE_NAME


@dataclass
class ProbeResult:
    label: str
    expect: str
    result: str
    detail: str
    line: int
    gate: str = DEFAULT_GATE_NAME


class ProbeFileError(ValueError):
    """A probes file line that cannot be run; the line number is in the message."""


def parse_probes(text: str) -> list[Probe]:
    """Parse the probes file: `label | expect | mutation`, `#` comments, blank lines.

    `expect` is `caught` or `missed`, optionally followed by `:<gate>` naming which
    gate must catch the defect — `caught:guard` for a mutation only the verifier
    guard's unit table sees. The gate name has to be in GATES; an unknown one is a
    parse error, because a probe that names a gate nobody runs measures nothing and
    would report as a clean `missed`.

    Raises ProbeFileError on the first malformed line — a probe that cannot be
    parsed must not silently vanish from the contract.
    """
    if not isinstance(text, str):
        raise TypeError("probes text must be a string")
    probes: list[Probe] = []
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            raise ProbeFileError(f"line {no}: expected 'label | expect | mutation', got: {raw.strip()[:60]}")
        label, expect, mutation = (p.strip() for p in parts)
        if not label:
            raise ProbeFileError(f"line {no}: empty label")
        verdict, sep, gate = expect.partition(":")
        verdict, gate = verdict.strip(), gate.strip()
        if sep and not gate:
            raise ProbeFileError(f"line {no}: '{expect}' names no gate after the colon")
        gate = gate or DEFAULT_GATE_NAME
        if verdict not in EXPECTATIONS:
            raise ProbeFileError(f"line {no}: expect must be one of {EXPECTATIONS}, got '{verdict}'")
        if gate not in GATES:
            raise ProbeFileError(f"line {no}: unknown gate '{gate}'; known gates are {sorted(GATES)}")
        if not mutation:
            raise ProbeFileError(f"line {no}: empty mutation")
        # The label is committed, contributor-editable text that lands in
        # probes.json and from there in a specialist's input (finding R-007).
        probes.append(Probe(audit_env.quote(label), verdict, mutation, no, gate))
    return probes


def summarize(results: list[ProbeResult]) -> dict:
    """Counts plus the two lists that matter: regressions and promotions.

    Skipped probes (mutation exit 3, not applicable here) are outside the rate.

    A regression is a probe expected `caught` that was missed — the gate lost a
    guarantee. A promotion is a probe expected `missed` that was caught — a check
    landed and the list should say so. Errors are probes whose mutation failed.
    """
    caught = [r for r in results if r.result == "caught"]
    missed = [r for r in results if r.result == "missed"]
    skipped = [r for r in results if r.result == "skipped"]
    errors = [r for r in results if r.result == "error"]
    regressions = [r for r in results if r.expect == "caught" and r.result == "missed"]
    promotions = [r for r in results if r.expect == "missed" and r.result == "caught"]
    total = len(caught) + len(missed)  # skipped probes measure nothing
    return {
        "total": total,
        "caught": len(caught),
        "missed": len(missed),
        "skipped": len(skipped),
        "errors": len(errors),
        "catch_rate": (len(caught) / total) if total else 0.0,
        "regressions": [r.label for r in regressions],
        "promotions": [r.label for r in promotions],
        "error_labels": [r.label for r in errors],
        "gates": sorted({r.gate for r in results}),
    }


def _run(cmd: list[str], cwd: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)


def probe_env(scratch: str) -> dict[str, str]:
    """The environment a mutation and the gate run under: minimal, with a private HOME.

    A mutation is a shell snippet from a committed data file, so it gets the
    allow-list in tools/audit_env.py and nothing else — not the operator's
    tokens, not the CCGG_* variables that would let it sync from the operator's
    guide clone. That rule has one home now; this was where it was written first.
    """
    home = os.path.join(scratch, "home")
    os.makedirs(home, exist_ok=True)
    return audit_env.sandbox_env(home, actor="probes")


def make_scratch_copy(repo: str, scratch: str) -> tuple[str, dict[str, str]]:
    """Unpack HEAD into scratch/repo, commit it once as the baseline, return (path, env)."""
    dest = os.path.join(scratch, "repo")
    os.makedirs(dest)
    archive = subprocess.run(
        ["git", "archive", "--format=tar", "HEAD"], cwd=repo, capture_output=True, check=True
    )
    subprocess.run(["tar", "-xf", "-", "-C", dest], input=archive.stdout, check=True)
    env = probe_env(scratch)
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "baseline"]):
        proc = _run(cmd, dest, env)
        if proc.returncode != 0:
            raise RuntimeError(f"scratch setup failed at {' '.join(cmd)}: {proc.stderr.strip()}")
    return dest, env


def run_probe(probe: Probe, scratch_repo: str, gates: dict[str, list[str]],
              env: dict[str, str]) -> ProbeResult:
    """Reset, mutate, stage, run the probe's gate. Never raises on a bad mutation — it records `error`."""
    def result(verdict: str, detail: str) -> ProbeResult:
        # detail is the gate's own output, which quotes file content back.
        return ProbeResult(probe.label, probe.expect, verdict, audit_env.quote(detail),
                           probe.line, probe.gate)

    for cmd in (["git", "reset", "-q", "--hard", "HEAD"], ["git", "clean", "-fdq"]):
        proc = _run(cmd, scratch_repo, env)
        if proc.returncode != 0:
            return result("error", f"reset failed: {proc.stderr.strip()}")
    if not probe.mutation.strip():
        return result("error", "empty mutation plants nothing")
    gate = gates.get(probe.gate)
    if not gate:
        return result("error", f"no command for gate '{probe.gate}'")
    mutated = _run(["bash", "-c", probe.mutation], scratch_repo, env)
    if mutated.returncode == SKIP_EXIT:
        return result("skipped", "mutation reported not applicable (exit 3)")
    if mutated.returncode != 0:
        return result("error", f"mutation exited {mutated.returncode}: {mutated.stderr.strip()[:200]}")
    _run(["git", "add", "-A"], scratch_repo, env)
    # A mutation that changed nothing is not a blind spot, it is a broken probe —
    # a sed whose pattern stopped matching plants no defect, the gate passes, and
    # the row reads `missed` as if the gate had a hole. Two of the first guard
    # probes written failed exactly this way, so the harness says so itself.
    if _run(["git", "diff", "--cached", "--quiet", "HEAD"], scratch_repo, env).returncode == 0:
        return result("error", "mutation left the tree unchanged — it plants nothing to catch")
    gated = _run(gate, scratch_repo, env)
    if gated.returncode == 0:
        return result("missed", "gate exited 0")
    # The validator prints its findings indented; a test runner prints to stderr.
    # Either way the detail is the first line that says something.
    first = next((ln.strip() for ln in gated.stdout.splitlines() if ln.startswith("  ")), "")
    if not first:
        first = next((ln.strip() for ln in gated.stderr.splitlines()
                      if ln.strip() and not ln.startswith("-")), "")
    return result("caught", first[:200])


def format_table(results: list[ProbeResult], summary: dict) -> str:
    width = max((len(r.label) for r in results), default=10)
    # The gate column appears only when more than one gate ran: which gate caught
    # a defect is the thing worth reading once the answer is not always the same.
    gates = summary.get("gates") or [DEFAULT_GATE_NAME]
    gate_width = max(len(g) for g in gates) if len(gates) > 1 else 0
    lines = []
    for r in results:
        flag = ""
        if r.label in summary["regressions"]:
            flag = "  <- REGRESSION (expected caught)"
        elif r.label in summary["promotions"]:
            flag = "  <- promote to caught"
        elif r.result == "error":
            flag = f"  <- {r.detail}"
        gate_col = f"{r.gate.ljust(gate_width)}  " if gate_width else ""
        lines.append(f"{r.result.upper():7} {gate_col}{r.label.ljust(width)}{flag}")
    lines.append("")
    across = f" across {len(gates)} gates" if len(gates) > 1 else ""
    lines.append(
        f"catch rate: {summary['caught']}/{summary['total']} ({summary['catch_rate']:.0%}){across} — "
        f"{len(summary['regressions'])} regression(s), {len(summary['promotions'])} promotion(s), "
        f"{summary['skipped']} skipped, {summary['errors']} error(s)"
    )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=None, help="repository root (default: the current git toplevel)")
    parser.add_argument("--probes", default=DEFAULT_PROBES, help="probes file, relative to the repo")
    parser.add_argument("--gate", default=DEFAULT_GATE,
                        help="command for the default gate; probes naming another gate are unaffected")
    parser.add_argument("--out", default=None, help="directory to write probes.json into")
    args = parser.parse_args(argv)

    repo = args.repo or subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, encoding="utf-8"
    ).strip()
    probes_path = os.path.join(repo, args.probes)
    if not os.path.isfile(probes_path):
        # Not "nothing to measure, all clear": a harness pointed at a file that
        # is not there measured the gate's whole contract as zero probes, and a
        # mistyped --probes path was a silent success in CI (finding T-001).
        print(f"audit-probes: no probes file at {args.probes} — the gate's contract is unmeasured")
        return 1
    try:
        with open(probes_path, encoding="utf-8") as fh:
            probes = parse_probes(fh.read())
    except ProbeFileError as exc:
        print(f"audit-probes: {args.probes}: {exc}")
        return 1
    if not probes:
        print(f"audit-probes: {args.probes} lists no probes — the gate's contract is unmeasured")
        return 1

    gates = {name: shlex.split(cmd) for name, cmd in GATES.items()}
    gates[DEFAULT_GATE_NAME] = shlex.split(args.gate)
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="ccgg-probes-") as scratch:
        scratch_repo, env = make_scratch_copy(repo, scratch)
        results = [run_probe(p, scratch_repo, gates, env) for p in probes]
    summary = summarize(results)
    summary["gate"] = args.gate
    summary["gate_commands"] = {name: " ".join(cmd) for name, cmd in gates.items()
                                if name in summary["gates"]}
    summary["duration_s"] = round(time.time() - started, 1)

    print(format_table(results, summary))
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "probes.json"), "w", encoding="utf-8") as fh:
            json.dump({"summary": summary, "probes": [asdict(r) for r in results]}, fh, indent=2)
            fh.write("\n")
    if summary["regressions"] or summary["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
