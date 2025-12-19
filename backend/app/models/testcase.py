"""测试用例相关的枚举类型"""
import enum


class TestType(str, enum.Enum):
    """测试类型枚举"""
    UI = "ui"
    UNIT = "unit"
    INTEGRATION = "integration"
    STATIC = "static"
    PERFORMANCE = "performance"
    MEMORY = "memory"  # 内存调试
    ROBOT_FRAMEWORK = "robot_framework"  # Robot Framework + SikuliLibrary系统测试


class TestPriority(str, enum.Enum):
    """优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# 注意：TestCase 模型已移至 app.db.models.test_case
# 请使用: from app.db.models.test_case import TestCase

