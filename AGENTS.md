# Agent instructions

## Purpose

This repository implements the Agentic Development Framework described in `instruction.md`.
Keep the core provider-agnostic, local-first, persistent, safe, and incrementally verifiable.

## Engineering rules

- Support Python 3.11 and newer.
- Keep dependencies small and interfaces modular.
- Use Typer for CLI commands, Pydantic for validation, YAML for configuration, and pytest.
- Preserve unrelated user changes and inspect the working tree before edits.
- Never expose secrets, force-push, or perform destructive Git operations.
- Do not claim functionality is complete until its tests pass.
- Add focused tests with every behavioral change.
- Keep user-facing errors actionable and avoid leaking tracebacks for expected input errors.
- Do not begin a later implementation phase until the current phase tests pass.

## Source layout

- `src/agentic_framework/`: distributable framework code.
- `tests/`: unit, integration, and acceptance tests.
- `docs/`: architecture, plans, decisions, and progress.
- `framework/`: canonical assets added in later phases.

## Verification

Run before reporting a phase complete:

```bash
ruff check .
pytest
```

