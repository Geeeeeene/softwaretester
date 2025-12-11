"""Clazy 静态分析执行器"""
import time
import os
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List
from app.executors.base import BaseExecutor
from app.core.config import settings


class ClazyExecutor(BaseExecutor):
    """Clazy Qt 静态分析执行器"""
    
    def __init__(self):
        self.name = "Clazy"
        self.clazy_path = Path(settings.CLAZY_PATH).resolve() if settings.CLAZY_PATH else None
        self.clazy_executable = settings.CLAZY_EXECUTABLE or "clazy-standalone"
        print(f"🔧 初始化 {self.name} 执行器")
        print(f"   Clazy 路径: {self.clazy_path}")
        print(f"   Clazy 可执行文件: {self.clazy_executable}")
        
        # 检查可执行文件是否可用
        self.clazy_available = self._check_executable()
        if not self.clazy_available:
            print(f"   ⚠️  警告: Clazy 不可用，请确保已安装并配置到 PATH")
    
    def _check_executable(self) -> bool:
        """检查可执行文件是否可用"""
        if not self.clazy_executable:
            return False
        # 检查系统 PATH
        return shutil.which(self.clazy_executable) is not None
    
    def validate_ir(self, test_ir: Dict[str, Any]) -> bool:
        """验证 Static Analysis IR"""
        required_fields = ["type"]
        if not all(field in test_ir for field in required_fields):
            return False
        if test_ir["type"] != "static":
            return False
        # 检查是否指定了 Clazy 工具
        tool = test_ir.get("tool", "clazy")
        return tool == "clazy"
    
    def execute(self, test_ir: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Clazy 静态分析"""
        print(f"  🔍 Clazy执行器: 开始静态分析")
        
        if not self.validate_ir(test_ir):
            return {
                "status": "error",
                "error_message": "Invalid Static Analysis IR format or wrong tool",
                "duration": 0
            }
        
        if not self.clazy_available:
            return {
                "status": "error",
                "error_message": "Clazy executable not found. Please install Clazy and ensure it's in PATH.",
                "duration": 0
            }
        
        start_time = time.time()
        duration = 0
        
        try:
            # 获取分析目标
            target_files = test_ir.get("target_files", [])
            target_directories = test_ir.get("target_directories", [])
            
            print(f"     [Debug] target_directories: {target_directories}")
            
            # 如果没有指定具体文件，但指定了目录，自动扫描 C++ 源文件
            if not target_files and target_directories:
                for directory in target_directories:
                    path = Path(directory)
                    print(f"     [Debug] Scanning directory: {path} (exists: {path.exists()})")
                    if path.exists() and path.is_dir():
                        # 查找所有 .cpp, .cxx, .cc, .c, .h, .hpp 文件
                        found_files = []
                        for ext in ['*.cpp', '*.cxx', '*.cc', '*.c', '*.h', '*.hpp']:
                            found = list(path.rglob(ext))
                            found_files.extend([str(p) for p in found])
                        
                        # 排除 build 目录和生成的文件（moc_*.cpp, qrc_*.cpp, ui_*.h 等）
                        filtered_files = []
                        exclude_patterns = ['build', 'moc_', 'qrc_', 'ui_', 'qrc_', '.qrc']
                        for file_path in found_files:
                            path_str = str(file_path)
                            # 排除 build 目录下的文件
                            if '/build/' in path_str or '\\build\\' in path_str:
                                continue
                            # 排除 Qt 生成的文件
                            if any(pattern in path_str for pattern in exclude_patterns[1:]):
                                # 但允许 .qrc 资源文件本身（不是生成的）
                                if path_str.endswith('.qrc'):
                                    continue
                                # 检查是否是生成的文件（在 build 目录外但文件名匹配模式）
                                file_name = file_path.name
                                if file_name.startswith('moc_') or file_name.startswith('qrc_') or file_name.startswith('ui_'):
                                    continue
                            filtered_files.append(path_str)
                        
                        print(f"     [Debug] Found {len(found_files)} files, filtered to {len(filtered_files)} source files")
                        target_files.extend(filtered_files)
            
            if not target_files:
                print("     [Error] No source files found")
                return {
                    "status": "error",
                    "error_message": "No source files found in target directories",
                    "duration": 0
                }
            
            print(f"     [Debug] Total target files: {len(target_files)}")
            
            # 构建 Clazy 命令
            cmd = [self.clazy_executable]
            
            # 添加检查项（clazy-standalone 使用 --checks=level1 格式）
            checks = test_ir.get("checks", ["level1"])
            if isinstance(checks, list):
                checks_str = ",".join(checks)
            else:
                checks_str = str(checks)
            cmd.append(f"--checks={checks_str}")
            
            # 检查是否存在编译命令数据库（compile_commands.json）
            # 如果存在，使用 -p 选项指定构建路径
            compile_db_found = False
            if target_directories:
                for directory in target_directories:
                    build_path = Path(directory) / "build"
                    compile_db = build_path / "compile_commands.json"
                    if compile_db.exists():
                        cmd.extend(["-p", str(build_path)])
                        print(f"     [Debug] 找到编译命令数据库: {compile_db}")
                        compile_db_found = True
                        break
                    # 也检查项目根目录
                    compile_db_root = Path(directory) / "compile_commands.json"
                    if compile_db_root.exists():
                        cmd.extend(["-p", str(directory)])
                        print(f"     [Debug] 找到编译命令数据库: {compile_db_root}")
                        compile_db_found = True
                        break
            
            # 添加排除模式（使用 --ignore-dirs）
            exclude_patterns = test_ir.get("exclude_patterns", [])
            if exclude_patterns:
                ignore_dirs = "|".join(exclude_patterns)
                cmd.extend(["--ignore-dirs", ignore_dirs])
            else:
                # 默认排除 build 目录
                cmd.extend(["--ignore-dirs", "build|Build|BUILD"])
                
            # 使用 --extra-arg 添加编译器参数
            # 添加 Qt 头文件路径（如果存在）
            qt_include_paths = [
                "/usr/include/qt5",
                "/usr/include/x86_64-linux-gnu/qt5",
                "/usr/include/qt",
                "/usr/include/x86_64-linux-gnu/qt",
            ]
            qt_found = False
            qt_include_args = []
            for qt_path in qt_include_paths:
                if Path(qt_path).exists():
                    qt_include_args = [
                        f"-I{qt_path}",
                        f"-I{qt_path}/QtCore",
                        f"-I{qt_path}/QtGui",
                        f"-I{qt_path}/QtWidgets"
                    ]
                    for arg in qt_include_args:
                        cmd.extend(["--extra-arg", arg])
                    qt_found = True
                    print(f"     [Debug] 添加 Qt 头文件路径: {qt_path}")
                    break
            
            # 添加标准 C++ 选项
            cmd.extend(["--extra-arg", "-I."])
            cmd.extend(["--extra-arg", "-std=c++17"])
            cmd.extend(["--extra-arg", "-fPIC"])  # 位置无关代码，有助于解析
            
            # 添加目标文件（确保是绝对路径）
            # 如果文件太多，可能超过命令行长度限制，需要分批处理（这里暂简化处理）
            absolute_files = []
            for file_path in target_files:
                abs_path = Path(file_path).resolve()
                if abs_path.exists():
                    absolute_files.append(str(abs_path))
                else:
                    print(f"     [Warning] 文件不存在，跳过: {file_path}")
            
            if not absolute_files:
                return {
                    "status": "error",
                    "error_message": "没有有效的源文件可以分析",
                    "duration": 0
                }
            
            # 如果没有编译数据库，为每个文件生成基本的编译命令条目
            if not compile_db_found and target_directories:
                project_dir = Path(target_directories[0])
                compile_db_path = project_dir / "compile_commands.json"
                
                if not compile_db_path.exists():
                    # 为每个源文件生成基本的编译命令条目
                    compile_commands = []
                    for file_path in absolute_files:
                        file_path_obj = Path(file_path)
                        # 获取相对于项目目录的路径
                        try:
                            rel_path = file_path_obj.relative_to(project_dir)
                        except ValueError:
                            # 如果无法计算相对路径，使用文件名
                            rel_path = Path(file_path_obj.name)
                        
                        # 构建编译命令参数
                        compile_args = ["-c", str(rel_path), "-std=c++17", "-fPIC", "-I."]
                        # 添加 Qt 包含路径（qt_include_args 已经包含 -I 前缀）
                        if qt_found and qt_include_args:
                            compile_args.extend(qt_include_args)
                        
                        # 构建完整的编译命令字符串
                        compile_cmd = "clang++ " + " ".join(compile_args)
                        
                        # 创建编译命令条目
                        compile_command = {
                            "directory": str(project_dir),
                            "command": compile_cmd,
                            "file": str(rel_path)
                        }
                        compile_commands.append(compile_command)
                    
                    # 写入 compile_commands.json
                    import json
                    compile_db_path.write_text(
                        json.dumps(compile_commands, indent=2, ensure_ascii=False),
                        encoding='utf-8'
                    )
                    print(f"     [Debug] 生成编译命令数据库: {compile_db_path} (包含 {len(compile_commands)} 个文件)")
                
                # 使用项目目录作为构建路径
                cmd.extend(["-p", str(project_dir)])
                print(f"     [Debug] 使用项目目录作为构建路径: {project_dir}")
                # 使用 --ignore-included-files 选项，只分析当前文件
                cmd.append("--ignore-included-files")
                print(f"     [Debug] 启用 --ignore-included-files 模式（忽略包含的头文件）")
            
            cmd.extend(absolute_files)
            print(f"     [Debug] 将分析 {len(absolute_files)} 个文件（已过滤无效文件）")
            
            print(f"     执行命令: {' '.join(cmd)}")
            
            # 执行 Clazy
            print(f"     [Debug] 开始执行 Clazy 命令，分析 {len(absolute_files)} 个文件...")
            
            # 设置工作目录为第一个目标目录（如果存在）
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
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # 如果编码失败，用替换字符而不是报错
                timeout=300,  # 5分钟超时
                cwd=cwd,
                env=env
            )
            
            # 计算执行时间
            duration = time.time() - start_time
            print(f"     [Debug] Clazy 执行完成，耗时: {duration:.2f} 秒")
            print(f"     [Debug] 返回码: {result.returncode}")
            print(f"     [Debug] stdout 长度: {len(result.stdout)} 字符")
            print(f"     [Debug] stderr 长度: {len(result.stderr)} 字符")
            
            # 合并标准输出和错误输出（Clazy 通常输出到 stderr）
            output = result.stdout + result.stderr
            
            # 检查是否是命令错误（不是编译错误）
            # Clazy 返回码 2 通常表示有编译错误，这是正常的分析结果
            # 只有当输出包含真正的命令错误时才视为执行失败
            if result.returncode != 0:
                command_error_keywords = [
                    "Unknown command line argument",
                    "Try: 'clazy-standalone --help'",
                    "Error while trying to load a compilation database",
                    "Could not auto-detect compilation database"
                ]
                # 检查是否是命令错误（而不是编译错误）
                is_command_error = any(keyword in output for keyword in command_error_keywords)
                
                # 如果输出中有文件路径和行号，说明是编译错误，不是命令错误
                has_compile_errors = any(
                    ':' in line and 
                    (line.split(':')[0].replace('/', '').replace('\\', '').replace('.', '').isalnum() or 
                     '/' in line.split(':')[0] or '\\' in line.split(':')[0])
                    for line in output.split('\n')[:10]  # 只检查前10行
                )
                
                if is_command_error and not has_compile_errors:
                    print(f"     [Error] Clazy 命令执行失败:")
                    print(f"     {'='*60}")
                    print(output[:1000])
                    print(f"     {'='*60}")
                    duration = time.time() - start_time
                    return {
                        "status": "error",
                        "duration": duration,
                        "error_message": f"Clazy 执行失败: {output[:200]}",
                        "metadata": {
                            "executor": "clazy",
                            "command": " ".join(cmd),
                            "return_code": result.returncode,
                            "stdout": result.stdout,
                            "stderr": result.stderr
                        }
                    }
                else:
                    # 返回码非 0 但有编译错误，这是正常的分析结果
                    print(f"     [Debug] Clazy 返回码 {result.returncode}，但检测到编译错误，继续解析...")
            
            # 如果没有任何输出，可能是命令格式错误或文件路径问题
            if not output.strip():
                print(f"     [Warning] Clazy 没有产生任何输出！")
                print(f"     [Warning] 这可能表示：")
                print(f"     [Warning]   1. 命令格式错误")
                print(f"     [Warning]   2. 文件路径不存在")
                print(f"     [Warning]   3. Clazy 无法解析文件")
            else:
                # 提取处理进度信息（[1/23] Processing file ...）
                import re
                progress_lines = []
                for line in output.split('\n'):
                    if re.search(r'\[\d+/\d+\]\s+Processing file', line):
                        progress_lines.append(line.strip())
                
                if progress_lines:
                    print(f"     [Debug] 文件处理进度:")
                    for progress_line in progress_lines:
                        # 提取文件名
                        if 'Processing file' in progress_line:
                            file_part = progress_line.split('Processing file')[-1].strip()
                            print(f"     [Debug]   {progress_line.split('Processing')[0].strip()} - {file_part}")
                    print(f"     [Debug] 共处理 {len(progress_lines)} 个文件")
                else:
                    # 如果没有进度信息，打印前几行输出
                    output_lines = output.split('\n')
                    print(f"     [Debug] 输出预览（前 20 行）:")
                    print(f"     {'='*60}")
                    for line in output_lines[:20]:
                        if line.strip():
                            print(f"     {line}")
                    if len(output_lines) > 20:
                        print(f"     ... (共 {len(output_lines)} 行，仅显示前 20 行)")
                    print(f"     {'='*60}")
            
            issues = self._parse_output(output)
            print(f"     [Debug] 解析到 {len(issues)} 个问题")
            
            # 判断是否通过（根据规则中的严重程度）
            rules = test_ir.get("rules", [])
            passed = self._evaluate_results(issues, rules)
            
            # 生成日志路径
            log_path = f"/artifacts/logs/clazy_{int(time.time())}.log"
            
            return {
                "status": "passed" if passed else "failed",
                "duration": duration,
                "log_path": log_path,
                "error_message": None if passed else f"Found {len(issues)} issues",
                "metadata": {
                    "executor": "clazy",
                    "command": " ".join(cmd),
                    "return_code": result.returncode,
                    "issues_found": len(issues),
                    "issues": issues,
                    "checks_used": checks_str,
                    "files_analyzed": len(target_files),
                    "directories_analyzed": len(target_directories),
                    "stdout_preview": result.stdout[:500] if result.stdout else "",
                    "stderr_preview": result.stderr[:500] if result.stderr else ""
                }
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                "status": "error",
                "duration": duration,
                "error_message": "Clazy analysis timed out after 5 minutes",
                "metadata": {"executor": "clazy"}
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "status": "error",
                "duration": duration,
                "error_message": f"Clazy execution failed: {str(e)}",
                "metadata": {"executor": "clazy"}
            }
    
    def _parse_output(self, output: str) -> List[Dict[str, Any]]:
        """解析 Clazy 输出，提取问题信息
        
        Clazy 输出格式示例:
        /path/to/file.cpp:42:5: warning: Use QString::append() instead of operator<< [clazy-qstring-arg]
        
        也支持 Clang 编译错误格式:
        /path/to/file.cpp:11:13: error: use of overloaded operator '<<' is ambiguous
        """
        issues = []
        lines = output.split('\n')
        
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
            file_path_normalized = file_path.replace('\\', '/')
            return any(file_path_normalized.startswith(sys_path) for sys_path in system_paths)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 跳过注释行和 note 行（这些是辅助信息）
            if line.startswith('note:') or line.startswith('Note:'):
                continue
            
            # 跳过处理进度信息
            if line.startswith('[') and 'Processing file' in line:
                continue
            
            # 跳过 "In file included from" 行
            if line.startswith('In file included from'):
                continue
            
            # 尝试解析格式: file:line:column: severity: message [check-name]
            # 或者: file:line:column: error/warning: message
            parts = line.split(':')
            if len(parts) >= 4:
                try:
                    file_path = parts[0]
                    # 检查文件路径是否有效（包含 / 或 \）
                    if '/' not in file_path and '\\' not in file_path:
                        continue
                    
                    # 过滤系统库文件的问题
                    if is_system_file(file_path):
                        continue
                    
                    line_num = int(parts[1]) if parts[1].isdigit() else None
                    col_num = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
                    
                    # 提取严重程度和消息
                    severity = "warning"  # 默认
                    message = ""
                    check_name = ""
                    
                    if len(parts) >= 4:
                        # 第4部分开始是严重程度和消息
                        severity_part = parts[3].strip().split()[0] if parts[3] else ""
                        if severity_part in ["error", "warning", "info", "note"]:
                            severity = severity_part
                        
                        # 提取完整消息（从第3部分开始到末尾）
                        message_part = ':'.join(parts[3:]) if len(parts) > 3 else ""
                        # 移除严重程度关键词
                        for sev in ["error", "warning", "info", "note"]:
                            if message_part.startswith(sev + ":"):
                                message_part = message_part[len(sev) + 1:].strip()
                                break
                        
                        # 检查是否有 Clazy 检查名称 [clazy-xxx]
                        if '[' in message_part and ']' in message_part:
                            # 提取检查名称
                            check_start = message_part.find('[')
                            check_end = message_part.find(']', check_start)
                            if check_end > check_start:
                                check_name = message_part[check_start + 1:check_end].strip()
                                message = message_part[:check_start].strip()
                            else:
                                message = message_part.strip()
                        else:
                            message = message_part.strip()
                        
                        # 如果消息为空，跳过
                        if not message:
                            continue
                    
                    issues.append({
                        "file": file_path,
                        "line": line_num,
                        "column": col_num,
                        "severity": severity,
                        "message": message,
                        "check_name": check_name if check_name else ("clazy-compile-error" if severity == "error" else "clazy-warning"),
                        "tool": "clazy"
                    })
                except (ValueError, IndexError) as e:
                    # 如果解析失败，跳过这行（可能是其他格式的输出）
                    continue
        
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
                if rule_id in issue.get("check_name", "") or rule_id in issue.get("message", ""):
                    issue_severity = issue.get("severity", "warning")
                    # 如果问题严重程度 >= 规则要求的严重程度，则失败
                    severity_levels = {"info": 0, "warning": 1, "error": 2, "critical": 3}
                    if severity_levels.get(issue_severity, 0) >= severity_levels.get(rule_severity, 0):
                        return False
        
        return True

