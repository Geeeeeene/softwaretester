"""Cppcheck 静态分析执行器"""
import time
import os
import subprocess
import json
import xml.etree.ElementTree as ET
import shutil
from pathlib import Path
from typing import Dict, Any, List
from app.executors.base import BaseExecutor
from app.core.config import settings


class CppcheckExecutor(BaseExecutor):
    """Cppcheck C/C++ 静态分析执行器"""
    
    def __init__(self):
        self.name = "Cppcheck"
        self.cppcheck_path = Path(settings.CPPCHECK_PATH).resolve() if settings.CPPCHECK_PATH else None
        self.cppcheck_executable = settings.CPPCHECK_EXECUTABLE or "cppcheck"
        print(f"🔧 初始化 {self.name} 执行器")
        print(f"   Cppcheck 路径: {self.cppcheck_path}")
        print(f"   Cppcheck 可执行文件: {self.cppcheck_executable}")
        
        # 检查可执行文件是否可用
        self.cppcheck_available = self._check_executable()
        if not self.cppcheck_available:
            print(f"   ⚠️  警告: Cppcheck 不可用，请确保已安装并配置到 PATH")
    
    def _check_executable(self) -> bool:
        """检查可执行文件是否可用"""
        if not self.cppcheck_executable:
            return False
        # 检查系统 PATH
        return shutil.which(self.cppcheck_executable) is not None
    
    def validate_ir(self, test_ir: Dict[str, Any]) -> bool:
        """验证 Static Analysis IR"""
        required_fields = ["type"]
        if not all(field in test_ir for field in required_fields):
            return False
        if test_ir["type"] != "static":
            return False
        # 检查是否指定了 Cppcheck 工具
        tool = test_ir.get("tool", "cppcheck")
        return tool == "cppcheck"
    
    def execute(self, test_ir: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Cppcheck 静态分析
        
        Args:
            test_ir: Test IR 数据，包含:
                - type: "static"
                - tool: "cppcheck"
                - target_files: 要分析的文件列表
                - target_directories: 要分析的目录列表
                - rules: 分析规则列表
                - enable: 启用的检查类型（如 "all", "error", "warning", "performance", "style"）
                - exclude_patterns: 排除模式列表
                - suppress: 抑制的警告列表
                
        Returns:
            执行结果字典
        """
        print(f"  🔍 Cppcheck执行器: 开始静态分析")
        
        if not self.validate_ir(test_ir):
            return {
                "status": "error",
                "error_message": "Invalid Static Analysis IR format or wrong tool",
                "duration": 0
            }
        
        if not self.cppcheck_available:
            return {
                "status": "error",
                "error_message": "Cppcheck executable not found. Please install Cppcheck and ensure it's in PATH.",
                "duration": 0
            }
        
        start_time = time.time()
        
        try:
            # 获取分析目标
            target_files = test_ir.get("target_files", [])
            target_directories = test_ir.get("target_directories", [])
            
            print(f"     [Debug] 目标文件数: {len(target_files)}")
            print(f"     [Debug] 目标目录数: {len(target_directories)}")
            if target_files:
                print(f"     [Debug] 前3个文件: {target_files[:3]}")
            if target_directories:
                print(f"     [Debug] 目录列表: {target_directories}")
            
            # 验证文件/目录是否存在
            valid_files = []
            for file_path in target_files:
                path = Path(file_path)
                if path.exists():
                    valid_files.append(file_path)
                    print(f"     [Debug] ✓ 文件存在: {file_path}")
                else:
                    print(f"     [Warning] ✗ 文件不存在: {file_path}")
            
            valid_dirs = []
            for dir_path in target_directories:
                path = Path(dir_path)
                if path.exists() and path.is_dir():
                    valid_dirs.append(dir_path)
                    print(f"     [Debug] ✓ 目录存在: {dir_path}")
                else:
                    print(f"     [Warning] ✗ 目录不存在: {dir_path}")
            
            if not valid_files and not valid_dirs:
                return {
                    "status": "error",
                    "error_message": "No target files or directories specified",
                    "duration": 0
                }
            
            # 构建 Cppcheck 命令
            cmd = [self.cppcheck_executable]
            
            # 添加启用的检查类型（Cppcheck 使用 --enable=value 格式）
            enable = test_ir.get("enable", "all")
            if enable:
                cmd.append(f"--enable={enable}")
            
            # 添加排除模式
            exclude_patterns = test_ir.get("exclude_patterns", [])
            for pattern in exclude_patterns:
                cmd.extend(["--suppress", pattern])
            
            # 添加抑制的警告
            suppress = test_ir.get("suppress", [])
            for supp in suppress:
                cmd.extend(["--suppress", supp])
            
            # 生成 XML 输出以便解析
            xml_output = True
            if xml_output:
                cmd.append("--xml")
                cmd.append("--xml-version=2")
            
            # 添加 Qt 头文件路径（使用 -I 选项）
            qt_include_paths = [
                "/usr/include/qt5",
                "/usr/include/x86_64-linux-gnu/qt5",
                "/usr/include/qt",
                "/usr/include/x86_64-linux-gnu/qt",
            ]
            qt_found = False
            for qt_path in qt_include_paths:
                if Path(qt_path).exists():
                    cmd.append(f"-I{qt_path}")
                    cmd.append(f"-I{qt_path}/QtCore")
                    cmd.append(f"-I{qt_path}/QtGui")
                    cmd.append(f"-I{qt_path}/QtWidgets")
                    qt_found = True
                    print(f"     [Debug] 添加 Qt 头文件路径: {qt_path}")
                    break
            
            # 添加当前目录到包含路径
            if target_directories:
                first_dir = Path(target_directories[0])
                if first_dir.exists():
                    cmd.append(f"-I{first_dir}")
                    print(f"     [Debug] 添加项目目录到包含路径: {first_dir}")
            
            # 如果只有目录没有文件，需要递归扫描
            # 或者扫描目录中的源文件
            if not valid_files and valid_dirs:
                # 扫描目录中的源文件
                scanned_files = []
                for dir_path in valid_dirs:
                    dir_obj = Path(dir_path)
                    if dir_obj.exists() and dir_obj.is_dir():
                        # 查找所有 C++ 源文件
                        for ext in ['*.cpp', '*.cxx', '*.cc', '*.c', '*.h', '*.hpp']:
                            found = list(dir_obj.rglob(ext))
                            scanned_files.extend([str(p) for p in found])
                        
                        # 排除 build 目录和生成的文件
                        filtered_files = []
                        exclude_patterns = ['build', 'moc_', 'qrc_', 'ui_']
                        for file_path in scanned_files:
                            path_str = str(file_path)
                            if '/build/' in path_str or '\\build\\' in path_str:
                                continue
                            file_name = Path(file_path).name
                            if any(file_name.startswith(pattern) for pattern in exclude_patterns[1:]):
                                continue
                            filtered_files.append(file_path)
                        
                        scanned_files = filtered_files
                        print(f"     [Debug] 从目录 {dir_path} 扫描到 {len(scanned_files)} 个源文件")
                
                if scanned_files:
                    valid_files = scanned_files
                    print(f"     [Debug] 将分析 {len(valid_files)} 个源文件")
                else:
                    # 如果没有找到文件，使用递归模式分析目录
                    cmd.append("--recursive")
                    print(f"     [Debug] 未找到源文件，使用递归模式分析目录")
            
            # 添加目标文件或目录（只使用有效的文件/目录）
            all_targets = valid_files + valid_dirs
            if not all_targets:
                return {
                    "status": "error",
                    "error_message": "没有有效的文件或目录可以分析",
                    "duration": time.time() - start_time
                }
            cmd.extend(all_targets)
            print(f"     [Debug] 将分析 {len(all_targets)} 个有效目标")
            
            print(f"     执行命令: {' '.join(cmd)}")
            
            # 设置工作目录（如果指定了目录，使用第一个目录）
            cwd = None
            if target_directories:
                first_dir = Path(target_directories[0])
                if first_dir.exists() and first_dir.is_dir():
                    cwd = str(first_dir)
                    print(f"     [Debug] 工作目录: {cwd}")
            
            # 设置环境变量以支持 UTF-8 编码（解决中文乱码问题）
            env = os.environ.copy()
            env['LC_ALL'] = 'C.UTF-8'
            env['LANG'] = 'C.UTF-8'
            env['PYTHONIOENCODING'] = 'utf-8'
            
            print(f"     [Debug] 开始执行 Cppcheck，分析 {len(all_targets)} 个目标...")
            
            # 执行 Cppcheck
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # 如果编码失败，用替换字符而不是报错
                timeout=600,  # 10分钟超时
                cwd=cwd,
                env=env
            )
            
            duration = time.time() - start_time
            print(f"     [Debug] Cppcheck 执行完成，耗时: {duration:.2f} 秒")
            print(f"     [Debug] 返回码: {result.returncode}")
            print(f"     [Debug] stdout 长度: {len(result.stdout)} 字符")
            print(f"     [Debug] stderr 长度: {len(result.stderr)} 字符")
            
            # 打印实际输出内容（用于调试）
            if result.stdout:
                print(f"     [Debug] stdout 内容预览:")
                stdout_lines = result.stdout.split('\n')
                for i, line in enumerate(stdout_lines[:10]):  # 显示前10行
                    if line.strip():
                        print(f"     [Debug]   {line}")
                if len(stdout_lines) > 10:
                    print(f"     [Debug]   ... (共 {len(stdout_lines)} 行)")
            
            if result.stderr:
                print(f"     [Debug] stderr 内容预览:")
                stderr_lines = result.stderr.split('\n')
                for i, line in enumerate(stderr_lines[:10]):  # 显示前10行
                    if line.strip():
                        print(f"     [Debug]   {line}")
                if len(stderr_lines) > 10:
                    print(f"     [Debug]   ... (共 {len(stderr_lines)} 行)")
            
            # 解析输出
            # Cppcheck 的 XML 输出在 stderr 中，stdout 包含进度信息
            if xml_output:
                # 优先从 stderr 读取 XML（Cppcheck 的标准行为）
                xml_content = result.stderr if result.stderr else result.stdout
                if xml_content and xml_content.strip().startswith('<?xml'):
                    issues = self._parse_xml_output(xml_content)
                else:
                    # 如果没有有效的 XML，尝试文本解析
                    print(f"     [Warning] 未找到有效的 XML 输出，尝试文本解析")
                    issues = self._parse_text_output(result.stdout + result.stderr)
            else:
                issues = self._parse_text_output(result.stdout + result.stderr)
            
            # 判断是否通过（根据规则中的严重程度）
            rules = test_ir.get("rules", [])
            passed = self._evaluate_results(issues, rules)
            
            # 生成日志路径
            log_path = f"/artifacts/logs/cppcheck_{int(time.time())}.log"
            
            return {
                "status": "passed" if passed else "failed",
                "duration": duration,
                "log_path": log_path,
                "error_message": None if passed else f"Found {len(issues)} issues",
                "metadata": {
                    "executor": "cppcheck",
                    "command": " ".join(cmd),
                    "return_code": result.returncode,
                    "issues_found": len(issues),
                    "issues": issues,
                    "enable_used": enable,
                    "files_analyzed": len(target_files),
                    "directories_analyzed": len(target_directories)
                }
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                "status": "error",
                "duration": duration,
                "error_message": "Cppcheck analysis timed out after 10 minutes",
                "metadata": {"executor": "cppcheck"}
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "status": "error",
                "duration": duration,
                "error_message": f"Cppcheck execution failed: {str(e)}",
                "metadata": {"executor": "cppcheck"}
            }
    
    def _parse_xml_output(self, xml_output: str) -> List[Dict[str, Any]]:
        """解析 Cppcheck XML 输出"""
        issues = []
        
        # 需要过滤的信息级别警告 ID
        filtered_ids = [
            "toomanyconfigs",  # 配置太多
            "missingIncludeSystem",  # 缺少系统头文件（信息级别，不影响分析）
            "unusedFunction",  # 未使用的函数（信息级别）
            "checkersReport",  # 检查器报告
        ]
        
        # 需要过滤的消息内容（部分匹配）
        filtered_messages = [
            "This file is not analyzed",
            "failed to extract a valid configuration",
            "There was critical errors",
            "Active checkers:",
        ]
        
        # 系统库路径前缀（需要过滤掉）
        system_paths = [
            '/usr/include/',
            '/usr/lib/',
            '/usr/local/include/',
            '/usr/local/lib/',
            '/opt/',
            '/System/Library/',
            '/Library/',
        ]
        
        def is_system_file(file_path: str) -> bool:
            """检查文件是否属于系统库"""
            if not file_path or file_path == "unknown":
                return False
            file_path_normalized = file_path.replace('\\', '/')
            return any(file_path_normalized.startswith(sys_path) for sys_path in system_paths)
        
        try:
            root = ET.fromstring(xml_output)
            
            # 查找所有错误节点
            for error in root.findall('.//error'):
                error_id = error.get("id", "")
                severity = error.get("severity", "error")
                message = error.get("msg", "")
                
                # 过滤信息级别的系统警告
                if error_id in filtered_ids and severity == "information":
                    continue
                
                # 过滤特定消息内容
                if any(filtered_msg in message for filtered_msg in filtered_messages):
                    continue
                
                # 从 location 节点获取文件路径（Cppcheck XML 格式）
                location = error.find("location")
                if location is not None:
                    file_path = location.get("file", "unknown")
                    line_str = location.get("line", "0")
                    column_str = location.get("column", "0")
                else:
                    # 如果没有 location 节点，尝试从 error 属性获取
                    file_path = error.get("file", "unknown")
                    line_str = error.get("line", "0")
                    column_str = error.get("column", "0")
                
                # 过滤系统库文件的问题
                if is_system_file(file_path):
                    continue
                
                # 如果文件路径仍然是 unknown，跳过
                if file_path == "unknown" or not file_path:
                    continue
                
                # 过滤 build 目录中的文件
                file_path_normalized = file_path.replace('\\', '/')
                if '/build/' in file_path_normalized or file_path_normalized.endswith('/build'):
                    continue
                # 也检查 build 目录的各种变体
                if any(pattern in file_path_normalized.lower() for pattern in ['/build/', '/debug/', '/release/', '/minGW_', '/msvc']):
                    continue
                
                # 解析行号和列号（0 表示未知）
                line_num = int(line_str) if line_str and line_str.isdigit() and int(line_str) > 0 else None
                column_num = int(column_str) if column_str and column_str.isdigit() and int(column_str) > 0 else None
                
                # 提取消息（优先使用 msg，然后是 verbose，最后是 error_id）
                # 首先尝试从 verbose 节点获取（通常包含更详细的描述）
                verbose = error.find("verbose")
                verbose_text = verbose.text.strip() if verbose is not None and verbose.text else None
                
                # 消息提取优先级：verbose > msg > error_id > 构造消息
                if verbose_text:
                    message = verbose_text
                elif message and message.strip():
                    # msg 已经有值，使用它
                    message = message.strip()
                elif error_id:
                    # 将 error_id 转换为可读的消息
                    # 常见 error_id 的映射
                    error_id_map = {
                        "syntaxError": "Syntax error",
                        "invalidCode": "Invalid code",
                        "unusedFunction": "Unused function",
                        "missingInclude": "Missing include",
                        "toomanyconfigs": "Too many configurations",
                        "syntax": "Syntax error",
                        "code": "Code issue",
                    }
                    base_message = error_id_map.get(error_id, error_id.replace("_", " ").replace("-", " ").title())
                    message = f"{severity.title()}: {base_message}" if severity else base_message
                else:
                    # 最后的兜底：使用文件路径和行号构造描述性消息
                    file_name = Path(file_path).name if file_path else "unknown file"
                    if line_num:
                        message = f"{severity.title()}: Issue detected in {file_name} at line {line_num}" if severity else f"Issue detected in {file_name} at line {line_num}"
                    else:
                        message = f"{severity.title()}: Issue detected in {file_name}" if severity else f"Issue detected in {file_name}"
                
                # 最终确保消息不为空
                if not message or not message.strip():
                    message = f"Cppcheck found an {severity or 'unknown'} issue"
                
                issue = {
                    "file": file_path,
                    "line": line_num,
                    "column": column_num,
                    "severity": severity,
                    "id": error_id,
                    "message": message.strip() if message else "Unknown issue",
                    "tool": "cppcheck"
                }
                
                # 获取详细消息（如果 verbose 还没有被使用）
                if verbose is not None and verbose.text:
                    issue["verbose_message"] = verbose.text
                elif message and message != issue["message"]:
                    issue["verbose_message"] = message
                
                issues.append(issue)
        except ET.ParseError as e:
            print(f"   ⚠️  XML 解析错误: {e}")
            # 如果 XML 解析失败，尝试文本解析
            return self._parse_text_output(xml_output)
        
        return issues
    
    def _parse_text_output(self, output: str) -> List[Dict[str, Any]]:
        """解析 Cppcheck 文本输出
        
        Cppcheck 文本输出格式示例:
        [file.cpp:42]: (error) Array 'arr[10]' accessed at index 10, which is out of bounds.
        """
        issues = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('Checking'):
                continue
            
            # 尝试解析格式: [file:line]: (severity) message
            if '[' in line and ']' in line:
                try:
                    bracket_start = line.index('[')
                    bracket_end = line.index(']')
                    file_line = line[bracket_start + 1:bracket_end]
                    
                    if ':' in file_line:
                        file_path, line_num = file_line.rsplit(':', 1)
                        line_num = int(line_num) if line_num.isdigit() else None
                    else:
                        file_path = file_line
                        line_num = None
                    
                    # 提取严重程度和消息
                    remaining = line[bracket_end + 1:].strip()
                    if remaining.startswith('(') and ')' in remaining:
                        severity_end = remaining.index(')')
                        severity = remaining[1:severity_end]
                        message = remaining[severity_end + 1:].strip()
                    else:
                        severity = "error"
                        message = remaining
                    
                    issues.append({
                        "file": file_path,
                        "line": line_num,
                        "column": None,
                        "severity": severity,
                        "message": message,
                        "id": "unknown",
                        "tool": "cppcheck"
                    })
                except (ValueError, IndexError):
                    # 如果解析失败，至少保存原始行
                    issues.append({
                        "file": "unknown",
                        "line": None,
                        "column": None,
                        "severity": "error",
                        "message": line,
                        "id": "unknown",
                        "tool": "cppcheck"
                    })
        
        return issues
    
    def _evaluate_results(self, issues: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> bool:
        """根据规则评估结果
        
        Args:
            issues: 发现的问题列表
            rules: 规则列表，每个规则包含 rule_id 和 severity
            
        Returns:
            是否通过（没有违反规则的严重问题）
        """
        if not rules:
            # 如果没有规则，只要有 error 级别的问题就失败
            return not any(issue.get("severity") == "error" for issue in issues)
        
        # 检查是否有违反规则的问题
        for rule in rules:
            rule_id = rule.get("rule_id", "")
            rule_severity = rule.get("severity", "error")
            
            # 查找匹配的问题
            for issue in issues:
                issue_id = issue.get("id", "")
                issue_severity = issue.get("severity", "error")
                
                # 匹配规则 ID 或消息
                if rule_id in issue_id or rule_id in issue.get("message", ""):
                    # 如果问题严重程度 >= 规则要求的严重程度，则失败
                    severity_levels = {"style": 0, "performance": 1, "portability": 1, "warning": 1, "error": 2}
                    if severity_levels.get(issue_severity, 2) >= severity_levels.get(rule_severity, 2):
                        return False
        
        return True

