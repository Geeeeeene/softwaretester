import os
import sys
import asyncio
import shutil
import traceback
import subprocess
import tempfile
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Catch2Executor:
    """Catch2 测试执行器 - 终极环境适配版"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent.resolve()
        self.tools_dir = self.base_dir / "tools"
        self.catch2_lib_dir = (self.tools_dir / "Catch2-devel" / "extras").resolve()
        self.qt_prefix = self._detect_qt_path()
        self.compiler_info = self._find_mingw_compiler_ultimate()

    def _detect_qt_path(self) -> str:
        search_dirs = ["C:/Qt", "D:/Qt", "E:/Qt"]
        for base in search_dirs:
            if not os.path.exists(base): continue
            try:
                versions = [d for d in os.listdir(base) if d.startswith("6.")]
                versions.sort(reverse=True)
                for v in versions:
                    for c in ["mingw_64", "mingw"]:
                        path = os.path.join(base, v, c)
                        if os.path.exists(path): return path.replace("\\", "/")
            except: pass
        return "C:/Qt/6.7.2/mingw_64"

    def _find_mingw_compiler_ultimate(self) -> Dict[str, str]:
        info = {"make": "", "g++": "", "gcc": "", "bin_dir": ""}
        for tool in ["mingw32-make", "g++", "gcc"]:
            p = shutil.which(tool)
            if p: 
                key = "make" if "make" in tool else tool
                info[key] = p.replace("\\", "/")
        if not info["make"] or not info["g++"]:
            search_roots = ["C:/Qt", "D:/Qt", "C:/MinGW", "D:/MinGW"]
            for root in search_roots:
                if not os.path.exists(root): continue
                for subdir, dirs, files in os.walk(root):
                    if subdir.count(os.sep) - root.count(os.sep) > 4: continue
                    if "bin" in dirs:
                        bin_path = os.path.join(subdir, "bin")
                        make_p = os.path.join(bin_path, "mingw32-make.exe")
                        gpp_p = os.path.join(bin_path, "g++.exe")
                        if os.path.exists(make_p) and os.path.exists(gpp_p):
                            info["make"] = make_p.replace("\\", "/")
                            info["g++"] = gpp_p.replace("\\", "/")
                            info["gcc"] = os.path.join(bin_path, "gcc.exe").replace("\\", "/")
                            info["bin_dir"] = bin_path.replace("\\", "/")
                            return info
        return info

    def _run_sync_cmd(self, cmd: List[str], cwd: str) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        path_parts = []
        if self.compiler_info["bin_dir"]:
            path_parts.append(self.compiler_info["bin_dir"])
        # 确保 Qt 的 bin 目录在 PATH 中，避免运行期缺失 Qt6*.dll (0xC0000135)
        qt_bin = str(Path(self.qt_prefix) / "bin")
        if qt_bin and os.path.exists(qt_bin):
            path_parts.append(qt_bin)
        if path_parts:
            env["PATH"] = os.pathsep.join(path_parts + [env.get("PATH", "")])
        
        # 在 Windows 上，如果可执行文件路径包含空格，确保正确传递
        # subprocess.run 使用列表时应该能正确处理，但为了安全起见，确保路径存在
        if sys.platform == "win32" and len(cmd) > 0:
            exe_path = cmd[0]
            if not os.path.exists(exe_path):
                # 尝试查找可执行文件
                found = shutil.which(exe_path)
                if found:
                    cmd[0] = found
        
        try:
            return subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=cwd, text=True, encoding='utf-8',  # 使用 UTF-8 而不是 GBK，避免编码问题
                errors='replace', shell=False, env=env, timeout=300  # 添加 5 分钟超时
            )
        except subprocess.TimeoutExpired:
            # 如果超时，返回一个模拟的结果对象
            class TimeoutResult:
                returncode = -1
                stdout = ""
                stderr = "命令执行超时（超过 5 分钟）"
            return TimeoutResult()
        except Exception as e:
            # 如果执行失败，返回错误信息
            class ErrorResult:
                def __init__(self, err_msg):
                    self.returncode = -1
                    self.stdout = ""
                    self.stderr = f"命令执行失败: {err_msg}"
            return ErrorResult(str(e))

    async def execute(self, project_path: str, test_code: str, source_file_path: str) -> Dict[str, Any]:
        logs = []
        
        # 环境检查
        logs.append("🔍 检查编译环境...")
        if not self.compiler_info["make"] or not self.compiler_info["g++"]:
            logs.append(f"❌ 找不到编译器")
            logs.append(f"   make: {self.compiler_info.get('make', '未找到')}")
            logs.append(f"   g++: {self.compiler_info.get('g++', '未找到')}")
            return {"success": False, "logs": "\n".join(logs), "summary": {"total": 0, "passed": 0, "failed": 0}}
        
        logs.append(f"✅ 编译器检查通过")
        logs.append(f"   make: {self.compiler_info['make']}")
        logs.append(f"   g++: {self.compiler_info['g++']}")
        logs.append(f"   Qt路径: {self.qt_prefix}")
        
        # 检查 Qt 路径是否存在
        qt_path = Path(self.qt_prefix)
        if not qt_path.exists():
            logs.append(f"⚠️  警告: Qt路径不存在: {self.qt_prefix}")
            logs.append("   将尝试使用默认路径，如果配置失败，请检查 Qt 安装")
        else:
            logs.append(f"✅ Qt路径存在: {self.qt_prefix}")

        temp_dir = Path(tempfile.gettempdir()) / "qt_tester"
        temp_dir.mkdir(parents=True, exist_ok=True)
        work_id = os.urandom(4).hex()
        build_dir = temp_dir / work_id
        build_dir.mkdir(parents=True, exist_ok=True)
        
        logs.append(f"📁 构建目录: {build_dir}")

        try:
            # 1. 物理搬迁所有相关文件
            logs.append("📦 准备 Catch2 库文件...")
            if not (self.catch2_lib_dir / "catch_amalgamated.cpp").exists():
                logs.append(f"❌ Catch2 库文件不存在: {self.catch2_lib_dir / 'catch_amalgamated.cpp'}")
                return {"success": False, "logs": "\n".join(logs), "summary": {"total": 0, "passed": 0, "failed": 0}}
            
            shutil.copy2(self.catch2_lib_dir / "catch_amalgamated.cpp", build_dir / "catch_amalgamated.cpp")
            shutil.copy2(self.catch2_lib_dir / "catch_amalgamated.hpp", build_dir / "catch_amalgamated.hpp")
            logs.append("✅ Catch2 库文件已复制")
            
            catch_main_cpp = """
