#!/usr/bin/env pwsh
# Zero-dependency Web Search Scraper
# Usage: ./web_search.ps1 -Query "markdown table specifications"

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Query,
    [string]$Engine = "auto", # ddg, wiki, auto
    [string]$Output = "markdown" # json, markdown
)

function Clean-Html($text) {
    if ($null -eq $text) { return "" }
    # Strip HTML tags
    $text = $text -replace "<[^>]+>", ""
    # Decode entities
    $text = $text.Replace("&quot;", '"').Replace("&amp;", "&").Replace("&lt;", "<").Replace("&gt;", ">").Replace("&#x27;", "'").Replace("&nbsp;", " ")
    return $text.Trim()
}

function Search-Wikipedia($q) {
    $encoded = [uri]::EscapeDataString($q)
    $url = "https://en.wikipedia.org/w/api.php?action=opensearch&search=$encoded&limit=5&namespace=0&format=json"
    
    try {
        $data = Invoke-RestMethod -Uri $url -UserAgent "RalphLoopLibrary/1.0" -TimeoutSec 15
        
        $results = @()
        $titles = $data[1]
        $summaries = $data[2]
        $links = $data[3]
        
        for ($i = 0; $i -lt $titles.Count; $i++) {
            $results += @{
                title   = $titles[$i]
                snippet = $summaries[$i]
                url     = $links[$i]
                source  = "Wikipedia"
            }
        }
        return $results
    } catch {
        Write-Warning "Wikipedia search failed: $_"
        return @()
    }
}

function Search-DuckDuckGo($q) {
    $encoded = [uri]::EscapeDataString($q)
    $url = "https://html.duckduckgo.com/html/?q=$encoded"
    $userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
    
    try {
        $html = Invoke-WebRequest -Uri $url -UserAgent $userAgent -TimeoutSec 15 -UseBasicParsing
        $htmlContent = $html.Content
        
        $results = @()
        
        # Regex matching
        $urlMatches = [regex]::Matches($htmlContent, '<a class="result__url" href="([^"]+)"')
        $snippetMatches = [regex]::Matches($htmlContent, '<a class="result__snippet"[^>]*>([\s\S]*?)</a>')
        $titleMatches = [regex]::Matches($htmlContent, '<a class="result__link"[^>]*>([\s\S]*?)</a>')
        
        $limit = [Math]::Min($urlMatches.Count, [Math]::Min($snippetMatches.Count, $titleMatches.Count))
        if ($limit -gt 5) { $limit = 5 }
        
        for ($i = 0; $i -lt $limit; $i++) {
            $targetUrl = $urlMatches[$i].Groups[1].Value
            
            # Clean redirected URLs
            if ($targetUrl -like "*/l/?kh=*") {
                if ($targetUrl -match "uddg=([^&]+)") {
                    $targetUrl = [uri]::UnescapeDataString($Matches[1])
                }
            }
            
            $results += @{
                title   = Clean-Html $titleMatches[$i].Groups[1].Value
                snippet = Clean-Html $snippetMatches[$i].Groups[1].Value
                url     = $targetUrl
                source  = "DuckDuckGo"
            }
        }
        return $results
    } catch {
        Write-Warning "DuckDuckGo search failed: $_"
        return @()
    }
}

$results = @()
if ($Engine -eq "wiki") {
    $results = Search-Wikipedia $Query
} elseif ($Engine -eq "ddg") {
    $results = Search-DuckDuckGo $Query
} else {
    # Auto Selection
    $words = $Query.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
    if ($words.Count -le 4) {
        $results = Search-Wikipedia $Query
    }
    if ($results.Count -eq 0) {
        $results = Search-DuckDuckGo $Query
    }
}

if ($Output -eq "json") {
    $jsonResults = @()
    foreach ($r in $results) {
        $jsonResults += [PSCustomObject]$r
    }
    $jsonResults | ConvertTo-Json -Depth 5
} else {
    Write-Host "# Search Results for: $Query`n"
    if ($results.Count -eq 0) {
        Write-Host "No results found."
        return
    }
    
    $counter = 1
    foreach ($r in $results) {
        Write-Host "### $counter. $($r.title)"
        Write-Host "- **Source**: $($r.source)"
        Write-Host "- **URL**: $($r.url)"
        Write-Host "- **Snippet**: $($r.snippet)`n"
        $counter++
    }
}
