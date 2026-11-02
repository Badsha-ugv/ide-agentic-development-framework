"""Project discovery used by safe initialization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_TECHNOLOGY_MARKERS: dict[str, tuple[str, ...]] = {
    "Docker": (
        "Dockerfile",
        "compose.yaml",
        "compose.yml",
        "docker-compose.yaml",
        "docker-compose.yml",
    ),
    "Django": ("manage.py",),
    "JavaScript": ("package.json",),
    "Next.js": ("next.config.js", "next.config.mjs", "next.config.ts"),
    "Python": ("pyproject.toml", "setup.py", "requirements.txt"),
}

_PACKAGE_MANAGER_MARKERS: dict[str, tuple[str, ...]] = {
    "npm": ("package-lock.json",),
    "pip": ("pyproject.toml", "requirements.txt", "setup.py"),
    "pnpm": ("pnpm-lock.yaml",),
    "Poetry": ("poetry.lock",),
    "uv": ("uv.lock",),
    "Yarn": ("yarn.lock",),
}

@dataclass(frozen=True, slots=True)
class ProjectInspection:
    """Read-only facts discovered about an initialization target."""

    root: Path
    is_empty: bool
    git_root: Path | None
    technologies: tuple[str, ...]
    package_managers: tuple[str, ...]

    @property
    def has_git(self) -> bool:
        return self.git_root is not None


def _matching_labels(root: Path, markers: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    excluded = {".agentic", ".git", ".venv", "node_modules"}

    def exists(candidate: str) -> bool:
        direct = root / candidate
        if direct.exists():
            return True
        name = Path(candidate).name
        for match in root.rglob(name):
            relative = match.relative_to(root)
            if len(relative.parts) <= 4 and not excluded.intersection(relative.parts):
                return True
        return False

    return tuple(
        label
        for label, candidates in markers.items()
        if any(exists(candidate) for candidate in candidates)
    )


def find_git_root(root: Path) -> Path | None:
    """Find a repository marker in the target or one of its parents."""

    for candidate in (root, *root.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def inspect_project(root: Path) -> ProjectInspection:
    """Inspect a target without modifying it or invoking project tooling."""

    resolved = root.expanduser().resolve()
    if not resolved.exists():
        is_empty = True
    elif not resolved.is_dir():
        raise NotADirectoryError(f"initialization target is not a directory: {resolved}")
    else:
        is_empty = next(resolved.iterdir(), None) is None

    return ProjectInspection(
        root=resolved,
        is_empty=is_empty,
        git_root=find_git_root(resolved),
        technologies=_matching_labels(resolved, _TECHNOLOGY_MARKERS),
        package_managers=_matching_labels(resolved, _PACKAGE_MANAGER_MARKERS),
    )
