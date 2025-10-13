# .local_env.ps1
# Load environment variables from .env and set up project environment

# Resolve project root
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Add src folder to PYTHONPATH
$SrcPath = Join-Path $ProjectRoot "src"
[System.Environment]::SetEnvironmentVariable("PYTHONPATH", $SrcPath, "Process")

# Set GRPC verbosity
[System.Environment]::SetEnvironmentVariable("GRPC_VERBOSITY", "NONE", "Process")

# Load .env file
$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    Write-Host "Loading environment variables from .env..."
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^\s*#") { return } # Skip comments
        if ($_ -match "^\s*$") { return } # Skip empty lines
        $parts = $_ -split "=", 2
        if ($parts.Length -eq 2) {
            $name = $parts[0].Trim()
            $value = $parts[1].Trim()
            Write-Host "Setting $name"
            Set-Item -Path "Env:$name" -Value $value
        }
    }
} else {
    Write-Warning ".env file not found at $EnvFile"
}

Write-Host "Environment loaded for SophGenV3"