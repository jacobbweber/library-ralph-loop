<#
run_librarian.ps1
Wrapper to run dev/tools/librarian.py --run-tests using a resolved interpreter from env_check.ps1
#>

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$envCheck = Join-Path $scriptDir "env_check.ps1"
if (-not (Test-Path $envCheck)) {
    Write-Error "env_check.ps1 not found in $scriptDir"
    exit 1
}

# Call env_check and capture the interpreter path
$pyPath = & $envCheck
if ($LASTEXITCODE -ne 0 -or -not $pyPath) {
    Write-Error "Failed to locate a usable Python interpreter. See errors above."
    exit 1
}

$librarian = Join-Path $scriptDir "librarian.py"
if (-not (Test-Path $librarian)) {
    Write-Error "librarian.py not found at $librarian"
    exit 1
}

Write-Host "Running librarian tests with interpreter: $pyPath" -ForegroundColor Cyan
& $pyPath $librarian --run-tests
exit $LASTEXITCODE
