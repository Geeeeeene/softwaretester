"""FastAPI主应用入口"""
import os
import sys
import asyncio

# Windows 平台异步子进程支持修复 (必须在任何事件循环创建前设置)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


# 强制注册上传和单元测试路由（修复路由未生效问题）
from app.api.v1.endpoints import upload, unit_tests
app.include_router(unit_tests.router, prefix="/api/v1/unit-tests", tags=["unit-tests"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])

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
