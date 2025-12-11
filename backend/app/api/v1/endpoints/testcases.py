from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.db.session import get_db
from app.db.models.test_case import TestCase
from app.models.testcase import TestType
from app.db.models.project import Project
from app.schemas.testcase import (
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    TestCaseListResponse
)

router = APIRouter()


@router.post("", response_model=TestCaseResponse, status_code=201)
async def create_testcase(
    testcase_in: TestCaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建测试用例"""
    # 验证项目是否存在
    result = await db.execute(
        select(Project).where(Project.id == testcase_in.project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 创建测试用例
    testcase = TestCase(**testcase_in.model_dump())
    db.add(testcase)
    await db.commit()
    await db.refresh(testcase)
    return testcase


@router.get("", response_model=TestCaseListResponse)
async def list_testcases(
    project_id: Optional[int] = None,
    test_type: Optional[TestType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取测试用例列表"""
    query = select(TestCase)
    
    if project_id:
        query = query.where(TestCase.project_id == project_id)
    if test_type:
        query = query.where(TestCase.test_type == test_type)
    
    # 获取总数
    count_query = select(func.count()).select_from(TestCase)
    if project_id:
        count_query = count_query.where(TestCase.project_id == project_id)
    if test_type:
        count_query = count_query.where(TestCase.test_type == test_type)
    
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 获取用例列表
    query = query.offset(skip).limit(limit).order_by(TestCase.created_at.desc())
    result = await db.execute(query)
    testcases = result.scalars().all()
    
    return TestCaseListResponse(total=total, items=testcases)


@router.get("/{testcase_id}", response_model=TestCaseResponse)
async def get_testcase(
    testcase_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取测试用例详情"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == testcase_id)
    )
    testcase = result.scalar_one_or_none()
    
    if not testcase:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    return testcase


@router.patch("/{testcase_id}", response_model=TestCaseResponse)
async def update_testcase(
    testcase_id: int,
    testcase_in: TestCaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新测试用例"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == testcase_id)
    )
    testcase = result.scalar_one_or_none()
    
    if not testcase:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    update_data = testcase_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(testcase, field, value)
    
    await db.commit()
    await db.refresh(testcase)
    return testcase


@router.delete("/{testcase_id}", status_code=204)
async def delete_testcase(
    testcase_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除测试用例"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == testcase_id)
    )
    testcase = result.scalar_one_or_none()
    
    if not testcase:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    await db.delete(testcase)
    await db.commit()
    return None


@router.post("/{testcase_id}/execute")
async def execute_testcase(
    testcase_id: int,
    db: AsyncSession = Depends(get_db)
):
    """执行测试用例（异步任务）"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == testcase_id)
    )
    testcase = result.scalar_one_or_none()
    
    if not testcase:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    # TODO: 提交到任务队列
    # job = queue.enqueue('execute_test', testcase_id)
    
    return {
        "message": "测试任务已提交",
        "testcase_id": testcase_id,
        "status": "queued"
    }

