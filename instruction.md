# Build an Agentic Development Framework

## Project objective

Build a reusable, portable, AI-powered software development framework named **Agentic Development Framework (ADF)**.

The framework will allow developers to use an AI coding agent inside supported IDEs, including:

- OpenAI Codex in VS Code
- Google Antigravity
- Other IDE agents that support repository instructions, skills, custom agents or equivalent capabilities

A developer should be able to install the framework into an existing or new software project, open that project in an IDE, select their preferred AI model, and control the development lifecycle through simple chat commands.

The initial developer experience must be:

```bash
python -m agentic_framework init
```

Then, inside the IDE agent chat:

```text
/start
```

The AI should understand the framework, inspect the project, and follow the configured software development lifecycle.

The developer should not need to manually create agent files, instruction files, workflow files, project folders, or configuration files.

**Build the actual working framework. Do not stop after producing documentation, diagrams, or a proposed architecture.**

---

# 1. Core product principles

Follow these principles throughout implementation:

1. Local-first: the initial framework must work locally without requiring a hosted orchestration server.
2. AI-provider agnostic: do not hard-code OpenAI, Claude, Gemini or any other provider into the core framework.
3. IDE-aware: generate appropriate configuration for each supported IDE/harness.
4. Human-controlled: important deliverables must have explicit review and approval states.
5. Persistent: workflow state must survive IDE closure, terminal closure and machine restarts.
6. Resumable: execution must resume from verified checkpoints rather than replaying the entire conversation.
7. Safe: agents must not overwrite unrelated changes, expose secrets or perform unsafe Git operations.
8. Extensible: new agents, skills, IDE adapters and workflow stages must be addable without rewriting the core.
9. Portable: developers should be able to share the framework through GitHub and install it in their own projects.
10. Minimal initial complexity: do not build a web dashboard, hosted service, custom IDE extension or remote agent runtime in the first release.

The framework must have a clean separation between:

- Core framework logic
- Agent definitions
- Skills
- Workflow definitions
- IDE adapters
- Project-specific configuration
- Runtime state
- User-provided requirements

Do not duplicate the entire workflow for every IDE. Maintain one canonical workflow and generate or adapt IDE-specific configuration from it.

---

# 2. Technology decisions

Use the following initial technology stack:

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| CLI | Typer |
| State database | SQLite |
| Configuration | YAML |
| Validation | Pydantic |
| Logging | Python logging + JSONL event log |
| Testing | Pytest |
| Git integration | Git CLI through a safe wrapper |
| Container integration | Docker CLI |
| Documentation | Markdown |
| CI/CD | GitHub Actions |
| Package management | pyproject.toml |
| IDE integration | Native instructions, skills and agent adapters |

Use well-maintained dependencies and keep the dependency list small.

Do not introduce LangGraph, CrewAI, a vector database, PostgreSQL, Redis, a web dashboard or a custom IDE extension in the first version.

Keep interfaces modular so these technologies can be added later if justified.

---

# 3. Repository structure

Create a professional and maintainable repository.

Use this structure as the starting point. You may improve it when there is a clear technical reason, but document structural changes.

