#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
辅助脚本：在指定坐标位置点击鼠标
用于 Robot Framework 脚本中点击相对坐标
"""
import sys
import ctypes
import time

def click_at(x, y):
    """在指定坐标位置点击鼠标"""
    try:
        # 移动鼠标到目标位置
        ctypes.windll.user32.SetCursorPos(int(x), int(y))
        time.sleep(0.1)  # 等待鼠标移动
        
        # 按下鼠标左键
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        
        # 释放鼠标左键
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
        
        return True
    except Exception as e:
        print(f"点击失败: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python click_coordinate.py <x> <y>", file=sys.stderr)
        sys.exit(1)
    
    x = int(sys.argv[1])
    y = int(sys.argv[2])
    
    success = click_at(x, y)
    sys.exit(0 if success else 1)





