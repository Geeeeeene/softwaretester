"""本地项目后台任务定义"""
import time
import os
from typing import List
from datetime import datetime
from pathlib import Path

from app.db.session import SessionLocal
from app.db.models.test_execution import TestExecution


def run_local_project_test(execution_id: int, source_path: str, build_path: str):
    """为本地项目执行单元测试（UTBot + gcov + lcov + Dr.Memory）
    
    Args:
        execution_id: 执行记录ID
        source_path: 源代码路径（临时目录）
        build_path: 构建路径（临时目录）
    """
    db = SessionLocal()
    execution = None
    
    try:
        # 获取执行记录
        execution = db.query(TestExecution).filter(
            TestExecution.id == execution_id
        ).first()
        
        if not execution:
            print(f"❌ 执行记录 {execution_id} 不存在")
            return
        
        # 更新状态为运行中
        execution.status = "running"
        execution.started_at = datetime.utcnow()
        db.commit()
        
        print(f"▶️  开始本地项目单元测试 (ID: {execution_id})")
        print(f"   源代码路径: {source_path}")
        print(f"   构建路径: {build_path}")
        
        # 获取执行器
        from app.executors.unit_executor import UnitExecutor
        executor = UnitExecutor()
        
        # 执行项目测试
        import asyncio
        result = asyncio.run(executor.execute_project(Path(source_path), build_path))
        
        # 更新执行记录
        execution.status = "completed" if result.get("passed") else "failed"
        execution.completed_at = datetime.utcnow()
        execution.passed_tests = result.get("passed_tests", 0)
        execution.failed_tests = result.get("failed_tests", 0)
        execution.total_tests = result.get("total_tests", 0)
        execution.duration_seconds = result.get("duration", 0)
        
        if result.get("logs"):
            execution.logs = result["logs"]
        if result.get("coverage"):
            execution.coverage_data = result["coverage"]
        if result.get("artifacts"):
            execution.artifacts = result["artifacts"]
        
        # 更新结果，包含内存问题
        execution.result = {
            "passed": result.get("passed_tests", 0),
            "failed": result.get("failed_tests", 0),
            "total": result.get("total_tests", 0),
            "coverage_percentage": result.get("coverage", {}).get("percentage", 0) if result.get("coverage") else 0,
        }
        
        # 添加内存调试结果
        if result.get("result") and result["result"].get("issues"):
            execution.result["issues"] = result["result"]["issues"]
            execution.result["total_issues"] = result["result"].get("total_issues", len(result["result"]["issues"]))
            execution.result["error_count"] = result["result"].get("error_count", 0)
            execution.result["warning_count"] = result["result"].get("warning_count", 0)
        
        if result.get("error_message"):
            execution.error_message = result["error_message"]
        
        db.commit()
        
        print(f"✅ 本地项目测试完成 (ID: {execution_id})")
        print(f"   通过: {execution.passed_tests}, 失败: {execution.failed_tests}, 总计: {execution.total_tests}")
        if result.get("coverage"):
            print(f"   覆盖率: {result['coverage'].get('percentage', 0):.2f}%")
        if result.get("result") and result["result"].get("issues"):
            print(f"   内存问题: {len(result['result']['issues'])} 个")
        
    except Exception as e:
        print(f"❌ 本地项目测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if execution:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            db.commit()
    
    finally:
        db.close()

