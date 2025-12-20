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
            
            catch_main_cpp = """
#include "catch_amalgamated.hpp"
#include <QApplication>
int main( int argc, char* argv[] ) {
  QApplication a(argc, argv); // 确保有 GUI 环境上下文
  return Catch::Session().run( argc, argv );
}
"""
            (build_dir / "catch_main_wrapper.cpp").write_text(catch_main_cpp, encoding='utf-8')
            (build_dir / "test_cases.cpp").write_text(test_code, encoding='utf-8')
            
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
            cpp_sources_str = "\n    ".join([f'"{f}"' for f in cpp_files])
            ui_sources_str = "\n    ".join([f'"{f}"' for f in ui_files])

            cmake_content = f"""
cmake_minimum_required(VERSION 3.16)
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
            return {
                "success": True, 
                "logs": "\n".join(logs) + "\n\n--- 终端输出 ---\n" + run_res.stdout + run_res.stderr,
                "summary": summary
            }
            
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
