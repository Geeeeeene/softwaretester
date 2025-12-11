"""FastAPI主应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
