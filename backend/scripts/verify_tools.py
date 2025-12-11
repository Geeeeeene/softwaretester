#!/usr/bin/env python3
"""
工具验证脚本
确保 UTBotCpp、gcov+lcov、Dr. Memory 等工具存在且可执行
"""
import os
import sys
import shutil
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.executors.unit_executor import UnitExecutor
from app.executors.memory_executor import MemoryExecutor


def check_tool(name: str, path: str, required: bool = True) -> tuple[bool, str]:
    """检查工具是否存在"""
    if not path:
        if required:
            return False, f"❌ {name} 未找到（路径为空）"
        else:
            return False, f"⚠️  {name} 未找到（可选工具）"
    
    path_obj = Path(path)
    if not path_obj.exists():
        if required:
            return False, f"❌ {name} 路径不存在: {path}"
        else:
            return False, f"⚠️  {name} 路径不存在: {path}（可选工具）"
    
    if not path_obj.is_file():
        return False, f"❌ {name} 路径不是文件: {path}"
    
    if not os.access(path_obj, os.X_OK):
        return False, f"❌ {name} 文件不可执行: {path}"
    
    return True, f"✅ {name} 已找到: {path}"


def check_system_tool(name: str, required: bool = True) -> tuple[bool, str]:
    """检查系统工具（从PATH查找）"""
    exe_name = f"{name}.exe" if os.name == 'nt' else name
    tool_path = shutil.which(name) or shutil.which(exe_name)
    
    if tool_path:
        return True, f"✅ {name} 已找到: {tool_path}"
    else:
        if required:
            return False, f"❌ {name} 未找到，请安装 {name}"
        else:
            return False, f"⚠️  {name} 未找到（可选工具）"


def main():
    """主函数"""
    print("=" * 80)
    print("工具验证脚本")
    print("=" * 80)
    print()
    
    all_ok = True
    
    # 1. 检查 UTBotCpp
    print("1. 检查 UTBotCpp（单元测试生成工具）")
    print("-" * 80)
    unit_executor = UnitExecutor()
    
    if unit_executor.utbot_executable:
        ok, msg = check_tool("UTBotCpp", unit_executor.utbot_executable, required=True)
        print(f"  {msg}")
        if not ok:
            all_ok = False
            print(f"  💡 提示: UTBotCpp 需要编译后才能使用")
            print(f"  💡 路径配置: {settings.UTBOT_PATH}")
            print(f"  💡 可执行文件配置: {settings.UTBOT_EXECUTABLE}")
    else:
        print("  ❌ UTBotCpp 可执行文件未找到")
        all_ok = False
        print(f"  💡 提示: 请检查 UTBotCpp 是否已编译")
        print(f"  💡 路径配置: {settings.UTBOT_PATH}")
        print(f"  💡 可执行文件配置: {settings.UTBOT_EXECUTABLE}")
    print()
    
    # 2. 检查 gcov
    print("2. 检查 gcov（代码覆盖率工具）")
    print("-" * 80)
    if unit_executor.gcov_path:
        ok, msg = check_tool("gcov", unit_executor.gcov_path, required=True)
        print(f"  {msg}")
        if not ok:
            all_ok = False
    else:
        ok, msg = check_system_tool("gcov", required=True)
        print(f"  {msg}")
        if not ok:
            all_ok = False
            print(f"  💡 提示: gcov 通常随 MinGW/GCC 安装")
            print(f"  💡 配置路径: {settings.GCOV_PATH}")
    print()
    
    # 3. 检查 lcov
    print("3. 检查 lcov（覆盖率报告生成工具）")
    print("-" * 80)
    if unit_executor.lcov_path:
        ok, msg = check_tool("lcov", unit_executor.lcov_path, required=True)
        print(f"  {msg}")
        if not ok:
            all_ok = False
    else:
        ok, msg = check_system_tool("lcov", required=True)
        print(f"  {msg}")
        if not ok:
            all_ok = False
            print(f"  💡 提示: Windows 可以使用 Chocolatey 安装: choco install lcov")
            print(f"  💡 或使用 MSYS2: pacman -S mingw-w64-x86_64-lcov")
            print(f"  💡 配置路径: {settings.LCOV_PATH}")
    print()
    
    # 4. 检查 genhtml
    print("4. 检查 genhtml（HTML覆盖率报告生成工具）")
    print("-" * 80)
    if unit_executor.genhtml_path:
        ok, msg = check_tool("genhtml", unit_executor.genhtml_path, required=False)
        print(f"  {msg}")
    else:
        ok, msg = check_system_tool("genhtml", required=False)
        print(f"  {msg}")
        if not ok:
            print(f"  💡 提示: genhtml 通常与 lcov 一起安装")
    print()
    
    # 5. 检查 Dr. Memory
    print("5. 检查 Dr. Memory（内存调试工具）")
    print("-" * 80)
    memory_executor = MemoryExecutor()
    
    if memory_executor.drmemory_executable:
        ok, msg = check_tool("Dr. Memory", memory_executor.drmemory_executable, required=True)
        print(f"  {msg}")
        if not ok:
            all_ok = False
    else:
        print("  ❌ Dr. Memory 可执行文件未找到")
        all_ok = False
        print(f"  💡 提示: 请下载并安装 Dr. Memory")
        print(f"  💡 下载地址: https://github.com/DynamoRIO/drmemory/releases")
        print(f"  💡 路径配置: {settings.DRMEMORY_PATH}")
        print(f"  💡 可执行文件配置: {settings.DRMEMORY_EXECUTABLE}")
    print()
    
    # 总结
    print("=" * 80)
    if all_ok:
        print("✅ 所有必需工具都已找到且可执行！")
        return 0
    else:
        print("❌ 部分工具未找到或不可执行，请根据上述提示安装/配置工具")
        return 1


if __name__ == "__main__":
    sys.exit(main())



