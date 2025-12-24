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
        # 覆盖率工具路径（可选，如果未找到不影响正常测试）
        self.gcov_path = self._find_tool("gcov")
        self.lcov_path = self._find_tool("lcov")
    
    def _find_tool(self, tool_name: str) -> Optional[str]:
        """查找工具可执行文件（用于覆盖率统计）"""
        exe_name = f"{tool_name}.exe" if sys.platform == "win32" else tool_name
        return shutil.which(tool_name) or shutil.which(exe_name)

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
        return subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=cwd, text=True, encoding='gbk' if sys.platform=="win32" else 'utf-8', 
            errors='replace', shell=False, env=env
        )

    async def execute(self, project_path: str, test_code: str, source_file_path: str) -> Dict[str, Any]:
        logs = []
        if not self.compiler_info["make"] or not self.compiler_info["g++"]:
            return {"success": False, "logs": "❌ 找不到编译器", "summary": {"total": 0, "passed": 0, "failed": 0}}

        temp_dir = Path(tempfile.gettempdir()) / "qt_tester"
        temp_dir.mkdir(parents=True, exist_ok=True)
        work_id = os.urandom(4).hex()
        build_dir = temp_dir / work_id
        build_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. 物理搬迁所有相关文件
            shutil.copy2(self.catch2_lib_dir / "catch_amalgamated.cpp", build_dir / "catch_amalgamated.cpp")
            shutil.copy2(self.catch2_lib_dir / "catch_amalgamated.hpp", build_dir / "catch_amalgamated.hpp")
            
            src_file_full = Path(source_file_path).resolve()
            src_dir = src_file_full.parent
            cpp_files = ["catch_main_wrapper.cpp", "catch_amalgamated.cpp", "test_cases.cpp"]
            ui_files = []
            qrc_files = []
            
            blocklist = {"main.cpp", "mygraphicsview.cpp"}  # 避免已知与测试无关且会触发编译错误的文件

            # 第一遍：收集所有文件
            for item in src_dir.iterdir():
                if item.is_file():
                    ext = item.suffix.lower()
                    if ext in {'.h', '.hpp', '.hh', '.hxx', '.ui', '.qrc', '.png', '.jpg', '.ico', '.jpeg', '.svg'}:
                        shutil.copy2(item, build_dir / item.name)
                        if ext == '.ui': 
                            ui_files.append(item.name)
                        elif ext == '.qrc':
                            qrc_files.append(item.name)
                    elif ext in {'.cpp', '.cc', '.cxx', '.c'}:
                        if item.name.lower() in blocklist:
                            continue
                        if item.name.lower() != "main.cpp":
                            shutil.copy2(item, build_dir / item.name)
                            cpp_files.append(item.name)
            
            # 第二遍：处理 .qrc 文件中引用的资源文件（递归复制资源目录）
            # Qt 资源系统在编译时需要找到资源文件，所以需要保持目录结构
            # CMake 的 AUTORCC 会在构建目录中查找 .qrc 文件中引用的资源文件
            if qrc_files:
                logs.append(f"📦 检测到 {len(qrc_files)} 个资源文件: {', '.join(qrc_files)}")
                
                # 先尝试复制常见的资源目录（如 images/），这样可以覆盖大部分资源文件
                common_resource_dirs = ['images', 'resources', 'icons', 'pics']
                for resource_dir in common_resource_dirs:
                    resource_path = src_dir / resource_dir
                    if resource_path.exists() and resource_path.is_dir():
                        dest_resource_dir = build_dir / resource_dir
                        if not dest_resource_dir.exists():
                            shutil.copytree(resource_path, dest_resource_dir)
                            logs.append(f"📁 已复制资源目录: {resource_dir}/")
                
                # 解析 .qrc 文件，找出其中引用的资源路径，确保所有资源文件都被复制
                for qrc_file in qrc_files:
                    qrc_path = build_dir / qrc_file
                    if qrc_path.exists():
                        try:
                            qrc_content = qrc_path.read_text(encoding='utf-8')
                            # 简单的 XML 解析，找出 <file> 标签中的路径
                            import re
                            file_pattern = r'<file[^>]*>([^<]+)</file>'
                            resource_files = re.findall(file_pattern, qrc_content)
                            if resource_files:
                                logs.append(f"   📄 {qrc_file} 中引用了 {len(resource_files)} 个资源文件")
                                copied_count = 0
                                missing_count = 0
                                # 复制所有资源文件（不只是前5个）
                                for res_file in resource_files:
                                    # 处理路径，移除前导斜杠（如果有）
                                    res_file_clean = res_file.lstrip('/')
                                    res_path = src_dir / res_file_clean
                                    if res_path.exists():
                                        # 确保目录结构被复制
                                        dest_res_path = build_dir / res_file_clean
                                        dest_res_path.parent.mkdir(parents=True, exist_ok=True)
                                        if not dest_res_path.exists():
                                            shutil.copy2(res_path, dest_res_path)
                                            copied_count += 1
                                    else:
                                        missing_count += 1
                                        if missing_count <= 3:  # 只显示前3个缺失的文件
                                            logs.append(f"   ⚠️ 资源文件不存在: {res_file_clean}")
                                
                                if copied_count > 0:
                                    logs.append(f"   ✅ 已复制 {copied_count} 个资源文件")
                                if missing_count > 0:
                                    if missing_count > 3:
                                        logs.append(f"   ⚠️ 还有 {missing_count - 3} 个资源文件不存在")
                                    else:
                                        logs.append(f"   ⚠️ 共 {missing_count} 个资源文件不存在")
                        except Exception as e:
                            logs.append(f"   ⚠️ 解析 {qrc_file} 失败: {str(e)}")
                            import traceback
                            logs.append(f"   ⚠️ 错误详情: {traceback.format_exc()}")
            
            # 生成资源初始化代码
            # 注意：在 Qt6 中，使用 CMAKE_AUTORCC 时，资源会自动注册
            # CMake 会生成 qrc_*.cpp 文件，这些文件会自动注册资源
            # 但是，如果资源文件路径不正确，资源就不会被加载
            qrc_includes = ""
            qrc_init_calls = ""
            if qrc_files:
                # 在 Qt6 中，使用 CMAKE_AUTORCC 时，资源会自动注册
                # 但为了确保资源可用，我们可以添加调试代码
                qrc_includes = "#include <QtCore/QResource>\n#include <QDebug>\n"
                # 注意：Q_INIT_RESOURCE 在 Qt6 中使用 CMAKE_AUTORCC 时通常不需要
                # CMake 会自动生成资源初始化代码
                # 但如果需要手动调用，资源名称应该是 .qrc 文件名（不含扩展名）
                # 不过，由于 CMAKE_AUTORCC 会自动处理，我们暂时不调用 Q_INIT_RESOURCE
                # 如果资源加载失败，可能是路径问题或资源文件不存在
                logs.append(f"💡 提示：Qt6 的 CMAKE_AUTORCC 会自动处理资源文件")
            
            catch_main_cpp = f"""
#include "catch_amalgamated.hpp"
#include <QApplication>
{qrc_includes}
int main( int argc, char* argv[] ) {{
  QApplication a(argc, argv); // 确保有 GUI 环境上下文
  // 注意：在 Qt6 中使用 CMAKE_AUTORCC 时，资源会自动注册，无需手动调用 Q_INIT_RESOURCE
  // 如果资源加载失败，请检查：
  // 1. .qrc 文件中的资源路径是否正确
  // 2. 资源文件是否存在于构建目录中
  // 3. CMake 是否正确处理了 .qrc 文件
{qrc_init_calls}
  return Catch::Session().run( argc, argv );
}}
"""
            (build_dir / "catch_main_wrapper.cpp").write_text(catch_main_cpp, encoding='utf-8')
            (build_dir / "test_cases.cpp").write_text(test_code, encoding='utf-8')
            
            cmake_exe = shutil.which("cmake") or "cmake"
            cpp_sources_str = "\n    ".join([f'"{f}"' for f in cpp_files])
            ui_sources_str = "\n    ".join([f'"{f}"' for f in ui_files])
            qrc_sources_str = "\n    ".join([f'"{f}"' for f in qrc_files])

            # 检查是否启用覆盖率统计（如果工具可用）
            coverage_flags = ""
            if self.gcov_path:
                coverage_flags = "-fprofile-arcs -ftest-coverage"
                logs.append("📊 检测到 gcov，将启用行覆盖率统计")
            
            cmake_content = f"""
cmake_minimum_required(VERSION 3.16)
project(Catch2Test LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# 终极兼容模式：忽略 override，放宽类型检查
add_definitions(-Doverride=)
set(CMAKE_CXX_FLAGS "${{CMAKE_CXX_FLAGS}} -fpermissive {coverage_flags}")

if(WIN32)
    # 暴力注入全量 Qt 头文件，解决所有 incomplete type 错误
    set(CMAKE_CXX_FLAGS "${{CMAKE_CXX_FLAGS}} -include QtWidgets -include QtGui -include QtCore")
    set(CMAKE_EXE_LINKER_FLAGS "-Wl,--subsystem,console {coverage_flags}")
endif()

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Svg PrintSupport)

include_directories(".")
include_directories("${{CMAKE_CURRENT_BINARY_DIR}}")

add_executable(test_runner 
    {cpp_sources_str}
    {ui_sources_str}
    {qrc_sources_str}
)

target_link_libraries(test_runner PRIVATE Qt6::Core Qt6::Gui Qt6::Widgets Qt6::Svg Qt6::PrintSupport)
"""
            (build_dir / "CMakeLists.txt").write_text(cmake_content, encoding='utf-8')

            # 1. 配置
            config_cmd = [
                cmake_exe, "-G", "MinGW Makefiles",
                f"-DCMAKE_PREFIX_PATH={self._get_short_path(self.qt_prefix)}",
                f"-DCMAKE_MAKE_PROGRAM={self._get_short_path(self.compiler_info['make'])}",
                f"-DCMAKE_C_COMPILER={self._get_short_path(self.compiler_info['gcc'] or self.compiler_info['g++'])}",
                f"-DCMAKE_CXX_COMPILER={self._get_short_path(self.compiler_info['g++'])}",
                "."
            ]
            
            conf_res = await asyncio.to_thread(self._run_sync_cmd, config_cmd, str(build_dir))
            if conf_res.returncode != 0:
                logs.append(f"❌ 配置失败:\n{conf_res.stdout}{conf_res.stderr}")
                return {"success": False, "logs": "\n".join(logs), "summary": {"total": 0, "passed": 0, "failed": 0}}

            # 2. 编译
            logs.append("🔨 编译中...")
            build_res = await asyncio.to_thread(self._run_sync_cmd, [cmake_exe, "--build", "."], str(build_dir))
            if build_res.returncode != 0:
                logs.append(f"❌ 编译失败:\n{build_res.stdout}{build_res.stderr}")
                return {"success": False, "logs": "\n".join(logs), "summary": {"total": 0, "passed": 0, "failed": 0}}

            # 3. 运行
            logs.append("🚀 运行中...")
            exe_path = build_dir / "test_runner.exe"
            run_res = await asyncio.to_thread(self._run_sync_cmd, [str(exe_path), "--reporter", "xml"], str(build_dir))

            # 如果没有任何标准输出/错误输出，提示用户可能没有生成用例或程序提前退出
            if not run_res.stdout and not run_res.stderr:
                logs.append(f"⚠️ test_runner 无输出，退出码 {run_res.returncode}")
            
            summary = self._parse_catch2_results(run_res.stdout)
            
            # 收集覆盖率数据（如果工具可用且已启用覆盖率编译）
            coverage_data = None
            if self.gcov_path and coverage_flags:
                try:
                    coverage_data = await self._collect_coverage(build_dir, logs)
                    if not coverage_data:
                        logs.append("⚠️ 覆盖率数据收集失败，可能原因：")
                        logs.append("   1. 测试未运行或提前退出")
                        logs.append("   2. 覆盖率数据文件 (.gcda) 未生成")
                        if not self.lcov_path:
                            logs.append("   3. 建议安装 lcov 以获得更准确的覆盖率报告")
                            logs.append("      Windows: choco install lcov")
                            logs.append("      Linux: sudo apt install lcov")
                except Exception as e:
                    logger.warning(f"覆盖率收集失败: {str(e)}")
                    logs.append(f"⚠️ 覆盖率收集失败: {str(e)}")
                    if not self.lcov_path:
                        logs.append("💡 提示: 安装 lcov 可能有助于解决问题")
            
            result = {
                "success": True, 
                "logs": "\n".join(logs) + "\n\n--- 终端输出 ---\n" + run_res.stdout + run_res.stderr,
                "summary": summary
            }
            
            # 如果收集到覆盖率数据，添加到结果中（使用 coverage_data 字段，与现有代码兼容）
            if coverage_data:
                result["coverage_data"] = coverage_data
            
            return result
            
        except Exception as e:
            return {"success": False, "logs": f"❌ 异常: {str(e)}", "summary": {"total": 0, "passed": 0, "failed": 0}}

    def _get_short_path(self, path: str) -> str:
        if sys.platform != "win32": return path
        try:
            import ctypes
            from ctypes import wintypes
            buf = ctypes.create_unicode_buffer(512)
            if ctypes.windll.kernel32.GetShortPathNameW(path, buf, 512):
                return buf.value.replace("\\", "/")
        except: pass
        return path.replace("\\", "/")

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
    
    async def _collect_coverage(self, build_dir: Path, logs: List[str]) -> Optional[Dict[str, Any]]:
        """收集行覆盖率数据（使用 gcov 和 lcov）"""
        if not self.gcov_path:
            return None
        
        try:
            logs.append("📊 开始收集行覆盖率数据...")
            
            # 如果 lcov 可用，使用 lcov 收集数据（更准确）
            if self.lcov_path:
                return await self._collect_coverage_with_lcov(build_dir, logs)
            else:
                # 仅使用 gcov（功能有限）
                return await self._collect_coverage_with_gcov(build_dir, logs)
        except Exception as e:
            logger.warning(f"覆盖率收集异常: {str(e)}")
            logs.append(f"⚠️ 覆盖率收集异常: {str(e)}")
            return None
    
    async def _collect_coverage_with_lcov(self, build_dir: Path, logs: List[str]) -> Optional[Dict[str, Any]]:
        """使用 lcov 收集覆盖率数据"""
        try:
            coverage_info = build_dir / "coverage.info"
            
            lcov_cmd = [
                self.lcov_path,
                "--capture",
                "--directory", str(build_dir),
                "--output-file", str(coverage_info)
            ]
            
            process = await asyncio.to_thread(
                self._run_sync_cmd, lcov_cmd, str(build_dir)
            )
            
            if process.returncode == 0:
                logs.append("✅ 覆盖率数据收集成功")
                # 解析 lcov 信息文件
                coverage_data = self._parse_lcov_info(coverage_info)
                return coverage_data
            else:
                logs.append(f"⚠️ lcov 收集失败: {process.stderr}")
                return None
        except Exception as e:
            logs.append(f"⚠️ lcov 收集异常: {str(e)}")
            return None
    
    async def _collect_coverage_with_gcov(self, build_dir: Path, logs: List[str]) -> Optional[Dict[str, Any]]:
        """仅使用 gcov 收集覆盖率数据"""
        try:
            # 查找所有 .gcda 文件
            gcda_files = list(build_dir.rglob("*.gcda"))
            if not gcda_files:
                logs.append("⚠️ 未找到覆盖率数据文件 (.gcda)，可能测试未运行或覆盖率标志未生效")
                return {
                    "percentage": 0.0,
                    "lines_covered": 0,
                    "lines_total": 0,
                    "warning": "未找到覆盖率数据文件，请确保测试已运行"
                }
            
            logs.append(f"📊 找到 {len(gcda_files)} 个覆盖率数据文件")
            
            # 使用 gcov 处理每个 .gcda 文件并解析 .gcov 文件
            total_lines = 0
            covered_lines = 0
            total_functions = 0
            covered_functions = 0
            
            for gcda_file in gcda_files:
                # 运行 gcov 生成 .gcov 文件
                # gcov 需要源文件路径，从 .gcda 文件名推断
                gcda_name = gcda_file.stem  # 例如 "test_cases.gcda" -> "test_cases"
                gcov_cmd = [self.gcov_path, "-b", "-c", str(gcda_file)]
                
                process = await asyncio.to_thread(
                    self._run_sync_cmd, gcov_cmd, str(build_dir)
                )
                
                # 查找生成的 .gcov 文件
                gcov_files = list(build_dir.glob(f"{gcda_name}.gcov"))
                if not gcov_files:
                    # 尝试查找所有 .gcov 文件
                    gcov_files = list(build_dir.glob("*.gcov"))
                
                # 解析 .gcov 文件
                for gcov_file in gcov_files:
                    try:
                        content = gcov_file.read_text(encoding='utf-8', errors='ignore')
                        for line in content.split('\n'):
                            # .gcov 文件格式：执行次数:行号:源代码内容
                            # 例如：1:10:void test() {
                            parts = line.split(':', 2)
                            if len(parts) >= 2:
                                try:
                                    exec_count = parts[0].strip()
                                    line_num = parts[1].strip()
                                    
                                    # 跳过非代码行（如注释、空行等）
                                    if exec_count in ['-', '#']:
                                        continue
                                    
                                    # 统计可执行行
                                    if exec_count.isdigit() or exec_count == '#####':
                                        total_lines += 1
                                        if exec_count != '#####' and int(exec_count) > 0:
                                            covered_lines += 1
                                except (ValueError, IndexError):
                                    continue
                    except Exception as e:
                        logger.warning(f"解析 .gcov 文件失败 {gcov_file}: {str(e)}")
                        continue
            
            # 计算覆盖率百分比
            percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
            
            logs.append(f"📊 覆盖率统计: {covered_lines}/{total_lines} 行 ({percentage:.1f}%)")
            
            return {
                "percentage": round(percentage, 2),
                "lines_covered": covered_lines,
                "lines_total": total_lines,
                "branches_covered": 0,  # gcov 单独使用时难以统计分支
                "branches_total": 0,
                "functions_covered": covered_functions,
                "functions_total": total_functions,
                "warning": "仅使用 gcov，建议安装 lcov 以获得完整覆盖率报告（包括分支覆盖率）"
            }
        except Exception as e:
            logger.warning(f"gcov 收集异常: {str(e)}")
            logs.append(f"⚠️ gcov 收集异常: {str(e)}")
            return {
                "percentage": 0.0,
                "lines_covered": 0,
                "lines_total": 0,
                "warning": f"覆盖率收集失败: {str(e)}"
            }
    
    def _parse_lcov_info(self, info_file: Path) -> Dict[str, Any]:
        """解析 lcov info 文件获取覆盖率统计"""
        try:
            if not info_file.exists():
                return {}
            
            content = info_file.read_text(encoding='utf-8', errors='ignore')
            
            # 解析 lcov 格式
            lines_covered = 0
            lines_total = 0
            branches_covered = 0
            branches_total = 0
            functions_covered = 0
            functions_total = 0
            
            # 查找汇总行（通常在文件末尾）
            for line in content.split('\n'):
                if line.startswith('LF:'):  # Lines found
                    lines_total = int(line.split(':')[1].strip())
                elif line.startswith('LH:'):  # Lines hit
                    lines_covered = int(line.split(':')[1].strip())
                elif line.startswith('BRF:'):  # Branches found
                    branches_total = int(line.split(':')[1].strip())
                elif line.startswith('BRH:'):  # Branches hit
                    branches_covered = int(line.split(':')[1].strip())
                elif line.startswith('FNF:'):  # Functions found
                    functions_total = int(line.split(':')[1].strip())
                elif line.startswith('FNH:'):  # Functions hit
                    functions_covered = int(line.split(':')[1].strip())
            
            # 如果没有找到汇总行，尝试从各个源文件汇总
            if lines_total == 0:
                current_file = None
                file_lines_total = 0
                file_lines_covered = 0
                
                for line in content.split('\n'):
                    if line.startswith('SF:'):  # Source file
                        if current_file and file_lines_total > 0:
                            lines_total += file_lines_total
                            lines_covered += file_lines_covered
                        current_file = line.split(':', 1)[1].strip()
                        file_lines_total = 0
                        file_lines_covered = 0
                    elif line.startswith('DA:'):  # Line data
                        parts = line.split(':')[1].split(',')
                        if len(parts) >= 2:
                            file_lines_total += 1
                            if int(parts[1].strip()) > 0:
                                file_lines_covered += 1
                
                # 添加最后一个文件
                if current_file and file_lines_total > 0:
                    lines_total += file_lines_total
                    lines_covered += file_lines_covered
            
            percentage = (lines_covered / lines_total * 100) if lines_total > 0 else 0.0
            
            return {
                "percentage": round(percentage, 2),
                "lines_covered": lines_covered,
                "lines_total": lines_total,
                "branches_covered": branches_covered,
                "branches_total": branches_total,
                "functions_covered": functions_covered,
                "functions_total": functions_total
            }
        except Exception as e:
            logger.warning(f"解析 lcov 信息文件失败: {str(e)}")
            return {}
