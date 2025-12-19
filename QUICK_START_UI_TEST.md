# UI测试功能快速开始

## 5分钟快速上手

### 第一步：配置API密钥

编辑 `backend/app/core/config.py`，配置Claude API密钥（已配置可跳过）：

```python
CLAUDE_API_KEY: Optional[str] = "your-claude-api-key-here"
```

### 第二步：启动服务

**启动后端（终端1）：**
```bash
cd backend
python -m app.main
```

**启动前端（终端2）：**
```bash
cd frontend
npm run dev
```

### 第三步：创建UI测试项目

1. 打开浏览器访问 `http://localhost:5173`
2. 进入"项目管理"页面
3. 点击"创建项目"
4. 选择项目类型：**UI测试**
5. 填写：
   - 项目名称：`我的第一个UI测试`
   - 源代码路径：`./test-app`（或实际应用路径）
6. 点击"创建项目" → 自动跳转到UI测试页面

### 第四步：生成并执行测试

1. 点击"**UI测试（使用AI生成UI测试用例）**"按钮
2. 填写测试信息：
   ```
   测试用例名称：简单按钮点击测试
   
   测试描述：
   1. 启动应用程序
   2. 等待主窗口加载完成
   3. 点击"确定"按钮
   4. 验证操作成功
   ```
3. 点击"**生成测试用例**"（等待10-30秒）
4. 查看AI生成的Robot Framework脚本
5. 点击"**执行UI测试**"
6. 等待测试完成，查看结果

### 第五步：查看测试结果

执行完成后，页面显示：
- ✅ 测试通过 / ❌ 测试失败
- 执行时长
- 详细日志
- 生成的报告文件

## 完整示例：登录测试

### 测试场景描述（复制使用）

```
测试用例名称：用户登录功能测试

测试描述：
1. 启动被测应用程序
2. 等待登录窗口显示
3. 在用户名输入框中输入"testuser"
4. 在密码输入框中输入"password123"
5. 点击"登录"按钮
6. 等待3秒
7. 验证登录成功，主界面已显示
8. 检查是否显示用户名"testuser"
```

### 预期生成的脚本（参考）

```robot
*** Settings ***
Library    SikuliLibrary

*** Variables ***
${APP_PATH}    C:/path/to/your/app.exe
${TIMEOUT}     30

*** Test Cases ***
用户登录功能测试
    [Documentation]    测试用户登录功能是否正常
    [Tags]    login    ui
    
    # 启动应用
    Start Process    ${APP_PATH}
    Sleep    2s
    
    # 输入用户名
    Wait For Image    username_field.png    timeout=${TIMEOUT}
    Click    username_field.png
    Input Text    testuser
    
    # 输入密码
    Click    password_field.png
    Input Text    password123
    
    # 点击登录
    Click    login_button.png
    Sleep    3s
    
    # 验证登录成功
    Wait For Image    main_window.png    timeout=${TIMEOUT}
    ${result}=    Image Should Exist    user_label.png
    Should Be True    ${result}
```

## 常见问题

### Q1: 生成测试用例时报错"Claude API调用失败"
**A:** 检查以下几点：
1. API密钥是否正确配置
2. 网络连接是否正常
3. API额度是否充足

### Q2: 测试执行失败，提示"Robot Framework未安装"
**A:** 安装依赖：
```bash
pip install robotframework robotframework-sikulilibrary
```

### Q3: 无法识别UI元素
**A:** SikuliLibrary基于图像识别：
1. 需要准备UI元素的截图（.png文件）
2. 将截图放在测试脚本可访问的位置
3. 在脚本中引用截图文件名

### Q4: 测试执行中，没有响应
**A:** 
1. 查看后端日志，检查是否有错误
2. 确认Robot Framework进程是否正常运行
3. 刷新前端页面，状态会自动更新

## 下一步

- 📖 阅读完整的 [UI测试使用指南](./UI_TEST_GUIDE.md)
- 🔧 查看 [实现总结](./UI_TEST_IMPLEMENTATION_SUMMARY.md)
- 🧪 运行验证脚本：`python test_ui_test_api.py`

## 提示和技巧

### 1. 编写好的测试描述
- ✅ 详细描述每个操作步骤
- ✅ 包含明确的验证点
- ✅ 使用清晰的语言
- ❌ 避免模糊的描述

### 2. 准备UI元素截图
对于复杂的UI操作，提前准备好关键元素的截图：
- 按钮
- 输入框
- 标签
- 窗口标题

### 3. 调整超时时间
如果应用启动较慢，在测试描述中说明：
```
1. 启动应用程序（等待30秒）
2. ...
```

### 4. 批量执行
虽然当前版本不支持批量执行，但可以：
1. 保存多个测试脚本
2. 依次执行
3. 汇总结果

## 支持

遇到问题？
1. 查看后端日志：`backend/logs/`
2. 查看测试日志：UI测试页面的"测试日志"部分
3. 运行验证脚本：`python test_ui_test_api.py`

---

**开始你的UI自动化测试之旅！** 🚀

