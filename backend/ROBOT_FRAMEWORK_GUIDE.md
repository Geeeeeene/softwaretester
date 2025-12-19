# Robot Framework + SikuliLibrary 使用指南

## 概述

本平台已集成 Robot Framework 和 SikuliLibrary，用于对Qt应用程序进行基于图像识别的系统级自动化测试。

## 什么是 Robot Framework？

Robot Framework 是一个开源的自动化测试框架，使用关键字驱动的测试方法，易于学习和使用。

## 什么是 SikuliLibrary？

SikuliLibrary 是 Robot Framework 的一个库，提供基于图像识别的UI自动化功能，特别适合测试桌面应用程序。

## 安装步骤

### Windows

```powershell
cd backend
.\scripts\setup_robot_framework.ps1
```

### Linux/macOS

```bash
cd backend
chmod +x scripts/setup_robot_framework.sh
./scripts/setup_robot_framework.sh
```

### 手动安装

```bash
# 安装Robot Framework
pip install robotframework

# 安装SikuliLibrary
pip install robotframework-sikulilibrary

# 安装Pillow（图像处理）
pip install Pillow

# 下载SikuliX（需要Java环境）
# 访问: https://raiman.github.io/SikuliX1/downloads.html
```

## 依赖要求

1. **Python 3.8+**
2. **Java JDK 8+** (SikuliX需要)
3. **操作系统**: Windows, Linux, macOS

## 快速开始

### 1. 准备测试图像

在进行图像识别测试前，需要准备好待识别的UI元素截图：

```
backend/examples/robot_resources/
├── main_window.png          # 主窗口
├── new_file_button.png      # 新建按钮
├── save_button.png          # 保存按钮
├── rectangle_tool.png       # 矩形工具
└── ...
```

**图像准备最佳实践**：
- 使用PNG格式保存，保持高质量
- 截图应包含独特的视觉特征
- 避免包含动态内容（如时间戳）
- 图像大小适中（不要整个屏幕）
- 保持屏幕DPI设置一致

### 2. 创建测试用例

#### 方式A: 使用完整的Robot脚本

```python
test_ir = {
    "test_type": "robot_framework",
    "name": "Qt流程图编辑器测试",
    "description": "测试基本功能",
    "robot_script": """
*** Settings ***
Library    SikuliLibrary

*** Variables ***
${APP_PATH}    C:/Program Files/FlowchartEditor/FlowchartEditor.exe

*** Test Cases ***
启动应用并验证主窗口
    [Documentation]    测试应用启动
    Add Image Path    resources
    Start Sikuli Process
    Run    ${APP_PATH}
    Sleep    3s
    Wait Until Screen Contain    main_window.png    30
    Click    new_file_button.png
    Capture Screen    screenshots/test_result.png
    Stop Remote Server
    """,
    "variables": {
        "APP_PATH": "C:/Program Files/FlowchartEditor/FlowchartEditor.exe"
    },
    "timeout": 120
}
```

#### 方式B: 使用结构化步骤

```python
test_ir = {
    "test_type": "robot_framework",
    "name": "简单测试",
    "description": "使用结构化步骤定义",
    "libraries": ["SikuliLibrary", "OperatingSystem"],
    "variables": {
        "APP_PATH": "C:/Program Files/FlowchartEditor/FlowchartEditor.exe"
    },
    "steps": [
        "Add Image Path    resources",
        "Start Sikuli Process",
        "Run    ${APP_PATH}",
        "Sleep    3s",
        "Wait Until Screen Contain    main_window.png    30",
        "Click    new_file_button.png",
        "Stop Remote Server"
    ],
    "tags": ["smoke", "ui"]
}
```

### 3. 通过API执行测试

```python
import requests

# 创建测试用例
response = requests.post(
    "http://localhost:8000/api/v1/testcases",
    json={
        "name": "Qt流程图编辑器测试",
        "test_type": "robot_framework",
        "project_id": 1,
        "test_ir": test_ir,
        "priority": "high",
        "tags": ["qt", "ui", "system-test"]
    }
)

testcase_id = response.json()["id"]

# 执行测试
response = requests.post(
    f"http://localhost:8000/api/v1/testcases/{testcase_id}/execute"
)

execution_id = response.json()["execution_id"]

# 获取执行结果
response = requests.get(
    f"http://localhost:8000/api/v1/executions/{execution_id}"
)

print(response.json())
```

## Robot Framework 常用关键字

### SikuliLibrary 关键字

| 关键字 | 说明 | 示例 |
|--------|------|------|
| `Start Sikuli Process` | 启动Sikuli进程 | `Start Sikuli Process` |
| `Stop Remote Server` | 停止Sikuli服务 | `Stop Remote Server` |
| `Add Image Path` | 添加图像搜索路径 | `Add Image Path    resources` |
| `Click` | 点击图像 | `Click    button.png` |
| `Double Click` | 双击图像 | `Double Click    icon.png` |
| `Right Click` | 右键点击 | `Right Click    item.png` |
| `Wait Until Screen Contain` | 等待图像出现 | `Wait Until Screen Contain    dialog.png    10` |
| `Screen Should Contain` | 验证图像存在 | `Screen Should Contain    message.png` |
| `Input Text` | 输入文本 | `Input Text    Hello World` |
| `Press Special Key` | 按特殊键 | `Press Special Key    Key.ENTER` |
| `Drag And Drop` | 拖拽 | `Drag And Drop    source.png    target.png` |
| `Capture Screen` | 截屏 | `Capture Screen    result.png` |

### 常用特殊键

- `Key.ENTER` - 回车
- `Key.TAB` - Tab键
- `Key.ESC` - Esc键
- `Key.DELETE` - Delete键
- `Key.BACKSPACE` - 退格键
- `Key.ALT` - Alt键
- `Key.CTRL` - Ctrl键
- `Key.SHIFT` - Shift键
- `Key.F1` - F1键（F1-F12）

