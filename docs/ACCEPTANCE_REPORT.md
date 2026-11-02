# Release acceptance report

Date: 2026-11-02

## Verdict

The repository passes the local release gates for the `agentic-development-framework` 0.1.0
alpha release. No package was uploaded, no tag was created, and no remote repository state was
changed. The remaining work is maintainer review plus the external GitHub environment and PyPI
Trusted Publisher configuration documented in `PYPI_RELEASE.md`.

This verdict covers the functionality represented by the package and README. Unfinished items in
the broader framework roadmap remain explicitly marked incomplete in `IMPLEMENTATION_PROGRESS.md`.

## Artifacts and metadata

- Python used for local verification: 3.14.4
- Wheel: `agentic_development_framework-0.1.0-py3-none-any.whl` (31,613 bytes, 26 entries)
- Wheel SHA-256: `ed08bb8b3c408c43461da56a37481374f628acea1c73d8c110c32e8930e91394`
- Source distribution: `agentic_development_framework-0.1.0.tar.gz` (51 entries)
- Distribution/import/command: `agentic-development-framework` / `agentic_framework` / `adt`
- Version/Python: `0.1.0` / `>=3.11`
- Build backend: Hatchling 1.26 through 1.31, producing Core Metadata 2.4
- License: MIT (SPDX expression and packaged license file)

The wheel contains every Python module and the runtime command skill at
`agentic_framework/templates/skills/agentic-commands/SKILL.md`. Runtime YAML, policy, workflow,
agent-registry, Codex, and Antigravity files are deterministically generated from packaged Python
code. The source distribution contains source, tests, release scripts, documentation, changelog,
license, README, and build metadata.

Neither archive contains local `.agentic` state, SQLite databases, `.env` files, virtual
environments, caches, Git data, or nested build artifacts.

## Passed checks

- `ruff check .`: passed.
- Repository pytest suite: 58 passed with 90.65% branch-aware coverage.
- The same 58 tests imported the non-editable installed wheel from a disposable environment and
  passed with 90.65% coverage.
- `python -m build`: built the wheel and source distribution through isolated environments.
- `python -m twine check dist/*`: both artifacts passed.
- Editor diagnostics for changed Python, TOML, and workflow files: none.
- Wheel and source-distribution member inspection: passed.
- Secret, database, local-state, cache, virtual-environment, and nested-build exclusion scan:
  passed.

## Clean-install acceptance

Both the wheel and source distribution were separately installed into disposable, non-editable
virtual environments outside the repository. Each artifact passed:

- `adt --help`, `adt --version`, and `python -m agentic_framework --help`;
- valid generated configuration validation;
- initialization of a completely empty project;
- initialization of a representative existing Django + React project;
- Codex instructions, command skill, Antigravity rules, workflow, policies, and eleven-agent
  registry generation;
- SQLite schema and expected runtime-state generation;
- a second initialization with zero newly created files;
- preservation of a conflicting existing `AGENTS.md` and creation of a proposal;
- two requirements ingestions, immutable versions, comparison, and impact-report generation; and
- start, continue, pause, resume, stop, and recovery across CLI processes.

These projects lived under operating-system temporary directories and had no access to package
files through the repository source tree.

## Release automation

Normal CI runs lint, coverage-enforced tests on Python 3.11, 3.12, and 3.13, builds both artifacts,
validates them with Twine, runs installed-wheel tests, exercises wheel and source-distribution
acceptance, and uploads the artifacts.

The separate publish workflow triggers only for pushed `v*` tags. Its publish job depends on all
test and build gates, uses the protected `pypi` GitHub environment, grants `id-token: write` only
to that job, downloads the already-tested artifacts, and invokes
`pypa/gh-action-pypi-publish@release/v1` without a token or password.

## Issue fixed during packaging review

Hatchling 1.32 changed its default to Core Metadata 2.5, which Twine 6.2 rejects. The build-system
requirement is intentionally constrained to `hatchling>=1.26,<1.32`; Hatchling 1.31 produces Core
Metadata 2.4, preserves SPDX license metadata, and passes Twine. This can be relaxed after the
release toolchain supports Metadata 2.5.
