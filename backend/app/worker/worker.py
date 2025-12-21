"""RQ Worker启动脚本"""
import redis
import os
from rq import Worker, Queue

from app.core.config import settings

# 连接Redis
redis_conn = redis.from_url(settings.REDIS_URL)

if __name__ == "__main__":
    # 从环境变量读取要监听的队列（Windows Worker可以指定特定队列）
    # 如果设置了 RQ_QUEUES 环境变量，使用指定的队列
    # 否则使用默认队列（default, high, low）
    rq_queues_env = os.environ.get('RQ_QUEUES', '').strip()
    
    if rq_queues_env:
        # 从环境变量读取队列名称（支持逗号分隔的多个队列）
        queue_names = [q.strip() for q in rq_queues_env.split(',') if q.strip()]
        queues = [Queue(name, connection=redis_conn) for name in queue_names]
        print(f"📋 从环境变量读取队列配置: RQ_QUEUES={rq_queues_env}")
    else:
        # 默认队列（Docker Worker使用）
        queues = [
            Queue("default", connection=redis_conn),
            Queue("high", connection=redis_conn),
            Queue("low", connection=redis_conn)
        ]
        print(f"📋 使用默认队列配置")
    
    # 启动Worker
    # Windows不支持fork和SIGALRM，需要使用SimpleWorker
    import sys
    if sys.platform == "win32":
        # Windows平台：使用SimpleWorker（不使用fork，不支持信号）
        from rq import SimpleWorker
        from rq.timeouts import BaseDeathPenalty
        
        # 创建一个Windows兼容的death_penalty类，不使用信号
        class WindowsDeathPenalty(BaseDeathPenalty):
            """Windows兼容的超时处理类，不使用SIGALRM信号"""
            def setup_death_penalty(self):
                # Windows不支持SIGALRM，所以不设置信号处理
                # 超时将通过其他机制处理（如线程）
                pass
            
            def cancel_death_penalty(self):
                # 无需取消信号处理
                pass
        
        # 创建一个Windows兼容的SimpleWorker子类
        class WindowsSimpleWorker(SimpleWorker):
            """Windows兼容的SimpleWorker，使用WindowsDeathPenalty"""
            death_penalty_class = WindowsDeathPenalty
        
        worker = WindowsSimpleWorker(
            queues, 
            connection=redis_conn
        )
        
        print(f"🚀 Worker启动成功（Windows模式），监听队列: {[q.name for q in queues]}")
    else:
        # Linux/Mac平台：使用标准Worker（支持fork）
        worker = Worker(queues, connection=redis_conn)
        print(f"🚀 Worker启动成功（Linux模式），监听队列: {[q.name for q in queues]}")
    
    worker.work()

