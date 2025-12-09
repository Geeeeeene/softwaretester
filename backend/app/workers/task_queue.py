"""
任务队列管理
使用Redis + RQ实现异步任务
"""
from redis import Redis
from rq import Queue
from app.core.config import settings

# 创建Redis连接
redis_conn = Redis.from_url(settings.REDIS_URL)

# 创建队列
default_queue = Queue('default', connection=redis_conn)
test_execution_queue = Queue('test_execution', connection=redis_conn)
static_analysis_queue = Queue('static_analysis', connection=redis_conn)
report_generation_queue = Queue('report_generation', connection=redis_conn)


def enqueue_test_execution(testcase_id: int, config: dict = None):
    """提交测试执行任务"""
    from app.workers.tasks.test_execution import execute_test
    job = test_execution_queue.enqueue(
        execute_test,
        testcase_id=testcase_id,
        config=config or {},
        job_timeout='30m'
    )
    return job.id


def enqueue_static_analysis(project_id: int, config: dict = None):
    """提交静态分析任务"""
    from app.workers.tasks.static_analysis import run_static_analysis
    job = static_analysis_queue.enqueue(
        run_static_analysis,
        project_id=project_id,
        config=config or {},
        job_timeout='1h'
    )
    return job.id


def get_job_status(job_id: str):
    """获取任务状态"""
    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        return {
            "id": job.id,
            "status": job.get_status(),
            "result": job.result,
            "exc_info": job.exc_info,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "ended_at": job.ended_at,
        }
    except Exception as e:
        return {"error": str(e)}

