"""
执行器工厂
根据测试类型创建相应的执行器
"""
from app.models.testcase import TestType
from app.executors.base_executor import BaseExecutor
from app.executors.ui_executor import UIExecutor
from app.executors.unit_executor import UnitExecutor
from app.executors.static_executor import StaticExecutor


class ExecutorFactory:
    """执行器工厂类"""
    
    _executors = {
        TestType.UI: UIExecutor,
        TestType.UNIT: UnitExecutor,
        TestType.STATIC: StaticExecutor,
    }
    
    @classmethod
    def get_executor(cls, test_type: TestType) -> BaseExecutor:
        """
        获取执行器实例
        
        Args:
            test_type: 测试类型
            
        Returns:
            执行器实例
            
        Raises:
            ValueError: 不支持的测试类型
        """
        executor_class = cls._executors.get(test_type)
        if not executor_class:
            raise ValueError(f"不支持的测试类型: {test_type}")
        
        return executor_class()
    
    @classmethod
    def register_executor(cls, test_type: TestType, executor_class: type):
        """注册新的执行器类型"""
        cls._executors[test_type] = executor_class

