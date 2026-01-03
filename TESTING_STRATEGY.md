# 测试方案文档

## 1. 整体测试思路

HomemadeTester 平台采用 **多层次、多维度、智能化** 的测试策略，通过 AI 技术降低测试用例编写成本，提高测试覆盖率和质量。

### 1.1 测试金字塔

```
                    ┌─────────────┐
                    │  系统测试    │  ← 少量，覆盖关键流程
                    │  (E2E)      │
                    └─────────────┘
                 ┌───────────────────┐
                 │    集成测试        │  ← 中等数量，验证模块协作
                 │  (Integration)    │
                 └───────────────────┘
            ┌──────────────────────────┐
            │       单元测试           │  ← 大量，覆盖函数逻辑
            │      (Unit Test)        │
            └──────────────────────────┘
        ┌────────────────────────────────┐
        │        静态分析                 │  ← 持续，代码质量检查
        │      (Static Analysis)         │
        └────────────────────────────────┘
```

### 1.2 测试流程

```
需求分析
    ↓
测试计划制定
    ↓
┌─────────────────────────────────────┐
│  AI 辅助测试用例生成                │
│  - 系统测试：自然语言 → Robot脚本     │
│  - 单元测试：源代码 → Catch2测试    │
│  - 集成测试：代码分析 → 测试用例    │
└─────────────────────────────────────┘
    ↓
测试用例审查与优化
    ↓
测试执行（异步队列）
    ↓
结果分析与报告
    ↓
问题修复与回归测试
```

### 1.3 智能化核心价值

1. **降低编写成本**：从手动编写到 AI 自动生成，减少 70%+ 的编写时间
2. **提高覆盖率**：AI 分析代码结构，自动生成边界和异常测试用例
3. **统一标准**：通过 Test IR 统一测试描述格式，保证一致性
4. **持续改进**：AI 学习项目特点，生成质量逐步提升

## 2. 系统测试模式

### 2.1 测试思路

系统测试采用 **基于图像识别的自动化测试**，适用于：
- Windows 桌面应用程序
- 无法通过 DOM/元素定位的传统 GUI 应用
- 需要视觉验证的界面测试

**核心思路**：
1. 使用自然语言描述测试步骤
2. AI 理解描述并生成 Robot Framework + SikuliLibrary 脚本
3. 通过图像识别定位界面元素
4. 执行操作并验证结果

### 2.2 智能化实现

#### 2.2.1 AI 生成流程

```
用户输入测试描述
    ↓
AI 分析（Claude Sonnet 4.5）
    ├─ 理解测试意图
    ├─ 识别操作步骤
    ├─ 匹配图像资源
    └─ 生成 Robot Framework 脚本
    ↓
脚本验证与优化
    ↓
保存为 Test IR
```

#### 2.2.2 技术实现

**AI 生成器** (`backend/app/system_tests/ai_generator.py`)：

```python
class SystemTestAIGenerator:
    """系统测试AI生成器"""
    
    def generate_robot_script(
        self,
        test_name: str,
        test_description: str,  # 自然语言描述
        project_info: Dict[str, Any]
    ) -> str:
        """
        生成Robot Framework脚本
        
        输入示例：
        - test_name: "测试退出功能"
        - test_description: "1. 启动应用程序\n2. 等待主界面出现\n3. 点击退出按钮\n4. 验证退出确认对话框"
        
        输出：完整的Robot Framework脚本
        """
```

**Prompt 工程**：
- 包含项目上下文（应用路径、图像资源库）
- 提供 Robot Framework 语法规范
- 指导图像资源引用方式
- 包含错误处理和超时设置

**知识库支持**：
- 图像资源知识库（`image_knowledge_base.json`）
- 常见操作模式模板
- 最佳实践规则

#### 2.2.3 执行流程

```
1. 接收 Test IR（包含 Robot Framework 脚本）
    ↓
2. RobotFrameworkExecutor 执行
    ├─ 复制图像资源到工作目录
    ├─ 转换路径格式（Windows兼容）
    ├─ 启动应用程序
    └─ 执行 Robot Framework 脚本
    ↓
3. 收集执行结果
    ├─ 测试通过/失败状态
    ├─ 执行日志
    ├─ 截图（失败时）
    └─ 执行时间
    ↓
4. 更新数据库并返回结果
```

#### 2.2.4 智能化特性

- **自动路径处理**：Windows 路径自动转换为 Robot Framework 格式
- **图像资源管理**：自动复制和管理测试图像
- **错误恢复**：超时重试、异常处理
- **结果可视化**：HTML 报告、截图对比

### 2.3 使用示例

