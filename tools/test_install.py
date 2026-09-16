#!/usr/bin/env python3
"""Install contract tests: install.sh and update.sh agree, and a fresh install validates.

The first test reads both scripts and checks that every CCGG-owned tools file
update.sh syncs is one install.sh copies (the probe lists are installed once and
never synced, by design). The second runs install.sh into an empty `git init`
repository and asserts the validator passes there on the first run — F002's
fresh-install criterion, previously stated and never tested.
"""

import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL_FILE_RE = re.compile(r"tools/[A-Za-z0-9_]+\.(?:py|json|txt)")


def tool_files(script: str) -> set[str]:
    with open(os.path.join(ROOT, script), encoding="utf-8") as fh:
        body = "\n".join(ln for ln in fh.read().splitlines() if not ln.lstrip().startswith("#"))
    return set(TOOL_FILE_RE.findall(body))


class InstallSetTests(unittest.TestCase):
    def test_update_syncs_only_what_install_copies(self):
        installed = tool_files("install.sh")
        synced = tool_files("update.sh")
        self.assertTrue(synced <= installed, f"update.sh syncs files install.sh never copies: {sorted(synced - installed)}")
        self.assertEqual(installed - synced, {"tools/probes.txt", "tools/redteam_probes.txt"},
                         "the only installed-but-never-synced tools files are the project's own probe contracts")

    def test_hook_count_label_matches_hooks_shipped(self):
        hooks = [f for f in os.listdir(os.path.join(ROOT, ".claude", "hooks")) if f.endswith(".sh")]
        with open(os.path.join(ROOT, "install.sh"), encoding="utf-8") as fh:
            label = re.search(r'\.claude/hooks/ \((\d+) hooks', fh.read())
        self.assertIsNotNone(label, "install.sh names the hook count it copies")
        self.assertEqual(int(label.group(1)), len(hooks))


class FreshInstallTests(unittest.TestCase):
    def test_fresh_install_validates_on_first_run(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-install-") as tmp:
            target = os.path.join(tmp, "project")
            os.makedirs(target)
            env = dict(os.environ, HOME=os.path.join(tmp, "home"), GIT_CONFIG_NOSYSTEM="1",
                       GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@local", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@local")
            os.makedirs(env["HOME"])
            subprocess.run(["git", "init", "-q"], cwd=target, env=env, check=True)
            install = subprocess.run(["bash", os.path.join(ROOT, "install.sh"), target], env=env,
                                     capture_output=True, text=True)
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            self.assertNotIn("validator reported findings", install.stdout)
            subprocess.run(["git", "add", "-A"], cwd=target, env=env, check=True)
            gate = subprocess.run([sys.executable, "tools/validate.py"], cwd=target, env=env, capture_output=True, text=True)
            self.assertEqual(gate.returncode, 0, gate.stdout)
            for rel in (".claude/skills/ccgg-audit/SKILL.md", ".claude/agents/audit-verifier.md",
                        ".claude/hooks/audit-verifier-guard.sh", "tools/probes.txt", "tools/audit_vocab.json"):
                self.assertTrue(os.path.exists(os.path.join(target, rel)), rel)


if __name__ == "__main__":
    unittest.main()
