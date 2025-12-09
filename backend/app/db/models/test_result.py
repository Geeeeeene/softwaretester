"""测试结果模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class TestResult(Base):
    """测试结果表"""
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("test_executions.id"), nullable=False, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=True, index=True)
    
    # 结果状态：passed, failed, error, skipped
    status = Column(String(20), nullable=False, index=True)
    
    # 执行时间
    duration_seconds = Column(Float, nullable=True)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # 日志和截图
    log_path = Column(String(512), nullable=True)
    screenshot_path = Column(String(512), nullable=True)
    
    # 覆盖率数据
    coverage_data = Column(JSON, nullable=True)
    
    # 断言信息
    assertions = Column(JSON, default=list)
    
    # 是否需要人工审查
    needs_review = Column(Boolean, default=False)
    
    # 元数据（不能使用metadata，它是SQLAlchemy保留字）
    extra_data = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    execution = relationship("TestExecution", back_populates="test_results")
    test_case = relationship("TestCase", back_populates="test_results")

    def __repr__(self):
        return f"<TestResult(id={self.id}, status='{self.status}')>"

