"""Safe, non-destructive Git workflow helpers."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentic_framework.exceptions import StateError

_SECRET_PATTERNS = re.compile(r"(^|/)\.env(\.|$)|\.pem$|\.key$|id_rsa", re.IGNORECASE)
_SAFE_BRANCH = re.compile(r"^[a-zA-Z0-9._/-]+$")


@dataclass(frozen=True, slots=True)
class GitState:
    """Read-only snapshot of repository Git status."""

    is_repo: bool
    branch: str | None
    dirty: bool
    changed_files: tuple[str, ...]


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise StateError(f"git command failed: {exc}") from exc


def inspect_git_state(root: Path) -> GitState:
    """Inspect current Git branch and working-tree changes without modifying anything."""

    resolved = root.expanduser().resolve()
    check = _run_git(resolved, "rev-parse", "--is-inside-work-tree")
    if check.returncode != 0 or check.stdout.strip() != "true":
        return GitState(is_repo=False, branch=None, dirty=False, changed_files=())

    branch_res = _run_git(resolved, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch_res.stdout.strip() if branch_res.returncode == 0 else None

    status_res = _run_git(resolved, "status", "--porcelain")
    lines = [line for line in status_res.stdout.splitlines() if line.strip()]
    changed = tuple(line[3:].strip() for line in lines if len(line) > 3)
    return GitState(is_repo=True, branch=branch or None, dirty=bool(lines), changed_files=changed)


def create_task_branch(root: Path, branch_name: str, *, allow_dirty: bool = False) -> str:
    """Create and switch to a task-specific branch safely."""

    name = branch_name.strip()
    if not name or not _SAFE_BRANCH.fullmatch(name) or ".." in name:
        raise StateError(f"invalid Git branch name: {branch_name}")
    state = inspect_git_state(root)
    if not state.is_repo:
        raise StateError("cannot create branch outside a Git repository")
    if state.dirty and not allow_dirty:
        raise StateError(
            "working tree has uncommitted changes; commit or stash them before branching"
        )
    res = _run_git(root.expanduser().resolve(), "checkout", "-b", name)
    if res.returncode != 0:
        detail = res.stderr.strip() or "unknown git checkout error"
        raise StateError(f"cannot create branch {name}: {detail}")
    return name


def safe_commit(root: Path, message: str, paths: tuple[str, ...] | list[str]) -> str:
    """Stage specific non-secret files and create a logical commit."""

    msg = message.strip()
    if not msg:
        raise StateError("commit message cannot be blank")
    if not paths:
        raise StateError("specify one or more paths to commit")
    for item in paths:
        if _SECRET_PATTERNS.search(item):
            raise StateError(f"refusing to stage potential secret file: {item}")

    resolved = root.expanduser().resolve()
    state = inspect_git_state(resolved)
    if not state.is_repo:
        raise StateError("cannot commit outside a Git repository")

    add_res = _run_git(resolved, "add", "--", *paths)
    if add_res.returncode != 0:
        raise StateError(f"git add failed: {add_res.stderr.strip()}")
    commit_res = _run_git(resolved, "commit", "-m", msg)
    if commit_res.returncode != 0:
        detail = (
            commit_res.stderr.strip() or commit_res.stdout.strip() or "unknown git commit error"
        )
        raise StateError(f"git commit failed: {detail}")
    rev_res = _run_git(resolved, "rev-parse", "--short", "HEAD")
    return rev_res.stdout.strip()