**输入（自然语言）**：
```
测试退出功能：
1. 启动应用程序
2. 等待屏幕上出现主界面 (main_window.png)
3. 点击退出按钮 (exit_button.png)
4. 验证屏幕上出现退出确认对话框 (exit_ask_window.png)
5. 关闭应用程序
```

**AI 生成（Robot Framework）**：
```robot
*** Settings ***
Library    SikuliLibrary
Library    Process

*** Variables ***
${APP_PATH}    C:/Users/.../app.exe
${IMAGE_PATH}  C:/.../robot_resources
${TIMEOUT}     30

*** Test Cases ***
测试退出功能
    Start Process    ${APP_PATH}    alias=app
    Sleep    5s
    
    Add Image Path    ${IMAGE_PATH}
    Set Min Similarity    0.7
    
    Wait Until Screen Contain    main_window.png    ${TIMEOUT}
    Click    exit_button.png
    Screen Should Contain    exit_ask_window.png
    
    [Teardown]    Terminate Process    app    kill=True
```

## 3. 单元测试模式

### 3.1 测试思路

单元测试采用 **基于源代码分析的自动生成**，适用于：
- C/C++ 代码的单元测试
- 函数级别的逻辑验证
- 边界条件和异常场景测试

**核心思路**：
1. 分析源代码结构（函数签名、依赖关系）
2. AI 理解代码逻辑并生成 Catch2 测试用例
3. 使用 Catch2 执行测试
4. 收集覆盖率数据

### 3.2 智能化实现

#### 3.2.1 AI 生成流程

```
源代码输入
    ↓
代码分析
    ├─ 提取函数签名
    ├─ 识别依赖关系
    ├─ 分析访问权限（public/protected/private）
    └─ 理解代码逻辑
    ↓
AI 生成测试用例（Claude）
    ├─ 正常场景测试
    ├─ 边界条件测试
    ├─ 异常场景测试
    └─ 参数组合测试
    ↓
代码验证与优化
    ├─ 语法检查
    ├─ 编译验证
    └─ 访问权限检查
    ↓
保存为 Test IR
```

#### 3.2.2 技术实现

**AI 生成器** (`backend/app/services/test_generation.py`)：

```python
class TestGenerationService:
    """测试生成服务"""
    
    async def generate_catch2_test(
        self,
        file_content: str,      # 源代码
        file_name: str,         # 文件名
        doc_summary: Optional[str] = None  # 项目文档要点
    ) -> str:
        """
        生成 Catch2 测试用例
        
        关键约束：
        1. 只能访问 public 接口
        2. 禁止访问 protected/private 成员
        3. 必须使用双括号包裹逻辑表达式
        4. 确保代码可编译
        """
```

**Prompt 工程要点**：
- **访问权限约束**：严格限制只能使用 public 接口
- **语法规范**：Catch2 特定语法要求（双括号、TEST_CASE 等）
- **代码完整性**：确保生成代码可编译
- **测试覆盖**：正常、边界、异常场景

**执行器** (`backend/app/executors/unit_executor.py`)：
- 支持 Catch2（AI生成）
- 集成 gcov/lcov 收集覆盖率
- 支持并行执行多个测试用例

#### 3.2.3 执行流程

```
1. 接收 Test IR（包含 Catch2 测试代码）
    ↓
2. UnitExecutor 执行
    ├─ 编译测试代码
    ├─ 链接被测代码
    ├─ 运行测试用例
    └─ 收集覆盖率数据
    ↓
3. 结果处理
    ├─ 解析测试结果
    ├─ 生成覆盖率报告（HTML）
    ├─ 提取覆盖率数据（JSON）
    └─ 保存执行日志
    ↓
4. 更新数据库并返回结果
```

#### 3.2.4 智能化特性

- **智能约束检查**：AI 自动识别并避免访问非 public 成员
- **自动依赖解析**：识别并包含必要的头文件
- **覆盖率分析**：自动生成覆盖率报告，识别未覆盖代码
- **增量测试**：只测试修改的函数

### 3.3 使用示例

**输入（源代码）**：
```cpp
// math_utils.h
class MathUtils {
public:
    int add(int a, int b);
    int multiply(int a, int b);
private:
    int validate(int x);
};
```

**AI 生成（Catch2 测试）**：
```cpp
#include "catch_amalgamated.hpp"
#include "math_utils.h"

TEST_CASE("MathUtils::add - 正常场景") {
    MathUtils utils;
    REQUIRE(utils.add(1, 2) == 3);
    REQUIRE(utils.add(-1, 1) == 0);
}

TEST_CASE("MathUtils::add - 边界条件") {
    MathUtils utils;
    REQUIRE(utils.add(INT_MAX, 0) == INT_MAX);
    REQUIRE(utils.add(INT_MIN, 0) == INT_MIN);
}

TEST_CASE("MathUtils::multiply - 正常场景") {
    MathUtils utils;
    REQUIRE(utils.multiply(3, 4) == 12);
    REQUIRE(utils.multiply(0, 100) == 0);
}
```

