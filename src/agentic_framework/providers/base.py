"""Base contracts and normalized execution models for AI provider adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    """Normalized capability flags for an AI coding environment."""

    supports_skills: bool = False
    supports_rules: bool = False
    supports_slash_commands: bool = False
    supports_subagents: bool = False
    supports_command_execution: bool = True


@dataclass(frozen=True, slots=True)
class ProviderExecutionResult:
    """Normalized execution report returned by any provider adapter."""

    provider_id: str
    status: str  # "completed" | "blocked" | "failed"
    summary: str = ""
    modified_files: tuple[str, ...] = ()
    blocker: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderAdapter(Protocol):
    """Interface every AI provider adapter must implement."""

    provider_id: str
    display_name: str
    capabilities: ProviderCapabilities

    def render_files(self, commands: dict[str, str]) -> dict[str, str]:
        """Return project-relative provider configuration and instruction files."""

    def normalize_result(self, raw: dict[str, Any]) -> ProviderExecutionResult:
        """Normalize provider-specific execution output into a canonical result."""


def normalize_execution_payload(
    provider_id: str,
    raw: dict[str, Any],
) -> ProviderExecutionResult:
    """Normalize heterogeneous provider payloads into a ProviderExecutionResult."""

    raw_status = str(raw.get("status", "failed")).strip().lower()
    if raw_status in {"ok", "success", "succeeded", "done", "completed"}:
        status = "completed"
    elif raw_status in {"blocked", "waiting", "awaiting_input"}:
        status = "blocked"
    else:
        status = "failed"

    files_raw = raw.get("modified_files") or raw.get("files") or ()
    modified_files = tuple(str(item) for item in files_raw if str(item).strip())
    summary = str(raw.get("summary") or raw.get("message") or "").strip()
    blocker = str(raw["blocker"]).strip() if raw.get("blocker") else None
    error = str(raw["error"]).strip() if raw.get("error") else None
    if status == "blocked" and not blocker:
        blocker = summary or "Provider reported a blocker without details."
    if status == "failed" and not error:
        error = summary or "Provider execution failed."

    return ProviderExecutionResult(
        provider_id=provider_id,
        status=status,
        summary=summary,
        modified_files=modified_files,
        blocker=blocker,
        error=error,
        metadata={
            k: v
            for k, v in raw.items()
            if k
            not in {"status", "summary", "message", "modified_files", "files", "blocker", "error"}
        },
    )
