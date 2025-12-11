# HomemadeTester 部署验证脚本
# 用于验证系统是否成功部署

Write-Host "🔍 开始验证 HomemadeTester 部署状态..." -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Docker 容器状态
Write-Host "1️⃣ 检查 Docker 容器状态..." -ForegroundColor Yellow
docker-compose ps
Write-Host ""

# 2. 检查服务健康状态
Write-Host "2️⃣ 检查服务健康状态..." -ForegroundColor Yellow
$services = @("postgres", "redis", "neo4j", "backend", "frontend", "worker")
foreach ($service in $services) {
    $status = docker-compose ps $service --format "{{.Status}}"
    if ($status -match "healthy|Up") {
        Write-Host "  ✅ $service : $status" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $service : $status" -ForegroundColor Red
    }
}
Write-Host ""

# 3. 检查后端 API
Write-Host "3️⃣ 检查后端 API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/projects" -Method GET -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ 后端 API 可访问 (状态码: $($response.StatusCode))" -ForegroundColor Green
        Write-Host "  📊 API 文档: http://localhost:8000/docs" -ForegroundColor Cyan
    } else {
        Write-Host "  ⚠️  后端 API 返回状态码: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ 后端 API 无法访问: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 4. 检查前端
Write-Host "4️⃣ 检查前端..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -Method GET -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ 前端可访问 (状态码: $($response.StatusCode))" -ForegroundColor Green
        Write-Host "  🌐 前端地址: http://localhost:5173" -ForegroundColor Cyan
    } else {
        Write-Host "  ⚠️  前端返回状态码: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ 前端无法访问: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 5. 检查数据库连接
Write-Host "5️⃣ 检查数据库连接..." -ForegroundColor Yellow
try {
    $pgStatus = docker-compose exec -T postgres pg_isready -U tester 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ PostgreSQL 数据库连接正常" -ForegroundColor Green
    } else {
        Write-Host "  ❌ PostgreSQL 数据库连接失败" -ForegroundColor Red
    }
} catch {
    Write-Host "  ⚠️  无法检查 PostgreSQL 连接" -ForegroundColor Yellow
}
Write-Host ""

# 6. 检查 Redis
Write-Host "6️⃣ 检查 Redis..." -ForegroundColor Yellow
try {
    $redisStatus = docker-compose exec -T redis redis-cli ping 2>&1
    if ($redisStatus -match "PONG") {
        Write-Host "  ✅ Redis 连接正常" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Redis 连接失败" -ForegroundColor Red
    }
} catch {
    Write-Host "  ⚠️  无法检查 Redis 连接" -ForegroundColor Yellow
}
Write-Host ""

# 7. 检查 Neo4j
Write-Host "7️⃣ 检查 Neo4j..." -ForegroundColor Yellow
try {
    $neo4jStatus = docker-compose exec -T neo4j wget --no-verbose --tries=1 --spider localhost:7474 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Neo4j 服务正常" -ForegroundColor Green
        Write-Host "  🔗 Neo4j 浏览器: http://localhost:7474" -ForegroundColor Cyan
    } else {
        Write-Host "  ❌ Neo4j 服务异常" -ForegroundColor Red
    }
} catch {
    Write-Host "  ⚠️  无法检查 Neo4j 服务" -ForegroundColor Yellow
}
Write-Host ""

# 8. 检查端口占用
Write-Host "8️⃣ 检查端口占用..." -ForegroundColor Yellow
$ports = @(8000, 5173, 5432, 6379, 7474, 7687)
foreach ($port in $ports) {
    $listening = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($listening) {
        Write-Host "  ✅ 端口 $port 正在监听" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  端口 $port 未监听" -ForegroundColor Yellow
    }
}
Write-Host ""

# 9. 检查后端日志（最近错误）
Write-Host "9️⃣ 检查后端日志（最近错误）..." -ForegroundColor Yellow
$errors = docker-compose logs backend --tail=50 2>&1 | Select-String -Pattern "ERROR|error|Error|Exception|Failed" | Select-Object -First 5
if ($errors) {
    Write-Host "  ⚠️  发现以下错误/警告:" -ForegroundColor Yellow
    $errors | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
} else {
    Write-Host "  ✅ 未发现明显错误" -ForegroundColor Green
}
Write-Host ""

# 10. 总结
Write-Host "📋 验证总结" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 访问地址:" -ForegroundColor Cyan
Write-Host "   前端:     http://localhost:5173" -ForegroundColor White
Write-Host "   API文档:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Neo4j:    http://localhost:7474" -ForegroundColor White
Write-Host ""
Write-Host "📊 查看日志:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f              # 查看所有服务日志" -ForegroundColor White
Write-Host "   docker-compose logs -f backend       # 查看后端日志" -ForegroundColor White
Write-Host "   docker-compose logs -f frontend     # 查看前端日志" -ForegroundColor White
Write-Host ""
Write-Host "🛠️  常用命令:" -ForegroundColor Cyan
Write-Host "   docker-compose ps                    # 查看服务状态" -ForegroundColor White
Write-Host "   docker-compose restart backend       # 重启后端" -ForegroundColor White
Write-Host "   docker-compose down                  # 停止所有服务" -ForegroundColor White
Write-Host "   docker-compose up -d                 # 启动所有服务" -ForegroundColor White
Write-Host ""
Write-Host "验证完成！" -ForegroundColor Green

