"""测试执行API"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.db.models.test_execution import TestExecution
from app.db.models.project import Project
from app.worker.tasks import execute_tests

router = APIRouter()


class ExecutionCreate(BaseModel):
    """执行创建Schema"""
    project_id: int
    executor_type: str
    test_case_ids: List[int] = Field(default_factory=list)


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
    
    class Config:
        from_attributes = True


from pydantic import BaseModel, Field
from typing import List


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
