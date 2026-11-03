# Approvals and revisions

Requirements, architecture, design, and release review are mandatory human approval gates.
Creating documents does not approve them.

When `adt stage complete` validates a review stage, its execution becomes `awaiting_approval` and
the workflow remains on that stage. Use `adt review` to inspect registered deliverables. Only an
explicit `adt approve STAGE` records approval and advances.

To request changes:

```bash
adt revise requirements_review "Clarify administrator permissions and acceptance criteria"
```

ADF copies the submitted registered artifacts to
`.agentic/revisions/STAGE/revision-N/`, records the feedback and snapshot path in SQLite, and
returns the same stage to `in_progress`. The IDE agent updates only affected working documents,
registers their new hashes, revalidates all deliverables, and runs `adt stage complete` again.
Approval is requested again; revision feedback never implies approval.

Revision snapshots, artifact metadata revisions, approval state, event history, and checkpoints
survive process and IDE restarts. The normal project documents remain the editable working copy;
the snapshot is the immutable review-history evidence.

For `design_review`, revision work changes the actual production frontend, documents the intentional
decision in `docs/frontend/revision-history.md`, registers the new source bytes, and reruns browser
verification for affected pages, states, and viewports. The frontend is never automatically
approved, and backend planning or implementation cannot begin until
`adt approve design_review` succeeds.
