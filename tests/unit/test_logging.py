import json
import logging
from pathlib import Path

from agentic_framework.logging import configure_logging, log_event


def test_jsonl_event_log_contains_structured_data(tmp_path: Path) -> None:
    event_log = tmp_path / "logs" / "events.jsonl"
    logger = configure_logging(level="INFO", event_log=event_log)

    log_event(logger, "workflow initialized", workflow_id="WF-001", attempt=1)

    record = json.loads(event_log.read_text(encoding="utf-8"))
    assert record["level"] == "INFO"
    assert record["logger"] == "agentic_framework"
    assert record["message"] == "workflow initialized"
    assert record["event"] == {"workflow_id": "WF-001", "attempt": 1}
    assert record["timestamp"].endswith("+00:00")


def test_reconfiguration_is_idempotent_and_preserves_host_handlers(tmp_path: Path) -> None:
    logger = logging.getLogger("agentic_framework")
    host_handler = logging.NullHandler()
    logger.addHandler(host_handler)
    try:
        configure_logging(event_log=tmp_path / "first.jsonl")
        configure_logging(event_log=tmp_path / "second.jsonl")

        assert host_handler in logger.handlers
        assert len(logger.handlers) == 3
    finally:
        logger.removeHandler(host_handler)

