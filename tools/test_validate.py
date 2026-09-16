#!/usr/bin/env python3
"""Unit tests for the pure parts of validate.py. Stdlib only.

Run: python -m unittest discover -s tools -p "test_*.py"
"""

import unittest

import validate

from validate import (
    frontmatter_scalar_problem,
    link_leaves_install_set,
    slugify,
    strip_code_blocks,
    volatile_lines,
)


class VolatileLinesTests(unittest.TestCase):
    # happy path — stable rules text produces no findings
    def test_stable_text_clean(self):
        text = "# Rules\n\n- Keep always-loaded files lean.\n- Version 1.2.3 is fine.\n"
        self.assertEqual(volatile_lines(text), [])

    # edge: empty input
    def test_empty_text(self):
        self.assertEqual(volatile_lines(""), [])

    # edge: boundary lookalikes that must NOT match
    def test_date_lookalikes_ignored(self):
        text = "phone 555-12-34\nsemver 2026.8.28\nshort date 2026-8-28\nlast running joke\n"
        self.assertEqual(volatile_lines(text), [])

    # edge: unexpected type fails loudly, not silently
    def test_non_string_raises(self):
        with self.assertRaises(AttributeError):
            volatile_lines(None)

    # failure mode — the two volatile classes are caught, with line numbers
    def test_volatile_content_found(self):
        text = "# Title\nAs of 2026-08-28 this holds.\nstable line\nLast updated: yesterday\n"
        hits = volatile_lines(text)
        self.assertEqual([no for no, _ in hits], [2, 4])
        self.assertIn("2026-08-28", hits[0][1])

    def test_case_insensitive_marker(self):
        hits = volatile_lines("LAST SYNCED by the hook\n")
        self.assertEqual(len(hits), 1)


class FrontmatterScalarTests(unittest.TestCase):
    # the real bug: an unquoted purpose with an inner ": " invalidated the block
    def test_unquoted_inner_colon_flagged(self):
        line = "purpose: Structured decision: research, debate, durable record"
        self.assertIsNotNone(frontmatter_scalar_problem(line))

    # quoting it is the fix, and must come back clean
    def test_quoted_inner_colon_ok(self):
        line = 'purpose: "Structured decision: research, debate, durable record"'
        self.assertIsNone(frontmatter_scalar_problem(line))

    # single quotes are valid YAML too
    def test_single_quoted_ok(self):
        self.assertIsNone(frontmatter_scalar_problem("purpose: 'a: b'"))

    # ordinary values must not be flagged
    def test_plain_value_ok(self):
        self.assertIsNone(frontmatter_scalar_problem("name: ship"))

    # a colon with no space is legal in an unquoted scalar
    def test_colon_without_space_ok(self):
        self.assertIsNone(frontmatter_scalar_problem("argument-hint: a:b"))

    # already-quoted hints that themselves contain ": " stay clean
    def test_quoted_argument_hint_ok(self):
        self.assertIsNone(frontmatter_scalar_problem('argument-hint: "[optional: no-merge]"'))

    # edge: line with no mapping at all
    def test_no_colon_ok(self):
        self.assertIsNone(frontmatter_scalar_problem("just text"))

    # edge: empty value
    def test_empty_value_ok(self):
        self.assertIsNone(frontmatter_scalar_problem("purpose: "))



class LinkInstallSetTests(unittest.TestCase):
    # happy path — the links rule files actually carry today
    def test_sibling_rule_file_ok(self):
        self.assertFalse(link_leaves_install_set("WORKING-CHARTER.md"))

    def test_reference_companion_ok(self):
        self.assertFalse(link_leaves_install_set(".claude/references/code-gate.md"))

    # edge: empty input — a bare anchor never leaves its own file
    def test_bare_anchor_ok(self):
        self.assertFalse(link_leaves_install_set("#skill-checker"))
        self.assertFalse(link_leaves_install_set(""))

    # edge: boundary — an anchor on an installed file is still installed,
    # and "./" is the same path written differently
    def test_anchor_and_dot_slash_ok(self):
        self.assertFalse(link_leaves_install_set("AGENTS.md#skill-system"))
        self.assertFalse(link_leaves_install_set("./.claude/skills/commit/SKILL.md"))

    # edge: a prefix that only looks installed must not slip through
    def test_lookalike_prefix_flagged(self):
        self.assertTrue(link_leaves_install_set(".claudex/notes.md"))
        self.assertTrue(link_leaves_install_set("AGENTS.md.bak"))

    # edge: unexpected type fails loudly, not silently
    def test_non_string_raises(self):
        with self.assertRaises(AttributeError):
            link_leaves_install_set(None)

    # failure mode — the real cases: targets install.sh does not copy
    def test_uninstalled_targets_flagged(self):
        for link in (
            "MEMORY.md",
            "decisions/README.md",
            "knowledge-base/entries/common-pitfalls.md",
            "docs/08-skills.md",
            "tools/catalog.py",
            "../outside-the-repo.md",
        ):
            with self.subTest(link=link):
                self.assertTrue(link_leaves_install_set(link))

    # external links are somebody else's problem, not a broken install
    def test_external_links_ignored(self):
        self.assertFalse(link_leaves_install_set("https://code.claude.com/docs"))
        self.assertFalse(link_leaves_install_set("mailto:someone@example.com"))


