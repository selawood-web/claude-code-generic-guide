#!/usr/bin/env bash
# Hook: audit-verifier-guard (PreToolUse, matcher Bash)
# Registered by: .claude/agents/audit-verifier.md, for that subagent only.
# Purpose: allow the audit's verifier only the commands a reproduction needs —
#          the repository's own tests and tools, git reads, and text inspection —
#          as a second layer under the worktree isolation the runtime already
#          enforces. Exit 2 blocks the call; the reason on stderr reaches the
#          model. The rule is an allow-list: a command is run only when every
#          segment of it (each side of a pipe, `&&`, `;`, and every `$(...)`)
#          starts with an allowed program in an allowed form. Anything else —
#          an unknown program, an interpreter given code on its command line,
#          a redirect to a file, a heredoc, a backtick — is refused, so the
#          guard fails closed by construction.
#
# Not registered in settings.json on purpose: this guard is scoped to one
# subagent. The audit's deterministic stage knows that and does not flag it.
# The table of allowed forms is tested by tools/test_verifier_guard.py.
set -uo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "audit-verifier-guard: python3 is required to inspect the command; refusing" >&2
  exit 2
fi

# The hook's JSON arrives on stdin; capture it before anything else reads stdin.
INPUT="$(cat)"

read -r -d '' GUARD <<'PY' || true
import json, re, shlex, sys

KEYWORDS = {"if", "then", "else", "elif", "fi", "for", "while", "until", "do", "done",
            "in", "!", "{", "}", "(", ")", "time", "[[", "]]"}
SEPARATORS = {"|", "||", "&&", ";", "&", ";;", "|&"}
# Programs that never write and never reach the network on their own.
PLAIN = {
    "cat", "head", "tail", "wc", "ls", "stat", "file", "diff", "cmp", "sort", "uniq",
    "cut", "tr", "grep", "egrep", "fgrep", "rg", "xxd", "od", "hexdump", "strings",
    "jq", "which", "type", "id", "whoami", "pwd", "date", "basename", "dirname",
    "realpath", "readlink", "tree", "column", "nl", "tac", "rev", "expr", "seq",
    "echo", "printf", "test", "[", "true", "false", "read", "sleep", "printenv",
    "md5sum", "sha256sum", "sha1sum", "du", "df", "cd", "pushd", "popd", "export",
    "local", "declare", "set", "unset", "exit", "return", "break", "continue", ":",
    "shift", "let", "shellcheck", "pytest", "ruff", "mypy", "flake8", "pyflakes",
    "git-lfs", "less", "more", "comm", "join", "paste", "fold", "fmt", "yes",
}
GIT_READ = {
    "log", "show", "diff", "status", "rev-parse", "ls-files", "ls-tree", "cat-file",
    "grep", "blame", "describe", "rev-list", "name-rev", "shortlog", "check-ignore",
    "check-attr", "diff-tree", "diff-index", "for-each-ref", "show-ref", "symbolic-ref",
    "var", "count-objects", "verify-commit", "verify-tag", "merge-base", "whatchanged",
    "reflog", "fsck", "version", "help",
}
GIT_LISTING = {"branch": {"--list", "-a", "-r", "-v", "-vv", "--show-current", "--contains",
                          "--merged", "--no-merged", "-l"},
               "tag": {"--list", "-l", "-n", "--contains", "--points-at"},
               "remote": {"-v", "show", "get-url"},
               "config": {"--get", "--get-all", "--get-regexp", "--list", "-l"},
               "worktree": {"list"},
               "stash": {"list", "show"},
               "notes": {"list", "show"}}
PY_MODULES = {"unittest", "pytest", "json.tool", "doctest", "py_compile", "tokenize"}
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
        if tok in SEPARATORS:
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


def check_python(args):
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-c", "-"):
            refuse("python code on the command line")
        if a == "-m":
            if i + 1 < len(args) and args[i + 1] in PY_MODULES:
                return
            refuse("python -m with a module outside the allow-list")
        if a in ("-W", "-X"):
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        return  # a script path: the repository's own code, run inside the worktree
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
        return  # a script path
    refuse("shell with no script")


def check_git(args):
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-C", "-c"):
            i += 2
            continue
        if a.startswith("--git-dir") or a.startswith("--work-tree"):
            refuse("git pointed at another repository")
        if a.startswith("-"):
            i += 1
            continue
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
    for a in args:
        if a in ("-e", "--eval", "-p", "--print", "-i", "--interactive", "-"):
            refuse("node code on the command line")
        if not a.startswith("-"):
            return
    refuse("node with no script")


def check_segment(seg):
    seg = strip_redirects(seg)
    while seg and (seg[0] in KEYWORDS or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", seg[0], re.S)):
        head = seg.pop(0)
        if head in ("for", "select", "case"):
            return  # the words of a for-list are data, not a command; case bodies follow
    if not seg:
        return
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
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
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
    sys.exit(0)
command = str((payload.get("tool_input") or {}).get("command", ""))
if not command.strip():
    refuse("empty command")
check_command(command)
sys.exit(0)
PY

printf '%s' "$INPUT" | python3 -c "$GUARD"
