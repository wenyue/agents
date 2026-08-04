$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'maintain_recommended_tools.py'
python $scriptPath @args
exit $LASTEXITCODE
