# env_check.ps1
# Ralph Loop Environment Verification Script
# Checks for Python 3.8+ availability and PATH configuration.

$ErrorActionPreference = "Stop"
Write-Host "=== Ralph Loop Environment Check ===" -ForegroundColor Cyan
Write-Host "Checking Python availability..." -ForegroundColor Gray

try {
    # Attempt to find python in PATH
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonPath = $pythonCmd.Source
        Write-Host "[OK] Python executable found at: $pythonPath" -ForegroundColor Green
        
        # Check version
        $versionOutput = & python --version 2>&1
        Write-Host "[OK] Python Version: $versionOutput" -ForegroundColor Green
        
        # Verify minimum version (3.8)
        $versionString = $versionOutput -replace "Python ", ""
        $major, $minor = $versionString.Split('.')
        if ([int]$major -ge 3 -and [int]$minor -ge 8) {
            Write-Host "[PASS] Environment is ready for Ralph Loop tools." -ForegroundColor Green
            exit 0
        } else {
            Write-Host "[FAIL] Python version $versionString is installed, but Ralph Loop requires 3.8+." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[FAIL] Python not found in system PATH." -ForegroundColor Red
        Write-Host "Please install Python 3.8+ and ensure 'python' is added to your PATH environment variable." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "[ERROR] Environment check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
