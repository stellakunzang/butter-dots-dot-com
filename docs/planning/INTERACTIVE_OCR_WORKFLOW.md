# Interactive OCR — Working Agreement

**Companion to:** [INTERACTIVE_OCR_PLAN.md](INTERACTIVE_OCR_PLAN.md)
**Purpose:** Instructions for a fresh chat picking up a single ticket from the plan. Read this *and* the plan ticket before writing any code.

---

## How this is structured

Each ticket (T-01, T-02, ...) is worked in its own fresh chat to keep context small. The user opens a new chat and says something like:

> Work on T-02 from the interactive OCR plan. Workflow is in `docs/planning/INTERACTIVE_OCR_WORKFLOW.md`.

You (the assistant) then:
1. Read this file
2. Read the specific ticket in `INTERACTIVE_OCR_PLAN.md`
3. Re-read the **Deployment posture** section of the plan
4. Confirm scope and base branch with the user before writing code

---

## Branching strategy

- **`main`** — production. Nothing in this plan merges here until the user explicitly says so. Do not target PRs at `main`.
- **`feat/interactive-ocr`** — long-lived integration branch off `main`. All ticket PRs target this. Sits open as long as needed.
- **`feat/interactive-ocr/T-NN-slug`** — one branch per ticket.
  - **Default:** branch off `feat/interactive-ocr`.
  - **Stacked case:** if the ticket depends on another whose PR is still open, branch off that dependency's branch instead. When the dependency merges into `feat/interactive-ocr`, rebase this branch onto `feat/interactive-ocr` and force-push (note: force-push to the ticket branch only — never `main` or `feat/interactive-ocr`).

The integration branch may not exist yet on a fresh chat. Check with `git branch -a` and `git fetch origin` first; if it's missing, create it: `git checkout -b feat/interactive-ocr origin/main && git push -u origin feat/interactive-ocr`.

### Slug convention

`feat/interactive-ocr/T-NN-short-slug`, e.g.:
- `feat/interactive-ocr/T-01-ocr-engine-sync`
- `feat/interactive-ocr/T-02-sanskrit-detector`
- `feat/interactive-ocr/T-02b-sanskrit-in-spellcheck-api`

---

## Per-ticket workflow

1. **Confirm the ticket with the user** before reading or editing anything. Surface dependencies (the ticket's `Dependencies:` line) and ask whether those are merged into `feat/interactive-ocr` or still open as PRs.
2. **Determine base branch:** `feat/interactive-ocr` by default; dependency's branch if stacking.
3. **Create the ticket branch** off the chosen base.
4. **Implement** against the ticket's scope and acceptance criteria. Stay in scope — if you find related work, note it for the user but don't expand the PR.
5. **Tick off A/C boxes** in `INTERACTIVE_OCR_PLAN.md` as you complete them. The plan edit goes in the same PR as the code.
6. **Commits:** use the `git-commit-agent` subagent for every commit. Do not run `git commit` directly via Bash. (Standing memory rule, repeated here for new chats.)
7. **PR:** use the `open-pr-agent` subagent.
   - Target: `feat/interactive-ocr` (not `main`).
   - Title: `[T-NN] <short description>`.
   - Body must:
     - Link back to the ticket section in `docs/planning/INTERACTIVE_OCR_PLAN.md`.
     - Reproduce the A/C checklist with boxes checked.
     - Note the `Deploy:` tag from the ticket.
     - Note if rebased on top of another open PR (stacked case).
8. **Do not merge.** The user reviews and merges on their own schedule.

---

## Deployment guardrails (re-read every time)

The plan's **Deployment posture** section tags each ticket as one of:

- **`prod`** — pure-local improvements, no API cost. Safe to ship later.
- **`local-only`** — workflow scaffolding. Code can live in the repo but entry points should be off in prod (no public route, no UI link).
- **`behind-flag`** — calls the Claude API. Must be gated; for now this means no prod wiring at all. When auth lands later, a `FEATURE_AI_OCR_ASSIST` flag plus admin role check will gate the routes.

**Concretely, while working a ticket:**
- `behind-flag` tickets must not add a frontend link or a publicly-reachable API route. Local CLI / direct backend call only.
- `local-only` tickets that add API routes should guard the routes with an env check (e.g., `if not settings.LOCAL_DEV_MODE: raise 404`). It's fine to leave the env var unset in prod — the route becomes a no-op.
- Anything tagged `prod` must not depend on anything tagged `local-only` or `behind-flag`.

If you can't tell which side of the line you're on, ask the user.

---

## Plan as living doc

If implementing the ticket reveals something that needs to change in the plan (a missed dependency, a renamed module, a wrong assumption), edit `INTERACTIVE_OCR_PLAN.md` in the same PR and call out the change in the PR body. Don't silently drift from the plan.

---

## Things to confirm before writing code (every fresh chat)

- [ ] Which ticket (`T-NN`)
- [ ] Have you read this workflow doc and the ticket in `INTERACTIVE_OCR_PLAN.md`?
- [ ] Are the ticket's dependencies merged into `feat/interactive-ocr`? If not, which open branch should this one stack on?
- [ ] What's the `Deploy:` tag, and are there any in-scope ways this could leak into prod?
- [ ] Anything in the plan that's now stale and should be edited as part of this PR?
