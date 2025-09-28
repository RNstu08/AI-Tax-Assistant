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

### PR2 — Knowledge Base and Retriever

-   **Knowledge Base:** Curated rules are stored as YAML files in `knowledge/rules/de/`.
-   **Ingestion:** A script validates these rules and builds a searchable JSON index.
-   **Retriever:** An `InMemoryRetriever` provides fast, deterministic, year-aware search.

To build the index manually:
```powershell
python -m app.knowledge.ingest

#### **`scripts/run.ps1`**
Update this script to automatically build the index before running tests.
```powershell
param()
$ErrorActionPreference = "Stop"

# Activate the virtual environment
$venvActivate = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
} else {
    Write-Error "Could not find the virtual environment activation script at $venvActivate"
}

# Build rules index (idempotent)
Write-Host "Building knowledge base index..."
python -m app.knowledge.ingest

# Run tests
Write-Host "Running tests..."
pytest -q


### PR3 — Orchestrator and Stubbed End-to-End Flow

-   **Orchestrator:** A deterministic graph of agent nodes is defined in `app/orchestrator/graph.py`.
-   **Contracts:** `TurnState` and other Pydantic models define the data flow.
-   **Stubs:** The flow is fully runnable offline using a mock `GroqAdapter`.

To run a single turn programmatically:
```python
from app.orchestrator.graph import run_turn
result = run_turn(user_id="demo", user_text="I commute 30 km in 2025.")
print(result.answer_revised)
