---
name: agentic-commands
description: Shared ADF execution protocol for stage-aware Antigravity commands, approvals, requirements, and recovery in an initialized project.
---

# ADF stage execution

The IDE agent is the execution layer. The `adt` CLI is the durable control plane: it stores the
current stage, attempts, artifact hashes, approvals, revisions, checkpoints, and errors. Never
describe a lifecycle command as if it performed the analysis or created the deliverables itself.

For `/start`, `/continue`, or `/adf-resume`, perform this loop from the project root:

1. Run `adt status`. For ADF recovery use `/adf-resume`, which runs `adt resume` first. For
   `/start`, run `adt start`. For `/continue`, run `adt start` when status is `not_started` and
   `adt continue` when it is active. A successful command prepares the stage and does not advance.
2. Read `.agentic/execution-contracts.yaml` and select the contract whose `id` is the reported
   stage. Treat its objective, prerequisites, inputs, responsibilities, instructions, outputs,
   validation, completion conditions, approval flag, and failure policy as mandatory.
3. Inspect every available required input and relevant project source. Do not invent missing facts.
4. Perform the stage's reasoning and repository work using the named specialist role. Keep work
   within the project and preserve unrelated changes.
5. If a material clarification or external dependency blocks correct work, record it in the
   appropriate artifact and run `adt stage fail --blocked "<actionable blocker>"`. Stop there.
6. Create every expected output. Outputs must be substantive, non-empty, and traceable to inputs.
7. Register every matching output with `adt artifact register <project-relative-path>`. Register
   again after any edit so the stored SHA-256 matches the current bytes.
8. Run the relevant project checks and contract validation criteria. On failure, preserve evidence
   and run `adt stage fail "<actionable failure>"`; do not advance.
9. Run `adt stage complete`. This is the only normal command that may advance a non-review stage.
10. If the stage enters `awaiting_approval`, show the registered deliverables and stop. Only the
    user may authorize `adt approve <stage>` or request `adt revise <stage> <feedback>`.
    Never infer approval of the production frontend or begin backend implementation early.
11. After revision feedback, update the deliverables, register the new bytes, rerun checks, and
    complete the same stage again. ADF preserves the previous reviewed artifact snapshot.
12. Summarize artifacts, checks, persisted state, and any remaining blocker. Never claim a stage is
    complete unless `adt stage complete` or `adt approve` succeeded.

## Existing-project discipline

For an existing or running application, **always read** `docs/discovery/existing-project-analysis.md`
and `.agentic/reports/existing-project-analysis.md` before proposing any work. Inspect the real
structure: source roots, frameworks, package managers, build and test commands, routes, modules,
data models, API boundaries, authentication, deployment configuration, conventions, and current
Git changes. Adapt the contract to that architecture; never impose a guessed folder layout.
Preserve staged, unstaged, and unrelated changes.

Compare requested behavior with the existing application and active ADF artifacts. Record discovered
bugs, broken commands, security concerns, inconsistent behavior, missing tests, and requirement
conflicts in the stage deliverable. Fix them only when the current approved scope authorizes the fix;
otherwise report them as actionable findings. Synchronize new work with completed and active tasks,
requirements IDs, decisions, and registered artifacts so parallel-looking requests do not conflict.

## Frontend implementation execution

For `frontend_implementation`, the deliverable is the actual production frontend — not a wireframe,
throwaway HTML demo, design prototype, or generic template.

### Step 1 — Design research (mandatory first step)

Before writing any code, research production websites and applications similar to the project idea:
- Identify 3–5 comparable sites and note their dominant design patterns.
- Record: color palette choices, typography decisions, navigation patterns, card/list styles,
  spacing density, use of imagery, micro-interaction patterns, and any unique design language.
- Identify what makes high-quality sites in this category feel authoritative and trustworthy.
- Save findings to `docs/frontend/design-research.md`.

### Step 2 — Design system definition (mandatory before page code)

Create `docs/frontend/design-system.md` with concrete values for every token category:

**Colors**: Define hex values for primary, primary-dark, primary-light, secondary, accent,
background, surface, surface-elevated, text-primary, text-secondary, text-disabled,
border, divider, success, warning, error, info, and overlay.

**Typography**: Font families (choose from Google Fonts or system fonts matching the project type),
weight scale (400, 500, 600, 700, 800), size scale (xs through 5xl with rem values), line-height
scale, and letter-spacing values.

**Spacing**: 4px base unit with a named scale (1–16 steps = 4px–64px).

**Border radius**: sm (4px), md (8px), lg (16px), xl (24px), full (9999px).

**Shadows**: none, xs, sm, md, lg, xl, 2xl — with actual box-shadow values.

**Motion**: duration-fast (100ms), duration-normal (200ms), duration-slow (300ms),
ease-in, ease-out, ease-in-out, ease-bounce — with cubic-bezier values.

**Breakpoints**: mobile (375px), tablet (768px), desktop (1024px), wide (1440px).

### Step 3 — Environment setup

