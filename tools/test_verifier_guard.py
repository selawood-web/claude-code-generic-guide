#!/usr/bin/env python3
"""Tests for .claude/hooks/audit-verifier-guard.sh — the verifier's allow-list.

Table-driven: every row is a command the audit's verifier might issue and the
exit code the guard must return for it (0 = run, 2 = refused). A row is the
contract; a change to the guard that flips a row is a change to what the
verifier may do, and belongs in the same pull request as its justification.
"""

import json
import os
import sys
import re
import shutil
import stat
import subprocess
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HOOK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    ".claude", "hooks", "audit-verifier-guard.sh")

ALLOWED = [
    "python3 tools/validate.py",
    "python3 -m unittest discover -s tools -p 'test_*.py' 2>&1 | tail -3",
    "python3 tools/audit_probes.py --probes tools/probes.txt",
    "timeout 60 python3 tools/validate.py",
    "bash -n .claude/hooks/session-start.sh",
    "CCGG_HOME=/tmp/x CLAUDE_PROJECT_DIR=\"$PWD\" bash -x .claude/hooks/session-start.sh 2>&1 | grep -E '^\\+ git'",
    "printf '{\"tool_name\":\"Bash\"}' | bash .claude/hooks/audit-verifier-guard.sh; echo \"exit $?\"",
    "for c in a b; do printf '%s' \"$c\" | bash .claude/hooks/audit-verifier-guard.sh; done",
    "git log --oneline -3 && git diff HEAD~1 --stat",
    "git -C . rev-parse HEAD",
    "git -C tools rev-parse --show-prefix",
    "git -P log -1",
    "git --no-optional-locks status --porcelain",
    "git ls-files -- 'decisions/*.md'",
    "git config --get remote.origin.url",
    "git branch --show-current",
    "git branch",
    "git remote -v",
    "x=$(git rev-parse HEAD); echo \"$x\"",
    "grep -n 'allowed-tools' .claude/skills/ccgg-audit/SKILL.md",
    "grep -rnE 'curl|wget' .claude/hooks/ || true",
    "sed -n 37p tools/probes.txt",
    "sed -n 's/x/y/p' f",
    "sed -n '/a/,/b/p' f",
    "awk -F'|' '{print $1}' tools/probes.txt",
    "find . -name '*.md' | wc -l",
    "cat < AGENTS.md",
    "[ -x .claude/hooks/x.sh ] && echo yes || echo no",
    "if grep -q x f; then echo y; else echo n; fi",
    "ls | while read -r f; do stat \"$f\"; done",
    "echo $((1+2))",
    "echo a 2>/dev/null; ls >/dev/null",
    "wc -c WORKING-CHARTER.md AGENTS.md",
    "command -v python3",
    "cd tools && python3 -m json.tool audit_vocab.json | head",
    "xxd AGENTS.md | head",
    "printenv | grep -c CCGG",
    # A newline is a command separator, so each line is checked on its own; both
    # of these are allowed programs and the two-line form must stay allowed.
    "git log --oneline -3\ngit status --porcelain",
    # A real newline inside quotes is data, not a separator: one token, one segment.
    "printf 'a\nb\n' | wc -l",
    # Python's option letters may carry their value attached, so an allow-listed
    # module in the attached form is the same request as the detached one.
    "python3 -mjson.tool tools/audit_vocab.json",
    "python3 -W ignore -m unittest discover -s tools",
    "python3 -I -m unittest discover -s tools",
    "python3 --version",
    # R-012: the gate tooling the verifier actually reproduces with, in every
    # spelling it reaches it by.
    "python3 tools/feature_lint.py",
    "python3 tools/catalog.py --check",
    "python3 tools/audit_report.py --dir CCGG-AUDIT-x",
    "python3 tools/test_validate.py",
    "python3 ./tools/validate.py",
    "cd tools && python3 validate.py",
    # S-001: the repository's own shell scripts stay runnable.
    "bash -n .claude/hooks/session-start.sh",
    "bash -n update.sh",
    "sh install.sh --help",
    # S-002: the assignment prefixes a reproduction actually needs.
    "CCGG_HOME=/tmp/x CCGG_REF=v1 bash -n .claude/hooks/session-start.sh",
    "LC_ALL=C grep -n foo AGENTS.md",
    # S-004: the pinned module and script names.
    "python3 -m unittest discover -s tools",
    "python3 -m unittest test_validate",
    "python3 tools/test_verifier_guard.py",
]

