# Start Docker Desktop Service Script
# Attempts to start the Docker Desktop service

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== Starting Docker Desktop Service ===" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[WARNING] This script may need administrator privileges" -ForegroundColor Yellow
    Write-Host "If it fails, try running PowerShell as Administrator" -ForegroundColor Yellow
    Write-Host ""
}

# Try to find and start Docker Desktop service
Write-Host "Step 1: Finding Docker Desktop service..." -ForegroundColor Yellow

$serviceNames = @(
    "com.docker.service",
    "Docker Desktop Service",
    "docker"
)

$dockerService = $null
foreach ($serviceName in $serviceNames) {
    try {
        $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($service) {
            $dockerService = $service
            Write-Host "   Found service: $serviceName" -ForegroundColor Green
            break
        }
    } catch {
        # Continue searching
    }
}

if (-not $dockerService) {
    Write-Host "   [INFO] Could not find Docker Desktop service by name" -ForegroundColor Yellow
    Write-Host "   Trying to find all Docker-related services..." -ForegroundColor Yellow
    
    $allServices = Get-Service | Where-Object { $_.DisplayName -like "*Docker*" -or $_.Name -like "*docker*" }
    if ($allServices) {
        Write-Host "   Found Docker-related services:" -ForegroundColor Cyan
        foreach ($svc in $allServices) {
            Write-Host "     - $($svc.Name): $($svc.DisplayName) [Status: $($svc.Status)]" -ForegroundColor Gray
        }
        $dockerService = $allServices | Select-Object -First 1
    }
}

if ($dockerService) {
    Write-Host ""
    Write-Host "Step 2: Starting Docker Desktop service..." -ForegroundColor Yellow
    Write-Host "   Service: $($dockerService.DisplayName)" -ForegroundColor Cyan
    Write-Host "   Current Status: $($dockerService.Status)" -ForegroundColor Gray
    
    if ($dockerService.Status -eq "Running") {
        Write-Host "   [OK] Service is already running" -ForegroundColor Green
    } else {
        try {
            Start-Service -Name $dockerService.Name -ErrorAction Stop
            Write-Host "   [OK] Service start command sent" -ForegroundColor Green
            
            # Wait for service to start
            Write-Host "   Waiting for service to start..." -ForegroundColor Yellow
            $timeout = 30
            $elapsed = 0
            $started = $false
            
            while ($elapsed -lt $timeout) {
                Start-Sleep -Seconds 2
                $elapsed += 2
                $dockerService.Refresh()
                
                if ($dockerService.Status -eq "Running") {
                    $started = $true
                    break
                }
                
                Write-Host "     Waiting... [$elapsed/$timeout seconds]" -ForegroundColor Gray
            }
            
            if ($started) {
                Write-Host "   [OK] Service is now running" -ForegroundColor Green
            } else {
                Write-Host "   [WARNING] Service may still be starting" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "   [ERROR] Failed to start service: $_" -ForegroundColor Red
            Write-Host "   You may need to run PowerShell as Administrator" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "   [WARNING] Could not find Docker Desktop service" -ForegroundColor Yellow
    Write-Host "   Docker Desktop may use a different service mechanism" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Step 3: Verifying Docker connection..." -ForegroundColor Yellow

# Wait a bit for Docker to be ready
Start-Sleep -Seconds 3

try {
    $null = docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Docker is now accessible!" -ForegroundColor Green
        Write-Host ""
        Write-Host "You can now run:" -ForegroundColor Cyan
        Write-Host "  docker compose up -d" -ForegroundColor White
    } else {
        Write-Host "   [WARNING] Docker service started but connection not ready yet" -ForegroundColor Yellow
        Write-Host "   Please wait a moment and try:" -ForegroundColor Yellow
        Write-Host "   - Open Docker Desktop application" -ForegroundColor White
        Write-Host "   - Wait for it to fully start" -ForegroundColor White
        Write-Host "   - Run: docker compose up -d" -ForegroundColor White
    }
} catch {
    Write-Host "   [WARNING] Cannot verify Docker connection: $_" -ForegroundColor Yellow
}

Write-Host ""


