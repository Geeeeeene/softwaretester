"""静态分析执行器"""
import time
import os
import shutil
from pathlib import Path
from typing import Dict, Any
from app.executors.base import BaseExecutor
from app.core.config import settings


class StaticAnalyzer(BaseExecutor):
    """静态分析执行器"""
    
    def __init__(self):
        self.name = "StaticAnalyzer"
        self.clazy_path = Path(settings.CLAZY_PATH).resolve()
        self.clazy_executable = settings.CLAZY_EXECUTABLE
        self.cppcheck_path = Path(settings.CPPCHECK_PATH).resolve()
        self.cppcheck_executable = settings.CPPCHECK_EXECUTABLE
        print(f"🔧 初始化 {self.name} 执行器")
        print(f"   Clazy 路径: {self.clazy_path}")
        print(f"   Cppcheck 路径: {self.cppcheck_path}")
        
        # 检查可执行文件
        self.clazy_available = self._check_executable(self.clazy_executable)
        self.cppcheck_available = self._check_executable(self.cppcheck_executable)
        
        if not self.clazy_available:
            print(f"   ⚠️  警告: Clazy 不可用")
        if not self.cppcheck_available:
            print(f"   ⚠️  警告: Cppcheck 不可用")
    
    def _check_executable(self, executable_name: str) -> bool:
        """检查可执行文件是否可用"""
        if not executable_name:
            return False
        # 检查系统 PATH
        return shutil.which(executable_name) is not None
    
    def validate_ir(self, test_ir: Dict[str, Any]) -> bool:
        """验证Static Analysis IR"""
        required_fields = ["type", "rules"]
        return all(field in test_ir for field in required_fields) and test_ir["type"] == "static"
    
    def execute(self, test_ir: Dict[str, Any]) -> Dict[str, Any]:
        """执行静态分析
        
        这里是简化的模拟实现，实际应该：
        1. 加载分析规则
        2. 扫描源代码
        3. 生成问题报告
        4. 构建调用图/CFG
        """
        print(f"  🔍 StaticAnalyzer执行器: 开始静态分析")
        
        if not self.validate_ir(test_ir):
            return {
                "status": "error",
                "error_message": "Invalid Static Analysis IR format",
                "duration": 0
            }
        
        start_time = time.time()
        
        try:
            # 模拟静态分析
            rules = test_ir.get("rules", [])
            target_files = test_ir.get("target_files", [])
            
            print(f"     分析规则: {len(rules)}")
            print(f"     目标文件: {len(target_files)}")
            
            time.sleep(0.3)  # 模拟分析延迟
            
            duration = time.time() - start_time
            
            # 模拟分析结果
            return {
                "status": "passed",
                "duration": duration,
                "log_path": f"/artifacts/logs/static_{int(time.time())}.log",
                "metadata": {
                    "executor": "static_analyzer",
                    "rules_checked": len(rules),
                    "files_analyzed": len(target_files),
                    "issues_found": 5,  # 模拟发现的问题数
                    "severity_breakdown": {
                        "critical": 0,
                        "error": 1,
                        "warning": 3,
                        "info": 1
                    }
                }
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                "status": "failed",
                "duration": duration,
                "error_message": str(e),
                "metadata": {"executor": "static_analyzer"}
            }

