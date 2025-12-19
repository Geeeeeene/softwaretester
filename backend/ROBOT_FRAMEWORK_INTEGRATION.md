# Robot Framework + SikuliLibrary 集成说明

## 集成概述

本文档说明如何在自动化测试平台中使用新增的Robot Framework + SikuliLibrary功能来测试Qt流程图编辑器项目。

## 已实现的功能

### 1. 核心组件

- ✅ **TestType枚举扩展**: 添加了 `ROBOT_FRAMEWORK` 测试类型
- ✅ **RobotFrameworkExecutor**: 专门的执行器来运行Robot Framework测试
- ✅ **ExecutorFactory集成**: 自动路由Robot Framework测试到正确的执行器
- ✅ **依赖管理**: requirements.txt已更新包含必要的库

### 2. 辅助工具

- ✅ **安装脚本**: 
  - Windows: `scripts/setup_robot_framework.ps1`
  - Linux/macOS: `scripts/setup_robot_framework.sh`
- ✅ **示例测试用例**: `examples/robot_framework_examples.json`
- ✅ **详细文档**: `ROBOT_FRAMEWORK_GUIDE.md`

## 快速开始

### 步骤1: 安装依赖

#### Windows

```powershell
cd backend
.\scripts\setup_robot_framework.ps1
```

#### Linux/macOS

```bash
cd backend
chmod +x scripts/setup_robot_framework.sh
./scripts/setup_robot_framework.sh
```

### 步骤2: 准备测试图像资源

为你的Qt流程图编辑器准备UI元素截图：

```
backend/examples/robot_resources/
├── main_window.png          # 主窗口截图
├── new_file_button.png      # 新建按钮
├── save_button.png          # 保存按钮
├── toolbar_items/           # 工具栏项目
│   ├── rectangle_tool.png
│   ├── circle_tool.png
│   └── connector_tool.png
└── dialogs/                 # 对话框
    ├── save_dialog.png
    └── open_dialog.png
```

**截图技巧**:
1. 确保应用程序窗口在前台
2. 使用截图工具精确截取目标元素
3. 保存为PNG格式
4. 文件命名清晰描述用途

### 步骤3: 创建测试用例

#### 通过Web界面创建

1. 登录测试平台
2. 选择项目
3. 点击"创建测试用例"
4. 选择测试类型: `Robot Framework`
5. 填写测试信息并编写Robot脚本
6. 保存并执行

#### 通过API创建

```python
import requests

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 创建测试用例
test_case_data = {
    "name": "Qt流程图编辑器-启动测试",
    "description": "验证应用程序能正常启动并显示主窗口",
    "test_type": "robot_framework",
    "project_id": 1,  # 你的项目ID
    "priority": "high",
    "test_ir": {
        "test_type": "robot_framework",
        "name": "启动测试",
        "description": "测试应用启动",
        "robot_script": """
*** Settings ***
Library    SikuliLibrary

*** Variables ***
${APP_PATH}    C:/Program Files/FlowchartEditor/FlowchartEditor.exe

*** Test Cases ***
验证应用启动
    [Documentation]    验证应用程序能正常启动
    [Tags]    smoke
    Add Image Path    examples/robot_resources
    Start Sikuli Process
    Run    ${APP_PATH}
    Sleep    3s
    Wait Until Screen Contain    main_window.png    30
    Capture Screen    screenshots/startup_success.png
    Stop Remote Server
        """,
        "variables": {
            "APP_PATH": "C:/Program Files/FlowchartEditor/FlowchartEditor.exe"
        },
        "timeout": 120
    },
    "tags": ["qt", "smoke", "ui"]
}

# 发送请求
response = requests.post(
    f"{BASE_URL}/testcases",
    json=test_case_data
)

if response.status_code == 200:
    test_case = response.json()
    print(f"测试用例创建成功，ID: {test_case['id']}")
    
    # 执行测试
    exec_response = requests.post(
        f"{BASE_URL}/testcases/{test_case['id']}/execute"
    )
    
    if exec_response.status_code == 200:
        execution = exec_response.json()
        print(f"测试执行已启动，执行ID: {execution['execution_id']}")
else:
    print(f"创建失败: {response.text}")
```

### 步骤4: 查看测试结果

测试执行后，系统会生成：

1. **输出文件**: `artifacts/robot_framework/{test_name}/output.xml`
2. **日志文件**: `artifacts/robot_framework/{test_name}/log.html` - 详细的执行日志
3. **报告文件**: `artifacts/robot_framework/{test_name}/report.html` - 测试报告
4. **截图文件**: `artifacts/robot_framework/{test_name}/screenshots/*.png`

通过API获取结果：

