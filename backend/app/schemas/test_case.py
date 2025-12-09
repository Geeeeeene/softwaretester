"""测试用例Schema"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class TestCaseBase(BaseModel):
    """测试用例基础Schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    test_type: str = Field(..., pattern="^(ui|unit|integration|static)$")
    priority: str = Field("medium", pattern="^(low|medium|high|critical)$")
    tags: List[str] = Field(default_factory=list)


class TestCaseCreate(TestCaseBase):
    """创建测试用例Schema"""
    project_id: int
    test_ir: Dict[str, Any] = Field(..., description="Test IR内容")


class TestCaseUpdate(BaseModel):
    """更新测试用例Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    test_ir: Optional[Dict[str, Any]] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    tags: Optional[List[str]] = None


class TestCaseResponse(TestCaseBase):
    """测试用例响应Schema"""
    id: int
    project_id: int
    test_ir: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TestCaseListResponse(BaseModel):
    """测试用例列表响应"""
    total: int
    items: List[TestCaseResponse]

