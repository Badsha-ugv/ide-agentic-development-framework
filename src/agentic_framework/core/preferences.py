"""Persistent Design Preference Engine (global, project-specific, and temporary)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field

from agentic_framework.core.config import StrictModel
from agentic_framework.exceptions import ConfigurationError

_DEFAULT_DISLIKED = [
    "excessive_gradients",
    "random_colorful_cards",
    "unnecessary_glassmorphism",
    "excessive_rounded_corners",
    "oversized_decorative_headings",
    "badge_clutter",
    "heavy_shadows",
]


class DesignPreferences(StrictModel):
    """Structured user or project design preferences."""

    schema_version: int = Field(default=1, ge=1, le=1)
    color_palettes: list[str] = Field(default_factory=list)
    typography: list[str] = Field(default_factory=list)
    spacing: str = "balanced"
    navigation_patterns: list[str] = Field(default_factory=list)
    dashboard_layouts: list[str] = Field(default_factory=list)
    button_styles: list[str] = Field(default_factory=list)
    card_structures: list[str] = Field(default_factory=list)
    form_layouts: list[str] = Field(default_factory=list)
    minimalism_level: str = "minimal"
    mobile_navigation: str = "bottom_or_drawer"
    animation_intensity: str = "subtle"
    disliked_patterns: list[str] = Field(default_factory=lambda: list(_DEFAULT_DISLIKED))
    approved_references: list[str] = Field(default_factory=list)
    rejected_patterns: list[str] = Field(default_factory=list)


def default_global_preferences_path() -> Path:
    """Return the default user-level design preferences path."""

    return Path.home() / ".agentic" / "preferences.yaml"


def project_preferences_path(project_root: Path) -> Path:
    """Return the project-level design preferences path."""

    return project_root.expanduser().resolve() / ".agentic" / "preferences.yaml"


def load_preferences_file(path: Path) -> DesignPreferences:
    """Load and validate a preferences YAML file, returning defaults if absent."""

    if not path.is_file():
        return DesignPreferences()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"cannot read design preferences {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError(f"design preferences must be a YAML mapping: {path}")
    return DesignPreferences.model_validate(data)


def save_preferences_file(path: Path, prefs: DesignPreferences) -> Path:
    """Persist validated design preferences to YAML."""

    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(prefs.model_dump(mode="json"), sort_keys=False)
    path.write_text(rendered, encoding="utf-8")
    return path


def resolve_effective_preferences(
    project_root: Path,
    *,
    global_path: Path | None = None,
) -> DesignPreferences:
    """Merge global preferences with project-specific overrides."""

    g_path = global_path or default_global_preferences_path()
    global_prefs = load_preferences_file(g_path)
    proj_path = project_preferences_path(project_root)
    if not proj_path.is_file():
        return global_prefs

    proj_raw = yaml.safe_load(proj_path.read_text(encoding="utf-8")) or {}
    merged: dict[str, Any] = global_prefs.model_dump(mode="json")
    for key, value in proj_raw.items():
        if value is not None:
            merged[key] = value
    return DesignPreferences.model_validate(merged)


def update_preference_field(
    path: Path,
    key: str,
    value: str,
) -> DesignPreferences:
    """Update a single scalar or list field in a sparse preferences YAML file."""

    if key not in DesignPreferences.model_fields or key == "schema_version":
        raise ConfigurationError(f"unknown design preference field: {key}")
    prefs = load_preferences_file(path)
    raw: dict[str, Any] = {}
    if path.is_file():
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            raw = dict(loaded)
    current = getattr(prefs, key)
    if isinstance(current, list):
        items = [item.strip() for item in value.split(",") if item.strip()]
        updated_val: Any = list(dict.fromkeys([*current, *items]))
    else:
        updated_val = value.strip()
    updated = prefs.model_copy(update={key: updated_val})
    raw[key] = updated_val
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return updated


def reset_preferences_file(path: Path) -> DesignPreferences:
    """Reset a preferences file back to clean defaults."""

    defaults = DesignPreferences()
    if path.is_file():
        path.write_text("{}\n", encoding="utf-8")
    return defaults
