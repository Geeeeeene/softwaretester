"""测试用例管理API"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.test_case import TestCase
from app.db.models.project import Project
from app.schemas.test_case import (
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    TestCaseListResponse
)

router = APIRouter()


@router.get("", response_model=TestCaseListResponse)
def list_test_cases(
    project_id: Optional[int] = None,
    test_type: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取测试用例列表"""
    query = db.query(TestCase)
    
    if project_id:
        query = query.filter(TestCase.project_id == project_id)
    if test_type:
        query = query.filter(TestCase.test_type == test_type)
    if priority:
        query = query.filter(TestCase.priority == priority)
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return TestCaseListResponse(total=total, items=items)


@router.get("/{test_case_id}", response_model=TestCaseResponse)
def get_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """获取测试用例详情"""
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    return test_case


@router.post("", response_model=TestCaseResponse, status_code=201)
def create_test_case(test_case_in: TestCaseCreate, db: Session = Depends(get_db)):
    """创建测试用例"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == test_case_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    test_case = TestCase(**test_case_in.model_dump())
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    return test_case


@router.put("/{test_case_id}", response_model=TestCaseResponse)
def update_test_case(
    test_case_id: int,
    test_case_in: TestCaseUpdate,
    db: Session = Depends(get_db)
):
    """更新测试用例"""
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    update_data = test_case_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(test_case, field, value)
    
    db.commit()
    db.refresh(test_case)
    return test_case


@router.delete("/{test_case_id}", status_code=204)
def delete_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """删除测试用例"""
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    db.delete(test_case)
    db.commit()
    return None

