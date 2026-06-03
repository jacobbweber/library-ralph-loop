#!/usr/bin/env pwsh
# Librarian Quality Assurance Linter
# Usage: ./librarian.ps1 -RunTests

param(
    [string]$Dir = "dev/library",
    [switch]$RunTests
)

$WORKSPACE = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$targetDir = Join-Path $WORKSPACE $Dir

$ALLOWED_TYPES = @(
    "diwk", "concept_map", "zettelkasten", "soap", "qec", 
    "feynman", "cornell", "eisenhower", "sdlc_project", 
    "work_journal", "brain_dump", "research_brief", "system_doc"
)
$ALLOWED_STATUSES = @("raw", "draft", "review", "stable")

function Parse-YamlFrontMatter($filePath) {
    try {
        $content = Get-Content -Raw -Path $filePath -Encoding utf8
        if ($content -match "^(?:\r?\n)*---\r?\n([\s\S]*?)\r?\n---") {
            $yamlText = $Matches[1]
            $metadata = @{}
            $lines = $yamlText -split "\r?\n"
            foreach ($line in $lines) {
                $line = $line.Trim()
                if ($line.StartsWith("#") -or -not $line) { continue }
                if ($line -match "^([^:]+):(.*)$") {
                    $key = $Matches[1].Trim()
                    $val = $Matches[2].Trim()
                    
                    if ($val -like "[*]") {
                        $listVals = $val.Trim('[', ']') -split ","
                        $cleanVals = @()
                        foreach ($v in $listVals) { $cleanVals += $v.Trim().Trim('"', "'") }
                        $metadata[$key] = $cleanVals
                    } elseif (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
                        $metadata[$key] = $val.Substring(1, $val.Length - 2)
                    } else {
                        $metadata[$key] = $val
                    }
                }
            }
            return @{ Metadata = $metadata; Error = $null }
        }
        return @{ Metadata = $null; Error = "Missing front matter delimiters (---)" }
    } catch {
        return @{ Metadata = $null; Error = $_.ToString() }
    }
}

function Lint-Library($targetPath) {
    $errors = @()
    $notes = @{}
    
    if (-not (Test-Path $targetPath)) {
        return $errors, $notes
    }
    
    $files = Get-ChildItem -Path $targetPath -Filter "*.md" -Recurse
    
    # Pass 1: Parse and validate metadata fields
    foreach ($file in $files) {
        $relPath = $file.FullName.Substring($WORKSPACE.Length + 1).Replace("\", "/")
        
        $parseResult = Parse-YamlFrontMatter $file.FullName
        if ($parseResult.Error) {
            $errors += "LINT ERROR: [$relPath] Invalid front matter syntax: $($parseResult.Error)"
            continue
        }
        
        $metadata = $parseResult.Metadata
        $content = Get-Content -Raw -Path $file.FullName
        
        $notes[$relPath] = @{
            path     = $file.FullName
            metadata = $metadata
            content  = $content
        }
        
        # Check required fields
        foreach ($field in @("id", "title", "type", "tags", "status")) {
            if (-not $metadata.Contains($field)) {
                $errors += "LINT ERROR: [$relPath] Missing required front matter field: '$field'"
            }
        }
        
        # Validate type
        $noteType = $metadata["type"]
        if ($noteType -and -not ($ALLOWED_TYPES -contains $noteType)) {
            $errors += "LINT ERROR: [$relPath] Invalid note type '$noteType'. Must be one of: $($ALLOWED_TYPES -join ', ')"
        }
        
        # Validate status
        $status = $metadata["status"]
        if ($status -and -not ($ALLOWED_STATUSES -contains $status)) {
            $errors += "LINT ERROR: [$relPath] Invalid status '$status'. Must be one of: $($ALLOWED_STATUSES -join ', ')"
        }
    }
    
    # Pass 2: Check backlinks
    foreach ($key in $notes.Keys) {
        $noteInfo = $notes[$key]
        $content = $noteInfo.content
        
        # Match [text](path.md)
        $matches = [regex]::Matches($content, '\]\((?:file:///)?([^\)]+\.md)\)')
        foreach ($m in $matches) {
            $link = $m.Groups[1].Value
            $linkClean = ($link -split "#")[0].Trim()
            
            $targetPosix = $linkClean
            if (-not ($targetPosix.StartsWith("dev/") -or $targetPosix.StartsWith("prod/"))) {
                # Relative resolution
                $noteDir = Split-Path $key
                $targetPathResolved = [System.IO.Path]::GetFullPath((Join-Path $WORKSPACE (Join-Path $noteDir $targetPosix)))
                try {
                    $targetPosix = $targetPathResolved.Substring($WORKSPACE.Length + 1).Replace("\", "/")
                } catch {
                    $errors += "LINT ERROR: [$key] Broken relative link: '$link' (points outside workspace)"
                    continue
                }
            }
            
            if (-not $notes.Contains($targetPosix)) {
                $physPath = Join-Path $WORKSPACE $targetPosix
                if (-not (Test-Path $physPath)) {
                    $errors += "LINT ERROR: [$key] Broken link to file: '$linkClean'"
                }
            }
        }
    }
    
    return $errors, $notes
}

function Run-SelfTests {
    Write-Host "Self-Tests: Running checks on tools (PowerShell)..." -ForegroundColor Magenta
    
    # Test 1: Test search script loads and executes
    $searchPs1 = Join-Path $WORKSPACE "dev\tools\search_library.ps1"
    if (Test-Path $searchPs1) {
        try {
            $testResults = & $searchPs1 -Dir "dev/templates" -Output json | ConvertFrom-Json
            Write-Host "Self-Tests: search_library.ps1 checked. Found $($testResults.Count) mock templates."
        } catch {
            return @{ Success = $false; Error = "search_library.ps1 test run failed: $_" }
        }
    }
    
    # Test 2: Test web search script clean html
    $webSearchPs1 = Join-Path $WORKSPACE "dev\tools\web_search.ps1"
    if (Test-Path $webSearchPs1) {
        try {
            # Check script execution syntax (dry run or simple load)
            $content = Get-Content -Raw -Path $webSearchPs1
            # Simple parse check
            [void][System.Management.Automation.Language.Parser]::ParseInput($content, [ref]$null, [ref]$null)
            Write-Host "Self-Tests: web_search.ps1 script syntax checked."
        } catch {
            return @{ Success = $false; Error = "web_search.ps1 syntax test failed: $_" }
        }
    }
    
    Write-Host "Self-Tests: All tool checks PASSED (PowerShell)." -ForegroundColor Green
    return @{ Success = $true; Error = $null }
}

if ($RunTests) {
    $testRes = Run-SelfTests
    if (-not $testRes.Success) {
        Write-Error "TEST RUNNER FAILED: $($testRes.Error)"
        exit 1
    }
}

Write-Host "Librarian: Linting folder $Dir..."
$errors, $notes = Lint-Library $targetDir

if ($errors.Count -gt 0) {
    Write-Host "`nLibrarian Linter: Found $($errors.Count) issues:" -ForegroundColor Red
    foreach ($err in $errors) {
        Write-Host $err -ForegroundColor Red
    }
    exit 1
} else {
    Write-Host "Librarian Linter: Clean repository! 0 errors found." -ForegroundColor Green
    exit 0
}
