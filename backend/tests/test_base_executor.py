"""
基础执行器测试
测试 BaseExecutor 的接口和工具方法
"""
import pytest
from app.executors.base_executor import BaseExecutor


class TestBaseExecutor:
    """基础执行器测试类"""
    
    def test_create_result_passed(self):
        """测试创建通过的结果"""
        result = BaseExecutor._create_result(
            BaseExecutor,
            passed=True,
            logs="测试通过",
            coverage={"percentage": 100}
        )
        
        assert result["passed"] is True
        assert result["logs"] == "测试通过"
        assert result["coverage"]["percentage"] == 100
        assert result["error_message"] is None
    
    def test_create_result_failed(self):
        """测试创建失败的结果"""
        result = BaseExecutor._create_result(
            BaseExecutor,
            passed=False,
            logs="测试失败",
            error_message="测试用例失败"
        )
        
        assert result["passed"] is False
        assert result["logs"] == "测试失败"
        assert result["error_message"] == "测试用例失败"
    
    def test_create_result_with_artifacts(self):
        """测试创建带 artifacts 的结果"""
        artifacts = [
            {"type": "test_code", "path": "/path/to/test.cpp"},
            {"type": "coverage_report", "path": "/path/to/report.html"}
        ]
        
        result = BaseExecutor._create_result(
            BaseExecutor,
            passed=True,
            artifacts=artifacts
        )
        
        assert result["artifacts"] == artifacts
        assert len(result["artifacts"]) == 2

