#!/usr/bin/env python3
"""Tests for tools/catalog.py — the fixer that keeps the stated skill counts true.

catalog.py rewrites counts in README.md, USER-MANUAL.md, SYSTEM-OVERVIEW.md and
install.sh. Until the audit looked, nothing tested it and the validator checked
only the first two files, so a catalog.py that quietly stopped rewriting would
have left two files wrong with every gate green (audit finding T-002).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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
        n = len(catalog.read_skills()[0])
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
        skills, _ = catalog.read_skills()
        table = catalog.render_table(skills, with_invoke=True)
        for name, _ in skills:
            self.assertIn(f"| `{name}` |", table)


def _skill(root: str, name: str, *, house_keys: bool = True) -> None:
    d = os.path.join(root, ".claude", "skills", name)
    os.makedirs(d, exist_ok=True)
    body = f"---\nname: {name}\ndescription: d\n"
    if house_keys:
        body += f'when_to_use: w\nargument-hint: "[x]"\npurpose: "Purpose of {name}"\n'
    body += "---\n\nBody.\n"
    open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8").write(body)


class UnreadableSkillTests(unittest.TestCase):
    """A skill this tool cannot render is reported, never crashed on, never written past.

    update.sh leaves a project's own skills in place on purpose. Exiting on the
    first one without CCGG's house keys made an ordinary sync look like stale
    tables, and the command update.sh then advised crashed the same way.
    """

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ccgg-catalog-")
        self.addCleanup(shutil.rmtree, self.root, True)
        _skill(self.root, "alpha")
        self._write_agents()

    def _write_agents(self):
        """AGENTS.md exactly as the tool would render it, so the tree starts current."""
        with mock.patch.object(catalog, "ROOT", self.root):
            skills, _ = catalog.read_skills()
        table = catalog.render_table(skills, with_invoke=False)
        open(os.path.join(self.root, "AGENTS.md"), "w", encoding="utf-8").write(
            f"# Rules\n\n{catalog.START}\n{table}{catalog.END}\n")

    def _run(self, argv=("catalog.py",)):
        with mock.patch.object(catalog, "ROOT", self.root), mock.patch.object(sys, "argv", list(argv)):
            return catalog.main()

    def test_all_readable_is_current(self):
        self.assertEqual(self._run(), catalog.EXIT_CURRENT)

    def test_unreadable_skill_is_returned_not_fatal(self):
        _skill(self.root, "project-only", house_keys=False)
        with mock.patch.object(catalog, "ROOT", self.root):
            skills, unreadable = catalog.read_skills()
        self.assertEqual([n for n, _ in skills], ["alpha"])
        self.assertEqual(unreadable, [os.path.join(".claude", "skills", "project-only", "SKILL.md")])

    def test_unreadable_skill_exits_distinctly_from_stale(self):
        _skill(self.root, "project-only", house_keys=False)
        self.assertEqual(self._run(), catalog.EXIT_UNREADABLE)
        self.assertNotEqual(catalog.EXIT_UNREADABLE, catalog.EXIT_STALE,
                            "update.sh tells the two apart by this code")

    def test_unreadable_skill_writes_nothing(self):
        """A count from a partial list is wrong — writing it would look consistent."""
        _skill(self.root, "project-only", house_keys=False)
        before = open(os.path.join(self.root, "AGENTS.md"), encoding="utf-8").read()
        self.assertEqual(self._run(("catalog.py", "--write")), catalog.EXIT_UNREADABLE)
        self.assertEqual(open(os.path.join(self.root, "AGENTS.md"), encoding="utf-8").read(), before)

    def test_stale_table_exits_stale(self):
        _skill(self.root, "beta")
        self.assertEqual(self._run(), catalog.EXIT_STALE)

    def test_write_repairs_a_stale_table(self):
        _skill(self.root, "beta")
        self.assertEqual(self._run(("catalog.py", "--write")), catalog.EXIT_CURRENT)
        self.assertEqual(self._run(), catalog.EXIT_CURRENT)
        self.assertIn("| `/beta` |", open(os.path.join(self.root, "AGENTS.md"), encoding="utf-8").read())

    def test_empty_skill_tree_is_unreadable_not_current(self):
        shutil.rmtree(os.path.join(self.root, ".claude", "skills", "alpha"))
        self.assertEqual(self._run(), catalog.EXIT_UNREADABLE)


class ReadSkillsTests(unittest.TestCase):
    def test_reads_name_and_purpose_from_disk(self):
        skills = dict(catalog.read_skills()[0])
        self.assertIn("gbb", skills)
        self.assertTrue(skills["gbb"].strip(), "a skill with an empty purpose renders a blank row")


if __name__ == "__main__":
    unittest.main()