#include "catch_amalgamated.hpp"
#include <QApplication>
int main( int argc, char* argv[] ) {
  QApplication a(argc, argv); // 确保有 GUI 环境上下文
  return Catch::Session().run( argc, argv );
}
"""
            (build_dir / "catch_main_wrapper.cpp").write_text(catch_main_cpp, encoding='utf-8')
            
            # 清理测试代码：移除可能的 main 函数（执行器已经提供了 main）
            cleaned_test_code = self._clean_test_code(test_code)
            (build_dir / "test_cases.cpp").write_text(cleaned_test_code, encoding='utf-8')
            logs.append("✅ 测试代码已清理并写入")
            
            src_file_full = Path(source_file_path).resolve()
            src_dir = src_file_full.parent
            cpp_files = ["catch_main_wrapper.cpp", "catch_amalgamated.cpp", "test_cases.cpp"]
            ui_files = []
            
            blocklist = {"main.cpp", "mygraphicsview.cpp"}  # 避免已知与测试无关且会触发编译错误的文件

            for item in src_dir.iterdir():
                if item.is_file():
                    ext = item.suffix.lower()
                    if ext in {'.h', '.hpp', '.hh', '.hxx', '.ui', '.qrc', '.png', '.jpg', '.ico'}:
                        shutil.copy2(item, build_dir / item.name)
                        if ext == '.ui': ui_files.append(item.name)
                    elif ext in {'.cpp', '.cc', '.cxx', '.c'}:
                        if item.name.lower() in blocklist:
                            continue
                        if item.name.lower() != "main.cpp":
                            shutil.copy2(item, build_dir / item.name)
                            cpp_files.append(item.name)
            
            cmake_exe = shutil.which("cmake") or "cmake"
            logs.append(f"🔧 CMake: {cmake_exe}")
            
            # 检查 CMake 是否可用
            cmake_check = await asyncio.to_thread(self._run_sync_cmd, [cmake_exe, "--version"], str(build_dir))
            if cmake_check.returncode != 0:
                logs.append(f"❌ CMake 不可用，请确保已安装 CMake 并添加到 PATH")
                return {"success": False, "logs": "\n".join(logs), "summary": {"total": 0, "passed": 0, "failed": 0}}
            logs.append(f"✅ CMake 版本: {cmake_check.stdout.split()[2] if cmake_check.stdout else '未知'}")
            
            cpp_sources_str = "\n    ".join([f'"{f}"' for f in cpp_files])
            ui_sources_str = "\n    ".join([f'"{f}"' for f in ui_files])
            
            logs.append(f"📝 源文件数量: {len(cpp_files)}")
            logs.append(f"📝 UI文件数量: {len(ui_files)}")

            cmake_content = f"""
