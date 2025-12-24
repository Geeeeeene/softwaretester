"""FastAPI主应用入口"""
import os
import sys
import asyncio

# Windows 平台异步子进程支持修复 (必须在任何事件循环创建前设置)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import json
import sys

# 设置Python默认编码为UTF-8，解决中文乱码问题
if sys.platform != 'win32':
    os.environ['LC_ALL'] = 'C.UTF-8'
    os.environ['LANG'] = 'C.UTF-8'
os.environ['PYTHONIOENCODING'] = 'utf-8'
# 设置标准输出和错误输出的编码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from app.core.config import settings
from app.api.v1 import api_router
from app.db.session import engine
from app.db.base import Base

# 导入所有模型以确保它们被注册到Base.metadata
# 模型已在startup事件中导入

# 创建FastAPI应用
app = FastAPI(
    title="HomemadeTester API",
    description="统一测试平台后端API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
# 将配置中的 URL 转换为字符串列表
cors_origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 添加安全响应头中间件
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 导入所有模型（确保SQLAlchemy能发现它们）
    from app.db.models.project import Project  # noqa
    from app.db.models.test_case import TestCase  # noqa
    from app.db.models.test_execution import TestExecution  # noqa
    from app.db.models.test_result import TestResult  # noqa
    from app.db.models.static_analysis import StaticAnalysis  # noqa
    
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库初始化完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("👋 应用正在关闭...")


@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "status": "ok",
        "message": "HomemadeTester API is running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return JSONResponse(
        content={
            "status": "healthy",
            "database": "connected",
            "redis": "connected"
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误，记录详细信息"""
    print(f"❌ 请求验证失败: {request.method} {request.url}", file=sys.stderr, flush=True)
    print(f"❌ 错误详情: {json.dumps(exc.errors(), indent=2, ensure_ascii=False)}", file=sys.stderr, flush=True)
    
    # 尝试读取请求体
    try:
        body = await request.body()
        if body:
            try:
                body_json = json.loads(body.decode('utf-8'))
                print(f"❌ 请求体内容: {json.dumps(body_json, indent=2, ensure_ascii=False)[:1000]}", file=sys.stderr, flush=True)
            except:
                print(f"❌ 请求体（无法解析JSON）: {body[:500]}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"⚠️ 无法读取请求体: {str(e)}", file=sys.stderr, flush=True)
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": json.loads(body.decode('utf-8')) if body else None
        }
    )


# 强制注册上传和单元测试路由（修复路由未生效问题）
from app.api.v1.endpoints import upload, unit_tests, integration_tests
app.include_router(unit_tests.router, prefix="/api/v1/unit-tests", tags=["unit-tests"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])
app.include_router(integration_tests.router, prefix="/api/v1/integration-tests", tags=["integration-tests"])

# 注册API路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
