from pathlib import Path

import yaml

from agentic_framework.core.initialization import initialize_project


def test_generates_valid_codex_antigravity_and_canonical_configuration(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)

    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    skill = (tmp_path / ".agents/skills/agentic-commands/SKILL.md").read_text(
        encoding="utf-8"
    )
    continue_skill = (tmp_path / ".agents/skills/continue/SKILL.md").read_text(
        encoding="utf-8"
    )
    adf_skill = (tmp_path / ".agents/skills/adf/SKILL.md").read_text(encoding="utf-8")
    rules = (tmp_path / ".agents/rules/adf.md").read_text(encoding="utf-8")
    codex_note = (tmp_path / ".codex/agents/README.md").read_text(encoding="utf-8")
    workflow = yaml.safe_load((tmp_path / ".agentic/workflow.yaml").read_text(encoding="utf-8"))
    contracts = yaml.safe_load(
        (tmp_path / ".agentic/execution-contracts.yaml").read_text(encoding="utf-8")
    )
    registry = yaml.safe_load(
        (tmp_path / ".agentic/agent-registry.yaml").read_text(encoding="utf-8")
    )

    assert "agentic-commands" in agents
    assert skill.startswith("---\nname: agentic-commands\n")
    assert "IDE agent performs reasoning and artifact creation" in rules
    assert "adt stage complete" in skill
    assert "## Existing-project discipline" in skill
    assert "## Frontend implementation execution" in skill
    assert "## Backend and integration sequence" in skill
    assert "actual production frontend" in skill
    assert "report discovered" in rules
    assert "adapter boundary" in rules
    assert "name: continue" in continue_skill
    assert "does not advance" in continue_skill
    assert "adt stage task" in adf_skill
    assert "does not assume an undocumented" in codex_note
    assert workflow["schema_version"] == 5
    assert len(workflow["stages"]) == 22
    assert workflow["stages"][6]["approval_required"] is True
    assert contracts["execution_model"] == "ide_agent"
    assert contracts["schema_version"] == 5
    assert contracts["stages"][2]["expected_outputs"][0] == (
        "docs/discovery/project-overview.md"
    )
    assert len(registry["agents"]) == 13
    assert (tmp_path / ".agentic/agents/ui_ux_designer/AGENT.md").is_file()
    assert (tmp_path / ".agentic/agents/mobile_developer/AGENT.md").is_file()
    assert (tmp_path / ".agentic/agents/documentation_engineer/AGENT.md").is_file()
    assert (tmp_path / ".agentic/templates/SIMPLE_FEATURE_DOC.md").is_file()
    assert (tmp_path / ".agentic/templates/MOBILE_ARCHITECTURE.md").is_file()
    assert (tmp_path / ".agents/skills/analyze/SKILL.md").is_file()
    assert (tmp_path / ".agents/skills/plan/SKILL.md").is_file()
    frontend = next(item for item in registry["agents"] if item["id"] == "frontend_developer")
    assert frontend["instructions_file"] == ".agentic/agents/frontend_developer/AGENT.md"
    assert any("complete production frontend" in r for r in frontend["responsibilities"])
    backend = next(item for item in registry["agents"] if item["id"] == "backend_developer")
    integration = next(item for item in registry["agents"] if item["id"] == "integration_engineer")
    assert "adapter boundary" in backend["responsibilities"][1]
    assert "frontend mocks" in integration["responsibilities"][0]


def test_adapter_files_are_idempotent(tmp_path: Path) -> None:
    first = initialize_project(tmp_path, initialize_git=False)
    second = initialize_project(tmp_path, initialize_git=False)

    assert len(first.files) == 46
    assert not second.conflicts
