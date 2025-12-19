# Robot Framework + SikuliLibrary 快速开始

## 概述

您的自动化测试平台现已集成 **Robot Framework** 和 **SikuliLibrary**，可以对Qt流程图编辑器进行基于图像识别的系统级自动化测试。

## 🎯 已完成的集成

### ✅ 核心功能
- **新测试类型**: `ROBOT_FRAMEWORK` 
- **专用执行器**: `RobotFrameworkExecutor`
- **自动路由**: 测试会自动分配到正确的执行器
- **依赖管理**: 所有必需的包已添加到 requirements.txt

### ✅ 工具和文档
- 📜 详细使用指南: `backend/ROBOT_FRAMEWORK_GUIDE.md`
- 🔧 安装脚本: `backend/scripts/setup_robot_framework.ps1` (Windows) / `.sh` (Linux/macOS)
- 📝 示例测试: `backend/examples/robot_framework_examples.json`
- 📚 集成说明: `backend/ROBOT_FRAMEWORK_INTEGRATION.md`

## 🚀 3步开始使用

### 第1步: 安装环境 (5分钟)

**Windows:**
```powershell
cd backend
.\scripts\setup_robot_framework.ps1
```

**Linux/macOS:**
```bash
cd backend
chmod +x scripts/setup_robot_framework.sh
./scripts/setup_robot_framework.sh
```

**需要的环境:**
- ✅ Python 3.8+
- ✅ Java JDK 8+ (SikuliX需要)

### 第2步: 准备测试图像 (10分钟)

为您的Qt流程图编辑器截取UI元素图像：

```
backend/examples/robot_resources/
├── main_window.png          # 主窗口
├── new_file_button.png      # 新建按钮
├── save_button.png          # 保存按钮
├── rectangle_tool.png       # 工具
└── ...
```

**截图技巧:**
- 使用 **Snipping Tool** (Windows) 或 **Screenshot** 工具
- 截取清晰、有特征的UI元素
- 保存为PNG格式
- 命名清晰易懂

### 第3步: 创建并运行测试 (5分钟)

#### 方式A: 通过API

```python
import requests

# 创建测试用例
response = requests.post(
    "http://localhost:8000/api/v1/testcases",
    json={
        "name": "Qt流程图编辑器-启动测试",
        "test_type": "robot_framework",
        "project_id": 1,
        "test_ir": {
            "test_type": "robot_framework",
            "name": "启动测试",
            "robot_script": """
*** Settings ***
Library    SikuliLibrary

*** Test Cases ***
验证应用启动
    Add Image Path    examples/robot_resources
    Start Sikuli Process
    Run    C:/Program Files/FlowchartEditor/FlowchartEditor.exe
    Sleep    3s
    Wait Until Screen Contain    main_window.png    30
    Capture Screen    screenshots/success.png
    Stop Remote Server
            """,
            "timeout": 120
        },
        "priority": "high",
        "tags": ["smoke", "qt"]
    }
)

# 执行测试
test_id = response.json()["id"]
exec_response = requests.post(
    f"http://localhost:8000/api/v1/testcases/{test_id}/execute"
)

print(f"测试执行ID: {exec_response.json()['execution_id']}")
```

#### 方式B: 直接运行Robot文件

```bash
# 测试安装
cd backend
robot examples/robot_quick_test.robot

# 查看报告
# 打开 output/log.html 和 report.html
```

## 📖 测试脚本示例

### 最简单的测试

```robot
*** Settings ***
Library    SikuliLibrary

*** Test Cases ***
点击按钮测试
    Add Image Path    examples/robot_resources
    Start Sikuli Process
    Click    button.png
    Sleep    1s
    Capture Screen    result.png
    Stop Remote Server
```

### 完整功能测试

```robot
*** Settings ***
Library    SikuliLibrary
Suite Setup    启动应用
Suite Teardown    关闭应用

*** Variables ***
${APP}    C:/Program Files/FlowchartEditor/FlowchartEditor.exe

*** Test Cases ***
创建流程图测试
    [Tags]    功能测试
    点击新建按钮
    添加矩形节点
    添加圆形节点
    连接节点
    保存流程图
    验证保存成功

*** Keywords ***
启动应用
    Add Image Path    examples/robot_resources
    Start Sikuli Process
    Run    ${APP}
    Sleep    3s
    Wait Until Screen Contain    main_window.png    30

关闭应用
    Press Special Key    Key.ALT+Key.F4
    Stop Remote Server

点击新建按钮
    Click    new_button.png
    Sleep    0.5s

添加矩形节点
    Click    rectangle_tool.png
    Click    300    200
    Sleep    0.5s

添加圆形节点
    Click    circle_tool.png
    Click    300    400
    Sleep    0.5s

连接节点
    Click    connector_tool.png
    Click    300    250
    Click    300    350
    Sleep    0.5s

保存流程图
    Press Special Key    Key.CTRL+Key.S
    Sleep    1s
    Input Text    test_flowchart.flow
    Press Special Key    Key.ENTER
    Sleep    1s

验证保存成功
    Screen Should Contain    save_success.png
    Capture Screen    screenshots/flowchart_saved.png
```

## 🔍 查看测试结果

测试执行后会生成：

