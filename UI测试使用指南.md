# 🧪 UI测试使用指南

## 📋 概述

本系统使用 **Robot Framework + SikuliLibrary** 进行UI自动化测试，支持通过AI自动生成测试脚本。

## 🚀 快速开始

### 前置条件

1. **确保服务已启动**
   - 后端API服务（Docker 或本地）
   - 前端服务（Docker 或本地）
   - Redis服务（Docker 或本地）
   - PostgreSQL数据库（Docker 或本地）
   - **Windows Worker（必须启动，用于执行UI测试）**

2. **环境要求**
   - Python 3.10+（系统Python，用于运行Robot Framework）
   - Java JDK（SikuliLibrary需要）
   - Robot Framework 已安装：`py -m pip install robotframework robotframework-sikulilibrary`

## 🔧 启动Windows Worker

### 为什么需要Windows Worker？

UI测试需要在Windows主机上执行，因为：
- 需要访问Windows应用程序（.exe文件）
- 需要Java环境运行SikuliLibrary
- 需要系统Python运行Robot Framework

### 启动步骤

#### 方法1：使用PowerShell（推荐）

1. **打开新的PowerShell窗口**

2. **进入后端目录**
   ```powershell
   cd C:\Users\Lenovo\Desktop\softwaretester\backend
   ```

3. **设置环境变量**
   ```powershell
   # Redis连接地址（如果使用Docker，通常是localhost:6379）
   $env:REDIS_URL="redis://localhost:6379/0"
   
   # 指定监听windows_ui队列
   $env:RQ_QUEUES="windows_ui"
   
   # 数据库连接（必须与后端API使用同一个数据库）
   # 如果使用Docker Compose，使用PostgreSQL
   $env:DATABASE_URL="postgresql://tester:tester123@localhost:5432/homemade_tester"
   ```

4. **启动Worker**
   ```powershell
   python -m app.worker.worker
   ```

5. **验证启动成功**
   看到以下输出表示启动成功：
   ```
   📋 从环境变量读取队列配置: RQ_QUEUES=windows_ui
   🚀 Worker启动成功（Windows模式），监听队列: ['windows_ui']
   15:54:59 Worker rq:worker:xxx started with PID xxxxx, version 1.15.1
   15:54:59 Subscribing to channel rq:pubsub:xxx
   15:54:59 *** Listening on windows_ui...
   ```

#### 方法2：创建启动脚本（方便重复使用）

创建文件 `backend/start_worker.ps1`：
```powershell
# Windows UI Worker 启动脚本

Write-Host "🚀 启动Windows UI Worker..." -ForegroundColor Cyan

# 设置环境变量
$env:REDIS_URL="redis://localhost:6379/0"
$env:RQ_QUEUES="windows_ui"
$env:DATABASE_URL="postgresql://tester:tester123@localhost:5432/homemade_tester"

# 进入后端目录
Set-Location $PSScriptRoot

# 启动Worker
Write-Host "📋 配置信息:" -ForegroundColor Yellow
Write-Host "   Redis: $env:REDIS_URL" -ForegroundColor Gray
Write-Host "   队列: $env:RQ_QUEUES" -ForegroundColor Gray
Write-Host "   数据库: $env:DATABASE_URL" -ForegroundColor Gray
Write-Host ""

python -m app.worker.worker
```

然后运行：
```powershell
.\backend\start_worker.ps1
```

#### 方法3：使用批处理文件

创建文件 `backend/start_worker.bat`：
```batch
@echo off
echo 🚀 启动Windows UI Worker...

set REDIS_URL=redis://localhost:6379/0
set RQ_QUEUES=windows_ui
set DATABASE_URL=postgresql://tester:tester123@localhost:5432/homemade_tester

cd /d %~dp0
python -m app.worker.worker

pause
```

然后双击运行 `start_worker.bat`

### 验证Worker是否正常工作

1. **检查Worker日志**
   - 启动后应该看到 "Listening on windows_ui..."
   - 没有错误信息

2. **执行一个测试**
   - 在前端创建一个UI测试并执行
   - Worker控制台应该显示：
     ```
     windows_ui: app.worker.tasks.run_ui_test(...)
     ▶️  开始执行UI测试 (ID: xx)
     ```

3. **检查队列状态**
   - 如果任务被成功接收，Worker会开始处理
   - 如果任务一直等待，检查：
     - Worker是否正在运行
     - 队列名称是否正确（`windows_ui`）
     - Redis连接是否正常

### 常见问题

#### 问题1：Worker无法连接到Redis

**错误信息**：`ConnectionError: Error connecting to Redis`

