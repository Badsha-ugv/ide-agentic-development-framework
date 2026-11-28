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
    "FastAPI": ("main.py",),
    "Flask": ("app.py", "wsgi.py"),
    "Laravel": ("artisan",),
    "JavaScript": ("package.json",),
    "Next.js": ("next.config.js", "next.config.mjs", "next.config.ts"),
    "NestJS": ("nest-cli.json",),
    "React": ("vite.config.ts", "vite.config.js"),
    "Vue": ("vue.config.js",),
    "TypeScript": ("tsconfig.json",),
    "Go": ("go.mod",),
    "Rust": ("Cargo.toml",),
    "PHP": ("composer.json",),
    "Ruby": ("Gemfile",),
    "Prisma": ("schema.prisma",),
    "Python": ("pyproject.toml", "setup.py", "requirements.txt"),
    "Flutter": ("pubspec.yaml",),
    "Expo": ("app.json", "app.config.js", "app.config.ts"),
    "Android": ("android/build.gradle", "android/build.gradle.kts"),
    "iOS": ("ios/Podfile",),
}

_PACKAGE_MANAGER_MARKERS: dict[str, tuple[str, ...]] = {
    "npm": ("package-lock.json",),
    "pip": ("pyproject.toml", "requirements.txt", "setup.py"),
    "pnpm": ("pnpm-lock.yaml",),
    "Poetry": ("poetry.lock",),
    "uv": ("uv.lock",),
    "Yarn": ("yarn.lock",),
    "bun": ("bun.lockb",),
    "Composer": ("composer.lock",),
    "Cargo": ("Cargo.lock",),
    "Bundler": ("Gemfile.lock",),
}

# Domain markers for existing-project completeness analysis.
_FRONTEND_MARKERS = (
    "src/app",
    "src/pages",
    "src/components",
    "app/page.tsx",
    "pages/index.tsx",
    "pages/index.jsx",
    "src/App.tsx",
    "src/App.jsx",
    "src/main.tsx",
    "src/views",
    "resources/views",
)

_BACKEND_MARKERS = (
    "manage.py",
    "app/Http/Controllers",
    "src/main.ts",
    "src/app.module.ts",
    "app.py",
    "main.py",
    "api",
    "server.py",
)

_DATABASE_MARKERS = (
    "schema.prisma",
    "migrations",
    "alembic.ini",
    "db/schema.rb",
    "database/migrations",
)

_AUTH_MARKERS = (
    "auth",
    "middleware/auth",
    "guards",
    "passport.ts",
    "passport.js",
    "jwt",
    "oauth",
)

_CI_MARKERS = (
    ".github/workflows",
    ".gitlab-ci.yml",
    "Jenkinsfile",
    ".circleci",
)

_MOBILE_MARKERS = (
    "pubspec.yaml",
    "android/build.gradle",
    "android/build.gradle.kts",
    "ios/Podfile",
    "app.config.ts",
    "app.config.js",
)


@dataclass(frozen=True, slots=True)
class DomainStatus:
    """Completion status of recognized project domains detected from the filesystem."""

    frontend: bool
    backend: bool
    database: bool
    auth: bool
    ci: bool
    mobile: bool = False

    @property
    def fully_complete(self) -> bool:
        return all((self.frontend, self.backend, self.database, self.auth, self.ci))

    @property
    def summary(self) -> str:
        parts = []
        if self.frontend:
            parts.append("frontend")
        if self.backend:
            parts.append("backend")
        if self.database:
            parts.append("database")
        if self.auth:
            parts.append("auth")
        if self.ci:
            parts.append("CI/CD")
        if self.mobile:
            parts.append("mobile")
        return ", ".join(parts) or "none detected"


@dataclass(frozen=True, slots=True)
class ProjectInspection:
    """Read-only facts discovered about an initialization target."""

    root: Path
    is_empty: bool
    git_root: Path | None
    technologies: tuple[str, ...]
    package_managers: tuple[str, ...]
    domain_status: DomainStatus = DomainStatus(
        frontend=False, backend=False, database=False, auth=False, ci=False
    )

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


def _any_exists(root: Path, candidates: tuple[str, ...]) -> bool:
    """Return True if any of the given paths exist under root."""
    excluded = {".agentic", ".git", ".venv", "node_modules", "__pycache__"}
    for candidate in candidates:
        direct = root / candidate
        if direct.exists():
            return True
        name = Path(candidate).name
        for match in root.rglob(name):
            relative = match.relative_to(root)
            if not excluded.intersection(relative.parts):
                return True
    return False


def _detect_domain_status(root: Path) -> DomainStatus:
    """Detect which domains are already implemented in an existing project."""
    return DomainStatus(
        frontend=_any_exists(root, _FRONTEND_MARKERS),
        backend=_any_exists(root, _BACKEND_MARKERS),
        database=_any_exists(root, _DATABASE_MARKERS),
        auth=_any_exists(root, _AUTH_MARKERS),
        ci=_any_exists(root, _CI_MARKERS),
        mobile=_any_exists(root, _MOBILE_MARKERS),
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

    domain = _detect_domain_status(resolved)
    return ProjectInspection(
        root=resolved,
        is_empty=is_empty,
        git_root=find_git_root(resolved),
        technologies=_matching_labels(resolved, _TECHNOLOGY_MARKERS),
        package_managers=_matching_labels(resolved, _PACKAGE_MANAGER_MARKERS),
        domain_status=domain,
    )
