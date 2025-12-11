"""
内存调试执行器 - Dr. Memory适配器
用于检测内存泄漏、未初始化内存访问、无效内存访问等问题
"""
from typing import Dict, Any, Optional, List
from app.executors.base_executor import BaseExecutor
from app.core.config import settings
import asyncio
import subprocess
import os
import shutil
import json
import re
from pathlib import Path


class MemoryExecutor(BaseExecutor):
    """内存调试执行器（Dr. Memory）"""
    
    def __init__(self):
        self.drmemory_path = Path(settings.DRMEMORY_PATH).resolve() if settings.DRMEMORY_PATH else None
        self.drmemory_executable = self._find_drmemory_executable()
    
    def _find_drmemory_executable(self) -> Optional[str]:
        """查找Dr. Memory可执行文件"""
        if settings.DRMEMORY_EXECUTABLE:
            exe_path = Path(settings.DRMEMORY_EXECUTABLE)
            if exe_path.exists():
                return str(exe_path)
            
            # 尝试在配置路径下查找
            if self.drmemory_path:
                exe_path = self.drmemory_path / settings.DRMEMORY_EXECUTABLE
                if exe_path.exists():
                    return str(exe_path)
        
        # 检查常见位置
        if self.drmemory_path:
            common_paths = [
                self.drmemory_path / "bin" / "drmemory.exe",
                self.drmemory_path / "drmemory.exe",
                self.drmemory_path / "bin" / "drmemory",
                self.drmemory_path / "drmemory",
            ]
            for path in common_paths:
                if path.exists():
                    return str(path)
        
        # 从系统PATH查找
        drmemory_exe = shutil.which("drmemory") or shutil.which("drmemory.exe")
        return drmemory_exe if drmemory_exe else None
    
    async def execute(self, test_ir: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """执行内存调试"""
        if not await self.validate_ir(test_ir):
            return self._create_result(
                passed=False,
                error_message="Invalid Test IR format"
            )
        
        try:
            logs = []
            logs.append("=== Dr. Memory 内存调试 ===\n")
            
            # 获取项目配置
            project_path = config.get("project_path", ".")
            binary_path = config.get("binary_path")
            source_path = config.get("source_path", project_path)
            
            if not binary_path:
                return self._create_result(
                    passed=False,
                    error_message="未指定二进制文件路径",
                    logs="\n".join(logs)
                )
            
            # 检查二进制文件是否存在
            if not os.path.exists(binary_path):
                return self._create_result(
                    passed=False,
                    error_message=f"二进制文件不存在: {binary_path}",
                    logs="\n".join(logs)
                )
            
            # 1. 使用Dr. Memory运行程序
            memory_issues = await self._run_drmemory(
                test_ir, binary_path, source_path, config, logs
            )
            
            # 2. 解析Dr. Memory报告
            parsed_issues = self._parse_drmemory_output(memory_issues, logs)
            
            # 3. 生成报告文件
            report_path = await self._generate_report(
                parsed_issues, project_path, logs
            )
            
            # 判断是否通过（没有错误级别的内存问题）
            passed = len([i for i in parsed_issues if i.get("severity") == "error"]) == 0
            
            # 构建日志
            log_text = "\n".join(logs)
            
            # 准备artifacts
            artifacts = []
            if report_path:
                artifacts.append({"type": "memory_report", "path": report_path})
            
            # 构建详细结果
            result_data = {
                "issues": parsed_issues,
                "total_issues": len(parsed_issues),
                "error_count": len([i for i in parsed_issues if i.get("severity") == "error"]),
                "warning_count": len([i for i in parsed_issues if i.get("severity") == "warning"]),
                "info_count": len([i for i in parsed_issues if i.get("severity") == "info"]),
            }
            
            return self._create_result(
                passed=passed,
                logs=log_text,
                error_message=None if passed else f"发现 {result_data['error_count']} 个内存错误",
                artifacts=artifacts
            )
            
        except Exception as e:
            error_msg = str(e)
            return self._create_result(
                passed=False,
                logs=f"执行失败: {error_msg}\n" + "\n".join(logs) if 'logs' in locals() else error_msg,
                error_message=error_msg
            )
    
    async def _run_drmemory(
        self, test_ir: Dict[str, Any], binary_path: str,
        source_path: str, config: Dict[str, Any], logs: list
    ) -> str:
        """使用Dr. Memory运行程序"""
        if not self.drmemory_executable:
            logs.append("⚠️  Dr. Memory未找到，使用模拟内存检查")
            return self._generate_mock_output()
        
        logs.append(f"🔍 使用Dr. Memory分析: {self.drmemory_executable}")
        logs.append(f"   目标程序: {binary_path}")
        
        try:
            # 构建Dr. Memory命令
            # Dr. Memory基本用法: drmemory.exe -- <program> [args]
            cmd = [
                self.drmemory_executable,
                "--",  # 分隔符，后面的参数传递给目标程序
                binary_path
            ]
            
            # 添加程序参数（如果有）
            program_args = test_ir.get("program_args", [])
            if program_args:
                cmd.extend(program_args)
            
            # 设置工作目录
            work_dir = os.path.dirname(binary_path) or source_path
            
            # 执行Dr. Memory
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir
            )
            
            stdout, stderr = await process.communicate()
            
            # Dr. Memory通常将输出写入stderr
            output = stderr.decode('utf-8', errors='ignore') + stdout.decode('utf-8', errors='ignore')
            
            if process.returncode == 0 or "ERROR" in output.upper() or "LEAK" in output.upper():
                logs.append("✅ Dr. Memory分析完成")
                return output
            else:
                logs.append(f"⚠️  Dr. Memory执行警告: {output[:200]}")
                return output
                
        except Exception as e:
            logs.append(f"⚠️  Dr. Memory执行异常: {str(e)}")
            return self._generate_mock_output()
    
    def _parse_drmemory_output(self, output: str, logs: list) -> List[Dict[str, Any]]:
        """解析Dr. Memory输出，提取内存问题"""
        issues = []
        
        if not output or "Dr. Memory" not in output:
            logs.append("⚠️  无法解析Dr. Memory输出，使用模拟数据")
            return self._generate_mock_issues()
        
        logs.append("📋 解析内存问题...")
        
        try:
            # Dr. Memory输出格式示例:
            # Error #1: UNADDRESSABLE ACCESS
            #   # 0 replace_malloc                    [d:\drmemory\...]
            #   # 1 main                              [test.cpp:42]
            #
            # Error #2: LEAK 20 bytes
            #   # 0 replace_malloc                    [d:\drmemory\...]
            #   # 1 main                              [test.cpp:45]
            
            current_issue = None
            stack_trace = []
            
            for line in output.split('\n'):
                line = line.strip()
                
                # 检测新的错误
                if line.startswith("Error #") or line.startswith("Warning #"):
                    # 保存上一个问题
                    if current_issue:
                        current_issue["stack_trace"] = stack_trace
                        issues.append(current_issue)
                    
                    # 解析错误类型
                    error_match = re.search(r'Error #(\d+):\s*(.+)', line)
                    if error_match:
                        error_num = error_match.group(1)
                        error_type = error_match.group(2).strip()
                        
                        # 确定严重程度
                        severity = "error"
                        if "LEAK" in error_type.upper():
                            issue_type = "memory_leak"
                        elif "UNADDRESSABLE" in error_type.upper():
                            issue_type = "invalid_access"
                        elif "UNINITIALIZED" in error_type.upper():
                            issue_type = "uninitialized_read"
                        else:
                            issue_type = "unknown"
                        
                        current_issue = {
                            "id": error_num,
                            "type": issue_type,
                            "severity": severity,
                            "message": error_type,
                            "stack_trace": []
                        }
                        stack_trace = []
                
                # 解析堆栈跟踪
                elif line.startswith("#") and current_issue:
                    stack_match = re.search(r'#\s*(\d+)\s+(\S+)\s+\[(.+)\]', line)
                    if stack_match:
                        frame_num = stack_match.group(1)
                        function = stack_match.group(2)
                        location = stack_match.group(3)
                        
                        # 解析文件位置
                        file_match = re.search(r'(.+):(\d+)', location)
                        if file_match:
                            file_path = file_match.group(1)
                            line_num = int(file_match.group(2))
                        else:
                            file_path = location
                            line_num = None
                        
                        stack_trace.append({
                            "frame": int(frame_num),
                            "function": function,
                            "file": file_path,
                            "line": line_num
                        })
            
            # 保存最后一个问题
            if current_issue:
                current_issue["stack_trace"] = stack_trace
                issues.append(current_issue)
            
            logs.append(f"   发现 {len(issues)} 个内存问题")
            
            # 如果没有解析到问题，使用模拟数据
            if len(issues) == 0:
                logs.append("   未发现内存问题（或输出格式不匹配）")
                return []
            
            return issues
            
        except Exception as e:
            logs.append(f"⚠️  解析异常: {str(e)}")
            return self._generate_mock_issues()
    
    def _generate_mock_output(self) -> str:
        """生成模拟的Dr. Memory输出"""
        return """Dr. Memory version 2.x
Error #1: LEAK 20 bytes
  # 0 replace_malloc                    [d:\\drmemory\\...]
  # 1 main                              [test.cpp:45]

Error #2: UNADDRESSABLE ACCESS
  # 0 replace_malloc                    [d:\\drmemory\\...]
  # 1 main                              [test.cpp:42]
"""
    
    def _generate_mock_issues(self) -> List[Dict[str, Any]]:
        """生成模拟的内存问题"""
        return [
            {
                "id": "1",
                "type": "memory_leak",
                "severity": "error",
                "message": "LEAK 20 bytes",
                "stack_trace": [
                    {
                        "frame": 0,
                        "function": "replace_malloc",
                        "file": "d:\\drmemory\\...",
                        "line": None
                    },
                    {
                        "frame": 1,
                        "function": "main",
                        "file": "test.cpp",
                        "line": 45
                    }
                ]
            },
            {
                "id": "2",
                "type": "invalid_access",
                "severity": "error",
                "message": "UNADDRESSABLE ACCESS",
                "stack_trace": [
                    {
                        "frame": 0,
                        "function": "replace_malloc",
                        "file": "d:\\drmemory\\...",
                        "line": None
                    },
                    {
                        "frame": 1,
                        "function": "main",
                        "file": "test.cpp",
                        "line": 42
                    }
                ]
            }
        ]
    
    async def _generate_report(
        self, issues: List[Dict[str, Any]], project_path: str, logs: list
    ) -> Optional[str]:
        """生成内存调试报告文件"""
        try:
            # 创建artifacts目录
            artifacts_dir = os.path.join(project_path, "artifacts", "memory_reports")
            os.makedirs(artifacts_dir, exist_ok=True)
            
            # 生成JSON报告
            import time
            report_file = os.path.join(
                artifacts_dir,
                f"memory_report_{int(time.time())}.json"
            )
            
            report_data = {
                "timestamp": time.time(),
                "total_issues": len(issues),
                "error_count": len([i for i in issues if i.get("severity") == "error"]),
                "warning_count": len([i for i in issues if i.get("severity") == "warning"]),
                "issues": issues
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logs.append(f"📄 报告已保存: {report_file}")
            return report_file
            
        except Exception as e:
            logs.append(f"⚠️  报告生成失败: {str(e)}")
            return None
    
    async def validate_ir(self, test_ir: Dict[str, Any]) -> bool:
        """验证Memory Debug IR"""
        # 支持两种格式
        if test_ir.get("type") == "memory":
            return "name" in test_ir
        else:
            return test_ir.get("test_type") == "memory" and "name" in test_ir

