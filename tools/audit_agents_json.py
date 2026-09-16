#!/usr/bin/env python3
"""Serialize .claude/agents/audit-*.md into the inline JSON a headless run needs.

A headless audit runs with project settings excluded, so the audited checkout's
agent files are never loaded. The agents arrive on the command line instead, and
this script builds them from the very same files an interactive run uses — one
set of briefs, two ways of running.

    python3 tools/audit_agents_json.py                    # JSON on stdout
    python3 tools/audit_agents_json.py --check            # parse only, exit 1 on drift
    python3 tools/audit_agents_json.py --guard /tmp/g.sh  # verifier guard from a trusted path
    python3 tools/audit_agents_json.py --only audit-harness,audit-verifier

Every frontmatter key must be one this script knows how to carry. An unknown key
is an error, not a silent drop: a field that exists in the file and vanishes on
the way to CI is the documented-but-dead defect this repository audits for.

The guard path matters. The verifier's hook runs a script, and in the file that
script is named relative to the audited checkout. When the checkout is one the
operator did not write — the case headless mode exists for — the audited tree
must not supply the guard that constrains the agent reading it. `--guard` points
the hook at a copy the caller controls, outside the tree.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

DEFAULT_DIR = os.path.join(".claude", "agents")
DEFAULT_GLOB = "audit-*.md"
# Frontmatter key -> key in the emitted JSON. Everything the agent files may say.
# `name` is the key of the emitted object, not a field inside it: the CLI's inline
# agent JSON is {name: definition}, and it validates the definition's fields at
# startup, so a field it does not know is a failed run.
SCALAR_KEYS = {
    "description": "description",
    "model": "model",
    "isolation": "isolation",
}
NAME_KEY = "name"
LIST_KEYS = {"tools": "tools", "disallowedTools": "disallowedTools"}
INT_KEYS = {"maxTurns": "maxTurns"}
BOOL_KEYS = {"omitClaudeMd": "omitClaudeMd"}
BLOCK_KEYS = {"hooks": "hooks"}
KNOWN_KEYS = ({NAME_KEY} | set(SCALAR_KEYS) | set(LIST_KEYS) | set(INT_KEYS)
              | set(BOOL_KEYS) | set(BLOCK_KEYS))
GUARD_HOOK_RE = re.compile(r"\.claude/hooks/[A-Za-z0-9._-]+\.sh")


class AgentFileError(Exception):
    """A definition this script will not guess at."""


def split_frontmatter(text: str) -> tuple[list[str], str]:
    """(frontmatter lines, body). Raises when the block is missing or unclosed."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise AgentFileError("frontmatter must start with --- on line 1")
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        raise AgentFileError("frontmatter never closed with ---") from None
    return lines[1:end], "\n".join(lines[end + 1:]).strip()


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _scalar(value: str):
    """A YAML scalar in the subset these files use: quoted string, bool, int, or string.

    A double-quoted scalar carries escapes — the verifier's hook command is
    `"\\"$CLAUDE_PROJECT_DIR\\"/.claude/..."` in the file and must reach the JSON
    as the shell sees it, quotes and all.
    """
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        if value[0] == '"':
            return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), inner)
        return inner
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def parse_block(lines: list[str], start: int, indent: int):
    """Parse the indented YAML subset used by agent frontmatter.

    Handles mappings, sequences of mappings, and scalars — the shape the hooks
    block takes and nothing more. Returns (value, index after the block).
    """
    items: list = []
    mapping: dict = {}
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        here = _indent(line)
        if here < indent:
            break
        if here > indent:
            raise AgentFileError(f"line {i + 1}: unexpected indentation")
        stripped = line.strip()
        if stripped.startswith("- "):
            entry = stripped[2:]
            key, sep, value = entry.partition(":")
            if not sep:
                items.append(_scalar(entry))
                i += 1
                continue
            # A sequence entry that opens a mapping: its siblings are indented to
            # the first key's column, two past the dash.
            item: dict = {}
            inner_indent = here + 2
            if value.strip():
                item[key.strip()] = _scalar(value)
                i += 1
            else:
                nested, i = parse_block(lines, i + 1, inner_indent + 2)
                item[key.strip()] = nested
            rest, i = parse_block(lines, i, inner_indent)
            if isinstance(rest, dict):
                item.update(rest)
            elif rest:
                raise AgentFileError(f"line {i}: sequence entry mixes a mapping and a list")
            items.append(item)
            continue
        key, sep, value = stripped.partition(":")
        if not sep:
            raise AgentFileError(f"line {i + 1}: '{stripped}' is not a key: value pair")
        if value.strip():
            mapping[key.strip()] = _scalar(value)
            i += 1
        else:
            nested, i = parse_block(lines, i + 1, here + 2)
            # `key:` with nothing indented under it is an empty value, not an
            # empty mapping — an emptied description must read as missing.
            mapping[key.strip()] = nested if nested else ""
    if items and mapping:
        raise AgentFileError("a block is either a mapping or a sequence, not both")
    return (items if items else mapping), i


