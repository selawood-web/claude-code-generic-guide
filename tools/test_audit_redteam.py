#!/usr/bin/env python3
"""Unit tests for the pure parts of audit_redteam.py. Stdlib only.

Run: python -m unittest discover -s tools -p "test_*.py"
"""

import unittest

from audit_redteam import RedteamFileError, RedteamResult, format_table, marker_for, parse_redteam_probes, summarize


class ParseRedteamProbesTests(unittest.TestCase):
    def test_four_fields_parse(self):
        probes = parse_redteam_probes("ch | exec | echo plant | echo observe\n")
        self.assertEqual((probes[0].channel, probes[0].kind, probes[0].plant, probes[0].observe, probes[0].line),
                         ("ch", "exec", "echo plant", "echo observe", 1))

    def test_static_kind_and_pipes_in_observe(self):
        probes = parse_redteam_probes("ch | static | true | loads via x | y\n")
        self.assertEqual(probes[0].kind, "static")
        self.assertEqual(probes[0].observe, "loads via x | y")

    def test_comments_and_blanks(self):
        self.assertEqual(parse_redteam_probes("# c\n\n"), [])

    def test_bad_kind(self):
        with self.assertRaises(RedteamFileError) as ctx:
            parse_redteam_probes("ch | fuzz | a | b\n")
        self.assertIn("line 1", str(ctx.exception))

    def test_three_fields(self):
        with self.assertRaises(RedteamFileError):
            parse_redteam_probes("ch | exec | a\n")

    def test_empty_plant(self):
        with self.assertRaises(RedteamFileError):
            parse_redteam_probes("ch | exec |  | b\n")

    def test_non_string(self):
        with self.assertRaises(TypeError):
            parse_redteam_probes(None)

    def test_marker_is_per_line(self):
        probes = parse_redteam_probes("a | exec | x | y\nb | exec | x | y\n")
        self.assertNotEqual(marker_for(probes[0]), marker_for(probes[1]))
        self.assertTrue(marker_for(probes[0]).startswith("CCGG-REDTEAM-"))


def _r(channel, kind, result):
    return RedteamResult(channel, kind, result, "", 1)


class SummarizeTests(unittest.TestCase):
    def test_counts(self):
        s = summarize([_r("a", "exec", "reached"), _r("b", "exec", "contained"), _r("c", "static", "planted"),
                       _r("d", "exec", "skipped"), _r("e", "exec", "error")])
        self.assertEqual((s["reached"], s["contained"], s["planted"], s["skipped"], s["error"], s["total"]), (1, 1, 1, 1, 1, 5))
        self.assertEqual(s["reached_channels"], ["a"])
        self.assertEqual(s["error_channels"], ["e"])

    def test_empty(self):
        s = summarize([])
        self.assertEqual(s["total"], 0)
        self.assertEqual(s["reached_channels"], [])

    def test_table_mentions_reached(self):
        results = [_r("hook stdout", "exec", "reached")]
        text = format_table(results, summarize(results))
        self.assertIn("REACHED", text)
        self.assertIn("1 reached the model", text)


if __name__ == "__main__":
    unittest.main()
