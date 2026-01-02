# HomemadeTester 快速启动指南

## Docker Compose 启动（推荐）

### 前提条件
- Docker Desktop 或 Docker Engine + Docker Compose
- 至少 4GB 可用内存

### 启动步骤

1. **克隆仓库并进入目录**
```bash
git clone https://cnb.cool/Tralalero_555/softwaretester.git
cd softwaretester
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

# 同时删除数据卷（会删除所有数据）
docker-compose down -v
```

### 数据库初始化

数据库表会在后端首次启动时自动创建，无需手动初始化。

## 验证安装

### 1. 检查服务状态
```bash
docker-compose ps
```
所有服务应该显示为 "Up" 状态

### 2. 检查后端API
访问 http://localhost:8000/health 应该返回：
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### 3. 检查前端
访问 http://localhost:5173 应该看到主页

### 4. 测试创建项目
1. 访问"项目管理"页面
2. 点击"创建项目"
3. 填写项目信息并提交
4. 查看项目列表

## 常见问题

### Q1: Docker容器无法启动
**A:** 检查端口是否被占用，特别是 5432 (PostgreSQL), 6379 (Redis), 8000 (API), 5173 (Frontend)
```bash
# Windows
netstat -ano | findstr "8000"

# Linux/Mac
lsof -i :8000
```

**解决方法：**
- 停止占用端口的程序
- 或修改 `docker-compose.yml` 中的端口映射

### Q2: Docker Desktop 未运行
**A:** 确保 Docker Desktop 已启动并运行
```bash
# 检查 Docker 状态
docker info
```

**解决方法：**
- 打开 Docker Desktop
- 等待 Docker 完全启动（系统托盘图标显示运行中）

### Q3: 前端无法连接后端
**A:** 检查 Docker 容器是否正常运行
```bash
docker-compose ps
```

**解决方法：**
- 确保 backend 和 frontend 服务都已启动
- 查看日志：`docker-compose logs frontend backend`

### Q4: 数据库连接失败
**A:** 确保 PostgreSQL 容器已启动并健康
```bash
docker-compose ps postgres
```

**解决方法：**
- 等待 PostgreSQL 容器完全启动（健康检查通过）
- 查看日志：`docker-compose logs postgres`

### Q5: Worker无法处理任务
**A:** 检查 Redis 和 Worker 服务是否运行
```bash
docker-compose ps redis worker
```

**解决方法：**
- 确保 Redis 容器已启动
- 查看 Worker 日志：`docker-compose logs worker`

## 下一步

现在您可以：
1. 📖 阅读完整文档：`README.md`
2. 🔍 浏览API文档：http://localhost:8000/docs
3. 🧪 创建第一个测试项目
4. 📝 编写Test IR格式的测试用例
5. ▶️ 运行测试并查看结果
6. 📚 查看 [UI测试使用指南](UI测试使用指南.md) 了解UI测试功能

## 管理命令

### 重启服务
```bash
docker-compose restart
```

### 重建并启动
```bash
docker-compose up -d --build
```

### 清理所有数据（谨慎使用）
```bash
docker-compose down -v
```

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
- 检查日志输出: `docker-compose logs -f`

祝使用愉快！🚀

