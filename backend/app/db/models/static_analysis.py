"""静态分析模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class StaticAnalysis(Base):
    """静态分析记录表"""
    __tablename__ = "static_analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # 分析状态
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed
    
    # 分析配置
    language = Column(String(50), nullable=True)
    use_llm = Column(Boolean, default=True)
    
    # 结果路径（存储在文件系统中）
    results_path = Column(String(512), nullable=True)
    timestamp = Column(Integer, nullable=True)  # 时间戳，用于定位文件系统中的结果
    
    # 摘要信息（存储在数据库中，方便快速查询）
    total_files = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    project = relationship("Project", back_populates="static_analyses")

    def __repr__(self):
        return f"<StaticAnalysis(id={self.id}, project_id={self.project_id}, status='{self.status}')>"

