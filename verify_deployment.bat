@echo off
REM HomemadeTester 部署验证脚本

echo ========================================
echo HomemadeTester 部署验证
echo ========================================
echo.

echo [1] 检查 Docker 容器状态...
docker-compose ps
echo.

echo [2] 检查服务健康状态...
docker-compose ps --format "table {{.Service}}\t{{.Status}}"
echo.

echo [3] 检查后端 API...
curl -s http://localhost:8000/api/v1/projects >nul 2>&1
if %errorlevel% equ 0 (
    echo    后端 API 可访问
    echo    API 文档: http://localhost:8000/docs
) else (
    echo    后端 API 无法访问
)
echo.

echo [4] 检查前端...
curl -s http://localhost:5173 >nul 2>&1
if %errorlevel% equ 0 (
    echo    前端可访问
    echo    前端地址: http://localhost:5173
) else (
    echo    前端无法访问
)
echo.

echo [5] 检查数据库连接...
docker-compose exec -T postgres pg_isready -U tester >nul 2>&1
if %errorlevel% equ 0 (
    echo    PostgreSQL 数据库连接正常
) else (
    echo    PostgreSQL 数据库连接失败
)
echo.

echo [6] 检查 Redis...
docker-compose exec -T redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo    Redis 连接正常
) else (
    echo    Redis 连接失败
)
echo.

echo ========================================
echo 验证完成！
echo ========================================
echo.
echo 访问地址:
echo   前端:     http://localhost:5173
echo   API文档:   http://localhost:8000/docs
echo   Neo4j:    http://localhost:7474
echo.
echo 查看日志:
echo   docker-compose logs -f
echo   docker-compose logs -f backend
echo.
pause

