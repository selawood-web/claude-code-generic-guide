#!/usr/bin/env python3
"""Unit tests for the pure checks in audit_facts.py. Stdlib only.

Run: python -m unittest discover -s tools -p "test_*.py"
"""

import json
import os
import sys
import tempfile
import unittest

import audit_facts
from audit_facts import (
    Facts,
    command_references,
    frontmatter_facts,
    hidden_characters,
    hook_commands,
    hook_registration,
    hook_stdout_facts,
    network_patterns,
    parse_frontmatter,
    permission_surface,
    resolve_commands,
    split_tools,
    spelling_variant,
    tool_name,
)

VOCAB = json.load(open(os.path.join(os.path.dirname(__file__), "audit_vocab.json"), encoding="utf-8"))


def findings(facts: Facts, kind=None):
    return [f for f in facts.items if f.status == "finding" and (kind is None or f.kind == kind)]


class HiddenCharactersTests(unittest.TestCase):
    def test_clean_text(self):
        self.assertEqual(hidden_characters("plain\nlines\n"), [])

    def test_zero_width_and_bidi_found_with_line(self):
        hits = hidden_characters("ok\nbad\u200bhere\n\u202eflip\n")
        self.assertEqual([h[0] for h in hits], [2, 3])
        self.assertEqual(hits[0][1], ["U+200B"])

    def test_empty(self):
        self.assertEqual(hidden_characters(""), [])

    def test_ordinary_unicode_ignored(self):
        self.assertEqual(hidden_characters("café — naïve 中文\n"), [])

    def test_non_string_raises(self):
        with self.assertRaises(TypeError):
            hidden_characters(b"bytes")


class FrontmatterParseTests(unittest.TestCase):
    def test_top_level_keys(self):
        fields = parse_frontmatter("---\nname: x\ndescription: does y\nhooks:\n  PreToolUse:\n    - matcher: Bash\n---\nbody\n")
        self.assertEqual(fields, {"name": "x", "description": "does y", "hooks": ""})

    def test_not_on_line_one_is_none(self):
        self.assertIsNone(parse_frontmatter("\n---\nname: x\n---\n"))

    def test_unclosed_is_none(self):
        self.assertIsNone(parse_frontmatter("---\nname: x\n"))

    def test_empty_is_none(self):
        self.assertIsNone(parse_frontmatter(""))

    def test_non_string_raises(self):
        with self.assertRaises(TypeError):
            parse_frontmatter(None)


class ToolListTests(unittest.TestCase):
    def test_comma_and_space_separated(self):
        self.assertEqual(split_tools("Read, Grep Bash(git diff *)"), ["Read", "Grep", "Bash(git diff *)"])

    def test_yaml_list_form(self):
        self.assertEqual(split_tools("[Read, Glob]"), ["Read", "Glob"])

    def test_empty(self):
        self.assertEqual(split_tools(""), [])

    def test_tool_name_strips_specifier(self):
        self.assertEqual(tool_name("Bash(git *)"), "Bash")
        self.assertEqual(tool_name("mcp__github__x"), "mcp__github__x")

    def test_spelling_variant(self):
        self.assertEqual(spelling_variant("when-to-use", VOCAB["skill_keys"]), "when_to_use")
        self.assertIsNone(spelling_variant("purpose", VOCAB["skill_keys"]))


class FrontmatterFactsTests(unittest.TestCase):
    def test_clean_skill_is_ok(self):
        facts = Facts()
        frontmatter_facts("s/SKILL.md", "---\nname: s\ndescription: d\nallowed-tools: Read Bash(git *)\n---\n", "skill", VOCAB, facts)
        self.assertEqual(findings(facts), [])
        self.assertEqual(facts.items[-1].status, "ok")

    def test_variant_key_named(self):
        facts = Facts()
        frontmatter_facts("s/SKILL.md", "---\nname: s\ndescription: d\nwhen-to-use: x\n---\n", "skill", VOCAB, facts)
        self.assertTrue(any("when_to_use" in f.evidence for f in findings(facts)))

    def test_unknown_tool_flagged(self):
        facts = Facts()
        frontmatter_facts("s/SKILL.md", "---\nname: s\ndescription: d\nallowed-tools: powershell, bash\n---\n", "skill", VOCAB, facts)
        self.assertEqual(len(findings(facts)), 2)

    def test_empty_description_flagged(self):
        facts = Facts()
        frontmatter_facts("s/SKILL.md", "---\nname: s\ndescription:\n---\n", "skill", VOCAB, facts)
        self.assertTrue(any("description" in f.evidence for f in findings(facts)))

    def test_agent_specifier_flagged(self):
        facts = Facts()
        frontmatter_facts("a.md", "---\nname: a\ndescription: d\ndisallowedTools: Bash(git push *)\n---\n", "agent", VOCAB, facts)
        self.assertTrue(any("specifier" in f.evidence for f in findings(facts)))

    def test_no_frontmatter_is_dead_mechanism(self):
        facts = Facts()
        frontmatter_facts("s/SKILL.md", "# no header\n", "skill", VOCAB, facts)
        self.assertEqual(len(findings(facts)), 1)
        self.assertIn("dead-mechanism", facts.items[0].detail)


