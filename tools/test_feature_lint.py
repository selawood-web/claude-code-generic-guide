#!/usr/bin/env python3
"""Unit tests for the pure parts of feature_lint.py. Stdlib only.

Run: python -m unittest discover -s tools -p "test_*.py"
"""

import unittest

from feature_lint import (
    Finding,
    bullets,
    counts_as_failure,
    lint_text,
    parse_frontmatter,
    split_sections,
    strip_code_blocks,
)

COMPLETE = """---
id: F009
title: Bulk invoice export
status: ready
owner: finance lead
target: 2026-Q4
---

# F009 — Bulk invoice export

## Summary
Finance can export a month of invoices in one file instead of clicking each one.

## Problem
Closing the month costs a day of manual downloads.

## Outcome
- Metric: month-end close, from 8 hours to 30 minutes, measured by the close checklist

## Scope
- A finance user can export a date range as one file

## Non-goals
- Not a scheduled export — that is a later feature

## Acceptance criteria
- Given 200 invoices in a month, when the user exports it, then one file contains all 200
- Given an empty month, when the user exports it, then an empty file downloads with headers

## Dependencies and risks
Depends on the invoice service staying available during the export.

## Open questions
- Which timezone bounds the range? — owner: finance lead, blocks: no
"""


def messages(text, filename="F009-bulk-invoice-export.md"):
    return [f.message for f in lint_text(text, filename)]


class FrontmatterTests(unittest.TestCase):
    # happy path — flat keys parse, values unquoted
    def test_parses_flat_keys(self):
        fields, problems = parse_frontmatter(COMPLETE)
        self.assertEqual(problems, [])
        self.assertEqual(fields["id"], "F009")
        self.assertEqual(fields["target"], "2026-Q4")

    # failure mode — no opening fence at all
    def test_missing_open_fence(self):
        _, problems = parse_frontmatter("# Title\n")
        self.assertEqual(problems[0].level, "error")

    # failure mode — opened and never closed
    def test_unclosed_frontmatter(self):
        _, problems = parse_frontmatter("---\nid: F001\n# Title\n")
        self.assertIn("never closed", problems[0].message)

    # edge: empty input must not raise
    def test_empty_text(self):
        fields, problems = parse_frontmatter("")
        self.assertEqual(fields, {})
        self.assertEqual(len(problems), 1)


class SectionTests(unittest.TestCase):
    def test_sections_are_lowercased_and_carry_bodies(self):
        sections = split_sections(COMPLETE)
        self.assertIn("non-goals", sections)
        self.assertTrue(sections["summary"][1])

    # edge: a fenced example inside a definition is never read as content
    def test_code_blocks_blanked(self):
        lines = strip_code_blocks(["## Scope", "```", "## Fake", "```", "real"])
        self.assertNotIn("## Fake", lines)

    # edge: a wrapped bullet stays one item, so Given/When/Then survives wrapping
    def test_bullet_continuation_joined(self):
        items = bullets(["- Given a month,", "  when exported, then one file"])
        self.assertEqual(len(items), 1)
        self.assertIn("then one file", items[0])


