from fastapi import APIRouter
from app.api.v1.endpoints import projects, testcases, executions, upload, tools, unit_tests, integration_tests

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(testcases.router, prefix="/testcases", tags=["testcases"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(unit_tests.router, prefix="/unit-tests", tags=["unit-tests"])
api_router.include_router(integration_tests.router, prefix="/integration-tests", tags=["integration-tests"])

