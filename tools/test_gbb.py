#!/usr/bin/env python3
"""The GBB skill's own contract — the consistency a reader assumes and nothing checked.

Every other part of this system is measured. GBB shipped as six markdown files
whose only checks were structural: frontmatter keys, working links, catalog
rows. Its internal consistency was checked by a person, once, and both defects
the audit found inside it were exactly that class:

  H-001  the modes table defined the light path as "Steps 1 and 3", and Step 3
         began "Start the product for real", while Step 3's own fallback
         offered the light path for a product that cannot be started.
  H-002  the argument hint listed flags in an order and a shape the modes table
         did not have.

Both are two lines of one file disagreeing. A person caught them at the cost of
an audit run; these cost milliseconds. The checks here are deliberately narrow:
each one fails on a real disagreement and on nothing else, because a check that
cries wolf is a check the next person switches off (the same reasoning as
validate.py's description rules).

Known limit, stated rather than hidden: the council-size check reads the four
phrasings the repository actually uses. A fifth phrasing invented later is not
seen. That is a smaller cost than a regex loose enough to fire on the light
path's "three council members".
"""
from __future__ import annotations

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GBB = os.path.join(ROOT, ".claude", "skills", "gbb")

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}

# Files that describe the council to a reader. A count stated in any of them is
# a claim about the same list of members.
COUNCIL_CLAIM_FILES = (
    ".claude/skills/gbb/SKILL.md",
    ".claude/skills/gbb/design-council.md",
    "USER-MANUAL.md",
    "SYSTEM-OVERVIEW.md",
    "features/F003-gbb.md",
)

# The four phrasings this repository uses to assert the size of the whole
# council. Each captures the count word. "three council members" in the light
# path is not one of them, and must not be.
COUNCIL_CLAIM_RES = (
    re.compile(r"\b([a-z]+) minds\b"),
    re.compile(r"\b([a-z]+)-member design council\b"),
    re.compile(r"\bruns all ([a-z]+)\b"),
    re.compile(r"\bthe ([a-z]+) council members\b"),
)

MEMBER_RE = re.compile(r"^### (\d+)\. The ([^—\n]+?) — ", re.M)
MEMBER_FIELDS = ("From:", "Stance:", "Looks at:", "Signature move:", "Kill question:")


def canonical(text: str) -> str:
    """Lowercase, hyphens as spaces, one space between words.

    The two files hyphenate the test names differently and one of them wraps
    across a line break, so a raw substring test compares typography rather
    than meaning.
    """
    return " ".join(text.lower().replace("-", " ").split())


def read(rel: str) -> str:
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def skill() -> str:
    return read(".claude/skills/gbb/SKILL.md")


def council() -> str:
    return read(".claude/skills/gbb/design-council.md")


def members() -> list[tuple[int, str]]:
    return [(int(n), name.strip()) for n, name in MEMBER_RE.findall(council())]


def modes_rows() -> list[str]:
    """The rows of the Modes table, which is the skill's own list of invocations."""
    body = skill().split("## Modes", 1)[1].split("\n\n", 1)[0]
    return [ln for ln in body.splitlines() if ln.startswith("| `/gbb")]


def flags_in(text: str) -> set[str]:
    return set(re.findall(r"--[a-z][a-z-]*", text))


class ModesAndHintTests(unittest.TestCase):
    """The frontmatter hint and the modes table describe one command (finding H-002)."""

    def test_the_skill_has_modes(self):
        self.assertGreaterEqual(len(modes_rows()), 2, "a Modes table with one row is not a table")

    def test_hint_and_table_name_the_same_flags(self):
        hint = re.search(r"^argument-hint:\s*(.+)$", skill(), re.M)
        self.assertIsNotNone(hint, "the skill states an argument-hint")
        self.assertEqual(
            flags_in(hint.group(1)), flags_in("\n".join(modes_rows())),
            "every mode the table documents is offered in the hint, and no other")

    def test_every_step_a_mode_names_exists(self):
        headings = set(re.findall(r"^### Step (\d+) — ", skill(), re.M))
        self.assertTrue(headings, "the skill has numbered steps")
        for row in modes_rows():
            for step in re.findall(r"\bSteps? ([\d, and]+)", row):
                for n in re.findall(r"\d+", step):
                    self.assertIn(n, headings, f"a mode runs Step {n}, which the skill does not define")

    def test_a_mode_that_cannot_run_the_product_says_so(self):
        """H-001: the fallback for an unstartable product must be a mode, not an aside."""
        rows = "\n".join(modes_rows())
        self.assertIn("--paper", rows,
                      "the product that cannot be started needs a mode of its own; "
                      "offering the light path instead contradicts the light path's definition")
        paper = [r for r in modes_rows() if "--paper" in r][0]
        self.assertIn("not run", paper,
                      "a run on supplied screenshots reports its stranger tests as not run")


