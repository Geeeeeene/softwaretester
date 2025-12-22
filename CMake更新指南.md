# CMake 版本更新指南

## 当前问题

系统当前安装的是 **CMake 4.2.1**，这是一个非常新的版本，可能与 Qt6 和 MinGW 存在兼容性问题，导致访问冲突错误（0xC0000005）。

## 推荐版本

对于 Qt 6.10.1 和 MinGW，推荐使用 **CMake 3.16 到 3.28** 之间的稳定版本：

- **最佳选择**: CMake 3.28.x（最新稳定 3.x 版本）
- **备选**: CMake 3.27.x 或 3.26.x
- **最低要求**: CMake 3.16.0

## 更新方法

### 方法 1: 使用 CMake 官方安装程序（推荐）

1. **下载 CMake 3.28.x**
   - 访问：https://cmake.org/download/
   - 选择 "Windows x64 Installer" (cmake-3.28.x-windows-x86_64.msi)
   - 或直接下载：https://github.com/Kitware/CMake/releases/download/v3.28.7/cmake-3.28.7-windows-x86_64.msi

2. **安装步骤**
   - 运行安装程序
   - 选择 "Add CMake to the system PATH for all users" 或 "Add CMake to the system PATH for current user"
   - 完成安装

3. **验证安装**
   ```powershell
   cmake --version
   ```
   应该显示 `cmake version 3.28.x`

### 方法 2: 使用包管理器（如果已安装）

#### 使用 Chocolatey
```powershell
choco uninstall cmake
choco install cmake --version=3.28.7
```

#### 使用 Scoop
```powershell
scoop uninstall cmake
scoop install cmake@3.28.7
```

### 方法 3: 手动安装（便携版）

1. **下载便携版**
   - 访问：https://cmake.org/download/
   - 下载 "Windows x64 ZIP" (cmake-3.28.x-windows-x86_64.zip)

2. **解压到目录**
   - 解压到 `C:\Program Files\CMake` 或自定义目录

3. **更新 PATH**
   - 打开"系统属性" → "环境变量"
   - 编辑"Path"变量，添加 CMake 的 bin 目录（如 `C:\Program Files\CMake\bin`）

## 卸载旧版本

在安装新版本之前，建议先卸载 CMake 4.2.1：

1. **通过控制面板卸载**
   - 打开"设置" → "应用" → "应用和功能"
   - 搜索 "CMake"
   - 点击"卸载"

2. **或使用命令行**
   ```powershell
   # 如果使用 Chocolatey
   choco uninstall cmake
   
   # 如果使用 Scoop
   scoop uninstall cmake
   ```

## 验证更新

更新后，运行以下命令验证：

```powershell
cmake --version
```

应该显示类似：
```
cmake version 3.28.7

CMake suite maintained and supported by Kitware (kitware.com/cmake).
```

## 如果问题仍然存在

如果降级到 CMake 3.28 后问题仍然存在，请检查：

1. **Qt 路径是否正确**
   - 确认 `D:/Qt/6.10.1/mingw_64` 存在
   - 确认该目录包含 `lib/cmake/Qt6` 文件夹

2. **编译器路径是否正确**
   - 确认 `D:/Qt/Tools/mingw1310_64/bin/mingw32-make.exe` 存在
   - 确认 `D:/Qt/Tools/mingw1310_64/bin/g++.exe` 存在

3. **环境变量**
   - 确认 PATH 中包含 CMake 的 bin 目录
   - 确认 PATH 中包含 MinGW 的 bin 目录

4. **权限问题**
   - 确保有权限访问临时目录和工作目录
   - 尝试以管理员身份运行

## 版本兼容性参考

| CMake 版本 | Qt 6.10.1 | MinGW | 推荐度 |
|-----------|-----------|-------|--------|
| 3.16-3.20 | ✅ 支持 | ✅ 支持 | ⭐⭐⭐ |
| 3.21-3.25 | ✅ 支持 | ✅ 支持 | ⭐⭐⭐⭐ |
| 3.26-3.28 | ✅ 支持 | ✅ 支持 | ⭐⭐⭐⭐⭐ |
| 4.0+ | ⚠️ 可能有问题 | ⚠️ 可能有问题 | ❌ 不推荐 |

## 注意事项

- CMake 4.x 是主要版本更新，可能存在向后兼容性问题
- 对于生产环境，建议使用经过充分测试的 3.x 版本
- 如果必须使用 CMake 4.x，请确保所有依赖（Qt、编译器）都是最新版本