**解决方法**：
1. 检查Redis是否运行：`docker ps | grep redis`
2. 检查Redis端口：默认6379
3. 如果使用Docker，确保Redis容器已启动

#### 问题2：Worker无法连接到数据库

**错误信息**：`❌ 执行记录 xx 不存在` 或数据库连接错误

**解决方法**：
1. 确保设置了正确的 `DATABASE_URL`
2. 如果后端使用PostgreSQL，Worker也必须使用PostgreSQL
3. 检查数据库连接字符串格式

#### 问题3：Worker启动后立即退出

**可能原因**：
- Python环境问题
- 缺少依赖包
- 配置文件错误

**解决方法**：
1. 检查Python版本：`python --version`（应该是3.10+）
2. 安装依赖：`pip install -r requirements.txt`
3. 检查错误日志

#### 问题4：任务执行失败 - SIGALRM错误

**错误信息**：`AttributeError: module 'signal' has no attribute 'SIGALRM'`

**解决方法**：
- 确保使用最新版本的 `backend/app/worker/worker.py`
- 该问题已在代码中修复（使用Windows兼容的Worker）

### Worker运行状态

Worker运行时会显示：
- ✅ 启动成功信息
- 📋 队列配置信息
- 🔍 任务接收和执行日志
- ✅ 任务完成信息

**注意**：Worker窗口必须保持打开状态，关闭窗口会停止Worker。

## 📝 使用步骤

### 步骤1：创建UI测试项目

1. 访问前端：http://localhost:5173
2. 点击 **"创建项目"** 按钮
3. 填写项目信息：
   - **项目名称**：例如 "FreeCharts UI测试"
   - **项目类型**：选择 **"UI测试"**
   - **源代码路径**：填写要测试的应用程序路径
     - 例如：`C:\Users\Lenovo\Desktop\FreeCharts_Release\FreeCharts\diagramscene.exe`
   - **项目描述**：可选，描述项目用途
4. 点击 **"创建"** 按钮

### 步骤2：进入UI测试页面

1. 在项目列表中，找到刚创建的UI测试项目
2. 点击项目名称进入项目详情页
3. 点击 **"UI测试"** 标签页（或直接访问 `/projects/{项目ID}/ui-test`）

### 步骤3：使用AI生成测试用例

1. 在UI测试页面，点击 **"UI测试（使用AI生成UI测试用例）"** 按钮
2. 填写测试信息：
   - **测试用例名称**：例如 "测试退出功能"
   - **测试描述**：详细描述测试步骤，例如：
     ```
     1. 启动应用程序
     2. 等待屏幕上出现主界面 (main_window.png)
     3. 点击退出按钮 (exit_button.png)
     4. 验证屏幕上出现退出确认对话框 (exit_ask_window.png)
     5. 关闭应用程序
     ```
3. 点击 **"生成测试用例"** 按钮
   - AI会自动生成Robot Framework脚本
   - 生成过程可能需要10-30秒

### 步骤4：查看生成的脚本

生成完成后，会显示：
- **测试用例名称**
- **测试描述**
- **Robot Framework 脚本**（可查看和编辑）

生成的脚本包含：
- Robot Framework 设置（导入SikuliLibrary等）
- 变量定义（应用程序路径、图像路径等）
- 测试用例步骤

### 步骤5：执行测试

1. 查看生成的脚本，确认无误
2. 点击 **"执行UI测试"** 按钮
3. 测试会自动提交到 Windows Worker 队列执行
4. 页面会自动跳转到执行状态页面

### 步骤6：查看测试结果

执行过程中，页面会显示：
- **执行状态**：running（执行中）、completed（完成）、failed（失败）
- **实时日志**：显示测试执行的详细日志
- **测试结果**：
  - 通过/失败状态
  - 执行时间
  - 错误信息（如果有）

## 🎯 功能特性

### 1. AI自动生成测试脚本

- 使用 Claude AI 根据测试描述自动生成Robot Framework脚本
- 自动识别应用程序路径
- 自动配置图像识别路径

### 2. 图像识别测试

- 使用 SikuliLibrary 进行基于图像的UI测试
- 支持点击、等待、验证等操作
- 图像文件自动复制到工作目录

### 3. 测试用例管理

- 自动保存生成的测试用例
- 支持重复执行已保存的测试用例
- 查看测试执行历史

### 4. 实时执行监控

- 实时查看测试执行状态
- 自动刷新执行结果
- 详细的执行日志

## 📂 文件结构

### 测试用例保存位置

- **数据库**：测试用例信息保存在数据库中
- **脚本内容**：保存在 `test_ir` 字段中

### 执行结果保存位置

