$ErrorActionPreference = 'Stop'
$workflow = Join-Path $PSScriptRoot 'workflow.py'

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'
    if ($LASTEXITCODE -eq 0) {
        & py -3 $workflow @args
        exit $LASTEXITCODE
    }
}

$pythonCommands = @('python3', 'python') + @(
    Get-Command 'python3.*' -CommandType Application -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^python3\.\d+(?:\.exe)?$' } |
        Select-Object -ExpandProperty Source
)
foreach ($pythonCommand in $pythonCommands) {
    if (Get-Command $pythonCommand -ErrorAction SilentlyContinue) {
        & $pythonCommand -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'
        if ($LASTEXITCODE -eq 0) {
            & $pythonCommand $workflow @args
            exit $LASTEXITCODE
        }
    }
}

if (Get-Command uv -ErrorAction SilentlyContinue) {
    $pythonOutput = $null
    $uvExitCode = 1
    try {
        $pythonOutput = & uv python find '>=3.10' 2>$null
        $uvExitCode = $LASTEXITCODE
    }
    catch {
        $uvExitCode = 1
    }
    if ($uvExitCode -eq 0 -and $pythonOutput) {
        $pythonPath = "$pythonOutput".Trim()
        if ($pythonPath) {
            & $pythonPath $workflow @args
            exit $LASTEXITCODE
        }
    }
}

[Console]::Error.WriteLine('Python 3.10 or newer is required.')
exit 2
