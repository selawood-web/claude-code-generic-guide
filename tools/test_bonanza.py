#!/usr/bin/env python3
"""The bonanza skill's own contract — what a reader assumes and nothing else checks.

The validator proves the seven files exist, parse and link. It cannot prove they
agree with each other, and this skill's whole design rests on three agreements
that live in different files:

  1. Separation. The part that invents never reads the part that judges. One
     link from `imagination.md` to `judges.md`, added in good faith, ends it.
  2. Lens packs. Each generator gets a different set of tools, which is what
     forces the generators apart. A tool in two packs, or in none, quietly
     removes that.
  3. Stated counts. "Twelve tools", "ten domains", "six components" and "all
     four hold" are stated in prose beside the tables they count.

The same class of defect was found inside the gbb skill by an audit run
(H-001, H-002: two lines of one file disagreeing). These checks cost
milliseconds. Each fails on a real disagreement and on nothing else.

Known limit, stated rather than hidden: nothing here proves a run *obeys* the
separation. That is behaviour, and only a real run shows it.
"""
from __future__ import annotations

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(ROOT, ".claude", "skills", "bonanza")

LINK_RE = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
TOOL_ROW_RE = re.compile(r"^\|\s*(\d+)\.\s", re.M)
TAGS = ("[known]", "[assumed]", "[hoped]")


def read(name: str) -> str:
    with open(os.path.join(SKILL_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def section(text: str, heading: str) -> str:
    """The body under one `## heading`, up to the next heading of the same level."""
    match = re.search(rf"^## {re.escape(heading)}[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if match is None:
        raise AssertionError(f"section not found: {heading!r}")
    return match.group(1)


def links(name: str) -> set[str]:
    return {os.path.basename(target) for target in LINK_RE.findall(read(name))}


class CompanionFiles(unittest.TestCase):
    def test_skill_lists_exactly_the_companions_that_exist(self):
        on_disk = {n for n in os.listdir(SKILL_DIR) if n.endswith(".md")} - {"SKILL.md"}
        block = re.search(r"Companion files beside this one:\n((?:- .*\n)+)", read("SKILL.md"))
        self.assertIsNotNone(block, "SKILL.md lost its companion list")
        listed = {os.path.basename(t) for t in LINK_RE.findall(block.group(1))}
        self.assertEqual(listed, on_disk)


class Separation(unittest.TestCase):
    def test_generators_file_does_not_link_the_judges(self):
        self.assertNotIn("judges.md", links("imagination.md"))
        self.assertNotIn("sharpening.md", links("imagination.md"))

    def test_judges_file_does_not_link_the_generators(self):
        self.assertNotIn("imagination.md", links("judges.md"))

    def test_generator_contract_forbids_a_verdict(self):
        contract = section(read("imagination.md"), "The generator's contract")
        never = re.search(r"\*\*You never return:\*\*([^\n]*(?:\n(?!\n)[^\n]*)*)", contract)
        self.assertIsNotNone(never, "the generator's contract lost its 'never return' clause")
        for word in ("score", "ranking", "risk assessment", "recommendation"):
            self.assertIn(word, never.group(1))

    def test_generator_return_format_has_no_verdict_field(self):
        contract = section(read("imagination.md"), "The generator's contract")
        fenced = re.search(r"```\n(.*?)```", contract, re.S)
        self.assertIsNotNone(fenced)
        self.assertNotIn("Verdict", fenced.group(1))


class LensPacks(unittest.TestCase):
    def setUp(self):
        self.text = read("imagination.md")
        self.tools = sorted(
            int(n)
            for heading in ("Perception tools", "Thinking tools")
            for n in TOOL_ROW_RE.findall(section(self.text, heading))
        )

    def test_tools_are_numbered_without_gaps(self):
        self.assertEqual(self.tools, list(range(1, len(self.tools) + 1)))

    def test_stated_tool_count_matches_the_tables(self):
        self.assertEqual(len(self.tools), 12)
        self.assertIn("twelve perception and thinking tools", read("SKILL.md"))

    def test_every_tool_but_the_shared_one_is_in_exactly_one_pack(self):
        packs = section(self.text, "Lens packs")
        rows = re.findall(r"^\|\s*[A-Z] — [^|]*\|([^|]*)\|", packs, re.M)
        self.assertTrue(rows, "no lens pack rows found")
        assigned = [int(n) for row in rows for n in re.findall(r"\d+", row)]
        shared = re.search(r"Tool (\d+) belongs to every pack", packs)
        self.assertIsNotNone(shared, "the shared tool is no longer named")
        shared_tool = int(shared.group(1))
        self.assertNotIn(shared_tool, assigned)
        self.assertEqual(sorted(assigned + [shared_tool]), self.tools)


class StatedCounts(unittest.TestCase):
    def test_ten_domains(self):
        text = read("knowledge-map.md")
        domains = sorted(int(n) for n in TOOL_ROW_RE.findall(text))
        self.assertEqual(domains, list(range(1, 11)))
        self.assertIn("ten knowledge domains", read("SKILL.md"))

    def test_six_components(self):
        table = section(read("character.md"), "The six components")
        rows = [r for r in re.findall(r"^\|\s*([A-Za-z]+)\s*\|", table, re.M) if r != "Component"]
        self.assertEqual(len(rows), 6, rows)
        self.assertIn("six components", read("SKILL.md"))

    def test_four_decision_rules(self):
        rules = section(read("character.md"), "Decision rules")
        self.assertEqual(len(re.findall(r"^- ", rules, re.M)), 4)
        self.assertIn("all four hold", rules)
        self.assertIn("the four rules", read("SKILL.md"))


class HonestyTags(unittest.TestCase):
    def test_the_three_tags_are_defined_once_and_used_everywhere(self):
        contract = section(read("character.md"), "Honesty")
        defined = re.findall(r"^\|\s*`(\[[a-z]+\])`\s*\|", contract, re.M)
        self.assertEqual(tuple(defined), TAGS)
        for name in ("SKILL.md", "judges.md", "idea-record.md"):
            text = read(name)
            for tag in TAGS:
                self.assertIn(tag, text, f"{name} does not mention {tag}")

    def test_no_file_invents_a_fourth_tag(self):
        allowed = set(TAGS)
        for name in sorted(os.listdir(SKILL_DIR)):
            if not name.endswith(".md"):
                continue
            # Only the lowercase one-word shape a tag has; template placeholders
            # such as [line] and [what] are excluded by name.
            found = set(re.findall(r"\[(?:known|assumed|hoped|unverified|guessed|verified|estimated)\]", read(name)))
            self.assertLessEqual(found, allowed, f"{name}: {found - allowed}")


class RecordLifecycle(unittest.TestCase):
    def test_the_owner_pick_list_matches_the_statuses(self):
        record = read("idea-record.md")
        status_line = re.search(r"\*\*Status:\*\* ([^\n]+)", record)
        self.assertIsNotNone(status_line)
        statuses = {s.strip() for s in status_line.group(1).split("|")}
        self.assertEqual(statuses, {"proposed", "testing", "proven", "killed", "parked"})
        step7 = re.search(r"### Step 7[^\n]*\n(.*?)(?=^### )", read("SKILL.md"), re.M | re.S)
        self.assertIsNotNone(step7)
        for word in ("cheap test", "park", "kill"):
            self.assertIn(word, step7.group(1))


if __name__ == "__main__":
    unittest.main()
