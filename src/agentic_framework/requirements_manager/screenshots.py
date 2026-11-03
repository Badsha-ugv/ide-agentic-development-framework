"""Immutable screenshot-reference discovery and metadata versioning."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agentic_framework.exceptions import RequirementsError

SUPPORTED_SCREENSHOT_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})
_GENERATED_START = "<!-- ADF:SCREENSHOT-INVENTORY:START -->"
_GENERATED_END = "<!-- ADF:SCREENSHOT-INVENTORY:END -->"


@dataclass(frozen=True, slots=True)
class ScreenshotReference:
    """Metadata for one unmodified screenshot reference."""

    path: Path
    relative_path: Path
    sha256: str
    size: int
    width: int
    height: int
    format: str
    context: tuple[str, ...]
    device_hint: str
    page_hint: str
    role_hint: str | None

    def as_dict(self) -> dict[str, Any]:
        """Return stable JSON-compatible metadata."""

        return {
            "path": self.relative_path.as_posix(),
            "sha256": self.sha256,
            "size": self.size,
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "context": list(self.context),
            "device_hint": self.device_hint,
            "page_hint": self.page_hint,
            "role_hint": self.role_hint,
        }


@dataclass(frozen=True, slots=True)
class ScreenshotSyncResult:
    """Outcome of screenshot discovery and immutable catalog publication."""

    revision: int
    file_count: int
    duplicate: bool
    manifest_path: Path
    analysis_path: Path
    version_path: Path | None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise RequirementsError(f"cannot read screenshot reference {path}: {exc}") from exc
    return digest.hexdigest()


def _png_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n") and data[12:16] == b"IHDR":
        return struct.unpack(">II", data[16:24])
    return None


def _jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    if not data.startswith(b"\xff\xd8"):
        return None
    offset = 2
    start_of_frame = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in {0x01, *range(0xD0, 0xDA)}:
            continue
        if offset + 2 > len(data):
            break
        length = int.from_bytes(data[offset : offset + 2], "big")
        if length < 2 or offset + length > len(data):
            break
        if marker in start_of_frame and length >= 7:
            height = int.from_bytes(data[offset + 3 : offset + 5], "big")
            width = int.from_bytes(data[offset + 5 : offset + 7], "big")
            return width, height
        offset += length
    return None


def _little_uint24(value: bytes) -> int:
    return int.from_bytes(value, "little")


def _webp_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    kind = data[12:16]
    if kind == b"VP8X":
        return 1 + _little_uint24(data[24:27]), 1 + _little_uint24(data[27:30])
    if kind == b"VP8 " and data[23:26] == b"\x9d\x01\x2a":
        width = int.from_bytes(data[26:28], "little") & 0x3FFF
        height = int.from_bytes(data[28:30], "little") & 0x3FFF
        return width, height
    if kind == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
        bits = int.from_bytes(data[21:25], "little")
        return 1 + (bits & 0x3FFF), 1 + ((bits >> 14) & 0x3FFF)
    return None


def image_dimensions(path: Path) -> tuple[int, int]:
    """Read dimensions from a supported image header without modifying the file."""

    try:
        data = path.read_bytes()
    except OSError as exc:
        raise RequirementsError(f"cannot read screenshot reference {path}: {exc}") from exc
    suffix = path.suffix.lower()
    dimensions = {
        ".png": _png_dimensions,
        ".jpg": _jpeg_dimensions,
        ".jpeg": _jpeg_dimensions,
        ".webp": _webp_dimensions,
    }[suffix](data)
    if dimensions is None or min(dimensions) <= 0:
        raise RequirementsError(f"invalid or unsupported {suffix} screenshot image: {path}")
    return dimensions


def _hints(relative: Path, width: int, height: int) -> tuple[str, str, str | None]:
    context = [part.lower() for part in relative.parent.parts if part not in {".", ""}]
    if "mobile" in context:
        device = "mobile"
    elif "desktop" in context:
        device = "desktop"
    elif "tablet" in context:
        device = "tablet"
    else:
        ratio = width / height
        device = "mobile" if ratio < 0.75 else "desktop" if ratio > 1.15 else "unknown"
    roles = ("admin", "vendor", "customer")
    role = next((name for name in roles if any(name in part for part in context)), None)
    ignored = {"desktop", "mobile", "tablet", "references", "other"}
    page = next((part for part in reversed(context) if part not in ignored), relative.stem)
    return device, page, role


class ScreenshotManager:
    """Discover screenshots recursively and preserve immutable reference revisions."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.expanduser().resolve()
        self.root = self.project_root / "requirements" / "screenshots"
        self.versions = self.root / ".versions"
        self.manifest_path = self.root / "manifest.json"
        self.analysis_path = self.project_root / "docs" / "ui-ux" / (
            "screenshot-reference-analysis.md"
        )

    def discover(self) -> tuple[ScreenshotReference, ...]:
        """Recursively inventory supported screenshot files and contextual folder hints."""

        self.root.mkdir(parents=True, exist_ok=True)
        references: list[ScreenshotReference] = []
        for path in sorted(self.root.rglob("*")):
            relative = path.relative_to(self.root)
            if relative.parts and relative.parts[0] == ".versions":
                continue
            if path.is_symlink():
                raise RequirementsError(f"symbolic screenshot references are not accepted: {path}")
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_SCREENSHOT_SUFFIXES:
                continue
            width, height = image_dimensions(path)
            device, page, role = _hints(relative, width, height)
            references.append(
                ScreenshotReference(
                    path=path,
                    relative_path=relative,
                    sha256=_sha256(path),
                    size=path.stat().st_size,
                    width=width,
                    height=height,
                    format=path.suffix.lower().removeprefix(".").replace("jpeg", "jpg"),
                    context=relative.parent.parts,
                    device_hint=device,
                    page_hint=page,
                    role_hint=role,
                )
            )
        return tuple(references)

    @staticmethod
    def _signature(references: tuple[ScreenshotReference, ...]) -> dict[str, str]:
        return {item.relative_path.as_posix(): item.sha256 for item in references}

    def _read_manifest(self) -> dict[str, Any] | None:
        if not self.manifest_path.is_file():
            return None
        try:
            value = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RequirementsError(
                f"cannot read screenshot manifest {self.manifest_path}: {exc}"
            ) from exc
        if not isinstance(value, dict) or not isinstance(value.get("screenshots"), list):
            raise RequirementsError(f"invalid screenshot manifest: {self.manifest_path}")
        return value

    def _validate_versions(self) -> list[dict[str, Any]]:
        manifests: list[dict[str, Any]] = []
        if not self.versions.is_dir():
            return manifests
        for directory in sorted(self.versions.glob("version-*")):
            manifest_path = directory / "manifest.json"
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise RequirementsError(
                    f"cannot validate immutable screenshot revision {directory}: {exc}"
                ) from exc
            if not isinstance(manifest, dict) or manifest.get("immutable") is not True:
                raise RequirementsError(f"invalid immutable screenshot revision: {directory}")
            expected_revision = int(directory.name.removeprefix("version-"))
            if manifest.get("revision") != expected_revision:
                raise RequirementsError(f"invalid screenshot revision number: {directory}")
            screenshots = manifest.get("screenshots")
            if not isinstance(screenshots, list):
                raise RequirementsError(f"invalid screenshot inventory: {directory}")
            source_root = (directory / "source-files").resolve()
            for item in screenshots:
                if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                    raise RequirementsError(f"invalid screenshot record: {directory}")
                source = (source_root / item["path"]).resolve()
                if (
                    not source.is_relative_to(source_root)
                    or not source.is_file()
                    or source.is_symlink()
                    or _sha256(source) != item.get("sha256")
                ):
                    raise RequirementsError(
                        f"immutable screenshot reference was modified or removed: {source}"
                    )
            manifests.append(manifest)
        return manifests

    @staticmethod
    def _manifest_signature(manifest: dict[str, Any]) -> dict[str, str]:
        return {item["path"]: item["sha256"] for item in manifest["screenshots"]}

    @staticmethod
    def _atomic_text(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)

    def _analysis_inventory(
        self, references: tuple[ScreenshotReference, ...], revision: int
    ) -> str:
        lines = [
            _GENERATED_START,
            "# Screenshot reference analysis",
            "",
            f"Manifest revision: **{revision}**",
            "",
            "## Screenshot inventory",
            "",
        ]
        if not references:
            lines.append("No screenshot references were discovered.")
        else:
            lines.extend(
                [
                    "| Original path | Dimensions | Device hint | Page hint | Role hint |",
                    "| --- | ---: | --- | --- | --- |",
                ]
            )
            for item in references:
                role = item.role_hint or "unspecified"
                lines.append(
                    f"| `requirements/screenshots/{item.relative_path.as_posix()}` | "
                    f"{item.width}×{item.height} | {item.device_hint} | "
                    f"{item.page_hint} | {role} |"
                )
        lines.extend(
            [
                "",
                "> Folder-derived labels are contextual hints only. The frontend agent must "
                "inspect "
                "the actual images before recording conclusions.",
                _GENERATED_END,
            ]
        )
        return "\n".join(lines)

    def _update_analysis(
        self, references: tuple[ScreenshotReference, ...], revision: int
    ) -> None:
        generated = self._analysis_inventory(references, revision)
        editable = """

## Visual patterns and reusable components

To be completed by the frontend agent after visual inspection.

## Missing pages and responsive states

To be completed against approved requirements and the page inventory.

## Assumptions and inferred design decisions

Record evidence, confidence, and questions that materially affect usability.

## Reference-to-frontend traceability

Map each reference to the production frontend pages and components that use it.
"""
        if self.analysis_path.is_file():
            existing = self.analysis_path.read_text(encoding="utf-8")
            if _GENERATED_END in existing:
                editable = existing.split(_GENERATED_END, maxsplit=1)[1]
            elif existing.strip():
                editable = (
                    "\n\n## Preserved pre-existing analysis\n\n"
                    + existing.rstrip()
                    + "\n"
                )
        self._atomic_text(self.analysis_path, generated + editable.rstrip() + "\n")

    def sync(self) -> ScreenshotSyncResult:
        """Publish a new immutable screenshot revision when reference bytes change."""

        references = self.discover()
        versions = self._validate_versions()
        current = self._read_manifest()
        if versions and current is None:
            raise RequirementsError(
                "current screenshot manifest is missing while immutable revisions exist"
            )
        if current and versions:
            latest = versions[-1]
            if current.get("revision") != latest.get("revision") or self._manifest_signature(
                current
            ) != self._manifest_signature(latest):
                raise RequirementsError(
                    "current screenshot manifest does not match the latest immutable revision"
                )
        if current and self._manifest_signature(current) == self._signature(references):
            revision = int(current.get("revision", 1))
            self._update_analysis(references, revision)
            return ScreenshotSyncResult(
                revision=revision,
                file_count=len(references),
                duplicate=True,
                manifest_path=self.manifest_path,
                analysis_path=self.analysis_path,
                version_path=self.versions / f"version-{revision:03d}",
            )

        revision = int(current.get("revision", 0)) + 1 if current else 1
        version_path = self.versions / f"version-{revision:03d}"
        self.versions.mkdir(parents=True, exist_ok=True)
        if version_path.exists():
            raise RequirementsError(f"screenshot revision target already exists: {version_path}")
        manifest: dict[str, Any] = {
            "schema_version": 1,
            "revision": revision,
            "created_at": datetime.now(UTC).isoformat(),
            "immutable": True,
            "previous_revision": int(current["revision"]) if current else None,
            "screenshots": [item.as_dict() for item in references],
        }
        with tempfile.TemporaryDirectory(prefix=".adf-screenshots-", dir=self.versions) as temp:
            staging = Path(temp)
            for item in references:
                destination = staging / "source-files" / item.relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(item.path, destination)
                if _sha256(destination) != item.sha256:
                    raise RequirementsError(
                        f"copied screenshot failed hash verification: {item.path}"
                    )
            (staging / "manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            os.replace(staging, version_path)
        self._atomic_text(
            self.manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
        self._update_analysis(references, revision)
        return ScreenshotSyncResult(
            revision=revision,
            file_count=len(references),
            duplicate=False,
            manifest_path=self.manifest_path,
            analysis_path=self.analysis_path,
            version_path=version_path,
        )
