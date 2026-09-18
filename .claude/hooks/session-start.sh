#!/usr/bin/env bash
# Hook: session-start
# Triggered: at the start of every session (startup, resume, clear, compact)
# Purpose: open the session with repo health and memory pointers, per the
#          session protocol's "On session START" checklist.
#
# Portable by design: every check degrades to silence when its subject is
# absent, so this script is safe in any project that copies .claude/ in.
#
# Everything this hook prints reaches the model as context. So it prints fixed
# strings, timestamps, and names that pass a character allow-list — never a
# configured URL, an environment value, a file's contents, or a validator
# finding verbatim. A planted value has no path from disk into the prompt here.
set -uo pipefail

# Live update: sync CCGG-owned files (skills, hooks, agents, validator) from the
# guide clone at CCGG_HOME, so every session starts on the guide revision the
# project pinned. Skills also refresh mid-session on next invocation.
#
# Trust boundary: whatever update.sh finds in that clone runs here with the
# user's permissions, on every session start, resume, clear, and compact — and
# under `claude -p` with no trust dialog at all. So update.sh runs only when
#   - CCGG_REPO and CCGG_REF are both set. A missing value is not a check that
#     passed: without them there is no origin to verify the clone against and
#     no revision to hold it at, and update.sh would sync whatever the clone
#     happens to contain (finding R-001/S-004),
#   - CCGG_REPO is listed in the user-level record ~/.claude/ccgg-origins (or
#     $CLAUDE_CONFIG_DIR/ccgg-origins). The in-tree .claude/ccgg-origins is the
#     validator's reviewer aid, never this hook's boundary: it arrives on the
#     same branch as the env block that names the repository, so a checkout
#     could vouch for itself (findings R-002/S-001). No record allows nothing,
#   - CCGG_HOME and its update.sh are owned by this user (a pre-planted
#     directory at a shared path such as /tmp fails this),
#   - the clone's origin is CCGG_REPO,
#   - CCGG_REF is a refname (no leading `-`, no `..`, only [A-Za-z0-9._/-]) and
#     the clone's HEAD is at it. A 40-hex commit is checked locally; a tag or
#     branch is re-fetched from origin on every session start, and
#     tools/validate.py fails a project that pins one — a name is a value its
#     owner can move,
#   - the clone's working tree matches that commit: no tracked modification, and
#     nothing untracked or ignored under the directories update.sh copies
#     wholesale (finding R-001).
# A clone from CCGG_REPO is made only at CCGG_REF. Failures are printed, never
# hidden: a silent sync failure looks exactly like a compromised one.
ccgg_is_sha() { case "$1" in *[!0-9a-f]*|"") return 1 ;; esac; [ "${#1}" -eq 40 ]; }
# CCGG_REF reaches git as a bare argv element, so a value starting with `-` lands
# in option position: `fetch origin --upload-pack=...` is git's own documented way
# of naming a program to run (finding S-006). A refname cannot start with `-` or
# contain anything outside this class, so refusing the rest costs nothing.
ccgg_ref_ok() {
  case "$1" in -*|"") return 1 ;; esac
  case "$1" in *..*) return 1 ;; esac
  # The whole value, not a line of it: grep matches any one line, so a value
  # holding a newline passed on the strength of its first line.
  [[ "$1" =~ ^[A-Za-z0-9._/-]+$ ]]
}
ccgg_owned() { [ -O "$1" ] && [ -O "$1/update.sh" ]; }
# The pin check reads HEAD; the files update.sh copies come from the working
# tree. An update.sh edited in place, or a file dropped under the directories
# update.sh walks with find, passed every check above while HEAD sat at the pin
# (finding R-001). Tracked modifications anywhere refuse the sync — update.sh
# and the tools/ scripts are copied by name — and under the four directories
# copied wholesale, an untracked or ignored file refuses it too. A file outside
# those, such as a test run's cache, is not something update.sh would copy.
# A git that cannot answer is a refusal, never a clean bill.
ccgg_clean() { # $1 = clone
  dirty="$(git -C "$1" status --porcelain --untracked-files=no 2>/dev/null)" || return 1
  [ -z "$dirty" ] || return 1
  dirty="$(git -C "$1" status --porcelain --untracked-files=all --ignored=matching -- \
             .claude/skills .claude/hooks .claude/references .claude/agents 2>/dev/null)" || return 1
  [ -z "$dirty" ]
}
# One URL per line, `#` comments and blanks ignored, whole-line match — the same
# format tools/validate.py reads in the tree. The file must be this user's: a
# record anyone else could write is a record anyone else could extend.
ccgg_origin_trusted() { # $1 = CCGG_REPO
  [ -n "$1" ] || return 1
  record="${CLAUDE_CONFIG_DIR:-${HOME:-}/.claude}/ccgg-origins"
  [ -f "$record" ] && [ -O "$record" ] || return 1
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    case "$line" in ""|\#*) continue ;; esac
    [ "$line" = "$1" ] && return 0
  done < "$record"
  return 1
}
ccgg_origin_ok() { # $1 = clone, $2 = expected URL
  [ -n "$2" ] || return 1 # nothing to compare against is a failed check, not a passed one
  [ "$(git -C "$1" remote get-url origin 2>/dev/null)" = "$2" ]
}
ccgg_at_ref() { # $1 = clone, $2 = ref name or commit
  ccgg_ref_ok "$2" || return 1
  head="$(git -C "$1" rev-parse HEAD 2>/dev/null)" || return 1
  if ccgg_is_sha "$2"; then want="$2"; else
    # A name is answered only by refs/ccgg/pin, and only when the pin was written
    # for this same name by ccgg_move_to_ref — the fetch from the verified origin
    # that always precedes this check for a name. Never by the clone's own
    # refs/heads/<name> or refs/tags/<name>: `fetch origin -- <name>` leaves those
    # untouched, so a hand-cloned CCGG_HOME answered from a stale local branch —
    # first failing open (R-004), then, after the first fix resolved the name
    # first, failing closed forever, because nothing ever moved that branch.
    [ "$(git -C "$1" config --get ccgg.pinnedRef 2>/dev/null)" = "$2" ] || return 1
    want="$(git -C "$1" rev-parse --verify -q "refs/ccgg/pin^{commit}" 2>/dev/null)" || return 1
  fi
  [ -n "$head" ] && [ "$head" = "$want" ]
}
ccgg_move_to_ref() { # $1 = clone, $2 = ref name or commit: fetch it from origin, detach there
  ccgg_ref_ok "$2" || return 1
  git -C "$1" fetch -q --depth 1 --force origin -- "$2" \
    && git -C "$1" update-ref refs/ccgg/pin FETCH_HEAD \
    && git -C "$1" config ccgg.pinnedRef "$2" \
    && git -C "$1" checkout -q --detach refs/ccgg/pin
}
ccgg_clone() { # $1 = repo URL, $2 = ref name or commit, $3 = destination
  # core.autocrlf=false: on Windows a CRLF checkout of the guide makes every
  # sync copy every file (cmp sees CR bytes) and ships hooks that fail on
  # Linux with "bad interpreter: /bin/bash^M".
  git init -q "$3" \
    && git -C "$3" config core.autocrlf false \
    && git -C "$3" remote add origin "$1" \
    && ccgg_move_to_ref "$3" "$2" \
    && return 0
  rm -rf "$3"
  return 1
}
if [ -n "${CCGG_HOME:-}" ]; then
  CCGG_HOME="${CCGG_HOME/#\~/$HOME}" # settings.json env values are not shell-expanded
  if [ ! -e "$CCGG_HOME" ] && [ -n "${CCGG_REPO:-}" ] && command -v git >/dev/null 2>&1; then
    if [ -z "${CCGG_REF:-}" ]; then
      echo "-- ccgg: CCGG_REPO is set without CCGG_REF; refusing an unpinned clone — set CCGG_REF to a tag, branch, or commit --"
    elif ! ccgg_origin_trusted "$CCGG_REPO"; then
      echo "-- ccgg: CCGG_REPO is not listed in the user-level ccgg-origins record; refusing to clone — add its URL to ~/.claude/ccgg-origins to trust it on this machine --"
    else
      ccgg_clone "$CCGG_REPO" "$CCGG_REF" "$CCGG_HOME" >/dev/null 2>&1 \
        || echo "-- ccgg: clone of CCGG_REPO at CCGG_REF failed; live sync skipped --"
    fi
  fi
  if [ -x "${CCGG_HOME}/update.sh" ]; then
    if [ -z "${CCGG_REPO:-}" ] || [ -z "${CCGG_REF:-}" ]; then
      echo "-- ccgg: CCGG_HOME needs CCGG_REPO and CCGG_REF; refusing to run an unverified, unpinned update.sh --"
    elif ! ccgg_origin_trusted "$CCGG_REPO"; then
      echo "-- ccgg: CCGG_REPO is not listed in the user-level ccgg-origins record; live sync skipped — add its URL to ~/.claude/ccgg-origins to trust it on this machine --"
    elif ! ccgg_owned "$CCGG_HOME"; then
      echo "-- ccgg: CCGG_HOME is not owned by this user; live sync skipped --"
    elif ! ccgg_origin_ok "$CCGG_HOME" "$CCGG_REPO"; then
      echo "-- ccgg: CCGG_HOME's origin is not CCGG_REPO; live sync skipped --"
    elif ! ccgg_ref_ok "$CCGG_REF"; then
      echo "-- ccgg: CCGG_REF is not a refname; live sync skipped --"
    elif ! { ccgg_is_sha "$CCGG_REF" && ccgg_at_ref "$CCGG_HOME" "$CCGG_REF"; } \
        && ! { ccgg_move_to_ref "$CCGG_HOME" "$CCGG_REF" >/dev/null 2>&1 \
               && ccgg_at_ref "$CCGG_HOME" "$CCGG_REF"; }; then
      # A project that bumps CCGG_REF is followed, not stranded: the clone is
      # moved to the new pin (from the origin verified just above), and only a
      # clone that still is not there is refused.
      #
      # Only a commit pin takes the local fast path. A name is re-fetched every
      # session, because a name is a question only the origin can answer and the
      # clone was answering it from its own refs (finding R-004). update.sh
      # already re-fetches a name unconditionally; this hook now agrees with it.
      # That cost is one more reason tools/validate.py fails a movable CCGG_REF.
      echo "-- ccgg: CCGG_HOME could not be moved to CCGG_REF; live sync skipped --"
    elif ! ccgg_clean "$CCGG_HOME"; then
      echo "-- ccgg: CCGG_HOME has local modifications; live sync skipped — run git status there and restore it to the pin --"
    else
      "${CCGG_HOME}/update.sh" --quiet "${CLAUDE_PROJECT_DIR:-.}" || echo "-- ccgg: update.sh failed --"
    fi
  fi
