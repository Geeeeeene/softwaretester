"""后台任务定义"""
import time
from typing import List
from datetime import datetime

from app.db.session import SessionLocal
from app.db.models.test_execution import TestExecution
from app.db.models.test_case import TestCase
from app.db.models.test_result import TestResult
from app.executors.factory import ExecutorFactory


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
        
        # 获取执行器
        executor = ExecutorFactory.get_executor(execution.executor_type)
        
        # 执行每个测试用例
        passed = 0
        failed = 0
        skipped = 0
        
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
                # 执行测试
                result = executor.execute(test_case.test_ir)
                
                # 保存结果
                test_result = TestResult(
                    execution_id=execution_id,
                    test_case_id=test_case_id,
                    status=result["status"],
                    duration_seconds=result.get("duration"),
                    error_message=result.get("error_message"),
                    log_path=result.get("log_path"),
                    screenshot_path=result.get("screenshot_path"),
                    extra_data=result.get("metadata", {}) or result.get("extra_data", {})
                )
                db.add(test_result)
                
                if result["status"] == "passed":
                    passed += 1
                    print(f"    ✅ 通过")
                elif result["status"] == "failed" or result["status"] == "error":
                    failed += 1
                    error_msg = result.get('error_message', '未知错误')
                    print(f"    ❌ 失败: {error_msg}")
                else:
                    skipped += 1
                    print(f"    ⏭️  跳过 (状态: {result['status']})")
                
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
        
        db.commit()
        
        print(f"✅ 测试执行完成 (ID: {execution_id})")
        print(f"   通过: {passed}, 失败: {failed}, 跳过: {skipped}")
        print(f"   耗时: {duration:.2f}秒")
        
    except Exception as e:
        # 处理执行失败
        print(f"❌ 测试执行失败: {str(e)}")
        
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