class LintTests(unittest.TestCase):
    # happy path — a complete definition is silent
    def test_complete_definition_is_clean(self):
        self.assertEqual(lint_text(COMPLETE, "F009-bulk-invoice-export.md"), [])

    # the point of the tool: a missing section is structural, not advisory
    def test_missing_section_is_an_error(self):
        text = COMPLETE.replace("## Non-goals\n- Not a scheduled export — that is a later feature\n", "")
        findings = lint_text(text, "F009-bulk-invoice-export.md")
        self.assertTrue(any(f.level == "error" and "non-goals" in f.message.lower() for f in findings))

    # a heading with nothing under it reads finished and is not
    def test_empty_section_is_an_error(self):
        text = COMPLETE.replace("Closing the month costs a day of manual downloads.\n", "")
        self.assertTrue(any(f.level == "error" and "empty" in f.message for f in lint_text(text)))

    def test_unknown_status_rejected(self):
        self.assertTrue(any("not one of" in m for m in messages(COMPLETE.replace("status: ready", "status: cooking"))))

    # the file and its tracker item must never drift apart
    def test_filename_must_carry_the_id(self):
        self.assertTrue(any("does not start with the id" in m for m in messages(COMPLETE, "invoices.md")))

    def test_bad_id_shape_rejected(self):
        self.assertTrue(any("tracker-style id" in m for m in messages(COMPLETE.replace("id: F009", "id: the big one"))))

    def test_placeholder_is_a_gap(self):
        findings = lint_text(COMPLETE.replace("finance lead", "TBD"), "F009-bulk-invoice-export.md")
        self.assertTrue(any(f.level == "gap" and "placeholder" in f.message for f in findings))

    # "users will like it" is the failure this catches
    def test_unmeasurable_outcome_is_a_gap(self):
        text = COMPLETE.replace(
            "- Metric: month-end close, from 8 hours to 30 minutes, measured by the close checklist",
            "- Users are happier with the close process",
        )
        self.assertTrue(any("measurable" in m for m in messages(text)))

    def test_one_criterion_is_not_enough(self):
        text = COMPLETE.replace(
            "- Given an empty month, when the user exports it, then an empty file downloads with headers\n",
            "",
        )
        self.assertTrue(any("Given/When/Then" in m for m in messages(text)))

    # a feature list masquerading as acceptance criteria
    def test_non_testable_criteria_flagged(self):
        text = COMPLETE.replace(
            "- Given 200 invoices in a month, when the user exports it, then one file contains all 200",
            "- Export works",
        )
        self.assertTrue(any("Given/When/Then" in m for m in messages(text)))

    def test_open_question_without_blocks_marker(self):
        text = COMPLETE.replace(" — owner: finance lead, blocks: no", "")
        self.assertTrue(any("blocks: yes|no" in m for m in messages(text)))

    # a blocking question past draft is a contradiction, so it is an error
    def test_blocking_question_past_draft_is_an_error(self):
        text = COMPLETE.replace("blocks: no", "blocks: yes")
        findings = lint_text(text, "F009-bulk-invoice-export.md")
        self.assertTrue(any(f.level == "error" and "blocking open question" in f.message for f in findings))

    # ... and the same question in a draft is merely a draft
    def test_blocking_question_in_draft_is_tolerated(self):
        text = COMPLETE.replace("status: ready", "status: draft").replace("blocks: no", "blocks: yes")
        findings = lint_text(text, "F009-bulk-invoice-export.md")
        self.assertFalse(any(f.level == "error" for f in findings))

    def test_none_is_a_valid_open_questions_answer(self):
        text = COMPLETE.replace(
            "- Which timezone bounds the range? — owner: finance lead, blocks: no", "None."
        )
        self.assertEqual(lint_text(text, "F009-bulk-invoice-export.md"), [])

    def test_long_summary_is_a_gap(self):
        text = COMPLETE.replace(
            "Finance can export a month of invoices in one file instead of clicking each one.",
            "word " * 70,
        )
        self.assertTrue(any("the cap is" in m for m in messages(text)))

    # edge: garbage input produces findings, never an exception
    def test_garbage_does_not_raise(self):
        self.assertTrue(lint_text("", "x.md"))
        self.assertTrue(lint_text("just some prose", "x.md"))


class SeverityPolicyTests(unittest.TestCase):
    gap = Finding("gap", 1, "gap")
    error = Finding("error", 1, "error")

    def test_error_always_fails(self):
        self.assertTrue(counts_as_failure(self.error, "draft", strict=False))

    def test_gap_tolerated_in_draft(self):
        self.assertFalse(counts_as_failure(self.gap, "draft", strict=False))

    def test_gap_fails_past_draft(self):
        self.assertTrue(counts_as_failure(self.gap, "ready", strict=False))

    def test_strict_fails_drafts_too(self):
        self.assertTrue(counts_as_failure(self.gap, "draft", strict=True))


if __name__ == "__main__":
    unittest.main()
