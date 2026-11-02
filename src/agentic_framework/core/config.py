"""Validated YAML configuration for the framework."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path, PurePath
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from agentic_framework.exceptions import ConfigurationError


class StrictModel(BaseModel):
    """Base model that rejects misspelled and unsupported configuration keys."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ProjectMode(StrEnum):
    """How project discovery should treat the target directory."""

    AUTO = "auto"
    NEW = "new"
    EXISTING = "existing"


class IdeKind(StrEnum):
    """IDE harnesses known to the initial product specification."""

    CODEX = "codex"
    ANTIGRAVITY = "antigravity"
    VSCODE = "vscode"


class LogLevel(StrEnum):
    """Supported Python logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProjectConfig(StrictModel):
    """Project identification and discovery preferences."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    mode: ProjectMode = ProjectMode.AUTO

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("project name cannot be blank")
        return normalized


class RuntimeConfig(StrictModel):
    """Local runtime storage and diagnostic preferences."""

    directory: Path = Path(".agentic")
    log_level: LogLevel = LogLevel.INFO

    @field_validator("directory")
    @classmethod
    def require_safe_relative_path(cls, value: Path) -> Path:
        path = PurePath(value)
        if path.is_absolute():
            raise ValueError("runtime directory must be project-relative")
        if not path.parts or any(part == ".." for part in path.parts):
            raise ValueError("runtime directory cannot traverse outside the project")
        return Path(path)


class IdeConfig(StrictModel):
    """IDE adapters requested for a project."""

    enabled: list[IdeKind] = Field(default_factory=lambda: [IdeKind.CODEX])

    @field_validator("enabled")
    @classmethod
    def require_unique_adapters(cls, value: list[IdeKind]) -> list[IdeKind]:
        if len(value) != len(set(value)):
            raise ValueError("IDE adapters must not be duplicated")
        return value


class PolicyConfig(StrictModel):
    """Conservative capability defaults for future execution phases."""

    allow_network: bool = False
    allow_destructive_operations: bool = False


class FrameworkConfig(StrictModel):
    """Root configuration document."""

    schema_version: int = Field(default=1, ge=1, le=1)
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    ide: IdeConfig = Field(default_factory=IdeConfig)
    policies: PolicyConfig = Field(default_factory=PolicyConfig)


def parse_config(data: Any) -> FrameworkConfig:
    """Validate decoded configuration data and present failures consistently."""

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ConfigurationError("configuration root must be a YAML mapping")
    try:
        return FrameworkConfig.model_validate(data)
    except ValidationError as exc:
        raise ConfigurationError(f"configuration validation failed:\n{exc}") from exc


def load_config(path: Path) -> FrameworkConfig:
    """Read and validate a UTF-8 YAML configuration file."""

    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigurationError(f"configuration file does not exist: {path}") from exc
    except OSError as exc:
        raise ConfigurationError(f"cannot read configuration file {path}: {exc}") from exc

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"invalid YAML in {path}: {exc}") from exc
    return parse_config(data)


def dump_config(config: FrameworkConfig) -> str:
    """Serialize a normalized configuration document as stable YAML."""

    data = config.model_dump(mode="json")
    return yaml.safe_dump(data, sort_keys=False)

