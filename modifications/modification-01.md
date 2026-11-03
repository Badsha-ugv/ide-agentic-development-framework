# Critical ADF Improvement: Implement Actual Workflow Execution

The first PyPI release of Agentic Development Framework is working, and I have tested it with a new project using Antigravity.

However, I discovered a critical functional gap.

## Current problem

My current workflow:

1. Run `adt init`.
2. Add a project description under `requirements/inbox/`.
3. Run `adt requirements ingest`.
4. Open the project in Antigravity.
5. Type `/continue`.

The CLI reports:

Status: active
Stage: project_discovery

But no discovery analysis, SRS, documentation, or other deliverables are generated.

The current `adt continue` implementation appears to advance the persisted workflow state without executing the actual responsibilities of the stage.

I do not want ADF to be just a workflow-state tracker. I want it to be an actual AI-driven software development orchestration framework controlled through IDE agents.

## Primary objective

Implement the missing execution layer so that a user can control the entire application development lifecycle through simple IDE commands.

The intended user experience:

```text
adt init
adt requirements ingest

Open project in Antigravity

/continue
```

The IDE agent should automatically:

- Read ADF instructions and skills.
- Inspect persisted workflow state.
- Identify the current stage.
- Understand the stage's execution requirements.
- Perform the actual work.
- Generate required documents and artifacts.
- Validate generated deliverables.
- Update persistent state and checkpoints.
- Present results to the user.
- Stop at mandatory approval gates.

The user should not need to write a long prompt describing what the agent should do after every command.

## 1. Audit the complete existing implementation

Before modifying anything, inspect:

- Workflow engine and stage definitions.
- CLI commands and lifecycle operations.
- SQLite state management.
- Checkpoint and recovery implementation.
- Approval management.
- Requirements ingestion.
- Generated AGENTS.md.
- Antigravity rules.
- Shared agentic-commands skill.
- Configuration and runtime templates.
- Existing documentation and tests.

Identify exactly why the current `/continue` command does not execute project discovery.

Do not assume the problem is limited to the skill file.

Provide an implementation plan before making changes.

Preserve existing working functionality and user data.

## 2. Separate workflow transition from workflow execution

This is mandatory.

The current workflow state management must not pretend that an AI task has been completed merely because a stage was advanced.

Define clear operations:

- Read current stage.
- Prepare stage execution instructions.
- Execute stage through the IDE agent.
- Record execution progress.
- Validate stage deliverables.
- Mark stage completed.
- Request approval.
- Approve or request revision.
- Advance to the next eligible stage.

The CLI cannot independently execute an AI model unless an AI provider is explicitly integrated. In the initial architecture, the IDE agent performs the reasoning and implementation while the CLI provides reliable state and artifact operations.

Redesign `adt continue` carefully so it cannot silently skip required work.

Provide a backward-compatible migration strategy for existing workflow databases.

## 3. Implement a complete command contract

Define and document the expected behavior of:

| Command | Expected behavior |
|---|---|
| `/start` | Begin the workflow and execute the first eligible stage |
| `/continue` | Execute or resume the current pending stage |
| `/status` | Show current stage, execution progress, approvals and blockers |
| `/pause` | Safely pause and checkpoint |
| `/resume` | Restore and continue execution |
| `/stop` | Stop without losing progress |
| `/review` | Show deliverables waiting for human review |
| `/approve` | Record approval and unlock the next eligible stage |
| `/revise` | Record feedback and return the relevant deliverable for revision |
| `/help` | Explain available commands |

CLI equivalents should be available where appropriate.

Do not claim that an arbitrary slash command is natively registered in every IDE. Implement and document Antigravity-compatible command interpretation through generated instructions and skills.

## 4. Implement the stage execution contract

Every workflow stage must have a machine-readable or clearly structured execution definition.

At minimum, define:

- Stage ID and name.
- Objective.
- Prerequisites.
- Required input files.
- Required agent responsibilities.
- Execution instructions.
- Expected output artifacts.
- Validation criteria.
- Completion conditions.
- Approval requirements.
- Failure and retry behavior.

The main orchestrator agent must use this contract to decide what to do.

Do not hardcode all stage behavior inside one enormous prompt.

Use reusable agent definitions and stage-specific instructions.

## 5. Implement actual project discovery and documentation generation

The first application workflow should work as follows:

### Stage 1: Project initialization

- Inspect the project.
- Read submitted requirements.
- Detect new or existing project.
- Identify project constraints and available resources.

### Stage 2: Project discovery

- Analyze the submitted project description.
- Identify business objectives.
- Identify stakeholders and user types.
- Identify application scope.
- Identify major features.
- Identify business rules.
- Identify known technical constraints.
- Identify risks, assumptions and missing information.
- Ask clarification questions through the IDE conversation.

Generate initial discovery artifacts, such as:

```text
docs/
  discovery/
    project-overview.md
    stakeholder-analysis.md
    clarification-log.md
    assumptions-and-risks.md
```

Do not fabricate answers to missing questions.

