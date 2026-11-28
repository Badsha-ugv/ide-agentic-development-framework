from agentic_framework.core.config import ProjectMode, ProjectTask, TaskComplexity
from agentic_framework.core.routing import classify_complexity, resolve_workflow_route


def test_classify_complexity_auto_defaults() -> None:
    assert classify_complexity(ProjectTask.SPECIFIC_ISSUE, TaskComplexity.AUTO) is (
        TaskComplexity.LEVEL_1
    )
    assert classify_complexity(ProjectTask.ADD_FEATURE, TaskComplexity.AUTO) is (
        TaskComplexity.LEVEL_2
    )
    assert classify_complexity(ProjectTask.FULL_WORKFLOW, TaskComplexity.AUTO) is (
        TaskComplexity.LEVEL_3
    )
    assert classify_complexity(ProjectTask.FULL_WORKFLOW, TaskComplexity.LEVEL_1) is (
        TaskComplexity.LEVEL_1
    )


def test_existing_project_routes_skip_greenfield_discovery() -> None:
    audit_route = resolve_workflow_route(
        ProjectMode.EXISTING, ProjectTask.SECURITY_AUDIT, TaskComplexity.AUTO
    )
    assert audit_route == (
        "existing_project_analysis",
        "security_testing",
        "code_review",
        "release_review",
        "completed",
    )

    bug_l1 = resolve_workflow_route(
        ProjectMode.EXISTING, ProjectTask.BUG_HUNT, TaskComplexity.LEVEL_1
    )
    assert bug_l1 == (
        "existing_project_analysis",
        "implementation",
        "qa_and_testing",
        "release_review",
        "completed",
    )


def test_new_project_full_workflow_skips_existing_analysis() -> None:
    route = resolve_workflow_route(
        ProjectMode.NEW, ProjectTask.FULL_WORKFLOW, TaskComplexity.LEVEL_3
    )
    assert "existing_project_analysis" not in route
    assert route[0] == "project_initialization"
    assert route[1] == "project_discovery"
    assert route[-1] == "completed"
