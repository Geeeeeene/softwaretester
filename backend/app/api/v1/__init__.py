"""API v1路由"""
from fastapi import APIRouter

from app.api.v1.endpoints import projects, test_cases, executions, upload, tools, static_analysis, ui_test

api_router = APIRouter()

# 注册子路由
api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["projects"]
)

api_router.include_router(
    test_cases.router,
    prefix="/test-cases",
    tags=["test-cases"]
)

api_router.include_router(
    executions.router,
    prefix="/executions",
    tags=["executions"]
)

api_router.include_router(
    upload.router,
    prefix="/upload",
    tags=["upload"]
)

api_router.include_router(
    tools.router,
    prefix="/tools",
    tags=["tools"]
)

api_router.include_router(
    static_analysis.router,
    prefix="",
    tags=["static-analysis"]
)

api_router.include_router(
    ui_test.router,
    tags=["ui-test"]
)
