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
# 导入 StaticAnalysis 以确保 SQLAlchemy 关系正确解析
from app.db.models.static_analysis import StaticAnalysis
from app.executors.factory import ExecutorFactory
from app.models.testcase import TestType
from app.core.config import settings


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
        print(f"   测试用例数量: {len(test_case_ids)}")
        print(f"   执行器类型: {execution.executor_type}")
        
        # 获取项目配置
        project = db.query(Project).filter(Project.id == execution.project_id).first()
        print(f"   项目ID: {execution.project_id}")
        if not project:
            print(f"   ❌ 项目不存在")
            execution.status = "failed"
            execution.error_message = "项目不存在"
            execution.completed_at = datetime.utcnow()
            db.commit()
            return
        
        print(f"   ✅ 找到项目: {project.name}")
        print(f"   项目路径: {project.source_path}")
        
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
        print(f"   🔧 获取执行器: {execution.executor_type}")
        try:
            # 直接使用字符串类型，不需要转换为枚举
            executor = ExecutorFactory.get_executor(execution.executor_type)
            print(f"   ✅ 执行器创建成功: {type(executor).__name__}")
        except ValueError as e:
            print(f"   ❌ 执行器创建失败: {e}")
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
            print(f"\n  📋 处理测试用例 ID: {test_case_id}")
            # 获取测试用例
            test_case = db.query(TestCase).filter(
                TestCase.id == test_case_id
            ).first()
            
            if not test_case:
                print(f"  ⚠️  测试用例 {test_case_id} 不存在，跳过")
                skipped += 1
                continue
            
            print(f"  🧪 执行测试用例: {test_case.name}")
            print(f"     Test IR: {test_case.test_ir}")
            
            try:
                # 执行测试
                print(f"     ⏳ 开始执行分析...")
                # CppcheckExecutor.execute 只接受 test_ir 参数，不需要 config
                # 因为配置信息已经在 test_ir 中了
                result = executor.execute(test_case.test_ir)
                print(f"     ✅ 分析完成，结果: {result.get('status', 'unknown')}")
                
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
                    extra_data=result.get("metadata", {}) or result.get("extra_data", {})
                )
                db.add(test_result)
                
                if result.get("passed"):
                    passed += 1
                    print(f"    ✅ 通过")
                elif result.get("status") in ["failed", "error"]:
                    failed += 1
                    error_msg = result.get('error_message', '未知错误')
                    print(f"    ❌ 失败: {error_msg}")
                else:
                    skipped += 1
                    print(f"    ⏭️  跳过 (状态: {result.get('status', 'unknown')})")
                
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


def run_ui_test(
    execution_id: int,
    project_id: int,
    test_name: str,
    test_description: str,
    robot_script: str
):
    """
    Worker任务：执行UI测试（Robot Framework）
    在Windows主机上的worker中执行，可以访问Windows路径和Java环境
    """
    import asyncio
    from app.executors.robot_framework_executor import RobotFrameworkExecutor
    
    db = SessionLocal()
    start_time = time.time()
    execution = None
    
    try:
        print(f"🔍 查询执行记录: execution_id={execution_id}, project_id={project_id}")
        print(f"   数据库URL: {settings.DATABASE_URL}")
        
        # 先检查数据库连接（通过查询项目）
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                print(f"✅ 数据库连接正常，找到项目: {project.name}")
            else:
                print(f"⚠️  数据库连接正常，但项目 {project_id} 不存在")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 获取执行记录
        execution = db.query(TestExecution).filter(
            TestExecution.id == execution_id
        ).first()
        
        if not execution:
            # 尝试查询所有执行记录，看看是否有其他记录
            all_executions = db.query(TestExecution).filter(
                TestExecution.project_id == project_id
            ).order_by(TestExecution.id.desc()).limit(5).all()
            print(f"❌ 执行记录 {execution_id} 不存在")
            print(f"   项目 {project_id} 的最近执行记录: {[e.id for e in all_executions]}")
            print(f"   尝试查询所有执行记录...")
            all_all = db.query(TestExecution).order_by(TestExecution.id.desc()).limit(10).all()
            print(f"   数据库中所有执行记录: {[e.id for e in all_all]}")
            return
        
        print(f"✅ 找到执行记录: id={execution.id}, status={execution.status}, executor_type={execution.executor_type}")
        
        print(f"▶️  开始执行UI测试 (ID: {execution_id})")
        print(f"   测试名称: {test_name}")
        print(f"   项目ID: {project_id}")
        
        # 创建执行器
        print(f"   步骤1: 创建RobotFrameworkExecutor...")
        executor = RobotFrameworkExecutor()
        print(f"   ✅ 执行器创建成功")
        
        # 构建Test IR
        print(f"   步骤2: 构建Test IR...")
        test_ir = {
            "test_type": "robot_framework",
            "name": test_name,
            "description": test_description,
            "robot_script": robot_script,
            "variables": {},
            "timeout": 300
        }
        print(f"   ✅ Test IR构建完成")
        
        # 执行测试（在同步函数中运行异步代码）
        print(f"   步骤3: 开始执行测试...")
        try:
            # 尝试获取当前事件循环
            try:
                loop = asyncio.get_event_loop()
                print(f"   步骤3.1: 获取到事件循环，检查是否运行中...")
                if loop.is_running():
                    # 如果事件循环正在运行，创建新的事件循环
                    print(f"   步骤3.2: 事件循环正在运行，创建新的事件循环...")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    print(f"   步骤3.3: 在新事件循环中执行...")
                    result = loop.run_until_complete(executor.execute(test_ir, {}))
                else:
                    print(f"   步骤3.4: 事件循环未运行，直接执行...")
                    result = loop.run_until_complete(executor.execute(test_ir, {}))
            except RuntimeError as e:
                # 如果没有事件循环，创建新的事件循环
                print(f"   步骤3.5: 没有事件循环 (RuntimeError: {e})，创建新的事件循环...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                print(f"   步骤3.6: 在新事件循环中执行...")
                result = loop.run_until_complete(executor.execute(test_ir, {}))
        except Exception as e:
            # 如果所有方法都失败，使用 asyncio.run()
            print(f"   步骤3.7: 所有方法失败 (Exception: {e})，使用 asyncio.run()...")
            result = asyncio.run(executor.execute(test_ir, {}))
        
        print(f"   ✅ 测试执行完成，开始更新执行记录...")
        
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
        
        if result.get("error_message"):
            execution.error_message = result["error_message"]
        
        if result.get("logs"):
            if not execution.extra_data:
                execution.extra_data = {}
            execution.extra_data["logs"] = result["logs"]
        
        if result.get("artifacts"):
            if not execution.extra_data:
                execution.extra_data = {}
            execution.extra_data["artifacts"] = result["artifacts"]
        
        db.commit()
        
        print(f"✅ UI测试完成 (ID: {execution_id})")
        print(f"   状态: {execution.status}")
        print(f"   通过: {execution.passed_tests}, 失败: {execution.failed_tests}")
        if execution.error_message:
            print(f"   错误: {execution.error_message}")
        
    except Exception as e:
        print(f"❌ UI测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if execution:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = time.time() - start_time
            if not execution.extra_data:
                execution.extra_data = {}
            execution.extra_data["error_traceback"] = traceback.format_exc()
            db.commit()
    
    finally:
        db.close()

