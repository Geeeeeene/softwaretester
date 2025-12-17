"""应用配置"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    PROJECT_NAME: str = "HomemadeTester"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # 安全配置
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 数据库配置（默认使用SQLite，无需安装PostgreSQL）
    DATABASE_URL: str = "sqlite:///./homemade_tester.db"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Neo4j配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "testpassword"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # 文件存储配置
    ARTIFACT_STORAGE_PATH: str = "./artifacts"
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    UPLOAD_DIR: str = "./artifacts/uploads"
    
    # 静态分析工具配置
    CPPCHECK_PATH: Optional[str] = None  # Cppcheck安装路径（可选，为None时从PATH查找）
    CPPCHECK_EXECUTABLE: str = "cppcheck"  # Cppcheck可执行文件名
    CLAZY_PATH: Optional[str] = None  # Clazy安装路径（可选）
    CLAZY_EXECUTABLE: str = "clazy-standalone"  # Clazy可执行文件名
    
    # 大模型API配置（用于深度静态分析）
    DASHSCOPE_API_KEY: Optional[str] = None  # 通义千问API密钥（可选，不使用大模型分析时可留空）
    CLAUDE_API_KEY: Optional[str] = "sk-K8eYxw7bz3rPzQdyakgVoyL5TJ55lBDFW7asbnB7vXU6uJlL"  # Claude API密钥
    CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929"  # Claude模型名称
    CLAUDE_BASE_URL: Optional[str] = "https://work.poloapi.com"  # Claude API base URL（不含/v1后缀）
    
    # 静态分析存储配置
    STATIC_ANALYSIS_STORAGE_PATH: str = "./artifacts/static_analysis"  # 静态分析结果存储路径
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建配置实例
settings = Settings()
