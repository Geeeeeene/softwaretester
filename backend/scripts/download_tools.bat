@echo off
REM 测试工具下载脚本 (批处理)
REM 调用 PowerShell 脚本执行下载

setlocal

echo ==========================================
echo   测试工具下载脚本
echo ==========================================
echo.

REM 检查 PowerShell 是否可用
powershell -Command "exit 0" >nul 2>&1
if errorlevel 1 (
    echo 错误: PowerShell 不可用
    exit /b 1
)

REM 获取脚本目录
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM 调用 PowerShell 脚本
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%\download_tools.ps1" %*

if errorlevel 1 (
    echo.
    echo 下载过程中出现错误
    exit /b 1
)

echo.
echo 下载完成！
pause


