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
        "UI/UX Design & Final Visual Prototype",
        "Produce the complete, high-fidelity visual specification that frontend work must follow.",
        prerequisites=("architecture_review",),
        inputs=(
            "docs/requirements/*.md",
            "docs/architecture/*.md",
            "requirements/screenshots/manifest.json",
            "requirements/screenshots/**",
            "existing project design assets",
            "optional Figma file or frame URL",
        ),
        agent="ui_ux_designer",
        responsibilities=(
            "Inventory every required page, user role, journey, state, and responsive layout.",
            "Treat the interactive prototype as the final visual source of truth, not a wireframe.",
            "Establish or faithfully preserve a coherent design system before building pages.",
            "Preserve traceability from requirements and visual references to generated pages.",
        ),
        instructions=(
            "Run adt requirements screenshots before analysis and inspect every discovered image.",
            "Record the selected Figma, generated-prototype, and screenshot methods in "
            "docs/ui-ux/design-inputs.json; methods may be combined.",
            "For Figma, use an available authenticated MCP integration, retrieve design context "
            "and screenshots, and block honestly when access or authentication fails.",
            "When no external source exists, propose the visual direction and design system for "
            "human review before generating every page.",
            "Build complete role-aware pages with realistic data, responsive layouts, reusable "
            "components, and loading, empty, success, validation, and error states.",
            "Give every visible control meaningful behavior; do not ship decorative controls.",
            "Run the prototype in a browser, inspect all pages at desktop, tablet, and mobile "
            "sizes, exercise interactions, capture rendered screenshots, fix defects, and repeat.",
            "Create an immutable prototype version under design-prototype/versions and update "
            "the revision history without overwriting the only prior approved version.",
        ),
        outputs=(
            "docs/design/ui-ux-specification.md",
            "docs/ui-ux/design-inputs.json",
            "docs/ui-ux/page-inventory.md",
            "docs/ui-ux/design-system.md",
            "docs/ui-ux/screenshot-reference-analysis.md",
            "docs/ui-ux/browser-verification.json",
            "docs/ui-ux/revision-history.md",
            "design-prototype/index.html",
            "design-prototype/versions/*/index.html",
            "design-prototype/verification-screenshots/**",
        ),
        validation=(
            "Design-input evidence selects a supported method and never claims unavailable Figma "
            "context was inspected.",
            "Page inventory covers approved roles, requirements, states, and responsive variants.",
            "The prototype uses a consistent documented design system and reusable components.",
            "Every visible interactive control has meaningful browser-tested behavior.",
            "Browser evidence passes every page at desktop, tablet, and mobile viewports and links "
            "to captured rendered screenshots.",
            "A versioned prototype and revision history preserve prior visual decisions.",
        ),
        completion=(
            "Every required output and rendered verification screenshot is registered with its "
            "current SHA-256 digest.",
            "Structured design-input and browser-verification evidence passes validation.",
            "The final prototype is complete enough for faithful production implementation.",
        ),
        design_inputs=("figma_mcp", "generated_prototype", "screenshots"),
    ),
    _contract(
        "design_review",
        "Final visual prototype review",
        "Present the complete browser-verified prototype for explicit human approval.",
        prerequisites=("ui_ux_design",),
        inputs=("docs/design/*.md", "docs/ui-ux/**", "design-prototype/**"),
        agent="main_orchestrator",
        instructions=(
            "Present the page inventory, local preview instructions, design system, responsive and "
            "interaction evidence, outstanding issues, and revision history.",
            "Require explicit human approval; never infer it from generated files or silence.",
            "For revision feedback, preserve unrelated approved decisions, update affected screens "
            "consistently, create a new prototype version, and rerun browser verification.",
        ),
        outputs=(
            "docs/design/ui-ux-specification.md",
            "docs/ui-ux/design-inputs.json",
            "docs/ui-ux/page-inventory.md",
            "docs/ui-ux/design-system.md",
            "docs/ui-ux/browser-verification.json",
            "docs/ui-ux/revision-history.md",
            "design-prototype/index.html",
            "design-prototype/versions/*/index.html",
            "design-prototype/verification-screenshots/**",
        ),
        validation=(
            "All final visual prototype evidence remains current and registered.",
            "Outstanding issues and assumptions are disclosed for human review.",
            "No frontend implementation begins before explicit approval is recorded.",
        ),
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
        inputs=(
            "docs/planning/*.md",
            "docs/ui-ux/*.md",
            "docs/ui-ux/*.json",
            "design-prototype/**",
        ),
        agent="main_orchestrator",
        instructions=(
            "Delegate sequential work, run focused tests, and record changed artifacts.",
            "Implement frontend pages from the approved prototype without independently "
            "redesigning or simplifying its layouts, components, interactions, or responsiveness.",
            "Compare production frontend rendering with approved prototype screenshots and record "
            "requirement, page, component, and visual-reference traceability.",
        ),
        outputs=(
            ".agentic/reports/implementation.md",
            "docs/reports/frontend-design-traceability.md",
        ),
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
        "schema_version": 3,
        "execution_model": "ide_agent",
        "stages": [contract.as_dict() for contract in CONTRACTS],
    }
