# Docker Status Check Script
# Quick diagnostic tool for Docker connection issues

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== Docker Status Check ===" -ForegroundColor Cyan
Write-Host ""

# Check Docker command
Write-Host "1. Docker Command:" -ForegroundColor Yellow
try {
    $version = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] $version" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Not available" -ForegroundColor Red
    }
} catch {
    Write-Host "   [ERROR] $_" -ForegroundColor Red
}

# Check Docker service
Write-Host ""
Write-Host "2. Docker Service:" -ForegroundColor Yellow
try {
    $info = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Docker service is running" -ForegroundColor Green
        $serverVersion = ($info | Select-String "Server Version:").ToString()
        if ($serverVersion) {
            Write-Host "   $serverVersion" -ForegroundColor Gray
        }
    } else {
        Write-Host "   [ERROR] Docker service is not running" -ForegroundColor Red
        Write-Host "   Error: $($info -join ' ')" -ForegroundColor Gray
    }
} catch {
    Write-Host "   [ERROR] Cannot connect: $_" -ForegroundColor Red
}

# Check Docker Desktop process
Write-Host ""
Write-Host "3. Docker Desktop Process:" -ForegroundColor Yellow
$processes = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
if ($processes) {
    Write-Host "   [OK] Docker Desktop process is running" -ForegroundColor Green
    foreach ($proc in $processes) {
        Write-Host "   PID: $($proc.Id), Memory: $([math]::Round($proc.WorkingSet64/1MB, 2)) MB" -ForegroundColor Gray
    }
} else {
    Write-Host "   [WARNING] Docker Desktop process not found" -ForegroundColor Yellow
}

# Check Docker Desktop service
Write-Host ""
Write-Host "4. Docker Desktop Service:" -ForegroundColor Yellow
$service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
if ($service) {
    $status = $service.Status
    if ($status -eq "Running") {
        Write-Host "   [OK] Docker Desktop service is running" -ForegroundColor Green
    } else {
        Write-Host "   [WARNING] Docker Desktop service status: $status" -ForegroundColor Yellow
    }
} else {
    Write-Host "   [INFO] Docker Desktop service not found (may use different service name)" -ForegroundColor Gray
}

# Check Docker Compose
Write-Host ""
Write-Host "5. Docker Compose:" -ForegroundColor Yellow
try {
    $composeVersion = docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] $composeVersion" -ForegroundColor Green
    } else {
        $composeVersion = docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   [OK] $composeVersion (old version)" -ForegroundColor Green
        } else {
            Write-Host "   [ERROR] Not available" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "   [ERROR] $_" -ForegroundColor Red
}

# Recommendations
Write-Host ""
Write-Host "=== Recommendations ===" -ForegroundColor Cyan

$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Docker service is not running. Try:" -ForegroundColor Yellow
    Write-Host "1. Open Docker Desktop from Start Menu" -ForegroundColor White
    Write-Host "2. Wait for the system tray icon to show 'Docker Desktop is running'" -ForegroundColor White
    Write-Host "3. Check if Docker Desktop shows any error messages" -ForegroundColor White
    Write-Host "4. Try restarting Docker Desktop" -ForegroundColor White
    Write-Host "5. Run this script again to verify" -ForegroundColor White
    Write-Host ""
    Write-Host "If Docker Desktop is already open but not working:" -ForegroundColor Yellow
    Write-Host "- Try restarting Docker Desktop" -ForegroundColor White
    Write-Host "- Check Windows Services for Docker-related services" -ForegroundColor White
    Write-Host "- Restart your computer if the issue persists" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Docker is ready! You can now run:" -ForegroundColor Green
    Write-Host "  docker compose up -d" -ForegroundColor White
}

Write-Host ""


