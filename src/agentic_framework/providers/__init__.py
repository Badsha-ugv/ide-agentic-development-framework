"""Provider adapter registry for multi-environment AI execution."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from agentic_framework.core.config import IdeKind
from agentic_framework.providers.antigravity import AntigravityProvider
from agentic_framework.providers.base import (
    ProviderAdapter,
    ProviderCapabilities,
    ProviderExecutionResult,
    normalize_execution_payload,
)
from agentic_framework.providers.claude import ClaudeCodeProvider
from agentic_framework.providers.codex import CodexProvider
from agentic_framework.providers.vscode import VSCodeProvider


class CustomProvider:
    """Fallback adapter for custom/compatible AI coding environments."""

    provider_id = "custom"
    display_name = "Custom Compatible Agent"
    capabilities = ProviderCapabilities()

    def render_files(self, commands: dict[str, str]) -> dict[str, str]:
        return {}

    def normalize_result(self, raw: dict[str, Any]) -> ProviderExecutionResult:
        return normalize_execution_payload(self.provider_id, raw)


_PROVIDERS: dict[IdeKind, ProviderAdapter] = {
    IdeKind.CODEX: CodexProvider(),
    IdeKind.CLAUDE: ClaudeCodeProvider(),
    IdeKind.ANTIGRAVITY: AntigravityProvider(),
    IdeKind.VSCODE: VSCodeProvider(),
    IdeKind.CUSTOM: CustomProvider(),
}


def get_provider(kind: IdeKind) -> ProviderAdapter:
    """Return the registered provider adapter for an IdeKind."""

    return _PROVIDERS[kind]


def list_providers() -> tuple[ProviderAdapter, ...]:
    """Return all registered provider adapters in deterministic order."""

    return tuple(_PROVIDERS.values())


def render_provider_files(
    enabled: Sequence[IdeKind],
    commands: dict[str, str],
) -> dict[str, str]:
    """Render provider files for enabled environments plus shared Codex/Antigravity baseline."""

    # Preserve shared Codex + Antigravity baseline for backward compatibility.
    selected: list[IdeKind] = [IdeKind.CODEX, IdeKind.ANTIGRAVITY]
    for kind in enabled:
        if kind not in selected:
            selected.append(kind)

    files: dict[str, str] = {}
    for kind in selected:
        files.update(get_provider(kind).render_files(commands))
    return files


__all__ = [
    "AntigravityProvider",
    "ClaudeCodeProvider",
    "CodexProvider",
    "CustomProvider",
    "ProviderAdapter",
    "ProviderCapabilities",
    "ProviderExecutionResult",
    "VSCodeProvider",
    "get_provider",
    "list_providers",
    "render_provider_files",
]
