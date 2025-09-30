param()
$ErrorActionPreference = "Stop"

# Activate the virtual environment
$venvActivate = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
} else {
    Write-Error "Could not find the virtual environment activation script at $venvActivate"
}

# Ensure the rules index is built before starting
Write-Host "Building knowledge base index..."
python -m app.knowledge.ingest

# FIX: Launch the Streamlit application instead of running tests
Write-Host "Launching Streamlit UI... Open the URL in your browser. (Stop with Ctrl+C)"
python -m streamlit run app/ui/streamlit_app.py --server.headless true
