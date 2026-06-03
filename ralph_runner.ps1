# PowerShell 7 Ralph Loop Runner Harness
# Usage: ./ralph_runner.ps1

$WORKSPACE = $PSScriptRoot
$CONFIG_PATH = Join-Path $WORKSPACE "config.json"
$PROMPT_PATH = Join-Path $WORKSPACE "PROMPT.md"
$DEV_DIR = Join-Path $WORKSPACE "dev"
$PLAN_PATH = Join-Path $DEV_DIR "plan.md"
$PROGRESS_PATH = Join-Path $DEV_DIR "progress.json"
$QUEUE_PATH = Join-Path $DEV_DIR "research_queue.json"
$ERROR_LOG_PATH = Join-Path $DEV_DIR "last_error.log"

# Make sure directories exist
New-Item -ItemType Directory -Force -Path $DEV_DIR | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DEV_DIR "library") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DEV_DIR "templates") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DEV_DIR "tools") | Out-Null

function Load-Config {
    if (-not (Test-Path $CONFIG_PATH)) {
        Write-Error "Error: config.json not found."
        exit 1
    }
    $content = Get-Content -Raw -Path $CONFIG_PATH -Encoding utf8
    return ConvertFrom-Json $content
}

function Save-Config($config) {
    $content = ConvertTo-Json $config -Depth 10
    Set-Content -Path $CONFIG_PATH -Value $content -Encoding utf8
}

function Run-GitCommit($msg) {
    try {
        git add -A
        git diff --cached --quiet
        if ($LASTEXITCODE -ne 0) {
            git commit -m $msg
            Write-Host "Git: Committed changes successfully." -ForegroundColor Green
        } else {
            Write-Host "Git: No changes to commit."
        }
    } catch {
        Write-Warning "Git Commit failed: $_"
    }
}

function Run-GitRollback {
    Write-Host "Warning: Running verification failed. Initiating Git rollback..." -ForegroundColor Yellow
    try {
        git reset --hard HEAD
        git clean -fd
        Write-Host "Git: Reverted working tree to last successful state." -ForegroundColor Green
    } catch {
        Write-Error "Critical: Git rollback failed: $_"
    }
}

function Run-Validation {
    $librarian_py = Join-Path $DEV_DIR "tools" "librarian.py"
    if (-not (Test-Path $librarian_py)) {
        Write-Host "Validation: dev/tools/librarian.py not found yet. Skipping validation (bootstrapping phase)."
        return @{ Success = $true; Error = "No librarian script yet" }
    }

    Write-Host "Validation: Running dev/tools/librarian.py --run-tests..."
    try {
        # Run python and capture exit code + output
        $process = Start-Process python -ArgumentList "$librarian_py --run-tests" -NoNewWindow -PassThru -Wait -RedirectStandardOutput "validation_stdout.tmp" -RedirectStandardError "validation_stderr.tmp"
        
        $stdout = ""
        $stderr = ""
        if (Test-Path "validation_stdout.tmp") {
            $stdout = Get-Content -Raw -Path "validation_stdout.tmp"
            Remove-Item "validation_stdout.tmp"
        }
        if (Test-Path "validation_stderr.tmp") {
            $stderr = Get-Content -Raw -Path "validation_stderr.tmp"
            Remove-Item "validation_stderr.tmp"
        }

        if ($process.ExitCode -eq 0) {
            Write-Host "Validation: Success! All checks passed." -ForegroundColor Green
            return @{ Success = $true; Error = $stdout }
        } else {
            Write-Host "Validation: Failed with exit code $($process.ExitCode)" -ForegroundColor Red
            $error_output = "EXIT CODE: $($process.ExitCode)`n`nSTDOUT:`n$stdout`n`nSTDERR:`n$stderr"
            return @{ Success = $false; Error = $error_output }
        }
    } catch {
        Write-Host "Validation: Error executing script: $_" -ForegroundColor Red
        return @{ Success = $false; Error = $_.ToString() }
    }
}

