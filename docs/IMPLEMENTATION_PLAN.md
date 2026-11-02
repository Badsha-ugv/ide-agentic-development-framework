# Implementation plan

The framework will be delivered in the ten phases defined by the product specification.
Each phase depends on passing verification for the preceding phase.

1. **Foundation** — package metadata, source layout, CLI entry point, validated configuration,
   logging, repository guidance, and unit tests.
2. **Project initialization** — safe and idempotent project discovery and file generation.
3. **Runtime and persistence** — SQLite state, repositories, events, checkpoints, and snapshots.
4. **Command system** — shared registry and lifecycle commands for CLI and chat adapters.
5. **Requirements management** — immutable source versions, extraction boundaries, comparison,
   impact reporting, and traceability.
6. **Agent and workflow system** — canonical contracts, configurable stages, dependencies,
   approval gates, and sequential execution fallback.
7. **IDE adapters** — verified Codex, Antigravity, and VS Code configuration generators.
8. **Engineering integrations** — safe Git wrapper, Docker detection/templates, CI templates,
   and documentation maintenance.
9. **Existing project and design workflows** — repository analysis, Figma boundary, prototype
   generation workflow, and implementation handoff.
10. **Acceptance and release** — end-to-end verification, security review, package builds,
    installation test, example project, and release documentation.

## Phase gates

At the end of every phase, run its tests and static checks, update progress documentation, and
record remaining work. A later phase must not start while current-phase verification is failing.

