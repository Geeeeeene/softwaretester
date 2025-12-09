from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.testcase import TestType, TestPriority


class TestCaseBase(BaseModel):
    """测试用例基础模型"""
    name: str = Field(..., description="用例名称")
    description: Optional[str] = Field(None, description="用例描述")
    test_type: TestType = Field(..., description="测试类型")
    priority: Optional[TestPriority] = Field(TestPriority.MEDIUM, description="优先级")


class TestCaseCreate(TestCaseBase):
    """创建测试用例"""
    project_id: int = Field(..., description="项目ID")
    test_ir: Dict[str, Any] = Field(..., description="Test IR内容")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    category: Optional[str] = Field(None, description="分类")


class TestCaseUpdate(BaseModel):
    """更新测试用例"""
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TestPriority] = None
    test_ir: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    is_enabled: Optional[bool] = None


class TestCaseResponse(TestCaseBase):
    """测试用例响应"""
    id: int
    project_id: int
    test_ir: Dict[str, Any]
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    is_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TestCaseListResponse(BaseModel):
    """测试用例列表响应"""
    total: int
    items: List[TestCaseResponse]

