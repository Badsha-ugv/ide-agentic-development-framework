"""Canonical workflow, agent, policy, and IDE adapter assets."""

from __future__ import annotations

from collections.abc import Sequence
from importlib.resources import files

import yaml

from agentic_framework.core.config import IdeKind
from agentic_framework.core.stages import CONTRACTS, contract_document
from agentic_framework.providers import render_provider_files

_AGENTS = (
    ("main_orchestrator", "Main Orchestrator"),
    ("requirements_analyst", "Requirements Analyst"),
    ("software_architect", "Software Architect"),
    ("ui_ux_designer", "UI/UX Designer"),
    ("frontend_developer", "Frontend Developer"),
    ("backend_developer", "Backend Developer"),
    ("mobile_developer", "Mobile Developer"),
    ("integration_engineer", "Integration Engineer"),
    ("qa_engineer", "QA Engineer"),
    ("code_reviewer", "Code Reviewer"),
    ("security_reviewer", "Security Reviewer"),
    ("devops_engineer", "DevOps Engineer"),
    ("documentation_engineer", "Documentation Engineer"),
)

_RULES = """# Agentic Development Framework rules

Read the root `AGENTS.md` and `.agentic/config.yaml` before framework work. Workspace skills
register `/start`, `/status`, `/pause`, `/continue`, `/stop`, `/review`, `/approve`, `/revise`,
`/requirements`, `/tasks`, `/adf-resume`, and `/adf`. For `/start`, `/continue`, and `/adf-resume`,
read the shared command skill and
`.agentic/execution-contracts.yaml`; do not merely run a lifecycle command and report its output.
The IDE agent performs reasoning and artifact creation while `adt` persists execution, artifacts,
validation, approvals, and recovery. Never bypass approval gates or overwrite unrelated changes.

**Existing projects**: Read `docs/discovery/existing-project-analysis.md` and
`.agentic/reports/existing-project-analysis.md` before proposing any work. Adapt the contract
to the actual architecture; never impose a guessed folder layout. Detect and follow the real
tech stack, conventions, Git state, and active ADF artifacts; report discovered defects and
conflicts instead of silently ignoring them.

**Frontend design quality is mandatory**: Before writing any page code, define a complete design
system (color palette, typography, spacing, motion, breakpoints). Research conventional websites
and applications similar to the project idea to understand industry design patterns. Build the
complete production frontend with no disposable prototypes. Supplied references govern presentation
and must have no unapproved visual deviation. Require explicit frontend approval before backend
planning or implementation.

**Workflow order**: documents → frontend implementation → frontend approval → backend
implementation → frontend/backend integration → database validation → security testing →
code review → Docker/CI/CD → final docs → release. Build the backend separately, then connect it
through the frontend adapter boundary during the API integration stage.

A custom `/adf` request may refine current-stage work but cannot skip this order.
"""

_CODEX_NOTE = """# Codex adapter

Codex discovers the root `AGENTS.md` and `.agents/skills/agentic-commands/SKILL.md`. Canonical
specialist roles live in `.agentic/agent-registry.yaml`. This directory is informational because
ADF does not assume an undocumented filesystem format for Codex custom agents.
"""

_ANTIGRAVITY_COMMANDS = {
    "start": "Begin the ADF workflow and execute the current eligible stage.",
    "continue": "Execute or resume the current ADF stage without skipping required work.",
    "status": "Inspect persisted ADF stage, execution, approval, artifact, and blocker state.",
    "pause": "Pause the active ADF workflow and create a recovery checkpoint.",
    "stop": "Stop the ADF workflow without losing its persisted progress.",
    "review": "Show ADF deliverables waiting for human review.",
    "approve": "Approve the current ADF review gate using the supplied or current stage.",
    "revise": "Record supplied revision feedback for the current ADF review gate.",
    "help": "Explain the available ADF commands and stage execution model.",
    "tasks": "Show persisted ADF workflow tasks.",
    "requirements": "Show the latest immutable ADF requirements version.",
    "analyze": "Inspect the existing project structure, stack, and domain completion.",
    "plan": "Inspect the dynamic workflow route and complexity classification.",
    "test": "Inspect verification criteria and run stage-relevant checks.",
    "docs": "Inspect or update documentation deliverables for the current stage.",
    "agents": "List specialized ADF agents and their AGENT.md instructions.",
    "design": "Modify or iterate on the application design while preserving functionality.",
    "preferences": "View, update, or reset saved user and project design preferences.",
}


def _yaml(value: object) -> str:
    return yaml.safe_dump(value, sort_keys=False)


def _workflow() -> str:
    stages = []
    for contract in CONTRACTS:
        stages.append(
            {
                "id": contract.id,
                "name": contract.name,
                "purpose": contract.objective,
                "required_inputs": list(contract.required_inputs),
                "agent": contract.agent,
                "expected_outputs": list(contract.expected_outputs),
                "dependencies": list(contract.prerequisites),
                "validation_rules": list(contract.validation_criteria),
                "approval_required": contract.approval_required,
                "failure_behavior": contract.failure_behavior,
                "retry_policy": {"max_attempts": contract.max_attempts},
                "checkpoint_policy": "on_completion",
            }
        )
    return _yaml({"schema_version": 5, "name": "default", "stages": stages})


