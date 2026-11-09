# UI contract — schema and rules

One JSON file per product, conventionally `design/ui-contract.json`. Checked by
`tools/ui_contract_lint.py`. A worked example: [`example-contract.json`](example-contract.json).

## Sections

| Key | Shape | Meaning |
|-----|-------|---------|
| `product` | string | name, for the report |
| `policy.off_context` | `"disabled"` or `"hidden"` | what a command shows outside the boards where it works; default `disabled` |
| `policy.max_enabled_per_context` | integer | the cognitive budget per context; default 12 |
| `model.layers` | list of names | every layer the one model has |
| `model.measurements` | list of names | every measurement kind the model can produce |
| `boards.<id>` | `label`, `purpose`, `profile` | a board is an output lens over the model |
| `boards.<id>.profile` | `output`, `layers`, `measurements` | the deliverable, and how each layer (`show`, `ghost`, `hide`) and measurement (`show`, `hide`) renders |
| `contexts.<id>` | `board`, `label` | a place the user can be; ids are conventionally `<board>.<state>` |
| `surfaces.<id>` | `label`, `contexts` | a toolbar, panel or menu, and the contexts (glob patterns) where it appears |
| `commands.<id>` | see below | one action |

A command:

| Key | Required | Meaning |
|-----|----------|---------|
| `label` | yes | the name the user sees; unique across the product |
| `does` | yes | one sentence, true in every context — never an object keyed by board |
| `home` | yes | the one surface where it canonically lives |
| `also` | no | further entry points, each `{"surface", "why"}` |
| `shortcut` | no | keyboard shortcut |
| `enabled` | yes | context patterns where it works |
| `disabled` | no | `{pattern: reason}` — where it shows grey, and the sentence that tells the user why and how to enable it |
| `hidden` | no | context patterns where it does not show at all |

Patterns are shell globs over context ids: `*`, `design.*`, `design.selection`.

**State resolution**, per command and context: `enabled` if a pattern matches; else
the matching `disabled` reason; else `hidden` if a pattern matches; else the policy —
`hidden`, or `disabled` with a generated reason naming the boards where it works
("Available in Manufacture"). Inside a board where the command works, the state must be
declared explicitly (UC12): a default reason there would be wrong.

## Rules

| Code | Severity | Fails when | The UX rule it guards |
|------|----------|-----------|-----------------------|
| UC01 | error | a section, key or value is missing or malformed | — |
| UC02 | error | a context names an undeclared board, or a board has no `purpose` | every place belongs to one purpose |
| UC03 | error | a profile omits or invents a layer or measurement, or names no `output` | same logic, other output |
| UC04 | error | `home` or an `also` surface is undeclared, repeated, or an `also` has no `why` | one home; a second way in must justify itself |
| UC05 | error | two commands share a label | one name, one command |
| UC06 | error | one shortcut fires two commands in a shared context | one key, one meaning |
| UC07 | error | a command is enabled where none of its surfaces appear | enabled must mean reachable |
| UC08 | error | a pattern matches no context, a surface appears nowhere, or a command is enabled nowhere | no dead entries |
| UC09 | warning | a context enables nothing | no dead ends |
| UC10 | warning | a context enables more than the budget | only what is relevant |
| UC11 | warning | a command has more than three entry points | users stop knowing where it lives |
| UC12 | error | a disabled state has no reason, or a state inside the command's own board is undeclared | grey must explain itself |
| UC13 | error | a command is claimed by two states in one context | one context, one state |
| UC14 | error | `does` varies by board | same tool, same behaviour |

`--strict` makes warnings fail; use it for the target contract and in CI.
