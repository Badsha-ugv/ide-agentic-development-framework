# Agentic Development Framework

Agentic Development Framework (ADF) is a local-first foundation for persistent,
human-controlled software development workflows driven through IDE coding agents.

The project is being delivered incrementally. The current implementation provides the
installable package, strict configuration validation, structured logging, safe project
initialization, immutable requirements versioning, SQLite workflow state, recovery checkpoints,
lifecycle commands, structured stage execution contracts, artifact validation, approval history,
Codex/Antigravity project configuration, and a browser-verified frontend-first delivery workflow.

## Requirements

- Python 3.11 or newer

## Installation

Install the latest released version from PyPI:

```bash
python -m pip install agentic-development-framework
adt --help
```

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

## CLI

Both entry points expose the same application:

```bash
adt --help
python -m agentic_framework --help
adt --version
adt init
adt config validate path/to/config.yaml
adt requirements ingest
adt requirements screenshots
adt start
adt status
adt pause
adt resume
adt continue
adt stage show
adt stage task "custom stage-scoped task"
adt artifact register docs/discovery/project-overview.md
adt artifact list
adt stage complete
adt stage fail --blocked "Clarification required"
adt stop
adt review
adt approve requirements_review
adt revise requirements_review "Clarify the acceptance criteria"
adt tasks
adt command create verify-api "Run the current-stage API checks"
adt command list
```

The validation command prints the normalized configuration as YAML and exits with code 2
for missing, malformed, or invalid configuration.

## Project initialization

Run `adt init` or `python -m agentic_framework init` from the project directory. Initialization:

- detects new and existing projects, common technologies, package managers, and parent Git roots;
- creates the ADF runtime, requirements, documentation, and IDE discovery directories;
- installs initial configuration and project guidance without replacing existing files;
- writes proposed content under `.agentic/proposals/` when a generated file conflicts; and
- initializes Git only when no repository is already present.

Use `--path DIRECTORY` to target another directory or `--no-git` to suppress Git initialization.
The operation is idempotent. Its latest report is written to
`.agentic/reports/initialization.md`.

## Requirements management

Add one or more source files below `requirements/inbox/`, including files in nested folders,
then run:

```bash
adt requirements ingest
```

Each changed submission creates the next directory under `requirements/versions/`. The version
contains byte-for-byte source copies, SHA-256 hashes, a manifest, consolidated extracted text, a
requirement index, and initial traceability records. Existing versions are hash-validated before
use and are never updated. An unchanged inbox is reported as a duplicate without creating a new
version.

Starting with the second version, ADF compares source files and `REQ-NNN` requirement blocks and
writes an impact report under `requirements/reports/`. Added, modified, removed, and unchanged
items are reported separately, along with documentation, architecture, implementation, testing,
and approval review prompts.

Markdown, text, CSV, TSV, JSON, YAML, and reStructuredText are extracted as UTF-8 text. Other
formats—including PDF, DOCX, XLSX, and images—are still preserved exactly and recorded with a
clear unsupported-extraction status. Optional binary-format extractors are future work.

See `docs/REQUIREMENTS_MANAGEMENT.md` for the file contract and safety behavior.

Place PNG, JPG, JPEG, or WEBP design references anywhere below `requirements/screenshots/` and
run `adt requirements screenshots`. ADF recursively catalogs them, preserves immutable reference
revisions, records dimensions and contextual folder hints, and updates
`docs/ui-ux/screenshot-reference-analysis.md` without modifying originals. Requirements ingestion
also performs this synchronization.

## Frontend-first visual workflow

The `ui_ux_design` stage now builds the complete production frontend—there is no disposable design
prototype. It accepts a Figma URL from requirements, recursively discovered screenshots, a generated
design direction, or a combination. Before implementation it verifies the chosen frontend stack,
package manager, runtime, dependencies, and production build. The result must be modern, accessible,
responsive, fully interactive, and visually faithful to supplied references without unapproved
deviations.

