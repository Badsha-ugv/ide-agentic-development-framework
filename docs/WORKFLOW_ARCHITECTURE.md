# Workflow architecture

ADF separates reasoning from durable control.

The IDE agent is the execution layer. It reads project inputs, applies a specialist role, asks
questions, writes artifacts, and runs verification. The `adt` CLI is the control plane. It does
not contain an AI provider and cannot honestly claim that analysis occurred. It persists workflow
and execution state in SQLite, registers artifact hashes, validates completion, enforces approval
gates, creates checkpoints, and records retries.

## Transition model

Each stage follows this sequence:

1. `adt start` or `adt continue` changes the current execution to `in_progress` and returns its
   contract. It never completes or advances the stage.
2. The IDE agent reads `.agentic/execution-contracts.yaml`, inspects inputs, performs the work, and
   creates the required outputs.
3. `adt artifact register PATH` records the stage, path, byte size, SHA-256, and metadata revision.
4. `adt stage complete` verifies that every output pattern resolves to non-empty files and that
   every file's current hash is registered.
5. A normal stage becomes `completed` and advances. A review stage becomes `awaiting_approval` and
   does not advance.
6. `adt approve STAGE` records explicit approval, completes the review stage, and advances.
   `adt revise STAGE FEEDBACK` snapshots the submitted files and returns the same stage to
   `in_progress`.

SQLite under `.agentic/database/` is authoritative. JSON files under `.agentic/state/` are
inspection snapshots only. Requirements source versions remain independently immutable under
`requirements/versions/`.

## Recovery

Pause and stop create integrity-checked checkpoints. Resume validates the newest checkpoint and
restores its stage. Stage execution rows retain the current task, attempt count, blocker, error,
timestamps, and completion state across IDE sessions. Artifact, approval, and revision records are
included in checkpoints.

## Compatibility

Schema version 1 databases are upgraded additively to schema version 2 when any workflow command
opens them. Existing workflow rows, requirements versions, tasks, approvals, checkpoints, and
events are preserved. Re-run `adt init` after upgrading ADF to install newly introduced managed
files. Conflicting generated instructions are preserved and updated content is written below
`.agentic/proposals/` for review rather than overwriting project customizations.
