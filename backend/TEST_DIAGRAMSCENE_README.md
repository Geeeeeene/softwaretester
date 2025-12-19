# Qt DiagramScene 流程图编辑器测试指南

## 测试文件

- **测试脚本**: `test_diagramscene.robot`
- **应用路径**: `C:\Users\lenovo\Desktop\diagramscene_ultima\build\Desktop_Qt_6_5_3_MinGW_64_bit-Debug\debug\diagramscene.exe`
- **测试图像**: `examples\robot_resources\main_window.png`

## 快速运行测试

### 运行所有测试

```powershell
cd C:\Users\lenovo\Desktop\homemadeTester\backend
py -m robot test_diagramscene.robot
```

### 运行特定测试

```powershell
# 只运行启动测试
py -m robot --test "测试1-验证应用启动" test_diagramscene.robot

# 只运行交互测试
py -m robot --test "测试2-简单交互测试" test_diagramscene.robot
```

### 按标签运行

```powershell
# 只运行smoke测试
py -m robot --include smoke test_diagramscene.robot

# 只运行交互测试
py -m robot --include interaction test_diagramscene.robot
```

## 测试说明

### 测试1: 验证应用启动
- **目的**: 验证DiagramScene应用能否正常启动
- **步骤**:
  1. 启动应用
  2. 等待主窗口出现（最多30秒）
  3. 截图记录
  4. 验证主窗口存在
  5. 关闭应用
- **预期结果**: 应用成功启动，主窗口正常显示

### 测试2: 简单交互测试
- **目的**: 测试基本的窗口交互
- **步骤**:
  1. 启动应用
  2. 点击主窗口
  3. 截图记录交互结果
  4. 关闭应用
- **预期结果**: 应用响应点击操作

## 查看测试结果

测试运行后，会在当前目录生成以下文件：

1. **log.html** - 详细的测试执行日志（推荐查看）
2. **report.html** - 测试报告概览
3. **output.xml** - XML格式的测试输出
4. **screenshots/** - 测试过程中的截图

### 在浏览器中打开报告

```powershell
# 打开测试报告
start log.html

# 或打开报告概览
start report.html
```

## 常见问题

### Q1: 应用启动失败
**症状**: 测试提示找不到main_window.png

**解决方案**:
- 确认应用路径正确
- 确认应用能正常启动
- 检查main_window.png是否在正确位置
- 尝试手动启动应用，看是否有错误

### Q2: 图像识别失败
**症状**: "FindFailed: can not find main_window.png"

**解决方案**:
- 重新截取main_window.png（确保应用在前台）
- 确保截图包含足够的独特特征
- 检查屏幕分辨率和DPI设置是否一致
- 增加等待时间：修改 `Wait Until Screen Contain main_window.png 30` 中的30为更大值

### Q3: 测试运行缓慢
**解决方案**:
- 这是正常的，图像识别需要时间
- 第一次运行SikuliX会慢一些
- 后续运行会快一些

## 下一步扩展

### 添加更多UI元素截图

继续截取更多UI元素：

```
examples/robot_resources/
├── main_window.png              ✓ 已有
├── new_button.png               # 新建按钮
├── save_button.png              # 保存按钮
├── rectangle_tool.png           # 矩形工具
├── circle_tool.png              # 圆形工具
├── line_tool.png                # 连线工具
└── ...
```

### 创建更复杂的测试

参考 `examples/robot_framework_examples.json` 创建更复杂的测试用例：
- 创建节点
- 连接节点
- 保存文件
- 拖拽操作
- 等等

### 示例：添加节点测试

```robot
测试3-添加矩形节点
    [Documentation]    测试在画布上添加矩形节点
    [Tags]    功能测试
    
    启动DiagramScene应用
    
    # 点击矩形工具
    Click    rectangle_tool.png
    Sleep    0.5s
    
    # 在画布上点击放置节点
    Click    400    300
    Sleep    1s
    
    # 截图验证
    Capture Screen    screenshots/node_added.png
    
    关闭DiagramScene应用
```

## 技巧提示

1. **截图时机**: 在应用窗口最大化、在前台时截图
2. **截图区域**: 只截取需要的部分，不要截取整个屏幕
3. **命名规范**: 使用描述性的文件名，如 `toolbar_rectangle_button.png`
4. **调试方法**: 使用 `Capture Screen` 在每个步骤后截图，便于查看执行过程
5. **等待时间**: 如果操作不稳定，增加 `Sleep` 时间

## 参考资源

- 详细指南: `backend/ROBOT_FRAMEWORK_GUIDE.md`
- 示例代码: `backend/examples/robot_framework_examples.json`
- 快速开始: `ROBOT_FRAMEWORK_QUICKSTART.md`

祝测试顺利！🚀

