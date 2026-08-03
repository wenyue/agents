$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'sync_public_agent_assets.py'
python $scriptPath @args
exit $LASTEXITCODE
