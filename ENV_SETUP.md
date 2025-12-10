# 环境配置指南

本文档说明如何配置 HomemadeTester 项目的运行环境。

## 📋 目录

- [快速开始](#快速开始)
- [方式一：Docker Compose（推荐）](#方式一docker-compose推荐)
- [方式二：本地开发环境](#方式二本地开发环境)
- [环境变量说明](#环境变量说明)
- [常见问题](#常见问题)

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

**最简单的方式，适合快速体验和开发**

1. **确保已安装 Docker Desktop**
   - Windows: 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
   - 确保 Docker Desktop 正在运行

2. **使用启动脚本**
   ```powershell
   # Windows
   .\start.bat
   
   # Linux/Mac
   ./start.sh
   ```

   或者手动启动：
   ```bash
   docker compose up -d
   ```

3. **访问应用**
   - 前端: http://localhost:5173
   - API文档: http://localhost:8000/docs
   - Neo4j浏览器: http://localhost:7474

**注意**：Docker Compose 方式会自动配置所有环境变量，无需手动配置。

---

### 方式二：本地开发环境

适合需要修改代码或调试的场景。

#### 前提条件

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+（可选，默认使用 SQLite）
- Redis 6+（可选，用于任务队列）

#### 步骤 1: 配置后端环境

1. **进入后端目录**
   ```bash
   cd backend
   ```

2. **创建虚拟环境**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   # Windows
   copy .env.example .env
   
   # Linux/Mac
   cp .env.example .env
   ```

5. **编辑 `.env` 文件**（可选）
   - 默认配置已适合开发环境
   - 如需使用 PostgreSQL，修改 `DATABASE_URL`
   - 如需使用远程 Redis，修改 `REDIS_URL`

6. **初始化数据库**
   ```bash
   python scripts/init_db.py
   ```

7. **启动后端服务**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

8. **启动 Worker 进程**（新终端）
   ```bash
   cd backend
   venv\Scripts\activate  # 或 source venv/bin/activate
   python -m app.worker.worker
   ```

#### 步骤 2: 配置前端环境

1. **进入前端目录**
   ```bash
   cd frontend
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **配置环境变量**
   ```bash
   # Windows
   copy .env.example .env
   
   # Linux/Mac
   cp .env.example .env
   ```

4. **编辑 `.env` 文件**（可选）
   - 默认 `VITE_API_BASE_URL=http://localhost:8000` 已适合本地开发
   - 如果后端运行在不同端口，修改此值

5. **启动开发服务器**
   ```bash
   npm run dev
   ```

6. **访问前端**
   - 打开浏览器访问: http://localhost:5173

---

## 📝 环境变量说明

### 后端环境变量（`backend/.env`）

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./homemade_tester.db` | ✅ |
| `REDIS_URL` | Redis 连接字符串 | `redis://localhost:6379/0` | ⚠️ |
| `NEO4J_URI` | Neo4j 连接 URI | `bolt://localhost:7687` | ❌ |
| `NEO4J_USER` | Neo4j 用户名 | `neo4j` | ❌ |
| `NEO4J_PASSWORD` | Neo4j 密码 | `testpassword` | ❌ |
| `SECRET_KEY` | JWT 密钥 | `dev-secret-key-change-in-production` | ✅ |
| `ARTIFACT_STORAGE_PATH` | 文件存储路径 | `./artifacts` | ✅ |
| `BACKEND_CORS_ORIGINS` | 允许的 CORS 源 | `http://localhost:5173,http://localhost:3000` | ✅ |

**数据库选择：**

- **SQLite（默认）**：无需安装，适合开发
  ```
  DATABASE_URL=sqlite:///./homemade_tester.db
  ```

- **PostgreSQL（生产推荐）**：需要安装 PostgreSQL
  ```
  DATABASE_URL=postgresql://用户名:密码@localhost:5432/数据库名
  ```

### 前端环境变量（`frontend/.env`）

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `VITE_API_BASE_URL` | 后端 API 地址 | `http://localhost:8000` | ✅ |
| `VITE_WS_URL` | WebSocket 地址 | `ws://localhost:8000/ws` | ❌ |

**注意**：Vite 要求环境变量必须以 `VITE_` 开头才能在前端代码中访问。

---

## 🔧 常见问题

### Q1: 如何检查环境配置是否正确？

**后端检查：**
```bash
# 访问健康检查端点
curl http://localhost:8000/health

# 应该返回：
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected"
# }
```

**前端检查：**
- 打开浏览器控制台，查看是否有 API 连接错误
- 访问 http://localhost:5173，应该能看到主页

### Q2: 数据库连接失败怎么办？

**SQLite：**
- 确保 `backend` 目录有写入权限
- 检查 `DATABASE_URL` 路径是否正确

**PostgreSQL：**
- 确保 PostgreSQL 服务正在运行
- 检查用户名、密码、数据库名是否正确
- 检查端口是否为 5432
- 测试连接：
  ```bash
  psql -h localhost -U tester -d homemade_tester
  ```

### Q3: Redis 连接失败怎么办？

- 确保 Redis 服务正在运行
- 检查端口是否为 6379
- 测试连接：
  ```bash
  redis-cli ping
  # 应该返回: PONG
  ```

### Q4: 前端无法连接后端？

1. **检查后端是否运行**
   ```bash
   curl http://localhost:8000/health
   ```

2. **检查 CORS 配置**
   - 确保 `BACKEND_CORS_ORIGINS` 包含前端地址
   - 默认已包含 `http://localhost:5173`

3. **检查 `VITE_API_BASE_URL`**
   - 确保与后端实际地址一致

### Q5: Docker 容器无法启动？

1. **检查端口占用**
   ```powershell
   # Windows
   netstat -ano | findstr "8000"
   netstat -ano | findstr "5173"
   ```

2. **查看容器日志**
   ```bash
   docker compose logs backend
   docker compose logs frontend
   ```

3. **重启容器**
   ```bash
   docker compose down
   docker compose up -d
   ```

### Q6: 如何重置环境？

**Docker 方式：**
```bash
# 停止并删除所有容器和数据卷
docker compose down -v

# 重新启动
docker compose up -d
```

**本地方式：**
```bash
# 删除数据库文件（SQLite）
rm backend/homemade_tester.db

# 重新初始化
cd backend
python scripts/init_db.py
```

---

## 📚 下一步

配置完成后，您可以：

1. 📖 阅读 [README.md](README.md) 了解项目功能
2. 🔍 浏览 API 文档：http://localhost:8000/docs
3. 🧪 创建第一个测试项目
4. 📝 编写 Test IR 格式的测试用例
5. ▶️ 运行测试并查看结果

---

## 💡 提示

- **开发环境**：使用 SQLite + 默认配置即可快速开始
- **生产环境**：务必使用 PostgreSQL，并修改 `SECRET_KEY`
- **Docker 方式**：最简单，推荐新手使用
- **本地方式**：适合需要调试和修改代码的场景

如有问题，请查看 [QUICK_START.md](QUICK_START.md) 或提交 Issue。