```text
agentic-development-framework/
│
├── AGENTS.md
├── README.md
├── LICENSE
├── CHANGELOG.md
├── pyproject.toml
├── .gitignore
│
├── requirements/
│   ├── framework/
│   │   ├── version-001/
│   │   └── README.md
│   └── development/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── INSTALLATION.md
│   ├── USER_GUIDE.md
│   ├── IDE_COMPATIBILITY.md
│   ├── AGENT_SYSTEM.md
│   ├── WORKFLOW_LIFECYCLE.md
│   ├── REQUIREMENTS_MANAGEMENT.md
│   ├── STATE_MANAGEMENT.md
│   ├── SECURITY.md
│   ├── CONTRIBUTING.md
│   └── decisions/
│
├── src/
│   └── agentic_framework/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       │
│       ├── core/
│       │   ├── config.py
│       │   ├── project.py
│       │   ├── workflow.py
│       │   ├── command_registry.py
│       │   ├── task_manager.py
│       │   ├── approval_manager.py
│       │   ├── checkpoint_manager.py
│       │   └── event_manager.py
│       │
│       ├── state/
│       │   ├── database.py
│       │   ├── models.py
│       │   ├── repositories.py
│       │   ├── migrations/
│       │   └── snapshots.py
│       │
│       ├── requirements_manager/
│       │   ├── ingestion.py
│       │   ├── versioning.py
│       │   ├── comparison.py
│       │   ├── traceability.py
│       │   └── validation.py
│       │
│       ├── project_analyzer/
│       │   ├── discovery.py
│       │   ├── stack_detector.py
│       │   ├── git_analyzer.py
│       │   └── existing_project.py
│       │
│       ├── integrations/
│       │   ├── git.py
│       │   ├── docker.py
│       │   ├── github.py
│       │   └── filesystem.py
│       │
│       ├── adapters/
│       │   ├── base.py
│       │   ├── codex.py
│       │   ├── antigravity.py
│       │   └── vscode.py
│       │
│       ├── templates/
│       │   ├── project/
│       │   ├── ide/
│       │   ├── agents/
│       │   ├── skills/
│       │   ├── workflows/
│       │   └── github-actions/
│       │
│       └── utils/
│           ├── paths.py
│           ├── validation.py
│           └── exceptions.py
│
├── framework/
│   ├── agents/
│   ├── skills/
│   ├── workflows/
│   ├── policies/
│   ├── templates/
│   └── config/
│
├── adapters/
│   ├── codex/
│   ├── antigravity/
│   └── vscode/
│
├── scripts/
│   ├── validate_framework.py
│   └── build_package.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── acceptance/
│   └── fixtures/
│
└── examples/
    ├── django-react/
    └── nextjs/
```

Keep canonical agent instructions and skills in the framework source. Generate project-specific IDE files from these canonical definitions during initialization.

Do not create unnecessary placeholder files. Every module must have a clear responsibility.

---

# 4. Installation and initialization

Implement the following command:

```bash
python -m agentic_framework init
```

Also expose a convenient installed CLI:

```bash
adt init
```

The initialization process must:

1. Detect the current working directory.
2. Determine whether it is an empty directory or an existing software project.
3. Detect whether the project already has Git initialized.
4. Detect available project technologies and package managers.
5. Detect supported IDE configuration where possible.
6. Ask only for essential missing project-level information.
7. Create the `.agentic/` runtime directory.
8. Initialize the SQLite database.
9. Install the canonical project instructions.
10. Install the relevant IDE adapter files.
11. Install the agent definitions and skills.
12. Create the requirements folder structure.
13. Create the documentation structure.
14. Create the initial workflow configuration.
15. Initialize Git only when Git is not already initialized.
16. Never overwrite existing project configuration without explicit permission.
17. Generate an initialization report.

The initialization command must be idempotent. Running it again must not duplicate files, reset state or overwrite user changes.

For existing files, provide a safe conflict strategy:

- Preserve the original.
- Compare the existing file with the framework template.
- Create a proposed updated copy when necessary.
- Report the conflict.
- Require approval before replacement.

The initialized project must have this structure:

```text
my-project/
│
├── .agentic/
│   ├── config.yaml
│   ├── workflow.yaml
│   ├── policies.yaml
│   ├── agent-registry.yaml
│   ├── database/
│   │   └── agentic.db
│   ├── state/
│   │   ├── workflow.json
│   │   ├── tasks.json
│   │   └── execution.json
│   ├── checkpoints/
│   ├── logs/
│   │   └── events.jsonl
│   └── reports/
│
├── .agents/
│   ├── rules/
│   └── skills/
│
├── .codex/
│   └── agents/
│
├── .github/
│   ├── agents/
│   ├── instructions/
│   └── workflows/
│
├── requirements/
│   ├── inbox/
│   ├── versions/
│   │   └── version-001/
│   ├── reports/
│   └── README.md
│
├── docs/
│   ├── PROJECT_CONTEXT.md
│   ├── SRS.md
│   ├── FEATURES.md
│   ├── USER_FLOWS.md
│   ├── REQUIREMENT_TRACEABILITY.md
│   ├── architecture/
│   ├── design/
│   ├── decisions/
│   ├── revisions/
│   └── reports/
│
├── design-prototype/
├── tests/
├── AGENTS.md
├── README.md
└── .gitignore
```

