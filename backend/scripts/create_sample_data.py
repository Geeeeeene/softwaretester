"""创建示例数据"""
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models.project import Project
from app.db.models.test_case import TestCase


def create_sample_data():
    """创建示例项目和测试用例"""
    db = SessionLocal()
    
    try:
        print("🚀 开始创建示例数据...")
        
        # 创建示例项目
        projects = [
            Project(
                name="Calculator App",
                description="简单的计算器应用UI测试",
                project_type="ui",
                language="python",
                framework="Qt",
                source_path="/samples/calculator",
            ),
            Project(
                name="String Utils",
                description="字符串工具库单元测试",
                project_type="unit",
                language="cpp",
                framework="GoogleTest",
                source_path="/samples/stringutils",
            ),
            Project(
                name="E-commerce API",
                description="电商API集成测试",
                project_type="integration",
                language="python",
                framework="FastAPI",
            ),
        ]
        
        for project in projects:
            db.add(project)
        
        db.commit()
        print(f"✅ 创建了 {len(projects)} 个示例项目")
        
        # 创建示例测试用例
        # UI测试用例
        ui_test_case = TestCase(
            project_id=1,
            name="测试加法运算",
            description="测试计算器的加法功能",
            test_type="ui",
            test_ir={
                "type": "ui",
                "name": "测试加法运算",
                "steps": [
                    {"type": "input", "target": "input1", "value": "5"},
                    {"type": "input", "target": "input2", "value": "3"},
                    {"type": "click", "target": "addButton"},
                    {"type": "assert", "target": "result", "value": "8"},
                ],
                "priority": "high",
            },
            priority="high",
            tags=["basic", "arithmetic"],
        )
        
        # 单元测试用例
        unit_test_case = TestCase(
            project_id=2,
            name="测试字符串反转",
            description="测试字符串反转函数",
            test_type="unit",
            test_ir={
                "type": "unit",
                "name": "测试字符串反转",
                "function_under_test": {
                    "name": "reverse_string",
                    "file_path": "src/string_utils.cpp",
                },
                "inputs": {
                    "parameters": {"input": "hello"}
                },
                "assertions": [
                    {"type": "equals", "expected": "olleh"}
                ],
                "priority": "medium",
            },
            priority="medium",
            tags=["string", "basic"],
        )
        
        db.add(ui_test_case)
        db.add(unit_test_case)
        db.commit()
        
        print("✅ 创建了 2 个示例测试用例")
        print("\n🎉 示例数据创建成功！")
        print("\n可以访问前端查看这些示例项目：")
        print("  http://localhost:5173/projects")
        
    except Exception as e:
        print(f"❌ 创建失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()

