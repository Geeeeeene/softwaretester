# Robot Framework + SikuliLibrary 安装脚本 (Windows)
# 用于配置Robot Framework和SikuliLibrary测试环境

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Robot Framework + SikuliLibrary 安装" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python是否安装
Write-Host "1. 检查Python环境..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python已安装: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python未安装或不在PATH中" -ForegroundColor Red
    Write-Host "  请先安装Python 3.8或更高版本: https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# 检查Java是否安装（SikuliX需要）
Write-Host ""
Write-Host "2. 检查Java环境..." -ForegroundColor Yellow
$javaCmd = Get-Command java -ErrorAction SilentlyContinue
if ($javaCmd) {
    $javaVersion = java -version 2>&1
    Write-Host "  ✓ Java已安装" -ForegroundColor Green
    $skipSikuli = $false
} else {
    Write-Host "  ✗ Java未安装或不在PATH中" -ForegroundColor Red
    Write-Host "  SikuliLibrary需要Java运行环境" -ForegroundColor Yellow
    Write-Host "  请安装Java JDK 8或更高版本: https://adoptium.net/" -ForegroundColor Yellow
    $continueWithoutJava = Read-Host "  是否继续安装（不包含SikuliLibrary）？ (y/N)"
    if ($continueWithoutJava -ne "y") {
        exit 1
    }
    $skipSikuli = $true
}

# 激活虚拟环境
Write-Host ""
Write-Host "3. 激活虚拟环境..." -ForegroundColor Yellow
$venvPath = "venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "  ✓ 虚拟环境已激活" -ForegroundColor Green
} else {
    Write-Host "  ⚠ 未找到虚拟环境，将使用全局Python环境" -ForegroundColor Yellow
}

# 安装Robot Framework
Write-Host ""
Write-Host "4. 安装Robot Framework..." -ForegroundColor Yellow
pip install --upgrade robotframework
if ($LASTEXITCODE -eq 0) {
    $robotVersion = robot --version 2>&1
    Write-Host "  ✓ Robot Framework安装成功" -ForegroundColor Green
} else {
    Write-Host "  ✗ Robot Framework安装失败" -ForegroundColor Red
    exit 1
}

# 安装SikuliLibrary
if (-not $skipSikuli) {
    Write-Host ""
    Write-Host "5. 下载并安装SikuliX..." -ForegroundColor Yellow
    
    $sikulixDir = "tools\sikulix"
    $sikulixJar = "$sikulixDir\sikulixide.jar"
    
    if (-not (Test-Path $sikulixDir)) {
        New-Item -ItemType Directory -Path $sikulixDir -Force | Out-Null
    }
    
    if (-not (Test-Path $sikulixJar)) {
        Write-Host "  下载SikuliX JAR文件..." -ForegroundColor Yellow
        $sikulixUrl = "https://launchpad.net/sikuli/sikulix/2.0.5/+download/sikulixide-2.0.5.jar"
        try {
            Invoke-WebRequest -Uri $sikulixUrl -OutFile $sikulixJar -ErrorAction Stop
            Write-Host "  ✓ SikuliX下载成功" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠ 自动下载失败，请手动下载SikuliX" -ForegroundColor Yellow
            Write-Host "  下载地址: https://raiman.github.io/SikuliX1/downloads.html" -ForegroundColor Yellow
            Write-Host "  下载后放置到: $sikulixJar" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✓ SikuliX已存在" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "6. 安装robotframework-SikuliLibrary..." -ForegroundColor Yellow
    pip install --upgrade robotframework-sikulilibrary
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ SikuliLibrary安装成功" -ForegroundColor Green
    } else {
        Write-Host "  ✗ SikuliLibrary安装失败" -ForegroundColor Red
        Write-Host "  可能需要手动配置Jython环境" -ForegroundColor Yellow
    }
}

# 安装其他依赖
Write-Host ""
Write-Host "7. 安装其他依赖..." -ForegroundColor Yellow
pip install --upgrade Pillow

# 创建资源目录
Write-Host ""
Write-Host "8. 创建测试资源目录..." -ForegroundColor Yellow
$resourceDirs = @(
    "artifacts\robot_framework",
    "artifacts\robot_framework\screenshots",
    "examples\robot_resources"
)

foreach ($dir in $resourceDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ 创建目录: $dir" -ForegroundColor Green
    }
}

# 验证安装
Write-Host ""
Write-Host "9. 验证安装..." -ForegroundColor Yellow

$allGood = $true

# 检查Robot Framework
$robotCmd = Get-Command robot -ErrorAction SilentlyContinue
if ($robotCmd) {
    Write-Host "  ✓ Robot Framework: 已安装" -ForegroundColor Green
} else {
    Write-Host "  ✗ Robot Framework: 未安装" -ForegroundColor Red
    $allGood = $false
}

# 检查SikuliLibrary
if (-not $skipSikuli) {
    python -c "import SikuliLibrary" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ SikuliLibrary: 已安装" -ForegroundColor Green
    } else {
        Write-Host "  ✗ SikuliLibrary: 未正确安装" -ForegroundColor Red
        $allGood = $false
    }
}

# 检查Pillow
python -c "import PIL" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Pillow: 已安装" -ForegroundColor Green
} else {
    Write-Host "  ✗ Pillow: 未安装" -ForegroundColor Red
    $allGood = $false
}

# 总结
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "✓ 安装完成！" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步:" -ForegroundColor Yellow
    Write-Host "1. 准备测试图像资源到 examples\robot_resources\ 目录" -ForegroundColor White
    Write-Host "2. 参考 examples\robot_framework_examples.json 创建测试用例" -ForegroundColor White
    Write-Host "3. 运行测试: robot your_test.robot" -ForegroundColor White
} else {
    Write-Host "⚠ 安装过程中遇到一些问题" -ForegroundColor Yellow
    Write-Host "请检查上面的错误信息并手动解决" -ForegroundColor Yellow
}
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 创建快速测试脚本
Write-Host "10. 创建快速测试脚本..." -ForegroundColor Yellow
$quickTestContent = @"
*** Settings ***
Library    OperatingSystem

*** Test Cases ***
简单测试
    [Documentation]    验证Robot Framework基本功能
    Log    Hello from Robot Framework!
    Should Be Equal    `${2+2}    4
"@

$quickTestFile = "examples\robot_quick_test.robot"
Set-Content -Path $quickTestFile -Value $quickTestContent -Encoding UTF8
Write-Host "  ✓ 创建快速测试文件: $quickTestFile" -ForegroundColor Green
Write-Host ""
Write-Host "运行快速测试: robot $quickTestFile" -ForegroundColor Cyan