class CompanionTests(unittest.TestCase):
    def test_every_companion_is_reachable_from_the_skill(self):
        """A companion nobody links is a file nobody reads."""
        body = skill()
        for name in sorted(os.listdir(GBB)):
            if name == "SKILL.md" or not name.endswith(".md"):
                continue
            self.assertIn(f"]({name})", body, f"{name} is shipped but never linked from SKILL.md")

    def test_the_skill_links_nothing_absent(self):
        for target in re.findall(r"\]\((?!\.\.|http|#)([A-Za-z0-9._-]+\.md)\)", skill()):
            self.assertTrue(os.path.exists(os.path.join(GBB, target)), f"SKILL.md links missing {target}")


class CouncilTests(unittest.TestCase):
    def test_members_are_numbered_from_one_without_gaps(self):
        numbers = [n for n, _ in members()]
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)),
                         "a gap or a repeat in the numbering means a member was added or removed by hand")

    def test_every_member_carries_the_output_contract(self):
        text = council()
        blocks = re.split(r"^### \d+\. ", text, flags=re.M)[1:]
        self.assertEqual(len(blocks), len(members()))
        for (n, name), block in zip(members(), blocks):
            for field in MEMBER_FIELDS:
                self.assertIn(f"**{field}**", block,
                              f"member {n}, the {name}, is missing its {field.rstrip(':')} line")

    def test_every_member_asks_exactly_one_kill_question(self):
        blocks = re.split(r"^### \d+\. ", council(), flags=re.M)[1:]
        for (n, name), block in zip(members(), blocks):
            self.assertEqual(block.count("**Kill question:**"), 1,
                             f"member {n}, the {name}, must ask one kill question, not several")

    def test_stated_council_size_matches_the_members(self):
        """The count drifted across five files when a tenth member was added."""
        size = len(members())
        for rel in COUNCIL_CLAIM_FILES:
            text = read(rel)
            for pattern in COUNCIL_CLAIM_RES:
                for word in pattern.findall(text):
                    if word not in NUMBER_WORDS:
                        continue
                    self.assertEqual(NUMBER_WORDS[word], size,
                                     f"{rel} says the council has {word} members; "
                                     f"design-council.md defines {size}")

    def test_light_path_names_only_members_that_exist(self):
        known = {name for _, name in members()}
        table = council().split("## Light path", 1)[1].split("##", 1)[0]
        rows = [ln for ln in table.splitlines() if ln.startswith("|") and "---" not in ln][1:]
        self.assertTrue(rows, "the light path table has rows")
        for row in rows:
            listed = [n.strip() for n in row.split("|")[2].split(",")]
            self.assertEqual(len(listed), 3, f"the light path runs three members, not {len(listed)}: {row.strip()}")
            for name in listed:
                self.assertIn(name, known, f"the light path names '{name}', who is not a council member")


class LadderTests(unittest.TestCase):
    def test_the_stranger_tests_are_the_same_five_in_both_files(self):
        ladder = read(".claude/skills/gbb/gbb-ladder.md")
        table = ladder.split("## The stranger tests", 1)[1].split("##", 1)[0]
        defined = [canonical(m) for m in re.findall(r"^\| \*\*([^*]+)\*\*", table, re.M)]
        self.assertEqual(len(defined), 5, f"five stranger tests define the ladder's numbers, found {len(defined)}")
        named = canonical(skill().split("### Step 3", 1)[1].split("### Step 4", 1)[0])
        for test in defined:
            self.assertIn(test, named,
                          f"Step 3 times the stranger tests but never names '{test}'")

    def test_every_stranger_test_has_a_pass_bar(self):
        ladder = read(".claude/skills/gbb/gbb-ladder.md")
        table = ladder.split("## The stranger tests", 1)[1].split("##", 1)[0]
        for row in [ln for ln in table.splitlines() if ln.startswith("| **")]:
            cells = [c.strip() for c in row.split("|")[1:-1]]
            self.assertEqual(len(cells), 4, f"a stranger test states task, measure and pass bar: {row.strip()}")
            self.assertTrue(cells[3], f"the test '{cells[0]}' has no pass bar, so it can never be passed")


class IntentTests(unittest.TestCase):
    def test_the_intent_covers_every_part_of_the_language(self):
        """The design vocabulary the owner asked for, each with a reason and a test."""
        intent = read(".claude/skills/gbb/design-intent.md")
        section = intent.split("### 5. The language", 1)[1].split("### 6.", 1)[0]
        for heading in ("Colour", "Type", "Icons", "Layout and spacing", "Motion", "Voice and copy"):
            self.assertIn(f"**{heading}**", section, f"the language section defines no {heading} decisions")
        self.assertIn("Tests:", section, "a language decision without a test is a hope")

    def test_the_intent_is_written_before_the_ladder_measures_it(self):
        self.assertIn("--intent", skill(), "the intent half needs a mode that writes it")
        self.assertIn("design-intent.md", skill(), "Step 1 reads the intent before the walk")


if __name__ == "__main__":
    unittest.main()
