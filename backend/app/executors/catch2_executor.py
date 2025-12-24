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
        
        # 设置编码环境变量，确保 CMake 能正确处理路径
        env['LC_ALL'] = 'C.UTF-8'
        env['LANG'] = 'C.UTF-8'
        if sys.platform == "win32":
            # Windows 上设置代码页为 UTF-8（Windows 10+）
            env['PYTHONIOENCODING'] = 'utf-8'
            # 尝试设置系统代码页（需要管理员权限，所以可能失败）
            try:
                import subprocess as sp
                sp.run(['chcp', '65001'], shell=True, capture_output=True, check=False)
            except:
                pass
        
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

        # 创建临时目录，避免中文路径问题
        # CMake 的 AutoGen 功能无法正确处理包含非 ASCII 字符的路径
        def is_ascii_path(path_str: str) -> bool:
            """检查路径是否只包含 ASCII 字符"""
            try:
                return all(ord(c) < 128 for c in path_str)
            except:
                return False
        
        def get_safe_temp_dir():
            """获取安全的临时目录（ASCII 路径）"""
            # 优先级 1: 使用项目目录下的临时目录（通常不包含中文）
            project_temp = self.base_dir / "temp" / "qt_tester"
            try:
                project_temp.mkdir(parents=True, exist_ok=True)
                project_temp_str = str(project_temp.resolve())
                if is_ascii_path(project_temp_str):
                    logs.append(f"✅ 使用项目临时目录: {project_temp_str}")
                    return project_temp
                else:
                    logs.append(f"⚠️  项目临时目录包含非 ASCII 字符: {project_temp_str}")
            except Exception as e:
                logs.append(f"⚠️  无法使用项目临时目录: {e}")
            
            # 优先级 2: 检查系统临时目录
            system_temp = Path(tempfile.gettempdir())
            system_temp_str = str(system_temp.resolve())
            if is_ascii_path(system_temp_str):
                temp_dir = system_temp / "qt_tester"
                try:
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    logs.append(f"✅ 使用系统临时目录: {str(temp_dir.resolve())}")
                    return temp_dir
                except Exception as e:
                    logs.append(f"⚠️  无法创建系统临时目录: {e}")
            else:
                logs.append(f"⚠️  系统临时目录包含非 ASCII 字符: {system_temp_str}")
            
            # 优先级 3: 使用备用路径（Windows: C:\temp, Linux/Mac: /tmp）
            if sys.platform == "win32":
                fallback = Path("C:/temp/qt_tester")
            else:
                fallback = Path("/tmp/qt_tester")
            try:
                fallback.mkdir(parents=True, exist_ok=True)
                fallback_str = str(fallback.resolve())
                if is_ascii_path(fallback_str):
                    logs.append(f"✅ 使用备用临时目录: {fallback_str}")
                    return fallback
                else:
                    logs.append(f"⚠️  备用临时目录也包含非 ASCII 字符: {fallback_str}")
            except Exception as e:
                logs.append(f"⚠️  无法创建备用临时目录: {e}")
            
            # 最后的备用方案：使用项目目录（即使可能包含非 ASCII）
            logs.append(f"⚠️  使用项目目录作为最后备用方案（可能包含非 ASCII 字符）")
            return project_temp
        
        temp_dir = get_safe_temp_dir()
        temp_dir.mkdir(parents=True, exist_ok=True)
        work_id = os.urandom(4).hex()
        build_dir = temp_dir / work_id
        build_dir.mkdir(parents=True, exist_ok=True)
        
        build_dir_str = str(build_dir.resolve())
        logs.append(f"📁 构建目录: {build_dir_str}")
        
        # 检查路径是否包含非 ASCII 字符
        if not is_ascii_path(build_dir_str):
            logs.append("⚠️  警告: 构建目录路径包含非 ASCII 字符")
            logs.append("   这可能导致 CMake AutoGen 功能出现问题")
            logs.append("   如果编译失败，请考虑将项目移动到只包含 ASCII 字符的路径")

        try:
            # 1. 物理搬迁所有相关文件
            logs.append("📦 准备 Catch2 库文件...")
            if not (self.catch2_lib_dir / "catch_amalgamated.cpp").exists():
                logs.append(f"❌ Catch2 库文件不存在: {self.catch2_lib_dir / 'catch_amalgamated.cpp'}")
                return {"success": False, "logs": "\n".join(logs), "summary": {"total": 0, "passed": 0, "failed": 0}}
            
            shutil.copy2(self.catch2_lib_dir / "catch_amalgamated.cpp", build_dir / "catch_amalgamated.cpp")
            shutil.copy2(self.catch2_lib_dir / "catch_amalgamated.hpp", build_dir / "catch_amalgamated.hpp")
            logs.append("✅ Catch2 库文件已复制")
            
