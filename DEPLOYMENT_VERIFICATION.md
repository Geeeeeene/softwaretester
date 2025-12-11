# HomemadeTester 部署验证指南

本文档说明如何验证 HomemadeTester 系统是否成功部署。

## 快速验证

### 方法一：使用验证脚本（推荐）

**Windows:**
```bash
verify_deployment.bat
```

**PowerShell:**
```powershell
powershell -ExecutionPolicy Bypass -File verify_deployment.ps1
```

### 方法二：手动验证

## 1. 检查 Docker 容器状态

```bash
docker-compose ps
```

**预期结果：** 所有服务状态应为 `Up` 或 `Up (healthy)`

```
NAME                        STATUS
softwaretester-backend-1    Up X minutes
softwaretester-frontend-1   Up X minutes
softwaretester-neo4j-1      Up X minutes (healthy)
softwaretester-postgres-1   Up X minutes (healthy)
softwaretester-redis-1     Up X minutes (healthy)
softwaretester-worker-1     Up X minutes
```

## 2. 检查服务健康状态

```bash
# 检查所有服务
docker-compose ps

# 检查特定服务
docker-compose ps backend
docker-compose ps postgres
docker-compose ps redis
docker-compose ps neo4j
```

## 3. 检查后端 API

### 3.1 检查 API 是否可访问

**PowerShell:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/projects" -UseBasicParsing
```

**浏览器:**
打开 http://localhost:8000/api/v1/projects

**预期结果：** 返回 JSON 数据或空数组 `[]`

### 3.2 检查 API 文档

**浏览器访问:**
http://localhost:8000/docs

**预期结果：** 显示 Swagger UI 文档界面

### 3.3 使用 curl（如果已安装）

```bash
curl http://localhost:8000/api/v1/projects
curl http://localhost:8000/docs
```

## 4. 检查前端

**浏览器访问:**
http://localhost:5173

**预期结果：** 显示 HomemadeTester 前端界面

**PowerShell 检查:**
```powershell
Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing
```

## 5. 检查数据库连接

```bash
# PostgreSQL
docker-compose exec postgres pg_isready -U tester

# 预期输出: postgres:5432 - accepting connections
```

## 6. 检查 Redis

```bash
docker-compose exec redis redis-cli ping

# 预期输出: PONG
```

## 7. 检查 Neo4j

**浏览器访问:**
http://localhost:7474

**预期结果：** 显示 Neo4j 浏览器界面

**命令行检查:**
```bash
docker-compose exec neo4j wget --no-verbose --tries=1 --spider localhost:7474
```

## 8. 检查端口占用

**PowerShell:**
```powershell
Get-NetTCPConnection -LocalPort 8000,5173,5432,6379,7474,7687 | Select-Object LocalPort, State
```

**预期结果：** 所有端口都显示 `Listen` 状态

## 9. 检查日志

### 查看所有服务日志
```bash
docker-compose logs -f
```

### 查看特定服务日志
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f neo4j
docker-compose logs -f worker
```

### 查看最近 50 行日志
```bash
docker-compose logs --tail=50 backend
```

### 检查错误日志
```bash
docker-compose logs backend | findstr /i "error exception failed"
```

## 10. 功能测试

### 10.1 创建测试项目

**使用 API:**
```bash
curl -X POST http://localhost:8000/api/v1/projects ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"测试项目\",\"description\":\"验证部署\",\"project_type\":\"static\"}"
```

### 10.2 获取项目列表

**浏览器:**
http://localhost:8000/api/v1/projects

**PowerShell:**
```powershell
(Invoke-WebRequest -Uri "http://localhost:8000/api/v1/projects" -UseBasicParsing).Content
```

## 验证清单

- [ ] 所有 Docker 容器都在运行
- [ ] 后端 API 可访问（http://localhost:8000）
- [ ] API 文档可访问（http://localhost:8000/docs）
- [ ] 前端可访问（http://localhost:5173）
- [ ] PostgreSQL 数据库连接正常
- [ ] Redis 连接正常
- [ ] Neo4j 可访问（http://localhost:7474）
- [ ] 所有端口都在监听
- [ ] 日志中没有严重错误

## 常见问题排查

### 问题 1: 容器无法启动

**检查:**
```bash
docker-compose ps
docker-compose logs [服务名]
```

**解决:**
```bash
docker-compose down
docker-compose up -d
```

### 问题 2: 端口被占用

**检查端口占用:**
```powershell
Get-NetTCPConnection -LocalPort 8000
```

**解决:** 修改 `docker-compose.yml` 中的端口映射

### 问题 3: 数据库连接失败

**检查:**
```bash
docker-compose logs postgres
docker-compose exec postgres pg_isready -U tester
```

**解决:**
```bash
docker-compose restart postgres
```

### 问题 4: 后端无法访问

**检查:**
```bash
docker-compose logs backend
docker-compose restart backend
```

### 问题 5: 前端无法访问

**检查:**
```bash
docker-compose logs frontend
docker-compose restart frontend
```

## 访问地址汇总

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:5173 | React 前端界面 |
| 后端 API | http://localhost:8000 | FastAPI 后端 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| Neo4j | http://localhost:7474 | Neo4j 浏览器 |
| PostgreSQL | localhost:5432 | 数据库（需要客户端） |
| Redis | localhost:6379 | 缓存和队列 |

## 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart [服务名]

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [服务名]

# 进入容器
docker-compose exec [服务名] sh

# 查看资源使用
docker stats
```

## 验证成功标志

✅ **所有检查项都通过，系统部署成功！**

如果所有验证步骤都通过，说明系统已成功部署，可以开始使用了。

