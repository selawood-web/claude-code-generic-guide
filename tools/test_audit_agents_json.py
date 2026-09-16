#!/usr/bin/env python3
"""Unit tests for audit_agents_json.py, plus the contract the inline JSON must keep.

The last class is the one that matters most: the F002 read-only boundary is
enforced by tools/validate.py on the agent *files*, and a headless run never
reads those files. These tests assert the boundary survives serialization.

Run: python -m unittest discover -s tools -p "test_*.py"
"""

import io
import json
import os
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout

import audit_agents_json
from audit_agents_json import (
    AgentFileError,
    _scalar,
    build,
    parse_agent,
    parse_block,
    retarget_hooks,
    split_frontmatter,
    split_tools,
    to_definition,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPECIALIST = """---
name: audit-demo
description: A demo specialist.
tools: Read, Glob, Grep
model: haiku
maxTurns: 60
omitClaudeMd: true
---

The brief.
"""

VERIFIER = """---
name: audit-demo-verifier
description: A demo verifier.
tools: Read, Glob, Grep, Bash
disallowedTools: Write, Edit, NotebookEdit
isolation: worktree
model: inherit
maxTurns: 60
omitClaudeMd: true
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "\\"$CLAUDE_PROJECT_DIR\\"/.claude/hooks/audit-verifier-guard.sh"
---

The verifier brief.
"""


class SplitFrontmatterTests(unittest.TestCase):
    def test_splits_frontmatter_and_body(self):
        front, body = split_frontmatter(SPECIALIST)
        self.assertEqual(front[0], "name: audit-demo")
        self.assertEqual(body, "The brief.")

    def test_missing_open(self):
        with self.assertRaises(AgentFileError):
            split_frontmatter("name: x\n---\nbody\n")

    def test_unclosed(self):
        with self.assertRaises(AgentFileError):
            split_frontmatter("---\nname: x\nbody\n")

    def test_non_string_raises(self):
        with self.assertRaises(TypeError):
            split_frontmatter(None)


class ScalarTests(unittest.TestCase):
    def test_types(self):
        self.assertEqual(_scalar("60"), 60)
        self.assertEqual(_scalar("-2"), -2)
        self.assertIs(_scalar("true"), True)
        self.assertIs(_scalar("False"), False)
        self.assertEqual(_scalar("inherit"), "inherit")

    def test_quotes_and_escapes(self):
        self.assertEqual(_scalar('"Bash"'), "Bash")
        self.assertEqual(_scalar("'Bash'"), "Bash")
        self.assertEqual(_scalar(r'"\"$X\"/a.sh"'), '"$X"/a.sh')
        self.assertEqual(_scalar(r"'\"literal\"'"), r"\"literal\"")

    def test_colon_bearing_value_is_a_string(self):
        self.assertEqual(_scalar("A demo: with a colon"), "A demo: with a colon")


class ParseBlockTests(unittest.TestCase):
    def test_flat_mapping(self):
        value, end = parse_block(["a: 1", "b: two"], 0, 0)
        self.assertEqual(value, {"a": 1, "b": "two"})
        self.assertEqual(end, 2)

    def test_nested_hook_structure(self):
        front, _ = split_frontmatter(VERIFIER)
        parsed, _ = parse_block(front, 0, 0)
        self.assertEqual(
            parsed["hooks"],
            {"PreToolUse": [{"matcher": "Bash",
                             "hooks": [{"type": "command",
                                        "command": '"$CLAUDE_PROJECT_DIR"/.claude/hooks/audit-verifier-guard.sh'}]}]},
        )

    def test_sequence_of_scalars(self):
        value, _ = parse_block(["items:", "  - one", "  - two"], 0, 0)
        self.assertEqual(value, {"items": ["one", "two"]})

    def test_blank_lines_ignored(self):
        value, _ = parse_block(["a: 1", "", "b: 2"], 0, 0)
        self.assertEqual(value, {"a": 1, "b": 2})

    def test_line_without_colon_raises(self):
        with self.assertRaises(AgentFileError):
            parse_block(["just text"], 0, 0)

    def test_unexpected_indentation_raises(self):
        with self.assertRaises(AgentFileError):
            parse_block(["a: 1", "    b: 2"], 0, 0)


class ParseAgentTests(unittest.TestCase):
    def test_specialist(self):
        parsed = parse_agent(SPECIALIST)
        self.assertEqual(parsed["name"], "audit-demo")
        self.assertEqual(parsed["prompt"], "The brief.")
        self.assertIs(parsed["omitClaudeMd"], True)

    def test_unknown_key_is_an_error_not_a_silent_drop(self):
        text = SPECIALIST.replace("model: haiku", "model: haiku\ntimeoutSeconds: 30")
        with self.assertRaises(AgentFileError) as caught:
            parse_agent(text, "demo.md")
        self.assertIn("timeoutSeconds", str(caught.exception))

    def test_missing_description(self):
        with self.assertRaises(AgentFileError):
            parse_agent(SPECIALIST.replace("description: A demo specialist.", "description:  "))

    def test_empty_body(self):
        with self.assertRaises(AgentFileError):
            parse_agent("---\nname: a\ndescription: b\n---\n\n")


class SplitToolsTests(unittest.TestCase):
    def test_comma_and_space_forms(self):
        self.assertEqual(split_tools("Read, Glob Grep"), ["Read", "Glob", "Grep"])
        self.assertEqual(split_tools("[Read, Glob]"), ["Read", "Glob"])
        self.assertEqual(split_tools(["Read", "Glob"]), ["Read", "Glob"])

    def test_empty(self):
        self.assertEqual(split_tools("  "), [])


class RetargetHooksTests(unittest.TestCase):
    def test_replaces_only_the_in_tree_script(self):
        hooks = {"PreToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": '"$CLAUDE_PROJECT_DIR"/.claude/hooks/audit-verifier-guard.sh'}]}]}
        out = retarget_hooks(hooks, "/trusted/guard.sh")
        self.assertEqual(out["PreToolUse"][0]["hooks"][0]["command"], "/trusted/guard.sh")
        self.assertEqual(out["PreToolUse"][0]["matcher"], "Bash")

    def test_leaves_unrelated_commands_alone(self):
        self.assertEqual(retarget_hooks({"c": "echo hi"}, "/g.sh"), {"c": "echo hi"})


