# HomemadeTester 架构设计文档

## 1. 系统概述

HomemadeTester是一个基于Test IR（测试中间表示）的统一测试平台，旨在通过标准化的测试描述格式，整合多种测试工具和执行器，提供一站式的测试管理和执行解决方案。

## 2. 核心设计理念

### 2.1 UI与后端解耦

- **统一Test IR层**：所有测试类型通过JSON/YAML格式的IR表示
- **执行器适配**：各执行器通过适配层转换IR到具体工具格式
- **队列驱动**：异步任务队列解耦请求和执行

### 2.2 分层架构

```
┌─────────────────────────────────────────┐
│          Web UI (React)                 │
│  - 项目管理                              │
│  - 用例编辑                              │
│  - 执行监控                              │
│  - 结果可视化                            │
└────────────┬────────────────────────────┘
             │ HTTP/WebSocket
┌────────────▼────────────────────────────┐
│     Backend API (FastAPI)               │
│  - REST API                             │
│  - Test IR 验证                         │
│  - 权限认证 (JWT)                       │
└────────────┬────────────────────────────┘
             │
     ┌───────┴───────┐
     ▼               ▼
┌─────────┐    ┌──────────────┐
│ Database│    │ Task Queue   │
│(Postgres│    │  (Redis+RQ)  │
│  Neo4j) │    └──────┬───────┘
└─────────┘           │
                      ▼
            ┌──────────────────┐
            │   Worker Pool    │
            │  - 任务调度       │
            │  - 并发控制       │
            └────────┬─────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│ Executor Layer  │    │  Graph Store     │
│ - Spix Adapter  │    │  - CFG           │
│ - UTBot Adapter │    │  - Call Graph    │
│ - Static Analyzer│   │  - State Machine │
└─────────────────┘    └──────────────────┘
         │
         ▼
┌─────────────────────┐
│ Artifact Storage    │
│ - Logs              │
│ - Screenshots       │
│ - Coverage Reports  │
└─────────────────────┘
```

## 3. 模块详细设计

### 3.1 Test IR（测试中间表示）

**设计目标**：
- 统一描述所有测试类型
- 便于版本管理和复用
- 支持工具无关的抽象

**IR类型**：

#### UI测试IR
```json
{
  "type": "ui",
  "name": "登录测试",
  "steps": [
    {"type": "input", "target": "username", "value": "admin"},
    {"type": "input", "target": "password", "value": "123456"},
    {"type": "click", "target": "loginButton"},
    {"type": "assert", "target": "welcome", "value": "欢迎"}
  ]
}
```

#### 单元测试IR
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

#### 静态分析IR
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

### 3.2 执行器适配层

**设计模式**：策略模式 + 工厂模式

```python
class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, test_ir: Dict) -> Dict:
        """执行测试"""
        pass
    
    @abstractmethod
    def validate_ir(self, test_ir: Dict) -> bool:
        """验证IR格式"""
        pass

class ExecutorFactory:
    _executors = {
        "robot_framework": RobotFrameworkAdapter,
        "utbot": UTBotAdapter,
        "static_analyzer": StaticAnalyzer
    }
    
    @classmethod
    def get_executor(cls, executor_type: str):
        return cls._executors[executor_type]()
```

### 3.3 任务队列架构

**技术选型**：Redis + RQ（可替换为RabbitMQ + Celery）

**队列设计**：
- `high`：高优先级队列（关键测试）
- `default`：默认队列
- `low`：低优先级队列（夜间批量测试）

**任务流程**：
```
1. API接收执行请求
2. 创建TestExecution记录（状态=pending）
3. 将任务推入队列
4. Worker拾取任务
5. 更新状态为running
6. 调用执行器
7. 保存TestResult
8. 更新TestExecution状态为completed
```

### 3.4 数据库设计

#### 关系型数据库（PostgreSQL）

**核心表结构**：

```sql
-- 项目表
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    project_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 测试用例表
CREATE TABLE test_cases (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    test_type VARCHAR(50) NOT NULL,
    test_ir JSONB NOT NULL,  -- Test IR内容
    created_at TIMESTAMP DEFAULT NOW()
);

-- 测试执行表
CREATE TABLE test_executions (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id),
    executor_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- pending/running/completed/failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 测试结果表
CREATE TABLE test_results (
    id SERIAL PRIMARY KEY,
    execution_id INT REFERENCES test_executions(id),
    test_case_id INT REFERENCES test_cases(id),
    status VARCHAR(20) NOT NULL,  -- passed/failed/error/skipped
    duration_seconds FLOAT,
    error_message TEXT,
    coverage_data JSONB
);
```

#### 图数据库（Neo4j）

**用途**：
- 存储CFG（控制流图）
- 存储调用图
- 存储状态机
- 支持路径查询和可视化

**示例Cypher**：
```cypher
// 创建函数节点和调用关系
CREATE (f1:Function {name: 'main'})
CREATE (f2:Function {name: 'calculate'})
CREATE (f1)-[:CALLS]->(f2)

// 查询调用链
MATCH path = (f:Function {name: 'main'})-[:CALLS*]->(target)
RETURN path
```

