#!/usr/bin/env bash
# SessionStart hook: tells Claude which global rule files apply to this
# project and which design files are missing. Output becomes session context.
# Never fails the session: any error just prints nothing.

dir="${CLAUDE_PROJECT_DIR:-$PWD}"
cd "$dir" 2>/dev/null || exit 0

notes=()

if [ -f package.json ] && grep -q '"next"' package.json 2>/dev/null; then
  notes+=("This is a Next.js project, so the Next.js stack rules apply.")
fi

if [ -d .claude/agents ] && ls .claude/agents 2>/dev/null | grep -qi 'prototyper'; then
  notes+=("This project runs the agent pipeline, so the pipeline design rules apply.")
fi

has_ui=false
if [ -f package.json ] || ls *.html >/dev/null 2>&1 || [ -d app ] || [ -d src ]; then
  has_ui=true
fi

if $has_ui; then
  [ -f PRODUCT.md ] || notes+=("PRODUCT.md is missing. On the first UI task, draft it with /impeccable init from the code and docs, labelling assumptions; ask the user only what the repository cannot answer.")
  [ -f DESIGN.md ]  || notes+=("DESIGN.md is missing. On the first UI task, create it right after PRODUCT.md, without asking: /impeccable document for an existing design, UI UX Pro Max for a new product. Report it in one line.")
fi

if [ ${#notes[@]} -gt 0 ]; then
  echo "Project design context:"
  for n in "${notes[@]}"; do echo "- $n"; done
fi

exit 0
