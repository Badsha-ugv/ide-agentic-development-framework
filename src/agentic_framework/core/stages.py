"""Machine-readable workflow stage execution contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class StageContract:
    """The durable contract an IDE agent must execute for one workflow stage."""

    id: str
    name: str
    objective: str
    prerequisites: tuple[str, ...]
    required_inputs: tuple[str, ...]
    agent: str
    responsibilities: tuple[str, ...]
    instructions: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    validation_criteria: tuple[str, ...]
    completion_conditions: tuple[str, ...]
    approval_required: bool = False
    failure_behavior: str = "Record the error, preserve work, and do not advance."
    max_attempts: int = 3

    def as_dict(self) -> dict[str, Any]:
        """Return a YAML/JSON-compatible representation."""

        return asdict(self)


def _contract(
    stage_id: str,
    name: str,
    objective: str,
    *,
    prerequisites: tuple[str, ...] = (),
    inputs: tuple[str, ...] = (),
    agent: str = "main_orchestrator",
    responsibilities: tuple[str, ...] = (),
    instructions: tuple[str, ...] = (),
    outputs: tuple[str, ...] = (),
    validation: tuple[str, ...] = ("Required outputs exist and are non-empty.",),
    completion: tuple[str, ...] = (
        "Every required output is registered with its current SHA-256 digest.",
        "Validation succeeds without unresolved execution errors.",
    ),
    approval: bool = False,
) -> StageContract:
    return StageContract(
        id=stage_id,
        name=name,
        objective=objective,
        prerequisites=prerequisites,
        required_inputs=inputs,
        agent=agent,
        responsibilities=responsibilities,
        instructions=instructions,
        expected_outputs=outputs,
        validation_criteria=validation,
        completion_conditions=completion,
        approval_required=approval,
    )


CONTRACTS = (
    _contract(
        "project_initialization",
        "Project initialization",
        "Create and inspect the durable ADF project foundation.",
        inputs=("requirements/inbox/**",),
        responsibilities=("Inspect project mode, technologies, constraints, and resources.",),
        instructions=("Run adt init safely and preserve existing project files.",),
        outputs=(".agentic/reports/initialization.md",),
    ),
    _contract(
        "project_discovery",
        "Project discovery",
        "Turn submitted source requirements into a factual discovery baseline.",
        prerequisites=("project_initialization",),
        inputs=(
            ".agentic/reports/initialization.md",
            "requirements/versions/*/requirements.md",
            "requirements/versions/*/manifest.json",
        ),
        agent="requirements_analyst",
        responsibilities=(
            "Identify objectives, stakeholders, users, scope, features, and business rules.",
            "Identify constraints, risks, assumptions, and missing information.",
            "Ask clarification questions instead of inventing missing facts.",
        ),
        instructions=(
            "Read the latest immutable requirements version and project inspection report.",
            "Separate sourced facts from assumptions and unanswered questions.",
            "Generate all discovery documents and register each artifact.",
            "If material questions remain, record them and block rather than fabricate answers.",
        ),
        outputs=(
            "docs/discovery/project-overview.md",
            "docs/discovery/stakeholder-analysis.md",
            "docs/discovery/clarification-log.md",
            "docs/discovery/assumptions-and-risks.md",
        ),
        validation=(
            "All four discovery documents exist and are non-empty.",
            "Claims distinguish source evidence, assumptions, risks, and open questions.",
        ),
    ),
    _contract(
        "requirements_ingestion",
        "Requirements ingestion",
        "Confirm immutable source requirements are available for engineering.",
        prerequisites=("project_discovery",),
        inputs=("requirements/inbox/**",),
        agent="requirements_analyst",
        instructions=("Run adt requirements ingest and inspect the latest manifest.",),
        outputs=(
            "requirements/versions/*/manifest.json",
            "requirements/versions/*/requirements.md",
            "requirements/versions/*/traceability.json",
        ),
    ),
    _contract(
        "requirements_analysis",
        "Requirements engineering",
        "Produce stable, traceable functional and quality requirements.",
        prerequisites=("requirements_ingestion",),
        inputs=("docs/discovery/*.md", "requirements/versions/*/requirements-index.json"),
        agent="requirements_analyst",
        responsibilities=("Maintain stable requirement IDs and source traceability.",),
        instructions=(
            "Resolve only answered clarifications and retain unresolved items explicitly.",
            "Derive requirements and acceptance criteria from immutable sources.",
        ),
        outputs=(
            "docs/requirements/functional-requirements.md",
            "docs/requirements/non-functional-requirements.md",
            "docs/requirements/user-stories.md",
            "docs/requirements/acceptance-criteria.md",
            "docs/requirements/requirements-traceability.md",
        ),
    ),
    _contract(
        "srs_and_project_documentation",
        "Software requirements specification",
        "Consolidate approved-source requirements into a reviewable SRS.",
        prerequisites=("requirements_analysis",),
        inputs=("docs/requirements/*.md",),
        agent="requirements_analyst",
        instructions=("Create an SRS without weakening IDs or traceability.",),
        outputs=("docs/requirements/SRS.md",),
    ),
    _contract(
        "requirements_review",
        "Requirements review",
        "Validate requirements deliverables and request explicit human approval.",
        prerequisites=("srs_and_project_documentation",),
        inputs=("docs/requirements/*.md",),
        agent="main_orchestrator",
        instructions=("Register the reviewed requirements set and summarize open concerns.",),
        outputs=(
            "docs/requirements/SRS.md",
            "docs/requirements/functional-requirements.md",
            "docs/requirements/non-functional-requirements.md",
            "docs/requirements/user-stories.md",
            "docs/requirements/acceptance-criteria.md",
            "docs/requirements/requirements-traceability.md",
        ),
        approval=True,
    ),
    _contract(
        "system_architecture",
        "System architecture",
        "Design the system from approved requirements and explicit constraints.",
        prerequisites=("requirements_review",),
        inputs=("docs/requirements/*.md",),
        agent="software_architect",
        instructions=(
            "Evaluate technology choices and document trade-offs.",
            "Define components, data, APIs, identity, security, deployment, and infrastructure.",
        ),
        outputs=(
            "docs/architecture/technology-evaluation.md",
            "docs/architecture/system-architecture.md",
            "docs/architecture/component-boundaries.md",
            "docs/architecture/database-design.md",
            "docs/architecture/api-design.md",
            "docs/architecture/security-architecture.md",
            "docs/architecture/deployment-architecture.md",
        ),
    ),
    _contract(
        "architecture_review",
        "Architecture review",
        "Validate architecture traceability and request explicit approval.",
        prerequisites=("system_architecture",),
        inputs=("docs/architecture/*.md",),
        agent="software_architect",
        instructions=("Review risks, requirement coverage, and unresolved decisions.",),
        outputs=("docs/architecture/system-architecture.md",),
        approval=True,
    ),
    _contract(
        "ui_ux_design",
        "UI/UX design",
        "Create a reviewable experience design before production frontend work.",
        prerequisites=("architecture_review",),
        inputs=("docs/requirements/*.md", "docs/architecture/*.md"),
        agent="ui_ux_designer",
        instructions=(
            "Use a configured Figma integration only when a Figma file is supplied.",
            "Otherwise create an interactive local HTML/CSS/JavaScript prototype.",
        ),
        outputs=("docs/design/ui-ux-specification.md", "design-prototype/index.html"),
    ),
    _contract(
        "design_review",
        "Design review",
        "Validate the prototype and request explicit approval before implementation.",
        prerequisites=("ui_ux_design",),
        inputs=("docs/design/*.md", "design-prototype/**"),
        agent="main_orchestrator",
        instructions=("Review accessibility, flows, requirements coverage, and feedback.",),
        outputs=("docs/design/ui-ux-specification.md", "design-prototype/index.html"),
        approval=True,
    ),
    _contract(
        "development_planning",
        "Development planning",
        "Create an executable, dependency-aware delivery plan.",
        prerequisites=("design_review",),
        inputs=("docs/requirements/*.md", "docs/architecture/*.md", "docs/design/*.md"),
        responsibilities=("Separate frontend, backend, integration, and verification work.",),
        instructions=("Define milestones, tasks, dependencies, tests, and delivery criteria.",),
        outputs=(
            "docs/planning/milestones.md",
            "docs/planning/task-breakdown.md",
            "docs/planning/testing-plan.md",
            "docs/planning/integration-plan.md",
        ),
    ),
    _contract(
        "implementation",
        "Implementation",
        "Implement approved tasks traceably against requirements and architecture.",
        prerequisites=("development_planning",),
        inputs=("docs/planning/*.md",),
        agent="main_orchestrator",
        instructions=(
            "Delegate sequential work, run focused tests, and record changed artifacts.",
        ),
        outputs=(".agentic/reports/implementation.md",),
    ),
    _contract(
        "integration",
        "Integration",
        "Integrate application components and verify their contracts.",
        prerequisites=("implementation",),
        agent="integration_engineer",
        instructions=("Run integration checks and document failures and resolutions.",),
        outputs=("docs/reports/integration.md",),
    ),
    _contract(
        "qa_and_testing",
        "QA and testing",
        "Verify acceptance criteria with reproducible automated and manual evidence.",
        prerequisites=("integration",),
        agent="qa_engineer",
        instructions=("Run the approved test plan and map results to requirement IDs.",),
        outputs=("docs/reports/qa-and-testing.md",),
    ),
    _contract(
        "code_and_security_review",
        "Code and security review",
        "Review correctness, maintainability, dependencies, and security risks.",
        prerequisites=("qa_and_testing",),
        agent="security_reviewer",
        instructions=("Record findings and verify critical issues are resolved.",),
        outputs=("docs/reports/code-review.md", "docs/reports/security-review.md"),
    ),
    _contract(
        "docker_and_ci_cd_validation",
        "Docker and CI/CD validation",
        "Validate reproducible builds, containers, and delivery automation.",
        prerequisites=("code_and_security_review",),
        agent="devops_engineer",
        instructions=(
            "Validate only integrations in project scope; do not deploy without approval.",
        ),
        outputs=("docs/reports/docker-and-ci-cd.md",),
    ),
    _contract(
        "final_documentation",
        "Final documentation",
        "Complete user, operator, developer, and traceability documentation.",
        prerequisites=("docker_and_ci_cd_validation",),
        instructions=("Reconcile documentation with the verified implementation.",),
        outputs=("docs/reports/final-documentation.md",),
    ),
    _contract(
        "release_review",
        "Release review",
        "Present verified release evidence for explicit human approval.",
        prerequisites=("final_documentation",),
        inputs=("docs/reports/*.md",),
        agent="main_orchestrator",
        instructions=("Summarize release evidence, limitations, and rollback considerations.",),
        outputs=("docs/reports/release-verification.md",),
        approval=True,
    ),
    _contract(
        "completed",
        "Completed",
        "Represent a fully approved and verified workflow.",
        prerequisites=("release_review",),
        validation=("All prior stages are complete and required approvals are recorded.",),
        completion=("Workflow status is completed.",),
    ),
)

STAGES = tuple(contract.id for contract in CONTRACTS)
APPROVAL_STAGES = frozenset(
    contract.id for contract in CONTRACTS if contract.approval_required
)
CONTRACT_BY_ID = {contract.id: contract for contract in CONTRACTS}


def contract_document() -> dict[str, Any]:
    """Return the complete versioned stage contract document."""

    return {
        "schema_version": 2,
        "execution_model": "ide_agent",
        "stages": [contract.as_dict() for contract in CONTRACTS],
    }