### 3.5 前端架构

**技术栈**：
- React 18（组件化）
- TanStack Query（服务器状态管理）
- React Router（路由）
- TailwindCSS（样式）
- shadcn/ui（组件库）

**页面结构**：
```
/                      - 首页
/projects              - 项目列表
/projects/:id          - 项目详情
/test-cases            - 测试用例管理
/test-cases/:id/edit   - 用例编辑器
/execution             - 测试执行
/results               - 结果分析
/coverage              - 覆盖率视图
/cfg-viewer            - CFG可视化
```

**状态管理**：
```typescript
// 使用React Query管理服务器状态
const { data: projects } = useQuery({
  queryKey: ['projects'],
  queryFn: () => projectsApi.list()
})

// 使用mutation更新数据
const createProject = useMutation({
  mutationFn: projectsApi.create,
  onSuccess: () => {
    queryClient.invalidateQueries(['projects'])
  }
})
```

## 4. 关键流程

### 4.1 测试执行流程

```
用户点击"运行测试"
    ↓
前端发送POST /api/v1/executions
    ↓
Backend创建TestExecution记录
    ↓
将任务推入RQ队列
    ↓
返回execution_id给前端
    ↓
Worker拾取任务
    ↓
调用ExecutorFactory.get_executor()
    ↓
执行器执行测试
    ↓
保存TestResult
    ↓
更新TestExecution状态
    ↓
前端轮询/WebSocket获取状态
    ↓
显示结果
```

### 4.2 Test IR编辑流程

```
用户进入用例编辑器
    ↓
选择测试类型（UI/Unit/Integration/Static）
    ↓
加载对应IR Schema
    ↓
提供YAML/JSON双模式编辑
    ↓
实时Schema验证（AJV）
    ↓
保存前后端二次验证（Pydantic）
    ↓
存储到数据库（JSONB字段）
```

### 4.3 覆盖率收集流程

```
测试执行
    ↓
执行器注入覆盖率收集器
    ↓
运行目标代码
    ↓
收集覆盖率数据
    ↓
生成覆盖率报告（HTML/JSON）
    ↓
存储到Artifact Storage
    ↓
写入TestResult的coverage_data字段
    ↓
前端解析展示
```

## 5. 可扩展性设计

### 5.1 添加新执行器

1. 继承`BaseExecutor`
2. 实现`execute()`和`validate_ir()`
3. 在`ExecutorFactory`注册
4. 无需修改其他代码

### 5.2 添加新测试类型

1. 在`test_ir/schemas.py`定义新IR
2. 创建对应执行器
3. 更新前端类型定义
4. 添加编辑器模板

### 5.3 水平扩展

- **Worker扩展**：增加Worker进程数
- **数据库分片**：按项目分片
- **缓存层**：添加Redis缓存
- **负载均衡**：Nginx反向代理多个Backend实例

## 6. 安全性设计

### 6.1 认证与授权

- JWT Token认证
- RBAC角色权限控制
- API速率限制

### 6.2 数据安全

- SQL注入防护（ORM参数化）
- XSS防护（React自动转义）
- CSRF Token
- HTTPS传输加密

### 6.3 执行器隔离

- 容器化执行（Docker）
- 资源限制（CPU/内存）
- 超时控制
- 沙箱环境

## 7. 性能优化

### 7.1 数据库优化

- 索引优化（project_id, test_type等）
- 查询优化（JOIN减少）
- 连接池配置
- 定期vacuum

### 7.2 API优化

- 分页查询
- 字段选择（只返回必要字段）
- 缓存策略（Redis）
- 异步处理

### 7.3 前端优化

- 代码分割（React.lazy）
- 虚拟滚动（长列表）
- 图片懒加载
- CDN加速

## 8. 监控与运维

### 8.1 日志系统

- 结构化日志（JSON格式）
- 分级日志（DEBUG/INFO/WARNING/ERROR）
- 日志聚合（ELK Stack）
- 错误追踪（Sentry）

### 8.2 监控指标

- 应用指标（QPS、响应时间）
- 系统指标（CPU、内存、磁盘）
- 业务指标（测试通过率、执行时长）
- 告警配置（Prometheus + Alertmanager）

### 8.3 备份策略

- 数据库定期备份
- Artifact增量备份
- 配置文件版本控制
- 灾难恢复演练

## 9. 技术债务

### 当前限制

1. Worker暂未实现分布式调度
2. 缺少实时WebSocket推送
3. 图数据库集成待完善
4. 缺少权限系统
5. 测试覆盖率不足

### 未来规划

1. 集成更多执行器（Selenium, Playwright等）
2. AI辅助用例生成
3. 测试数据管理
4. 多租户支持
5. CI/CD集成优化

## 10. 参考资料

- FastAPI文档: https://fastapi.tiangolo.com/
- React文档: https://react.dev/
- RQ文档: https://python-rq.org/
- Neo4j文档: https://neo4j.com/docs/

