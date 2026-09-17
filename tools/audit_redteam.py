#!/usr/bin/env python3
"""Red-team probes for /ccgg-audit — which content channels reach the model.

For each line in tools/redteam_probes.txt this script plants a marker in a scratch
copy of the tree at HEAD and, for `exec` probes, runs the observation command and
searches its stdout for the marker: a hit means content an outsider could place
there reaches what the model sees. `static` probes are planted and described, for
the red-team specialist's judgment and the verifier's inspection.

    python3 tools/audit_redteam.py --out CCGG-AUDIT-<stamp>/

Writes redteam.json. Exit 0 when the stage ran; the verdict belongs to the report.
The scratch copy gets its own HOME so probes that touch ~/.claude never reach the
real one. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audit_env  # noqa: E402  (same directory, installed together)
import tempfile
import time
from dataclasses import asdict, dataclass

DEFAULT_PROBES = os.path.join("tools", "redteam_probes.txt")
KINDS = ("exec", "static")
SKIP_EXIT = 3


@dataclass(frozen=True)
class RedteamProbe:
    channel: str
    kind: str
    plant: str
    observe: str
    line: int


@dataclass
class RedteamResult:
    channel: str
    kind: str
    result: str  # reached | contained | planted | skipped | error
    detail: str
    line: int


class RedteamFileError(ValueError):
    """A probes file line that cannot be run; the line number is in the message."""


def parse_redteam_probes(text: str) -> list[RedteamProbe]:
    """Parse `channel | kind | plant | observe`; `#` comments and blank lines skipped."""
    if not isinstance(text, str):
        raise TypeError("probes text must be a string")
    probes: list[RedteamProbe] = []
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|", 3)
        if len(parts) != 4:
            raise RedteamFileError(f"line {no}: expected 'channel | kind | plant | observe', got: {raw.strip()[:60]}")
        channel, kind, plant, observe = (p.strip() for p in parts)
        if not channel:
            raise RedteamFileError(f"line {no}: empty channel")
        if kind not in KINDS:
            raise RedteamFileError(f"line {no}: kind must be one of {KINDS}, got '{kind}'")
        if not plant or not observe:
            raise RedteamFileError(f"line {no}: plant and observe are both required")
        probes.append(RedteamProbe(channel, kind, plant, observe, no))
    return probes


def marker_for(probe: RedteamProbe) -> str:
    return f"CCGG-REDTEAM-{probe.line:03d}"


def summarize(results: list[RedteamResult]) -> dict:
    counts = {k: sum(1 for r in results if r.result == k) for k in ("reached", "contained", "planted", "skipped", "error")}
    counts["total"] = len(results)
    counts["reached_channels"] = [r.channel for r in results if r.result == "reached"]
    counts["error_channels"] = [r.channel for r in results if r.result == "error"]
    return counts


def _run(cmd: list[str], cwd: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)


def make_scratch_copy(repo: str, scratch: str) -> tuple[str, dict]:
    """HEAD unpacked and committed once, with a private HOME beside it."""
    dest = os.path.join(scratch, "repo")
    home = os.path.join(scratch, "home")
    os.makedirs(dest)
    os.makedirs(home)
    archive = subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["tar", "-xf", "-", "-C", dest], input=archive.stdout, check=True)
    # An allow-list, not os.environ minus the three names somebody thought of.
    # A plant and an observe are shell snippets from a committed data file in the
    # audited tree; under dict(os.environ, ...) they ran with the operator's
    # ANTHROPIC_API_KEY, GITHUB_TOKEN and cloud credentials (finding S-004).
    env = audit_env.sandbox_env(home, actor="redteam")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "baseline"]):
        proc = _run(cmd, dest, env)
        if proc.returncode != 0:
            raise RuntimeError(f"scratch setup failed at {' '.join(cmd)}: {proc.stderr.strip()}")
    return dest, env


def run_probe(probe: RedteamProbe, scratch_repo: str, env: dict) -> RedteamResult:
    marker = marker_for(probe)
    penv = dict(env, MARKER=marker)
    for cmd in (["git", "reset", "-q", "--hard", "HEAD"], ["git", "clean", "-fdq"]):
        if _run(cmd, scratch_repo, penv).returncode != 0:
            return RedteamResult(probe.channel, probe.kind, "error", "reset failed", probe.line)
    home = penv["HOME"]
    for entry in os.listdir(home):  # a private HOME is reset with the tree
        subprocess.run(["rm", "-rf", os.path.join(home, entry)], check=False)
    planted = _run(["bash", "-c", probe.plant], scratch_repo, penv)
    if planted.returncode == SKIP_EXIT:
        return RedteamResult(probe.channel, probe.kind, "skipped", "plant reported not applicable (exit 3)", probe.line)
    if planted.returncode != 0:
        return RedteamResult(probe.channel, probe.kind, "error", f"plant exited {planted.returncode}: {planted.stderr.strip()[:200]}", probe.line)
    if probe.kind == "static":
        return RedteamResult(probe.channel, probe.kind, "planted", f"marker {marker} planted; loads via: {probe.observe}", probe.line)
    observed = _run(["bash", "-c", probe.observe], scratch_repo, penv)
    if observed.returncode == SKIP_EXIT:
        return RedteamResult(probe.channel, probe.kind, "skipped", "observe reported not applicable (exit 3)", probe.line)
    if marker in observed.stdout:
        hit = next(ln.strip() for ln in observed.stdout.splitlines() if marker in ln)
        return RedteamResult(probe.channel, probe.kind, "reached", f"marker in stdout: {hit[:160]}", probe.line)
    return RedteamResult(probe.channel, probe.kind, "contained", f"marker absent from stdout ({len(observed.stdout)} bytes)", probe.line)


def format_table(results: list[RedteamResult], summary: dict) -> str:
    width = max((len(r.channel) for r in results), default=10)
    lines = [f"{r.result.upper():10} {r.channel.ljust(width)}  {r.detail[:70]}" for r in results]
    lines.append("")
    lines.append(f"channels: {summary['total']} — {summary['reached']} reached the model, {summary['contained']} contained, "
                 f"{summary['planted']} planted for judgment, {summary['skipped']} skipped, {summary['error']} error(s)")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=None)
    parser.add_argument("--probes", default=DEFAULT_PROBES)
    parser.add_argument("--out", default=None, help="directory to write redteam.json into")
    args = parser.parse_args(argv)
    repo = args.repo or subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True, encoding="utf-8").strip()
    probes_path = os.path.join(repo, args.probes)
    if not os.path.isfile(probes_path):
        print(f"audit-redteam: no probes file at {args.probes} — nothing to measure")
        return 0
    try:
        probes = parse_redteam_probes(open(probes_path, encoding="utf-8").read())
    except RedteamFileError as exc:
        print(f"audit-redteam: {args.probes}: {exc}")
        return 1
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="ccgg-redteam-") as scratch:
        scratch_repo, env = make_scratch_copy(repo, scratch)
        results = [run_probe(p, scratch_repo, env) for p in probes]
    summary = summarize(results)
    summary["duration_s"] = round(time.time() - started, 1)
    print(format_table(results, summary))
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "redteam.json"), "w", encoding="utf-8") as fh:
            json.dump({"summary": summary, "probes": [asdict(r) for r in results]}, fh, indent=2)
            fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
