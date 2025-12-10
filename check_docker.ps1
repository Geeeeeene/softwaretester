# Docker 环境检查脚本

Write-Host "=== Docker 环境检查 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Docker 命令
Write-Host "1. 检查 Docker 命令..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Docker 已安装: $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Docker 未安装或不在 PATH 中" -ForegroundColor Red
        Write-Host "   请访问 https://www.docker.com/products/docker-desktop 下载安装" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "   ❌ Docker 命令不可用: $_" -ForegroundColor Red
    exit 1
}

# 2. 检查 Docker Compose（新版本）
Write-Host ""
Write-Host "2. 检查 Docker Compose..." -ForegroundColor Yellow
$composeAvailable = $false
$composeCmd = $null

try {
    $composeVersion = docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Docker Compose (新版本) 可用: $composeVersion" -ForegroundColor Green
        $composeAvailable = $true
        $composeCmd = "docker compose"
    }
} catch {
    Write-Host "   ⚠️  Docker Compose (新版本) 不可用" -ForegroundColor Yellow
}

# 3. 检查 Docker Compose（旧版本）
if (-not $composeAvailable) {
    try {
        $composeVersion = docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Docker Compose (旧版本) 可用: $composeVersion" -ForegroundColor Green
            $composeAvailable = $true
            $composeCmd = "docker-compose"
        }
    } catch {
        Write-Host "   ❌ Docker Compose (旧版本) 也不可用" -ForegroundColor Red
    }
}

if (-not $composeAvailable) {
    Write-Host ""
    Write-Host "❌ 未找到 Docker Compose" -ForegroundColor Red
    Write-Host "请确保 Docker Desktop 已正确安装并包含 Compose 插件" -ForegroundColor Yellow
    exit 1
}

# 4. 检查 Docker 是否运行
Write-Host ""
Write-Host "3. 检查 Docker 服务状态..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Docker 服务正在运行" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Docker 服务未运行" -ForegroundColor Red
        Write-Host "   请启动 Docker Desktop" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "   ❌ 无法连接到 Docker: $_" -ForegroundColor Red
    Write-Host "   请确保 Docker Desktop 正在运行" -ForegroundColor Yellow
    exit 1
}

# 5. 测试 docker compose 命令
Write-Host ""
Write-Host "4. 测试 Docker Compose 命令..." -ForegroundColor Yellow
try {
    $testOutput = Invoke-Expression "$composeCmd version" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Docker Compose 命令可用" -ForegroundColor Green
        Write-Host "   使用命令: $composeCmd" -ForegroundColor Cyan
    } else {
        Write-Host "   ❌ Docker Compose 命令测试失败" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Docker Compose 命令执行错误: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== 检查完成 ===" -ForegroundColor Green
Write-Host ""
Write-Host "可以使用以下命令启动项目:" -ForegroundColor Cyan
Write-Host "  $composeCmd up -d" -ForegroundColor White
Write-Host ""
Write-Host "或运行启动脚本:" -ForegroundColor Cyan
Write-Host "  .\start.ps1" -ForegroundColor White
Write-Host ""

