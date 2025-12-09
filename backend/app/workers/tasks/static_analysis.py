"""
静态分析任务
"""
import asyncio


def run_static_analysis(project_id: int, config: dict):
    """
    运行静态代码分析
    """
    return asyncio.run(_run_static_analysis_async(project_id, config))


async def _run_static_analysis_async(project_id: int, config: dict):
    """异步执行静态分析"""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.core.config import settings
    from app.models.project import Project
    
    # 创建数据库会话
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 获取项目
        result = await session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return {"error": "项目不存在"}
        
        # TODO: 实现静态分析逻辑
        # 1. 解析源代码
        # 2. 构建AST/CFG
        # 3. 运行分析规则
        # 4. 存储结果到Neo4j
        
        return {
            "project_id": project_id,
            "status": "completed",
            "issues_found": 0,
            "message": "静态分析功能开发中"
        }

