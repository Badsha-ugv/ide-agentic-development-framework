"""Requirements ingestion, immutable versioning, and comparison."""

from agentic_framework.requirements_manager.ingestion import (
    IngestionResult,
    RequirementsManager,
)
from agentic_framework.requirements_manager.screenshots import (
    SUPPORTED_SCREENSHOT_SUFFIXES,
    ScreenshotManager,
    ScreenshotReference,
    ScreenshotSyncResult,
    image_dimensions,
)

__all__ = [
    "SUPPORTED_SCREENSHOT_SUFFIXES",
    "IngestionResult",
    "RequirementsManager",
    "ScreenshotManager",
    "ScreenshotReference",
    "ScreenshotSyncResult",
    "image_dimensions",
]
