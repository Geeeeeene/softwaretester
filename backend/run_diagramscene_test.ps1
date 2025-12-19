# DiagramScene 测试快速运行脚本
# 用于快速执行DiagramScene流程图编辑器的自动化测试

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Qt DiagramScene 自动化测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查测试文件
if (-not (Test-Path "test_diagramscene.robot")) {
    Write-Host "错误: 找不到 test_diagramscene.robot" -ForegroundColor Red
    Write-Host "请确认在 backend 目录中运行此脚本" -ForegroundColor Yellow
    exit 1
}

# 检查图像资源
if (-not (Test-Path "examples\robot_resources\main_window.png")) {
    Write-Host "警告: 找不到 main_window.png" -ForegroundColor Yellow
    Write-Host "请确保已将主窗口截图放在 examples\robot_resources\ 目录中" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "准备运行测试..." -ForegroundColor Yellow
Write-Host "测试文件: test_diagramscene.robot" -ForegroundColor White
Write-Host "应用路径: C:\Users\lenovo\Desktop\diagramscene_ultima\...\diagramscene.exe" -ForegroundColor White
Write-Host ""

# 显示菜单
Write-Host "请选择要运行的测试:" -ForegroundColor Cyan
Write-Host "1. 运行所有测试" -ForegroundColor White
Write-Host "2. 只运行启动测试 (测试1)" -ForegroundColor White
Write-Host "3. 只运行交互测试 (测试2)" -ForegroundColor White
Write-Host "4. 只运行smoke标签的测试" -ForegroundColor White
Write-Host "Q. 退出" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 (1-4/Q)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "运行所有测试..." -ForegroundColor Green
        py -m robot test_diagramscene.robot
    }
    "2" {
        Write-Host ""
        Write-Host "运行测试1: 验证应用启动..." -ForegroundColor Green
        py -m robot --test "测试1-验证应用启动" test_diagramscene.robot
    }
    "3" {
        Write-Host ""
        Write-Host "运行测试2: 简单交互测试..." -ForegroundColor Green
        py -m robot --test "测试2-简单交互测试" test_diagramscene.robot
    }
    "4" {
        Write-Host ""
        Write-Host "运行smoke测试..." -ForegroundColor Green
        py -m robot --include smoke test_diagramscene.robot
    }
    "Q" {
        Write-Host "退出" -ForegroundColor Yellow
        exit 0
    }
    "q" {
        Write-Host "退出" -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "无效选项" -ForegroundColor Red
        exit 1
    }
}

# 测试完成后的提示
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试执行完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "查看测试结果:" -ForegroundColor Yellow
Write-Host "1. 在浏览器中打开 log.html 查看详细日志" -ForegroundColor White
Write-Host "2. 在浏览器中打开 report.html 查看测试报告" -ForegroundColor White
Write-Host "3. 查看 artifacts\robot_framework\screenshots\ 目录中的截图" -ForegroundColor White
Write-Host ""

$openReport = Read-Host "是否打开测试报告? (y/N)"
if ($openReport -eq "y" -or $openReport -eq "Y") {
    if (Test-Path "log.html") {
        Write-Host "正在打开测试日志..." -ForegroundColor Green
        Start-Process "log.html"
    } else {
        Write-Host "未找到 log.html 文件" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "感谢使用！" -ForegroundColor Cyan

