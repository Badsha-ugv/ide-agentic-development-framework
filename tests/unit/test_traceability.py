from agentic_framework.requirements_manager.traceability import (
    extract_requirement_records,
    traceability_document,
)


def test_extracts_multiline_requirement_blocks() -> None:
    records, conflicts = extract_requirement_records(
        {
            "features.md": (
                "# Features\nREQ-002: Export reports\nThe export must be CSV.\n\n"
                "REQ-001 - Sign in\nUsers authenticate securely.\n"
            )
        }
    )

    assert tuple(sorted(records)) == ("REQ-001", "REQ-002")
    assert "Users authenticate securely." in records["REQ-001"].text
    assert conflicts == ()
    document = traceability_document(records)
    assert document["requirements"][0]["id"] == "REQ-001"
    assert document["requirements"][0]["tasks"] == []


def test_reports_conflicting_duplicate_requirement_ids() -> None:
    records, conflicts = extract_requirement_records(
        {
            "a.md": "REQ-001: First wording\n",
            "b.md": "REQ-001: Different wording\n",
        }
    )

    assert records["REQ-001"].source == "a.md"
    assert conflicts == ("REQ-001",)

