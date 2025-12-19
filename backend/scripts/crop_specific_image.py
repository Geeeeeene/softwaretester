"""
从指定截图中裁剪出矩形区域
"""
from PIL import Image
from pathlib import Path

def crop_image(source_path: str, left: int, top: int, right: int, bottom: int, output_path: str):
    """
    从源图像裁剪指定区域并保存
    
    Args:
        source_path: 源图像路径
        left: 左上角X坐标
        top: 左上角Y坐标
        right: 右下角X坐标
        bottom: 右下角Y坐标
        output_path: 输出图像路径
    """
    try:
        # 打开源图像
        img = Image.open(source_path)
        print(f"✓ 已打开源图像: {source_path}")
        print(f"  图像尺寸: {img.size[0]} x {img.size[1]}")
        
        # 验证坐标
        if left < 0 or top < 0 or right > img.size[0] or bottom > img.size[1]:
            print(f"⚠️  警告: 坐标可能超出图像范围")
            print(f"  图像范围: (0, 0) 到 ({img.size[0]}, {img.size[1]})")
            print(f"  裁剪区域: ({left}, {top}) 到 ({right}, {bottom})")
        
        # 裁剪图像
        cropped_img = img.crop((left, top, right, bottom))
        
        # 确保输出目录存在
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存裁剪后的图像
        cropped_img.save(output_path)
        
        print(f"\n✓ 图像已裁剪并保存到: {output_path}")
        print(f"  裁剪区域: ({left}, {top}) 到 ({right}, {bottom})")
        print(f"  裁剪后尺寸: {cropped_img.width} x {cropped_img.height}")
        
        return output_path
        
    except FileNotFoundError:
        print(f"✗ 错误: 找不到源图像文件: {source_path}")
        return None
    except Exception as e:
        print(f"✗ 错误: 裁剪图像失败: {e}")
        return None

if __name__ == "__main__":
    # 用户指定的参数
    source_image = r"C:\Users\lenovo\Desktop\homemadeTester\backend\artifacts\robot_framework\应用启动测试\sikuli_captured\sikuliximage-1766125671591.png"
    
    # 左上角坐标
    left = 711
    top = 438
    
    # 右下角坐标
    right = 966
    bottom = 551
    
    # 输出路径（保存到robot_resources目录）
    backend_dir = Path(__file__).parent.parent
    output_dir = backend_dir / "examples" / "robot_resources"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 输出文件名（可以根据需要修改）
    output_file = output_dir / "rectangle_element.png"
    
    print("=" * 60)
    print("图像裁剪工具")
    print("=" * 60)
    print(f"\n源图像: {source_image}")
    print(f"裁剪区域: 左上角({left}, {top}), 右下角({right}, {bottom})")
    print(f"输出路径: {output_file}")
    print("\n开始裁剪...\n")
    
    result = crop_image(source_image, left, top, right, bottom, str(output_file))
    
    if result:
        print("\n" + "=" * 60)
        print("✓ 裁剪完成！")
        print("=" * 60)
        print(f"\n下一步:")
        print(f"  1. 检查图像: {output_file}")
        print(f"  2. 在 Robot Framework 脚本中使用:")
        print(f"     ${{RECTANGLE_ELEMENT}}    rectangle_element.png")
    else:
        print("\n" + "=" * 60)
        print("✗ 裁剪失败")
        print("=" * 60)

