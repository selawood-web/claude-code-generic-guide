#!/usr/bin/env bash
# Hook: audit-verifier-guard (PreToolUse, matcher Bash)
# Registered by: .claude/settings.json (PreToolUse/Bash, --only-agent
#                audit-verifier) and .claude/agents/audit-verifier.md, for
#                that subagent only.
# Purpose: allow the audit's verifier only the commands a reproduction needs —
#          the repository's own tests and tools, git reads, and text inspection —
#          as a second layer under the worktree isolation the runtime already
#          enforces. Exit 2 blocks the call; the reason on stderr reaches the
#          model. A command that passes prints a PreToolUse allow decision, so
#          the guard is what approves the verifier's Bash: headless there is no
#          prompt to answer, and the audit skill grants only its four report
#          scripts, so without this every reproduction command is refused.
#          The rule is an allow-list: a command is run only when every
#          segment of it (each side of a pipe, `&&`, `;`, a newline, and every
#          `$(...)`) starts with an allowed program in an allowed form. Anything
#          else — an unknown program, an interpreter given code on its command
#          line, a redirect to a file, a heredoc, a backtick — is refused, so
#          the guard fails closed by construction.
#
# Registered twice, on purpose, and the two serve different dispatch paths.
# Interactive verifiers are guarded by the settings.json registration
# (PreToolUse/Bash, `--only-agent audit-verifier`): a 2026-09-17 run and a
# 2026-09-18 run with only the frontmatter block in place measured that block
# from inside a live verifier and the hook did not fire — the commands below
# were refused here, with exit 2, and ran as Bash tool calls (findings R-008,
# H-001, S-003) — and the 2026-09-18 run on 4818aeb, the first with the
# settings.json registration, came back refused in every verifier, each
# refusal naming this command with `--only-agent` and never the frontmatter
# one. With `--only-agent`, any other agent's Bash — the main session's
# included — passes through with no opinion, before python3 is even looked
# for. The frontmatter block in audit-verifier.md stays for the headless
# path: with the briefs passed inline it measurably fires, and it is the one
# the headless launcher retargets to a trusted copy.
#
# The table of allowed forms is tested by tools/test_verifier_guard.py. What
# that table proves is this program's verdicts, not that anything consults
# them: every audit run still starts its verifiers with a canary and records
# the answer in guard.json, because a registration proven on one head is a
# claim on the next.
set -uo pipefail

ONLY_AGENT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --only-agent)
      ONLY_AGENT="${2:-}"
      case "$ONLY_AGENT" in
        *[!A-Za-z0-9_-]*|"")
          echo "audit-verifier-guard: --only-agent needs an agent name; refusing" >&2
          exit 2 ;;
      esac
      # A failed shift would leave $1 in place and this loop spinning; that is
      # what a mutant that accepted an empty name did. Never loop on a refusal.
      shift 2 || { echo "audit-verifier-guard: --only-agent needs an agent name; refusing" >&2; exit 2; } ;;
    *)
      echo "audit-verifier-guard: unknown argument; refusing" >&2
      exit 2 ;;
  esac
done

# The hook's JSON arrives on stdin; capture it before anything else reads stdin.
INPUT="$(cat)"

# Scoped registration: decide only the named agent's calls. `agent_type` is a
# top-level string the product writes into the hook input for a subagent, so a
# plain substring test on the machine-written JSON is enough to say "not mine";
# it needs no interpreter, so a project without python3 is not locked out of
# Bash by a guard meant for one agent. A call the test does match goes on to the
# full check below, where the JSON is parsed properly.
if [ -n "$ONLY_AGENT" ]; then
  case "$INPUT" in
    *"\"agent_type\":\"$ONLY_AGENT\""*|*"\"agent_type\": \"$ONLY_AGENT\""*) ;;
    *) exit 0 ;;
  esac
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "audit-verifier-guard: python3 is required to inspect the command; refusing" >&2
  exit 2
fi

read -r -d '' GUARD <<'PY' || true
import json, posixpath, re, shlex, sys

KEYWORDS = {"if", "then", "else", "elif", "fi", "for", "while", "until", "do", "done",
            "in", "!", "{", "}", "(", ")", "time", "[[", "]]"}
