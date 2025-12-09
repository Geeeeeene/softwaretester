#!/bin/bash

# HomemadeTester 启动脚本（Linux/Mac）

echo "🚀 启动 HomemadeTester..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 未检测到Docker，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 未检测到Docker Compose，请先安装Docker Compose"
    exit 1
fi

# 启动服务
echo "📦 启动所有服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态:"
docker-compose ps

echo ""
echo "✅ 启动完成！"
echo ""
echo "访问地址："
echo "  前端:     http://localhost:5173"
echo "  API文档:  http://localhost:8000/docs"
echo "  Neo4j:    http://localhost:7474"
echo ""
echo "查看日志："
echo "  docker-compose logs -f"
echo ""
echo "停止服务："
echo "  docker-compose down"

