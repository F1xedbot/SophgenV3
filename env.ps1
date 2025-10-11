# env.ps1
# Setup environment for SophGenV3
# Add src folder to PYTHONPATH
$env:PYTHONPATH = "$PWD\src"
$env:GRPC_VERBOSITY = "NONE"
Write-Host "Environment loaded for SophGenV3"