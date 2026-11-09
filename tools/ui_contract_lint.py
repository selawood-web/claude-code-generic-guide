#!/usr/bin/env python3
"""Lint a UI contract — the one file that says what a user can do, where, and why.

A UI contract (schema: .claude/skills/ui-contract/contract-schema.md) lists the
places a user can be (contexts), the boards those places belong to, the output
profile of each board, the surfaces that hold controls, and every command with
its one home and its state in every context. This script checks the contract
against the rules that keep an interface learnable:

  one command, one meaning   a command's behaviour is one sentence, everywhere
  one home                   every command has exactly one canonical surface;
                             any other entry point must say why it exists
  only what is relevant      every command x context has a resolved state —
                             enabled, disabled with a reason, or hidden
  same logic, other output   every board renders the same model; boards differ
                             only in their profile's values, never its keys

Usage:
  python3 tools/ui_contract_lint.py <contract.json>            findings, exit 1 on errors
  python3 tools/ui_contract_lint.py <contract.json> --strict   warnings fail too
  python3 tools/ui_contract_lint.py <contract.json> --matrix   print the context x command matrix

Standard library only, so it runs in any project's CI without an install step.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from dataclasses import dataclass

STATES = ("enabled", "disabled", "hidden")
PROFILE_LAYER_VALUES = ("show", "ghost", "hide")
PROFILE_MEASURE_VALUES = ("show", "hide")
DEFAULT_MAX_ENABLED = 12
MAX_EXTRA_ENTRIES = 2


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str  # "error" or "warning"
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.severity.upper():7} {self.code} {self.where}: {self.message}"


@dataclass(frozen=True)
class State:
    kind: str  # one of STATES
    reason: str = ""


def _matches(pattern: str, context: str) -> bool:
    return fnmatch.fnmatchcase(context, pattern)


def _patterns_hit(patterns, contexts) -> dict[str, list[str]]:
    return {p: [c for c in contexts if _matches(p, c)] for p in patterns}


def _is_text(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


class Contract:
    """A parsed contract plus the findings its structure produced."""

    def __init__(self, data):
        self.findings: list[Finding] = []
        if not isinstance(data, dict):
            self._err("UC01", "contract", "top level must be a JSON object")
            data = {}
        self.data = data
        self.policy = data.get("policy") if isinstance(data.get("policy"), dict) else {}
        self.model = self._section("model")
        self.boards = self._section("boards")
        self.contexts = self._section("contexts")
        self.surfaces = self._section("surfaces")
        self.commands = self._section("commands")

    def _err(self, code: str, where: str, message: str) -> None:
        self.findings.append(Finding(code, "error", where, message))

    def _warn(self, code: str, where: str, message: str) -> None:
        self.findings.append(Finding(code, "warning", where, message))

    def _section(self, name: str) -> dict:
        value = self.data.get(name)
        if not isinstance(value, dict) or not value:
            self._err("UC01", name, "missing or empty — it must be a non-empty object")
            return {}
        return value

    # -- state resolution -------------------------------------------------

    def off_context(self) -> str:
        value = self.policy.get("off_context", "disabled")
        return value if value in ("disabled", "hidden") else "disabled"

    def boards_enabled(self, cmd: dict) -> list[str]:
        boards = []
        for ctx in self.contexts:
            if any(_matches(p, ctx) for p in _list(cmd.get("enabled"))):
                board = self.contexts[ctx].get("board") if isinstance(self.contexts[ctx], dict) else None
                if board and board not in boards:
                    boards.append(board)
        return boards

    def state(self, cmd: dict, context: str) -> State:
        """The one state a command has in a context. Enabled wins only when unambiguous;
        ambiguity is reported by check_commands, not resolved silently here."""
        if any(_matches(p, context) for p in _list(cmd.get("enabled"))):
            return State("enabled")
        disabled = cmd.get("disabled") if isinstance(cmd.get("disabled"), dict) else {}
        for pattern, reason in disabled.items():
            if _matches(pattern, context):
                return State("disabled", reason if isinstance(reason, str) else "")
        if any(_matches(p, context) for p in _list(cmd.get("hidden"))):
            return State("hidden")
        if self.off_context() == "hidden":
            return State("hidden")
        labels = [self._board_label(b) for b in self.boards_enabled(cmd)]
        reason = f"Available in {', '.join(labels)}" if labels else ""
        return State("disabled", reason)

    def _board_label(self, board: str) -> str:
        b = self.boards.get(board)
        return b.get("label", board) if isinstance(b, dict) else board

    def surfaces_in(self, context: str) -> set[str]:
        return {
            name for name, s in self.surfaces.items()
            if isinstance(s, dict) and any(_matches(p, context) for p in _list(s.get("contexts")))
        }


def _list(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


# -- checks -----------------------------------------------------------------

def check_policy(c: Contract) -> None:
    off = c.policy.get("off_context", "disabled")
    if off not in ("disabled", "hidden"):
        c._err("UC01", "policy.off_context", f"'{off}' is not 'disabled' or 'hidden'")
    cap = c.policy.get("max_enabled_per_context", DEFAULT_MAX_ENABLED)
    if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1:
        c._err("UC01", "policy.max_enabled_per_context", "must be a positive integer")


def check_boards(c: Contract) -> None:
    """Same logic, other output: a profile may change values, never which keys exist."""
    layers = _list(c.model.get("layers"))
    measures = _list(c.model.get("measurements"))
    if c.model and (not layers or not measures):
        c._err("UC01", "model", "must list 'layers' and 'measurements' — the one model every board renders")
    for name, board in c.boards.items():
        where = f"boards.{name}"
        if not isinstance(board, dict):
            c._err("UC01", where, "must be an object")
            continue
        if not _is_text(board.get("purpose")):
            c._err("UC02", where, "has no 'purpose' — one sentence on what a user comes to this board to produce")
        profile = board.get("profile")
        if not isinstance(profile, dict):
            c._err("UC03", where, "has no 'profile' — a board is an output lens over the shared model")
            continue
        for key, expected, allowed in (("layers", layers, PROFILE_LAYER_VALUES),
                                       ("measurements", measures, PROFILE_MEASURE_VALUES)):
            got = profile.get(key) if isinstance(profile.get(key), dict) else {}
            missing = [k for k in expected if k not in got]
            extra = [k for k in got if k not in expected]
            if missing:
                c._err("UC03", f"{where}.profile.{key}", f"does not say how to render {missing} — every board renders every {key[:-1]} of the model")
            if extra:
                c._err("UC03", f"{where}.profile.{key}", f"invents {extra}, not in the model — a board may change how a {key[:-1]} shows, not which exist")
            bad = [k for k, v in got.items() if v not in allowed]
            if bad:
                c._err("UC01", f"{where}.profile.{key}", f"{bad} must be one of {list(allowed)}")
        if not _is_text(profile.get("output")):
            c._err("UC03", f"{where}.profile", "has no 'output' — name the deliverable this board produces")


def check_contexts(c: Contract) -> None:
    for name, ctx in c.contexts.items():
        where = f"contexts.{name}"
        if not isinstance(ctx, dict):
            c._err("UC01", where, "must be an object")
            continue
        if ctx.get("board") not in c.boards:
            c._err("UC02", where, f"names board '{ctx.get('board')}', which is not declared")
        if not _is_text(ctx.get("label")):
            c._err("UC01", where, "has no 'label' — what the user sees that tells them they are here")


def check_surfaces(c: Contract) -> None:
    for name, s in c.surfaces.items():
        where = f"surfaces.{name}"
        if not isinstance(s, dict):
            c._err("UC01", where, "must be an object")
            continue
        for pattern, hits in _patterns_hit(_list(s.get("contexts")), c.contexts).items():
            if not hits:
                c._err("UC08", f"{where}.contexts", f"pattern '{pattern}' matches no context")
        if not _list(s.get("contexts")):
            c._err("UC08", where, "appears in no context")


def check_commands(c: Contract) -> None:
    labels: dict[str, str] = {}
    for name, cmd in c.commands.items():
        where = f"commands.{name}"
        if not isinstance(cmd, dict):
            c._err("UC01", where, "must be an object")
            continue
        label = cmd.get("label")
        if not _is_text(label):
            c._err("UC01", where, "has no 'label'")
        else:
            key = label.strip().lower()
            if key in labels:
                c._err("UC05", where, f"label '{label}' is also used by {labels[key]} — one name, one command")
            labels.setdefault(key, name)

        does = cmd.get("does")
        if isinstance(does, dict):
            c._err("UC14", f"{where}.does", "varies by board — split it into separate commands with separate names, "
                   "or move the difference into the boards' profiles")
        elif not _is_text(does):
            c._err("UC01", where, "has no 'does' — one sentence, true in every context")

        home = cmd.get("home")
        if home not in c.surfaces:
            c._err("UC04", f"{where}.home", f"'{home}' is not a declared surface — every command has exactly one home")
        seen = {home}
        extras = _list(cmd.get("also"))
        for i, entry in enumerate(extras):
            ewhere = f"{where}.also[{i}]"
            if not isinstance(entry, dict):
                c._err("UC04", ewhere, "must be an object with 'surface' and 'why'")
                continue
            surface = entry.get("surface")
            if surface not in c.surfaces:
                c._err("UC04", ewhere, f"'{surface}' is not a declared surface")
            if surface in seen:
                c._err("UC04", ewhere, f"'{surface}' is already an entry point of this command")
            seen.add(surface)
            if not _is_text(entry.get("why")):
                c._err("UC04", ewhere, "has no 'why' — a second way in must say what the home cannot do")
        if len(extras) > MAX_EXTRA_ENTRIES:
            c._warn("UC11", where, f"has {len(extras) + 1} entry points — past {MAX_EXTRA_ENTRIES + 1}, users stop knowing where it lives")

        all_patterns = _list(cmd.get("enabled")) + list((cmd.get("disabled") or {}).keys()) + _list(cmd.get("hidden"))
        for pattern, hits in _patterns_hit(all_patterns, c.contexts).items():
            if not hits:
                c._err("UC08", where, f"pattern '{pattern}' matches no context")
        disabled = cmd.get("disabled") if isinstance(cmd.get("disabled"), dict) else {}
        for pattern, reason in disabled.items():
            if not _is_text(reason):
                c._err("UC12", f"{where}.disabled", f"'{pattern}' has no reason — a grey control must say how to make it work")

        enabled_in = []
        for ctx in c.contexts:
            claims = [k for k, pats in (("enabled", _list(cmd.get("enabled"))),
                                        ("disabled", list(disabled.keys())),
                                        ("hidden", _list(cmd.get("hidden"))))
                      if any(_matches(p, ctx) for p in pats)]
            if len(claims) > 1:
                c._err("UC13", where, f"is both {' and '.join(claims)} in '{ctx}' — one context, one state")
            ctx_board = c.contexts[ctx].get("board") if isinstance(c.contexts[ctx], dict) else None
            if not claims and ctx_board in c.boards_enabled(cmd):
                c._err("UC12", where, f"has no declared state in '{ctx}', inside its own board — "
                       "say whether it is enabled, or disabled with the reason")
            if c.state(cmd, ctx).kind == "enabled":
                enabled_in.append(ctx)
                entry_points = {home, *(e.get("surface") for e in extras if isinstance(e, dict))}
                if not entry_points & c.surfaces_in(ctx):
                    c._err("UC07", where, f"is enabled in '{ctx}' but none of its surfaces appear there — unreachable")
        if not enabled_in:
            c._err("UC08", where, "is enabled in no context — dead command")


def check_shortcuts(c: Contract) -> None:
    owners: dict[str, list[str]] = {}
    for name, cmd in c.commands.items():
        if isinstance(cmd, dict) and _is_text(cmd.get("shortcut")):
            owners.setdefault(cmd["shortcut"].strip().lower(), []).append(name)
    for key, names in owners.items():
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                shared = [ctx for ctx in c.contexts
                          if c.state(c.commands[a], ctx).kind == "enabled"
                          and c.state(c.commands[b], ctx).kind == "enabled"]
                if shared:
                    c._err("UC06", f"commands.{a}", f"shortcut '{key}' also triggers {b} in {shared}")


def check_load(c: Contract) -> None:
    cap = c.policy.get("max_enabled_per_context", DEFAULT_MAX_ENABLED)
    if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1:
        cap = DEFAULT_MAX_ENABLED
    for ctx in c.contexts:
        n = sum(1 for cmd in c.commands.values() if isinstance(cmd, dict) and c.state(cmd, ctx).kind == "enabled")
        if n == 0:
            c._warn("UC09", f"contexts.{ctx}", "no command is enabled — a dead end with no way forward")
        elif n > cap:
            c._warn("UC10", f"contexts.{ctx}", f"{n} commands enabled, over the budget of {cap} — split the context or demote commands")


def lint(data) -> list[Finding]:
    c = Contract(data)
    check_policy(c)
    check_boards(c)
    check_contexts(c)
    check_surfaces(c)
    check_commands(c)
    check_shortcuts(c)
    check_load(c)
    return c.findings


SYMBOLS = {"enabled": "●", "disabled": "○", "hidden": "·"}


def matrix(data) -> str:
    """Commands as rows, contexts as columns: ● enabled, ○ disabled, · hidden."""
    c = Contract(data)
    ctxs = list(c.contexts)
    lines = ["| command | " + " | ".join(ctxs) + " |", "|---|" + "---|" * len(ctxs)]
    for name, cmd in c.commands.items():
        if not isinstance(cmd, dict):
            continue
        cells = [SYMBOLS[c.state(cmd, ctx).kind] for ctx in ctxs]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    totals = [str(sum(1 for cmd in c.commands.values() if isinstance(cmd, dict)
                      and c.state(cmd, ctx).kind == "enabled")) for ctx in ctxs]
    lines.append("| **enabled** | " + " | ".join(totals) + " |")
    lines.append("\n● enabled · ○ disabled (reason shown to the user) · · hidden")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("contract")
    ap.add_argument("--strict", action="store_true", help="warnings fail the run too")
    ap.add_argument("--matrix", action="store_true", help="print the context x command matrix")
    args = ap.parse_args(argv)
    try:
        with open(args.contract, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ui-contract: cannot read {args.contract}: {exc}", file=sys.stderr)
        return 2
    findings = lint(data)
    for f in findings:
        print(f)
    if args.matrix:
        print(matrix(data))
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = len(findings) - errors
    print(f"ui-contract: {errors} error(s), {warnings} warning(s)")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
