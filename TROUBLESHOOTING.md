# 故障排查指南

## 常见错误及解决方案

### 1. CORS 错误

**错误信息：**
```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/...' from origin 'http://localhost:5173' 
has been blocked by CORS policy
```

**解决方案：**
- 已修复：后端 CORS 配置已更新
- 如果仍然出现，重启后端：
  ```bash
  docker-compose restart backend
  ```
- 清除浏览器缓存并刷新页面

### 2. 前端编译错误

**错误信息：**
```
error TS6133: 'xxx' is declared but its value is never read
```

**解决方案：**
- 已修复：已移除未使用的变量
- 如果仍有错误，检查浏览器控制台的具体错误信息

### 3. 按钮点击无反应

**问题：** 点击"创建项目"或"创建第一个项目"按钮没有反应

**解决方案：**
- 已修复：已添加 onClick 处理函数
- 刷新浏览器页面（Ctrl+F5）
- 检查浏览器控制台是否有 JavaScript 错误

### 4. API 请求失败

**错误信息：**
```
Failed to load resource: net::ERR_FAILED
```

**解决方案：**
1. 检查后端是否运行：
   ```bash
   docker-compose ps backend
   ```

2. 检查后端日志：
   ```bash
   docker-compose logs backend
   ```

3. 测试 API 是否可访问：
   ```bash
   curl http://localhost:8000/api/v1/projects
   ```

### 5. 前端页面空白

**解决方案：**
1. 检查前端是否运行：
   ```bash
   docker-compose ps frontend
   ```

2. 检查前端日志：
   ```bash
   docker-compose logs frontend
   ```

3. 重启前端：
   ```bash
   docker-compose restart frontend
   ```

### 6. 数据库连接错误

**错误信息：**
```
database connection failed
```

**解决方案：**
1. 检查 PostgreSQL 是否运行：
   ```bash
   docker-compose ps postgres
   ```

2. 重启数据库：
   ```bash
   docker-compose restart postgres
   ```

### 7. 工具找不到

**问题：** 创建测试用例时找不到 Clazy 或 Cppcheck

**解决方案：**
- 这是正常的，工具需要在系统中安装
- 执行器会检查工具是否可用
- 如果工具未安装，会显示警告但不会阻止创建测试用例

## 快速修复命令

### 重启所有服务
```bash
docker-compose restart
```

### 查看所有服务状态
```bash
docker-compose ps
```

### 查看所有服务日志
```bash
docker-compose logs -f
```

### 查看特定服务日志
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 完全重置（删除所有数据）
```bash
docker-compose down -v
docker-compose up -d
```

## 浏览器调试

### 打开开发者工具
- Windows/Linux: `F12` 或 `Ctrl+Shift+I`
- Mac: `Cmd+Option+I`

### 检查控制台错误
1. 打开开发者工具
2. 切换到 "Console" 标签
3. 查看红色错误信息
4. 截图或复制错误信息以便排查

### 检查网络请求
1. 打开开发者工具
2. 切换到 "Network" 标签
3. 刷新页面
4. 查看失败的请求（红色）
5. 点击查看详细信息

## 常见问题

### Q: 页面显示"加载中..."一直不消失
**A:** 可能是 API 请求失败，检查：
1. 后端是否运行
2. 浏览器控制台的错误信息
3. 网络标签中的请求状态

### Q: 创建项目后看不到
**A:** 
1. 刷新页面
2. 检查是否选择了正确的项目类型过滤器
3. 查看浏览器控制台是否有错误

### Q: 无法创建测试用例
**A:**
1. 确保已创建项目
2. 从项目详情页进入测试用例页面
3. 检查浏览器控制台错误

## 获取帮助

如果以上方法都无法解决问题：

1. **收集错误信息：**
   - 浏览器控制台的错误（F12）
   - 后端日志：`docker-compose logs backend`
   - 前端日志：`docker-compose logs frontend`

2. **检查服务状态：**
   ```bash
   docker-compose ps
   ```

3. **验证部署：**
   ```bash
   verify_deployment.bat
   ```


