#!/usr/bin/env python3
"""Tests for tools/catalog.py — the fixer that keeps the stated skill counts true.

catalog.py rewrites counts in README.md, USER-MANUAL.md, SYSTEM-OVERVIEW.md and
install.sh. Until the audit looked, nothing tested it and the validator checked
only the first two files, so a catalog.py that quietly stopped rewriting would
have left two files wrong with every gate green (audit finding T-002).
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import catalog
import validate


class UpdateCountsTests(unittest.TestCase):
    def test_digit_count_rewritten(self):
        self.assertEqual(catalog.update_counts("all 27 skills ship", 28), "all 28 skills ship")

    def test_every_occurrence_rewritten(self):
        out = catalog.update_counts("27 skills here and 27 skills there", 28)
        self.assertNotIn("27 skills", out)
        self.assertEqual(out.count("28 skills"), 2)

    def test_qualified_forms_rewritten(self):
        for text in ("27 production-ready skills", "27 reusable skills",
                     "27 installed skills", "27 skill workflows"):
            with self.subTest(text=text):
                self.assertIn("28", catalog.update_counts(text, 28))

    def test_spelled_out_count_rewritten(self):
        self.assertEqual(catalog.update_counts("expect twenty-seven.", 28), "expect twenty-eight.")

    def test_unrelated_numbers_untouched(self):
        self.assertEqual(catalog.update_counts("27 hooks and 3 agents", 28), "27 hooks and 3 agents")

    def test_identity_when_already_current(self):
        self.assertEqual(catalog.update_counts("28 skills", 28), "28 skills")


class SpelledCountAgreementTests(unittest.TestCase):
    """The fixer writes the word; the validator checks it. One table, or they drift."""

    def test_tables_agree(self):
        self.assertEqual(catalog.WORDS, validate.SPELLED_COUNTS)

    def test_current_count_is_spellable(self):
        n = len(catalog.read_skills())
        self.assertIn(n, catalog.WORDS,
                      "a count with no spelled-out form leaves install.sh unfixable")


class RenderTableTests(unittest.TestCase):
    def test_invoke_table_row_shape_matches_the_validator(self):
        table = catalog.render_table([("gbb", "Purpose here")], with_invoke=True)
        self.assertIn("| `gbb` | `/gbb` | Purpose here |", table)

    def test_purpose_table_row_shape_matches_the_validator(self):
        table = catalog.render_table([("gbb", "Purpose here")], with_invoke=False)
        self.assertIn("| `/gbb` | Purpose here |", table)

    def test_every_skill_on_disk_appears(self):
        skills = catalog.read_skills()
        table = catalog.render_table(skills, with_invoke=True)
        for name, _ in skills:
            self.assertIn(f"| `{name}` |", table)


class ReadSkillsTests(unittest.TestCase):
    def test_reads_name_and_purpose_from_disk(self):
        skills = dict(catalog.read_skills())
        self.assertIn("gbb", skills)
        self.assertTrue(skills["gbb"].strip(), "a skill with an empty purpose renders a blank row")


if __name__ == "__main__":
    unittest.main()
