#!/usr/bin/env pwsh
# Rebuild Library Catalog Index
# Usage: ./cataloger.ps1

param(
    [string]$Dir = "dev/library"
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
                        foreach ($v in $listVals) { $cleanVals += $v.Trim().Trim('"', "'") }
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
    } catch {}
    return $null
}

$nodes = @()
$links = @()
$tagsMap = @{}
$categoriesMap = @{}
$typesMap = @{}
$notesData = @{}

$files = Get-ChildItem -Path $targetDir -Filter "*.md" -Recurse

# Parse metadata
foreach ($file in $files) {
    $relPath = $file.FullName.Substring($WORKSPACE.Length + 1).Replace("\", "/")
    
    # Skip writing the index itself
    if ($relPath.EndsWith("/index.md")) { continue }
    
    $metadata = Parse-YamlFrontMatter $file.FullName
    if (-not $metadata) { continue }
    
    $title = ($metadata["title"] ? $metadata["title"] : $file.BaseName)
    $noteType = ($metadata["type"] ? $metadata["type"] : "unknown")
    $summary = ($metadata["summary"] ? $metadata["summary"] : "No summary.")
    $status = ($metadata["status"] ? $metadata["status"] : "draft")
    
    $tags = @()
    if ($metadata["tags"] -is [array]) { $tags = $metadata["tags"] }
    elseif ($metadata["tags"]) { $tags += $metadata["tags"].ToString() }
    
    $categories = @()
    if ($metadata["categories"] -is [array]) { $categories = $metadata["categories"] }
    elseif ($metadata["categories"]) { $categories += $metadata["categories"].ToString() }
    
    $notesData[$relPath] = @{
        title      = $title
        type       = $noteType
        tags       = $tags
        categories = $categories
        summary    = $summary
        status     = $status
        links      = @()
    }
    
    # Populate mapping groupings
    foreach ($t in $tags) {
        if (-not $tagsMap.ContainsKey($t)) { $tagsMap[$t] = @() }
        $tagsMap[$t] += $relPath
    }
    foreach ($c in $categories) {
        if (-not $categoriesMap.ContainsKey($c)) { $categoriesMap[$c] = @() }
        $categoriesMap[$c] += $relPath
    }
    if (-not $typesMap.ContainsKey($noteType)) { $typesMap[$noteType] = @() }
    $typesMap[$noteType] += $relPath
    
    $nodes += @{
        id     = $relPath
        title  = $title
        type   = $noteType
        tags   = $tags
        summary = $summary
        status = $status
    }
}

# Resolve Links
foreach ($key in $notesData.Keys) {
    $noteInfo = $notesData[$key]
    $content = Get-Content -Raw -Path (Join-Path $WORKSPACE $key)
    
    $foundLinks = [regex]::Matches($content, '\]\((?:file:///)?([^\)]+\.md)\)')
    foreach ($fl in $foundLinks) {
        $linkClean = ($fl.Groups[1].Value -split "#")[0].Trim()
        $targetPosix = $linkClean
        
        if (-not ($targetPosix.StartsWith("dev/") -or $targetPosix.StartsWith("prod/"))) {
            $noteDir = Split-Path $key
            $targetPathResolved = [System.IO.Path]::GetFullPath((Join-Path $WORKSPACE (Join-Path $noteDir $targetPosix)))
            try {
                $targetPosix = $targetPathResolved.Substring($WORKSPACE.Length + 1).Replace("\", "/")
            } catch { continue }
        }
        
        if ($notesData.ContainsKey($targetPosix) -and $targetPosix -ne $key) {
            $links += @{
                source = $key
                target = $targetPosix
                type   = "references"
            }
            $noteInfo.links += $targetPosix
        }
    }
}

# Save network_index.json
$networkPath = Join-Path $targetDir "network_index.json"
$nodesObj = @()
foreach ($n in $nodes) { $nodesObj += [PSCustomObject]$n }
$linksObj = @()
foreach ($l in $links) { $linksObj += [PSCustomObject]$l }
@{ nodes = $nodesObj; links = $linksObj } | ConvertTo-Json -Depth 5 | Set-Content -Path $networkPath -Encoding utf8
Write-Host "Cataloger: Saved programmatic graph to dev/library/network_index.json"

# Write human-readable index.md
$indexPath = Join-Path $targetDir "index.md"
$md = @()
$md += "---"
$md += "id: `"system_index`""
$md += "title: `"Library Catalog Index`""
$md += "type: `"system_doc`""
$md += "tags: [`"index`", `"catalog`", `"system`"]"
$md += "status: `"stable`""
$md += "summary: `"Automated Master Index of the Library files.`""
$md += "---"
$md += "`n# Library Master Index Catalog`n"
$md += "*This index is automatically rebuilt by ``cataloger.ps1``.*"
$md += "`nTotal Cataloged Notes: **$($nodes.Count)**`n"

# 1. Categories
$md += "## 📁 Grouped by Category`n"
if ($categoriesMap.Keys.Count -eq 0) {
    $md += "*No categories classified yet.*`n"
}
foreach ($category in ($categoriesMap.Keys | Sort-Object)) {
    $md += "### $($category.Substring(0,1).ToUpper() + $category.Substring(1))"
    foreach ($p in ($categoriesMap[$category] | Sort-Object)) {
        $info = $notesData[$p]
        # Use POSIX forward slashes for clickability
        $md += "- **[$($info.title)](file:///$($WORKSPACE.Replace('\','/'))/$p)** ($($info.type)) — *$($info.summary)*"
    }
    $md += ""
}

# 2. Note Types
$md += "## 📝 Grouped by Document Type`n"
foreach ($ntype in ($typesMap.Keys | Sort-Object)) {
    $md += "### $($ntype.ToUpper())"
    foreach ($p in ($typesMap[$ntype] | Sort-Object)) {
        $info = $notesData[$p]
        $md += "- **[$($info.title)](file:///$($WORKSPACE.Replace('\','/'))/$p)** — *$($info.summary)*"
    }
    $md += ""
}

# 3. Tags
$md += "## 🏷️ Popular Tags`n"
if ($tagsMap.Keys.Count -eq 0) {
    $md += "*No tags applied yet.*`n"
} else {
    # Sort tags by note count desc
    $sortedTags = $tagsMap.Keys | ForEach-Object {
        [PSCustomObject]@{ Tag = $_; Count = $tagsMap[$_].Count }
    } | Sort-Object Count -Descending
    
    foreach ($st in $sortedTags) {
        $pathsLinks = @()
        foreach ($p in ($tagsMap[$st.Tag] | Sort-Object)) {
            $info = $notesData[$p]
            $pathsLinks += "[$($info.title)](file:///$($WORKSPACE.Replace('\','/'))/$p)"
        }
        $linksJoined = $pathsLinks -join ", "
        $md += "- **#$($st.Tag)** ($($st.Count)): $linksJoined"
    }
    $md += ""
}

$md -join "`n" | Set-Content -Path $indexPath -Encoding utf8
Write-Host "Cataloger: Saved human catalog index to dev/library/index.md"
