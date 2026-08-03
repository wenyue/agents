$ErrorActionPreference = 'Stop'
$bootstrap = Join-Path $PSScriptRoot 'bootstrap.py'
python $bootstrap @args
exit $LASTEXITCODE
