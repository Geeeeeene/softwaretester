# UI测试集成使用指南

## 📋 概述

本系统已成功集成 **Robot Framework + SikuliLibrary** 作为UI测试的后端，支持使用AI自动生成测试脚本，实现基于图像识别的UI自动化测试。

## 🎯 功能特性

### 1. **AI驱动的测试用例生成**
- 使用Claude AI根据测试描述自动生成Robot Framework脚本
- 智能生成测试步骤、断言和错误处理逻辑
- 自动配置SikuliLibrary和Process库

### 2. **完整的UI测试工作流**
- 创建UI测试项目
- AI生成测试脚本
- 执行测试并实时监控
- 查看详细的测试结果和日志

### 3. **四栏式项目管理界面**
- **测试分析栏**：创建测试、查看结果
- **基本信息栏**：项目配置信息
- **源代码文件栏**：应用程序路径
- **测试统计栏**：执行记录和通过率

## 🚀 快速开始

### 步骤1：创建UI测试项目

在前端"项目管理"页面：

1. 点击"创建项目"
2. 填写项目信息：
   - **项目名称**：例如 "流程图编辑器UI测试"
   - **项目类型**：选择 "UI测试"
   - **源代码路径**：填写应用程序的完整路径
     ```
     例如：C:\Users\lenovo\Desktop\FreeCharts\diagramscene.exe
     ```
3. 点击"创建项目"

创建成功后会自动跳转到UI测试页面。

### 步骤2：准备图像资源

在执行测试前，需要准备用于图像识别的截图：

1. 运行您的应用程序
2. 截取需要识别的UI元素（如按钮、窗口、图标等）
3. 将截图保存为PNG格式
4. 放置到项目的 `backend/examples/robot_resources/` 目录下

**推荐截图方法**：
- 使用 Win + Shift + S 截取小区域
- 或使用之前的 `create_target_image.py` 脚本从SikuliX截图中裁剪

**命名建议**：
- `main_window.png` - 主窗口
- `login_button.png` - 登录按钮
- `menu_file.png` - 文件菜单
- 等等...

### 步骤3：使用AI生成测试用例

在UI测试页面：

1. 点击"UI测试（使用AI生成UI测试用例）"按钮
2. 在弹窗中填写：
   - **测试用例名称**：例如 "应用启动测试"
   - **测试描述**：详细描述测试场景和步骤
     ```
     示例：
     测试应用程序能否正常启动并显示主窗口。
     测试步骤：
     1. 启动应用程序
     2. 等待5秒让应用完全加载
     3. 验证主窗口是否出现（检查main_window.png）
     4. 点击某个按钮（click_button.png）
     5. 验证结果窗口出现（result_window.png）
     6. 关闭应用程序
     ```
3. 点击"生成测试用例"

AI会根据您的描述生成完整的Robot Framework脚本。

### 步骤4：查看生成的脚本

生成完成后，弹窗会显示：
- 测试用例名称
- 测试描述
- **Robot Framework脚本**（可以查看和验证）

脚本示例：
```robot
*** Settings ***
Library    SikuliLibrary
Library    Process
Library    OperatingSystem

*** Variables ***
${APP_PATH}           C:\Users\lenovo\Desktop\FreeCharts\diagramscene.exe
${IMAGE_PATH}         examples/robot_resources
${TIMEOUT}            30

*** Test Cases ***
应用启动测试
    [Documentation]    测试应用程序能否正常启动并显示主窗口
    [Tags]    ui-test    auto-generated
    
    # 1. 启动应用程序
    Start Process    ${APP_PATH}    alias=app_under_test
    Sleep    5s
    
    # 2. 设置图像识别参数
    Add Image Path    ${IMAGE_PATH}
    Set Min Similarity    0.7
    
    # 3. 验证主窗口
    Wait Until Screen Contain    main_window.png    ${TIMEOUT}
    
    # 4. 清理
    [Teardown]    Terminate Process    app_under_test    kill=True
```

