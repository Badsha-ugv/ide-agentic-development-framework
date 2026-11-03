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
    supported_design_inputs: tuple[str, ...] = ()
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
    design_inputs: tuple[str, ...] = (),
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
        supported_design_inputs=design_inputs,
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
        "Frontend environment & complete UI implementation",
        "Configure and build the complete production frontend before backend implementation.",
        prerequisites=("architecture_review",),
        inputs=(
            "docs/requirements/*.md",
            "docs/architecture/*.md",
            "requirements/screenshots/manifest.json",
            "requirements/screenshots/**",
            "existing project design assets and frontend source",
            "optional Figma file or frame URL recorded in requirements",
        ),
        agent="frontend_developer",
        responsibilities=(
            "Inventory every required page, user role, journey, state, and responsive layout.",
            "Verify the selected frontend stack, package manager, runtime, and environment first.",
            "Build the actual maintainable production frontend; never create a disposable "
            "prototype.",
            "Reproduce approved Figma or screenshot references without unapproved visual "
            "deviation.",
            "Create an excellent modern interface when no external visual reference is supplied.",
        ),
        instructions=(
            "Run adt requirements screenshots before analysis and inspect every discovered image.",
            "Record the selected Figma, screenshot, and generated-frontend methods in "
            "docs/frontend/design-inputs.json; methods may be combined.",
            "For Figma, use an available authenticated MCP integration, retrieve design context "
            "and screenshots, and block honestly when access or authentication fails.",
            "Inspect the architecture and existing repository, select its required frontend stack, "
            "install dependencies with its package manager, and prove the environment and build "
            "work.",
            "Keep frontend and backend separate. Use typed mock data or an adapter boundary in "
            "this stage; do not implement the backend or couple components directly to unfinished "
            "APIs.",
            "For supplied references, match layout, dimensions, spacing, typography, colors, "
            "assets, responsive behavior, states, and interactions exactly except for documented "
            "approved revisions.",
            "When no external reference exists, establish a cohesive modern design system with "
            "strong information hierarchy, typography, spacing, color, depth, and restrained "
            "purposeful motion.",
            "Build complete role-aware production pages with realistic data, reusable components, "
            "design tokens, responsive layouts, and loading, empty, success, validation, and error "
            "states.",
            "Make every control meaningful and accessible: semantic structure, keyboard operation, "
            "visible focus, sufficient contrast, reduced-motion support, and clear feedback are "
            "mandatory.",
            "Optimize rendering, assets, navigation, and perceived performance; avoid generic "
            "template-like screens, placeholder content, decorative controls, and inconsistent "
            "one-off styling.",
            "Run the actual frontend in a browser at desktop, tablet, and mobile sizes, exercise "
            "all interactions and states, compare it with every reference, capture evidence, fix "
            "defects, and repeat.",
        ),
        outputs=(
            "docs/frontend/technology-and-environment.md",
            "docs/frontend/design-inputs.json",
            "docs/frontend/page-inventory.md",
            "docs/frontend/design-system.md",
            "docs/frontend/implementation-manifest.json",
            "docs/ui-ux/screenshot-reference-analysis.md",
            "docs/frontend/browser-verification.json",
            "docs/frontend/reference-comparison.md",
            "docs/frontend/revision-history.md",
            "docs/frontend/verification-screenshots/**",
        ),
        validation=(
            "Frontend environment and production build verification pass for the documented stack.",
            "Design-input evidence selects supported methods and never claims unavailable Figma "
            "context.",
            "The implementation manifest identifies existing production source files registered "
            "for review.",
            "Page inventory covers approved roles, requirements, states, and responsive variants.",
            "Every visible control has meaningful, accessible, browser-tested behavior.",
            "Browser evidence passes every page at desktop, tablet, and mobile with no console "
            "errors, links to captured screenshots, and records no unapproved reference "
            "deviations.",
        ),
        completion=(
            "Every required document, production frontend source file, and verification screenshot "
            "is registered with its current SHA-256 digest.",
            "Structured design-input, implementation, and browser evidence passes validation.",
            "The complete production frontend is ready for explicit visual and functional review.",
        ),
        design_inputs=("figma_mcp", "generated_frontend", "screenshots"),
    ),
    _contract(
        "design_review",
        "Production frontend review",
        "Present the complete browser-verified production frontend for explicit human approval.",
        prerequisites=("ui_ux_design",),
        inputs=(
            "docs/frontend/**",
            "docs/ui-ux/screenshot-reference-analysis.md",
            "frontend source",
        ),
        agent="main_orchestrator",
        instructions=(
            "Present the page inventory, local preview instructions, design system, responsive and "
            "interaction evidence, outstanding issues, and revision history.",
            "Require explicit human approval; never infer it from generated files or silence.",
            "For revision feedback, update affected production screens consistently, document the "
            "intentional design change, preserve unrelated decisions, and rerun frontend "
            "verification.",
        ),
        outputs=(
            "docs/frontend/technology-and-environment.md",
            "docs/frontend/design-inputs.json",
            "docs/frontend/page-inventory.md",
            "docs/frontend/design-system.md",
            "docs/frontend/implementation-manifest.json",
            "docs/frontend/browser-verification.json",
            "docs/frontend/reference-comparison.md",
            "docs/frontend/revision-history.md",
            "docs/frontend/verification-screenshots/**",
        ),
        validation=(
            "All production frontend source and review evidence remains current and registered.",
            "Outstanding issues and assumptions are disclosed for human review.",
            "No backend implementation begins before explicit frontend approval is recorded.",
        ),
        approval=True,
    ),
    _contract(
        "development_planning",
        "Backend & API integration planning",
        "Plan backend implementation and later API integration around the approved frontend.",
        prerequisites=("design_review",),
        inputs=("docs/requirements/*.md", "docs/architecture/*.md", "docs/frontend/**"),
        responsibilities=(
            "Separate backend construction from frontend/API integration and verification.",
        ),
        instructions=(
            "Derive API contracts from approved requirements, architecture, and frontend adapter "
            "needs.",
            "Define backend milestones, tasks, migrations, security, tests, integration, and "
            "delivery criteria.",
            "Do not redesign or rebuild the approved frontend during backend planning.",
        ),
        outputs=(
            "docs/planning/backend-implementation-plan.md",
            "docs/planning/api-integration-plan.md",
            "docs/planning/backend-testing-plan.md",
        ),
    ),
    _contract(
        "implementation",
        "Backend implementation",
        "Implement and verify the backend independently against approved contracts.",
        prerequisites=("development_planning",),
        inputs=(
            "docs/planning/*.md",
            "docs/frontend/implementation-manifest.json",
            "docs/frontend/page-inventory.md",
        ),
        agent="main_orchestrator",
        instructions=(
            "Implement data, domain, service, API, security, and persistence behavior from the "
            "plan.",
            "Run focused backend tests and record requirement and API-contract traceability.",
            "Do not redesign the approved frontend or bypass its documented adapter boundary.",
        ),
        outputs=(
            ".agentic/reports/backend-implementation.md",
            "docs/backend/implementation-manifest.json",
        ),
    ),
    _contract(
        "integration",
        "Frontend/backend API integration",
        "Connect the approved frontend to the verified backend and test end-to-end behavior.",
        prerequisites=("implementation",),
        agent="integration_engineer",
        instructions=(
            "Replace frontend mocks through its adapter boundary without changing approved "
            "presentation.",
            "Verify API contracts, authentication, validation, loading, empty, success, and error "
            "behavior.",
            "Run integration and browser checks and document failures, fixes, and remaining "
            "constraints.",
        ),
        outputs=("docs/reports/api-integration.md",),
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
        "schema_version": 4,
        "execution_model": "ide_agent",
        "stages": [contract.as_dict() for contract in CONTRACTS],
    }
