@echo off
chcp 65001
cd /d "%~dp0"
echo 当前目录：%CD%
echo.
echo 正在获取远程分支...
git fetch origin
echo.
echo 当前在 main 分支
git checkout main
echo.
echo 正在将 jqh 分支合并到 main 分支...
git merge origin/jqh
echo.
echo 合并完成！
echo.
pause

