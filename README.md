# DE Tax Assistant (MVP scaffold)

This is the baseline scaffold for a German employee deductions assistant (DE 2024–2025).

## What works in PR1
- Clean repo with linting/formatting/type-checking/tests on Windows + Linux
- Money helpers (Decimal-safe), year constants, config and logging stubs
- Memory store interface skeleton
- Basic unit tests

## Quickstart (Windows PowerShell)

1.  Create virtual env and install dev deps:
    ```powershell
    scripts\setup.ps1
    ```

2.  Run tests:
    ```powershell
    pytest -q
    ```

3.  Lint, format, type-check:
    ```powershell
    ruff check .
    black --check .
    mypy .
    ```