1. **执行日志**: 在API响应的 `logs` 字段中
2. **HTML报告**: `backend/artifacts/robot_framework/{test_name}/report.html`
3. **详细日志**: `backend/artifacts/robot_framework/{test_name}/log.html`
4. **截图**: `backend/artifacts/robot_framework/{test_name}/screenshots/*.png`

**在浏览器中打开HTML报告**查看详细的测试执行情况，包括：
- 每个测试步骤的状态
- 执行时间统计
- 失败原因分析
- 截图记录

## 💡 常用操作速查

### 基本操作

| 操作 | 代码 |
|------|------|
| 点击图像 | `Click    button.png` |
| 双击 | `Double Click    icon.png` |
| 右键点击 | `Right Click    item.png` |
| 拖拽 | `Drag And Drop    source.png    target.png` |
| 等待图像出现 | `Wait Until Screen Contain    image.png    10` |
| 验证图像存在 | `Screen Should Contain    image.png` |
| 输入文本 | `Input Text    Hello World` |
| 按键 | `Press Special Key    Key.ENTER` |
| 截屏 | `Capture Screen    screenshot.png` |
| 等待 | `Sleep    2s` |

### 组合键

| 功能 | 代码 |
|------|------|
| 保存 (Ctrl+S) | `Press Special Key    Key.CTRL+Key.S` |
| 复制 (Ctrl+C) | `Press Special Key    Key.CTRL+Key.C` |
| 粘贴 (Ctrl+V) | `Press Special Key    Key.CTRL+Key.V` |
| 撤销 (Ctrl+Z) | `Press Special Key    Key.CTRL+Key.Z` |
| 关闭 (Alt+F4) | `Press Special Key    Key.ALT+Key.F4` |

## 🎓 学习路径

### 新手入门
1. ✅ 完成环境安装
2. 📸 准备几个简单的测试图像
3. 🧪 运行示例测试 `robot_quick_test.robot`
4. 📝 修改示例测试适应您的应用

### 进阶使用
1. 📚 阅读 `backend/ROBOT_FRAMEWORK_GUIDE.md`
2. 🔍 查看 `backend/examples/robot_framework_examples.json` 中的复杂示例
3. 🎯 创建完整的测试套件
4. 🔧 集成到CI/CD流程

### 高级功能
1. 自定义关键字库
2. 数据驱动测试
3. 测试报告定制
4. 并行执行优化

## ❓ 常见问题

### Q: 图像识别失败怎么办？

**A:** 
- 确保图像路径正确
- 检查图像是否清晰且有特征
- 尝试截取更大的区域
- 确认测试环境和截图环境的分辨率一致

### Q: 测试运行很慢？

**A:**
- 减少不必要的 `Sleep` 
- 使用 `Wait Until Screen Contain` 替代固定等待
- 优化图像大小
- 只在必要时截图

### Q: SikuliLibrary导入失败？

**A:**
```bash
# 确认Java已安装
java -version

# 重新安装
pip install robotframework-sikulilibrary

# 验证安装
python -c "import SikuliLibrary"
```

### Q: 如何调试测试？

**A:**
1. 添加更多的 `Capture Screen` 查看执行过程
2. 添加 `Log` 语句输出调试信息
3. 使用 `Sleep` 暂停观察
4. 查看生成的 `log.html` 详细日志

## 📁 项目文件结构

```
homemadeTester/
├── backend/
│   ├── app/
│   │   ├── executors/
│   │   │   └── robot_framework_executor.py    # ⭐ 新增
│   │   └── models/
│   │       └── testcase.py                     # 已更新
│   ├── artifacts/
│   │   └── robot_framework/                    # 测试输出
│   ├── examples/
│   │   ├── robot_framework_examples.json       # ⭐ 示例
│   │   ├── robot_resources/                    # 图像资源
│   │   └── robot_quick_test.robot             # ⭐ 快速测试
│   ├── scripts/
│   │   ├── setup_robot_framework.ps1          # ⭐ 安装脚本
│   │   └── setup_robot_framework.sh           # ⭐ 安装脚本
│   ├── ROBOT_FRAMEWORK_GUIDE.md               # ⭐ 详细指南
│   ├── ROBOT_FRAMEWORK_INTEGRATION.md         # ⭐ 集成说明
│   └── requirements.txt                        # 已更新
└── ROBOT_FRAMEWORK_QUICKSTART.md              # ⭐ 本文档
```

## 🔗 有用的资源

- 📘 [Robot Framework 官方文档](https://robotframework.org/)
- 📗 [SikuliLibrary GitHub](https://github.com/rainmanwy/robotframework-SikuliLibrary)
- 📙 [SikuliX 官网](https://raiman.github.io/SikuliX1/)
- 📕 本项目详细指南: `backend/ROBOT_FRAMEWORK_GUIDE.md`

## 🎉 下一步

现在您可以：

1. ✨ 运行安装脚本设置环境
2. 📸 为您的Qt流程图编辑器准备测试图像
3. 🚀 创建并运行第一个测试
4. 📊 查看测试报告
5. 🔄 逐步完善测试套件

**祝测试顺利！** 如有问题，请查阅详细文档或提交Issue。

---

💡 **提示**: 建议从简单的"启动应用并验证主窗口"测试开始，逐步增加更复杂的交互测试。

