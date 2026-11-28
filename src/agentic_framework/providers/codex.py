"""OpenAI Codex provider adapter."""

from __future__ import annotations

from typing import Any

from agentic_framework.providers.base import (
    ProviderCapabilities,
    ProviderExecutionResult,
    normalize_execution_payload,
)

_CODEX_NOTE = """# Codex adapter

Codex discovers the root `AGENTS.md` and `.agents/skills/agentic-commands/SKILL.md`. Canonical
specialist roles live in `.agentic/agent-registry.yaml` and `.agentic/agents/*/AGENT.md`.
This directory is informational because ADF does not assume an undocumented filesystem format
for Codex custom agents.
"""


class CodexProvider:
    """Adapter for OpenAI Codex."""

    provider_id = "codex"
    display_name = "OpenAI Codex"
    capabilities = ProviderCapabilities(
        supports_skills=True,
        supports_rules=False,
        supports_slash_commands=True,
        supports_subagents=False,
        supports_command_execution=True,
    )

    def render_files(self, commands: dict[str, str]) -> dict[str, str]:
        return {".codex/agents/README.md": _CODEX_NOTE}

    def normalize_result(self, raw: dict[str, Any]) -> ProviderExecutionResult:
        return normalize_execution_payload(self.provider_id, raw)
