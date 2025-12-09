"""数据库初始化脚本"""
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import engine
from app.db.base import Base
# 导入所有模型
from app.db.models.project import Project  # noqa
from app.db.models.test_case import TestCase  # noqa
from app.db.models.test_execution import TestExecution  # noqa
from app.db.models.test_result import TestResult  # noqa


def init_db():
    """初始化数据库"""
    print("🚀 开始初始化数据库...")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("✅ 数据库表创建完成")
    print("\n已创建的表:")
    print("  - projects (项目)")
    print("  - test_cases (测试用例)")
    print("  - test_executions (测试执行)")
    print("  - test_results (测试结果)")
    print("\n🎉 数据库初始化成功！")


def drop_db():
    """删除所有表（慎用）"""
    confirm = input("⚠️  确定要删除所有表吗？(yes/no): ")
    if confirm.lower() == "yes":
        Base.metadata.drop_all(bind=engine)
        print("✅ 所有表已删除")
    else:
        print("❌ 操作已取消")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        drop_db()
    else:
        init_db()

