"""测试用例模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class TestCase(Base):
    """测试用例表"""
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 测试类型：ui, unit, integration, static
    test_type = Column(String(50), nullable=False, default="ui")
    
    # Test IR内容（JSON格式）
    test_ir = Column(JSON, nullable=False)
    
    # 优先级：low, medium, high, critical
    priority = Column(String(20), default="medium")
    
    # 标签（用于分类和筛选）
    tags = Column(JSON, default=list)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="test_cases")
    test_results = relationship("TestResult", back_populates="test_case", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestCase(id={self.id}, name='{self.name}', type='{self.test_type}')>"