Create application-specific folders such as `frontend/`, `backend/`, `docker/` and deployment configuration later, according to the project's requirements and architecture. Do not assume every project uses the same stack.

---

# 5. Command system

Implement a centralized command registry.

The following commands must be supported by the framework:

| Command | Behavior |
|---|---|
| `/start` | Start a new workflow or initialize the current project workflow |
| `/status` | Display current workflow and task status |
| `/pause` | Safely pause execution and persist state |
| `/resume` | Resume from the last verified checkpoint |
| `/continue` | Execute the next eligible pending task |
| `/stop` | Safely stop active execution and persist state |
| `/help` | Show available commands |
| `/review` | Show deliverables waiting for approval |
| `/approve` | Approve a pending deliverable |
| `/revise` | Record revision feedback |
| `/requirements` | Show current requirements version and ingestion status |
| `/tasks` | Display tasks, dependencies and progress |

Also implement CLI equivalents:

```bash
adt start
adt status
adt pause
adt resume
adt continue
adt stop
adt help
adt review
adt approve
adt revise
adt requirements
adt tasks
```

### IDE command compatibility

Do not assume that arbitrary slash commands can be registered natively in every IDE.

Implement a shared command interpretation skill and generate IDE-specific command/skill entry points where supported.

For Codex, generate:

- Root `AGENTS.md`
- Project skills in the supported skill discovery location
- Codex custom agent definitions
- A command interpretation skill that maps the user's commands to framework operations

For Antigravity, generate:

- `AGENTS.md`
- `.agents/rules/`
- `.agents/skills/`

For VS Code agent environments, generate the relevant supported agent and instruction files.

The chat agent must interpret `/start`, `/pause`, `/resume` and other commands as framework commands when the user sends them.

If a native slash command is not supported, the user must still be able to type the same command as ordinary chat input.

Do not require the user to manually configure these files.

---

# 6. Workflow orchestration

Create a configurable workflow state machine.

The initial default lifecycle must be:

```text
PROJECT INITIALIZATION
        |
        v
PROJECT DISCOVERY
        |
        v
REQUIREMENTS INGESTION
        |
        v
REQUIREMENTS ANALYSIS
        |
        v
SRS AND PROJECT DOCUMENTATION
        |
        v
REQUIREMENTS REVIEW
        |
        v
SYSTEM ARCHITECTURE
        |
        v
ARCHITECTURE REVIEW
        |
        v
UI/UX DESIGN
        |
        v
DESIGN REVIEW
        |
        v
DEVELOPMENT PLANNING
        |
        v
FRONTEND / BACKEND IMPLEMENTATION
        |
        v
INTEGRATION
        |
        v
QA AND TESTING
        |
        v
CODE REVIEW AND SECURITY REVIEW
        |
        v
DOCKER AND CI/CD VALIDATION
        |
        v
FINAL DOCUMENTATION
        |
        v
RELEASE REVIEW
        |
        v
COMPLETED
```

Each stage must define:

- Stage ID
- Purpose
- Required inputs
- Assigned agent
- Expected outputs
- Dependencies
- Validation rules
- Approval requirements
- Failure behavior
- Retry policy
- Checkpoint policy

The workflow must be configurable. Different projects may skip or modify stages where appropriate, but required safety and verification checks must remain.

Do not allow the workflow to advance past a mandatory approval gate without approval.

---

