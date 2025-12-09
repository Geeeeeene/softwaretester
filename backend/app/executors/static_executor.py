"""
静态分析执行器
"""
from typing import Dict, Any
from app.executors.base_executor import BaseExecutor
import asyncio


class StaticExecutor(BaseExecutor):
    """静态分析执行器"""
    
    async def execute(self, test_ir: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """执行静态分析"""
        if not await self.validate_ir(test_ir):
            return self._create_result(
                passed=False,
                error_message="Invalid Test IR format"
            )
        
        try:
            logs = "静态分析执行（模拟）\n"
            logs += f"分析任务: {test_ir.get('name')}\n"
            logs += f"目标路径: {test_ir.get('target_paths')}\n"
            logs += f"规则数量: {len(test_ir.get('rules', []))}\n"
            
            # 模拟分析
            await asyncio.sleep(0.3)
            
            # 模拟发现的问题
            issues = [
                {
                    "rule_id": "null-pointer",
                    "severity": "error",
                    "file": "src/main.cpp",
                    "line": 42,
                    "message": "潜在的空指针解引用"
                },
                {
                    "rule_id": "unused-variable",
                    "severity": "warning",
                    "file": "src/utils.cpp",
                    "line": 15,
                    "message": "未使用的变量 'temp'"
                }
            ]
            
            logs += f"\n发现 {len(issues)} 个问题\n"
            for issue in issues:
                logs += f"  [{issue['severity'].upper()}] {issue['file']}:{issue['line']} - {issue['message']}\n"
            
            return self._create_result(
                passed=len([i for i in issues if i['severity'] == 'error']) == 0,
                logs=logs,
                artifacts=[
                    {"type": "analysis_report", "path": "/artifacts/static_analysis.json"}
                ]
            )
            
        except Exception as e:
            return self._create_result(
                passed=False,
                logs=f"分析失败: {str(e)}",
                error_message=str(e)
            )
    
    async def validate_ir(self, test_ir: Dict[str, Any]) -> bool:
        """验证Static Analysis IR"""
        required_fields = ['test_type', 'name', 'target_paths', 'rules']
        return all(field in test_ir for field in required_fields)

