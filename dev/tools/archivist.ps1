#!/usr/bin/env pwsh
# Archivist Dev-to-Prod component promotion script
# Usage: ./archivist.ps1 -Promote "dev/tools/cataloger.ps1"

param(
    [string]$Promote = $null,
    [switch]$UpdateDocs
)

$WORKSPACE = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))

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
                    $metadata[$Matches[1].Trim()] = $Matches[2].Trim().Trim('"', "'")
                }
            }
            return $metadata
        }
    } catch {}
    return $null
}

function Update-LivingDocumentation {
    Write-Host "Archivist: Rebuilding living production documentation in prod/docs/..." -ForegroundColor Magenta
    
    $prodDir = Join-Path $WORKSPACE "prod"
    $docsDir = Join-Path $prodDir "docs"
    New-Item -ItemType Directory -Force -Path $docsDir | Out-Null
    
    # 1. Promoted tools
    $tools = @()
    $toolsDir = Join-Path $prodDir "tools"
    if (Test-Path $toolsDir) {
        $tools = Get-ChildItem -Path $toolsDir | Where-Object { $_.Extension -eq ".py" -or $_.Extension -eq ".ps1" } | Sort-Object Name
    }
    
    # 2. Promoted templates
    $templates = @()
    $templatesDir = Join-Path $prodDir "templates"
    if (Test-Path $templatesDir) {
        $templates = Get-ChildItem -Path $templatesDir -Filter "*.md" | Sort-Object Name
    }

    # Rebuild architecture.md
    $arch = @()
    $arch += "# Production Architecture Specifications"
    $arch += "*This document is automatically updated by the Archivist.*"
    $arch += "`nThis library system is optimized for high-speed, token-efficient queries with a 64k context constraint."
    $arch += "`n## Stable Active Tools (The Roster)"
    $arch += "The following management tools are active in the production environment:`n"
    
    if ($tools.Count -eq 0) {
        $arch += "*No tools have been promoted to production yet.*"
    } else {
        foreach ($t in $tools) {
            $lang = ($t.Extension -eq ".py" ? "Python 3" : "PowerShell 7")
            $arch += "- **$($t.Name)** ($lang) — System utility located in ``prod/tools/``."
        }
    }
    
    $arch += "`n## Directory Layout Rules"
    $arch += "All stable, human-readable assets are organized in the following root tree:"
    $arch += "- `prod/library/` - Verified wiki articles, Zettelkastens, and clinical briefs."
    $arch += "- `prod/templates/` - Active layouts for structural note-taking."
    $arch += "- `prod/tools/` - Executable scripts for cataloging, search, and quality control."
    
    $arch -join "`n" | Set-Content -Path (Join-Path $docsDir "architecture.md") -Encoding utf8

    # Rebuild system_blueprints.md
    $blue = @()
    $blue += "# System Design & Document Blueprints"
    $blue += "*This document is automatically updated by the Archivist.*"
    $blue += "`nThe library classification relies on custom note-taking structures designed for both human readability and low-token AI parsing."
    $blue += "`n## Production Note Templates"
    $blue += "The following templates are registered and stable:`n"
    
    if ($templates.Count -eq 0) {
        $blue += "*No templates have been promoted to production yet.*"
    } else {
        foreach ($temp in $templates) {
            $summary = "Structured note layout."
            $metadata = Parse-YamlFrontMatter $temp.FullName
            if ($metadata -and $metadata.ContainsKey("summary")) {
                $summary = $metadata["summary"]
            }
            $blue += "- **[$($temp.Name)](file:///prod/templates/$($temp.Name))** — $summary"
        }
    }
    
    $blue += "`n## Standard YAML Metadata Schema"
    $blue += "All files in the library database must validate against this format:"
    $blue += "```yaml"
    $blue += "---"
    $blue += "id: `"YYYYMMDDHHMM`"      # Strict 12-digit timestamp identifier"
    $blue += "title: `"Title Name`"     # Clear, human-readable title"
    $blue += "type: `"zettelkasten`"    # Registered note structure type"
    $blue += "tags: [tag1, tag2]       # Category tags for search indexing"
    $blue += "categories: [cat1]      # Broad namespace categorization"
    $blue += "created: `"YYYY-MM-DD`"   # ISO created date"
    $blue += "modified: `"YYYY-MM-DD`"  # ISO last modified date"
    $blue += "status: `"stable`"        # Must be 'stable' to remain in production"
    $blue += "summary: `"Single-sentence summary of the note contents.`""
    $blue += "---"
    $blue += "```"
    
    $blue -join "`n" | Set-Content -Path (Join-Path $docsDir "system_blueprints.md") -Encoding utf8

    # Rebuild implementation.md
    $impl = @()
    $impl += "# Production Implementation & Deployment Guide"
    $impl += "*This document is automatically updated by the Archivist.*"
    $impl += "`n## Installation & Setup"
    $impl += "This system is completely portable and contains no external package dependencies."
    $impl += "`n### Running Search Queries"
    $impl += "To run a high-speed metadata search:"
    $impl += "```bash"
    $impl += "# Python"
    $impl += "python prod/tools/search_library.py --dir prod/library --tag target_tag"
    $impl += ""
    $impl += "# PowerShell 7"
    $impl += "pwsh prod/tools/search_library.ps1 -Dir prod/library -Tag target_tag"
    $impl += "```"
    $impl += "`n### Library Indexing & Cataloging"
    $impl += "To rebuild the dynamic index file (``prod/library/index.md``) and check backlinks:"
    $impl += "```bash"
    $impl += "python prod/tools/cataloger.py --dir prod/library"
    $impl += "```"
    
    $impl -join "`n" | Set-Content -Path (Join-Path $docsDir "implementation.md") -Encoding utf8
    Write-Host "Archivist: Production documentation successfully updated." -ForegroundColor Green
}

