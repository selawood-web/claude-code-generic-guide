#!/usr/bin/env python3
"""Unit tests for the pure parts of feature_lint.py. Stdlib only.

Run: python -m unittest discover -s tools -p "test_*.py"
"""

import os
import tempfile
import unittest
from contextlib import contextmanager

from feature_lint import (
    Finding,
    PRE_SHIP_STATUSES,
    bullets,
    check_index,
    counts_as_failure,
    default_paths,
    lint_text,
    parse_frontmatter,
    read_index,
    render_index,
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

## Ideas and changes
- 2026-09-04 — Also export the credit notes — [in]
- 2026-09-04 — Schedule the export monthly — [deferred] after the manual export ships
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


class LedgerTests(unittest.TestCase):
    """The ninth section — capture in flight, close out at ship."""

    # every idea carries a decision, so nothing sits in the file undecided by accident
    def test_untagged_idea_is_a_gap(self):
        text = COMPLETE.replace("Also export the credit notes — [in]", "Also export the credit notes")
        self.assertTrue(any("no [open|in|next|deferred|dropped] tag" in m for m in messages(text)))

    # a cut without a reason is the same as a forgotten one, six months later
    def test_dropped_without_reason_is_a_gap(self):
        text = COMPLETE.replace(
            "- 2026-09-04 — Schedule the export monthly — [deferred] after the manual export ships",
            "- 2026-09-04 — Schedule the export monthly — [dropped]",
        )
        self.assertTrue(any("gives no reason" in m for m in messages(text)))

    def test_deferred_with_reason_is_clean(self):
        self.assertEqual(lint_text(COMPLETE, "F009-bulk-invoice-export.md"), [])

    # an undecided idea is expected while the work is live ...
    def test_open_idea_allowed_while_building(self):
        text = COMPLETE.replace("status: ready", "status: building").replace("[in]", "[open]")
        findings = lint_text(text, "F009-bulk-invoice-export.md")
        self.assertFalse(any(f.level == "error" for f in findings))

    # ... and is the close-out failure at ship: this is the whole point of the ledger
    def test_open_idea_blocks_shipped(self):
        text = COMPLETE.replace("status: ready", "status: shipped").replace("[in]", "[open]")
        findings = lint_text(text, "F009-bulk-invoice-export.md")
        self.assertTrue(
            any(f.level == "error" and "undecided idea" in f.message for f in findings)
        )

    def test_none_yet_is_a_valid_empty_ledger(self):
        text = COMPLETE.replace(
            "- 2026-09-04 — Also export the credit notes — [in]\n"
            "- 2026-09-04 — Schedule the export monthly — [deferred] after the manual export ships",
            "None yet.",
        )
        self.assertEqual(lint_text(text, "F009-bulk-invoice-export.md"), [])

    # edge: a tag in the middle of the sentence still counts, and prose "in" does not
    def test_bare_word_in_is_not_a_tag(self):
        text = COMPLETE.replace(
            "Also export the credit notes — [in]", "Also export the credit notes, in the same file"
        )
        self.assertTrue(any("no [open|in|next|deferred|dropped] tag" in m for m in messages(text)))

    def test_missing_ledger_section_is_an_error(self):
        text = COMPLETE.split("## Ideas and changes")[0]
        findings = lint_text(text, "F009-bulk-invoice-export.md")
        self.assertTrue(
            any(f.level == "error" and "Ideas and changes" in f.message for f in findings)
        )



def with_status(status):
    return COMPLETE.replace("status: ready", f"status: {status}")


def with_ledger(entry, status="ready"):
    """COMPLETE with its ledger replaced by one entry."""
    head = with_status(status).split("## Ideas and changes")[0]
    return head + "## Ideas and changes\n" + entry + "\n"


class PostShipLedgerTests(unittest.TestCase):
    """[next] — the disposition for an idea raised after the definition shipped.

    Before this there was no tag that was both truthful and passing for such an
    idea: [open] is an error at `shipped`, and leaving it untagged is a gap. So
    authors took the third option, which is the one the ledger exists to stop.
    """

    # happy path — the case the tag was added for
    def test_next_passes_on_shipped(self):
        text = with_ledger("- 2026-09-16 — reactions on a message — [next] F011 takes it", "shipped")
        self.assertEqual(messages(text), [])

    # edge: `dropped` is terminal too — a dropped definition may still collect ideas
    def test_next_passes_on_dropped(self):
        text = with_ledger("- 2026-09-16 — reactions — [next] F011 takes it", "dropped")
        self.assertEqual([f for f in lint_text(text, "F009-x.md") if f.level == "error"], [])

    # edge: like [deferred] and [dropped], it must say where the idea went
    def test_next_needs_a_reason(self):
        text = with_ledger("- 2026-09-16 — reactions — [next]", "shipped")
        self.assertTrue(any("gives no reason" in m for m in messages(text)))

    # edge: tag matching stays case-insensitive across the new word
    def test_next_case_insensitive(self):
        text = with_ledger("- 2026-09-16 — reactions — [NEXT] F011", "shipped")
        self.assertEqual(messages(text), [])

    # failure mode — before shipping, [next] is [open] with the blocking filed off
    def test_next_is_an_error_before_shipping(self):
        for status in PRE_SHIP_STATUSES:
            with self.subTest(status=status):
                text = with_ledger("- 2026-09-16 — reactions — [next] F011 takes it", status)
                self.assertTrue(any("use [open] until it ships" in m for m in messages(text)))

    # failure mode — and it fails the run, including in a draft, where gaps are forgiven
    def test_next_in_draft_actually_fails_the_run(self):
        text = with_ledger("- 2026-09-16 — reactions — [next] F011 takes it", "draft")
        errors = [f for f in lint_text(text, "F009-x.md") if f.level == "error"]
        self.assertTrue(any(counts_as_failure(f, "draft", strict=False) for f in errors))

    # the close-out itself is untouched — the whole point of adding a tag rather
    # than loosening the rule that catches an idea shipped over
    def test_open_at_shipped_still_errors(self):
        text = with_ledger("- 2026-09-16 — a thought — [open]", "shipped")
        self.assertTrue(any("undecided idea" in m for m in messages(text)))


class FreeTextBracketTests(unittest.TestCase):
    """An entry may carry its own words in brackets beside the canonical tag.

    Real ledgers record decisions in a richer vocabulary than five words. The
    tag is found by search, so the extra brackets are simply not seen — but one
    canonical tag still has to be there.
    """

    def test_canonical_first_then_free_text(self):
        text = with_ledger("- 2026-09-16 — reactions — [in] [added] a fixed set, selftested")
        self.assertEqual(messages(text), [])

    def test_free_text_first_then_canonical(self):
        text = with_ledger("- 2026-09-16 — reactions — [added] a fixed set — [in]")
        self.assertEqual(messages(text), [])

    def test_bracketed_phrase_is_not_a_tag(self):
        text = with_ledger("- 2026-09-16 — seen marks — [in] [reversed the 2026-09-15 drop] ticks")
        self.assertEqual(messages(text), [])

    def test_verification_record_passes(self):
        text = with_ledger(
            "- 2026-09-16 — [in] Shipped in three PRs, each verified on prod. "
            "[verified] the anchor rule. [not exercised from this seat] the email.",
            "shipped",
        )
        self.assertEqual(messages(text), [])

    # failure mode — free text alone is still not a disposition
    def test_free_text_without_canonical_is_still_a_gap(self):
        text = with_ledger("- 2026-09-16 — reactions — [accepted] a fixed set")
        self.assertTrue(any("no [open|in|next|deferred|dropped] tag" in m for m in messages(text)))


@contextmanager
def repo(definitions, index=None):
    """A throwaway repo root with a features/ directory, as the linter sees it."""
    with tempfile.TemporaryDirectory() as root:
        os.mkdir(os.path.join(root, "features"))
        for name, text in definitions.items():
            with open(os.path.join(root, "features", name), "w", encoding="utf-8") as fh:
                fh.write(text)
        if index is not None:
            with open(os.path.join(root, "features", "README.md"), "w", encoding="utf-8") as fh:
                fh.write(index)
        was = os.getcwd()
        os.chdir(root)
        try:
            yield root
        finally:
            os.chdir(was)


def named(ident, title, status="draft"):
    text = with_status(status)
    text = text.replace("id: F009", f"id: {ident}")
    text = text.replace("title: Bulk invoice export", f"title: {title}")
    return text.replace("# F009 —", f"# {ident} —")


class IndexRenderTests(unittest.TestCase):
    """features/README.md is derived data, rendered from the frontmatter.

    Hand-maintained it conflicted by construction — every new definition appends
    a row to the same table — and its status column drifted from the files it
    describes. Generated, it can do neither.
    """

    def test_two_definitions_render_two_rows(self):
        with repo({"F002-b.md": named("F002", "Second"), "F001-a.md": named("F001", "First")}):
            out = render_index(default_paths())
        rows = [line for line in out.splitlines() if line.startswith("| [")]
        self.assertEqual(len(rows), 2)
        self.assertIn("[F001](F001-a.md)", rows[0])
        self.assertIn("[F002](F002-b.md)", rows[1])

    def test_rows_sort_by_id_not_title(self):
        with repo({"F001-a.md": named("F001", "Zebra"), "F002-b.md": named("F002", "Aardvark")}):
            out = render_index(default_paths())
        rows = [line for line in out.splitlines() if line.startswith("| [")]
        self.assertIn("F001", rows[0])
        self.assertIn("F002", rows[1])

    def test_header_paragraph_kept_verbatim(self):
        header = "# Our Features\n\nHouse rule: every definition names an owner.\n"
        existing = header + "\n| Id | Title | Status | Owner | Target |\n|--|--|--|--|--|\n| stale |\n"
        with repo({"F001-a.md": named("F001", "First")}, index=existing):
            out = render_index(default_paths(), read_index())
        self.assertTrue(out.startswith("# Our Features"))
        self.assertIn("House rule: every definition names an owner.", out)
        self.assertNotIn("stale", out)

    def test_missing_index_gets_a_default_header(self):
        with repo({"F001-a.md": named("F001", "First")}):
            out = render_index(default_paths(), read_index())
        self.assertTrue(out.startswith("# Feature Definitions"))

    def test_pipe_in_a_title_is_escaped(self):
        with repo({"F001-a.md": named("F001", "Plan | Elevation")}):
            out = render_index(default_paths())
        row = next(line for line in out.splitlines() if line.startswith("| ["))
        self.assertIn("Plan \\| Elevation", row)
        self.assertEqual(row.count(" | "), 4)

    def test_render_is_stable(self):
        with repo({"F001-a.md": named("F001", "First")}):
            once = render_index(default_paths(), read_index())
            with open(os.path.join("features", "README.md"), "w", encoding="utf-8") as fh:
                fh.write(once)
            self.assertEqual(render_index(default_paths(), read_index()), once)
            self.assertEqual(check_index(default_paths()), [])


class IndexDriftTests(unittest.TestCase):
    # failure mode — a status hand-copied into the index and left behind
    def test_stale_status_in_the_index_fails(self):
        with repo({"F001-a.md": named("F001", "First", status="shipped")}):
            fresh = render_index(default_paths(), read_index())
            with open(os.path.join("features", "README.md"), "w", encoding="utf-8") as fh:
                fh.write(fresh.replace("| shipped |", "| draft |"))
            findings = check_index(default_paths())
            self.assertEqual([f.level for f in findings], ["error"])
            self.assertIn("--write-index", findings[0].message)

            with open(os.path.join("features", "README.md"), "w", encoding="utf-8") as fh:
                fh.write(render_index(default_paths(), read_index()))
            self.assertEqual(check_index(default_paths()), [])

    # edge: while everything is still a draft, drift is a gap like any other
    def test_drift_is_only_a_gap_while_all_drafts(self):
        with repo({"F001-a.md": named("F001", "First", status="draft")}):
            with open(os.path.join("features", "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Feature Definitions\n\n| Id | Title | Status | Owner | Target |\n")
            self.assertEqual([f.level for f in check_index(default_paths())], ["gap"])

    # edge: an added definition is drift too, which is the conflict case itself
    def test_a_definition_missing_from_the_index_fails(self):
        with repo({"F001-a.md": named("F001", "First", status="ready")}):
            with open(os.path.join("features", "README.md"), "w", encoding="utf-8") as fh:
                fh.write(render_index(default_paths(), read_index()))
            with open(os.path.join("features", "F002-b.md"), "w", encoding="utf-8") as fh:
                fh.write(named("F002", "Second", status="ready"))
            self.assertEqual([f.level for f in check_index(default_paths())], ["error"])

    # edge: no definitions at all is not drift — a project may simply have none
    def test_no_definitions_is_not_drift(self):
        with repo({}):
            self.assertEqual(check_index(default_paths()), [])

    # README.md is the index, never itself a definition to be linted
    def test_readme_is_not_linted_as_a_definition(self):
        with repo({"F001-a.md": named("F001", "First")}):
            with open(os.path.join("features", "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Feature Definitions\n")
            self.assertNotIn("README.md", " ".join(default_paths()))

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


class MainIntegrationTests(unittest.TestCase):
    def test_main_reports_per_file_and_exit_code(self):
        import io
        import os
        import tempfile
        from contextlib import redirect_stdout
        import feature_lint
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "F999-none.md")
            out = io.StringIO()
            with redirect_stdout(out):
                rc = feature_lint.main([missing])
            self.assertEqual(rc, 1)
            self.assertIn("no such file", out.getvalue())
            out = io.StringIO()
            with redirect_stdout(out):
                rc = feature_lint.main(["--strict", missing, missing])
            self.assertIn("2 file(s), 2 failing", out.getvalue())


if __name__ == "__main__":
    unittest.main()
