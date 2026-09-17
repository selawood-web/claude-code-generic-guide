#!/usr/bin/env python3
"""Unit tests for audit_redteam.py. Stdlib only.

Run: python -m unittest discover -s tools -p "test_*.py"

The parse and summary helpers were the only things covered here. run_probe —
the function that decides whether a planted marker `reached` the model or was
`contained` — and main were executed by no test at all, so the harness the audit
uses to prove containment had nothing proving the harness (finding T-002). The
classes below run them for real against a throwaway git repository.
"""

import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout

import audit_redteam
from audit_redteam import (RedteamFileError, RedteamProbe, RedteamResult, format_table, main,
                           make_scratch_copy, marker_for, parse_redteam_probes, run_probe, summarize)


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




@unittest.skipUnless(shutil.which("git") and shutil.which("bash") and shutil.which("tar"),
                     "needs git, bash and tar")
class ScratchCopyTests(unittest.TestCase):
    """make_scratch_copy: HEAD unpacked, committed once, with a private HOME."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ccgg-rt-test-")
        self.repo = os.path.join(self.tmp.name, "repo")
        os.makedirs(self.repo)
        write(self.repo, "kept.txt", "committed\n")
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base")
        self.scratch = os.path.join(self.tmp.name, "scratch")
        os.makedirs(self.scratch)

    def tearDown(self):
        self.tmp.cleanup()

    def test_head_is_unpacked_and_committed(self):
        dest, _ = make_scratch_copy(self.repo, self.scratch)
        self.assertTrue(os.path.isfile(os.path.join(dest, "kept.txt")))
        self.assertEqual(git(dest, "status", "--porcelain"), "")

    def test_uncommitted_work_does_not_travel(self):
        write(self.repo, "scratch-only.txt", "uncommitted\n")
        dest, _ = make_scratch_copy(self.repo, self.scratch)
        self.assertFalse(os.path.exists(os.path.join(dest, "scratch-only.txt")))

    def test_home_is_private_and_carries_no_operator_credentials(self):
        _, env = make_scratch_copy(self.repo, self.scratch)
        self.assertTrue(env["HOME"].startswith(self.scratch))
        self.assertTrue(os.path.isdir(env["HOME"]))
        self.assertEqual(audit_redteam.audit_env.leaked_names(env, allow=("MARKER",)), [])


@unittest.skipUnless(shutil.which("git") and shutil.which("bash") and shutil.which("tar"),
                     "needs git, bash and tar")
class RunProbeTests(unittest.TestCase):
    """Every verdict run_probe can return, produced by a real plant and observe."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ccgg-rt-test-")
        self.repo = os.path.join(self.tmp.name, "repo")
        os.makedirs(self.repo)
        write(self.repo, "page.md", "a line\n")
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base")
        scratch = os.path.join(self.tmp.name, "scratch")
        os.makedirs(scratch)
        self.scratch_repo, self.env = make_scratch_copy(self.repo, scratch)

    def tearDown(self):
        self.tmp.cleanup()

    def probe(self, kind="exec", plant='echo "$MARKER" >> page.md', observe="cat page.md", line=7):
        return RedteamProbe("a channel", kind, plant, observe, line)

    def test_a_marker_the_observation_prints_is_reached(self):
        result = run_probe(self.probe(), self.scratch_repo, self.env)
        self.assertEqual(result.result, "reached")
        self.assertIn(marker_for(self.probe()), result.detail)

    def test_a_marker_the_observation_never_prints_is_contained(self):
        result = run_probe(self.probe(observe="echo nothing to see"), self.scratch_repo, self.env)
        self.assertEqual(result.result, "contained")

    def test_an_observation_that_prints_nothing_at_all_is_contained(self):
        result = run_probe(self.probe(observe="true"), self.scratch_repo, self.env)
        self.assertEqual(result.result, "contained")
        self.assertIn("0 bytes", result.detail)

    def test_a_static_probe_is_planted_and_the_observation_never_runs(self):
        result = run_probe(self.probe(kind="static", observe="echo $MARKER > SHOULD-NOT-EXIST"),
                           self.scratch_repo, self.env)
        self.assertEqual(result.result, "planted")
        self.assertFalse(os.path.exists(os.path.join(self.scratch_repo, "SHOULD-NOT-EXIST")))

    def test_a_plant_that_reports_not_applicable_is_skipped(self):
        result = run_probe(self.probe(plant="exit 3"), self.scratch_repo, self.env)
        self.assertEqual(result.result, "skipped")

    def test_an_observation_that_reports_not_applicable_is_skipped(self):
        result = run_probe(self.probe(observe="exit 3"), self.scratch_repo, self.env)
        self.assertEqual(result.result, "skipped")

    def test_a_plant_that_fails_is_an_error_and_not_a_verdict(self):
        result = run_probe(self.probe(plant="echo boom >&2; exit 9"), self.scratch_repo, self.env)
        self.assertEqual(result.result, "error")
        self.assertIn("exited 9", result.detail)

    def test_the_marker_is_per_probe_so_one_probe_cannot_answer_for_another(self):
        first = run_probe(self.probe(line=7), self.scratch_repo, self.env)
        second = run_probe(self.probe(line=8, plant="true", observe="cat page.md"),
                           self.scratch_repo, self.env)
        self.assertEqual(first.result, "reached")
        self.assertEqual(second.result, "contained", "a stale plant answered for the next probe")

    def test_the_tree_is_reset_between_probes(self):
        run_probe(self.probe(plant="echo junk > left-behind.txt"), self.scratch_repo, self.env)
        run_probe(self.probe(plant="true", observe="ls"), self.scratch_repo, self.env)
        self.assertFalse(os.path.exists(os.path.join(self.scratch_repo, "left-behind.txt")))

    def test_the_private_home_is_reset_between_probes(self):
        """A probe that writes to ~/.claude must not still be there for the next one.

        The wipe happens at the start of each probe, so the assertion belongs
        after the second call, not the first.
        """
        run_probe(self.probe(plant='mkdir -p "$HOME/.claude" && echo x > "$HOME/.claude/CLAUDE.md"'),
                  self.scratch_repo, self.env)
        self.assertTrue(os.path.exists(os.path.join(self.env["HOME"], ".claude")))
        run_probe(self.probe(line=8, plant="true", observe="true"), self.scratch_repo, self.env)
        self.assertFalse(os.path.exists(os.path.join(self.env["HOME"], ".claude")))

    def test_a_plant_cannot_see_the_operator_credentials(self):
        """S-004's rule, asserted where a plant would actually read it.

        The observation reports the marker only if the canary is in its
        environment, so `reached` here would mean the leak, not the plant.
        """
        os.environ["CCGG_TEST_CANARY"] = "must-not-leak"
        try:
            result = run_probe(
                self.probe(plant='printenv > seen.txt',
                           observe='grep -q must-not-leak seen.txt && echo "$MARKER" || true'),
                self.scratch_repo, self.env)
        finally:
            del os.environ["CCGG_TEST_CANARY"]
        self.assertEqual(result.result, "contained", "the operator's environment reached a plant")