function Promote-File($relPathStr) {
    $srcFile = [System.IO.Path]::GetFullPath((Join-Path $WORKSPACE $relPathStr))
    if (-not (Test-Path $srcFile)) {
        Write-Error "Archivist Error: Source file $relPathStr does not exist."
        return $false
    }
    
    if (-not $srcFile.StartsWith($WORKSPACE)) {
        Write-Error "Archivist Error: Security breach. File path is outside workspace."
        return $false
    }
    
    if (-not $relPathStr.StartsWith("dev/")) {
        Write-Error "Archivist Error: Can only promote files from 'dev/' folder."
        return $false
    }
    
    # Check markdown front-matter status before promoting
    if ($srcFile.EndsWith(".md") -and $relPathStr -notlike "dev/templates/*") {
        $metadata = Parse-YamlFrontMatter $srcFile
        if ($null -eq $metadata) {
            Write-Error "Archivist Error: $relPathStr has missing or invalid front-matter."
            return $false
        }
        $status = $metadata["status"]
        if ($status -ne "stable") {
            Write-Warning "Archivist Warning: Note $relPathStr has status '$status' (not 'stable'). Forcing promote anyway."
        }
    }
    
    # Map target path
    $relativeToDev = $relPathStr.Substring(4) # strip 'dev/'
    $destFile = Join-Path (Join-Path $WORKSPACE "prod") $relativeToDev
    
    $destDir = Split-Path $destFile -Parent
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    
    Copy-Item -Path $srcFile -Destination $destFile -Force
    Write-Host "Archivist: Promoted $relPathStr -> prod/$relativeToDev" -ForegroundColor Green
    
    return $true
}

if ($Promote) {
    $success = Promote-File $Promote
    if ($success) {
        Update-LivingDocumentation
        exit 0
    } else {
        exit 1
    }
}

if ($UpdateDocs) {
    Update-LivingDocumentation
    exit 0
}

Write-Host "Archivist: Please specify -Promote <path> or -UpdateDocs" -ForegroundColor Yellow
