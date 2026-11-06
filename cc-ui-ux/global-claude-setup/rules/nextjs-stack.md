---
paths:
  - "**/next.config.*"
  - "app/**"
  - "src/app/**"
  - "components/**"
  - "**/*.{ts,tsx}"
---

# Next.js stack rules

Apply this file only when the project's `package.json` lists `next` as a dependency. Ignore it in any other project.

## Stack

- Next.js App Router (`app/` directory). No Pages Router.
- TypeScript with `strict: true`. No `any`; use `unknown` and narrow it.
- Tailwind CSS v4. Theme lives in CSS (`@theme` in `app/globals.css`). No `tailwind.config.js`; do not create one.
- shadcn/ui on Radix primitives. Icons from `lucide-react` only.
- Forms with `react-hook-form` and `zod` v4 via `@hookform/resolvers/zod`.
- Use the package manager the project's lockfile shows. Do not add dependencies without saying why and asking first.

## Server and client boundary

- Every component is a Server Component by default.
- Add `"use client"` only to the smallest leaf that needs state, effects, event handlers, or browser APIs. Never mark a whole page or layout as client.
- Pass only plain serializable props from server to client.
- `useState` for local state, `useContext` for state shared across a subtree. No global state library unless asked.
- Never import server-only code into a client component.

## Data and mutations

- Fetch data in Server Components with `async`/`await`. No `useEffect` fetching for initial data.
- Mutations go through Server Actions in an `actions.ts` next to the route, marked `"use server"`.
- Every Server Action validates input with the same `zod` schema the form uses.
- After a mutation, call `revalidatePath` or `revalidateTag` explicitly.
- Only `NEXT_PUBLIC_` environment variables may reach the client.

## Structure and naming

```
app/[route]/page.tsx, loading.tsx, error.tsx, actions.ts
components/ui/          shadcn generated
components/[feature]/   feature components built from ui/
lib/schemas/            zod schemas shared by forms and actions
lib/utils.ts            cn() and small helpers
hooks/                  client hooks, prefixed use-
types/                  shared types
```

- Files and folders in kebab-case. Components exported in PascalCase.
- One component per file. Named exports, except the files Next.js requires as default exports.
- Any route that fetches data has `loading.tsx` and `error.tsx`.

## shadcn/ui

- Add components only with `npx shadcn@latest add <component-name>`.
- Do not edit `components/ui/` for feature needs; wrap instead. Edit it only for a deliberate project-wide change, and say so.
- Use `cn()` for conditional classes and `cva` for variants.
- Use semantic token classes like `bg-background`, `text-muted-foreground`, `border-border`. Never raw palette classes like `bg-blue-500`, and no arbitrary values like `w-[347px]` without a stated reason.

## Checks before done

```bash
npm run lint
npx tsc --noEmit
npm run build
```

Swap `npm` for the project's package manager.
