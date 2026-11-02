# Agentic Development Framework

Agentic Development Framework (ADF) is a local-first foundation for persistent,
human-controlled software development workflows driven through IDE coding agents.

The project is being delivered incrementally. The current implementation provides the
installable package, strict configuration validation, structured logging, safe project
initialization, immutable requirements versioning, SQLite workflow state, recovery checkpoints,
lifecycle commands, and Codex/Antigravity project configuration.

## Requirements

- Python 3.11 or newer

## Installation

The first PyPI release is prepared but has not been published yet. Until it is available, install
from a checked-out repository:

```bash
python -m pip install .
adt --help
```

After release, the installation command will be:

```bash
python -m pip install agentic-development-framework
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
adt start
adt status
adt pause
adt resume
adt continue
adt stop
adt review
adt approve requirements_review
adt revise requirements_review "Clarify the acceptance criteria"
adt tasks
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

## Runtime state and recovery

Initialization creates `.agentic/database/agentic.db` as the transactional source of truth,
inspection snapshots under `.agentic/state/`, a JSONL event history, and checkpoint storage.
Pause and stop persist checkpoints. Resume verifies checkpoint integrity and restores the
checkpoint stage instead of trusting potentially inconsistent conversational context or snapshot
files. Mandatory workflow approval stages cannot advance until approval is recorded.

## IDE configuration

ADF generates root `AGENTS.md`, a shared command skill under
`.agents/skills/agentic-commands/`, and Antigravity rules under `.agents/rules/`. The Codex adapter
uses the documented root instructions and repository-local skill surfaces. The `.codex/agents/`
directory contains an informational compatibility note; ADF does not claim an undocumented
custom-agent file format is automatically discovered.

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