def _registry() -> str:
    agents = []
    for agent_id, name in _AGENTS:
        responsibilities = [f"Perform {name.lower()} work within approved scope"]
        required_inputs: list[str] = []
        expected_outputs = ["standardized agent result"]
        verification = ["run relevant checks"]
        if agent_id == "frontend_developer":
            responsibilities = [
                "Research comparable production websites and apps to inform design decisions",
                "Define a complete design system (colors, typography, spacing, motion) first",
                "Verify the frontend stack and environment before implementation",
                "Build the complete production frontend before any backend implementation",
                "Match approved references exactly; create a modern, distinctive interface "
                "when no external reference exists",
                "Deliver accessible, responsive, meaningful interactions with no generic "
                "placeholder styling",
            ]
            required_inputs = [
                "approved requirements, architecture, and visual references",
                "docs/discovery/existing-project-analysis.md if mode=existing",
            ]
            expected_outputs = [
                "docs/frontend/design-research.md",
                "docs/frontend/design-system.md with concrete token values",
                "production frontend source with design system applied",
                "browser verification evidence at desktop, tablet, and mobile",
            ]
            verification = [
                "prove environment setup and production build before completion",
                "confirm design system tokens are applied consistently across all pages",
                "compare actual frontend rendering with every approved reference",
                "test pages, states, controls, accessibility, console, and responsive layouts",
                "confirm no hardcoded one-off color, font, or spacing values exist",
            ]
        elif agent_id == "backend_developer":
            responsibilities = [
                "Implement backend services from approved API and architecture contracts",
                "Preserve the approved frontend and its adapter boundary",
                "Implement persistence, validation, security, migrations, and failure behavior",
                "Write tests covering all API endpoints, business rules, and error paths",
            ]
            required_inputs = ["approved backend plan, architecture, and frontend adapter needs"]
            expected_outputs = ["tested backend implementation and traceability manifest"]
            verification = ["run backend unit, integration, migration, and security checks"]
        elif agent_id == "integration_engineer":
            responsibilities = [
                "Replace frontend mocks through the documented adapter boundary",
                "Verify API, authentication, validation, and failure-state behavior end to end",
                "Prevent silent visual drift during frontend/backend integration",
                "Confirm all loading, empty, error, and success states render with real data",
            ]
            required_inputs = ["approved frontend, verified backend, and API integration plan"]
            expected_outputs = ["API integration report with reproducible evidence"]
            verification = ["run backend, frontend, API, and browser integration checks"]
        elif agent_id == "security_reviewer":
            responsibilities = [
                "Test authentication flows, authorization rules, and session management",
                "Test all inputs for injection, XSS, CSRF, and mass assignment vulnerabilities",
                "Audit secrets management, dependency versions, and HTTP security headers",
                "Document every finding with severity, reproduction steps, and remediation",
                "Re-test critical and high findings after remediation",
            ]
            required_inputs = [
                "docs/architecture/security-architecture.md",
                "integrated application source and running environment",
            ]
            expected_outputs = [
                "docs/reports/security-testing.md",
                "docs/reports/security-remediation.md",
            ]
            verification = [
                "every authentication endpoint is tested",
                "injection testing covers SQL, XSS, and CSRF at minimum",
                "dependency audit is complete with CVE status",
                "no unresolved critical or high findings remain",
            ]
        elif agent_id == "qa_engineer":
            responsibilities = [
                "Execute the approved test plan against the integrated application",
                "Map test results to requirement IDs",
                "Validate the database schema, migrations, indexes, and data integrity",
                "Document failures with reproduction steps",
            ]
            required_inputs = [
                "docs/planning/backend-testing-plan.md",
                "docs/requirements/acceptance-criteria.md",
                "integrated application and database",
            ]
            expected_outputs = [
                "docs/reports/qa-and-testing.md",
                "docs/reports/database-validation.md",
            ]
            verification = [
                "all acceptance criteria are tested and mapped to requirements",
                "migration forward and rollback tests pass",
                "no SQL injection vulnerabilities present",
            ]
        agents.append(
            {
                "id": agent_id,
                "name": name,
                "role": name,
                "instructions_file": f".agentic/agents/{agent_id}/AGENT.md",
                "responsibilities": responsibilities,
                "scope": "assigned tasks only",
                "required_inputs": required_inputs,
                "expected_outputs": expected_outputs,
                "allowed_tools": ["repository read/write tools", "project test commands"],
                "restricted_operations": ["secrets", "force push", "unapproved deployment"],
                "verification_requirements": verification,
                "handoff_format": "agent result contract",
                "failure_and_escalation": "record blocker and escalate to orchestrator",
            }
        )
    return _yaml({"schema_version": 1, "agents": agents})


