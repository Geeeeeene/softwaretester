"""
使用SikuliX Python API来截图并定位元素坐标
需要先安装: pip install sikulix4python
或者使用SikuliX IDE
"""
import sys
from pathlib import Path

try:
    from sikulix4python import *
except ImportError:
    print("未安装 sikulix4python，请使用以下方法之一：")
    print("1. 使用SikuliX IDE（推荐）")
    print("2. 使用Robot Framework的Capture Screen功能")
    print("3. 安装 sikulix4python: pip install sikulix4python")
    sys.exit(1)

def capture_and_find_coordinates():
    """截图并帮助定位元素坐标"""
    
    # 应用路径
    app_path = r"C:\Users\lenovo\Desktop\FreeCharts\diagramscene.exe"
    screenshot_dir = Path("screenshots")
    screenshot_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("SikuliX 元素坐标定位工具")
    print("=" * 60)
    
    # 1. 启动应用
    print("\n1. 启动应用...")
    app = App(app_path)
    app.open()
    wait(5)  # 等待应用启动
    
    # 2. 截图
    print("\n2. 截图整个屏幕...")
    screen = Screen()
    full_screenshot = screen.capture()
    screenshot_path = screenshot_dir / "full_screen.png"
    full_screenshot.save(str(screenshot_path))
    print(f"   截图已保存: {screenshot_path}")
    
    # 3. 提示用户操作
    print("\n3. 请手动操作应用：")
    print("   - 点击左侧图元集的一个图元")
    print("   - 在右侧空白区域点击一下")
    print("   操作完成后，按回车继续...")
    input()
    
    # 4. 再次截图
    print("\n4. 截图操作后的状态...")
    after_screenshot = screen.capture()
    after_path = screenshot_dir / "after_action.png"
    after_screenshot.save(str(after_path))
    print(f"   截图已保存: {after_path}")
    
    # 5. 获取鼠标位置
    print("\n5. 请将鼠标移动到目标元素上（例如：左侧图元集中的图元）")
    print("   移动完成后，按回车获取坐标...")
    input()
    
    mouse_pos = screen.getMouseLocation()
    print(f"\n   鼠标当前位置: X={mouse_pos.x}, Y={mouse_pos.y}")
    
    # 6. 在鼠标位置周围截图（用于裁剪）
    print("\n6. 在鼠标位置周围截图（200x200像素）...")
    region = Region(mouse_pos.x - 100, mouse_pos.y - 100, 200, 200)
    element_screenshot = region.capture()
    element_path = screenshot_dir / f"element_at_{mouse_pos.x}_{mouse_pos.y}.png"
    element_screenshot.save(str(element_path))
    print(f"   元素截图已保存: {element_path}")
    
    # 7. 关闭应用
    print("\n7. 关闭应用...")
    app.close()
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    print(f"\n截图文件位置: {screenshot_dir.absolute()}")
    print(f"\n坐标信息:")
    print(f"  X坐标: {mouse_pos.x}")
    print(f"  Y坐标: {mouse_pos.y}")
    print(f"\n下一步:")
    print(f"  1. 查看 {element_path} 文件")
    print(f"  2. 如果图像正确，可以将其复制到 examples/robot_resources/ 目录")
    print(f"  3. 或者使用图像编辑工具进一步裁剪")

if __name__ == "__main__":
    capture_and_find_coordinates()