REFUSED = [
    "python3 -c 'print(1)'",
    "python3 -",
    "python3",
    "python3 -m http.server",
    # S-002: the module and code flags were matched only as the exact tokens `-m`
    # and `-c`, so the attached and clustered forms python itself accepts walked
    # past both refusals and were taken for a script path.
    "python3 -mhttp.server 8000",
    "python3 -mtimeit",
    "python3 -msocketserver",
    "python3 -c'import os' x",
    "python3 -cimport os",
    "python3 -Sc 'import os'",
    "python3 -IBc 'import os'",
    "python3 -Zz tools/validate.py",
    # S-001: check_shell returned on the first non-flag argument, so any .sh the
    # audited branch carried ran — the hole R-012 closed for python, four lines up.
    "bash tools/whatever.sh",
    "bash /tmp/evil.sh",
    "sh ../outside.sh",
    "bash .claude/hooks/../../etc/x.sh",
    "bash",
    # S-002: the VAR= prefix was popped without reading the name, so a variable
    # that names a program to run passed behind an allow-listed one.
    "LD_PRELOAD=tools/evil.so cat README.md",
    "LESSOPEN=@tools/x.sh less README.md",
    "GIT_EXTERNAL_DIFF=./payload.sh git diff HEAD~1 HEAD",
    "PAGER=./payload.sh git log",
    "PYTHONSTARTUP=tools/x.py python3 tools/validate.py",
    # S-004: the python allow-list matched a prefix, not a name.
    "python3 tools/test_pwn.py",
    "python3 tools/audit_pwn.py",
    "python3 -m unittest discover -s /tmp",
    "python3 -m unittest test_pwn",
    "python3 -m doctest tools/pwn.py",
    # R-012: `python3 <path>` was allowed unconditionally as "the repository's
    # own code", so any .py file an audited branch carries ran inside the
    # verifier's worktree — in CI, on the runner that holds the API key.
    "python3 setup.py install",
    "python3 scripts/deploy.py",
    "python3 evil.py",
    "python3 /tmp/x.py",
    # An absolute path at the filesystem root: rpartition leaves the directory
    # empty, which is one of PY_SCRIPT_DIRS, and the basename is an allowed name.
    # Only the worktree check stands between `python3 /validate.py` and whatever
    # is at that path. Found by the guard mutation probes, which is what they are
    # for — no row covered it, so the check that stops it was untested.
    "python3 /validate.py",
    "bash /install.sh",
    "python3 ../outside.py",
    "python3 tools/../setup.py",
    "python3 .github/x.py",
    "python3 tools/sub/x.py",
    # R-013: pytest imports conftest.py and its plugins from whatever tree it is
    # pointed at; ruff, mypy and flake8 load project config the same way. None of
    # them is used by this repository's gate, so none is in the allow-list.
    "pytest tools",
    "pytest",
    "python3 -m pytest tools",
    "ruff check .",
    "mypy tools",
    "flake8 tools",
    "pyflakes tools",
    "bash -c id",
    "printf x | bash",
    "sh -s < x",
    "git fetch origin",
    "git clone https://example.invalid/x /tmp/x",
    "git pull",
    "git push",
    "git commit -am x",
    "git checkout -- .",
    "git config core.hooksPath /tmp/h",
    "git branch new",
    "git tag v9",
    "git --git-dir=/x/.git log",
    # S-003: git's options before the subcommand were skipped, not read, so every
    # spelling that names a program to run reached an allow-listed read subcommand.
    # `git -c diff.external=<cmd> diff` really does run <cmd>; the environment
    # spellings of that same capability were already refused two blocks up.
    "git -c diff.external=id diff",
    "git -c core.pager=id log",
    "git -c core.sshCommand=id ls-remote",
    "git -c alias.x=!id x",
    "git --config-env=diff.external=EVIL diff",
    "git --exec-path=/tmp log",
    "git -p log",
    "git --namespace=x log",
    # -C carries a path, and the refusal it walked past said "pointed at another
    # repository" — which --git-dir alone was never the only way to do.
    "git -C /etc rev-parse",
    "git -C ../other log",
    "git -C tools/../.. log",
    "git -C",
    "git apply p.diff",
    "sed -i s/a/b/ AGENTS.md",
    "sed -n 's/x/y/w out.txt' f",
    "sed '1,3w x' f",
    "sed -e 's/a/b/' -e '2e id' f",
    "awk '{print $1 > \"x\"}' f",
    "awk '{system(\"id\")}' f",
    "find . -name '*.md' -delete",
    "find . -exec rm {} \;",
    "curl http://127.0.0.1:9/",
    "wget -q http://x",
    "ssh host id",
    "echo hi > /tmp/x",
    "echo hi >> AGENTS.md",
    "echo hi | tee x",
    "cat <<EOF\nhi\nEOF",
    "echo `id`",
    "rm -rf /tmp/x",
    "mv a b",
    "cp a b",
    "touch x",
    "mkdir x",
    "chmod +x x",
    "ln -s a b",
    "xargs rm",
    "env FOO=1 bash x.sh",
    "exec bash",
    "eval id",
    "source x.sh",
    ". x.sh",
    "gh pr merge 1",
    "pip install x",
    "npm install",
    "node -e 'require(\"fs\").writeFileSync(\"x\",\"\")'",
    # The same whole-token defect as S-002, in the branch next door: node's
    # letters cluster (`-pe`) and carry an attached value (`-e'code'`).
    "node -e'require(\"fs\")' y",
    "node -pe 'process.exit()'",
    "node --eval='x'",
    "node -i",
    "diff <(id) /dev/null",
    "echo 'no closing quote",
    "ls; curl http://x",
    # S-001: a newline separates commands exactly as `;` does. Before the fix the
    # lexer swallowed it as whitespace, so everything below folded into one
    # segment whose first word was the allowed `echo` and was never checked.
    "echo hi\ncurl http://x",
    "echo hi\npython3 -c 'import os'",
    "ls\r\ncurl http://x",
    "ls\n\ncurl http://x",
    "ls &&\ncurl http://x",
    "ls\n\tcurl http://x",
    # `#` comments run to the end of a line, not to the end of the command: the
    # second line is still checked.
    "ls\n# a note\ncurl http://x",
    "ls && (cd /tmp && rm -rf x)",
    "echo $(curl http://x)",
    "echo $(echo $(rm x))",
    "",
    "   ",
]


