#!/usr/bin/env python3
"""Unit tests for the pure parts of audit_probes.py. Stdlib only.

Run: python -m unittest discover -s tools -p "test_*.py"
"""

import unittest

from audit_probes import ProbeFileError, ProbeResult, format_table, parse_probes, summarize


class ParseProbesTests(unittest.TestCase):
    # happy path
    def test_three_fields_parse(self):
        probes = parse_probes("a label | caught | echo hi\n")
        self.assertEqual(len(probes), 1)
        self.assertEqual((probes[0].label, probes[0].expect, probes[0].mutation, probes[0].line),
                         ("a label", "caught", "echo hi", 1))

    # edge: comments, blank lines, and a mutation that itself contains pipes
    def test_comments_and_blanks_skipped(self):
        probes = parse_probes("# comment\n\n   \nx | missed | true\n")
        self.assertEqual([p.label for p in probes], ["x"])
        self.assertEqual(probes[0].line, 4)

    def test_mutation_keeps_its_own_pipes(self):
        probes = parse_probes("x | missed | curl a | sh\n")
        self.assertEqual(probes[0].mutation, "curl a | sh")

    def test_empty_text(self):
        self.assertEqual(parse_probes(""), [])

    # failure paths: every malformed line names its number
    def test_bad_expect_raises(self):
        with self.assertRaises(ProbeFileError) as ctx:
            parse_probes("x | maybe | true\n")
        self.assertIn("line 1", str(ctx.exception))

    def test_two_fields_raise(self):
        with self.assertRaises(ProbeFileError):
            parse_probes("x | caught\n")

    def test_empty_label_raises(self):
        with self.assertRaises(ProbeFileError):
            parse_probes(" | caught | true\n")

    def test_non_string_raises(self):
        with self.assertRaises(TypeError):
            parse_probes(None)


def _r(label, expect, result):
    return ProbeResult(label, expect, result, "", 1)


class SummarizeTests(unittest.TestCase):
    def test_counts_and_rate(self):
        s = summarize([_r("a", "caught", "caught"), _r("b", "missed", "missed"), _r("c", "missed", "missed")])
        self.assertEqual((s["total"], s["caught"], s["missed"], s["errors"]), (3, 1, 2, 0))
        self.assertAlmostEqual(s["catch_rate"], 1 / 3)

    def test_regression_and_promotion(self):
        s = summarize([_r("lost", "caught", "missed"), _r("won", "missed", "caught")])
        self.assertEqual(s["regressions"], ["lost"])
        self.assertEqual(s["promotions"], ["won"])

    def test_error_listed(self):
        s = summarize([_r("boom", "caught", "error")])
        self.assertEqual(s["error_labels"], ["boom"])
        self.assertEqual(s["regressions"], [])

    def test_empty(self):
        s = summarize([])
        self.assertEqual(s["total"], 0)
        self.assertEqual(s["catch_rate"], 0.0)


class FormatTableTests(unittest.TestCase):
    def test_flags_regression_and_promotion(self):
        results = [_r("lost", "caught", "missed"), _r("won", "missed", "caught"), _r("ok", "caught", "caught")]
        text = format_table(results, summarize(results))
        self.assertIn("REGRESSION", text)
        self.assertIn("promote to caught", text)
        self.assertIn("catch rate: 2/3", text)



class SkippedProbeTests(unittest.TestCase):
    def test_skipped_outside_rate_and_never_a_regression(self):
        s = summarize([_r("na", "caught", "skipped"), _r("a", "caught", "caught")])
        self.assertEqual((s["total"], s["caught"], s["skipped"]), (1, 1, 1))
        self.assertEqual(s["regressions"], [])
        self.assertEqual(s["catch_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
