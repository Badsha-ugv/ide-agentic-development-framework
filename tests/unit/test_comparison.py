from agentic_framework.requirements_manager.comparison import (
    compare_versions,
    render_impact_report,
)


def test_compares_versions_and_renders_impact() -> None:
    previous_manifest = {
        "version": "version-001",
        "files": [
            {"path": "changed.md", "sha256": "old"},
            {"path": "removed.md", "sha256": "removed"},
            {"path": "same.md", "sha256": "same"},
        ],
    }
    current_manifest = {
        "version": "version-002",
        "files": [
            {"path": "added.md", "sha256": "added"},
            {"path": "changed.md", "sha256": "new"},
            {"path": "same.md", "sha256": "same"},
        ],
        "conflicts": ["REQ-004"],
    }
    previous_index = {
        "requirements": [
            {"id": "REQ-001", "text_sha256": "old"},
            {"id": "REQ-002", "text_sha256": "removed"},
        ]
    }
    current_index = {
        "requirements": [
            {"id": "REQ-001", "text_sha256": "new"},
            {"id": "REQ-003", "text_sha256": "added"},
        ]
    }

    comparison = compare_versions(
        previous_manifest, current_manifest, previous_index, current_index
    )
    report = render_impact_report(comparison)

    assert comparison.files.added == ("added.md",)
    assert comparison.files.modified == ("changed.md",)
    assert comparison.files.removed == ("removed.md",)
    assert comparison.files.unchanged == ("same.md",)
    assert comparison.requirements.added == ("REQ-003",)
    assert comparison.requirements.modified == ("REQ-001",)
    assert comparison.requirements.removed == ("REQ-002",)
    assert "REQ-001, REQ-002, REQ-003" in report
    assert "Conflicts requiring resolution" in report


def test_report_handles_no_changes() -> None:
    comparison = compare_versions(
        {"version": "version-001", "files": []},
        {"version": "version-002", "files": []},
        {"requirements": []},
        {"requirements": []},
    )

    report = render_impact_report(comparison)

    assert "Requirement IDs requiring review: none identified." in report
    assert "- None" in report
