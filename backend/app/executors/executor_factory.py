"""
执行器工厂
根据测试类型创建相应的执行器
"""
from app.models.testcase import TestType
from app.executors.base_executor import BaseExecutor
# UIExecutor已废弃，UI测试现在使用RobotFrameworkExecutor
# from app.executors.ui_executor import UIExecutor
from app.executors.unit_executor import UnitExecutor
from app.executors.static_executor import StaticExecutor
from app.executors.memory_executor import MemoryExecutor
from app.executors.robot_framework_executor import RobotFrameworkExecutor


class ExecutorFactory:
    """执行器工厂类"""
    
    _executors = {
        # UI测试项目使用Robot Framework + SikuliLibrary
        TestType.UI: RobotFrameworkExecutor,
        TestType.UNIT: UnitExecutor,
        TestType.STATIC: StaticExecutor,
        TestType.MEMORY: MemoryExecutor,
        TestType.ROBOT_FRAMEWORK: RobotFrameworkExecutor,
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

