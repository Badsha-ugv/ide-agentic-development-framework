"""Comparison and human-readable impact reporting for requirements versions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ChangeSet:
    """Added, modified, removed, and unchanged identifiers."""

    added: tuple[str, ...]
    modified: tuple[str, ...]
    removed: tuple[str, ...]
    unchanged: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class VersionComparison:
    """File-level and requirement-level changes between two versions."""

    previous_version: str
    current_version: str
    files: ChangeSet
    requirements: ChangeSet
    conflicts: tuple[str, ...]


def _changes(previous: dict[str, str], current: dict[str, str]) -> ChangeSet:
    previous_keys = set(previous)
    current_keys = set(current)
    shared = previous_keys & current_keys
    return ChangeSet(
        added=tuple(sorted(current_keys - previous_keys)),
        modified=tuple(sorted(key for key in shared if previous[key] != current[key])),
        removed=tuple(sorted(previous_keys - current_keys)),
        unchanged=tuple(sorted(key for key in shared if previous[key] == current[key])),
    )


def compare_versions(
    previous_manifest: dict[str, Any],
    current_manifest: dict[str, Any],
    previous_requirements: dict[str, Any],
    current_requirements: dict[str, Any],
) -> VersionComparison:
    """Compare source hashes and extracted requirement hashes."""

    previous_files = {item["path"]: item["sha256"] for item in previous_manifest["files"]}
    current_files = {item["path"]: item["sha256"] for item in current_manifest["files"]}
    previous_ids = {
        item["id"]: item["text_sha256"] for item in previous_requirements["requirements"]
    }
    current_ids = {
        item["id"]: item["text_sha256"] for item in current_requirements["requirements"]
    }
    return VersionComparison(
        previous_version=previous_manifest["version"],
        current_version=current_manifest["version"],
        files=_changes(previous_files, current_files),
        requirements=_changes(previous_ids, current_ids),
        conflicts=tuple(current_manifest.get("conflicts", [])),
    )


def _section(title: str, values: tuple[str, ...]) -> list[str]:
    lines = [f"### {title}", ""]
    lines.extend(f"- `{value}`" for value in values)
    if not values:
        lines.append("- None")
    lines.append("")
    return lines


def render_impact_report(comparison: VersionComparison) -> str:
    """Render an actionable Markdown impact report."""

    changed_ids = tuple(
        sorted(
            set(comparison.requirements.added)
            | set(comparison.requirements.modified)
            | set(comparison.requirements.removed)
        )
    )
    lines = [
        f"# Requirements impact: {comparison.previous_version} to {comparison.current_version}",
        "",
        "## Summary",
        "",
        "| Scope | Added | Modified | Removed | Unchanged |",
        "|---|---:|---:|---:|---:|",
        (
            f"| Source files | {len(comparison.files.added)} | {len(comparison.files.modified)} | "
            f"{len(comparison.files.removed)} | {len(comparison.files.unchanged)} |"
        ),
        (
            f"| Requirement IDs | {len(comparison.requirements.added)} | "
            f"{len(comparison.requirements.modified)} | {len(comparison.requirements.removed)} | "
            f"{len(comparison.requirements.unchanged)} |"
        ),
        "",
        "## Source file changes",
        "",
    ]
    lines.extend(_section("Added", comparison.files.added))
    lines.extend(_section("Modified", comparison.files.modified))
    lines.extend(_section("Removed", comparison.files.removed))
    lines.extend(["## Requirement changes", ""])
    lines.extend(_section("Added", comparison.requirements.added))
    lines.extend(_section("Modified", comparison.requirements.modified))
    lines.extend(_section("Removed", comparison.requirements.removed))
    lines.extend(_section("Conflicts requiring resolution", comparison.conflicts))
    lines.extend(
        [
            "## Impact review",
            "",
            f"Requirement IDs requiring review: {', '.join(changed_ids) or 'none identified'}.",
            "",
            "- Documentation: review the SRS, feature descriptions, user flows, and traceability.",
            "- Architecture: review components, data models, APIs, and decisions linked to "
            "changed IDs.",
            "- Implementation: review planned and active tasks linked to changed IDs.",
            "- Tests: add, update, or retire tests linked to changed IDs.",
            "- Approval: do not change approved decisions until this impact is reviewed.",
            "",
        ]
    )
    return "\n".join(lines)
