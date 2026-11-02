# PyPI release procedure

This project publishes the `agentic-development-framework` distribution from
`Badsha-ugv/ide-agentic-development-framework`. The import package is `agentic_framework`, the
command is `adt`, and production publishing is restricted to `.github/workflows/publish.yml`.
The workflow uses PyPI Trusted Publishing; it does not use a repository secret or long-lived PyPI
API token.

## One-time Trusted Publishing setup

1. In the GitHub repository, open **Settings → Environments → New environment** and create an
   environment named `pypi`. Add required reviewers or deployment protection rules as desired.
2. For a first release, open <https://pypi.org/manage/account/publishing/> and create a pending
   publisher with these exact values:
   - PyPI project name: `agentic-development-framework`
   - Owner: `Badsha-ugv`
   - Repository: `ide-agentic-development-framework`
   - Workflow: `publish.yml`
   - Environment: `pypi`
3. If the project already exists on PyPI, configure the same publisher under the project's
   **Publishing** settings instead.
4. Do not create `PYPI_TOKEN`, `PYPI_API_TOKEN`, or password secrets. The publish job receives only
   the short-lived GitHub OIDC identity permission.

## Update the version

The single version source is `src/agentic_framework/__init__.py`. Update `__version__`, update
`CHANGELOG.md`, and ensure the tag will be exactly `v<version>`. Hatchling reads package metadata
from this file, so there is no second version value to synchronize in `pyproject.toml`.

Confirm the resolved version:

```bash
python -c "import agentic_framework; print(agentic_framework.__version__)"
adt --version
```

## Build and inspect locally

From a clean working tree and an activated Python 3.11-or-newer environment:

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest --cov=agentic_framework --cov-branch --cov-report=term-missing --cov-fail-under=90
python -m build
python -m twine check dist/*
python -m zipfile -l dist/agentic_development_framework-*.whl
tar -tzf dist/agentic_development_framework-*.tar.gz
```

The wheel must include `agentic_framework/templates/skills/agentic-commands/SKILL.md`. Neither
archive may include `.env` files, virtual environments, caches, local SQLite databases, or local
project state.

## Test the built distributions

The repository scripts create temporary virtual environments outside the source tree and install
non-editable artifacts:

```bash
python scripts/installed_distribution_tests.py dist/agentic_development_framework-*.whl
python scripts/release_acceptance.py dist/agentic_development_framework-*.whl
python scripts/release_acceptance.py dist/agentic_development_framework-*.tar.gz
```

For a manual smoke test:

```bash
release_tmp="$(mktemp -d)"
python -m venv "$release_tmp/venv"
"$release_tmp/venv/bin/python" -m pip install dist/agentic_development_framework-*.whl
mkdir "$release_tmp/project"
cd "$release_tmp/project"
"$release_tmp/venv/bin/adt" --version
"$release_tmp/venv/bin/adt" init --no-git
```

## Create the release

Review the complete diff and confirm CI on `main` is green. Then create and push the tag manually:

```bash
git switch main
git pull --ff-only
git status --short
git tag -s v0.2.0 -m "Release 0.2.0"
git push origin v0.2.0
```

Use an annotated unsigned tag (`git tag -a`) only if signed tags are not available. Do not reuse a
published version or move a release tag. A pushed `v*` tag starts the publish workflow; tests,
linting, artifact builds, Twine validation, installed-distribution tests, and acceptance checks
must all pass before the OIDC publishing job can run.

## Verify the release

1. Confirm all jobs in the **Publish to PyPI** workflow succeeded and the GitHub `pypi`
   environment recorded the deployment.
2. Inspect <https://pypi.org/project/agentic-development-framework/> and verify version, README,
   license, Python requirement, project links, wheel, and source distribution.
3. Install from PyPI into another clean environment:

   ```bash
   verify_tmp="$(mktemp -d)"
   python -m venv "$verify_tmp/venv"
   "$verify_tmp/venv/bin/python" -m pip install agentic-development-framework==0.2.0
   "$verify_tmp/venv/bin/adt" --version
   "$verify_tmp/venv/bin/adt" --help
   ```

For later releases, update the single version source and changelog, repeat all local checks, merge
through CI, and push a new immutable `v<version>` tag. PyPI files and versions cannot be replaced.
