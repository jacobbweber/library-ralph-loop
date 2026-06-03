#!/usr/bin/env pwsh
# Search the library metadata and files efficiently
# Usage: ./search_library.ps1 -Tag "python"

param(
    [string]$Dir = "dev/library",
    [string]$Tag = $null,
    [string]$Category = $null,
    [string]$Type = $null,
    [string]$Query = $null,
    [string]$Output = "json" # json or table
)

$WORKSPACE = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$targetDir = Join-Path $WORKSPACE $Dir

if (-not (Test-Path $targetDir)) {
    Write-Error "Directory $targetDir does not exist."
    exit 1
}

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
                        foreach ($v in $listVals) {
                            $cleanVals += $v.Trim().Trim('"', "'")
                        }
                        $metadata[$key] = $cleanVals
                    } elseif (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
                        $metadata[$key] = $val.Substring(1, $val.Length - 2)
                    } else {
                        $metadata[$key] = $val
                    }
                }
            }
            return $metadata
        }
    } catch {
        Write-Warning "Failed parsing YAML in $filePath : $_"
    }
    return $null
}

$results = @()
$files = Get-ChildItem -Path $targetDir -Filter "*.md" -Recurse

foreach ($file in $files) {
    $metadata = Parse-YamlFrontMatter $file.FullName
    if (-not $metadata) { continue }
    
    $matched = $true
    
    if ($Type -and $metadata["type"] -ne $Type) {
        $matched = $false
    }
    
    if ($Tag) {
        $tags = @()
        if ($metadata["tags"] -is [array]) {
            foreach ($t in $metadata["tags"]) { $tags += $t.ToLower() }
        } elseif ($metadata["tags"]) {
            $tags += $metadata["tags"].ToString().ToLower()
        }
        if (-not ($tags -contains $Tag.ToLower())) {
            $matched = $false
        }
    }
    
    if ($Category) {
        $categories = @()
        if ($metadata["categories"] -is [array]) {
            foreach ($c in $metadata["categories"]) { $categories += $c.ToLower() }
        } elseif ($metadata["categories"]) {
            $categories += $metadata["categories"].ToString().ToLower()
        }
        if (-not ($categories -contains $Category.ToLower())) {
            $matched = $false
        }
    }
    
    if ($Query) {
        $q = $Query.ToLower()
        $title = ($metadata["title"] ? $metadata["title"] : $file.BaseName).ToLower()
        $summary = ($metadata["summary"] ? $metadata["summary"] : "").ToLower()
        
        $content = Get-Content -Raw -Path $file.FullName
        $contentMatch = $content.ToLower().Contains($q)
        
        if (-not ($title.Contains($q) -or $summary.Contains($q) -or $contentMatch)) {
            $matched = $false
        }
    }
    
    if ($matched) {
        # Resolve relative path using POSIX style
        $relPath = $file.FullName.Substring($WORKSPACE.Length + 1).Replace("\", "/")
        
        $results += [PSCustomObject]@{
            path     = $relPath
            title    = ($metadata["title"] ? $metadata["title"] : $file.BaseName)
            type     = ($metadata["type"] ? $metadata["type"] : "unknown")
            tags     = ($metadata["tags"] ? $metadata["tags"] : @())
            categories = ($metadata["categories"] ? $metadata["categories"] : @())
            summary  = ($metadata["summary"] ? $metadata["summary"] : "No summary provided.")
            modified = ($metadata["modified"] ? $metadata["modified"] : "")
        }
    }
}

if ($Output -eq "json") {
    $results | ConvertTo-Json -Depth 5
} else {
    if ($results.Count -eq 0) {
        Write-Host "No matching files found."
        return
    }
    
    Write-Host "| Title | Path | Type | Tags | Summary |"
    Write-Host "|---|---|---|---|---|"
    foreach ($r in $results) {
        $tagsStr = $r.tags -join ", "
        # Generate clean link
        $urlPath = $r.path
        Write-Host "| $($r.title) | [$urlPath](file:///$($WORKSPACE.Replace('\','/'))/$urlPath) | $($r.type) | $tagsStr | $($r.summary) |"
    }
}
