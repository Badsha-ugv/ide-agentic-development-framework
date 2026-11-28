"""Deep existing-project inspection, dependency detection, and focused impact analysis."""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from agentic_framework.core.project import ProjectInspection, inspect_project

_EXCLUDED_DIRS = frozenset(
    {
        ".agentic",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        "dist",
        "build",
    }
)
_CODE_EXTENSIONS = frozenset(
    {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".rb", ".php", ".dart", ".kt", ".swift"}
)
_CONFIG_FILES = (
    "pyproject.toml",
    "package.json",
    "tsconfig.json",
    "requirements.txt",
    "Dockerfile",
    "compose.yaml",
    "docker-compose.yml",
    "alembic.ini",
    "schema.prisma",
)


@dataclass(frozen=True, slots=True)
class ProjectIntelligenceReport:
    """Structured technical snapshot of an existing or initialized repository."""

    inspection: ProjectInspection
    dependencies: dict[str, tuple[str, ...]]
    modules: tuple[str, ...]
    config_files: tuple[str, ...]
    test_runners: tuple[str, ...]
    existing_docs: tuple[str, ...]
    todo_count: int
    todo_samples: tuple[str, ...]
    git_branch: str | None
    git_dirty: bool


@dataclass(frozen=True, slots=True)
class ImpactAnalysisReport:
    """Focused module and test impact analysis for a requested change."""

    query: str
    keywords: tuple[str, ...]
    matched_files: tuple[str, ...]
    related_tests: tuple[str, ...]
    affected_domains: tuple[str, ...]


def _iter_project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    if not root.exists():
        return files
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if _EXCLUDED_DIRS.intersection(relative.parts):
            continue
        files.append(path)
    return files


def _read_dependencies(root: Path) -> dict[str, tuple[str, ...]]:
    deps: dict[str, tuple[str, ...]] = {}

    pkg_json = root / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            names = sorted(
                {
                    *data.get("dependencies", {}).keys(),
                    *data.get("devDependencies", {}).keys(),
                }
            )
            if names:
                deps["node"] = tuple(names[:30])
        except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
            pass

    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            raw = data.get("project", {}).get("dependencies", [])
            names = sorted(
                {
                    re.split(r"[<>=!~;\[\s]", str(item), maxsplit=1)[0].strip()
                    for item in raw
                    if str(item).strip()
                }
            )
            if names:
                deps["python"] = tuple(names[:30])
        except (OSError, UnicodeError, tomllib.TOMLDecodeError, AttributeError):
            pass

    req_txt = root / "requirements.txt"
    if req_txt.is_file() and "python" not in deps:
        try:
            lines = req_txt.read_text(encoding="utf-8").splitlines()
            names = sorted(
                {
                    re.split(r"[<>=!~;\[\s#]", line.strip(), maxsplit=1)[0].strip()
                    for line in lines
                    if line.strip() and not line.strip().startswith("#")
                }
            )
            if names:
                deps["python"] = tuple(names[:30])
        except (OSError, UnicodeError):
            pass

    return deps


def _detect_test_runners(
    root: Path,
    deps: dict[str, tuple[str, ...]],
    files: list[Path],
) -> tuple[str, ...]:
    runners: list[str] = []
    all_deps = {name.lower() for group in deps.values() for name in group}
    rel_paths = {f.relative_to(root).as_posix() for f in files}

    if "pytest" in all_deps or any(p.startswith("tests/") for p in rel_paths):
        runners.append("pytest")
    if "vitest" in all_deps or any("vitest.config" in p for p in rel_paths):
        runners.append("vitest")
    if "jest" in all_deps or any("jest.config" in p for p in rel_paths):
        runners.append("jest")
    if "playwright" in all_deps or "@playwright/test" in all_deps:
        runners.append("playwright")
    return tuple(runners)


def _git_status(root: Path, has_git: bool) -> tuple[str | None, bool]:
    if not has_git or not root.exists():
        return None, False
    try:
        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        branch = branch_res.stdout.strip() if branch_res.returncode == 0 else None
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        dirty = bool(status_res.stdout.strip()) if status_res.returncode == 0 else False
        return branch or None, dirty
    except OSError:
        return None, False


