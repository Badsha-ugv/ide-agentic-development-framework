# Release acceptance report

Date: 2026-11-02

## Verdict

The requested Django + React acceptance slice passes. The complete first release is **not yet
ready** against the repository Definition of Done because the release blockers listed below are
outside the implemented slice.

## Environment and artifact

- Python: 3.14.4
- Package: `agentic_development_framework-0.1.0-py3-none-any.whl`
- Final wheel SHA-256: `3408c997c3b26a24999571a318f14664f31cc3b9c9082957faa5a2b8f48c36ad`
- Installation: clean virtual environment using the wheel and declared dependencies
- Project: disposable Django-style backend plus React frontend with npm lockfile

The disposable project is created under the operating-system temporary directory and removed
after the run. The repeatable harness is `scripts/release_acceptance.py`.

## Passed checks

- Wheel builds and contains the packaged `agentic-commands` skill.
- The canonical skill passes the Codex skill validator.
- The wheel installs into a clean virtual environment with declared dependencies.
- Both `adt init` and `python -m agentic_framework init` work from the external project.
- Repeated initialization creates zero additional generated files and preserves state.
- Nested Django, React/JavaScript, and npm markers are detected.
- Root Codex instructions and the repository-local command skill are generated.
- Antigravity persistent rules and the shared command skill are generated.
- Workflow, policies, and all eleven canonical agent definitions parse as YAML.
- Requirements inbox, versions, reports, source preservation, comparison, and impact reporting
  work through the installed CLI.
- SQLite schema version and required state tables are present.
- Workflow, task, and execution snapshots plus JSONL events are present.
- Start, status, continue, pause, resume, stop, review, approve, revise, requirements, tasks, and
  help commands are registered and covered by automated tests.
- Pause/resume and stop/resume work across separate CLI processes.
- Resume validates checkpoint integrity and restores the checkpoint stage.
- Mandatory approval gates block continuation until an approval is recorded.

## Critical findings fixed during review

1. Monorepo technology detection originally inspected only root-level markers. It now safely
   searches common markers in nested application folders while excluding runtime/vendor trees.
2. Resume originally trusted the current workflow row after validating a checkpoint. It now
   restores the verified checkpoint stage and rejects missing, corrupt, malformed, or unknown-stage
   checkpoints.
3. Invalid approval targets and blank revision feedback are now rejected.
4. SQLite connections owned by tests are closed cleanly; runtime connections were already scoped.
5. Codex generation no longer implies that an undocumented `.codex/agents/*.toml` format is
   portable or automatically discovered.
6. The acceptance harness now performs a real dependency-resolved wheel installation and surfaces
   child-process stdout/stderr on failure.

## Automated evidence

- Ruff: passed
- Pytest: 56 passed
- Branch-aware coverage: 90.65%
- Editor diagnostics: none
- Canonical skill validation: passed
- External wheel-installed acceptance harness: passed
- `git diff --check`: passed

## Remaining first-release blockers

- Implement safe Git operations beyond initialization, including working-tree guards and branch
  policy integration.
- Implement Docker detection/templates and GitHub Actions generation/validation.
- Generate and validate the VS Code agent-environment adapter.
- Implement task creation/dependency management and genuine sequential specialist execution rather
  than stage-only lifecycle transitions.
- Implement existing-project analysis reports and the design workflow boundary.
- Complete security review, example-project documentation, installation testing across the stated
  Python support range, and the final release checklist.
