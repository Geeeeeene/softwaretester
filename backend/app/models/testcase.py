from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class TestType(str, enum.Enum):
    """测试类型枚举"""
    UI = "ui"
    UNIT = "unit"
    INTEGRATION = "integration"
    STATIC = "static"
    PERFORMANCE = "performance"
    MEMORY = "memory"  # 内存调试


class TestPriority(str, enum.Enum):
    """优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TestCase(Base):
    """测试用例模型"""
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text)
    test_type = Column(Enum(TestType), nullable=False)
    priority = Column(Enum(TestPriority), default=TestPriority.MEDIUM)
    
    # Test IR存储
    test_ir = Column(JSON, nullable=False)  # 统一的测试中间表示
    
    # 标签和分类
    tags = Column(JSON)  # ["smoke", "regression", "api"]
    category = Column(String)
    
    # 状态
    is_enabled = Column(Integer, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    project = relationship("Project", back_populates="test_cases")
    executions = relationship("TestExecution", back_populates="test_case", cascade="all, delete-orphan")