### 步骤5：执行UI测试

1. 确认脚本无误后，点击"执行UI测试"
2. 系统会在后台执行测试
3. 弹窗显示"测试执行中..."状态

### 步骤6：查看测试结果

测试完成后，弹窗会显示：
- ✓ 测试通过 / ✗ 测试失败
- 执行时长
- 错误信息（如果有）
- 详细的测试日志
- 生成的文件（output.xml, log.html, report.html等）

点击"完成"关闭弹窗。

### 步骤7：查看执行历史

在UI测试页面：
- 点击"查看测试结果"按钮
- 或滚动到"测试执行历史"部分

可以看到：
- 所有执行记录
- 每次执行的状态（通过/失败/执行中）
- 执行时间和时长
- 测试结果统计

点击"查看详情"可以查看单次执行的完整信息。

## 📊 测试统计

在UI测试页面的"测试统计"卡片中，可以实时查看：
- **测试用例数**：创建的测试用例总数
- **执行记录数**：完成的测试执行次数
- **通过率**：测试通过的百分比

## 🔧 技术架构

### 后端架构

```
UI测试模块
├── app/ui_test/
│   ├── __init__.py
│   └── ai_generator.py          # AI测试脚本生成器
├── app/api/v1/endpoints/
│   └── ui_test.py                # UI测试API端点
├── app/executors/
│   └── robot_framework_executor.py  # Robot Framework执行器
└── examples/robot_resources/     # 图像资源目录
```

### API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/projects/{id}/ui-test/generate` | POST | 使用AI生成测试用例 |
| `/projects/{id}/ui-test/execute` | POST | 执行UI测试 |
| `/projects/{id}/ui-test/results/{execution_id}` | GET | 获取测试结果 |
| `/projects/{id}/ui-test/executions` | GET | 获取执行历史 |

### 数据流

```
用户输入测试描述
    ↓
Claude AI生成Robot Framework脚本
    ↓
验证脚本有效性
    ↓
保存到数据库并返回给前端
    ↓
用户点击执行
    ↓
RobotFrameworkExecutor执行测试
    ↓
解析测试结果（output.xml, log.html等）
    ↓
更新数据库执行记录
    ↓
前端轮询获取结果并展示
```

## 📝 AI提示词模板

系统使用以下提示词模板生成测试脚本：

```
你是一个Robot Framework + SikuliLibrary专家。请根据以下需求生成一个完整的UI自动化测试脚本。

【测试需求】
测试用例名称：{name}
测试描述：{description}

【项目信息】
- 项目名称：{project_name}
- 应用程序路径：{app_path}
- 项目描述：{project_description}

【技术要求】
1. 使用Robot Framework语法编写测试脚本
2. 使用SikuliLibrary进行基于图像识别的UI自动化测试
3. 使用Process库来启动和管理应用程序进程
...
```

## 🎨 前端界面

### UI测试页面布局

```
┌─────────────────────────────────────────────────────────┐
│  [← 返回]  项目名称 - UI测试                              │
├─────────────┬─────────────┬─────────────┬───────────────┤
│  测试分析    │  基本信息    │ 源代码文件   │  测试统计      │
│             │             │             │               │
│ [UI测试]    │ 项目名称     │ 源代码路径   │ 测试用例: 5   │
│ [查看结果]  │ 项目描述     │ C:\app.exe  │ 执行记录: 10  │
│             │ 创建时间     │             │ 通过率: 80%   │
└─────────────┴─────────────┴─────────────┴───────────────┘
│                                                           │
│  测试执行历史                                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │ ✓ 执行 #1  [通过]  2025-12-18 17:30  [查看详情]   │  │
│  │ ✗ 执行 #2  [失败]  2025-12-18 17:35  [查看详情]   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 测试对话框

```
┌─────────────────────────────────────────────────────────┐
│  UI测试（使用AI生成测试用例）                    [×]      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  测试用例名称 *                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 应用启动测试                                     │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  测试描述 *                                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 测试应用程序能否正常启动并显示主窗口...          │    │
│  │                                                  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│                            [取消]  [生成测试用例]         │
└─────────────────────────────────────────────────────────┘
```

## 🛠️ 配置说明

### 环境变量配置

在 `backend/app/core/config.py` 中配置：

```python
# Claude API配置（用于AI生成测试脚本）
CLAUDE_API_KEY: Optional[str] = "sk-xxx..."
CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929"
CLAUDE_BASE_URL: Optional[str] = "https://work.poloapi.com"
```

### 依赖安装

确保已安装以下依赖：

```bash
# Python依赖
pip install robotframework
pip install robotframework-sikulilibrary
pip install Pillow
pip install anthropic