# 7. Agent system

Create canonical agent definitions.

Initial agents:

1. Main Orchestrator
2. Requirements Analyst
3. Software Architect
4. UI/UX Designer
5. Frontend Developer
6. Backend Developer
7. Integration Engineer
8. QA Engineer
9. Code Reviewer
10. Security Reviewer
11. DevOps Engineer

Each agent definition must include:

- Unique ID
- Name
- Role
- Responsibilities
- Scope
- Required inputs
- Expected outputs
- Allowed tools
- Restricted operations
- Verification requirements
- Handoff format
- Failure and escalation rules

### Main Orchestrator

The orchestrator is the main coordinator between the developer and the specialist agents.

It must:

- Understand the user's goals.
- Inspect the project.
- Ask relevant clarification questions.
- Maintain the project context.
- Build and maintain the task plan.
- Assign tasks to appropriate agents.
- Track dependencies and progress.
- Collect agent outputs.
- Verify required deliverables.
- Present review items to the developer.
- Record approvals and revisions.
- Recover interrupted tasks.
- Update project documentation.
- Decide the next eligible workflow action.

The orchestrator must not assume that it can spawn specialist agents in every IDE.

Use native subagents when the selected harness supports them. If it does not, use a sequential specialist workflow in the current agent session.

A specialist role must remain usable even when native subagent delegation is unavailable.

Do not pretend that a separate agent or model was invoked if the IDE did not actually invoke one.

### Agent execution contract

All agents must use a standardized task contract.

A task must contain:

```json
{
  "task_id": "TASK-001",
  "agent_id": "backend_developer",
  "title": "Implement authentication",
  "description": "Implement the approved authentication requirements",
  "inputs": [],
  "dependencies": [],
  "expected_outputs": [],
  "acceptance_criteria": [],
  "status": "pending"
}
```

An agent result must contain:

- Task ID
- Status
- Files created or modified
- Decisions made
- Tests performed
- Test results
- Unresolved issues
- Risks
- Next recommended action

The orchestrator must validate the result before marking a task complete.

---

# 8. Requirements management

This is a critical framework feature.

Developers must be able to supply requirements through multiple files:

- PDF
- DOCX
- Markdown
- TXT
- XLSX
- CSV
- Images
- Other supported formats

Do not assume every format can be extracted using the Python standard library. Use appropriate optional dependencies and report unsupported or failed extraction clearly.

### Requirements folder

Create:

```text
requirements/
├── inbox/
├── versions/
│   ├── version-001/
│   ├── version-002/
│   └── version-003/
├── reports/
└── README.md
```

The user can put initial requirement files in `requirements/inbox/`.

When `/start` is executed:

1. Find the supplied files.
2. Inventory and identify their types.
3. Extract available text and metadata.
4. Identify missing, ambiguous and conflicting requirements.
5. Create an immutable initial requirements version.
6. Preserve the original files.
7. Produce a requirements summary.
8. Generate the SRS and traceability records.
9. Request review where required.

### Requirements versioning

Never silently overwrite an existing version.

For every new requirements submission:

1. Create a new version.
2. Preserve the previous version.
3. Compare the new version with the previous version.
4. Identify added requirements.
5. Identify modified requirements.
6. Identify removed requirements.
7. Identify conflicting requirements.
8. Identify affected documents.
9. Identify affected architecture components.
10. Identify affected implementation tasks and tests.
11. Generate an impact report.
12. Ask for approval before changing approved project decisions.

Example:

```text
requirements/
├── inbox/
├── versions/
│   ├── version-001/
│   │   ├── source-files/
│   │   ├── manifest.json
│   │   └── requirements.md
│   └── version-002/
│       ├── source-files/
│       ├── manifest.json
│       └── requirements.md
└── reports/
    └── version-001-to-002-impact.md
```

Use file hashes to detect duplicate or changed source files.

Maintain requirement IDs and traceability:

```text
REQ-001
  -> SRS section
  -> Architecture component
  -> Development task
  -> Test case
```

