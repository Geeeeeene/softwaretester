"""测试执行模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class TestExecution(Base):
    """测试执行表"""
    __tablename__ = "test_executions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # 执行器类型：spix, utbot, static_analyzer
    executor_type = Column(String(50), nullable=False)
    
    # 状态：pending, running, completed, failed, cancelled
    status = Column(String(20), nullable=False, default="pending", index=True)
    
    # RQ任务ID
    task_id = Column(String(100), nullable=True, index=True)
    
    # 执行统计
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    
    # 执行时间
    duration_seconds = Column(Float, nullable=True)
    
    # 错误信息
    error_message = Column(String(1000), nullable=True)
    
    # 元数据（不能使用metadata，它是SQLAlchemy保留字）
    extra_data = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    project = relationship("Project", back_populates="test_executions")
    test_results = relationship("TestResult", back_populates="execution", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestExecution(id={self.id}, executor='{self.executor_type}', status='{self.status}')>"