## 4. 集成测试模式

### 4.1 测试思路

集成测试采用 **模块间协作验证**，适用于：
- 多个模块/类的交互测试
- 数据流验证
- 接口契约测试

**核心思路**：
1. 分析模块间依赖关系
2. AI 生成集成测试用例
3. 支持真实执行和 AI 模拟执行两种模式

### 4.2 智能化实现

#### 4.2.1 AI 生成流程

```
项目代码分析
    ├─ 识别模块边界
    ├─ 分析依赖关系
    ├─ 理解数据流
    └─ 识别接口契约
    ↓
AI 生成集成测试
    ├─ 模块间调用测试
    ├─ 数据传递验证
    ├─ 错误传播测试
    └─ 状态转换测试
    ↓
测试执行模式选择
    ├─ 真实执行（编译运行）
    └─ AI 模拟执行（快速验证）
```

#### 4.2.2 技术实现

**AI 生成器** (`backend/app/services/test_generation.py`)：

```python
async def generate_integration_test_from_code(
    self,
    file_content: str,
    file_name: str,
    project_info: Dict[str, Any],
    additional_info: Optional[str] = None
) -> str:
    """
    生成集成测试用例
    
    特点：
    - 分析多个文件/模块
    - 生成模块间交互测试
    - 验证数据流和状态转换
    """
```

**AI 模拟执行**：

```python
async def execute_tests_with_ai(
    self,
    test_code: str,
    source_code: str,
    source_file_name: str
) -> Dict[str, Any]:
    """
    使用 AI 模拟执行测试用例
    
    优势：
    - 无需编译环境
    - 快速验证测试逻辑
    - 识别潜在问题
    """
```

#### 4.2.3 执行流程

**模式1：真实执行**
```
1. 编译测试代码和被测代码
    ↓
2. 运行测试用例
    ↓
3. 收集执行结果
```

**模式2：AI 模拟执行**
```
1. AI 分析源代码和测试代码
    ↓
2. 模拟执行每个测试用例
    ↓
3. 推断执行结果
    ├─ 通过/失败判断
    ├─ 失败原因分析
    └─ 潜在问题识别
    ↓
4. 返回模拟结果
```

#### 4.2.4 智能化特性

- **快速验证**：AI 模拟执行，无需编译环境即可验证测试逻辑
- **问题预测**：AI 分析可能失败的测试用例及原因
- **依赖分析**：自动识别模块依赖，生成合理的测试顺序
- **数据流追踪**：验证数据在模块间的正确传递

## 5. 静态分析模式

### 5.1 测试思路

静态分析采用 **代码质量检查 + AI 深度分析**，适用于：
- 代码质量检查
- 潜在缺陷发现
- 编码规范验证

**核心思路**：
1. 传统工具（Cppcheck）进行基础检查
2. AI 进行深度语义分析
3. 结合两种结果，提供综合报告

### 5.2 智能化实现

#### 5.2.1 分析流程

```
源代码输入
    ↓
传统工具分析（Cppcheck）
    ├─ 语法检查
    ├─ 常见错误检测
    └─ 编码规范检查
    ↓
AI 深度分析（可选）
    ├─ 语义理解
    ├─ 逻辑缺陷识别
    ├─ 设计问题发现
    └─ 安全漏洞检测
    ↓
结果融合
    ├─ 去重
    ├─ 优先级排序
    └─ 生成综合报告
```

#### 5.2.2 技术实现

**静态分析服务** (`backend/app/static_analysis/service.py`)：

```python
class StaticAnalysisService:
    """静态分析服务"""
    
    def run_analysis(
        self,
        project_id: int,
        project_path: str,
        language: Optional[str] = None,
        use_llm: bool = True  # 是否使用AI分析
    ) -> Dict[str, Any]:
        """
        运行静态分析
        
        模式：
        1. 仅传统工具（use_llm=False）
        2. 传统工具 + AI分析（use_llm=True）
        """
```

**执行器** (`backend/app/executors/static_executor.py`)：
- 支持多种静态分析工具（Cppcheck、Clazy 等）
- 统一结果格式
- 支持增量分析

#### 5.2.3 智能化特性

