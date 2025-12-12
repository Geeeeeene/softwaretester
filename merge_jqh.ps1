# PowerShell script to merge jqh branch into main
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "当前目录: $PWD" -ForegroundColor Green
Write-Host ""

Write-Host "正在获取远程分支..." -ForegroundColor Yellow
git fetch origin

Write-Host ""
Write-Host "切换到 main 分支..." -ForegroundColor Yellow
git checkout main

Write-Host ""
Write-Host "正在将 origin/jqh 分支合并到 main 分支..." -ForegroundColor Yellow
git merge origin/jqh -m "Merge jqh branch into main"

Write-Host ""
Write-Host "合并完成！" -ForegroundColor Green
Write-Host ""
Write-Host "查看合并后的状态:" -ForegroundColor Cyan
git status

Write-Host ""
Write-Host "最近的提交:" -ForegroundColor Cyan
git log --oneline -5

