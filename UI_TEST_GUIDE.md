# UI测试功能使用指南

## 功能概述

本系统集成了基于 **Robot Framework + SikuliLibrary** 的UI自动化测试功能，支持通过AI自动生成测试用例脚本。

## 功能特点

1. **AI驱动的测试用例生成**：使用Claude AI根据测试描述自动生成Robot Framework脚本
2. **图像识别测试**：基于SikuliLibrary实现UI元素的图像识别和操作
3. **完整的测试流程**：从用例创建、脚本生成、测试执行到结果查看的全流程支持
4. **详细的测试报告**：包含测试日志、执行时长、成功/失败状态等信息

## 使用步骤

### 1. 创建UI测试项目

1. 进入"项目管理"页面
2. 点击"创建项目"
3. 选择项目类型为"**UI测试**"
4. 填写以下必填项：
   - **项目名称**：测试项目的名称
   - **源代码路径**：待测试应用的源代码路径
5. 填写描述（可选）
6. 点击右下角"创建项目"按钮

创建成功后会自动跳转到该项目的UI测试分析界面。

### 2. UI测试分析界面

界面分为四栏：

#### 第一栏：测试分析
- **UI测试（使用AI生成UI测试用例）**：点击后打开测试用例生成对话框
- **查看测试结果**：滚动到页面底部查看执行历史

#### 第二栏：基本信息
显示项目的基本配置信息：
- 项目名称
- 项目描述
- 项目类型
- 创建时间

#### 第三栏：源代码文件
显示配置的源代码路径信息

#### 第四栏：测试统计
- **测试用例**：执行总次数
- **执行记录**：完成的测试次数
- **通过率**：测试成功的百分比

### 3. 使用AI生成测试用例

1. 点击"UI测试（使用AI生成UI测试用例）"按钮
2. 在弹窗中填写：
   - **测试用例名称**：如"登录功能测试"
   - **测试描述**：详细描述测试场景和步骤，例如：
     ```
     1. 打开登录页面
     2. 输入用户名和密码
     3. 点击登录按钮
     4. 验证登录成功
     ```
3. 点击"生成测试用例"按钮
4. AI将自动生成完整的Robot Framework脚本
5. 查看生成的脚本，确认无误后点击"执行UI测试"

### 4. 执行UI测试

点击"执行UI测试"后：
- 系统在后台执行Robot Framework脚本
- 显示"测试执行中..."状态
- 自动轮询测试状态（每2秒刷新）
- 执行完成后显示测试结果

### 5. 查看测试结果

执行完成后会显示：
- **测试状态**：通过/失败
- **执行时长**：测试运行的秒数
- **错误信息**：如果失败，显示详细错误
- **测试日志**：完整的执行日志
- **生成的文件**：
  - `output.xml`：Robot Framework输出文件
  - `log.html`：测试日志（HTML格式）
  - `report.html`：测试报告（HTML格式）
  - 测试截图（如有）

### 6. 查看历史记录

在UI测试页面底部的"测试执行历史"区域：
- 查看所有测试执行记录
- 每条记录显示：
  - 执行ID和状态（执行中/通过/失败）
  - 执行时间
  - 执行时长
  - 测试结果统计
  - 错误信息（如果有）
- 点击"查看详情"查看完整的测试结果

## 技术栈

### 后端
- **FastAPI**：API框架
- **Robot Framework**：测试框架
- **SikuliLibrary**：UI图像识别库
- **Claude API**：AI测试用例生成

### 前端
- **React + TypeScript**：UI框架
- **TanStack Query**：数据获取和缓存
- **Tailwind CSS**：样式框架

## API端点

### 1. 生成UI测试用例
```
POST /api/v1/projects/{project_id}/ui-test/generate
```
请求体：
```json
{
  "name": "测试用例名称",
  "description": "测试描述"
}
```

### 2. 执行UI测试
```
POST /api/v1/projects/{project_id}/ui-test/execute
```
请求体：
```json
{
  "name": "测试用例名称",
  "description": "测试描述",
  "robot_script": "Robot Framework脚本内容"
}
```

### 3. 获取测试结果
```
GET /api/v1/projects/{project_id}/ui-test/results/{execution_id}
```

### 4. 获取执行历史
```
GET /api/v1/projects/{project_id}/ui-test/executions
```

## 配置说明

在 `backend/app/core/config.py` 中配置Claude API：

```python
# 大模型API配置（用于深度静态分析和UI测试用例生成）
CLAUDE_API_KEY: Optional[str] = "your-api-key"
CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929"
CLAUDE_BASE_URL: Optional[str] = "https://work.poloapi.com"
```

## 注意事项

1. **API密钥**：需要配置有效的Claude API密钥才能使用AI生成功能
2. **Robot Framework安装**：确保系统已安装Robot Framework和SikuliLibrary
3. **依赖检查**：可使用 `RobotFrameworkExecutor.check_dependencies()` 检查依赖是否安装
4. **图像资源**：如需使用图像识别，需准备好对应的UI元素截图
5. **执行环境**：建议在有图形界面的环境中执行UI测试

## 依赖安装

### Python依赖
```bash
pip install robotframework robotframework-sikulilibrary anthropic
```

### 系统依赖
- **Java**：SikuliLibrary需要Java运行环境
- **Jython**：部分SikuliLibrary功能需要

## 故障排除

### 1. 生成测试用例失败
- 检查Claude API密钥是否正确配置
- 检查网络连接是否正常
- 查看后端日志获取详细错误信息

### 2. 测试执行失败
- 检查Robot Framework是否正确安装
- 检查SikuliLibrary依赖是否完整
- 查看测试日志中的错误信息

### 3. 无法查看结果
- 检查测试执行是否已完成
- 刷新页面重新加载数据
- 检查后端数据库连接

## 未来扩展

1. **测试用例库**：保存和复用常用测试用例
2. **批量执行**：支持一次执行多个测试用例
3. **定时任务**：定时自动执行UI测试
4. **测试录制**：录制UI操作自动生成测试脚本
5. **更多AI模型**：支持其他AI模型（如GPT-4、通义千问等）

## 联系支持

如有问题或建议，请联系开发团队。

