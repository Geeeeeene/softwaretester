"""UTBot执行器适配器"""
import time
import os
import shutil
from pathlib import Path
from typing import Dict, Any
from app.executors.base import BaseExecutor
from app.core.config import settings


class UTBotAdapter(BaseExecutor):
    """UTBot单元测试执行器"""
    
    def __init__(self):
        self.name = "UTBot"
        self.utbot_path = Path(settings.UTBOT_PATH).resolve()
        self.utbot_executable = settings.UTBOT_EXECUTABLE or self._find_utbot_executable()
        print(f"🔧 初始化 {self.name} 执行器")
        print(f"   UTBot 路径: {self.utbot_path}")
        if self.utbot_executable:
            print(f"   UTBot 可执行文件: {self.utbot_executable}")
        else:
            print(f"   ⚠️  警告: 未找到 UTBot 可执行文件")
    
    def _find_utbot_executable(self) -> str:
        """查找 UTBot 可执行文件"""
        # 首先检查配置的路径
        if settings.UTBOT_EXECUTABLE:
            exe_path = Path(settings.UTBOT_EXECUTABLE)
            if exe_path.exists():
                return str(exe_path)
        
        # 检查常见位置
        common_paths = [
            self.utbot_path / "build" / "utbot",
            self.utbot_path / "build" / "utbot.exe",
            self.utbot_path / "bin" / "utbot",
            self.utbot_path / "bin" / "utbot.exe",
        ]
        
        for path in common_paths:
            if path.exists():
                return str(path)
        
        # 从系统 PATH 查找
        utbot_exe = shutil.which("utbot") or shutil.which("utbot.exe")
        if utbot_exe:
            return utbot_exe
        
        return ""
    
    def validate_ir(self, test_ir: Dict[str, Any]) -> bool:
        """验证Unit Test IR"""
        required_fields = ["type", "function_under_test", "inputs", "assertions"]
        return all(field in test_ir for field in required_fields) and test_ir["type"] == "unit"
    
    def execute(self, test_ir: Dict[str, Any]) -> Dict[str, Any]:
        """执行单元测试
        
        这里是简化的模拟实现，实际应该：
        1. 生成UTBot测试代码
        2. 编译并运行测试
        3. 收集覆盖率数据
        4. 返回结果
        """
        print(f"  🧬 UTBot执行器: 开始执行单元测试")
        
        if not self.validate_ir(test_ir):
            return {
                "status": "error",
                "error_message": "Invalid Unit Test IR format",
                "duration": 0
            }
        
        start_time = time.time()
        
        try:
            # 模拟执行单元测试
            function_name = test_ir.get("function_under_test", {}).get("name", "unknown")
            assertions = test_ir.get("assertions", [])
            
            print(f"     测试函数: {function_name}")
            print(f"     断言数量: {len(assertions)}")
            
            time.sleep(0.2)  # 模拟执行延迟
            
            duration = time.time() - start_time
            
            # 模拟成功结果
            return {
                "status": "passed",
                "duration": duration,
                "log_path": f"/artifacts/logs/utbot_{int(time.time())}.log",
                "coverage_data": {
                    "line_coverage": 0.85,
                    "branch_coverage": 0.75
                },
                "metadata": {
                    "executor": "utbot",
                    "function": function_name,
                    "assertions_count": len(assertions)
                }
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                "status": "failed",
                "duration": duration,
                "error_message": str(e),
                "metadata": {"executor": "utbot"}
            }

