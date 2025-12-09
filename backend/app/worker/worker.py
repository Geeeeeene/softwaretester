"""RQ Worker启动脚本"""
import redis
from rq import Worker, Queue, Connection

from app.core.config import settings

# 连接Redis
redis_conn = redis.from_url(settings.REDIS_URL)

if __name__ == "__main__":
    with Connection(redis_conn):
        # 创建队列
        queues = [
            Queue("default"),
            Queue("high"),
            Queue("low")
        ]
        
        # 启动Worker
        worker = Worker(queues)
        print(f"🚀 Worker启动成功，监听队列: {[q.name for q in queues]}")
        worker.work()

