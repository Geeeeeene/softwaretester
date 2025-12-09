# 工具完整性检测脚本
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  工具完整性检测报告" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$tools = @(
    @{
        Name = "Spix"
        Path = "backend/tools/spix/spix"
        KeyFiles = @("CMakeLists.txt", "README.md", "LICENSE.txt")
        ExpectedFiles = 100
    },
    @{
        Name = "UTBotCpp"
        Path = "backend/tools/utbot/UTBotCpp"
        KeyFiles = @("CMakeLists.txt", "README.md")
        ExpectedFiles = 1000
        Submodules = @("submodules")
    },
    @{
        Name = "Clazy"
        Path = "backend/tools/clazy/clazy"
        KeyFiles = @("CMakeLists.txt", "README.md")
        ExpectedFiles = 500
    },
    @{
        Name = "Cppcheck"
        Path = "backend/tools/cppcheck/cppcheck"
        KeyFiles = @("CMakeLists.txt", "README.md")
        ExpectedFiles = 500
    },
    @{
        Name = "GammaRay"
        Path = "backend/tools/gammaray/GammaRay"
        KeyFiles = @("CMakeLists.txt", "README.md")
        ExpectedFiles = 1000
        Submodules = @("3rdparty")
    }
)

$allComplete = $true

foreach ($tool in $tools) {
    Write-Host "检查 $($tool.Name)..." -ForegroundColor Yellow
    
    $toolPath = $tool.Path
    $exists = Test-Path $toolPath
    
    if (-not $exists) {
        Write-Host "  ❌ 目录不存在: $toolPath" -ForegroundColor Red
        $allComplete = $false
        Write-Host ""
        continue
    }
    
    Write-Host "  ✓ 目录存在" -ForegroundColor Green
    
    # 检查关键文件
    $missingFiles = @()
    foreach ($keyFile in $tool.KeyFiles) {
        $filePath = Join-Path $toolPath $keyFile
        if (-not (Test-Path $filePath)) {
            $missingFiles += $keyFile
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Host "  ⚠️  缺少关键文件: $($missingFiles -join ', ')" -ForegroundColor Yellow
    } else {
        Write-Host "  ✓ 所有关键文件存在" -ForegroundColor Green
    }
    
    # 检查子模块
    if ($tool.Submodules) {
        foreach ($submodule in $tool.Submodules) {
            $submodulePath = Join-Path $toolPath $submodule
            if (Test-Path $submodulePath) {
                $submoduleFiles = (Get-ChildItem -Path $submodulePath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
                Write-Host "  ✓ 子模块 $submodule 存在 ($submoduleFiles 个文件)" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  子模块 $submodule 不存在" -ForegroundColor Yellow
            }
        }
    }
    
    # 统计文件数量
    $fileCount = (Get-ChildItem -Path $toolPath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host "  📊 文件总数: $fileCount"
    
    if ($fileCount -lt $tool.ExpectedFiles) {
        Write-Host "  ⚠️  文件数量可能不完整 (期望至少 $($tool.ExpectedFiles) 个文件)" -ForegroundColor Yellow
    } else {
        Write-Host "  ✓ 文件数量正常" -ForegroundColor Green
    }
    
    # 检查是否有 .git 目录（说明是完整的 git 仓库）
    $gitPath = Join-Path $toolPath ".git"
    if (Test-Path $gitPath) {
        Write-Host "  [INFO] Contains .git directory (complete git repository)" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

Write-Host "==========================================" -ForegroundColor Cyan
if ($allComplete) {
    Write-Host "✅ 所有工具检测完成" -ForegroundColor Green
} else {
    Write-Host "❌ 部分工具不完整" -ForegroundColor Red
}
Write-Host "==========================================" -ForegroundColor Cyan

