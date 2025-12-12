"""RQ Worker启动脚本"""
import redis
from rq import Worker, Queue

from app.core.config import settings

# 连接Redis
redis_conn = redis.from_url(settings.REDIS_URL)

if __name__ == "__main__":
    # 创建队列（新版rq不需要Connection上下文管理器）
    queues = [
        Queue("default", connection=redis_conn),
        Queue("high", connection=redis_conn),
        Queue("low", connection=redis_conn)
    ]
    
    # 启动Worker
    worker = Worker(queues, connection=redis_conn)
    print(f"🚀 Worker启动成功，监听队列: {[q.name for q in queues]}")
    worker.work()

