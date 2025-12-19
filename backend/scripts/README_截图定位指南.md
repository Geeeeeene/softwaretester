# Sikuli 元素截图和坐标定位指南

## 方法一：使用 Robot Framework 截图（推荐）

### 步骤 1: 运行截图脚本

```powershell
cd backend
py -m robot scripts/capture_and_find_element.robot
```

这个脚本会：
1. 启动应用
2. 截图整个屏幕
3. 等待你手动操作（点击图元等）
4. 再次截图
5. 保存截图到 `sikuli_captured/` 目录

### 步骤 2: 查看截图并找到坐标

1. 打开 `sikuli_captured/` 目录，找到最新的截图文件（通常是 `sikuliximage-*.png`）
2. 使用 Windows 画图工具打开截图
3. 将鼠标移动到目标元素上，左下角会显示坐标（例如：`(150, 200)`）
4. 记录目标元素的：
   - 左上角坐标 (x, y)
   - 宽度 (width)
   - 高度 (height)

### 步骤 3: 裁剪元素图像

运行裁剪脚本：

```powershell
py scripts/create_element_image.py
```

按提示输入：
- 元素左上角 X 坐标
- 元素左上角 Y 坐标
- 元素宽度
- 元素高度
- 元素名称（例如：`rectangle_element`）

脚本会自动裁剪并保存到 `examples/robot_resources/` 目录。

## 方法二：使用 SikuliX IDE（如果已安装）

### 步骤 1: 启动 SikuliX IDE

1. 下载 SikuliX IDE: https://sikulix.github.io/
2. 启动 SikuliX IDE

### 步骤 2: 截图和定位

1. 在 SikuliX IDE 中，点击 "Capture" 按钮
2. 选择要截图的区域（例如：左侧图元集中的图元）
3. 保存图像到 `examples/robot_resources/` 目录

### 步骤 3: 获取坐标

在 SikuliX IDE 中：
- 将鼠标移动到目标位置
- 查看状态栏显示的坐标
- 或者使用 `Region` 对象获取坐标

## 方法三：使用 Python 脚本（需要 sikulix4python）

### 安装依赖

```powershell
pip install sikulix4python
```

### 运行脚本

```powershell
py scripts/find_element_coordinates.py
```

脚本会：
1. 启动应用
2. 截图
3. 提示你操作应用
4. 获取鼠标位置坐标
5. 在鼠标位置周围截图

## 实际示例：创建第二个测试用例

### 测试场景
1. 启动应用
2. 点击左侧图元集的一个图元（例如：矩形图元）
3. 在右侧空白区域点击一下，创建这种图元

### 步骤

#### 1. 截图左侧图元集中的图元

```powershell
# 运行截图脚本
py -m robot scripts/capture_and_find_element.robot
```

在等待期间：
- 应用启动后，找到左侧图元集中的矩形图元
- 将鼠标移动到矩形图元上
- 等待脚本完成

#### 2. 找到矩形图元的坐标

1. 打开 `sikuli_captured/` 目录中的最新截图
2. 使用画图工具，找到矩形图元的位置
3. 记录坐标（例如：`x=50, y=150, width=80, height=80`）

#### 3. 裁剪矩形图元图像

```powershell
py scripts/create_element_image.py
```

输入：
- X: 50
- Y: 150
- Width: 80
- Height: 80
- 名称: rectangle_element

#### 4. 截图右侧空白区域（用于点击创建图元）

重复步骤 1-3，但这次：
- 在右侧空白区域点击一下（创建图元后）
- 找到创建出的图元的位置
- 裁剪出创建出的图元图像（例如：`created_rectangle.png`）

#### 5. 编写测试脚本

在 `test_diagramscene.robot` 中添加新的测试用例：

```robot
*** Test Cases ***
测试2-创建矩形图元
    [Documentation]    点击左侧图元集的矩形图元，然后在右侧空白区域点击创建图元
    
    # 启动应用
    Start Process    ${APP_PATH}    alias=app
    Sleep    5s
    
    # 设置图像路径
    Add Image Path    ${IMAGE_PATH}
    Set Min Similarity    0.7
    
    # 等待主窗口显示
    Wait Until Screen Contain    main_window.png    30
    
    # 点击左侧图元集中的矩形图元
    Click    rectangle_element.png
    
    # 等待一下
    Sleep    1s
    
    # 在右侧空白区域点击（创建图元）
    # 注意：这里需要根据实际应用确定点击位置
    # 可以使用坐标点击：Click    Region(500, 300, 100, 100)
    Click    Region(500, 300)  # 右侧空白区域的坐标
    
    # 等待图元创建
    Sleep    2s
    
    # 验证图元已创建（检查创建出的图元是否存在）
    ${exists} =    Exists    created_rectangle.png    timeout=5
    Should Be True    ${exists}    图元未成功创建
    
    # 截图记录
    Capture Screen
    
    # 清理
    Terminate Process    app    kill=True
    Stop Remote Server
```

## 提示和技巧

### 1. 如何确定点击坐标？

- **方法1**: 使用画图工具查看坐标
- **方法2**: 使用 Robot Framework 的 `Get Mouse Location` 关键字
- **方法3**: 使用 SikuliX IDE 的坐标显示功能

### 2. 如何提高图像识别准确度？

- 裁剪出足够大的区域（包含足够的特征）
- 避免包含会变化的内容（如时间、动态元素）
- 使用合适的相似度阈值（0.7-0.9）

### 3. 如何处理动态内容？

- 使用相对坐标而不是绝对坐标
- 使用图像识别而不是坐标点击
- 等待元素出现后再操作

### 4. 调试技巧

- 使用 `Capture Screen` 记录每个步骤的截图
- 使用 `Log` 输出坐标信息
- 使用 `Set Min Similarity` 调整相似度阈值

## 常见问题

### Q: 截图后找不到元素？

A: 
1. 检查截图是否正确（应用是否完全加载）
2. 检查坐标是否在截图范围内
3. 尝试裁剪更大的区域（包含更多上下文）

### Q: 图像识别失败？

A:
1. 降低相似度阈值（例如：从 0.8 降到 0.7）
2. 重新截图（确保截图时应用状态一致）
3. 检查图像路径是否正确

### Q: 坐标点击不准确？

A:
1. 使用图像识别代替坐标点击
2. 或者使用相对坐标（相对于窗口位置）
3. 考虑 DPI 缩放问题

