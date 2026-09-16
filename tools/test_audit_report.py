#!/usr/bin/env python3
"""Unit tests for the schema and renderer in audit_report.py. Stdlib only.

Run: python -m unittest discover -s tools -p "test_*.py"
"""

import json
import os
import tempfile
import contextlib
import io
import unittest

import audit_report


def _quiet_main(argv):
    with contextlib.redirect_stdout(io.StringIO()):
        return audit_report.main(argv)
from audit_report import candidates_as_unverified, load_findings, render, revision_of, validate_record

GOOD = {
    "id": "H-001", "layer": "harness", "class": "dead-mechanism", "severity": "important",
    "confidence": "verified", "location": ".claude/hooks/pre-compact.sh:8",
    "claim": "the hook prints to a channel the model never sees",
    "evidence": "hooks reference, exit code 0", "reproduction": "grep -n echo .claude/hooks/pre-compact.sh",
    "fix": "emit additionalContext JSON", "becomes_check": "hook-stdout fact",
}


class ValidateRecordTests(unittest.TestCase):
    def test_good_record(self):
        self.assertEqual(validate_record(GOOD), [])

    def test_unverified_blocker_rejected(self):
        rec = dict(GOOD, confidence="unverified", severity="blocker", reproduction="")
        self.assertIn("an unverified finding cannot be a blocker", validate_record(rec))

    def test_verified_needs_reproduction(self):
        rec = dict(GOOD, reproduction="")
        self.assertTrue(any("reproduction" in p for p in validate_record(rec)))

    def test_missing_field_named(self):
        rec = dict(GOOD)
        del rec["fix"]
        self.assertEqual(validate_record(rec), ["missing field 'fix'"])

    def test_bad_enum_values(self):
        rec = dict(GOOD, layer="kernel", severity="meh")
        problems = validate_record(rec)
        self.assertEqual(len(problems), 2)

    def test_becomes_check_null_ok(self):
        self.assertEqual(validate_record(dict(GOOD, becomes_check=None)), [])

    def test_non_object(self):
        self.assertEqual(validate_record(["x"]), ["finding is not a JSON object"])


class LoadFindingsTests(unittest.TestCase):
    def test_jsonl_with_blank_lines(self):
        records, problems = load_findings(json.dumps(GOOD) + "\n\n" + json.dumps(dict(GOOD, id="H-002")) + "\n")
        self.assertEqual([r["id"] for r in records], ["H-001", "H-002"])
        self.assertEqual(problems, [])

    def test_bad_json_line_numbered(self):
        records, problems = load_findings("{not json}\n")
        self.assertEqual(records, [])
        self.assertTrue(problems[0].startswith("line 1"))

    def test_empty(self):
        self.assertEqual(load_findings(""), ([], []))

    def test_non_string_raises(self):
        with self.assertRaises(TypeError):
            load_findings(None)


class RenderTests(unittest.TestCase):
    def test_orders_by_severity_then_confidence(self):
        a = dict(GOOD, id="S-1", severity="suggestion")
        b = dict(GOOD, id="B-1", severity="blocker")
        c = dict(GOOD, id="I-unv", severity="important", confidence="unverified", reproduction="")
        d = dict(GOOD, id="I-ver", severity="important")
        text = render([a, b, c, d], None, None, None)
        self.assertLess(text.index("B-1"), text.index("I-ver"))
        self.assertLess(text.index("I-ver"), text.index("I-unv"))
        self.assertLess(text.index("I-unv"), text.index("S-1"))

    def test_counts_probes_and_checks(self):
        probes = {"summary": {"caught": 10, "total": 21, "regressions": [], "promotions": ["x"]}}
        text = render([GOOD], {"facts": [{"status": "finding"}, {"status": "ok"}]}, probes, {"head": "abc", "scope": "all"})
        self.assertIn("**1 finding(s):** 0 blocker, 1 important", text)
        self.assertIn("10/21 probes", text)
        self.assertIn("1 promotion(s)", text)
        self.assertIn("2 fact(s), 1 flagged", text)
        self.assertIn("- H-001: hook-stdout fact", text)

    def test_no_findings(self):
        text = render([], None, None, None)
        self.assertIn("_None verified._", text)
        self.assertIn("_No finding proposes a permanent check._", text)


class CandidateFallbackTests(unittest.TestCase):
    CAND = {"id": "S-001", "layer": "harness", "class": "supply-chain", "severity": "blocker",
            "location": "x.sh:1", "claim": "c", "evidence": "e", "hypothesis": "h", "falsifier": "grep x"}

    def test_blocker_capped_and_unverified(self):
        rec = candidates_as_unverified([self.CAND])[0]
        self.assertEqual((rec["severity"], rec["confidence"]), ("important", "unverified"))
        self.assertIn("grep x", rec["fix"])
        self.assertEqual(validate_record(rec), [])

    def test_missing_fields_defaulted_not_dropped(self):
        rec = candidates_as_unverified([{"id": "X-1"}])[0]
        self.assertEqual(validate_record(rec), [])
        self.assertEqual(rec["layer"], "harness")

    def test_garbage_skipped(self):
        self.assertEqual(candidates_as_unverified([{"claim": "no id"}, "text", 3]), [])


class ReportDirTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ccgg-report-")
        self.dir = self.tmp.name
        os.makedirs(os.path.join(self.dir, "candidates"))
        with open(os.path.join(self.dir, "candidates", "audit-security.json"), "w") as fh:
            json.dump([CandidateFallbackTests.CAND, dict(CandidateFallbackTests.CAND, id="S-002")], fh)
        with open(os.path.join(self.dir, "inventory.json"), "w") as fh:
            json.dump({"head": "abc1234", "dirty": True}, fh)

    def tearDown(self):
        self.tmp.cleanup()

    def report(self):
        with open(os.path.join(self.dir, "REPORT.md"), encoding="utf-8") as fh:
            return fh.read()

    def test_revision_falls_back_to_inventory(self):
        self.assertEqual(revision_of(self.dir)["head"], "abc1234")
        with open(os.path.join(self.dir, "REVISION-abc.json"), "w") as fh:
            json.dump({"head": "stamped"}, fh)
        self.assertEqual(revision_of(self.dir)["head"], "stamped")

    def test_candidates_without_verifier_render_unverified(self):
        self.assertEqual(_quiet_main(["--dir", self.dir]), 0)
        text = self.report()
        self.assertIn("**2 finding(s):** 0 blocker, 2 important, 0 suggestion — 2 unverified.", text)
        self.assertIn("`abc1234`", text)
        self.assertIn("uncommitted changes present", text)

    def test_verifier_records_take_precedence(self):
        with open(os.path.join(self.dir, "findings.jsonl"), "w") as fh:
            fh.write(json.dumps(dict(GOOD, id="S-001", severity="blocker")) + "\n")
        self.assertEqual(_quiet_main(["--dir", self.dir]), 0)
        text = self.report()
        self.assertIn("1 blocker, 1 important", text)
        self.assertEqual(text.count("S-001 —"), 1)

    def test_schema_violation_still_fails(self):
        with open(os.path.join(self.dir, "findings.jsonl"), "w") as fh:
            fh.write(json.dumps(dict(GOOD, confidence="unverified", severity="blocker")) + "\n")
        self.assertEqual(_quiet_main(["--dir", self.dir]), 1)

    def test_missing_dir(self):
        self.assertEqual(_quiet_main(["--dir", os.path.join(self.dir, "nope")]), 2)


if __name__ == "__main__":
    unittest.main()
