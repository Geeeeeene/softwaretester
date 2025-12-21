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
    
    # 检查名称是否重复，如果重复则自动添加编号
    import logging
    logger = logging.getLogger(__name__)
    
    base_name = test_case_in.name
    final_name = base_name
    counter = 1
    
    # 在同一项目内检查是否有重复名称
    existing_count = db.query(TestCase).filter(
        TestCase.project_id == test_case_in.project_id,
        TestCase.name == base_name
    ).count()
    
    logger.info(f"创建测试用例: project_id={test_case_in.project_id}, 原始名称='{base_name}', 已存在同名用例数={existing_count}")
    
    while db.query(TestCase).filter(
        TestCase.project_id == test_case_in.project_id,
        TestCase.name == final_name
    ).first():
        counter += 1
        final_name = f"{base_name}_{counter}"
        logger.debug(f"名称 '{base_name}' 重复，尝试 '{final_name}'")
    
    # 如果名称被修改，记录日志
    if final_name != base_name:
        logger.info(f"✅ 测试用例名称重复，自动重命名: '{base_name}' -> '{final_name}' (project_id={test_case_in.project_id})")
    else:
        logger.info(f"✅ 测试用例名称唯一，使用原始名称: '{final_name}' (project_id={test_case_in.project_id})")
    
    # 使用处理后的名称创建测试用例
    test_case_data = test_case_in.model_dump()
    test_case_data['name'] = final_name
    test_case = TestCase(**test_case_data)
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
    
    # 如果更新了名称，检查是否与其他测试用例重复
    if 'name' in update_data and update_data['name']:
        new_name = update_data['name']
        # 检查同一项目内是否有其他测试用例使用相同名称（排除自己）
        existing = db.query(TestCase).filter(
            TestCase.project_id == test_case.project_id,
            TestCase.name == new_name,
            TestCase.id != test_case_id
        ).first()
        
        if existing:
            # 如果重复，自动添加编号
            base_name = new_name
            final_name = base_name
            counter = 1
            
            while db.query(TestCase).filter(
                TestCase.project_id == test_case.project_id,
                TestCase.name == final_name,
                TestCase.id != test_case_id
            ).first():
                counter += 1
                final_name = f"{base_name}_{counter}"
            
            update_data['name'] = final_name
    
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

