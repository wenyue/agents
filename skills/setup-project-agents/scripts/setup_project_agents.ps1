$ErrorActionPreference = 'Stop'
$workflow = Join-Path $PSScriptRoot 'workflow.py'
python $workflow @args
exit $LASTEXITCODE
