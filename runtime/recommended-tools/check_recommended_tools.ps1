$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'check_recommended_tools.py'
try {
    python $scriptPath @args
    $status = $LASTEXITCODE
} catch {
    $status = 1
}
if ($args.Count -gt 0 -and $args[0] -eq 'hook') {
    exit 0
}
exit $status