def analyze_existing_project(root: Path) -> ProjectIntelligenceReport:
    """Perform read-only structural, dependency, and status analysis of a repository."""

    inspection = inspect_project(root)
    resolved = inspection.root
    files = _iter_project_files(resolved)
    deps = _read_dependencies(resolved)

    modules = tuple(
        sorted(
            {
                f.relative_to(resolved).parts[0]
                for f in files
                if len(f.relative_to(resolved).parts) > 1
            }
        )[:20]
    )
    configs = tuple(name for name in _CONFIG_FILES if (resolved / name).is_file())
    docs = tuple(
        f.relative_to(resolved).as_posix()
        for f in files
        if f.suffix.lower() == ".md"
    )[:20]

    todo_samples: list[str] = []
    todo_count = 0
    for path in files:
        if path.suffix.lower() not in _CODE_EXTENSIONS:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for idx, line in enumerate(lines, start=1):
            if "TODO" in line or "FIXME" in line:
                todo_count += 1
                if len(todo_samples) < 10:
                    rel = path.relative_to(resolved).as_posix()
                    todo_samples.append(f"{rel}:{idx}: {line.strip()[:80]}")

    branch, dirty = _git_status(resolved, inspection.has_git)
    return ProjectIntelligenceReport(
        inspection=inspection,
        dependencies=deps,
        modules=modules,
        config_files=configs,
        test_runners=_detect_test_runners(resolved, deps, files),
        existing_docs=docs,
        todo_count=todo_count,
        todo_samples=tuple(todo_samples),
        git_branch=branch,
        git_dirty=dirty,
    )


def analyze_impact(root: Path, query: str) -> ImpactAnalysisReport:
    """Identify files, tests, and domains likely affected by a focused change request."""

    resolved = root.expanduser().resolve()
    keywords = tuple(
        dict.fromkeys(
            token
            for token in re.findall(r"[a-z0-9]{3,}", query.lower())
            if token not in {"add", "the", "and", "for", "with", "from", "into", "update", "fix"}
        )
    )
    files = _iter_project_files(resolved)
    matched: list[str] = []
    tests: list[str] = []

    for path in files:
        rel = path.relative_to(resolved).as_posix()
        rel_lower = rel.lower()
        is_test = "test" in rel_lower or "spec" in rel_lower
        hit = any(kw in rel_lower for kw in keywords)
        if not hit and path.suffix.lower() in _CODE_EXTENSIONS:
            try:
                content_lower = path.read_text(encoding="utf-8", errors="ignore").lower()
                hit = any(kw in content_lower for kw in keywords)
            except OSError:
                hit = False
        if hit:
            if is_test:
                tests.append(rel)
            else:
                matched.append(rel)

    matched_stems = {Path(m).stem.lower() for m in matched}
    if matched_stems:
        for path in files:
            rel = path.relative_to(resolved).as_posix()
            if rel in tests:
                continue
            rel_lower = rel.lower()
            if ("test" in rel_lower or "spec" in rel_lower) and any(
                stem in rel_lower for stem in matched_stems if len(stem) >= 3
            ):
                tests.append(rel)

    domains: list[str] = []
    joined = " ".join(matched).lower()
    if any(tok in joined for tok in ("frontend", "components", "pages", ".tsx", ".jsx", "ui")):
        domains.append("frontend")
    if any(tok in joined for tok in ("backend", "api", "views", "routes", "models", "server")):
        domains.append("backend")
    if any(tok in joined for tok in ("migration", "schema", "database", "db")):
        domains.append("database")
    if any(tok in joined for tok in ("auth", "login", "jwt", "session")):
        domains.append("auth")

    return ImpactAnalysisReport(
        query=query,
        keywords=keywords,
        matched_files=tuple(matched[:25]),
        related_tests=tuple(tests[:25]),
        affected_domains=tuple(domains),
    )
