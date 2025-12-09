"""
执行器基类
定义执行器的统一接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseExecutor(ABC):
    """测试执行器基类"""
    
    @abstractmethod
    async def execute(self, test_ir: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行测试
        
        Args:
            test_ir: Test IR字典
            config: 执行配置
            
        Returns:
            执行结果字典
        """
        pass
    
    @abstractmethod
    async def validate_ir(self, test_ir: Dict[str, Any]) -> bool:
        """
        验证Test IR格式
        
        Args:
            test_ir: Test IR字典
            
        Returns:
            是否有效
        """
        pass
    
    def _create_result(
        self,
        passed: bool,
        logs: str = "",
        error_message: str = None,
        coverage: Dict[str, Any] = None,
        artifacts: list = None
    ) -> Dict[str, Any]:
        """创建标准结果格式"""
        return {
            "passed": passed,
            "logs": logs,
            "error_message": error_message,
            "coverage": coverage,
            "artifacts": artifacts or []
        }

