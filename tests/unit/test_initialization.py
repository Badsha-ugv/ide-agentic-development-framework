from pathlib import Path

import pytest

from agentic_framework.core.initialization import FileStatus, initialize_project
from agentic_framework.exceptions import InitializationError


def test_initializes_new_project_structure_without_git(tmp_path: Path) -> None:
    target = tmp_path / "sample"

    result = initialize_project(target, initialize_git=False)

    assert result.mode == "new"
    assert all(item.status is FileStatus.CREATED for item in result.files)
    assert (target / ".agentic" / "config.yaml").is_file()
    assert (target / ".agentic" / "reports" / "initialization.md").is_file()
    assert (target / "requirements" / "inbox").is_dir()
    assert (target / "requirements" / "screenshots" / "desktop" / "homepage").is_dir()
    assert (target / "requirements" / "screenshots" / "mobile" / "dashboard").is_dir()
    assert (target / "requirements" / "screenshots" / "admin-dashboard").is_dir()
    assert (target / "requirements" / "versions").is_dir()
    assert not (target / "requirements" / "versions" / "version-001").exists()
    assert (target / "docs" / "architecture").is_dir()
    assert (target / "docs" / "ui-ux").is_dir()
    assert (target / ".agents" / "skills").is_dir()
    assert (target / ".codex" / "agents").is_dir()
    assert (target / ".github" / "instructions").is_dir()


def test_repeated_initialization_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "sample"
    first = initialize_project(target, initialize_git=False)
    config_before = (target / ".agentic" / "config.yaml").read_bytes()

    second = initialize_project(target, initialize_git=False)

    assert first.mode == second.mode == "new"
    assert all(item.status is FileStatus.UNCHANGED for item in second.files)
    assert second.conflicts == ()
    assert (target / ".agentic" / "config.yaml").read_bytes() == config_before


def test_existing_valid_config_is_preserved_byte_for_byte(tmp_path: Path) -> None:
    config = tmp_path / ".agentic" / "config.yaml"
    config.parent.mkdir(parents=True)
    original = "project: {name: custom, mode: existing}\n"
    config.write_text(original, encoding="utf-8")

    result = initialize_project(tmp_path, initialize_git=False)

    config_result = next(item for item in result.files if item.path == Path(".agentic/config.yaml"))
    assert config_result.status is FileStatus.UNCHANGED
    assert config.read_text(encoding="utf-8") == original
    assert not (tmp_path / ".agentic" / "proposals" / ".agentic").exists()


def test_invalid_existing_config_is_preserved_with_valid_proposal(tmp_path: Path) -> None:
    config = tmp_path / ".agentic" / "config.yaml"
    config.parent.mkdir(parents=True)
    invalid = "runtime: [invalid]\n"
    config.write_text(invalid, encoding="utf-8")

    result = initialize_project(tmp_path, initialize_git=False)

    conflict = next(item for item in result.conflicts if item.path == Path(".agentic/config.yaml"))
    assert config.read_text(encoding="utf-8") == invalid
    assert conflict.proposal == Path(".agentic/proposals/.agentic/config.yaml.proposed")
    proposal = tmp_path / conflict.proposal
    assert "schema_version: 1" in proposal.read_text(encoding="utf-8")


def test_preserves_conflicting_file_and_writes_proposal(tmp_path: Path) -> None:
    existing = "# Existing project rules\n"
    (tmp_path / "AGENTS.md").write_text(existing, encoding="utf-8")

    result = initialize_project(tmp_path, initialize_git=False)

    conflict = next(item for item in result.conflicts if item.path == Path("AGENTS.md"))
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == existing
    assert conflict.proposal == Path(".agentic/proposals/AGENTS.md.proposed")
    assert (tmp_path / conflict.proposal).read_text(encoding="utf-8").startswith(
        "# Project agent instructions"
    )
    report = (tmp_path / ".agentic" / "reports" / "initialization.md").read_text(
        encoding="utf-8"
    )
    assert "`AGENTS.md` preserved" in report


def test_existing_application_is_detected_and_preserved(tmp_path: Path) -> None:
    package = tmp_path / "package.json"
    package.write_text('{"private": true}', encoding="utf-8")

    result = initialize_project(tmp_path, initialize_git=False)

    assert result.mode == "existing"
    assert result.inspection.technologies == ("JavaScript",)
    assert package.read_text(encoding="utf-8") == '{"private": true}'


def test_git_is_initialized_only_when_not_detected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    initialized: list[Path] = []
    monkeypatch.setattr("agentic_framework.core.project.find_git_root", lambda _root: None)
    result = initialize_project(tmp_path, git_initializer=initialized.append)

    assert result.git_initialized is True
    assert initialized == [tmp_path.resolve()]

    initialized.clear()
    nested = tmp_path / "nested"
    nested.mkdir()
    (tmp_path / ".git").mkdir()
    monkeypatch.undo()
    nested_result = initialize_project(nested, git_initializer=initialized.append)
    assert nested_result.git_initialized is False
    assert initialized == []


def test_initializer_wraps_invalid_target_error(tmp_path: Path) -> None:
    target = tmp_path / "file"
    target.write_text("data", encoding="utf-8")

    with pytest.raises(InitializationError, match="not a directory"):
        initialize_project(target, initialize_git=False)

