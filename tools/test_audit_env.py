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
from unittest import mock

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


def _tar(members):
    import io
    import tarfile
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as archive:
        for name, data in members:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return buf.getvalue()


class UnpackTarTests(unittest.TestCase):
    """PR #93: a bare "tar" on Windows is bsdtar, which skipped every non-ASCII name."""

    def test_a_non_ascii_filename_survives(self):
        with tempfile.TemporaryDirectory() as dest:
            audit_env.unpack_tar(_tar([("docs/שלום.md", b"shalom\n"), ("a.txt", b"a")]), dest)
            with open(os.path.join(dest, "docs", "שלום.md"), encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "shalom\n")
            self.assertTrue(os.path.isfile(os.path.join(dest, "a.txt")))

    def test_a_member_that_leaves_the_destination_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "repo")
            os.makedirs(dest)
            with self.assertRaises(Exception):
                audit_env.unpack_tar(_tar([("../escaped.txt", b"x")]), dest)
            self.assertFalse(os.path.exists(os.path.join(tmp, "escaped.txt")))

    def test_an_empty_archive_unpacks_to_nothing(self):
        with tempfile.TemporaryDirectory() as dest:
            audit_env.unpack_tar(_tar([]), dest)
            self.assertEqual(os.listdir(dest), [])

    def test_bytes_that_are_not_a_tar_are_an_error(self):
        with tempfile.TemporaryDirectory() as dest:
            with self.assertRaises(Exception):
                audit_env.unpack_tar(b"not a tar archive at all", dest)


class SystemRootTests(unittest.TestCase):
    """PR #93: without SYSTEMROOT, winsock and the C runtime refuse to start on Windows."""

    def test_windows_gets_systemroot(self):
        with mock.patch.object(audit_env.os, "name", "nt"), \
                mock.patch.dict(os.environ, {"SYSTEMROOT": r"D:\Win"}):
            self.assertEqual(sandbox_env("/tmp/h")["SYSTEMROOT"], r"D:\Win")

    def test_other_hosts_do_not(self):
        with mock.patch.object(audit_env.os, "name", "posix"):
            self.assertNotIn("SYSTEMROOT", sandbox_env("/tmp/h"))

    def test_systemroot_is_on_the_allow_list_so_it_is_not_reported_as_a_leak(self):
        self.assertIn("SYSTEMROOT", ALLOWED)


class BashPathTests(unittest.TestCase):
    """S0-2: a bare "bash" on Windows is the WSL launcher, whatever PATH says."""

    def test_the_launcher_is_recognised_in_system32_and_windowsapps(self):
        for path in (r"C:\Windows\System32\bash.exe", r"c:\windows\system32\BASH.EXE",
                     r"C:\Users\u\AppData\Local\Microsoft\WindowsApps\bash.exe",
                     "C:/Windows/System32/bash.exe"):
            with self.subTest(path=path):
                self.assertTrue(audit_env.is_wsl_launcher(path))

    def test_git_for_windows_bash_is_not_the_launcher(self):
        for path in (r"C:\Program Files\Git\usr\bin\bash.exe", r"C:\Program Files\Git\bin\bash.exe",
                     "/usr/bin/bash", r"D:\Windows\System32\bash.exe"):
            with self.subTest(path=path):
                self.assertFalse(audit_env.is_wsl_launcher(path))

    def test_a_windows_directory_elsewhere_is_honoured(self):
        self.assertTrue(audit_env.is_wsl_launcher(r"D:\Win\System32\bash.exe", windir=r"D:\Win"))

    def test_candidates_follow_git_exe_and_the_default_install(self):
        found = audit_env.git_bash_candidates(r"C:\Program Files\Git\cmd\git.exe", r"C:\Program Files")
        self.assertEqual(found[0], r"C:\Program Files\Git\bin\bash.exe")
        self.assertIn(r"C:\Program Files\Git\usr\bin\bash.exe", found)
        self.assertEqual(found[-1], r"C:\Program Files\Git\bin\bash.exe")

    def test_mingw_git_exe_reaches_the_same_bash(self):
        found = audit_env.git_bash_candidates(r"C:\Program Files\Git\mingw64\bin\git.exe", None)
        self.assertIn(r"C:\Program Files\Git\bin\bash.exe", found)

    def test_no_git_and_no_program_files_gives_nothing_to_try(self):
        self.assertEqual(audit_env.git_bash_candidates(None, None), [])

    def test_an_explicit_override_wins(self):
        with mock.patch.dict(os.environ, {"CCGG_BASH": "/opt/bash5/bin/bash"}):
            self.assertEqual(audit_env.bash_path(), "/opt/bash5/bin/bash")

    def test_the_answer_is_never_the_launcher_where_git_bash_exists(self):
        path = audit_env.bash_path()
        if os.name == "nt" and os.path.isfile(r"C:\Program Files\Git\bin\bash.exe"):
            self.assertFalse(audit_env.is_wsl_launcher(path), path)
        self.assertTrue(path)


if __name__ == "__main__":
    unittest.main()
