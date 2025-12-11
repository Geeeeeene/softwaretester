@echo off
echo ========================================
echo 后端环境设置脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

echo ✅ Python已安装
python --version
echo.

REM 检查虚拟环境是否存在
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
) else (
    echo ✅ 虚拟环境已存在
)
echo.

REM 激活虚拟环境
echo 🔄 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b 1
)
echo ✅ 虚拟环境已激活
echo.

REM 升级pip
echo 📦 升级pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

REM 安装依赖
echo 📦 安装依赖包（这可能需要几分钟）...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo.

echo ========================================
echo ✅ 环境设置完成！
echo ========================================
echo.
echo 下一步：
echo 1. 运行: uvicorn app.main:app --reload --port 8000
echo 2. 或者运行: python -m uvicorn app.main:app --reload --port 8000
echo.
pause

