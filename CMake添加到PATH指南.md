# 将 CMake 添加到系统 PATH 指南

## 方法 1: 通过 CMake 安装程序（推荐）

### 步骤：
1. **重新运行 CMake 安装程序**
   - 如果已安装，可以重新运行安装程序
   - 下载地址：https://cmake.org/download/

2. **在安装过程中选择**
   - 选择 "Add CMake to the system PATH for all users"（为所有用户添加）
   - 或选择 "Add CMake to the system PATH for current user"（为当前用户添加）

3. **完成安装**
   - 安装完成后，重启命令行窗口或重新登录

## 方法 2: 手动添加到 PATH（Windows）

### 步骤：

#### 1. 找到 CMake 安装路径
通常 CMake 安装在以下位置之一：
- `C:\Program Files\CMake\bin`
- `C:\Program Files (x86)\CMake\bin`
- `C:\CMake\bin`

#### 2. 添加到系统 PATH

**方法 A: 通过图形界面（推荐）**

1. **打开系统属性**
   - 按 `Win + R`，输入 `sysdm.cpl`，按回车
   - 或右键"此电脑" → "属性" → "高级系统设置"

2. **打开环境变量设置**
   - 点击"环境变量"按钮

3. **编辑 PATH**
   - 在"系统变量"（或"用户变量"）中找到 `Path`
   - 点击"编辑"

4. **添加 CMake 路径**
   - 点击"新建"
   - 输入 CMake 的 bin 目录路径，例如：`C:\Program Files\CMake\bin`
   - 点击"确定"保存

5. **应用更改**
   - 依次点击"确定"关闭所有对话框
   - **重要**：关闭并重新打开所有命令行窗口（CMD、PowerShell、终端等）

**方法 B: 通过 PowerShell（管理员权限）**

```powershell
# 以管理员身份运行 PowerShell，然后执行：

# 获取当前 PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")

# 添加 CMake 路径（如果还没有）
$cmakePath = "C:\Program Files\CMake\bin"
if ($currentPath -notlike "*$cmakePath*") {
    $newPath = $currentPath + ";" + $cmakePath
    [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
    Write-Host "CMake 已添加到系统 PATH"
} else {
    Write-Host "CMake 已在 PATH 中"
}
```

**方法 C: 通过命令提示符（管理员权限）**

```cmd
# 以管理员身份运行 CMD，然后执行：

# 添加到系统 PATH（永久）
setx /M PATH "%PATH%;C:\Program Files\CMake\bin"

# 注意：setx 不会立即生效，需要重新打开命令行窗口
```

#### 3. 验证安装

重新打开命令行窗口（CMD 或 PowerShell），运行：

```cmd
cmake --version
```

应该显示 CMake 版本信息。

## 方法 3: 临时添加到当前会话 PATH

如果只是临时使用，可以在当前命令行窗口中运行：

**CMD:**
```cmd
set PATH=%PATH%;C:\Program Files\CMake\bin
```

**PowerShell:**
```powershell
$env:PATH += ";C:\Program Files\CMake\bin"
```

**注意**：这种方法只在当前命令行窗口有效，关闭窗口后失效。

## 常见问题

### 1. 找不到 CMake 安装路径

运行以下命令查找：

**PowerShell:**
```powershell
Get-ChildItem -Path "C:\Program Files" -Filter "cmake.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object FullName
```

**CMD:**
```cmd
dir /s /b "C:\Program Files\cmake.exe"
```

### 2. 添加后仍然找不到

- **确保路径正确**：检查 CMake 的 bin 目录是否真的存在
- **重启命令行**：添加 PATH 后必须关闭并重新打开命令行窗口
- **检查权限**：确保有管理员权限（如果添加到系统 PATH）
- **检查路径格式**：确保路径中没有多余的空格或引号

### 3. 多个 CMake 版本

如果系统中有多个 CMake 安装，PATH 中靠前的路径会优先使用。可以通过以下命令查看：

```cmd
where cmake
```

这会显示 PATH 中找到的第一个 cmake.exe 的路径。

## 验证步骤

1. **检查 PATH 中是否包含 CMake**
   ```cmd
   echo %PATH% | findstr /i cmake
   ```

2. **检查 CMake 版本**
   ```cmd
   cmake --version
   ```

3. **检查 CMake 路径**
   ```cmd
   where cmake
   ```

## 推荐做法

1. **使用安装程序添加**：最简单可靠的方法
2. **添加到系统 PATH**：所有用户都可以使用
3. **添加到用户 PATH**：仅当前用户可以使用（如果无管理员权限）

