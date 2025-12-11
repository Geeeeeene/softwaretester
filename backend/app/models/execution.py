"""执行相关模型和枚举"""
import enum


class ExecutionStatus(str, enum.Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"

# 注意：TestExecution 模型已移至 app.db.models.test_execution
# 请使用: from app.db.models.test_execution import TestExecution