Requirements versions and implementation document revisions must be tracked separately.

---

# 9. New and existing project support

The framework must support two project modes.

### New project

The orchestrator should:

- Understand the business objective.
- Collect requirements.
- Identify users and user roles.
- Define functional and non-functional requirements.
- Generate SRS.
- Generate features and user flows.
- Propose a technology stack.
- Design the architecture and database.
- Define APIs and integrations.
- Prepare development tasks.
- Start implementation after approval.

### Existing project

The orchestrator must not assume that the repository is empty.

It must first:

- Inspect the Git repository and working tree.
- Identify the existing application structure.
- Detect programming languages and frameworks.
- Inspect dependencies.
- Inspect existing documentation.
- Inspect models, APIs and routes.
- Inspect Docker and CI/CD configuration.
- Inspect tests and test coverage where available.
- Identify existing features.
- Identify incomplete features.
- Identify technical debt.
- Identify security and reliability risks.
- Run safe existing checks where possible.

Generate:

```text
docs/reports/EXISTING_PROJECT_ANALYSIS.md
docs/reports/RECOMMENDED_ROADMAP.md
```

Do not rewrite working code merely to match framework templates.

The framework must adapt its workflow to the actual repository.

---

# 10. Design workflow

The framework must support two design scenarios.

### Scenario A: Existing Figma design

If the user supplies a Figma URL or an accessible Figma project:

- Use available Figma MCP capabilities when configured.
- Inspect frames, components, styles and layout.
- Identify reusable design components.
- Document design decisions.
- Implement the approved design in the selected frontend technology.
- Preserve the original design intent.

If Figma access is unavailable, report the limitation and request an export or other usable design input.

### Scenario B: No Figma design

Do not automatically create a Figma file.

Instead, the UI/UX agent must generate a working visual prototype using:

- HTML
- CSS
- JavaScript
- Tailwind CSS where appropriate

Store it in:

```text
design-prototype/
```

The prototype must:

- Be responsive.
- Have realistic sample data.
- Include functional navigation.
- Include meaningful interactions.
- Represent important user flows.
- Use a consistent design system.
- Be easy to preview locally.

The developer/client reviews the prototype.

Only after approval should the frontend implementation agent build the production frontend in the selected framework, such as React, Next.js or Vue.

Do not mechanically convert prototype HTML into production code. Use the prototype as an approved visual and interaction reference.

---

# 11. Development execution

After architecture and design approval:

1. Break implementation into epics and tasks.
2. Identify dependencies.
3. Assign tasks to specialist agents.
4. Define acceptance criteria.
5. Create feature branches where appropriate.
6. Implement backend and frontend work.
7. Integrate components.
8. Run tests.
9. Review code.
10. Update documentation.
11. Record checkpoints.

Prefer small, verifiable implementation tasks.

Avoid allowing multiple agents to edit the same files simultaneously unless the execution environment safely isolates their work.

When native subagents are available, use them for independent work. Otherwise execute sequentially.

Do not mark work complete merely because code was generated. Require appropriate verification.

---

# 12. Git management

The framework must provide safe Git integration.

Requirements:

- Detect existing Git repositories.
- Initialize Git only when necessary.
- Inspect uncommitted changes before modifying files.
- Never overwrite unrelated user changes.
- Never commit credentials, `.env` files or secrets.
- Use meaningful branch names.
- Use conventional commit messages.
- Associate commits with task IDs.
- Check changes before committing.
- Run relevant tests before merge.
- Preserve Git history.
- Avoid force-pushing.
- Respect protected branches.
- Prepare pull requests where GitHub integration is available.
- Do not merge without the configured approval policy.

Suggested branches:

```text
main
develop
feature/TASK-001-authentication
bugfix/TASK-020-login-error
release/v1.0.0
```

Do not assume that every repository uses this exact branch model. Detect and respect existing conventions.

---

# 13. Docker and CI/CD

