"""
从SikuliX截图中创建目标图像
这个脚本帮助您从完整的屏幕截图中裁剪出应用窗口的一小部分
"""
from PIL import Image
import os
from pathlib import Path

def list_screenshots():
    """列出sikuli_captured目录中的所有截图"""
    capture_dir = Path("sikuli_captured")
    if not capture_dir.exists():
        print("错误: sikuli_captured 目录不存在")
        return []
    
    screenshots = sorted(capture_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
    return screenshots

def crop_and_save(source_image_path, left, top, right, bottom, output_path):
    """
    从源图像中裁剪指定区域并保存
    
    Args:
        source_image_path: 源图像路径
        left: 左边界（像素）
        top: 上边界（像素）
        right: 右边界（像素）
        bottom: 下边界（像素）
        output_path: 输出图像路径
    """
    try:
        img = Image.open(source_image_path)
        print(f"源图像尺寸: {img.width} x {img.height}")
        
        # 裁剪
        cropped = img.crop((left, top, right, bottom))
        cropped_width = right - left
        cropped_height = bottom - top
        print(f"裁剪区域: ({left}, {top}) 到 ({right}, {bottom})")
        print(f"裁剪后尺寸: {cropped_width} x {cropped_height}")
        
        # 保存
        cropped.save(output_path)
        print(f"✓ 已保存到: {output_path}")
        
        img.close()
        
    except Exception as e:
        print(f"✗ 错误: {e}")

def main():
    print("=" * 60)
    print("创建目标图像工具")
    print("=" * 60)
    print()
    
    # 列出最新的截图
    screenshots = list_screenshots()
    
    if not screenshots:
        print("没有找到截图文件")
        return
    
    print("最新的5个截图：")
    for i, screenshot in enumerate(screenshots[:5], 1):
        size = screenshot.stat().st_size
        print(f"{i}. {screenshot.name} ({size:,} 字节)")
    
    print()
    print("=" * 60)
    print("推荐裁剪参数：")
    print("=" * 60)
    print()
    print("方案1: 裁剪窗口左上角（标题栏）")
    print("  left=0, top=0, right=300, bottom=80")
    print()
    print("方案2: 裁剪更小的区域")
    print("  left=0, top=0, right=200, bottom=50")
    print()
    print("方案3: 裁剪中心区域")
    print("  left=400, top=200, right=800, bottom=400")
    print()
    print("=" * 60)
    print()
    
    # 使用最新的截图
    if screenshots:
        latest = screenshots[0]
        print(f"使用最新截图: {latest.name}")
        
        # 推荐的裁剪区域：窗口左上角
        output_path = "examples/robot_resources/main_window.png"
        
        # 默认裁剪左上角 300x80 区域
        print()
        print("自动裁剪左上角区域 (0,0) 到 (300,80)...")
        crop_and_save(latest, 0, 0, 300, 80, output_path)
        
        print()
        print("=" * 60)
        print("完成！")
        print("=" * 60)
        print()
        print("新的目标图像已创建。")
        print("现在运行测试: py -m robot test_diagramscene.robot")
        print()
        print("如果还是失败，可以修改裁剪参数：")
        print("  打开这个脚本，修改 crop_and_save() 的参数")

if __name__ == "__main__":
    main()

