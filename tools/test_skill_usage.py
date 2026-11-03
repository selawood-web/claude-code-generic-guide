#!/usr/bin/env python3
"""The skill-usage hook, run for real with the payloads Claude Code sends.

Run: python -m unittest discover -s tools -p "test_*.py"

Needs a bash and python3; skipped where either is missing. Stdlib only.
"""

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

BASH = audit_env.bash_path()

HERE = os.path.dirname(os.path.abspath(__file__))
GUIDE = os.path.dirname(HERE)
HOOK = os.path.join(GUIDE, ".claude", "hooks", "skill-usage.sh")
LINE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z (\S+) (model|typed)$")


@unittest.skipUnless(shutil.which("bash") and shutil.which("python3"), "needs bash and python3")
class SkillUsageTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ccgg-usage-")
        self.home = os.path.join(self.tmp.name, "home")
        self.project = os.path.join(self.tmp.name, "proj")
        os.makedirs(self.home)
        os.makedirs(os.path.join(self.project, ".claude", "skills", "commit"))
        open(os.path.join(self.project, ".claude", "skills", "commit", "SKILL.md"), "w").close()
        self.env = dict(os.environ, HOME=self.home, CLAUDE_PROJECT_DIR=self.project)
        self.env.pop("CCGG_SKILL_USAGE", None)

    def tearDown(self):
        self.tmp.cleanup()

    @property
    def log(self):
        return os.path.join(self.home, ".claude", "memory", "proj", "skill-usage.log")

    def lines(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as fh:
            return fh.read().splitlines()

    def run_hook(self, payload=None, raw=None, **env):
        text = raw if raw is not None else json.dumps(payload)
        return subprocess.run([BASH, HOOK], input=text, capture_output=True, text=True,
                              encoding="utf-8", env=dict(self.env, **env))

    def model_call(self, skill):
        # The shape measured on CLI 2.1.317, tool_response included.
        return {"session_id": "s-1", "hook_event_name": "PostToolUse", "tool_name": "Skill",
                "tool_input": {"skill": skill}, "tool_response": {"skill": "decoy", "ok": True}}

    def typed(self, name):
        return {"session_id": "s-1", "hook_event_name": "UserPromptExpansion",
                "expansion_type": "slash_command", "command_name": name, "command_args": "",
                "command_source": "projectSettings"}

    # --- what is recorded -----------------------------------------------------

    def test_a_skill_the_model_calls_is_recorded_once(self):
        result = self.run_hook(self.model_call("commit"))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "", "the hook never speaks")
        self.assertEqual(len(self.lines()), 1)
        self.assertEqual(LINE_RE.match(self.lines()[0]).groups(), ("commit", "model"))

    def test_the_name_comes_from_tool_input_not_the_response(self):
        self.run_hook(self.model_call("commit"))
        self.assertNotIn("decoy", self.lines()[0])

    def test_a_typed_project_skill_is_recorded(self):
        self.run_hook(self.typed("commit"))
        self.assertEqual(LINE_RE.match(self.lines()[0]).groups(), ("commit", "typed"))

    def test_a_typed_user_level_skill_is_recorded(self):
        os.makedirs(os.path.join(self.home, ".claude", "skills", "mine"))
        open(os.path.join(self.home, ".claude", "skills", "mine", "SKILL.md"), "w").close()
        self.run_hook(self.typed("mine"))
        self.assertEqual(LINE_RE.match(self.lines()[0]).group(1), "mine")

    def test_a_typed_plugin_skill_is_recorded(self):
        self.run_hook(self.typed("design:ux-copy"))
        self.assertEqual(LINE_RE.match(self.lines()[0]).group(1), "design:ux-copy")

    def test_lines_append(self):
        self.run_hook(self.model_call("commit"))
        self.run_hook(self.typed("commit"))
        self.assertEqual(len(self.lines()), 2)

    # --- what is not ----------------------------------------------------------

    def test_a_typed_command_that_is_not_a_skill_is_ignored(self):
        self.run_hook(self.typed("compact"))
        self.assertEqual(self.lines(), [])

    def test_other_tools_and_events_are_ignored(self):
        self.run_hook({"hook_event_name": "PostToolUse", "tool_name": "Bash",
                       "tool_input": {"skill": "commit"}})
        self.run_hook({"hook_event_name": "UserPromptSubmit", "prompt": "/commit"})
        self.assertEqual(self.lines(), [])

    def test_a_name_that_could_forge_a_line_is_not_recorded(self):
        for bad in ("commit\n2026-01-01T00:00:00Z evil model", "a b", "x" * 65, "../etc", ".hidden", ""):
            with self.subTest(bad=bad):
                self.run_hook(self.model_call(bad))
        self.assertEqual(self.lines(), [])

    def test_a_non_string_name_is_ignored(self):
        self.run_hook(self.model_call(["commit"]))
        self.run_hook({"hook_event_name": "PostToolUse", "tool_name": "Skill", "tool_input": "commit"})
        self.assertEqual(self.lines(), [])

    def test_garbage_input_passes_silently(self):
        for raw in ("", "not json", "[1, 2]", "null"):
            with self.subTest(raw=raw):
                result = self.run_hook(raw=raw)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout + result.stderr, "")
        self.assertEqual(self.lines(), [])

    def test_the_off_switch(self):
        self.run_hook(self.model_call("commit"), CCGG_SKILL_USAGE="off")
        self.assertEqual(self.lines(), [])

    def test_an_unwritable_log_still_exits_zero(self):
        os.makedirs(os.path.dirname(self.log))
        os.makedirs(self.log)                    # a directory where the file should be
        self.assertEqual(self.run_hook(self.model_call("commit")).returncode, 0)

    def test_each_project_keeps_its_own_log(self):
        other = os.path.join(self.tmp.name, "other")
        os.makedirs(other)
        self.run_hook(self.model_call("commit"), CLAUDE_PROJECT_DIR=other)
        self.assertEqual(self.lines(), [])
        self.assertTrue(os.path.exists(os.path.join(self.home, ".claude", "memory", "other", "skill-usage.log")))

    # --- wiring ---------------------------------------------------------------

    def test_it_is_registered_on_both_events(self):
        with open(os.path.join(GUIDE, ".claude", "settings.json"), encoding="utf-8") as fh:
            hooks = json.load(fh)["hooks"]
        post = [b for b in hooks["PostToolUse"] if b.get("matcher") == "Skill"
                and any(h["command"].endswith("/.claude/hooks/skill-usage.sh") for h in b["hooks"])]
        typed = [b for b in hooks["UserPromptExpansion"]
                 if any(h["command"].endswith("/.claude/hooks/skill-usage.sh") for h in b["hooks"])]
        self.assertEqual((len(post), len(typed)), (1, 1))


if __name__ == "__main__":
    unittest.main()
