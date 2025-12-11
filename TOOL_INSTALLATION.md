# 工具安装说明

## 问题说明

如果你看到执行结果显示：
- **通过: 0**
- **失败: 0** 
- **跳过: 1**

这通常意味着**静态分析工具（Clazy 或 Cppcheck）没有安装**。

## 解决方案

### 选项 1: 安装工具（推荐用于生产环境）

#### 安装 Cppcheck

**Windows:**
```powershell
# 使用 Chocolatey
choco install cppcheck

# 或下载安装包
# https://github.com/danmar/cppcheck/releases
```

**Linux:**
```bash
sudo apt-get install cppcheck
# 或
sudo yum install cppcheck
```

**macOS:**
```bash
brew install cppcheck
```

#### 安装 Clazy

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install clazy
```

**macOS:**
```bash
brew install clazy
```

**Windows:**
Clazy 主要支持 Linux/macOS，Windows 上需要从源码编译。

### 选项 2: 使用模拟模式（用于演示）

如果你只是想验证系统功能，而不需要实际运行静态分析，可以：

1. **修改执行器**，在工具不可用时返回模拟结果
2. **或者**，创建一个测试模式，跳过工具检查

## 验证工具是否安装

在容器中检查：

```bash
# 检查 Cppcheck
docker-compose exec backend cppcheck --version

# 检查 Clazy
docker-compose exec backend clazy-standalone --version
```

## 当前状态

从日志可以看到：
```
⚠️  警告: Cppcheck 不可用，请确保已安装并配置到 PATH
⚠️  警告: Clazy 不可用，请确保已安装并配置到 PATH
```

## 修复后的行为

修复后，如果工具不可用：
- **状态**: `COMPLETED`
- **通过**: `0`
- **失败**: `1` （而不是跳过）
- **错误信息**: "Cppcheck executable not found..." 或 "Clazy executable not found..."

这样更清楚地表明测试失败是因为工具未安装，而不是测试被跳过。

## 下一步

1. **安装工具**（如果需要在生产环境使用）
2. **或者**，接受当前状态（用于演示系统功能）

系统已经正确集成了 Clazy 和 Cppcheck，只是需要安装实际的工具才能执行分析。