function Compile-Context($config) {
    $parts = @()

    # 1. Base Developer Prompt
    if (Test-Path $PROMPT_PATH) {
        $parts += "=== SYSTEM INSTRUCTIONS (PROMPT.md) ===`n$(Get-Content -Raw -Path $PROMPT_PATH -Encoding utf8)"
    } else {
        $parts += "=== SYSTEM INSTRUCTIONS ===`nYou are a Ralph Loop Builder Agent. Help design and build the Library system."
    }

    # 2. Critical error state (if any)
    if (Test-Path $ERROR_LOG_PATH) {
        $err = Get-Content -Raw -Path $ERROR_LOG_PATH -Encoding utf8
        $parts += "=== [CRITICAL ERROR] PREVIOUS RUN FAILED ===`nYour previous attempt was rolled back due to verification failures.`nYou must resolve the root cause of this error before proceeding with any other tasks.`n`nError Details:`n$err`n=========================================="
    }

    # 3. Plan & Roadmap
    if (Test-Path $PLAN_PATH) {
        $parts += "=== CURRENT ROADMAP & PLANS (dev/plan.md) ===`n$(Get-Content -Raw -Path $PLAN_PATH -Encoding utf8)"
    }

    # 4. PRD Progress Checklist
    if (Test-Path $PROGRESS_PATH) {
        $parts += "=== PROGRESS STATUS (dev/progress.json) ===`n$(Get-Content -Raw -Path $PROGRESS_PATH -Encoding utf8)"
    }

    # 5. Research Queue
    if (Test-Path $QUEUE_PATH) {
        $parts += "=== RESEARCH QUEUE (dev/research_queue.json) ===`n$(Get-Content -Raw -Path $QUEUE_PATH -Encoding utf8)"
    }

    # 6. Current Directory Map
    $parts += "=== CURRENT WORKING DIRECTORY ===`nRunning in workspace: $WORKSPACE"

    return $parts -join "`n`n"
}

function Parse-And-Apply-Changes($responseText) {
    $filesChanged = @()

    # Find <file path="...">...</file> blocks using regex
    # Match non-greedy content inside the tag
    $fileRegex = [regex]'<file path="([^"]+)">([\s\S]*?)<\/file>'
    $matches = $fileRegex.Matches($responseText)

    foreach ($m in $matches) {
        $pathStr = $m.Groups[1].Value
        $content = $m.Groups[2].Value

        # Resolve absolute path and prevent writing outside workspace
        $targetPath = [System.IO.Path]::GetFullPath((Join-Path $WORKSPACE $pathStr))
        if (-not $targetPath.StartsWith($WORKSPACE)) {
            Write-Warning "Warning: Model attempted to write outside workspace: $pathStr. Blocked."
            continue
        }

        # Create parent directory
        $parentDir = Split-Path $targetPath -Parent
        New-Item -ItemType Directory -Force -Path $parentDir | Out-Null

        # Clean leading/trailing newlines
        if ($content.StartsWith("`n")) {
            $content = $content.Substring(1)
        }
        if ($content.EndsWith("`n")) {
            $content = $content.Substring(0, $content.Length - 1)
        }

        Set-Content -Path $targetPath -Value $content -Encoding utf8
        Write-Host "Runner: Updated/Created file: $pathStr" -ForegroundColor Cyan
        $filesChanged += $pathStr
    }

    # Find <delete_file path="..."/> blocks
    $delRegex = [regex]'<delete_file path="([^"]+)"\s*/>'
    $delMatches = $delRegex.Matches($responseText)

    foreach ($dm in $delMatches) {
        $pathStr = $dm.Groups[1].Value
        $targetPath = [System.IO.Path]::GetFullPath((Join-Path $WORKSPACE $pathStr))
        if (-not $targetPath.StartsWith($WORKSPACE)) {
            Write-Warning "Warning: Model attempted to delete outside workspace: $pathStr. Blocked."
            continue
        }
        if (Test-Path $targetPath) {
            Remove-Item $targetPath -Force
            Write-Host "Runner: Deleted file: $pathStr" -ForegroundColor Red
            $filesChanged += $pathStr
        }
    }

    return $filesChanged
}