SEPARATORS = {"|", "||", "&&", ";", "&", ";;", "|&"}
# A newline starts a new command exactly as `;` does. shlex counts it as
# whitespace and drops it, so the lexer below lists it as punctuation instead;
# it then arrives glued to any adjacent separator (`&&\n`, `\r\n`, `\n\n`), which
# is why membership in SEPARATORS alone is not the test.
SEPARATOR_CHARS = frozenset("|&;\n\r")


def is_separator(tok):
    return bool(tok) and (tok in SEPARATORS or set(tok) <= SEPARATOR_CHARS)


# Programs that never write and never reach the network on their own.
PLAIN = {
    "cat", "head", "tail", "wc", "ls", "stat", "file", "diff", "cmp", "sort", "uniq",
    "cut", "tr", "grep", "egrep", "fgrep", "rg", "xxd", "od", "hexdump", "strings",
    "jq", "which", "type", "id", "whoami", "pwd", "date", "basename", "dirname",
    "realpath", "readlink", "tree", "column", "nl", "tac", "rev", "expr", "seq",
    "echo", "printf", "test", "[", "true", "false", "read", "sleep", "printenv",
    "md5sum", "sha256sum", "sha1sum", "du", "df", "cd", "pushd", "popd", "export",
    "local", "declare", "set", "unset", "exit", "return", "break", "continue", ":",
    "shift", "let", "shellcheck",
    "git-lfs", "less", "more", "comm", "join", "paste", "fold", "fmt", "yes",
}
GIT_READ = {
    "log", "show", "diff", "status", "rev-parse", "ls-files", "ls-tree", "cat-file",
    "grep", "blame", "describe", "rev-list", "name-rev", "shortlog", "check-ignore",
    "check-attr", "diff-tree", "diff-index", "for-each-ref", "show-ref", "symbolic-ref",
    "var", "count-objects", "verify-commit", "verify-tag", "merge-base", "whatchanged",
    "reflog", "fsck", "version", "help",
}
# git's options before the subcommand, named rather than skipped. A deny-list here
# would have to spell every option that names a program — `-c diff.external=`,
# `-c core.pager=`, `-c core.sshCommand=`, `--config-env=`, `--exec-path=` — and then
# keep pace with every git release. The environment spellings of that same
# capability (GIT_EXTERNAL_DIFF, PAGER) were already refused by the environment
# prefix rule; `-c` was the unlocked door to the same room (finding S-003).
# `-C` is handled separately: it takes a path, and that path may not leave the tree.
GIT_GLOBAL_FLAGS = frozenset((
    "-v", "--version", "-P", "--no-pager", "--no-replace-objects",
    "--no-optional-locks", "--no-lazy-fetch", "--no-advice",
    "--literal-pathspecs", "--glob-pathspecs", "--noglob-pathspecs",
    "--icase-pathspecs",
))
GIT_LISTING = {"branch": {"--list", "-a", "-r", "-v", "-vv", "--show-current", "--contains",
                          "--merged", "--no-merged", "-l"},
               "tag": {"--list", "-l", "-n", "--contains", "--points-at"},
               "remote": {"-v", "show", "get-url"},
               "config": {"--get", "--get-all", "--get-regexp", "--list", "-l"},
               "worktree": {"list"},
               "stash": {"list", "show"},
               "notes": {"list", "show"}}
