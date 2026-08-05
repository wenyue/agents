: << 'CMDBLOCK'
@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0check_recommended_tools.ps1" %*
exit /b %ERRORLEVEL%
CMDBLOCK
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec sh "${SCRIPT_DIR}/check_recommended_tools.sh" "$@"
