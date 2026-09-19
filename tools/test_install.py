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
                        ".claude/hooks/audit-verifier-guard.sh", "tools/probes.txt", "tools/audit_vocab.json",
                        "tools/audit_headless.py", "tools/audit_agents_json.py",
                        ".github/workflows/audit.yml"):
                self.assertTrue(os.path.exists(os.path.join(target, rel)), rel)
            for rel in (".claude/skills/gbb/SKILL.md", ".claude/skills/gbb/design-intent.md",
                        ".claude/skills/gbb/design-council.md", ".claude/skills/gbb/design-ownership.md",
                        ".claude/skills/gbb/gbb-ladder.md", ".claude/skills/gbb/research-protocol.md"):
                self.assertTrue(os.path.exists(os.path.join(target, rel)),
                                f"{rel} — a skill's companions ship with it or the skill is broken downstream")


class UpdateReportsTests(unittest.TestCase):
    """update.sh says which of the two happened, because it advises a different fix.

    Every non-zero exit from the catalog tool used to read as "tables are
    stale", so a project whose own skill the tool could not parse was told to
    run a command that failed the same way.
    """

    def _project(self, tmp):
        target = os.path.join(tmp, "project")
        os.makedirs(target)
        env = dict(os.environ, HOME=os.path.join(tmp, "home"), GIT_CONFIG_NOSYSTEM="1",
                   GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@local",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@local")
        os.makedirs(env["HOME"])
        subprocess.run(["git", "init", "-q"], cwd=target, env=env, check=True)
        install = subprocess.run(["bash", os.path.join(ROOT, "install.sh"), target], env=env,
                                 capture_output=True, text=True)
        self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
        return target, env

    def _update(self, target, env):
        proc = subprocess.run(["bash", os.path.join(ROOT, "update.sh"), target], env=env,
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc.stdout + proc.stderr

    def _project_skill(self, target, *, house_keys: bool) -> None:
        d = os.path.join(target, ".claude", "skills", "project-only")
        os.makedirs(d, exist_ok=True)
        body = "---\nname: project-only\ndescription: a skill this project wrote\n"
        if house_keys:
            body += 'when_to_use: local\nargument-hint: "[x]"\npurpose: "A skill this project wrote"\n'
        body += "---\n\nBody.\n"
        open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8").write(body)

    def test_unparsable_project_skill_is_not_reported_as_stale(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-update-") as tmp:
            target, env = self._project(tmp)
            self._project_skill(target, house_keys=False)
            out = self._update(target, env)
            self.assertIn("could not read every skill", out)
            self.assertIn("project-only", out)
            self.assertNotIn("STALE", out)
            self.assertNotIn("--write", out)

    def test_stale_table_is_reported_as_stale(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-update-") as tmp:
            target, env = self._project(tmp)
            self._project_skill(target, house_keys=True)
            out = self._update(target, env)
            self.assertIn("STALE", out)
            self.assertIn("--write", out)
            self.assertNotIn("could not read every skill", out)

    def test_current_project_reports_neither(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-update-") as tmp:
            target, env = self._project(tmp)
            out = self._update(target, env)
            self.assertNotIn("STALE", out)
            self.assertNotIn("could not read every skill", out)

    def test_the_advised_command_actually_repairs_it(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-update-") as tmp:
            target, env = self._project(tmp)
            self._project_skill(target, house_keys=True)
            self.assertIn("STALE", self._update(target, env))
            fix = subprocess.run([sys.executable, "tools/catalog.py", "--write"], cwd=target,
                                 env=env, capture_output=True, text=True)
            self.assertEqual(fix.returncode, 0, fix.stdout + fix.stderr)
            self.assertNotIn("STALE", self._update(target, env))


if __name__ == "__main__":
    unittest.main()
