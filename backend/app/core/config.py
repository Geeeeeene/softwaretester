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
    UPLOAD_DIR: str = "./projects"  # 项目源代码上传目录
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    
    # 工具路径配置
    TOOLS_BASE_PATH: str = "backend/tools"  # 工具基础路径（相对于项目根目录）
    
    # Spix 配置
    SPIX_PATH: str = f"{TOOLS_BASE_PATH}/spix/spix"
    SPIX_BUILD_PATH: str = f"{TOOLS_BASE_PATH}/spix/spix/build"
    SPIX_EXECUTOR_PATH: str = f"{TOOLS_BASE_PATH}/spix/spix"
    
    # UTBotCpp 配置
    UTBOT_PATH: str = f"{TOOLS_BASE_PATH}/utbot/UTBotCpp"
    UTBOT_EXECUTABLE: str = ""  # 编译后的可执行文件路径，从系统PATH查找或指定
    UTBOT_EXECUTOR_PATH: str = f"{TOOLS_BASE_PATH}/utbot/UTBotCpp"
    
    # Clazy 配置
    CLAZY_PATH: str = f"{TOOLS_BASE_PATH}/clazy/clazy"
    CLAZY_EXECUTABLE: str = "clazy-standalone"  # 系统路径或工具路径
    
    # Cppcheck 配置
    CPPCHECK_PATH: str = f"{TOOLS_BASE_PATH}/cppcheck/cppcheck"
    CPPCHECK_EXECUTABLE: str = "cppcheck"  # 系统路径或工具路径
    
    # 代码覆盖率配置
    GCOV_PATH: str = ""  # 从系统 PATH 查找，或指定路径（如: "C:/MinGW/bin/gcov.exe"）
    LCOV_PATH: str = ""  # 从系统 PATH 查找，或指定路径（如: "C:/Program Files/lcov/bin/lcov.exe"）
    GENHTML_PATH: str = ""  # genhtml路径（通常与lcov在同一目录）
    
    # 内存调试配置（Windows 使用 Dr. Memory）
    VALGRIND_PATH: str = ""  # Windows 不支持原生 Valgrind
    DRMEMORY_PATH: str = f"{TOOLS_BASE_PATH}/drmemory"  # Dr. Memory安装目录
    DRMEMORY_EXECUTABLE: str = "drmemory.exe"  # 可执行文件名，完整路径或系统PATH中的名称
    
    # GammaRay 配置
    GAMMARAY_PATH: str = f"{TOOLS_BASE_PATH}/gammaray/GammaRay"
    GAMMARAY_EXECUTABLE: str = ""  # 编译后的可执行文件路径
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建配置实例
settings = Settings()
