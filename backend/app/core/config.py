"""应用配置"""
from typing import List, Optional, Union, Any
from pydantic_settings import BaseSettings
from pydantic import field_validator
import json


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
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./homemade_tester.db"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Neo4j配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "testpassword"
    
    # CORS配置 - 使用Any类型以避免Pydantic自动JSON解析错误
    BACKEND_CORS_ORIGINS: Any = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)
    
    # 文件存储配置
    ARTIFACT_STORAGE_PATH: str = "./artifacts"
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    UPLOAD_DIR: str = "./artifacts/uploads"
    
    # 静态分析工具配置
    CPPCHECK_PATH: Optional[str] = None
    CPPCHECK_EXECUTABLE: str = "cppcheck"
    CLAZY_PATH: Optional[str] = None
    CLAZY_EXECUTABLE: str = "clazy-standalone"
    
    # AI配置
    DASHSCOPE_API_KEY: Optional[str] = None
    CLAUDE_API_KEY: Optional[str] = "sk-K8eYxw7bz3rPzQdyakgVoyL5TJ55lBDFW7asbnB7vXU6uJlL"
    CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929"
    CLAUDE_BASE_URL: Optional[str] = "https://work.poloapi.com"
    
    # 静态分析存储
    STATIC_ANALYSIS_STORAGE_PATH: str = "./artifacts/static_analysis"
    
    # Java配置
    JAVA_HOME: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# 创建配置实例
settings = Settings()