def parse_agent(text: str, path: str = "<agent>") -> dict:
    """One agent file -> {frontmatter fields, 'prompt': body}. Raises on anything unknown."""
    front, body = split_frontmatter(text)
    parsed, _ = parse_block(front, 0, 0)
    if not isinstance(parsed, dict):
        raise AgentFileError(f"{path}: frontmatter is not a mapping")
    unknown = sorted(set(parsed) - KNOWN_KEYS)
    if unknown:
        raise AgentFileError(
            f"{path}: frontmatter key(s) {', '.join(unknown)} are not carried into the inline "
            f"JSON — teach {os.path.basename(__file__)} the key or drop it, but do not let a "
            f"headless run differ from an interactive one"
        )
    for required in ("name", "description"):
        if not str(parsed.get(required, "")).strip():
            raise AgentFileError(f"{path}: frontmatter '{required}' is required")
    if not body.strip():
        raise AgentFileError(f"{path}: the body is the agent's brief and cannot be empty")
    parsed["prompt"] = body
    return parsed


def split_tools(value) -> list[str]:
    """`Read, Glob Grep` -> ["Read", "Glob", "Grep"]; already-a-list passes through."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [t.strip() for t in re.split(r"[,\s]+", str(value).strip("[] ")) if t.strip()]


def retarget_hooks(hooks, guard: str):
    """Point every hook command at `guard` instead of the path inside the tree."""
    if isinstance(hooks, dict):
        return {k: retarget_hooks(v, guard) for k, v in hooks.items()}
    if isinstance(hooks, list):
        return [retarget_hooks(v, guard) for v in hooks]
    if isinstance(hooks, str) and GUARD_HOOK_RE.search(hooks):
        return guard
    return hooks


def to_definition(parsed: dict, guard: str | None = None) -> dict:
    """The parsed file as one inline agent definition."""
    out: dict = {}
    for key, out_key in SCALAR_KEYS.items():
        if key in parsed:
            out[out_key] = str(parsed[key])
    for key, out_key in LIST_KEYS.items():
        if key in parsed:
            out[out_key] = split_tools(parsed[key])
    for key, out_key in INT_KEYS.items():
        if key in parsed:
            out[out_key] = int(parsed[key])
    for key, out_key in BOOL_KEYS.items():
        if key in parsed:
            value = parsed[key]
            out[out_key] = value if isinstance(value, bool) else str(value).lower() == "true"
    if "hooks" in parsed:
        hooks = parsed["hooks"]
        out["hooks"] = retarget_hooks(hooks, guard) if guard else hooks
    out["prompt"] = parsed["prompt"]
    return out


def tracked_agent_files(root: str, directory: str, pattern: str) -> list[str]:
    """Agent files git tracks, so an untracked file dropped in a checkout is not picked up."""
    try:
        out = subprocess.check_output(
            ["git", "ls-files", os.path.join(directory, pattern)],
            cwd=root, text=True, encoding="utf-8",
        )
        paths = [p for p in out.splitlines() if p]
        if paths:
            return sorted(paths)
    except (OSError, subprocess.CalledProcessError):
        pass
    full = os.path.join(root, directory)
    if not os.path.isdir(full):
        return []
    prefix = pattern.split("*")[0]
    return sorted(
        os.path.join(directory, n) for n in os.listdir(full)
        if n.startswith(prefix) and n.endswith(".md")
    )


def build(root: str, directory: str, pattern: str, guard: str | None,
          only: set[str] | None) -> dict:
    """{agent name: definition} for every agent file, sorted by name."""
    definitions: dict[str, dict] = {}
    for rel in tracked_agent_files(root, directory, pattern):
        with open(os.path.join(root, rel), encoding="utf-8") as fh:
            parsed = parse_agent(fh.read(), rel)
        name = str(parsed["name"])
        if only and name not in only:
            continue
        if name in definitions:
            raise AgentFileError(f"{rel}: two agent files both define '{name}'")
        definitions[name] = to_definition(parsed, guard)
    if only:
        missing = sorted(only - set(definitions))
        if missing:
            raise AgentFileError(f"no agent definition named {', '.join(missing)}")
    return {name: definitions[name] for name in sorted(definitions)}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=None, help="repository root (default: the current git toplevel)")
    parser.add_argument("--dir", default=DEFAULT_DIR, help=f"agent directory (default: {DEFAULT_DIR})")
    parser.add_argument("--pattern", default=DEFAULT_GLOB, help=f"file pattern (default: {DEFAULT_GLOB})")
    parser.add_argument("--guard", default=None,
                        help="absolute path to the verifier's guard hook, for a checkout you do not trust")
    parser.add_argument("--only", default=None, help="comma-separated agent names to include")
    parser.add_argument("--check", action="store_true", help="parse and report; write nothing to stdout")
    parser.add_argument("--indent", type=int, default=None, help="pretty-print with this indent")
    args = parser.parse_args(argv)

    root = args.repo
    if root is None:
        try:
            root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True, encoding="utf-8"
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            root = os.getcwd()
    if args.guard and not os.path.isabs(args.guard):
        print("audit-agents-json: --guard must be an absolute path", file=sys.stderr)
        return 2
    only = {n.strip() for n in args.only.split(",") if n.strip()} if args.only else None
    try:
        definitions = build(root, args.dir, args.pattern, args.guard, only)
    except (AgentFileError, OSError) as exc:
        print(f"audit-agents-json: {exc}", file=sys.stderr)
        return 1
    if not definitions:
        print(f"audit-agents-json: no agent files at {args.dir}/{args.pattern}", file=sys.stderr)
        return 1
    if args.check:
        print(f"audit-agents-json: {len(definitions)} agent(s) parse and carry every key: "
              f"{', '.join(definitions)}")
        return 0
    json.dump(definitions, sys.stdout, indent=args.indent, sort_keys=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
