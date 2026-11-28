import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentic_framework.cli import app
from agentic_framework.core.initialization import initialize_project
from agentic_framework.core.preferences import (
    DesignPreferences,
    project_preferences_path,
    reset_preferences_file,
    resolve_effective_preferences,
    save_preferences_file,
    update_preference_field,
)
from agentic_framework.exceptions import ConfigurationError

runner = CliRunner()


def test_global_and_project_preferences_merge_without_overwriting_global(tmp_path: Path) -> None:
    global_path = tmp_path / "global_prefs.yaml"
    project_root = tmp_path / "app"
    project_root.mkdir()

    save_preferences_file(
        global_path,
        DesignPreferences(
            minimalism_level="minimal",
            navigation_patterns=["sidebar"],
            color_palettes=["slate-neutral"],
        ),
    )
    update_preference_field(
        project_preferences_path(project_root),
        "navigation_patterns",
        "top_nav",
    )

    merged = resolve_effective_preferences(project_root, global_path=global_path)
    assert merged.minimalism_level == "minimal"
    assert merged.color_palettes == ["slate-neutral"]
    assert merged.navigation_patterns == ["top_nav"]

    reset_preferences_file(project_preferences_path(project_root))
    after_reset = resolve_effective_preferences(project_root, global_path=global_path)
    assert after_reset.navigation_patterns == ["sidebar"]


def test_unknown_preference_field_raises_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="unknown design preference field"):
        update_preference_field(project_preferences_path(tmp_path), "invalid_field", "x")


def test_design_and_preferences_cli(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)

    set_res = runner.invoke(
        app,
        ["preferences", "set", "minimalism_level", "balanced", "--path", str(tmp_path)],
    )
    assert set_res.exit_code == 0
    assert "minimalism_level: balanced" in set_res.stdout

    show_res = runner.invoke(app, ["preferences", "--path", str(tmp_path)])
    assert show_res.exit_code == 0
    assert "minimalism_level: balanced" in show_res.stdout

    design_res = runner.invoke(
        app,
        ["design", "use a sidebar instead of top navigation", "--path", str(tmp_path)],
    )
    assert design_res.exit_code == 0
    assert "Design mode: greenfield_frontend" in design_res.stdout
    session = json.loads(
        (tmp_path / ".agentic/state/design-session.json").read_text(encoding="utf-8")
    )
    assert session["instruction"] == "use a sidebar instead of top navigation"
