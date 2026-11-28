"""Google Antigravity provider adapter."""

from __future__ import annotations

from typing import Any

from agentic_framework.providers.base import (
    ProviderCapabilities,
    ProviderExecutionResult,
    normalize_execution_payload,
)

_RULES = """# Agentic Development Framework rules

Read the root `AGENTS.md` and `.agentic/config.yaml` before framework work. Workspace skills
register `/start`, `/status`, `/pause`, `/continue`, `/stop`, `/review`, `/approve`, `/revise`,
`/requirements`, `/tasks`, `/analyze`, `/plan`, `/test`, `/docs`, `/agents`, `/adf-resume`, and
`/adf`. For `/start`, `/continue`, and `/adf-resume`, read the shared command skill and
`.agentic/execution-contracts.yaml`; do not merely run a lifecycle command and report its output.
The IDE agent performs reasoning and artifact creation while `adt` persists execution, artifacts,
validation, approvals, and recovery. Never bypass approval gates or overwrite unrelated changes.

**Specialist instructions**: Read `.agentic/agents/<agent_id>/AGENT.md` for the stage's assigned
specialist before executing stage work.

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


class AntigravityProvider:
    """Adapter for Google Antigravity."""

    provider_id = "antigravity"
    display_name = "Google Antigravity"
    capabilities = ProviderCapabilities(
        supports_skills=True,
        supports_rules=True,
        supports_slash_commands=True,
        supports_subagents=True,
        supports_command_execution=True,
    )

    def render_files(self, commands: dict[str, str]) -> dict[str, str]:
        files: dict[str, str] = {".agents/rules/adf.md": _RULES}
        for name, description in commands.items():
            files[f".agents/skills/{name}/SKILL.md"] = _command_skill(name, description)
        files[".agents/skills/adf-resume/SKILL.md"] = _resume_skill()
        files[".agents/skills/adf/SKILL.md"] = _adf_skill()
        return files

    def normalize_result(self, raw: dict[str, Any]) -> ProviderExecutionResult:
        return normalize_execution_payload(self.provider_id, raw)
