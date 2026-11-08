from pathlib import Path

import pytest

from agentic_framework.core.project import DomainStatus, find_git_root, inspect_project


def test_inspects_empty_directory(tmp_path: Path) -> None:
    inspection = inspect_project(tmp_path)

    assert inspection.root == tmp_path.resolve()
    assert inspection.is_empty is True
    assert inspection.git_root == find_git_root(tmp_path.resolve())
    assert inspection.technologies == ()
    assert inspection.package_managers == ()


def test_detects_existing_technology_and_package_managers(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text("{}", encoding="utf-8")
    (frontend / "pnpm-lock.yaml").write_text("lockfileVersion: 9", encoding="utf-8")
    (tmp_path / "next.config.js").write_text("export default {}", encoding="utf-8")

    inspection = inspect_project(tmp_path)

    assert inspection.is_empty is False
    assert inspection.technologies == ("JavaScript", "Next.js")
    assert inspection.package_managers == ("pnpm",)


def test_detects_parent_git_repository(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    nested = tmp_path / "packages" / "app"
    nested.mkdir(parents=True)

    assert find_git_root(nested) == tmp_path
    assert inspect_project(nested).has_git is True


def test_nonexistent_directory_is_treated_as_empty(tmp_path: Path) -> None:
    inspection = inspect_project(tmp_path / "new-project")

    assert inspection.is_empty is True


def test_rejects_file_target(tmp_path: Path) -> None:
    target = tmp_path / "not-a-directory"
    target.write_text("content", encoding="utf-8")

    with pytest.raises(NotADirectoryError, match="not a directory"):
        inspect_project(target)


def test_domain_status_summary_and_completion() -> None:
    empty = DomainStatus(frontend=False, backend=False, database=False, auth=False, ci=False)
    assert empty.fully_complete is False
    assert empty.summary == "none detected"

    full = DomainStatus(frontend=True, backend=True, database=True, auth=True, ci=True)
    assert full.fully_complete is True
    assert "frontend" in full.summary
    assert "backend" in full.summary
    assert "database" in full.summary
    assert "auth" in full.summary
    assert "CI/CD" in full.summary


def test_detects_domain_status_from_filesystem(tmp_path: Path) -> None:
    app_file = tmp_path / "src" / "App.tsx"
    app_file.parent.mkdir(parents=True)
    app_file.write_text("export default function App() {}", encoding="utf-8")
    (tmp_path / "server.py").write_text("# backend", encoding="utf-8")
    (tmp_path / "alembic.ini").write_text("# migrations", encoding="utf-8")
    (tmp_path / "auth").mkdir()
    (tmp_path / ".github" / "workflows").mkdir(parents=True)

    inspection = inspect_project(tmp_path)
    assert inspection.domain_status.frontend is True
    assert inspection.domain_status.backend is True
    assert inspection.domain_status.database is True
    assert inspection.domain_status.auth is True
    assert inspection.domain_status.ci is True
    assert inspection.domain_status.fully_complete is True

