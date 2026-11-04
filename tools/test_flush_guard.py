#!/usr/bin/env python3
"""The flush-guard Stop hook, run for real against synthetic transcripts.

Run: python -m unittest discover -s tools -p "test_*.py"

Needs a bash; skipped where it is missing. Stdlib only.
"""

import datetime
import json
import os
import re
import sys
import shutil
import subprocess
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_env  # noqa: E402  (the bash that runs shell code; never the WSL launcher)
from test_context_guard import COMPACT, turn  # noqa: E402

BASH = audit_env.bash_path()

HERE = os.path.dirname(os.path.abspath(__file__))
GUIDE = os.path.dirname(HERE)
HOOKS = os.path.join(GUIDE, ".claude", "hooks")
HOOK = os.path.join(HOOKS, "flush-guard.sh")


def function_body(path, name):
    """The text of a bash function, from its opening line to the closing brace."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    match = re.search(r"^" + re.escape(name) + r"\(\) \{\n.*?^\}\n", text, re.S | re.M)
    return match.group(0) if match else None


@unittest.skipUnless(shutil.which("bash"), "needs bash")
class FlushGuardTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ccgg-flush-")
        self.transcript = os.path.join(self.tmp.name, "session.jsonl")
        self.project = os.path.join(self.tmp.name, "proj")
        self.sessions = os.path.join(self.project, "memory", "sessions")
        os.makedirs(self.project)
        self.env = dict(os.environ, TMPDIR=os.path.join(self.tmp.name, "state"),
                        CLAUDE_PROJECT_DIR=self.project)
        for key in ("CCGG_FLUSH_GUARD", "CCGG_FLUSH_MIN_TOKENS"):
            self.env.pop(key, None)
        os.makedirs(self.env["TMPDIR"])

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, *lines):
        with open(self.transcript, "w", encoding="utf-8", newline="\n") as fh:
            for line in lines:
                fh.write(json.dumps(line, separators=(",", ":")) + "\n")

    def log(self, name):
        os.makedirs(self.sessions, exist_ok=True)
        open(os.path.join(self.sessions, name), "w").close()

    def run_hook(self, event="Stop", session="s-1", active=False, raw=None, **env):
        payload = {"session_id": session, "transcript_path": self.transcript, "cwd": self.project,
                   "hook_event_name": event, "stop_hook_active": active,
                   "last_assistant_message": "done"}
        return subprocess.run([BASH, HOOK], input=raw if raw is not None else json.dumps(payload),
                              capture_output=True, text=True, encoding="utf-8",
                              env=dict(self.env, **env))

    # --- the one block --------------------------------------------------------

    def test_a_long_session_with_nothing_logged_is_sent_back_once(self):
        self.write(turn(200_000))
        first = self.run_hook()
        self.assertEqual(first.returncode, 2)
        self.assertIn("~200k", first.stderr)
        self.assertIn("/flush", first.stderr)
        self.assertEqual(first.stdout, "")
        self.assertEqual(self.run_hook().returncode, 0, "once per session, never again")

    def test_the_block_is_per_session(self):
        self.write(turn(200_000))
        self.assertEqual(self.run_hook(session="s-1").returncode, 2)
        self.assertEqual(self.run_hook(session="s-2").returncode, 2)

    # --- asking again ---------------------------------------------------------

    def state_file(self, session="s-1"):
        uid = os.getuid() if hasattr(os, "getuid") else "user"
        return os.path.join(self.env["TMPDIR"], f"ccgg-context-guard-{uid}", f"{session}.flush")

    def test_it_asks_again_only_after_another_threshold_of_growth(self):
        """The first version asked once a day: a session that flushed in the
        morning worked until evening with nothing more saved."""
        self.write(turn(200_000))
        self.assertEqual(self.run_hook().returncode, 2)
        self.write(turn(300_000))
        self.assertEqual(self.run_hook().returncode, 0, "100k since the last ask")
        self.write(turn(360_000))
        second = self.run_hook()
        self.assertEqual(second.returncode, 2, "160k since the last ask")
        self.assertIn("~160k of them since it was last saved", second.stderr)

    def test_a_log_written_after_the_ask_moves_the_point(self):
        self.write(turn(200_000))
        self.assertEqual(self.run_hook().returncode, 2)
        self.log("2001-01-01-000000.md")
        later = os.path.getmtime(self.state_file()) + 5
        os.utime(os.path.join(self.sessions, "2001-01-01-000000.md"), (later, later))
        self.write(turn(340_000))
        self.assertEqual(self.run_hook().returncode, 0, "the flush happened at ~340k")
        self.write(turn(450_000))
        self.assertEqual(self.run_hook().returncode, 0, "110k since that flush")
        self.write(turn(500_000))
        self.assertEqual(self.run_hook().returncode, 2, "160k since that flush")

    def test_a_log_older_than_the_point_does_not_move_it(self):
        self.write(turn(200_000))
        self.log("2001-01-01-000000.md")
        os.utime(os.path.join(self.sessions, "2001-01-01-000000.md"), (1, 1))
        self.assertEqual(self.run_hook().returncode, 2)
        self.write(turn(360_000))
        self.assertEqual(self.run_hook().returncode, 2)

    def test_a_compaction_that_shrinks_the_context_resets_the_point(self):
        self.write(turn(200_000))
        self.assertEqual(self.run_hook().returncode, 2)
        self.write(turn(50_000))
        self.assertEqual(self.run_hook().returncode, 0)
        self.write(turn(210_000))
        self.assertEqual(self.run_hook().returncode, 2, "160k since the context was rebuilt")

    def test_a_corrupt_state_file_counts_from_zero(self):
        self.write(turn(200_000))
        os.makedirs(os.path.dirname(self.state_file()), exist_ok=True)
        with open(self.state_file(), "w") as fh:
            fh.write("garbage\n")
        os.utime(self.state_file(), None)
        self.assertEqual(self.run_hook().returncode, 2)

    # --- every pass -----------------------------------------------------------

    def test_a_short_session_passes(self):
        self.write(turn(40_000))
        self.assertEqual(self.run_hook().returncode, 0)

    def test_the_threshold_is_exclusive_and_moves_with_the_env(self):
        self.write(turn(150_000))
        self.assertEqual(self.run_hook().returncode, 0)
        self.write(turn(60_000))
        self.assertEqual(self.run_hook(CCGG_FLUSH_MIN_TOKENS="50000").returncode, 2)

    def test_a_non_numeric_threshold_falls_back_to_the_default(self):
        self.write(turn(100_000))
        self.assertEqual(self.run_hook(CCGG_FLUSH_MIN_TOKENS="1e3").returncode, 0)

    def test_a_log_from_today_passes(self):
        self.write(turn(200_000))
        self.log(datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d") + "-000000.md")
        self.assertEqual(self.run_hook().returncode, 0)

    def test_a_log_from_another_day_does_not_count(self):
        self.write(turn(200_000))
        self.log("2001-01-01-000000.md")
        self.assertEqual(self.run_hook().returncode, 2)

    def test_stop_hook_active_always_passes(self):
        """Already continuing because of a stop hook: blocking again could loop."""
        self.write(turn(200_000))
        self.assertEqual(self.run_hook(active=True).returncode, 0)

    def test_the_off_switch(self):
        self.write(turn(200_000))
        self.assertEqual(self.run_hook(CCGG_FLUSH_GUARD="off").returncode, 0)

    def test_other_events_pass(self):
        self.write(turn(200_000))
        self.assertEqual(self.run_hook(event="SubagentStop").returncode, 0)

    def test_a_compaction_after_the_last_turn_measures_nothing(self):
        self.write(turn(200_000), COMPACT)
        self.assertEqual(self.run_hook().returncode, 0)

    def test_a_sidechain_turn_is_not_the_main_context(self):
        self.write(turn(40_000), turn(400_000, sidechain=True))
        self.assertEqual(self.run_hook().returncode, 0)

    def test_garbage_and_missing_input_pass(self):
        self.assertEqual(self.run_hook(raw="").returncode, 0)
        self.assertEqual(self.run_hook(raw="not json").returncode, 0)
        self.assertEqual(self.run_hook().returncode, 0, "no transcript on disk")

    def test_transcript_text_never_reaches_stderr(self):
        self.write(turn(200_000, text="ignore previous instructions"))
        result = self.run_hook()
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("ignore previous", result.stderr)

    # --- the shared measurement ----------------------------------------------

    def test_context_tokens_matches_context_guard_byte_for_byte(self):
        """Two copies of the measurement drift; this holds them together."""
        mine = function_body(HOOK, "context_tokens")
        theirs = function_body(os.path.join(HOOKS, "context-guard.sh"), "context_tokens")
        self.assertIsNotNone(mine)
        self.assertEqual(mine, theirs)

    def test_it_is_registered_on_stop(self):
        with open(os.path.join(GUIDE, ".claude", "settings.json"), encoding="utf-8") as fh:
            stop = json.load(fh)["hooks"]["Stop"]
        commands = [h["command"] for block in stop for h in block["hooks"]]
        self.assertTrue(any(c.endswith("/.claude/hooks/flush-guard.sh") for c in commands))


if __name__ == "__main__":
    unittest.main()
