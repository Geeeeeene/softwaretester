# HomemadeTester 快速启动指南

## 方式一：Docker Compose（推荐）

### 前提条件
- Docker Desktop 或 Docker Engine + Docker Compose
- 至少 4GB 可用内存

### 启动步骤

1. **克隆仓库并进入目录**
```bash
cd homemadeTester
```

2. **启动所有服务**
```bash
docker-compose up -d
```

这将启动以下服务：
- PostgreSQL (端口 5432)
- Redis (端口 6379)
- Neo4j (端口 7474, 7687)
- Backend API (端口 8000)
- Worker进程
- Frontend (端口 5173)

3. **查看服务状态**
```bash
docker-compose ps
```

4. **访问应用**
- 前端: http://localhost:5173
- API文档: http://localhost:8000/docs
- Neo4j浏览器: http://localhost:7474

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

# 同时删除数据卷
docker-compose down -v
```

## 方式二：本地开发环境

### 前提条件
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Neo4j 5+ (可选)

### 后端设置

1. **创建虚拟环境**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

编辑 `.env` 文件，配置数据库连接信息。

4. **启动后端**
```bash
# 方式1：使用uvicorn
uvicorn app.main:app --reload --port 8000

# 方式2：使用Python
python -m app.main
```

5. **启动Worker（新终端）**
```bash
cd backend
venv\Scripts\activate  # 或 source venv/bin/activate
python -m app.worker.worker
```

### 前端设置

1. **安装依赖**
```bash
cd frontend
npm install
```

2. **配置环境变量**
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

3. **启动开发服务器**
```bash
npm run dev
```

前端将运行在 http://localhost:5173

### 数据库初始化

数据库表会在后端首次启动时自动创建。如需手动初始化：

```bash
cd backend
python scripts/init_db.py
```

## 验证安装

### 1. 检查后端API
访问 http://localhost:8000/health 应该返回：
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### 2. 检查前端
访问 http://localhost:5173 应该看到主页

### 3. 测试创建项目
1. 访问"项目管理"页面
2. 点击"创建项目"
3. 填写项目信息并提交
4. 查看项目列表

## 常见问题

### Q1: Docker容器无法启动
**A:** 检查端口是否被占用，特别是 5432 (PostgreSQL), 6379 (Redis), 8000 (API)
```bash
# Windows
netstat -ano | findstr "8000"

# Linux/Mac
lsof -i :8000
```

### Q2: 前端无法连接后端
**A:** 检查 `frontend/.env` 中的 `VITE_API_BASE_URL` 配置是否正确

### Q3: 数据库连接失败
**A:** 确保PostgreSQL服务正在运行，检查 `backend/.env` 中的数据库连接字符串

### Q4: Worker无法处理任务
**A:** 检查Redis服务是否运行，查看Worker日志排查错误

### Q5: 前端编译错误
**A:** 删除 `node_modules` 和 `package-lock.json`，重新安装依赖：
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 下一步

现在您可以：
1. 📖 阅读完整文档：`README.md`
2. 🔍 浏览API文档：http://localhost:8000/docs
3. 🧪 创建第一个测试项目
4. 📝 编写Test IR格式的测试用例
5. ▶️ 运行测试并查看结果

## 开发工具推荐

- **API测试**: Postman, Insomnia, httpie
- **数据库管理**: pgAdmin, DBeaver
- **Redis客户端**: RedisInsight
- **Neo4j浏览器**: http://localhost:7474
- **代码编辑器**: VS Code, PyCharm

## 支持与反馈

如遇到问题或有建议，请：
- 查看文档: `README.md`
- 查看API文档: http://localhost:8000/docs
- 检查日志输出

祝使用愉快！🚀