<<<<<<< HEAD
=======
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
            
            # 验证测试代码
            is_valid, error_msg = self._validate_test_code(cleaned_test_code)
            if not is_valid:
                logs.append(f"⚠️ 测试代码验证警告: {error_msg}")
                logs.append("   但将继续尝试编译，请查看编译错误信息")
            else:
                logs.append("✅ 测试代码验证通过")
            
            # 生成测试辅助头文件，解决私有成员访问问题
            test_helper_header = """
#ifndef TEST_HELPER_H
#define TEST_HELPER_H

// 测试辅助头文件：为测试代码提供必要的访问权限和类型定义

// 前向声明
class MainWindow;
struct WriteDiagramItem;
struct WriteDiagramPath;
class DiagramItem;

// 测试辅助类：通过 friend 声明访问 MainWindow 的私有成员
// 注意：这需要在 MainWindow 类定义中添加 friend class TestHelper;
class TestHelper {
public:
    // 这些函数将在测试代码中通过 MainWindow 的公共接口或 friend 访问
    // 如果 MainWindow 没有 friend 声明，这些函数将无法编译
    // 但我们可以通过宏定义来临时改变访问权限
};

// 如果 MainWindow 类定义在 mainwindow.h 中，我们需要在包含它之前定义这个宏
// 但更好的方法是在 mainwindow.h 中添加条件编译
#define TESTING_MODE 1

#endif // TEST_HELPER_H
"""
            
            # 检查测试代码是否需要访问私有成员
            needs_test_helper = any(keyword in cleaned_test_code for keyword in [
                'saveSaveFilePath', 'loadSaveFilePath', 'saveSavePicPath', 'loadSavePicPath',
                'sceneVector', 'viewVector', 'tabwidget', 'scene', 'undoStack',
                'newScene', 'closeScene', 'sceneChanged', 'getStructList', 'getStructList1',
                'handleFindText', 'handleReplaceText', 'deleteItem', 'bringToFront', 'sendToBack',
                'savefilestack', 'autoCleanStack', 'currentTextItem', 'WriteDiagramItem',
                'WriteDiagramPath', 'DiagramItem::Top', 'DiagramItem::Bottom'
            ])
            
            if needs_test_helper:
                # 生成测试辅助头文件
                (build_dir / "test_helper.h").write_text(test_helper_header, encoding='utf-8')
                logs.append("✅ 测试辅助头文件已生成")
                
                # 在测试代码开头添加包含测试辅助头文件的指令
                # 但更好的方法是在 mainwindow.h 中添加 friend 声明
                # 由于我们无法修改用户的源代码，我们只能通过修改测试代码来解决
                # 实际上，最好的方法是修改测试代码生成逻辑，只使用公共接口
                # 但这里我们提供一个临时的解决方案：在测试代码前添加必要的类型定义
                
                # 检查是否需要添加类型定义
                type_defs = ""
                needs_qstring = False
                
                if 'WriteDiagramItem' in cleaned_test_code:
                    # 检查是否已经有完整定义
                    has_full_def = 'struct WriteDiagramItem' in cleaned_test_code and '{' in cleaned_test_code.split('struct WriteDiagramItem')[1].split('}')[0] if 'struct WriteDiagramItem' in cleaned_test_code else False
                    if not has_full_def:
                        type_defs += """
// 临时类型定义（如果源代码中没有完整定义）
#ifndef WRITE_DIAGRAM_ITEM_DEFINED
#define WRITE_DIAGRAM_ITEM_DEFINED
#include <QString>
struct WriteDiagramItem {
    int x, y;
    int width, height;
    int rbg[3];
    QString internalText;
    int type;
    int itemtype;
    int texttype;
    int textsize;
    int boldtype;
    int itlatic;
    int textrbg[3];
};
#endif
"""
                        needs_qstring = True
                
                if 'WriteDiagramPath' in cleaned_test_code:
                    has_full_def = 'struct WriteDiagramPath' in cleaned_test_code and '{' in cleaned_test_code.split('struct WriteDiagramPath')[1].split('}')[0] if 'struct WriteDiagramPath' in cleaned_test_code else False
                    if not has_full_def:
                        type_defs += """
#ifndef WRITE_DIAGRAM_PATH_DEFINED
#define WRITE_DIAGRAM_PATH_DEFINED
struct WriteDiagramPath {
    int start;
    int end;
    // 添加其他必要的字段
};
#endif
"""
                
                # 处理 DiagramItem::Top 和 DiagramItem::Bottom
                # 在测试代码中替换为可能的正确值
                if 'DiagramItem::Top' in cleaned_test_code or 'DiagramItem::Bottom' in cleaned_test_code:
                    # 尝试在源代码中查找 DiagramItem 的定义
                    # 如果找不到，使用替换策略
                    cleaned_test_code = cleaned_test_code.replace('DiagramItem::Top', '0')  # 通常 Top = 0
                    cleaned_test_code = cleaned_test_code.replace('DiagramItem::Bottom', '1')  # 通常 Bottom = 1
                    logs.append("⚠️  已替换 DiagramItem::Top/Bottom 为数值常量（如果编译失败，请检查源代码中的实际枚举值）")
                
                if type_defs:
                    # 在测试代码的 include 部分之后添加类型定义
                    lines = cleaned_test_code.split('\n')
                    insert_pos = 0
                    last_include_pos = -1
                    for i, line in enumerate(lines):
                        if line.strip().startswith('#include'):
                            last_include_pos = i
                            insert_pos = i + 1
                        elif line.strip() and not line.strip().startswith('//') and not line.strip().startswith('#') and insert_pos > 0:
                            # 找到第一个非 include/注释/预处理指令的行
                            break
                    
                    # 如果没有找到 include，在文件开头插入
                    if insert_pos == 0:
                        insert_pos = 0
                        # 确保包含必要的头文件
                        if needs_qstring and '#include <QString>' not in cleaned_test_code and '#include <QtCore/QString>' not in cleaned_test_code:
                            type_defs = '#include <QString>\n' + type_defs
                    
                    # 在适当位置插入类型定义
                    lines.insert(insert_pos, type_defs)
                    cleaned_test_code = '\n'.join(lines)
                    logs.append("✅ 已添加必要的类型定义")
            
            (build_dir / "test_cases.cpp").write_text(cleaned_test_code, encoding='utf-8')
            logs.append("✅ 测试代码已清理并写入")
            
