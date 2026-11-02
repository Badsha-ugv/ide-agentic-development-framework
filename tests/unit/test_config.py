from pathlib import Path

import pytest

from agentic_framework.core.config import FrameworkConfig, dump_config, load_config, parse_config
from agentic_framework.exceptions import ConfigurationError


def test_default_configuration_is_conservative() -> None:
    config = parse_config({})

    assert config.schema_version == 1
    assert config.runtime.directory == Path(".agentic")
    assert config.runtime.log_level == "INFO"
    assert config.ide.enabled == ["codex"]
    assert config.policies.allow_network is False
    assert config.policies.allow_destructive_operations is False


def test_loads_and_normalizes_yaml(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        "project:\n  name: '  sample  '\n  mode: existing\n"
        "runtime:\n  directory: .runtime\n  log_level: DEBUG\n"
        "ide:\n  enabled: [codex, vscode]\n",
        encoding="utf-8",
    )

    config = load_config(path)

    assert config.project.name == "sample"
    assert config.project.mode == "existing"
    assert config.runtime.directory == Path(".runtime")
    assert FrameworkConfig.model_validate(config.model_dump()) == config
    assert "schema_version: 1" in dump_config(config)


@pytest.mark.parametrize("directory", ["/tmp/adf", "../outside", "nested/../../outside"])
def test_rejects_unsafe_runtime_directory(directory: str) -> None:
    with pytest.raises(ConfigurationError, match="runtime directory"):
        parse_config({"runtime": {"directory": directory}})


def test_rejects_unknown_keys() -> None:
    with pytest.raises(ConfigurationError, match="extra_forbidden"):
        parse_config({"runtime": {"verbosity": "high"}})


def test_rejects_duplicate_ide_adapters() -> None:
    with pytest.raises(ConfigurationError, match="must not be duplicated"):
        parse_config({"ide": {"enabled": ["codex", "codex"]}})


def test_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="root must be a YAML mapping"):
        load_config(path)


def test_reports_missing_and_malformed_files(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="does not exist"):
        load_config(tmp_path / "missing.yaml")

    malformed = tmp_path / "malformed.yaml"
    malformed.write_text("project: [", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="invalid YAML"):
        load_config(malformed)

