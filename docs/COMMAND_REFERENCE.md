# Command reference

Commands are available as CLI operations. Antigravity discovers workspace skills at
`.agents/skills/<name>/SKILL.md` and exposes them as `/<name>`. ADF generates command-named skills
that delegate to the shared `agentic-commands` execution protocol.

| IDE request | CLI operation | Contract |
|---|---|---|
| `/start` | `adt start` | Activate and prepare the first pending stage; the IDE agent then executes it. |
| `/continue` | `adt continue` | Prepare or resume the current stage; never silently advance. |
| `/status` | `adt status` | Show workflow stage, execution state, current task, attempts, approval, artifacts, errors, and blockers. |
| `/pause` | `adt pause` | Pause and create a checkpoint. |
| `/adf-resume` | `adt resume`, then `adt continue` | Validate the latest checkpoint, restore its stage, and continue IDE-agent execution. Antigravity owns the built-in `/resume`. |
| `/stop` | `adt stop` | Stop and checkpoint without deleting progress. |
| `/review` | `adt review` | List pending/revision-requested gates and registered deliverables. |
| `/approve STAGE` | `adt approve STAGE` | Explicitly approve the current waiting gate and advance. |
| `/revise STAGE FEEDBACK` | `adt revise STAGE FEEDBACK` | Preserve the submitted version, store feedback, and reopen the same stage. |
| `/help` | `adt help` | Explain framework commands. |

Execution support commands:

```bash
adt stage show
adt stage task "custom stage-scoped request"
adt artifact register docs/discovery/project-overview.md
adt artifact list
adt stage complete
adt stage fail "test command failed"
adt stage fail --blocked "Product owner must answer the retention question"
adt command create verify-api "Run API verification relevant to the current stage"
adt command list
```

`adt stage complete` is the normal advancement operation. It fails when required outputs are
missing, empty, unregistered, or changed after registration. Re-register a changed file before
retrying completion.

`/adf <request>` is the generic state-aware entry point. A command created with `adt command create`
also performs status and contract preflight, persists its current task, and cannot bypass stage
prerequisites, policy, validation, or approvals.
