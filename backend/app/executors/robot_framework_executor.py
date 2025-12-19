"""
Robot Framework + SikuliLibrary 执行器
用于执行基于图像识别的系统级测试
"""
from typing import Dict, Any, Optional
from app.executors.base_executor import BaseExecutor
from app.core.config import settings
import asyncio
import subprocess
import os
import sys
from pathlib import Path
import json
import shutil


class RobotFrameworkExecutor(BaseExecutor):
    """Robot Framework + SikuliLibrary 执行器"""
    
    def __init__(self):
        """初始化执行器"""
        import sys
        
        # 优先尝试使用系统Python（因为Robot Framework可能安装在系统Python中）
        # 如果失败，再尝试使用当前Python环境
        
        # 方法1: 尝试使用系统Python的py命令（Windows）
        if sys.platform == "win32":
            python_exe = shutil.which("py")
            if python_exe:
                # 使用系统Python的py命令，添加-3参数强制使用系统Python 3
                # 这样可以避免使用虚拟环境的Python
                self.robot_executable = "py"
                self.robot_args = ["-3", "-m", "robot"]  # -3 强制使用系统Python 3
                self.use_system_python = True
            else:
                # 方法2: 尝试使用当前Python环境
                # 检查当前环境中是否有robot
                try:
                    import subprocess
                    result = subprocess.run(
                        [sys.executable, "-m", "robot", "--version"],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        # 当前环境有robot
                        self.robot_executable = sys.executable
                        self.robot_args = ["-m", "robot"]
                        self.use_system_python = False
                    else:
                        # 回退到直接使用robot命令
                        self.robot_executable = "robot"
                        self.robot_args = []
                        self.use_system_python = False
                except Exception:
                    # 回退到直接使用robot命令
                    self.robot_executable = "robot"
                    self.robot_args = []
                    self.use_system_python = False
        else:
            # Linux/Mac上先尝试当前Python环境
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, "-m", "robot", "--version"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.robot_executable = sys.executable
                    self.robot_args = ["-m", "robot"]
                    self.use_system_python = False
                else:
                    self.robot_executable = "robot"
                    self.robot_args = []
                    self.use_system_python = False
            except Exception:
                self.robot_executable = "robot"
                self.robot_args = []
                self.use_system_python = False
        
        # 确保output_dir是绝对路径（相对于backend目录）
        backend_dir = Path(__file__).parent.parent.parent  # backend目录
        self.output_dir = (backend_dir / "artifacts" / "robot_framework").resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _find_java_home(self) -> Optional[Path]:
        """
        查找Java安装路径
        
        Returns:
            Java安装路径，如果找不到则返回None
        """
        # 方法1: 从配置中读取
        if settings.JAVA_HOME:
            java_home = Path(settings.JAVA_HOME)
            if java_home.exists() and (java_home / "bin" / "java.exe").exists():
                return java_home.resolve()
        
        # 方法2: 从环境变量读取
        java_home_env = os.environ.get('JAVA_HOME')
        if java_home_env:
            java_home = Path(java_home_env)
            if java_home.exists() and (java_home / "bin" / "java.exe").exists():
                return java_home.resolve()
        
        # 方法3: 尝试常见路径（Windows）- 优先检查用户指定的路径
        if sys.platform == "win32":
            common_paths = [
                Path("D:/Downloads/java"),  # 用户指定的路径（优先）
                Path("D:\\Downloads\\java"),  # Windows路径格式
                Path("C:/Program Files/Java"),
                Path("C:/Program Files (x86)/Java"),
                Path(os.path.expanduser("~/java")),
            ]
            
            for java_path in common_paths:
                # 尝试解析路径（处理相对路径和符号链接）
                try:
                    resolved_path = java_path.resolve()
                except (OSError, RuntimeError):
                    continue
                
                if resolved_path.exists():
                    # 检查是否有bin/java.exe
                    java_exe = resolved_path / "bin" / "java.exe"
                    if java_exe.exists():
                        return resolved_path
                    
                    # 也可能java_path本身就是bin目录的父目录
                    # 检查子目录（如 jdk-21, jre-21 等）
                    try:
                        for subdir in resolved_path.iterdir():
                            if subdir.is_dir() and (subdir / "bin" / "java.exe").exists():
                                return subdir.resolve()
                    except (OSError, PermissionError):
                        continue
        
        # 方法4: 尝试从PATH中查找java.exe
        java_exe = shutil.which("java")
        if java_exe:
            java_exe_path = Path(java_exe)
            # java.exe通常在bin目录下，JAVA_HOME是bin的父目录
            if java_exe_path.parent.name == "bin":
                return java_exe_path.parent.parent.resolve()
        
        return None
    
    async def execute(self, test_ir: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Robot Framework测试
        
        Args:
            test_ir: Test IR字典，包含：
                - test_type: "robot_framework"
                - name: 测试名称
                - description: 测试描述
                - robot_script: Robot Framework脚本内容
                - resources: 资源文件路径列表（如图像文件）
                - variables: 测试变量字典
                - timeout: 超时时间（秒）
            config: 执行配置
                
        Returns:
            执行结果字典
        """
        if not await self.validate_ir(test_ir):
            return self._create_result(
                passed=False,
                error_message="Invalid Test IR format: missing required fields"
            )
        
        try:
            # 使用永久工作目录而不是临时目录
            # 因为SikuliLibrary的Java进程可能还在使用文件，临时目录清理会失败
            work_dir = self.output_dir / "work" / test_ir['name']
            work_dir.mkdir(parents=True, exist_ok=True)
            temp_path = work_dir
            
            # 1. 复制图像资源文件到工作目录
            resources_dir = temp_path / "robot_resources"
            resources_dir.mkdir(exist_ok=True)
            
            # 查找并复制examples/robot_resources目录中的图像文件
            backend_dir = Path(__file__).parent.parent.parent  # backend目录
            examples_resources = backend_dir / "examples" / "robot_resources"
            
            if examples_resources.exists():
                # 复制所有图像文件
                for image_file in examples_resources.glob("*.png"):
                    target_file = resources_dir / image_file.name
                    shutil.copy2(image_file, target_file)
                logs = f"已复制 {len(list(examples_resources.glob('*.png')))} 个图像文件到工作目录\n"
            else:
                logs = f"警告: 图像资源目录不存在: {examples_resources}\n"
            
            # 2. 修改脚本中的图像路径为工作目录中的路径
            robot_script = self._generate_robot_script(test_ir)
            # 替换脚本中的图像路径
            robot_script = robot_script.replace(
                "${IMAGE_PATH}         examples/robot_resources",
                f"${{IMAGE_PATH}}         {str(resources_dir).replace(chr(92), '/')}"  # 使用正斜杠
            )
            robot_script = robot_script.replace(
                "examples/robot_resources",
                str(resources_dir).replace(chr(92), '/')  # 使用正斜杠
            )
            
            # 3. 写入Robot Framework脚本
            robot_file = temp_path / f"{test_ir['name']}.robot"
            robot_file.write_text(robot_script, encoding='utf-8')
            
            # 4. 如果test_ir中指定了额外的资源文件，也复制它们
            if 'resources' in test_ir:
                await self._copy_resources(test_ir['resources'], resources_dir)
            
            # 5. 构建Robot Framework命令
            output_dir = (self.output_dir / test_ir['name']).resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = self._build_robot_command(
                robot_file=robot_file,
                output_dir=output_dir,
                variables=test_ir.get('variables', {}),
                timeout=test_ir.get('timeout', 300)
            )
            
            # 6. 执行Robot Framework
            logs += f"执行Robot Framework测试: {test_ir['name']}\n"
            logs += f"工作目录: {temp_path}\n"
            logs += f"图像资源目录: {resources_dir}\n"
            logs += f"Robot可执行文件: {self.robot_executable}\n"
            logs += f"完整命令: {' '.join(cmd)}\n"
            logs += f"命令参数数量: {len(cmd)}\n\n"
            
            # 检查robot命令是否可用
            robot_cmd = self.robot_executable
            if self.robot_args:
                # 如果是 py -m robot，检查 py 是否可用
                if not shutil.which(robot_cmd):
                    raise FileNotFoundError(
                        f"找不到 {robot_cmd} 命令。"
                        f"请确保Python已安装并配置到PATH，或使用 'py -m pip install robotframework' 安装Robot Framework"
                    )
            else:
                # 如果是直接使用robot命令，检查是否可用
                if not shutil.which(robot_cmd):
                    raise FileNotFoundError(
                        f"找不到 {robot_cmd} 命令。"
                        f"请确保Robot Framework已安装：'py -m pip install robotframework'"
                        f"或使用 'py -m robot' 代替"
                    )
            
            logs += f"✓ 命令检查通过，开始执行...\n\n"
            
            try:
                # 执行Robot Framework命令
                # 注意：在Windows的BackgroundTasks线程中，事件循环可能不支持异步子进程
                # 因此使用同步的subprocess.run()，通过线程执行以避免阻塞
                env = os.environ.copy()
                
                # 使用同步的subprocess.run()，在线程中执行
                def run_robot_sync():
                    nonlocal logs  # 允许修改外层的logs变量
                    
                    # 如果使用系统Python，需要清除VIRTUAL_ENV环境变量
                    # 这样py命令会使用系统Python而不是虚拟环境
                    exec_env = env.copy()
                    if self.use_system_python and 'VIRTUAL_ENV' in exec_env:
                        # 临时移除VIRTUAL_ENV，让py命令使用系统Python
                        del exec_env['VIRTUAL_ENV']
                        # 也移除相关的PATH条目
                        if 'PATH' in exec_env:
                            venv_path = env.get('VIRTUAL_ENV', '')
                            if venv_path:
                                # 移除虚拟环境的Scripts和bin目录
                                paths = exec_env['PATH'].split(os.pathsep)
                                paths = [p for p in paths if venv_path not in p]
                                exec_env['PATH'] = os.pathsep.join(paths)
                    
                    # 设置Java环境变量（SikuliLibrary需要）
                    java_home = self._find_java_home()
                    if java_home:
                        # 确保使用绝对路径
                        java_home_str = str(java_home.resolve())
                        exec_env['JAVA_HOME'] = java_home_str
                        
                        # 将Java的bin目录添加到PATH的最前面（优先使用）
                        java_bin = java_home / "bin"
                        if java_bin.exists():
                            java_bin_str = str(java_bin.resolve())
                            current_path = exec_env.get('PATH', '')
                            # 如果PATH中已经有java_bin，先移除它
                            paths = current_path.split(os.pathsep) if current_path else []
                            paths = [p for p in paths if java_bin_str.lower() != p.lower()]
                            # 将java_bin添加到最前面
                            exec_env['PATH'] = f"{java_bin_str}{os.pathsep}{os.pathsep.join(paths)}"
                            logs += f"✓ 已自动配置Java环境:\n"
                            logs += f"   JAVA_HOME: {java_home_str}\n"
                            logs += f"   Java bin: {java_bin_str}\n"
                        else:
                            logs += f"⚠️  警告: Java bin目录不存在: {java_bin}\n"
                    else:
                        logs += f"⚠️  警告: 未找到Java环境，SikuliLibrary可能无法工作\n"
                        logs += f"   查找的路径:\n"
                        logs += f"   - 配置: {settings.JAVA_HOME or '未设置'}\n"
                        logs += f"   - 环境变量: {os.environ.get('JAVA_HOME', '未设置')}\n"
                        logs += f"   - 常见路径: D:/Downloads/java\n"
                        logs += f"   请确保Java已安装并配置JAVA_HOME环境变量\n"
                    
                    return subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=temp_path,
                        env=exec_env,  # 使用修改后的环境变量
                        timeout=test_ir.get('timeout', 300),
                        encoding='utf-8',
                        errors='replace'
                    )
                
                # 在线程中运行同步函数，避免阻塞事件循环
                # 在BackgroundTasks中，可能没有事件循环，所以需要处理这种情况
                try:
                    # 尝试获取事件循环
                    try:
                        loop = asyncio.get_event_loop()
                        # Python 3.9+ 使用 asyncio.to_thread
                        if hasattr(asyncio, 'to_thread'):
                            result = await asyncio.to_thread(run_robot_sync)
                        else:
                            # Python 3.7-3.8 使用 run_in_executor
                            result = await loop.run_in_executor(None, run_robot_sync)
                    except RuntimeError:
                        # 没有事件循环，直接同步运行（在BackgroundTasks线程中）
                        result = run_robot_sync()
                    
                    stdout_text = result.stdout
                    stderr_text = result.stderr
                    return_code = result.returncode
                    
                except Exception as e:
                    # 如果所有异步方法都失败，直接同步运行
                    # 这在BackgroundTasks线程中是安全的
                    result = run_robot_sync()
                    stdout_text = result.stdout
                    stderr_text = result.stderr
                    return_code = result.returncode
                
            except FileNotFoundError as e:
                # 命令找不到
                error_msg = f"执行失败: 找不到命令 '{cmd[0]}'。\n"
                error_msg += f"当前使用的Python: {self.robot_executable}\n"
                if self.robot_args:
                    error_msg += f"命令参数: {' '.join(self.robot_args)}\n"
                error_msg += f"\n请确保Robot Framework已正确安装。\n"
                error_msg += f"系统Python安装: py -m pip install robotframework\n"
                error_msg += f"虚拟环境安装: pip install robotframework\n"
                error_msg += f"验证命令: py -m robot --version\n"
                raise FileNotFoundError(error_msg) from e
            except Exception as e:
                # 其他执行错误
                error_msg = f"执行Robot Framework命令时出错: {str(e)}\n"
                error_msg += f"命令: {' '.join(cmd)}\n"
                error_msg += f"工作目录: {temp_path}\n"
                raise RuntimeError(error_msg) from e
            
            # 7. 解析结果
            # stdout_text 和 stderr_text 已经在上面获取了
            
            # 添加详细的输出信息
            logs += "=== Robot Framework 标准输出 ===\n"
            logs += stdout_text + "\n\n"
            if stderr_text:
                logs += "=== Robot Framework 错误输出 ===\n"
                logs += stderr_text + "\n\n"
            
            result = await self._parse_robot_output(
                output_dir=output_dir,
                stdout=stdout_text,
                stderr=stderr_text,
                return_code=return_code,
                test_name=test_ir['name']
            )
            
            logs += result['logs']
            
            return self._create_result(
                passed=result['passed'],
                logs=logs,
                error_message=result.get('error_message'),
                artifacts=result.get('artifacts', [])
            )
            
            # 注意：不再自动清理工作目录
            # 因为SikuliLibrary的Java进程可能还在使用文件
            # 工作目录保留在 artifacts/robot_framework/work/{test_name}/
            # 可以手动清理或定期清理
                
        except Exception as e:
            import traceback
            error_logs = f"执行失败: {str(e)}\n\n"
            error_logs += f"错误类型: {type(e).__name__}\n\n"
            error_logs += "详细错误信息:\n"
            error_logs += traceback.format_exc()
            return self._create_result(
                passed=False,
                logs=error_logs,
                error_message=str(e)
            )
    
    async def validate_ir(self, test_ir: Dict[str, Any]) -> bool:
        """
        验证Robot Framework Test IR格式
        
        必需字段:
        - test_type: "robot_framework"
        - name: 测试名称
        - robot_script: Robot Framework脚本内容
        """
        required_fields = ['test_type', 'name', 'robot_script']
        if not all(field in test_ir for field in required_fields):
            return False
        
        if test_ir['test_type'] != 'robot_framework':
            return False
        
        return True
    
    def _generate_robot_script(self, test_ir: Dict[str, Any]) -> str:
        """
        生成Robot Framework脚本
        
        如果test_ir中提供了完整的robot_script，则直接使用；
        否则根据test_ir中的其他字段生成
        """
        if 'robot_script' in test_ir and test_ir['robot_script']:
            return test_ir['robot_script']
        
        # 如果提供了结构化的测试步骤，生成Robot脚本
        script = f"*** Settings ***\n"
        script += "Library    SikuliLibrary\n"
        
        # 添加其他库
        if 'libraries' in test_ir:
            for lib in test_ir['libraries']:
                script += f"Library    {lib}\n"
        
        # 添加资源文件
        if 'resource_files' in test_ir:
            for resource in test_ir['resource_files']:
                script += f"Resource    {resource}\n"
        
        script += f"\n*** Variables ***\n"
        variables = test_ir.get('variables', {})
        for key, value in variables.items():
            script += f"${{{{}}}}    {value}\n".format(key)
        
        script += f"\n*** Test Cases ***\n"
        script += f"{test_ir.get('name', 'Test Case')}\n"
        
        if 'description' in test_ir:
            script += f"    [Documentation]    {test_ir['description']}\n"
        
        if 'tags' in test_ir:
            tags = "    ".join(test_ir['tags'])
            script += f"    [Tags]    {tags}\n"
        
        # 添加测试步骤
        if 'steps' in test_ir:
            for step in test_ir['steps']:
                script += f"    {step}\n"
        
        return script
    
    async def _copy_resources(self, resources: list, target_dir: Path):
        """复制资源文件到临时目录"""
        for resource in resources:
            resource_path = Path(resource)
            if resource_path.exists():
                target_path = target_dir / resource_path.name
                shutil.copy2(resource_path, target_path)
    
    def _build_robot_command(
        self, 
        robot_file: Path, 
        output_dir: Path,
        variables: Dict[str, Any],
        timeout: int
    ) -> list:
        """构建Robot Framework执行命令"""
        cmd = [self.robot_executable]
        # 如果是 py -m robot，需要添加 -m robot
        cmd.extend(self.robot_args)
        
        # 添加Robot Framework参数
        cmd.extend([
            "--outputdir", str(output_dir),
            "--output", "output.xml",
            "--log", "log.html",
            "--report", "report.html",
        ])
        
        # 添加变量
        for key, value in variables.items():
            cmd.extend(["--variable", f"{key}:{value}"])
        
        # 添加超时
        if timeout:
            cmd.extend(["--variable", f"TIMEOUT:{timeout}"])
        
        # 添加测试文件
        cmd.append(str(robot_file))
        
        return cmd
    
    async def _parse_robot_output(
        self, 
        output_dir: Path,
        stdout: str,
        stderr: str,
        return_code: int,
        test_name: str = "unknown"
    ) -> Dict[str, Any]:
        """
        解析Robot Framework输出结果
        
        Robot Framework返回码:
        0: 所有测试通过
        1-249: 测试失败数量
        250: 用户中断
        251: 帮助或版本信息
        252: 无效数据或命令行参数
        253: 执行测试出错
        """
        result = {
            'passed': return_code == 0,
            'logs': '',
            'artifacts': []
        }
        
        # 添加标准输出和错误输出
        result['logs'] += "=== 标准输出 ===\n"
        result['logs'] += stdout + "\n"
        
        if stderr:
            result['logs'] += "\n=== 错误输出 ===\n"
            result['logs'] += stderr + "\n"
        
        # 解析返回码
        if return_code == 0:
            result['logs'] += "\n✓ 所有测试通过\n"
        elif 1 <= return_code <= 249:
            result['logs'] += f"\n✗ {return_code} 个测试失败\n"
            result['error_message'] = f"{return_code} tests failed"
        elif return_code == 250:
            result['logs'] += "\n⚠ 测试被用户中断\n"
            result['error_message'] = "Tests interrupted by user"
        elif return_code == 252:
            result['logs'] += "\n✗ 无效的数据或命令行参数\n"
            result['error_message'] = "Invalid data or command line arguments"
        elif return_code == 253:
            result['logs'] += "\n✗ 执行测试时出错\n"
            result['error_message'] = "Test execution failed"
        
        # 收集生成的文件
        artifacts = []
        
        # 确保output_dir是绝对路径
        output_dir_abs = Path(output_dir).resolve()
        
        # 获取项目根目录（backend的父目录）用于计算相对路径
        backend_dir = Path(__file__).parent.parent.parent  # backend目录
        project_root = backend_dir.parent  # 项目根目录
        
        # 输出文件
        output_xml = output_dir_abs / "output.xml"
        if output_xml.exists():
            try:
                # 尝试相对于项目根目录
                rel_path = output_xml.relative_to(project_root)
            except ValueError:
                # 如果不在项目根目录下，使用绝对路径
                rel_path = output_xml
            artifacts.append({
                "type": "robot_output",
                "path": str(rel_path),
                "name": "output.xml"
            })
        
        # 日志文件
        log_html = output_dir_abs / "log.html"
        if log_html.exists():
            try:
                rel_path = log_html.relative_to(project_root)
            except ValueError:
                rel_path = log_html
            artifacts.append({
                "type": "robot_log",
                "path": str(rel_path),
                "name": "log.html"
            })
        
        # 报告文件
        report_html = output_dir_abs / "report.html"
        if report_html.exists():
            try:
                rel_path = report_html.relative_to(project_root)
            except ValueError:
                rel_path = report_html
            artifacts.append({
                "type": "robot_report",
                "path": str(rel_path),
                "name": "report.html"
            })
        
        # Sikuli截图
        # SikuliLibrary会将截图保存到工作目录的sikuli_captured目录中
        # 需要从工作目录查找截图，然后复制到输出目录的screenshots目录
        
        # 1. 查找工作目录中的sikuli_captured目录
        work_dir = self.output_dir / "work" / test_name
        sikuli_captured_dir = work_dir / "sikuli_captured"
        
        # 2. 创建输出目录的screenshots目录
        screenshots_dir = output_dir_abs / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # 3. 从sikuli_captured目录复制截图到screenshots目录
        if sikuli_captured_dir.exists():
            for screenshot in sikuli_captured_dir.glob("*.png"):
                # 复制截图到输出目录
                target_screenshot = screenshots_dir / screenshot.name
                try:
                    shutil.copy2(screenshot, target_screenshot)
                    screenshot_abs = target_screenshot.resolve()
                    try:
                        rel_path = screenshot_abs.relative_to(project_root)
                    except ValueError:
                        rel_path = screenshot_abs
                    artifacts.append({
                        "type": "screenshot",
                        "path": str(rel_path),
                        "name": screenshot.name
                    })
                except Exception as e:
                    # 如果复制失败，仍然添加原始路径
                    screenshot_abs = screenshot.resolve()
                    try:
                        rel_path = screenshot_abs.relative_to(project_root)
                    except ValueError:
                        rel_path = screenshot_abs
                    artifacts.append({
                        "type": "screenshot",
                        "path": str(rel_path),
                        "name": screenshot.name
                    })
        
        # 4. 也检查输出目录的screenshots目录（如果直接保存在那里）
        if screenshots_dir.exists():
            for screenshot in screenshots_dir.glob("*.png"):
                # 避免重复添加
                if not any(a.get("name") == screenshot.name for a in artifacts if a.get("type") == "screenshot"):
                    screenshot_abs = screenshot.resolve()
                    try:
                        rel_path = screenshot_abs.relative_to(project_root)
                    except ValueError:
                        rel_path = screenshot_abs
                    artifacts.append({
                        "type": "screenshot",
                        "path": str(rel_path),
                        "name": screenshot.name
                    })
        
        result['artifacts'] = artifacts
        
        return result
    
    def check_dependencies(self) -> Dict[str, bool]:
        """
        检查依赖是否安装
        
        Returns:
            依赖检查结果字典
        """
        dependencies = {}
        
        # 检查Robot Framework
        try:
            result = subprocess.run(
                [self.robot_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            dependencies['robot_framework'] = result.returncode == 0
        except Exception:
            dependencies['robot_framework'] = False
        
        # 检查SikuliLibrary
        try:
            result = subprocess.run(
                ["python", "-c", "import SikuliLibrary"],
                capture_output=True,
                text=True,
                timeout=10
            )
            dependencies['sikuli_library'] = result.returncode == 0
        except Exception:
            dependencies['sikuli_library'] = False
        
        # 检查Jython（SikuliLibrary需要）
        try:
            result = subprocess.run(
                ["jython", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            dependencies['jython'] = result.returncode == 0
        except Exception:
            dependencies['jython'] = False
        
        return dependencies

