"""Atomic requirements ingestion and immutable version publication."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agentic_framework.exceptions import RequirementsError
from agentic_framework.requirements_manager.comparison import (
    VersionComparison,
    compare_versions,
    render_impact_report,
)
from agentic_framework.requirements_manager.extraction import ExtractionResult, extract_text
from agentic_framework.requirements_manager.screenshots import ScreenshotManager
from agentic_framework.requirements_manager.traceability import (
    RequirementRecord,
    extract_requirement_records,
    traceability_document,
)

_VERSION_NAME = re.compile(r"version-(\d+)$")


@dataclass(frozen=True, slots=True)
class InventoryItem:
    """One inbox source and its stable metadata."""

    path: Path
    relative_path: Path
    sha256: str
    size: int
    media_type: str
    extraction: ExtractionResult


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Outcome of an ingestion attempt."""

    version: str
    version_path: Path
    file_count: int
    requirement_count: int
    duplicate: bool
    previous_version: str | None = None
    impact_report: Path | None = None
    comparison: VersionComparison | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise RequirementsError(f"cannot read requirement source {path}: {exc}") from exc
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RequirementsError(f"cannot read version metadata {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RequirementsError(f"version metadata must be a JSON object: {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@contextmanager
def _ingestion_lock(requirements_root: Path) -> Iterator[None]:
    lock = requirements_root / ".ingestion.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RequirementsError(
            "requirements ingestion is already running; remove stale lock only after "
            f"verification: {lock}"
        ) from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode())
        os.close(descriptor)
        yield
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
        lock.unlink(missing_ok=True)


