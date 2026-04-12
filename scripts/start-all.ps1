param(
    [switch]$SkipDockerDesktop,
    [switch]$SkipMiddleware,
    [switch]$SkipOllama,
    [switch]$SkipApi,
    [switch]$SkipWeb
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$DockerComposeFile = Join-Path $Root "docker/docker-compose.middleware.yaml"
$ApiDir = Join-Path $Root "api"
$WebDir = Join-Path $Root "web"
$ApiPython = Join-Path $ApiDir ".venv/Scripts/python.exe"
$ApiLog = Join-Path $ApiDir "logs/manual-api.out.log"
$WebLog = Join-Path $WebDir "dev.out.log"
$OllamaLog = Join-Path $Root "storage/ollama/ollama.out.log"
$PwshPath = (Get-Process -Id $PID).Path

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[ok] $Message" -ForegroundColor Green
}

function Write-WarnLine {
    param([string]$Message)
    Write-Host "[warn] $Message" -ForegroundColor Yellow
}

function Test-PortListening {
    param([int]$Port)

    $connection = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    return $null -ne $connection
}

function Wait-ForPort {
    param(
        [int]$Port,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-PortListening -Port $Port) {
            return $true
        }
        Start-Sleep -Seconds 2
    }

    return $false
}

function Ensure-Directory {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Start-BackgroundPwsh {
    param(
        [string]$WorkingDirectory,
        [string]$Command
    )

    Start-Process -FilePath $PwshPath `
        -WorkingDirectory $WorkingDirectory `
        -ArgumentList @("-NoLogo", "-NoProfile", "-Command", $Command) `
        -WindowStyle Hidden | Out-Null
}

function Ensure-DockerDesktopRunning {
    if ($SkipDockerDesktop) {
        Write-WarnLine "Skipping Docker Desktop startup."
        return
    }

    Write-Step "Checking Docker Desktop"
    $dockerReady = $false

    try {
        docker info | Out-Null
        $dockerReady = $true
    }
    catch {
        $dockerDesktopPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if (-not (Test-Path -LiteralPath $dockerDesktopPath)) {
            throw "Docker Desktop is not installed at $dockerDesktopPath"
        }

        Write-WarnLine "Docker engine is not ready. Starting Docker Desktop..."
        Start-Process -FilePath $dockerDesktopPath | Out-Null

        $deadline = (Get-Date).AddMinutes(2)
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Seconds 5
            try {
                docker info | Out-Null
                $dockerReady = $true
                break
            }
            catch {
            }
        }
    }

    if (-not $dockerReady) {
        throw "Docker Desktop did not become ready within 2 minutes."
    }

    Write-Ok "Docker Desktop is ready."
}

function Ensure-MiddlewareRunning {
    if ($SkipMiddleware) {
        Write-WarnLine "Skipping middleware startup."
        return
    }

    Write-Step "Ensuring middleware containers"

    Push-Location (Join-Path $Root "docker")
    try {
        try {
            docker compose -f $DockerComposeFile up -d
            Write-Ok "docker compose finished."
        }
        catch {
            Write-WarnLine "docker compose returned a non-zero exit code. Checking whether required services are already up."
        }
    }
    finally {
        Pop-Location
    }

    $ports = @(5432, 5002)
    foreach ($port in $ports) {
        if (Wait-ForPort -Port $port -TimeoutSeconds 20) {
            Write-Ok "Port $port is listening."
        }
        else {
            Write-WarnLine "Port $port is not listening yet. You may need to inspect Docker containers manually."
        }
    }
}

function Ensure-OllamaRunning {
    if ($SkipOllama) {
        Write-WarnLine "Skipping Ollama startup."
        return
    }

    Write-Step "Checking Ollama"

    if (Test-PortListening -Port 11434) {
        Write-Ok "Ollama is already listening on port 11434."
        return
    }

    $ollamaPath = "C:\Users\33814\AppData\Local\Programs\Ollama\ollama.exe"
    if (-not (Test-Path -LiteralPath $ollamaPath)) {
        $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
        if ($ollamaCommand) {
            $ollamaPath = $ollamaCommand.Source
        }
        else {
            throw "Cannot find ollama.exe. Install Ollama or update the script path."
        }
    }

    Ensure-Directory -Path (Split-Path -Parent $OllamaLog)
    $command = "& '$ollamaPath' serve *>> '$OllamaLog'"
    Start-BackgroundPwsh -WorkingDirectory $Root -Command $command

    if (-not (Wait-ForPort -Port 11434 -TimeoutSeconds 30)) {
        throw "Ollama did not start listening on port 11434."
    }

    Write-Ok "Ollama is ready on port 11434."
}

function Ensure-ApiRunning {
    if ($SkipApi) {
        Write-WarnLine "Skipping API startup."
        return
    }

    Write-Step "Checking API"

    if (Test-PortListening -Port 5001) {
        Write-Ok "API is already listening on port 5001."
        return
    }

    if (-not (Test-Path -LiteralPath $ApiPython)) {
        throw "Cannot find API Python interpreter at $ApiPython"
    }

    Ensure-Directory -Path (Split-Path -Parent $ApiLog)
    $command = "Set-Location '$ApiDir'; & '$ApiPython' app.py *>> '$ApiLog'"
    Start-BackgroundPwsh -WorkingDirectory $ApiDir -Command $command

    if (-not (Wait-ForPort -Port 5001 -TimeoutSeconds 60)) {
        throw "API did not start listening on port 5001."
    }

    Write-Ok "API is ready on port 5001."
}

function Ensure-WebRunning {
    if ($SkipWeb) {
        Write-WarnLine "Skipping web startup."
        return
    }

    Write-Step "Checking web app"

    if (Test-PortListening -Port 3000) {
        Write-Ok "Web app is already listening on port 3000."
        return
    }

    Ensure-Directory -Path (Split-Path -Parent $WebLog)
    $command = "Set-Location '$WebDir'; pnpm dev *>> '$WebLog'"
    Start-BackgroundPwsh -WorkingDirectory $WebDir -Command $command

    if (-not (Wait-ForPort -Port 3000 -TimeoutSeconds 120)) {
        throw "Web app did not start listening on port 3000."
    }

    Write-Ok "Web app is ready on port 3000."
}

Write-Host "Starting CheersAI Desktop dependencies..." -ForegroundColor Magenta
Write-Host "Workspace: $Root"

Ensure-DockerDesktopRunning
Ensure-MiddlewareRunning
Ensure-OllamaRunning
Ensure-ApiRunning
Ensure-WebRunning

Write-Host ""
Write-Host "Startup complete." -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000"
Write-Host "API:      http://localhost:5001"
Write-Host "Plugin:   http://localhost:5002"
Write-Host "Ollama:   http://localhost:11434"
Write-Host ""
Write-Host "Logs:"
Write-Host "  API    -> $ApiLog"
Write-Host "  Web    -> $WebLog"
Write-Host "  Ollama -> $OllamaLog"
Write-Host ""
Write-Host "Tip: this script is safe to run repeatedly. Services already listening will be skipped."
