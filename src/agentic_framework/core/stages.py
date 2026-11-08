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
        "Create and inspect the durable ADF project foundation. "
        "Ask the user whether this is a new or existing project if not already determined. "
        "For existing projects, also ask what the primary goal is for this session.",
        inputs=("requirements/inbox/**",),
        responsibilities=(
            "Inspect project mode (new or existing) and ask the user when AUTO.",
            "For existing projects, detect completed domains: frontend, backend, "
            "database, auth, CI.",
            "Identify technologies, package managers, and framework versions from the filesystem.",
            "Ask the user for the session task when mode is existing: security audit, bug hunt, "
            "UI redesign, specific issue, add feature, or full workflow.",
        ),
        instructions=(
            "Run adt init safely and preserve existing project files.",
            "When mode is AUTO and the directory is non-empty, prompt: "
            "'Is this a new or existing project? [new/existing]'",
            "For existing projects, prompt: 'What do you want to do next? "
            "[security_audit / bug_hunt / ui_redesign / "
            "specific_issue / add_feature / full_workflow]'",
            "Record the chosen mode and task in .agentic/config.yaml.",
        ),
        outputs=(".agentic/reports/initialization.md",),
    ),
    _contract(
        "existing_project_analysis",
        "Existing project analysis",
        "Deeply analyze an existing project before proposing new work. "
        "Understand what is already built, what is missing, and what the requested task requires.",
        prerequisites=("project_initialization",),
        inputs=(
            ".agentic/reports/initialization.md",
            ".agentic/config.yaml",
            "source files, package.json, pyproject.toml, or equivalent",
            "existing routes, models, controllers, components, migrations",
        ),
        agent="requirements_analyst",
        responsibilities=(
            "Read every significant source file, config, and existing document "
            "before writing anything.",
            "Map completed work per domain: frontend pages/components, backend routes/services, "
            "database schema/migrations, auth implementation, CI/CD pipelines.",
            "Identify partial implementations, broken features, security gaps, and technical debt.",
            "Determine what the requested session task (from config) requires from existing code.",
            "Never invent facts about files that do not exist; report unknowns explicitly.",
        ),
        instructions=(
            "Read .agentic/config.yaml to determine project.task.",
            "Walk the entire source tree and catalogue: framework/runtime, entry points, routes, "
            "components/views, services, models, migrations, test suite, CI config, env files.",
            "For each domain (frontend, backend, database, auth, CI), state: "
            "complete, partial, or absent. List evidence files for each assessment.",
            "Identify issues relevant to the session task: "
            "security vulnerabilities for security_audit, failing code for bug_hunt, "
            "outdated or inconsistent UI for ui_redesign, error traces for specific_issue.",
            "Generate a comprehensive analysis report and a work-completion status document.",
            "If the task is security_audit, also run conceptual security analysis on auth, input "
            "validation, secrets management, dependency versions, and injection points.",
        ),
        outputs=(
            "docs/discovery/existing-project-analysis.md",
            "docs/discovery/work-completion-status.md",
        ),
        validation=(
            "Both documents exist and are substantive (not placeholder text).",
            "Each domain is explicitly assessed with evidence files cited.",
            "Session task findings are present and actionable.",
        ),
        completion=(
            "Every required output is registered with its current SHA-256 digest.",
            "Analysis grounds every claim in an observed file or command output.",
        ),
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
            "Research conventional websites and apps similar to the project idea to understand "
            "industry-standard UX patterns, design conventions, and feature expectations.",
        ),
        instructions=(
            "Read the latest immutable requirements version and project inspection report.",
            "Separate sourced facts from assumptions and unanswered questions.",
            "Research comparable production apps and websites to identify design and feature "
            "conventions relevant to the project type.",
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
            "Comparable product research is included to inform design and feature decisions.",
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
            "Select the frontend framework (React, Vue, etc.) and backend stack appropriate to "
            "the project requirements—do not default to any stack without justification.",
            "Design the database schema with indexing, relations, and migration strategy.",
            "Specify the API contract (REST or GraphQL), authentication flow, "
            "and authorization model.",
            "Document the security architecture including input validation, rate limiting, secrets "
            "management, CORS policy, and dependency audit plan.",
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
        "frontend_implementation",
        "Frontend implementation",
        "Build the complete, production-quality frontend application before any backend work. "
        "Design quality is the highest priority: modern, project-requirements-oriented, "
        "visually excellent with intentional color, typography, spacing, and motion.",
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
            "Research production websites and apps similar to the project idea; "
            "study their layout, color palette, component patterns, and typography before coding.",
            "Define a full design system: color palette (primary, secondary, accent, neutral, "
            "semantic), typography scale, spacing scale, border radius, shadow system, motion "
            "tokens, and breakpoints—before writing any page code.",
            "Inventory every required page, user role, journey, state, and responsive layout.",
            "Verify the selected frontend stack, package manager, runtime, and environment first.",
            "Build the actual maintainable production frontend; never create a "
            "disposable prototype, wireframe, or placeholder screen.",
            "Reproduce approved Figma or screenshot references without unapproved "
            "visual deviation.",
            "Create an excellent modern interface when no external visual reference is supplied; "
            "generic template output or inconsistent one-off styling is a build failure.",
        ),
        instructions=(
            "Step 1 — Research: Look up conventional websites and applications similar to the "
            "project idea. Note their dominant color schemes, typography choices, navigation "
            "patterns, card styles, and interaction paradigms. Record findings in "
            "docs/frontend/design-research.md.",
            "Step 2 — Design system: Create docs/frontend/design-system.md defining: "
            "color palette (hex values for primary, secondary, accent, background, surface, text, "
            "border, semantic states), typography (font families, weight scale, size scale, "
            "line-height), spacing scale, border radii, shadow levels, motion durations/easings, "
            "and responsive breakpoints. Every visual decision must be intentional and cohesive.",
            "Step 3 — Environment: Inspect the architecture and existing repository, select the "
            "required frontend stack, install dependencies with its package manager, and prove "
            "the environment and build work. Record in "
            "docs/frontend/technology-and-environment.md.",
            "Step 4 — Design inputs: Record the selected design input methods in "
            "docs/frontend/design-inputs.json (figma_mcp, screenshots, generated_frontend). "
            "For Figma, use an authenticated MCP integration; block honestly when access fails.",
            "Step 5 — Page inventory: Inventory all roles, routes, journeys, pages, responsive "
            "layouts, and loading/empty/success/validation/error states before writing page code. "
            "Record in docs/frontend/page-inventory.md.",
            "Step 6 — Implementation: Build complete role-aware production pages with realistic "
            "data, reusable components, design tokens, responsive layouts, and all required "
            "states. Every color, font, spacing, and animation value must reference design system "
            "tokens. No hardcoded one-off values. No Lorem Ipsum on key pages.",
            "Step 7 — Accessibility: Every control must be semantic, keyboard-accessible, have "
            "visible focus, sufficient color contrast (WCAG AA minimum), reduced-motion support, "
            "and meaningful ARIA labels. Accessibility is not optional.",
            "Step 8 — Separation: Keep frontend and backend separate. Use typed mock data or an "
            "adapter boundary; do not implement backend logic or couple components "
            "to unfinished APIs.",
            "Step 9 — Browser verification: Run the actual frontend in a browser at desktop "
            "(1440px), tablet (768px), and mobile (375px). Exercise all interactions and states, "
            "check the console for errors, capture rendered evidence, compare each page to its "
            "reference, fix defects, and repeat until clean.",
            "Step 10 — Registration: Register all required documents, source files, and "
            "verification screenshots. The implementation manifest must record successful "
            "environment and production-build checks.",
        ),
        outputs=(
            "docs/frontend/design-research.md",
            "docs/frontend/design-system.md",
            "docs/frontend/technology-and-environment.md",
            "docs/frontend/design-inputs.json",
            "docs/frontend/page-inventory.md",
            "docs/frontend/implementation-manifest.json",
            "docs/frontend/browser-verification.json",
            "docs/frontend/reference-comparison.md",
            "docs/frontend/revision-history.md",
            "docs/frontend/verification-screenshots/**",
        ),
        validation=(
            "Design system document defines all required token categories with concrete values.",
            "Design research document records comparable websites and extracted patterns.",
            "Frontend environment and production build verification pass for the documented stack.",
            "Design-input evidence selects supported methods and never claims unavailable Figma "
            "context.",
            "The implementation manifest identifies existing production source files registered "
            "for review.",
            "Page inventory covers approved roles, requirements, states, and responsive variants.",
            "Every visible control has meaningful, accessible, browser-tested behavior.",
            "Browser evidence passes every page at desktop, tablet, and mobile with no console "
            "errors, links to captured screenshots, and records no unapproved "
            "reference deviations.",
        ),
        completion=(
            "Every required document, production frontend source file, and verification screenshot "
            "is registered with its current SHA-256 digest.",
            "Structured design-input, implementation, and browser evidence passes validation.",
            "The complete production frontend with a high-quality design system is ready for "
            "explicit visual and functional review.",
        ),
        design_inputs=("figma_mcp", "generated_frontend", "screenshots"),
    ),
    _contract(
        "frontend_review",
        "Frontend review",
        "Present the complete browser-verified production frontend for explicit human approval.",
        prerequisites=("frontend_implementation",),
        inputs=(
            "docs/frontend/**",
            "frontend source",
        ),
        agent="main_orchestrator",
        instructions=(
            "Present the design system, page inventory, local preview instructions, responsive "
            "and interaction evidence, outstanding issues, and revision history.",
            "Show the color palette, typography choices, and design rationale.",
            "Require explicit human approval; never infer it from generated files or silence.",
            "For revision feedback, update affected production screens consistently, document the "
            "intentional design change, preserve unrelated decisions, and rerun frontend "
            "verification.",
        ),
        outputs=(
            "docs/frontend/design-system.md",
            "docs/frontend/technology-and-environment.md",
            "docs/frontend/design-inputs.json",
            "docs/frontend/page-inventory.md",
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
        prerequisites=("frontend_review",),
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
            "Plan database migrations and seed data strategy.",
            "Define authentication and authorization flows with token lifecycle.",
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
            "Implement all database migrations with rollback support.",
            "Implement input validation, error responses, and rate limiting.",
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
            "Test all authenticated and unauthenticated flows.",
            "Confirm loading and error states render correctly with real API responses.",
        ),
        outputs=("docs/reports/api-integration.md",),
    ),
    _contract(
        "database_validation",
        "Database and data integrity validation",
        "Verify the database schema, migrations, indexes, constraints, and data integrity "
        "against the architecture specification and production-readiness standards.",
        prerequisites=("integration",),
        agent="qa_engineer",
        responsibilities=(
            "Verify every migration runs cleanly forward and can be rolled back.",
            "Confirm all foreign key constraints, unique indexes, and NOT NULL "
            "constraints are present.",
            "Test for N+1 query patterns, missing indexes on frequently queried columns, and "
            "unprotected bulk operations.",
            "Confirm sensitive columns (passwords, tokens, PII) are properly protected.",
            "Verify seed data and initial migration state match the application's assumptions.",
        ),
        instructions=(
            "Run all migrations from scratch against a clean database and confirm success.",
            "Attempt rollback of the latest migration and confirm the previous state is restored.",
            "Inspect the schema: list all tables, columns, types, constraints, and indexes.",
            "Compare the actual schema against docs/architecture/database-design.md; record every "
            "deviation.",
            "Run query analysis on the most common application queries and confirm index usage.",
            "Confirm no raw SQL interpolation exists that could enable SQL injection.",
            "Record all findings in docs/reports/database-validation.md.",
        ),
        outputs=("docs/reports/database-validation.md",),
        validation=(
            "Migration forward and rollback tests are documented with actual command output.",
            "Schema comparison against architecture document is complete.",
            "Index analysis covers all primary read paths.",
            "No SQL injection vulnerabilities are present.",
        ),
    ),
    _contract(
        "qa_and_testing",
        "QA and testing",
        "Verify acceptance criteria with reproducible automated and manual evidence.",
        prerequisites=("database_validation",),
        agent="qa_engineer",
        instructions=(
            "Run the approved test plan and map results to requirement IDs.",
            "Execute unit, integration, and end-to-end test suites.",
            "Test all user roles, flows, and edge cases defined in acceptance criteria.",
            "Document test failures with reproduction steps.",
        ),
        outputs=("docs/reports/qa-and-testing.md",),
    ),
    _contract(
        "security_testing",
        "Security testing",
        "Conduct a focused security review and penetration test of the integrated application, "
        "covering authentication, authorization, injection, data exposure, and dependency risks.",
        prerequisites=("qa_and_testing",),
        agent="security_reviewer",
        responsibilities=(
            "Test authentication flows for session fixation, brute-force exposure, "
            "and weak tokens.",
            "Test authorization for privilege escalation and horizontal access control failures.",
            "Test all input fields for SQL injection, XSS, CSRF, and command injection.",
            "Audit secrets management: no credentials in source, logs, or HTTP responses.",
            "Review all third-party dependencies for known CVEs.",
            "Test API endpoints for missing authentication, over-fetching, and mass assignment.",
        ),
        instructions=(
            "Read docs/architecture/security-architecture.md and use it as the security baseline.",
            "Test each authentication endpoint: login, logout, token refresh, password reset, "
            "and account lockout behavior.",
            "Test authorization: attempt to access resources of another user or with an expired "
            "or absent token; confirm all receive 401/403.",
            "Test all form inputs and URL parameters for injection: attempt SQL, XSS, and SSTI "
            "payloads and confirm they are sanitized.",
            "Inspect HTTP response headers: confirm Content-Security-Policy, X-Frame-Options, "
            "X-Content-Type-Options, and Strict-Transport-Security are present.",
            "Review package.json / pyproject.toml / composer.json for known vulnerable package "
            "versions using available audit tools.",
            "Audit .env handling: confirm secrets are never logged, committed, or returned in API "
            "responses.",
            "Document every finding with severity (Critical / High / Medium / Low), reproduction "
            "steps, evidence, and remediation recommendation.",
            "Re-test critical and high-severity findings after remediation and confirm resolution.",
        ),
        outputs=(
            "docs/reports/security-testing.md",
            "docs/reports/security-remediation.md",
        ),
        validation=(
            "All authentication and authorization controls are tested with documented evidence.",
            "Injection testing covers SQL, XSS, and CSRF at minimum.",
            "Dependency audit is complete with identified CVEs and remediation status.",
            "Every critical and high finding has a confirmed remediation status.",
        ),
        completion=(
            "Security testing report and remediation log are registered with SHA-256 digests.",
            "No unresolved critical or high severity findings remain.",
        ),
    ),
    _contract(
        "code_review",
        "Code review",
        "Review correctness, maintainability, and dependency hygiene.",
        prerequisites=("security_testing",),
        agent="security_reviewer",
        instructions=(
            "Review code correctness, error handling, and test coverage.",
            "Identify dead code, overly complex logic, and missing documentation.",
        ),
        outputs=("docs/reports/code-review.md",),
    ),
    _contract(
        "docker_and_ci_cd_validation",
        "Docker and CI/CD validation",
        "Validate reproducible builds, containers, and delivery automation.",
        prerequisites=("code_review",),
        agent="devops_engineer",
        instructions=(
            "Validate only integrations in project scope; do not deploy without approval.",
            "Confirm Docker builds succeed and containers start correctly.",
            "Validate CI pipeline configuration and test execution.",
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
        "schema_version": 5,
        "execution_model": "ide_agent",
        "stages": [contract.as_dict() for contract in CONTRACTS],
    }
