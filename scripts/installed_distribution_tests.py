"""Run the repository test suite against a non-editable built distribution."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def test_distribution(artifact: Path, repository: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="adf-installed-tests-") as temporary:
        root = Path(temporary)
        environment = root / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
        python = environment / "bin" / "python"
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                f"{artifact.resolve()}[dev]",
            ],
            cwd=root,
        )
        shutil.copytree(repository / "tests", root / "tests")
        _run(
            [
                str(python),
                "-m",
                "pytest",
                "tests",
                "--strict-markers",
                "--cov=agentic_framework",
                "--cov-branch",
                "--cov-report=term-missing",
                "--cov-fail-under=90",
            ],
            cwd=root,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    arguments = parser.parse_args()
    test_distribution(arguments.artifact, arguments.repository.resolve())


if __name__ == "__main__":
    main()
