"""Engineering integrations (Git, testing, and deployment helpers)."""

from agentic_framework.integrations.git import (
    GitState,
    create_task_branch,
    inspect_git_state,
    safe_commit,
)

__all__ = ["GitState", "create_task_branch", "inspect_git_state", "safe_commit"]
