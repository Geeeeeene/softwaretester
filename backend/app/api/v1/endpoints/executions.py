"""测试执行API"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, Field
import os
import sys

from app.db.session import get_db
from app.db.models.test_execution import TestExecution
from app.db.models.project import Project
from app.worker.tasks import execute_tests
from app.core.config import settings

# 添加tools目录到路径
tools_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "tools")
sys.path.insert(0, tools_path)

try:
    from report_generator import generate_report_zip
except ImportError:
    generate_report_zip = None

router = APIRouter()


class ExecutionCreate(BaseModel):
    """执行创建Schema"""
    project_id: int
    executor_type: str
    test_case_ids: List[int] = Field(default_factory=list)


class TestResultResponse(BaseModel):
    """测试结果Schema"""
    id: int
    test_case_id: Optional[int]
    status: str
    duration_seconds: Optional[float]
    error_message: Optional[str]
    log_path: Optional[str]
    extra_data: Optional[dict] = None
    
    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    """执行响应Schema"""
    id: int
    project_id: int
    executor_type: str
    status: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    duration_seconds: Optional[float]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    # 添加覆盖率、结果、日志和artifacts字段
    coverage_data: Optional[dict] = None
    result: Optional[dict] = None
    logs: Optional[str] = None
    artifacts: Optional[List[dict]] = None
    
    test_results: List[TestResultResponse] = []
    
    class Config:
        from_attributes = True


@router.post("", response_model=ExecutionResponse, status_code=201)
def create_execution(
    execution_in: ExecutionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建并启动测试执行"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == execution_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 创建执行记录
    execution = TestExecution(
        project_id=execution_in.project_id,
        executor_type=execution_in.executor_type,
        status="pending",
        total_tests=len(execution_in.test_case_ids)
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # 添加后台任务
    background_tasks.add_task(
        execute_tests,
        execution.id,
        execution_in.test_case_ids
    )
    
    return execution


@router.get("/{execution_id}", response_model=ExecutionResponse)
def get_execution(execution_id: int, db: Session = Depends(get_db)):
    """获取执行详情"""
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return execution


@router.get("", response_model=List[ExecutionResponse])
def list_executions(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取执行列表"""
    query = db.query(TestExecution)
    
    if project_id:
        query = query.filter(TestExecution.project_id == project_id)
    if status:
        query = query.filter(TestExecution.status == status)
    
    query = query.order_by(TestExecution.created_at.desc())
    executions = query.offset(skip).limit(limit).all()
    
    return executions


@router.get("/{execution_id}/report")
def generate_execution_report(
    execution_id: int,
    db: Session = Depends(get_db)
):
    """生成执行报告（ZIP文件）"""
    if not generate_report_zip:
        raise HTTPException(
            status_code=501,
            detail="报告生成功能不可用（report_generator模块未找到）"
        )
    
    # 获取执行记录
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    
    # 获取项目信息
    project = db.query(Project).filter(Project.id == execution.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 构建工作流数据
    workflow_data = {
        'bug_detection': {
            'bugs': execution.result.get('issues', []) if execution.result else []
        },
        'testing': {
            'test_results': [],
            'pass_rate': (
                (execution.passed_tests / execution.total_tests * 100)
                if execution.total_tests > 0
                else 0
            )
        }
    }
    
    # 如果有覆盖率数据，添加到测试结果中
    if execution.coverage_data:
        workflow_data['testing']['coverage'] = execution.coverage_data
    
    # 生成报告
    output_dir = os.path.join(settings.ARTIFACT_STORAGE_PATH, "reports")
    os.makedirs(output_dir, exist_ok=True)
    
    zip_path, download_url = generate_report_zip(
        workflow_id=f"execution_{execution_id}",
        workflow_data=workflow_data,
        output_dir=output_dir,
        project_name=project.name
    )
    
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(
            status_code=500,
            detail="报告生成失败"
        )
    
    # 返回文件
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"report_execution_{execution_id}.zip"
    )
