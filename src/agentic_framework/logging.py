"""Console and JSONL event logging utilities."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_MANAGED_HANDLER = "_agentic_framework_handler"


class JsonLineFormatter(logging.Formatter):
    """Render each log record as one machine-readable JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event_data = getattr(record, "event_data", None)
        if event_data:
            payload["event"] = event_data
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


def _managed(handler: logging.Handler) -> logging.Handler:
    setattr(handler, _MANAGED_HANDLER, True)
    return handler


def configure_logging(
    *,
    level: str | int = logging.INFO,
    event_log: Path | None = None,
) -> logging.Logger:
    """Configure ADF logging without disturbing handlers owned by the host application."""

    logger = logging.getLogger("agentic_framework")
    logger.setLevel(level)
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, _MANAGED_HANDLER, False):
            handler.close()
            logger.removeHandler(handler)

    console = _managed(logging.StreamHandler())
    console.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logger.addHandler(console)

    if event_log is not None:
        event_log.parent.mkdir(parents=True, exist_ok=True)
        jsonl = _managed(logging.FileHandler(event_log, encoding="utf-8"))
        jsonl.setFormatter(JsonLineFormatter())
        logger.addHandler(jsonl)

    return logger


def log_event(logger: logging.Logger, message: str, **event_data: Any) -> None:
    """Record a normal log message with optional structured event fields."""

    logger.info(message, extra={"event_data": event_data})

