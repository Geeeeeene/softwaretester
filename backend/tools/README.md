# 测试工具目录

本目录包含所有测试工具的统一管理。所有工具都下载到 `backend/tools/` 目录下，便于版本控制和统一配置。

## 目录结构

```
backend/tools/
├── spix/              # Spix UI 测试框架
│   └── spix/
├── utbot/             # UTBotCpp 单元测试工具
│   └── UTBotCpp/
├── clazy/             # Clazy 静态分析工具
│   └── clazy/
├── cppcheck/          # Cppcheck 静态分析工具
│   └── cppcheck/
├── gcov-lcov/         # 代码覆盖率工具
├── valgrind/          # Valgrind 或替代工具
│   └── drmemory/      # Dr. Memory (Windows 替代)
└── gammaray/          # GammaRay Qt 调试工具
    └── GammaRay/
```

## 工具列表

### 1. Spix

**用途**: Qt/QML 应用 UI 测试框架

**状态**: ✅ 已下载（从 `backend/spix/` 移动）

**官方文档**: https://github.com/faaxm/spix

**使用说明**:
- Spix 是一个最小侵入性的 UI 测试库
- 支持通过 C++ 代码或 HTTP RPC 接口控制 Qt/QML 应用
- 需要编译后才能使用

**编译步骤**:
```bash
cd backend/tools/spix/spix
mkdir build
cd build
cmake ..
cmake --build .
```

**配置路径**: `SPIX_PATH` (在 `backend/app/core/config.py` 中配置)

---

### 2. UTBotCpp

**用途**: C++ 单元测试自动生成工具

**状态**: ❌ 需要下载

**官方文档**: https://github.com/UnitTestBot/UTBotCpp

**下载方式**:
```bash
# 使用下载脚本
.\backend\scripts\download_tools.ps1

# 或手动克隆
git clone --recursive https://github.com/UnitTestBot/UTBotCpp.git backend/tools/utbot/UTBotCpp
```

**依赖项**:
- CMake 3.18+
- C++ 编译器 (GCC/Clang/MSVC)
- LLVM (用于代码分析)

**编译步骤**:
```bash
cd backend/tools/utbot/UTBotCpp
mkdir build
cd build
cmake ..
cmake --build .
```

**配置路径**: `UTBOT_PATH`, `UTBOT_EXECUTABLE`

---

### 3. Clazy

**用途**: Qt 代码静态分析工具（基于 Clang）

**状态**: ❌ 需要下载

**官方文档**: https://github.com/KDE/clazy

**下载方式**:
```bash
git clone https://github.com/KDE/clazy.git backend/tools/clazy/clazy
```

**依赖项**:
- Clang/LLVM
- Qt 开发库
- CMake

**Windows 安装说明**:
1. 安装 LLVM: https://llvm.org/builds/
2. 安装 Qt: https://www.qt.io/download
3. 编译 Clazy:
```bash
cd backend/tools/clazy/clazy
mkdir build
cd build
cmake -DCMAKE_PREFIX_PATH="C:/Qt/6.x.x/msvc2019_64" ..
cmake --build .
```

**配置路径**: `CLAZY_PATH`, `CLAZY_EXECUTABLE`

---

### 4. Cppcheck

**用途**: C/C++ 静态代码分析工具

**状态**: ❌ 需要下载

**官方文档**: https://github.com/danmar/cppcheck

**下载方式**:

**方式1: 下载 Windows 安装包（推荐）**
- 从 https://github.com/danmar/cppcheck/releases 下载最新版本
- 运行安装程序

**方式2: 克隆源码**
```bash
git clone https://github.com/danmar/cppcheck.git backend/tools/cppcheck/cppcheck
```

**编译步骤** (如果使用源码):
```bash
cd backend/tools/cppcheck/cppcheck
# 使用 Visual Studio 或 MinGW 编译
```

**配置路径**: `CPPCHECK_PATH`, `CPPCHECK_EXECUTABLE`

---

### 5. gcov + lcov

**用途**: 代码覆盖率工具

**状态**: 需要系统安装

**官方文档**:
- gcov: https://gcc.gnu.org/onlinedocs/gcc/Gcov.html
- lcov: https://github.com/linux-test-project/lcov

**Windows 安装说明**:

**gcov**:
- 随 MinGW/GCC 安装，通常位于 `C:\MinGW\bin\gcov.exe`
- 或使用 MSYS2: `pacman -S mingw-w64-x86_64-gcc`

**lcov**:
- 需要 Perl 环境
- 使用 Chocolatey: `choco install lcov`
- 或从源码编译: https://github.com/linux-test-project/lcov

**MSVC 替代方案**:
- 使用 OpenCppCoverage: https://github.com/OpenCppCoverage/OpenCppCoverage

**配置路径**: `GCOV_PATH`, `LCOV_PATH`

---

### 6. Valgrind / Dr. Memory

**用途**: 内存调试和性能分析工具

**状态**: ❌ 需要下载（Windows 使用 Dr. Memory）

**官方文档**:
- Valgrind: https://valgrind.org/ (仅 Linux/macOS)
- Dr. Memory: https://github.com/DynamoRIO/drmemory

