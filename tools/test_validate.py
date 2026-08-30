#!/usr/bin/env python3
"""Unit tests for the pure parts of validate.py. Stdlib only.

Run: python -m unittest discover -s tools -p "test_*.py"
"""

import unittest

from validate import (
    frontmatter_scalar_problem,
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
