@echo off
echo ========================================
echo 启动后端服务
echo ========================================
echo.

REM 检查虚拟环境是否存在
if not exist "venv" (
    echo ❌ 虚拟环境不存在，请先运行 setup.bat
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 启动服务
echo 🚀 启动后端服务...
echo 访问地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

uvicorn app.main:app --reload --port 8000

