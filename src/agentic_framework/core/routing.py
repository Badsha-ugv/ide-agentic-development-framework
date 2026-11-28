"""Dynamic workflow routing and task complexity classification."""

from __future__ import annotations

from agentic_framework.core.config import ProjectMode, ProjectTask, TaskComplexity
from agentic_framework.core.stages import STAGES

_GREENFIELD_STAGES: tuple[str, ...] = tuple(
    stage for stage in STAGES if stage != "existing_project_analysis"
)

_EXISTING_FULL_STAGES: tuple[str, ...] = tuple(
    stage for stage in STAGES if stage != "project_initialization"
)


def classify_complexity(task: ProjectTask, configured: TaskComplexity) -> TaskComplexity:
    """Resolve AUTO complexity into a concrete Level 1/2/3 classification."""

    if configured is not TaskComplexity.AUTO:
        return configured
    if task is ProjectTask.SPECIFIC_ISSUE:
        return TaskComplexity.LEVEL_1
    if task in {
        ProjectTask.BUG_HUNT,
        ProjectTask.SECURITY_AUDIT,
        ProjectTask.UI_REDESIGN,
        ProjectTask.ADD_FEATURE,
    }:
        return TaskComplexity.LEVEL_2
    return TaskComplexity.LEVEL_3


def resolve_workflow_route(
    mode: ProjectMode,
    task: ProjectTask,
    complexity: TaskComplexity = TaskComplexity.AUTO,
) -> tuple[str, ...]:
    """Return the ordered stage IDs required for the given project mode, task, and complexity."""

    effective = classify_complexity(task, complexity)
    if mode is ProjectMode.NEW:
        if effective is TaskComplexity.LEVEL_1 and task is ProjectTask.SPECIFIC_ISSUE:
            return (
                "project_discovery",
                "implementation",
                "qa_and_testing",
                "release_review",
                "completed",
            )
        return _GREENFIELD_STAGES

    if mode is ProjectMode.EXISTING:
        if task is ProjectTask.SECURITY_AUDIT:
            return (
                "existing_project_analysis",
                "security_testing",
                "code_review",
                "release_review",
                "completed",
            )
        if task in {ProjectTask.BUG_HUNT, ProjectTask.SPECIFIC_ISSUE}:
            if effective is TaskComplexity.LEVEL_1:
                return (
                    "existing_project_analysis",
                    "implementation",
                    "qa_and_testing",
                    "release_review",
                    "completed",
                )
            return (
                "existing_project_analysis",
                "development_planning",
                "implementation",
                "qa_and_testing",
                "code_review",
                "release_review",
                "completed",
            )
        if task is ProjectTask.UI_REDESIGN:
            return (
                "existing_project_analysis",
                "frontend_implementation",
                "frontend_review",
                "integration",
                "qa_and_testing",
                "release_review",
                "completed",
            )
        if task is ProjectTask.ADD_FEATURE:
            if effective is TaskComplexity.LEVEL_1:
                return (
                    "existing_project_analysis",
                    "implementation",
                    "qa_and_testing",
                    "release_review",
                    "completed",
                )
            if effective is TaskComplexity.LEVEL_2:
                return (
                    "existing_project_analysis",
                    "requirements_analysis",
                    "system_architecture",
                    "frontend_implementation",
                    "frontend_review",
                    "development_planning",
                    "implementation",
                    "integration",
                    "qa_and_testing",
                    "code_review",
                    "release_review",
                    "completed",
                )
            return _EXISTING_FULL_STAGES
        return _EXISTING_FULL_STAGES

    return STAGES
