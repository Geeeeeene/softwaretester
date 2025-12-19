# Robot Framework 简化安装脚本
# 如果完整脚本有问题，使用这个简化版本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Robot Framework 简化安装" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python
Write-Host "检查Python..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "错误: Python未找到" -ForegroundColor Red
    exit 1
}
Write-Host "Python已安装" -ForegroundColor Green
Write-Host ""

# 安装Robot Framework
Write-Host "安装Robot Framework..." -ForegroundColor Yellow
pip install --upgrade robotframework
Write-Host ""

# 安装Pillow
Write-Host "安装Pillow..." -ForegroundColor Yellow
pip install --upgrade Pillow
Write-Host ""

# 安装SikuliLibrary (可选)
Write-Host "尝试安装SikuliLibrary..." -ForegroundColor Yellow
pip install --upgrade robotframework-sikulilibrary
Write-Host ""

# 创建目录
Write-Host "创建必要目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "artifacts\robot_framework" -Force | Out-Null
New-Item -ItemType Directory -Path "artifacts\robot_framework\screenshots" -Force | Out-Null
New-Item -ItemType Directory -Path "examples\robot_resources" -Force | Out-Null
Write-Host "目录创建完成" -ForegroundColor Green
Write-Host ""

# 验证安装
Write-Host "验证安装..." -ForegroundColor Yellow
$robotCmd = Get-Command robot -ErrorAction SilentlyContinue
if ($robotCmd) {
    Write-Host "✓ Robot Framework已安装" -ForegroundColor Green
} else {
    Write-Host "✗ Robot Framework安装失败" -ForegroundColor Red
}

python -c "import PIL" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Pillow已安装" -ForegroundColor Green
} else {
    Write-Host "✗ Pillow安装失败" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

