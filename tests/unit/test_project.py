from pathlib import Path

import pytest

from agentic_framework.core.project import find_git_root, inspect_project


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

