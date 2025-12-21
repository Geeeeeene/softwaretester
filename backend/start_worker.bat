@echo off
chcp 65001 >nul
echo 🚀 启动Windows UI Worker...
echo.

set REDIS_URL=redis://localhost:6379/0
set RQ_QUEUES=windows_ui
set DATABASE_URL=postgresql://tester:tester123@localhost:5432/homemade_tester

cd /d %~dp0

echo 📋 配置信息:
echo    Redis: %REDIS_URL%
echo    队列: %RQ_QUEUES%
echo    数据库: %DATABASE_URL%
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 找不到Python，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

echo 🔄 正在启动Worker...
echo.

python -m app.worker.worker

pause

