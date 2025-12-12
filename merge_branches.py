#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import os
import sys

def run_command(cmd):
    """运行命令并打印输出"""
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode

def main():
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print(f"当前工作目录: {os.getcwd()}")
    
    # 获取远程分支
    print("\n" + "="*60)
    print("步骤 1: 获取远程分支信息...")
    print("="*60)
    run_command("git fetch origin")
    
    # 查看所有分支
    print("\n" + "="*60)
    print("步骤 2: 查看所有分支...")
    print("="*60)
    run_command("git branch -a")
    
    # 确保在 main 分支
    print("\n" + "="*60)
    print("步骤 3: 切换到 main 分支...")
    print("="*60)
    run_command("git checkout main")
    
    # 合并 jqh 分支
    print("\n" + "="*60)
    print("步骤 4: 合并 origin/jqh 分支到 main...")
    print("="*60)
    returncode = run_command('git merge origin/jqh -m "Merge jqh branch features into main"')
    
    if returncode == 0:
        print("\n✓ 合并成功！")
    else:
        print("\n✗ 合并过程中遇到问题，请检查上面的错误信息")
        return 1
    
    # 查看合并后的状态
    print("\n" + "="*60)
    print("步骤 5: 查看合并后的状态...")
    print("="*60)
    run_command("git status")
    
    # 查看最近的提交
    print("\n" + "="*60)
    print("最近的提交记录:")
    print("="*60)
    run_command("git log --oneline --graph -10")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)

