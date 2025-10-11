# Resolve the current script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Load environment variables
$EnvScript = Join-Path $ScriptDir "env.ps1"
if (Test-Path $EnvScript) {
    Write-Host "Loading environment from env.ps1..."
    . $EnvScript
} else {
    Write-Warning "env.ps1 not found. Continuing without it."
}

# Start FastAPI app with uvicorn
Write-Host "Starting FastAPI app..."
uvicorn src.app:app --reload --host 127.0.0.1 --port 3008