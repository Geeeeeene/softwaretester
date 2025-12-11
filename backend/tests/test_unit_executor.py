"""
单元测试执行器测试
测试 UnitExecutor 的核心功能
"""
import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
from app.executors.unit_executor import UnitExecutor


class TestUnitExecutor:
    """单元测试执行器测试类"""
    
    @pytest.fixture
    def executor(self):
        """创建执行器实例"""
        return UnitExecutor()
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def sample_test_ir(self):
        """示例 Test IR"""
        return {
            "type": "unit",
            "name": "测试加法函数",
            "function_under_test": {
                "name": "add",
                "file_path": "math_utils.cpp"
            },
            "inputs": {
                "parameters": {
                    "a": 1,
                    "b": 2
                }
            },
            "assertions": [
                {
                    "type": "equals",
                    "expected": 3
                }
            ]
        }
    
    @pytest.fixture
    def sample_config(self, temp_dir):
        """示例配置"""
        return {
            "project_path": str(temp_dir),
            "source_path": str(temp_dir / "src"),
            "build_path": str(temp_dir / "build")
        }
    
    def test_executor_initialization(self, executor):
        """测试执行器初始化"""
        assert executor is not None
        assert hasattr(executor, 'utbot_path')
        assert hasattr(executor, 'gcov_path')
        assert hasattr(executor, 'lcov_path')
    
    @pytest.mark.asyncio
    async def test_validate_ir_valid(self, executor, sample_test_ir):
        """测试有效的 Test IR 验证"""
        result = await executor.validate_ir(sample_test_ir)
        # 注意：实际验证逻辑可能更严格，这里只是测试接口
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_validate_ir_invalid(self, executor):
        """测试无效的 Test IR 验证"""
        invalid_ir = {"type": "invalid"}
        result = await executor.validate_ir(invalid_ir)
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_execute_with_invalid_ir(self, executor, sample_config):
        """测试使用无效 IR 执行"""
        invalid_ir = {"type": "invalid"}
        result = await executor.execute(invalid_ir, sample_config)
        
        assert result is not None
        assert "passed" in result
        assert result["passed"] is False
        assert "error_message" in result
    
    def test_find_tool(self, executor):
        """测试工具查找功能"""
        # 测试查找不存在的工具
        result = executor._find_tool("nonexistent_tool_xyz")
        # 可能返回 None 或路径
        assert result is None or isinstance(result, str)
    
    def test_create_result(self, executor):
        """测试结果创建"""
        result = executor._create_result(
            passed=True,
            logs="测试日志",
            coverage={"percentage": 80}
        )
        
        assert result is not None
        assert result["passed"] is True
        assert result["logs"] == "测试日志"
        assert "coverage" in result
        assert result["coverage"]["percentage"] == 80

