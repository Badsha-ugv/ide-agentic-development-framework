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

For an existing or running application, inspect its real structure before proposing work: source
roots, frameworks, package managers, build and test commands, routes, modules, data models, API
boundaries, authentication, deployment configuration, conventions, and current Git changes. Adapt
the contract to that architecture; never impose a guessed folder layout. Preserve staged, unstaged,
and unrelated changes.

Compare requested behavior with the existing application and active ADF artifacts. Record discovered
bugs, broken commands, security concerns, inconsistent behavior, missing tests, and requirement
conflicts in the stage deliverable. Fix them only when the current approved scope authorizes the fix;
otherwise report them as actionable findings. Synchronize new work with completed and active tasks,
requirements IDs, decisions, and registered artifacts so parallel-looking requests do not conflict.

## Production frontend execution

For `ui_ux_design`, the deliverable is the actual production frontend—not a wireframe, throwaway
HTML demo, or design prototype.

1. Run `adt requirements screenshots` and open every relevant image. Search approved requirements for
   Figma URLs. A manifest or filename is not visual inspection.
2. Inspect the architecture and existing frontend. Record the frontend root, framework, language,
   styling and component systems, package manager, runtime, install command, and build command.
3. Install only compatible required dependencies. Prove the environment works before UI coding and
   record the result in `docs/frontend/technology-and-environment.md`.
4. Select one or more honest input modes in `docs/frontend/design-inputs.json`: `figma_mcp`,
   `screenshots`, or `generated_frontend`. When Figma is selected, use authenticated design context
   and record its requirement source and URL; persist a blocker if it cannot be inspected.
5. Inventory all roles, routes, journeys, pages, responsive layouts, and relevant loading, empty,
   success, validation, permission, offline, and error states before declaring coverage complete.
6. For supplied references, reproduce layout, dimensions, spacing, typography, colors, assets,
   hierarchy, responsive behavior, and interactions without unapproved deviation. Requirements govern
   behavior; references govern presentation. Ask when they materially conflict.
7. Without an external reference, create a distinctive, coherent design system before pages. Use
   deliberate typography, spacing, color, hierarchy, reusable tokens/components, realistic content,
   restrained purposeful motion, and strong information architecture. Avoid generic template output.
8. Every visible control must do meaningful work. Implement semantic structure, keyboard access,
   visible focus, contrast, reduced-motion support, clear feedback, and good perceived performance.
9. Keep frontend and backend separate. Use typed mock data behind an adapter/service boundary; do not
   build backend logic or couple UI components directly to unfinished endpoints in this stage.
10. Run the real frontend in a browser. Exercise every page, state, navigation path, form, filter,
    dialog, and other control at desktop, tablet, and mobile sizes. Check the console, capture rendered
    evidence, compare each page to its reference, fix defects, and repeat.
11. Register all required evidence and every source file listed in
    `docs/frontend/implementation-manifest.json`. The manifest must record successful environment and
    production-build checks. Do not claim exactness based only on code inspection.

For `design_review`, present the running production frontend, reference comparison, known constraints,
browser evidence, and revision history. Stop for explicit approval. Revision feedback changes the
production frontend itself, documents the intentional difference, preserves unrelated approved work,
reruns affected build/browser checks, and registers the new bytes. Backend work cannot begin early.

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
