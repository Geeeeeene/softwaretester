"""后台任务定义"""
import time
import os
from typing import List
from datetime import datetime
from pathlib import Path

from app.db.session import SessionLocal
from app.db.models.test_execution import TestExecution
from app.db.models.test_case import TestCase
from app.db.models.test_result import TestResult
from app.db.models.project import Project
from app.executors.executor_factory import ExecutorFactory
from app.models.testcase import TestType


def execute_tests(execution_id: int, test_case_ids: List[int]):
    """执行测试任务
    
    Args:
        execution_id: 执行记录ID
        test_case_ids: 测试用例ID列表
    """
    db = SessionLocal()
    
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
        
        print(f"▶️  开始执行测试 (ID: {execution_id})")
        
        # 获取项目配置
        project = db.query(Project).filter(Project.id == execution.project_id).first()
        if not project:
            execution.status = "failed"
            execution.error_message = "项目不存在"
            execution.completed_at = datetime.utcnow()
            db.commit()
            return
        
        # 构建执行配置
        config = {
            "project_path": project.source_path or ".",
            "source_path": project.source_path or ".",
            "build_path": project.build_path or (os.path.join(project.source_path, "build") if project.source_path else "./build"),
            "binary_path": project.binary_path
        }
        
        # 确保build_path存在
        if config["build_path"]:
            build_dir = Path(config["build_path"])
            build_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取执行器
        try:
            test_type = TestType(execution.executor_type)
            executor = ExecutorFactory.get_executor(test_type)
        except ValueError:
            execution.status = "failed"
            execution.error_message = f"不支持的执行器类型: {execution.executor_type}"
            execution.completed_at = datetime.utcnow()
            db.commit()
            return
        
        # 执行每个测试用例
        passed = 0
        failed = 0
        skipped = 0
        all_logs = []
        coverage_data = None
        artifacts = []
        
        start_time = time.time()
        
        for test_case_id in test_case_ids:
            # 获取测试用例
            test_case = db.query(TestCase).filter(
                TestCase.id == test_case_id
            ).first()
            
            if not test_case:
                print(f"⚠️  测试用例 {test_case_id} 不存在，跳过")
                skipped += 1
                continue
            
            print(f"  🧪 执行测试用例: {test_case.name}")
            
            try:
                # 执行测试（传递配置）
                import asyncio
                result = asyncio.run(executor.execute(test_case.test_ir, config))
                
                # 收集日志和覆盖率数据
                if result.get("logs"):
                    all_logs.append(f"=== {test_case.name} ===\n{result['logs']}")
                
                if result.get("coverage") and not coverage_data:
                    coverage_data = result["coverage"]
                
                if result.get("artifacts"):
                    artifacts.extend(result["artifacts"])
                
                # 保存结果
                test_result = TestResult(
                    execution_id=execution_id,
                    test_case_id=test_case_id,
                    status="passed" if result.get("passed") else "failed",
                    duration_seconds=result.get("duration"),
                    error_message=result.get("error_message"),
                    log_path=result.get("log_path"),
                    screenshot_path=result.get("screenshot_path"),
                    extra_data=result.get("metadata", {})  # 使用extra_data而不是metadata
                )
                db.add(test_result)
                
                if result.get("passed"):
                    passed += 1
                    print(f"    ✅ 通过")
                else:
                    failed += 1
                    error_msg = result.get("error_message", "未知错误")
                    print(f"    ❌ 失败: {error_msg}")
                
            except Exception as e:
                print(f"    ❌ 执行异常: {str(e)}")
                failed += 1
                
                # 保存错误结果
                test_result = TestResult(
                    execution_id=execution_id,
                    test_case_id=test_case_id,
                    status="error",
                    error_message=str(e)
                )
                db.add(test_result)
            
            db.commit()
        
        # 计算执行时间
        duration = time.time() - start_time
        
        # 更新执行记录
        execution.status = "completed"
        execution.completed_at = datetime.utcnow()
        execution.passed_tests = passed
        execution.failed_tests = failed
        execution.skipped_tests = skipped
        execution.duration_seconds = duration
        
        # 保存日志、覆盖率和artifacts
        if all_logs:
            execution.logs = "\n\n".join(all_logs)
        if coverage_data:
            execution.coverage_data = coverage_data
            execution.coverage_percentage = coverage_data.get("percentage", 0)
        if artifacts:
            execution.artifacts = artifacts
        
        # 保存结果摘要
        execution.result = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": len(test_case_ids)
        }
        
        db.commit()
        
        print(f"✅ 测试执行完成 (ID: {execution_id})")
        print(f"   通过: {passed}, 失败: {failed}, 跳过: {skipped}")
        print(f"   耗时: {duration:.2f}秒")
        
    except Exception as e:
        # 处理执行失败
        print(f"❌ 测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 确保execution变量存在
        execution = None
        try:
            execution = db.query(TestExecution).filter(
                TestExecution.id == execution_id
            ).first()
        except:
            pass
        
        if execution:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            db.commit()
    
    finally:
        db.close()


def parse_documentation(project_id: int, file_path: str):
    """解析文档任务（示例）"""
    print(f"📄 解析文档: {file_path} (项目ID: {project_id})")
    time.sleep(2)  # 模拟处理
    print(f"✅ 文档解析完成")


def analyze_coverage(execution_id: int):
    """分析覆盖率任务（示例）"""
    print(f"📊 分析覆盖率 (执行ID: {execution_id})")
    time.sleep(3)  # 模拟处理
    print(f"✅ 覆盖率分析完成")


def run_utbot_project_test(execution_id: int):
    """使用UTBotCpp对项目进行单元测试
    
    Args:
        execution_id: 执行记录ID
    """
    db = SessionLocal()
    execution = None  # 初始化execution变量
    
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
        
        print(f"▶️  开始UTBotCpp项目测试 (ID: {execution_id})")
        
        # 获取项目配置
        project = db.query(Project).filter(Project.id == execution.project_id).first()
        if not project:
            execution.status = "failed"
            execution.error_message = "项目不存在"
            execution.completed_at = datetime.utcnow()
            db.commit()
            return
        
        if not project.source_path:
            execution.status = "failed"
            execution.error_message = "项目未上传源代码"
            execution.completed_at = datetime.utcnow()
            db.commit()
            return
        
        # 构建执行配置
        # 确保路径是绝对路径
        source_path = Path(project.source_path).resolve()
        if not source_path.exists():
            execution.status = "failed"
            execution.error_message = f"源代码路径不存在: {project.source_path}"
            execution.completed_at = datetime.utcnow()
            db.commit()
            return
        
        build_path = project.build_path or str(source_path / "build")
        build_dir = Path(build_path)
        build_dir.mkdir(parents=True, exist_ok=True)
        
        config = {
            "project_path": str(source_path),
            "source_path": str(source_path),
            "build_path": build_path,
            "binary_path": project.binary_path
        }
        
        # 获取执行器
        from app.executors.unit_executor import UnitExecutor
        executor = UnitExecutor()
        
        # 自动发现C++源文件并生成测试
        import asyncio
        result = asyncio.run(executor.execute_project(source_path, build_path))
        
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
            # 设置覆盖率百分比
            coverage_percentage = result["coverage"].get("percentage", 0)
            execution.coverage_percentage = coverage_percentage
        if result.get("artifacts"):
            execution.artifacts = result["artifacts"]
        
        execution.result = {
            "passed": result.get("passed_tests", 0),
            "failed": result.get("failed_tests", 0),
            "total": result.get("total_tests", 0),
            "coverage_percentage": result.get("coverage", {}).get("percentage", 0) if result.get("coverage") else 0
        }
        
        if result.get("error_message"):
            execution.error_message = result["error_message"]
        
        db.commit()
        
        print(f"✅ UTBotCpp项目测试完成 (ID: {execution_id})")
        print(f"   通过: {execution.passed_tests}, 失败: {execution.failed_tests}, 总计: {execution.total_tests}")
        if result.get("coverage"):
            print(f"   覆盖率: {result['coverage'].get('percentage', 0):.2f}%")
        
    except Exception as e:
        print(f"❌ UTBotCpp项目测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if execution:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            db.commit()
    
    finally:
        db.close()

