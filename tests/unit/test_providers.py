from pathlib import Path

from typer.testing import CliRunner

from agentic_framework.cli import app
from agentic_framework.core.config import IdeKind
from agentic_framework.core.initialization import initialize_project
from agentic_framework.providers import get_provider, list_providers

runner = CliRunner()


def test_claude_and_vscode_provider_files_generated_when_enabled(tmp_path: Path) -> None:
    initialize_project(
        tmp_path,
        initialize_git=False,
        ide_override=[IdeKind.CODEX, IdeKind.CLAUDE, IdeKind.VSCODE],
    )

    claude_md = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    claude_start = (tmp_path / ".claude/commands/start.md").read_text(encoding="utf-8")
    claude_plan = (tmp_path / ".claude/commands/plan.md").read_text(encoding="utf-8")
    copilot = (tmp_path / ".github/copilot-instructions.md").read_text(encoding="utf-8")
    vscode_rules = (tmp_path / ".github/instructions/adf.instructions.md").read_text(
        encoding="utf-8"
    )

    assert "Agentic Development Framework" in claude_md
    assert "adt stage complete" in claude_start
    assert "adt plan" in claude_plan
    assert "adt status" in copilot
    assert 'applyTo: "**"' in vscode_rules
    assert (tmp_path / ".agents/skills/agentic-commands/SKILL.md").is_file()
    assert (tmp_path / ".codex/agents/README.md").is_file()


def test_provider_result_normalization_across_providers() -> None:
    for provider in list_providers():
        ok = provider.normalize_result(
            {"status": "success", "summary": "Done", "files": ["a.py"]}
        )
        assert ok.status == "completed"
        assert ok.modified_files == ("a.py",)

        blocked = provider.normalize_result({"status": "waiting", "summary": "Need API key"})
        assert blocked.status == "blocked"
        assert blocked.blocker == "Need API key"

        failed = provider.normalize_result({"status": "error", "error": "Tests failed"})
        assert failed.status == "failed"
        assert failed.error == "Tests failed"

    assert get_provider(IdeKind.CLAUDE).capabilities.supports_slash_commands is True


def test_providers_cli_and_init_ide_flag(tmp_path: Path) -> None:
    providers_res = runner.invoke(app, ["providers"])
    assert providers_res.exit_code == 0
    assert "codex: OpenAI Codex" in providers_res.stdout
    assert "claude: Anthropic Claude Code" in providers_res.stdout
    assert "antigravity: Google Antigravity" in providers_res.stdout
    assert "vscode: VS Code AI" in providers_res.stdout

    init_res = runner.invoke(
        app, ["init", "--path", str(tmp_path), "--no-git", "--ide", "claude", "--ide", "vscode"]
    )
    assert init_res.exit_code == 0
    assert (tmp_path / "CLAUDE.md").is_file()
    assert (tmp_path / ".github/copilot-instructions.md").is_file()