Every generated application must be designed to run using Docker.

The framework must generate or maintain appropriate:

- Dockerfile
- docker-compose.yml
- .dockerignore
- .env.example
- Development configuration
- Production configuration
- Health checks
- Service dependencies

Select services according to the application architecture.

For example, a Django application may require:

- Django/Gunicorn
- PostgreSQL
- Redis
- Celery
- Nginx

Do not add unnecessary services.

Implement GitHub Actions workflows appropriate to the project:

- Linting
- Unit tests
- Integration tests
- Build verification
- Dependency/security scanning
- Docker image build
- Deployment workflow

Deployment must require the configured approval policy.

Never commit real secrets. Use repository secrets or environment-based configuration.

---

# 14. State management and recovery

Use SQLite as the transactional source of truth.

Store:

- Project metadata
- Workflow status
- Current phase
- Tasks
- Task dependencies
- Agent assignments
- Deliverables
- Approvals
- Revisions
- Checkpoints
- Events
- Requirements version metadata

Also maintain:

- JSON snapshots for convenient inspection.
- Markdown reports for human-readable state.
- JSONL event logs for execution history.
- Git history for source and documentation changes.

The runtime state must not depend on the current IDE conversation.

### Pause

When `/pause` is received:

- Stop scheduling new tasks.
- Finish or safely interrupt the current operation.
- Save the active task state.
- Save a checkpoint.
- Record pending approvals.
- Mark the workflow as paused.

### Stop

When `/stop` is received:

- Stop new execution immediately.
- Safely handle active operations.
- Persist the latest recoverable state.
- Record which tasks were completed, interrupted or left pending.
- Do not delete project files or state.

### Resume

When `/resume` is received:

- Load the latest database state.
- Validate the last checkpoint.
- Inspect the Git working tree.
- Identify interrupted tasks.
- Check relevant project health.
- Reconstruct the minimum required agent context.
- Resume from the next safe operation.

### Continue

When `/continue` is received:

- Identify the next eligible task.
- Check dependencies and approvals.
- Execute the next task.
- Verify the result.
- Update state.

The framework must be idempotent. It must not repeat already-completed work or create duplicate commits simply because an execution was interrupted.

---

# 15. Human approval and revision

The human developer must remain in control of important decisions.

Use explicit approval states:

```text
pending
in_review
approved
revision_requested
rejected
blocked
```

Approval gates should initially apply to:

- Requirements/SRS
- System architecture
- Design prototype
- Major implementation milestones
- Release/deployment

The developer must be able to review a deliverable, request changes and approve it.

When a revision is requested:

1. Record the feedback.
2. Identify the affected deliverable.
3. Assign it to the correct agent.
4. Preserve the previous revision.
5. Update affected tasks and dependencies.
6. Re-submit for review.

Do not interpret silence as approval.

Allow approval requirements to be configured per project and workflow stage.

---

# 16. Security and permissions

Natural-language instructions alone are not a security boundary.

Implement configurable policies for:

- Filesystem access
- Git operations
- Shell commands
- Network access
- Secrets
- Deployment
- Destructive operations

Use least privilege.

Important rules:

- Do not read or expose secrets unnecessarily.
- Do not commit credentials.
- Do not delete files without appropriate authorization.
- Do not force-push.
- Do not bypass protected branches.
- Do not deploy without approval.
- Do not overwrite user changes.
- Do not run destructive shell commands without authorization.

Where possible, use tool restrictions and execution sandboxing provided by the IDE/harness. If the harness cannot enforce a restriction, document that limitation instead of claiming the framework guarantees it.

---

# 17. Documentation management

Generate and maintain:

```text
README.md
docs/PROJECT_CONTEXT.md
docs/SRS.md
docs/FEATURES.md
docs/USER_FLOWS.md
docs/REQUIREMENT_TRACEABILITY.md

docs/architecture/
  SYSTEM_ARCHITECTURE.md
  DATABASE.md
  API_SPEC.md
  TECHNOLOGY_STACK.md

docs/design/
  DESIGN_DIRECTION.md
  DESIGN_SYSTEM.md
  SCREEN_SPECIFICATIONS.md

docs/decisions/
docs/revisions/
docs/reports/
```

