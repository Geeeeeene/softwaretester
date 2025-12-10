# HomemadeTester 项目启动脚本
# 同时启动后端和前端服务

Write-Host "🚀 启动 HomemadeTester 项目..." -ForegroundColor Cyan
Write-Host ""

# 检查后端服务是否已在运行
$backendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $backendRunning = $true
        Write-Host "✅ 后端服务已在运行" -ForegroundColor Green
    }
} catch {
    $backendRunning = $false
}

# 启动后端服务（如果未运行）
if (-not $backendRunning) {
    Write-Host "📦 启动后端服务..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; .\venv\Scripts\activate; uvicorn app.main:app --reload --port 8000" -WindowStyle Normal
    Write-Host "⏳ 等待后端服务启动..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
} else {
    Write-Host "✅ 后端服务已在运行" -ForegroundColor Green
}

# 启动前端服务
Write-Host "🎨 启动前端服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host "✅ 项目启动完成！" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址：" -ForegroundColor Cyan
Write-Host "  前端:     http://localhost:5173" -ForegroundColor White
Write-Host "  API文档:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  健康检查: http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "提示:" -ForegroundColor Yellow
Write-Host "  - 后端和前端服务已在新的 PowerShell 窗口中启动" -ForegroundColor Gray
Write-Host "  - 关闭对应的窗口即可停止服务" -ForegroundColor Gray
Write-Host ""

