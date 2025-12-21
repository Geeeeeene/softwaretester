"""
配置测试
测试应用配置是否正确加载
"""
import pytest
from app.core.config import settings


class TestConfig:
    """配置测试类"""
    
    def test_settings_loaded(self):
        """测试配置已加载"""
        assert settings is not None
        assert hasattr(settings, 'PROJECT_NAME')
        assert hasattr(settings, 'DATABASE_URL')
    
    def test_project_name(self):
        """测试项目名称"""
        assert settings.PROJECT_NAME == "HomemadeTester"
    
    def test_database_url(self):
        """测试数据库URL"""
        assert settings.DATABASE_URL is not None
        assert isinstance(settings.DATABASE_URL, str)
    
    def test_cors_origins(self):
        """测试CORS配置"""
        assert settings.BACKEND_CORS_ORIGINS is not None
        assert isinstance(settings.BACKEND_CORS_ORIGINS, list)
        assert len(settings.BACKEND_CORS_ORIGINS) > 0
    
    def test_tools_paths(self):
        """测试工具路径配置"""
        assert hasattr(settings, 'UTBOT_PATH')
        assert hasattr(settings, 'CLAZY_PATH')
        assert hasattr(settings, 'CPPCHECK_PATH')

