# HomemadeTester - 统一测试平台

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18.2-blue.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104-green.svg)](https://fastapi.tiangolo.com/)

HomemadeTester 是一个基于 **Test IR（测试中间表示）** 的统一测试平台，旨在通过标准化的测试描述格式，整合多种测试工具和执行器，提供一站式的测试管理和执行解决方案。

## ✨ 核心特性

- 🎯 **统一测试接口**：基于 Test IR 的标准化测试描述格式
- 🔌 **多执行器支持**：支持 UI 测试（Spix）、单元测试（UTBot）、静态分析等多种测试类型
- 📊 **可视化界面**：现代化的 React 前端，提供直观的测试管理和结果展示
- 🚀 **异步执行**：基于 Redis Queue 的异步任务处理，支持并发执行
- 📈 **结果分析**：详细的测试结果、覆盖率报告和可视化分析
- 🐳 **容器化部署**：Docker Compose 一键启动所有服务
- 🔄 **实时监控**：测试执行状态实时更新，支持 WebSocket 推送

## 🏗️ 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15, Neo4j 5
- **队列**: Redis 7 + RQ
- **ORM**: SQLAlchemy 2.0
- **验证**: Pydantic 2.5

### 前端
- **框架**: React 18 + TypeScript
- **构建**: Vite 5
- **路由**: React Router 6
- **状态**: TanStack Query
- **样式**: TailwindCSS + shadcn/ui
- **HTTP**: Axios
- **代码高亮**: react-syntax-highlighter

### 基础设施
- **容器**: Docker + Docker Compose
- **图数据库**: Neo4j（可选）
- **存储**: 本地文件系统/MinIO（可扩展）

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

1. **克隆仓库**
```bash
git clone https://cnb.cool/Tralalero_555/softwaretester.git
cd softwaretester
```

2. **启动所有服务**
```bash
docker-compose up -d
```

3. **访问应用**
- 前端: http://localhost:5173
- API文档: http://localhost:8000/docs
- Neo4j浏览器: http://localhost:7474

### 方式二：本地开发环境

详细步骤请参考 [QUICK_START.md](QUICK_START.md)

## 📁 项目结构

```
homemadeTester/
├── backend/              # FastAPI 后端服务
│   ├── app/
│   │   ├── api/         # REST API 路由
│   │   ├── db/          # 数据库模型和会话
│   │   ├── executors/   # 测试执行器适配层
│   │   ├── schemas/     # Pydantic Schema
│   │   ├── test_ir/     # Test IR 定义
│   │   └── worker/      # 后台任务处理
│   ├── scripts/         # 工具脚本
│   └── requirements.txt
├── frontend/            # React 前端应用
│   ├── src/
│   │   ├── components/  # React 组件
│   │   ├── pages/       # 页面组件
│   │   └── lib/         # 工具库
│   └── package.json
├── docker-compose.yml   # Docker 编排配置
└── README.md
```

详细结构说明请参考 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 🎯 核心概念

### Test IR（测试中间表示）

Test IR 是一个统一的测试描述格式，支持多种测试类型：

#### UI 测试 IR
```json
{
  "type": "ui",
  "name": "登录测试",
  "steps": [
    {"type": "input", "target": "username", "value": "admin"},
    {"type": "click", "target": "loginButton"},
    {"type": "assert", "target": "welcome", "value": "欢迎"}
  ]
}
```

#### 单元测试 IR
```json
{
  "type": "unit",
  "name": "测试加法函数",
  "function_under_test": {
    "name": "add",
    "file_path": "math_utils.cpp"
  },
  "inputs": {"parameters": {"a": 1, "b": 2}},
  "assertions": [{"type": "equals", "expected": 3}]
}
```

#### 静态分析 IR
```json
{
  "type": "static",
  "name": "代码质量检查",
  "target_files": ["src/**/*.cpp"],
  "rules": [
    {"rule_id": "mem-leak", "severity": "error"}
  ]
}
```

## 📖 文档

- [快速启动指南](QUICK_START.md) - 详细的安装和启动说明
- [项目结构说明](PROJECT_STRUCTURE.md) - 代码组织结构
- [架构设计文档](ARCHITECTURE.md) - 系统架构和设计理念

## 🔧 开发指南

### 添加新的执行器

1. 在 `backend/app/executors/` 创建新适配器
2. 继承 `BaseExecutor` 基类
3. 实现 `execute()` 和 `validate_ir()` 方法
4. 在 `factory.py` 注册执行器

### 添加新的测试类型

1. 在 `backend/app/test_ir/schemas.py` 定义新 IR Schema
2. 创建对应执行器
3. 更新前端类型定义
4. 添加编辑器模板

详细开发指南请参考 [ARCHITECTURE.md](ARCHITECTURE.md)

## 🧪 功能模块

### 项目管理
- 创建和管理测试项目
- 支持多种项目类型（UI、单元、集成、静态分析）
- 项目配置和元数据管理

### 测试用例管理
- Test IR 格式的测试用例编辑
- JSON/YAML 双模式编辑
- 实时 Schema 验证
- 用例版本管理

### 测试执行
- 异步任务队列处理
- 多执行器支持
- 实时状态监控
- 执行历史记录

### 结果分析
- 详细的测试结果展示
- 覆盖率报告
- 错误日志和堆栈跟踪
- 可视化图表

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

## 🐛 常见问题

### Q1: Docker 容器无法启动
**A:** 检查端口是否被占用，特别是 5432 (PostgreSQL), 6379 (Redis), 8000 (API)

### Q2: 前端无法连接后端
**A:** 检查 `frontend/.env` 中的 `VITE_API_BASE_URL` 配置是否正确

### Q3: 数据库连接失败
**A:** 确保 PostgreSQL 服务正在运行，检查 `backend/.env` 中的数据库连接字符串

更多问题请参考 [QUICK_START.md](QUICK_START.md) 的常见问题部分

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🔗 相关链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [RQ 文档](https://python-rq.org/)
- [Neo4j 文档](https://neo4j.com/docs/)

## 📧 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue: https://cnb.cool/Tralalero_555/softwaretester/issues
- 项目地址: https://cnb.cool/Tralalero_555/softwaretester

---

⭐ 如果这个项目对你有帮助，请给个 Star！