@unittest.skipUnless(shutil.which("git") and shutil.which("bash") and shutil.which("tar"),
                     "needs git, bash and tar")
class MainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ccgg-rt-main-")
        self.repo = os.path.join(self.tmp.name, "repo")
        os.makedirs(os.path.join(self.repo, "tools"))
        write(self.repo, "page.md", "a line\n")

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self):
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base")

    def run_main(self, *extra):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(["--repo", self.repo, *extra])
        return code, buffer.getvalue()

    def test_a_missing_probes_file_is_not_a_failure(self):
        self.commit()
        code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("nothing to measure", out)

    def test_a_malformed_probes_file_fails_loudly(self):
        write(self.repo, "tools/redteam_probes.txt", "only | three | fields\n")
        self.commit()
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("line 1", out)

    def test_a_full_run_writes_the_verdicts_it_measured(self):
        write(self.repo, "tools/redteam_probes.txt",
              "reaching | exec | echo \"$MARKER\" >> page.md | cat page.md\n"
              "held | exec | echo \"$MARKER\" >> page.md | echo quiet\n"
              "described | static | echo \"$MARKER\" >> page.md | loaded at session start\n")
        self.commit()
        out_dir = os.path.join(self.tmp.name, "report")
        code, printed = self.run_main("--out", out_dir)
        self.assertEqual(code, 0)
        self.assertIn("reached the model", printed)
        with open(os.path.join(out_dir, "redteam.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["summary"]["total"], 3)
        self.assertEqual(data["summary"]["reached"], 1)
        self.assertEqual(data["summary"]["contained"], 1)
        self.assertEqual(data["summary"]["planted"], 1)
        self.assertEqual(data["summary"]["reached_channels"], ["reaching"])
        self.assertEqual([p["result"] for p in data["probes"]], ["reached", "contained", "planted"])


def git(cwd, *args):
    return subprocess.check_output(
        ["git", *args], cwd=cwd, text=True, encoding="utf-8",
        env=dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@local",
                 GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@local"))


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


if __name__ == "__main__":
    unittest.main()
