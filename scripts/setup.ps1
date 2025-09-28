param()
# Stop script on any error
$ErrorActionPreference = "Stop"

# Create virtual environment if it doesn't exist
if (!(Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment in ./.venv..."
    python -m venv .venv
}

# Activate the virtual environment for this script's session
$venvActivate = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
} else {
    Write-Error "Could not find the virtual environment activation script at $venvActivate"
}

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "Installing dependencies from requirements-dev.txt..."
pip install -r requirements-dev.txt

# --- ADD THIS LINE ---
Write-Host "Installing project in editable mode..."
pip install -e .
# --------------------

Write-Host "Installing pre-commit hooks..."
pre-commit install

Write-Host "✅ Setup complete. To activate the environment in a new shell, run: .\.venv\Scripts\Activate.ps1"
