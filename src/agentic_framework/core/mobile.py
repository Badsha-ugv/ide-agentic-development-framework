"""Mobile quality-gate validation for React Native, Expo, Flutter, and native apps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentic_framework.exceptions import StateError

_SUPPORTED_MOBILE_FRAMEWORKS = frozenset(
    {"react_native", "expo", "flutter", "android_kotlin", "ios_swift"}
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StateError(f"invalid mobile evidence {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise StateError(f"mobile evidence must be a JSON object: {path.name}")
    return data


def validate_mobile_evidence(project_root: Path) -> None:
    """Validate mobile implementation and Android/iOS device verification evidence."""

    root = project_root.expanduser().resolve()
    manifest = _read_json(root / "docs" / "mobile" / "implementation-manifest.json")
    framework = str(manifest.get("framework", "")).strip().lower()
    if framework not in _SUPPORTED_MOBILE_FRAMEWORKS:
        raise StateError(
            "mobile implementation manifest must specify a supported framework: "
            + ", ".join(sorted(_SUPPORTED_MOBILE_FRAMEWORKS))
        )
    platforms = manifest.get("platforms")
    if not isinstance(platforms, list) or not ({"android", "ios"} <= set(platforms)):
        raise StateError("mobile implementation manifest must target both android and ios")

    verification = _read_json(root / "docs" / "mobile" / "device-verification.json")
    if verification.get("passed") is not True:
        raise StateError("mobile device verification has not passed")
    for key in ("android_passed", "ios_passed", "permissions_verified", "offline_verified"):
        if verification.get(key) is not True:
            raise StateError(f"mobile device verification check failed: {key}")
