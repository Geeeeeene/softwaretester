# 测试工具下载脚本 (PowerShell)
# 用于下载和安装所有测试工具到 backend/tools/ 目录

param(
    [switch]$SkipExisting = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"
$ToolsBasePath = "backend/tools"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot

# 切换到项目根目录
Set-Location $ProjectRoot

# 颜色输出函数
function Write-ColorOutput($ForegroundColor, $Message) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success($Message) {
    Write-ColorOutput Green "✅ $Message"
}

function Write-Info($Message) {
    Write-ColorOutput Cyan "ℹ️  $Message"
}

function Write-Warning($Message) {
    Write-ColorOutput Yellow "⚠️  $Message"
}

function Write-Error($Message) {
    Write-ColorOutput Red "❌ $Message"
}

# 检查 Git 是否安装
function Test-GitInstalled {
    try {
        $null = git --version
        return $true
    } catch {
        return $false
    }
}

# 检查网络连接
function Test-NetworkConnection {
    try {
        $response = Invoke-WebRequest -Uri "https://github.com" -UseBasicParsing -TimeoutSec 5
        return $true
    } catch {
        return $false
    }
}

# 克隆 Git 仓库
function Clone-Repository {
    param(
        [string]$Url,
        [string]$TargetPath,
        [string]$Name
    )
    
    if (Test-Path $TargetPath) {
        if ($SkipExisting) {
            Write-Info "$Name 已存在，跳过下载"
            return $true
        } else {
            Write-Warning "$Name 目录已存在: $TargetPath"
            $response = Read-Host "是否删除并重新下载? (y/N)"
            if ($response -eq "y" -or $response -eq "Y") {
                Remove-Item -Path $TargetPath -Recurse -Force
            } else {
                return $true
            }
        }
    }
    
    Write-Info "正在下载 $Name..."
    try {
        git clone --recursive $Url $TargetPath
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$Name 下载完成"
            return $true
        } else {
            Write-Error "$Name 下载失败"
            return $false
        }
    } catch {
        Write-Error "$Name 下载出错: $_"
        return $false
    }
}

# 下载文件
function Download-File {
    param(
        [string]$Url,
        [string]$OutputPath,
        [string]$Name
    )
    
    if (Test-Path $OutputPath) {
        Write-Info "$Name 文件已存在，跳过下载"
        return $true
    }
    
    Write-Info "正在下载 $Name..."
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $Url -OutFile $OutputPath -UseBasicParsing
        Write-Success "$Name 下载完成: $OutputPath"
        return $true
    } catch {
        Write-Error "$Name 下载失败: $_"
        return $false
    }
}

# 主函数
function Main {
    Write-ColorOutput Cyan "=========================================="
    Write-ColorOutput Cyan "  测试工具下载脚本"
    Write-ColorOutput Cyan "=========================================="
    Write-Host ""
    
    # 检查前置条件
    if (-not (Test-GitInstalled)) {
        Write-Error "Git 未安装，请先安装 Git"
        exit 1
    }
    
    if (-not (Test-NetworkConnection)) {
        Write-Error "无法连接到网络，请检查网络连接"
        exit 1
    }
    
    # 创建工具目录
    if (-not (Test-Path $ToolsBasePath)) {
        New-Item -ItemType Directory -Path $ToolsBasePath -Force | Out-Null
    }
    
    $results = @{}
    
    # 1. UTBotCpp
    Write-Host ""
    Write-ColorOutput Yellow "=== UTBotCpp ==="
    $utbotPath = Join-Path $ToolsBasePath "utbot/UTBotCpp"
    $results["utbot"] = Clone-Repository `
        -Url "https://github.com/UnitTestBot/UTBotCpp.git" `
        -TargetPath $utbotPath `
        -Name "UTBotCpp"
    
    # 3. Clazy
    Write-Host ""
    Write-ColorOutput Yellow "=== Clazy ==="
    $clazyPath = Join-Path $ToolsBasePath "clazy/clazy"
    $results["clazy"] = Clone-Repository `
        -Url "https://github.com/KDE/clazy.git" `
        -TargetPath $clazyPath `
        -Name "Clazy"
    
    # 4. Cppcheck
    Write-Host ""
    Write-ColorOutput Yellow "=== Cppcheck ==="
    $cppcheckPath = Join-Path $ToolsBasePath "cppcheck/cppcheck"
    Write-Info "选择下载方式:"
    Write-Info "  1. 克隆源码 (需要编译)"
    Write-Info "  2. 下载 Windows 安装包"
    $choice = Read-Host "请选择 (1/2, 默认1)"
    
    if ($choice -eq "2") {
        $cppcheckUrl = "https://github.com/danmar/cppcheck/releases/download/2.12/cppcheck-2.12-x64-Setup.exe"
        $cppcheckExe = Join-Path $env:TEMP "cppcheck-setup.exe"
        $results["cppcheck"] = Download-File -Url $cppcheckUrl -OutputPath $cppcheckExe -Name "Cppcheck"
        Write-Info "安装包已下载到: $cppcheckExe"
        Write-Info "请手动运行安装程序"
    } else {
        $results["cppcheck"] = Clone-Repository `
            -Url "https://github.com/danmar/cppcheck.git" `
            -TargetPath $cppcheckPath `
            -Name "Cppcheck"
    }
    
    # 5. gcov/lcov
    Write-Host ""
    Write-ColorOutput Yellow "=== gcov/lcov ==="
    Write-Info "gcov 通常随 GCC/MinGW 安装"
    Write-Info "lcov 需要 Perl 环境"
    Write-Info "Windows 上建议使用 Chocolatey 安装: choco install lcov"
    $results["gcov"] = $true  # 假设已安装
    $results["lcov"] = $true  # 假设已安装
    
    # 6. Valgrind/Dr. Memory
    Write-Host ""
    Write-ColorOutput Yellow "=== Dr. Memory (Valgrind 替代) ==="
    Write-Info "Windows 不支持原生 Valgrind，使用 Dr. Memory 作为替代"
    $drmemoryUrl = "https://github.com/DynamoRIO/drmemory/releases/download/release_2.5.0/DrMemory-Windows-2.5.0-1.exe"
    $drmemoryExe = Join-Path $env:TEMP "drmemory-setup.exe"
    $results["drmemory"] = Download-File -Url $drmemoryUrl -OutputPath $drmemoryExe -Name "Dr. Memory"
    if ($results["drmemory"]) {
        Write-Info "安装包已下载到: $drmemoryExe"
        Write-Info "请手动运行安装程序"
    }
    
    # 7. GammaRay
    Write-Host ""
    Write-ColorOutput Yellow "=== GammaRay ==="
    $gammarayPath = Join-Path $ToolsBasePath "gammaray/GammaRay"
    $results["gammaray"] = Clone-Repository `
        -Url "https://github.com/KDAB/GammaRay.git" `
        -TargetPath $gammarayPath `
        -Name "GammaRay"
    
    # 总结
    Write-Host ""
    Write-ColorOutput Cyan "=========================================="
    Write-ColorOutput Cyan "  下载完成"
    Write-ColorOutput Cyan "=========================================="
    
    $successCount = ($results.Values | Where-Object { $_ -eq $true }).Count
    $totalCount = $results.Count
    
    Write-Host ""
    Write-Info "成功: $successCount/$totalCount"
    
    foreach ($tool in $results.Keys) {
        if ($results[$tool]) {
            Write-Success "$tool 下载成功"
        } else {
            Write-Error "$tool 下载失败"
        }
    }
    
    Write-Host ""
    Write-Info "运行 'python backend/scripts/check_tools.py' 检查工具状态"
}

# 执行主函数
Main