Inspect the architecture and existing repository. Select the required frontend stack. Install
dependencies with its package manager. Prove the environment and build work. Record in
`docs/frontend/technology-and-environment.md`.

### Step 4 — Design inputs

Record input methods in `docs/frontend/design-inputs.json`: `figma_mcp`, `screenshots`, or
`generated_frontend`. For Figma, use authenticated design context and block honestly when access fails.

### Step 5 — Page inventory

Inventory all roles, routes, journeys, pages, responsive layouts, and all required states
(loading, empty, success, validation, permission, offline, error) before writing page code.
Record in `docs/frontend/page-inventory.md`.

### Step 6 — Implementation rules

- **Every color, font, spacing, border radius, shadow, and animation value must reference design
  system tokens.** No hardcoded one-off values (`#3B82F6` → `var(--color-primary)`).
- **No Lorem Ipsum on key pages.** Use realistic, project-appropriate placeholder content.
- **No generic template output.** Every page must feel designed for this specific project.
- Build complete role-aware production pages with realistic data, reusable components,
  responsive layouts, and all required states.

### Step 7 — Accessibility

Every visible control must be: semantic HTML, keyboard-accessible, have visible focus outline,
sufficient contrast (WCAG AA: 4.5:1 text, 3:1 UI), reduced-motion support, and meaningful
ARIA labels. This is not optional.

### Step 8 — Separation

Keep frontend and backend separate. Use typed mock data behind an adapter/service boundary.
Do not build backend logic or couple components to unfinished endpoints.

### Step 9 — Browser verification

Run the actual frontend in a browser at desktop (1440px), tablet (768px), and mobile (375px).
Exercise every page, state, navigation, form, dialog, and control. Check the console for errors.
Capture rendered screenshots. Compare to references. Fix defects. Repeat until clean.

### Step 10 — Registration

Register all required documents, source files, and verification screenshots. The implementation
manifest must record successful environment and production-build checks.

For `frontend_review`, present the running production frontend, design system summary, reference
comparison, known constraints, browser evidence, and revision history. Stop for explicit approval.
Revision feedback changes the production frontend itself, documents the intentional difference,
reruns build/browser checks, and registers the new bytes. Backend work cannot begin early.

## Backend and integration sequence

For `development_planning`, plan the backend and later integration from approved requirements,
architecture, frontend adapter needs, and page/state inventory. Define API contracts, validation,
identity and permissions, persistence, migrations, security, tests, dependencies, and failure behavior.

For `implementation`, build and test only the backend plan. Do not redesign the approved frontend or
bypass its adapter boundary. Record backend source, migrations, commands, tests, and API-contract
traceability in the required manifest and report.

For `integration`, replace frontend mocks through the adapter boundary. Verify request/response
contracts, authentication and authorization, validation, loading, empty, success, retry, timeout, and
error behavior end to end. Rerun backend, frontend, integration, and browser checks relevant to the
change. Visual changes require explicit revision rather than silent drift.

## Database validation

For `database_validation`: run all migrations from scratch, attempt rollback, inspect the actual
schema, compare to `docs/architecture/database-design.md`, run query analysis on primary read paths,
confirm no SQL injection vulnerabilities, and record all findings with command output as evidence.

## Security testing

For `security_testing`: read `docs/architecture/security-architecture.md` as the security baseline.
Test every authentication endpoint (login, logout, token refresh, password reset, account lockout).
Test authorization by attempting cross-user and unauthenticated access. Test all inputs for SQL
injection, XSS, CSRF, and SSTI. Check HTTP response headers (CSP, X-Frame-Options, HSTS).
Audit dependencies for CVEs. Confirm secrets never appear in logs, commits, or API responses.
Document every finding with severity (Critical / High / Medium / Low), reproduction steps,
evidence, and remediation. Re-test critical and high findings after remediation.

## Evidence quality

Evidence must name the command or inspection performed and its observed result. A planned check,
placeholder, generated filename, or assertion without execution is not evidence. Report failures
honestly, preserve diagnostics without secrets, and leave the workflow at the current stage when any
completion condition remains unsatisfied.

Other mappings:

- `/status`, `/pause`, `/stop`, `/review`, `/requirements`, and `/tasks` map to the same `adt`
  subcommand.
- `/approve <stage>` maps to `adt approve <stage>` only after explicit user approval.
- `/revise <stage> <feedback>` maps to `adt revise <stage> <feedback>`.
- `/help` maps to `adt help`; `adt stage show` displays the current structured contract.
- `adt artifact list` displays current registered deliverables and immutable metadata revisions.
- `/adf <request>` handles lifecycle or custom stage-scoped requests. It must persist custom work
  with `adt stage task` and may not bypass the current contract.
- Antigravity reserves `/resume` for conversation recovery. Use `/adf-resume` for ADF checkpoint
  recovery.

If checkpoint validation, artifact validation, or state migration fails, present the actionable
error. Do not reconstruct, skip, or overwrite durable state from conversation memory.
