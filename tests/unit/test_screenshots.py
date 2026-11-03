import hashlib
import json
from pathlib import Path

import pytest

from agentic_framework.exceptions import RequirementsError
from agentic_framework.requirements_manager import ScreenshotManager, image_dimensions


def _png(width: int, height: int) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + width.to_bytes(
        4, "big"
    ) + height.to_bytes(4, "big")


def _jpeg(width: int, height: int) -> bytes:
    return (
        b"\xff\xd8\xff\xc0\x00\x0b\x08"
        + height.to_bytes(2, "big")
        + width.to_bytes(2, "big")
        + b"\x01\x01\x11\x00\xff\xd9"
    )


def _webp(width: int, height: int) -> bytes:
    return (
        b"RIFF\x16\x00\x00\x00WEBPVP8X\x0a\x00\x00\x00\x00\x00\x00\x00"
        + (width - 1).to_bytes(3, "little")
        + (height - 1).to_bytes(3, "little")
    )


def _webp_lossy(width: int, height: int) -> bytes:
    return (
        b"RIFF\x16\x00\x00\x00WEBPVP8 \x0a\x00\x00\x00\x00\x00\x00\x9d\x01\x2a"
        + width.to_bytes(2, "little")
        + height.to_bytes(2, "little")
    )


def _webp_lossless(width: int, height: int) -> bytes:
    bits = (width - 1) | ((height - 1) << 14)
    header = b"RIFF\x11\x00\x00\x00WEBPVP8L\x05\x00\x00\x00\x2f"
    return header + bits.to_bytes(4, "little") + b"\0" * 5


def test_reads_supported_image_dimensions(tmp_path: Path) -> None:
    images = {
        "screen.png": (_png(1440, 900), (1440, 900)),
        "screen.jpg": (_jpeg(800, 1200), (800, 1200)),
        "screen.webp": (_webp(1024, 768), (1024, 768)),
        "lossy.webp": (_webp_lossy(640, 480), (640, 480)),
        "lossless.webp": (_webp_lossless(320, 240), (320, 240)),
    }
    for name, (content, dimensions) in images.items():
        path = tmp_path / name
        path.write_bytes(content)
        assert image_dimensions(path) == dimensions


def test_recursively_versions_screenshots_without_changing_originals(tmp_path: Path) -> None:
    root = tmp_path / "requirements" / "screenshots"
    desktop = root / "desktop" / "dashboard" / "overview.PNG"
    mobile = root / "customer-dashboard" / "nested" / "account.jpeg"
    desktop.parent.mkdir(parents=True)
    mobile.parent.mkdir(parents=True)
    desktop_bytes = _png(1440, 900)
    mobile_bytes = _jpeg(390, 844)
    desktop.write_bytes(desktop_bytes)
    mobile.write_bytes(mobile_bytes)
    (root / "notes.txt").write_text("not an image", encoding="utf-8")

    manager = ScreenshotManager(tmp_path)
    first = manager.sync()

    assert first.duplicate is False
    assert first.revision == 1
    assert first.file_count == 2
    assert desktop.read_bytes() == desktop_bytes
    assert mobile.read_bytes() == mobile_bytes
    manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))
    by_path = {item["path"]: item for item in manifest["screenshots"]}
    assert by_path["desktop/dashboard/overview.PNG"]["device_hint"] == "desktop"
    assert by_path["desktop/dashboard/overview.PNG"]["page_hint"] == "dashboard"
    assert by_path["customer-dashboard/nested/account.jpeg"]["role_hint"] == "customer"
    assert by_path["customer-dashboard/nested/account.jpeg"]["width"] == 390
    immutable = first.version_path / "source-files/desktop/dashboard/overview.PNG"
    assert immutable.read_bytes() == desktop_bytes
    assert by_path["desktop/dashboard/overview.PNG"]["sha256"] == hashlib.sha256(
        desktop_bytes
    ).hexdigest()

    analysis = first.analysis_path
    analysis.write_text(
        analysis.read_text(encoding="utf-8").replace(
            "To be completed by the frontend agent after visual inspection.",
            "Compact sidebar and dense data table.",
        ),
        encoding="utf-8",
    )
    duplicate = manager.sync()
    assert duplicate.duplicate is True
    assert "Compact sidebar" in analysis.read_text(encoding="utf-8")

    desktop.write_bytes(_png(1280, 720))
    second = manager.sync()
    assert second.revision == 2
    assert second.duplicate is False
    assert immutable.read_bytes() == desktop_bytes
    assert "Compact sidebar" in analysis.read_text(encoding="utf-8")


