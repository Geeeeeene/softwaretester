# HomemadeTester 启动指南

## 📋 目录
- [方式一：Docker Compose（推荐）](#方式一docker-compose推荐)
- [方式二：本地开发环境](#方式二本地开发环境)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

---

## 方式一：Docker Compose（推荐）

### 前提条件
- ✅ Docker Desktop 已安装并运行
- ✅ 至少 4GB 可用内存
- ✅ 端口 8000, 5173, 5432, 6379, 7474 未被占用

### Windows 启动步骤

1. **打开项目目录**
```powershell
cd D:\测试项目\softwaretester
```

2. **使用启动脚本（最简单）**
```powershell
.\start.bat
```

3. **或手动启动**
```powershell
docker-compose up -d
```

4. **查看服务状态**
```powershell
docker-compose ps
```

5. **访问应用**
- 🌐 前端界面: http://localhost:5173
- 📚 API文档: http://localhost:8000/docs
- 🔍 Neo4j浏览器: http://localhost:7474

6. **查看日志**
```powershell
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

7. **停止服务**
```powershell
docker-compose down
```

---

## 方式二：本地开发环境

### 前提条件
- ✅ Python 3.10+ 已安装
- ✅ Node.js 18+ 已安装
- ✅ PostgreSQL 14+ 已安装并运行（或使用SQLite）
- ✅ Redis 6+ 已安装并运行（可选，用于任务队列）

### 步骤 1: 后端设置

#### 1.1 进入后端目录
```powershell
cd D:\测试项目\softwaretester\backend
```

#### 1.2 创建并激活虚拟环境
```powershell
# 创建虚拟环境（如果还没有）
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\activate
```

#### 1.3 安装依赖
```powershell
pip install -r requirements.txt
```

#### 1.4 初始化数据库
```powershell
# 数据库表会在首次启动时自动创建
# 或手动初始化
python scripts\init_db.py
```

#### 1.5 启动后端服务
```powershell
# 方式1：使用启动脚本
.\start.bat

# 方式2：使用uvicorn命令
uvicorn app.main:app --reload --port 8000

# 方式3：使用Python
python -m app.main
```

后端将运行在 http://localhost:8000

#### 1.6 启动Worker（可选，用于后台任务处理）
```powershell
# 新开一个终端窗口
cd D:\测试项目\softwaretester\backend
.\venv\Scripts\activate
python -m app.worker.worker
```

### 步骤 2: 前端设置

#### 2.1 进入前端目录
```powershell
cd D:\测试项目\softwaretester\frontend
```

#### 2.2 安装依赖
```powershell
npm install
```

#### 2.3 配置环境变量（可选）
创建 `.env` 文件（如果不存在）：
```env
VITE_API_BASE_URL=http://localhost:8000
```

#### 2.4 启动开发服务器
```powershell
npm run dev
```

前端将运行在 http://localhost:5173

---

## 验证安装

### 1. 检查后端API
访问 http://localhost:8000/health

应该返回：
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### 2. 检查API文档
访问 http://localhost:8000/docs

应该看到 Swagger UI 文档界面

### 3. 检查前端
访问 http://localhost:5173

应该看到应用主页

### 4. 测试创建项目
1. 在浏览器中访问 http://localhost:5173
2. 点击"项目管理"
3. 点击"创建项目"
4. 填写项目信息：
   - 项目名称：测试项目
   - 项目类型：单元测试
   - 编程语言：cpp
5. 点击"创建项目"
6. 查看项目列表

---

## 常见问题

### ❌ 问题1: 端口被占用

**错误信息：**
```
Error: bind: address already in use
```

**解决方法：**
```powershell
# Windows - 查找占用端口的进程
netstat -ano | findstr "8000"

# 结束进程（替换PID为实际进程ID）
taskkill /PID <PID> /F

# 或修改配置文件中的端口号
```

### ❌ 问题2: 前端无法连接后端

**错误信息：**
```
Network Error: Failed to fetch
```

**解决方法：**
1. 检查后端是否正在运行
2. 检查 `frontend/.env` 中的 `VITE_API_BASE_URL` 配置
3. 检查浏览器控制台的CORS错误
4. 确保后端CORS配置正确

### ❌ 问题3: 数据库连接失败

**错误信息：**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决方法：**
1. 检查PostgreSQL服务是否运行
2. 检查数据库连接配置（`backend/app/core/config.py`）
3. 如果使用SQLite，确保有写入权限

### ❌ 问题4: 模块导入错误

**错误信息：**
```
ModuleNotFoundError: No module named 'app'
```

**解决方法：**
```powershell
# 确保在正确的目录下运行
cd D:\测试项目\softwaretester\backend

# 确保虚拟环境已激活
.\venv\Scripts\activate

# 重新安装依赖
pip install -r requirements.txt
```

### ❌ 问题5: 前端编译错误

**错误信息：**
```
npm ERR! code ELIFECYCLE
```

**解决方法：**
```powershell
cd frontend

# 删除node_modules和锁文件
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json

# 重新安装
npm install
```

### ❌ 问题6: Docker容器无法启动

**解决方法：**
```powershell
# 检查Docker是否运行
docker ps

# 查看容器日志
docker-compose logs backend

# 重启服务
docker-compose down
docker-compose up -d
```

---

## 快速命令参考

### Docker Compose
```powershell
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启特定服务
docker-compose restart backend
```

### 后端
```powershell
# 激活虚拟环境
.\venv\Scripts\activate

# 启动服务
uvicorn app.main:app --reload --port 8000

# 初始化数据库
python scripts\init_db.py
```

### 前端
```powershell
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

---

## 下一步

启动成功后，您可以：

1. 📖 **阅读文档**
   - `README.md` - 项目概述
   - `ARCHITECTURE.md` - 架构设计
   - `QUICK_START.md` - 快速开始

2. 🧪 **创建测试项目**
   - 访问 http://localhost:5173
   - 创建新项目
   - 上传源代码

3. 🔧 **使用UTBotCpp测试**
   - 创建C++项目
   - 上传源代码ZIP文件
   - 运行UTBotCpp测试

4. 📊 **查看测试结果**
   - 查看测试执行状态
   - 查看覆盖率报告
   - 分析测试日志

---

## 获取帮助

如果遇到问题：
1. 查看日志输出
2. 检查常见问题部分
3. 查看API文档：http://localhost:8000/docs
4. 检查项目文档

祝使用愉快！🚀