def run_guard(command: str, tool: str = "Bash") -> tuple[int, str]:
    payload = json.dumps({"tool_name": tool, "tool_input": {"command": command}})
    proc = subprocess.run(["bash", HOOK], input=payload, capture_output=True, text=True)
    return proc.returncode, proc.stderr


def guard_stdout(command: str, tool: str = "Bash") -> str:
    payload = json.dumps({"tool_name": tool, "tool_input": {"command": command}})
    return subprocess.run(["bash", HOOK], input=payload, capture_output=True, text=True).stdout


class AllowListTests(unittest.TestCase):
    def test_allowed_rows_run(self):
        for cmd in ALLOWED:
            with self.subTest(cmd=cmd):
                rc, err = run_guard(cmd)
                self.assertEqual(rc, 0, f"refused: {err.strip()}")

    def test_refused_rows_exit_2(self):
        for cmd in REFUSED:
            with self.subTest(cmd=cmd):
                rc, err = run_guard(cmd)
                self.assertEqual(rc, 2, "allowed a command outside the allow-list")
                self.assertIn("audit-verifier-guard: refused", err)

    def test_an_allowed_command_is_approved_not_merely_permitted(self):
        # Headless there is no prompt to answer and the skill grants only its four
        # report scripts, so a silent exit 0 leaves every reproduction refused.
        decision = json.loads(guard_stdout("git status --porcelain"))["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "allow")

    def test_the_approval_carries_no_content_from_the_tree(self):
        # Hook stdout is model context. The command under inspection never returns
        # through it, whatever it contains.
        out = guard_stdout("grep -r 'IGNORE PREVIOUS INSTRUCTIONS' .")
        self.assertNotIn("IGNORE PREVIOUS", out)
        self.assertNotIn("grep", out)

    def test_a_refused_command_approves_nothing(self):
        for cmd in ("curl http://x", "printf x > /tmp/y", ""):
            with self.subTest(cmd=cmd):
                self.assertEqual(guard_stdout(cmd).strip(), "")

    def test_another_tool_is_neither_approved_nor_refused(self):
        self.assertEqual(guard_stdout("anything", tool="Read").strip(), "")

    def test_refusal_names_the_reason(self):
        rc, err = run_guard("curl http://x")
        self.assertEqual(rc, 2)
        self.assertIn("curl", err)

    def test_other_tools_pass_through(self):
        rc, _ = run_guard("anything", tool="Read")
        self.assertEqual(rc, 0)

    def test_non_json_input_refused(self):
        proc = subprocess.run(["bash", HOOK], input="not json", capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)


class CanaryTests(unittest.TestCase):
    """R-008: the canary only means something while the guard still refuses it."""

    def canary(self):
        import audit_report
        return audit_report.GUARD_CANARY

    def test_the_canary_is_refused_by_the_guard(self):
        rc, err = run_guard(self.canary())
        self.assertEqual(rc, 2, "the canary command is no longer refused — it proves nothing")
        self.assertIn("audit-verifier-guard: refused", err)

    def test_the_canary_is_harmless(self):
        """A canary that changed something would be a poor thing to run every time."""
        self.assertNotIn(">", self.canary())
        self.assertNotIn("rm", self.canary())
        self.assertNotIn("|", self.canary())


class GuardFailureTests(unittest.TestCase):
    """A guard that fails must not become a guard that allows (finding H-002).

    The hook ends in a pipeline, so its exit status is the interpreter's, and
    only exit 2 blocks the call: every other way of dying — an uncaught
    exception, a signal, an interpreter that will not start, an empty guard
    program — used to reach Claude Code as "no objection" and run the command.
    """

    def _run(self, stub_body=None, hook=HOOK):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "curl http://x"}})
        env = dict(os.environ)
        with tempfile.TemporaryDirectory() as tmp:
            if stub_body is not None:
                stub = os.path.join(tmp, "python3")
                with open(stub, "w", encoding="utf-8") as fh:
                    fh.write(stub_body)
                os.chmod(stub, os.stat(stub).st_mode | stat.S_IEXEC)
                env["PATH"] = tmp + os.pathsep + env.get("PATH", "")
            proc = subprocess.run(["bash", hook], input=payload,
                                  capture_output=True, text=True, env=env)
        return proc.returncode, proc.stderr

    def test_interpreter_exiting_nonzero_refuses(self):
        for code in (1, 3, 70, 127):
            with self.subTest(exit_code=code):
                rc, err = self._run(f"#!/bin/sh\ncat >/dev/null\nexit {code}\n")
                self.assertEqual(rc, 2, "a crashed guard allowed the command")
                self.assertIn("audit-verifier-guard", err)

    def test_interpreter_killed_by_signal_refuses(self):
        rc, err = self._run("#!/bin/sh\ncat >/dev/null\nkill -TERM $$\n")
        self.assertEqual(rc, 2, "a killed guard allowed the command")
        self.assertIn("audit-verifier-guard", err)

    def test_interpreter_that_cannot_start_refuses(self):
        rc, _ = self._run("#!/nonexistent/interpreter\n")
        self.assertEqual(rc, 2, "an unstartable guard allowed the command")

    def test_empty_guard_program_refuses(self):
        """If the heredoc ever stops reaching GUARD, `python3 -c ''` exits 0."""
        with open(HOOK, encoding="utf-8") as fh:
            source = fh.read()
        blanked = re.sub(r"(<<'PY'[^\n]*\n).*?(\nPY\n)", r"\1\2", source, count=1, flags=re.S)
        self.assertNotEqual(blanked, source, "could not blank the guard program")
        with tempfile.TemporaryDirectory() as tmp:
            copy = os.path.join(tmp, "guard.sh")
            with open(copy, "w", encoding="utf-8") as fh:
                fh.write(blanked)
            shutil.copymode(HOOK, copy)
            rc, err = self._run(hook=copy)
        self.assertEqual(rc, 2, "an empty guard program allowed the command")
        self.assertIn("audit-verifier-guard", err)

    def test_healthy_guard_still_answers_both_ways(self):
        rc, _ = self._run()
        self.assertEqual(rc, 2)
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}})
        proc = subprocess.run(["bash", HOOK], input=payload, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)