def test_rejects_invalid_images_symlinks_and_tampered_history(tmp_path: Path) -> None:
    root = tmp_path / "requirements" / "screenshots"
    root.mkdir(parents=True)
    invalid = root / "invalid.png"
    invalid.write_bytes(b"not-png")
    with pytest.raises(RequirementsError, match="invalid or unsupported"):
        ScreenshotManager(tmp_path).sync()

    invalid.unlink()
    external = tmp_path / "external.png"
    external.write_bytes(_png(10, 10))
    (root / "linked.png").symlink_to(external)
    with pytest.raises(RequirementsError, match="symbolic"):
        ScreenshotManager(tmp_path).sync()

    (root / "linked.png").unlink()
    actual = root / "actual.png"
    actual.write_bytes(_png(20, 20))
    result = ScreenshotManager(tmp_path).sync()
    archived = result.version_path / "source-files/actual.png"
    archived.write_bytes(_png(30, 30))
    with pytest.raises(RequirementsError, match="immutable screenshot reference"):
        ScreenshotManager(tmp_path).sync()


def test_empty_catalog_and_context_hint_variants(tmp_path: Path) -> None:
    manager = ScreenshotManager(tmp_path)
    manager.analysis_path.parent.mkdir(parents=True)
    manager.analysis_path.write_text("# Existing visual research\n", encoding="utf-8")
    empty = manager.sync()
    assert empty.file_count == 0
    assert "No screenshot references" in empty.analysis_path.read_text(encoding="utf-8")
    assert "# Existing visual research" in empty.analysis_path.read_text(encoding="utf-8")

    tablet = manager.root / "tablet/references/square.png"
    tablet.parent.mkdir(parents=True)
    tablet.write_bytes(_png(800, 800))
    result = manager.sync()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["screenshots"][0]["device_hint"] == "tablet"
    assert manifest["screenshots"][0]["page_hint"] == "square"


@pytest.mark.parametrize(
    ("manifest_value", "message"),
    [
        ({"immutable": False, "revision": 1, "screenshots": []}, "invalid immutable"),
        ({"immutable": True, "revision": 9, "screenshots": []}, "revision number"),
        ({"immutable": True, "revision": 1, "screenshots": {}}, "inventory"),
        ({"immutable": True, "revision": 1, "screenshots": ["bad"]}, "record"),
    ],
)
def test_rejects_invalid_immutable_revision_metadata(
    tmp_path: Path, manifest_value: object, message: str
) -> None:
    manager = ScreenshotManager(tmp_path)
    version = manager.versions / "version-001"
    version.mkdir(parents=True)
    (version / "manifest.json").write_text(json.dumps(manifest_value), encoding="utf-8")

    with pytest.raises(RequirementsError, match=message):
        manager.sync()


def test_rejects_missing_malformed_or_divergent_current_manifest(tmp_path: Path) -> None:
    manager = ScreenshotManager(tmp_path)
    manager.sync()
    manager.manifest_path.unlink()
    with pytest.raises(RequirementsError, match="current screenshot manifest is missing"):
        manager.sync()

    archived = manager.versions / "version-001/manifest.json"
    current = json.loads(archived.read_text(encoding="utf-8"))
    manager.manifest_path.write_text("not-json", encoding="utf-8")
    with pytest.raises(RequirementsError, match="cannot read screenshot manifest"):
        manager.sync()

    manager.manifest_path.write_text(json.dumps([]), encoding="utf-8")
    with pytest.raises(RequirementsError, match="invalid screenshot manifest"):
        manager.sync()

    current["revision"] = 2
    manager.manifest_path.write_text(json.dumps(current), encoding="utf-8")
    with pytest.raises(RequirementsError, match="does not match"):
        manager.sync()


def test_rejects_unreadable_immutable_revision_manifest(tmp_path: Path) -> None:
    manager = ScreenshotManager(tmp_path)
    version = manager.versions / "version-001"
    version.mkdir(parents=True)
    (version / "manifest.json").write_text("not-json", encoding="utf-8")

    with pytest.raises(RequirementsError, match="cannot validate immutable"):
        manager.sync()
