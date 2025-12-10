"""项目Schema"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """项目基础Schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_type: str = Field(..., pattern="^(ui|unit|integration|static)$")
    language: Optional[str] = None
    framework: Optional[str] = None


class ProjectCreate(ProjectBase):
    """创建项目Schema"""
    source_path: Optional[str] = None
    build_path: Optional[str] = None
    binary_path: Optional[str] = None


class ProjectUpdate(BaseModel):
    """更新项目Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    source_path: Optional[str] = None
    build_path: Optional[str] = None
    binary_path: Optional[str] = None


class ProjectResponse(ProjectBase):
    """项目响应Schema"""
    id: int
    source_path: Optional[str] = None
    build_path: Optional[str] = None
    binary_path: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    total: int
    items: List[ProjectResponse]