组合键示例：
```robot
Press Special Key    Key.CTRL+Key.S    # Ctrl+S 保存
Press Special Key    Key.ALT+Key.F4    # Alt+F4 关闭窗口
```

## 测试脚本结构

### 基本结构

```robot
*** Settings ***
# 导入库
Library    SikuliLibrary
Library    OperatingSystem

# 测试套件设置
Suite Setup    启动测试环境
Suite Teardown    清理测试环境
Test Timeout    2 minutes

*** Variables ***
# 定义变量
${APP_PATH}    C:/Program Files/MyApp/MyApp.exe
${TIMEOUT}     30

*** Test Cases ***
# 测试用例
测试用例1
    [Documentation]    用例说明
    [Tags]    smoke    ui
    # 测试步骤
    步骤1
    步骤2
    验证结果

测试用例2
    [Documentation]    另一个用例
    [Tags]    功能测试
    执行操作
    验证结果

*** Keywords ***
# 自定义关键字
启动测试环境
    Add Image Path    resources
    Start Sikuli Process

清理测试环境
    Stop Remote Server

步骤1
    Click    button1.png
    Sleep    1s
```

## Qt应用测试最佳实践

### 1. 启动和初始化

```robot
*** Keywords ***
启动Qt应用
    [Arguments]    ${app_path}
    Add Image Path    resources
    Start Sikuli Process
    Run    ${app_path}
    Sleep    3s
    Wait Until Screen Contain    main_window.png    30
```

### 2. 等待UI就绪

Qt应用可能有启动动画或加载过程：

```robot
等待应用就绪
    Wait Until Screen Contain    ready_indicator.png    timeout=30
    Sleep    0.5s    # 额外等待确保稳定
```

### 3. 处理对话框

```robot
处理保存对话框
    Wait Until Screen Contain    save_dialog.png    10
    Input Text    my_file.txt
    Press Special Key    Key.ENTER
    Sleep    1s
```

### 4. 拖拽操作

```robot
拖拽节点
    Drag And Drop    node_source.png    canvas_target.png
    Sleep    0.5s
    # 验证拖拽成功
    Screen Should Contain    node_at_new_position.png
```

### 5. 菜单操作

```robot
打开文件菜单
    Click    menu_file.png
    Sleep    0.3s
    Click    menu_open.png
```

### 6. 组合键操作

```robot
保存文件
    Press Special Key    Key.CTRL+Key.S
    Sleep    0.5s

撤销操作
    Press Special Key    Key.CTRL+Key.Z
```

## 调试技巧

### 1. 添加截图

在关键步骤添加截图便于调试：

```robot
执行操作
    Click    button.png
    Capture Screen    screenshots/after_click.png
    验证结果
```

### 2. 添加日志

```robot
Log    开始执行测试步骤1
Click    button.png
Log    按钮点击完成
```

### 3. 调整等待时间

如果测试不稳定，尝试增加等待时间：

```robot
Click    button.png
Sleep    1s    # 等待动画完成
Wait Until Screen Contain    result.png    20
```

### 4. 图像匹配失败

如果图像匹配失败：
- 检查图像文件路径是否正确
- 验证图像质量和大小
- 考虑屏幕分辨率和DPI差异
- 使用更具特征的图像区域

## 示例项目

参考 `backend/examples/robot_framework_examples.json` 获取完整示例。

### 示例1：基本功能测试

测试流程图编辑器的启动、创建节点、连接节点等基本功能。

### 示例2：拖拽功能测试

测试拖拽节点移动、从工具栏拖拽组件等交互功能。

### 示例3：完整工作流测试

测试创建流程图 → 编辑 → 保存 → 关闭的完整工作流。

## 常见问题

### Q: SikuliLibrary导入失败

A: 确保已安装Java环境，并正确安装了SikuliX。检查环境变量JAVA_HOME是否设置正确。

### Q: 图像识别不准确

A: 
- 使用高质量PNG图像
- 确保测试环境和截图环境的屏幕设置一致
- 尝试截取更具特征的图像区域
- 考虑使用相似度阈值调整

### Q: 测试运行缓慢

A: 
- 减少不必要的Sleep等待
- 使用Wait Until关键字替代固定等待
- 优化图像大小和数量
- 并行运行测试用例

### Q: Windows高DPI问题

A: 在Windows高DPI屏幕上，可能需要：
- 设置应用程序兼容性（禁用DPI缩放）
- 使用相同DPI设置截取图像
- 或在代码中调整匹配相似度阈值

## 进阶主题

### 1. 图像相似度调整

```robot
Click    button.png    similarity=0.8
```

### 2. 区域识别

```robot
${region}=    Get Screen Region
Click In Region    button.png    ${region}
```

### 3. OCR文字识别

```robot
Library    SikuliLibrary
${text}=    Extract Text    text_area.png
Should Contain    ${text}    Expected Text
```

### 4. 参数化测试

```robot
*** Test Cases ***
测试不同输入
    [Template]    测试输入功能
    input1.txt    expected1
    input2.txt    expected2
    input3.txt    expected3

*** Keywords ***
测试输入功能
    [Arguments]    ${input}    ${expected}
    输入数据    ${input}
    验证结果    ${expected}
```

## 资源链接

- [Robot Framework 官方文档](https://robotframework.org/)
- [SikuliLibrary GitHub](https://github.com/rainmanwy/robotframework-SikuliLibrary)
- [SikuliX 官网](https://raiman.github.io/SikuliX1/)
- [Robot Framework 用户指南](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html)

## 支持与反馈

如有问题或建议，请通过项目issue系统反馈。