SETTINGS = {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/a.sh"}]}],
                      "PreCompact": [{"hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/b.sh"}]}]}}


class HookRegistrationTests(unittest.TestCase):
    def test_commands_extracted(self):
        self.assertEqual(sorted(e for e, _ in hook_commands(SETTINGS)), ["PreCompact", "SessionStart"])

    def test_all_registered_and_present_is_ok(self):
        facts = Facts()
        hook_registration(SETTINGS, [".claude/hooks/a.sh", ".claude/hooks/b.sh"], VOCAB, facts)
        self.assertEqual(findings(facts), [])

    def test_registered_but_missing(self):
        facts = Facts()
        hook_registration(SETTINGS, [".claude/hooks/a.sh"], VOCAB, facts)
        self.assertTrue(any("does not exist" in f.evidence for f in findings(facts)))

    def test_present_but_unregistered(self):
        facts = Facts()
        hook_registration({"hooks": {}}, [".claude/hooks/a.sh"], VOCAB, facts)
        self.assertTrue(any("no settings.json hook references" in f.evidence for f in findings(facts)))

    def test_scoped_registration_counts(self):
        facts = Facts()
        hook_registration({"hooks": {}}, [".claude/hooks/guard.sh"], VOCAB, facts, {"guard.sh"})
        self.assertEqual(findings(facts), [])

    def test_unknown_event(self):
        facts = Facts()
        hook_registration({"hooks": {"OnMoonrise": [{"hooks": [{"type": "command", "command": "x"}]}]}}, [], VOCAB, facts)
        self.assertTrue(any("unknown event" in f.evidence for f in findings(facts)))

    def test_malformed_settings_tolerated(self):
        facts = Facts()
        hook_registration({"hooks": "nope"}, [], VOCAB, facts)
        self.assertEqual(facts.items[-1].status, "skipped")


class HookStdoutTests(unittest.TestCase):
    def test_agent_instruction_on_precompact_flagged(self):
        facts = Facts()
        hook_stdout_facts(SETTINGS, lambda n: 'echo "run /flush"\n' if n == "b.sh" else "exit 0\n", VOCAB, facts)
        self.assertEqual(len(findings(facts, "hook-stdout")), 1)
        self.assertIn("PreCompact", findings(facts)[0].evidence)

    def test_summary_instruction_on_precompact_is_ok(self):
        facts = Facts()
        hook_stdout_facts(SETTINGS, lambda n: 'echo "Preserve open threads and decisions"\n' if n == "b.sh" else "exit 0\n", VOCAB, facts)
        self.assertEqual(findings(facts, "hook-stdout"), [])
        self.assertTrue(any(f.status == "ok" and "summary" in f.evidence for f in facts.items))

    def test_echo_on_other_debug_only_event_flagged(self):
        facts = Facts()
        settings = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": ".claude/hooks/s.sh"}]}]}}
        hook_stdout_facts(settings, lambda n: 'echo "remember to test"\n', VOCAB, facts)
        self.assertEqual(len(findings(facts, "hook-stdout")), 1)

    def test_echo_on_session_start_fine(self):
        facts = Facts()
        hook_stdout_facts(SETTINGS, lambda n: 'echo hi\n', VOCAB, facts)
        self.assertEqual([f for f in findings(facts) if "SessionStart" in f.evidence], [])

    def test_json_additional_context_accepted(self):
        facts = Facts()
        hook_stdout_facts(SETTINGS, lambda n: 'echo "{\\"additionalContext\\": \\"x\\"}"\n', VOCAB, facts)
        self.assertEqual(findings(facts, "hook-stdout"), [])


class CommandResolutionTests(unittest.TestCase):
    def test_references_found(self):
        self.assertEqual(command_references("run `/flush` then `/plan`; not /bare or `/Bad`"), {"flush", "plan"})

    def test_resolution(self):
        self.assertEqual(resolve_commands({"flush", "plan", "ghost"}, {"flush"}, VOCAB["builtin_commands"]), ["ghost"])

    def test_empty(self):
        self.assertEqual(command_references(""), set())
        self.assertEqual(resolve_commands(set(), set(), []), [])


