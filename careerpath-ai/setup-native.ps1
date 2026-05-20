# ═══════════════════════════════════════════════════════════════════════════
# CareerPath AI — Setup Script (Native, No Docker)
# ═══════════════════════════════════════════════════════════════════════════
# Rulare: powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1

param(
    [ValidateSet("install", "start", "stop", "status", "clean")]
    [string]$Action = "install"
)

$ProjectRoot = "C:\Rares\Carrer_Path\careerpath-ai"
$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Text)
    Write-Host "`n" -ForegroundColor Gray
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║ $Text" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "ℹ️  $Text" -ForegroundColor Yellow
}

# ═══════════════════════════════════════════════════════════════════════════
# INSTALL DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════

function Install-Dependencies {
    Write-Header "STEP 1: Checking Prerequisites"

    # Check Node.js
    try {
        $nodeVersion = node --version
        Write-Success "Node.js $nodeVersion found"
    } catch {
        Write-Error-Custom "Node.js not found. Download from https://nodejs.org"
        exit 1
    }

    # Check Python
    try {
        $pythonVersion = python --version
        Write-Success "$pythonVersion found"
    } catch {
        Write-Error-Custom "Python not found. Download from https://www.python.org/downloads/"
        exit 1
    }

    # Check PostgreSQL
    try {
        $pgVersion = psql --version
        Write-Success "$pgVersion found"
    } catch {
        Write-Error-Custom "PostgreSQL not found. Download from https://www.postgresql.org/download/windows/"
        exit 1
    }

    # Check Redis
    try {
        $redisVersion = redis-cli --version
        Write-Success "$redisVersion found"
    } catch {
        Write-Error-Custom "Redis not found. Download or install from WSL2"
        exit 1
    }

    Write-Header "STEP 2: Installing Node Dependencies"

    # API Gateway
    Write-Info "Building api-gateway..."
    Push-Location "$ProjectRoot\api-gateway"
    npm install --silent | Out-Null
    npm run build --silent | Out-Null
    Pop-Location
    Write-Success "api-gateway ready"

    # Frontend
    Write-Info "Installing frontend..."
    Push-Location "$ProjectRoot\frontend"
    npm install --silent | Out-Null
    Pop-Location
    Write-Success "frontend ready"

    Write-Header "STEP 3: Setting Up Python Virtual Environments"

    $services = @(
        "services\cv-analyzer-agent",
        "services\hr-interview-agent",
        "services\agent-orchestrator"
    )

    foreach ($service in $services) {
        $servicePath = "$ProjectRoot\$service"
        Write-Info "Setting up $service..."

        if (Test-Path "$servicePath\.venv") {
            Write-Info "  Virtual env already exists, skipping..."
        } else {
            Push-Location $servicePath
            python -m venv .venv | Out-Null
            & ".\.venv\Scripts\pip.exe" install -q -r requirements.txt
            Pop-Location
            Write-Success "  ✓ $service ready"
        }
    }

    Write-Header "✅ INSTALLATION COMPLETE"
    Write-Host "Next step: " -NoNewline -ForegroundColor Gray
    Write-Host "powershell -File setup.ps1 -Action start" -ForegroundColor Cyan
}

# ═══════════════════════════════════════════════════════════════════════════
# START SERVICES
# ═══════════════════════════════════════════════════════════════════════════