The following `design_review` stage reviews the actual frontend and always waits for explicit human
approval. Revisions update that production frontend. Backend implementation begins only afterward,
followed by frontend/backend API integration. See
[`docs/UI_UX_WORKFLOW.md`](docs/UI_UX_WORKFLOW.md).

## Runtime state and recovery

Initialization creates `.agentic/database/agentic.db` as the transactional source of truth,
inspection snapshots under `.agentic/state/`, a JSONL event history, and checkpoint storage.
Pause and stop persist checkpoints. Resume verifies checkpoint integrity and restores the
checkpoint stage instead of trusting potentially inconsistent conversational context or snapshot
files. Execution status, current task, attempts, errors, blockers, registered artifact hashes,
approvals, and revisions survive IDE and computer restarts. Mandatory workflow approval stages
cannot advance until approval is recorded.

`adt start` and `adt continue` prepare the current stage; they do not pretend that an AI task was
completed and never silently skip deliverables. The IDE agent performs reasoning and file changes
using `.agentic/execution-contracts.yaml`. It registers each output with `adt artifact register`,
then uses `adt stage complete` to validate and advance. Review stages stop at
`awaiting_approval` until an explicit `adt approve` or `adt revise` operation. See
[`docs/WORKFLOW_ARCHITECTURE.md`](docs/WORKFLOW_ARCHITECTURE.md),
[`docs/COMMAND_REFERENCE.md`](docs/COMMAND_REFERENCE.md), and
[`docs/STAGE_EXECUTION.md`](docs/STAGE_EXECUTION.md).

## IDE configuration

ADF generates root `AGENTS.md`, command-named Antigravity skills under `.agents/skills/`, a shared
execution protocol under `.agents/skills/agentic-commands/`, and rules under `.agents/rules/`.
Antigravity indexes each skill as `/<skill-name>`, so `/continue` invokes the generated `continue`
skill and causes the IDE agent—not the terminal process—to execute the current stage. The Codex adapter
uses the documented root instructions and repository-local skill surfaces. The `.codex/agents/`
directory contains an informational compatibility note; ADF does not claim an undocumented
custom-agent file format is automatically discovered.

After `adt init` and `adt requirements ingest`, open the project root in Antigravity and type
`/continue`. Generated rules instruct the agent to load the current contract, perform project
discovery, create and register its four discovery documents, and persist a blocker instead of
fabricating missing answers. See [`docs/ANTIGRAVITY_SETUP.md`](docs/ANTIGRAVITY_SETUP.md) and
[`docs/APPROVALS_AND_REVISIONS.md`](docs/APPROVALS_AND_REVISIONS.md).

Use `/adf <request>` for an ad hoc request that must remain bound to the current stage and status.
To register a reusable project-specific slash command, run `adt command create NAME
"INSTRUCTIONS"`; `/NAME` then performs the same persisted-state and contract preflight. Because
Antigravity reserves `/resume` for its conversation feature, ADF checkpoint recovery is exposed as
`/adf-resume`.

For projects initialized by an earlier ADF version, upgrade the package and rerun `adt init`.
SQLite schema migration is automatic and additive. New managed files are created, while conflicts
with customized guidance are preserved as `.agentic/proposals/**/*.proposed` for manual review.

## Configuration

ADF configuration uses YAML and rejects unknown keys to catch mistakes early:

```yaml
schema_version: 1
project:
  name: example-project
  mode: auto
runtime:
  directory: .agentic
  log_level: INFO
ide:
  enabled:
    - codex
policies:
  allow_network: false
  allow_destructive_operations: false
```

Runtime directories must be project-relative and cannot contain parent-directory traversal.

## Logging

`configure_logging()` sets up readable console output and can additionally write a JSONL
event stream. Reconfiguration is idempotent and only replaces handlers managed by ADF.

See `docs/IMPLEMENTATION_PLAN.md` and `docs/IMPLEMENTATION_PROGRESS.md` for scope and status. The
maintainer release procedure is documented in `docs/PYPI_RELEASE.md`.