class RequirementsManager:
    """Version requirement sources without changing the inbox or prior versions."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.expanduser().resolve()
        self.requirements_root = self.project_root / "requirements"
        self.inbox = self.requirements_root / "inbox"
        self.versions = self.requirements_root / "versions"
        self.reports = self.requirements_root / "reports"

    def _prepare_directories(self) -> None:
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.versions.mkdir(parents=True, exist_ok=True)
        self.reports.mkdir(parents=True, exist_ok=True)

    def inventory(self) -> tuple[InventoryItem, ...]:
        """Hash and inspect every regular inbox file without modifying it."""

        items: list[InventoryItem] = []
        for path in sorted(self.inbox.rglob("*")):
            if path.is_symlink():
                raise RequirementsError(
                    f"symbolic links are not accepted in requirements inbox: {path}"
                )
            if not path.is_file():
                continue
            relative = path.relative_to(self.inbox)
            media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            items.append(
                InventoryItem(
                    path=path,
                    relative_path=relative,
                    sha256=_sha256(path),
                    size=path.stat().st_size,
                    media_type=media_type,
                    extraction=extract_text(path),
                )
            )
        if not items:
            raise RequirementsError(f"no requirement files found in {self.inbox}")
        return tuple(items)

    def _published_versions(self) -> list[tuple[Path, dict[str, Any]]]:
        published: list[tuple[Path, dict[str, Any]]] = []
        directories = [
            path
            for path in self.versions.glob("version-*")
            if path.is_dir() and _VERSION_NAME.fullmatch(path.name)
        ]
        directories.sort(key=lambda path: int(path.name.removeprefix("version-")))
        for directory in directories:
            manifest = directory / "manifest.json"
            if manifest.is_file():
                metadata = _read_json(manifest)
                self._validate_published_version(directory, metadata)
                published.append((directory, metadata))
            elif any(directory.iterdir()):
                raise RequirementsError(
                    f"incomplete requirements version must be repaired: {directory}"
                )
        return published

    def latest_version(self) -> dict[str, Any] | None:
        """Return validated metadata for the latest published version."""

        self._prepare_directories()
        published = self._published_versions()
        return published[-1][1] if published else None

    @staticmethod
    def _validate_published_version(directory: Path, manifest: dict[str, Any]) -> None:
        if manifest.get("version") != directory.name or manifest.get("immutable") is not True:
            raise RequirementsError(f"invalid immutable version manifest: {directory}")
        files = manifest.get("files")
        if not isinstance(files, list):
            raise RequirementsError(f"invalid file inventory in version manifest: {directory}")
        source_root = (directory / "source-files").resolve()
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("stored_path"), str):
                raise RequirementsError(f"invalid source record in version manifest: {directory}")
            stored = (directory / item["stored_path"]).resolve()
            if not stored.is_relative_to(source_root) or not stored.is_file():
                raise RequirementsError(f"missing or unsafe immutable source copy: {stored}")
            if _sha256(stored) != item.get("sha256"):
                raise RequirementsError(f"immutable source copy was modified: {stored}")
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, dict):
            raise RequirementsError(f"invalid artifact inventory in version manifest: {directory}")
        for relative, expected_hash in artifacts.items():
            artifact = (directory / relative).resolve()
            if not artifact.is_relative_to(directory.resolve()) or not artifact.is_file():
                raise RequirementsError(f"missing or unsafe immutable version artifact: {artifact}")
            if _sha256(artifact) != expected_hash:
                raise RequirementsError(f"immutable version artifact was modified: {artifact}")

    @staticmethod
    def _signature(items: tuple[InventoryItem, ...]) -> dict[str, str]:
        return {item.relative_path.as_posix(): item.sha256 for item in items}

    @staticmethod
    def _manifest_signature(manifest: dict[str, Any]) -> dict[str, str]:
        return {item["path"]: item["sha256"] for item in manifest["files"]}

    def _next_target(self, published: list[tuple[Path, dict[str, Any]]]) -> tuple[str, Path]:
        number = (
            int(published[-1][0].name.removeprefix("version-")) + 1 if published else 1
        )
        version = f"version-{number:03d}"
        target = self.versions / version
        if target.exists() and any(target.iterdir()):
            raise RequirementsError(f"requirements version target already contains data: {target}")
        return version, target

    @staticmethod
    def _requirements_markdown(items: tuple[InventoryItem, ...]) -> str:
        lines = ["# Consolidated requirements", ""]
        for item in items:
            relative = item.relative_path.as_posix()
            lines.extend([f"## Source: `{relative}`", ""])
            if item.extraction.text is not None:
                lines.extend([item.extraction.text.rstrip(), ""])
            else:
                lines.extend(
                    [
                        f"Extraction status: **{item.extraction.status.value}**.",
                        "",
                        item.extraction.message or "No diagnostic was provided.",
                        "",
                    ]
                )
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _requirements_index(records: dict[str, RequirementRecord]) -> dict[str, object]:
        return {
            "schema_version": 1,
            "requirements": [
                {
                    "id": record.requirement_id,
                    "source": record.source,
                    "text": record.text,
                    "text_sha256": record.sha256,
                }
                for record in sorted(records.values(), key=lambda item: item.requirement_id)
            ],
        }

    def _publish(
        self,
        items: tuple[InventoryItem, ...],
        version: str,
        target: Path,
        previous_version: str | None,
    ) -> tuple[dict[str, Any], dict[str, object]]:
        extracted = {
            item.relative_path.as_posix(): item.extraction.text
            for item in items
            if item.extraction.text is not None
        }
        records, conflicts = extract_requirement_records(extracted)
        manifest: dict[str, Any] = {
            "schema_version": 1,
            "version": version,
            "created_at": datetime.now(UTC).isoformat(),
            "previous_version": previous_version,
            "immutable": True,
            "files": [
                {
                    "path": item.relative_path.as_posix(),
                    "stored_path": f"source-files/{item.relative_path.as_posix()}",
                    "sha256": item.sha256,
                    "size": item.size,
                    "media_type": item.media_type,
                    "extraction": {
                        "status": item.extraction.status.value,
                        "message": item.extraction.message,
                    },
                }
                for item in items
            ],
            "conflicts": list(conflicts),
        }
        requirements_index = self._requirements_index(records)
        with tempfile.TemporaryDirectory(prefix=".adf-version-", dir=self.versions) as temporary:
            staging = Path(temporary)
            for item in items:
                destination = staging / "source-files" / item.relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(item.path, destination)
                if _sha256(destination) != item.sha256:
                    raise RequirementsError(f"copied source failed hash verification: {item.path}")
            _write_json(staging / "requirements-index.json", requirements_index)
            _write_json(staging / "traceability.json", traceability_document(records))
            (staging / "requirements.md").write_text(
                self._requirements_markdown(items), encoding="utf-8"
            )
            manifest["artifacts"] = {
                name: _sha256(staging / name)
                for name in (
                    "requirements-index.json",
                    "requirements.md",
                    "traceability.json",
                )
            }
            _write_json(staging / "manifest.json", manifest)
            if target.exists():
                target.rmdir()
            os.replace(staging, target)
        return manifest, requirements_index

    def _write_impact_report(self, comparison: VersionComparison) -> Path:
        report = self.reports / (
            f"{comparison.previous_version}-to-{comparison.current_version}-impact.md"
        )
        content = render_impact_report(comparison)
        if report.exists():
            if report.read_text(encoding="utf-8") != content:
                raise RequirementsError(f"refusing to overwrite existing impact report: {report}")
            return report
        report.write_text(content, encoding="utf-8")
        return report

    def ingest(self) -> IngestionResult:
        """Publish the inbox as the next immutable version or identify a duplicate."""

        self._prepare_directories()
        with _ingestion_lock(self.requirements_root):
            items = self.inventory()
            ScreenshotManager(self.project_root).sync()
            published = self._published_versions()
            latest = published[-1] if published else None
            if latest and self._manifest_signature(latest[1]) == self._signature(items):
                index = _read_json(latest[0] / "requirements-index.json")
                return IngestionResult(
                    version=latest[1]["version"],
                    version_path=latest[0],
                    file_count=len(items),
                    requirement_count=len(index["requirements"]),
                    duplicate=True,
                    previous_version=latest[1].get("previous_version"),
                )

            version, target = self._next_target(published)
            previous_version = latest[1]["version"] if latest else None
            manifest, index = self._publish(items, version, target, previous_version)
            comparison = None
            impact_report = None
            if latest:
                previous_index = _read_json(latest[0] / "requirements-index.json")
                comparison = compare_versions(latest[1], manifest, previous_index, index)
                impact_report = self._write_impact_report(comparison)
            return IngestionResult(
                version=version,
                version_path=target,
                file_count=len(items),
                requirement_count=len(index["requirements"]),
                duplicate=False,
                previous_version=previous_version,
                impact_report=impact_report,
                comparison=comparison,
            )