**Windows 说明**:
Windows 不支持原生 Valgrind，使用 Dr. Memory 作为替代。

**下载 Dr. Memory**:
- 从 https://github.com/DynamoRIO/drmemory/releases 下载
- 或使用 Chocolatey: `choco install drmemory`

**WSL 选项**:
如果必须使用 Valgrind，可以在 WSL (Windows Subsystem for Linux) 中运行。

**配置路径**: `DRMEMORY_PATH`, `DRMEMORY_EXECUTABLE`

---

### 7. GammaRay

**用途**: Qt 应用程序调试和检查工具

**状态**: ❌ 需要下载

**官方文档**: https://github.com/KDAB/GammaRay

**下载方式**:
```bash
git clone --recursive https://github.com/KDAB/GammaRay.git backend/tools/gammaray/GammaRay
```

**依赖项**:
- Qt 5.12+ 或 Qt 6.x
- CMake 3.16+

**编译步骤**:
```bash
cd backend/tools/gammaray/GammaRay
mkdir build
cd build
cmake -DCMAKE_PREFIX_PATH="C:/Qt/6.x.x/msvc2019_64" ..
cmake --build .
```

**配置路径**: `GAMMARAY_PATH`, `GAMMARAY_EXECUTABLE`

---

## 快速开始

### 1. 检测工具状态

运行检测脚本查看所有工具的安装状态:

```bash
python backend/scripts/check_tools.py
```

### 2. 下载工具

使用下载脚本自动下载所有工具:

**PowerShell**:
```powershell
.\backend\scripts\download_tools.ps1
```

**批处理**:
```batch
.\backend\scripts\download_tools.bat
```

### 3. 配置工具路径

工具路径在 `backend/app/core/config.py` 中配置，也可以通过 `.env` 文件覆盖:

```env
TOOLS_BASE_PATH=./tools
SPIX_PATH=./tools/spix/spix
UTBOT_PATH=./tools/utbot/UTBotCpp
# ... 其他工具路径
```

---

## Windows 特殊说明

### 编译环境要求

大多数工具需要编译，建议安装:

1. **Visual Studio Build Tools** 或 **Visual Studio Community**
   - 下载: https://visualstudio.microsoft.com/downloads/
   - 安装 "Desktop development with C++" 工作负载

2. **CMake**
   - 下载: https://cmake.org/download/
   - 或使用 Chocolatey: `choco install cmake`

3. **Qt** (用于 Spix, Clazy, GammaRay)
   - 下载: https://www.qt.io/download
   - 或使用在线安装器

4. **LLVM/Clang** (用于 Clazy)
   - 下载: https://llvm.org/builds/
   - 或使用 Chocolatey: `choco install llvm`

### 包管理器推荐

使用 **Chocolatey** 可以简化安装:

```powershell
# 安装 Chocolatey (需要管理员权限)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装常用工具
choco install cmake llvm qt-creator -y
```

---

## 已知问题和限制

### Windows 兼容性

1. **Valgrind**: Windows 不支持，使用 Dr. Memory 替代
2. **Clazy**: 需要 Clang 和 Qt，编译可能较复杂
3. **gcov/lcov**: 在 Windows 上支持有限，建议使用 MinGW 或 MSVC 替代方案

### 路径问题

- 所有路径使用相对路径（相对于项目根目录）
- Windows 路径分隔符会自动处理
- 如果工具安装在系统路径，可执行文件会自动检测

### 编译问题

- 某些工具需要特定版本的依赖库
- 建议查看各工具的官方文档获取最新编译说明
- 如果遇到编译错误，检查 CMake 配置和依赖项版本

---

## 故障排除

### 工具检测失败

1. 检查工具路径是否正确
2. 确认工具已下载到指定目录
3. 对于需要编译的工具，确认已编译完成
4. 检查可执行文件是否在系统 PATH 中

### 下载失败

1. 检查网络连接
2. 确认 Git 已安装
3. 某些仓库可能需要较长时间下载
4. 如果下载中断，可以重新运行脚本（使用 `-SkipExisting` 参数跳过已存在的工具）

### 编译失败

1. 检查所有依赖项是否已安装
2. 确认 CMake 版本符合要求
3. 查看工具的官方文档获取编译说明
4. 检查编译器版本兼容性

---

## 维护

### 更新工具

1. 进入工具目录
2. 使用 Git 拉取最新代码: `git pull`
3. 重新编译（如需要）

### 清理构建产物

构建产物（如 `build/`, `bin/`, `lib/` 等）已添加到 `.gitignore`，不会被提交到仓库。

手动清理:
```bash
# 清理所有构建目录
Get-ChildItem -Path backend/tools -Recurse -Directory -Filter "build" | Remove-Item -Recurse -Force
```

---

## 相关文档

- [项目架构文档](../../ARCHITECTURE.md)
- [快速启动指南](../../QUICK_START.md)
- [项目结构说明](../../PROJECT_STRUCTURE.md)

---

## 贡献

如果发现工具配置问题或有改进建议，请提交 Issue 或 Pull Request。


