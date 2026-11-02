from pathlib import Path

import yaml

from agentic_framework.core.initialization import initialize_project


def test_generates_valid_codex_antigravity_and_canonical_configuration(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)

    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    skill = (tmp_path / ".agents/skills/agentic-commands/SKILL.md").read_text(
        encoding="utf-8"
    )
    rules = (tmp_path / ".agents/rules/adf.md").read_text(encoding="utf-8")
    codex_note = (tmp_path / ".codex/agents/README.md").read_text(encoding="utf-8")
    workflow = yaml.safe_load((tmp_path / ".agentic/workflow.yaml").read_text(encoding="utf-8"))
    registry = yaml.safe_load(
        (tmp_path / ".agentic/agent-registry.yaml").read_text(encoding="utf-8")
    )

    assert "agentic-commands" in agents
    assert skill.startswith("---\nname: agentic-commands\n")
    assert "adt <command>" in rules
    assert "does not assume an undocumented" in codex_note
    assert len(workflow["stages"]) == 19
    assert workflow["stages"][5]["approval_required"] is True
    assert len(registry["agents"]) == 11


def test_adapter_files_are_idempotent(tmp_path: Path) -> None:
    first = initialize_project(tmp_path, initialize_git=False)
    second = initialize_project(tmp_path, initialize_git=False)

    assert len(first.files) == 10
    assert not second.conflicts
