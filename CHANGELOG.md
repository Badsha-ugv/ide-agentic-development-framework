# Changelog

All notable changes to this project will be documented in this file.

## 0.5.0 - 2026-11-08

### Added

- Interactive `adt init` workflow supporting both new and existing projects with terminal prompts.
- Existing-project domain detection scanning frontend, backend, database, auth, and CI completion.
- Session task selection for existing projects: `security_audit`, `bug_hunt`, `specific_issue`, `ui_redesign`, `add_feature`, or `full_workflow`.
- Automatic existing-project analysis reports generated during initialization: `.agentic/reports/existing-project-analysis.md`, `docs/discovery/existing-project-analysis.md`, and `docs/discovery/work-completion-status.md`.
- New stages: `existing_project_analysis`, `database_validation`, and `security_testing`.
- Expanded technology detection covering React, Vue, FastAPI, Flask, Laravel, NestJS, Go, Rust, PHP, Ruby, and Prisma.

### Changed

- Completely removed all UI/UX prototype concepts: the workflow directly builds the production frontend using chosen tech stack (React, Vue, etc.).
- Renamed stages to `frontend_implementation` and `frontend_review` with high-priority design standards: mandatory research into conventional sites similar to the project idea, comprehensive design system (colors, typography, spacing, motion), and zero generic placeholder styling.
- Richer agent context: expanded responsibilities, step-by-step instructions, and thorough cross-stage input traceability so agents have complete context.
- Workflow execution order: documentation → frontend implementation & review → backend planning & implementation → integration → database validation → QA & testing → security testing → code review → CI/CD → final documentation → release review.

## 0.4.0 - 2026-11-03

### Changed

- Removed disposable design-prototype step: the frontend stage verifies the toolchain and builds the complete production frontend before backend work begins.
- Figma links from requirements, recursively discovered screenshots, and generated frontend design remain supported with exact-reference, accessibility, interaction, responsive, and state checks.
- Workflow order updated to frontend implementation and approval, backend planning and implementation, then explicit frontend/backend API integration.

### Added

- Structured frontend implementation-manifest validation for environment, production build, actual registered source files, browser evidence, console errors, accessibility, and reference deviations.

## 0.3.0 - 2026-11-03

### Added

- Recursive PNG/JPG/JPEG/WEBP screenshot-reference discovery with dimensions, contextual hints,
  immutable byte-preserving revisions, tamper detection, and generated analysis inventory.
- `adt requirements screenshots` plus automatic screenshot synchronization during requirements
  ingestion and UI/UX stage preparation.
- Structured design-input and browser-verification evidence gates, versioned prototypes, and
  frontend design-reference traceability.

### Changed

- The existing UI/UX stages now treat the interactive prototype as the final visual source of
  truth, support Figma MCP, generated, and screenshot inputs together, and require desktop,
  tablet, mobile, interaction, revision, and explicit human-approval evidence.

## 0.2.0 - 2026-11-02

### Added

- Machine-readable IDE-agent stage execution contracts for all nineteen workflow stages.
- Persistent execution attempts, current tasks, blockers, errors, and explicit stage-completion
  commands.
- SHA-256 artifact validation, mandatory approval gates, revision feedback, and preserved review
  snapshots.
- Additive runtime schema migration plus Antigravity execution and recovery documentation.
- Command-named Antigravity workspace skills so `/continue` invokes IDE-agent execution rather
  than relying on rule interpretation alone.
- State-aware `/adf` requests, `/adf-resume`, and safe project-specific slash-command generation.

### Changed

- `adt continue` now prepares or resumes the current stage and cannot silently advance it.
- Project initialization completes its own stage and leaves project discovery pending for the IDE
  agent.
- Clean-install acceptance now validates generated Antigravity command skills and stage execution.

## 0.1.0 - 2026-11-02

### Added

- Initial package and CLI foundation.
- Validated YAML configuration models.
- Console logging and structured JSONL event logging.
- Phase 1 unit tests and project documentation.
- Safe, idempotent project initialization for new and existing repositories.
- Project, Git, technology, and package-manager discovery.
- Conflict proposals and human-readable initialization reports.
- Atomic, hash-verified requirements ingestion with immutable source versions.
- Requirement-ID traceability, duplicate detection, version comparison, and impact reports.
- Requirements management unit, integration, and acceptance coverage.
- SQLite runtime state, JSON snapshots, events, integrity-checked checkpoints, and recovery.
- Central lifecycle command registry with CLI and chat-command mappings.
- Canonical workflow, policy, and eleven-agent registry generation.
- Documented Codex skill/instructions and Antigravity rule generation.
- Wheel-installed Django + React release acceptance harness.
- Single-source package versioning and explicit wheel/source-distribution content rules.
- Installed-distribution resource and full-suite regression tests.
- Python 3.11–3.13 CI plus tag-only PyPI OIDC Trusted Publishing.
- Maintainer checklist for building, inspecting, testing, and publishing releases.

