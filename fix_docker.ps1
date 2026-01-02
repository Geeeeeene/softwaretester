# Docker Connection Fix Script
# Fixes Docker Desktop connection issues

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== Docker Connection Diagnostic and Fix ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Docker command
Write-Host "Step 1: Checking Docker command..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Docker installed: $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Docker not installed or not in PATH" -ForegroundColor Red
        Write-Host "   Please visit https://www.docker.com/products/docker-desktop to download" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "   [ERROR] Docker command unavailable: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Check Docker service status
Write-Host ""
Write-Host "Step 2: Checking Docker service status..." -ForegroundColor Yellow
try {
    $null = docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Docker service is running" -ForegroundColor Green
        Write-Host "   You can now use Docker Compose" -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "   [ERROR] Docker service is not running or cannot connect" -ForegroundColor Red
    }
} catch {
    Write-Host "   [ERROR] Cannot connect to Docker: $_" -ForegroundColor Red
}

# Step 3: Try to start Docker Desktop
Write-Host ""
Write-Host "Step 3: Attempting to start Docker Desktop..." -ForegroundColor Yellow

# Find Docker Desktop installation path
$dockerDesktopPath = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
if (-not (Test-Path $dockerDesktopPath)) {
    $dockerDesktopPath = "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
}

if (Test-Path $dockerDesktopPath) {
    Write-Host "   Found Docker Desktop: $dockerDesktopPath" -ForegroundColor Cyan
    
    # Check if already running
    $dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if ($dockerProcess) {
        Write-Host "   [WARNING] Docker Desktop process exists but service may not be ready" -ForegroundColor Yellow
        Write-Host "   Waiting for Docker service to start..." -ForegroundColor Yellow
    } else {
        Write-Host "   Starting Docker Desktop..." -ForegroundColor Cyan
        Start-Process -FilePath $dockerDesktopPath -WindowStyle Hidden
        Write-Host "   Docker Desktop started, waiting for service to be ready..." -ForegroundColor Yellow
    }
    
    # Wait for Docker service to be ready (max 60 seconds)
    $maxWaitTime = 60
    $waitInterval = 2
    $elapsedTime = 0
    $dockerReady = $false
    
    while ($elapsedTime -lt $maxWaitTime) {
        Start-Sleep -Seconds $waitInterval
        $elapsedTime += $waitInterval
        
        try {
            $null = docker info 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $dockerReady = $true
                break
            }
        } catch {
            # Continue waiting
        }
        
        $progress = "[$elapsedTime/$maxWaitTime seconds]"
        Write-Host "   Waiting... $progress" -ForegroundColor Gray
    }
    
    if ($dockerReady) {
        Write-Host "   [OK] Docker service is ready!" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Docker service failed to start within $maxWaitTime seconds" -ForegroundColor Red
        Write-Host ""
        Write-Host "   Please manually:" -ForegroundColor Yellow
        Write-Host "   1. Open Docker Desktop application" -ForegroundColor White
        Write-Host "   2. Wait for Docker Desktop to fully start (system tray icon stops animating)" -ForegroundColor White
        Write-Host "   3. Then run: docker compose up -d" -ForegroundColor White
        exit 1
    }
} else {
    Write-Host "   [ERROR] Docker Desktop installation path not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Please manually:" -ForegroundColor Yellow
    Write-Host "   1. Open Docker Desktop application" -ForegroundColor White
    Write-Host "   2. Wait for Docker Desktop to fully start" -ForegroundColor White
    Write-Host "   3. Then run: docker compose up -d" -ForegroundColor White
    exit 1
}

# Step 4: Verify Docker Compose
Write-Host ""
Write-Host "Step 4: Verifying Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Docker Compose available: $composeVersion" -ForegroundColor Green
    } else {
        Write-Host "   [WARNING] Docker Compose (new) not available, trying old version..." -ForegroundColor Yellow
        $composeVersion = docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   [OK] Docker Compose (old) available: $composeVersion" -ForegroundColor Green
        } else {
            Write-Host "   [ERROR] Docker Compose not available" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "   [ERROR] Docker Compose check failed: $_" -ForegroundColor Red
    exit 1
}

# Step 5: Test Docker Compose connection
Write-Host ""
Write-Host "Step 5: Testing Docker Compose connection..." -ForegroundColor Yellow
try {
    $null = docker compose ps 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Docker Compose connection is normal" -ForegroundColor Green
    } else {
        Write-Host "   [INFO] Docker Compose test completed (no running containers)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   [WARNING] Docker Compose test warning: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Fix Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run:" -ForegroundColor Cyan
Write-Host "  docker compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "Or use the start script:" -ForegroundColor Cyan
Write-Host "  .\start.ps1" -ForegroundColor White
Write-Host ""
