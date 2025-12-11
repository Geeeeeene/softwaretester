"""
测试执行任务
"""
import asyncio
from datetime import datetime
from app.executors.executor_factory import ExecutorFactory


def execute_test(testcase_id: int, config: dict):
    """
    执行测试用例
    这是RQ任务函数，在worker进程中执行
    """
    # RQ在同步上下文中运行，需要创建新的事件循环
    return asyncio.run(_execute_test_async(testcase_id, config))


async def _execute_test_async(testcase_id: int, config: dict):
    """异步执行测试"""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.core.config import settings
    from app.db.models.test_case import TestCase
    from app.db.models.test_execution import TestExecution
    from app.models.execution import ExecutionStatus
    
    # 创建数据库会话
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 获取测试用例
        result = await session.execute(
            select(TestCase).where(TestCase.id == testcase_id)
        )
        testcase = result.scalar_one_or_none()
        
        if not testcase:
            return {"error": "测试用例不存在"}
        
        # 创建执行记录
        execution = TestExecution(
            project_id=testcase.project_id,
            test_case_id=testcase.id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow(),
            executor_type=testcase.test_type.value,
            environment=config
        )
        session.add(execution)
        await session.commit()
        await session.refresh(execution)
        
        try:
            # 获取执行器
            executor = ExecutorFactory.get_executor(testcase.test_type)
            
            # 执行测试
            result = await executor.execute(testcase.test_ir, config)
            
            # 更新执行记录
            execution.status = ExecutionStatus.PASSED if result.get("passed") else ExecutionStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.result = result
            execution.logs = result.get("logs", "")
            execution.error_message = result.get("error_message")
            execution.coverage_data = result.get("coverage")
            execution.artifacts = result.get("artifacts", [])
            
            if result.get("coverage"):
                execution.coverage_percentage = result["coverage"].get("percentage", 0)
            
        except Exception as e:
            # 执行失败
            execution.status = ExecutionStatus.ERROR
            execution.completed_at = datetime.utcnow()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.error_message = str(e)
            execution.logs = f"执行错误: {str(e)}"
        
        await session.commit()
        
        return {
            "execution_id": execution.id,
            "status": execution.status.value,
            "duration": execution.duration
        }