fi

# Repo health: run the validator when the project ships one. Only its verdict
# line is printed — findings quote file content, and file content is not
# something this hook forwards to the model.
if [ -f "${CLAUDE_PROJECT_DIR:-.}/tools/validate.py" ] && command -v python3 >/dev/null 2>&1; then
  echo "-- repo validation --"
  VERDICT="$(python3 "${CLAUDE_PROJECT_DIR:-.}/tools/validate.py" 2>&1)"
  RC=$?
  echo "${VERDICT%%$'\n'*}"
  if [ "$RC" -ne 0 ]; then
    echo "(run python3 tools/validate.py for the findings — worth fixing early)"
  fi
fi

# Memory pointers: surface where the last session left off. The log name is
# the date /flush wrote it under; anything else in that directory is not named.
PROJECT_SLUG=$(basename "${CLAUDE_PROJECT_DIR:-$(pwd)}")
SESSIONS_DIR="${HOME}/.claude/memory/${PROJECT_SLUG}/sessions"
if [ -d "$SESSIONS_DIR" ]; then
  LATEST=$(ls -1 "$SESSIONS_DIR" 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$' | sort | tail -1)
  if [ -n "${LATEST:-}" ]; then
    echo "-- last session log: ${LATEST} in ~/.claude/memory/<project>/sessions/ (read it to pick up open threads) --"
  fi
fi
MARKERS="${HOME}/.claude/memory/session-markers.log"
if [ -f "$MARKERS" ]; then
  STAMP="$(tail -1 "$MARKERS" | sed -n 's/^\(\[[0-9TZ:+-]*\]\).*/\1/p')"
  if [ -n "${STAMP:-}" ]; then
    echo "-- last session end: ${STAMP} --"
  fi
fi

# Open decisions: surface records still awaiting confirmation — tracked files
# only, named only when the name is plain.
DECISIONS_DIR="${CLAUDE_PROJECT_DIR:-.}/decisions"
if [ -d "$DECISIONS_DIR" ] && command -v git >/dev/null 2>&1; then
  OPEN=""
  SKIPPED=0
  while IFS= read -r rec; do
    [ -n "$rec" ] || continue
    name="$(basename "$rec")"
    grep -q '\*\*Status:\*\* proposed' "${CLAUDE_PROJECT_DIR:-.}/$rec" 2>/dev/null || continue
    # No word from the tree reaches the prompt. The first fix replaced a
    # character allow-list (which forbade spaces and read as safe, but hyphens
    # join words as well as spaces do) with a date-prefixed slug of at most seven
    # words — and seven words is a sentence: R-001's own payload,
    # `ignore-previous-instructions-and-do-x`, fit. So the slug decides only
    # whether a record is well-formed; what is printed is its date, which is
    # enough to find it with `ls decisions/<date>-*.md`.
    if [[ "$name" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2})-[a-z0-9]+(-[a-z0-9]+){0,6}\.md$ ]]; then
      OPEN="${OPEN}decisions/${BASH_REMATCH[1]}-*.md"$'\n'
    else
      SKIPPED=$((SKIPPED + 1))
    fi
  done < <(git -C "${CLAUDE_PROJECT_DIR:-.}" ls-files -- 'decisions/*.md' 2>/dev/null)
  if [ -n "${OPEN:-}" ]; then
    echo "-- open decisions (status: proposed), by date --"
    printf '%s' "$OPEN" | sort | uniq -c | sed 's/^ *\([0-9]*\) \(.*\)$/\2 (\1)/'
  fi
  # Counted, never named: a record whose name does not fit the slug is still
  # worth knowing about, and the count carries no text from the tree.
  if [ "$SKIPPED" -gt 0 ]; then
    echo "-- ${SKIPPED} decision record(s) skipped: name is not a date-prefixed slug --"
  fi
fi

exit 0
