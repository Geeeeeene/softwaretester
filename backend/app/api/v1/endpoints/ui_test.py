"""系统测试API端点"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
from pathlib import Path
import time
from datetime import datetime

from app.db.session import get_db
from app.db.models.project import Project
from app.db.models.test_execution import TestExecution
from app.db.models.test_case import TestCase
from app.core.config import settings
from app.executors.robot_framework_executor import RobotFrameworkExecutor
from app.ui_test.ai_generator import UITestAIGenerator
from app.workers.task_queue import enqueue_ui_test

router = APIRouter()


class UITestCaseGenerateRequest(BaseModel):
    """AI生成系统测试用例请求"""
    name: str
    description: str


class UITestCaseGenerateResponse(BaseModel):
    """AI生成系统测试用例响应"""
    name: str
    description: str
    robot_script: str
    test_ir: dict


class UITestExecuteRequest(BaseModel):
    """执行系统测试请求"""
    name: str
    description: str
    robot_script: str


class UITestExecuteResponse(BaseModel):
    """执行系统测试响应"""
    execution_id: int
    status: str
    message: str


class UITestResult(BaseModel):
    """系统测试结果"""
    execution_id: int
    status: str
    passed: bool
    logs: Optional[str] = None
    error_message: Optional[str] = None
    artifacts: list = []
    duration_seconds: Optional[float] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


@router.post("/projects/{project_id}/system-test/generate", response_model=UITestCaseGenerateResponse)
async def generate_ui_test_case(
    project_id: int,
    request: UITestCaseGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    使用AI生成系统测试用例（Robot Framework脚本）
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if project.project_type != "ui":
        raise HTTPException(status_code=400, detail="该项目不是系统测试项目")
    
    try:
        # 使用AI生成器生成Robot Framework脚本
        generator = UITestAIGenerator()
        
        project_info = {
            'name': project.name,
            'source_path': project.source_path,
            'description': project.description
        }
        
        robot_script = generator.generate_robot_script(
            test_name=request.name,
            test_description=request.description,
            project_info=project_info
        )
        
        # 验证生成的脚本
        is_valid, error_msg = generator.validate_script(robot_script)
        if not is_valid:
            raise ValueError(f"生成的脚本无效: {error_msg}")
        
        # 构建Test IR
        test_ir = {
            "test_type": "robot_framework",
            "name": request.name,
            "description": request.description,
            "robot_script": robot_script,
            "variables": {},
            "timeout": 300
        }
        
        return UITestCaseGenerateResponse(
            name=request.name,
            description=request.description,
            robot_script=robot_script,
            test_ir=test_ir
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成测试用例失败: {str(e)}"
        )


@router.post("/projects/{project_id}/system-test/execute", response_model=UITestExecuteResponse)
async def execute_ui_test(
    project_id: int,
    request: UITestExecuteRequest,
    db: Session = Depends(get_db)
):
    """
    执行系统测试（Robot Framework脚本）
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if project.project_type != "ui":
        raise HTTPException(status_code=400, detail="该项目不是系统测试项目")
    
    try:
        # 保存或更新测试用例（如果不存在则创建，存在则更新）
        test_case = db.query(TestCase).filter(
            TestCase.project_id == project_id,
            TestCase.name == request.name,
            TestCase.test_type == "ui"
        ).first()
        
        # 构建Test IR
        test_ir = {
            "test_type": "robot_framework",
            "name": request.name,
            "description": request.description,
            "robot_script": request.robot_script,
            "variables": {},
            "timeout": 300
        }
        
        if test_case:
            # 更新现有测试用例
            test_case.description = request.description
            test_case.test_ir = test_ir
            test_case.updated_at = datetime.utcnow()
        else:
            # 检查名称是否重复，如果重复则自动添加编号
            base_name = request.name
            final_name = base_name
            counter = 1
            
            while db.query(TestCase).filter(
                TestCase.project_id == project_id,
                TestCase.name == final_name,
                TestCase.test_type == "ui"
            ).first():
                counter += 1
                final_name = f"{base_name}_{counter}"
            
            # 创建新测试用例
            test_case = TestCase(
                project_id=project_id,
                name=final_name,
                description=request.description,
                test_type="ui",
                test_ir=test_ir,
                priority="medium",
                tags=["ui", "robot_framework", "ai_generated"]
            )
            db.add(test_case)
        
        db.flush()  # 确保测试用例已保存
        
        # 创建测试执行记录
        execution = TestExecution(
            project_id=project_id,
            executor_type="robot_framework",
            status="running",
            total_tests=1,
            passed_tests=0,
            failed_tests=0,
            skipped_tests=0,
            started_at=datetime.utcnow()
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # 提交到worker队列执行（在Windows主机上的worker中执行）
        try:
            job_id = enqueue_ui_test(
                execution_id=execution.id,
                project_id=project_id,
                test_name=request.name,
                test_description=request.description,
                robot_script=request.robot_script
            )
            print(f"✅ 系统测试任务已提交到worker队列: job_id={job_id}, execution_id={execution.id}")
        except Exception as e:
            # 如果worker队列不可用，回退到直接执行（同步方式，不推荐）
            print(f"⚠️  Worker队列不可用，直接执行: {str(e)}")
            import asyncio
            from app.executors.robot_framework_executor import RobotFrameworkExecutor
            
            # 在后台线程中执行
            import threading
            def run_in_thread():
                try:
                    executor = RobotFrameworkExecutor()
                    test_ir = {
                        "test_type": "robot_framework",
                        "name": request.name,
                        "description": request.description,
                        "robot_script": request.robot_script,
                        "variables": {},
                        "timeout": 300
                    }
                    result = asyncio.run(executor.execute(test_ir, {}))
                    # 更新执行记录
                    from app.db.session import SessionLocal
                    db = SessionLocal()
                    execution = db.query(TestExecution).filter(TestExecution.id == execution.id).first()
                    if execution:
                        execution.status = "completed" if result["passed"] else "failed"
                        execution.completed_at = datetime.utcnow()
                        if result["passed"]:
                            execution.passed_tests = 1
                            execution.failed_tests = 0
                        else:
                            execution.passed_tests = 0
                            execution.failed_tests = 1
                        execution.error_message = result.get("error_message")
                        db.commit()
                    db.close()
                except Exception as e:
                    print(f"❌ 直接执行失败: {str(e)}")
            
            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()
        
        return UITestExecuteResponse(
            execution_id=execution.id,
            status="running",
            message="系统测试已开始执行"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"启动系统测试失败: {str(e)}"
        )


@router.get("/projects/{project_id}/system-test/results/{execution_id}", response_model=UITestResult)
async def get_ui_test_result(
    project_id: int,
    execution_id: int,
    db: Session = Depends(get_db)
):
    """
    获取系统测试结果
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取执行记录
    execution = db.query(TestExecution).filter(
        TestExecution.id == execution_id,
        TestExecution.project_id == project_id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="测试执行记录不存在")
    
    # 构建结果
    passed = execution.status == "completed" and execution.failed_tests == 0
    
    # 获取日志内容
    logs = None
    if execution.extra_data and "logs" in execution.extra_data:
        logs = execution.extra_data["logs"]
    
    # 获取artifacts
    artifacts = []
    if execution.extra_data and "artifacts" in execution.extra_data:
        artifacts = execution.extra_data["artifacts"]
    
    return UITestResult(
        execution_id=execution.id,
        status=execution.status,
        passed=passed,
        logs=logs,
        error_message=execution.error_message,
        artifacts=artifacts,
        duration_seconds=execution.duration_seconds,
        created_at=execution.created_at.isoformat() if execution.created_at else None,
        completed_at=execution.completed_at.isoformat() if execution.completed_at else None
    )


@router.get("/projects/{project_id}/system-test/report/{execution_id}")
async def get_ui_test_report(
    project_id: int,
    execution_id: int,
    report_type: str = Query("log", description="报告类型: log, report, output"),
    db: Session = Depends(get_db)
):
    """
    获取系统测试报告文件内容
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取执行记录
    execution = db.query(TestExecution).filter(
        TestExecution.id == execution_id,
        TestExecution.project_id == project_id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="测试执行记录不存在")
    
    # 从artifacts中查找报告文件
    artifacts = []
    if execution.extra_data and "artifacts" in execution.extra_data:
        artifacts = execution.extra_data["artifacts"]
    
    # 根据report_type查找对应的文件
    report_file = None
    if report_type == "log":
        report_file = next((a for a in artifacts if a.get("type") == "robot_log"), None)
    elif report_type == "report":
        report_file = next((a for a in artifacts if a.get("type") == "robot_report"), None)
    elif report_type == "output":
        report_file = next((a for a in artifacts if a.get("type") == "robot_output"), None)
    
    if not report_file:
        raise HTTPException(status_code=404, detail=f"未找到{report_type}报告文件")
    
    # 读取文件内容
    from pathlib import Path
    import os
    
    # 处理路径：可能是相对路径或绝对路径
    report_path_str = report_file.get("path", "")
    
    # 获取项目根目录（backend的父目录）
    backend_dir = Path(__file__).parent.parent.parent.parent  # 从endpoints -> v1 -> api -> app -> backend -> 项目根目录
    project_root = backend_dir
    
    # 处理路径
    report_path = None
    if os.path.isabs(report_path_str):
        # 绝对路径，直接使用
        report_path = Path(report_path_str)
    else:
        # 相对路径，相对于项目根目录
        # 去掉开头的斜杠
        report_path_str = report_path_str.lstrip("/")
        report_path = project_root / report_path_str
    
    # 尝试解析路径
    try:
        report_path = report_path.resolve()
    except (OSError, RuntimeError):
        pass
    
    if not report_path or not report_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"报告文件不存在: {report_path_str} (尝试路径: {report_path})"
        )
    
    # 读取文件内容
    try:
        with open(report_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return {"content": content, "type": report_type, "path": str(report_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取报告文件失败: {str(e)}")


@router.get("/projects/{project_id}/system-test/executions")
async def list_ui_test_executions(
    project_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取项目的系统测试执行历史
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 查询执行记录
    query = db.query(TestExecution).filter(
        TestExecution.project_id == project_id,
        TestExecution.executor_type == "robot_framework"
    ).order_by(TestExecution.created_at.desc())
    
    total = query.count()
    executions = query.offset(skip).limit(limit).all()
    
    # 计算通过率
    # 获取所有已完成的执行记录（包括completed和failed状态）
    completed_executions = db.query(TestExecution).filter(
        TestExecution.project_id == project_id,
        TestExecution.executor_type == "robot_framework",
        TestExecution.status.in_(["completed", "failed"])
    ).all()
    
    total_completed = len(completed_executions)
    # 通过的执行记录：status为completed且failed_tests为0
    passed_count = sum(1 for e in completed_executions if e.status == "completed" and e.failed_tests == 0)
    pass_rate = (passed_count / total_completed * 100) if total_completed > 0 else 0
    
    return {
        "total": total,
        "items": executions,
        "statistics": {
            "total_executions": total,
            "completed_executions": total_completed,
            "passed_executions": passed_count,
            "pass_rate": round(pass_rate, 2)
        }
    }


@router.delete("/projects/{project_id}/system-test/executions/{execution_id}", status_code=204)
async def delete_ui_test_execution(
    project_id: int,
    execution_id: int,
    db: Session = Depends(get_db)
):
    """
    删除系统测试执行记录
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 查询执行记录
    execution = db.query(TestExecution).filter(
        TestExecution.id == execution_id,
        TestExecution.project_id == project_id,
        TestExecution.executor_type == "robot_framework"
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    
    # 删除执行记录
    db.delete(execution)
    db.commit()
    
    return None


def run_robot_framework_test(
    execution_id: int,
    project_id: int,
    test_name: str,
    test_description: str,
    robot_script: str
):
    """
    后台任务：执行Robot Framework测试
    """
    import asyncio
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    start_time = time.time()
    
    try:
        # 获取执行记录
        execution = db.query(TestExecution).filter(
            TestExecution.id == execution_id
        ).first()
        
        if not execution:
            return
        
        # 创建执行器
        executor = RobotFrameworkExecutor()
        
        # 构建Test IR
        test_ir = {
            "test_type": "robot_framework",
            "name": test_name,
            "description": test_description,
            "robot_script": robot_script,
            "variables": {},
            "timeout": 300
        }
        
        # 执行测试（在同步函数中运行异步代码）
        # 在BackgroundTasks中，需要创建新的事件循环
        try:
            # 尝试获取当前事件循环
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，创建新的事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(executor.execute(test_ir, {}))
                else:
                    result = loop.run_until_complete(executor.execute(test_ir, {}))
            except RuntimeError:
                # 如果没有事件循环，创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(executor.execute(test_ir, {}))
        except Exception as e:
            # 如果所有方法都失败，使用 asyncio.run()
            # 这会创建新的事件循环并运行
            result = asyncio.run(executor.execute(test_ir, {}))
        
        # 更新执行记录
        execution.status = "completed" if result["passed"] else "failed"
        execution.completed_at = datetime.utcnow()
        execution.duration_seconds = time.time() - start_time
        
        if result["passed"]:
            execution.passed_tests = 1
            execution.failed_tests = 0
        else:
            execution.passed_tests = 0
            execution.failed_tests = 1
        
        execution.error_message = result.get("error_message")
        
        # 保存日志和artifacts到extra_data
        execution.extra_data = {
            "logs": result.get("logs", ""),
            "artifacts": result.get("artifacts", [])
        }
        
        db.commit()
        
    except Exception as e:
        # 更新执行记录为失败
        import traceback
        execution = db.query(TestExecution).filter(
            TestExecution.id == execution_id
        ).first()
        
        if execution:
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = time.time() - start_time
            error_detail = f"执行失败: {str(e)}\n\n详细错误:\n{traceback.format_exc()}"
            execution.error_message = error_detail
            execution.failed_tests = 1
            
            # 保存错误日志到extra_data
            if not execution.extra_data:
                execution.extra_data = {}
            execution.extra_data["logs"] = error_detail
            execution.extra_data["error_traceback"] = traceback.format_exc()
            
            db.commit()
    
    finally:
        db.close()

