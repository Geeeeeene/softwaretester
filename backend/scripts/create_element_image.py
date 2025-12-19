"""
从完整截图中裁剪出目标元素图像
使用方法：
1. 先运行 test_diagramscene.robot 或 capture_and_find_element.robot 获取截图
2. 打开截图，找到目标元素的坐标和大小
3. 运行此脚本，输入坐标和大小，裁剪出目标元素
"""
from PIL import Image
from pathlib import Path
import sys

def create_element_image():
    """从截图中裁剪出目标元素"""
    
    # 截图目录
    screenshot_dir = Path("sikuli_captured")
    if not screenshot_dir.exists():
        screenshot_dir = Path("screenshots")
    
    # 查找最新的截图
    screenshots = list(screenshot_dir.glob("*.png"))
    if not screenshots:
        print(f"错误: 在 {screenshot_dir} 目录中未找到截图文件")
        print("请先运行 Robot Framework 测试或使用 SikuliX 截图")
        return
    
    # 按修改时间排序，获取最新的截图
    latest_screenshot = max(screenshots, key=lambda p: p.stat().st_mtime)
    print(f"找到最新截图: {latest_screenshot}")
    
    # 打开截图
    try:
        img = Image.open(latest_screenshot)
        print(f"截图尺寸: {img.size[0]} x {img.size[1]}")
    except Exception as e:
        print(f"错误: 无法打开截图文件: {e}")
        return
    
    # 显示截图信息
    print("\n" + "=" * 60)
    print("元素坐标定位工具")
    print("=" * 60)
    print(f"\n当前截图: {latest_screenshot.name}")
    print(f"截图尺寸: {img.size[0]} x {img.size[1]} 像素")
    
    # 获取用户输入
    print("\n请打开截图文件，找到目标元素的位置和大小")
    print("（可以使用Windows画图工具查看坐标：鼠标移动到元素上，左下角会显示坐标）")
    
    try:
        x = int(input("\n请输入元素左上角 X 坐标: "))
        y = int(input("请输入元素左上角 Y 坐标: "))
        width = int(input("请输入元素宽度 (width): "))
        height = int(input("请输入元素高度 (height): "))
    except ValueError:
        print("错误: 请输入有效的数字")
        return
    
    # 验证坐标
    if x < 0 or y < 0 or x + width > img.size[0] or y + height > img.size[1]:
        print(f"错误: 坐标超出截图范围")
        print(f"截图范围: 0, 0 到 {img.size[0]}, {img.size[1]}")
        print(f"您输入的坐标: ({x}, {y}) 到 ({x + width}, {y + height})")
        return
    
    # 裁剪图像
    try:
        cropped = img.crop((x, y, x + width, y + height))
        
        # 保存裁剪后的图像
        output_dir = Path("examples/robot_resources")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        element_name = input("\n请输入元素名称（例如: rectangle_element）: ").strip()
        if not element_name:
            element_name = f"element_{x}_{y}_{width}_{height}"
        
        output_path = output_dir / f"{element_name}.png"
        cropped.save(output_path)
        
        print(f"\n✓ 成功！元素图像已保存: {output_path}")
        print(f"\n图像信息:")
        print(f"  位置: ({x}, {y})")
        print(f"  大小: {width} x {height}")
        print(f"  文件: {output_path}")
        
        print(f"\n下一步:")
        print(f"  1. 检查 {output_path} 是否正确")
        print(f"  2. 在 Robot Framework 脚本中使用: ${{ELEMENT_NAME}}    {element_name}.png")
        
    except Exception as e:
        print(f"错误: 裁剪图像失败: {e}")

if __name__ == "__main__":
    create_element_image()