```python
# 获取执行结果
result = requests.get(f"{BASE_URL}/executions/{execution_id}")
execution_data = result.json()

print(f"状态: {execution_data['status']}")
print(f"是否通过: {execution_data['passed']}")
print(f"日志: {execution_data['logs']}")
print(f"产物: {execution_data['artifacts']}")
```

## 测试用例示例

### 示例1: 基础功能测试

```robot
*** Settings ***
Library    SikuliLibrary
Suite Setup    启动应用
Suite Teardown    关闭应用

*** Variables ***
${APP_PATH}    C:/Program Files/FlowchartEditor/FlowchartEditor.exe

*** Test Cases ***
创建新流程图
    点击新建按钮
    验证空白画布显示
    
添加矩形节点
    选择矩形工具
    在画布上点击
    验证节点已创建

保存流程图
    点击保存按钮
    输入文件名    test.flow
    确认保存
    验证文件已保存

*** Keywords ***
启动应用
    Add Image Path    examples/robot_resources
    Start Sikuli Process
    Run    ${APP_PATH}
    Sleep    3s
    Wait Until Screen Contain    main_window.png    30

关闭应用
    Press Special Key    Key.ALT+Key.F4
    Sleep    1s
    Stop Remote Server

点击新建按钮
    Click    new_file_button.png
    Sleep    0.5s

验证空白画布显示
    Wait Until Screen Contain    blank_canvas.png    10
    Capture Screen    screenshots/blank_canvas.png
```

### 示例2: 拖拽交互测试

```robot
*** Test Cases ***
拖拽节点到新位置
    [Documentation]    测试节点拖拽功能
    # 创建节点
    Click    rectangle_tool.png
    Click    300    200
    Sleep    0.5s
    
    # 拖拽节点
    Drag And Drop    node_handle.png    target_location.png
    Sleep    0.5s
    
    # 验证
    Screen Should Contain    node_at_target.png
    Capture Screen    screenshots/node_dragged.png

连接两个节点
    [Documentation]    测试节点连接功能
    # 创建第一个节点
    Click    rectangle_tool.png
    Click    300    200
    
    # 创建第二个节点
    Click    rectangle_tool.png
    Click    300    400
    
    # 使用连线工具连接
    Click    connector_tool.png
    Click    300    250
    Click    300    350
    
    # 验证连线
    Wait Until Screen Contain    connection_line.png    5
    Capture Screen    screenshots/nodes_connected.png
```

## Test IR 格式说明

### 完整脚本格式

```json
{
  "test_type": "robot_framework",
  "name": "测试名称",
  "description": "测试描述",
  "robot_script": "完整的Robot Framework脚本内容",
  "variables": {
    "VAR1": "value1",
    "VAR2": "value2"
  },
  "resources": [
    "path/to/image1.png",
    "path/to/image2.png"
  ],
  "timeout": 120
}
```

### 结构化步骤格式

```json
{
  "test_type": "robot_framework",
  "name": "测试名称",
  "description": "测试描述",
  "libraries": ["SikuliLibrary", "OperatingSystem"],
  "variables": {
    "APP_PATH": "C:/Program Files/App/App.exe"
  },
  "steps": [
    "Add Image Path    resources",
    "Start Sikuli Process",
    "Run    ${APP_PATH}",
    "Sleep    3s",
    "Wait Until Screen Contain    main.png    30",
    "Click    button.png",
    "Stop Remote Server"
  ],
  "tags": ["smoke", "ui"]
}
```

## 架构说明

### 执行流程

```
用户提交测试用例
    ↓
API接收请求 (FastAPI)
    ↓
存储到数据库 (SQLAlchemy)
    ↓
创建执行任务
    ↓
ExecutorFactory.get_executor(TestType.ROBOT_FRAMEWORK)
    ↓
RobotFrameworkExecutor.execute()
    ↓
1. 验证Test IR
2. 生成.robot文件
3. 复制资源文件
4. 执行robot命令
5. 解析输出结果
6. 收集产物
    ↓
返回执行结果
    ↓
更新数据库记录
    ↓
用户查看结果
```

### 文件结构

```
backend/
├── app/
│   ├── executors/
│   │   ├── base_executor.py
│   │   ├── robot_framework_executor.py  # 新增
│   │   └── executor_factory.py          # 已更新
│   └── models/
│       └── testcase.py                   # 已更新（新增TestType）
├── artifacts/
│   └── robot_framework/                  # 测试输出目录
│       └── {test_name}/
│           ├── output.xml
│           ├── log.html
│           ├── report.html
│           └── screenshots/
├── examples/
│   ├── robot_framework_examples.json     # 示例用例
│   ├── robot_resources/                  # 测试图像资源
│   └── robot_quick_test.robot           # 快速测试
├── scripts/
│   ├── setup_robot_framework.ps1        # Windows安装脚本
│   └── setup_robot_framework.sh         # Linux/macOS安装脚本
├── ROBOT_FRAMEWORK_GUIDE.md             # 使用指南
└── ROBOT_FRAMEWORK_INTEGRATION.md       # 本文档
```

