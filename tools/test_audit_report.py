#!/usr/bin/env python3
"""Unit tests for the schema and renderer in audit_report.py. Stdlib only.

Run: python -m unittest discover -s tools -p "test_*.py"
"""

import contextlib
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


class RunEvidenceTests(unittest.TestCase):
    """Zero findings from a run that never happened must not read as a clean audit."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ccgg-evidence-")
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text="{}"):
        path = os.path.join(self.dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def test_bare_directory_is_incomplete(self):
        self.assertFalse(audit_report.run_evidence(self.dir)["complete"])

    def test_deterministic_artifacts_alone_are_not_evidence_of_an_audit(self):
        self.write("facts.json")
        self.write("probes.json")
        self.write("inventory.json")
        self.assertFalse(audit_report.run_evidence(self.dir)["complete"])

    def test_candidates_stamp_or_records_each_prove_the_run(self):
        for rel in ("candidates/audit-harness.json", "REVISION-abc.json"):
            with self.subTest(rel=rel):
                with tempfile.TemporaryDirectory() as d:
                    path = os.path.join(d, rel)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write("[]")
                    self.assertTrue(audit_report.run_evidence(d)["complete"])
        self.write("findings.jsonl", json.dumps(GOOD) + "\n")
        self.assertTrue(audit_report.run_evidence(self.dir)["complete"])

    def test_empty_findings_file_is_not_evidence(self):
        self.write("findings.jsonl", "\n\n")
        self.assertFalse(audit_report.run_evidence(self.dir)["complete"])

    def test_render_banners_an_incomplete_run(self):
        text = render([], None, None, None, {"complete": False})
        self.assertIn("did not audit anything", text)
        self.assertIn("not a clean bill", text)
        self.assertIn("Incomplete run", text)

    def test_render_says_nothing_extra_for_a_real_clean_run(self):
        text = render([], None, None, None, {"complete": True})
        self.assertNotIn("did not audit anything", text)
        self.assertNotIn("Incomplete", text)

    def test_main_writes_status_json_and_says_incomplete(self):
        self.write("facts.json")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(audit_report.main(["--dir", self.dir]), 0)
        self.assertIn("INCOMPLETE", out.getvalue())
        with open(os.path.join(self.dir, "status.json"), encoding="utf-8") as fh:
            status = json.load(fh)
        self.assertEqual((status["complete"], status["findings"], status["blockers"]), (False, 0, 0))
        with open(os.path.join(self.dir, "REPORT.md"), encoding="utf-8") as fh:
            self.assertIn("not a clean bill", fh.read())

    def test_status_counts_blockers_for_a_complete_run(self):
        self.write("findings.jsonl", json.dumps(dict(GOOD, severity="blocker")) + "\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(audit_report.main(["--dir", self.dir]), 0)
        with open(os.path.join(self.dir, "status.json"), encoding="utf-8") as fh:
            status = json.load(fh)
        self.assertEqual((status["complete"], status["blockers"]), (True, 1))


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


class DeterministicStageTests(unittest.TestCase):
    """A stage that did not run measured nothing, and the report says so (S-011)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def facts(self, scope):
        with open(os.path.join(self.dir, "facts.json"), "w", encoding="utf-8") as fh:
            json.dump({"scope": scope, "facts": []}, fh)

    def touch(self, name):
        with open(os.path.join(self.dir, name), "w", encoding="utf-8") as fh:
            fh.write("{}")

    def test_all_scope_reports_a_missing_redteam_stage(self):
        self.facts("all")
        self.touch("probes.json")
        self.assertEqual(audit_report.run_evidence(self.dir)["stages_missing"], ["redteam"])

    def test_harness_scope_requires_it_too(self):
        self.facts("harness")
        self.touch("probes.json")
        self.assertEqual(audit_report.run_evidence(self.dir)["stages_missing"], ["redteam"])

    def test_process_scope_does_not_require_it(self):
        self.facts("process")
        self.touch("probes.json")
        self.assertEqual(audit_report.run_evidence(self.dir)["stages_missing"], [])

    def test_a_complete_deterministic_stage_reports_nothing_missing(self):
        self.facts("all")
        self.touch("probes.json")
        self.touch("redteam.json")
        self.assertEqual(audit_report.run_evidence(self.dir)["stages_missing"], [])

    def test_an_unknown_scope_reports_only_the_missing_facts(self):
        """No facts.json means no scope to reason from; do not invent a requirement."""
        self.assertEqual(audit_report.run_evidence(self.dir)["stages_missing"], ["facts"])

    def test_a_missing_stage_does_not_by_itself_make_a_run_incomplete(self):
        """`complete` is about the model stage; these are different questions."""
        self.facts("all")
        with open(os.path.join(self.dir, "findings.jsonl"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(GOOD) + "\n")
        evidence = audit_report.run_evidence(self.dir)
        self.assertTrue(evidence["complete"])
        self.assertIn("redteam", evidence["stages_missing"])

    def test_the_report_says_the_red_team_stage_measured_nothing(self):
        text = render([], None, None, None,
                      {"complete": True, "stages_missing": ["redteam"], "scope": "all"})
        self.assertIn("redteam.json", text)
        self.assertIn("not the same as finding none", text)

    def test_a_clean_run_carries_no_warning(self):
        text = render([], None, None, None, {"complete": True, "stages_missing": [], "scope": "all"})
        self.assertNotIn("measured no injection channel", text)
        self.assertNotIn("did not complete", text)

    def test_status_json_carries_the_missing_stages(self):
        self.facts("all")
        self.touch("probes.json")
        audit_report.main(["--dir", self.dir])
        with open(os.path.join(self.dir, "status.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["stages_missing"], ["redteam"])
