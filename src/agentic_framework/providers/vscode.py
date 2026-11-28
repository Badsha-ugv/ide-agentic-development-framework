"""VS Code / GitHub Copilot AI environment provider adapter."""

from __future__ import annotations

from typing import Any

from agentic_framework.providers.base import (
    ProviderCapabilities,
    ProviderExecutionResult,
    normalize_execution_payload,
)

_COPILOT_INSTRUCTIONS = """# Agentic Development Framework (VS Code)

This repository uses the Agentic Development Framework (ADF).

- Read `.agentic/config.yaml`, `.agentic/execution-contracts.yaml`, and
  `.agentic/agent-registry.yaml` before making changes.
- Run `adt status` to inspect the active stage, complexity route, and blockers.
- Follow the assigned specialist guidance in `.agentic/agents/<agent_id>/AGENT.md`.
- Register all stage deliverables with `adt artifact register <path>` and validate via
  `adt stage complete`. Never bypass `adt approve` gates.
- Preserve existing architecture, conventions, and unrelated user changes.
"""

_ADF_INSTRUCTIONS = """---
applyTo: "**"
---

# ADF Stage Discipline

Always check `adt status` before editing. Only work within the active stage contract in
`.agentic/execution-contracts.yaml`, and register changed deliverables with `adt artifact register`.
"""


class VSCodeProvider:
    """Adapter for VS Code-based AI coding environments."""

    provider_id = "vscode"
    display_name = "VS Code AI"
    capabilities = ProviderCapabilities(
        supports_skills=False,
        supports_rules=True,
        supports_slash_commands=False,
        supports_subagents=False,
        supports_command_execution=True,
    )

    def render_files(self, commands: dict[str, str]) -> dict[str, str]:
        return {
            ".github/copilot-instructions.md": _COPILOT_INSTRUCTIONS,
            ".github/instructions/adf.instructions.md": _ADF_INSTRUCTIONS,
        }

    def normalize_result(self, raw: dict[str, Any]) -> ProviderExecutionResult:
        return normalize_execution_payload(self.provider_id, raw)