def _command_skill(name: str, description: str) -> str:
    if name in {"start", "continue"}:
        action = f"/{name}"
        body = f"""Read `.agents/skills/agentic-commands/SKILL.md` completely and execute its
stage loop for `{action}`. Always begin with `adt status`. For `/continue`, if the workflow is
`not_started`, run `adt start` instead of failing; otherwise run `adt continue`. Do not stop after
printing CLI output: the IDE agent must load the current contract, perform the work, create and
register deliverables, validate them, and complete the stage or persist a blocker. Never skip an
approval gate. The `adt continue` operation prepares the current stage and does not advance it.
"""
    elif name == "approve":
        body = """Run `adt status`, identify the current stage, and require explicit user approval.
Use the stage argument supplied with this invocation, or the current stage when none is supplied.
Run `adt approve <stage>`, then report the new durable state. Never infer approval from file
existence or from a previous conversation.
"""
    elif name == "revise":
        body = """Run `adt status` and use the current review stage. Require non-empty feedback from
this invocation; ask the user when it is missing. Run `adt revise <stage> <feedback>`, then read
`.agents/skills/agentic-commands/SKILL.md` and execute the revision loop against the same stage.
"""
    else:
        body = f"""Run `adt status` first so the response is grounded in the persisted project.
Then run `adt {name}` and explain the result in the context of the current stage. Do not change or
advance the stage unless the command contract explicitly permits it.
"""
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"# ADF /{name}\n\n"
        f"{body}"
    )


def _resume_skill() -> str:
    return (
        "---\n"
        "name: adf-resume\n"
        "description: Resume an ADF checkpoint and continue its restored stage; use this instead "
        "of Antigravity's built-in /resume conversation command.\n"
        "---\n"
        """

# ADF resume

Run `adt status`, then `adt resume`, then `adt continue`. Read
`.agents/skills/agentic-commands/SKILL.md` completely and execute the restored stage contract.
Do not stop after reporting CLI state, and do not advance until required artifacts validate.
"""
    )


def _adf_skill() -> str:
    return (
        "---\n"
        "name: adf\n"
        "description: Execute an ADF lifecycle action or custom stage-scoped request using "
        "persisted project state and the current execution contract.\n"
        "---\n"
        """

# ADF state-aware command

Interpret the text following `/adf` as the requested action.

1. Run `adt status` before doing work.
2. For a lifecycle action, follow `.agents/skills/agentic-commands/SKILL.md`. Use `adt start` when
   the workflow is `not_started`. Use `adt continue` only when it is active. For ADF recovery use
   `adt resume` followed by `adt continue`.
3. For any custom request, prepare the current stage, read its entry from
   `.agentic/execution-contracts.yaml`, and run `adt stage task "<concise request>"` so the active
   work survives a new chat or restart.
4. Execute the custom request only when it is compatible with the current stage, approved inputs,
   and safety policy. Do not let a custom request skip prerequisites or approval gates.
5. Register changed stage deliverables. Run `adt stage complete` only if the entire stage contract
   is satisfied; otherwise report the persisted current task and remaining work.
6. Persist failures or missing decisions using `adt stage fail` or `adt stage fail --blocked`.

The terminal `adt` process is not an AI provider. This Antigravity skill is what causes the IDE
agent to reason and act; `adt` supplies durable state and validation.
"""
    )


def generated_project_files(
    enabled_ides: Sequence[IdeKind] = (IdeKind.CODEX, IdeKind.ANTIGRAVITY),
) -> dict[str, str]:
    """Return deterministic canonical assets for project initialization."""

    skill = (
        files("agentic_framework")
        .joinpath("templates/skills/agentic-commands/SKILL.md")
        .read_text(encoding="utf-8")
    )
    generated = {
        ".agentic/workflow.yaml": _workflow(),
        ".agentic/execution-contracts.yaml": _yaml(contract_document()),
        ".agentic/policies.yaml": _yaml(
            {
                "schema_version": 1,
                "filesystem": "project_only",
                "destructive_operations": "require_explicit_approval",
                "network": "deny_by_default",
                "deployment": "require_approval",
                "secrets": "never_expose_or_commit",
            }
        ),
        ".agentic/agent-registry.yaml": _registry(),
        ".agents/skills/agentic-commands/SKILL.md": skill,
    }
    generated.update(render_provider_files(enabled_ides, _ANTIGRAVITY_COMMANDS))
    templates_root = files("agentic_framework").joinpath("templates")
    for agent_id, _ in _AGENTS:
        agent_doc = templates_root.joinpath(f"agents/{agent_id}/AGENT.md").read_text(
            encoding="utf-8"
        )
        generated[f".agentic/agents/{agent_id}/AGENT.md"] = agent_doc
    generated[".agentic/templates/SIMPLE_FEATURE_DOC.md"] = templates_root.joinpath(
        "docs/SIMPLE_FEATURE_DOC.md"
    ).read_text(encoding="utf-8")
    generated[".agentic/templates/MOBILE_ARCHITECTURE.md"] = templates_root.joinpath(
        "docs/MOBILE_ARCHITECTURE.md"
    ).read_text(encoding="utf-8")
    return generated
