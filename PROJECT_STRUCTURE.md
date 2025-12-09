# 项目结构说明

## 目录结构

```
homemadeTester/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # REST API路由
│   │   │   └── v1/
│   │   │       ├── endpoints/ # API端点实现
│   │   │       │   ├── projects.py      # 项目管理API
│   │   │       │   ├── test_cases.py    # 测试用例API
│   │   │       │   └── executions.py    # 测试执行API
│   │   │       └── __init__.py
│   │   │
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 应用配置
│   │   │   └── __init__.py
│   │   │
│   │   ├── db/                # 数据库
│   │   │   ├── models/        # SQLAlchemy模型
│   │   │   │   ├── project.py           # 项目模型
│   │   │   │   ├── test_case.py         # 测试用例模型
│   │   │   │   ├── test_execution.py    # 测试执行模型
│   │   │   │   └── test_result.py       # 测试结果模型
│   │   │   ├── base.py        # Base模型
│   │   │   ├── session.py     # 数据库会话
│   │   │   └── __init__.py
│   │   │
│   │   ├── schemas/           # Pydantic Schema
│   │   │   ├── project.py     # 项目Schema
│   │   │   ├── test_case.py   # 测试用例Schema
│   │   │   └── __init__.py
│   │   │
│   │   ├── test_ir/           # Test IR定义
│   │   │   ├── schemas.py     # IR Schema定义
│   │   │   └── __init__.py
│   │   │
│   │   ├── executors/         # 执行器适配层
│   │   │   ├── base.py        # 执行器基类
│   │   │   ├── spix_adapter.py       # Spix适配器
│   │   │   ├── utbot_adapter.py      # UTBot适配器
│   │   │   ├── static_analyzer.py    # 静态分析器
│   │   │   ├── factory.py     # 执行器工厂
│   │   │   └── __init__.py
│   │   │
│   │   ├── worker/            # 后台任务
│   │   │   ├── tasks.py       # 任务定义
│   │   │   ├── worker.py      # Worker启动脚本
│   │   │   └── __init__.py
│   │   │
│   │   └── main.py            # FastAPI应用入口
│   │
│   ├── scripts/               # 工具脚本
│   │   ├── init_db.py         # 数据库初始化
│   │   └── create_sample_data.py  # 创建示例数据
│   │
│   ├── requirements.txt       # Python依赖
│   ├── Dockerfile            # Docker镜像
│   └── .env.example          # 环境变量示例
│
├── frontend/                  # React前端
│   ├── src/
│   │   ├── components/       # React组件
│   │   │   ├── ui/          # UI组件（shadcn/ui）
│   │   │   │   ├── button.tsx
│   │   │   │   └── card.tsx
│   │   │   └── Layout.tsx   # 布局组件
│   │   │
│   │   ├── pages/           # 页面组件
│   │   │   ├── HomePage.tsx            # 首页
│   │   │   ├── ProjectsPage.tsx        # 项目列表
│   │   │   ├── ProjectDetailPage.tsx   # 项目详情
│   │   │   ├── TestCasesPage.tsx       # 测试用例
│   │   │   ├── TestExecutionPage.tsx   # 测试执行
│   │   │   └── ResultsPage.tsx         # 结果分析
│   │   │
│   │   ├── lib/             # 工具库
│   │   │   ├── api.ts       # API客户端
│   │   │   └── utils.ts     # 工具函数
│   │   │
│   │   ├── App.tsx          # 应用根组件
│   │   ├── main.tsx         # 应用入口
│   │   └── index.css        # 全局样式
│   │
│   ├── package.json         # Node依赖
│   ├── vite.config.ts       # Vite配置
│   ├── tsconfig.json        # TypeScript配置
│   ├── tailwind.config.js   # Tailwind配置
│   ├── Dockerfile          # Docker镜像
│   └── index.html          # HTML模板
│
├── docker-compose.yml       # Docker编排配置
├── .gitignore              # Git忽略文件
├── README.md               # 项目文档
├── QUICK_START.md          # 快速启动指南
├── PROJECT_STRUCTURE.md    # 本文件
├── start.sh                # Linux/Mac启动脚本
└── start.bat               # Windows启动脚本
```

## 核心模块说明

### 1. Backend（后端）

#### API层 (`app/api/v1/`)
- 提供RESTful API接口
- 分模块管理：项目、测试用例、执行记录
- 使用FastAPI的依赖注入

#### 数据库层 (`app/db/`)
- SQLAlchemy ORM模型
- PostgreSQL关系型存储
- 支持项目、用例、执行、结果等实体

#### Test IR层 (`app/test_ir/`)
- 统一的测试中间表示
- 支持UI、单元、集成、静态分析
- Pydantic模型验证

#### 执行器层 (`app/executors/`)
- 适配不同测试工具
- 抽象基类定义接口
- 工厂模式创建执行器

#### Worker层 (`app/worker/`)
- 基于Redis Queue的任务队列
- 异步执行测试任务
- 支持多Worker并发

### 2. Frontend（前端）

#### 组件层 (`src/components/`)
- Layout：应用布局
- UI组件：基于shadcn/ui

#### 页面层 (`src/pages/`)
- 单页应用（SPA）
- React Router路由管理
- 响应式设计

#### 服务层 (`src/lib/`)
- API客户端封装
- Axios请求拦截
- 工具函数

### 3. 配置文件

#### Docker配置
- `docker-compose.yml`：编排所有服务
- `Dockerfile`：构建镜像

#### 环境配置
- `.env.example`：环境变量模板
- 生产环境需创建`.env`文件

## 数据流

```
用户操作 → Frontend → API Gateway → Backend Service
                                    ↓
                              Database (PostgreSQL)
                                    ↓
                              Task Queue (Redis)
                                    ↓
                              Worker → Executor → Target System
                                    ↓
                              Results → Database → Frontend
```

## 扩展点

### 添加新的执行器

1. 在 `backend/app/executors/` 创建新适配器
2. 继承 `BaseExecutor` 基类
3. 实现 `execute()` 和 `validate_ir()` 方法
4. 在 `factory.py` 注册执行器

### 添加新的页面

1. 在 `frontend/src/pages/` 创建页面组件
2. 在 `App.tsx` 添加路由
3. 在 `Layout.tsx` 添加导航链接

### 添加新的API端点

1. 在 `backend/app/api/v1/endpoints/` 创建端点文件
2. 定义Schema在 `backend/app/schemas/`
3. 在 `__init__.py` 注册路由
4. 更新前端 `api.ts` 添加客户端方法

## 技术栈

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

### 基础设施
- **容器**: Docker + Docker Compose
- **图数据库**: Neo4j（可选）
- **存储**: 本地文件系统/MinIO（可扩展）

## 开发建议

1. **后端开发**：使用虚拟环境，热重载开发
2. **前端开发**：Vite HMR快速刷新
3. **数据库**：使用pgAdmin管理PostgreSQL
4. **调试**：查看Docker日志或本地进程输出
5. **测试**：编写pytest单元测试

## 部署建议

1. **开发环境**：本地启动或Docker Compose
2. **生产环境**：
   - 使用Gunicorn/Uvicorn多进程
   - Nginx反向代理
   - 容器编排（Kubernetes/Docker Swarm）
   - 配置SSL证书
   - 设置环境变量

## 维护指南

- **日志管理**：配置日志轮转
- **备份策略**：定期备份PostgreSQL和Neo4j
- **监控告警**：集成Prometheus/Grafana
- **性能优化**：缓存、数据库索引、CDN

