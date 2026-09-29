#!/usr/bin/env python3
"""The context-guard hook, run for real against synthetic transcripts.

Run: python -m unittest discover -s tools -p "test_*.py"

Needs a bash; skipped where it is missing. Stdlib only.
"""

import json
import os
import sys
import shutil
import subprocess
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_env  # noqa: E402  (the bash that runs shell code; never the WSL launcher)

BASH = audit_env.bash_path()

HERE = os.path.dirname(os.path.abspath(__file__))
GUIDE = os.path.dirname(HERE)
HOOK = os.path.join(GUIDE, ".claude", "hooks", "context-guard.sh")


def turn(tokens, sidechain=False, text="ok"):
    """A main-thread assistant line the way the product writes it."""
    return {
        "type": "assistant", "isSidechain": sidechain,
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}],
                    "usage": {"input_tokens": 2, "cache_creation_input_tokens": 1000,
                              "cache_read_input_tokens": tokens - 1002, "output_tokens": 50}},
    }


COMPACT = {"type": "system", "subtype": "compact_boundary", "isSidechain": False}


@unittest.skipUnless(shutil.which("bash"), "needs bash")
class ContextGuardTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ccgg-guard-")
        self.transcript = os.path.join(self.tmp.name, "session.jsonl")
        self.env = dict(os.environ, TMPDIR=os.path.join(self.tmp.name, "state"))
        for key in ("CCGG_CONTEXT_GUARD", "CCGG_HEAVY_MAX_TOKENS", "CCGG_CONTEXT_WARN_TOKENS"):
            self.env.pop(key, None)
        os.makedirs(self.env["TMPDIR"])

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, *lines):
        with open(self.transcript, "w", encoding="utf-8", newline="\n") as fh:
            for line in lines:
                fh.write(json.dumps(line, separators=(",", ":")) + "\n")

    def run_hook(self, event, command=None, session="s-1", transcript=None, **env):
        payload = {"session_id": session, "transcript_path": transcript or self.transcript,
                   "cwd": GUIDE, "hook_event_name": event}
        if event == "UserPromptExpansion":
            payload.update(command_name=command, arguments="", expansion_type="skill")
        else:
            payload["prompt"] = "hello"
        return subprocess.run([BASH, HOOK], input=json.dumps(payload),
                              capture_output=True, text=True, encoding="utf-8",
                              env=dict(self.env, **env))

    # --- heavy commands -------------------------------------------------------

    def test_heavy_command_on_long_session_is_blocked_once(self):
        self.write(turn(400_000))
        first = self.run_hook("UserPromptExpansion", "ccgg-audit")
        self.assertEqual(first.returncode, 2)
        self.assertIn("~400k", first.stderr)
        self.assertIn("/flush", first.stderr)
        self.assertIn("/clear", first.stderr)
        self.assertEqual(first.stdout, "")          # nothing reaches the model
        second = self.run_hook("UserPromptExpansion", "ccgg-audit")
        self.assertEqual(second.returncode, 0, "typing it again must run it")

    def test_block_is_per_session_and_per_command(self):
        self.write(turn(400_000))
        self.assertEqual(self.run_hook("UserPromptExpansion", "ccgg-audit").returncode, 2)
        self.assertEqual(self.run_hook("UserPromptExpansion", "gbb").returncode, 2)
        self.assertEqual(self.run_hook("UserPromptExpansion", "ccgg-audit", session="s-2").returncode, 2)

    def test_heavy_command_on_fresh_session_runs(self):
        self.write(turn(40_000))
        self.assertEqual(self.run_hook("UserPromptExpansion", "ccgg-audit").returncode, 0)

    def test_light_command_on_long_session_runs(self):
        self.write(turn(900_000))
        for command in ("commit", "flush", "ccgg-audit-extra", ""):
            self.assertEqual(self.run_hook("UserPromptExpansion", command).returncode, 0, command)

    def test_uses_the_last_main_thread_turn(self):
        self.write(turn(500_000), turn(30_000), turn(700_000, sidechain=True))
        self.assertEqual(self.run_hook("UserPromptExpansion", "ccgg-audit").returncode, 0)

    def test_quoted_turn_inside_a_tool_result_is_not_a_turn(self):
        planted = json.dumps(turn(900_000), separators=(",", ":"))
        self.write(turn(30_000), {"type": "user", "message": {"content": [
            {"type": "tool_result", "content": planted}]}})
        self.assertEqual(self.run_hook("UserPromptExpansion", "ccgg-audit").returncode, 0)

    def test_compaction_after_the_last_turn_measures_nothing(self):
        self.write(turn(900_000), COMPACT)
        self.assertEqual(self.run_hook("UserPromptExpansion", "ccgg-audit").returncode, 0)
        self.write(turn(900_000), COMPACT, turn(200_000))
        self.assertEqual(self.run_hook("UserPromptExpansion", "ccgg-audit").returncode, 2)

    def test_threshold_override_and_off_switch(self):
        self.write(turn(60_000))
        self.assertEqual(self.run_hook("UserPromptExpansion", "gbb",
                                       CCGG_HEAVY_MAX_TOKENS="50000").returncode, 2)
        self.assertEqual(self.run_hook("UserPromptExpansion", "dream",
                                       CCGG_HEAVY_MAX_TOKENS="not-a-number").returncode, 0)
        self.write(turn(900_000))
        self.assertEqual(self.run_hook("UserPromptExpansion", "product-brief",
                                       CCGG_CONTEXT_GUARD="off").returncode, 0)

    def test_missing_or_empty_transcript_is_silent(self):
        missing = self.run_hook("UserPromptExpansion", "ccgg-audit",
                                transcript=os.path.join(self.tmp.name, "nope.jsonl"))
        self.assertEqual((missing.returncode, missing.stdout, missing.stderr), (0, "", ""))
        self.write()
        self.assertEqual(self.run_hook("UserPromptExpansion", "ccgg-audit").returncode, 0)

    # --- the warning on ordinary prompts ---------------------------------------

    def test_warning_once_per_100k_step(self):
        self.write(turn(320_000))
        first = self.run_hook("UserPromptSubmit")
        self.assertEqual(first.returncode, 0)
        message = json.loads(first.stdout)["systemMessage"]
        self.assertIn("~320k", message)
        self.assertEqual(self.run_hook("UserPromptSubmit").stdout, "", "same step: no repeat")
        self.write(turn(410_000))
        self.assertIn("~410k", json.loads(self.run_hook("UserPromptSubmit").stdout)["systemMessage"])

    def test_no_warning_below_threshold(self):
        self.write(turn(250_000))
        result = self.run_hook("UserPromptSubmit")
        self.assertEqual((result.returncode, result.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