>>>>>>> origin/tzf
            src_file_full = Path(source_file_path).resolve()
            src_dir = src_file_full.parent
            cpp_files = ["catch_main_wrapper.cpp", "catch_amalgamated.cpp", "test_cases.cpp"]
            ui_files = []
            qrc_files = []
            
            blocklist = {"main.cpp", "mygraphicsview.cpp"}  # 避免已知与测试无关且会触发编译错误的文件

<<<<<<< HEAD
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
=======
            # 检查是否需要修改 mainwindow.h 以支持测试
            mainwindow_h_modified = False
            mainwindow_h_path = None
            
            for item in src_dir.iterdir():
                if item.is_file():
                    ext = item.suffix.lower()
                    if ext in {'.h', '.hpp', '.hh', '.hxx', '.ui', '.qrc', '.png', '.jpg', '.ico'}:
                        if item.name.lower() in {'mainwindow.h', 'mainwindow.hpp'}:
                            # 修改 mainwindow.h 以支持测试访问私有成员
                            mainwindow_h_path = build_dir / item.name
                            try:
                                content = item.read_text(encoding='utf-8', errors='ignore')
                                # 在文件开头添加测试模式宏定义
                                if '#ifndef TESTING_MODE' not in content:
                                    # 在第一个 #ifndef 或文件开头添加
                                    lines = content.split('\n')
                                    insert_pos = 0
                                    for i, line in enumerate(lines):
                                        if line.strip().startswith('#ifndef') or line.strip().startswith('#pragma'):
                                            insert_pos = i
                                            break
                                    
                                    # 在适当位置插入测试模式定义
                                    test_macro = """
// 测试模式：允许测试代码访问私有成员
#ifndef TESTING_MODE
#define TESTING_MODE 1
#endif
"""
                                    lines.insert(insert_pos, test_macro)
                                    content = '\n'.join(lines)
                                
                                # 替换 private: 为条件编译，在测试模式下使用 public:
                                # 使用正则表达式匹配 private: 关键字
                                import re
                                # 匹配 private: 后面可能跟注释的情况，但要避免匹配 protected: 和 public:
                                # 只匹配独立的 private: 行
                                pattern = r'^(\s*)private\s*:(\s*(?://.*)?)$'
                                
                                def replace_private(match):
                                    indent = match.group(1)
                                    comment = match.group(2) if match.group(2) else ''
                                    return f'{indent}#ifndef TESTING_MODE\n{indent}private:{comment}\n{indent}#else\n{indent}public:  // TESTING_MODE: 临时公开以支持测试{comment}\n{indent}#endif'
                                
                                modified_content = re.sub(pattern, replace_private, content, flags=re.MULTILINE)
                                
                                # 如果内容有变化，写入修改后的文件
                                if modified_content != content:
                                    mainwindow_h_path.write_text(modified_content, encoding='utf-8')
                                    mainwindow_h_modified = True
                                    logs.append(f"✅ 已修改 {item.name} 以支持测试访问")
                                else:
                                    shutil.copy2(item, mainwindow_h_path)
                            except Exception as e:
                                logs.append(f"⚠️  无法修改 {item.name}: {e}")
                                shutil.copy2(item, mainwindow_h_path)
                        else:
                            shutil.copy2(item, build_dir / item.name)
                        if ext == '.ui': ui_files.append(item.name)
