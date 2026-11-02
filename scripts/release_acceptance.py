"""Exercise a built distribution in clean new and Django + React projects."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path

import yaml


def _run(command: list[str], *, cwd: Path) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout


def _write_project(root: Path) -> None:
    backend = root / "backend"
    frontend = root / "frontend"
    (backend / "config").mkdir(parents=True)
    (frontend / "src").mkdir(parents=True)
    (backend / "manage.py").write_text(
        "#!/usr/bin/env python\nfrom django.core.management import execute_from_command_line\n",
        encoding="utf-8",
    )
    (backend / "config" / "settings.py").write_text(
        "SECRET_KEY = 'test-only'\nINSTALLED_APPS = []\n", encoding="utf-8"
    )
    (frontend / "package.json").write_text(
        json.dumps(
            {
                "name": "acceptance-frontend",
                "private": True,
                "scripts": {"test": "vitest run"},
                "dependencies": {"react": "^19.0.0", "react-dom": "^19.0.0"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (frontend / "package-lock.json").write_text(
        '{"name":"acceptance-frontend","lockfileVersion":3}\n', encoding="utf-8"
    )
    (frontend / "src" / "App.jsx").write_text(
        "export default function App() { return <main>Acceptance</main>; }\n",
        encoding="utf-8",
    )
    (root / "AGENTS.md").write_text("# Existing project instructions\n", encoding="utf-8")


def _verify_files(root: Path) -> None:
    required = (
        "AGENTS.md",
        ".agents/rules/adf.md",
        ".agents/skills/agentic-commands/SKILL.md",
        ".codex/agents/README.md",
        ".agentic/config.yaml",
        ".agentic/workflow.yaml",
        ".agentic/policies.yaml",
        ".agentic/agent-registry.yaml",
        ".agentic/database/agentic.db",
        ".agentic/state/workflow.json",
        ".agentic/state/tasks.json",
        ".agentic/state/execution.json",
        ".agentic/logs/events.jsonl",
        "requirements/inbox",
        "requirements/versions",
        "requirements/reports",
    )
    missing = [relative for relative in required if not (root / relative).exists()]
    if missing:
        raise AssertionError(f"missing initialized paths: {missing}")
    workflow = yaml.safe_load((root / ".agentic/workflow.yaml").read_text(encoding="utf-8"))
    registry = yaml.safe_load(
        (root / ".agentic/agent-registry.yaml").read_text(encoding="utf-8")
    )
    assert len(workflow["stages"]) == 19
    assert len(registry["agents"]) == 11


def _verify_database(root: Path) -> None:
    database = root / ".agentic/database/agentic.db"
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert {"workflow", "tasks", "approvals", "checkpoints", "events"} <= tables


def run_acceptance(artifact: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="adf-release-") as temporary:
        temporary_root = Path(temporary)
        root = temporary_root / "django-react"
        new_project = temporary_root / "new-project"
        root.mkdir()
        new_project.mkdir()
        _write_project(root)
        environment = Path(temporary) / "venv"
        subprocess.run(
            [sys.executable, "-m", "venv", str(environment)],
            check=True,
        )
        python = environment / "bin" / "python"
        adt = environment / "bin" / "adt"
        _run([str(python), "-m", "pip", "install", str(artifact)], cwd=root)
        assert "Local-first agentic development" in _run([str(adt), "--help"], cwd=root)
        assert "adt 0.1.0" in _run([str(adt), "--version"], cwd=root)
        assert "Local-first agentic development" in _run(
            [str(python), "-m", "agentic_framework", "--help"], cwd=root
        )

        new_init = _run(
            [str(adt), "init", "--path", str(new_project), "--no-git"], cwd=root
        )
        new_second_init = _run(
            [str(adt), "init", "--path", str(new_project), "--no-git"], cwd=root
        )
        _verify_files(new_project)
        _verify_database(new_project)
        assert "Project mode: new" in new_init
        assert "Created files: 10" in new_init
        assert "Created files: 0" in new_second_init

        init_output = _run([str(adt), "init", "--no-git"], cwd=root)
        second_init = _run([str(python), "-m", "agentic_framework", "init", "--no-git"], cwd=root)
        _verify_files(root)
        _verify_database(root)
        assert (root / "AGENTS.md").read_text(encoding="utf-8") == (
            "# Existing project instructions\n"
        )
        assert (root / ".agentic/proposals/AGENTS.md.proposed").is_file()
        report = (root / ".agentic/reports/initialization.md").read_text(encoding="utf-8")
        assert "Django" in report and "JavaScript" in report and "npm" in report
        assert "Project mode: existing" in init_output
        assert "Created files: 9" in init_output
        assert "Conflicts: 1" in init_output
        assert "Created files: 0" in second_init
        assert "Conflicts: 1" in second_init
        assert "schema_version: 1" in _run(
            [str(adt), "config", "validate", ".agentic/config.yaml"], cwd=root
        )

        inbox = root / "requirements/inbox"
        (inbox / "product.md").write_text("REQ-001: Sign in\n", encoding="utf-8")
        _run([str(adt), "requirements", "ingest"], cwd=root)
        (inbox / "product.md").write_text(
            "REQ-001: Sign in with MFA\nREQ-002: Dashboard\n", encoding="utf-8"
        )
        second_requirements = _run([str(adt), "requirements", "ingest"], cwd=root)
        assert "version-002" in second_requirements
        assert (root / "requirements/reports/version-001-to-version-002-impact.md").is_file()

        assert "Status: active" in _run([str(adt), "start"], cwd=root)
        assert "project_discovery" in _run([str(adt), "continue"], cwd=root)
        assert "Status: paused" in _run([str(adt), "pause"], cwd=root)
        assert "project_discovery" in _run([str(adt), "status"], cwd=root)
        assert "Status: active" in _run([str(adt), "resume"], cwd=root)
        assert "Status: stopped" in _run([str(adt), "stop"], cwd=root)
        assert "Status: active" in _run([str(adt), "resume"], cwd=root)
        return {
            "artifact": artifact.name,
            "projects": ["new", "Django + React"],
            "idempotent_initialization": True,
            "existing_files_preserved": True,
            "codex_configuration": True,
            "antigravity_configuration": True,
            "configuration_validation": True,
            "state_database": True,
            "requirements_versions": 2,
            "recovery": True,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(run_acceptance(arguments.artifact.resolve()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