Not every project needs every document. Generate only relevant documents.

The root README must describe the actual implementation, installation, configuration, development setup, Docker usage and testing.

Update documentation after meaningful milestones.

Do not claim a feature exists in documentation unless it has been implemented and verified.

---

# 18. IDE adapter architecture

Create a common adapter interface.

Each adapter must describe:

- Instruction discovery mechanism
- Skill discovery mechanism
- Agent definition format
- Subagent support
- Model selection limitations
- Command entry-point support
- Tool permission capabilities
- Known limitations

Implement the initial adapters:

1. Codex
2. Antigravity
3. VS Code agent environments

### Codex adapter

Generate the appropriate supported project configuration, including:

- Root AGENTS.md
- Project skills
- Custom agent definitions in the supported format
- Framework command interpretation skill
- Relevant policy and workflow references

Do not assume that the Codex VS Code extension exposes every capability of Codex CLI or that every configuration file is automatically loaded by every harness.

Verify the actual discovery behavior against current official Codex documentation.

### Antigravity adapter

Generate:

- AGENTS.md
- .agents/rules/
- .agents/skills/

Use rules for persistent project constraints and skills for repeatable workflows.

### VS Code adapter

Generate the supported custom agent and instruction configuration for the selected agent environment.

Do not generate unsupported or obsolete configuration formats.

### Compatibility principle

The core framework must remain usable if an IDE does not support:

- Native slash commands
- Multiple simultaneous agents
- Different models per agent
- Automatic agent delegation
- Native approval UI

Provide a sequential or conversational fallback.

Never falsely report that an unsupported capability is active.

---

# 19. Testing requirements

Build tests throughout development.

At minimum, implement tests for:

### Initialization

- Empty directory
- Existing Git repository
- Existing application repository
- Repeated initialization
- Existing conflicting files
- Unsupported project structure

### Commands

- Start
- Status
- Pause
- Resume
- Stop
- Continue
- Approve
- Revise

### Requirements

- Initial version creation
- File hashing
- Duplicate detection
- New version creation
- Requirement comparison
- Conflict detection
- Traceability

### State

- Database persistence
- Checkpoint creation
- Interrupted task recovery
- Idempotent execution
- Snapshot generation
- Event logging

### Integrations

- Git status and safe operations
- Docker availability detection
- IDE adapter generation
- Project structure validation

### Acceptance tests

Create temporary test projects and verify that:

1. The framework initializes a new project.
2. The generated structure is correct.
3. The requirements directory exists.
4. Initial requirements can be registered.
5. Workflow state persists.
6. Pause and resume work.
7. A second initialization does not destroy data.
8. Existing project files are preserved.
9. Codex adapter files are generated.
10. Antigravity adapter files are generated.

Use mocks for unavailable external services. Do not require real API keys for core framework tests.

---

# 20. Implementation strategy

Build in small, verified phases.

Do not attempt to implement the entire framework in one enormous code-generation step.

Use the following sequence:

### Phase 1 — Foundation

- Repository setup
- pyproject.toml
- Package structure
- CLI entry point
- Configuration system
- Logging
- Initial tests
- AGENTS.md

### Phase 2 — Project initialization

- `python -m agentic_framework init`
- Directory generation
- Existing project detection
- Safe file conflict handling
- Git detection
- Initialization report

### Phase 3 — Runtime and persistence

- SQLite schema
- Repositories
- Workflow state
- Task state
- Event log
- Checkpoints
- Snapshots

### Phase 4 — Command system

- Command registry
- CLI commands
- Chat command interpretation skill
- Status reporting
- Pause/resume/stop/continue

### Phase 5 — Requirements management

