#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检测 CMake 版本"""
import sys
import os
import subprocess
import shutil

def check_cmake_version():
    """检测 CMake 版本"""
    print("=" * 60)
    print("CMake 版本检测")
    print("=" * 60)
    print()
    
    # 1. 查找 CMake 可执行文件
    print("[1] 查找 CMake 可执行文件...")
    cmake_exe = shutil.which("cmake")
    
    if not cmake_exe:
        # 尝试常见安装路径（包括 .EXE 大写扩展名）
        common_paths = [
            r"C:\Program Files\CMake\bin\cmake.exe",
            r"C:\Program Files\CMake\bin\cmake.EXE",
            r"C:\Program Files (x86)\CMake\bin\cmake.exe",
            r"C:\Program Files (x86)\CMake\bin\cmake.EXE",
            r"C:\CMake\bin\cmake.exe",
            r"C:\CMake\bin\cmake.EXE",
        ]
        for path in common_paths:
            if os.path.exists(path):
                cmake_exe = path
                print(f"   在常见路径找到: {cmake_exe}")
                break
    
    if not cmake_exe:
        print("   [失败] 未找到 CMake 可执行文件")
        print("   可能原因:")
        print("   1. CMake 未安装")
        print("   2. CMake 未添加到系统 PATH")
        print("   3. CMake 安装在非标准路径")
        return False
    
    print(f"   [成功] CMake 路径: {cmake_exe}")
    print(f"   文件存在: {os.path.exists(cmake_exe)}")
    print()
    
    # 2. 检查版本
    print("[2] 检查 CMake 版本...")
    try:
        result = subprocess.run(
            [cmake_exe, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"   [成功] {version_line}")
            
            # 提取版本号
            try:
                version_str = version_line.split()[2]
                print(f"   版本号: {version_str}")
                
                # 解析主版本号
                version_parts = version_str.split('.')
                major = int(version_parts[0])
                minor = int(version_parts[1]) if len(version_parts) > 1 else 0
                patch = int(version_parts[2]) if len(version_parts) > 2 else 0
                
                # 评估版本
                print()
                print("[3] 版本评估...")
                if major == 4:
                    print(f"   [警告] CMake {version_str} 是 4.x 版本")
                    print("   可能存在的问题:")
                    print("   - 与 Qt6 和 MinGW 可能存在兼容性问题")
                    print("   - 可能导致访问冲突错误 (0xC0000005)")
                    print("   建议: 降级到 CMake 3.28.x 或更低版本")
                elif major == 3:
                    if minor >= 16:
                        print(f"   [良好] CMake {version_str} 版本符合要求 (>= 3.16)")
                        if minor >= 31:
                            print("   [注意] 这是非常新的版本 (3.31.x)")
                            print("   - 可能包含最新的功能和修复")
                            print("   - 但可能存在未发现的兼容性问题")
                            print("   - 建议先测试是否能正常工作")
                            print("   - 如果遇到问题，可降级到 3.28.x")
                        elif minor >= 28:
                            print("   [推荐] 这是最新稳定版本，兼容性最好")
                        elif minor >= 26:
                            print("   [推荐] 版本较新，兼容性良好")
                        else:
                            print("   [可用] 版本可用，但建议升级到 3.26+")
                    else:
                        print(f"   [警告] CMake {version_str} 版本过低 (< 3.16)")
                        print("   建议: 升级到 CMake 3.16 或更高版本")
                else:
                    print(f"   [未知] CMake {version_str} 版本未知")
                    print("   建议: 使用 CMake 3.16-3.28 之间的版本")
                
            except Exception as e:
                print(f"   [警告] 无法解析版本号: {e}")
        else:
            print(f"   [失败] 无法获取版本信息")
            print(f"   退出码: {result.returncode}")
            if result.stderr:
                print(f"   错误: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   [失败] CMake 版本检查超时")
        return False
    except Exception as e:
        print(f"   [失败] 检查版本时出错: {e}")
        return False
    
    print()
    print("=" * 60)
    print("检测完成")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = check_cmake_version()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[错误] 检测过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

