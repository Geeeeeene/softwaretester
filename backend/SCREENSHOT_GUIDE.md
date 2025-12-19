# 正确截图指南

## 问题诊断

如果测试一直失败，很可能是因为截图太大或包含了易变的内容。

## ✅ 正确的截图方法

### 推荐选项1：只截取窗口标题栏的小部分

**最佳选择** - 标题栏通常最稳定

**大小**：约 200x50 像素
**位置**：窗口左上角，包含应用图标和标题文字

**步骤**：
1. 启动应用：`C:\Users\lenovo\Desktop\FreeCharts\diagramscene.exe`
2. 按 `Win + Shift + S`
3. **只截取**窗口标题栏的左侧部分（图标+标题文字）
4. 截图应该类似这样：
   ```
   ┌─────────────────────┐
   │ [图标] DiagramScene │  ← 只要这一小部分
   └─────────────────────┘
   ```
5. 保存为：`examples\robot_resources\main_window.png`

### 推荐选项2：截取工具栏的某个独特按钮

**大小**：约 64x64 像素
**选择**：一个颜色鲜明、形状独特的工具栏按钮

### 推荐选项3：截取左上角的一小块区域

**大小**：约 300x200 像素
**位置**：窗口左上角，包含标题栏+部分菜单栏

## ❌ 避免的做法

- ❌ 不要截取整个窗口
- ❌ 不要截取包含文本内容的大区域（文本渲染可能不同）
- ❌ 不要包含动画、鼠标光标
- ❌ 不要包含会变化的内容（状态文字、时间等）

## 🔍 检查截图尺寸

运行这个PowerShell命令检查图像大小：

```powershell
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile("examples\robot_resources\main_window.png")
Write-Host "图像尺寸: $($img.Width) x $($img.Height) 像素"
$img.Dispose()
```

**理想尺寸**：
- ✅ 100-300 像素宽
- ✅ 50-200 像素高
- ❌ 超过 800 像素任何一边都可能导致问题

## 🎯 测试流程

1. 截取新图像
2. 检查尺寸
3. 运行测试
4. 如果失败，查看 `sikuli_captured` 目录中的截图对比
5. 重复直到找到稳定的匹配区域

## 💡 高级技巧

如果应用窗口在不同启动时外观会变化，可以：

1. **截取多个目标图像**，轮流尝试：
   ```robot
   Set Min Similarity    0.5
   ${found1}=    Exists    main_window1.png    timeout=5
   ${found2}=    Exists    main_window2.png    timeout=5
   ${found}=    Evaluate    ${found1} or ${found2}
   ```

2. **使用文本识别代替图像匹配**（如果SikuliX支持OCR）

3. **降低相似度到 0.3-0.4**（但可能误匹配）

## 🚀 快速成功的秘诀

**截取窗口图标**（通常 32x32 像素）+ 一小段标题文字

这是最稳定的方法，因为：
- ✅ 图标通常不变
- ✅ 应用标题通常固定
- ✅ 小区域匹配快且准确
- ✅ 受DPI缩放影响小



