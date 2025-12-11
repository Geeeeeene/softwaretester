"""项目模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 项目类型：ui, unit, integration, static
    project_type = Column(String(50), nullable=False, default="ui")
    
    # 源代码路径或二进制路径
    source_path = Column(String(512), nullable=True)  # 源代码目录路径
    build_path = Column(String(512), nullable=True)  # 构建输出目录路径
    binary_path = Column(String(512), nullable=True)  # 编译后的二进制文件路径
    
    # 语言和框架
    language = Column(String(50), nullable=True)  # cpp, python, java等
    framework = Column(String(100), nullable=True)  # Qt, GTK, Web等
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    test_cases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")
    test_executions = relationship("TestExecution", back_populates="project", cascade="all, delete-orphan")
    static_analyses = relationship("StaticAnalysis", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', type='{self.project_type}')>"

