"""Canonical workflow, agent, policy, and IDE adapter assets."""

from __future__ import annotations

from importlib.resources import files

import yaml

from agentic_framework.core.stages import CONTRACTS, contract_document

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

Read the root `AGENTS.md` and `.agentic/config.yaml` before framework work. Workspace skills
register `/start`, `/status`, `/pause`, `/continue`, `/stop`, `/review`, `/approve`, `/revise`,
`/requirements`, `/tasks`, `/adf-resume`, and `/adf`. For `/start`, `/continue`, and `/adf-resume`,
read the shared command skill and
`.agentic/execution-contracts.yaml`; do not merely run a lifecycle command and report its output.
The IDE agent performs reasoning and artifact creation while `adt` persists execution, artifacts,
validation, approvals, and recovery. Never bypass approval gates or overwrite unrelated changes.
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
    return _yaml({"schema_version": 2, "name": "default", "stages": stages})


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


def generated_project_files() -> dict[str, str]:
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
        ".agents/rules/adf.md": _RULES,
        ".agents/skills/agentic-commands/SKILL.md": skill,
        ".codex/agents/README.md": _CODEX_NOTE,
    }
    generated.update(
        {
            f".agents/skills/{name}/SKILL.md": _command_skill(name, description)
            for name, description in _ANTIGRAVITY_COMMANDS.items()
        }
    )
    generated[".agents/skills/adf-resume/SKILL.md"] = _resume_skill()
    generated[".agents/skills/adf/SKILL.md"] = _adf_skill()
    return generated
