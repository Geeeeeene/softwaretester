"""执行器工厂"""
from typing import Dict
from app.executors.base import BaseExecutor
from app.executors.spix_adapter import SpixAdapter
from app.executors.utbot_adapter import UTBotAdapter
from app.executors.static_analyzer import StaticAnalyzer


class ExecutorFactory:
    """执行器工厂类"""
    
    _executors: Dict[str, type] = {
        "spix": SpixAdapter,
        "utbot": UTBotAdapter,
        "static_analyzer": StaticAnalyzer,
    }
    
    @classmethod
    def get_executor(cls, executor_type: str) -> BaseExecutor:
        """获取执行器实例
        
        Args:
            executor_type: 执行器类型
            
        Returns:
            执行器实例
            
        Raises:
            ValueError: 不支持的执行器类型
        """
        executor_class = cls._executors.get(executor_type)
        
        if not executor_class:
            raise ValueError(
                f"不支持的执行器类型: {executor_type}. "
                f"支持的类型: {list(cls._executors.keys())}"
            )
        
        return executor_class()
    
    @classmethod
    def register_executor(cls, name: str, executor_class: type):
        """注册新的执行器
        
        Args:
            name: 执行器名称
            executor_class: 执行器类
        """
        if not issubclass(executor_class, BaseExecutor):
            raise TypeError(f"{executor_class} 必须继承自 BaseExecutor")
        
        cls._executors[name] = executor_class
        print(f"✅ 注册执行器: {name}")
    
    @classmethod
    def list_executors(cls) -> list:
        """列出所有可用的执行器"""
        return list(cls._executors.keys())