class ScopedRegistrationTests(unittest.TestCase):
    """H-001/S-003: the settings.json registration decides only the verifier's calls.

    The frontmatter registration was measured not firing from inside a live
    interactive verifier, twice. settings.json hooks fire, but they fire for
    every agent's Bash — the main session's included — so that registration
    carries `--only-agent audit-verifier` and the guard reads the product's
    `agent_type` field before it does anything else. Without the flag (the
    frontmatter and headless paths) the guard decides every call it is given.
    """

    SCOPED = ("--only-agent", "audit-verifier")

    def run_scoped(self, command, agent_type=None, args=SCOPED, tool="Bash", env=None):
        payload = {"tool_name": tool, "tool_input": {"command": command}}
        if agent_type is not None:
            payload["agent_id"] = "agent_0123"
            payload["agent_type"] = agent_type
        # A guard that never answers is a guard that blocks nothing a human is
        # waiting on; a hang here is a failure, not a pause (a mutant that accepted
        # an empty --only-agent looped forever on a lone flag).
        proc = subprocess.run([shutil.which("bash"), HOOK, *args], input=json.dumps(payload),
                              capture_output=True, text=True, env=env, timeout=20)
        return proc.returncode, proc.stdout, proc.stderr

    def test_the_verifier_is_refused_and_approved_exactly_as_before(self):
        rc, out, err = self.run_scoped("uname -a", agent_type="audit-verifier")
        self.assertEqual(rc, 2, err)
        self.assertIn("audit-verifier-guard: refused", err)
        self.assertEqual(out.strip(), "")
        rc, out, err = self.run_scoped("ls -la", agent_type="audit-verifier")
        self.assertEqual(rc, 0, err)
        self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "allow")

    def test_the_main_session_passes_through_with_no_opinion(self):
        # No agent_type at all: the hook input of a call the main agent makes.
        rc, out, err = self.run_scoped("uname -a")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.strip(), "")
        self.assertEqual(err.strip(), "")

    def test_every_other_agent_passes_through(self):
        for name in ("audit-harness", "Explore", "general-purpose", "audit-verifier-2", "verifier"):
            with self.subTest(agent=name):
                rc, out, err = self.run_scoped("curl http://x", agent_type=name)
                self.assertEqual(rc, 0, err)
                self.assertEqual(out.strip(), "")

    def test_compact_json_matches_too(self):
        # json.dumps writes a space after the colon; the product may not.
        payload = '{"tool_name":"Bash","tool_input":{"command":"uname -a"},"agent_type":"audit-verifier"}'
        proc = subprocess.run([shutil.which("bash"), HOOK, *self.SCOPED], input=payload,
                              capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_without_the_flag_agent_type_is_not_consulted(self):
        # The frontmatter and headless paths: the guard decides whoever's call it is given.
        for agent in (None, "someone-else", "audit-verifier"):
            with self.subTest(agent=agent):
                rc, _, err = self.run_scoped("uname -a", agent_type=agent, args=())
                self.assertEqual(rc, 2, err)

    def test_an_empty_or_malformed_agent_name_refuses_loudly(self):
        # A misconfigured scope must not silently become "decide nobody" or "decide everybody".
        for args in (("--only-agent",), ("--only-agent", ""), ("--only-agent", "a b"),
                     ("--only-agent", "x;id"), ("--only-agent", "audit-verifier", "--extra"), ("--bogus",)):
            with self.subTest(args=args):
                rc, out, err = self.run_scoped("ls", agent_type="audit-verifier", args=args)
                self.assertEqual(rc, 2, err)
                self.assertEqual(out.strip(), "")
                self.assertIn("audit-verifier-guard", err)

    def test_a_scoped_out_call_needs_no_interpreter(self):
        """A project without python3 keeps its Bash; only the verifier's calls need it."""
        bindir = tempfile.mkdtemp(prefix="ccgg-nopy-")
        try:
            for tool in ("cat", "env"):
                os.symlink(shutil.which(tool), os.path.join(bindir, tool))
            env = {"PATH": bindir}
            rc, out, err = self.run_scoped("ls", env=env)
            self.assertEqual(rc, 0, err)
            self.assertEqual(out.strip(), "")
            self.assertEqual(err.strip(), "")
            rc, _, err = self.run_scoped("ls", agent_type="audit-verifier", env=env)
            self.assertEqual(rc, 2, err)
            self.assertIn("python3 is required", err)
        finally:
            shutil.rmtree(bindir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
