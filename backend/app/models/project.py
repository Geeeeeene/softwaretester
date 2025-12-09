from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Project(Base):
    """项目模型"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    project_type = Column(String)  # ui, unit, integration, static
    language = Column(String)  # python, java, cpp, etc.
    repository_url = Column(String)
    source_path = Column(String)  # MinIO路径
    metadata = Column(JSON)  # 额外元数据
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    test_cases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")
    executions = relationship("TestExecution", back_populates="project", cascade="all, delete-orphan")

