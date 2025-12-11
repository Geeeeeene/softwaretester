# HomemadeTester 启动脚本（PowerShell）

Write-Host "🚀 启动 HomemadeTester..." -ForegroundColor Cyan

# 检查Docker是否安装
$dockerInstalled = $false
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker 已安装: $dockerVersion" -ForegroundColor Green
        $dockerInstalled = $true
    }
} catch {
    Write-Host "❌ 未检测到Docker" -ForegroundColor Red
}

if (-not $dockerInstalled) {
    Write-Host ""
    Write-Host "请先安装 Docker Desktop:" -ForegroundColor Yellow
    Write-Host "  1. 访问 https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Write-Host "  2. 下载并安装 Docker Desktop for Windows" -ForegroundColor Yellow
    Write-Host "  3. 安装后重启此脚本" -ForegroundColor Yellow
    Read-Host "按 Enter 键退出"
    exit 1
}

# 检查Docker Compose（支持新旧两种格式）
$composeCmd = $null

# 尝试新版本 docker compose
try {
    $null = docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $composeCmd = "docker compose"
        Write-Host "✅ 使用 Docker Compose (新版本)" -ForegroundColor Green
    }
} catch {
    # 忽略错误，继续尝试旧版本
}

# 尝试旧版本 docker-compose
if (-not $composeCmd) {
    try {
        $null = docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $composeCmd = "docker-compose"
            Write-Host "✅ 使用 Docker Compose (旧版本)" -ForegroundColor Green
        }
    } catch {
        # 忽略错误
    }
}

if (-not $composeCmd) {
    Write-Host "❌ 未检测到 Docker Compose" -ForegroundColor Red
    Write-Host "请确保 Docker Desktop 已正确安装并包含 Compose 插件" -ForegroundColor Yellow
    Read-Host "按 Enter 键退出"
    exit 1
}

# 检查Docker是否运行
try {
    $null = docker ps 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Docker 未运行，请启动 Docker Desktop" -ForegroundColor Yellow
        Write-Host "等待 Docker 启动..." -ForegroundColor Yellow
        
        # 等待Docker启动（最多等待30秒）
        $maxWait = 30
        $waited = 0
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 2
            $waited += 2
            try {
                $null = docker ps 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ Docker 已启动" -ForegroundColor Green
                    break
                }
            } catch {
                # 继续等待
            }
        }
        
        if ($waited -ge $maxWait) {
            Write-Host "❌ Docker 启动超时，请手动启动 Docker Desktop" -ForegroundColor Red
            Read-Host "按 Enter 键退出"
            exit 1
        }
    }
} catch {
    Write-Host "❌ 无法连接到 Docker，请确保 Docker Desktop 正在运行" -ForegroundColor Red
    Read-Host "按 Enter 键退出"
    exit 1
}

# 启动服务
Write-Host ""
Write-Host "📦 启动所有服务..." -ForegroundColor Cyan
Invoke-Expression "$composeCmd up -d"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 服务启动失败" -ForegroundColor Red
    Read-Host "按 Enter 键退出"
    exit 1
}

# 等待服务启动
Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 检查服务状态
Write-Host ""
Write-Host "📊 服务状态:" -ForegroundColor Cyan
Invoke-Expression "$composeCmd ps"

Write-Host ""
Write-Host "✅ 启动完成！" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址：" -ForegroundColor Cyan
Write-Host "  前端:     http://localhost:5173" -ForegroundColor White
Write-Host "  API文档:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Neo4j:    http://localhost:7474" -ForegroundColor White
Write-Host ""
Write-Host "查看日志：" -ForegroundColor Cyan
Write-Host "  $composeCmd logs -f" -ForegroundColor White
Write-Host ""
Write-Host "停止服务：" -ForegroundColor Cyan
Write-Host "  $composeCmd down" -ForegroundColor White
Write-Host ""

Read-Host "按 Enter 键退出"

