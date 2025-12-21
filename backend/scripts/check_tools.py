#!/usr/bin/env python3
"""
工具检测脚本
检测所有测试工具是否已下载、安装和可用
"""
import os
import sys
import shutil
import json
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.core.config import settings


class ToolChecker:
    """工具检测器"""
    
    def __init__(self):
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        # 工具基础路径相对于项目根目录
        tools_base_rel = Path(settings.TOOLS_BASE_PATH)
        if tools_base_rel.is_absolute():
            self.tools_base = tools_base_rel.resolve()
        else:
            self.tools_base = (project_root / tools_base_rel).resolve()
        self.results: Dict[str, Dict[str, Any]] = {}
    
    def check_tool(self, name: str, path: str, executable: str = "", 
                   download_url: str = "", needs_build: bool = False) -> Dict[str, Any]:
        """检测单个工具"""
        if path:
            # 如果路径是相对路径，相对于项目根目录解析
            tool_path = Path(path)
            if not tool_path.is_absolute():
                tool_path = project_root / tool_path
            tool_path = tool_path.resolve()
        else:
            tool_path = None
        result = {
            "name": name,
            "installed": False,
            "path": str(tool_path) if tool_path else None,
            "path_exists": tool_path.exists() if tool_path else False,
            "executable": executable,
            "executable_found": False,
            "executable_path": None,
            "version": "unknown",
            "needs_build": needs_build,
            "download_url": download_url,
            "status": "not_installed"
        }
        
        # 检查路径是否存在
        if tool_path and tool_path.exists():
            result["installed"] = True
            result["status"] = "installed"
        
        # 检查可执行文件
        if executable:
            exe_path = self._find_executable(executable, tool_path)
            if exe_path:
                result["executable_found"] = True
                result["executable_path"] = str(exe_path)
                result["status"] = "ready"
            else:
                if result["installed"]:
                    result["status"] = "needs_build" if needs_build else "executable_not_found"
        
        # 尝试获取版本信息
        if result["executable_found"]:
            result["version"] = self._get_version(exe_path, executable)
        
        return result
    
    def _find_executable(self, executable_name: str, base_path: Optional[Path] = None) -> Optional[Path]:
        """查找可执行文件"""
        # 检查系统 PATH
        exe_path = shutil.which(executable_name)
        if exe_path:
            return Path(exe_path)
        
        # 检查基础路径下的常见位置
        if base_path:
            common_paths = [
                base_path / executable_name,
                base_path / f"{executable_name}.exe",
                base_path / "build" / executable_name,
                base_path / "build" / f"{executable_name}.exe",
                base_path / "bin" / executable_name,
                base_path / "bin" / f"{executable_name}.exe",
            ]
            
            for path in common_paths:
                if path.exists() and path.is_file():
                    return path
        
        return None
    
    def _get_version(self, exe_path: Path, executable_name: str) -> str:
        """获取工具版本"""
        try:
            import subprocess
            # 尝试常见的版本参数
            for flag in ["--version", "-v", "-V", "version"]:
                try:
                    result = subprocess.run(
                        [str(exe_path), flag],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        # 提取版本号（简单处理）
                        output = result.stdout.strip() or result.stderr.strip()
                        if output:
                            # 尝试提取版本号
                            import re
                            version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', output)
                            if version_match:
                                return version_match.group(1)
                            return output.split('\n')[0][:50]  # 返回第一行前50个字符
                except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                    continue
        except Exception:
            pass
        
        return "unknown"
    
    def check_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """检测所有工具"""
        print("🔍 开始检测工具...")
        print(f"工具基础路径: {self.tools_base}\n")
        
        # UTBotCpp
        self.results["utbot"] = self.check_tool(
            "UTBotCpp",
            settings.UTBOT_PATH,
            executable="utbot",
            download_url="https://github.com/UnitTestBot/UTBotCpp",
            needs_build=True
        )
        
        # Clazy
        self.results["clazy"] = self.check_tool(
            "Clazy",
            settings.CLAZY_PATH,
            executable=settings.CLAZY_EXECUTABLE,
            download_url="https://github.com/KDE/clazy",
            needs_build=True
        )
        
        # Cppcheck
        self.results["cppcheck"] = self.check_tool(
            "Cppcheck",
            settings.CPPCHECK_PATH,
            executable=settings.CPPCHECK_EXECUTABLE,
            download_url="https://github.com/danmar/cppcheck",
            needs_build=False
        )
        
        # gcov
        self.results["gcov"] = self.check_tool(
            "gcov",
            settings.GCOV_PATH if settings.GCOV_PATH else "",
            executable="gcov",
            download_url="通常随 GCC/MinGW 安装",
            needs_build=False
        )
        
        # lcov
        self.results["lcov"] = self.check_tool(
            "lcov",
            settings.LCOV_PATH if settings.LCOV_PATH else "",
            executable="lcov",
            download_url="https://github.com/linux-test-project/lcov",
            needs_build=False
        )
        
        # Valgrind (Windows 不支持，检查 Dr. Memory)
        self.results["valgrind"] = self.check_tool(
            "Valgrind/Dr. Memory",
            settings.DRMEMORY_PATH,
            executable=settings.DRMEMORY_EXECUTABLE,
            download_url="https://github.com/DynamoRIO/drmemory",
            needs_build=False
        )
        
        # GammaRay
        self.results["gammaray"] = self.check_tool(
            "GammaRay",
            settings.GAMMARAY_PATH,
            executable="gammaray",
            download_url="https://github.com/KDAB/GammaRay",
            needs_build=True
        )
        
        return self.results
    
    def print_report(self):
        """打印检测报告"""
        print("\n" + "="*80)
        print("工具检测报告")
        print("="*80 + "\n")
        
        for tool_name, result in self.results.items():
            status_icon = {
                "ready": "✅",
                "installed": "📦",
                "needs_build": "🔨",
                "executable_not_found": "⚠️",
                "not_installed": "❌"
            }.get(result["status"], "❓")
            
            print(f"{status_icon} {result['name']}")
            print(f"   状态: {result['status']}")
            print(f"   路径: {result['path'] or '未设置'}")
            if result['path_exists']:
                print(f"   ✓ 路径存在")
            else:
                print(f"   ✗ 路径不存在")
            
            if result['executable']:
                print(f"   可执行文件: {result['executable']}")
                if result['executable_found']:
                    print(f"   ✓ 找到: {result['executable_path']}")
                    if result['version'] != "unknown":
                        print(f"   版本: {result['version']}")
                else:
                    print(f"   ✗ 未找到可执行文件")
            
            if result['needs_build'] and result['installed'] and not result['executable_found']:
                print(f"   ⚠️  需要编译")
            
            if result['status'] == "not_installed" and result['download_url']:
                print(f"   下载地址: {result['download_url']}")
            
            print()
        
        # 统计
        ready_count = sum(1 for r in self.results.values() if r['status'] == 'ready')
        installed_count = sum(1 for r in self.results.values() if r['installed'])
        total_count = len(self.results)
        
        print("="*80)
        print(f"统计: {ready_count}/{total_count} 工具就绪, {installed_count}/{total_count} 工具已安装")
        print("="*80)
    
    def save_json_report(self, output_path: str = "tools_check_report.json"):
        """保存 JSON 格式报告"""
        report_path = Path(output_path)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 JSON 报告已保存到: {report_path}")


def main():
    """主函数"""
    checker = ToolChecker()
    checker.check_all_tools()
    checker.print_report()
    checker.save_json_report()
    
    # 返回退出码
    ready_count = sum(1 for r in checker.results.values() if r['status'] == 'ready')
    if ready_count == 0:
        print("\n⚠️  警告: 没有工具就绪，请运行下载脚本安装工具")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