function Start-Services {
    Write-Header "STARTING CareerPath AI Services"

    # Check .env exists
    if (-not (Test-Path "$ProjectRoot\.env")) {
        Write-Error-Custom ".env not found!"
        Write-Info "Run: cd $ProjectRoot; cp .env.example .env"
        exit 1
    }

    Write-Info "Services vor porni în terminale separate..."
    Write-Host "Apasă Enter pentru a continua..." -ForegroundColor Yellow
    Read-Host | Out-Null

    # PostgreSQL
    Write-Header "Starting PostgreSQL"
    try {
        $pgService = Get-Service postgresql* | Where-Object { $_.Name -like "*15*" } | Select-Object -First 1
        if ($pgService) {
            Start-Service $pgService.Name -ErrorAction SilentlyContinue
            Write-Success "PostgreSQL started"
        }
    } catch {}

    Start-Sleep -Seconds 2

    # Redis
    Write-Header "Starting Redis"
    $redisProcess = Get-Process redis-server -ErrorAction SilentlyContinue
    if (-not $redisProcess) {
        Write-Info "Opening Redis server in new terminal..."
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "redis-server"
        Write-Success "Redis terminal opened"
    } else {
        Write-Success "Redis already running"
    }

    Start-Sleep -Seconds 2

    # API Gateway
    Write-Header "Starting API Gateway (NestJS)"
    Write-Info "Terminal will open separately..."
    $apiGatewayCmd = @"
cd "$ProjectRoot\api-gateway"
Write-Host "API Gateway starting on http://localhost:8000/health" -ForegroundColor Cyan
npm run start:dev
"@
    Start-Process powershell -ArgumentList "-NoExit", "-NoProfile", "-Command", $apiGatewayCmd

    Start-Sleep -Seconds 3

    # Frontend
    Write-Header "Starting Frontend (Next.js)"
    Write-Info "Terminal will open separately..."
    $frontendCmd = @"
cd "$ProjectRoot\frontend"
Write-Host "Frontend starting on http://localhost:3000" -ForegroundColor Cyan
npm run dev
"@
    Start-Process powershell -ArgumentList "-NoExit", "-NoProfile", "-Command", $frontendCmd

    Start-Sleep -Seconds 2

    # Agents
    $agents = @(
        @{ Name = "CV Analyzer"; Port = 8002; Path = "services\cv-analyzer-agent" },
        @{ Name = "HR Interview"; Port = 8003; Path = "services\hr-interview-agent" },
        @{ Name = "Agent Orchestrator"; Port = 8005; Path = "services\agent-orchestrator" }
    )

    foreach ($agent in $agents) {
        Write-Header "Starting $($agent.Name)"
        Write-Info "Terminal will open separately..."
        $agentCmd = @"
`$env:PYTHONUNBUFFERED = 1
cd "$ProjectRoot\$($agent.Path)"
& ".\.venv\Scripts\Activate.ps1"
Write-Host "$($agent.Name) starting on http://localhost:$($agent.Port)/docs" -ForegroundColor Cyan
uvicorn src.main:app --port $($agent.Port) --reload
"@
        Start-Process powershell -ArgumentList "-NoExit", "-NoProfile", "-Command", $agentCmd
        Start-Sleep -Seconds 1
    }

    Write-Header "✅ ALL SERVICES STARTED"
    Write-Host "
📊 Access Points:
   Frontend        → http://localhost:3000
   API Gateway     → http://localhost:8000/health
   CV Analyzer     → http://localhost:8002/docs
   HR Interview    → http://localhost:8003/docs
   Orchestrator    → http://localhost:8005/docs
   PostgreSQL      → localhost:5432
   Redis           → localhost:6379

💡 Tip: Check each terminal for errors. Service status may take 30s to stabilize.
" -ForegroundColor Green
}

# ═══════════════════════════════════════════════════════════════════════════
# STOP SERVICES
# ═══════════════════════════════════════════════════════════════════════════

function Stop-Services {
    Write-Header "STOPPING CareerPath AI Services"

    $processes = @("node", "python", "redis-server")

    foreach ($proc in $processes) {
        $running = Get-Process $proc -ErrorAction SilentlyContinue
        if ($running) {
            Write-Info "Stopping $proc..."
            Stop-Process -Name $proc -Force -ErrorAction SilentlyContinue
            Write-Success "$proc stopped"
        }
    }

    Write-Success "All services stopped"
}

# ═══════════════════════════════════════════════════════════════════════════
# CHECK STATUS
# ═══════════════════════════════════════════════════════════════════════════

function Check-Status {
    Write-Header "SERVICE STATUS"

    $services = @(
        @{ Name = "API Gateway"; URL = "http://localhost:8000/health"; Port = 8000 },
        @{ Name = "Frontend"; URL = "http://localhost:3000"; Port = 3000 },
        @{ Name = "CV Analyzer"; URL = "http://localhost:8002/docs"; Port = 8002 },
        @{ Name = "HR Interview"; URL = "http://localhost:8003/docs"; Port = 8003 },
        @{ Name = "Orchestrator"; URL = "http://localhost:8005/docs"; Port = 8005 },
        @{ Name = "PostgreSQL"; URL = ""; Port = 5432 },
        @{ Name = "Redis"; URL = ""; Port = 6379 }
    )

    foreach ($service in $services) {
        if ($service.URL) {
            try {
                $response = Invoke-WebRequest -Uri $service.URL -TimeoutSec 2 -ErrorAction SilentlyContinue
                Write-Success "$($service.Name) ✓"
            } catch {
                Write-Error-Custom "$($service.Name) ✗"
            }
        } else {
            try {
                $tcpClient = New-Object System.Net.Sockets.TcpClient
                $tcpClient.Connect("localhost", $service.Port)
                $tcpClient.Close()
                Write-Success "$($service.Name) ✓"
            } catch {
                Write-Error-Custom "$($service.Name) ✗"
            }
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# CLEAN
# ═══════════════════════════════════════════════════════════════════════════

function Clean-Environment {
    Write-Header "CLEANING UP"

    Write-Info "Removing Python virtual environments..."
    $services = @("services\cv-analyzer-agent", "services\hr-interview-agent", "services\agent-orchestrator")

    foreach ($service in $services) {
        $venvPath = "$ProjectRoot\$service\.venv"
        if (Test-Path $venvPath) {
            Remove-Item -Recurse -Force $venvPath
            Write-Success "  Removed $service\.venv"
        }
    }

    Write-Info "Clearing Redis..."
    redis-cli FLUSHALL | Out-Null
    Write-Success "Redis cleared"

    Write-Success "Cleanup complete"
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

switch ($Action) {
    "install" { Install-Dependencies }
    "start" { Start-Services }
    "stop" { Stop-Services }
    "status" { Check-Status }
    "clean" { Clean-Environment }
    default {
        Write-Host "
Usage: powershell -File setup.ps1 -Action <action>

Actions:
  install    - Install all dependencies (run first time)
  start      - Start all services in separate terminals
  stop       - Stop all running services
  status     - Check which services are running
  clean      - Remove virtual environments and clear Redis

Example:
  powershell -File setup.ps1 -Action install
  powershell -File setup.ps1 -Action start
" -ForegroundColor Cyan
    }
}