function Call-LMStudio($config, $contextPrompt) {
    $apiUrl = "$($config.api_base)/chat/completions"
    
    $body = @{
        model = $config.model
        messages = @(
            @{
                role = "user"
                content = $contextPrompt
            }
        )
        temperature = $config.temperature
        max_tokens = $config.max_tokens
    } | ConvertTo-Json -Depth 10

    $headers = @{
        "Content-Type" = "application/json"
    }

    $startTime = Get-Date
    try {
        $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body -Headers $headers -TimeoutSec 300
        $duration = ((Get-Date) - $startTime).TotalSeconds

        $choices = $response.choices
        if ($choices.Count -eq 0) {
            return $null, 0, 0, $duration
        }

        $responseText = $choices[0].message.content
        $usage = $response.usage
        $promptTokens = $usage.prompt_tokens
        $completionTokens = $usage.completion_tokens

        return $responseText, $promptTokens, $completionTokens, $duration
    } catch {
        $duration = ((Get-Date) - $startTime).TotalSeconds
        Write-Host "API Error: Failed to connect to LM Studio: $_" -ForegroundColor Red
        return $null, 0, 0, $duration
    }
}

# MAIN EXECUTION
$config = Load-Config
$maxIters = $config.max_iterations

Write-Host "Starting Ralph Loop (PowerShell 7). Model: $($config.model). Max iterations: $maxIters." -ForegroundColor Magenta
Write-Host "LM Studio API Base: $($config.api_base)"

$iteration = 0
while ($iteration -lt $maxIters) {
    $iteration++
    Write-Host "`n--- TURN $iteration / $maxIters ---" -ForegroundColor Blue

    # 1. Compile Context
    $contextPrompt = Compile-Context $config

    # 2. Call API
    Write-Host "Runner: Querying model $($config.model)..."
    $response, $pTok, $cTok, $duration = Call-LMStudio $config $contextPrompt

    if ($null -eq $response) {
        Write-Host "Runner: Received empty or error response. Sleeping and retrying..." -ForegroundColor Yellow
        Start-Sleep -Seconds $config.sleep_seconds_between_turns
        continue
    }

    Write-Host "Runner: Received response. Duration: $("{0:N2}" -f $duration)s. Tokens: $pTok prompt, $cTok completion." -ForegroundColor Green

    # 3. Apply changes
    $filesChanged = Parse-And-Apply-Changes $response

    # 4. Check for COMPLETE token
    $complete = $response.Contains("<promise>COMPLETE</promise>") -or $response.Contains("<promise>COMPLETED</promise>")

    # 5. Run Validation
    if ($filesChanged.Count -gt 0) {
        $valRes = Run-Validation
        if ($valRes.Success) {
            if ($config.git_commit_on_success) {
                Run-GitCommit "ralph-loop turn $iteration: completed task"
            }
            if (Test-Path $ERROR_LOG_PATH) {
                Remove-Item $ERROR_LOG_PATH -Force
            }
            $config.stats.successful_turns++
        } else {
            Set-Content -Path $ERROR_LOG_PATH -Value $valRes.Error -Encoding utf8
            Run-GitRollback
            $config.stats.failed_turns++
        }
    } else {
        Write-Host "Runner: No files changed this turn."
    }

    # Update stats
    $config.stats.total_turns = $iteration
    $config.stats.total_tokens_consumed += $pTok
    $config.stats.total_tokens_generated += $cTok
    Save-Config $config

    if ($complete) {
        Write-Host "Runner: Stop signal <promise>COMPLETE</promise> detected. Terminating loop." -ForegroundColor Green
        break
    }

    Write-Host "Runner: End of turn $iteration. Sleeping for $($config.sleep_seconds_between_turns)s..."
    Start-Sleep -Seconds $config.sleep_seconds_between_turns
}
