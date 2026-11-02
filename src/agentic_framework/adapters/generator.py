"""Canonical workflow, agent, policy, and IDE adapter assets."""

from __future__ import annotations

from importlib.resources import files

import yaml

STAGES = (
    "project_initialization",
    "project_discovery",
    "requirements_ingestion",
    "requirements_analysis",
    "srs_and_project_documentation",
    "requirements_review",
    "system_architecture",
    "architecture_review",
    "ui_ux_design",
    "design_review",
    "development_planning",
    "implementation",
    "integration",
    "qa_and_testing",
    "code_and_security_review",
    "docker_and_ci_cd_validation",
    "final_documentation",
    "release_review",
    "completed",
)

APPROVAL_STAGES = {
    "requirements_review",
    "architecture_review",
    "design_review",
    "release_review",
}

_AGENTS = (
    ("main_orchestrator", "Main Orchestrator"),
    ("requirements_analyst", "Requirements Analyst"),
    ("software_architect", "Software Architect"),
    ("ui_ux_designer", "UI/UX Designer"),
    ("frontend_developer", "Frontend Developer"),
    ("backend_developer", "Backend Developer"),
    ("integration_engineer", "Integration Engineer"),
    ("qa_engineer", "QA Engineer"),
    ("code_reviewer", "Code Reviewer"),
    ("security_reviewer", "Security Reviewer"),
    ("devops_engineer", "DevOps Engineer"),
)

_RULES = """# Agentic Development Framework rules

Read the root `AGENTS.md` and `.agentic/config.yaml` before framework work. Interpret `/start`,
`/status`, `/pause`, `/resume`, `/continue`, `/stop`, `/review`, `/approve`, `/revise`,
`/requirements`, and `/tasks` as ADF workflow commands. Use `adt <command>` to persist state.
Never bypass approval gates or overwrite unrelated project changes.
"""

_CODEX_NOTE = """# Codex adapter

Codex discovers the root `AGENTS.md` and `.agents/skills/agentic-commands/SKILL.md`. Canonical
specialist roles live in `.agentic/agent-registry.yaml`. This directory is informational because
ADF does not assume an undocumented filesystem format for Codex custom agents.
"""


def _yaml(value: object) -> str:
    return yaml.safe_dump(value, sort_keys=False)


def _workflow() -> str:
    stages = []
    for index, stage_id in enumerate(STAGES):
        stages.append(
            {
                "id": stage_id,
                "purpose": stage_id.replace("_", " ").title(),
                "required_inputs": [],
                "agent": "main_orchestrator",
                "expected_outputs": [],
                "dependencies": [STAGES[index - 1]] if index else [],
                "validation_rules": ["required checks pass"],
                "approval_required": stage_id in APPROVAL_STAGES,
                "failure_behavior": "stop and preserve recoverable state",
                "retry_policy": {"max_attempts": 3},
                "checkpoint_policy": "on_completion",
            }
        )
    return _yaml({"schema_version": 1, "name": "default", "stages": stages})


def _registry() -> str:
    agents = []
    for agent_id, name in _AGENTS:
        agents.append(
            {
                "id": agent_id,
                "name": name,
                "role": name,
                "responsibilities": [f"Perform {name.lower()} work within approved scope"],
                "scope": "assigned tasks only",
                "required_inputs": [],
                "expected_outputs": ["standardized agent result"],
                "allowed_tools": ["repository read/write tools", "project test commands"],
                "restricted_operations": ["secrets", "force push", "unapproved deployment"],
                "verification_requirements": ["run relevant checks"],
                "handoff_format": "agent result contract",
                "failure_and_escalation": "record blocker and escalate to orchestrator",
            }
        )
    return _yaml({"schema_version": 1, "agents": agents})


def generated_project_files() -> dict[str, str]:
    """Return deterministic canonical assets for project initialization."""

    skill = (
        files("agentic_framework")
        .joinpath("templates/skills/agentic-commands/SKILL.md")
        .read_text(encoding="utf-8")
    )
    return {
        ".agentic/workflow.yaml": _workflow(),
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
        ".agents/rules/adf.md": _RULES,
        ".agents/skills/agentic-commands/SKILL.md": skill,
        ".codex/agents/README.md": _CODEX_NOTE,
    }
