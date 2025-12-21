# Windows UI Worker 启动脚本

Write-Host "🚀 启动Windows UI Worker..." -ForegroundColor Cyan
Write-Host ""

# 设置环境变量
$env:REDIS_URL="redis://localhost:6379/0"
$env:RQ_QUEUES="windows_ui"
$env:DATABASE_URL="postgresql://tester:tester123@localhost:5432/homemade_tester"

# 进入后端目录
Set-Location $PSScriptRoot

# 显示配置信息
Write-Host "📋 配置信息:" -ForegroundColor Yellow
Write-Host "   Redis: $env:REDIS_URL" -ForegroundColor Gray
Write-Host "   队列: $env:RQ_QUEUES" -ForegroundColor Gray
Write-Host "   数据库: $env:DATABASE_URL" -ForegroundColor Gray
Write-Host ""

# 检查Python是否可用
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: 找不到Python，请确保Python已安装并添加到PATH" -ForegroundColor Red
    pause
    exit 1
}

# 启动Worker
Write-Host "🔄 正在启动Worker..." -ForegroundColor Cyan
Write-Host ""

python -m app.worker.worker

