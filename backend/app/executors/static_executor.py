"""
静态分析执行器
根据 Test IR 中的 tool 字段委托给具体的执行器（Clazy 或 Cppcheck）
"""
from typing import Dict, Any
from app.executors.base_executor import BaseExecutor
from app.executors.factory import ExecutorFactory
import asyncio


class StaticExecutor(BaseExecutor):
    """静态分析执行器（路由器）
    
    根据 Test IR 中的 tool 字段，委托给具体的执行器：
    - clazy -> ClazyExecutor
    - cppcheck -> CppcheckExecutor
    """
    
    async def execute(self, test_ir: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """执行静态分析"""
        if not await self.validate_ir(test_ir):
            return self._create_result(
                passed=False,
                error_message="Invalid Test IR format"
            )
        
        try:
            # 获取工具类型（默认为 cppcheck）
            tool = test_ir.get('tool', 'cppcheck')
            
            # 从工厂获取对应的执行器
            try:
                executor = ExecutorFactory.get_executor(tool)
            except ValueError:
                # 如果工具不存在，尝试使用旧的 static_analyzer
                try:
                    executor = ExecutorFactory.get_executor('static_analyzer')
                except ValueError:
                    return self._create_result(
                        passed=False,
                        error_message=f"不支持的静态分析工具: {tool}"
                    )
            
            # 执行器使用同步接口，需要在线程中运行
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            with concurrent.futures.ThreadPoolExecutor() as executor_pool:
                # 执行器是同步的，需要在线程中运行
                result = await loop.run_in_executor(
                    executor_pool,
                    executor.execute,
                    test_ir
                )
            
            # 转换结果格式（从同步格式转换为异步格式）
            return self._convert_result(result)
            
        except Exception as e:
            return self._create_result(
                passed=False,
                logs=f"分析失败: {str(e)}",
                error_message=str(e)
            )
    
    def _convert_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转换同步执行器结果格式为异步格式"""
        # 同步格式: {status, duration, log_path, error_message, metadata}
        # 异步格式: {passed, logs, error_message, coverage, artifacts, extra_data}
        
        passed = result.get('status') == 'passed'
        logs = f"执行时间: {result.get('duration', 0):.2f}秒\n"
        
        if result.get('log_path'):
            logs += f"日志路径: {result.get('log_path')}\n"
        
        metadata = result.get('metadata', {})
        if metadata.get('issues_found'):
            logs += f"发现问题数: {metadata.get('issues_found')}\n"
        
        artifacts = []
        if result.get('log_path'):
            artifacts.append({
                "type": "analysis_log",
                "path": result.get('log_path')
            })
        
        # 将 metadata 传递给 extra_data
        result_dict = self._create_result(
            passed=passed,
            logs=logs,
            error_message=result.get('error_message'),
            artifacts=artifacts
        )
        result_dict['extra_data'] = metadata
        return result_dict
    
    async def validate_ir(self, test_ir: Dict[str, Any]) -> bool:
        """验证Static Analysis IR"""
        required_fields = ['type']
        if not all(field in test_ir for field in required_fields):
            return False
        if test_ir.get('type') != 'static':
            return False
        return True