>>>>>>> origin/tzf
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
            logs.append(f"🔧 CMake: {cmake_exe}")
            
            # 检查 CMake 是否可用
            cmake_check = await asyncio.to_thread(self._run_sync_cmd, [cmake_exe, "--version"], str(build_dir))
            if cmake_check.returncode != 0:
                logs.append(f"❌ CMake 不可用，请确保已安装 CMake 并添加到 PATH")
                return {"success": False, "logs": "\n".join(logs), "summary": {"total": 0, "passed": 0, "failed": 0}}
            logs.append(f"✅ CMake 版本: {cmake_check.stdout.split()[2] if cmake_check.stdout else '未知'}")
            
            cpp_sources_str = "\n    ".join([f'"{f}"' for f in cpp_files])
            ui_sources_str = "\n    ".join([f'"{f}"' for f in ui_files])
<<<<<<< HEAD
            qrc_sources_str = "\n    ".join([f'"{f}"' for f in qrc_files])
=======
            
            logs.append(f"📝 源文件数量: {len(cpp_files)}")
            logs.append(f"📝 UI文件数量: {len(ui_files)}")
>>>>>>> origin/tzf

            # 检查是否启用覆盖率统计（如果工具可用）
            coverage_flags = ""
            if self.gcov_path:
                coverage_flags = "-fprofile-arcs -ftest-coverage"
                logs.append("📊 检测到 gcov，将启用行覆盖率统计")
            
            cmake_content = f"""
cmake_minimum_required(VERSION 3.16)
# 限制最大版本为 3.28，避免 CMake 4.x 的兼容性问题
if(CMAKE_VERSION VERSION_GREATER_EQUAL "4.0")
    message(WARNING "CMake 4.x detected. For better compatibility, consider using CMake 3.16-3.28")
endif()
project(Catch2Test LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)

# 启用 AutoGen（MOC/UIC/RCC）
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# 设置 AutoGen 输出目录为二进制目录下的子目录（使用相对路径避免编码问题）
# 注意：使用 CMAKE_CURRENT_BINARY_DIR 的相对路径，而不是绝对路径
set(CMAKE_AUTOGEN_BUILD_DIR "${{CMAKE_CURRENT_BINARY_DIR}}/autogen")

# 确保 AutoGen 目录存在
file(MAKE_DIRECTORY "${{CMAKE_AUTOGEN_BUILD_DIR}}")

# 设置 AutoGen 并行处理（提高性能）
set(CMAKE_AUTOGEN_PARALLEL 1)

# 终极兼容模式：忽略 override，放宽类型检查
add_definitions(-Doverride=)
set(CMAKE_CXX_FLAGS "${{CMAKE_CXX_FLAGS}} -fpermissive {coverage_flags}")

# 定义测试模式宏，允许测试代码访问私有成员
add_definitions(-DTESTING_MODE=1)

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
            
            # 清理可能存在的旧 CMake 缓存（避免 AutoGen 问题）
            cmake_cache = build_dir / "CMakeCache.txt"
            cmake_files = build_dir / "CMakeFiles"
            if cmake_cache.exists():
                try:
                    cmake_cache.unlink()
                    logs.append("🧹 已清理旧的 CMakeCache.txt")
                except Exception as e:
                    logs.append(f"⚠️  无法删除 CMakeCache.txt: {e}")
            if cmake_files.exists():
                try:
                    shutil.rmtree(cmake_files)
                    logs.append("🧹 已清理旧的 CMakeFiles 目录")
                except Exception as e:
                    logs.append(f"⚠️  无法删除 CMakeFiles 目录: {e}")
            
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
                
                # 添加常见错误诊断
                error_output = (build_res.stdout or "") + (build_res.stderr or "")
                error_lower = error_output.lower()
                
                if "autogen" in error_lower or "autogeninfo.json" in error_lower or "dependinfo.cmake" in error_lower:
                    logs.append("--- 诊断：CMake AutoGen 错误 ---")
                    logs.append("   可能原因：")
                    logs.append("   1. 构建目录路径包含非 ASCII 字符（如中文），导致 AutoGen 无法正确处理")
                    logs.append("   2. 文件权限问题，AutoGen 无法读取或写入文件")
                    logs.append("   3. CMake 缓存损坏")
                    logs.append("   解决方案：")
                    logs.append("   1. 系统已自动使用 ASCII 路径的临时目录")
                    logs.append("   2. 如果问题仍然存在，请检查文件权限")
                    logs.append("   3. 尝试清理 CMake 缓存：删除构建目录中的 CMakeFiles 和 CMakeCache.txt")
                elif "no matching function" in error_lower or "no matching function for call" in error_lower:
                    logs.append("--- 诊断：函数调用不匹配 ---")
                    logs.append("   可能原因：")
                    logs.append("   1. 函数参数数量或类型不匹配")
                    logs.append("   2. 构造函数缺少必需参数")
                    logs.append("   3. 调用了不存在的重载函数")
                    logs.append("   解决方案：检查函数签名，确保参数完全匹配")
                elif "undefined reference" in error_lower:
                    logs.append("--- 诊断：未定义的引用 ---")
                    logs.append("   可能原因：")
                    logs.append("   1. 缺少必要的头文件包含")
                    logs.append("   2. 链接库缺失")
                    logs.append("   3. 函数声明和定义不匹配")
                    logs.append("   解决方案：确保包含所有必要的头文件")
                elif "incomplete type" in error_lower:
                    logs.append("--- 诊断：不完整类型 ---")
                    logs.append("   可能原因：")
                    logs.append("   1. 缺少前向声明或头文件")
                    logs.append("   2. Qt 类未正确包含")
                    logs.append("   3. 模板类未完全实例化")
                    logs.append("   解决方案：添加相应的头文件包含")
                elif "cannot convert" in error_lower or "invalid conversion" in error_lower:
                    logs.append("--- 诊断：类型转换错误 ---")
                    logs.append("   可能原因：")
                    logs.append("   1. 参数类型不匹配")
                    logs.append("   2. 缺少必要的类型转换")
                    logs.append("   解决方案：检查参数类型，使用正确的类型或添加转换")
                elif "was not declared" in error_lower or "does not name a type" in error_lower:
                    logs.append("--- 诊断：未声明的标识符 ---")
                    logs.append("   可能原因：")
                    logs.append("   1. 缺少头文件包含")
                    logs.append("   2. 命名空间问题")
                    logs.append("   3. 类或函数名拼写错误")
                    logs.append("   解决方案：检查是否包含相应的头文件，确认类名和函数名正确")
                elif "private" in error_lower and ("member" in error_lower or "within this context" in error_lower):
                    logs.append("--- 诊断：访问私有成员 ---")
                    logs.append("   可能原因：")
                    logs.append("   1. 尝试调用私有或受保护的成员函数")
                    logs.append("   2. 访问私有成员变量")
                    logs.append("   解决方案：只能测试公共接口，通过公共方法间接测试")
                elif "protected" in error_lower and ("member" in error_lower or "within this context" in error_lower):
                    logs.append("--- 诊断：访问受保护成员 ---")
                    logs.append("   可能原因：")
                    logs.append("   1. 尝试调用受保护的成员函数（如 paint(), mousePressEvent()）")
                    logs.append("   解决方案：只能测试公共接口，通过公共方法间接测试")
                
                logs.append("--- 故障排查建议 ---")
                logs.append("1. 检查生成的测试代码是否有语法错误")
                logs.append("2. 检查是否包含了不存在的头文件或库")
                logs.append("3. 检查是否使用了不支持的 C++ 特性")
                logs.append("4. 检查是否调用了私有/受保护的成员函数")
                logs.append("5. 检查函数参数是否完全匹配")
                logs.append("6. 查看上方的编译错误信息，定位具体问题")
                logs.append("7. 如果问题持续，尝试重新生成测试用例")
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

            # 检查退出码和输出
            if run_res.returncode != 0:
                logs.append(f"⚠️ 测试程序异常退出，退出码: {run_res.returncode}")
                if run_res.returncode == 3221226505:  # 0xC0000005 (Windows 访问冲突)
                    logs.append("   这是 Windows 访问冲突错误 (0xC0000005)，可能原因：")
                    logs.append("   1. 测试代码访问了无效内存")
                    logs.append("   2. 调用了未初始化的对象")
                    logs.append("   3. Qt 对象生命周期管理问题")
                    logs.append("   4. 空指针解引用")
                    logs.append("   解决方案：检查测试代码中的对象初始化和指针使用")
                elif run_res.returncode == -1073741819:  # 0xC0000005 (另一种表示)
                    logs.append("   这是访问冲突错误，可能原因：")
                    logs.append("   1. 测试代码访问了无效内存")
                    logs.append("   2. 调用了未初始化的对象")
                    logs.append("   解决方案：检查测试代码中的对象初始化")
                elif run_res.returncode == 3221226506:  # 0xC0000006 (堆栈溢出)
                    logs.append("   这是堆栈溢出错误，可能原因：")
                    logs.append("   1. 递归调用过深")
                    logs.append("   2. 局部变量过大")
                    logs.append("   解决方案：简化测试代码，避免深度递归")
            
            # 如果没有任何标准输出/错误输出，提示用户可能没有生成用例或程序提前退出
            if not run_res.stdout and not run_res.stderr:
                logs.append(f"⚠️ test_runner 无输出，退出码 {run_res.returncode}")
                logs.append("   可能的原因：")
                logs.append("   1. 测试代码中没有定义任何 TEST_CASE")
                logs.append("   2. 程序在初始化时崩溃")
                logs.append("   3. 测试代码有运行时错误")
                logs.append("   4. 程序提前退出（访问冲突、段错误等）")
            
            summary = self._parse_catch2_results(run_res.stdout)
            
<<<<<<< HEAD
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
=======
            # 如果解析结果为空，说明可能没有测试用例
            if summary["total"] == 0 and not run_res.stdout:
                logs.append("⚠️ 未检测到任何测试用例")
                logs.append("   请检查生成的测试代码是否包含 TEST_CASE 定义")
            
            return {
>>>>>>> origin/tzf
                "success": True, 
                "logs": "\n".join(logs) + "\n\n--- 终端输出 ---\n" + (run_res.stdout or "") + (run_res.stderr or ""),
                "summary": summary
            }
            
            # 如果收集到覆盖率数据，添加到结果中（使用 coverage_data 字段，与现有代码兼容）
            if coverage_data:
                result["coverage_data"] = coverage_data
            
            return result
            
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

    def _validate_test_code(self, test_code: str) -> tuple[bool, str]:
        """验证测试代码是否有效"""
        issues = []
        
        # 检查是否包含 TEST_CASE
        if 'TEST_CASE' not in test_code:
            issues.append("未找到 TEST_CASE 定义")
        
        # 检查是否包含必要的头文件
        if '#include "catch_amalgamated.hpp"' not in test_code and '#include <catch2/' not in test_code:
            issues.append("未包含 Catch2 头文件")
        
        # 检查是否有明显的语法错误（如未闭合的括号）
        open_braces = test_code.count('{')
        close_braces = test_code.count('}')
        if open_braces != close_braces:
            issues.append(f"括号不匹配：开括号 {open_braces}，闭括号 {close_braces}")
        
        # 检查是否有未闭合的引号（简单检查）
        single_quotes = test_code.count("'")
        double_quotes = test_code.count('"')
        # 注意：这个检查不完美，因为字符串中可能包含引号，但可以作为初步检查
        if single_quotes % 2 != 0:
            issues.append("可能有不匹配的单引号")
        if double_quotes % 2 != 0:
            issues.append("可能有不匹配的双引号")
        
        if issues:
            return False, "; ".join(issues)
        return True, ""

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