- **深度语义分析**：AI 理解代码语义，发现工具无法检测的问题
- **上下文感知**：结合项目上下文，提供更准确的建议
- **问题分类**：自动分类问题类型（性能、安全、可维护性等）
- **修复建议**：AI 提供具体修复建议和代码示例

## 6. 系统测试模式

### 6.1 测试思路

系统测试采用 **端到端场景验证**，适用于：
- 完整业务流程测试
- 用户场景验证
- 系统级测试

**核心思路**：
1. 基于需求描述生成测试套件
2. 使用 Robot Framework 执行
3. 支持无头模式（Xvfb）执行

### 6.2 智能化实现

#### 6.2.1 AI 生成流程

```
需求描述输入
    ├─ 功能需求
    ├─ 测试场景
    └─ 图像资源
    ↓
AI 生成测试套件
    ├─ 生成主测试文件
    ├─ 生成资源文件
    ├─ 组织测试用例
    └─ 配置执行参数
    ↓
保存为 Test IR
```

#### 6.2.2 技术实现

**系统测试生成** (`backend/app/api/v1/endpoints/system_tests.py`)：

```python
@router.post("/projects/{project_id}/system-tests/generate")
def generate_system_tests(
    project_id: int,
    payload: SystemTestGenerateRequest,
    ...
):
    """
    生成系统测试套件
    
    输入：
    - requirements: 测试需求描述
    - image_files: 图像资源列表
    - entry: 入口文件名称
    
    输出：
    - 完整的 Robot Framework 测试套件
    """
```

## 7. 测试执行架构

### 7.1 异步任务队列

**设计**：基于 Redis Queue 的异步执行

```
API 接收请求
    ↓
创建 TestExecution 记录（状态=pending）
    ↓
任务推入队列
    ├─ high: 高优先级
    ├─ default: 默认
    └─ low: 低优先级
    ↓
Worker 拾取任务
    ↓
更新状态为 running
    ↓
调用对应 Executor
    ↓
保存结果
    ↓
更新状态为 completed/failed
```

### 7.2 结果收集

**统一结果格式**：
```json
{
  "passed": true/false,
  "logs": "执行日志",
  "error_message": "错误信息（如有）",
  "coverage": {
    "line_coverage": 85.5,
    "branch_coverage": 78.2,
    "details": {...}
  },
  "artifacts": [
    {
      "type": "coverage_report",
      "path": "/path/to/report.html"
    },
    {
      "type": "screenshot",
      "path": "/path/to/screenshot.png"
    }
  ]
}
```

## 8. 最佳实践

### 8.1 系统测试

1. **图像资源管理**：
   - 使用清晰的图像资源命名
   - 保持图像资源版本一致
   - 定期更新过时的图像资源

2. **测试描述**：
   - 使用清晰、具体的步骤描述
   - 明确指定图像资源名称
   - 包含预期结果验证

3. **稳定性**：
   - 设置合理的超时时间
   - 使用等待机制而非固定延迟
   - 处理界面变化和异常情况

### 8.2 单元测试

1. **测试覆盖**：
   - 正常场景：验证基本功能
   - 边界条件：最大值、最小值、空值等
   - 异常场景：错误输入、异常情况

2. **代码质量**：
   - 只测试 public 接口
   - 避免测试实现细节
   - 保持测试独立性和可重复性

3. **AI 生成优化**：
   - 提供项目文档要点，帮助 AI 理解上下文
   - 审查生成的测试用例
   - 根据执行结果迭代优化

### 8.3 集成测试

1. **模块边界**：
   - 明确模块职责
   - 定义清晰的接口契约
   - 验证数据传递正确性

2. **测试策略**：
   - 自底向上：先测试底层模块
   - 自顶向下：先测试高层模块
   - 混合策略：根据实际情况选择

### 8.4 静态分析

1. **工具选择**：
   - 基础检查：使用 Cppcheck 等工具
   - 深度分析：结合 AI 分析
   - 持续集成：定期运行分析

2. **问题处理**：
   - 按优先级处理问题
   - 区分严重问题和建议
   - 记录修复历史

## 9. 未来规划

1. **AI 能力增强**：
   - 支持更多编程语言
   - 提高生成代码质量
   - 学习项目特点，个性化生成

2. **测试优化**：
   - 智能测试用例选择
   - 增量测试执行
   - 测试用例优先级排序

3. **集成扩展**：
   - CI/CD 集成
   - 更多测试工具支持
   - 测试数据管理

4. **可视化增强**：
   - 测试覆盖率热力图
   - 测试执行时间线
   - 问题趋势分析

---

本文档描述了 HomemadeTester 平台的测试策略和智能化实现方案。通过 AI 技术的应用，我们显著降低了测试用例编写成本，提高了测试覆盖率和质量。

