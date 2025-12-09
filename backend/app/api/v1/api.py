from fastapi import APIRouter
from app.api.v1.endpoints import projects, testcases, executions, upload

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(testcases.router, prefix="/testcases", tags=["testcases"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])

