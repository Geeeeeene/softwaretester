# 🤖 AI驱动的UI自动化测试系统

> 基于Robot Framework + SikuliLibrary + Claude AI的完整UI自动化测试解决方案

## 🎯 项目概述

本系统成功将**Robot Framework + SikuliLibrary**集成到自动化测试平台中，并使用**Claude AI**自动生成测试脚本，实现了真正的智能化UI自动化测试。

### 核心特性

- 🤖 **AI自动生成测试脚本**：只需描述测试场景，Claude AI自动生成完整的Robot Framework脚本
- 🖼️ **图像识别测试**：基于SikuliLibrary，无需修改应用代码，直接识别UI元素
- 📊 **完整的测试管理**：项目创建、测试执行、结果查看、历史统计一站式解决
- 🎨 **友好的Web界面**：四栏式布局，多步骤对话框，操作简单直观
- 📈 **详细的测试报告**：执行日志、测试报告、截图等完整artifacts

## 🚀 快速开始

### 5分钟上手

1. **创建UI测试项目**
   ```
   项目名称：我的UI测试
   项目类型：UI测试
   源代码路径：C:\path\to\your\app.exe
   ```

2. **准备图像资源**
   ```
   将UI元素截图放到：backend/examples/robot_resources/
   例如：main_window.png, button.png
   ```

3. **AI生成测试用例**
   ```
   测试名称：应用启动测试
   测试描述：
   测试应用程序能否正常启动并显示主窗口。
   测试步骤：
   1. 启动应用程序
   2. 等待5秒让应用完全加载
   3. 验证主窗口是否出现（检查main_window.png）
   4. 关闭应用程序
   ```

4. **执行测试并查看结果**
   - 点击"执行UI测试"
   - 等待测试完成
   - 查看详细的测试报告

详细教程请查看：[UI_TEST_QUICK_START.md](UI_TEST_QUICK_START.md)

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| [UI_TEST_QUICK_START.md](UI_TEST_QUICK_START.md) | 5分钟快速开始指南 |
| [UI_TEST_INTEGRATION_GUIDE.md](UI_TEST_INTEGRATION_GUIDE.md) | 完整的使用指南和最佳实践 |
| [UI_TEST_IMPLEMENTATION_SUMMARY.md](UI_TEST_IMPLEMENTATION_SUMMARY.md) | 技术实现总结和架构说明 |
| [ROBOT_FRAMEWORK_GUIDE.md](ROBOT_FRAMEWORK_GUIDE.md) | Robot Framework基础指南 |
| [SCREENSHOT_GUIDE.md](SCREENSHOT_GUIDE.md) | 截图最佳实践 |

## 🏗️ 系统架构

### 技术栈

**后端**：
- FastAPI - Web框架
- SQLAlchemy - ORM
- Anthropic SDK - Claude API
- Robot Framework - 测试框架
- SikuliLibrary - 图像识别

**前端**：
- React + TypeScript
- React Query - 数据管理
- Tailwind CSS - 样式

### 核心模块

```
├── 后端
│   ├── app/ui_test/ai_generator.py      # AI脚本生成器
│   ├── app/api/v1/endpoints/ui_test.py  # API端点
│   └── app/executors/robot_framework_executor.py  # 测试执行器
│
└── 前端
    ├── pages/UITestPage.tsx              # UI测试页面
    ├── components/ui-test/UITestDialog.tsx  # 测试对话框
    └── lib/api.ts                        # API客户端
```

### 数据流

```
用户描述测试场景
    ↓
Claude AI生成Robot Framework脚本
    ↓
验证脚本有效性
    ↓
用户确认并执行
    ↓
RobotFrameworkExecutor异步执行
    ↓
解析测试结果
    ↓
展示详细报告
```

## 💡 使用示例

### 示例1：登录功能测试

**测试描述**：
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

**AI生成的脚本**：
```robot
*** Settings ***
Library    SikuliLibrary
Library    Process
Library    OperatingSystem

*** Variables ***
${APP_PATH}           C:\path\to\app.exe
${IMAGE_PATH}         examples/robot_resources
${TIMEOUT}            30

*** Test Cases ***
用户登录测试
    [Documentation]    测试用户登录功能
    [Tags]    ui-test    login
    
    # 启动应用
    Start Process    ${APP_PATH}    alias=app
    Sleep    5s
    
    # 设置图像识别
    Add Image Path    ${IMAGE_PATH}
    Set Min Similarity    0.7
    
    # 等待登录窗口
    Wait Until Screen Contain    login_window.png    ${TIMEOUT}
    
    # 输入用户名
    Click    username_field.png
    Input Text    username_field.png    admin
    
    # 输入密码
    Click    password_field.png
    Input Text    password_field.png    password123
    
    # 点击登录
    Click    login_button.png
    
    # 验证登录成功
    Wait Until Screen Contain    main_dashboard.png    ${TIMEOUT}
    Screen Should Contain    main_dashboard.png
    
    # 清理
    [Teardown]    Terminate Process    app    kill=True
```

### 示例2：文件操作测试

**测试描述**：
```
测试文件的创建和保存功能。
测试步骤：
1. 启动应用程序
2. 点击"文件"菜单（menu_file.png）
3. 点击"新建"选项（menu_new.png）
4. 在编辑区输入内容
5. 点击"保存"按钮（button_save.png）
6. 验证保存成功提示（success_message.png）
7. 关闭应用程序
```

