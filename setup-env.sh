#!/bin/bash
# HomemadeTester 环境配置脚本 (Bash)
# 用于 Linux/Mac 系统

echo "🚀 开始配置 HomemadeTester 环境..."
echo ""

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 配置后端环境
echo "📝 配置后端环境..."
if [ ! -f "backend/.env" ]; then
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo "✅ 已创建 backend/.env（从 .env.example）"
    else
        # 创建默认的 .env 文件
        cat > backend/.env << 'EOF'
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
EOF
        echo "✅ 已创建 backend/.env（默认配置）"
    fi
else
    echo "ℹ️  backend/.env 已存在，跳过"
fi

# 配置前端环境
echo "📝 配置前端环境..."
if [ ! -f "frontend/.env" ]; then
    if [ -f "frontend/.env.example" ]; then
        cp frontend/.env.example frontend/.env
        echo "✅ 已创建 frontend/.env（从 .env.example）"
    else
        # 创建默认的 .env 文件
        cat > frontend/.env << 'EOF'
# HomemadeTester 前端环境配置
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
EOF
        echo "✅ 已创建 frontend/.env（默认配置）"
    fi
else
    echo "ℹ️  frontend/.env 已存在，跳过"
fi

# 创建 artifacts 目录
echo "📁 创建必要的目录..."
if [ ! -d "backend/artifacts" ]; then
    mkdir -p backend/artifacts
    echo "✅ 已创建 artifacts 目录"
else
    echo "ℹ️  artifacts 目录已存在"
fi

echo ""
echo "✅ 环境配置完成！"
echo ""
echo "下一步："
echo "  1. 如需修改配置，请编辑 backend/.env 和 frontend/.env"
echo "  2. 使用 Docker Compose 启动: docker compose up -d"
echo "  3. 或使用启动脚本: ./start.sh"
echo ""

