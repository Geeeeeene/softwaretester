# HomemadeTester 环境配置脚本 (PowerShell)
# 用于 Windows 系统

Write-Host "🚀 开始配置 HomemadeTester 环境..." -ForegroundColor Green
Write-Host ""

# 检查是否在项目根目录
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ 错误: 请在项目根目录运行此脚本" -ForegroundColor Red
    exit 1
}

# 配置后端环境
Write-Host "📝 配置后端环境..." -ForegroundColor Yellow
$backendEnvPath = "backend\.env"
$backendEnvExample = "backend\.env.example"

if (-not (Test-Path $backendEnvPath)) {
    if (Test-Path $backendEnvExample) {
        Copy-Item $backendEnvExample $backendEnvPath
        Write-Host "✅ 已创建 backend/.env（从 .env.example）" -ForegroundColor Green
    } else {
        # 创建默认的 .env 文件
        @"
# HomemadeTester 后端环境配置
PROJECT_NAME=HomemadeTester
VERSION=0.1.0
API_V1_STR=/api/v1

SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

DATABASE_URL=sqlite:///./homemade_tester.db
REDIS_URL=redis://localhost:6379/0

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=testpassword

BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:3000

ARTIFACT_STORAGE_PATH=./artifacts
MAX_UPLOAD_SIZE=104857600

TOOLS_BASE_PATH=backend/tools
"@ | Out-File -FilePath $backendEnvPath -Encoding UTF8
        Write-Host "✅ 已创建 backend/.env（默认配置）" -ForegroundColor Green
    }
} else {
    Write-Host "ℹ️  backend/.env 已存在，跳过" -ForegroundColor Cyan
}

# 配置前端环境
Write-Host "📝 配置前端环境..." -ForegroundColor Yellow
$frontendEnvPath = "frontend\.env"
$frontendEnvExample = "frontend\.env.example"

if (-not (Test-Path $frontendEnvPath)) {
    if (Test-Path $frontendEnvExample) {
        Copy-Item $frontendEnvExample $frontendEnvPath
        Write-Host "✅ 已创建 frontend/.env（从 .env.example）" -ForegroundColor Green
    } else {
        # 创建默认的 .env 文件
        @"
# HomemadeTester 前端环境配置
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
"@ | Out-File -FilePath $frontendEnvPath -Encoding UTF8
        Write-Host "✅ 已创建 frontend/.env（默认配置）" -ForegroundColor Green
    }
} else {
    Write-Host "ℹ️  frontend/.env 已存在，跳过" -ForegroundColor Cyan
}

# 创建 artifacts 目录
Write-Host "📁 创建必要的目录..." -ForegroundColor Yellow
$artifactsPath = "backend\artifacts"
if (-not (Test-Path $artifactsPath)) {
    New-Item -ItemType Directory -Path $artifactsPath -Force | Out-Null
    Write-Host "✅ 已创建 artifacts 目录" -ForegroundColor Green
} else {
    Write-Host "ℹ️  artifacts 目录已存在" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "✅ 环境配置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  1. 如需修改配置，请编辑 backend/.env 和 frontend/.env" -ForegroundColor White
Write-Host "  2. 使用 Docker Compose 启动: docker compose up -d" -ForegroundColor White
Write-Host "  3. 或使用启动脚本: .\start.bat" -ForegroundColor White
Write-Host ""

