"""Anthropic Claude / Claude Code provider adapter."""

from __future__ import annotations

from typing import Any

from agentic_framework.providers.base import (
    ProviderCapabilities,
    ProviderExecutionResult,
    normalize_execution_payload,
)

_CLAUDE_MD = """# Claude Code — Agentic Development Framework (ADF)

This project is managed by the Agentic Development Framework (ADF).

## Core Protocol
1. Read `.agentic/config.yaml`, `.agentic/execution-contracts.yaml`, and
   `.agentic/agent-registry.yaml` before starting work.
2. Run `adt status` to inspect the current stage, complexity route, and blockers.
3. Read the assigned specialist instructions in `.agentic/agents/<agent_id>/AGENT.md`.
4. For existing projects, inspect `docs/discovery/existing-project-analysis.md` and the
   real codebase before proposing or modifying any code.
5. Register every created or updated deliverable with `adt artifact register <path>`.
6. Validate and advance with `adt stage complete`. Never skip approval gates (`adt approve`).

## Slash Commands
Claude Code slash commands for ADF are installed in `.claude/commands/`.
Use `/start`, `/continue`, `/status`, `/plan`, `/analyze`, `/review`, `/approve`, and `/revise`.
"""


def _claude_command(name: str, description: str) -> str:
    if name in {"start", "continue"}:
        body = (
            f"Run `adt status` and `adt {name}` (for `/continue`, run `adt start` if "
            "`not_started`). Read `.agentic/execution-contracts.yaml` and the assigned "
            "specialist instructions in `.agentic/agents/<agent>/AGENT.md`. Perform the "
            "stage work, register every output with `adt artifact register <path>`, and run "
            "`adt stage complete`."
        )
    elif name == "approve":
        body = (
            "Run `adt status` to verify the stage awaiting approval, confirm explicit user "
            "authorization, then run `adt approve <stage>`."
        )
    elif name == "revise":
        body = (
            "Run `adt status`, collect explicit revision feedback from the user, run "
            "`adt revise <stage> \"<feedback>\"`, and update the stage deliverables."
        )
    else:
        body = (
            f"Run `adt status` and `adt {name}`, then summarize the persisted state and "
            "next action for the user."
        )
    return f"# /{name}\n\n{description}\n\n{body}\n"


class ClaudeCodeProvider:
    """Adapter for Anthropic Claude Code."""

    provider_id = "claude"
    display_name = "Anthropic Claude Code"
    capabilities = ProviderCapabilities(
        supports_skills=True,
        supports_rules=True,
        supports_slash_commands=True,
        supports_subagents=True,
        supports_command_execution=True,
    )

    def render_files(self, commands: dict[str, str]) -> dict[str, str]:
        files = {"CLAUDE.md": _CLAUDE_MD}
        for name, description in commands.items():
            files[f".claude/commands/{name}.md"] = _claude_command(name, description)
        return files

    def normalize_result(self, raw: dict[str, Any]) -> ProviderExecutionResult:
        return normalize_execution_payload(self.provider_id, raw)