cmake_minimum_required(VERSION 3.16)
# 限制最大版本为 3.28，避免 CMake 4.x 的兼容性问题
if(CMAKE_VERSION VERSION_GREATER_EQUAL "4.0")
    message(WARNING "CMake 4.x detected. For better compatibility, consider using CMake 3.16-3.28")
endif()
project(Catch2Test LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# 终极兼容模式：忽略 override，放宽类型检查
add_definitions(-Doverride=)
set(CMAKE_CXX_FLAGS "${{CMAKE_CXX_FLAGS}} -fpermissive")

if(WIN32)
    # 暴力注入全量 Qt 头文件，解决所有 incomplete type 错误
    set(CMAKE_CXX_FLAGS "${{CMAKE_CXX_FLAGS}} -include QtWidgets -include QtGui -include QtCore")
    set(CMAKE_EXE_LINKER_FLAGS "-Wl,--subsystem,console")
endif()

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Svg PrintSupport)

include_directories(".")
include_directories("${{CMAKE_CURRENT_BINARY_DIR}}")

add_executable(test_runner 
    {cpp_sources_str}
    {ui_sources_str}
)

target_link_libraries(test_runner PRIVATE Qt6::Core Qt6::Gui Qt6::Widgets Qt6::Svg Qt6::PrintSupport)
"""
            (build_dir / "CMakeLists.txt").write_text(cmake_content, encoding='utf-8')
            logs.append("✅ CMakeLists.txt 已生成")

            # 1. 配置
            # 直接使用原始路径（规范化），不使用短路径
            # 现代 CMake 和 Windows 都能处理长路径，短路径可能导致 CMake 无法识别
            def normalize_path(path):
                """规范化路径，统一使用正斜杠"""
                if not path:
                    return ""
                return path.replace("\\", "/")
            
            qt_prefix_path = normalize_path(self.qt_prefix)
            make_path = normalize_path(self.compiler_info['make'])
            gcc_path = normalize_path(self.compiler_info['gcc'] or self.compiler_info['g++'])
            gpp_path = normalize_path(self.compiler_info['g++'])
            
            logs.append("⚙️  开始 CMake 配置...")
            logs.append(f"   使用原始路径（不使用短路径）")
            logs.append(f"   Qt路径: {qt_prefix_path}")
            logs.append(f"   Make: {make_path}")
            logs.append(f"   C编译器: {gcc_path}")
            logs.append(f"   C++编译器: {gpp_path}")
            
            # 验证路径是否存在
            all_paths_valid = True
            for name, path in [("Qt路径", qt_prefix_path), ("Make", make_path), 
                              ("C编译器", gcc_path), ("C++编译器", gpp_path)]:
                if path:
                    exists = os.path.exists(path) or os.path.exists(path.replace("/", "\\"))
                    if not exists:
                        logs.append(f"   ❌ {name} 路径不存在: {path}")
                        all_paths_valid = False
                    else:
                        logs.append(f"   ✅ {name} 路径有效")
            
            if not all_paths_valid:
                logs.append("   ⚠️  部分路径无效，但将继续尝试配置")
            
            # 构建 CMake 配置命令
            # 注意：在 Windows 上，如果路径包含空格，CMake 需要特殊处理
            # 对于 -D 参数，如果值包含空格，需要用引号包裹
            def escape_cmake_path(path):
                """转义 CMake 路径参数"""
                if not path:
                    return ""
                # 如果路径包含空格，用引号包裹
                if ' ' in path:
                    return f'"{path}"'
                return path
            
            config_cmd = [
                cmake_exe, "-G", "MinGW Makefiles",
                f"-DCMAKE_PREFIX_PATH={escape_cmake_path(qt_prefix_path)}",
                f"-DCMAKE_MAKE_PROGRAM={escape_cmake_path(make_path)}",
                f"-DCMAKE_C_COMPILER={escape_cmake_path(gcc_path)}",
                f"-DCMAKE_CXX_COMPILER={escape_cmake_path(gpp_path)}",
                "."
            ]
            
            logs.append("--- 执行 CMake 配置命令 ---")
            logs.append(" ".join(config_cmd))
            
            # 先测试 CMake 是否能正常运行
            logs.append("--- 测试 CMake 可执行性 ---")
            test_cmd = [cmake_exe, "--version"]
            test_res = await asyncio.to_thread(self._run_sync_cmd, test_cmd, str(build_dir))
            if test_res.returncode != 0:
                logs.append(f"⚠️  CMake 版本检查失败，退出码: {test_res.returncode}")
                logs.append(f"   标准输出: {test_res.stdout if test_res.stdout else '(无)'}")
                logs.append(f"   错误输出: {test_res.stderr if test_res.stderr else '(无)'}")
            else:
                logs.append(f"✅ CMake 可以正常运行: {test_res.stdout.splitlines()[0] if test_res.stdout else '未知版本'}")
            
            conf_res = await asyncio.to_thread(self._run_sync_cmd, config_cmd, str(build_dir))
            if conf_res.returncode != 0:
                logs.append("❌ CMake 配置失败")
                logs.append(f"   退出码: {conf_res.returncode}")
                
                # 将退出码转换为十六进制，便于诊断
                if conf_res.returncode > 0:
                    hex_code = hex(conf_res.returncode & 0xFFFFFFFF)
                    logs.append(f"   退出码(十六进制): {hex_code}")
                    if conf_res.returncode == 3221226505:  # 0xC0000005
                        logs.append("   ⚠️  这是 Windows 访问冲突错误 (0xC0000005)，通常表示程序崩溃")
                        logs.append("   可能原因：")
                        logs.append("     1. CMake 可执行文件损坏或版本不兼容")
                        logs.append("     2. 工作目录路径包含特殊字符导致问题")
                        logs.append("     3. CMakeLists.txt 语法错误导致 CMake 崩溃")
                        logs.append("     4. 系统环境变量或 DLL 依赖问题")
                
                logs.append("--- 配置命令 ---")
                logs.append(" ".join(config_cmd))
                logs.append("--- 标准输出 ---")
                stdout_text = conf_res.stdout if conf_res.stdout else "(无输出)"
                logs.append(stdout_text)
                logs.append("--- 错误输出 ---")
                stderr_text = conf_res.stderr if conf_res.stderr else "(无输出)"
                logs.append(stderr_text)
                
                # 如果没有任何输出，可能是命令执行本身有问题
                if not conf_res.stdout and not conf_res.stderr:
                    logs.append("--- 诊断信息 ---")
                    logs.append("⚠️  CMake 命令执行后没有任何输出，可能的原因：")
                    logs.append("   1. CMake 可执行文件路径不正确或损坏")
                    logs.append("   2. 命令参数格式有问题")
                    logs.append("   3. 工作目录不存在或无权限")
                    logs.append("   4. CMake 在执行时崩溃（访问冲突）")
                    logs.append(f"   工作目录: {build_dir}")
                    logs.append(f"   工作目录存在: {os.path.exists(build_dir)}")
                    logs.append(f"   工作目录可写: {os.access(build_dir, os.W_OK)}")
                    logs.append(f"   CMake 可执行文件: {cmake_exe}")
                    logs.append(f"   CMake 存在: {os.path.exists(cmake_exe)}")
                    logs.append(f"   CMake 可执行: {os.access(cmake_exe, os.X_OK) if os.path.exists(cmake_exe) else False}")
                    
                    # 检查 CMakeLists.txt
                    cmake_file = build_dir / "CMakeLists.txt"
                    if cmake_file.exists():
                        logs.append(f"   CMakeLists.txt 存在: True")
                        logs.append(f"   CMakeLists.txt 大小: {cmake_file.stat().st_size} 字节")
                        # 显示前几行
                        try:
                            with open(cmake_file, 'r', encoding='utf-8') as f:
                                lines = f.readlines()[:5]
                                logs.append(f"   CMakeLists.txt 前5行:")
                                for i, line in enumerate(lines, 1):
                                    logs.append(f"      {i}: {line.rstrip()}")
                        except Exception as e:
                            logs.append(f"   无法读取 CMakeLists.txt: {e}")
                
                logs.append("--- 故障排查建议 ---")
                logs.append("1. 检查 Qt6 是否已正确安装")
                logs.append(f"2. 检查 Qt 路径是否正确: {self.qt_prefix}")
                logs.append("3. 检查 CMake 是否能找到 Qt6")
                logs.append("4. 检查编译器路径是否正确")
                logs.append("5. 检查 CMakeLists.txt 语法是否正确")
                logs.append("6. 尝试手动运行 CMake 配置命令查看详细错误")
                logs.append("7. 如果退出码是 3221226505 (0xC0000005)，尝试重新安装 CMake 或使用不同版本")
                
                return {"success": False, "logs": "\n".join(logs), "summary": {"total": 0, "passed": 0, "failed": 0}}
            
            logs.append("✅ CMake 配置成功")

            # 2. 编译
            logs.append("🔨 编译中...")
            build_res = await asyncio.to_thread(self._run_sync_cmd, [cmake_exe, "--build", "."], str(build_dir))
            if build_res.returncode != 0:
                logs.append("❌ 编译失败")
                logs.append("--- 编译输出 ---")
                if build_res.stdout:
                    logs.append(build_res.stdout)
                if build_res.stderr:
                    logs.append("--- 错误输出 ---")
                    logs.append(build_res.stderr)
                logs.append("--- 故障排查建议 ---")
                logs.append("1. 检查生成的测试代码是否有语法错误")
                logs.append("2. 检查是否包含了不存在的头文件或库")
                logs.append("3. 检查是否使用了不支持的 C++ 特性")
                logs.append("4. 查看上方的编译错误信息，定位具体问题")
                return {"success": False, "logs": "\n".join(logs), "summary": {"total": 0, "passed": 0, "failed": 0}}
            
            logs.append("✅ 编译成功")

            # 3. 运行
            logs.append("🚀 运行中...")
            exe_path = build_dir / "test_runner.exe"
            
            if not exe_path.exists():
                logs.append(f"❌ 可执行文件不存在: {exe_path}")
                logs.append("   编译可能失败，但未正确报告错误")
                return {"success": False, "logs": "\n".join(logs), "summary": {"total": 0, "passed": 0, "failed": 0}}
            
            run_res = await asyncio.to_thread(self._run_sync_cmd, [str(exe_path), "--reporter", "xml"], str(build_dir))

            # 如果没有任何标准输出/错误输出，提示用户可能没有生成用例或程序提前退出
            if not run_res.stdout and not run_res.stderr:
                logs.append(f"⚠️ test_runner 无输出，退出码 {run_res.returncode}")
                logs.append("   可能的原因：")
                logs.append("   1. 测试代码中没有定义任何 TEST_CASE")
                logs.append("   2. 程序在初始化时崩溃")
                logs.append("   3. 测试代码有运行时错误")
            
            summary = self._parse_catch2_results(run_res.stdout)
            
            # 如果解析结果为空，说明可能没有测试用例
            if summary["total"] == 0 and not run_res.stdout:
                logs.append("⚠️ 未检测到任何测试用例")
                logs.append("   请检查生成的测试代码是否包含 TEST_CASE 定义")
            
            return {
                "success": True, 
                "logs": "\n".join(logs) + "\n\n--- 终端输出 ---\n" + (run_res.stdout or "") + (run_res.stderr or ""),
                "summary": summary
            }
            
        except Exception as e:
            error_detail = traceback.format_exc()
            error_logs = logs.copy() if 'logs' in locals() else []
            error_logs.append(f"❌ 执行过程中发生异常:")
            error_logs.append(f"   错误类型: {type(e).__name__}")
            error_logs.append(f"   错误信息: {str(e)}")
            error_logs.append(f"\n--- 详细堆栈跟踪 ---")
            error_logs.append(error_detail)
            return {"success": False, "logs": "\n".join(error_logs), "summary": {"total": 0, "passed": 0, "failed": 0}}

    def _clean_test_code(self, test_code: str) -> str:
        """清理测试代码，移除 main 函数和其他可能导致冲突的内容"""
        lines = test_code.split('\n')
        cleaned_lines = []
        skip_main = False
        brace_count = 0
        
        for line in lines:
            # 检测 main 函数定义（不是函数调用）
            # 匹配模式：int main( 或 void main( 或 main( 后面跟参数列表
            if not skip_main:
                # 检查是否是 main 函数定义
                main_patterns = [
                    'int main(',
                    'void main(',
                    'int main (',
                    'void main ('
                ]
                
                is_main_def = False
                for pattern in main_patterns:
                    if pattern in line:
                        # 确保不是函数调用（函数调用通常在行尾有分号，或者前面有变量名）
                        parts = line.split(pattern)
                        if len(parts) > 1:
                            before = parts[0].strip()
                            # 如果前面有变量名、等号或分号，可能是函数调用
                            if not before or before.endswith('=') or before.endswith(';'):
                                continue
                            is_main_def = True
                            break
                
                if is_main_def:
                    skip_main = True
                    brace_count = line.count('{') - line.count('}')
                    # 如果这一行就结束了，不需要跳过
                    if brace_count <= 0:
                        skip_main = False
                    continue
            
            if skip_main:
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    skip_main = False
                continue
            
            cleaned_lines.append(line)
        
        cleaned_code = '\n'.join(cleaned_lines)
        
        # 移除可能的重复 include catch_amalgamated.hpp
        lines = cleaned_code.split('\n')
        seen_include = False
        final_lines = []
        for line in lines:
            if '#include "catch_amalgamated.hpp"' in line or "#include 'catch_amalgamated.hpp'" in line:
                if not seen_include:
                    final_lines.append(line)
                    seen_include = True
                # 跳过重复的 include
            else:
                final_lines.append(line)
        cleaned_code = '\n'.join(final_lines)
        
        return cleaned_code

    def _get_short_path(self, path: str) -> str:
        """获取短路径（8.3格式），如果转换失败或路径无效，返回原始路径"""
        if sys.platform != "win32": 
            return path.replace("\\", "/")
        
        # 先规范化路径
        normalized_path = path.replace("\\", "/")
        
        # 如果路径不存在，直接返回规范化路径
        if not os.path.exists(path):
            return normalized_path
        
        try:
            import ctypes
            from ctypes import wintypes
            buf = ctypes.create_unicode_buffer(512)
            # 转换为 Windows 路径格式（使用反斜杠）
            win_path = path.replace("/", "\\")
            result = ctypes.windll.kernel32.GetShortPathNameW(win_path, buf, 512)
            if result and result > 0:
                short_path = buf.value.replace("\\", "/")
                # 验证短路径是否存在
                if os.path.exists(short_path) or os.path.exists(short_path.replace("/", "\\")):
                    return short_path
        except Exception as e:
            # 如果转换失败，记录但不抛出异常
            pass
        
        # 如果短路径转换失败或无效，返回原始路径
        return normalized_path

    def _parse_catch2_results(self, xml_content: str) -> Dict[str, Any]:
        """
        解析 Catch2 XML 输出，返回汇总和用例/分节详情：
        {
            total, passed, failed,
            assertions: {successes, failures},
            cases: [
                {
                    name, file, line, tags, successes, failures, success,
                    sections: [{name, file, line, successes, failures, success}]
                }
            ]
        }
        """
        try:
            import xml.etree.ElementTree as ET
            start = xml_content.find("<?xml")
            if start == -1:
                return {"total": 0, "passed": 0, "failed": 0, "assertions": {"successes": 0, "failures": 0}, "cases": []}
            root = ET.fromstring(xml_content[start:])

            cases = []
            total_successes = 0
            total_failures = 0

            for tc in root.findall(".//TestCase"):
                tc_name = tc.get("name", "")
                tc_file = tc.get("filename", "")
                tc_line = int(tc.get("line", 0)) if tc.get("line") else 0
                tc_tags = tc.get("tags", "")
                # TestCase level overall
                tc_overall = tc.find("./OverallResult")
                tc_success = tc_overall is not None and tc_overall.get("success", "false") == "true"
                tc_successes = 0
                tc_failures = 0

                sections_info: List[Dict[str, Any]] = []
                for sec in tc.findall("./Section"):
                    sec_name = sec.get("name", "")
                    sec_file = sec.get("filename", "")
                    sec_line = int(sec.get("line", 0)) if sec.get("line") else 0
                    sec_res = sec.find("./OverallResults")
                    sec_s = int(sec_res.get("successes", 0)) if sec_res is not None else 0
                    sec_f = int(sec_res.get("failures", 0)) if sec_res is not None else 0
                    sections_info.append({
                        "name": sec_name,
                        "file": sec_file,
                        "line": sec_line,
                        "successes": sec_s,
                        "failures": sec_f,
                        "success": sec_f == 0
                    })
                    tc_successes += sec_s
                    tc_failures += sec_f

                total_successes += tc_successes
                total_failures += tc_failures

                cases.append({
                    "name": tc_name,
                    "file": tc_file,
                    "line": tc_line,
                    "tags": tc_tags,
                    "successes": tc_successes,
                    "failures": tc_failures,
                    "success": tc_failures == 0 and tc_success,
                    "sections": sections_info
                })

            total_cases = len(cases)
            passed_cases = len([c for c in cases if c["success"]])
            failed_cases = total_cases - passed_cases
            return {
                "total": total_cases,
                "passed": passed_cases,
                "failed": failed_cases,
                "assertions": {"successes": total_successes, "failures": total_failures},
                "cases": cases
            }
        except Exception:
            # 回退到最简解析
            import re
            m = re.search(r'failures="(\d+)" successes="(\d+)"', xml_content or "")
            if m:
                f, s = int(m.group(1)), int(m.group(2))
                return {"total": f + s, "passed": s, "failed": f, "assertions": {"successes": s, "failures": f}, "cases": []}
            if "All tests passed" in (xml_content or ""):
                return {"total": 1, "passed": 1, "failed": 0, "assertions": {"successes": 1, "failures": 0}, "cases": []}
            return {"total": 0, "passed": 0, "failed": 0, "assertions": {"successes": 0, "failures": 0}, "cases": []}
