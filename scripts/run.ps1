param()
# Stop script on any error
$ErrorActionPreference = "Stop"

# Activate the virtual environment
$venvActivate = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
} else {
    Write-Error "Could not find the virtual environment activation script at $venvActivate"
}

# Placeholder: In PR1, we just run tests to verify setup.
# In PR4, this will be replaced with 'streamlit run ...'
Write-Host "Running tests as a placeholder..."
pytest -q