class NetworkPatternTests(unittest.TestCase):
    def test_curl_pipe_sh(self):
        hits = network_patterns("set -e\ncurl -s http://x | sh\n")
        self.assertEqual([h[1] for h in hits], ["curl", "pipe to shell"])
        self.assertEqual(hits[0][0], 2)

    def test_comment_lines_ignored(self):
        self.assertEqual(network_patterns("# never curl here\n"), [])

    def test_clean(self):
        self.assertEqual(network_patterns("echo ok\nexit 0\n"), [])


class PermissionSurfaceTests(unittest.TestCase):
    def test_fields_listed(self):
        s = permission_surface({"permissions": {"allow": ["Bash(ls *)"]}, "env": {"B": 1, "A": 2}, "hooks": SETTINGS["hooks"]})
        self.assertEqual(s["allow"], ["Bash(ls *)"])
        self.assertEqual(s["env"], ["A", "B"])
        self.assertEqual(s["hooks"], ["PreCompact", "SessionStart"])

    def test_empty_settings(self):
        s = permission_surface({})
        self.assertEqual((s["allow"], s["env"], s["hooks"]), ([], [], []))


if __name__ == "__main__":
    unittest.main()


class ToolingKeysAndRedirectTests(unittest.TestCase):
    def test_tooling_key_is_ok_not_finding(self):
        facts = Facts()
        frontmatter_facts("s/SKILL.md", "---\nname: s\ndescription: d\npurpose: p\n---\n", "skill", VOCAB, facts, {"purpose"})
        self.assertEqual(findings(facts), [])
        self.assertTrue(any("repository tooling reads it" in f.evidence for f in facts.items))

    def test_redirected_echo_not_model_output(self):
        facts = Facts()
        hook_stdout_facts(SETTINGS, lambda n: 'echo "marker" >> "$LOG"\n', VOCAB, facts)
        self.assertEqual(findings(facts, "hook-stdout"), [])

    def test_regex_literal_not_network_call(self):
        self.assertEqual(network_patterns('    (r"\\b(curl|wget)\\b", "network"),\n'), [])


class RunGateTests(unittest.TestCase):
    """run_gate executes code out of the audited tree, so: not by default, and
    never with the operator's environment attached (finding S-005)."""

    def collect_facts(self):
        facts = audit_facts.Facts()
        return facts

    def test_the_default_runs_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = os.path.join(tmp, "ran")
            facts = self.collect_facts()
            audit_facts.run_gate(tmp, "canary", [sys.executable, "-c", f"open({marker!r},'w').write('x')"], facts)
            self.assertFalse(os.path.exists(marker), "run_gate executed the command without --run-gates")
        recorded = [f for f in facts.items if f.kind == "gate"]
        self.assertEqual(len(recorded), 1)
        self.assertEqual(recorded[0].status, "skipped")
        self.assertIn("--run-gates", recorded[0].evidence)

    def test_execute_true_actually_runs_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = os.path.join(tmp, "ran")
            facts = self.collect_facts()
            audit_facts.run_gate(tmp, "canary", [sys.executable, "-c", f"open({marker!r},'w').write('x')"], facts,
                                 execute=True)
            self.assertTrue(os.path.exists(marker))
        self.assertEqual([f.status for f in facts.items if f.kind == "gate"], ["ok"])

    def test_the_command_never_sees_the_operators_environment(self):
        """The canary the audit used to demonstrate the finding, as a test."""
        os.environ["CCGG_TEST_CANARY"] = "leak-me"
        self.addCleanup(os.environ.pop, "CCGG_TEST_CANARY", None)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "seen")
            facts = self.collect_facts()
            audit_facts.run_gate(
                tmp, "canary",
                [sys.executable, "-c",
                 f"import os;open({out!r},'w').write(repr(os.environ.get('CCGG_TEST_CANARY')))"],
                facts, execute=True)
            with open(out, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "None", "the gate command saw a variable from the operator's shell")

    def test_the_command_gets_a_home_that_is_not_the_operators(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "home")
            facts = self.collect_facts()
            audit_facts.run_gate(
                tmp, "canary",
                [sys.executable, "-c", f"import os;open({out!r},'w').write(os.environ['HOME'])"],
                facts, execute=True)
            with open(out, encoding="utf-8") as fh:
                seen = fh.read()
        self.assertNotEqual(seen, os.path.expanduser("~"))
        self.assertFalse(os.path.exists(seen), "the throwaway HOME outlived the gate run")
