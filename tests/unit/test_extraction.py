from pathlib import Path

from agentic_framework.requirements_manager.extraction import ExtractionStatus, extract_text


def test_extracts_utf8_text_with_bom(tmp_path: Path) -> None:
    source = tmp_path / "requirements.md"
    source.write_bytes(b"\xef\xbb\xbfREQ-001: Sign in\n")

    result = extract_text(source)

    assert result.status is ExtractionStatus.EXTRACTED
    assert result.text == "REQ-001: Sign in\n"


def test_reports_unsupported_binary_format(tmp_path: Path) -> None:
    source = tmp_path / "requirements.pdf"
    source.write_bytes(b"%PDF")

    result = extract_text(source)

    assert result.status is ExtractionStatus.UNSUPPORTED
    assert result.text is None
    assert ".pdf" in (result.message or "")


def test_reports_invalid_utf8_as_failed(tmp_path: Path) -> None:
    source = tmp_path / "requirements.txt"
    source.write_bytes(b"\xff\xfe")

    result = extract_text(source)

    assert result.status is ExtractionStatus.FAILED
    assert result.message

