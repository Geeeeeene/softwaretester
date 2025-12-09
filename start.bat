@echo off
REM HomemadeTester 启动脚本（Windows）

echo 🚀 启动 HomemadeTester...

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Docker，请先安装Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Docker Compose，请先安装Docker Desktop
    pause
    exit /b 1
)

REM 启动服务
echo 📦 启动所有服务...
docker-compose up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 5 /nobreak >nul

REM 检查服务状态
echo.
echo 📊 服务状态:
docker-compose ps

echo.
echo ✅ 启动完成！
echo.
echo 访问地址：
echo   前端:     http://localhost:5173
echo   API文档:  http://localhost:8000/docs
echo   Neo4j:    http://localhost:7474
echo.
echo 查看日志：
echo   docker-compose logs -f
echo.
echo 停止服务：
echo   docker-compose down
echo.

pause

