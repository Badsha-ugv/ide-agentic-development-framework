from pathlib import Path

import pytest

from agentic_framework.core.custom_commands import create_custom_command, custom_commands
from agentic_framework.core.initialization import initialize_project
from agentic_framework.exceptions import StateError


def test_creates_stage_aware_antigravity_command_without_overwrite(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)

    command = create_custom_command(
        tmp_path,
        "verify-api",
        "Inspect the current API deliverables and run relevant contract tests.",
    )
    content = (tmp_path / command.path).read_text(encoding="utf-8")

    assert command.name == "verify-api"
    assert content.startswith("---\nname: verify-api\n")
    assert "adt status" in content
    assert "adt stage task" in content
    assert "cannot override" in content
    assert command in custom_commands(tmp_path)
    with pytest.raises(StateError, match="already exists"):
        create_custom_command(tmp_path, "verify-api", "Replace it")


@pytest.mark.parametrize(
    ("name", "instructions", "message"),
    [
        ("Invalid Name", "Do work", "lowercase"),
        ("resume", "Do work", "reserved"),
        ("valid-name", " ", "cannot be blank"),
    ],
)
def test_rejects_unsafe_custom_command_inputs(
    tmp_path: Path, name: str, instructions: str, message: str
) -> None:
    initialize_project(tmp_path, initialize_git=False)

    with pytest.raises(StateError, match=message):
        create_custom_command(tmp_path, name, instructions)


def test_custom_command_requires_initialized_project(tmp_path: Path) -> None:
    assert custom_commands(tmp_path) == ()
    with pytest.raises(StateError, match="run adt init"):
        create_custom_command(tmp_path, "verify-api", "Run checks")
