@echo off
chcp 65001 >nul
REM HomemadeTester 启动脚本（Windows）

echo [启动] 启动 HomemadeTester...

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Docker，请先安装Docker Desktop
    echo.
    echo 请访问 https://www.docker.com/products/docker-desktop 下载并安装
    pause
    exit /b 1
)

REM 检查Docker Compose（支持新旧两种格式）
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo [错误] 未检测到Docker Compose，请确保Docker Desktop已正确安装
        pause
        exit /b 1
    ) else (
        REM 使用旧版 docker-compose
        set DOCKER_COMPOSE_CMD=docker-compose
    )
) else (
    REM 使用新版 docker compose
    set DOCKER_COMPOSE_CMD=docker compose
)

REM 启动服务
echo [信息] 启动所有服务...
%DOCKER_COMPOSE_CMD% up -d

REM 等待服务启动
echo [信息] 等待服务启动...
timeout /t 5 /nobreak >nul

REM 检查服务状态
echo.
echo [信息] 服务状态:
%DOCKER_COMPOSE_CMD% ps

echo.
echo [完成] 启动完成！
echo.
echo 访问地址：
echo   前端:     http://localhost:5173
echo   API文档:  http://localhost:8000/docs
echo   Neo4j:    http://localhost:7474
echo.
echo 查看日志：
echo   %DOCKER_COMPOSE_CMD% logs -f
echo.
echo 停止服务：
echo   %DOCKER_COMPOSE_CMD% down
echo.

pause