## 前端集成建议

### 创建测试用例表单

前端可以添加一个专门的Robot Framework测试用例创建界面：

```typescript
// 示例组件结构
interface RobotFrameworkTestForm {
  name: string;
  description: string;
  scriptType: 'full' | 'structured';  // 完整脚本或结构化步骤
  robotScript?: string;                // 完整脚本模式
  libraries?: string[];                // 结构化模式
  steps?: string[];                    // 结构化模式
  variables: Record<string, string>;
  resources: File[];                   // 图像文件上传
  timeout: number;
  tags: string[];
}
```

### 结果展示

```typescript
interface RobotFrameworkResult {
  passed: boolean;
  logs: string;
  artifacts: Array<{
    type: 'robot_output' | 'robot_log' | 'robot_report' | 'screenshot';
    path: string;
    name: string;
  }>;
}

// 展示Robot Framework HTML报告
<iframe src={`/artifacts/${result.artifacts.find(a => a.type === 'robot_report').path}`} />

// 展示截图
{result.artifacts.filter(a => a.type === 'screenshot').map(screenshot => (
  <img src={`/artifacts/${screenshot.path}`} alt={screenshot.name} />
))}
```

## 调试与故障排除

### 常见问题

#### 1. SikuliLibrary导入失败

**症状**: 执行测试时报错 "ImportError: No module named SikuliLibrary"

**解决方案**:
```bash
# 检查是否正确安装
python -c "import SikuliLibrary"

# 重新安装
pip install robotframework-sikulilibrary

# 检查Java环境
java -version
```

#### 2. 图像识别失败

**症状**: "FindFailed: can not find image.png"

**解决方案**:
- 确认图像文件路径正确
- 检查图像质量和特征明显性
- 验证屏幕分辨率和DPI设置一致
- 尝试增加等待时间
- 使用更大或更具特征的图像区域

#### 3. 测试超时

**症状**: 测试执行时间过长导致超时

**解决方案**:
- 增加timeout设置
- 优化等待时间
- 检查应用是否正常响应
- 简化测试步骤

### 启用详细日志

在robot_script中添加：

```robot
*** Settings ***
Library    SikuliLibrary    mode=INFO    timeout=10
```

### 手动运行测试调试

```bash
# 直接运行robot文件进行调试
cd backend
robot --outputdir artifacts/debug examples/robot_quick_test.robot
```

## 性能优化建议

1. **图像优化**: 使用适当大小的图像（不要太大）
2. **并行执行**: 配置多个测试并行运行
3. **智能等待**: 使用Wait Until而非固定Sleep
4. **资源复用**: 共享公共的关键字定义
5. **选择性截图**: 仅在必要时截图

## 扩展功能建议

### 1. 图像库管理

创建一个图像资源管理系统：
- 上传和组织测试图像
- 图像版本控制
- 跨测试用例共享图像

### 2. 可视化测试编辑器

提供拖拽式界面来创建测试：
- 可视化选择操作类型
- 图像选择器
- 自动生成Robot脚本

### 3. 智能图像捕获

集成截图工具：
- 自动识别UI元素
- 智能命名建议
- 自动裁剪和优化

### 4. 测试录制功能

录制用户操作自动生成测试：
- 记录鼠标和键盘操作
- 自动截取关键UI元素
- 生成Robot Framework脚本

## 与其他测试类型的协作

Robot Framework测试可以与平台中的其他测试类型配合：

```python
# 测试套件示例
test_suite = {
    "name": "完整测试套件",
    "tests": [
        {"type": "static", "name": "静态代码分析"},
        {"type": "unit", "name": "单元测试"},
        {"type": "robot_framework", "name": "UI系统测试"},
        {"type": "memory", "name": "内存检测"}
    ]
}
```

## 最佳实践总结

1. **图像管理**: 统一管理和命名测试图像
2. **模块化**: 使用Keywords抽取可复用逻辑
3. **文档化**: 为每个测试用例添加详细文档
4. **标签化**: 使用标签组织和过滤测试
5. **截图验证**: 关键步骤添加截图便于调试
6. **稳定性**: 添加适当的等待确保测试稳定
7. **维护性**: 定期更新图像资源适应UI变化

## 下一步

1. 运行安装脚本配置环境
2. 准备Qt应用的UI元素截图
3. 参考示例创建第一个测试用例
4. 通过API执行并查看结果
5. 根据需要调整和优化测试

## 技术支持

- 查看 `ROBOT_FRAMEWORK_GUIDE.md` 获取详细使用说明
- 参考 `examples/robot_framework_examples.json` 获取示例
- 查阅 Robot Framework 官方文档
- 提交Issue报告问题或建议

祝测试愉快！🚀