- Requirements inbox
- File inventory
- Extraction interfaces
- Immutable versions
- Comparison reports
- Traceability

### Phase 6 — Agent and workflow system

- Canonical agent definitions
- Agent contracts
- Workflow definitions
- Task dependencies
- Approval management
- Sequential fallback execution

### Phase 7 — IDE adapters

- Codex
- Antigravity
- VS Code agent environments
- Adapter validation

### Phase 8 — Engineering integrations

- Git integration
- Docker integration
- GitHub Actions templates
- README maintenance

### Phase 9 — Existing project and design workflows

- Existing project analyzer
- Figma integration boundary
- HTML prototype workflow
- Frontend/backend development workflow

### Phase 10 — Acceptance and release

- Full test suite
- Security review
- Package build
- Installation test
- Example project test
- User documentation
- Release checklist

At the end of each phase:

1. Run the relevant tests.
2. Fix failures.
3. Update documentation.
4. Record a checkpoint.
5. Summarize implemented functionality.
6. Identify remaining work.
7. Continue to the next phase unless a genuine blocker requires human input.

---

# 21. Development behavior for Codex

You are acting as the lead engineer implementing this framework.

Follow these rules:

1. Begin by inspecting the current repository.
2. Read and follow this entire implementation specification.
3. Create a concise implementation plan with phases and dependencies.
4. Save the plan in `docs/IMPLEMENTATION_PLAN.md`.
5. Create the repository foundation.
6. Implement Phase 1 immediately.
7. Run tests and validate the result.
8. Continue phase by phase.
9. Do not stop after writing the plan.
10. Do not ask me to manually create files or folders that your implementation can create.
11. Do not replace working code without a reason.
12. Do not add unnecessary abstractions.
13. Do not leave core functionality as TODOs or placeholder functions.
14. If a capability cannot be implemented because the IDE or provider does not expose it, create a clean adapter interface and document the limitation.
15. Ask me only when a decision genuinely requires my business input or approval.
16. Make reasonable technical decisions independently and document them.
17. Keep all project state and implementation decisions in repository files, not only in the chat.
18. Never claim a phase is complete without running its verification tests.
19. Keep the package installable throughout development.
20. Maintain a clear progress report in `docs/IMPLEMENTATION_PROGRESS.md`.

Use small commits when appropriate, but inspect the current Git state before committing. Do not commit unrelated changes.

---

# 22. Definition of done

The first usable release is complete only when all of the following are true:

- [ ] The framework can be installed locally.
- [ ] `python -m agentic_framework init` works.
- [ ] `adt init` works after installation.
- [ ] Initialization supports new and existing projects.
- [ ] Initialization is safe and repeatable.
- [ ] Requirements folders are automatically generated.
- [ ] Requirements can be stored in immutable versions.
- [ ] Requirement changes can be compared.
- [ ] Workflow state persists in SQLite.
- [ ] Task state and checkpoints persist.
- [ ] CLI commands work.
- [ ] IDE chat commands have a working interpretation skill.
- [ ] Codex adapter is generated and validated.
- [ ] Antigravity adapter is generated and validated.
- [ ] Canonical agents and skills exist.
- [ ] Sequential agent execution works without native subagents.
- [ ] Human approval and revision workflows work.
- [ ] Existing project analysis works.
- [ ] Git safety checks are implemented.
- [ ] Docker and CI/CD templates are available.
- [ ] Tests pass.
- [ ] Documentation is accurate.
- [ ] A sample project can be initialized and used.

Do not mark the project complete simply because all directories and configuration files exist. Demonstrate the core workflows through automated tests and a sample project.

---

# Final instruction

Start implementing the framework now.

First inspect the repository, create the implementation plan and begin Phase 1.

Work incrementally until the first usable release is implemented, tested and documented.

Prioritize a reliable, genuinely usable framework over an impressive but incomplete architecture.

Keep the framework portable and make sure that a developer can eventually install it into a project and start working with it through their IDE agent without manually configuring the framework.