AI会根据这个描述生成相应的测试脚本！

## 🎨 界面预览

### UI测试页面（四栏布局）

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
```

### 测试对话框（多步骤）

```
步骤1: 输入测试信息
  ↓
步骤2: 查看生成的脚本
  ↓
步骤3: 执行测试（显示进度）
  ↓
步骤4: 查看测试结果
```

## ⚙️ 环境配置

### 必需环境

```bash
# Python 3.8+
python --version

# Robot Framework
pip install robotframework

# SikuliLibrary
pip install robotframework-sikulilibrary

# Java 8+（SikuliLibrary需要）
java -version

# Anthropic SDK
pip install anthropic
```

### 配置Claude API

在 `backend/app/core/config.py` 中配置：

```python
CLAUDE_API_KEY = "sk-xxx..."
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
CLAUDE_BASE_URL = "https://work.poloapi.com"
```

## 📊 功能特性详解

### 1. AI脚本生成

**输入**：自然语言测试描述

**输出**：完整的Robot Framework脚本

**优势**：
- 无需学习Robot Framework语法
- 自动生成最佳实践代码
- 包含完整的错误处理
- 支持复杂的测试场景

### 2. 图像识别测试

**基于SikuliLibrary**：
- 通过图像匹配定位UI元素
- 无需修改应用代码
- 支持任何GUI应用
- 跨平台支持

**常用操作**：
- `Wait Until Screen Contain` - 等待元素出现
- `Click` - 点击元素
- `Input Text` - 输入文本
- `Screen Should Contain` - 断言元素存在

### 3. 测试执行管理

**异步执行**：
- 不阻塞API响应
- 支持长时间运行的测试
- 实时状态更新

**结果收集**：
- 详细的执行日志
- HTML测试报告
- XML输出文件
- 截图artifacts

### 4. 测试历史和统计

**执行历史**：
- 所有测试执行记录
- 状态和时间信息
- 详细结果查看

**统计信息**：
- 总执行次数
- 完成次数
- 通过次数
- 通过率计算

## 🔍 调试技巧

### 图像识别失败？

1. **使用SikuliX自己的截图**
   ```python
   # 使用 create_target_image.py 从SikuliX截图中裁剪
   python backend/create_target_image.py
   ```

2. **调整相似度**
   ```robot
   Set Min Similarity    0.6  # 降低到60%
   ```

3. **检查分辨率**
   - 确保截图和实际屏幕分辨率一致
   - 注意Windows DPI缩放设置

### 测试超时？

1. **增加等待时间**
   ```robot
   ${TIMEOUT}    60  # 增加到60秒
   ```

2. **添加更多Sleep**
   ```robot
   Sleep    10s  # 等待应用完全启动
   ```

### AI生成的脚本不理想？

1. **提供更详细的描述**
   - 明确每个步骤
   - 指定图像文件名
   - 说明预期结果

2. **手动修改脚本**
   - 生成后可以手动调整
   - 保存为模板供后续使用

## 📈 最佳实践

### 1. 测试描述编写

✅ **好的描述**：
```
测试用户登录功能。
测试步骤：
1. 启动应用程序
2. 等待登录窗口出现（login_window.png）
3. 点击用户名输入框（username_field.png）
...
```

❌ **不好的描述**：
```
测试登录
```

### 2. 图像文件管理

✅ **好的命名**：
- `main_window.png`
- `login_button.png`
- `username_field.png`

❌ **不好的命名**：
- `img1.png`
- `screenshot.png`
- `test.png`

### 3. 测试组织

- 每个测试关注单一功能
- 使用描述性的测试名称
- 添加适当的Tags
- 确保测试独立性

## 🐛 常见问题

### Q: Java环境配置问题？

**A**: 确保Java已安装并配置到PATH：
```bash
# Windows
set JAVA_HOME=D:\Downloads\java
set PATH=%JAVA_HOME%\bin;%PATH%

# 验证
java -version
```

### Q: Claude API调用失败？

**A**: 检查以下几点：
1. API Key是否正确
2. 网络连接是否正常
3. API配额是否用完
4. Base URL是否正确

### Q: 图像识别总是失败？

**A**: 参考我们之前的调试经验：
1. 使用同源图像（SikuliX截图）
2. 使用`create_target_image.py`裁剪
3. 调整相似度阈值
4. 检查DPI缩放设置

## 🎓 学习资源

- [Robot Framework官方文档](https://robotframework.org/)
- [SikuliLibrary GitHub](https://github.com/rainmanwy/robotframework-SikuliLibrary)
- [Claude AI文档](https://docs.anthropic.com/)
- 本项目的详细文档（见上方文档导航）

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🎉 总结

这是一个**生产就绪**的完整UI自动化测试解决方案，具有：

- ✅ AI驱动，降低测试编写成本
- ✅ 图像识别，无需修改应用代码
- ✅ 完整工作流，从创建到报告
- ✅ 友好界面，操作简单直观
- ✅ 详细文档，快速上手

**立即开始您的UI自动化测试之旅吧！** 🚀

---

**需要帮助？** 查看[完整使用指南](UI_TEST_INTEGRATION_GUIDE.md)或[快速开始](UI_TEST_QUICK_START.md)

