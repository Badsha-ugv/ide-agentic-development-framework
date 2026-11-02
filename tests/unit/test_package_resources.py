"""Regression coverage for resources required by installed distributions."""

from importlib.resources import files

from agentic_framework.adapters import generated_project_files


def test_command_skill_is_packaged_and_loadable() -> None:
    skill = files("agentic_framework").joinpath(
        "templates/skills/agentic-commands/SKILL.md"
    )

    assert skill.is_file()
    assert skill.read_text(encoding="utf-8").startswith(
        "---\nname: agentic-commands\n"
    )


def test_generated_assets_use_packaged_command_skill() -> None:
    generated = generated_project_files()

    assert ".agents/skills/agentic-commands/SKILL.md" in generated
    assert generated[".agents/skills/agentic-commands/SKILL.md"].startswith("---\n")
