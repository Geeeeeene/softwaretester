# 工具集成使用说明

本文档说明如何在项目中使用已集成的测试工具：UTBotCpp、gcov+lcov 和 Dr. Memory。

## 目录

- [UTBotCpp 单元测试生成](#utbotcpp-单元测试生成)
- [gcov + lcov 代码覆盖率](#gcov--lcov-代码覆盖率)
- [Dr. Memory 内存调试](#dr-memory-内存调试)
- [前端结果展示](#前端结果展示)

---

## UTBotCpp 单元测试生成

### 功能说明

UTBotCpp 执行器会自动生成单元测试代码，编译并运行测试，同时收集代码覆盖率数据。

### 使用方法

#### 1. 创建单元测试用例

通过 Test IR 格式创建单元测试用例：

```json
{
  "type": "unit",
  "name": "测试加法函数",
  "function_under_test": {
    "name": "add",
    "file_path": "math_utils.cpp"
  },
  "inputs": {
    "parameters": {
      "a": 1,
      "b": 2
    }
  },
  "assertions": [
    {
      "type": "equals",
      "expected": 3
    }
  ]
}
```

#### 2. 配置项目路径

在执行测试时，需要提供项目配置：

```python
config = {
    "project_path": "/path/to/project",
    "source_path": "/path/to/project/src",
    "build_path": "/path/to/project/build"
}
```

#### 3. 执行测试

通过 API 创建执行记录：

```bash
POST /api/v1/executions
{
  "project_id": 1,
  "executor_type": "unit",
  "test_case_ids": [1, 2, 3]
}
```

### 工具要求

- **UTBotCpp**: 需要编译或安装 UTBotCpp 工具
- **编译器**: GCC 或 Clang（带 gcov 支持）
- **配置**: 在 `backend/app/core/config.py` 中配置 `UTBOT_EXECUTABLE` 路径

### 输出结果

执行完成后，会生成：
- 测试代码文件（`.cpp`）
- 覆盖率数据（JSON格式）
- HTML覆盖率报告（如果 lcov 可用）

---

## gcov + lcov 代码覆盖率

### 功能说明

代码覆盖率工具会自动在单元测试执行后收集覆盖率数据，生成详细的覆盖率报告。

### 工作流程

1. **编译阶段**: 使用 `-fprofile-arcs -ftest-coverage` 标志编译测试代码
2. **运行阶段**: 执行测试程序，生成 `.gcda` 文件
3. **收集阶段**: 使用 `lcov` 收集覆盖率数据
4. **报告阶段**: 使用 `genhtml` 生成 HTML 报告

### 配置要求

在 `backend/app/core/config.py` 中配置工具路径：

```python
GCOV_PATH = ""  # 从系统PATH查找，或指定完整路径
LCOV_PATH = ""  # 从系统PATH查找，或指定完整路径
GENHTML_PATH = ""  # genhtml路径（通常与lcov在同一目录）
```

### 覆盖率数据格式

```json
{
  "percentage": 85.5,
  "lines_covered": 342,
  "lines_total": 400,
  "branches_covered": 45,
  "branches_total": 60,
  "functions_covered": 12,
  "functions_total": 15
}
```

### 前端展示

覆盖率数据会在前端结果页面自动显示：
- 总体覆盖率百分比
- 行覆盖率统计
- 分支覆盖率统计
- 函数覆盖率统计
- HTML报告链接

---

## Dr. Memory 内存调试

### 功能说明

Dr. Memory 执行器用于检测程序中的内存问题，包括：
- 内存泄漏
- 未初始化内存访问
- 无效内存访问
- 双重释放

### 使用方法

#### 1. 创建内存调试用例

通过 Test IR 格式创建内存调试用例：

```json
{
  "type": "memory",
  "name": "内存泄漏检测",
  "program_args": []
}
```

#### 2. 配置二进制文件路径

在执行测试时，需要提供二进制文件路径：

```python
config = {
    "project_path": "/path/to/project",
    "source_path": "/path/to/project/src",
    "binary_path": "/path/to/project/build/my_program.exe"
}
```

#### 3. 执行内存调试

通过 API 创建执行记录：

```bash
POST /api/v1/executions
{
  "project_id": 1,
  "executor_type": "memory",
  "test_case_ids": [1]
}
```

### 工具要求

- **Dr. Memory**: 需要安装 Dr. Memory（Windows）
- **配置**: 在 `backend/app/core/config.py` 中配置 `DRMEMORY_PATH` 和 `DRMEMORY_EXECUTABLE`

### 输出结果

执行完成后，会生成：
- 内存问题列表（JSON格式）
- 详细的内存调试报告文件
- 堆栈跟踪信息

### 内存问题格式

```json
{
  "id": "1",
  "type": "memory_leak",
  "severity": "error",
  "message": "LEAK 20 bytes",
  "stack_trace": [
    {
      "frame": 0,
      "function": "replace_malloc",
      "file": "d:\\drmemory\\...",
      "line": null
    },
    {
      "frame": 1,
      "function": "main",
      "file": "test.cpp",
      "line": 45
    }
  ]
}
```

### 前端展示

内存调试结果会在前端结果页面自动显示：
- 问题总数统计
- 按严重程度分类的问题列表
- 每个问题的堆栈跟踪
- JSON报告链接

---

## 前端结果展示

### 结果页面功能

访问 `/results` 页面可以查看：

1. **执行列表**: 所有测试执行记录
2. **执行概览**: 状态、通过数、失败数、耗时
3. **代码覆盖率**: 
   - 总体覆盖率百分比（进度条）
   - 行/分支/函数覆盖率详细统计
   - HTML报告链接
4. **内存调试结果**:
   - 问题列表（按严重程度分类）
   - 堆栈跟踪信息
   - JSON报告链接
5. **执行日志**: 完整的执行日志输出
6. **错误信息**: 如果有错误，会单独显示

### 数据联动

前端会自动从后端 API 获取：
- 执行记录列表
- 执行详情（包含覆盖率、内存问题等）
- Artifacts（报告文件路径）

所有数据都是实时从数据库获取，确保显示最新的执行结果。

---

## 配置示例

### .env 文件配置

```env
# UTBotCpp
UTBOT_EXECUTABLE=C:\tools\utbot\bin\utbot.exe

# 代码覆盖率工具
GCOV_PATH=C:\MinGW\bin\gcov.exe
LCOV_PATH=C:\Program Files\lcov\bin\lcov.exe
GENHTML_PATH=C:\Program Files\lcov\bin\genhtml.exe

# Dr. Memory
DRMEMORY_PATH=C:\tools\drmemory
DRMEMORY_EXECUTABLE=drmemory.exe
```

### 工具路径配置

如果工具在系统 PATH 中，可以留空配置项，系统会自动查找。

---

## 常见问题

### Q1: UTBotCpp 未找到

**A**: 检查 `UTBOT_EXECUTABLE` 配置，确保路径正确。如果工具在系统 PATH 中，可以只配置可执行文件名。

### Q2: 覆盖率数据为 0

**A**: 确保：
1. 使用 `-fprofile-arcs -ftest-coverage` 标志编译
2. 程序已运行并生成 `.gcda` 文件
3. `lcov` 工具可用

### Q3: Dr. Memory 无法运行

**A**: 检查：
1. `DRMEMORY_EXECUTABLE` 路径是否正确
2. 二进制文件路径是否正确
3. 程序是否可以在当前环境运行

### Q4: 前端无法显示结果

**A**: 检查：
1. API 返回的数据格式是否正确
2. 浏览器控制台是否有错误
3. 执行记录是否包含 `coverage_data` 和 `result` 字段

---

## 下一步

- 查看 [TOOLS_USAGE.md](TOOLS_USAGE.md) 了解工具的详细配置
- 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解系统架构
- 查看 API 文档: http://localhost:8000/docs

