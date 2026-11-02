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
11. After revision feedback, update the deliverables, register the new bytes, rerun checks, and
    complete the same stage again. ADF preserves the previous reviewed artifact snapshot.
12. Summarize artifacts, checks, persisted state, and any remaining blocker. Never claim a stage is
    complete unless `adt stage complete` or `adt approve` succeeded.

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