### Stage 3: Requirements engineering

After clarification, generate:

```text
docs/
  requirements/
    SRS.md
    functional-requirements.md
    non-functional-requirements.md
    user-stories.md
    acceptance-criteria.md
    requirements-traceability.md
```

Maintain stable requirement IDs and traceability to the immutable source requirements.

Present the generated documents for review.

Wait for approval.

### Stage 4: System architecture

After requirements approval, prepare:

- Technology evaluation.
- System architecture.
- Application component boundaries.
- Database design and ERD.
- API design.
- Authentication and authorization.
- Security architecture.
- Deployment architecture.
- Infrastructure requirements.

Generate architecture documents and request approval.

### Stage 5: UI/UX design

- Use Figma MCP when a Figma file is provided and the integration is configured.
- Otherwise generate an interactive HTML/CSS/JavaScript prototype.
- Present the prototype for approval.
- Do not start production frontend implementation before approval.

### Stage 6: Development planning

Generate:

- Development milestones.
- Task breakdown.
- Dependencies.
- Frontend/backend separation.
- Testing plan.
- Integration plan.
- Delivery criteria.

### Stage 7 onward: Implementation and delivery

Support:

- Frontend development.
- Backend development.
- Database implementation.
- API integration.
- Automated testing.
- Code review.
- Security checks.
- Docker configuration.
- CI/CD.
- Deployment preparation.
- Technical documentation.
- Release verification.

All work must remain traceable to approved requirements and architecture.

## 6. Implement proper IDE agent instructions

The generated Antigravity configuration must explicitly explain:

When a user types `/continue`:

1. Read the ADF command skill.
2. Read the current persisted workflow state.
3. Identify the current stage.
4. Load that stage's execution contract.
5. Inspect all required input artifacts.
6. Execute the actual stage responsibilities.
7. Ask clarification questions when necessary.
8. Generate expected artifacts.
9. Validate the deliverables.
10. Update ADF state using the appropriate CLI operations.
11. Present a clear summary.
12. Stop at mandatory approval gates.

The agent must not simply execute `adt continue` and report the new stage.

The same principle applies to `/start` and `/resume`.

Make the command skill concise, reusable, and explicit.

Check Antigravity's actual skill and rule discovery behavior. Do not invent unsupported IDE functionality.

## 7. Approval and revision behavior

Implement real approval gates.

For example:

```text
Stage: requirements_engineering
Status: awaiting_approval

Deliverables:
- SRS.md
- functional-requirements.md
- non-functional-requirements.md

User actions:
- /review
- /approve
- /revise
```

When a user requests revisions:

- Preserve the previous approved or submitted version.
- Record revision feedback.
- Update affected documents.
- Revalidate the deliverables.
- Request approval again.

Never mark a stage approved merely because documents exist.

## 8. Persistent execution and recovery

The workflow must survive:

- Closing Antigravity.
- Starting a new IDE conversation.
- Restarting the computer.
- Pausing a task.
- An agent execution failure.

SQLite and project artifacts remain the source of truth.

Persist:

- Current stage.
- Execution status.
- Current task.
- Generated artifacts.
- Approval status.
- Revision history.
- Checkpoints.
- Errors and retry information.

The IDE conversation must never be the only place where execution progress exists.

## 9. Testing requirements

Add integration tests proving:

1. `/continue` instructions resolve the current stage rather than blindly advancing it.
2. Project discovery instructions are available to the IDE agent.
3. Discovery artifacts can be generated and registered.
4. The stage cannot complete before its required deliverables are validated.
5. Requirements approval blocks architecture execution.
6. Revision requests preserve history.
7. A new IDE session can recover the correct next action.
8. Pausing and resuming do not lose execution progress.
9. Failed execution does not falsely mark a stage complete.
10. Antigravity's generated instruction and skill files contain the correct command contract.

Use mock agent execution for tests. Do not require actual paid AI API calls in the test suite.

## 10. Documentation and migration

Update:

- README.
- Workflow architecture documentation.
- Command reference.
- Antigravity setup guide.
- Stage execution guide.
- Approval and revision guide.
- Existing implementation progress documentation.

Explain the distinction between CLI state operations and IDE agent execution.

Ensure existing initialized projects can upgrade without losing their SQLite state, requirements versions, or generated files.

## 11. Final delivery

Do not stop after writing a proposal.

Implement the changes, add tests, run the test suite, and report:

- Root cause of the current problem.
- Architecture changes.
- CLI behavior changes.
- IDE instruction changes.
- New execution contracts.
- Tests and results.
- Migration requirements.
- Any remaining limitations.

Do not publish a new PyPI version automatically.

The definition of done is simple:

I initialize a new project, submit a project description, ingest requirements, open Antigravity, and type `/continue`.

The agent must actually perform project discovery, ask questions when needed, generate the discovery artifacts, and maintain persistent workflow state.

I should not have to explain the workflow to the agent every time.

Build this as a reusable framework capability, not a one-off prompt for a single application.