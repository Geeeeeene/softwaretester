"""应用配置"""
from typing import List
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
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:5173",
        "http://localhost:3000"
    ]
    
    # 文件存储配置
    ARTIFACT_STORAGE_PATH: str = "./artifacts"
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建配置实例
settings = Settings()