# pytest is deliberately absent, here and from PLAIN: it imports conftest.py and
# its entry-point plugins from whatever tree it is pointed at, as ruff, mypy and
# flake8 load project config from it (finding R-013). This repository's gate uses
# none of them, so a reproduction never needs one; a future need is a row added
# here with its constraint, not a program that was never really read.
PY_MODULES = {"unittest", "json.tool", "doctest", "py_compile", "tokenize"}
# `python3 <path>` used to be allowed unconditionally as "the repository's own
# code", which on an audited branch means any .py file the branch carries
# (finding R-012). The verifier reproduces with the gate's own tooling; that is
# what these name.
# By name, never by prefix: `tools/test_*.py` matched anything a branch chose to
# call test_something, which is the capability PY_SCRIPT_NAMES existed to remove
# (finding S-004). check_guard_allow_lists in tools/validate.py keeps this equal
# to the tree, so adding a script to the gate is a visible change to this list.
PY_SCRIPT_DIRS = frozenset(("", "tools"))
PY_SCRIPTS = frozenset((
    "audit_agents_json.py", "audit_env.py", "audit_facts.py", "audit_headless.py",
    "audit_pr_comment.py", "audit_probes.py", "audit_redteam.py", "audit_report.py",
    "catalog.py", "feature_lint.py", "validate.py",
    "test_audit_agents_json.py", "test_audit_env.py", "test_audit_facts.py",
    "test_audit_headless.py", "test_audit_pr_comment.py", "test_audit_probes.py",
    "test_audit_redteam.py", "test_audit_report.py", "test_catalog.py", "test_feature_lint.py",
    "test_install.py", "test_session_start_hook.py", "test_validate.py",
    "test_verifier_guard.py",
))
PY_TEST_MODULES = frozenset(n[:-3] for n in PY_SCRIPTS if n.startswith("test_"))
UNITTEST_DISCOVER_DIRS = frozenset(("tools",))
# python's option letters cluster and may carry their value attached, so `-c`,
# `-Sc`, `-cCODE` and `-IBc CODE` are all the code flag (finding S-002). The
# letters are split and classified rather than matched as whole tokens.
PY_BOOL_FLAGS = frozenset("bBdEhiIOPqRsSuvVx")   # take no value
PY_SKIP_FLAGS = frozenset("WXQ")                 # take a value the guard ignores
PY_LONG_FLAGS = {"--help", "--help-env", "--help-xoptions", "--help-all", "--version"}
PY_LONG_VALUE_FLAGS = {"--check-hash-based-pycs"}
NODE_CODE_FLAGS = frozenset("epi")                # -e, -p, -i and their clusters
NODE_CODE_LONG = {"--eval", "--print", "--interactive"}
# A `VAR=value cmd` prefix used to be popped without reading the name, so a
# variable that names a program to run — LD_PRELOAD, LESSOPEN, GIT_EXTERNAL_DIFF,
# PAGER, PYTHONSTARTUP — passed behind an allow-listed program (finding S-002).
# These are the names a reproduction in this repository actually needs.
ENV_PREFIX_ALLOWED = frozenset((
    "CCGG_HOME", "CCGG_REPO", "CCGG_REF", "CLAUDE_PROJECT_DIR",
    "LANG", "LC_ALL", "TZ", "NO_COLOR", "GIT_CONFIG_NOSYSTEM", "PYTHONHASHSEED",
))
# The repository's own shell scripts, by name. check_shell used to return on the
# first non-flag argument, so `bash <anything>.sh` — including an absolute path —
# ran whatever the audited branch carried (finding S-001). Kept in step with the
# tree by check_guard_allow_lists in tools/validate.py.
SH_SCRIPTS = frozenset((
    ".claude/hooks/audit-verifier-guard.sh",
    ".claude/hooks/pre-compact.sh",
    ".claude/hooks/session-end.sh",
    ".claude/hooks/session-start.sh",
    "install.sh",
    "update.sh",
))
_ADDR = r"(?:\d+|\$|/(?:[^/\\]|\\.)*/)?(?:,(?:\d+|\$|/(?:[^/\\]|\\.)*/))?"
SED_WRITE_RE = re.compile(r"(?:^|[;\n{])\s*" + _ADDR + r"\s*[wWe]\b")
SED_SUBST_WRITE_RE = re.compile(
    r"(?:^|[;\n{])\s*" + _ADDR + r"\s*s(?P<d>.)(?:\\.|(?!(?P=d)).)*(?P=d)(?:\\.|(?!(?P=d)).)*(?P=d)[gpImM0-9]*[we]")
SAFE_REDIRECT_RE = re.compile(r"\s2>&1(?=\s|$)|\s&>\s*/dev/null|\s[12]?>\s*/dev/null")


def refuse(reason):
    print(f"audit-verifier-guard: refused ({reason}): the verifier runs read-only commands "
          f"from its allow-list only", file=sys.stderr)
    sys.exit(2)


