#requires -Version 5.1
<#
.SYNOPSIS
  Record everything from the CareerPath AI Docker stack into one timestamped log
  file so we can grep for errors after a manual test session.

.DESCRIPTION
  Tails ALL container logs with timestamps to logs/session-YYYYMMDD-HHMMSS.log.
  Writes a header with git SHA, .env hash, and the list of running containers
  so the log is self-describing when we open it later.

  Stop the recording with Ctrl+C — the log file stays on disk.

.PARAMETER OutDir
  Where to put the log file. Default: ./logs (relative to careerpath-ai/).

.EXAMPLE
  # From inside careerpath-ai/
  .\scripts\record-session.ps1

.EXAMPLE
  # Custom output directory
  .\scripts\record-session.ps1 -OutDir C:\demo-logs
#>

param(
    [string]$OutDir = "logs"
)

$ErrorActionPreference = "Stop"

# We must be in careerpath-ai/ for docker compose to find docker-compose.yml.
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "ERROR: Run this script from the careerpath-ai/ directory" -ForegroundColor Red
    Write-Host "       (the one that contains docker-compose.yml)." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = Join-Path $OutDir "session-$timestamp.log"

# ---------------------------------------------------------------------------
# Header — makes the log self-describing without needing external context.
# ---------------------------------------------------------------------------
$gitSha = try { (git rev-parse --short HEAD 2>$null) } catch { "unknown" }
if (-not $gitSha) { $gitSha = "unknown" }

$envHash = "no .env"
if (Test-Path ".env") {
    $envHash = (Get-FileHash ".env" -Algorithm SHA1).Hash.Substring(0, 12)
}

$header = @"
================================================================================
CareerPath AI — Session Recording
Started:  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')
Git SHA:  $gitSha
.env:     $envHash
Host:     $env:COMPUTERNAME ($env:USERNAME)
================================================================================

"@

$header | Out-File -FilePath $logFile -Encoding utf8

# ---------------------------------------------------------------------------
# Snapshot the container state so we can correlate logs with "what was up".
# ---------------------------------------------------------------------------
Write-Host "→ Snapshotting container state..." -ForegroundColor Cyan
"--- docker compose ps (snapshot at start) ---" | Out-File -FilePath $logFile -Encoding utf8 -Append
docker compose ps 2>&1 | Out-File -FilePath $logFile -Encoding utf8 -Append
""                                              | Out-File -FilePath $logFile -Encoding utf8 -Append
"--- live logs follow ---"                      | Out-File -FilePath $logFile -Encoding utf8 -Append

Write-Host ""
Write-Host "Recording to: $logFile" -ForegroundColor Green
Write-Host ""
Write-Host "Now do your manual test (browser, upload CV, run interview, etc.)." -ForegroundColor Yellow
Write-Host "When you're done, press Ctrl+C in this window to stop recording." -ForegroundColor Yellow
Write-Host ""

# ---------------------------------------------------------------------------
# Tail with --timestamps so every line is correlatable to UI actions.
# --tail=0 means "only show NEW lines from now on" — we don't want to capture
# the full container history, just what happens during this session.
# ---------------------------------------------------------------------------
try {
    docker compose logs -f --timestamps --tail=0 *>&1 | Tee-Object -FilePath $logFile -Append
} catch {
    # Ctrl+C lands here — that's the normal exit path.
} finally {
    Write-Host ""
    Write-Host "Recording stopped. Log saved to: $logFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "Useful greps:" -ForegroundColor Cyan
    Write-Host "  Select-String -Path $logFile -Pattern 'ERROR|Exception|Traceback'"
    Write-Host "  Select-String -Path $logFile -Pattern 'profile.extracted|cv.analyzed|interview\.'"
    Write-Host "  Select-String -Path $logFile -Pattern '5[0-9][0-9] '   # 5xx HTTP responses"
}
