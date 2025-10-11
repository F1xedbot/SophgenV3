# Resolve the current script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Set src folder to PYTHONPATH and other env vars
$env:PYTHONPATH = Join-Path $ScriptDir "src"
$env:GRPC_VERBOSITY = "NONE"

Write-Host "Environment loaded for SophGenV3"

# Start FastAPI app via uvicorn
uvicorn src.app:app --reload --host 127.0.0.1 --port 3008 --env-file .env
