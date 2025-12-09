"""执行器基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseExecutor(ABC):
    """执行器基类"""
    
    @abstractmethod
    def execute(self, test_ir: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试
        
        Args:
            test_ir: Test IR数据
            
        Returns:
            执行结果字典，包含:
            - status: 状态 (passed/failed/error/skipped)
            - duration: 执行时间（秒）
            - error_message: 错误信息（如果失败）
            - log_path: 日志文件路径
            - screenshot_path: 截图路径（UI测试）
            - metadata: 其他元数据
        """
        pass
    
    @abstractmethod
    def validate_ir(self, test_ir: Dict[str, Any]) -> bool:
        """验证Test IR格式
        
        Args:
            test_ir: Test IR数据
            
        Returns:
            是否有效
        """
        pass
    
    def cleanup(self):
        """清理资源"""
        pass

