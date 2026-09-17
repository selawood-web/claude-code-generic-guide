#!/usr/bin/env python3
"""Tests for .claude/hooks/audit-verifier-guard.sh — the verifier's allow-list.

Table-driven: every row is a command the audit's verifier might issue and the
exit code the guard must return for it (0 = run, 2 = refused). A row is the
contract; a change to the guard that flips a row is a change to what the
verifier may do, and belongs in the same pull request as its justification.
"""

import json
import os
import subprocess
import unittest

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


if __name__ == "__main__":
    unittest.main()