class ToDefinitionTests(unittest.TestCase):
    def test_name_is_the_key_not_a_field(self):
        d = to_definition(parse_agent(SPECIALIST))
        self.assertNotIn("name", d, "the CLI validates definition fields; name is the object key")

    def test_types_are_json_native(self):
        d = to_definition(parse_agent(SPECIALIST))
        self.assertEqual(d["tools"], ["Read", "Glob", "Grep"])
        self.assertIsInstance(d["maxTurns"], int)
        self.assertIsInstance(d["omitClaudeMd"], bool)
        self.assertEqual(json.loads(json.dumps(d)), d)

    def test_verifier_keeps_every_boundary_field(self):
        d = to_definition(parse_agent(VERIFIER), guard="/trusted/guard.sh")
        self.assertEqual(d["isolation"], "worktree")
        self.assertEqual(d["disallowedTools"], ["Write", "Edit", "NotebookEdit"])
        self.assertEqual(d["hooks"]["PreToolUse"][0]["hooks"][0]["command"], "/trusted/guard.sh")


class BuildAndMainTests(unittest.TestCase):
    def test_build_sorted_and_filtered(self):
        definitions = build(ROOT, os.path.join(".claude", "agents"), "audit-*.md", None, None)
        self.assertEqual(list(definitions), sorted(definitions))
        self.assertIn("audit-verifier", definitions)
        one = build(ROOT, os.path.join(".claude", "agents"), "audit-*.md", None, {"audit-harness"})
        self.assertEqual(list(one), ["audit-harness"])

    def test_unknown_name_in_only_is_an_error(self):
        with self.assertRaises(AgentFileError):
            build(ROOT, os.path.join(".claude", "agents"), "audit-*.md", None, {"audit-nope"})

    def test_main_emits_parsable_json(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(audit_agents_json.main(["--repo", ROOT]), 0)
        self.assertEqual(len(json.loads(out.getvalue())), 7)

    def test_main_check_mode_writes_no_json(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(audit_agents_json.main(["--repo", ROOT, "--check"]), 0)
        self.assertNotIn("{", out.getvalue())

    def test_main_rejects_a_relative_guard(self):
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(audit_agents_json.main(["--repo", ROOT, "--guard", "g.sh"]), 2)
        self.assertIn("absolute", err.getvalue())

    def test_main_reports_a_directory_with_no_agents(self):
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(audit_agents_json.main(["--repo", ROOT, "--dir", "tools"]), 1)
        self.assertIn("no agent files", err.getvalue())


class BoundarySurvivesSerializationTests(unittest.TestCase):
    """What validate.py enforces on the files, asserted on the JSON a headless run gets."""

    @classmethod
    def setUpClass(cls):
        cls.definitions = build(ROOT, os.path.join(".claude", "agents"), "audit-*.md", None, None)

    def test_every_tracked_agent_file_is_represented(self):
        tracked = subprocess.check_output(
            ["git", "ls-files", ".claude/agents/audit-*.md"], cwd=ROOT, text=True
        ).split()
        self.assertEqual(len(self.definitions), len(tracked))

    def test_no_definition_carries_a_field_the_cli_does_not_define(self):
        # The fields the CLI documents for inline agents. A new one is a deliberate
        # change here, not a surprise at startup in CI.
        supported = {"description", "prompt", "tools", "disallowedTools", "model", "permissionMode",
                     "mcpServers", "hooks", "maxTurns", "skills", "memory", "effort", "background",
                     "omitClaudeMd", "isolation", "initialPrompt"}
        for name, d in self.definitions.items():
            with self.subTest(agent=name):
                self.assertEqual(set(d) - supported, set())

    def test_specialists_carry_no_execution_tool(self):
        for name, d in self.definitions.items():
            if name == "audit-verifier":
                continue
            with self.subTest(agent=name):
                self.assertEqual(d["tools"], ["Read", "Glob", "Grep"])
                self.assertIs(d["omitClaudeMd"], True)
                self.assertNotIn("isolation", d)

    def test_verifier_alone_executes_and_keeps_its_guard(self):
        v = self.definitions["audit-verifier"]
        self.assertIn("Bash", v["tools"])
        self.assertEqual(v["isolation"], "worktree")
        self.assertEqual(sorted(v["disallowedTools"]), ["Edit", "NotebookEdit", "Write"])
        self.assertIn("audit-verifier-guard.sh", json.dumps(v["hooks"]))

    def test_every_brief_is_carried(self):
        for name, d in self.definitions.items():
            with self.subTest(agent=name):
                self.assertGreater(len(d["prompt"]), 200, "the brief is the agent")

    def test_guard_retargeting_leaves_no_in_tree_path(self):
        retargeted = build(ROOT, os.path.join(".claude", "agents"), "audit-*.md", "/trusted/guard.sh", None)
        self.assertNotIn(".claude/hooks/", json.dumps(retargeted["audit-verifier"]["hooks"]))


if __name__ == "__main__":
    unittest.main()
