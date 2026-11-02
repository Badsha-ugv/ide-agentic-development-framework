"""Small, explicit text-extraction boundary for requirement sources."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

_TEXT_EXTENSIONS = {".csv", ".json", ".md", ".rst", ".tsv", ".txt", ".yaml", ".yml"}


class ExtractionStatus(StrEnum):
    """Result of trying to extract searchable text from a source file."""

    EXTRACTED = "extracted"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Text and diagnostics produced by an extractor."""

    status: ExtractionStatus
    text: str | None = None
    message: str | None = None


def extract_text(path: Path) -> ExtractionResult:
    """Extract UTF-8 text or report why extraction was not possible."""

    extension = path.suffix.lower()
    if extension not in _TEXT_EXTENSIONS:
        label = extension or "files without an extension"
        return ExtractionResult(
            status=ExtractionStatus.UNSUPPORTED,
            message=f"text extraction is not configured for {label}",
        )
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return ExtractionResult(status=ExtractionStatus.FAILED, message=str(exc))
    return ExtractionResult(status=ExtractionStatus.EXTRACTED, text=text)
