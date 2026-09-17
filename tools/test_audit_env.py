#!/usr/bin/env python3
"""Unit tests for audit_env.py — what a command from the audited tree may see.

Findings S-004 and S-005: the red-team harness and the deterministic gate both
ran code out of the checkout with the operator's environment attached. These
tests are the assertion both findings asked for — the environment a harness
actually builds, checked against the allow-list rather than against the three
names somebody remembered to remove.

Run: python -m unittest discover -s tools -p "test_*.py"
"""

import os
import tempfile
import unittest

import audit_env
import audit_probes
import audit_redteam
from audit_env import ALLOWED, leaked_names, sandbox_env

# Names an operator plausibly has exported. None of them may survive.
CREDENTIALS = {
    "ANTHROPIC_API_KEY": "sk-ant-secret",
    "GITHUB_TOKEN": "ghp_secret",
    "AWS_SECRET_ACCESS_KEY": "aws-secret",
    "CCGG_HOME": "/home/someone/guide",
    "CCGG_REPO": "https://example.invalid/g.git",
    "CCGG_REF": "main",
    "NPM_TOKEN": "npm-secret",
}


class SandboxEnvTests(unittest.TestCase):
    def test_no_operator_variable_survives(self):
        with tempfile.TemporaryDirectory() as home:
            for name, value in CREDENTIALS.items():
                os.environ[name] = value
            try:
                env = sandbox_env(home)
            finally:
                for name in CREDENTIALS:
                    os.environ.pop(name, None)
        self.assertEqual(leaked_names(env), [])
        for name in CREDENTIALS:
            self.assertNotIn(name, env)

    def test_home_is_the_one_the_caller_owns(self):
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(sandbox_env(home)["HOME"], home)

    def test_path_is_carried_so_interpreters_resolve(self):
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(sandbox_env(home)["PATH"], os.environ.get("PATH", audit_env.DEFAULT_PATH))

    def test_git_can_commit_without_the_operators_identity(self):
        with tempfile.TemporaryDirectory() as home:
            env = sandbox_env(home, actor="probes")
        self.assertEqual(env["GIT_AUTHOR_NAME"], "probes")
        self.assertEqual(env["GIT_COMMITTER_EMAIL"], "probes@local")
        self.assertEqual(env["GIT_CONFIG_NOSYSTEM"], "1")

    def test_extra_is_added_but_still_accounted_for(self):
        with tempfile.TemporaryDirectory() as home:
            env = sandbox_env(home, extra={"MARKER": "CCGG-X"})
        self.assertEqual(env["MARKER"], "CCGG-X")
        self.assertEqual(leaked_names(env), ["MARKER"])          # unaccounted by default
        self.assertEqual(leaked_names(env, allow=("MARKER",)), [])  # named, so allowed

    def test_an_empty_home_is_refused(self):
        with self.assertRaises(ValueError):
            sandbox_env("")

    def test_leaked_names_rejects_a_non_dict(self):
        with self.assertRaises(TypeError):
            leaked_names(None)

    def test_the_allow_list_names_no_credential(self):
        for name in ALLOWED:
            self.assertFalse(
                any(word in name for word in ("KEY", "TOKEN", "SECRET", "PASSWORD")),
                f"{name} does not belong in an allow-list",
            )


class HarnessEnvTests(unittest.TestCase):
    """The environments the two harnesses actually build — S-004's becomes_check."""

    def setUp(self):
        for name, value in CREDENTIALS.items():
            os.environ[name] = value
        self.addCleanup(lambda: [os.environ.pop(n, None) for n in CREDENTIALS])

    def test_probe_env_leaks_nothing(self):
        with tempfile.TemporaryDirectory() as scratch:
            env = audit_probes.probe_env(scratch)
        self.assertEqual(leaked_names(env), [])

    def test_redteam_scratch_env_leaks_nothing(self):
        """make_scratch_copy builds the env every plant and observe runs under."""
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as scratch:
            _, env = audit_redteam.make_scratch_copy(root, scratch)
        self.assertEqual(leaked_names(env), [])
        for name in CREDENTIALS:
            self.assertNotIn(name, env)


if __name__ == "__main__":
    unittest.main()
