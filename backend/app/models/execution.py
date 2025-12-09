from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class ExecutionStatus(str, enum.Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class TestExecution(Base):
    """测试执行记录模型"""
    __tablename__ = "test_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"))
    
    # 执行信息
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    executor_type = Column(String)  # spix, utbot, static_analyzer
    
    # 时间信息
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration = Column(Float)  # 秒
    
    # 结果数据
    result = Column(JSON)  # 执行结果详情
    logs = Column(Text)  # 执行日志
    error_message = Column(Text)  # 错误信息
    
    # 覆盖率
    coverage_data = Column(JSON)  # 覆盖率数据
    coverage_percentage = Column(Float)
    
    # 截图和artifact
    artifacts = Column(JSON)  # [{type: "screenshot", path: "..."}]
    
    # 环境信息
    environment = Column(JSON)  # 执行环境配置
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    project = relationship("Project", back_populates="executions")
    test_case = relationship("TestCase", back_populates="executions")

