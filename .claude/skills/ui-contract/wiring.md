# Wiring the contract into the app

A contract that only documents drifts within a release. Two pieces make it the source.

## 1. The app reads it — a command registry

Every control is rendered from a command id, never from a hand-placed button. The
registry answers one question — what is this command's state here — from the same
resolution rules the linter uses ([`contract-schema.md`](contract-schema.md)):

```js
// ui/commands.js — the only place that decides enabled, disabled, hidden
import contract from "../design/ui-contract.json";

const match = (pattern, ctx) =>
  new RegExp("^" + pattern.split("*").map(s => s.replace(/[.+?^${}()|[\]\\]/g, "\\$&")).join(".*") + "$").test(ctx);

export function commandState(id, ctx) {
  const c = contract.commands[id];
  if ((c.enabled || []).some(p => match(p, ctx))) return { kind: "enabled" };
  for (const [p, reason] of Object.entries(c.disabled || {})) if (match(p, ctx)) return { kind: "disabled", reason };
  if ((c.hidden || []).some(p => match(p, ctx))) return { kind: "hidden" };
  if (contract.policy?.off_context === "hidden") return { kind: "hidden" };
  const boards = [...new Set(Object.entries(contract.contexts)
    .filter(([cx]) => (c.enabled || []).some(p => match(p, cx)))
    .map(([, v]) => contract.boards[v.board].label))];
  return { kind: "disabled", reason: `Available in ${boards.join(", ")}` };
}

// A surface renders the commands whose home or `also` is this surface.
export function commandsOn(surface) {
  return Object.entries(contract.commands)
    .filter(([, c]) => c.home === surface || (c.also || []).some(a => a.surface === surface))
    .map(([id]) => id);
}
```

The current context is one value in app state — `"design.selection"` — set by the
board switcher and the selection model. Toolbars, menus and keyboard handlers all ask
`commandState(id, context)`; a shortcut for a non-enabled command does nothing. Each
control carries `data-command="<id>"` so tests can find it. A disabled control shows
the reason as its tooltip and accessible description.

Board output works the same way: the renderer and every exporter read
`boards[board].profile` for layer visibility and which measurements to draw. The
dimension tool never asks which board it is on; the profile answers.

## 2. A test holds the UI to it

One end-to-end test walks every context and compares what is rendered with what the
contract resolves. With Playwright, the app exposes a test hook to enter a context
(`window.__setContext("design.selection")`):

```js
// e2e/ui-contract.spec.js
import { test, expect } from "@playwright/test";
import contract from "../design/ui-contract.json";
import { commandState } from "../ui/commands.js";

for (const ctx of Object.keys(contract.contexts)) {
  test(`UI matches contract in ${ctx}`, async ({ page }) => {
    await page.goto("/");
    await page.evaluate(c => window.__setContext(c), ctx);
    for (const id of Object.keys(contract.commands)) {
      const want = commandState(id, ctx);
      const el = page.locator(`[data-command="${id}"]`).first();
      if (want.kind === "hidden") { await expect(el).toHaveCount(0); continue; }
      await expect(el).toBeVisible();
      if (want.kind === "enabled") await expect(el).toBeEnabled();
      else {
        await expect(el).toBeDisabled();
        await expect(el).toHaveAttribute("title", want.reason);
      }
    }
    // Nothing on screen that the contract does not know about.
    const rendered = await page.locator("[data-command]").evaluateAll(n => n.map(x => x.dataset.command));
    for (const id of rendered) expect(Object.keys(contract.commands)).toContain(id);
  });
}
```

The CI job runs both: `python3 tools/ui_contract_lint.py design/ui-contract.json --strict`
and this test. A pull request that adds a button edits the contract first, or fails.

Adapt the language and test runner to the project's stack; keep the two invariants —
one resolver, and a test that compares the rendered UI to it in every context.
