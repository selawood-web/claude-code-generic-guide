#!/usr/bin/env python3
"""Unit tests for the pure parts of audit_probes.py. Stdlib only.

Run: python -m unittest discover -s tools -p "test_*.py"
"""

import json
import os
import subprocess
import tempfile
import contextlib
import io
import unittest

import audit_probes


def _quiet_main(argv):
    with contextlib.redirect_stdout(io.StringIO()):
        return audit_probes.main(argv)
from audit_probes import (
    Probe,
    ProbeFileError,
    ProbeResult,
    format_table,
    make_scratch_copy,
    parse_probes,
    probe_env,
    run_probe,
    summarize,
)


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


class ProbeEnvTests(unittest.TestCase):
    def test_minimal_env_with_private_home(self):
        with tempfile.TemporaryDirectory() as scratch:
            os.environ["CCGG_PROBE_TEST_SECRET"] = "leak"
            os.environ["CCGG_HOME"] = "/nowhere"
            try:
                env = probe_env(scratch)
            finally:
                del os.environ["CCGG_PROBE_TEST_SECRET"]
                del os.environ["CCGG_HOME"]
            self.assertNotIn("CCGG_PROBE_TEST_SECRET", env)
            self.assertNotIn("CCGG_HOME", env)
            self.assertTrue(env["HOME"].startswith(scratch))
            self.assertTrue(os.path.isdir(env["HOME"]))
            self.assertIn("PATH", env)


def _tiny_repo(root: str) -> str:
    repo = os.path.join(root, "src")
    os.makedirs(repo)
    with open(os.path.join(repo, "README.md"), "w") as fh:
        fh.write("# tiny\n")
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@l", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@l")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "init"]):
        subprocess.run(cmd, cwd=repo, env=env, check=True, capture_output=True)
    return repo


GATE = ["bash", "-c", "test ! -e BROKEN"]


class RunProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ccgg-probe-test-")
        self.repo = _tiny_repo(self.tmp.name)
        self.scratch = os.path.join(self.tmp.name, "scratch")
        os.makedirs(self.scratch)
        self.copy, self.env = make_scratch_copy(self.repo, self.scratch)

    def tearDown(self):
        self.tmp.cleanup()

    def probe(self, mutation, expect="caught"):
        return run_probe(Probe("p", expect, mutation, 1), self.copy, GATE, self.env)

    def test_scratch_is_a_committed_copy_with_its_own_env(self):
        self.assertTrue(os.path.exists(os.path.join(self.copy, "README.md")))
        self.assertTrue(os.path.exists(os.path.join(self.copy, ".git")))
        self.assertTrue(self.env["HOME"].startswith(self.scratch))

    def test_caught_and_missed(self):
        self.assertEqual(self.probe("touch BROKEN").result, "caught")
        self.assertEqual(self.probe("echo fine > README.md").result, "missed")

    def test_reset_between_probes_is_complete(self):
        self.probe("touch BROKEN")
        self.assertEqual(self.probe("true").result, "missed")
        self.assertFalse(os.path.exists(os.path.join(self.copy, "BROKEN")))

    def test_mutation_cannot_see_the_operator_environment(self):
        os.environ["CCGG_PROBE_TEST_SECRET"] = "leak"
        try:
            r = self.probe('[ -z "${CCGG_PROBE_TEST_SECRET:-}" ] || exit 9')
        finally:
            del os.environ["CCGG_PROBE_TEST_SECRET"]
        self.assertEqual(r.result, "missed", r.detail)

    def test_mutation_home_is_private(self):
        r = self.probe('mkdir -p "$HOME/.claude" && echo x > "$HOME/.claude/planted"')
        self.assertEqual(r.result, "missed", r.detail)
        self.assertTrue(os.path.exists(os.path.join(self.env["HOME"], ".claude", "planted")))
        self.assertFalse(os.path.exists(os.path.expanduser("~/.claude/planted")))

    def test_empty_mutation_is_an_error(self):
        self.assertEqual(self.probe("   ").result, "error")

    def test_skip_and_failing_mutation(self):
        self.assertEqual(self.probe("exit 3").result, "skipped")
        r = self.probe("exit 7")
        self.assertEqual(r.result, "error")
        self.assertIn("exited 7", r.detail)


class MainIntegrationTests(unittest.TestCase):
    def test_end_to_end_writes_probes_json_and_reports_regressions(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-probe-main-") as tmp:
            repo = _tiny_repo(tmp)
            with open(os.path.join(repo, "probes.txt"), "w") as fh:
                fh.write("# probes\nplant | caught | touch BROKEN\nquiet | missed | echo x > README.md\n"
                         "regressed | caught | true\nna | caught | exit 3\n")
            out = os.path.join(tmp, "out")
            rc = _quiet_main(["--repo", repo, "--probes", "probes.txt", "--gate", "bash -c 'test ! -e BROKEN'", "--out", out])
            self.assertEqual(rc, 1)
            with open(os.path.join(out, "probes.json")) as fh:
                data = json.load(fh)
            self.assertEqual(data["summary"]["regressions"], ["regressed"])
            self.assertEqual((data["summary"]["caught"], data["summary"]["skipped"]), (1, 1))

    def test_a_missing_probes_file_is_a_failure_not_a_clean_sheet(self):
        """T-001: a gate that measured nothing used to report the same as a clean one."""
        with tempfile.TemporaryDirectory(prefix="ccgg-probe-main-") as tmp:
            repo = _tiny_repo(tmp)
            rc = _quiet_main(["--repo", repo, "--probes", "nope.txt"])
            self.assertEqual(rc, 1, "a mistyped --probes path was a silent success")

    def test_a_probes_file_with_no_probes_is_a_failure(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-probe-main-") as tmp:
            repo = _tiny_repo(tmp)
            with open(os.path.join(repo, "probes.txt"), "w") as fh:
                fh.write("# every probe commented out\n\n")
            self.assertEqual(_quiet_main(["--repo", repo, "--probes", "probes.txt"]), 1)

    def test_clean_run_exits_zero(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-probe-main-") as tmp:
            repo = _tiny_repo(tmp)
            with open(os.path.join(repo, "probes.txt"), "w") as fh:
                fh.write("plant | caught | touch BROKEN\n")
            self.assertEqual(_quiet_main(["--repo", repo, "--probes", "probes.txt", "--gate", "bash -c 'test ! -e BROKEN'"]), 0)


if __name__ == "__main__":
    unittest.main()
