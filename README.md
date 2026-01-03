# HomemadeTester - 智能统一测试平台

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18.2-blue.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104-green.svg)](https://fastapi.tiangolo.com/)

HomemadeTester 是一个基于 **Test IR（测试中间表示）** 的智能统一测试平台，通过标准化的测试描述格式和 AI 驱动的测试生成，整合多种测试工具和执行器，提供一站式的测试管理和执行解决方案。

## 🎯 核心设计理念

### 1. 统一测试接口（Test IR）

通过 **Test IR（测试中间表示）** 抽象层，将不同测试类型（系统、单元、集成、静态分析）统一为 JSON/YAML 格式的描述，实现：

- **工具无关性**：测试用例与具体执行工具解耦
- **可移植性**：测试用例可在不同工具间迁移
- **可扩展性**：新增测试类型只需定义新的 IR Schema

### 2. 分层架构设计

```
┌─────────────────────────────────────────┐
│          Web UI (React)                 │
│  - 项目管理                              │
│  - 用例编辑（AI辅助）                     │
│  - 执行监控                              │
│  - 结果可视化                            │
└────────────┬────────────────────────────┘
             │ HTTP/WebSocket
┌────────────▼────────────────────────────┐
│     Backend API (FastAPI)               │
│  - REST API                             │
│  - Test IR 验证                         │
│  - AI 服务集成                          │
└────────────┬────────────────────────────┘
             │
     ┌───────┴───────┐
     ▼               ▼
┌─────────┐    ┌──────────────┐
│ Database│    │ Task Queue   │
│(Postgres│    │  (Redis+RQ)  │
│    )    │    └──────┬───────┘
└─────────┘           │
                      ▼
            ┌──────────────────┐
            │   Worker Pool    │
            │  - 任务调度       │
            │  - 并发控制       │
            └────────┬─────────┘
                     │
                     ▼
         ┌─────────────────────┐
         │   Executor Layer    │
         │ - System Executor   │
         │ - Unit Executor     │
         │ - Static Executor   │
         └─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Artifact Storage    │
│ - Logs              │
│ - Screenshots       │
│ - Coverage Reports  │
└─────────────────────┘
```

### 3. AI 驱动的测试智能化

- **系统测试**：根据自然语言描述，AI 自动生成 Robot Framework + SikuliLibrary 测试脚本
- **单元测试**：基于源代码分析，AI 自动生成 Catch2 测试用例
- **集成测试**：AI 生成测试代码并支持模拟执行
- **静态分析**：AI 辅助深度代码分析和问题定位

## 🏗️ 系统架构

### 后端架构

**技术栈**：
- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15（关系数据）
- **队列**: Redis 7 + RQ（异步任务）
- **ORM**: SQLAlchemy 2.0
- **验证**: Pydantic 2.5
- **AI**: Claude API（测试生成）

**核心模块**：

1. **Test IR 层** (`app/test_ir/`)
   - 定义统一的测试描述格式
   - 支持多种测试类型的 IR Schema
   - 提供验证和转换功能

2. **执行器适配层** (`app/executors/`)
   - 策略模式 + 工厂模式
   - 统一的执行器接口（BaseExecutor）
   - 支持多种测试工具（Robot Framework、Catch2、Cppcheck 等）

3. **AI 服务层** (`app/services/`, `app/system_tests/`)
   - 系统测试 AI 生成器（Robot Framework 脚本生成）
   - 单元测试 AI 生成器（Catch2 测试生成）
   - 集成测试 AI 生成器（测试代码生成和模拟执行）

4. **任务队列** (`app/worker/`)
   - 基于 Redis Queue 的异步任务处理
   - 支持多 Worker 并发执行
   - 任务状态实时更新

### 前端架构

**技术栈**：
- **框架**: React 18 + TypeScript
- **构建**: Vite 5
- **路由**: React Router 6
- **状态**: TanStack Query（服务器状态）
- **样式**: TailwindCSS + shadcn/ui
- **HTTP**: Axios

**核心特性**：
- 组件化设计，可复用性强
- 实时状态同步（轮询 + WebSocket）
- 响应式布局，支持多设备访问

### 数据存储

**PostgreSQL**：
- 项目、测试用例、执行记录等关系数据
- Test IR 以 JSONB 格式存储，支持灵活查询

**文件系统**：
- 测试执行日志
- 截图和覆盖率报告
- 生成的测试代码

## 🚀 快速开始

### 前提条件

- Docker Desktop 或 Docker Engine + Docker Compose
- 至少 4GB 可用内存
- （系统测试需要）Windows 系统 + Python 3.10+ + Java JDK

### Docker Compose 启动

1. **克隆仓库并进入目录**
```bash
git clone https://github.com/Geeeeeene/softwaretester.git
cd softwaretester
```

2. **启动所有服务**
```bash
docker-compose up -d
```

这将启动以下服务：
- PostgreSQL (端口 5432)
- Redis (端口 6379)
- Backend API (端口 8000)
- Worker进程（Docker 容器内）
- Frontend (端口 5173)

3. **查看服务状态**
```bash
docker-compose ps
```

4. **访问应用**
- 前端: http://localhost:5173
- API文档: http://localhost:8000/docs

5. **查看日志**
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f worker
```

6. **停止服务**
```bash
docker-compose down

# 同时删除数据卷（会删除所有数据）
docker-compose down -v
```

### Windows Worker 启动（系统测试必需）

系统测试需要在 Windows 主机上执行，因为需要访问 Windows 应用程序和运行 Robot Framework。

#### 为什么需要 Windows Worker？

- 需要访问 Windows 应用程序（.exe 文件）
- 需要 Java 环境运行 SikuliLibrary
- 需要系统 Python 运行 Robot Framework

#### 启动步骤

**方法1：使用 PowerShell（推荐）**

1. **打开新的 PowerShell 窗口**

2. **进入后端目录**
```powershell
cd backend
```

3. **设置环境变量**
```powershell
# Redis连接地址（如果使用Docker，通常是localhost:6379）
$env:REDIS_URL="redis://localhost:6379/0"

# 指定监听windows_ui队列
$env:RQ_QUEUES="windows_ui"

# 数据库连接（必须与后端API使用同一个数据库）
$env:DATABASE_URL="postgresql://tester:tester123@localhost:5432/homemade_tester"
```

4. **启动 Worker**
```powershell
python -m app.worker.worker
```

5. **验证启动成功**
看到以下输出表示启动成功：
```
📋 从环境变量读取队列配置: RQ_QUEUES=windows_ui
🚀 Worker启动成功（Windows模式），监听队列: ['windows_ui']
*** Listening on windows_ui...
```

**方法2：使用启动脚本**

如果项目中有 `backend/start_worker.ps1` 脚本，直接运行：
```powershell
.\backend\start_worker.ps1
```

#### 环境要求

- Python 3.10+（系统 Python，用于运行 Robot Framework）
- Java JDK（SikuliLibrary 需要）
- Robot Framework 已安装：`py -m pip install robotframework robotframework-sikulilibrary`

#### 验证 Worker 是否正常工作

1. **检查 Worker 日志**：启动后应该看到 "Listening on windows_ui..."
2. **执行一个测试**：在前端创建系统测试并执行，Worker 控制台应该显示任务处理信息
3. **检查队列状态**：确保 Worker 正在监听 `windows_ui` 队列

#### Worker 常见问题

**Q1: Worker 无法连接到 Redis**
- 检查 Redis 是否运行：`docker ps | grep redis`
- 确保 Redis 容器已启动

**Q2: Worker 无法连接到数据库**
- 确保设置了正确的 `DATABASE_URL`
- 如果后端使用 PostgreSQL，Worker 也必须使用 PostgreSQL
- 检查数据库连接字符串格式

**Q3: Worker 启动后立即退出**
- 检查 Python 版本：`python --version`（应该是 3.10+）
- 安装依赖：`pip install -r requirements.txt`
- 检查错误日志

**注意**：Worker 窗口必须保持打开状态，关闭窗口会停止 Worker。

### 验证安装

1. **检查服务状态**
```bash
docker-compose ps
```
所有服务应该显示为 "Up" 状态

2. **检查后端 API**
访问 http://localhost:8000/health 应该返回：
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

3. **检查前端**
访问 http://localhost:5173 应该看到主页

4. **测试创建项目**
- 访问"项目管理"页面
- 点击"创建项目"
- 填写项目信息并提交
- 查看项目列表

### 常见问题

**Q1: Docker 容器无法启动**
- 检查端口是否被占用，特别是 5432 (PostgreSQL), 6379 (Redis), 8000 (API), 5173 (Frontend)
- 停止占用端口的程序，或修改 `docker-compose.yml` 中的端口映射

**Q2: Docker Desktop 未运行**
- 打开 Docker Desktop
- 等待 Docker 完全启动（系统托盘图标显示运行中）
- 检查 Docker 状态：`docker info`

**Q3: 前端无法连接后端**
- 检查 Docker 容器是否正常运行：`docker-compose ps`
- 确保 backend 和 frontend 服务都已启动
- 查看日志：`docker-compose logs frontend backend`

**Q4: 数据库连接失败**
- 确保 PostgreSQL 容器已启动并健康：`docker-compose ps postgres`
- 等待 PostgreSQL 容器完全启动（健康检查通过）
- 查看日志：`docker-compose logs postgres`

**Q5: Worker 无法处理任务**
- 检查 Redis 和 Worker 服务是否运行：`docker-compose ps redis worker`
- 确保 Redis 容器已启动
- 查看 Worker 日志：`docker-compose logs worker`

### 管理命令

```bash
# 重启服务
docker-compose restart

# 重建并启动
docker-compose up -d --build

# 清理所有数据（谨慎使用）
docker-compose down -v
```

## 📖 文档

- [测试方案文档](TESTING_STRATEGY.md) - 整体测试思路和智能化实现方案

## 🔧 扩展性设计

### 添加新执行器

1. 在 `backend/app/executors/` 创建新适配器
2. 继承 `BaseExecutor` 基类
3. 实现 `execute()` 和 `validate_ir()` 方法
4. 在 `ExecutorFactory` 注册执行器

### 添加新测试类型

1. 在 `backend/app/test_ir/schemas.py` 定义新 IR Schema
2. 创建对应执行器
3. 更新前端类型定义
4. 添加编辑器模板

### 集成新的 AI 能力

1. 在 `backend/app/services/` 创建 AI 服务类
2. 实现测试生成接口
3. 在对应的 API 端点中集成

## 🔒 安全特性

- JWT Token 认证
- RBAC 角色权限控制
- SQL 注入防护（ORM 参数化）
- XSS 防护（React 自动转义）
- HTTPS 传输加密（生产环境）

## 📊 性能优化

- 数据库索引优化
- Redis 缓存策略
- 异步任务处理
- 前端代码分割和懒加载
- 虚拟滚动（长列表）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

⭐ 如果这个项目对你有帮助，请给个 Star！