class SlugifyTests(unittest.TestCase):
    # punctuation is deleted in place, leaving two spaces -> two hyphens
    def test_plus_leaves_double_hyphen(self):
        self.assertEqual(slugify("5.2 Registration + dispatch"), "52-registration--dispatch")

    # an em dash behaves the same way, and the apostrophe simply disappears
    def test_em_dash_and_apostrophe(self):
        self.assertEqual(
            slugify("Tier 3 — The moat ArchiWood can't touch"),
            "tier-3--the-moat-archiwood-cant-touch",
        )

    # an inline link contributes its text, never its URL
    def test_inline_link_contributes_text_only(self):
        self.assertEqual(
            slugify("7.3 The Intellisense ghost ([Pillar 2](../02-cabinetry-intellisense.md))"),
            "73-the-intellisense-ghost-pillar-2",
        )

    # the ordinary case stays ordinary
    def test_plain_heading(self):
        self.assertEqual(slugify("Plain Heading"), "plain-heading")

    # a single space is still a single hyphen
    def test_single_space(self):
        self.assertEqual(slugify("a b"), "a-b")


class StripCodeBlocksTests(unittest.TestCase):
    # link-like regex syntax inside a fence must not be scanned
    def test_fenced_content_blanked(self):
        lines = ["intro", "```", "FEET : /^(\\d+)[-\\s](\\d+)$/", "```", "outro"]
        self.assertEqual(strip_code_blocks(lines), ["intro", "", "", "", "outro"])

    # line count is preserved so positions stay meaningful
    def test_line_count_preserved(self):
        lines = ["a", "```", "x", "y", "```", "b"]
        self.assertEqual(len(strip_code_blocks(lines)), len(lines))

    # tildes open and close a fence too, and do not close a backtick fence
    def test_tilde_fence(self):
        self.assertEqual(strip_code_blocks(["~~~", "x", "~~~"]), ["", "", ""])

    # prose is returned untouched
    def test_no_fence(self):
        self.assertEqual(strip_code_blocks(["a", "b"]), ["a", "b"])

    # an unclosed fence blanks to end of file rather than leaking content
    def test_unclosed_fence(self):
        self.assertEqual(strip_code_blocks(["a", "```", "x"]), ["a", "", ""])


if __name__ == "__main__":
    unittest.main()


class AgentFrontmatterTests(unittest.TestCase):
    """Check 12 — the F002 read-only boundary for audit agents."""

    def _fields(self, **kw):
        base = {"name": "audit-x", "description": "d", "tools": "Read, Glob, Grep", "omitClaudeMd": "true"}
        base.update(kw)
        return base

    # happy paths
    def test_specialist_clean(self):
        self.assertEqual(validate.agent_frontmatter_problems("a.md", self._fields()), [])

    def test_verifier_clean(self):
        fields = self._fields(name="audit-verifier", tools="Read, Glob, Grep, Bash",
                              disallowedTools="Write, Edit, NotebookEdit", isolation="worktree")
        self.assertEqual(validate.agent_frontmatter_problems("v.md", fields), [])

    # edge: a non-audit agent only needs name and description
    def test_other_agent_unconstrained(self):
        self.assertEqual(validate.agent_frontmatter_problems("o.md", {"name": "helper", "description": "d", "tools": "Bash"}), [])

    def test_space_separated_tools_accepted(self):
        self.assertEqual(validate.agent_frontmatter_problems("a.md", self._fields(tools="Read Glob Grep")), [])

    # failure paths
    def test_specialist_with_bash_rejected(self):
        problems = validate.agent_frontmatter_problems("a.md", self._fields(tools="Read, Glob, Grep, Bash"))
        self.assertTrue(any("exactly Read, Glob, Grep" in p for p in problems))

    def test_specialist_missing_omit_claude_md(self):
        problems = validate.agent_frontmatter_problems("a.md", self._fields(omitClaudeMd=""))
        self.assertTrue(any("omitClaudeMd" in p for p in problems))

    def test_verifier_without_worktree_or_disallowed(self):
        problems = validate.agent_frontmatter_problems("v.md", self._fields(name="audit-verifier", tools="Bash"))
        self.assertTrue(any("worktree" in p for p in problems))
        self.assertTrue(any("disallow" in p for p in problems))

    def test_missing_description(self):
        problems = validate.agent_frontmatter_problems("a.md", self._fields(description=""))
        self.assertIn("a.md: frontmatter missing key 'description'", problems)


class ParseFrontmatterFieldsTests(unittest.TestCase):
    def test_parses_and_skips_nested(self):
        fields, why = validate.parse_frontmatter_fields(["---", "name: a", "hooks:", "  PreToolUse:", "---", "body"])
        self.assertIsNone(why)
        self.assertEqual(fields, {"name": "a", "hooks": ""})

    def test_missing_open(self):
        fields, why = validate.parse_frontmatter_fields(["name: a", "---"])
        self.assertIsNone(fields)
        self.assertIn("line 1", why)

    def test_unclosed(self):
        fields, why = validate.parse_frontmatter_fields(["---", "name: a"])
        self.assertIsNone(fields)
        self.assertIn("never closed", why)

    def test_empty(self):
        self.assertIsNone(validate.parse_frontmatter_fields([])[0])

    def test_split_tool_list_keeps_names_drops_specifiers(self):
        self.assertEqual(validate.split_tool_list("Read, Bash(git *) Grep"), {"Read", "Bash", "Grep"})
        self.assertEqual(validate.split_tool_list(""), set())
