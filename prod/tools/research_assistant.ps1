#!/usr/bin/env pwsh
# Research Assistant for compiling web search briefs
# Usage: ./research_assistant.ps1 -Query "Ollama API setup instructions"

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Query
)

$WORKSPACE = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$webSearchPs1 = Join-Path $WORKSPACE "dev\tools\web_search.ps1"

if (-not (Test-Path $webSearchPs1)) {
    Write-Error "Research Assistant Error: dev/tools/web_search.ps1 not found."
    exit 1
}

Write-Host "Research Assistant: Querying web search for '$Query'..." -ForegroundColor Magenta

try {
    # Run search script and output JSON
    $searchJson = & $webSearchPs1 -Query $Query -Output json
    $results = ConvertFrom-Json $searchJson
} catch {
    Write-Error "Research Assistant Error executing search: $_"
    exit 1
}

if ($null -eq $results -or $results.Count -eq 0) {
    Write-Host "Research Assistant: No search results returned." -ForegroundColor Yellow
    exit 1
}

# Clean filename
$cleanName = ""
foreach ($char in $Query.ToLower().ToCharArray()) {
    if ([char]::IsLetterOrDigit($char)) {
        $cleanName += $char
    } else {
        $cleanName += "_"
    }
}
$cleanName = ($cleanName -replace "_+", "_").Trim("_")
if ($cleanName.Length -gt 50) { $cleanName = $cleanName.Substring(0, 50) }

$timestamp = (Get-Date).ToString("yyyyMMddHHmm")
$dateStr = (Get-Date).ToString("yyyy-MM-dd")

$briefsDir = Join-Path $WORKSPACE "dev\library\research_briefs"
New-Item -ItemType Directory -Force -Path $briefsDir | Out-Null

$briefFile = Join-Path $briefsDir "brief_$cleanName.md"

$md = @()
$md += "---"
$md += "id: `"$timestamp`""
$md += "title: `"Research Brief: $Query`""
$md += "type: `"research_brief`""
$md += "tags: [`"research`", `"web_search`", `"synthesis`"]"
$md += "categories: [`"research`"]"
$md += "created: `"$dateStr`""
$md += "modified: `"$dateStr`""
$md += "status: `"draft`""
$md += "summary: `"Research synthesis and sources gathered for query: $Query.`""
$md += "---"
$md += "`n# Research Brief: $Query`n"
$md += "**Date Compiled**: $dateStr  "
$md += "**Status**: Draft  "
$md += "**Source**: Automated Web Crawl`n"
$md += "## 🔍 Core Question / Topic"
$md += "> What are the key details, definitions, and systems associated with **$Query**?`n"
$md += "## 📊 Synthesized Findings (Information & Knowledge)"
$md += "Here is the synthesized summary of observations from search engines:`n"

$counter = 1
foreach ($r in $results) {
    $md += "### $counter. $($r.title)"
    $md += "- **Source**: $($r.source)"
    $md += "- **URL**: $($r.url)"
    $md += "- **Summary**: $($r.snippet)`n"
    $counter++
}

$md += "## 💡 Architectural Insights / Wisdom"
$md += "Based on the data collected above, the following systems, actions, or ideas are proposed:"
$md += "- [ ] Propose library integration or note structures for: *$Query*."
$md += "- [ ] Review backlinks and expand concepts to Zettelkasten nodes.`n"

$md -join "`n" | Set-Content -Path $briefFile -Encoding utf8
Write-Host "Research Assistant: Created research brief at dev/library/research_briefs/brief_$cleanName.md" -ForegroundColor Green
exit 0