def extract_substitutions(text):
    """Replace every $(...) with a placeholder and return the inner commands."""
    inner = []
    out = []
    i = 0
    while i < len(text):
        if text.startswith("$((", i):
            depth, j = 0, i + 1
            while j < len(text):
                if text[j] == "(":
                    depth += 1
                elif text[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if depth != 0:
                refuse("unbalanced arithmetic expansion")
            out.append("__ARITH__")
            i = j + 1
            continue
        if text.startswith("$(", i):
            depth, j = 0, i + 1
            while j < len(text):
                if text[j] == "(":
                    depth += 1
                elif text[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if depth != 0:
                refuse("unbalanced command substitution")
            inner.append(text[i + 2:j])
            out.append("__SUBST__")
            i = j + 1
            continue
        out.append(text[i])
        i += 1
    return "".join(out), inner


def segments(tokens):
    seg = []
    for tok in tokens:
        if is_separator(tok):
            if seg:
                yield seg
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg


def strip_redirects(seg):
    """Drop input redirects (`< file`, `<<< word`); refuse anything that writes."""
    out = []
    i = 0
    while i < len(seg):
        tok = seg[i]
        if tok in ("<", "<<<"):
            i += 2
            continue
        if tok.startswith("<<"):
            refuse("heredoc: pass input with printf ... |")
        if tok in ("<(", ">("):
            refuse("process substitution")
        if ">" in tok and re.fullmatch(r"[<>&|;()]+", tok):
            refuse("redirect to file")
        out.append(tok)
        i += 1
    return out


def check_py_script(path):
    """Allow the gate's own scripts as a script argument, and nothing else.

    Names, not contents: the guard cannot read what a file does. What it can do
    is keep `python3` pointed at the dozen files the gate consists of instead of
    at anything an audited branch adds (finding R-012). A branch that edits
    tools/validate.py itself still gets execution — that is what the base-ref
    copies in .github/workflows/audit.yml are for, not this hook.
    """
    norm = posixpath.normpath(path)
    if posixpath.isabs(norm) or norm == ".." or norm.startswith("../"):
        refuse("python script outside the worktree")
    directory, _, name = norm.rpartition("/")
    if directory not in PY_SCRIPT_DIRS:
        refuse("python script outside tools/")
    if name in PY_SCRIPTS:
        return
    refuse(f"{name} is not one of the gate's own scripts")


def check_sh_script(path):
    """Allow the repository's own shell scripts, and nothing else (finding S-001)."""
    norm = posixpath.normpath(path)
    if posixpath.isabs(norm) or norm == ".." or norm.startswith("../"):
        refuse("shell script outside the worktree")
    if norm in SH_SCRIPTS:
        return
    refuse(f"{norm} is not one of the repository's own shell scripts")


def check_py_module(module, rest):
    """`-m unittest` may discover only in the gate's own directory, or name a pinned
    test module; `-m doctest` takes a file, so it goes through the script rule."""
    if module == "unittest":
        target = next((a for a in rest if not a.startswith("-")), "")
        if target == "discover":
            where = rest[rest.index("-s") + 1] if "-s" in rest[:-1] else "tools"
            if posixpath.normpath(where) not in UNITTEST_DISCOVER_DIRS:
                refuse(f"unittest discover outside {'/'.join(sorted(UNITTEST_DISCOVER_DIRS))}/")
            return
        if target and target.split(".")[0] not in PY_TEST_MODULES:
            refuse(f"unittest target '{target}' is not one of the gate's own test modules")
        return
    if module == "doctest":
        target = next((a for a in rest if not a.startswith("-")), "")
        if target:
            check_py_script(target)
        return


def check_python(args):
    """Refuse code on the command line and any module outside PY_MODULES.

    Letters are read the way python reads them: a cluster like `-IBc` ends in
    the code flag, and a value may be attached (`-cCODE`, `-mjson.tool`) or be
    the next argument. Matching `-c` and `-m` as whole tokens missed every one
    of those forms, and the unrecognised token then fell through to the
    script-path branch (finding S-002).
    """
    i = 0
    saw_long_only = False
    while i < len(args):
        a = args[i]
        if a == "-":
            refuse("python code on the command line")
        if a == "--":
            i += 1
            continue
        if a.startswith("--"):
            name, sep, _ = a.partition("=")
            if name in PY_LONG_VALUE_FLAGS:
                i += 1 if sep else 2
                continue
            if name in PY_LONG_FLAGS:
                saw_long_only = True
                i += 1
                continue
            refuse(f"python option {name} is not in the allow-list")
        if a.startswith("-"):
            letters = a[1:]
            for pos, letter in enumerate(letters):
                rest = letters[pos + 1:]
                if letter == "c":
                    refuse("python code on the command line")
                if letter == "m":
                    attached = bool(rest)
                    module = rest or (args[i + 1] if i + 1 < len(args) else "")
                    if module in PY_MODULES:
                        return check_py_module(module, args[i + (1 if attached else 2):])
                    refuse("python -m with a module outside the allow-list")
                if letter in PY_SKIP_FLAGS:
                    i += 1 if rest else 2
                    break
                if letter not in PY_BOOL_FLAGS:
                    refuse(f"python option -{letter} is not in the allow-list")
            else:
                i += 1
            continue
        return check_py_script(a)
    if saw_long_only:
        return  # --version / --help print and exit; they run nothing
    refuse("python with no script")


def check_shell(args):
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-c", "-s", "-i", "-"):
            refuse("shell code on the command line or from stdin")
        if a == "-o":
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        return check_sh_script(a)
    refuse("shell with no script")


def check_git(args):
    i = 0
    while i < len(args):
        a = args[i]
        if a == "-C":
            # git takes -C's path as its own token; an attached -Cpath is git's own
            # error, not a spelling to cover here. The path may not leave the
            # worktree, or "git pointed at another repository" is a claim the
            # shorter option walks straight past.
            path = args[i + 1] if i + 1 < len(args) else ""
            if not path or path.startswith("-") or path.startswith("/") or ".." in path.split("/"):
                refuse("git -C pointed outside the worktree")
            i += 2
            continue
        if a in GIT_GLOBAL_FLAGS:
            i += 1
            continue
        if a.startswith("-"):
            refuse(f"git global option {a}")
        break
    if i >= len(args):
        refuse("git with no subcommand")
    sub, rest = args[i], args[i + 1:]
    if sub in GIT_READ:
        if sub == "log" and any(r.startswith("--output") for r in rest):
            refuse("git log --output")
        return
    if sub in GIT_LISTING:
        if any(r in GIT_LISTING[sub] for r in rest) or (sub in ("branch", "tag", "stash") and not rest):
            return
        refuse(f"git {sub} in a form that may write")
    refuse(f"git {sub}")


def check_sed(args):
    for a in args:
        if a in ("-i", "--in-place") or a.startswith("-i") or a.startswith("--in-place="):
            refuse("sed -i")
    scripts = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-e", "--expression", "-f", "--file"):
            if a in ("-f", "--file"):
                refuse("sed script from a file")
            scripts.append(args[i + 1] if i + 1 < len(args) else "")
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        if not scripts:
            scripts.append(a)
        i += 1
    for s in scripts:
        if SED_WRITE_RE.search(s) or SED_SUBST_WRITE_RE.search(s):
            refuse("sed w/e command")


def check_awk(args):
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-f", "--file"):
            refuse("awk program from a file")
        if a in ("-F", "-v"):
            i += 2
            continue
        if a.startswith("-") and a != "--":
            i += 1
            continue
        program = args[i + 1] if a == "--" and i + 1 < len(args) else a
        if "system(" in program or ">" in program or "|" in program or "getline" in program:
            refuse("awk writes or executes")
        return
    refuse("awk with no program")


def check_find(args):
    for a in args:
        if a in ("-delete", "-exec", "-execdir", "-ok", "-okdir") or a.startswith("-fprint") or a == "-fls":
            refuse(f"find {a}")


def check_node(args):
    """Same rule as check_python: node's letters cluster (`-pe`) and carry an
    attached value (`-e'code'`), so they are split rather than matched whole."""
    for a in args:
        if a == "-":
            refuse("node code on the command line")
        if a.startswith("--"):
            if a.partition("=")[0] in NODE_CODE_LONG:
                refuse("node code on the command line")
            continue
        if a.startswith("-"):
            for letter in a[1:]:
                if letter in NODE_CODE_FLAGS:
                    refuse("node code on the command line")
                if letter == "r":  # --require takes a value; stop reading letters
                    break
            continue
        return
    refuse("node with no script")


def check_segment(seg):
    seg = strip_redirects(seg)
    assigned = []
    while seg and (seg[0] in KEYWORDS or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", seg[0], re.S)):
        head = seg.pop(0)
        if head in ("for", "select", "case"):
            return  # the words of a for-list are data, not a command; case bodies follow
        name, sep, _ = head.partition("=")
        if sep:
            assigned.append(name)
    if not seg:
        return  # `x=$(...)` on its own is a shell variable, not an environment prefix
    # A name only matters once a command follows it: `VAR=value cmd` puts VAR in that
    # command's environment, and a variable can name a program to run (finding S-002).
    for name in assigned:
        if name not in ENV_PREFIX_ALLOWED:
            refuse(f"{name}= before a command is not an assignment the verifier may set — "
                   f"a variable can name a program for that command to run")
    prog = seg[0].rsplit("/", 1)[-1]
    args = seg[1:]
    if prog in ("timeout", "nice", "nohup", "command", "builtin", "exec"):
        if prog in ("exec", "nohup"):
            refuse(prog)
        if prog == "command" and args and args[0] in ("-v", "-V"):
            return
        i = 0
        while i < len(args) and (args[i].startswith("-") or (prog == "timeout" and re.fullmatch(r"[0-9.]+[smhd]?", args[i]))):
            i += 2 if args[i] in ("-k", "-s", "--kill-after", "--signal", "-n") else 1
        if i >= len(args):
            refuse(f"{prog} with no command")
        return check_segment(args[i:])
    if prog in PLAIN:
        return
    if prog in ("python3", "python", "python3.11", "python3.12", "python3.13", "python3.14"):
        return check_python(args)
    if prog in ("bash", "sh", "dash", "zsh"):
        return check_shell(args)
    if prog == "git":
        return check_git(args)
    if prog == "sed":
        return check_sed(args)
    if prog in ("awk", "gawk", "mawk"):
        return check_awk(args)
    if prog == "find":
        return check_find(args)
    if prog == "node":
        return check_node(args)
    if prog == "env" and not args:
        return
    refuse(f"{prog} is not in the allow-list")


def check_command(text, depth=0):
    if depth > 4:
        refuse("nesting")
    if "`" in text:
        refuse("backtick")
    text, inner = extract_substitutions(text)
    for sub in inner:
        check_command(sub, depth + 1)
    text = SAFE_REDIRECT_RE.sub(" ", text)
    # punctuation_chars=True is shlex's "();<>|&"; the newline and carriage return
    # are added so a second command on a second line is its own segment rather
    # than an argument to the first (finding S-001). Removing them from the
    # whitespace set is what makes shlex emit them; a newline inside quotes is
    # still ordinary data and stays inside its token.
    lexer = shlex.shlex(text, posix=True, punctuation_chars="();<>|&\n\r")
    lexer.whitespace_split = True
    lexer.whitespace = " \t"
    try:
        tokens = list(lexer)
    except ValueError:
        refuse("unparsable command")
    for seg in segments(tokens):
        check_segment(seg)


try:
    payload = json.load(sys.stdin)
except ValueError:
    print("audit-verifier-guard: hook input is not JSON; refusing", file=sys.stderr)
    sys.exit(2)
if payload.get("tool_name") != "Bash":
    sys.exit(0)  # this guard speaks only for Bash; anything else keeps its own rules
command = str((payload.get("tool_input") or {}).get("command", ""))
if not command.strip():
    refuse("empty command")
check_command(command)
# The allow-list is the verifier's permission, not merely its ceiling. Headless,
# nobody is there to answer a prompt, and the audit skill's grants name only the
# four report scripts — so a reproduction command that passes every check above
# was still refused before it ran. The hook decides, which is the right place:
# the guard has read the command, the grant set has not. Fixed string only: the
# command came from the tree under audit and never goes back into the model's
# context through here.
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "audit-verifier-guard: on the read-only allow-list",
}}))
sys.exit(0)
PY

# The guard program is the heredoc above. If it ever stops reaching this
# variable, `python3 -c ""` exits 0 and every command is allowed silently.
if [ -z "${GUARD:-}" ]; then
  echo "audit-verifier-guard: the guard program is empty; refusing" >&2
  exit 2
fi

printf '%s' "$INPUT" | python3 -c "$GUARD"
STATUS=$?
# Only two statuses are the guard's answer: 0 allow, 2 refuse. Anything else
# means it never got to decide — an uncaught exception, a signal, an interpreter
# that would not start. Claude Code blocks on exit 2 and treats every other
# status as "no objection", so this hook ending on the interpreter's own status
# let a crashed guard run the command (finding H-002). Fail closed instead.
case "$STATUS" in
  0|2) exit "$STATUS" ;;
esac
echo "audit-verifier-guard: the guard itself failed (exit $STATUS); refusing" >&2
exit 2
