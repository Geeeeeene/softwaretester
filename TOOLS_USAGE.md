# 测试工具使用说明

本文档详细说明如何在 HomemadeTester 项目中配置和使用各个测试工具。

## 目录

- [Spix - UI 测试框架](#spix---ui-测试框架)
- [UTBotCpp - 单元测试生成工具](#utbotcpp---单元测试生成工具)
- [Clazy - Qt 静态代码分析工具](#clazy---qt-静态代码分析工具)
- [Cppcheck - C/C++ 静态分析工具](#cppcheck---cc-静态分析工具)
- [GammaRay - Qt 调试工具](#gammaray---qt-调试工具)
- [gcov + lcov - 代码覆盖率工具](#gcov--lcov---代码覆盖率工具)
- [Dr. Memory - 内存调试工具](#dr-memory---内存调试工具)

---

## Spix - UI 测试框架

### 工具简介

Spix 是一个最小侵入性的 UI 测试库，支持通过 C++ 代码或 HTTP RPC 接口控制 Qt/QML 应用。

### 配置方法

#### 1. 环境要求

- **Qt**: Qt 5.15.2+ 或 Qt 6.2.3+
- **AnyRPC**: Spix 的依赖库
- **CMake**: 3.18+

#### 2. 安装依赖 (AnyRPC)

**Linux/macOS:**
```bash
git clone https://github.com/sgieseking/anyrpc.git
cd anyrpc
mkdir build && cd build
cmake -DBUILD_EXAMPLES=OFF -DBUILD_WITH_LOG4CPLUS=OFF -DBUILD_PROTOCOL_MESSAGEPACK=OFF ..
cmake --build .
sudo cmake --install .
```

**Windows:**
参考 `backend/tools/spix/spix/ci/install-deps.sh` 脚本

#### 3. 编译 Spix

```bash
cd backend/tools/spix/spix
mkdir build && cd build
cmake -DSPIX_QT_MAJOR=6 -DCMAKE_PREFIX_PATH="C:/Qt/6.x.x/msvc2019_64" ..
cmake --build .
```

**CMake 选项:**
- `SPIX_QT_MAJOR`: Qt 主版本号 (5 或 6，默认 6)
- `SPIX_BUILD_QTQUICK`: 构建 QtQuick 场景支持 (默认: ON)
- `SPIX_BUILD_EXAMPLES`: 构建示例应用 (默认: ON)
- `SPIX_BUILD_TESTS`: 构建单元测试 (默认: OFF)

#### 4. 在项目中使用 Spix

**CMake 项目:**
```cmake
find_package(Spix REQUIRED)
target_link_libraries(your_app PRIVATE Spix::QtQuick)
```

**在 main.cpp 中启用 Spix:**
```cpp
#include <Spix/AnyRpcServer.h>
#include <Spix/QtQmlBot.h>

int main(int argc, char *argv[]) {
    QGuiApplication app(argc, argv);
    
    // 启动 Spix RPC 服务器
    spix::AnyRpcServer server;
    auto bot = new spix::QtQmlBot();
    bot->runTestServer(server);
    
    // 你的应用代码...
    return app.exec();
}
```

#### 5. 配置路径

在 `backend/app/core/config.py` 中配置：
```python
SPIX_PATH = "backend/tools/spix/spix"
SPIX_BUILD_PATH = "backend/tools/spix/spix/build"
```

### 验证功能

#### 1. 检查编译是否成功

```bash
cd backend/tools/spix/spix/build
ls -la lib/
# 应该看到 libSpixCore.a 和 libSpixQtQuick.a (或 .so/.dll)
```

#### 2. 运行示例程序

```bash
cd backend/tools/spix/spix/examples/qtquick/Basic
mkdir build && cd build
cmake -DSPIX_QT_MAJOR=6 ..
cmake --build .
./Basic  # 或 Basic.exe on Windows
```

#### 3. 使用 Python 测试 RPC 接口

创建测试脚本 `test_spix.py`:
```python
import xmlrpc.client
import time

# 连接到 Spix RPC 服务器（默认端口 9000）
s = xmlrpc.client.ServerProxy('http://localhost:9000')

# 列出所有可用方法
print("可用方法:", s.system.listMethods())

# 测试鼠标点击
s.mouseClick("mainWindow/ok_button")
time.sleep(0.2)

# 获取属性
text = s.getStringProperty("mainWindow/results", "text")
print(f"结果文本: {text}")

# 退出应用
s.quit()
```

运行测试：
```bash
# 1. 启动你的 Qt 应用（已集成 Spix）
./your_app

# 2. 在另一个终端运行测试脚本
python test_spix.py
```

#### 4. 验证检查清单

- [ ] Spix 库编译成功
- [ ] 示例程序可以运行
- [ ] RPC 服务器可以连接（端口 9000）
- [ ] 可以执行鼠标点击操作
- [ ] 可以获取 UI 元素属性
- [ ] 可以调用 QML 方法

---

## UTBotCpp - 单元测试生成工具

### 工具简介

UTBotCpp 是一个 C/C++ 单元测试自动生成工具，通过代码分析生成测试用例，最大化语句和路径覆盖率。

### 配置方法

#### 1. 环境要求

- **操作系统**: Ubuntu 20.04+ (目前主要支持)
- **CMake**: 3.18+
- **LLVM/Clang**: 用于代码分析
- **编译器**: GCC 或 Clang

#### 2. 编译 UTBotCpp

```bash
cd backend/tools/utbot/UTBotCpp
mkdir build && cd build
cmake ..
cmake --build . --config Release
```

**注意**: UTBotCpp 包含多个子模块（Bear, KLEE, json 等），编译可能需要较长时间。

#### 3. 安装 UTBotCpp

**方式1: 使用预编译版本（推荐）**

从 [GitHub Releases](https://github.com/UnitTestBot/UTBotCpp/releases) 下载：
```bash
# 下载 utbot_distr.tar.gz
tar -xzf utbot_distr.tar.gz
cd utbot_distr
./unpack_and_run_utbot.sh
```

**方式2: 从源码编译**

```bash
cd backend/tools/utbot/UTBotCpp
./build.sh
```

#### 4. 配置路径

在 `backend/app/core/config.py` 中配置：
```python
UTBOT_PATH = "backend/tools/utbot/UTBotCpp"
UTBOT_EXECUTABLE = "backend/tools/utbot/UTBotCpp/build/utbot"  # 或系统路径
```

#### 5. 安装 VSCode 插件（可选）

```bash
# 下载 utbot_plugin.vsix
code --install-extension utbot_plugin.vsix
```

### 验证功能

#### 1. 检查可执行文件

```bash
# 检查 UTBot 是否在 PATH 中
which utbot

# 或检查编译后的可执行文件
ls -la backend/tools/utbot/UTBotCpp/build/utbot
```

#### 2. 运行版本检查

```bash
utbot --version
# 或
backend/tools/utbot/UTBotCpp/build/utbot --version
```

#### 3. 测试生成单元测试

创建测试文件 `test_example.cpp`:
```cpp
// example.cpp
int add(int a, int b) {
    return a + b;
}
```

使用 UTBot 生成测试：
```bash
# 生成测试用例
utbot generate --target example.cpp --output tests/

# 查看生成的测试文件
ls tests/
```

#### 4. 验证检查清单

- [ ] UTBot 可执行文件存在
- [ ] 可以运行 `utbot --version`
- [ ] 可以生成测试用例
- [ ] 生成的测试可以编译
- [ ] 生成的测试可以运行

---

## Clazy - Qt 静态代码分析工具

### 工具简介

Clazy 是一个 Clang 编译器插件，提供 50+ 个 Qt 相关的编译器警告，包括内存分配优化、API 误用检测等。

### 配置方法

#### 1. 环境要求

- **Clang/LLVM**: >= 11.0
- **Qt**: Qt 5 或 Qt 6
- **CMake**: 3.16+

#### 2. 安装 Clang/LLVM

**Windows:**
```bash
# 下载并安装 LLVM
# 从 https://llvm.org/builds/ 下载
# 或使用 Chocolatey
choco install llvm
```

**Linux:**
```bash
# Ubuntu
sudo apt install clang llvm-dev libclang-dev

# 或从源码编译（参考 Clazy README）
```

#### 3. 编译 Clazy

```bash
cd backend/tools/clazy/clazy
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_BUILD_TYPE=Release ..
cmake --build .
sudo cmake --install .
```

**Windows 编译:**
```bash
cd backend/tools/clazy/clazy
mkdir build && cd build
cmake -DCMAKE_PREFIX_PATH="C:/Qt/6.x.x/msvc2019_64;C:/LLVM" -G "Visual Studio 17 2022" ..
cmake --build . --config Release
```

#### 4. 配置路径

在 `backend/app/core/config.py` 中配置：
```python
CLAZY_PATH = "backend/tools/clazy/clazy"
CLAZY_EXECUTABLE = "clazy-standalone"  # 或完整路径
```

#### 5. 在项目中使用 Clazy

**方式1: 通过环境变量**
```bash
export CLAZY_CHECKS="level1,level2"
clang++ -c your_file.cpp
```

**方式2: 通过 CMake**
```cmake
find_program(CLAZY_EXE clazy-standalone)
if(CLAZY_EXE)
    set(CMAKE_CXX_CLANG_TIDY ${CLAZY_EXE})
endif()
```

**方式3: 作为编译器包装器**
```bash
export CXX="clazy"
cmake ..
make
```

### 验证功能

#### 1. 检查 Clazy 是否安装

```bash
clazy-standalone --version
# 或
clazy --version
```

#### 2. 测试基本功能

创建测试文件 `test_clazy.cpp`:
```cpp
#include <QString>
#include <QList>

void test() {
    QString str = "test";
    QList<QString> list;
    list << str;  // Clazy 会警告使用 append() 而不是 <<
}
```

运行 Clazy 分析：
```bash
clazy-standalone -c test_clazy.cpp
# 应该看到警告信息
```

#### 3. 查看可用的检查项

```bash
clazy-standalone --list
# 或
clazy-standalone --help
```

#### 4. 测试不同级别的检查

```bash
# Level 1 检查
clazy-standalone -c -Xclang -plugin-arg-clazy -Xclang level1 test.cpp

# Level 2 检查
clazy-standalone -c -Xclang -plugin-arg-clazy -Xclang level2 test.cpp
```

#### 5. 验证检查清单

- [ ] Clazy 可执行文件存在
- [ ] 可以运行 `clazy-standalone --version`
- [ ] 可以分析 C++ 文件
- [ ] 可以检测 Qt 相关问题
- [ ] 警告信息正确显示

---

## Cppcheck - C/C++ 静态分析工具

### 工具简介

Cppcheck 是一个开源的 C/C++ 静态代码分析工具，用于检测代码中的错误、未定义行为和性能问题。

### 配置方法

#### 1. 环境要求

- **编译器**: GCC 5.1+ / Clang 3.5+ / Visual Studio 2015+
- **CMake**: 3.13+ (用于 GUI 版本)
- **Python**: 3.6+ (可选，用于某些功能)

#### 2. 安装 Cppcheck

**方式1: 使用预编译版本（推荐 Windows）**

从 [GitHub Releases](https://github.com/danmar/cppcheck/releases) 下载 Windows 安装包：
```bash
# 下载 cppcheck-2.12-x64-Setup.exe
# 运行安装程序
```

**方式2: 从源码编译**

```bash
cd backend/tools/cppcheck/cppcheck
mkdir build && cd build
cmake -S . -B . -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

**CMake 选项:**
- `-DBUILD_GUI=ON`: 构建 GUI 版本
- `-DHAVE_RULES=ON`: 启用规则支持（需要 PCRE）
- `-DUSE_MATCHCOMPILER=ON`: 启用匹配编译器（推荐用于发布版本）
- `-DBUILD_TESTS=ON`: 构建测试

**方式3: 使用包管理器**

```bash
# Ubuntu/Debian
sudo apt install cppcheck

# Windows (Chocolatey)
choco install cppcheck
```

#### 3. 配置路径

在 `backend/app/core/config.py` 中配置：
```python
CPPCHECK_PATH = "backend/tools/cppcheck/cppcheck"
CPPCHECK_EXECUTABLE = "cppcheck"  # 或完整路径
```

### 验证功能

#### 1. 检查 Cppcheck 是否安装

```bash
cppcheck --version
# 应该显示版本号，如: Cppcheck 2.12
```

#### 2. 测试基本分析

创建测试文件 `test_cppcheck.cpp`:
```cpp
#include <iostream>

void test() {
    int arr[10];
    arr[10] = 0;  // 数组越界
    int *p = nullptr;
    *p = 5;  // 空指针解引用
}
```

运行 Cppcheck:
```bash
cppcheck test_cppcheck.cpp
# 应该检测到数组越界和空指针问题
```

#### 3. 测试不同检查级别

```bash
# 基本检查
cppcheck test.cpp

# 启用所有检查
cppcheck --enable=all test.cpp

# 仅检查错误
cppcheck --enable=error test.cpp

# 检查性能和风格问题
cppcheck --enable=performance,style test.cpp
```

#### 4. 生成 XML 报告

```bash
cppcheck --xml --xml-version=2 test.cpp 2> report.xml
```

#### 5. 使用配置文件

创建 `cppcheck.cfg`:
```xml
<?xml version="1.0"?>
<defines>
    <define name="DEBUG"/>
</defines>
<undefines>
    <undefine name="WIN32"/>
</undefines>
```

使用配置文件：
```bash
cppcheck --library=std.cfg --library=posix.cfg test.cpp
```

#### 6. 验证检查清单

- [ ] Cppcheck 可执行文件存在
- [ ] 可以运行 `cppcheck --version`
- [ ] 可以分析 C++ 文件
- [ ] 可以检测常见错误（数组越界、空指针等）
- [ ] 可以生成 XML 报告
- [ ] GUI 版本可以运行（如果编译了）

---

## GammaRay - Qt 调试工具

### 工具简介

GammaRay 是 KDAB 开发的 Qt 应用软件内省工具，允许在运行时观察和操作 Qt 应用程序。

### 配置方法

#### 1. 环境要求

- **Qt**: Qt 5.12+ 或 Qt 6.x
- **CMake**: 3.16+
- **编译器**: 支持 C++17

#### 2. 编译 GammaRay

```bash
cd backend/tools/gammaray/GammaRay
mkdir build && cd build
cmake -DCMAKE_PREFIX_PATH="C:/Qt/6.x.x/msvc2019_64" -DCMAKE_BUILD_TYPE=Release ..
cmake --build . --config Release
```

**CMake 选项:**
- `-DCMAKE_PREFIX_PATH`: Qt 安装路径
- `-DGAMMARAY_BUILD_UI=ON`: 构建 UI（默认开启）
- `-DGAMMARAY_BUILD_PROBES=ON`: 构建探针（默认开启）

#### 3. 安装 GammaRay

```bash
cd build
sudo cmake --install .  # Linux/macOS
# 或
cmake --install . --config Release  # Windows
```

#### 4. 配置路径

在 `backend/app/core/config.py` 中配置：
```python
GAMMARAY_PATH = "backend/tools/gammaray/GammaRay"
GAMMARAY_EXECUTABLE = "backend/tools/gammaray/GammaRay/build/bin/gammaray.exe"
```

#### 5. 在应用中使用 GammaRay

**方式1: 作为独立工具（推荐）**

不需要修改应用代码，直接附加到运行中的应用：
```bash
gammaray your_app.exe
```

**方式2: 嵌入到应用中**

在应用启动时加载 GammaRay 探针：
```cpp
#include <QApplication>
#include <gammaray/core/probe.h>

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    
    // 加载 GammaRay 探针
    GammaRay::Probe::instance()->attach();
    
    // 你的应用代码...
    return app.exec();
}
```

### 验证功能

#### 1. 检查 GammaRay 是否编译成功

```bash
ls backend/tools/gammaray/GammaRay/build/bin/
# 应该看到 gammaray 可执行文件
```

#### 2. 运行 GammaRay GUI

```bash
cd backend/tools/gammaray/GammaRay/build/bin
./gammaray  # 或 gammaray.exe on Windows
```

#### 3. 附加到运行中的应用

```bash
# 1. 启动你的 Qt 应用
./your_qt_app &

# 2. 使用 GammaRay 附加
gammaray --attach your_qt_app
```

#### 4. 测试功能

创建一个简单的 Qt 应用 `test_app.cpp`:
```cpp
#include <QApplication>
#include <QPushButton>
#include <QWidget>

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    
    QWidget window;
    QPushButton button("Click Me", &window);
    window.show();
    
    return app.exec();
}
```

使用 GammaRay 调试：
```bash
# 编译应用
g++ test_app.cpp -o test_app -fPIC $(pkg-config --cflags --libs Qt6Core Qt6Gui Qt6Widgets)

# 使用 GammaRay 启动
gammaray ./test_app
```

在 GammaRay 界面中应该能看到：
- QObject 树
- 按钮的属性
- 信号/槽连接
- 布局信息

#### 5. 验证检查清单

- [ ] GammaRay 可执行文件存在
- [ ] GUI 可以启动
- [ ] 可以附加到运行中的应用
- [ ] 可以查看 QObject 树
- [ ] 可以查看和编辑属性
- [ ] 可以查看信号/槽连接

---

## gcov + lcov - 代码覆盖率工具

### 工具简介

- **gcov**: GCC 自带的代码覆盖率工具
- **lcov**: gcov 的图形前端，用于生成 HTML 报告

### 配置方法

#### 1. 环境要求

- **GCC**: 带 gcov 支持
- **lcov**: 需要 Perl 环境

#### 2. 安装 gcov

**gcov 通常随 GCC 一起安装**

**Windows (MinGW):**
```bash
# gcov 通常位于 MinGW bin 目录
# C:\MinGW\bin\gcov.exe
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install gcc

# 验证
gcov --version
```

#### 3. 安装 lcov

**Windows:**
```bash
# 使用 Chocolatey
choco install lcov

# 或从源码编译（需要 Perl）
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install lcov

# 验证
lcov --version
```

#### 4. 配置路径

在 `backend/app/core/config.py` 中配置：
```python
GCOV_PATH = ""  # 从系统 PATH 查找
LCOV_PATH = ""  # 从系统 PATH 查找
```

### 验证功能

#### 1. 检查工具是否安装

```bash
gcov --version
lcov --version
```

#### 2. 编译带覆盖率信息的程序

```bash
# 使用 -fprofile-arcs -ftest-coverage 标志编译
gcc -fprofile-arcs -ftest-coverage -o test_program test_program.c

# 运行程序
./test_program

# 生成 .gcda 文件
```

#### 3. 生成覆盖率数据

```bash
# 使用 gcov 生成 .gcov 文件
gcov test_program.c

# 使用 lcov 收集数据
lcov --capture --directory . --output-file coverage.info
```

#### 4. 生成 HTML 报告

```bash
# 生成 HTML 报告
genhtml coverage.info --output-directory coverage_html

# 打开报告
# 在浏览器中打开 coverage_html/index.html
```

#### 5. 验证检查清单

- [ ] gcov 可以运行
- [ ] lcov 可以运行
- [ ] 可以编译带覆盖率信息的程序
- [ ] 可以生成 .gcda 文件
- [ ] 可以生成 HTML 报告

---

## Dr. Memory - 内存调试工具

### 工具简介

Dr. Memory 是 Windows 上的内存调试工具，作为 Valgrind 的替代方案。

### 配置方法

#### 1. 环境要求

- **操作系统**: Windows
- **架构**: x86 或 x64

#### 2. 安装 Dr. Memory

**方式1: 下载预编译版本**

从 [GitHub Releases](https://github.com/DynamoRIO/drmemory/releases) 下载：
```bash
# 下载 DrMemory-Windows-2.5.0-1.exe
# 运行安装程序
```

**方式2: 使用 Chocolatey**

```bash
choco install drmemory
```

#### 3. 配置路径

在 `backend/app/core/config.py` 中配置：
```python
DRMEMORY_PATH = "backend/tools/valgrind/drmemory"
DRMEMORY_EXECUTABLE = "drmemory.exe"  # 或完整路径
```

### 验证功能

#### 1. 检查 Dr. Memory 是否安装

```bash
drmemory --version
```

#### 2. 测试基本功能

创建测试程序 `test_memory.cpp`:
```cpp
#include <iostream>

int main() {
    int *p = new int[10];
    // 忘记释放内存（内存泄漏）
    // delete[] p;
    return 0;
}
```

编译并运行：
```bash
g++ test_memory.cpp -o test_memory
drmemory -- test_memory.exe
```

#### 3. 查看报告

Dr. Memory 会生成详细的报告，包括：
- 内存泄漏
- 未初始化内存访问
- 无效内存访问
- 双重释放

#### 4. 验证检查清单

- [ ] Dr. Memory 可执行文件存在
- [ ] 可以运行 `drmemory --version`
- [ ] 可以检测内存泄漏
- [ ] 可以检测未初始化内存访问
- [ ] 报告格式正确

---

## 工具集成验证

### 使用检测脚本验证所有工具

运行工具检测脚本：
```bash
python backend/scripts/check_tools.py
```

脚本会检查：
- 工具是否已下载
- 可执行文件是否存在
- 工具版本信息
- 依赖项是否满足

### 在 HomemadeTester 中使用工具

#### 1. 通过 Test IR 使用

所有工具都通过统一的 Test IR 格式使用：

**UI 测试 (Spix):**
```json
{
  "type": "ui",
  "name": "登录测试",
  "steps": [
    {"type": "input", "target": "username", "value": "admin"},
    {"type": "click", "target": "loginButton"},
    {"type": "assert", "target": "welcome", "value": "欢迎"}
  ]
}
```

**单元测试 (UTBot):**
```json
{
  "type": "unit",
  "name": "测试加法函数",
  "function_under_test": {
    "name": "add",
    "file_path": "math_utils.cpp"
  },
  "inputs": {"parameters": {"a": 1, "b": 2}},
  "assertions": [{"type": "equals", "expected": 3}]
}
```

**静态分析 (Clazy/Cppcheck):**
```json
{
  "type": "static",
  "name": "代码质量检查",
  "target_files": ["src/**/*.cpp"],
  "rules": [
    {"rule_id": "mem-leak", "severity": "error"}
  ]
}
```

#### 2. 通过 API 使用

```bash
# 创建测试执行
curl -X POST http://localhost:8000/api/v1/executions \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "executor_type": "spix",
    "test_ir": {...}
  }'
```

#### 3. 查看执行结果

```bash
# 获取执行状态
curl http://localhost:8000/api/v1/executions/1

# 获取测试结果
curl http://localhost:8000/api/v1/executions/1/results
```

---

## 常见问题

### Spix

**Q: RPC 服务器无法连接**
- 检查应用是否已启动
- 检查端口 9000 是否被占用
- 确认 Spix 已正确集成到应用中

**Q: 无法找到 UI 元素**
- 确保 QML 元素设置了 `objectName` 或 `id`
- 检查路径是否正确（使用 `/` 分隔）

### UTBotCpp

**Q: 编译失败**
- 检查 LLVM/Clang 是否正确安装
- 确认所有子模块已下载
- 检查 CMake 版本是否满足要求

**Q: 生成的测试无法编译**
- 检查目标代码的依赖项
- 确认编译器设置正确

### Clazy

**Q: Clazy 不工作**
- 确认 Clang 版本 >= 11.0
- 检查 Clazy 是否正确编译和安装
- 确认使用 Clazy 作为编译器

**Q: 警告太多**
- 使用 `-Xclang -plugin-arg-clazy -Xclang level1` 只启用 Level 1 检查
- 使用 `-Xclang -plugin-arg-clazy -Xclang no-*` 禁用特定检查

### Cppcheck

**Q: 误报太多**
- 使用 `--suppress` 选项抑制特定警告
- 创建配置文件排除某些路径
- 使用 `--inline-suppr` 在代码中抑制警告

**Q: 分析速度慢**
- 使用 `-j` 选项启用多线程
- 排除不需要分析的目录
- 使用 `--max-configs` 限制配置数量

### GammaRay

**Q: 无法附加到应用**
- 确认应用使用 Qt 框架
- 检查应用是否在运行
- 尝试使用 `--attach` 选项

**Q: 看不到某些信息**
- 确认应用编译时包含调试信息
- 检查 Qt 版本是否兼容
- 查看 GammaRay 日志

---

## 参考资源

- [Spix 官方文档](https://github.com/faaxm/spix)
- [UTBotCpp Wiki](https://github.com/UnitTestBot/UTBotCpp/wiki)
- [Clazy 文档](https://github.com/KDE/clazy)
- [Cppcheck 手册](https://cppcheck.sourceforge.io/manual.pdf)
- [GammaRay 文档](https://github.com/KDAB/GammaRay)
- [gcov 文档](https://gcc.gnu.org/onlinedocs/gcc/Gcov.html)
- [lcov 文档](https://github.com/linux-test-project/lcov)

---

## 更新日志

- 2024-12-09: 初始版本，包含所有工具的配置和验证说明