- **工作目录**：`backend/artifacts/robot_framework/work/{测试名称}/`
- **输出目录**：`backend/artifacts/robot_framework/{测试名称}/`
  - `output.xml`：Robot Framework输出XML
  - `log.html`：测试日志（HTML格式）
  - `report.html`：测试报告（HTML格式）

### 图像资源

- **源目录**：`backend/examples/robot_resources/`
- **工作目录**：自动复制到 `work/{测试名称}/robot_resources/`

## 🔧 配置说明

### 应用程序路径

在创建项目时，需要指定要测试的应用程序路径：
- **Windows路径格式**：`C:\Users\...\app.exe`
- 系统会自动转换为Robot Framework可用的格式

### 图像文件

1. 准备测试所需的图像文件（PNG格式）
2. 将图像文件放到 `backend/examples/robot_resources/` 目录
3. 在测试描述中引用图像文件名，例如：`main_window.png`

### Java环境

SikuliLibrary需要Java环境：
- 系统会自动检测 `JAVA_HOME` 环境变量
- 或配置在 `backend/app/core/config.py` 中

## 📊 测试执行流程

```
1. 用户填写测试信息
   ↓
2. AI生成Robot Framework脚本
   ↓
3. 脚本保存到数据库
   ↓
4. 提交到Windows Worker队列
   ↓
5. Worker执行测试：
   - 复制图像资源
   - 转换路径格式
   - 执行Robot Framework
   - 收集结果
   ↓
6. 更新执行记录
   ↓
7. 前端显示结果
```

## ⚠️ 注意事项

### 1. Windows Worker必须运行

- UI测试必须在Windows Worker中执行
- 确保Worker正在监听 `windows_ui` 队列
- Worker需要连接到PostgreSQL数据库

### 2. 应用程序路径

- 确保应用程序路径正确
- 路径中的反斜杠会自动转换为正斜杠
- 如果路径不存在，测试会失败

### 3. 图像识别

- 图像文件必须是PNG格式
- 图像文件名在脚本中引用
- 确保图像文件在 `robot_resources` 目录中

### 4. 测试超时

- 默认超时时间：300秒（5分钟）
- 可以在生成的脚本中修改 `TIMEOUT` 变量

## 🐛 故障排除

### 问题1：测试执行失败 - 找不到文件

**原因**：应用程序路径不正确

**解决**：
1. 检查项目配置中的源代码路径
2. 确保路径使用正斜杠或双反斜杠
3. 验证文件是否存在

### 问题2：图像识别失败

**原因**：图像文件不存在或路径不正确

**解决**：
1. 检查图像文件是否在 `backend/examples/robot_resources/` 目录
2. 确认图像文件名与脚本中引用的一致
3. 检查图像文件格式（必须是PNG）

### 问题3：Worker无法连接数据库

**原因**：Worker使用SQLite，而API使用PostgreSQL

**解决**：
设置环境变量：
```powershell
$env:DATABASE_URL="postgresql://tester:tester123@localhost:5432/homemade_tester"
```

### 问题4：Java环境未找到

**原因**：SikuliLibrary需要Java环境

**解决**：
1. 安装Java JDK
2. 设置 `JAVA_HOME` 环境变量
3. 或在配置文件中指定Java路径

## 📚 相关文档

- [Robot Framework 官方文档](https://robotframework.org/)
- [SikuliLibrary 文档](https://github.com/rainmanwy/robotframework-SikuliLibrary)
- [项目运行指南](./运行指南.md)

## 🎉 示例

### 示例1：测试应用程序退出功能

**测试描述**：
```
1. 启动应用程序
2. 等待屏幕上出现主界面 (main_window.png)
3. 点击退出按钮 (exit_button.png)
4. 验证屏幕上出现退出确认对话框 (exit_ask_window.png)
5. 关闭应用程序
```

**生成的脚本**（部分）：
```robot
*** Settings ***
Library    SikuliLibrary
Library    Process

*** Variables ***
${APP_PATH}           C:/Users/Lenovo/Desktop/FreeCharts_Release/FreeCharts/diagramscene.exe
${IMAGE_PATH}         C:/Users/Lenovo/Desktop/softwaretester/backend/artifacts/robot_framework/work/tuichu/robot_resources
${TIMEOUT}            30

*** Test Cases ***
tuichu
    Start Process    ${APP_PATH}    alias=app_under_test
    Sleep    5s
    
    Add Image Path    ${IMAGE_PATH}
    Set Min Similarity    0.7
    
    Wait Until Screen Contain    main_window.png    ${TIMEOUT}
    Click    exit_button.png
    Screen Should Contain    exit_ask_window.png
    
    [Teardown]    Terminate Process    app_under_test    kill=True
```

---

**祝您使用愉快！** 🚀