# Java环境（SikuliLibrary需要）
# 确保Java已安装并配置到PATH
java -version
```

## 📖 最佳实践

### 1. 测试描述编写

**好的测试描述**：
```
测试用户登录功能。
测试步骤：
1. 启动应用程序
2. 等待登录窗口出现（login_window.png）
3. 点击用户名输入框（username_field.png）
4. 输入用户名"admin"
5. 点击密码输入框（password_field.png）
6. 输入密码"password123"
7. 点击登录按钮（login_button.png）
8. 验证主界面出现（main_dashboard.png）
9. 关闭应用程序
```

**不好的测试描述**：
```
测试登录
```

### 2. 图像命名规范

- 使用描述性名称：`login_button.png` 而不是 `img1.png`
- 使用小写和下划线：`main_window.png`
- 包含元素类型：`submit_button.png`, `username_field.png`

### 3. 相似度设置

- 默认使用 `0.7`（70%相似度）
- 如果匹配失败，可以降低到 `0.6` 或 `0.5`
- 如果误匹配，可以提高到 `0.8` 或 `0.9`

### 4. 等待时间

- 应用启动：`Sleep 5s` 或更长
- UI响应：`Sleep 1s` 到 `3s`
- 使用 `Wait Until Screen Contain` 而不是固定Sleep

## 🐛 常见问题

### Q1: AI生成的脚本无法执行？

**A**: 检查以下几点：
1. 应用程序路径是否正确
2. 图像文件是否存在于 `examples/robot_resources/` 目录
3. Java环境是否正确配置
4. SikuliLibrary是否正确安装

### Q2: 图像识别失败？

**A**: 参考之前的调试经验：
1. 使用SikuliX自己截取的图像
2. 使用 `create_target_image.py` 从SikuliX截图中裁剪
3. 调整相似度阈值
4. 确保截图和实际屏幕分辨率一致

### Q3: 测试超时？

**A**: 
1. 增加 `${TIMEOUT}` 变量的值
2. 在应用启动后增加 `Sleep` 时间
3. 检查应用是否真的启动成功

### Q4: Claude API调用失败？

**A**:
1. 检查 `CLAUDE_API_KEY` 是否正确配置
2. 检查网络连接
3. 检查API配额是否用完

## 📚 参考资料

- [Robot Framework官方文档](https://robotframework.org/)
- [SikuliLibrary文档](https://github.com/rainmanwy/robotframework-SikuliLibrary)
- [之前的Robot Framework集成文档](ROBOT_FRAMEWORK_GUIDE.md)
- [截图指南](SCREENSHOT_GUIDE.md)

## 🎉 总结

现在您已经拥有了一个完整的、AI驱动的UI自动化测试系统！

**核心优势**：
- ✅ AI自动生成测试脚本，无需手写
- ✅ 基于图像识别，无需修改应用代码
- ✅ 完整的Web界面，操作简单直观
- ✅ 详细的测试报告和日志
- ✅ 支持测试历史和统计分析

**下一步**：
1. 为您的应用准备更多的UI元素截图
2. 编写更多的测试场景描述
3. 让AI为您生成测试脚本
4. 执行测试并持续改进

祝测试顺利！🚀

